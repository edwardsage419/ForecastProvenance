from __future__ import annotations

import base64
import binascii
from typing import Any, Callable, Mapping

from .canonical import (
    CanonicalizationError,
    canonical_json,
    content_hash,
    require_utc_timestamp,
    seal_object,
    sorted_refs,
    validate_ref,
    verify_sealed_object,
)


SCHEMA_VERSION = "1.0"
STABLE_CONTEXT = "v1"
HISTORY_SIGNATURE_PROJECTION = "FPP_QUALIFICATION_STATE_HISTORY_SNAPSHOT_V1"
HISTORY_SIGNATURE_DOMAIN = HISTORY_SIGNATURE_PROJECTION.encode("ascii") + b"\x00"

ACCEPTED_QUALIFICATION_INPUT_ROLES = (
    "provider_metadata_review",
    "provider_profile",
    "qualification_decision",
    "qualification_evidence_manifest",
    "qualification_review",
    "requalification_event",
    "roughtime_verifier_build_profile",
    "state_history_snapshot",
    "state_report",
)

INVALID_REASON_PRECEDENCE = (
    "PACKAGE_STRICT_JSON_INVALID",
    "PACKAGE_SCHEMA_INVALID",
    "PACKAGE_SEALED_IDENTITY_OR_REFERENCE_INVALID",
    "PACKAGE_MEMBER_MANIFEST_INVALID",
    "PACKAGE_MEMBER_CLOSURE_INVALID",
    "QUALIFICATION_INPUT_SCHEMA_INVALID",
    "STATE_REPORT_MEMBER_INVALID",
    "HISTORY_SNAPSHOT_AUTHENTICATION_INVALID",
    "HISTORY_CUTOFF_INVALID",
    "HISTORY_SUCCESSION_INVALID",
    "HISTORY_COMPLETENESS_INVALID",
    "QUALIFICATION_EVIDENCE_PACKAGE_INVALID",
    "QUALIFICATION_AUTHORITY_CHAIN_INVALID",
    "QUALIFICATION_STATE_DERIVATION_INVALID",
    "STATE_REPORT_SEMANTIC_MISMATCH",
)

QUALIFICATION_STATES = frozenset(
    {
        "QUALIFICATION_BLOCKED",
        "QUALIFICATION_EXPIRED",
        "REQUALIFICATION_REQUIRED",
        "PRODUCTION_QUALIFIED",
    }
)

