import pytest

import forecast_trust_core.genesis_lifecycle_contract_gate_v1 as gate
from forecast_trust_core.canonical import seal_object


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="genesis-lifecycle-contract-gate-test",
        semantic_id=object_id,
    )


def reseal(obj, *, object_id=None, **changes):
    payload = {
        key: value
        for key, value in obj.items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload.update(changes)
    return seal_object(
        payload,
        object_type=obj["object_type"],
        stable_context="genesis-lifecycle-contract-gate-test-mutation",
        semantic_id=object_id or obj["object_id"],
    )


def fixture_set():
    manifest = sealed("TrustedManifest", "manifest:genesis-lifecycle:v1", value="manifest")
    schedule_policy = sealed("PolicyDefinition", "policy:schedule:v1", value="schedule")
    retry_policy = sealed("PolicyDefinition", "policy:retry:v1", value="retry")
    omission_policy = sealed("PolicyDefinition", "policy:omission:v1", value="omission")
    correction_policy = sealed("PolicyDefinition", "policy:correction:v1", value="correction")
    method = sealed("ForecastMethod", "method:last-observed-value:v1", value="method")
    target_definition = sealed("TargetDefinition", "target:test:v1", value="target")
    resolution_rule = sealed("ResolutionRule", "resolution:test:v1", value="resolution")
    schedule_source_contract = sealed("SourceContract", "source:schedule:v1", value="schedule-source")
    baseline_source_contract = sealed("SourceContract", "source:first-release:v1", value="baseline-source")
    schedule_raw = sealed("RawArtifact", "artifact:schedule:v1", value="schedule-raw")
    baseline_raw = sealed("RawArtifact", "artifact:baseline:v1", value="baseline-raw")

    schedule_artifact = sealed(
        "SourceArtifactEvidence",
        "source-artifact:schedule:v1",
        source_contract_ref=ref(schedule_source_contract),
        resolved_url="https://example.test/schedule",
        retrieved_at="2026-09-01T12:00:00Z",
        http_status=200,
        raw_sha256="1" * 64,
        raw_artifact_ref=ref(schedule_raw),
    )
    baseline_artifact = sealed(
        "SourceArtifactEvidence",
        "source-artifact:baseline:v1",
        source_contract_ref=ref(baseline_source_contract),
        resolved_url="https://example.test/release",
        retrieved_at="2026-09-08T12:00:00Z",
        http_status=200,
        raw_sha256="2" * 64,
        raw_artifact_ref=ref(baseline_raw),
    )
    schedule_snapshot = sealed(
        "ScheduleSnapshot",
        "schedule-snapshot:test:v1",
        schedule_source_contract_ref=ref(schedule_source_contract),
        source_artifact_evidence_ref=ref(schedule_artifact),
        parsed_release_identifier="release-2026-09-16",
        reference_period="2026-08",
        published_release_date="2026-09-16",
        published_release_time="08:30:00",
        published_timezone="America/New_York",
        parser_version="schedule-parser-v1",
    )
    target_instance = sealed(
        "TargetInstance",
        "target-instance:test:2026-08",
        target_definition_ref=ref(target_definition),
        resolution_rule_ref=ref(resolution_rule),
        schedule_snapshot_ref=ref(schedule_snapshot),
        reference_period="2026-08",
        outcome_information_barrier="2026-09-16T12:30:00Z",
    )
    slot = sealed(
        "Slot",
        "slot:test:2026-08:baseline",
        target_instance_ref=ref(target_instance),
        method_ref=ref(method),
        output_schema="continuous_scalar_forecast_v1",
        forecast_horizon="P7D",
        selection_control_class="DETERMINISTIC_REPLAY",
        forecast_cardinality=1,
    )
    plan = sealed(
        "IssuanceCyclePlan",
        "cycle-plan:test:2026-08",
        trusted_manifest_ref=ref(manifest),
        schedule_policy_ref=ref(schedule_policy),
        schedule_snapshot_ref=ref(schedule_snapshot),
        target_instance_ref=ref(target_instance),
        method_refs=[ref(method)],
        information_cutoff="2026-09-09T12:30:00Z",
        plan_commitment_deadline="2026-09-08T12:30:00Z",
        execution_window_open="2026-09-09T12:30:00Z",
        execution_window_close="2026-09-10T12:30:00Z",
        external_proof_deadline="2026-09-15T12:30:00Z",
        durability_completion_deadline="2026-09-16T12:30:00Z",
        expected_slots=[ref(slot)],
        retry_policy_ref=ref(retry_policy),
        omission_policy_ref=ref(omission_policy),
    )
    preceding_instance = sealed(
        "TargetInstance",
        "target-instance:test:2026-07",
        target_definition_ref=ref(target_definition),
        resolution_rule_ref=ref(resolution_rule),
        schedule_snapshot_ref=ref(schedule_snapshot),
        reference_period="2026-07",
        outcome_information_barrier="2026-08-14T12:30:00Z",
    )
    evidence_snapshot = sealed(
        "EvidenceSnapshot",
        "evidence-snapshot:test:2026-08",
        method_ref=ref(method),
        current_target_instance_ref=ref(target_instance),
        information_cutoff="2026-09-09T12:30:00Z",
        preceding_target_instance_ref=ref(preceding_instance),
        preceding_first_release_source_contract_ref=ref(baseline_source_contract),
        preceding_source_artifact_evidence_ref=ref(baseline_artifact),
        parsed_decimal_value="0.2",
        parser_version="baseline-parser-v1",
    )
    attempt = sealed(
        "ForecastRunAttempt",
        "attempt:test:2026-08:1",
        method_ref=ref(method),
        target_instance_ref=ref(target_instance),
        slot_ref=ref(slot),
        information_cutoff="2026-09-09T12:30:00Z",
        evidence_snapshot_refs=[ref(evidence_snapshot)],
        runtime_configuration_ref_or_none="NONE",
        randomness_evidence_ref_or_none="NONE",
        retrieval_log_ref_or_none="NONE",
        terminal_status="SUCCEEDED",
        failure_code_or_none="NONE",
        point_forecast_decimal_or_none="0.2",
        attempt_sequence=1,
        retry_of_or_none="NONE",
        issuance_eligible=True,
    )
    forecast = sealed(
        "IssuedForecast",
        "forecast:test:2026-08",
        target_instance_ref=ref(target_instance),
        resolution_rule_ref=ref(resolution_rule),
        method_ref=ref(method),
        successful_attempt_ref=ref(attempt),
        evidence_snapshot_refs=[ref(evidence_snapshot)],
        information_cutoff="2026-09-09T12:30:00Z",
        forecast_horizon="P7D",
        point_forecast_decimal="0.2",
        claimed_issuance_time="2026-09-09T12:31:00Z",
        cycle_plan_ref=ref(plan),
        correction_policy_ref=ref(correction_policy),
        retry_policy_ref=ref(retry_policy),
        trusted_manifest_ref=ref(manifest),
    )
    cycle_manifest = sealed(
        "IssuanceCycleManifest",
        "cycle-manifest:test:2026-08",
        cycle_plan_ref=ref(plan),
        slot_accounting=[
            {
                "slot_ref": ref(slot),
                "attempt_refs": [ref(attempt)],
                "outcome": "ISSUED",
                "issued_forecast_ref_or_none": ref(forecast),
                "omission_code_or_none": "NONE",
                "failure_code_or_none": "NONE",
            }
        ],
    )
    return {
        "manifest": manifest,
        "method": method,
        "slot": slot,
        "plan": plan,
        "schedule_artifact": schedule_artifact,
        "baseline_artifact": baseline_artifact,
        "schedule_snapshot": schedule_snapshot,
        "target_instance": target_instance,
        "evidence_snapshot": evidence_snapshot,
        "attempt": attempt,
        "forecast": forecast,
        "cycle_manifest": cycle_manifest,
    }


def test_complete_initial_genesis_contract_set_is_accepted():
    fx = fixture_set()
    gate.validate_lifecycle_contract_set(
        source_artifacts=[fx["schedule_artifact"], fx["baseline_artifact"]],
        schedule_snapshot=fx["schedule_snapshot"],
        target_instance=fx["target_instance"],
        cycle_plan=fx["plan"],
        slot=fx["slot"],
        evidence_snapshot=fx["evidence_snapshot"],
        attempts=[fx["attempt"]],
        forecast=fx["forecast"],
        cycle_manifest=fx["cycle_manifest"],
    )


def test_forecast_self_prospective_field_is_rejected():
    fx = fixture_set()
    bad = reseal(fx["forecast"], prospective_eligible=True)
    with pytest.raises(ValueError, match="IssuedForecast field set mismatch"):
        gate.validate_issued_forecast_contract(bad)


def test_cycle_plan_cannot_expand_initial_profile_to_two_methods():
    fx = fixture_set()
    second_method = sealed("ForecastMethod", "method:second:v1", value="second")
    bad = reseal(fx["plan"], method_refs=sorted([ref(fx["method"]), ref(second_method)], key=lambda item: (item["object_id"], item["content_sha256"])))
    with pytest.raises(ValueError, match="method_refs cardinality invalid"):
        gate.validate_cycle_plan_contract(bad)


def test_cycle_plan_deadline_order_fails_closed():
    fx = fixture_set()
    bad = reseal(fx["plan"], external_proof_deadline="2026-09-09T12:00:00Z")
    with pytest.raises(ValueError, match="deadline ordering invalid"):
        gate.validate_cycle_plan_contract(bad)


def test_second_attempt_requires_exact_predecessor_ref_shape():
    fx = fixture_set()
    bad = reseal(
        fx["attempt"],
        object_id="attempt:test:2026-08:2",
        attempt_sequence=2,
        retry_of_or_none="NONE",
    )
    with pytest.raises(ValueError, match="must bind retry predecessor"):
        gate.validate_forecast_run_attempt_contract(bad)


def test_failed_attempt_cannot_retain_prediction():
    fx = fixture_set()
    bad = reseal(
        fx["attempt"],
        terminal_status="FAILED",
        failure_code_or_none="EXECUTION_TIMEOUT",
        point_forecast_decimal_or_none="0.2",
        issuance_eligible=False,
    )
    with pytest.raises(ValueError, match="cannot retain an issuable prediction"):
        gate.validate_forecast_run_attempt_contract(bad)


def test_failed_attempt_cannot_be_issuance_eligible():
    fx = fixture_set()
    bad = reseal(
        fx["attempt"],
        terminal_status="FAILED",
        failure_code_or_none="EXECUTION_TIMEOUT",
        point_forecast_decimal_or_none="NONE",
        issuance_eligible=True,
    )
    with pytest.raises(ValueError, match="cannot be issuance eligible"):
        gate.validate_forecast_run_attempt_contract(bad)


def test_noncanonical_snapshot_decimal_is_rejected():
    fx = fixture_set()
    bad = reseal(fx["evidence_snapshot"], parsed_decimal_value="0.20")
    with pytest.raises(ValueError, match="parsed_decimal_value invalid"):
        gate.validate_evidence_snapshot_contract(bad)


def test_source_artifact_requires_https_and_successful_retrieval():
    fx = fixture_set()
    bad_url = reseal(fx["baseline_artifact"], resolved_url="http://example.test/release")
    with pytest.raises(ValueError, match="absolute HTTPS URL"):
        gate.validate_source_artifact_evidence_contract(bad_url)
    bad_status = reseal(fx["baseline_artifact"], http_status=404)
    with pytest.raises(ValueError, match="http_status must be 200"):
        gate.validate_source_artifact_evidence_contract(bad_status)


def test_schedule_snapshot_freezes_new_york_timezone():
    fx = fixture_set()
    bad = reseal(fx["schedule_snapshot"], published_timezone="UTC")
    with pytest.raises(ValueError, match="must be America/New_York"):
        gate.validate_schedule_snapshot_contract(bad)


def test_issued_manifest_requires_forecast_ref_and_no_failure_codes():
    fx = fixture_set()
    row = dict(fx["cycle_manifest"]["slot_accounting"][0])
    row["issued_forecast_ref_or_none"] = "NONE"
    bad = reseal(fx["cycle_manifest"], slot_accounting=[row])
    with pytest.raises(ValueError, match="must bind an IssuedForecast"):
        gate.validate_cycle_manifest_contract(bad)


def test_omitted_manifest_cannot_hide_attempts():
    fx = fixture_set()
    row = dict(fx["cycle_manifest"]["slot_accounting"][0])
    row.update(
        outcome="OMITTED",
        issued_forecast_ref_or_none="NONE",
        omission_code_or_none="MISSING_REQUIRED_EVIDENCE",
    )
    bad = reseal(fx["cycle_manifest"], slot_accounting=[row])
    with pytest.raises(ValueError, match="OMITTED slot cannot contain forecast execution attempts"):
        gate.validate_cycle_manifest_contract(bad)


def test_unknown_attempt_extension_field_is_rejected():
    fx = fixture_set()
    bad = reseal(fx["attempt"], replay_verified=True)
    with pytest.raises(ValueError, match="ForecastRunAttempt field set mismatch"):
        gate.validate_forecast_run_attempt_contract(bad)
