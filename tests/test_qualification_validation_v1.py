from __future__ import annotations

import base64
import hashlib
import importlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from forecast_trust_core.canonical import (
    canonical_json,
    content_hash,
    seal_object,
    verify_sealed_object,
)
from forecast_trust_core.qualification_validation_contracts_v1 import (
    ACCEPTED_QUALIFICATION_INPUT_ROLES,
    INVALID_REASON_PRECEDENCE,
    build_qualification_validation_contract,
    build_qualification_validation_invocation,
    qualification_state_history_snapshot_signed_projection,
    validate_qualification_validation_result,
)


def _ref(value):
    return {"object_id": value["object_id"], "content_sha256": value["content_sha256"]}


def test_expected_validation_contract_ref_is_required_without_resolver_use(
    tmp_path: Path,
):
    qualification_validation = importlib.import_module(
        "forecast_trust_core.qualification_validation_v1"
    )
    calls: list[str] = []

    def unavailable(*_args, **_kwargs):
        calls.append("called")
        raise AssertionError("resolver must not run without a trusted selector")

    result = qualification_validation.execute_qualification_validation(
        None,
        {"object_id": "invocation:test", "content_sha256": "1" * 64},
        tmp_path / "package",
        tmp_path / "evidence",
        resolve_static_object=unavailable,
        resolve_invocation=unavailable,
        resolve_package=unavailable,
        resolve_evidence_manifest=unavailable,
        qualification_authority_public_key=None,
        qualification_ed25519_build_profile=None,
        qualification_ed25519_binary=None,
    )

    assert result is None
    assert calls == []

def _sealed_static(object_type: str, name: str, **fields):
    return seal_object(
        {"schema_version": "1.0", "name": name, **fields},
        object_type=object_type,
        stable_context="qualification-validation-test",
        semantic_id=f"{object_type.lower()}:{name}:v1",
    )


