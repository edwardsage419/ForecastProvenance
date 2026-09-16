from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .canonical import CanonicalizationError, sorted_refs, validate_ref, verify_sealed_object
from .genesis_lifecycle_contract_gate_v1 import (
    validate_lifecycle_contract_set,
    validate_target_instance_contract,
)
from .genesis_source_authority_v1 import (
    BASELINE_METHOD_ID,
    derive_cycle_times_from_barrier,
    validate_baseline_evidence_snapshot_authoritatively,
    validate_schedule_snapshot_authoritatively,
    validate_target_instance_authoritatively,
)


GENESIS_SCHEDULE_POLICY_ID = "policy:genesis-issuance-schedule:v1"
GENESIS_RETRY_POLICY_ID = "policy:genesis-retry:v1"
GENESIS_OMISSION_POLICY_ID = "policy:genesis-omission:v1"
GENESIS_CORRECTION_POLICY_ID = "policy:genesis-correction:v1"


@dataclass(frozen=True)
class GenesisLifecycleAuthorityContext:
    trusted_manifest_ref: Mapping[str, str]
    target_refs: tuple[Mapping[str, str], ...]
    resolution_rule_refs: tuple[Mapping[str, str], ...]
    method_refs: tuple[Mapping[str, str], ...]
    source_contract_refs: tuple[Mapping[str, str], ...]
    issuance_schedule_policy_ref: Mapping[str, str]
    retry_policy_ref: Mapping[str, str]
    omission_policy_ref: Mapping[str, str]
    correction_policy_ref: Mapping[str, str]


@dataclass(frozen=True)
class GenesisIssuedLifecycleAuthority:
    trusted_manifest_ref: Mapping[str, str]
    cycle_plan_ref: Mapping[str, str]
    slot_ref: Mapping[str, str]
    evidence_snapshot_ref: Mapping[str, str]
    successful_attempt_ref: Mapping[str, str]
    forecast_ref: Mapping[str, str]
    cycle_manifest_ref: Mapping[str, str]
    point_forecast_decimal: str


def _fail(message: str) -> None:
    raise ValueError(f"Genesis v1 lifecycle authority violation: {message}")


def _exact_ref(obj: Mapping[str, Any], *, object_type: str | None = None) -> dict[str, str]:
    if not isinstance(obj, Mapping) or not verify_sealed_object(obj):
        _fail("authority input must be a valid sealed object")
    if object_type is not None and obj.get("object_type") != object_type:
        _fail(f"expected sealed object_type {object_type}")
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def _required_ref(manifest: Mapping[str, Any], field: str) -> dict[str, str]:
    value = manifest.get(field)
    try:
        validate_ref(value)
    except (CanonicalizationError, TypeError) as exc:
        raise ValueError(
            f"Genesis v1 lifecycle authority violation: TrustedManifest {field} is missing or malformed"
        ) from exc
    return dict(value)


def _required_ref_set(
    manifest: Mapping[str, Any],
    field: str,
    *,
    exact_count: int,
) -> tuple[Mapping[str, str], ...]:
    value = manifest.get(field)
    if not isinstance(value, list):
        _fail(f"TrustedManifest {field} must be a list")
    try:
        normalized = sorted_refs(value)
    except CanonicalizationError as exc:
        raise ValueError(
            f"Genesis v1 lifecycle authority violation: TrustedManifest {field} contains malformed references"
        ) from exc
    pairs = [(item["object_id"], item["content_sha256"]) for item in normalized]
    if len(normalized) != exact_count or len(pairs) != len(set(pairs)):
        _fail(f"TrustedManifest {field} must contain exactly {exact_count} unique references")
    if value != normalized:
        _fail(f"TrustedManifest {field} must be deterministically sorted")
    return tuple(normalized)


