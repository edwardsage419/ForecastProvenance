from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from forecast_trust_core import genesis_contracts_v1 as contracts
from forecast_trust_core.canonical import seal_object, verify_sealed_object
from forecast_trust_core.genesis_contracts_v1 import (
    ContractViolation,
    reconstruct_forecast_slot,
    reconstruct_issuance_cycle_manifest,
    reconstruct_issuance_cycle_plan,
    reconstruct_schedule_derivation_evidence,
    reconstruct_target_instance,
    require_schedule_derivation_authority,
)


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="genesis-runtime-contract-test",
        semantic_id=object_id,
    )


def sorted_refs(*objects):
    return sorted((ref(obj) for obj in objects), key=lambda item: (item["object_id"], item["content_sha256"]))


@pytest.fixture()
def fx():
    sources = [
        sealed("SourceContract", f"source:s{index}:v1", value=f"source-{index}")
        for index in range(6)
    ]
    targets = [
        sealed(
            "TargetDefinition",
            f"target:t{index}:v1",
            schedule_source_ref=ref(sources[index * 2]),
            measurement_source_ref=ref(sources[index * 2 + 1]),
            value=f"target-{index}",
        )
        for index in range(3)
    ]
    methods = [
        sealed(
            "ForecastMethod",
            "method:m0:v1",
            compatible_target_refs=sorted_refs(*targets),
            output_schema="continuous_scalar_forecast_v1",
            selection_control_class="DETERMINISTIC_REPLAY",
        )
    ]
    resolutions = [
        sealed("ResolutionRule", f"resolution:r{index}:v1", value=f"resolution-{index}")
        for index in range(3)
    ]
    schedule = sealed(
        "PolicyDefinition",
        "policy:genesis-issuance-schedule:v3",
        policy_type="ISSUANCE_SCHEDULE",
        canonical_runtime_contract_version="GENESIS_RUNTIME_CONTRACT_V1",
        normative_timezone="America/New_York",
        schedule_parser_id="GENESIS_SCHEDULE_PARSER_V1",
    )
    retry = sealed("PolicyDefinition", "policy:retry:v1", policy_type="RETRY")
    omission = sealed("PolicyDefinition", "policy:omission:v1", policy_type="OMISSION")
    correction = sealed("PolicyDefinition", "policy:correction:v1", policy_type="CORRECTION")
    evaluation = sealed("PolicyDefinition", "policy:evaluation:v2", policy_type="EVALUATION")
    validator = sealed(
        "ValidatorContract",
        "validator:genesis:v1",
        value="validator",
        schedule_parser_id="GENESIS_SCHEDULE_PARSER_V1",
        schedule_parser_version="1.0",
    )
    quorum = sealed("PolicyDefinition", "policy:quorum:v1", value="quorum")
    qualification_verifier = sealed("ValidatorContract", "validator:qualification:v1", value="qualification")
    bitcoin = sealed("StrongBitcoinVerifierContract", "validator:bitcoin:v1", value="bitcoin")
    profiles = [
        sealed("RoughtimeProductionProviderProfile", f"profile:p{index}:v1", provider_id=f"p{index}")
        for index in range(3)
    ]
    decisions = [
        sealed("RoughtimeQualificationDecision", f"decision:p{index}:v1", provider_id=f"p{index}")
        for index in range(3)
    ]
    manifest = sealed(
        "TrustedManifest",
        "manifest:genesis:v1",
        manifest_sequence=1,
        target_refs=sorted_refs(*targets),
        resolution_rule_refs=sorted_refs(*resolutions),
        method_refs=sorted_refs(*methods),
        source_contract_refs=sorted_refs(*sources),
        issuance_schedule_policy_ref=ref(schedule),
        retry_policy_ref=ref(retry),
        omission_policy_ref=ref(omission),
        correction_policy_ref=ref(correction),
        evaluation_policy_ref=ref(evaluation),
        validator_contract_ref=ref(validator),
        deadline_receipt_quorum_policy_ref=ref(quorum),
        provider_profile_refs=sorted_refs(*profiles),
        qualification_decision_refs=sorted_refs(*decisions),
        qualification_verifier_contract_ref=ref(qualification_verifier),
        strong_bitcoin_verifier_contract_ref=ref(bitcoin),
    )
    schedule_artifact = sealed("RetainedScheduleArtifact", "artifact:schedule:v1", raw_sha256="a" * 64)
    tzdb_artifact = sealed("IanaTzdbArtifact", "artifact:tzdb:2026a", iana_tzdb_version="2026a")
    evidence_payload = {
        "schema_version": "1.0",
        "trusted_manifest_ref": ref(manifest),
        "issuance_schedule_policy_ref": ref(schedule),
        "target_ref": ref(targets[0]),
        "schedule_source_ref": ref(sources[0]),
        "schedule_artifact_ref": ref(schedule_artifact),
        "schedule_artifact_sha256": "a" * 64,
        "parser_id": "GENESIS_SCHEDULE_PARSER_V1",
        "parser_version": "1.0",
        "iana_tzdb_version": "2026a",
        "tzdb_artifact_ref": ref(tzdb_artifact),
        "retrieved_at": "2026-09-01T00:00:00Z",
        "parsed_release_identifier": "CPI-2026-08",
        "reference_period": "2026-08",
        "published_local_date": "2026-09-15",
        "published_local_time": "08:30:00",
        "published_timezone": "America/New_York",
        "authoritative_release_time": "2026-09-15T12:30:00Z",
        "plan_commitment_deadline": "2026-09-07T12:30:00Z",
        "information_cutoff": "2026-09-08T12:30:00Z",
        "execution_window_open": "2026-09-08T12:30:00Z",
        "execution_window_close": "2026-09-09T12:30:00Z",
        "external_proof_deadline": "2026-09-14T12:30:00Z",
        "durability_completion_deadline": "2026-09-15T12:30:00Z",
        "resolution_deadline": "2026-10-30T12:30:00Z",
    }
    evidence = reconstruct_schedule_derivation_evidence(evidence_payload)
    target_payload = {
        "schema_version": "1.0",
        "trusted_manifest_ref": ref(manifest),
        "issuance_schedule_policy_ref": ref(schedule),
        "target_ref": ref(targets[0]),
        "schedule_source_ref": ref(sources[0]),
        "measurement_source_ref": ref(sources[1]),
        "schedule_derivation_evidence_ref": ref(evidence),
        "reference_period": "2026-08",
        "release_identifier": "CPI-2026-08",
        "outcome_information_barrier": "2026-09-15T12:30:00Z",
        "information_cutoff": "2026-09-08T12:30:00Z",
        "resolution_deadline": "2026-10-30T12:30:00Z",
    }
    target_instance = reconstruct_target_instance(target_payload)
    slot_payload = {
        "schema_version": "1.0",
        "trusted_manifest_ref": ref(manifest),
        "issuance_schedule_policy_ref": ref(schedule),
        "target_instance_ref": ref(target_instance),
        "schedule_derivation_evidence_ref": ref(evidence),
        "method_ref": ref(methods[0]),
        "source_contract_refs": sorted_refs(sources[0], sources[1]),
        "information_cutoff": "2026-09-08T12:30:00Z",
        "output_schema": "continuous_scalar_forecast_v1",
        "selection_control_class": "DETERMINISTIC_REPLAY",
        "forecast_cardinality": 1,
    }
    slot = reconstruct_forecast_slot(slot_payload)
    plan_payload = {
        "schema_version": "1.0",
        "trusted_manifest_ref": ref(manifest),
        "schedule_policy_ref": ref(schedule),
        "schedule_derivation_evidence_ref": ref(evidence),
        "target_instance_ref": ref(target_instance),
        "method_refs": sorted_refs(*methods),
        "information_cutoff": "2026-09-08T12:30:00Z",
        "plan_commitment_deadline": "2026-09-07T12:30:00Z",
        "execution_window_open": "2026-09-08T12:30:00Z",
        "execution_window_close": "2026-09-09T12:30:00Z",
        "external_proof_deadline": "2026-09-14T12:30:00Z",
        "durability_completion_deadline": "2026-09-15T12:30:00Z",
        "expected_slots": [ref(slot)],
        "retry_policy_ref": ref(retry),
        "omission_policy_ref": ref(omission),
    }
    plan = reconstruct_issuance_cycle_plan(plan_payload)
    attempt = sealed("ForecastAttempt", "attempt:one:v1", value="attempt")
    forecast = sealed("IssuedForecast", "forecast:one:v1", value="forecast")
    correction_record = sealed("ForecastCorrection", "correction:one:v1", value="correction")
    withdrawal_record = sealed("ForecastWithdrawal", "withdrawal:one:v1", value="withdrawal")
    manifest_payload = {
        "schema_version": "1.0",
        "trusted_manifest_ref": ref(manifest),
        "cycle_plan_ref": ref(plan),
        "retry_policy_ref": ref(retry),
        "omission_policy_ref": ref(omission),
        "correction_policy_ref": ref(correction),
        "evaluation_policy_ref": ref(evaluation),
        "slot_accounting": [
            {
                "slot_ref": ref(slot),
                "issuance_outcome": "ISSUED",
                "eligibility_state": "INELIGIBLE",
                "withdrawal_state": "WITHDRAWN",
                "attempt_refs": [ref(attempt)],
                "issued_forecast_refs": [ref(forecast)],
                "failure_record_refs": [],
                "omission_evidence_refs": [],
                "ineligibility_evidence_refs": [ref(attempt)],
                "unresolved_evidence_refs": [],
                "withdrawal_refs": [ref(withdrawal_record)],
                "correction_refs": [ref(correction_record)],
            }
        ],
    }
    return {
        **locals(),
        "evidence": evidence,
        "target_instance": target_instance,
        "slot": slot,
        "plan": plan,
    }