def _early_pipeline_fixture(package_bytes: bytes):
    authority_key = b"k" * 32
    validator = _sealed_static("ValidatorContract", "main")
    verifier = _sealed_static(
        "RoughtimeQualificationVerifierContract",
        "qualification",
        criteria_id="FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1",
        criteria_sha256="88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e",
        validator_contract_ref=_ref(validator),
        decision_signature_projection="FPP_ROUGHTIME_QUALIFICATION_DECISION_V1",
        signature_algorithm="ED25519",
        authority_id="authority:test-only:v1",
        authority_public_key_sha256=hashlib.sha256(authority_key).hexdigest(),
        ed25519_verifier_build_profile_sha256="a" * 64,
        ed25519_verifier_binary_sha256="b" * 64,
    )
    schemas = {
        role: _sealed_static("SchemaAuthority", f"input-{index}")
        for index, role in enumerate(ACCEPTED_QUALIFICATION_INPUT_ROLES)
    }
    invocation_schema = _sealed_static("SchemaAuthority", "invocation")
    package_schema = _sealed_static("SchemaAuthority", "package")
    history_schema = _sealed_static("SchemaAuthority", "history")
    report_schema = _sealed_static("SchemaAuthority", "report")
    result_schema = _sealed_static("SchemaAuthority", "result")
    contract = build_qualification_validation_contract(
        {
            "schema_version": "1.0",
            "object_role": "NORMATIVE",
            "qualification_integration_semantics_id": "FPP_QUALIFICATION_VALIDATION_INTEGRATION_V1",
            "qualification_state_derivation_semantics_id": "FPP_ROUGHTIME_QUALIFICATION_STATE_DERIVATION_V1",
            "validator_contract_ref": _ref(validator),
            "roughtime_qualification_verifier_contract_ref": _ref(verifier),
            "accepted_qualification_input_schema_refs": [
                {"role": role, "schema_ref": _ref(schemas[role])}
                for role in ACCEPTED_QUALIFICATION_INPUT_ROLES
            ],
            "qualification_validation_invocation_schema_ref": _ref(invocation_schema),
            "dynamic_qualification_state_package_v2_schema_ref": _ref(package_schema),
            "dynamic_qualification_state_package_v2_role_semantics_id": "FPP_DYNAMIC_QUALIFICATION_STATE_PACKAGE_ROLE_SEMANTICS_V2",
            "dynamic_qualification_state_package_v2_member_closure_semantics_id": "FPP_DYNAMIC_QUALIFICATION_STATE_PACKAGE_MEMBER_CLOSURE_V2",
            "qualification_state_history_snapshot_schema_ref": _ref(history_schema),
            "qualification_state_history_completeness_semantics_id": "FPP_QUALIFICATION_STATE_HISTORY_COMPLETENESS_V1",
            "qualification_state_history_succession_semantics_id": "FPP_QUALIFICATION_STATE_HISTORY_SUCCESSION_V1",
            "qualification_state_history_snapshot_signature_projection": "FPP_QUALIFICATION_STATE_HISTORY_SNAPSHOT_V1",
            "qualification_state_history_snapshot_signer_semantics_id": "FPP_HISTORY_SIGNER_SAME_AS_QUALIFICATION_AUTHORITY_V1",
            "state_report_schema_ref": _ref(report_schema),
            "state_report_semantic_hash_projection": "SHA256_FPP_JCS_1_EXCLUDING_REPORT_SHA256",
            "qualification_validation_result_schema_ref": _ref(result_schema),
            "invalid_reason_vocabulary_id": "FPP_QUALIFICATION_VALIDATION_INVALID_REASON_V1",
            "invalid_reason_precedence": list(INVALID_REASON_PRECEDENCE),
            "no_authoritative_result_semantics_id": "FPP_QUALIFICATION_NO_AUTHORITATIVE_RESULT_V1",
            "strict_json_profile": "FPP_STRICT_JSON_1",
            "canonicalization_profile": "FPP_JCS_1",
            "inclusive_cutoff_semantics_id": "FPP_INCLUSIVE_CUTOFF_V1",
        }
    )
    package_ref = {
        "object_id": "dynamicqualificationstatepackage:v2:fixture",
        "content_sha256": "f" * 64,
    }
    invocation = build_qualification_validation_invocation(
        {
            "schema_version": "1.0",
            "qualification_validation_contract_ref": _ref(contract),
            "qualification_state_package_ref": package_ref,
            "qualification_state_package_serialized_sha256": hashlib.sha256(
                package_bytes
            ).hexdigest(),
        }
    )
    static_values = [
        contract,
        validator,
        verifier,
        *schemas.values(),
        invocation_schema,
        package_schema,
        history_schema,
        report_schema,
        result_schema,
    ]
    static_by_ref = {
        (value["object_id"], value["content_sha256"]): canonical_json(value)
        for value in static_values
    }

    def resolve_static(ref):
        return static_by_ref[(ref["object_id"], ref["content_sha256"])]

    def resolve_invocation(ref):
        assert dict(ref) == _ref(invocation)
        return canonical_json(invocation)

    return {
        "authority_key": authority_key,
        "contract": contract,
        "invocation": invocation,
        "package_ref": package_ref,
        "resolve_static": resolve_static,
        "resolve_invocation": resolve_invocation,
        "resolve_package": lambda ref: package_bytes
        if dict(ref) == package_ref
        else (_ for _ in ()).throw(KeyError(ref)),
    }


