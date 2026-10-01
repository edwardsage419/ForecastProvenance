from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from forecast_trust_core.canonical import canonical_json, content_hash, seal_object, verify_sealed_object


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"

INVALID_REASON_PRECEDENCE = [
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
]
ACCEPTED_INPUT_ROLES = [
    "provider_metadata_review",
    "provider_profile",
    "qualification_decision",
    "qualification_evidence_manifest",
    "qualification_review",
    "requalification_event",
    "roughtime_verifier_build_profile",
    "state_history_snapshot",
    "state_report",
]


def ref(seed: str) -> dict[str, str]:
    return {"object_id": f"schema:{seed}:v1", "content_sha256": seed[0] * 64}


def accepted_inputs() -> list[dict[str, object]]:
    return [
        {"role": role, "schema_ref": ref(str(index + 1))}
        for index, role in enumerate(ACCEPTED_INPUT_ROLES)
    ]


def contract_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "object_role": "NORMATIVE",
        "qualification_integration_semantics_id": "FPP_QUALIFICATION_VALIDATION_INTEGRATION_V1",
        "qualification_state_derivation_semantics_id": "FPP_ROUGHTIME_QUALIFICATION_STATE_DERIVATION_V1",
        "validator_contract_ref": ref("a"),
        "roughtime_qualification_verifier_contract_ref": ref("b"),
        "accepted_qualification_input_schema_refs": accepted_inputs(),
        "qualification_validation_invocation_schema_ref": ref("c"),
        "dynamic_qualification_state_package_v2_schema_ref": ref("d"),
        "dynamic_qualification_state_package_v2_role_semantics_id": "FPP_DYNAMIC_QUALIFICATION_STATE_PACKAGE_ROLE_SEMANTICS_V2",
        "dynamic_qualification_state_package_v2_member_closure_semantics_id": "FPP_DYNAMIC_QUALIFICATION_STATE_PACKAGE_MEMBER_CLOSURE_V2",
        "qualification_state_history_snapshot_schema_ref": ref("e"),
        "qualification_state_history_completeness_semantics_id": "FPP_QUALIFICATION_STATE_HISTORY_COMPLETENESS_V1",
        "qualification_state_history_succession_semantics_id": "FPP_QUALIFICATION_STATE_HISTORY_SUCCESSION_V1",
        "qualification_state_history_snapshot_signature_projection": "FPP_QUALIFICATION_STATE_HISTORY_SNAPSHOT_V1",
        "qualification_state_history_snapshot_signer_semantics_id": "FPP_HISTORY_SIGNER_SAME_AS_QUALIFICATION_AUTHORITY_V1",
        "state_report_schema_ref": ref("f"),
        "state_report_semantic_hash_projection": "SHA256_FPP_JCS_1_EXCLUDING_REPORT_SHA256",
        "qualification_validation_result_schema_ref": ref("1"),
        "invalid_reason_vocabulary_id": "FPP_QUALIFICATION_VALIDATION_INVALID_REASON_V1",
        "invalid_reason_precedence": list(INVALID_REASON_PRECEDENCE),
        "no_authoritative_result_semantics_id": "FPP_QUALIFICATION_NO_AUTHORITATIVE_RESULT_V1",
        "strict_json_profile": "FPP_STRICT_JSON_1",
        "canonicalization_profile": "FPP_JCS_1",
        "inclusive_cutoff_semantics_id": "FPP_INCLUSIVE_CUTOFF_V1",
    }


def invocation_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "qualification_validation_contract_ref": ref("a"),
        "qualification_state_package_ref": ref("b"),
        "qualification_state_package_serialized_sha256": "c" * 64,
    }


