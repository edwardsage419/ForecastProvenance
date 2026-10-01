from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
SHA_A = "a" * 64
SHA_B = "b" * 64


def exact_ref(name: str) -> dict[str, str]:
    return {"object_id": f"{name}:v1", "content_sha256": SHA_A}


def sealed_identity(object_type: str) -> dict[str, str]:
    return {
        "object_type": object_type,
        "schema_version": "1.0",
        "object_id": f"{object_type.lower()}:v1:test",
        "payload_sha256": SHA_A,
        "content_sha256": SHA_B,
    }


def role_binding(role_id: str) -> dict[str, object]:
    return {
        "role_id": role_id,
        "object_type": "ExampleObject",
        "schema_version": "1.0",
        "schema_ref": exact_ref(f"schema:{role_id}"),
    }


def validator_contract() -> dict[str, object]:
    return {
        **sealed_identity("ValidatorContract"),
        "contract_version": "1.0.0",
        "authority_scope": "STRUCTURAL_VALIDATION_ONLY",
        "component_contract_refs": [exact_ref("component:validator")],
        "operation_registry_ref": exact_ref("registry:validator"),
        "implementation_binding_ref": exact_ref("binding:validator"),
        "test_contract_ref": exact_ref("tests:validator"),
        "runtime_profile_ref": exact_ref("runtime:validator"),
    }


def component_contract() -> dict[str, object]:
    return {
        **sealed_identity("ComponentContract"),
        "component_role": "claim_validator",
        "contract_version": "1.0.0",
        "operation_ids": ["validate_claim", "project_claim"],
        "input_role_bindings": [role_binding("claim_input")],
        "output_role_bindings": [role_binding("validation_output")],
        "failure_vocabulary_ref": exact_ref("vocabulary:failure"),
        "failure_precedence": ["PARSE_FAILURE", "SCHEMA_FAILURE"],
        "determinism_requirement": "DETERMINISTIC_FOR_IDENTICAL_INPUTS",
    }


def operation_registry() -> dict[str, object]:
    return {
        **sealed_identity("OperationRegistry"),
        "registry_version": "1.0.0",
        "operations": [
            {
                "operation_id": "validate_claim",
                "owning_component_role": "claim_validator",
                "input_role_bindings": [role_binding("claim_input")],
                "output_role_bindings": [role_binding("validation_output")],
                "implementation_entrypoint_id": "validate_claim_v1",
                "failure_vocabulary_ref": exact_ref("vocabulary:failure"),
                "determinism_requirement": "DETERMINISTIC_FOR_IDENTICAL_INPUTS",
            }
        ],
    }


def implementation_binding() -> dict[str, object]:
    return {
        **sealed_identity("ImplementationBinding"),
        "binding_version": "1.0.0",
        "source_file_manifest_ref": exact_ref("manifest:source"),
        "package_artifact_ref": exact_ref("artifact:package"),
        "dependency_lock_ref": exact_ref("lock:dependencies"),
        "runtime_profile_ref": exact_ref("runtime:validator"),
        "entrypoint_bindings": [
            {
                "operation_id": "validate_claim",
                "logical_entrypoint_id": "validate_claim_v1",
                "source_unit_ref": exact_ref("source:validator"),
                "symbol": "forecast_trust_core.claims.validate_claim",
            }
        ],
    }


def build_test_contract() -> dict[str, object]:
    return {
        **sealed_identity("TestContract"),
        "test_contract_version": "1.0.0",
        "fixture_refs": [exact_ref("fixture:valid-claim")],
        "command_declarations": [
            {
                "command_id": "focused_contract_tests",
                "argv": ["pytest", "tests/test_claims.py"],
            }
        ],
        "runtime_profile_ref": exact_ref("runtime:validator"),
        "operation_coverage": [
            {
                "operation_id": "validate_claim",
                "command_ids": ["focused_contract_tests"],
            }
        ],
        "expected_result_vocabulary": ["PASS", "FAIL"],
        "projection_profile_ref": exact_ref("projection:test-result"),
    }


def runtime_profile() -> dict[str, object]:
    return {
        **sealed_identity("RuntimeProfile"),
        "runtime_profile_version": "1.0.0",
        "runtime_identity": {
            "runtime_name": "cpython",
            "runtime_version": "3.11.9",
        },
        "execution_engine": {
            "engine_id": "cpython-3.11",
            "executable_sha256": SHA_A,
        },
        "dependency_environment": {
            "dependency_lock_ref": exact_ref("lock:dependencies"),
            "environment_variables": [
                {"name": "PYTHONHASHSEED", "value": "0"}
            ],
        },
        "platform_constraints": ["linux", "x86_64"],
        "deterministic_settings": [
            {"setting_id": "network_access", "value": False},
            {"setting_id": "timezone", "value": "UTC"},
        ],
    }


SCHEMA_CASES = [
    ("validator_contract_v1.schema.json", "ValidatorContract", validator_contract),
    ("component_contract_v1.schema.json", "ComponentContract", component_contract),
    ("operation_registry_v1.schema.json", "OperationRegistry", operation_registry),
    ("implementation_binding_v1.schema.json", "ImplementationBinding", implementation_binding),
    ("test_contract_v1.schema.json", "TestContract", build_test_contract),
    ("runtime_profile_v1.schema.json", "RuntimeProfile", runtime_profile),
]


