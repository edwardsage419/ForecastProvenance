from __future__ import annotations

import hashlib

import pytest

from forecast_trust_core.canonical import seal_object
from forecast_trust_core.genesis_lifecycle_authority_v1 import (
    derive_genesis_lifecycle_authority_context,
    validate_genesis_v1_issued_lifecycle_from_trusted_manifest,
)
from forecast_trust_core.genesis_source_authority_v1 import (
    FIRST_RELEASE_PARSER_VERSION,
    SCHEDULE_PARSER_VERSION,
)


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="genesis-lifecycle-authority-test",
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
        stable_context="genesis-lifecycle-authority-test-mutation",
        semantic_id=object_id or obj["object_id"],
    )


def source_contract(object_id, primary_url, hosts):
    return sealed(
        "SourceContract",
        object_id,
        access_mode="HTTPS_PUBLIC",
        allowed_hosts=hosts,
        primary_url=primary_url,
    )


def artifact(contract, raw, url, *, object_id, retrieved_at):
    return sealed(
        "SourceArtifactEvidence",
        object_id,
        source_contract_ref=ref(contract),
        resolved_url=url,
        retrieved_at=retrieved_at,
        http_status=200,
        raw_sha256=hashlib.sha256(raw).hexdigest(),
        raw_artifact_ref={"object_id": f"raw:{object_id}", "content_sha256": "a" * 64},
    )