def test_authenticated_malformed_package_json_seals_strict_json_invalid(
    tmp_path: Path,
):
    qualification_validation = importlib.import_module(
        "forecast_trust_core.qualification_validation_v1"
    )
    fixture = _early_pipeline_fixture(b"{")

    result = qualification_validation.execute_qualification_validation(
        _ref(fixture["contract"]),
        _ref(fixture["invocation"]),
        tmp_path / "package",
        tmp_path / "evidence",
        resolve_static_object=fixture["resolve_static"],
        resolve_invocation=fixture["resolve_invocation"],
        resolve_package=fixture["resolve_package"],
        resolve_evidence_manifest=lambda _digest: (_ for _ in ()).throw(
            AssertionError("evidence is later than package strict JSON")
        ),
        qualification_authority_public_key=fixture["authority_key"],
        qualification_ed25519_build_profile={"profile_sha256": "a" * 64, "binary_sha256": "b" * 64},
        qualification_ed25519_binary=tmp_path / "verifier",
    )

    assert result["validation_status"] == "INVALID"
    assert result["primary_invalid_reason_code"] == "PACKAGE_STRICT_JSON_INVALID"
    assert result["qualification_validation_contract_ref"] == _ref(fixture["contract"])
    assert result["qualification_validation_invocation_ref"] == _ref(fixture["invocation"])
    assert result["qualification_state_package_ref"] == fixture["package_ref"]
    assert set(result) == {
        "schema_version",
        "object_type",
        "qualification_validation_contract_ref",
        "qualification_validation_invocation_ref",
        "qualification_state_package_ref",
        "validation_status",
        "primary_invalid_reason_code",
        "object_id",
        "payload_sha256",
        "content_sha256",
    }
    assert verify_sealed_object(result)
    assert validate_qualification_validation_result(result) == _ref(result)

def _execute_early(fixture, tmp_path: Path, **overrides):
    qualification_validation = importlib.import_module(
        "forecast_trust_core.qualification_validation_v1"
    )
    arguments = {
        "resolve_static_object": fixture["resolve_static"],
        "resolve_invocation": fixture["resolve_invocation"],
        "resolve_package": fixture["resolve_package"],
        "resolve_evidence_manifest": lambda _digest: (_ for _ in ()).throw(
            AssertionError("evidence resolver must not run in an early-stage test")
        ),
        "qualification_authority_public_key": fixture["authority_key"],
        "qualification_ed25519_build_profile": None,
        "qualification_ed25519_binary": None,
    }
    arguments.update(overrides)
    return qualification_validation.execute_qualification_validation(
        _ref(fixture["contract"]),
        _ref(fixture["invocation"]),
        tmp_path / "package",
        tmp_path / "evidence",
        **arguments,
    )


def test_missing_static_dependency_produces_no_authoritative_result(tmp_path: Path):
    fixture = _early_pipeline_fixture(canonical_json({}))

    def missing_verifier(ref):
        if ref == fixture["contract"]["roughtime_qualification_verifier_contract_ref"]:
            raise FileNotFoundError
        return fixture["resolve_static"](ref)

    assert (
        _execute_early(
            fixture,
            tmp_path,
            resolve_static_object=missing_verifier,
        )
        is None
    )


def test_package_serialized_digest_mismatch_produces_no_authoritative_result(
    tmp_path: Path,
):
    fixture = _early_pipeline_fixture(canonical_json({}))
    assert (
        _execute_early(
            fixture,
            tmp_path,
            resolve_package=lambda _ref: b"different authenticated candidate",
        )
        is None
    )


