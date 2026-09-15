from __future__ import annotations

import base64
import binascii
import hashlib
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping, Sequence

from .canonical import (
    canonical_json,
    content_hash,
    require_ascii_token,
    require_utc_timestamp,
    verify_sealed_object,
)
from ._roughtime_profile import (
    NONCE_PROFILE,
    PACKET_PROFILE,
    PROVIDER_BY_ID,
    TRANSPORT_PROFILE,
    VERIFIER_COMMIT,
    VERIFIER_REPOSITORY,
    VERIFIER_TAG,
)

CRITERIA_ID = "FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1"
CRITERIA_SHA256 = "88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e"

PROFILE_SCHEMA_VERSION = "1.0"
PROFILE_OBJECT_TYPE = "RoughtimeProductionProviderProfile"
MANIFEST_SCHEMA_VERSION = "1.0"
MANIFEST_OBJECT_TYPE = "RoughtimeQualificationEvidenceManifest"
REVIEW_SCHEMA_VERSION = "1.0"
REVIEW_OBJECT_TYPE = "RoughtimeQualificationReview"
METADATA_SCHEMA_VERSION = "1.0"
METADATA_OBJECT_TYPE = "RoughtimeProviderMetadataReview"
REQUALIFICATION_SCHEMA_VERSION = "1.0"
REQUALIFICATION_OBJECT_TYPE = "RoughtimeRequalificationEvent"
DECISION_SCHEMA_VERSION = "1.0"
DECISION_OBJECT_TYPE = "RoughtimeQualificationDecision"
STATE_SCHEMA_VERSION = "1.0"
STATE_OBJECT_TYPE = "RoughtimeQualificationStateReport"

DECISION_SIGNATURE_PROJECTION = "FPP_ROUGHTIME_QUALIFICATION_DECISION_V1"
DECISION_SIGNATURE_DOMAIN = b"FPP_ROUGHTIME_QUALIFICATION_DECISION_V1\x00"
METADATA_REVIEW_INTERVAL_DAYS = 90

SignatureVerifier = Callable[[bytes, bytes, bytes], bool]

HEX64_RE = __import__("re").compile(r"^[0-9a-f]{64}$")

PROFILE_KEYS = frozenset({
    "schema_version", "object_type", "criteria_id", "criteria_sha256", "provider_id",
    "operator_identity", "host", "port", "transport", "operator_declared_protocol",
    "wire_version_hex", "offered_version_hex", "wire_profile", "require_type",
    "require_srv", "root_public_key_base64", "packet_profile", "transport_profile",
    "nonce_profile", "verifier_repository", "verifier_tag", "verifier_commit",
    "verifier_build_profile_sha256", "service_classification", "no_fallback",
    "object_id", "payload_sha256", "content_sha256",
})
MANIFEST_KEYS = frozenset({
    "schema_version", "object_type", "criteria_id", "criteria_sha256",
    "provider_id", "entries",
})
MANIFEST_ENTRY_REQUIRED_KEYS = frozenset({
    "relative_path", "size", "sha256", "artifact_type", "required",
})
MANIFEST_ENTRY_OPTIONAL_KEYS = frozenset({"provider_id", "attempt_number"})
REVIEW_KEYS = frozenset({
    "schema_version", "object_type", "criteria_id", "criteria_sha256", "provider_id",
    "provider_profile_ref", "evidence_manifest_sha256", "execution_report_sha256",
    "verifier_build_profile_sha256", "verifier_binary_sha256", "metadata_review_ref",
    "executor_id", "reviewer_id", "review_basis_sha256", "criteria_checks",
    "evidence_complete", "deterministic_validation_passed", "strict_replay_passed",
    "blocking_findings", "review_result", "reviewed_at",
    "object_id", "payload_sha256", "content_sha256",
})
REVIEW_CHECK_KEYS = frozenset({
    "criterion_id", "disposition", "evidence_sha256s", "reason_codes",
})
METADATA_KEYS = frozenset({
    "schema_version", "object_type", "provider_id", "provider_profile_ref",
    "reviewed_at", "source_captures", "operator_identity_status", "service_status",
    "endpoint_status", "root_key_status", "protocol_status", "use_permission_status",
    "lifecycle_status", "rotation_notice_status", "change_disposition", "reason_codes",
    "object_id", "payload_sha256", "content_sha256",
})
SOURCE_CAPTURE_KEYS = frozenset({
    "source_id", "evidence_locator", "retrieved_at", "capture_sha256",
})
REQUALIFICATION_KEYS = frozenset({
    "schema_version", "object_type", "provider_id", "provider_profile_ref",
    "trigger_code", "detected_at", "evidence_sha256s", "reason_codes",
    "object_id", "payload_sha256", "content_sha256",
})
DECISION_KEYS = frozenset({
    "schema_version", "object_type", "signature_projection", "signed_payload",
    "signed_payload_sha256", "signature_algorithm", "authority_signature_base64",
    "object_id", "payload_sha256", "content_sha256",
})
SIGNED_PAYLOAD_KEYS = frozenset({
    "criteria_id", "criteria_sha256", "provider_id", "provider_profile_ref",
    "evidence_manifest_sha256", "verifier_build_profile_sha256",
    "verifier_binary_sha256", "independent_review_ref", "metadata_review_ref",
    "decision_result", "decision_timestamp", "authority_id",
    "authority_public_key_sha256",
})
STATE_REQUIRED_KEYS = frozenset({
    "schema_version", "object_type", "provider_id", "as_of_utc", "state",
    "reason_codes", "active_requalification_event_refs", "report_sha256",
})
STATE_OPTIONAL_KEYS = frozenset({
    "decision_ref", "review_ref", "latest_metadata_review_ref",
})