def fixture_set(*, schedule_retrieved_at="2026-09-01T00:00:00Z"):
    schedule_source = source_contract(
        "source:bls-cpi-release-schedule:v1",
        "https://www.bls.gov/schedule/news_release/cpi.htm",
        ["www.bls.gov"],
    )
    first_release_source = source_contract(
        "source:bls-cpi-first-release:v1",
        "https://www.bls.gov/bls/news-release/cpi.htm",
        ["www.bls.gov"],
    )
    other_sources = [
        source_contract(
            "source:bls-employment-situation-schedule:v1",
            "https://www.bls.gov/schedule/news_release/empsit.htm",
            ["www.bls.gov"],
        ),
        source_contract(
            "source:bls-u3-first-release:v1",
            "https://www.bls.gov/bls/news-release/empsit.htm",
            ["www.bls.gov"],
        ),
        source_contract(
            "source:bea-gdp-release-schedule:v1",
            "https://www.bea.gov/news/schedule",
            ["www.bea.gov"],
        ),
        source_contract(
            "source:bea-real-gdp-advance:v1",
            "https://www.bea.gov/news/",
            ["www.bea.gov", "apps.bea.gov"],
        ),
    ]

    target = sealed(
        "TargetDefinition",
        "target:us-cpi-all-items-mom-sa:v1",
        schedule_source_ref=ref(schedule_source),
        measurement_source_ref=ref(first_release_source),
        compatible_resolution_rule_ids=["resolution:us-cpi-all-items-mom-sa:v1"],
        forecast_horizon_rule="minimum_7_calendar_days",
    )
    dummy_targets = [
        sealed("TargetDefinition", "target:us-unemployment-rate-u3-sa:v1", value="dummy-u3"),
        sealed("TargetDefinition", "target:us-real-gdp-qoq-saar-advance:v1", value="dummy-gdp"),
    ]
    resolution = sealed(
        "ResolutionRule",
        "resolution:us-cpi-all-items-mom-sa:v1",
        compatible_target_refs=[ref(target)],
        source_priority=[ref(first_release_source)],
        vintage_selection="FIRST_RELEASE_ONLY",
    )
    dummy_resolutions = [
        sealed("ResolutionRule", "resolution:us-unemployment-rate-u3-sa:v1", value="dummy-u3"),
        sealed("ResolutionRule", "resolution:us-real-gdp-qoq-saar-advance:v1", value="dummy-gdp"),
    ]
    method = sealed(
        "ForecastMethod",
        "method:last-observed-value:v1",
        compatible_target_refs=[ref(target)],
        compatible_forecast_class="continuous_scalar_point",
        output_schema="continuous_scalar_forecast_v1",
        selection_control_class="DETERMINISTIC_REPLAY",
        randomness_policy="NONE",
        output_rule="copy_canonical_decimal_from_admissible_preceding_first_release",
    )
    schedule_policy = sealed(
        "PolicyDefinition",
        "policy:genesis-issuance-schedule:v1",
        cycle_model="ONE_CYCLE_PER_TARGET_RELEASE_INSTANCE",
        normative_timezone="America/New_York",
        plan_commitment_offset_days_before_barrier=8,
        information_cutoff_offset_days_before_barrier=7,
        execution_window_open_offset_days_before_barrier=7,
        execution_window_close_offset_days_before_barrier=6,
        external_proof_margin_hours_before_barrier=24,
        durability_completion_deadline="OUTCOME_INFORMATION_BARRIER",
    )
    retry_policy = sealed(
        "PolicyDefinition",
        "policy:genesis-retry:v1",
        max_attempts=2,
        issuance_eligible_success_rule="FIRST_SUCCESS_ONLY",
        retry_eligible_failure_codes=[
            "EXECUTION_TIMEOUT",
            "LOCAL_IO_TRANSIENT",
            "PROCESS_CRASH",
        ],
    )
    omission_policy = sealed(
        "PolicyDefinition",
        "policy:genesis-omission:v1",
        operator_discretion_rule="PROHIBITED_AFTER_OUTPUT_INSPECTION",
    )
    correction_policy = sealed(
        "PolicyDefinition",
        "policy:genesis-correction:v1",
        replacement_requirement="substantive_change_requires_new_forecast",
    )

    manifest = sealed(
        "TrustedManifest",
        "manifest:genesis:v1",
        target_refs=sorted(
            [ref(target), *(ref(item) for item in dummy_targets)],
            key=lambda item: (item["object_id"], item["content_sha256"]),
        ),
        resolution_rule_refs=sorted(
            [ref(resolution), *(ref(item) for item in dummy_resolutions)],
            key=lambda item: (item["object_id"], item["content_sha256"]),
        ),
        method_refs=[ref(method)],
        source_contract_refs=sorted(
            [ref(schedule_source), ref(first_release_source), *(ref(item) for item in other_sources)],
            key=lambda item: (item["object_id"], item["content_sha256"]),
        ),
        issuance_schedule_policy_ref=ref(schedule_policy),
        retry_policy_ref=ref(retry_policy),
        omission_policy_ref=ref(omission_policy),
        correction_policy_ref=ref(correction_policy),
    )

    schedule_raw = b"""
    <html><body><h1>Schedule of Releases for the Consumer Price Index</h1>
    <table><tr><th>Reference Month</th><th>Release Date</th><th>Release Time</th></tr>
    <tr><td>August 2026</td><td>Sep. 11, 2026</td><td>08:30 AM</td></tr></table>
    </body></html>
    """
    schedule_artifact = artifact(
        schedule_source,
        schedule_raw,
        schedule_source["primary_url"],
        object_id="source-artifact:cpi-schedule:2026-08",
        retrieved_at=schedule_retrieved_at,
    )
    schedule_snapshot = sealed(
        "ScheduleSnapshot",
        "schedule-snapshot:cpi:2026-08",
        schedule_source_contract_ref=ref(schedule_source),
        source_artifact_evidence_ref=ref(schedule_artifact),
        parsed_release_identifier="BLS_CPI:2026-08",
        reference_period="2026-08",
        published_release_date="2026-09-11",
        published_release_time="08:30:00",
        published_timezone="America/New_York",
        parser_version=SCHEDULE_PARSER_VERSION,
    )
    target_instance = sealed(
        "TargetInstance",
        "target-instance:cpi:2026-08",
        target_definition_ref=ref(target),
        resolution_rule_ref=ref(resolution),
        schedule_snapshot_ref=ref(schedule_snapshot),
        reference_period="2026-08",
        outcome_information_barrier="2026-09-11T12:30:00Z",
    )
    preceding_target_instance = sealed(
        "TargetInstance",
        "target-instance:cpi:2026-07",
        target_definition_ref=ref(target),
        resolution_rule_ref=ref(resolution),
        schedule_snapshot_ref={"object_id": "schedule-snapshot:cpi:2026-07", "content_sha256": "b" * 64},
        reference_period="2026-07",
        outcome_information_barrier="2026-08-12T12:30:00Z",
    )
    slot = sealed(
        "Slot",
        "slot:cpi:2026-08:baseline",
        target_instance_ref=ref(target_instance),
        method_ref=ref(method),
        output_schema="continuous_scalar_forecast_v1",
        forecast_horizon="P7D",
        selection_control_class="DETERMINISTIC_REPLAY",
        forecast_cardinality=1,
    )
    plan = sealed(
        "IssuanceCyclePlan",
        "cycle-plan:cpi:2026-08",
        trusted_manifest_ref=ref(manifest),
        schedule_policy_ref=ref(schedule_policy),
        schedule_snapshot_ref=ref(schedule_snapshot),
        target_instance_ref=ref(target_instance),
        method_refs=[ref(method)],
        information_cutoff="2026-09-04T12:30:00Z",
        plan_commitment_deadline="2026-09-03T12:30:00Z",
        execution_window_open="2026-09-04T12:30:00Z",
        execution_window_close="2026-09-05T12:30:00Z",
        external_proof_deadline="2026-09-10T12:30:00Z",
        durability_completion_deadline="2026-09-11T12:30:00Z",
        expected_slots=[ref(slot)],
        retry_policy_ref=ref(retry_policy),
        omission_policy_ref=ref(omission_policy),
    )

    baseline_raw = b"""
    <html><body>
    <h1>CONSUMER PRICE INDEX - JULY 2026</h1>
    <p>The Consumer Price Index for All Urban Consumers (CPI-U) increased 0.1 percent on a seasonally adjusted basis in July.</p>
    </body></html>
    """
    baseline_artifact = artifact(
        first_release_source,
        baseline_raw,
        "https://www.bls.gov/news.release/cpi.nr0.htm",
        object_id="source-artifact:cpi-first-release:2026-07",
        retrieved_at="2026-09-01T01:00:00Z",
    )
    evidence_snapshot = sealed(
        "EvidenceSnapshot",
        "evidence-snapshot:cpi:2026-08",
        method_ref=ref(method),
        current_target_instance_ref=ref(target_instance),
        information_cutoff="2026-09-04T12:30:00Z",
        preceding_target_instance_ref=ref(preceding_target_instance),
        preceding_first_release_source_contract_ref=ref(first_release_source),
        preceding_source_artifact_evidence_ref=ref(baseline_artifact),
        parsed_decimal_value="0.1",
        parser_version=FIRST_RELEASE_PARSER_VERSION,
    )
    attempt = sealed(
        "ForecastRunAttempt",
        "attempt:cpi:2026-08:1",
        method_ref=ref(method),
        target_instance_ref=ref(target_instance),
        slot_ref=ref(slot),
        information_cutoff="2026-09-04T12:30:00Z",
        evidence_snapshot_refs=[ref(evidence_snapshot)],
        runtime_configuration_ref_or_none="NONE",
        randomness_evidence_ref_or_none="NONE",
        retrieval_log_ref_or_none="NONE",
        terminal_status="SUCCEEDED",
        failure_code_or_none="NONE",
        point_forecast_decimal_or_none="0.1",
        attempt_sequence=1,
        retry_of_or_none="NONE",
        issuance_eligible=True,
    )
    forecast = sealed(
        "IssuedForecast",
        "forecast:cpi:2026-08",
        target_instance_ref=ref(target_instance),
        resolution_rule_ref=ref(resolution),
        method_ref=ref(method),
        successful_attempt_ref=ref(attempt),
        evidence_snapshot_refs=[ref(evidence_snapshot)],
        information_cutoff="2026-09-04T12:30:00Z",
        forecast_horizon="P7D",
        point_forecast_decimal="0.1",
        claimed_issuance_time="2026-09-04T12:31:00Z",
        cycle_plan_ref=ref(plan),
        correction_policy_ref=ref(correction_policy),
        retry_policy_ref=ref(retry_policy),
        trusted_manifest_ref=ref(manifest),
    )
    cycle_manifest = sealed(
        "IssuanceCycleManifest",
        "cycle-manifest:cpi:2026-08",
        cycle_plan_ref=ref(plan),
        slot_accounting=[{
            "slot_ref": ref(slot),
            "attempt_refs": [ref(attempt)],
            "outcome": "ISSUED",
            "issued_forecast_ref_or_none": ref(forecast),
            "omission_code_or_none": "NONE",
            "failure_code_or_none": "NONE",
        }],
    )
    return {
        "trusted_manifest": manifest,
        "target_definition": target,
        "resolution_rule": resolution,
        "method": method,
        "schedule_source_contract": schedule_source,
        "first_release_source_contract": first_release_source,
        "schedule_policy": schedule_policy,
        "retry_policy": retry_policy,
        "omission_policy": omission_policy,
        "correction_policy": correction_policy,
        "schedule_artifact_evidence": schedule_artifact,
        "schedule_raw_bytes": schedule_raw,
        "schedule_snapshot": schedule_snapshot,
        "target_instance": target_instance,
        "preceding_target_instance": preceding_target_instance,
        "cycle_plan": plan,
        "slot": slot,
        "baseline_artifact_evidence": baseline_artifact,
        "baseline_raw_bytes": baseline_raw,
        "evidence_snapshot": evidence_snapshot,
        "attempts": [attempt],
        "forecast": forecast,
        "cycle_manifest": cycle_manifest,
    }