def test_invocation_contract_mismatch_produces_no_authoritative_result(
    tmp_path: Path,
):
    fixture = _early_pipeline_fixture(canonical_json({}))
    payload = {
        key: value
        for key, value in fixture["invocation"].items()
        if key
        not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload["qualification_validation_contract_ref"] = {
        "object_id": "qualificationvalidationcontract:other",
        "content_sha256": "0" * 64,
    }
    invocation = build_qualification_validation_invocation(payload)

    assert (
        _execute_early(
            fixture,
            tmp_path,
            resolve_invocation=lambda _ref: canonical_json(invocation),
        )
        is None
    )


@pytest.mark.parametrize(
    "stage",
    [
        "PACKAGE_SCHEMA_INVALID",
        "PACKAGE_SEALED_IDENTITY_OR_REFERENCE_INVALID",
        "PACKAGE_MEMBER_MANIFEST_INVALID",
        "PACKAGE_MEMBER_CLOSURE_INVALID",
        "QUALIFICATION_INPUT_SCHEMA_INVALID",
        "STATE_REPORT_MEMBER_INVALID",
    ],
)
def test_phase4d_typed_prehistory_failure_maps_without_message_parsing(
    tmp_path: Path,
    monkeypatch,
    stage: str,
):
    qualification_validation = importlib.import_module(
        "forecast_trust_core.qualification_validation_v1"
    )
    package_v2 = importlib.import_module(
        "forecast_trust_core.qualification_state_package_v2"
    )
    fixture = _early_pipeline_fixture(canonical_json({}))

    def fail_closure(*_args, **_kwargs):
        raise package_v2.QualificationStatePackageError(
            "deliberately unrelated diagnostic wording",
            stage=package_v2.QualificationStatePackageStage(stage),
        )

    monkeypatch.setattr(
        qualification_validation,
        "build_package_closure",
        fail_closure,
    )

    result = _execute_early(fixture, tmp_path)

    assert result["validation_status"] == "INVALID"
    assert result["primary_invalid_reason_code"] == stage
    assert validate_qualification_validation_result(result) == _ref(result)


class _VerifierOutcome:
    def __init__(self, outcome=True, error: Exception | None = None):
        self.outcome = outcome
        self.error = error

    def __call__(self, *_args):
        if self.error is not None:
            raise self.error
        return self.outcome


def _state_report(state: str):
    core = {
        "schema_version": "1.0",
        "object_type": "RoughtimeQualificationStateReport",
        "provider_id": "roughtime.se",
        "as_of_utc": "2026-09-20T00:00:00Z",
        "state": state,
        "reason_codes": [f"TEST_{state}"],
        "decision_ref": {
            "object_id": "decision:test",
            "content_sha256": "d" * 64,
        },
        "review_ref": {
            "object_id": "review:test",
            "content_sha256": "e" * 64,
        },
        "latest_metadata_review_ref": {
            "object_id": "metadata:test",
            "content_sha256": "a" * 64,
        },
        "active_requalification_event_refs": [],
    }
    return {**core, "report_sha256": content_hash(core)}


def _late_pipeline_fixture(
    package_bytes: bytes = canonical_json({}),
    *,
    evidence_bytes: bytes | None = None,
):
    fixture = _early_pipeline_fixture(package_bytes)
    manifest_bytes = evidence_bytes or canonical_json(
        {
            "schema_version": "1.0",
            "object_type": "RoughtimeQualificationEvidenceManifest",
        }
    )
    evidence_selector = hashlib.sha256(manifest_bytes).hexdigest()
    metadata = {
        "object_id": "metadata:test",
        "content_sha256": "a" * 64,
        "reviewed_at": "2026-09-18T00:00:00Z",
    }
    history_payload = {
        "schema_version": "1.0",
        "provider_profile_ref": {
            "object_id": "profile:test",
            "content_sha256": "b" * 64,
        },
        "snapshot_sequence": 0,
        "through_as_of_utc": "2026-09-20T00:00:00Z",
        "metadata_review_refs": [_ref(metadata)],
        "requalification_event_refs": [],
        "authority_signature_base64": base64.b64encode(b"H" * 64).decode("ascii"),
    }
    projection = qualification_state_history_snapshot_signed_projection(
        history_payload
    )
    history_payload["signed_payload_sha256"] = content_hash(projection)
    history = seal_object(
        history_payload,
        object_type="QualificationStateHistorySnapshot",
        stable_context="v1",
    )
    decision = {
        "signed_payload": {
            "evidence_manifest_sha256": evidence_selector,
            "metadata_review_ref": _ref(metadata),
        }
    }
    review = {
        "evidence_manifest_sha256": evidence_selector,
        "verifier_build_profile_sha256": "c" * 64,
        "metadata_review_ref": _ref(metadata),
    }
    report = _state_report("PRODUCTION_QUALIFIED")
    closure = SimpleNamespace(
        package_ref=fixture["package_ref"],
        parsed_package={},
        typed_exact_ref_member_map={
            (metadata["object_id"], metadata["content_sha256"]): (
                "RoughtimeProviderMetadataReview",
                metadata,
                "metadata.json",
            ),
            (history["object_id"], history["content_sha256"]): (
                "QualificationStateHistorySnapshot",
                history,
                "history.json",
            ),
        },
        provider_profile={"provider_id": "roughtime.se"},
        provider_profile_ref=history["provider_profile_ref"],
        qualification_decision=decision,
        qualification_decision_ref={
            "object_id": "decision:test",
            "content_sha256": "d" * 64,
        },
        qualification_review=review,
        qualification_review_ref={
            "object_id": "review:test",
            "content_sha256": "e" * 64,
        },
        selected_history_snapshot=history,
        selected_history_snapshot_ref=_ref(history),
        ordered_history_snapshot_chain=(history,),
        metadata_reviews=(metadata,),
        requalification_events=(),
        state_report=report,
        state_report_member_sha256=report["report_sha256"],
        as_of_utc="2026-09-20T00:00:00Z",
        history_predecessor_cycle=False,
    )
    fixture.update({"closure": closure, "evidence_bytes": manifest_bytes})
    return fixture


def _execute_late(
    fixture,
    tmp_path: Path,
    monkeypatch,
    *,
    verifier_outcome=True,
    verifier_error: Exception | None = None,
    derived_state: str = "PRODUCTION_QUALIFIED",
    resolve_evidence_manifest=None,
):
    qualification_validation = importlib.import_module(
        "forecast_trust_core.qualification_validation_v1"
    )
    verifier = qualification_validation._ConclusiveSignatureVerifier(
        _VerifierOutcome(verifier_outcome, verifier_error)
    )
    monkeypatch.setattr(
        qualification_validation,
        "build_package_closure",
        lambda *_args, **_kwargs: fixture["closure"],
    )
    monkeypatch.setattr(
        qualification_validation,
        "_prepare_signature_verifier",
        lambda *_args, **_kwargs: (
            "authority:test-only:v1",
            fixture["authority_key"],
            verifier,
        ),
    )
    monkeypatch.setattr(
        qualification_validation,
        "_resolve_roughtime_build_profile",
        lambda *_args, **_kwargs: {},
    )
    monkeypatch.setattr(
        qualification_validation, "_validate_evidence", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        qualification_validation, "_validate_authority", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        qualification_validation,
        "_derive_state_report",
        lambda *_args, **_kwargs: _state_report(derived_state),
    )
    fixture["closure"].state_report = _state_report(derived_state)
    return _execute_early(
        fixture,
        tmp_path,
        resolve_evidence_manifest=(
            resolve_evidence_manifest
            or (lambda _digest: fixture["evidence_bytes"])
        ),
        qualification_authority_public_key=fixture["authority_key"],
        qualification_ed25519_build_profile={},
        qualification_ed25519_binary=tmp_path / "synthetic-verifier",
    )


@pytest.mark.parametrize(
    "state",
    [
        "QUALIFICATION_BLOCKED",
        "QUALIFICATION_EXPIRED",
        "REQUALIFICATION_REQUIRED",
        "PRODUCTION_QUALIFIED",
    ],
)
def test_all_four_recomputed_states_produce_exact_valid_result(
    tmp_path: Path,
    monkeypatch,
    state: str,
):
    fixture = _late_pipeline_fixture()
    result = _execute_late(
        fixture, tmp_path, monkeypatch, derived_state=state
    )

    assert result["validation_status"] == "VALID"
    assert result["qualification_state"] == state
    assert result["derived_state_report_semantic_sha256"] == content_hash(
        {
            key: value
            for key, value in _state_report(state).items()
            if key != "report_sha256"
        }
    )
    assert set(result) == {
        "schema_version",
        "object_type",
        "qualification_validation_contract_ref",
        "qualification_validation_invocation_ref",
        "qualification_state_package_ref",
        "validation_status",
        "provider_profile_ref",
        "qualification_decision_ref",
        "qualification_state_history_snapshot_ref",
        "as_of_utc",
        "qualification_state",
        "derived_state_report_semantic_sha256",
        "object_id",
        "payload_sha256",
        "content_sha256",
    }
    assert validate_qualification_validation_result(result) == _ref(result)


def test_false_history_signature_precedes_later_failures(tmp_path: Path, monkeypatch):
    fixture = _late_pipeline_fixture()
    result = _execute_late(
        fixture,
        tmp_path,
        monkeypatch,
        verifier_outcome=False,
        resolve_evidence_manifest=lambda _digest: (_ for _ in ()).throw(
            AssertionError("history authentication precedes evidence")
        ),
    )
    assert result["primary_invalid_reason_code"] == (
        "HISTORY_SNAPSHOT_AUTHENTICATION_INVALID"
    )


def test_history_verifier_exception_produces_no_authoritative_result(
    tmp_path: Path,
    monkeypatch,
):
    fixture = _late_pipeline_fixture()
    assert (
        _execute_late(
            fixture,
            tmp_path,
            monkeypatch,
            verifier_error=TimeoutError("indeterminate verifier"),
        )
        is None
    )


@pytest.mark.parametrize(
    ("target", "reason"),
    [
        ("validate_history_cutoff", "HISTORY_CUTOFF_INVALID"),
        ("validate_history_succession", "HISTORY_SUCCESSION_INVALID"),
        ("validate_history_completeness", "HISTORY_COMPLETENESS_INVALID"),
    ],
)
def test_history_structural_stage_mapping(
    tmp_path: Path,
    monkeypatch,
    target: str,
    reason: str,
):
    qualification_validation = importlib.import_module(
        "forecast_trust_core.qualification_validation_v1"
    )
    package_v2 = importlib.import_module(
        "forecast_trust_core.qualification_state_package_v2"
    )
    fixture = _late_pipeline_fixture()

    def fail(_closure):
        raise package_v2.QualificationStatePackageError(
            "diagnostic text is non-authoritative",
            stage=package_v2.QualificationStatePackageStage(reason),
        )

    monkeypatch.setattr(qualification_validation, target, fail)
    result = _execute_late(fixture, tmp_path, monkeypatch)
    assert result["primary_invalid_reason_code"] == reason


def test_cutoff_failure_wins_before_succession_and_completeness(
    tmp_path: Path,
    monkeypatch,
):
    qualification_validation = importlib.import_module(
        "forecast_trust_core.qualification_validation_v1"
    )
    package_v2 = importlib.import_module(
        "forecast_trust_core.qualification_state_package_v2"
    )
    fixture = _late_pipeline_fixture()
    later_calls: list[str] = []

    def cutoff(_closure):
        raise package_v2.QualificationStatePackageError(
            "cutoff",
            stage=package_v2.QualificationStatePackageStage.HISTORY_CUTOFF_INVALID,
        )

    monkeypatch.setattr(qualification_validation, "validate_history_cutoff", cutoff)
    monkeypatch.setattr(
        qualification_validation,
        "validate_history_succession",
        lambda _closure: later_calls.append("succession"),
    )
    monkeypatch.setattr(
        qualification_validation,
        "validate_history_completeness",
        lambda _closure: later_calls.append("completeness"),
    )
    result = _execute_late(fixture, tmp_path, monkeypatch)

    assert result["primary_invalid_reason_code"] == "HISTORY_CUTOFF_INVALID"
    assert later_calls == []


def test_public_key_unavailable_produces_no_authoritative_result(
    tmp_path: Path,
    monkeypatch,
):
    qualification_validation = importlib.import_module(
        "forecast_trust_core.qualification_validation_v1"
    )
    fixture = _late_pipeline_fixture()
    monkeypatch.setattr(
        qualification_validation,
        "build_package_closure",
        lambda *_args, **_kwargs: fixture["closure"],
    )

    assert (
        _execute_early(
            fixture,
            tmp_path,
            resolve_evidence_manifest=lambda _digest: fixture["evidence_bytes"],
            qualification_authority_public_key=None,
            qualification_ed25519_build_profile={},
            qualification_ed25519_binary=tmp_path / "synthetic-verifier",
        )
        is None
    )


def test_evidence_unavailable_and_wrong_content_address_produce_no_result(
    tmp_path: Path,
    monkeypatch,
):
    resolvers = (
        lambda _digest: (_ for _ in ()).throw(FileNotFoundError()),
        lambda _digest: b"wrong candidate bytes",
    )
    for resolver in resolvers:
        fixture = _late_pipeline_fixture()
        assert (
            _execute_late(
                fixture,
                tmp_path,
                monkeypatch,
                resolve_evidence_manifest=resolver,
            )
            is None
        )


def test_authenticated_malformed_evidence_manifest_is_invalid(
    tmp_path: Path,
    monkeypatch,
):
    fixture = _late_pipeline_fixture(evidence_bytes=b"{")
    result = _execute_late(fixture, tmp_path, monkeypatch)
    assert result["primary_invalid_reason_code"] == (
        "QUALIFICATION_EVIDENCE_PACKAGE_INVALID"
    )


@pytest.mark.parametrize(
    "reason",
    [
        "QUALIFICATION_EVIDENCE_PACKAGE_INVALID",
        "QUALIFICATION_AUTHORITY_CHAIN_INVALID",
        "QUALIFICATION_STATE_DERIVATION_INVALID",
    ],
)
def test_late_deterministic_stage_maps_to_single_invalid_reason(
    tmp_path: Path,
    monkeypatch,
    reason: str,
):
    qualification_validation = importlib.import_module(
        "forecast_trust_core.qualification_validation_v1"
    )
    fixture = _late_pipeline_fixture()
    target = {
        "QUALIFICATION_EVIDENCE_PACKAGE_INVALID": "_validate_evidence",
        "QUALIFICATION_AUTHORITY_CHAIN_INVALID": "_validate_authority",
        "QUALIFICATION_STATE_DERIVATION_INVALID": "_derive_state_report",
    }[reason]
    _execute_late(fixture, tmp_path, monkeypatch)

    def fail(*_args, **_kwargs):
        raise qualification_validation._DeterministicInvalid(reason)

    monkeypatch.setattr(qualification_validation, target, fail)
    result = _execute_early(
        fixture,
        tmp_path,
        resolve_evidence_manifest=lambda _digest: fixture["evidence_bytes"],
        qualification_authority_public_key=fixture["authority_key"],
        qualification_ed25519_build_profile={},
        qualification_ed25519_binary=tmp_path / "synthetic-verifier",
    )

    assert result["validation_status"] == "INVALID"
    assert result["primary_invalid_reason_code"] == reason
    assert "provider_profile_ref" not in result
    assert set(result) == {
        "schema_version",
        "object_type",
        "qualification_validation_contract_ref",
        "qualification_validation_invocation_ref",
        "qualification_state_package_ref",
        "validation_status",
        "primary_invalid_reason_code",
        "object_id",
        "payload_sha256",
        "content_sha256",
    }


def test_unexpected_derivation_exception_produces_no_authoritative_result(
    tmp_path: Path,
    monkeypatch,
):
    qualification_validation = importlib.import_module(
        "forecast_trust_core.qualification_validation_v1"
    )
    fixture = _late_pipeline_fixture()
    _execute_late(fixture, tmp_path, monkeypatch)
    monkeypatch.setattr(
        qualification_validation,
        "_derive_state_report",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("unexpected implementation failure")
        ),
    )

    assert (
        _execute_early(
            fixture,
            tmp_path,
            resolve_evidence_manifest=lambda _digest: fixture["evidence_bytes"],
            qualification_authority_public_key=fixture["authority_key"],
            qualification_ed25519_build_profile={},
            qualification_ed25519_binary=tmp_path / "synthetic-verifier",
        )
        is None
    )


