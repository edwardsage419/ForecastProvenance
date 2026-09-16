from __future__ import annotations

import re
from typing import Any, Mapping, Sequence
from urllib.parse import urlparse

from .canonical import (
    CanonicalizationError,
    require_ascii_token,
    require_decimal_string,
    require_utc_timestamp,
    validate_ref,
    verify_sealed_object,
)


SEALED = frozenset({"schema_version", "object_type", "object_id", "payload_sha256", "content_sha256"})

SOURCE_ARTIFACT_KEYS = SEALED | frozenset({
    "source_contract_ref",
    "resolved_url",
    "retrieved_at",
    "http_status",
    "raw_sha256",
    "raw_artifact_ref",
})
SCHEDULE_SNAPSHOT_KEYS = SEALED | frozenset({
    "schedule_source_contract_ref",
    "source_artifact_evidence_ref",
    "parsed_release_identifier",
    "reference_period",
    "published_release_date",
    "published_release_time",
    "published_timezone",
    "parser_version",
})
TARGET_INSTANCE_KEYS = SEALED | frozenset({
    "target_definition_ref",
    "resolution_rule_ref",
    "schedule_snapshot_ref",
    "reference_period",
    "outcome_information_barrier",
})
CYCLE_PLAN_KEYS = SEALED | frozenset({
    "trusted_manifest_ref",
    "schedule_policy_ref",
    "schedule_snapshot_ref",
    "target_instance_ref",
    "method_refs",
    "information_cutoff",
    "plan_commitment_deadline",
    "execution_window_open",
    "execution_window_close",
    "external_proof_deadline",
    "durability_completion_deadline",
    "expected_slots",
    "retry_policy_ref",
    "omission_policy_ref",
})
SLOT_KEYS = SEALED | frozenset({
    "target_instance_ref",
    "method_ref",
    "output_schema",
    "forecast_horizon",
    "selection_control_class",
    "forecast_cardinality",
})
EVIDENCE_SNAPSHOT_KEYS = SEALED | frozenset({
    "method_ref",
    "current_target_instance_ref",
    "information_cutoff",
    "preceding_target_instance_ref",
    "preceding_first_release_source_contract_ref",
    "preceding_source_artifact_evidence_ref",
    "parsed_decimal_value",
    "parser_version",
})
ATTEMPT_KEYS = SEALED | frozenset({
    "method_ref",
    "target_instance_ref",
    "slot_ref",
    "information_cutoff",
    "evidence_snapshot_refs",
    "runtime_configuration_ref_or_none",
    "randomness_evidence_ref_or_none",
    "retrieval_log_ref_or_none",
    "terminal_status",
    "failure_code_or_none",
    "point_forecast_decimal_or_none",
    "attempt_sequence",
    "retry_of_or_none",
    "issuance_eligible",
})
ISSUED_FORECAST_KEYS = SEALED | frozenset({
    "target_instance_ref",
    "resolution_rule_ref",
    "method_ref",
    "successful_attempt_ref",
    "evidence_snapshot_refs",
    "information_cutoff",
    "forecast_horizon",
    "point_forecast_decimal",
    "claimed_issuance_time",
    "cycle_plan_ref",
    "correction_policy_ref",
    "retry_policy_ref",
    "trusted_manifest_ref",
})
CYCLE_MANIFEST_KEYS = SEALED | frozenset({
    "cycle_plan_ref",
    "slot_accounting",
})
ACCOUNTING_ROW_KEYS = frozenset({
    "slot_ref",
    "attempt_refs",
    "outcome",
    "issued_forecast_ref_or_none",
    "omission_code_or_none",
    "failure_code_or_none",
})

HEX64 = frozenset("0123456789abcdef")
DATE_RE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
TIME_RE = re.compile(r"^[0-9]{2}:[0-9]{2}:[0-9]{2}$")


def _fail(message: str) -> None:
    raise ValueError(f"Genesis v1 lifecycle contract violation: {message}")