def require_runtime_authority(fx, **overrides):
    manifest_payload = overrides.pop("manifest_payload", fx["manifest_payload"])
    arguments = {
        "trusted_manifest": fx["manifest"],
        "schedule_policy": fx["schedule"],
        "target_definition": fx["targets"][0],
        "forecast_methods": fx["methods"],
        "schedule_artifact": fx["schedule_artifact"],
        "tzdb_artifact": fx["tzdb_artifact"],
        "validator_contract": fx["validator"],
        "schedule_derivation_evidence": fx["evidence"],
        "target_instance": fx["target_instance"],
        "forecast_slots": [fx["slot"]],
        "issuance_cycle_plan": fx["plan"],
    }
    arguments.update(overrides)
    contracts.require_issuance_cycle_manifest_authority(
        manifest_payload, **arguments
    )


def schema_validator(filename):
    schema = json.loads((SCHEMAS / filename).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


@pytest.mark.parametrize(
    ("filename", "fixture_key"),
    [
        ("target_instance_v1.schema.json", "target_instance"),
        ("forecast_slot_v1.schema.json", "slot"),
        ("schedule_derivation_evidence_v1.schema.json", "evidence"),
        ("issuance_cycle_plan_v1.schema.json", "plan"),
    ],
)
def test_closed_runtime_schemas_accept_only_the_frozen_object_shape(fx, filename, fixture_key):
    validator = schema_validator(filename)
    obj = fx[fixture_key]
    validator.validate(obj)
    bad = dict(obj)
    bad["caller_authority_ref"] = ref(fx["schedule"])
    with pytest.raises(ValidationError):
        validator.validate(bad)


def test_cycle_manifest_schema_and_semantics_preserve_additive_history(fx):
    obj = reconstruct_issuance_cycle_manifest(fx["manifest_payload"])
    assert verify_sealed_object(obj)
    schema_validator("issuance_cycle_manifest_v1.schema.json").validate(obj)
    row = obj["slot_accounting"][0]
    assert row["issuance_outcome"] == "ISSUED"
    assert row["eligibility_state"] == "INELIGIBLE"
    assert row["withdrawal_state"] == "WITHDRAWN"
    assert row["issued_forecast_refs"] == [ref(fx["forecast"])]
    assert row["correction_refs"] == [ref(fx["correction_record"])]
    assert row["withdrawal_refs"] == [ref(fx["withdrawal_record"])]


def test_target_instance_identity_covers_every_consequential_payload_field(fx):
    original = reconstruct_target_instance(fx["target_payload"])
    mutations = {
        "trusted_manifest_ref": ref(fx["schedule"]),
        "issuance_schedule_policy_ref": ref(fx["retry"]),
        "target_ref": ref(fx["targets"][1]),
        "schedule_source_ref": ref(fx["sources"][2]),
        "measurement_source_ref": ref(fx["sources"][3]),
        "schedule_derivation_evidence_ref": ref(fx["schedule_artifact"]),
        "reference_period": "2026-07",
        "release_identifier": "CPI-2026-07",
        "outcome_information_barrier": "2026-09-15T12:30:01Z",
        "information_cutoff": "2026-09-08T12:30:01Z",
        "resolution_deadline": "2026-10-30T12:30:01Z",
    }
    for field, replacement in mutations.items():
        payload = copy.deepcopy(fx["target_payload"])
        payload[field] = replacement
        changed = reconstruct_target_instance(payload)
        assert ref(changed) != ref(original), field


def test_forecast_slot_identity_changes_for_target_method_cycle_and_authority_bindings(fx):
    original = reconstruct_forecast_slot(fx["slot_payload"])
    alternative_method = sealed("ForecastMethod", "method:other:v1", value="other")
    mutations = {
        "trusted_manifest_ref": ref(fx["schedule"]),
        "issuance_schedule_policy_ref": ref(fx["retry"]),
        "target_instance_ref": ref(fx["target_instance"] | {"content_sha256": "0" * 64}),
        "schedule_derivation_evidence_ref": ref(fx["schedule_artifact"]),
        "method_ref": ref(alternative_method),
        "source_contract_refs": sorted_refs(fx["sources"][0], fx["sources"][3]),
        "information_cutoff": "2026-09-08T12:30:01Z",
        "output_schema": "continuous_scalar_forecast_v2",
        "selection_control_class": "PRECOMMITTED_RANDOMNESS",
        "forecast_cardinality": 2,
    }
    for field, replacement in mutations.items():
        payload = copy.deepcopy(fx["slot_payload"])
        payload[field] = replacement
        try:
            changed = reconstruct_forecast_slot(payload)
        except ContractViolation:
            continue
        assert ref(changed) != ref(original), field


def test_runtime_identity_reconstruction_rejects_semantic_id_and_context_substitution(fx):
    first = reconstruct_target_instance(fx["target_payload"])
    second = reconstruct_target_instance(copy.deepcopy(fx["target_payload"]))
    assert first == second
    semantic_substitute = seal_object(
        fx["target_payload"],
        object_type="TargetInstance",
        stable_context=f"genesis-target-instance:{fx['targets'][0]['object_id']}:2026-08",
        semantic_id="target-instance:caller-selected:v1",
    )
    context_substitute = seal_object(
        fx["target_payload"], object_type="TargetInstance", stable_context="caller-selected-context"
    )
    assert ref(semantic_substitute) != ref(first)
    assert ref(context_substitute) != ref(first)


def test_ref_sets_must_be_sorted_unique_and_refs_must_be_exact(fx):
    unsorted = copy.deepcopy(fx["slot_payload"])
    unsorted["source_contract_refs"] = list(reversed(unsorted["source_contract_refs"]))
    with pytest.raises(ContractViolation, match="sorted"):
        reconstruct_forecast_slot(unsorted)
    duplicate = copy.deepcopy(fx["plan_payload"])
    duplicate["method_refs"] = duplicate["method_refs"] * 2
    with pytest.raises(ContractViolation, match="unique"):
        reconstruct_issuance_cycle_plan(duplicate)
    malformed = copy.deepcopy(fx["target_payload"])
    malformed["target_ref"] = {"object_id": fx["targets"][0]["object_id"]}
    with pytest.raises(ContractViolation, match="target_ref"):
        reconstruct_target_instance(malformed)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("issuance_schedule_policy_ref", {"object_id": "policy:other:v1", "content_sha256": "1" * 64}),
        ("schedule_source_ref", {"object_id": "source:other:v1", "content_sha256": "2" * 64}),
        ("schedule_artifact_ref", {"object_id": "artifact:other:v1", "content_sha256": "3" * 64}),
        ("parser_id", "CALLER_PARSER"),
        ("parser_version", "9.9"),
        ("iana_tzdb_version", "caller-tzdb"),
        ("tzdb_artifact_ref", {"object_id": "artifact:tzdb:other", "content_sha256": "4" * 64}),
    ],
)
def test_schedule_derivation_evidence_cannot_self_authorize(fx, field, replacement):
    payload = copy.deepcopy(fx["evidence_payload"])
    payload[field] = replacement
    evidence = reconstruct_schedule_derivation_evidence(payload)
    with pytest.raises(ContractViolation):
        require_schedule_derivation_authority(
            evidence,
            trusted_manifest=fx["manifest"],
            schedule_policy=fx["schedule"],
            target_definition=fx["targets"][0],
            schedule_artifact=fx["schedule_artifact"],
            tzdb_artifact=fx["tzdb_artifact"],
            validator_contract=fx["validator"],
        )