def test_complete_object_mismatch_fails_even_if_report_hash_field_matches(
    tmp_path: Path,
    monkeypatch,
):
    qualification_validation = importlib.import_module(
        "forecast_trust_core.qualification_validation_v1"
    )
    fixture = _late_pipeline_fixture()
    _execute_late(fixture, tmp_path, monkeypatch)
    recomputed = _state_report("PRODUCTION_QUALIFIED")
    supplied = dict(recomputed)
    supplied["reason_codes"] = ["DIFFERENT_CONTENT_WITH_SAME_HASH_FIELD"]
    fixture["closure"].state_report = supplied
    monkeypatch.setattr(
        qualification_validation,
        "_derive_state_report",
        lambda *_args, **_kwargs: recomputed,
    )

    result = _execute_early(
        fixture,
        tmp_path,
        resolve_evidence_manifest=lambda _digest: fixture["evidence_bytes"],
        qualification_authority_public_key=fixture["authority_key"],
        qualification_ed25519_build_profile={},
        qualification_ed25519_binary=tmp_path / "synthetic-verifier",
    )
    assert result["primary_invalid_reason_code"] == "STATE_REPORT_SEMANTIC_MISMATCH"


def test_static_wrong_requested_identity_and_invocation_auth_failure_are_no_result(
    tmp_path: Path,
):
    fixture = _early_pipeline_fixture(canonical_json({}))
    wrong_static = canonical_json(fixture["contract"])

    assert (
        _execute_early(
            fixture,
            tmp_path,
            resolve_static_object=lambda _ref: wrong_static,
        )
        is None
    )
    assert (
        _execute_early(
            fixture,
            tmp_path,
            resolve_invocation=lambda _ref: b"{}",
        )
        is None
    )