def _exact_sealed(obj: Mapping[str, Any], *, object_type: str, keys: frozenset[str]) -> None:
    if not isinstance(obj, Mapping):
        _fail(f"{object_type} must be an object")
    if frozenset(obj) != keys:
        _fail(f"{object_type} field set mismatch")
    if not verify_sealed_object(obj):
        _fail(f"{object_type} seal invalid")
    if obj.get("schema_version") != "1.0":
        _fail(f"{object_type} schema_version mismatch")
    if obj.get("object_type") != object_type:
        _fail(f"{object_type} object_type mismatch")


def _ref(value: Any, field: str) -> None:
    try:
        validate_ref(value)
    except (CanonicalizationError, TypeError) as exc:
        raise ValueError(f"Genesis v1 lifecycle contract violation: {field} reference malformed") from exc


def _ref_list(value: Any, field: str, *, minimum: int, maximum: int, sorted_set: bool) -> None:
    if not isinstance(value, list) or not minimum <= len(value) <= maximum:
        _fail(f"{field} cardinality invalid")
    pairs: list[tuple[str, str]] = []
    for index, item in enumerate(value):
        _ref(item, f"{field}[{index}]")
        pair = (item["object_id"], item["content_sha256"])
        if pair in pairs:
            _fail(f"{field} contains duplicate references")
        pairs.append(pair)
    if sorted_set and pairs != sorted(pairs):
        _fail(f"{field} must be deterministically sorted")


def _none_or_ref(value: Any, field: str) -> None:
    if value == "NONE":
        return
    _ref(value, field)


def _token(value: Any, field: str) -> str:
    try:
        return require_ascii_token(value, field)
    except (CanonicalizationError, TypeError) as exc:
        raise ValueError(f"Genesis v1 lifecycle contract violation: {field} invalid") from exc


def _timestamp(value: Any, field: str) -> str:
    try:
        return require_utc_timestamp(value)
    except (CanonicalizationError, TypeError) as exc:
        raise ValueError(f"Genesis v1 lifecycle contract violation: {field} invalid") from exc


def _decimal(value: Any, field: str) -> str:
    try:
        return require_decimal_string(value)
    except (CanonicalizationError, TypeError) as exc:
        raise ValueError(f"Genesis v1 lifecycle contract violation: {field} invalid") from exc


