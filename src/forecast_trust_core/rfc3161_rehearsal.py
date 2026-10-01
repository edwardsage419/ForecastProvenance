from __future__ import annotations

import hashlib
import os
import re
import subprocess
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Protocol, Sequence

from .canonical import parse_json_strict, seal_object, verify_sealed_object


CLASSIFICATION = "NON_FORECAST_REHEARSAL"
FINAL_STATUSES = {
    "REHEARSAL_VERIFIED",
    "REHEARSAL_INCOMPLETE",
    "REHEARSAL_FAILED",
}
CHECKER_VERSION = "1.3"
REVIEWED_ASSERTION_CLASSIFICATION = "REVIEWED_RFC3161_QUALIFICATION_SEMANTICS"
REVOCATION_VERIFICATION_SCOPE = "TSA_SIGNER_ONLY"
REQUIRED_EVIDENCE_NAMES = ("subject", "request", "response", "tool_versions")
QUALIFICATION_EVIDENCE_NAMES = ("trust_anchor", "independent_tsa_certificate")
OPTIONAL_EVIDENCE_NAMES = (
    "untrusted_chain",
    "crl",
    "provider_policy",
    "reviewed_semantic_assertion",
)
HEX_64 = re.compile(r"^[0-9a-f]{64}$")
PEM_CERTIFICATE = re.compile(
    rb"-----BEGIN CERTIFICATE-----\s+.*?-----END CERTIFICATE-----\s*",
    re.DOTALL,
)


class RehearsalEvidenceError(ValueError):
    pass


@dataclass(frozen=True)
class CertificateObservation:
    subject: str
    issuer: str
    serial: str
    not_before: str
    not_after: str
    eku: tuple[str, ...]
    eku_critical: bool
    sha256_der: str
    pem: bytes


@dataclass(frozen=True)
class TokenObservation:
    response_status: str
    message_imprint_algorithm: str
    message_imprint: str
    response_nonce: str
    gen_time: str
    policy_oid: str
    accuracy: str
    ordering: str
    certificates: tuple[CertificateObservation, ...]
    signer_sha256_der: str


@dataclass(frozen=True)
class RequestObservation:
    message_imprint_algorithm: str
    message_imprint: str
    nonce: str
    certificate_requested: bool


@dataclass(frozen=True)
class CrlObservation:
    issuer: str
    last_update: str
    next_update: str


class VerificationBackend(Protocol):
    def version(self) -> str: ...
    def parse_request(self, request: Path) -> RequestObservation: ...
    def parse_response(self, response: Path) -> TokenObservation: ...
    def inspect_trust_anchor(self, trust_anchor: Path) -> CertificateObservation: ...
    def inspect_certificate_chain(self, chain: Path) -> tuple[CertificateObservation, ...]: ...
    def verify_chain(
        self,
        tsa_certificate: bytes,
        trust_anchor: Path,
        untrusted_chain: Path | None,
        crl: Path | None,
        at_time: str,
    ) -> tuple[bool, str]: ...
    def verify_response(
        self,
        request: Path,
        response: Path,
        trust_anchor: Path,
        untrusted_chain: Path | None,
    ) -> tuple[bool, str]: ...
    def inspect_crl(self, crl: Path) -> CrlObservation: ...
    def verify_crl_signature(self, crl: Path, issuer_certificate: bytes) -> tuple[bool, str]: ...


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _resolve_evidence_path(root: Path, value: object, field: str) -> Path:
    if not isinstance(value, str) or not value:
        raise RehearsalEvidenceError(f"{field} must be a non-empty relative path")
    candidate = Path(value)
    if candidate.is_absolute():
        raise RehearsalEvidenceError(f"{field} must be relative to the evidence directory")
    resolved_root = root.resolve()
    resolved = (resolved_root / candidate).resolve()
    try:
        resolved.relative_to(resolved_root)
    except ValueError as exc:
        raise RehearsalEvidenceError(f"{field} escapes the evidence directory") from exc
    return resolved


def _required_profile(profile: Mapping[str, Any], key: str, expected_type: type) -> Any:
    value = profile.get(key)
    if not isinstance(value, expected_type):
        raise RehearsalEvidenceError(f"profile field {key} must be {expected_type.__name__}")
    return value