def derive_genesis_lifecycle_authority_context(
    trusted_manifest: Mapping[str, Any],
) -> GenesisLifecycleAuthorityContext:
    """Extract the initial Genesis-v1 lifecycle authority roots from a sealed manifest.

    This proves only exact dependency binding. It does not prove that the manifest has
    been accepted, finally validated, or authorized for Genesis execution.
    """
    manifest_ref = _exact_ref(trusted_manifest, object_type="TrustedManifest")
    if "status" in trusted_manifest:
        _fail("TrustedManifest may not self-assert acceptance status")
    return GenesisLifecycleAuthorityContext(
        trusted_manifest_ref=manifest_ref,
        target_refs=_required_ref_set(trusted_manifest, "target_refs", exact_count=3),
        resolution_rule_refs=_required_ref_set(
            trusted_manifest, "resolution_rule_refs", exact_count=3
        ),
        method_refs=_required_ref_set(trusted_manifest, "method_refs", exact_count=1),
        source_contract_refs=_required_ref_set(
            trusted_manifest, "source_contract_refs", exact_count=6
        ),
        issuance_schedule_policy_ref=_required_ref(
            trusted_manifest, "issuance_schedule_policy_ref"
        ),
        retry_policy_ref=_required_ref(trusted_manifest, "retry_policy_ref"),
        omission_policy_ref=_required_ref(trusted_manifest, "omission_policy_ref"),
        correction_policy_ref=_required_ref(trusted_manifest, "correction_policy_ref"),
    )


def _require_member(
    obj: Mapping[str, Any],
    admitted_refs: Sequence[Mapping[str, str]],
    *,
    object_type: str,
    label: str,
) -> dict[str, str]:
    item_ref = _exact_ref(obj, object_type=object_type)
    if item_ref not in admitted_refs:
        _fail(f"{label} is not admitted by TrustedManifest")
    return item_ref


def _require_policy(
    policy: Mapping[str, Any],
    expected_ref: Mapping[str, str],
    *,
    expected_id: str,
    label: str,
) -> dict[str, str]:
    policy_ref = _exact_ref(policy, object_type="PolicyDefinition")
    if policy_ref != dict(expected_ref):
        _fail(f"{label} differs from TrustedManifest")
    if policy.get("object_id") != expected_id:
        _fail(f"{label} semantic identity mismatch")
    return policy_ref


def _validate_profile_policy_semantics(
    *,
    schedule_policy: Mapping[str, Any],
    retry_policy: Mapping[str, Any],
    omission_policy: Mapping[str, Any],
    correction_policy: Mapping[str, Any],
) -> None:
    expected_schedule = {
        "normative_timezone": "America/New_York",
        "plan_commitment_offset_days_before_barrier": 8,
        "information_cutoff_offset_days_before_barrier": 7,
        "execution_window_open_offset_days_before_barrier": 7,
        "execution_window_close_offset_days_before_barrier": 6,
        "external_proof_margin_hours_before_barrier": 24,
        "durability_completion_deadline": "OUTCOME_INFORMATION_BARRIER",
    }
    for field, expected in expected_schedule.items():
        if schedule_policy.get(field) != expected:
            _fail(f"IssuanceSchedulePolicy {field} mismatch")
    if schedule_policy.get("cycle_model") != "ONE_CYCLE_PER_TARGET_RELEASE_INSTANCE":
        _fail("IssuanceSchedulePolicy cycle_model mismatch")
    if retry_policy.get("max_attempts") != 2:
        _fail("RetryPolicy max_attempts mismatch")
    if retry_policy.get("issuance_eligible_success_rule") != "FIRST_SUCCESS_ONLY":
        _fail("RetryPolicy first-success rule mismatch")
    allowed = retry_policy.get("retry_eligible_failure_codes")
    if not isinstance(allowed, list) or set(allowed) != {
        "EXECUTION_TIMEOUT",
        "LOCAL_IO_TRANSIENT",
        "PROCESS_CRASH",
    }:
        _fail("RetryPolicy retry-eligible failure-code set mismatch")
    if omission_policy.get("operator_discretion_rule") != "PROHIBITED_AFTER_OUTPUT_INSPECTION":
        _fail("OmissionPolicy operator discretion rule mismatch")
    if correction_policy.get("replacement_requirement") != "substantive_change_requires_new_forecast":
        _fail("CorrectionPolicy replacement rule mismatch")


