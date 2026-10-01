from __future__ import annotations

import base64
import binascii
import hashlib
from pathlib import Path
from typing import Any, Callable, Mapping

from ._ed25519_qualification import (
    validate_build_profile as validate_ed25519_build_profile,
)
from ._ed25519_verifier import PinnedEd25519Verifier
from ._roughtime_control import (
    validate_verifier_build_profile as validate_roughtime_verifier_build_profile,
)
from ._roughtime_production_qualification import (
    CRITERIA_ID,
    CRITERIA_SHA256,
    DECISION_SIGNATURE_PROJECTION,
    collect_manifest_artifacts,
)
from ._roughtime_production_qualification_hardening import (
    derive_authoritative_qualification_state,
    validate_bound_qualification_decision,
    validate_bound_qualification_review,
)
from .canonical import (
    CanonicalizationError,
    canonical_json,
    content_hash,
    parse_json_strict,
    validate_ref,
    verify_sealed_object,
)
from .qualification_state_package_v2 import (
    PackageClosureResult,
    QualificationStatePackageError,
    QualificationStatePackageStage,
    build_package_closure,
    validate_history_completeness,
    validate_history_cutoff,
    validate_history_succession,
)
from .qualification_validation_contracts_v1 import (
    build_qualification_validation_result,
    qualification_state_history_snapshot_signature_message,
    qualification_state_history_snapshot_signed_projection,
    validate_qualification_validation_contract,
    validate_qualification_validation_invocation,
)



class _NoAuthoritativeResult(Exception):
    """A trusted input could not be authenticated or resolved."""


def _exact_ref(value: Mapping[str, Any]) -> dict[str, str]:
    try:
        validate_ref(value)
    except (CanonicalizationError, KeyError, TypeError, ValueError) as exc:
        raise _NoAuthoritativeResult from exc
    return dict(value)


def _resolve_strict_mapping(
    ref: Mapping[str, Any], resolver: Callable[..., Any]
) -> dict[str, Any]:
    exact_ref = _exact_ref(ref)
    try:
        serialized = resolver(exact_ref)
        if not isinstance(serialized, (bytes, bytearray, str)):
            raise _NoAuthoritativeResult
        value = parse_json_strict(serialized)
    except _NoAuthoritativeResult:
        raise
    except Exception as exc:
        raise _NoAuthoritativeResult from exc
    if not isinstance(value, Mapping) or not verify_sealed_object(value):
        raise _NoAuthoritativeResult
    if {
        "object_id": value.get("object_id"),
        "content_sha256": value.get("content_sha256"),
    } != exact_ref:
        raise _NoAuthoritativeResult
    return dict(value)


def _invalid_result(
    contract_ref: Mapping[str, Any],
    invocation_ref: Mapping[str, Any],
    package_ref: Mapping[str, Any],
    reason: str,
) -> dict[str, Any]:
    return build_qualification_validation_result(
        {
            "schema_version": "1.0",
            "qualification_validation_contract_ref": dict(contract_ref),
            "qualification_validation_invocation_ref": dict(invocation_ref),
            "qualification_state_package_ref": dict(package_ref),
            "validation_status": "INVALID",
            "primary_invalid_reason_code": reason,
        }
    )


def _static_dependency_refs(contract: Mapping[str, Any]) -> list[dict[str, str]]:
    refs = [
        contract["validator_contract_ref"],
        contract["roughtime_qualification_verifier_contract_ref"],
        contract["qualification_validation_invocation_schema_ref"],
        contract["dynamic_qualification_state_package_v2_schema_ref"],
        contract["qualification_state_history_snapshot_schema_ref"],
        contract["state_report_schema_ref"],
        contract["qualification_validation_result_schema_ref"],
    ]
    refs.extend(
        entry["schema_ref"]
        for entry in contract["accepted_qualification_input_schema_refs"]
    )
    return [_exact_ref(ref) for ref in refs]