def test_unstable_package_read_produces_no_authoritative_result(tmp_path: Path):
    fixture = _early_pipeline_fixture(canonical_json({}))
    assert (
        _execute_early(
            fixture,
            tmp_path,
            resolve_package=lambda _ref: (_ for _ in ()).throw(
                OSError("unstable read")
            ),
        )
        is None
    )


def test_roughtime_build_profile_is_discovered_from_evidence_artifacts(
    tmp_path: Path,
    monkeypatch,
):
    qualification_validation = importlib.import_module(
        "forecast_trust_core.qualification_validation_v1"
    )
    profile = {"profile_sha256": "c" * 64, "binary_sha256": "d" * 64}
    monkeypatch.setattr(
        qualification_validation,
        "collect_manifest_artifacts",
        lambda *_args, **_kwargs: {
            "profile.json": canonical_json(profile),
            "noise.json": canonical_json({"not": "a build profile"}),
        },
    )

    def validate(candidate):
        if candidate != profile:
            raise ValueError("not a build profile")
        return candidate["profile_sha256"]

    monkeypatch.setattr(
        qualification_validation,
        "validate_roughtime_verifier_build_profile",
        validate,
    )

    assert qualification_validation._resolve_roughtime_build_profile(
        tmp_path,
        "manifest.json",
        profile["profile_sha256"],
    ) == profile


def test_missing_authenticated_roughtime_build_profile_is_evidence_invalid(
    tmp_path: Path,
    monkeypatch,
):
    qualification_validation = importlib.import_module(
        "forecast_trust_core.qualification_validation_v1"
    )
    monkeypatch.setattr(
        qualification_validation,
        "collect_manifest_artifacts",
        lambda *_args, **_kwargs: {"noise.json": canonical_json({"noise": True})},
    )
    monkeypatch.setattr(
        qualification_validation,
        "validate_roughtime_verifier_build_profile",
        lambda _candidate: (_ for _ in ()).throw(ValueError("not a profile")),
    )

    with pytest.raises(qualification_validation._DeterministicInvalid) as captured:
        qualification_validation._resolve_roughtime_build_profile(
            tmp_path,
            "manifest.json",
            "c" * 64,
        )
    assert captured.value.reason == "QUALIFICATION_EVIDENCE_PACKAGE_INVALID"