def validate(fx):
    return validate_genesis_v1_issued_lifecycle_from_trusted_manifest(**fx)


def test_context_extracts_exact_lifecycle_roots():
    fx = fixture_set()
    context = derive_genesis_lifecycle_authority_context(fx["trusted_manifest"])
    assert context.trusted_manifest_ref == ref(fx["trusted_manifest"])
    assert context.method_refs == (ref(fx["method"]),)
    assert context.issuance_schedule_policy_ref == ref(fx["schedule_policy"])
    assert context.retry_policy_ref == ref(fx["retry_policy"])


def test_complete_manifest_rooted_issued_lifecycle_is_accepted_without_prospective_claim():
    fx = fixture_set()
    result = validate(fx)
    assert result.trusted_manifest_ref == ref(fx["trusted_manifest"])
    assert result.forecast_ref == ref(fx["forecast"])
    assert result.cycle_manifest_ref == ref(fx["cycle_manifest"])
    assert result.point_forecast_decimal == "0.1"
    assert not hasattr(result, "prospective_eligible")
    assert not hasattr(result, "state")


def test_manifest_self_acceptance_status_is_rejected():
    fx = fixture_set()
    manifest = reseal(fx["trusted_manifest"], status="ACCEPTED")
    fx["trusted_manifest"] = manifest
    with pytest.raises(ValueError, match="self-assert acceptance"):
        validate(fx)