_DERIVED_FIELDS = frozenset({"object_id", "payload_sha256", "content_sha256"})
_CONTRACT_FIELDS = frozenset(
    {
        "schema_version",
        "object_role",
        "qualification_integration_semantics_id",
        "qualification_state_derivation_semantics_id",
        "validator_contract_ref",
        "roughtime_qualification_verifier_contract_ref",
        "accepted_qualification_input_schema_refs",
        "qualification_validation_invocation_schema_ref",
        "dynamic_qualification_state_package_v2_schema_ref",
        "dynamic_qualification_state_package_v2_role_semantics_id",
        "dynamic_qualification_state_package_v2_member_closure_semantics_id",
        "qualification_state_history_snapshot_schema_ref",
        "qualification_state_history_completeness_semantics_id",
        "qualification_state_history_succession_semantics_id",
        "qualification_state_history_snapshot_signature_projection",
        "qualification_state_history_snapshot_signer_semantics_id",
        "state_report_schema_ref",
        "state_report_semantic_hash_projection",
        "qualification_validation_result_schema_ref",
        "invalid_reason_vocabulary_id",
        "invalid_reason_precedence",
        "no_authoritative_result_semantics_id",
        "strict_json_profile",
        "canonicalization_profile",
        "inclusive_cutoff_semantics_id",
    }
)
_INVOCATION_FIELDS = frozenset(
    {
        "schema_version",
        "qualification_validation_contract_ref",
        "qualification_state_package_ref",
        "qualification_state_package_serialized_sha256",
    }
)
_HISTORY_COMMON_FIELDS = frozenset(
    {
        "schema_version",
        "provider_profile_ref",
        "snapshot_sequence",
        "through_as_of_utc",
        "metadata_review_refs",
        "requalification_event_refs",
        "signed_payload_sha256",
        "authority_signature_base64",
    }
)
_RESULT_COMMON_FIELDS = frozenset(
    {
        "schema_version",
        "qualification_validation_contract_ref",
        "qualification_validation_invocation_ref",
        "qualification_state_package_ref",
        "validation_status",
    }
)
_INVALID_RESULT_FIELDS = _RESULT_COMMON_FIELDS | {"primary_invalid_reason_code"}
_VALID_RESULT_FIELDS = _RESULT_COMMON_FIELDS | {
    "provider_profile_ref",
    "qualification_decision_ref",
    "qualification_state_history_snapshot_ref",
    "as_of_utc",
    "qualification_state",
    "derived_state_report_semantic_sha256",
}
_CONTRACT_CONSTANTS = {
    "schema_version": SCHEMA_VERSION,
    "object_role": "NORMATIVE",
    "qualification_integration_semantics_id": "FPP_QUALIFICATION_VALIDATION_INTEGRATION_V1",
    "qualification_state_derivation_semantics_id": "FPP_ROUGHTIME_QUALIFICATION_STATE_DERIVATION_V1",
    "dynamic_qualification_state_package_v2_role_semantics_id": "FPP_DYNAMIC_QUALIFICATION_STATE_PACKAGE_ROLE_SEMANTICS_V2",
    "dynamic_qualification_state_package_v2_member_closure_semantics_id": "FPP_DYNAMIC_QUALIFICATION_STATE_PACKAGE_MEMBER_CLOSURE_V2",
    "qualification_state_history_completeness_semantics_id": "FPP_QUALIFICATION_STATE_HISTORY_COMPLETENESS_V1",
    "qualification_state_history_succession_semantics_id": "FPP_QUALIFICATION_STATE_HISTORY_SUCCESSION_V1",
    "qualification_state_history_snapshot_signature_projection": HISTORY_SIGNATURE_PROJECTION,
    "qualification_state_history_snapshot_signer_semantics_id": "FPP_HISTORY_SIGNER_SAME_AS_QUALIFICATION_AUTHORITY_V1",
    "state_report_semantic_hash_projection": "SHA256_FPP_JCS_1_EXCLUDING_REPORT_SHA256",
    "invalid_reason_vocabulary_id": "FPP_QUALIFICATION_VALIDATION_INVALID_REASON_V1",
    "no_authoritative_result_semantics_id": "FPP_QUALIFICATION_NO_AUTHORITATIVE_RESULT_V1",
    "strict_json_profile": "FPP_STRICT_JSON_1",
    "canonicalization_profile": "FPP_JCS_1",
    "inclusive_cutoff_semantics_id": "FPP_INCLUSIVE_CUTOFF_V1",
}
_CONTRACT_REF_FIELDS = (
    "validator_contract_ref",
    "roughtime_qualification_verifier_contract_ref",
    "qualification_validation_invocation_schema_ref",
    "dynamic_qualification_state_package_v2_schema_ref",
    "qualification_state_history_snapshot_schema_ref",
    "state_report_schema_ref",
    "qualification_validation_result_schema_ref",
)


class QualificationValidationContractError(ValueError):
    """A Phase 4C object violates its frozen structural contract."""


def _fail(message: str) -> None:
    raise QualificationValidationContractError(message)


def _require_exact_fields(
    value: Mapping[str, Any], expected: frozenset[str], label: str
) -> None:
    if not isinstance(value, Mapping):
        _fail(f"{label} payload must be a mapping")
    actual = set(value)
    if actual != expected:
        _fail(
            f"{label} fields invalid; "
            f"missing={sorted(expected - actual)}; extra={sorted(actual - expected)}"
        )
    if any(member is None for member in value.values()):
        _fail(f"{label} null values are prohibited")
    if value.get("schema_version") != SCHEMA_VERSION:
        _fail(f"{label} schema_version must be 1.0")


def _require_ref(value: Any, field: str) -> dict[str, str]:
    try:
        validate_ref(value)
    except (CanonicalizationError, KeyError, TypeError) as exc:
        raise QualificationValidationContractError(
            f"{field} must be an exact full reference"
        ) from exc
    return dict(value)