def history_payload(sequence: int = 0) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "1.0",
        "provider_profile_ref": ref("a"),
        "snapshot_sequence": sequence,
        "through_as_of_utc": "2026-09-24T00:00:00Z",
        "metadata_review_refs": [ref("b"), ref("c")],
        "requalification_event_refs": [ref("d"), ref("e")],
        "authority_signature_base64": "dGVzdC1zaWduYXR1cmU=",
    }
    if sequence:
        payload["predecessor_snapshot_ref"] = ref("f")
    signed_projection = {
        key: value
        for key, value in payload.items()
        if key not in {"signed_payload_sha256", "authority_signature_base64"}
    }
    payload["signed_payload_sha256"] = content_hash(
        {"object_type": "QualificationStateHistorySnapshot", **signed_projection}
    )
    return payload


def invalid_result_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "qualification_validation_contract_ref": ref("a"),
        "qualification_validation_invocation_ref": ref("b"),
        "qualification_state_package_ref": ref("c"),
        "validation_status": "INVALID",
        "primary_invalid_reason_code": INVALID_REASON_PRECEDENCE[0],
    }


def valid_result_payload() -> dict[str, object]:
    return {
        "schema_version": "1.0",
        "qualification_validation_contract_ref": ref("a"),
        "qualification_validation_invocation_ref": ref("b"),
        "qualification_state_package_ref": ref("c"),
        "validation_status": "VALID",
        "provider_profile_ref": ref("d"),
        "qualification_decision_ref": ref("e"),
        "qualification_state_history_snapshot_ref": ref("f"),
        "as_of_utc": "2026-09-24T00:00:00Z",
        "qualification_state": "PRODUCTION_QUALIFIED",
        "derived_state_report_semantic_sha256": "1" * 64,
    }


def sealed(payload: dict[str, object], object_type: str) -> dict[str, object]:
    return seal_object(payload, object_type=object_type, stable_context="v1")