REVIEW_CRITERIA = (
    "CRYPTOGRAPHIC",
    "PROTOCOL_STABILITY",
    "PRODUCTION_USE_PERMISSION",
    "LIVE_REPEATABILITY",
    "PILOT_EXPERIMENTAL",
    "OPERATIONAL",
    "INDEPENDENCE",
    "COMMON_DEPENDENCY",
    "PROVENANCE",
    "EVIDENCE_MANIFEST",
    "FRESHNESS",
    "FAILURE_PATH",
    "MERKLE_COVERAGE",
    "STANDARDS_TRANSITION",
    "SCHEMA_VALIDATOR_REGRESSION",
)
REVIEW_CRITERIA_SET = frozenset(REVIEW_CRITERIA)

REQUALIFICATION_TRIGGER_CODES = frozenset({
    "ROOT_ENDPOINT_PORT_TRANSPORT_CHANGE",
    "WIRE_TYPE_SRV_MERKLE_CHANGE",
    "CONTROL_DOMAIN_CHANGE",
    "STANDARDS_MIGRATION",
    "VERIFIER_CORRECTNESS_BUG",
    "REQUEST_BUILDER_CHANGE",
    "QUALIFICATION_VALIDATOR_OR_SCHEMA_CHANGE",
    "EVIDENCE_CORRUPTION",
    "PRODUCTION_USE_AUTHORIZATION_WITHDRAWN",
    "SERVICE_RETIRED",
    "BLOCKING_COMMON_DEPENDENCY",
})

QUALIFICATION_STATES = frozenset({
    "UNREVIEWED",
    "REHEARSAL_VERIFIED",
    "QUALIFICATION_REVIEW_READY",
    "QUALIFICATION_BLOCKED",
    "PRODUCTION_QUALIFIED",
    "QUALIFICATION_EXPIRED",
    "REQUALIFICATION_REQUIRED",
})


def _exact_keys(value: Mapping[str, Any], expected: frozenset[str], name: str) -> None:
    actual = frozenset(value)
    if actual != expected:
        raise ValueError(
            f"{name} keys invalid; missing={sorted(expected - actual)} "
            f"extra={sorted(actual - expected)}"
        )


def _keys_with_optional(
    value: Mapping[str, Any],
    required: frozenset[str],
    optional: frozenset[str],
    name: str,
) -> None:
    actual = frozenset(value)
    missing = required - actual
    extra = actual - required - optional
    if missing or extra:
        raise ValueError(
            f"{name} keys invalid; missing={sorted(missing)} extra={sorted(extra)}"
        )


def _hex64(value: Any, name: str) -> str:
    if not isinstance(value, str) or HEX64_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be 64 lowercase hex characters")
    return value


def _nonempty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")
    return value


def _ref(value: Any, name: str) -> dict[str, str]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name} must be an object reference")
    if set(value) != {"object_id", "content_sha256"}:
        raise ValueError(f"{name} must contain object_id and content_sha256 only")
    object_id = value["object_id"]
    require_ascii_token(object_id, f"{name}.object_id")
    return {
        "object_id": object_id,
        "content_sha256": _hex64(value["content_sha256"], f"{name}.content_sha256"),
    }