def _validate_target_method_resolution_bindings(
    *,
    target_definition: Mapping[str, Any],
    target_ref: Mapping[str, str],
    resolution_rule: Mapping[str, Any],
    resolution_ref: Mapping[str, str],
    method: Mapping[str, Any],
    method_ref: Mapping[str, str],
    schedule_source_contract: Mapping[str, Any],
    schedule_source_ref: Mapping[str, str],
    first_release_source_contract: Mapping[str, Any],
    first_release_source_ref: Mapping[str, str],
) -> None:
    if target_definition.get("schedule_source_ref") != dict(schedule_source_ref):
        _fail("TargetDefinition schedule SourceContract mismatch")
    if target_definition.get("measurement_source_ref") != dict(first_release_source_ref):
        _fail("TargetDefinition measurement SourceContract mismatch")
    compatible_resolution_ids = target_definition.get("compatible_resolution_rule_ids")
    if not isinstance(compatible_resolution_ids, list) or resolution_rule.get("object_id") not in compatible_resolution_ids:
        _fail("TargetDefinition does not admit ResolutionRule")
    resolution_targets = resolution_rule.get("compatible_target_refs")
    if not isinstance(resolution_targets, list) or dict(target_ref) not in resolution_targets:
        _fail("ResolutionRule does not bind exact target")
    source_priority = resolution_rule.get("source_priority")
    if not isinstance(source_priority, list) or not source_priority or source_priority[0] != dict(first_release_source_ref):
        _fail("ResolutionRule first-release source priority mismatch")
    compatible_targets = method.get("compatible_target_refs")
    if not isinstance(compatible_targets, list) or dict(target_ref) not in compatible_targets:
        _fail("ForecastMethod does not bind exact target")
    if method.get("object_id") != BASELINE_METHOD_ID:
        _fail("initial Genesis method semantic identity mismatch")
    if method.get("output_schema") != "continuous_scalar_forecast_v1":
        _fail("ForecastMethod output schema mismatch")
    if method.get("selection_control_class") != "DETERMINISTIC_REPLAY":
        _fail("ForecastMethod selection control mismatch")
    if method.get("randomness_policy") != "NONE":
        _fail("ForecastMethod randomness policy mismatch")
    if schedule_source_contract.get("object_id") == first_release_source_contract.get("object_id"):
        _fail("schedule and first-release SourceContracts must be distinct")
    # Keep parameters live for explicit exact-ref review in this helper.
    if method_ref.get("object_id") != BASELINE_METHOD_ID or resolution_ref.get("object_id") != resolution_rule.get("object_id"):
        _fail("method or resolution exact-ref binding mismatch")


def _validate_attempt_chain_authoritatively(
    attempts: Sequence[Mapping[str, Any]],
    *,
    method_ref: Mapping[str, str],
    target_instance_ref: Mapping[str, str],
    slot_ref: Mapping[str, str],
    evidence_snapshot_ref: Mapping[str, str],
    information_cutoff: str,
    retry_policy: Mapping[str, Any],
    replayed_prediction: str,
) -> Mapping[str, Any]:
    if not isinstance(attempts, Sequence) or isinstance(attempts, (str, bytes, bytearray)):
        _fail("attempt set must be a sequence")
    if not 1 <= len(attempts) <= 2:
        _fail("initial Genesis attempt count must be one or two")
    allowed_failures = set(retry_policy["retry_eligible_failure_codes"])
    success: Mapping[str, Any] | None = None
    for index, attempt in enumerate(attempts, start=1):
        if attempt.get("attempt_sequence") != index:
            _fail("ForecastRunAttempt sequence is not exact and contiguous")
        if attempt.get("method_ref") != dict(method_ref):
            _fail("ForecastRunAttempt method mismatch")
        if attempt.get("target_instance_ref") != dict(target_instance_ref):
            _fail("ForecastRunAttempt target mismatch")
        if attempt.get("slot_ref") != dict(slot_ref):
            _fail("ForecastRunAttempt slot mismatch")
        if attempt.get("information_cutoff") != information_cutoff:
            _fail("ForecastRunAttempt information cutoff mismatch")
        if attempt.get("evidence_snapshot_refs") != [dict(evidence_snapshot_ref)]:
            _fail("ForecastRunAttempt evidence snapshot set mismatch")
        if index == 1:
            if attempt.get("retry_of_or_none") != "NONE":
                _fail("first ForecastRunAttempt must not have a retry predecessor")
        else:
            predecessor_ref = _exact_ref(attempts[index - 2], object_type="ForecastRunAttempt")
            if attempt.get("retry_of_or_none") != predecessor_ref:
                _fail("retry attempt predecessor mismatch")
            predecessor = attempts[index - 2]
            if predecessor.get("terminal_status") != "FAILED" or predecessor.get("failure_code_or_none") not in allowed_failures:
                _fail("retry attempt was not triggered by a precommitted eligible failure")
        if attempt.get("terminal_status") == "SUCCEEDED":
            if success is not None:
                _fail("multiple successful attempts violate first-success-only rule")
            if index != len(attempts):
                _fail("attempts after first success are prohibited")
            if attempt.get("issuance_eligible") is not True:
                _fail("first successful attempt must be issuance eligible")
            if attempt.get("point_forecast_decimal_or_none") != replayed_prediction:
                _fail("successful attempt prediction differs from deterministic replay")
            success = attempt
    if success is None:
        _fail("issued lifecycle requires one successful attempt")
    return success