def test_schedule_derivation_evidence_accepts_exact_manifest_bound_authority(fx):
    require_schedule_derivation_authority(
        fx["evidence"],
        trusted_manifest=fx["manifest"],
        schedule_policy=fx["schedule"],
        target_definition=fx["targets"][0],
        schedule_artifact=fx["schedule_artifact"],
        tzdb_artifact=fx["tzdb_artifact"],
        validator_contract=fx["validator"],
    )


@pytest.mark.parametrize("runtime_contract_version", [None, "CALLER_SELECTED_RUNTIME_V1"])
def test_schedule_derivation_requires_authority_bound_genesis_runtime_contract_v1(
    fx, runtime_contract_version
):
    payload = {
        key: value
        for key, value in fx["schedule"].items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    if runtime_contract_version is None:
        payload.pop("canonical_runtime_contract_version")
    else:
        payload["canonical_runtime_contract_version"] = runtime_contract_version
    schedule = seal_object(
        payload,
        object_type="PolicyDefinition",
        stable_context="genesis-runtime-contract-test",
        semantic_id=fx["schedule"]["object_id"],
    )
    manifest_payload = {
        key: value
        for key, value in fx["manifest"].items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    manifest_payload["issuance_schedule_policy_ref"] = ref(schedule)
    manifest = seal_object(
        manifest_payload,
        object_type="TrustedManifest",
        stable_context="genesis-runtime-contract-test",
        semantic_id=fx["manifest"]["object_id"],
    )
    with pytest.raises(ContractViolation, match="GENESIS_RUNTIME_CONTRACT_V1"):
        require_schedule_derivation_authority(
            fx["evidence"],
            trusted_manifest=manifest,
            schedule_policy=schedule,
            target_definition=fx["targets"][0],
            schedule_artifact=fx["schedule_artifact"],
            tzdb_artifact=fx["tzdb_artifact"],
            validator_contract=fx["validator"],
        )


def test_schedule_derivation_rejects_caller_selected_validator_contract(fx):
    rogue = sealed(
        "ValidatorContract",
        "validator:rogue:v1",
        schedule_parser_id="GENESIS_SCHEDULE_PARSER_V1",
        schedule_parser_version="1.0",
    )
    with pytest.raises(ContractViolation, match="validator"):
        require_schedule_derivation_authority(
            fx["evidence"],
            trusted_manifest=fx["manifest"],
            schedule_policy=fx["schedule"],
            target_definition=fx["targets"][0],
            schedule_artifact=fx["schedule_artifact"],
            tzdb_artifact=fx["tzdb_artifact"],
            validator_contract=rogue,
        )


def test_runtime_authority_accepts_one_exact_fully_bound_chain(fx):
    require_runtime_authority(fx)


def test_runtime_authority_rejects_caller_authored_eligible_accounting_row(fx):
    payload = copy.deepcopy(fx["manifest_payload"])
    payload["slot_accounting"][0].update(
        eligibility_state="ELIGIBLE",
        ineligibility_evidence_refs=[],
    )

    with pytest.raises(ContractViolation, match="authoritative eligibility derivation"):
        require_runtime_authority(fx, manifest_payload=payload)


def test_runtime_authority_rejects_coordinated_mandatory_slot_replacement(fx):
    replacement_payload = copy.deepcopy(fx["slot_payload"])
    replacement_payload["information_cutoff"] = "2026-09-08T12:30:01Z"
    replacement_slot = reconstruct_forecast_slot(replacement_payload)

    plan_payload = copy.deepcopy(fx["plan_payload"])
    plan_payload["expected_slots"] = [ref(replacement_slot)]
    replacement_plan = reconstruct_issuance_cycle_plan(plan_payload)

    manifest_payload = copy.deepcopy(fx["manifest_payload"])
    manifest_payload["cycle_plan_ref"] = ref(replacement_plan)
    manifest_payload["slot_accounting"][0]["slot_ref"] = ref(replacement_slot)

    with pytest.raises(ContractViolation, match="mandatory ForecastSlot denominator"):
        require_runtime_authority(
            fx,
            manifest_payload=manifest_payload,
            forecast_slots=[replacement_slot],
            issuance_cycle_plan=replacement_plan,
        )


def test_runtime_authority_rejects_empty_caller_forecast_slots(fx):
    with pytest.raises(ContractViolation, match="mandatory ForecastSlot denominator"):
        require_runtime_authority(fx, forecast_slots=[])


def test_runtime_authority_rejects_duplicate_caller_forecast_slots(fx):
    with pytest.raises(ContractViolation, match="mandatory ForecastSlot denominator"):
        require_runtime_authority(fx, forecast_slots=[fx["slot"], fx["slot"]])


def test_runtime_authority_rejects_manifest_admitted_method_incompatible_with_target(fx):
    incompatible_method = sealed(
        "ForecastMethod",
        "method:m0:v1",
        compatible_target_refs=sorted_refs(*fx["targets"][1:]),
        output_schema="continuous_scalar_forecast_v1",
        selection_control_class="DETERMINISTIC_REPLAY",
    )
    trusted_manifest_payload = {
        key: value
        for key, value in fx["manifest"].items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    trusted_manifest_payload["method_refs"] = [ref(incompatible_method)]
    trusted_manifest = seal_object(
        trusted_manifest_payload,
        object_type="TrustedManifest",
        stable_context="genesis-runtime-contract-test",
        semantic_id=fx["manifest"]["object_id"],
    )

    evidence_payload = copy.deepcopy(fx["evidence_payload"])
    evidence_payload["trusted_manifest_ref"] = ref(trusted_manifest)
    evidence = reconstruct_schedule_derivation_evidence(evidence_payload)
    target_payload = copy.deepcopy(fx["target_payload"])
    target_payload.update(
        trusted_manifest_ref=ref(trusted_manifest),
        schedule_derivation_evidence_ref=ref(evidence),
    )
    target_instance = reconstruct_target_instance(target_payload)
    slot_payload = copy.deepcopy(fx["slot_payload"])
    slot_payload.update(
        trusted_manifest_ref=ref(trusted_manifest),
        target_instance_ref=ref(target_instance),
        schedule_derivation_evidence_ref=ref(evidence),
        method_ref=ref(incompatible_method),
    )
    slot = reconstruct_forecast_slot(slot_payload)
    plan_payload = copy.deepcopy(fx["plan_payload"])
    plan_payload.update(
        trusted_manifest_ref=ref(trusted_manifest),
        schedule_derivation_evidence_ref=ref(evidence),
        target_instance_ref=ref(target_instance),
        method_refs=[ref(incompatible_method)],
        expected_slots=[ref(slot)],
    )
    plan = reconstruct_issuance_cycle_plan(plan_payload)
    cycle_manifest_payload = copy.deepcopy(fx["manifest_payload"])
    cycle_manifest_payload.update(
        trusted_manifest_ref=ref(trusted_manifest),
        cycle_plan_ref=ref(plan),
    )
    cycle_manifest_payload["slot_accounting"][0]["slot_ref"] = ref(slot)

    with pytest.raises(ContractViolation, match="compatible_target_refs"):
        require_runtime_authority(
            fx,
            manifest_payload=cycle_manifest_payload,
            trusted_manifest=trusted_manifest,
            forecast_methods=[incompatible_method],
            schedule_derivation_evidence=evidence,
            target_instance=target_instance,
            forecast_slots=[slot],
            issuance_cycle_plan=plan,
        )


def test_manifest_authority_rejects_omitted_expected_slot(fx):
    payload = copy.deepcopy(fx["manifest_payload"])
    payload["slot_accounting"] = []
    with pytest.raises(ContractViolation):
        require_runtime_authority(fx, manifest_payload=payload)


def foreign_slot(fx, *, target_instance=None, method=None, sources=None):
    payload = copy.deepcopy(fx["slot_payload"])
    if target_instance is not None:
        payload["target_instance_ref"] = ref(target_instance)
    if method is not None:
        payload["method_ref"] = ref(method)
    if sources is not None:
        payload["source_contract_refs"] = sorted_refs(*sources)
    return reconstruct_forecast_slot(payload)


@pytest.mark.parametrize("mode", ["substituted", "extra"])
def test_manifest_authority_rejects_substituted_or_extra_slot(fx, mode):
    other_target_payload = copy.deepcopy(fx["target_payload"])
    other_target_payload.update(
        target_ref=ref(fx["targets"][1]),
        schedule_source_ref=ref(fx["sources"][2]),
        measurement_source_ref=ref(fx["sources"][3]),
    )
    other_target = reconstruct_target_instance(other_target_payload)
    alien = foreign_slot(fx, target_instance=other_target)
    payload = copy.deepcopy(fx["manifest_payload"])
    alien_row = copy.deepcopy(payload["slot_accounting"][0])
    alien_row["slot_ref"] = ref(alien)
    payload["slot_accounting"] = (
        [alien_row]
        if mode == "substituted"
        else sorted(
            [payload["slot_accounting"][0], alien_row],
            key=lambda row: (row["slot_ref"]["object_id"], row["slot_ref"]["content_sha256"]),
        )
    )
    with pytest.raises(ContractViolation, match="expected_slots"):
        require_runtime_authority(
            fx, manifest_payload=payload, forecast_slots=[fx["slot"], alien]
        )


def test_manifest_reconstruction_rejects_duplicate_slot_rows(fx):
    payload = copy.deepcopy(fx["manifest_payload"])
    payload["slot_accounting"] *= 2
    with pytest.raises(ContractViolation, match="unique"):
        reconstruct_issuance_cycle_manifest(payload)


def test_runtime_authority_rejects_wrong_issuance_cycle_plan(fx):
    payload = copy.deepcopy(fx["plan_payload"])
    payload["external_proof_deadline"] = "2026-09-14T12:30:01Z"
    wrong_plan = reconstruct_issuance_cycle_plan(payload)
    with pytest.raises(ContractViolation, match="cycle_plan_ref"):
        require_runtime_authority(fx, issuance_cycle_plan=wrong_plan)


def test_runtime_authority_rejects_slot_for_another_target_instance(fx):
    payload = copy.deepcopy(fx["target_payload"])
    payload["reference_period"] = "2026-07"
    other_target = reconstruct_target_instance(payload)
    alien = foreign_slot(fx, target_instance=other_target)
    with pytest.raises(ContractViolation, match="target_instance_ref"):
        require_runtime_authority(fx, forecast_slots=[alien])


@pytest.mark.parametrize("boundary", ["source", "method"])
def test_runtime_authority_rejects_unauthorized_source_or_method(fx, boundary):
    if boundary == "source":
        alien = foreign_slot(fx, sources=[fx["sources"][0], fx["sources"][3]])
    else:
        rogue_method = sealed("ForecastMethod", "method:rogue:v1", value="rogue")
        alien = foreign_slot(fx, method=rogue_method)
    with pytest.raises(ContractViolation, match=boundary):
        require_runtime_authority(fx, forecast_slots=[alien])


@pytest.mark.parametrize(
    ("issuance_outcome", "eligibility_state", "withdrawal_state"),
    [
        ("EXPECTED", "NOT_YET_DETERMINED", "ACTIVE"),
        ("ISSUED", "ELIGIBLE", "ACTIVE"),
        ("ISSUED", "INELIGIBLE", "ACTIVE"),
        ("ISSUED", "UNRESOLVED", "ACTIVE"),
        ("ISSUED", "ELIGIBLE", "WITHDRAWN"),
        ("FAILED", "NOT_APPLICABLE", "ACTIVE"),
        ("OMITTED", "NOT_APPLICABLE", "ACTIVE"),
    ],
)
def test_denominator_categories_remain_distinguishable(
    fx, issuance_outcome, eligibility_state, withdrawal_state
):
    row = copy.deepcopy(fx["manifest_payload"]["slot_accounting"][0])
    row.update(
        issuance_outcome=issuance_outcome,
        eligibility_state=eligibility_state,
        withdrawal_state=withdrawal_state,
        attempt_refs=[],
        issued_forecast_refs=[],
        failure_record_refs=[],
        omission_evidence_refs=[],
        ineligibility_evidence_refs=[],
        unresolved_evidence_refs=[],
        withdrawal_refs=[],
        correction_refs=[],
    )
    if issuance_outcome == "ISSUED":
        row["attempt_refs"] = [ref(fx["attempt"])]
        row["issued_forecast_refs"] = [ref(fx["forecast"])]
    if issuance_outcome == "FAILED":
        row["attempt_refs"] = [ref(fx["attempt"])]
        row["failure_record_refs"] = [ref(fx["attempt"])]
    if issuance_outcome == "OMITTED":
        row["omission_evidence_refs"] = [ref(fx["attempt"])]
    if eligibility_state == "INELIGIBLE":
        row["ineligibility_evidence_refs"] = [ref(fx["attempt"])]
    if eligibility_state == "UNRESOLVED":
        row["unresolved_evidence_refs"] = [ref(fx["attempt"])]
    if withdrawal_state == "WITHDRAWN":
        row["withdrawal_refs"] = [ref(fx["withdrawal_record"])]
    payload = copy.deepcopy(fx["manifest_payload"])
    payload["slot_accounting"] = [row]
    reconstructed = reconstruct_issuance_cycle_manifest(payload)
    assert reconstructed["slot_accounting"][0]["issuance_outcome"] == issuance_outcome
    assert reconstructed["slot_accounting"][0]["eligibility_state"] == eligibility_state
    assert reconstructed["slot_accounting"][0]["withdrawal_state"] == withdrawal_state


def test_manifest_rejects_corrections_or_withdrawals_that_erase_original_forecast(fx):
    for removed_field in ("issued_forecast_refs", "attempt_refs"):
        payload = copy.deepcopy(fx["manifest_payload"])
        payload["slot_accounting"][0][removed_field] = []
        with pytest.raises(ContractViolation):
            reconstruct_issuance_cycle_manifest(payload)