def test_unsorted_manifest_target_set_is_rejected():
    fx = fixture_set()
    refs = list(fx["trusted_manifest"]["target_refs"])
    manifest = reseal(fx["trusted_manifest"], target_refs=list(reversed(refs)))
    fx["trusted_manifest"] = manifest
    with pytest.raises(ValueError, match="deterministically sorted"):
        validate(fx)


def test_target_substitution_is_rejected_by_manifest():
    fx = fixture_set()
    substitute = reseal(fx["target_definition"], object_id=fx["target_definition"]["object_id"], extra="substitute")
    fx["target_definition"] = substitute
    with pytest.raises(ValueError, match="not admitted by TrustedManifest"):
        validate(fx)


def test_cycle_plan_manifest_substitution_is_rejected():
    fx = fixture_set()
    wrong_ref = {"object_id": "manifest:other:v1", "content_sha256": "f" * 64}
    fx["cycle_plan"] = reseal(fx["cycle_plan"], trusted_manifest_ref=wrong_ref)
    with pytest.raises(ValueError, match="TrustedManifest mismatch"):
        validate(fx)


def test_schedule_derived_deadline_substitution_is_rejected():
    fx = fixture_set()
    fx["cycle_plan"] = reseal(
        fx["cycle_plan"], plan_commitment_deadline="2026-09-03T13:30:00Z"
    )
    with pytest.raises(ValueError, match="plan_commitment_deadline differs"):
        validate(fx)


def test_evidence_snapshot_cutoff_must_equal_cycle_plan():
    fx = fixture_set()
    fx["evidence_snapshot"] = reseal(
        fx["evidence_snapshot"], information_cutoff="2026-09-04T12:00:00Z"
    )
    with pytest.raises(ValueError, match="information cutoff differs from cycle plan"):
        validate(fx)


def test_schedule_artifact_after_plan_commitment_deadline_is_rejected():
    fx = fixture_set(schedule_retrieved_at="2026-09-03T12:30:01Z")
    with pytest.raises(ValueError, match="retrieved after plan commitment deadline"):
        validate(fx)