def load_schema(filename: str) -> dict[str, object]:
    path = SCHEMAS / filename
    assert path.is_file(), f"missing normative schema: {filename}"
    return json.loads(path.read_text(encoding="utf-8"))


def validator(filename: str) -> Draft202012Validator:
    schema = load_schema(filename)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.mark.parametrize(("filename", "object_type", "payload_factory"), SCHEMA_CASES)
def test_schema_is_draft_2020_12_and_accepts_minimal_object(
    filename: str, object_type: str, payload_factory
):
    schema = load_schema(filename)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == f"https://forecastprovenance.org/schemas/{filename}"
    Draft202012Validator.check_schema(schema)
    validator(filename).validate(payload_factory())


@pytest.mark.parametrize(("filename", "_object_type", "payload_factory"), SCHEMA_CASES)
def test_schema_rejects_every_missing_required_field(
    filename: str, _object_type: str, payload_factory
):
    schema_validator = validator(filename)
    payload = payload_factory()
    for field in tuple(payload):
        missing = copy.deepcopy(payload)
        missing.pop(field)
        with pytest.raises(ValidationError, match="is a required property"):
            schema_validator.validate(missing)


@pytest.mark.parametrize(("filename", "_object_type", "payload_factory"), SCHEMA_CASES)
def test_schema_rejects_additional_properties_and_nulls(
    filename: str, _object_type: str, payload_factory
):
    schema_validator = validator(filename)
    extra = payload_factory()
    extra["unexpected"] = "value"
    with pytest.raises(ValidationError):
        schema_validator.validate(extra)

    for field in tuple(payload_factory()):
        null_value = payload_factory()
        null_value[field] = None
        with pytest.raises(ValidationError):
            schema_validator.validate(null_value)


@pytest.mark.parametrize(("filename", "object_type", "payload_factory"), SCHEMA_CASES)
def test_schema_rejects_wrong_object_type_and_schema_version(
    filename: str, object_type: str, payload_factory
):
    schema_validator = validator(filename)
    for field, bad_value in (
        ("object_type", f"Not{object_type}"),
        ("schema_version", "2.0"),
    ):
        invalid = payload_factory()
        invalid[field] = bad_value
        with pytest.raises(ValidationError):
            schema_validator.validate(invalid)


@pytest.mark.parametrize(("filename", "_object_type", "payload_factory"), SCHEMA_CASES)
def test_schema_rejects_malformed_identity_sha256(
    filename: str, _object_type: str, payload_factory
):
    schema_validator = validator(filename)
    for field in ("payload_sha256", "content_sha256"):
        invalid = payload_factory()
        invalid[field] = "A" * 64
        with pytest.raises(ValidationError):
            schema_validator.validate(invalid)


@pytest.mark.parametrize(
    ("filename", "payload_factory", "ref_path"),
    [
        ("validator_contract_v1.schema.json", validator_contract, ("operation_registry_ref",)),
        ("component_contract_v1.schema.json", component_contract, ("failure_vocabulary_ref",)),
        (
            "operation_registry_v1.schema.json",
            operation_registry,
            ("operations", 0, "failure_vocabulary_ref"),
        ),
        ("implementation_binding_v1.schema.json", implementation_binding, ("package_artifact_ref",)),
        ("test_contract_v1.schema.json", build_test_contract, ("projection_profile_ref",)),
        (
            "runtime_profile_v1.schema.json",
            runtime_profile,
            ("dependency_environment", "dependency_lock_ref"),
        ),
    ],
)
def test_exact_ref_shape_is_sealed_and_hash_checked(filename, payload_factory, ref_path):
    schema_validator = validator(filename)

    def selected(payload):
        value = payload
        for part in ref_path:
            value = value[part]
        return value

    for mutation in (
        lambda ref: ref.pop("object_id"),
        lambda ref: ref.__setitem__("extra", "value"),
        lambda ref: ref.__setitem__("content_sha256", "not-a-sha256"),
        lambda ref: ref.__setitem__("content_sha256", None),
    ):
        invalid = payload_factory()
        mutation(selected(invalid))
        with pytest.raises(ValidationError):
            schema_validator.validate(invalid)


FORBIDDEN_AUTHORITY_FIELDS = (
    "signing_authority",
    "anchoring_authority",
    "genesis_authorization",
    "production_qualification",
)


@pytest.mark.parametrize(("filename", "_object_type", "payload_factory"), SCHEMA_CASES)
def test_schema_rejects_authority_escalation_fields(
    filename: str, _object_type: str, payload_factory
):
    schema_validator = validator(filename)
    for forbidden_field in FORBIDDEN_AUTHORITY_FIELDS:
        invalid = payload_factory()
        invalid[forbidden_field] = True
        with pytest.raises(ValidationError):
            schema_validator.validate(invalid)


def test_ordered_arrays_are_validated_without_mutation_or_sorting():
    component = component_contract()
    component["operation_ids"] = ["z_operation", "a_operation"]
    before = copy.deepcopy(component)
    validator("component_contract_v1.schema.json").validate(component)
    assert component == before
    assert component["operation_ids"] == ["z_operation", "a_operation"]