def object_ref(obj: Mapping[str, Any]) -> dict[str, str]:
    if not verify_sealed_object(obj):
        raise ValueError("cannot reference object with invalid seal")
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def _dt(value: Any, name: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a canonical UTC timestamp")
    require_utc_timestamp(value)
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _sorted_unique_strings(
    values: Any,
    name: str,
    *,
    tokens: bool = False,
    digests: bool = False,
) -> list[str]:
    if not isinstance(values, list):
        raise ValueError(f"{name} must be an array")
    normalized: list[str] = []
    for index, value in enumerate(values):
        if not isinstance(value, str):
            raise ValueError(f"{name}[{index}] must be a string")
        if tokens:
            require_ascii_token(value, f"{name}[{index}]")
        if digests:
            _hex64(value, f"{name}[{index}]")
        normalized.append(value)
    if normalized != sorted(normalized) or len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must be unique and sorted")
    return normalized


def _strict_b64(value: Any, name: str, expected_len: int) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be nonempty base64")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(f"{name} must be strict base64") from exc
    if len(decoded) != expected_len:
        raise ValueError(f"{name} must decode to {expected_len} bytes")
    if base64.b64encode(decoded).decode("ascii") != value:
        raise ValueError(f"{name} must use canonical base64")
    return decoded


def _provider_expected(provider_id: str) -> Mapping[str, Any]:
    provider = PROVIDER_BY_ID.get(provider_id)
    if provider is None:
        raise ValueError("provider_id is outside the frozen provider pool")
    return {
        "provider_id": provider.provider_id,
        "operator_identity": provider.operator_identity,
        "host": provider.host,
        "port": provider.port,
        "transport": provider.transport,
        "operator_declared_protocol": provider.operator_declared_protocol,
        "wire_version_hex": provider.wire_version_hex,
        "offered_version_hex": provider.offered_version_hex,
        "wire_profile": provider.wire_profile,
        "require_type": provider.require_type,
        "require_srv": provider.require_srv,
        "root_public_key_base64": provider.root_public_key_base64,
    }


def validate_production_provider_profile(profile: Mapping[str, Any]) -> str:
    if not isinstance(profile, Mapping):
        raise ValueError("provider profile must be an object")
    _exact_keys(profile, PROFILE_KEYS, "provider profile")
    if not verify_sealed_object(profile):
        raise ValueError("provider profile seal invalid")
    if profile["schema_version"] != PROFILE_SCHEMA_VERSION:
        raise ValueError("provider profile schema_version mismatch")
    if profile["object_type"] != PROFILE_OBJECT_TYPE:
        raise ValueError("provider profile object_type mismatch")
    if profile["criteria_id"] != CRITERIA_ID or profile["criteria_sha256"] != CRITERIA_SHA256:
        raise ValueError("provider profile criteria binding mismatch")

    expected = _provider_expected(profile["provider_id"])
    for field, expected_value in expected.items():
        if profile[field] != expected_value:
            raise ValueError(f"provider profile {field} mismatch for frozen provider")

    if profile["packet_profile"] != PACKET_PROFILE:
        raise ValueError("provider profile packet_profile mismatch")
    if profile["transport_profile"] != TRANSPORT_PROFILE:
        raise ValueError("provider profile transport_profile mismatch")
    if profile["nonce_profile"] != NONCE_PROFILE:
        raise ValueError("provider profile nonce_profile mismatch")
    if profile["verifier_repository"] != VERIFIER_REPOSITORY:
        raise ValueError("provider profile verifier_repository mismatch")
    if profile["verifier_tag"] != VERIFIER_TAG:
        raise ValueError("provider profile verifier_tag mismatch")
    if profile["verifier_commit"] != VERIFIER_COMMIT:
        raise ValueError("provider profile verifier_commit mismatch")
    _hex64(profile["verifier_build_profile_sha256"], "verifier_build_profile_sha256")
    if profile["no_fallback"] is not True:
        raise ValueError("provider profile must prohibit fallback")

    expected_class = (
        "PILOT_EXPERIMENTAL"
        if profile["provider_id"] == "TimeNL-Roughtime"
        else "STANDARD_PUBLIC_SERVICE"
    )
    if profile["service_classification"] != expected_class:
        raise ValueError("provider profile service_classification mismatch")
    return profile["content_sha256"]


def canonical_manifest_relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or not value.isascii():
        raise ValueError("relative_path must be nonempty ASCII")
    if "\\" in value or value.startswith("/") or value.endswith("/") or "//" in value:
        raise ValueError("relative_path must be canonical POSIX relative path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("relative_path traversal or ambiguity prohibited")
    if path.as_posix() != value:
        raise ValueError("relative_path is not canonical")
    return value


def validate_qualification_evidence_manifest(
    manifest: Mapping[str, Any],
    *,
    artifact_bytes: Mapping[str, bytes] | None = None,
) -> str:
    if not isinstance(manifest, Mapping):
        raise ValueError("evidence manifest must be an object")
    _exact_keys(manifest, MANIFEST_KEYS, "evidence manifest")
    if manifest["schema_version"] != MANIFEST_SCHEMA_VERSION:
        raise ValueError("evidence manifest schema_version mismatch")
    if manifest["object_type"] != MANIFEST_OBJECT_TYPE:
        raise ValueError("evidence manifest object_type mismatch")
    if manifest["criteria_id"] != CRITERIA_ID or manifest["criteria_sha256"] != CRITERIA_SHA256:
        raise ValueError("evidence manifest criteria binding mismatch")
    _provider_expected(manifest["provider_id"])

    entries = manifest["entries"]
    if not isinstance(entries, list) or not entries:
        raise ValueError("evidence manifest entries must be a nonempty array")
    paths: list[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, Mapping):
            raise ValueError(f"entries[{index}] must be an object")
        _keys_with_optional(
            entry,
            MANIFEST_ENTRY_REQUIRED_KEYS,
            MANIFEST_ENTRY_OPTIONAL_KEYS,
            f"entries[{index}]",
        )
        relative_path = canonical_manifest_relative_path(entry["relative_path"])
        paths.append(relative_path)
        size = entry["size"]
        if not isinstance(size, int) or isinstance(size, bool) or size < 0 or size > 2**53 - 1:
            raise ValueError(f"entries[{index}].size invalid")
        _hex64(entry["sha256"], f"entries[{index}].sha256")
        require_ascii_token(entry["artifact_type"], f"entries[{index}].artifact_type")
        if not isinstance(entry["required"], bool):
            raise ValueError(f"entries[{index}].required must be boolean")
        if "provider_id" in entry and entry["provider_id"] != manifest["provider_id"]:
            raise ValueError(f"entries[{index}].provider_id mismatch")
        if "attempt_number" in entry:
            if "provider_id" not in entry:
                raise ValueError(f"entries[{index}] attempt_number requires provider_id")
            attempt_number = entry["attempt_number"]
            if (
                not isinstance(attempt_number, int)
                or isinstance(attempt_number, bool)
                or attempt_number not in {1, 2}
            ):
                raise ValueError(f"entries[{index}].attempt_number invalid")
    if paths != sorted(paths) or len(set(paths)) != len(paths):
        raise ValueError("manifest relative_path values must be unique and sorted")

    if artifact_bytes is not None:
        actual_paths = sorted(artifact_bytes)
        for path in actual_paths:
            canonical_manifest_relative_path(path)
            data = artifact_bytes[path]
            if not isinstance(data, bytes):
                raise ValueError(f"artifact_bytes[{path!r}] must be bytes")
        if actual_paths != paths:
            missing = sorted(set(paths) - set(actual_paths))
            unexpected = sorted(set(actual_paths) - set(paths))
            raise ValueError(
                f"manifest artifact closure mismatch; missing={missing} unexpected={unexpected}"
            )
        for entry in entries:
            data = artifact_bytes[entry["relative_path"]]
            if len(data) != entry["size"]:
                raise ValueError(f"artifact size mismatch: {entry['relative_path']}")
            if hashlib.sha256(data).hexdigest() != entry["sha256"]:
                raise ValueError(f"artifact SHA256 mismatch: {entry['relative_path']}")

    canonical_json(manifest)
    return hashlib.sha256(canonical_json(manifest)).hexdigest()


def collect_manifest_artifacts(
    package_root: Path,
    *,
    manifest_relative_path: str,
) -> dict[str, bytes]:
    root = package_root.resolve()
    if not root.is_dir():
        raise ValueError("qualification package root must be a directory")
    manifest_relative_path = canonical_manifest_relative_path(manifest_relative_path)
    artifacts: dict[str, bytes] = {}
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if stat.S_ISLNK(mode):
            raise ValueError(f"symlink prohibited in qualification package: {relative}")
        if not stat.S_ISREG(mode):
            raise ValueError(f"special file prohibited in qualification package: {relative}")
        canonical_manifest_relative_path(relative)
        if relative == manifest_relative_path:
            continue
        artifacts[relative] = path.read_bytes()
    return artifacts


def validate_provider_metadata_review(
    review: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
) -> str:
    if not isinstance(review, Mapping):
        raise ValueError("metadata review must be an object")
    _exact_keys(review, METADATA_KEYS, "metadata review")
    if not verify_sealed_object(review):
        raise ValueError("metadata review seal invalid")
    if review["schema_version"] != METADATA_SCHEMA_VERSION or review["object_type"] != METADATA_OBJECT_TYPE:
        raise ValueError("metadata review schema identity mismatch")
    validate_production_provider_profile(profile)
    if review["provider_id"] != profile["provider_id"]:
        raise ValueError("metadata review provider mismatch")
    if _ref(review["provider_profile_ref"], "provider_profile_ref") != object_ref(profile):
        raise ValueError("metadata review profile binding mismatch")
    _dt(review["reviewed_at"], "reviewed_at")

    captures = review["source_captures"]
    if not isinstance(captures, list) or not captures:
        raise ValueError("metadata review source_captures must be nonempty")
    ordering: list[tuple[str, str, str]] = []
    for index, capture in enumerate(captures):
        if not isinstance(capture, Mapping):
            raise ValueError(f"source_captures[{index}] must be an object")
        _exact_keys(capture, SOURCE_CAPTURE_KEYS, f"source_captures[{index}]")
        require_ascii_token(capture["source_id"], f"source_captures[{index}].source_id")
        _nonempty_string(capture["evidence_locator"], f"source_captures[{index}].evidence_locator")
        _dt(capture["retrieved_at"], f"source_captures[{index}].retrieved_at")
        _hex64(capture["capture_sha256"], f"source_captures[{index}].capture_sha256")
        ordering.append((capture["source_id"], capture["retrieved_at"], capture["capture_sha256"]))
    if ordering != sorted(ordering) or len(set(ordering)) != len(ordering):
        raise ValueError("metadata source captures must be unique and sorted")

    allowed = {
        "operator_identity_status": {"UNCHANGED", "CHANGED", "UNKNOWN"},
        "service_status": {"ACTIVE", "INACTIVE", "RETIRED", "UNKNOWN"},
        "endpoint_status": {"UNCHANGED", "CHANGED", "UNKNOWN"},
        "root_key_status": {"UNCHANGED", "CHANGED", "UNKNOWN"},
        "protocol_status": {"UNCHANGED", "CHANGED", "TRANSITION_ANNOUNCED", "UNKNOWN"},
        "use_permission_status": {"AFFIRMATIVE", "WITHDRAWN", "CONFLICTING", "UNKNOWN"},
        "lifecycle_status": {"STANDARD", "PILOT_EXPERIMENTAL", "DEPRECATED", "RETIRED", "UNKNOWN"},
        "rotation_notice_status": {"NONE_PUBLISHED", "PUBLISHED_CHANGE", "UNKNOWN"},
        "change_disposition": {"UNCHANGED", "QUALIFICATION_RELEVANT_CHANGE", "BLOCKING_UNKNOWN"},
    }
    for field, values in allowed.items():
        if review[field] not in values:
            raise ValueError(f"metadata review {field} invalid")
    _sorted_unique_strings(review["reason_codes"], "reason_codes", tokens=True)

    expected_lifecycle = (
        "PILOT_EXPERIMENTAL"
        if profile["service_classification"] == "PILOT_EXPERIMENTAL"
        else "STANDARD"
    )
    clean = (
        review["operator_identity_status"] == "UNCHANGED"
        and review["service_status"] == "ACTIVE"
        and review["endpoint_status"] == "UNCHANGED"
        and review["root_key_status"] == "UNCHANGED"
        and review["protocol_status"] == "UNCHANGED"
        and review["use_permission_status"] == "AFFIRMATIVE"
        and review["lifecycle_status"] == expected_lifecycle
        and review["rotation_notice_status"] in {"NONE_PUBLISHED", "UNKNOWN"}
    )
    if review["change_disposition"] == "UNCHANGED" and not clean:
        raise ValueError("UNCHANGED metadata disposition conflicts with reviewed metadata")
    if clean and review["change_disposition"] != "UNCHANGED":
        raise ValueError("clean metadata review must use UNCHANGED disposition")
    return review["content_sha256"]


def validate_qualification_review(
    review: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    metadata_review: Mapping[str, Any],
    evidence_manifest_sha256: str,
) -> str:
    if not isinstance(review, Mapping):
        raise ValueError("qualification review must be an object")
    _exact_keys(review, REVIEW_KEYS, "qualification review")
    if not verify_sealed_object(review):
        raise ValueError("qualification review seal invalid")
    if review["schema_version"] != REVIEW_SCHEMA_VERSION or review["object_type"] != REVIEW_OBJECT_TYPE:
        raise ValueError("qualification review schema identity mismatch")
    if review["criteria_id"] != CRITERIA_ID or review["criteria_sha256"] != CRITERIA_SHA256:
        raise ValueError("qualification review criteria binding mismatch")
    validate_production_provider_profile(profile)
    validate_provider_metadata_review(metadata_review, profile=profile)
    if review["provider_id"] != profile["provider_id"]:
        raise ValueError("qualification review provider mismatch")
    if _ref(review["provider_profile_ref"], "provider_profile_ref") != object_ref(profile):
        raise ValueError("qualification review profile binding mismatch")
    if _ref(review["metadata_review_ref"], "metadata_review_ref") != object_ref(metadata_review):
        raise ValueError("qualification review metadata binding mismatch")
    if review["evidence_manifest_sha256"] != _hex64(evidence_manifest_sha256, "evidence_manifest_sha256"):
        raise ValueError("qualification review manifest binding mismatch")
    _hex64(review["execution_report_sha256"], "execution_report_sha256")
    _hex64(review["verifier_build_profile_sha256"], "verifier_build_profile_sha256")
    _hex64(review["verifier_binary_sha256"], "verifier_binary_sha256")
    if review["verifier_build_profile_sha256"] != profile["verifier_build_profile_sha256"]:
        raise ValueError("qualification review verifier build/profile mismatch")
    _nonempty_string(review["executor_id"], "executor_id")
    _nonempty_string(review["reviewer_id"], "reviewer_id")
    _hex64(review["review_basis_sha256"], "review_basis_sha256")
    reviewed_at = _dt(review["reviewed_at"], "reviewed_at")
    if reviewed_at < _dt(metadata_review["reviewed_at"], "metadata_review.reviewed_at"):
        raise ValueError("qualification review predates its metadata review")

    checks = review["criteria_checks"]
    if not isinstance(checks, list):
        raise ValueError("criteria_checks must be an array")
    criterion_ids: list[str] = []
    dispositions: dict[str, str] = {}
    for index, check in enumerate(checks):
        if not isinstance(check, Mapping):
            raise ValueError(f"criteria_checks[{index}] must be an object")
        _exact_keys(check, REVIEW_CHECK_KEYS, f"criteria_checks[{index}]")
        criterion_id = require_ascii_token(check["criterion_id"], f"criteria_checks[{index}].criterion_id")
        if check["disposition"] not in {"PASS", "FAIL", "NOT_APPLICABLE"}:
            raise ValueError(f"criteria_checks[{index}].disposition invalid")
        evidence_sha256s = _sorted_unique_strings(
            check["evidence_sha256s"],
            f"criteria_checks[{index}].evidence_sha256s",
            digests=True,
        )
        if check["disposition"] != "NOT_APPLICABLE" and not evidence_sha256s:
            raise ValueError(f"criteria_checks[{index}] requires retained evidence")
        _sorted_unique_strings(check["reason_codes"], f"criteria_checks[{index}].reason_codes", tokens=True)
        criterion_ids.append(criterion_id)
        dispositions[criterion_id] = check["disposition"]
    if criterion_ids != sorted(criterion_ids) or len(set(criterion_ids)) != len(criterion_ids):
        raise ValueError("criteria_checks must be unique and sorted by criterion_id")
    if frozenset(criterion_ids) != REVIEW_CRITERIA_SET:
        raise ValueError("criteria_checks do not cover the complete frozen review matrix")

    for field in ("evidence_complete", "deterministic_validation_passed", "strict_replay_passed"):
        if not isinstance(review[field], bool):
            raise ValueError(f"{field} must be boolean")
    _sorted_unique_strings(review["blocking_findings"], "blocking_findings", tokens=True)
    if review["review_result"] not in {"PASS", "BLOCK"}:
        raise ValueError("review_result invalid")

    if profile["service_classification"] == "PILOT_EXPERIMENTAL":
        if dispositions["PILOT_EXPERIMENTAL"] != "PASS":
            raise ValueError("pilot provider requires PASS for PILOT_EXPERIMENTAL criterion")
    elif dispositions["PILOT_EXPERIMENTAL"] not in {"PASS", "NOT_APPLICABLE"}:
        raise ValueError("standard provider pilot criterion may only PASS or be NOT_APPLICABLE")

    pass_conditions = (
        review["evidence_complete"] is True
        and review["deterministic_validation_passed"] is True
        and review["strict_replay_passed"] is True
        and not review["blocking_findings"]
        and all(value in {"PASS", "NOT_APPLICABLE"} for value in dispositions.values())
    )
    if review["review_result"] == "PASS" and not pass_conditions:
        raise ValueError("PASS review has blocking or failed criteria")
    if pass_conditions and review["review_result"] != "PASS":
        raise ValueError("fully passing review must use PASS result")
    return review["content_sha256"]


def validate_requalification_event(
    event: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
) -> str:
    if not isinstance(event, Mapping):
        raise ValueError("requalification event must be an object")
    _exact_keys(event, REQUALIFICATION_KEYS, "requalification event")
    if not verify_sealed_object(event):
        raise ValueError("requalification event seal invalid")
    if (
        event["schema_version"] != REQUALIFICATION_SCHEMA_VERSION
        or event["object_type"] != REQUALIFICATION_OBJECT_TYPE
    ):
        raise ValueError("requalification event schema identity mismatch")
    validate_production_provider_profile(profile)
    if event["provider_id"] != profile["provider_id"]:
        raise ValueError("requalification event provider mismatch")
    if _ref(event["provider_profile_ref"], "provider_profile_ref") != object_ref(profile):
        raise ValueError("requalification event profile binding mismatch")
    if event["trigger_code"] not in REQUALIFICATION_TRIGGER_CODES:
        raise ValueError("requalification event trigger_code invalid")
    _dt(event["detected_at"], "detected_at")
    evidence = _sorted_unique_strings(event["evidence_sha256s"], "evidence_sha256s", digests=True)
    if not evidence:
        raise ValueError("requalification event must retain evidence")
    _sorted_unique_strings(event["reason_codes"], "reason_codes", tokens=True)
    return event["content_sha256"]


def qualification_decision_signing_bytes(signed_payload: Mapping[str, Any]) -> bytes:
    if not isinstance(signed_payload, Mapping):
        raise ValueError("signed payload must be an object")
    _exact_keys(signed_payload, SIGNED_PAYLOAD_KEYS, "signed payload")
    if signed_payload["criteria_id"] != CRITERIA_ID or signed_payload["criteria_sha256"] != CRITERIA_SHA256:
        raise ValueError("signed payload criteria binding mismatch")
    _provider_expected(signed_payload["provider_id"])
    _ref(signed_payload["provider_profile_ref"], "provider_profile_ref")
    _hex64(signed_payload["evidence_manifest_sha256"], "evidence_manifest_sha256")
    _hex64(signed_payload["verifier_build_profile_sha256"], "verifier_build_profile_sha256")
    _hex64(signed_payload["verifier_binary_sha256"], "verifier_binary_sha256")
    _ref(signed_payload["independent_review_ref"], "independent_review_ref")
    _ref(signed_payload["metadata_review_ref"], "metadata_review_ref")
    if signed_payload["decision_result"] not in {"PRODUCTION_QUALIFIED", "QUALIFICATION_BLOCKED"}:
        raise ValueError("signed payload decision_result invalid")
    _dt(signed_payload["decision_timestamp"], "decision_timestamp")
    require_ascii_token(signed_payload["authority_id"], "authority_id")
    _hex64(signed_payload["authority_public_key_sha256"], "authority_public_key_sha256")
    return DECISION_SIGNATURE_DOMAIN + canonical_json(signed_payload)


def validate_qualification_decision(
    decision: Mapping[str, Any],
    *,
    profile: Mapping[str, Any],
    review: Mapping[str, Any],
    metadata_review: Mapping[str, Any],
    evidence_manifest_sha256: str,
    expected_authority_id: str,
    expected_authority_public_key: bytes,
    signature_verifier: SignatureVerifier,
) -> str:
    if not isinstance(decision, Mapping):
        raise ValueError("qualification decision must be an object")
    _exact_keys(decision, DECISION_KEYS, "qualification decision")
    if not verify_sealed_object(decision):
        raise ValueError("qualification decision seal invalid")
    if decision["schema_version"] != DECISION_SCHEMA_VERSION or decision["object_type"] != DECISION_OBJECT_TYPE:
        raise ValueError("qualification decision schema identity mismatch")
    if decision["signature_projection"] != DECISION_SIGNATURE_PROJECTION:
        raise ValueError("qualification decision signature projection mismatch")
    if decision["signature_algorithm"] != "ED25519":
        raise ValueError("qualification decision signature algorithm mismatch")

    signed_payload = decision["signed_payload"]
    signing_bytes = qualification_decision_signing_bytes(signed_payload)
    if decision["signed_payload_sha256"] != content_hash(signed_payload):
        raise ValueError("qualification decision signed_payload_sha256 mismatch")
    signature = _strict_b64(decision["authority_signature_base64"], "authority_signature_base64", 64)
    if not isinstance(expected_authority_public_key, bytes) or len(expected_authority_public_key) != 32:
        raise ValueError("expected authority public key must be exactly 32 bytes")
    require_ascii_token(expected_authority_id, "expected_authority_id")
    if signed_payload["authority_id"] != expected_authority_id:
        raise ValueError("qualification decision authority_id mismatch")
    expected_key_hash = hashlib.sha256(expected_authority_public_key).hexdigest()
    if signed_payload["authority_public_key_sha256"] != expected_key_hash:
        raise ValueError("qualification decision authority public key mismatch")
    if not callable(signature_verifier):
        raise ValueError("signature_verifier must be callable")
    if signature_verifier(expected_authority_public_key, signing_bytes, signature) is not True:
        raise ValueError("qualification decision Ed25519 signature invalid")

    validate_production_provider_profile(profile)
    validate_provider_metadata_review(metadata_review, profile=profile)
    validate_qualification_review(
        review,
        profile=profile,
        metadata_review=metadata_review,
        evidence_manifest_sha256=evidence_manifest_sha256,
    )
    if signed_payload["provider_id"] != profile["provider_id"]:
        raise ValueError("qualification decision provider mismatch")
    if _ref(signed_payload["provider_profile_ref"], "provider_profile_ref") != object_ref(profile):
        raise ValueError("qualification decision profile binding mismatch")
    if signed_payload["evidence_manifest_sha256"] != _hex64(evidence_manifest_sha256, "evidence_manifest_sha256"):
        raise ValueError("qualification decision manifest binding mismatch")
    if signed_payload["verifier_build_profile_sha256"] != review["verifier_build_profile_sha256"]:
        raise ValueError("qualification decision verifier build binding mismatch")
    if signed_payload["verifier_binary_sha256"] != review["verifier_binary_sha256"]:
        raise ValueError("qualification decision verifier binary binding mismatch")
    if _ref(signed_payload["independent_review_ref"], "independent_review_ref") != object_ref(review):
        raise ValueError("qualification decision review binding mismatch")
    if _ref(signed_payload["metadata_review_ref"], "metadata_review_ref") != object_ref(metadata_review):
        raise ValueError("qualification decision metadata binding mismatch")

    decision_time = _dt(signed_payload["decision_timestamp"], "decision_timestamp")
    review_time = _dt(review["reviewed_at"], "review.reviewed_at")
    metadata_time = _dt(metadata_review["reviewed_at"], "metadata_review.reviewed_at")
    if decision_time < review_time or decision_time < metadata_time:
        raise ValueError("qualification decision predates required review evidence")
    if decision_time > metadata_time + timedelta(days=METADATA_REVIEW_INTERVAL_DAYS):
        raise ValueError("qualification decision metadata review is older than 90 days")

    if signed_payload["decision_result"] == "PRODUCTION_QUALIFIED":
        if review["review_result"] != "PASS":
            raise ValueError("production qualification requires PASS independent review")
        if metadata_review["change_disposition"] != "UNCHANGED":
            raise ValueError("production qualification requires unchanged current metadata")
        if metadata_review["service_status"] != "ACTIVE":
            raise ValueError("production qualification requires active service")
        if metadata_review["use_permission_status"] != "AFFIRMATIVE":
            raise ValueError("production qualification requires affirmative use permission")
    return decision["content_sha256"]


def _sorted_object_refs(objects: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    refs = [object_ref(obj) for obj in objects]
    return sorted(refs, key=lambda item: (item["object_id"], item["content_sha256"]))


def _state_report(core: Mapping[str, Any]) -> dict[str, Any]:
    report = dict(core)
    report["report_sha256"] = content_hash(core)
    return report


def validate_qualification_state_report(report: Mapping[str, Any]) -> str:
    if not isinstance(report, Mapping):
        raise ValueError("qualification state report must be an object")
    _keys_with_optional(report, STATE_REQUIRED_KEYS, STATE_OPTIONAL_KEYS, "qualification state report")
    if report["schema_version"] != STATE_SCHEMA_VERSION or report["object_type"] != STATE_OBJECT_TYPE:
        raise ValueError("qualification state report schema identity mismatch")
    _provider_expected(report["provider_id"])
    _dt(report["as_of_utc"], "as_of_utc")
    if report["state"] not in QUALIFICATION_STATES:
        raise ValueError("qualification state invalid")
    _sorted_unique_strings(report["reason_codes"], "reason_codes", tokens=True)
    if "decision_ref" in report:
        _ref(report["decision_ref"], "decision_ref")
    if "review_ref" in report:
        _ref(report["review_ref"], "review_ref")
    if "latest_metadata_review_ref" in report:
        _ref(report["latest_metadata_review_ref"], "latest_metadata_review_ref")
    active_refs = report["active_requalification_event_refs"]
    if not isinstance(active_refs, list):
        raise ValueError("active_requalification_event_refs must be an array")
    normalized = [_ref(item, "active_requalification_event_refs[]") for item in active_refs]
    if normalized != sorted(normalized, key=lambda item: (item["object_id"], item["content_sha256"])):
        raise ValueError("active_requalification_event_refs must be sorted")
    supplied = _hex64(report["report_sha256"], "report_sha256")
    core = dict(report)
    core.pop("report_sha256")
    if supplied != content_hash(core):
        raise ValueError("qualification state report hash mismatch")
    return supplied


def derive_qualification_state(
    *,
    provider_id: str,
    as_of_utc: str,
    rehearsal_verified: bool,
    profile: Mapping[str, Any] | None = None,
    evidence_manifest_sha256: str | None = None,
    review: Mapping[str, Any] | None = None,
    decision: Mapping[str, Any] | None = None,
    metadata_reviews: Sequence[Mapping[str, Any]] = (),
    requalification_events: Sequence[Mapping[str, Any]] = (),
    expected_authority_id: str | None = None,
    expected_authority_public_key: bytes | None = None,
    signature_verifier: SignatureVerifier | None = None,
) -> dict[str, Any]:
    _provider_expected(provider_id)
    as_of = _dt(as_of_utc, "as_of_utc")
    if not isinstance(rehearsal_verified, bool):
        raise ValueError("rehearsal_verified must be boolean")

    core: dict[str, Any] = {
        "schema_version": STATE_SCHEMA_VERSION,
        "object_type": STATE_OBJECT_TYPE,
        "provider_id": provider_id,
        "as_of_utc": as_of_utc,
        "reason_codes": [],
        "active_requalification_event_refs": [],
    }

    if review is None and decision is None:
        core["state"] = "REHEARSAL_VERIFIED" if rehearsal_verified else "UNREVIEWED"
        core["reason_codes"] = (
            ["REHEARSAL_EVIDENCE_VERIFIED"]
            if rehearsal_verified
            else ["NO_QUALIFICATION_REVIEW"]
        )
        report = _state_report(core)
        validate_qualification_state_report(report)
        return report

    if profile is None or evidence_manifest_sha256 is None:
        raise ValueError("profile and evidence_manifest_sha256 are required once qualification review exists")
    validate_production_provider_profile(profile)
    if profile["provider_id"] != provider_id:
        raise ValueError("state provider/profile mismatch")

    matching_metadata: list[Mapping[str, Any]] = []
    for metadata in metadata_reviews:
        validate_provider_metadata_review(metadata, profile=profile)
        if metadata["provider_id"] != provider_id:
            raise ValueError("metadata review provider mismatch in state inputs")
        if _dt(metadata["reviewed_at"], "metadata reviewed_at") <= as_of:
            matching_metadata.append(metadata)
    matching_metadata.sort(key=lambda item: (item["reviewed_at"], item["content_sha256"]))

    if review is not None:
        metadata_by_ref = {tuple(object_ref(item).items()): item for item in matching_metadata}
        review_metadata_ref = _ref(review["metadata_review_ref"], "review.metadata_review_ref")
        metadata_for_review = metadata_by_ref.get(tuple(review_metadata_ref.items()))
        if metadata_for_review is None:
            raise ValueError("state inputs do not contain the metadata review bound by qualification review")
        validate_qualification_review(
            review,
            profile=profile,
            metadata_review=metadata_for_review,
            evidence_manifest_sha256=evidence_manifest_sha256,
        )
        core["review_ref"] = object_ref(review)

    if decision is None:
        if review is None:
            raise ValueError("decision absent but qualification review missing")
        if review["review_result"] == "PASS":
            core["state"] = "QUALIFICATION_REVIEW_READY"
            core["reason_codes"] = ["INDEPENDENT_REVIEW_PASS_DECISION_REQUIRED"]
        else:
            core["state"] = "QUALIFICATION_BLOCKED"
            core["reason_codes"] = ["INDEPENDENT_REVIEW_BLOCK"]
        if matching_metadata:
            core["latest_metadata_review_ref"] = object_ref(matching_metadata[-1])
        report = _state_report(core)
        validate_qualification_state_report(report)
        return report

    if review is None:
        raise ValueError("qualification decision requires its independent review")
    if (
        expected_authority_id is None
        or expected_authority_public_key is None
        or signature_verifier is None
    ):
        raise ValueError("external qualification authority and signature verifier are required")

    decision_metadata_ref = _ref(
        decision["signed_payload"]["metadata_review_ref"],
        "decision.metadata_review_ref",
    )
    metadata_by_ref = {tuple(object_ref(item).items()): item for item in matching_metadata}
    decision_metadata = metadata_by_ref.get(tuple(decision_metadata_ref.items()))
    if decision_metadata is None:
        raise ValueError("state inputs do not contain the metadata review bound by qualification decision")
    validate_qualification_decision(
        decision,
        profile=profile,
        review=review,
        metadata_review=decision_metadata,
        evidence_manifest_sha256=evidence_manifest_sha256,
        expected_authority_id=expected_authority_id,
        expected_authority_public_key=expected_authority_public_key,
        signature_verifier=signature_verifier,
    )
    core["decision_ref"] = object_ref(decision)
    decision_time = _dt(decision["signed_payload"]["decision_timestamp"], "decision timestamp")
    if as_of < decision_time:
        raise ValueError("as_of_utc predates qualification decision")

    if decision["signed_payload"]["decision_result"] == "QUALIFICATION_BLOCKED":
        core["state"] = "QUALIFICATION_BLOCKED"
        core["reason_codes"] = ["SIGNED_QUALIFICATION_BLOCK"]
        if matching_metadata:
            core["latest_metadata_review_ref"] = object_ref(matching_metadata[-1])
        report = _state_report(core)
        validate_qualification_state_report(report)
        return report

    active_events: list[Mapping[str, Any]] = []
    for event in requalification_events:
        validate_requalification_event(event, profile=profile)
        if event["provider_id"] != provider_id:
            raise ValueError("requalification event provider mismatch in state inputs")
        event_time = _dt(event["detected_at"], "requalification detected_at")
        if decision_time <= event_time <= as_of:
            active_events.append(event)
    active_events.sort(key=lambda item: (item["detected_at"], item["content_sha256"]))
    core["active_requalification_event_refs"] = _sorted_object_refs(active_events)

    post_decision_changes = [
        item
        for item in matching_metadata
        if _dt(item["reviewed_at"], "metadata reviewed_at") >= decision_time
        and item["change_disposition"] != "UNCHANGED"
    ]
    if active_events or post_decision_changes:
        core["state"] = "REQUALIFICATION_REQUIRED"
        reasons = []
        if active_events:
            reasons.append("ACTIVE_REQUALIFICATION_TRIGGER")
        if post_decision_changes:
            reasons.append("QUALIFICATION_RELEVANT_METADATA_CHANGE")
        core["reason_codes"] = sorted(reasons)
        if matching_metadata:
            core["latest_metadata_review_ref"] = object_ref(matching_metadata[-1])
        report = _state_report(core)
        validate_qualification_state_report(report)
        return report

    if not matching_metadata:
        raise ValueError("qualified state requires retained metadata review")
    latest_metadata = matching_metadata[-1]
    core["latest_metadata_review_ref"] = object_ref(latest_metadata)
    latest_time = _dt(latest_metadata["reviewed_at"], "latest metadata reviewed_at")
    if as_of > latest_time + timedelta(days=METADATA_REVIEW_INTERVAL_DAYS):
        core["state"] = "QUALIFICATION_EXPIRED"
        core["reason_codes"] = ["METADATA_REVIEW_INTERVAL_EXCEEDED"]
    else:
        core["state"] = "PRODUCTION_QUALIFIED"
        core["reason_codes"] = ["SIGNED_DECISION_VALID_AND_METADATA_CURRENT"]
    report = _state_report(core)
    validate_qualification_state_report(report)
    return report