def schema_validator(filename: str) -> Draft202012Validator:
    path = SCHEMAS / filename
    assert path.is_file(), f"missing normative schema: {filename}"
    schema = json.loads(path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.mark.parametrize(
    ("filename", "object_type", "payload"),
    [
        ("qualification_validation_contract_v1.schema.json", "QualificationValidationContract", contract_payload()),
        ("qualification_validation_invocation_v1.schema.json", "QualificationValidationInvocation", invocation_payload()),
        ("qualification_state_history_snapshot_v1.schema.json", "QualificationStateHistorySnapshot", history_payload()),
        ("qualification_validation_result_v1.schema.json", "QualificationValidationResult", valid_result_payload()),
        ("qualification_validation_result_v1.schema.json", "QualificationValidationResult", invalid_result_payload()),
    ],
)
def test_schema_accepts_exact_sealed_projection(filename, object_type, payload):
    schema_validator(filename).validate(sealed(payload, object_type))


@pytest.mark.parametrize(
    ("filename", "object_type", "payload"),
    [
        ("qualification_validation_contract_v1.schema.json", "QualificationValidationContract", contract_payload()),
        ("qualification_validation_invocation_v1.schema.json", "QualificationValidationInvocation", invocation_payload()),
        ("qualification_state_history_snapshot_v1.schema.json", "QualificationStateHistorySnapshot", history_payload()),
        ("qualification_validation_result_v1.schema.json", "QualificationValidationResult", valid_result_payload()),
    ],
)
def test_schema_rejects_unknown_field_and_null(filename, object_type, payload):
    validator = schema_validator(filename)
    unknown = sealed({**payload, "unexpected": "value"}, object_type)
    with pytest.raises(ValidationError):
        validator.validate(unknown)
    null_value = copy.deepcopy(sealed(payload, object_type))
    null_value[next(key for key in payload if key != "schema_version")] = None
    with pytest.raises(ValidationError):
        validator.validate(null_value)


def test_contract_schema_closes_constants_roles_and_precedence():
    validator = schema_validator("qualification_validation_contract_v1.schema.json")
    contract = sealed(contract_payload(), "QualificationValidationContract")
    validator.validate(contract)
    assert [item["role"] for item in contract["accepted_qualification_input_schema_refs"]] == ACCEPTED_INPUT_ROLES
    assert contract["invalid_reason_precedence"] == INVALID_REASON_PRECEDENCE
    for mutation in (
        lambda value: value["accepted_qualification_input_schema_refs"].reverse(),
        lambda value: value["accepted_qualification_input_schema_refs"].__setitem__(1, copy.deepcopy(value["accepted_qualification_input_schema_refs"][0])),
        lambda value: value["invalid_reason_precedence"].reverse(),
        lambda value: value.__setitem__("state_report_semantic_hash_projection", "OTHER"),
    ):
        bad_payload = contract_payload()
        mutation(bad_payload)
        with pytest.raises(ValidationError):
            validator.validate(sealed(bad_payload, "QualificationValidationContract"))


def test_invocation_schema_requires_both_package_commitments():
    validator = schema_validator("qualification_validation_invocation_v1.schema.json")
    for missing in ("qualification_state_package_ref", "qualification_state_package_serialized_sha256"):
        payload = invocation_payload()
        del payload[missing]
        with pytest.raises(ValidationError):
            validator.validate(sealed(payload, "QualificationValidationInvocation"))


def test_history_schema_enforces_predecessor_condition():
    validator = schema_validator("qualification_state_history_snapshot_v1.schema.json")
    zero = history_payload()
    zero["predecessor_snapshot_ref"] = ref("f")
    with pytest.raises(ValidationError):
        validator.validate(sealed(zero, "QualificationStateHistorySnapshot"))
    successor = history_payload(1)
    del successor["predecessor_snapshot_ref"]
    with pytest.raises(ValidationError):
        validator.validate(sealed(successor, "QualificationStateHistorySnapshot"))


def test_result_schema_closes_valid_and_invalid_branches():
    validator = schema_validator("qualification_validation_result_v1.schema.json")
    invalid_with_valid_field = {**invalid_result_payload(), "as_of_utc": "2026-09-24T00:00:00Z"}
    with pytest.raises(ValidationError):
        validator.validate(sealed(invalid_with_valid_field, "QualificationValidationResult"))
    valid_with_reason = {**valid_result_payload(), "primary_invalid_reason_code": INVALID_REASON_PRECEDENCE[0]}
    with pytest.raises(ValidationError):
        validator.validate(sealed(valid_with_reason, "QualificationValidationResult"))
    invalid_without_reason = invalid_result_payload()
    del invalid_without_reason["primary_invalid_reason_code"]
    with pytest.raises(ValidationError):
        validator.validate(sealed(invalid_without_reason, "QualificationValidationResult"))


def test_result_schema_closes_qualification_state_vocabulary():
    validator = schema_validator("qualification_validation_result_v1.schema.json")
    for state in (
        "QUALIFICATION_BLOCKED",
        "QUALIFICATION_EXPIRED",
        "REQUALIFICATION_REQUIRED",
        "PRODUCTION_QUALIFIED",
    ):
        validator.validate(sealed({**valid_result_payload(), "qualification_state": state}, "QualificationValidationResult"))
    with pytest.raises(ValidationError):
        validator.validate(sealed({**valid_result_payload(), "qualification_state": "REHEARSAL_VERIFIED"}, "QualificationValidationResult"))


def contracts_module():
    from forecast_trust_core import qualification_validation_contracts_v1

    return qualification_validation_contracts_v1


def test_python_contract_builder_accepts_exact_projection_and_constants():
    contracts = contracts_module()
    contract = contracts.build_qualification_validation_contract(contract_payload())
    assert verify_sealed_object(contract)
    assert contract["object_type"] == "QualificationValidationContract"
    assert contract["object_id"].startswith("qualificationvalidationcontract:v1:")
    assert contract["accepted_qualification_input_schema_refs"] == accepted_inputs()
    assert contract["invalid_reason_precedence"] == INVALID_REASON_PRECEDENCE
    assert contracts.validate_qualification_validation_contract(contract) == {
        "object_id": contract["object_id"],
        "content_sha256": contract["content_sha256"],
    }


@pytest.mark.parametrize(
    "mutation",
    [
        lambda payload: payload.__setitem__("unexpected", "value"),
        lambda payload: payload.__setitem__("validator_contract_ref", None),
        lambda payload: payload["accepted_qualification_input_schema_refs"].reverse(),
        lambda payload: payload["accepted_qualification_input_schema_refs"].__setitem__(1, copy.deepcopy(payload["accepted_qualification_input_schema_refs"][0])),
        lambda payload: payload["invalid_reason_precedence"].reverse(),
        lambda payload: payload.__setitem__("canonicalization_profile", "OTHER"),
    ],
)
def test_python_contract_builder_rejects_non_frozen_projection(mutation):
    payload = contract_payload()
    mutation(payload)
    with pytest.raises(ValueError):
        contracts_module().build_qualification_validation_contract(payload)


def test_python_invocation_builder_requires_both_commitments_and_exact_projection():
    contracts = contracts_module()
    invocation = contracts.build_qualification_validation_invocation(invocation_payload())
    assert verify_sealed_object(invocation)
    assert invocation["object_id"].startswith("qualificationvalidationinvocation:v1:")
    assert contracts.validate_qualification_validation_invocation(invocation) == {
        "object_id": invocation["object_id"],
        "content_sha256": invocation["content_sha256"],
    }
    for mutation in (
        lambda payload: payload.pop("qualification_state_package_ref"),
        lambda payload: payload.pop("qualification_state_package_serialized_sha256"),
        lambda payload: payload.__setitem__("provider_profile_ref", ref("d")),
    ):
        payload = invocation_payload()
        mutation(payload)
        with pytest.raises(ValueError):
            contracts.build_qualification_validation_invocation(payload)


def test_python_history_builder_enforces_sequence_and_reference_ordering():
    contracts = contracts_module()
    genesis = contracts.build_qualification_state_history_snapshot(history_payload())
    successor = contracts.build_qualification_state_history_snapshot(history_payload(1))
    assert verify_sealed_object(genesis)
    assert verify_sealed_object(successor)
    assert "predecessor_snapshot_ref" not in genesis
    assert successor["predecessor_snapshot_ref"] == ref("f")
    for payload in (
        {**history_payload(), "predecessor_snapshot_ref": ref("f")},
        {key: value for key, value in history_payload(1).items() if key != "predecessor_snapshot_ref"},
        {**history_payload(), "metadata_review_refs": list(reversed(history_payload()["metadata_review_refs"]))},
        {**history_payload(), "requalification_event_refs": [ref("d"), ref("d")]},
    ):
        with pytest.raises(ValueError):
            contracts.build_qualification_state_history_snapshot(payload)


def test_history_signature_projection_and_message_are_exact():
    contracts = contracts_module()
    payload = history_payload(1)
    expected_projection = {
        "schema_version": "1.0",
        "object_type": "QualificationStateHistorySnapshot",
        "provider_profile_ref": ref("a"),
        "snapshot_sequence": 1,
        "predecessor_snapshot_ref": ref("f"),
        "through_as_of_utc": "2026-09-24T00:00:00Z",
        "metadata_review_refs": [ref("b"), ref("c")],
        "requalification_event_refs": [ref("d"), ref("e")],
    }
    snapshot = contracts.build_qualification_state_history_snapshot(payload)
    assert contracts.qualification_state_history_snapshot_signed_projection(snapshot) == expected_projection
    assert snapshot["signed_payload_sha256"] == content_hash(expected_projection)
    assert contracts.qualification_state_history_snapshot_signature_message(snapshot) == (
        b"FPP_QUALIFICATION_STATE_HISTORY_SNAPSHOT_V1\x00" + canonical_json(expected_projection)
    )


def test_history_builder_rejects_wrong_signed_projection_hash():
    payload = history_payload()
    payload["signed_payload_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="signed_payload_sha256"):
        contracts_module().build_qualification_state_history_snapshot(payload)


@pytest.mark.parametrize(
    ("payload", "expected_fields"),
    [
        (valid_result_payload(), {"schema_version", "object_type", "qualification_validation_contract_ref", "qualification_validation_invocation_ref", "qualification_state_package_ref", "validation_status", "provider_profile_ref", "qualification_decision_ref", "qualification_state_history_snapshot_ref", "as_of_utc", "qualification_state", "derived_state_report_semantic_sha256", "object_id", "payload_sha256", "content_sha256"}),
        (invalid_result_payload(), {"schema_version", "object_type", "qualification_validation_contract_ref", "qualification_validation_invocation_ref", "qualification_state_package_ref", "validation_status", "primary_invalid_reason_code", "object_id", "payload_sha256", "content_sha256"}),
    ],
)
def test_python_result_builder_accepts_exact_branch_projection(payload, expected_fields):
    contracts = contracts_module()
    result = contracts.build_qualification_validation_result(payload)
    assert set(result) == expected_fields
    assert verify_sealed_object(result)
    assert contracts.validate_qualification_validation_result(result) == {
        "object_id": result["object_id"],
        "content_sha256": result["content_sha256"],
    }


@pytest.mark.parametrize(
    "payload",
    [
        {**invalid_result_payload(), "provider_profile_ref": ref("d")},
        {**valid_result_payload(), "primary_invalid_reason_code": INVALID_REASON_PRECEDENCE[0]},
        {key: value for key, value in invalid_result_payload().items() if key != "primary_invalid_reason_code"},
        {**invalid_result_payload(), "primary_invalid_reason_code": "RETRIEVAL_FAILURE"},
        {**valid_result_payload(), "qualification_state": "REHEARSAL_VERIFIED"},
    ],
)
def test_python_result_builder_rejects_cross_branch_or_open_vocabulary(payload):
    with pytest.raises(ValueError):
        contracts_module().build_qualification_validation_result(payload)


@pytest.mark.parametrize(
    ("builder_name", "validator_name", "payload", "object_type"),
    [
        ("build_qualification_validation_contract", "validate_qualification_validation_contract", contract_payload(), "QualificationValidationContract"),
        ("build_qualification_validation_invocation", "validate_qualification_validation_invocation", invocation_payload(), "QualificationValidationInvocation"),
        ("build_qualification_state_history_snapshot", "validate_qualification_state_history_snapshot", history_payload(), "QualificationStateHistorySnapshot"),
        ("build_qualification_validation_result", "validate_qualification_validation_result", valid_result_payload(), "QualificationValidationResult"),
    ],
)
def test_python_validator_rejects_standard_seal_tampering(builder_name, validator_name, payload, object_type):
    contracts = contracts_module()
    obj = getattr(contracts, builder_name)(payload)
    assert obj["object_type"] == object_type
    tampered = copy.deepcopy(obj)
    tampered["content_sha256"] = "0" * 64
    with pytest.raises(ValueError):
        getattr(contracts, validator_name)(tampered)


@pytest.mark.parametrize(
    ("filename", "builder_name", "payload"),
    [
        ("qualification_validation_contract_v1.schema.json", "build_qualification_validation_contract", contract_payload()),
        ("qualification_validation_invocation_v1.schema.json", "build_qualification_validation_invocation", invocation_payload()),
        ("qualification_state_history_snapshot_v1.schema.json", "build_qualification_state_history_snapshot", history_payload()),
        ("qualification_validation_result_v1.schema.json", "build_qualification_validation_result", valid_result_payload()),
        ("qualification_validation_result_v1.schema.json", "build_qualification_validation_result", invalid_result_payload()),
    ],
)
def test_schema_and_python_builder_agree_on_valid_objects(filename, builder_name, payload):
    obj = getattr(contracts_module(), builder_name)(payload)
    schema_validator(filename).validate(obj)


def test_history_schema_and_python_reject_noncanonical_base64():
    payload = history_payload()
    payload["authority_signature_base64"] = "abcde"
    with pytest.raises(ValidationError):
        schema_validator("qualification_state_history_snapshot_v1.schema.json").validate(
            sealed(payload, "QualificationStateHistorySnapshot")
        )
    with pytest.raises(ValueError):
        contracts_module().build_qualification_state_history_snapshot(payload)