def _parse_utc(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (TypeError, ValueError) as exc:
        raise RehearsalEvidenceError(f"invalid UTC timestamp: {value!r}") from exc


def _normalize_hex(value: str) -> str:
    return re.sub(r"[^0-9A-Fa-f]", "", value).lower()


def _normalize_nonce(value: str) -> str:
    normalized = value.strip().lower()
    if normalized.startswith("0x"):
        normalized = normalized[2:]
    normalized = normalized.lstrip("0") or "0"
    if not re.fullmatch(r"[0-9a-f]+", normalized):
        raise RehearsalEvidenceError("nonce is not hexadecimal")
    return normalized


def _normalize_token_accuracy(value: str) -> str:
    if not isinstance(value, str):
        raise RehearsalEvidenceError("token accuracy must be a string")
    normalized = value.strip()
    if not normalized:
        raise RehearsalEvidenceError("token accuracy must be non-empty")
    if normalized.lower() == "unspecified":
        return "unspecified"
    return normalized


def _read_tool_versions(path: Path) -> list[str]:
    return [line.strip() for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip()]


def _blocker(code: str, detail: str) -> dict[str, str]:
    return {"code": code, "detail": detail}


def _result(ok: bool, detail: str) -> dict[str, object]:
    return {"verified": ok, "detail": detail}


def _redact_snapshot_path(value: str, snapshot_root: Path) -> str:
    redacted = value
    for variant in {str(snapshot_root), snapshot_root.as_posix()}:
        redacted = redacted.replace(variant, "<evidence_snapshot>")
    return redacted


class _SnapshotBackend:
    def __init__(self, backend: VerificationBackend, snapshot_root: Path) -> None:
        self._backend = backend
        self._snapshot_root = snapshot_root

    def __getattr__(self, name: str) -> Any:
        attribute = getattr(self._backend, name)
        if not callable(attribute):
            return attribute

        def invoke(*args: Any, **kwargs: Any) -> Any:
            try:
                result = attribute(*args, **kwargs)
            except (RehearsalEvidenceError, OSError, subprocess.SubprocessError) as exc:
                raise RehearsalEvidenceError(
                    _redact_snapshot_path(str(exc), self._snapshot_root)
                ) from exc
            if (
                isinstance(result, tuple)
                and len(result) == 2
                and isinstance(result[0], bool)
                and isinstance(result[1], str)
            ):
                return result[0], _redact_snapshot_path(result[1], self._snapshot_root)
            return result

        return invoke


def _snapshot_source_paths(
    evidence_dir: Path,
    files: Mapping[str, Any],
) -> tuple[dict[str, Path], dict[Path, Path]]:
    resolved_root = evidence_dir.resolve()
    resolved_fields: dict[str, Path] = {}
    resolved_paths: dict[Path, Path] = {}
    for name in (*REQUIRED_EVIDENCE_NAMES, *QUALIFICATION_EVIDENCE_NAMES):
        try:
            source = _resolve_evidence_path(
                evidence_dir, files.get(name), f"evidence_files.{name}"
            )
        except RehearsalEvidenceError:
            continue
        resolved_fields[name] = source
        resolved_paths[source] = source.relative_to(resolved_root)
    for name in OPTIONAL_EVIDENCE_NAMES:
        if name not in files:
            continue
        source = _resolve_evidence_path(
            evidence_dir, files[name], f"evidence_files.{name}"
        )
        resolved_fields[name] = source
        resolved_paths[source] = source.relative_to(resolved_root)
    return resolved_fields, resolved_paths


def check_rehearsal(
    evidence_dir: Path,
    profile: Mapping[str, Any],
    *,
    backend: VerificationBackend,
) -> dict[str, Any]:
    files = _required_profile(profile, "evidence_files", dict)
    if "crl_source" in profile:
        crl_source = profile["crl_source"]
        if not isinstance(crl_source, str) or not crl_source.strip():
            raise RehearsalEvidenceError(
                "profile field crl_source must be a non-empty string"
            )
    resolved_fields, source_paths = _snapshot_source_paths(evidence_dir, files)
    snapshot_profile = dict(profile)
    snapshot_files = dict(files)
    snapshot_profile["evidence_files"] = snapshot_files

    with tempfile.TemporaryDirectory(prefix="rfc3161-evidence-") as tmpdir:
        snapshot_root = Path(tmpdir)
        if os.name != "nt":
            snapshot_root.chmod(0o700)
        materialized_sources: set[Path] = set()
        for source, relative_path in source_paths.items():
            if not source.is_file():
                continue
            snapshot_path = snapshot_root / relative_path
            snapshot_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                snapshot_path.write_bytes(source.read_bytes())
            except OSError as exc:
                raise RehearsalEvidenceError(
                    "unable to create the private evidence snapshot"
                ) from exc
            snapshot_path.chmod(0o400)
            materialized_sources.add(source)
        for name, source in resolved_fields.items():
            if source in materialized_sources:
                snapshot_files[name] = source_paths[source].as_posix()
        return _check_snapshotted_rehearsal(
            snapshot_root,
            snapshot_profile,
            backend=_SnapshotBackend(backend, snapshot_root),
        )


def _review_semantic_assertion(
    path: Path | None,
    *,
    provider_id: str,
    provider_policy_sha256: str | None,
    token_policy_oid: str,
    token_accuracy: str,
) -> tuple[dict[str, Any], bool, bool, list[dict[str, str]], list[dict[str, str]]]:
    summary: dict[str, Any] = {"available": False, "verified": False}
    incomplete: list[dict[str, str]] = []
    failed: list[dict[str, str]] = []
    if path is None or not path.is_file():
        incomplete.append(_blocker(
            "REVIEWED_SEMANTIC_ASSERTION_MISSING",
            "no retained reviewed semantic assertion was configured",
        ))
        return summary, False, False, incomplete, failed

    summary["available"] = True
    summary["raw_sha256"] = _sha256(path)
    try:
        assertion = parse_json_strict(path.read_text(encoding="utf-8"))
        if not isinstance(assertion, dict) or not verify_sealed_object(assertion):
            raise RehearsalEvidenceError("reviewed semantic assertion seal is invalid")
        required = {
            "schema_version",
            "classification",
            "prospective_eligible",
            "provider_id",
            "provider_policy_sha256",
            "token_policy_oid",
            "policy_review_disposition",
            "accuracy_review_disposition",
            "observed_token_accuracy",
            "reviewer_id",
            "review_authority",
            "review_basis",
            "evidence_locator",
            "reviewed_at",
        }
        allowed = required | {
            "conservative_accuracy_bound_seconds",
            "object_type",
            "object_id",
            "payload_sha256",
            "content_sha256",
        }
        if not required.issubset(assertion):
            raise RehearsalEvidenceError("reviewed semantic assertion is missing required fields")
        if set(assertion) - allowed:
            raise RehearsalEvidenceError("reviewed semantic assertion contains unexpected fields")
        if assertion.get("object_type") != "RFC3161ReviewedSemanticAssertion":
            raise RehearsalEvidenceError("reviewed semantic assertion has the wrong object type")
        if assertion["schema_version"] != "1.1":
            raise RehearsalEvidenceError("reviewed semantic assertion has an unsupported schema version")
        if not isinstance(assertion["provider_policy_sha256"], str) or not HEX_64.fullmatch(
            assertion["provider_policy_sha256"]
        ):
            raise RehearsalEvidenceError("reviewed semantic assertion policy hash is invalid")
        if not isinstance(assertion["token_policy_oid"], str) or not assertion["token_policy_oid"].strip():
            raise RehearsalEvidenceError("reviewed semantic assertion policy OID is empty")
        if not isinstance(assertion["evidence_locator"], str) or not assertion["evidence_locator"].strip():
            raise RehearsalEvidenceError("reviewed semantic assertion evidence locator is empty")
        for field in ("reviewer_id", "review_authority", "review_basis"):
            if not isinstance(assertion[field], str) or not assertion[field].strip():
                raise RehearsalEvidenceError(f"reviewed semantic assertion {field} is empty")
        observed_accuracy = _normalize_token_accuracy(assertion["observed_token_accuracy"])
        current_accuracy = _normalize_token_accuracy(token_accuracy)
        _parse_utc(assertion["reviewed_at"])
        if assertion["policy_review_disposition"] not in {
            "DOCUMENTED_APPLICABLE", "NOT_DOCUMENTED", "NOT_APPLICABLE", "REJECTED"
        }:
            raise RehearsalEvidenceError("invalid policy review disposition")
        if assertion["accuracy_review_disposition"] not in {
            "DOCUMENTED_CONSERVATIVE_BOUND", "TOKEN_ACCURACY_ACCEPTED", "NOT_DOCUMENTED", "REJECTED"
        }:
            raise RehearsalEvidenceError("invalid accuracy review disposition")
        bound = assertion.get("conservative_accuracy_bound_seconds")
        if assertion["accuracy_review_disposition"] == "DOCUMENTED_CONSERVATIVE_BOUND":
            if observed_accuracy != "unspecified":
                raise RehearsalEvidenceError(
                    "conservative accuracy review requires an unspecified observed token accuracy"
                )
            if type(bound) is not int or bound < 0:
                raise RehearsalEvidenceError("conservative accuracy bound must be a non-negative integer")
        else:
            if "conservative_accuracy_bound_seconds" in assertion:
                raise RehearsalEvidenceError("conservative accuracy bound is present for an incompatible disposition")
            if (
                assertion["accuracy_review_disposition"] == "TOKEN_ACCURACY_ACCEPTED"
                and observed_accuracy == "unspecified"
            ):
                raise RehearsalEvidenceError(
                    "accepted token accuracy review requires a specified observed token accuracy"
                )
    except (OSError, ValueError, RehearsalEvidenceError) as exc:
        incomplete.append(_blocker("REVIEWED_SEMANTIC_ASSERTION_INVALID", str(exc)))
        return summary, False, False, incomplete, failed

    summary.update({
        "classification": assertion["classification"],
        "content_sha256": assertion["content_sha256"],
        "provider_id": assertion["provider_id"],
        "provider_policy_sha256": assertion["provider_policy_sha256"],
        "token_policy_oid": assertion["token_policy_oid"],
        "policy_review_disposition": assertion["policy_review_disposition"],
        "accuracy_review_disposition": assertion["accuracy_review_disposition"],
        "observed_token_accuracy": observed_accuracy,
        "reviewer_id": assertion["reviewer_id"],
        "review_authority": assertion["review_authority"],
        "review_basis": assertion["review_basis"],
        "evidence_locator": assertion["evidence_locator"],
        "reviewed_at": assertion["reviewed_at"],
    })
    if "conservative_accuracy_bound_seconds" in assertion:
        summary["conservative_accuracy_bound_seconds"] = assertion["conservative_accuracy_bound_seconds"]

    if (
        assertion["classification"] != REVIEWED_ASSERTION_CLASSIFICATION
        or assertion["prospective_eligible"] is not False
        or assertion["provider_id"] != provider_id
    ):
        failed.append(_blocker(
            "REVIEWED_SEMANTIC_ASSERTION_CONTRADICTION",
            "assertion classification, eligibility, or provider contradicts the rehearsal",
        ))
        return summary, False, False, incomplete, failed
    if provider_policy_sha256 is None or assertion["provider_policy_sha256"] != provider_policy_sha256:
        incomplete.append(_blocker(
            "REVIEWED_SEMANTIC_ASSERTION_POLICY_HASH_MISMATCH",
            "assertion does not bind the exact retained provider policy artifact",
        ))
        return summary, False, False, incomplete, failed
    if assertion["token_policy_oid"] != token_policy_oid:
        incomplete.append(_blocker(
            "REVIEWED_SEMANTIC_ASSERTION_POLICY_OID_MISMATCH",
            "assertion does not cover the observed token policy OID",
        ))
        return summary, False, False, incomplete, failed
    if observed_accuracy != current_accuracy:
        incomplete.append(_blocker(
            "REVIEWED_SEMANTIC_ASSERTION_ACCURACY_MISMATCH",
            "assertion does not bind the exact observed token accuracy",
        ))
        return summary, False, False, incomplete, failed

    policy_ok = assertion["policy_review_disposition"] == "DOCUMENTED_APPLICABLE"
    if current_accuracy == "unspecified":
        accuracy_ok = assertion["accuracy_review_disposition"] == "DOCUMENTED_CONSERVATIVE_BOUND"
    else:
        accuracy_ok = assertion["accuracy_review_disposition"] == "TOKEN_ACCURACY_ACCEPTED"
    summary["verified"] = policy_ok and accuracy_ok
    return summary, policy_ok, accuracy_ok, incomplete, failed


def _check_snapshotted_rehearsal(
    evidence_dir: Path,
    profile: Mapping[str, Any],
    *,
    backend: VerificationBackend,
) -> dict[str, Any]:
    provider_id = _required_profile(profile, "provider_id", str)
    classification = _required_profile(profile, "classification", str)
    prospective_eligible = profile.get("prospective_eligible")
    if classification != CLASSIFICATION or prospective_eligible is not False:
        raise RehearsalEvidenceError(
            "profile must be NON_FORECAST_REHEARSAL with prospective_eligible=false"
        )
    captured_utc = _required_profile(profile, "captured_utc", str)
    _parse_utc(captured_utc)
    files = _required_profile(profile, "evidence_files", dict)
    trust_anchor_source = _required_profile(profile, "trust_anchor_source", str)
    policy_source = profile.get("provider_policy_evidence_source", "UNAVAILABLE")
    if not isinstance(policy_source, str):
        raise RehearsalEvidenceError("provider_policy_evidence_source must be a string")
    crl_source = profile.get("crl_source", "UNSPECIFIED")
    if not isinstance(crl_source, str) or not crl_source.strip():
        raise RehearsalEvidenceError(
            "profile field crl_source must be a non-empty string"
        )

    paths: dict[str, Path] = {}
    incomplete: list[dict[str, str]] = []
    failed: list[dict[str, str]] = []
    core_evidence_missing = False
    for name in REQUIRED_EVIDENCE_NAMES:
        try:
            path = _resolve_evidence_path(evidence_dir, files.get(name), f"evidence_files.{name}")
        except RehearsalEvidenceError as exc:
            incomplete.append(_blocker("MISSING_RAW_EVIDENCE", str(exc)))
            core_evidence_missing = True
            continue
        paths[name] = path
        if not path.is_file():
            incomplete.append(_blocker("MISSING_RAW_EVIDENCE", f"missing {name}: {files.get(name)}"))
            core_evidence_missing = True

    for name in QUALIFICATION_EVIDENCE_NAMES:
        try:
            path = _resolve_evidence_path(evidence_dir, files.get(name), f"evidence_files.{name}")
        except RehearsalEvidenceError as exc:
            incomplete.append(_blocker("MISSING_QUALIFICATION_EVIDENCE", str(exc)))
            continue
        paths[name] = path
        if not path.is_file():
            incomplete.append(_blocker("MISSING_QUALIFICATION_EVIDENCE", f"missing {name}: {files.get(name)}"))

    optional_paths: dict[str, Path] = {}
    for name in OPTIONAL_EVIDENCE_NAMES:
        if name in files:
            path = _resolve_evidence_path(evidence_dir, files[name], f"evidence_files.{name}")
            optional_paths[name] = path
            if not path.is_file():
                incomplete.append(_blocker("MISSING_RAW_EVIDENCE", f"missing {name}: {files[name]}"))

    base_report: dict[str, Any] = {
        "schema_version": "1.2",
        "checker_version": CHECKER_VERSION,
        "classification": CLASSIFICATION,
        "prospective_eligible": False,
        "provider_id": provider_id,
        "captured_utc": captured_utc,
        "trust_anchor_source": trust_anchor_source,
        "provider_policy_evidence_source": policy_source,
        "policy_semantics_documented": False,
        "accuracy_semantics_documented": False,
        "semantic_assertion_evidence": {"available": False, "verified": False},
        "revocation_verification_scope": REVOCATION_VERIFICATION_SCOPE,
        "tool_versions": [],
        "raw_evidence_sha256": {},
        "embedded_certificate_inventory": [],
        "unresolved_qualification_blockers": [],
    }

    if core_evidence_missing:
        for name, path in sorted(paths.items()):
            if path.is_file():
                base_report["raw_evidence_sha256"][name] = _sha256(path)
        if paths.get("tool_versions", Path()).is_file():
            base_report["tool_versions"] = _read_tool_versions(paths["tool_versions"])
        base_report["unresolved_qualification_blockers"] = sorted(
            incomplete, key=lambda item: (item["code"], item["detail"])
        )
        base_report["final_rehearsal_status"] = "REHEARSAL_INCOMPLETE"
        return seal_object(
            base_report,
            object_type="RFC3161QualificationRehearsalReport",
            stable_context=provider_id,
        )

    for name, path in sorted({**paths, **optional_paths}.items()):
        if path.is_file():
            base_report["raw_evidence_sha256"][name] = _sha256(path)
    base_report["tool_versions"] = _read_tool_versions(paths["tool_versions"])
    base_report["checker_tool_version"] = backend.version()

    try:
        request = backend.parse_request(paths["request"])
        token = backend.parse_response(paths["response"])
    except (RehearsalEvidenceError, OSError, subprocess.SubprocessError) as exc:
        failed.append(_blocker("MALFORMED_RFC3161_RESPONSE", str(exc)))
        base_report["unresolved_qualification_blockers"] = failed
        base_report["final_rehearsal_status"] = "REHEARSAL_FAILED"
        return seal_object(
            base_report,
            object_type="RFC3161QualificationRehearsalReport",
            stable_context=provider_id,
        )

    anchor = None
    independent_tsa = None
    retained_chain_certificates: tuple[CertificateObservation, ...] = ()
    try:
        if paths.get("trust_anchor", Path()).is_file():
            anchor = backend.inspect_trust_anchor(paths["trust_anchor"])
        if paths.get("independent_tsa_certificate", Path()).is_file():
            independent_tsa = backend.inspect_trust_anchor(paths["independent_tsa_certificate"])
        if optional_paths.get("untrusted_chain", Path()).is_file():
            retained_chain_certificates = backend.inspect_certificate_chain(
                optional_paths["untrusted_chain"]
            )
    except (RehearsalEvidenceError, OSError, subprocess.SubprocessError) as exc:
        failed.append(_blocker("MALFORMED_CERTIFICATE_EVIDENCE", str(exc)))

    subject_sha256 = _sha256(paths["subject"])
    request_imprint = _normalize_hex(request.message_imprint)
    response_imprint = _normalize_hex(token.message_imprint)
    try:
        request_nonce = _normalize_nonce(request.nonce)
        response_nonce = _normalize_nonce(token.response_nonce)
    except RehearsalEvidenceError as exc:
        failed.append(_blocker("MALFORMED_NONCE", str(exc)))
        request_nonce = request.nonce
        response_nonce = token.response_nonce

    imprint_match = (
        request.message_imprint_algorithm.lower() == "sha256"
        and token.message_imprint_algorithm.lower() == "sha256"
        and request_imprint == subject_sha256
        and response_imprint == subject_sha256
    )
    nonce_equal = request_nonce == response_nonce
    if not imprint_match:
        failed.append(_blocker("MESSAGE_IMPRINT_MISMATCH", "request/response imprint does not match subject SHA256"))
    if not nonce_equal:
        failed.append(_blocker("NONCE_MISMATCH", "request nonce differs from response nonce"))
    if not request.certificate_requested:
        failed.append(_blocker("CERTIFICATE_NOT_REQUESTED", "request did not require embedded certificates"))
    if token.response_status.upper() not in {"GRANTED", "GRANTED_WITH_MODS"}:
        failed.append(_blocker("RFC3161_STATUS_NOT_GRANTED", token.response_status))

    inventory = []
    tsa_certificates = []
    for cert in token.certificates:
        role = "TSA_SIGNER" if cert.sha256_der == token.signer_sha256_der else "EMBEDDED_CHAIN"
        if role == "TSA_SIGNER":
            tsa_certificates.append(cert)
        inventory.append({
            "role": role,
            "subject": cert.subject,
            "issuer": cert.issuer,
            "serial": cert.serial.upper(),
            "not_before": cert.not_before,
            "not_after": cert.not_after,
            "extended_key_usage": list(cert.eku),
            "extended_key_usage_critical": cert.eku_critical,
            "sha256_der": cert.sha256_der,
        })
    inventory.sort(key=lambda item: (item["role"], item["sha256_der"]))
    base_report["embedded_certificate_inventory"] = inventory
    if len(tsa_certificates) != 1:
        failed.append(_blocker("TSA_CERTIFICATE_SELECTION_FAILED", f"expected one Time Stamping certificate, observed {len(tsa_certificates)}"))

    tsa = tsa_certificates[0] if len(tsa_certificates) == 1 else None
    independent_tsa_matches = bool(
        tsa and independent_tsa and tsa.sha256_der == independent_tsa.sha256_der
    )
    if tsa is not None and independent_tsa is not None and not independent_tsa_matches:
        failed.append(_blocker("INDEPENDENT_TSA_CERTIFICATE_MISMATCH", "independent TSA certificate differs from token-embedded signer"))
    chain_ok = False
    chain_detail = "not attempted because TSA certificate selection failed"
    signature_ok = False
    signature_detail = "not attempted because TSA certificate selection failed"
    revocation_ok = False
    revocation_detail = "CRL evidence unavailable"
    crl_signature_ok = False
    crl_signature_detail = "CRL evidence unavailable"

    if tsa is not None:
        if not tsa.eku_critical or tuple(item.lower() for item in tsa.eku) != ("time stamping",):
            failed.append(_blocker("INVALID_TSA_EKU", "TSA EKU must be critical and limited to Time Stamping"))
        try:
            gen_time = _parse_utc(token.gen_time)
            not_before = _parse_utc(tsa.not_before)
            not_after = _parse_utc(tsa.not_after)
            if not (not_before <= gen_time <= not_after):
                failed.append(_blocker("TSA_CERTIFICATE_INVALID_AT_GENTIME", "token genTime is outside TSA certificate validity"))
        except RehearsalEvidenceError as exc:
            failed.append(_blocker("INVALID_CERTIFICATE_TIME_RELATIONSHIP", str(exc)))

        if anchor is not None:
            chain_ok, chain_detail = backend.verify_chain(
                tsa.pem,
                paths["trust_anchor"],
                optional_paths.get("untrusted_chain"),
                None,
                token.gen_time,
            )
            signature_ok, signature_detail = backend.verify_response(
                paths["request"],
                paths["response"],
                paths["trust_anchor"],
                optional_paths.get("untrusted_chain"),
            )
            if not chain_ok:
                failed.append(_blocker("CERTIFICATE_CHAIN_VERIFICATION_FAILED", chain_detail))
            if not signature_ok:
                failed.append(_blocker("RFC3161_SIGNATURE_VERIFICATION_FAILED", signature_detail))

    crl_report: dict[str, object] = {"available": False}
    if "crl" in optional_paths and anchor is not None:
        try:
            crl_observation = backend.inspect_crl(optional_paths["crl"])
            issuer_candidates = [
                certificate
                for certificate in (anchor, *retained_chain_certificates)
                if tsa is not None and certificate.subject == tsa.issuer
            ]
            selected_issuer = issuer_candidates[0] if len(issuer_candidates) == 1 else None
            if selected_issuer is None:
                detail = (
                    "no independently retained certificate matches the TSA signer issuer"
                    if not issuer_candidates
                    else "multiple independently retained certificates match the TSA signer issuer"
                )
                failed.append(_blocker("SIGNER_ISSUER_CERTIFICATE_SELECTION_FAILED", detail))
                crl_signature_detail = f"not attempted: {detail}"
            else:
                crl_signature_ok, crl_signature_detail = backend.verify_crl_signature(
                    optional_paths["crl"], selected_issuer.pem
                )
            crl_window_ok = _parse_utc(crl_observation.last_update) <= _parse_utc(token.gen_time) <= _parse_utc(crl_observation.next_update)
            crl_issuer_matches = bool(tsa and crl_observation.issuer == tsa.issuer)
            revocation_chain_ok = False
            revocation_chain_detail = "not attempted because direct signer issuer selection failed"
            if selected_issuer is not None and crl_issuer_matches:
                revocation_chain_ok, revocation_chain_detail = backend.verify_chain(
                    tsa.pem,
                    paths["trust_anchor"],
                    optional_paths.get("untrusted_chain"),
                    optional_paths["crl"],
                    token.gen_time,
                )
            revocation_ok = (
                chain_ok
                and selected_issuer is not None
                and crl_signature_ok
                and crl_window_ok
                and crl_issuer_matches
                and revocation_chain_ok
            )
            revocation_detail = "CRL check and capture window verified" if revocation_ok else "CRL verification or capture window failed"
            crl_report = {
                "available": True,
                "verification_scope": REVOCATION_VERIFICATION_SCOPE,
                "source": crl_source,
                "sha256": _sha256(optional_paths["crl"]),
                "issuer": crl_observation.issuer,
                "signer_issuer_subject": tsa.issuer if tsa else "UNAVAILABLE",
                "selected_crl_issuer_certificate_subject": (
                    selected_issuer.subject if selected_issuer else "UNAVAILABLE"
                ),
                "selected_crl_issuer_certificate_sha256_der": (
                    selected_issuer.sha256_der if selected_issuer else "UNAVAILABLE"
                ),
                "crl_issuer_matches_signer_issuer": crl_issuer_matches,
                "last_update": crl_observation.last_update,
                "next_update": crl_observation.next_update,
                "signature_verification": _result(crl_signature_ok, crl_signature_detail),
                "chain_revocation_verification": _result(
                    revocation_chain_ok, revocation_chain_detail
                ),
                "certificate_revocation_check": _result(revocation_ok, revocation_detail),
            }
            if not crl_signature_ok:
                failed.append(_blocker("CRL_SIGNATURE_VERIFICATION_FAILED", crl_signature_detail))
            if not crl_issuer_matches:
                failed.append(_blocker("CRL_ISSUER_MISMATCH", "CRL issuer differs from TSA signer issuer"))
            if not crl_window_ok:
                failed.append(_blocker("CRL_WINDOW_EXCLUDES_GENTIME", "token genTime is outside retained CRL window"))
            if not revocation_ok:
                failed.append(_blocker("CERTIFICATE_REVOCATION_CHECK_FAILED", revocation_detail))
        except (RehearsalEvidenceError, OSError, subprocess.SubprocessError) as exc:
            failed.append(_blocker("CRL_EVIDENCE_MALFORMED", str(exc)))
    elif "crl" not in optional_paths:
        incomplete.append(_blocker("REVOCATION_EVIDENCE_MISSING", "no retained CRL was configured"))
    else:
        incomplete.append(_blocker("REVOCATION_EVIDENCE_UNVERIFIABLE", "CRL cannot be verified without a trust anchor"))

    provider_policy_sha256 = (
        _sha256(optional_paths["provider_policy"])
        if optional_paths.get("provider_policy", Path()).is_file()
        else None
    )
    assertion_summary, policy_ok, accuracy_ok, assertion_incomplete, assertion_failed = (
        _review_semantic_assertion(
            optional_paths.get("reviewed_semantic_assertion"),
            provider_id=provider_id,
            provider_policy_sha256=provider_policy_sha256,
            token_policy_oid=token.policy_oid,
            token_accuracy=token.accuracy,
        )
    )
    incomplete.extend(assertion_incomplete)
    failed.extend(assertion_failed)
    base_report["semantic_assertion_evidence"] = assertion_summary
    base_report["policy_semantics_documented"] = policy_ok
    base_report["accuracy_semantics_documented"] = accuracy_ok
    if not policy_ok:
        incomplete.append(_blocker("TOKEN_POLICY_SEMANTICS_UNDOCUMENTED", f"no frozen applicable semantics for {token.policy_oid}"))
    if token.accuracy.lower() == "unspecified" and not accuracy_ok:
        incomplete.append(_blocker("TIMESTAMP_ACCURACY_UNSPECIFIED", "token omits accuracy and no reviewed applicable conservative bound is retained"))
    elif token.accuracy.lower() != "unspecified" and not accuracy_ok:
        incomplete.append(_blocker("ACCURACY_SEMANTICS_UNDOCUMENTED", "declared token accuracy semantics are not frozen"))

    base_report.update({
        "subject_sha256": subject_sha256,
        "request_sha256": _sha256(paths["request"]),
        "response_sha256": _sha256(paths["response"]),
        "rfc3161_response_status": token.response_status,
        "message_imprint_algorithm": token.message_imprint_algorithm.lower(),
        "message_imprint": response_imprint,
        "message_imprint_matches_subject": imprint_match,
        "request_nonce": request_nonce,
        "response_nonce": response_nonce,
        "nonce_equal": nonce_equal,
        "certificate_requested": request.certificate_requested,
        "tsa_certificate_sha256_der": tsa.sha256_der if tsa else "UNAVAILABLE",
        "tsa_certificate_serial": tsa.serial.upper() if tsa else "UNAVAILABLE",
        "tsa_certificate_not_before": tsa.not_before if tsa else "UNAVAILABLE",
        "tsa_certificate_not_after": tsa.not_after if tsa else "UNAVAILABLE",
        "tsa_certificate_extended_key_usage": list(tsa.eku) if tsa else [],
        "tsa_certificate_extended_key_usage_critical": tsa.eku_critical if tsa else False,
        "token_gen_time": token.gen_time,
        "token_policy_oid": token.policy_oid,
        "token_accuracy": token.accuracy,
        "token_ordering": token.ordering,
        "trust_anchor_sha256_der": anchor.sha256_der if anchor else "UNAVAILABLE",
        "trust_anchor_matches_embedded_certificate": any(
            anchor is not None and cert.sha256_der == anchor.sha256_der for cert in token.certificates
        ),
        "independent_tsa_certificate_sha256_der": independent_tsa.sha256_der if independent_tsa else "UNAVAILABLE",
        "independent_tsa_certificate_matches_embedded": independent_tsa_matches,
        "certificate_chain_verification": _result(chain_ok, chain_detail),
        "rfc3161_signature_verification": _result(signature_ok, signature_detail),
        "crl_evidence": crl_report,
    })

    blockers = failed + incomplete
    base_report["unresolved_qualification_blockers"] = sorted(
        blockers, key=lambda item: (item["code"], item["detail"])
    )
    if failed:
        status = "REHEARSAL_FAILED"
    elif incomplete:
        status = "REHEARSAL_INCOMPLETE"
    else:
        status = "REHEARSAL_VERIFIED"
    if status not in FINAL_STATUSES:
        raise AssertionError("invalid internal rehearsal status")
    base_report["final_rehearsal_status"] = status
    return seal_object(
        base_report,
        object_type="RFC3161QualificationRehearsalReport",
        stable_context=provider_id,
    )


class OpenSSLBackend:
    def __init__(self, executable: str = "openssl") -> None:
        self.executable = executable

    def _run(self, args: Sequence[str], *, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
        result = subprocess.run(
            [self.executable, *args],
            input=input_bytes,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", errors="replace").strip()
            raise RehearsalEvidenceError(f"OpenSSL {' '.join(args[:2])} failed: {detail}")
        return result

    def version(self) -> str:
        return self._run(["version"]).stdout.decode("utf-8", errors="replace").strip()

    @staticmethod
    def _field(text: str, label: str) -> str:
        match = re.search(rf"^\s*{re.escape(label)}\s*[=:]\s*(.*?)\s*$", text, re.MULTILINE | re.IGNORECASE)
        if not match:
            raise RehearsalEvidenceError(f"OpenSSL output missing {label}")
        return match.group(1)

    @staticmethod
    def _message_data(text: str) -> str:
        match = re.search(r"Message data:\s*\n((?:\s+[0-9a-fA-F]{4}\s*-.*\n?)+)", text)
        if not match:
            raise RehearsalEvidenceError("OpenSSL output missing message data")
        octets = []
        for line in match.group(1).splitlines():
            _, payload = line.split("-", 1)
            hex_part = payload.split("   ", 1)[0]
            octets.append(_normalize_hex(hex_part))
        value = "".join(octets)
        if not HEX_64.fullmatch(value):
            raise RehearsalEvidenceError("message imprint is not SHA256 length")
        return value

    @staticmethod
    def _openssl_time(value: str) -> str:
        parsed = datetime.strptime(value.strip(), "%b %d %H:%M:%S %Y GMT").replace(tzinfo=timezone.utc)
        return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")

    def parse_request(self, request: Path) -> RequestObservation:
        text = self._run(["ts", "-query", "-in", str(request), "-text"]).stdout.decode("utf-8", errors="replace")
        return RequestObservation(
            message_imprint_algorithm=self._field(text, "Hash Algorithm"),
            message_imprint=self._message_data(text),
            nonce=self._field(text, "Nonce"),
            certificate_requested=self._field(text, "Certificate required").lower() == "yes",
        )

    def parse_response(self, response: Path) -> TokenObservation:
        text = self._run(["ts", "-reply", "-in", str(response), "-text"]).stdout.decode("utf-8", errors="replace")
        status = self._field(text, "Status").rstrip(".").upper().replace(" ", "_")
        with tempfile.TemporaryDirectory() as tmpdir:
            token_path = Path(tmpdir) / "token.der"
            certs_path = Path(tmpdir) / "certificates.pem"
            signer_path = Path(tmpdir) / "signer.pem"
            content_path = Path(tmpdir) / "signed-content.der"
            token_path.write_bytes(self._run(["ts", "-reply", "-in", str(response), "-token_out"]).stdout)
            certs_path.write_bytes(self._run(["pkcs7", "-inform", "DER", "-in", str(token_path), "-print_certs"]).stdout)
            certificates = tuple(self._inspect_certificate_bytes(value) for value in PEM_CERTIFICATE.findall(certs_path.read_bytes()))
            self._run([
                "cms", "-verify", "-inform", "DER", "-in", str(token_path),
                "-noverify", "-signer", str(signer_path), "-out", str(content_path),
            ])
            signer_matches = PEM_CERTIFICATE.findall(signer_path.read_bytes())
            if len(signer_matches) != 1:
                raise RehearsalEvidenceError("CMS signer extraction did not return exactly one certificate")
            signer_sha256_der = self._inspect_certificate_bytes(signer_matches[0]).sha256_der
        return TokenObservation(
            response_status=status,
            message_imprint_algorithm=self._field(text, "Hash Algorithm"),
            message_imprint=self._message_data(text),
            response_nonce=self._field(text, "Nonce"),
            gen_time=self._openssl_time(self._field(text, "Time stamp")),
            policy_oid=self._field(text, "Policy OID"),
            accuracy=self._field(text, "Accuracy"),
            ordering=self._field(text, "Ordering"),
            certificates=certificates,
            signer_sha256_der=signer_sha256_der,
        )

    def _inspect_certificate_bytes(self, pem: bytes) -> CertificateObservation:
        text = self._run([
            "x509", "-noout", "-subject", "-issuer", "-serial", "-dates", "-ext", "extendedKeyUsage"
        ], input_bytes=pem).stdout.decode("utf-8", errors="replace")
        der = self._run(["x509", "-outform", "DER"], input_bytes=pem).stdout
        eku_match = re.search(r"X509v3 Extended Key Usage:\s*(critical)?\s*\n\s*(.*?)\s*$", text, re.MULTILINE)
        eku = tuple(part.strip() for part in eku_match.group(2).split(",")) if eku_match else ()
        return CertificateObservation(
            subject=self._field(text, "subject"),
            issuer=self._field(text, "issuer"),
            serial=self._field(text, "serial"),
            not_before=self._openssl_time(self._field(text, "notBefore")),
            not_after=self._openssl_time(self._field(text, "notAfter")),
            eku=eku,
            eku_critical=bool(eku_match and eku_match.group(1)),
            sha256_der=_sha256_bytes(der),
            pem=pem,
        )

    def inspect_trust_anchor(self, trust_anchor: Path) -> CertificateObservation:
        matches = PEM_CERTIFICATE.findall(trust_anchor.read_bytes())
        if len(matches) != 1:
            raise RehearsalEvidenceError("trust anchor file must contain exactly one certificate")
        return self._inspect_certificate_bytes(matches[0])

    def inspect_certificate_chain(self, chain: Path) -> tuple[CertificateObservation, ...]:
        matches = PEM_CERTIFICATE.findall(chain.read_bytes())
        if not matches:
            raise RehearsalEvidenceError("untrusted chain file must contain at least one certificate")
        return tuple(self._inspect_certificate_bytes(match) for match in matches)

    @staticmethod
    def _epoch(value: str) -> str:
        return str(int(_parse_utc(value).timestamp()))

    def verify_chain(self, tsa_certificate: bytes, trust_anchor: Path, untrusted_chain: Path | None, crl: Path | None, at_time: str) -> tuple[bool, str]:
        with tempfile.TemporaryDirectory() as tmpdir:
            tsa_path = Path(tmpdir) / "tsa.pem"
            tsa_path.write_bytes(tsa_certificate)
            args = ["verify", "-attime", self._epoch(at_time), "-CAfile", str(trust_anchor)]
            if untrusted_chain is not None:
                args.extend(["-untrusted", str(untrusted_chain)])
            if crl is not None:
                args.extend(["-crl_check", "-CRLfile", str(crl)])
            args.append(str(tsa_path))
            result = subprocess.run([self.executable, *args], capture_output=True, check=False)
        detail = (result.stdout + result.stderr).decode("utf-8", errors="replace").strip()
        if result.returncode == 0:
            return True, "OpenSSL certificate verification succeeded"
        return False, detail.replace(str(tsa_path), "<tsa_certificate>")

    def verify_response(self, request: Path, response: Path, trust_anchor: Path, untrusted_chain: Path | None) -> tuple[bool, str]:
        args = ["ts", "-verify", "-queryfile", str(request), "-in", str(response), "-CAfile", str(trust_anchor)]
        if untrusted_chain is not None:
            args.extend(["-untrusted", str(untrusted_chain)])
        result = subprocess.run([self.executable, *args], capture_output=True, check=False)
        detail = (result.stdout + result.stderr).decode("utf-8", errors="replace").strip()
        return (
            (True, "OpenSSL RFC 3161 verification succeeded")
            if result.returncode == 0
            else (False, detail)
        )

    def inspect_crl(self, crl: Path) -> CrlObservation:
        text = self._run(["crl", "-in", str(crl), "-noout", "-issuer", "-lastupdate", "-nextupdate"]).stdout.decode("utf-8", errors="replace")
        return CrlObservation(
            issuer=self._field(text, "issuer"),
            last_update=self._openssl_time(self._field(text, "lastUpdate")),
            next_update=self._openssl_time(self._field(text, "nextUpdate")),
        )

    def verify_crl_signature(self, crl: Path, issuer_certificate: bytes) -> tuple[bool, str]:
        with tempfile.TemporaryDirectory() as tmpdir:
            issuer_path = Path(tmpdir) / "crl-issuer.pem"
            issuer_path.write_bytes(issuer_certificate)
            result = subprocess.run(
                [self.executable, "crl", "-in", str(crl), "-noout", "-verify", "-CAfile", str(issuer_path)],
                capture_output=True,
                check=False,
            )
        detail = (result.stdout + result.stderr).decode("utf-8", errors="replace").strip()
        return (
            (True, "OpenSSL CRL signature verification succeeded")
            if result.returncode == 0
            else (False, detail)
        )