def validate_genesis_v1_issued_lifecycle_from_trusted_manifest(
    trusted_manifest: Mapping[str, Any],
    *,
    target_definition: Mapping[str, Any],
    resolution_rule: Mapping[str, Any],
    method: Mapping[str, Any],
    schedule_source_contract: Mapping[str, Any],
    first_release_source_contract: Mapping[str, Any],
    schedule_policy: Mapping[str, Any],
    retry_policy: Mapping[str, Any],
    omission_policy: Mapping[str, Any],
    correction_policy: Mapping[str, Any],
    schedule_artifact_evidence: Mapping[str, Any],
    schedule_raw_bytes: bytes,
    schedule_snapshot: Mapping[str, Any],
    target_instance: Mapping[str, Any],
    preceding_target_instance: Mapping[str, Any],
    cycle_plan: Mapping[str, Any],
    slot: Mapping[str, Any],
    baseline_artifact_evidence: Mapping[str, Any],
    baseline_raw_bytes: bytes,
    evidence_snapshot: Mapping[str, Any],
    attempts: Sequence[Mapping[str, Any]],
    forecast: Mapping[str, Any],
    cycle_manifest: Mapping[str, Any],
) -> GenesisIssuedLifecycleAuthority:
    """Recompute the initial Genesis issued lifecycle under one exact manifest.

    A successful return proves lifecycle dependency closure only. It deliberately does
    not assert manifest acceptance, Genesis authorization, external existence,
    durability, or confirmatory prospective eligibility.
    """
    context = derive_genesis_lifecycle_authority_context(trusted_manifest)

    target_ref = _require_member(
        target_definition, context.target_refs, object_type="TargetDefinition", label="TargetDefinition"
    )
    resolution_ref = _require_member(
        resolution_rule,
        context.resolution_rule_refs,
        object_type="ResolutionRule",
        label="ResolutionRule",
    )
    method_ref = _require_member(
        method, context.method_refs, object_type="ForecastMethod", label="ForecastMethod"
    )
    schedule_source_ref = _require_member(
        schedule_source_contract,
        context.source_contract_refs,
        object_type="SourceContract",
        label="schedule SourceContract",
    )
    first_release_source_ref = _require_member(
        first_release_source_contract,
        context.source_contract_refs,
        object_type="SourceContract",
        label="first-release SourceContract",
    )
    schedule_policy_ref = _require_policy(
        schedule_policy,
        context.issuance_schedule_policy_ref,
        expected_id=GENESIS_SCHEDULE_POLICY_ID,
        label="IssuanceSchedulePolicy",
    )
    retry_policy_ref = _require_policy(
        retry_policy,
        context.retry_policy_ref,
        expected_id=GENESIS_RETRY_POLICY_ID,
        label="RetryPolicy",
    )
    omission_policy_ref = _require_policy(
        omission_policy,
        context.omission_policy_ref,
        expected_id=GENESIS_OMISSION_POLICY_ID,
        label="OmissionPolicy",
    )
    correction_policy_ref = _require_policy(
        correction_policy,
        context.correction_policy_ref,
        expected_id=GENESIS_CORRECTION_POLICY_ID,
        label="CorrectionPolicy",
    )
    _validate_profile_policy_semantics(
        schedule_policy=schedule_policy,
        retry_policy=retry_policy,
        omission_policy=omission_policy,
        correction_policy=correction_policy,
    )
    _validate_target_method_resolution_bindings(
        target_definition=target_definition,
        target_ref=target_ref,
        resolution_rule=resolution_rule,
        resolution_ref=resolution_ref,
        method=method,
        method_ref=method_ref,
        schedule_source_contract=schedule_source_contract,
        schedule_source_ref=schedule_source_ref,
        first_release_source_contract=first_release_source_contract,
        first_release_source_ref=first_release_source_ref,
    )

    validate_lifecycle_contract_set(
        source_artifacts=[schedule_artifact_evidence, baseline_artifact_evidence],
        schedule_snapshot=schedule_snapshot,
        target_instance=target_instance,
        cycle_plan=cycle_plan,
        slot=slot,
        evidence_snapshot=evidence_snapshot,
        attempts=attempts,
        forecast=forecast,
        cycle_manifest=cycle_manifest,
    )
    validate_target_instance_contract(preceding_target_instance)
    validate_schedule_snapshot_authoritatively(
        schedule_snapshot,
        target_definition,
        schedule_source_contract,
        schedule_artifact_evidence,
        schedule_raw_bytes,
    )
    validate_target_instance_authoritatively(
        target_instance, target_definition, schedule_snapshot
    )

    manifest_ref = dict(context.trusted_manifest_ref)
    schedule_snapshot_ref = _exact_ref(schedule_snapshot, object_type="ScheduleSnapshot")
    target_instance_ref = _exact_ref(target_instance, object_type="TargetInstance")
    slot_ref = _exact_ref(slot, object_type="Slot")
    plan_ref = _exact_ref(cycle_plan, object_type="IssuanceCyclePlan")
    evidence_snapshot_ref = _exact_ref(evidence_snapshot, object_type="EvidenceSnapshot")

    if target_instance.get("resolution_rule_ref") != resolution_ref:
        _fail("TargetInstance ResolutionRule mismatch")
    if cycle_plan.get("trusted_manifest_ref") != manifest_ref:
        _fail("IssuanceCyclePlan TrustedManifest mismatch")
    if cycle_plan.get("schedule_policy_ref") != schedule_policy_ref:
        _fail("IssuanceCyclePlan schedule policy mismatch")
    if cycle_plan.get("schedule_snapshot_ref") != schedule_snapshot_ref:
        _fail("IssuanceCyclePlan schedule snapshot mismatch")
    if cycle_plan.get("target_instance_ref") != target_instance_ref:
        _fail("IssuanceCyclePlan target instance mismatch")
    if cycle_plan.get("method_refs") != [method_ref]:
        _fail("IssuanceCyclePlan method set mismatch")
    if cycle_plan.get("expected_slots") != [slot_ref]:
        _fail("IssuanceCyclePlan expected slot set mismatch")
    if cycle_plan.get("retry_policy_ref") != retry_policy_ref:
        _fail("IssuanceCyclePlan retry policy mismatch")
    if cycle_plan.get("omission_policy_ref") != omission_policy_ref:
        _fail("IssuanceCyclePlan omission policy mismatch")

    expected_times = derive_cycle_times_from_barrier(
        target_instance["outcome_information_barrier"]
    )
    for field, expected in expected_times.items():
        if cycle_plan.get(field) != expected:
            _fail(f"IssuanceCyclePlan {field} differs from schedule-derived value")
    if schedule_artifact_evidence.get("retrieved_at") > cycle_plan["plan_commitment_deadline"]:
        _fail("official schedule artifact was retrieved after plan commitment deadline")

    if slot.get("target_instance_ref") != target_instance_ref:
        _fail("Slot target instance mismatch")
    if slot.get("method_ref") != method_ref:
        _fail("Slot method mismatch")
    if slot.get("output_schema") != method.get("output_schema"):
        _fail("Slot output schema differs from ForecastMethod")
    if slot.get("selection_control_class") != method.get("selection_control_class"):
        _fail("Slot selection control differs from ForecastMethod")
    if slot.get("forecast_horizon") != "P7D":
        _fail("initial Genesis Slot forecast_horizon must be P7D")

    if evidence_snapshot.get("information_cutoff") != cycle_plan["information_cutoff"]:
        _fail("EvidenceSnapshot information cutoff differs from cycle plan")
    replayed_prediction = validate_baseline_evidence_snapshot_authoritatively(
        evidence_snapshot,
        method=method,
        target_definition=target_definition,
        current_target_instance=target_instance,
        preceding_target_instance=preceding_target_instance,
        first_release_source_contract=first_release_source_contract,
        first_release_artifact_evidence=baseline_artifact_evidence,
        first_release_raw_bytes=baseline_raw_bytes,
    )

    successful_attempt = _validate_attempt_chain_authoritatively(
        attempts,
        method_ref=method_ref,
        target_instance_ref=target_instance_ref,
        slot_ref=slot_ref,
        evidence_snapshot_ref=evidence_snapshot_ref,
        information_cutoff=cycle_plan["information_cutoff"],
        retry_policy=retry_policy,
        replayed_prediction=replayed_prediction,
    )
    successful_attempt_ref = _exact_ref(
        successful_attempt, object_type="ForecastRunAttempt"
    )

    if forecast.get("target_instance_ref") != target_instance_ref:
        _fail("IssuedForecast target instance mismatch")
    if forecast.get("resolution_rule_ref") != resolution_ref:
        _fail("IssuedForecast ResolutionRule mismatch")
    if forecast.get("method_ref") != method_ref:
        _fail("IssuedForecast method mismatch")
    if forecast.get("successful_attempt_ref") != successful_attempt_ref:
        _fail("IssuedForecast successful attempt mismatch")
    if forecast.get("evidence_snapshot_refs") != [evidence_snapshot_ref]:
        _fail("IssuedForecast evidence snapshot set mismatch")
    if forecast.get("information_cutoff") != cycle_plan["information_cutoff"]:
        _fail("IssuedForecast information cutoff mismatch")
    if forecast.get("forecast_horizon") != slot.get("forecast_horizon"):
        _fail("IssuedForecast forecast horizon mismatch")
    if forecast.get("point_forecast_decimal") != replayed_prediction:
        _fail("IssuedForecast prediction differs from deterministic replay")
    if forecast.get("cycle_plan_ref") != plan_ref:
        _fail("IssuedForecast cycle plan mismatch")
    if forecast.get("correction_policy_ref") != correction_policy_ref:
        _fail("IssuedForecast correction policy mismatch")
    if forecast.get("retry_policy_ref") != retry_policy_ref:
        _fail("IssuedForecast retry policy mismatch")
    if forecast.get("trusted_manifest_ref") != manifest_ref:
        _fail("IssuedForecast TrustedManifest mismatch")
    issuance_time = forecast.get("claimed_issuance_time")
    if not (
        cycle_plan["execution_window_open"]
        <= issuance_time
        <= cycle_plan["execution_window_close"]
    ):
        _fail("IssuedForecast claimed issuance time is outside execution window")

    forecast_ref = _exact_ref(forecast, object_type="IssuedForecast")
    cycle_manifest_ref = _exact_ref(cycle_manifest, object_type="IssuanceCycleManifest")
    if cycle_manifest.get("cycle_plan_ref") != plan_ref:
        _fail("IssuanceCycleManifest cycle plan mismatch")
    row = cycle_manifest["slot_accounting"][0]
    if row.get("slot_ref") != slot_ref:
        _fail("IssuanceCycleManifest slot mismatch")
    expected_attempt_refs = [
        _exact_ref(item, object_type="ForecastRunAttempt") for item in attempts
    ]
    if row.get("attempt_refs") != expected_attempt_refs:
        _fail("IssuanceCycleManifest attempt accounting is incomplete or reordered")
    if row.get("outcome") != "ISSUED":
        _fail("positive lifecycle authority requires ISSUED slot outcome")
    if row.get("issued_forecast_ref_or_none") != forecast_ref:
        _fail("IssuanceCycleManifest forecast membership mismatch")
    if row.get("omission_code_or_none") != "NONE" or row.get("failure_code_or_none") != "NONE":
        _fail("issued slot cannot carry omission or terminal failure code")

    return GenesisIssuedLifecycleAuthority(
        trusted_manifest_ref=manifest_ref,
        cycle_plan_ref=plan_ref,
        slot_ref=slot_ref,
        evidence_snapshot_ref=evidence_snapshot_ref,
        successful_attempt_ref=successful_attempt_ref,
        forecast_ref=forecast_ref,
        cycle_manifest_ref=cycle_manifest_ref,
        point_forecast_decimal=replayed_prediction,
    )