def retry_fixture(*, failure_code="EXECUTION_TIMEOUT", second_prediction="0.1"):
    fx = fixture_set()
    first = reseal(
        fx["attempts"][0],
        terminal_status="FAILED",
        failure_code_or_none=failure_code,
        point_forecast_decimal_or_none="NONE",
        issuance_eligible=False,
    )
    second = sealed(
        "ForecastRunAttempt",
        "attempt:cpi:2026-08:2",
        method_ref=ref(fx["method"]),
        target_instance_ref=ref(fx["target_instance"]),
        slot_ref=ref(fx["slot"]),
        information_cutoff=fx["cycle_plan"]["information_cutoff"],
        evidence_snapshot_refs=[ref(fx["evidence_snapshot"])],
        runtime_configuration_ref_or_none="NONE",
        randomness_evidence_ref_or_none="NONE",
        retrieval_log_ref_or_none="NONE",
        terminal_status="SUCCEEDED",
        failure_code_or_none="NONE",
        point_forecast_decimal_or_none=second_prediction,
        attempt_sequence=2,
        retry_of_or_none=ref(first),
        issuance_eligible=True,
    )
    forecast = reseal(
        fx["forecast"], successful_attempt_ref=ref(second), point_forecast_decimal=second_prediction
    )
    row = dict(fx["cycle_manifest"]["slot_accounting"][0])
    row["attempt_refs"] = [ref(first), ref(second)]
    row["issued_forecast_ref_or_none"] = ref(forecast)
    cycle_manifest = reseal(fx["cycle_manifest"], slot_accounting=[row])
    fx.update(attempts=[first, second], forecast=forecast, cycle_manifest=cycle_manifest)
    return fx


def test_retry_after_precommitted_failure_is_accepted_and_fully_accounted():
    fx = retry_fixture()
    result = validate(fx)
    assert result.successful_attempt_ref == ref(fx["attempts"][1])
    assert result.point_forecast_decimal == "0.1"


def test_retry_after_noneligible_failure_is_rejected():
    fx = retry_fixture(failure_code="MODEL_DISAGREEMENT")
    with pytest.raises(ValueError, match="precommitted eligible failure"):
        validate(fx)


def test_retry_predecessor_must_be_exact_previous_attempt():
    fx = retry_fixture()
    second = reseal(
        fx["attempts"][1],
        retry_of_or_none={"object_id": "attempt:other:v1", "content_sha256": "e" * 64},
    )
    fx["attempts"] = [fx["attempts"][0], second]
    with pytest.raises(ValueError, match="predecessor mismatch"):
        validate(fx)


def test_attempt_after_first_success_is_rejected():
    fx = fixture_set()
    second = sealed(
        "ForecastRunAttempt",
        "attempt:cpi:2026-08:2",
        method_ref=ref(fx["method"]),
        target_instance_ref=ref(fx["target_instance"]),
        slot_ref=ref(fx["slot"]),
        information_cutoff=fx["cycle_plan"]["information_cutoff"],
        evidence_snapshot_refs=[ref(fx["evidence_snapshot"])],
        runtime_configuration_ref_or_none="NONE",
        randomness_evidence_ref_or_none="NONE",
        retrieval_log_ref_or_none="NONE",
        terminal_status="SUCCEEDED",
        failure_code_or_none="NONE",
        point_forecast_decimal_or_none="0.1",
        attempt_sequence=2,
        retry_of_or_none=ref(fx["attempts"][0]),
        issuance_eligible=False,
    )
    fx["attempts"] = [fx["attempts"][0], second]
    with pytest.raises(ValueError, match="precommitted eligible failure|after first success"):
        validate(fx)


def test_forecast_prediction_substitution_is_rejected():
    fx = fixture_set()
    fx["forecast"] = reseal(fx["forecast"], point_forecast_decimal="9.9")
    with pytest.raises(ValueError, match="prediction differs from deterministic replay"):
        validate(fx)


def test_cycle_manifest_forecast_membership_substitution_is_rejected():
    fx = fixture_set()
    row = dict(fx["cycle_manifest"]["slot_accounting"][0])
    row["issued_forecast_ref_or_none"] = {
        "object_id": "forecast:substitute:v1",
        "content_sha256": "d" * 64,
    }
    fx["cycle_manifest"] = reseal(fx["cycle_manifest"], slot_accounting=[row])
    with pytest.raises(ValueError, match="forecast membership mismatch"):
        validate(fx)