class _DeterministicInvalid(Exception):
    """An authenticated input conclusively fails one frozen stage."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


_QUALIFICATION_VERIFIER_CONTRACT_FIELDS = frozenset(
    {
        "schema_version",
        "object_type",
        "criteria_id",
        "criteria_sha256",
        "validator_contract_ref",
        "decision_signature_projection",
        "signature_algorithm",
        "authority_id",
        "authority_public_key_sha256",
        "ed25519_verifier_build_profile_sha256",
        "ed25519_verifier_binary_sha256",
        "object_id",
        "payload_sha256",
        "content_sha256",
    }
)


class _ConclusiveSignatureVerifier:
    def __init__(self, verifier: PinnedEd25519Verifier) -> None:
        self._verifier = verifier
        self._cache: dict[tuple[bytes, bytes, bytes], bool] = {}

    def __call__(self, public_key: bytes, message: bytes, signature: bytes) -> bool:
        key = (public_key, message, signature)
        if key in self._cache:
            return self._cache[key]
        try:
            result = self._verifier(public_key, message, signature)
        except Exception as exc:
            raise _NoAuthoritativeResult from exc
        if result is not True and result is not False:
            raise _NoAuthoritativeResult
        self._cache[key] = result
        return result


def _prepare_signature_verifier(
    contract: Mapping[str, Any],
    verifier_contract: Mapping[str, Any],
    public_key: bytes | None,
    build_profile: Mapping[str, Any] | None,
    binary: Path | None,
) -> tuple[str, bytes, _ConclusiveSignatureVerifier]:
    if (
        not isinstance(public_key, bytes)
        or len(public_key) != 32
        or build_profile is None
        or binary is None
    ):
        raise _NoAuthoritativeResult
    if (
        set(verifier_contract) != _QUALIFICATION_VERIFIER_CONTRACT_FIELDS
        or verifier_contract.get("schema_version") != "1.0"
        or verifier_contract.get("object_type")
        != "RoughtimeQualificationVerifierContract"
        or not verify_sealed_object(verifier_contract)
        or verifier_contract.get("criteria_id") != CRITERIA_ID
        or verifier_contract.get("criteria_sha256") != CRITERIA_SHA256
        or verifier_contract.get("decision_signature_projection")
        != DECISION_SIGNATURE_PROJECTION
        or verifier_contract.get("signature_algorithm") != "ED25519"
        or verifier_contract.get("validator_contract_ref")
        != contract["validator_contract_ref"]
    ):
        raise _DeterministicInvalid("HISTORY_SNAPSHOT_AUTHENTICATION_INVALID")
    authority_id = verifier_contract.get("authority_id")
    if not isinstance(authority_id, str) or not authority_id:
        raise _DeterministicInvalid("HISTORY_SNAPSHOT_AUTHENTICATION_INVALID")
    if verifier_contract.get("authority_public_key_sha256") != hashlib.sha256(
        public_key
    ).hexdigest():
        raise _DeterministicInvalid("HISTORY_SNAPSHOT_AUTHENTICATION_INVALID")
    try:
        profile_sha256 = validate_ed25519_build_profile(build_profile)
        binary_sha256 = build_profile["binary_sha256"]
        if (
            verifier_contract["ed25519_verifier_build_profile_sha256"]
            != profile_sha256
            or verifier_contract["ed25519_verifier_binary_sha256"]
            != binary_sha256
        ):
            raise _NoAuthoritativeResult
        pinned = PinnedEd25519Verifier(Path(binary), binary_sha256)
    except _NoAuthoritativeResult:
        raise
    except Exception as exc:
        raise _NoAuthoritativeResult from exc
    return authority_id, public_key, _ConclusiveSignatureVerifier(pinned)


def _strict_signature(value: Any) -> bytes:
    if not isinstance(value, str):
        raise _DeterministicInvalid("HISTORY_SNAPSHOT_AUTHENTICATION_INVALID")
    try:
        signature = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise _DeterministicInvalid(
            "HISTORY_SNAPSHOT_AUTHENTICATION_INVALID"
        ) from exc
    if (
        len(signature) != 64
        or base64.b64encode(signature).decode("ascii") != value
    ):
        raise _DeterministicInvalid("HISTORY_SNAPSHOT_AUTHENTICATION_INVALID")
    return signature


def _authenticate_history(
    closure: PackageClosureResult,
    public_key: bytes,
    verifier: _ConclusiveSignatureVerifier,
) -> None:
    for snapshot in closure.ordered_history_snapshot_chain:
        projection = qualification_state_history_snapshot_signed_projection(snapshot)
        if (
            not verify_sealed_object(snapshot)
            or snapshot.get("signed_payload_sha256") != content_hash(projection)
        ):
            raise _DeterministicInvalid(
                "HISTORY_SNAPSHOT_AUTHENTICATION_INVALID"
            )
        signature = _strict_signature(snapshot.get("authority_signature_base64"))
        message = qualification_state_history_snapshot_signature_message(snapshot)
        if verifier(public_key, message, signature) is not True:
            raise _DeterministicInvalid(
                "HISTORY_SNAPSHOT_AUTHENTICATION_INVALID"
            )


def _run_history_structure(closure: PackageClosureResult) -> None:
    for validator in (
        validate_history_cutoff,
        validate_history_succession,
        validate_history_completeness,
    ):
        try:
            validator(closure)
        except QualificationStatePackageError as exc:
            if exc.stage is None:
                raise _NoAuthoritativeResult from exc
            raise _DeterministicInvalid(exc.stage.value) from exc


def _member_for_ref(
    closure: PackageClosureResult, ref: Mapping[str, Any]
) -> Mapping[str, Any]:
    key = (ref["object_id"], ref["content_sha256"])
    try:
        return closure.typed_exact_ref_member_map[key][1]
    except (KeyError, TypeError) as exc:
        raise _NoAuthoritativeResult from exc


def _resolve_evidence_manifest(
    selector: str,
    resolver: Callable[..., Any],
) -> dict[str, Any]:
    try:
        candidate = resolver(selector)
    except Exception as exc:
        raise _NoAuthoritativeResult from exc
    if not isinstance(candidate, (bytes, bytearray)):
        raise _NoAuthoritativeResult
    raw = bytes(candidate)
    if hashlib.sha256(raw).hexdigest() != selector:
        raise _NoAuthoritativeResult
    try:
        manifest = parse_json_strict(raw)
    except (CanonicalizationError, UnicodeDecodeError) as exc:
        raise _DeterministicInvalid(
            "QUALIFICATION_EVIDENCE_PACKAGE_INVALID"
        ) from exc
    if not isinstance(manifest, Mapping):
        raise _DeterministicInvalid("QUALIFICATION_EVIDENCE_PACKAGE_INVALID")
    try:
        if canonical_json(manifest) != raw:
            raise _DeterministicInvalid(
                "QUALIFICATION_EVIDENCE_PACKAGE_INVALID"
            )
    except CanonicalizationError as exc:
        raise _DeterministicInvalid(
            "QUALIFICATION_EVIDENCE_PACKAGE_INVALID"
        ) from exc
    return dict(manifest)

def _resolve_roughtime_build_profile(
    evidence_package_root: Path,
    evidence_manifest_relative_path: str,
    expected_profile_sha256: str,
) -> dict[str, Any]:
    try:
        artifacts = collect_manifest_artifacts(
            evidence_package_root,
            manifest_relative_path=evidence_manifest_relative_path,
        )
    except OSError as exc:
        raise _NoAuthoritativeResult from exc
    except ValueError as exc:
        raise _DeterministicInvalid(
            "QUALIFICATION_EVIDENCE_PACKAGE_INVALID"
        ) from exc

    candidates: dict[bytes, dict[str, Any]] = {}
    for raw in artifacts.values():
        try:
            value = parse_json_strict(raw)
            if not isinstance(value, Mapping):
                continue
            if (
                validate_roughtime_verifier_build_profile(value)
                != expected_profile_sha256
            ):
                continue
            candidate = dict(value)
            candidates[canonical_json(candidate)] = candidate
        except (CanonicalizationError, UnicodeDecodeError, ValueError):
            continue
    if len(candidates) != 1:
        raise _DeterministicInvalid(
            "QUALIFICATION_EVIDENCE_PACKAGE_INVALID"
        )
    return next(iter(candidates.values()))



def _validate_evidence(
    closure: PackageClosureResult,
    manifest: Mapping[str, Any],
    evidence_package_root: Path,
    evidence_manifest_relative_path: str,
    build_profile: Mapping[str, Any],
) -> Mapping[str, Any]:
    decision_selector = closure.qualification_decision["signed_payload"][
        "evidence_manifest_sha256"
    ]
    review_selector = closure.qualification_review["evidence_manifest_sha256"]
    if decision_selector != review_selector:
        raise _DeterministicInvalid("QUALIFICATION_EVIDENCE_PACKAGE_INVALID")
    metadata = _member_for_ref(
        closure, closure.qualification_review["metadata_review_ref"]
    )
    try:
        validate_bound_qualification_review(
            closure.qualification_review,
            profile=closure.provider_profile,
            metadata_review=metadata,
            evidence_manifest=manifest,
            evidence_package_root=evidence_package_root,
            evidence_manifest_relative_path=evidence_manifest_relative_path,
            verifier_build_profile=build_profile,
        )
    except OSError as exc:
        raise _NoAuthoritativeResult from exc
    except ValueError as exc:
        raise _DeterministicInvalid(
            "QUALIFICATION_EVIDENCE_PACKAGE_INVALID"
        ) from exc
    return metadata


def _validate_authority(
    closure: PackageClosureResult,
    manifest: Mapping[str, Any],
    evidence_package_root: Path,
    evidence_manifest_relative_path: str,
    build_profile: Mapping[str, Any],
    authority_id: str,
    public_key: bytes,
    verifier: _ConclusiveSignatureVerifier,
) -> None:
    metadata = _member_for_ref(
        closure,
        closure.qualification_decision["signed_payload"]["metadata_review_ref"],
    )
    try:
        validate_bound_qualification_decision(
            closure.qualification_decision,
            profile=closure.provider_profile,
            review=closure.qualification_review,
            metadata_review=metadata,
            evidence_manifest=manifest,
            evidence_package_root=evidence_package_root,
            evidence_manifest_relative_path=evidence_manifest_relative_path,
            verifier_build_profile=build_profile,
            expected_authority_id=authority_id,
            expected_authority_public_key=public_key,
            signature_verifier=verifier,
        )
    except _NoAuthoritativeResult:
        raise
    except OSError as exc:
        raise _NoAuthoritativeResult from exc
    except ValueError as exc:
        raise _DeterministicInvalid(
            "QUALIFICATION_AUTHORITY_CHAIN_INVALID"
        ) from exc


def _derive_state_report(
    closure: PackageClosureResult,
    manifest: Mapping[str, Any],
    evidence_package_root: Path,
    evidence_manifest_relative_path: str,
    build_profile: Mapping[str, Any],
    authority_id: str,
    public_key: bytes,
    verifier: _ConclusiveSignatureVerifier,
) -> dict[str, Any]:
    try:
        return derive_authoritative_qualification_state(
            provider_id=str(closure.provider_profile["provider_id"]),
            as_of_utc=closure.as_of_utc,
            rehearsal_verified=True,
            profile=closure.provider_profile,
            evidence_manifest=manifest,
            evidence_package_root=evidence_package_root,
            evidence_manifest_relative_path=evidence_manifest_relative_path,
            verifier_build_profile=build_profile,
            review=closure.qualification_review,
            decision=closure.qualification_decision,
            metadata_reviews=closure.metadata_reviews,
            requalification_events=closure.requalification_events,
            expected_authority_id=authority_id,
            expected_authority_public_key=public_key,
            signature_verifier=verifier,
        )
    except _NoAuthoritativeResult:
        raise
    except OSError as exc:
        raise _NoAuthoritativeResult from exc
    except ValueError as exc:
        raise _DeterministicInvalid(
            "QUALIFICATION_STATE_DERIVATION_INVALID"
        ) from exc
    except Exception as exc:
        raise _NoAuthoritativeResult from exc


def _valid_result(
    contract_ref: Mapping[str, Any],
    invocation_ref: Mapping[str, Any],
    closure: PackageClosureResult,
    recomputed_report: Mapping[str, Any],
) -> dict[str, Any]:
    semantic_projection = {
        key: value
        for key, value in recomputed_report.items()
        if key != "report_sha256"
    }
    return build_qualification_validation_result(
        {
            "schema_version": "1.0",
            "qualification_validation_contract_ref": dict(contract_ref),
            "qualification_validation_invocation_ref": dict(invocation_ref),
            "qualification_state_package_ref": dict(closure.package_ref),
            "validation_status": "VALID",
            "provider_profile_ref": dict(closure.provider_profile_ref),
            "qualification_decision_ref": dict(
                closure.qualification_decision_ref
            ),
            "qualification_state_history_snapshot_ref": dict(
                closure.selected_history_snapshot_ref
            ),
            "as_of_utc": closure.as_of_utc,
            "qualification_state": recomputed_report["state"],
            "derived_state_report_semantic_sha256": content_hash(
                semantic_projection
            ),
        }
    )


def execute_qualification_validation(
    expected_qualification_validation_contract_ref: Mapping[str, Any] | None,
    qualification_validation_invocation_ref: Mapping[str, Any],
    package_root: Path,
    evidence_package_root: Path,
    *,
    resolve_static_object: Callable[..., Any],
    resolve_invocation: Callable[..., Any],
    resolve_package: Callable[..., Any],
    resolve_evidence_manifest: Callable[..., Any],
    qualification_authority_public_key: bytes | None,
    qualification_ed25519_build_profile: Mapping[str, Any] | None,
    qualification_ed25519_binary: Path | None,
    evidence_manifest_relative_path: str = "manifest.json",
) -> dict[str, Any] | None:
    """Execute the frozen qualification-validation pipeline."""
    try:
        contract_ref = _exact_ref(expected_qualification_validation_contract_ref)
        contract = _resolve_strict_mapping(contract_ref, resolve_static_object)
        try:
            if validate_qualification_validation_contract(contract) != contract_ref:
                raise _NoAuthoritativeResult
        except Exception as exc:
            raise _NoAuthoritativeResult from exc

        static_objects: dict[tuple[str, str], dict[str, Any]] = {}
        for dependency_ref in _static_dependency_refs(contract):
            dependency = _resolve_strict_mapping(
                dependency_ref, resolve_static_object
            )
            key = (dependency_ref["object_id"], dependency_ref["content_sha256"])
            static_objects[key] = dependency

        invocation_ref = _exact_ref(qualification_validation_invocation_ref)
        invocation = _resolve_strict_mapping(invocation_ref, resolve_invocation)
        try:
            if validate_qualification_validation_invocation(invocation) != invocation_ref:
                raise _NoAuthoritativeResult
        except Exception as exc:
            raise _NoAuthoritativeResult from exc
        if invocation["qualification_validation_contract_ref"] != contract_ref:
            raise _NoAuthoritativeResult

        package_ref = _exact_ref(invocation["qualification_state_package_ref"])
        try:
            package_bytes = resolve_package(package_ref)
        except Exception as exc:
            raise _NoAuthoritativeResult from exc
        if not isinstance(package_bytes, (bytes, bytearray)):
            raise _NoAuthoritativeResult
        package_bytes = bytes(package_bytes)
        if hashlib.sha256(package_bytes).hexdigest() != invocation[
            "qualification_state_package_serialized_sha256"
        ]:
            raise _NoAuthoritativeResult
        try:
            parsed_package = parse_json_strict(package_bytes)
        except (CanonicalizationError, UnicodeDecodeError):
            return _invalid_result(
                contract_ref,
                invocation_ref,
                package_ref,
                "PACKAGE_STRICT_JSON_INVALID",
            )
        try:
            closure = build_package_closure(
                package_ref,
                package_root,
                parsed_package=parsed_package,
            )
        except QualificationStatePackageError as exc:
            if exc.stage in {
                QualificationStatePackageStage.PACKAGE_SCHEMA_INVALID,
                QualificationStatePackageStage.PACKAGE_SEALED_IDENTITY_OR_REFERENCE_INVALID,
                QualificationStatePackageStage.PACKAGE_MEMBER_MANIFEST_INVALID,
                QualificationStatePackageStage.PACKAGE_MEMBER_CLOSURE_INVALID,
                QualificationStatePackageStage.QUALIFICATION_INPUT_SCHEMA_INVALID,
                QualificationStatePackageStage.STATE_REPORT_MEMBER_INVALID,
            }:
                return _invalid_result(
                    contract_ref, invocation_ref, package_ref, exc.stage.value
                )
            raise _NoAuthoritativeResult from exc
        verifier_ref = contract[
            "roughtime_qualification_verifier_contract_ref"
        ]
        verifier_contract = static_objects[
            (verifier_ref["object_id"], verifier_ref["content_sha256"])
        ]
        authority_id, public_key, signature_verifier = (
            _prepare_signature_verifier(
                contract,
                verifier_contract,
                qualification_authority_public_key,
                qualification_ed25519_build_profile,
                qualification_ed25519_binary,
            )
        )
        _authenticate_history(closure, public_key, signature_verifier)
        _run_history_structure(closure)

        evidence_selector = closure.qualification_decision["signed_payload"][
            "evidence_manifest_sha256"
        ]
        if (
            evidence_selector
            != closure.qualification_review["evidence_manifest_sha256"]
        ):
            raise _DeterministicInvalid(
                "QUALIFICATION_EVIDENCE_PACKAGE_INVALID"
            )
        evidence_manifest = _resolve_evidence_manifest(
            evidence_selector, resolve_evidence_manifest
        )
        build_profile = _resolve_roughtime_build_profile(
            evidence_package_root,
            evidence_manifest_relative_path,
            closure.qualification_review["verifier_build_profile_sha256"],
        )

        _validate_evidence(
            closure,
            evidence_manifest,
            evidence_package_root,
            evidence_manifest_relative_path,
            build_profile,
        )
        _validate_authority(
            closure,
            evidence_manifest,
            evidence_package_root,
            evidence_manifest_relative_path,
            build_profile,
            authority_id,
            public_key,
            signature_verifier,
        )
        recomputed_report = _derive_state_report(
            closure,
            evidence_manifest,
            evidence_package_root,
            evidence_manifest_relative_path,
            build_profile,
            authority_id,
            public_key,
            signature_verifier,
        )
        if dict(closure.state_report) != recomputed_report:
            raise _DeterministicInvalid("STATE_REPORT_SEMANTIC_MISMATCH")
        return _valid_result(
            contract_ref,
            invocation_ref,
            closure,
            recomputed_report,
        )
    except _DeterministicInvalid as exc:
        return _invalid_result(
            contract_ref, invocation_ref, package_ref, exc.reason
        )
    except _NoAuthoritativeResult:
        return None
    except Exception:
        return None