def _require_ref_array(value: Any, field: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        _fail(f"{field} must be a list")
    try:
        normalized = sorted_refs(value)
    except (CanonicalizationError, KeyError, TypeError) as exc:
        raise QualificationValidationContractError(
            f"{field} contains a malformed reference"
        ) from exc
    pairs = [(item["object_id"], item["content_sha256"]) for item in normalized]
    if len(pairs) != len(set(pairs)):
        _fail(f"{field} must contain unique references")
    if value != normalized:
        _fail(f"{field} must be sorted by object_id then content_sha256")
    return normalized


def _require_sha256(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _fail(f"{field} must be 64 lowercase hexadecimal characters")
    return value


def _require_utc(value: Any, field: str) -> str:
    try:
        return require_utc_timestamp(value)
    except (CanonicalizationError, TypeError) as exc:
        raise QualificationValidationContractError(
            f"{field} must be a canonical whole-second UTC timestamp"
        ) from exc


def _require_base64(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        _fail(f"{field} must be non-empty canonical base64")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise QualificationValidationContractError(
            f"{field} must be non-empty canonical base64"
        ) from exc
    if not decoded or base64.b64encode(decoded).decode("ascii") != value:
        _fail(f"{field} must be non-empty canonical base64")
    return value


def _seal(payload: Mapping[str, Any], object_type: str) -> dict[str, Any]:
    try:
        return seal_object(
            payload,
            object_type=object_type,
            stable_context=STABLE_CONTEXT,
        )
    except CanonicalizationError as exc:
        raise QualificationValidationContractError(
            f"{object_type} sealing failed"
        ) from exc


def _validate_sealed(
    obj: Mapping[str, Any],
    object_type: str,
    builder: Callable[[Mapping[str, Any]], dict[str, Any]],
) -> dict[str, str]:
    if not isinstance(obj, Mapping) or not verify_sealed_object(obj):
        _fail(f"expected a valid sealed {object_type}")
    if obj.get("object_type") != object_type:
        _fail(f"expected a valid sealed {object_type}")
    payload = {
        key: value
        for key, value in obj.items()
        if key not in _DERIVED_FIELDS | {"object_type"}
    }
    if builder(payload) != dict(obj):
        _fail(f"{object_type} identity was not canonically reconstructed")
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def _validate_accepted_inputs(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) != len(
        ACCEPTED_QUALIFICATION_INPUT_ROLES
    ):
        _fail("accepted_qualification_input_schema_refs must contain nine roles")
    normalized: list[dict[str, Any]] = []
    observed_roles: list[str] = []
    for entry in value:
        if not isinstance(entry, Mapping) or set(entry) != {"role", "schema_ref"}:
            _fail("accepted input entry must contain role and schema_ref only")
        role = entry["role"]
        if not isinstance(role, str):
            _fail("accepted input role must be a string")
        observed_roles.append(role)
        normalized.append({"role": role, "schema_ref": _require_ref(entry["schema_ref"], "schema_ref")})
    if tuple(observed_roles) != ACCEPTED_QUALIFICATION_INPUT_ROLES:
        _fail("accepted qualification input roles differ from the frozen lexical order")
    if len(observed_roles) != len(set(observed_roles)):
        _fail("accepted qualification input roles must be unique")
    return normalized


def build_qualification_validation_contract(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    _require_exact_fields(payload, _CONTRACT_FIELDS, "QualificationValidationContract")
    for field, expected in _CONTRACT_CONSTANTS.items():
        if payload[field] != expected:
            _fail(f"QualificationValidationContract {field} differs from the frozen value")
    for field in _CONTRACT_REF_FIELDS:
        _require_ref(payload[field], field)
    _validate_accepted_inputs(payload["accepted_qualification_input_schema_refs"])
    if payload["invalid_reason_precedence"] != list(INVALID_REASON_PRECEDENCE):
        _fail("invalid_reason_precedence differs from the frozen ordered vocabulary")
    return _seal(payload, "QualificationValidationContract")


def validate_qualification_validation_contract(
    obj: Mapping[str, Any],
) -> dict[str, str]:
    return _validate_sealed(
        obj,
        "QualificationValidationContract",
        build_qualification_validation_contract,
    )


def build_qualification_validation_invocation(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    _require_exact_fields(payload, _INVOCATION_FIELDS, "QualificationValidationInvocation")
    _require_ref(
        payload["qualification_validation_contract_ref"],
        "qualification_validation_contract_ref",
    )
    _require_ref(
        payload["qualification_state_package_ref"],
        "qualification_state_package_ref",
    )
    _require_sha256(
        payload["qualification_state_package_serialized_sha256"],
        "qualification_state_package_serialized_sha256",
    )
    return _seal(payload, "QualificationValidationInvocation")


def validate_qualification_validation_invocation(
    obj: Mapping[str, Any],
) -> dict[str, str]:
    return _validate_sealed(
        obj,
        "QualificationValidationInvocation",
        build_qualification_validation_invocation,
    )


def qualification_state_history_snapshot_signed_projection(
    snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    projection_fields = {
        "schema_version",
        "provider_profile_ref",
        "snapshot_sequence",
        "through_as_of_utc",
        "metadata_review_refs",
        "requalification_event_refs",
    }
    if "predecessor_snapshot_ref" in snapshot:
        projection_fields.add("predecessor_snapshot_ref")
    return {
        "schema_version": snapshot["schema_version"],
        "object_type": "QualificationStateHistorySnapshot",
        **{
            key: snapshot[key]
            for key in (
                "provider_profile_ref",
                "snapshot_sequence",
                "predecessor_snapshot_ref",
                "through_as_of_utc",
                "metadata_review_refs",
                "requalification_event_refs",
            )
            if key in projection_fields
        },
    }


def qualification_state_history_snapshot_signature_message(
    snapshot: Mapping[str, Any],
) -> bytes:
    return HISTORY_SIGNATURE_DOMAIN + canonical_json(
        qualification_state_history_snapshot_signed_projection(snapshot)
    )


def build_qualification_state_history_snapshot(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        _fail("QualificationStateHistorySnapshot payload must be a mapping")
    sequence = payload.get("snapshot_sequence")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        _fail("snapshot_sequence must be a non-negative integer")
    expected_fields = _HISTORY_COMMON_FIELDS
    if sequence == 0:
        if "predecessor_snapshot_ref" in payload:
            _fail("sequence zero prohibits predecessor_snapshot_ref")
    else:
        expected_fields = expected_fields | {"predecessor_snapshot_ref"}
    _require_exact_fields(payload, expected_fields, "QualificationStateHistorySnapshot")
    _require_ref(payload["provider_profile_ref"], "provider_profile_ref")
    if sequence > 0:
        _require_ref(payload["predecessor_snapshot_ref"], "predecessor_snapshot_ref")
    _require_utc(payload["through_as_of_utc"], "through_as_of_utc")
    _require_ref_array(payload["metadata_review_refs"], "metadata_review_refs")
    _require_ref_array(
        payload["requalification_event_refs"], "requalification_event_refs"
    )
    _require_sha256(payload["signed_payload_sha256"], "signed_payload_sha256")
    _require_base64(payload["authority_signature_base64"], "authority_signature_base64")
    projection = qualification_state_history_snapshot_signed_projection(payload)
    if payload["signed_payload_sha256"] != content_hash(projection):
        _fail("signed_payload_sha256 does not hash the canonical signed projection")
    return _seal(payload, "QualificationStateHistorySnapshot")


def validate_qualification_state_history_snapshot(
    obj: Mapping[str, Any],
) -> dict[str, str]:
    return _validate_sealed(
        obj,
        "QualificationStateHistorySnapshot",
        build_qualification_state_history_snapshot,
    )


def build_qualification_validation_result(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        _fail("QualificationValidationResult payload must be a mapping")
    status = payload.get("validation_status")
    if status == "INVALID":
        expected_fields = _INVALID_RESULT_FIELDS
    elif status == "VALID":
        expected_fields = _VALID_RESULT_FIELDS
    else:
        _fail("validation_status must be VALID or INVALID")
    _require_exact_fields(payload, expected_fields, "QualificationValidationResult")
    for field in (
        "qualification_validation_contract_ref",
        "qualification_validation_invocation_ref",
        "qualification_state_package_ref",
    ):
        _require_ref(payload[field], field)
    if status == "INVALID":
        if payload["primary_invalid_reason_code"] not in INVALID_REASON_PRECEDENCE:
            _fail("primary_invalid_reason_code is outside the frozen vocabulary")
    else:
        for field in (
            "provider_profile_ref",
            "qualification_decision_ref",
            "qualification_state_history_snapshot_ref",
        ):
            _require_ref(payload[field], field)
        _require_utc(payload["as_of_utc"], "as_of_utc")
        if payload["qualification_state"] not in QUALIFICATION_STATES:
            _fail("qualification_state is outside the frozen VALID vocabulary")
        _require_sha256(
            payload["derived_state_report_semantic_sha256"],
            "derived_state_report_semantic_sha256",
        )
    return _seal(payload, "QualificationValidationResult")


def validate_qualification_validation_result(
    obj: Mapping[str, Any],
) -> dict[str, str]:
    return _validate_sealed(
        obj,
        "QualificationValidationResult",
        build_qualification_validation_result,
    )