def _hex64(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(ch not in HEX64 for ch in value):
        _fail(f"{field} must be 64 lowercase hex characters")
    return value


def validate_source_artifact_evidence_contract(obj: Mapping[str, Any]) -> None:
    _exact_sealed(obj, object_type="SourceArtifactEvidence", keys=SOURCE_ARTIFACT_KEYS)
    _ref(obj.get("source_contract_ref"), "SourceArtifactEvidence.source_contract_ref")
    _ref(obj.get("raw_artifact_ref"), "SourceArtifactEvidence.raw_artifact_ref")
    url = obj.get("resolved_url")
    if not isinstance(url, str) or urlparse(url).scheme != "https" or not urlparse(url).hostname:
        _fail("SourceArtifactEvidence.resolved_url must be an absolute HTTPS URL")
    _timestamp(obj.get("retrieved_at"), "SourceArtifactEvidence.retrieved_at")
    if obj.get("http_status") != 200:
        _fail("SourceArtifactEvidence.http_status must be 200 for confirmatory input")
    _hex64(obj.get("raw_sha256"), "SourceArtifactEvidence.raw_sha256")


def validate_schedule_snapshot_contract(obj: Mapping[str, Any]) -> None:
    _exact_sealed(obj, object_type="ScheduleSnapshot", keys=SCHEDULE_SNAPSHOT_KEYS)
    _ref(obj.get("schedule_source_contract_ref"), "ScheduleSnapshot.schedule_source_contract_ref")
    _ref(obj.get("source_artifact_evidence_ref"), "ScheduleSnapshot.source_artifact_evidence_ref")
    _token(obj.get("parsed_release_identifier"), "ScheduleSnapshot.parsed_release_identifier")
    _token(obj.get("reference_period"), "ScheduleSnapshot.reference_period")
    date = obj.get("published_release_date")
    time = obj.get("published_release_time")
    if not isinstance(date, str) or DATE_RE.fullmatch(date) is None:
        _fail("ScheduleSnapshot.published_release_date must use YYYY-MM-DD")
    if not isinstance(time, str) or TIME_RE.fullmatch(time) is None:
        _fail("ScheduleSnapshot.published_release_time must use HH:MM:SS")
    if obj.get("published_timezone") != "America/New_York":
        _fail("ScheduleSnapshot.published_timezone must be America/New_York")
    _token(obj.get("parser_version"), "ScheduleSnapshot.parser_version")


def validate_target_instance_contract(obj: Mapping[str, Any]) -> None:
    _exact_sealed(obj, object_type="TargetInstance", keys=TARGET_INSTANCE_KEYS)
    _ref(obj.get("target_definition_ref"), "TargetInstance.target_definition_ref")
    _ref(obj.get("resolution_rule_ref"), "TargetInstance.resolution_rule_ref")
    _ref(obj.get("schedule_snapshot_ref"), "TargetInstance.schedule_snapshot_ref")
    _token(obj.get("reference_period"), "TargetInstance.reference_period")
    _timestamp(obj.get("outcome_information_barrier"), "TargetInstance.outcome_information_barrier")


def validate_cycle_plan_contract(obj: Mapping[str, Any]) -> None:
    _exact_sealed(obj, object_type="IssuanceCyclePlan", keys=CYCLE_PLAN_KEYS)
    for field in (
        "trusted_manifest_ref",
        "schedule_policy_ref",
        "schedule_snapshot_ref",
        "target_instance_ref",
        "retry_policy_ref",
        "omission_policy_ref",
    ):
        _ref(obj.get(field), f"IssuanceCyclePlan.{field}")
    _ref_list(obj.get("method_refs"), "IssuanceCyclePlan.method_refs", minimum=1, maximum=1, sorted_set=True)
    _ref_list(obj.get("expected_slots"), "IssuanceCyclePlan.expected_slots", minimum=1, maximum=1, sorted_set=True)
    times = {}
    for field in (
        "information_cutoff",
        "plan_commitment_deadline",
        "execution_window_open",
        "execution_window_close",
        "external_proof_deadline",
        "durability_completion_deadline",
    ):
        times[field] = _timestamp(obj.get(field), f"IssuanceCyclePlan.{field}")
    if times["information_cutoff"] != times["execution_window_open"]:
        _fail("IssuanceCyclePlan information_cutoff must equal execution_window_open")
    if not (
        times["plan_commitment_deadline"]
        < times["information_cutoff"]
        < times["execution_window_close"]
        < times["external_proof_deadline"]
        < times["durability_completion_deadline"]
    ):
        _fail("IssuanceCyclePlan deadline ordering invalid")


def validate_slot_contract(obj: Mapping[str, Any]) -> None:
    _exact_sealed(obj, object_type="Slot", keys=SLOT_KEYS)
    _ref(obj.get("target_instance_ref"), "Slot.target_instance_ref")
    _ref(obj.get("method_ref"), "Slot.method_ref")
    if obj.get("output_schema") != "continuous_scalar_forecast_v1":
        _fail("Slot.output_schema must be continuous_scalar_forecast_v1")
    _token(obj.get("forecast_horizon"), "Slot.forecast_horizon")
    if obj.get("selection_control_class") != "DETERMINISTIC_REPLAY":
        _fail("Slot.selection_control_class must be DETERMINISTIC_REPLAY")
    if obj.get("forecast_cardinality") != 1:
        _fail("Slot.forecast_cardinality must equal 1")


def validate_evidence_snapshot_contract(obj: Mapping[str, Any]) -> None:
    _exact_sealed(obj, object_type="EvidenceSnapshot", keys=EVIDENCE_SNAPSHOT_KEYS)
    for field in (
        "method_ref",
        "current_target_instance_ref",
        "preceding_target_instance_ref",
        "preceding_first_release_source_contract_ref",
        "preceding_source_artifact_evidence_ref",
    ):
        _ref(obj.get(field), f"EvidenceSnapshot.{field}")
    _timestamp(obj.get("information_cutoff"), "EvidenceSnapshot.information_cutoff")
    _decimal(obj.get("parsed_decimal_value"), "EvidenceSnapshot.parsed_decimal_value")
    _token(obj.get("parser_version"), "EvidenceSnapshot.parser_version")


def validate_forecast_run_attempt_contract(obj: Mapping[str, Any]) -> None:
    _exact_sealed(obj, object_type="ForecastRunAttempt", keys=ATTEMPT_KEYS)
    for field in ("method_ref", "target_instance_ref", "slot_ref"):
        _ref(obj.get(field), f"ForecastRunAttempt.{field}")
    _timestamp(obj.get("information_cutoff"), "ForecastRunAttempt.information_cutoff")
    _ref_list(
        obj.get("evidence_snapshot_refs"),
        "ForecastRunAttempt.evidence_snapshot_refs",
        minimum=1,
        maximum=1,
        sorted_set=True,
    )
    for field in (
        "runtime_configuration_ref_or_none",
        "randomness_evidence_ref_or_none",
        "retrieval_log_ref_or_none",
        "retry_of_or_none",
    ):
        _none_or_ref(obj.get(field), f"ForecastRunAttempt.{field}")
    if obj.get("runtime_configuration_ref_or_none") != "NONE":
        _fail("ForecastRunAttempt runtime configuration must be NONE for initial Genesis baseline")
    if obj.get("randomness_evidence_ref_or_none") != "NONE":
        _fail("ForecastRunAttempt randomness evidence must be NONE for deterministic Genesis baseline")
    if obj.get("retrieval_log_ref_or_none") != "NONE":
        _fail("ForecastRunAttempt retrieval log must be NONE; retained source evidence is authoritative")
    status = obj.get("terminal_status")
    if status not in {"SUCCEEDED", "FAILED"}:
        _fail("ForecastRunAttempt.terminal_status invalid")
    sequence = obj.get("attempt_sequence")
    if sequence not in {1, 2}:
        _fail("ForecastRunAttempt.attempt_sequence must be 1 or 2")
    if sequence == 1 and obj.get("retry_of_or_none") != "NONE":
        _fail("first ForecastRunAttempt cannot have retry predecessor")
    if sequence == 2 and obj.get("retry_of_or_none") == "NONE":
        _fail("second ForecastRunAttempt must bind retry predecessor")
    if not isinstance(obj.get("issuance_eligible"), bool):
        _fail("ForecastRunAttempt.issuance_eligible must be boolean")
    failure = obj.get("failure_code_or_none")
    prediction = obj.get("point_forecast_decimal_or_none")
    if status == "SUCCEEDED":
        if failure != "NONE":
            _fail("successful ForecastRunAttempt failure_code_or_none must be NONE")
        _decimal(prediction, "ForecastRunAttempt.point_forecast_decimal_or_none")
    else:
        if failure == "NONE":
            _fail("failed ForecastRunAttempt requires failure code")
        _token(failure, "ForecastRunAttempt.failure_code_or_none")
        if prediction != "NONE":
            _fail("failed ForecastRunAttempt cannot retain an issuable prediction")
        if obj.get("issuance_eligible") is True:
            _fail("failed ForecastRunAttempt cannot be issuance eligible")


def validate_issued_forecast_contract(obj: Mapping[str, Any]) -> None:
    _exact_sealed(obj, object_type="IssuedForecast", keys=ISSUED_FORECAST_KEYS)
    for field in (
        "target_instance_ref",
        "resolution_rule_ref",
        "method_ref",
        "successful_attempt_ref",
        "cycle_plan_ref",
        "correction_policy_ref",
        "retry_policy_ref",
        "trusted_manifest_ref",
    ):
        _ref(obj.get(field), f"IssuedForecast.{field}")
    _ref_list(
        obj.get("evidence_snapshot_refs"),
        "IssuedForecast.evidence_snapshot_refs",
        minimum=1,
        maximum=1,
        sorted_set=True,
    )
    _timestamp(obj.get("information_cutoff"), "IssuedForecast.information_cutoff")
    _token(obj.get("forecast_horizon"), "IssuedForecast.forecast_horizon")
    _decimal(obj.get("point_forecast_decimal"), "IssuedForecast.point_forecast_decimal")
    _timestamp(obj.get("claimed_issuance_time"), "IssuedForecast.claimed_issuance_time")


def validate_cycle_manifest_contract(obj: Mapping[str, Any]) -> None:
    _exact_sealed(obj, object_type="IssuanceCycleManifest", keys=CYCLE_MANIFEST_KEYS)
    _ref(obj.get("cycle_plan_ref"), "IssuanceCycleManifest.cycle_plan_ref")
    accounting = obj.get("slot_accounting")
    if not isinstance(accounting, list) or len(accounting) != 1:
        _fail("IssuanceCycleManifest.slot_accounting must contain exactly one Genesis v1 row")
    row = accounting[0]
    if not isinstance(row, Mapping) or frozenset(row) != ACCOUNTING_ROW_KEYS:
        _fail("IssuanceCycleManifest slot accounting field set mismatch")
    _ref(row.get("slot_ref"), "IssuanceCycleManifest.slot_accounting.slot_ref")
    _ref_list(
        row.get("attempt_refs"),
        "IssuanceCycleManifest.slot_accounting.attempt_refs",
        minimum=0,
        maximum=2,
        sorted_set=False,
    )
    _none_or_ref(
        row.get("issued_forecast_ref_or_none"),
        "IssuanceCycleManifest.slot_accounting.issued_forecast_ref_or_none",
    )
    outcome = row.get("outcome")
    if outcome not in {"ISSUED", "FAILED", "OMITTED"}:
        _fail("IssuanceCycleManifest slot outcome invalid")
    omission = row.get("omission_code_or_none")
    failure = row.get("failure_code_or_none")
    if outcome == "ISSUED":
        if not row.get("attempt_refs"):
            _fail("ISSUED slot must retain at least one attempt")
        if row.get("issued_forecast_ref_or_none") == "NONE":
            _fail("ISSUED slot must bind an IssuedForecast")
        if omission != "NONE" or failure != "NONE":
            _fail("ISSUED slot cannot carry omission or terminal failure code")
    elif outcome == "FAILED":
        if not row.get("attempt_refs"):
            _fail("FAILED slot must retain at least one attempt")
        if row.get("issued_forecast_ref_or_none") != "NONE":
            _fail("FAILED slot cannot bind an IssuedForecast")
        if omission != "NONE":
            _fail("FAILED slot cannot carry omission code")
        if failure == "NONE":
            _fail("FAILED slot requires failure code")
        _token(failure, "IssuanceCycleManifest.slot_accounting.failure_code_or_none")
    else:
        if row.get("attempt_refs"):
            _fail("OMITTED slot cannot contain forecast execution attempts")
        if row.get("issued_forecast_ref_or_none") != "NONE":
            _fail("OMITTED slot cannot bind an IssuedForecast")
        if failure != "NONE":
            _fail("OMITTED slot cannot carry execution failure code")
        if omission == "NONE":
            _fail("OMITTED slot requires omission code")
        _token(omission, "IssuanceCycleManifest.slot_accounting.omission_code_or_none")


def validate_lifecycle_contract_set(
    *,
    source_artifacts: Sequence[Mapping[str, Any]],
    schedule_snapshot: Mapping[str, Any],
    target_instance: Mapping[str, Any],
    cycle_plan: Mapping[str, Any],
    slot: Mapping[str, Any],
    evidence_snapshot: Mapping[str, Any],
    attempts: Sequence[Mapping[str, Any]],
    forecast: Mapping[str, Any],
    cycle_manifest: Mapping[str, Any],
) -> None:
    if not isinstance(source_artifacts, Sequence) or isinstance(source_artifacts, (str, bytes, bytearray)):
        _fail("source_artifacts must be a sequence")
    if len(source_artifacts) != 2:
        _fail("initial Genesis lifecycle requires exactly schedule and baseline source artifacts")
    for item in source_artifacts:
        validate_source_artifact_evidence_contract(item)
    validate_schedule_snapshot_contract(schedule_snapshot)
    validate_target_instance_contract(target_instance)
    validate_cycle_plan_contract(cycle_plan)
    validate_slot_contract(slot)
    validate_evidence_snapshot_contract(evidence_snapshot)
    if not isinstance(attempts, Sequence) or isinstance(attempts, (str, bytes, bytearray)):
        _fail("attempts must be a sequence")
    if not 1 <= len(attempts) <= 2:
        _fail("initial Genesis attempt count must be one or two")
    for item in attempts:
        validate_forecast_run_attempt_contract(item)
    validate_issued_forecast_contract(forecast)
    validate_cycle_manifest_contract(cycle_manifest)
