from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Mapping, Sequence

from .canonical import (
    CanonicalizationError,
    require_ascii_token,
    require_utc_timestamp,
    seal_object,
    sorted_refs,
    validate_ref,
    verify_sealed_object,
)


class ContractViolation(ValueError):
    """A Genesis v1 runtime object violates its frozen canonical contract."""


_DERIVED_FIELDS = frozenset({"object_id", "payload_sha256", "content_sha256"})
_REF_KEYS = frozenset({"object_id", "content_sha256"})

_SCHEDULE_EVIDENCE_FIELDS = frozenset(
    {
        "schema_version",
        "trusted_manifest_ref",
        "issuance_schedule_policy_ref",
        "target_ref",
        "schedule_source_ref",
        "schedule_artifact_ref",
        "schedule_artifact_sha256",
        "parser_id",
        "parser_version",
        "iana_tzdb_version",
        "tzdb_artifact_ref",
        "retrieved_at",
        "parsed_release_identifier",
        "reference_period",
        "published_local_date",
        "published_local_time",
        "published_timezone",
        "authoritative_release_time",
        "plan_commitment_deadline",
        "information_cutoff",
        "execution_window_open",
        "execution_window_close",
        "external_proof_deadline",
        "durability_completion_deadline",
        "resolution_deadline",
    }
)
_TARGET_INSTANCE_FIELDS = frozenset(
    {
        "schema_version",
        "trusted_manifest_ref",
        "issuance_schedule_policy_ref",
        "target_ref",
        "schedule_source_ref",
        "measurement_source_ref",
        "schedule_derivation_evidence_ref",
        "reference_period",
        "release_identifier",
        "outcome_information_barrier",
        "information_cutoff",
        "resolution_deadline",
    }
)
_FORECAST_SLOT_FIELDS = frozenset(
    {
        "schema_version",
        "trusted_manifest_ref",
        "issuance_schedule_policy_ref",
        "target_instance_ref",
        "schedule_derivation_evidence_ref",
        "method_ref",
        "source_contract_refs",
        "information_cutoff",
        "output_schema",
        "selection_control_class",
        "forecast_cardinality",
    }
)
_CYCLE_PLAN_FIELDS = frozenset(
    {
        "schema_version",
        "trusted_manifest_ref",
        "schedule_policy_ref",
        "schedule_derivation_evidence_ref",
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
    }
)
_CYCLE_MANIFEST_FIELDS = frozenset(
    {
        "schema_version",
        "trusted_manifest_ref",
        "cycle_plan_ref",
        "retry_policy_ref",
        "omission_policy_ref",
        "correction_policy_ref",
        "evaluation_policy_ref",
        "slot_accounting",
    }
)
_ACCOUNTING_FIELDS = frozenset(
    {
        "slot_ref",
        "issuance_outcome",
        "eligibility_state",
        "withdrawal_state",
        "attempt_refs",
        "issued_forecast_refs",
        "failure_record_refs",
        "omission_evidence_refs",
        "ineligibility_evidence_refs",
        "unresolved_evidence_refs",
        "withdrawal_refs",
        "correction_refs",
    }
)
_ACCOUNTING_REF_ARRAYS = (
    "attempt_refs",
    "issued_forecast_refs",
    "failure_record_refs",
    "omission_evidence_refs",
    "ineligibility_evidence_refs",
    "unresolved_evidence_refs",
    "withdrawal_refs",
    "correction_refs",
)


def _fail(message: str) -> None:
    raise ContractViolation(message)


def _require_exact_fields(payload: Mapping[str, Any], expected: frozenset[str], label: str) -> None:
    if not isinstance(payload, Mapping):
        _fail(f"{label} payload must be a mapping")
    actual = set(payload)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        _fail(f"{label} fields invalid; missing={missing}; extra={extra}")
    if payload.get("schema_version") != "1.0":
        _fail(f"{label} schema_version must be 1.0")
    if any(value is None for value in payload.values()):
        _fail(f"{label} null values are prohibited")


def _require_ref(value: Any, field: str) -> dict[str, str]:
    try:
        validate_ref(value)
    except (CanonicalizationError, KeyError, TypeError) as exc:
        raise ContractViolation(f"{field} must be an exact full reference") from exc
    return dict(value)


def _require_ref_array(
    value: Any,
    field: str,
    *,
    minimum: int = 0,
    maximum: int | None = None,
) -> list[dict[str, str]]:
    if not isinstance(value, list):
        _fail(f"{field} must be a list")
    try:
        normalized = sorted_refs(value)
    except (CanonicalizationError, KeyError, TypeError) as exc:
        raise ContractViolation(f"{field} contains a malformed reference") from exc
    pairs = [(item["object_id"], item["content_sha256"]) for item in normalized]
    if len(pairs) != len(set(pairs)):
        _fail(f"{field} must contain unique references")
    if value != normalized:
        _fail(f"{field} must be sorted by object_id then content_sha256")
    if len(value) < minimum or (maximum is not None and len(value) > maximum):
        _fail(f"{field} cardinality is outside the frozen contract")
    return normalized


def _require_token(value: Any, field: str) -> str:
    try:
        return require_ascii_token(value, field)
    except (CanonicalizationError, TypeError) as exc:
        raise ContractViolation(f"{field} must be a canonical ASCII token") from exc


def _require_utc(value: Any, field: str) -> str:
    try:
        return require_utc_timestamp(value)
    except (CanonicalizationError, TypeError) as exc:
        raise ContractViolation(f"{field} must be a canonical whole-second UTC timestamp") from exc


def _require_local_date(value: Any, field: str) -> None:
    if not isinstance(value, str):
        _fail(f"{field} must use YYYY-MM-DD")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%d")
    except ValueError as exc:
        raise ContractViolation(f"{field} must use YYYY-MM-DD") from exc
    if parsed.strftime("%Y-%m-%d") != value:
        _fail(f"{field} must use YYYY-MM-DD")


def _require_local_time(value: Any, field: str) -> None:
    if not isinstance(value, str):
        _fail(f"{field} must use HH:MM:SS")
    try:
        parsed = datetime.strptime(value, "%H:%M:%S")
    except ValueError as exc:
        raise ContractViolation(f"{field} must use HH:MM:SS") from exc
    if parsed.strftime("%H:%M:%S") != value:
        _fail(f"{field} must use HH:MM:SS")


def _require_sha256(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        _fail(f"{field} must be 64 lowercase hexadecimal characters")
    return value


def _seal(
    payload: Mapping[str, Any],
    *,
    object_type: str,
    stable_context: str,
) -> dict[str, Any]:
    try:
        return seal_object(payload, object_type=object_type, stable_context=stable_context)
    except CanonicalizationError as exc:
        raise ContractViolation(f"{object_type} sealing failed") from exc


def _payload_from_sealed(obj: Mapping[str, Any], object_type: str) -> dict[str, Any]:
    if not verify_sealed_object(obj) or obj.get("object_type") != object_type:
        _fail(f"expected a valid sealed {object_type}")
    return {key: value for key, value in obj.items() if key not in _DERIVED_FIELDS | {"object_type"}}


def _exact_ref(obj: Mapping[str, Any], object_type: str) -> dict[str, str]:
    if not verify_sealed_object(obj) or obj.get("object_type") != object_type:
        _fail(f"expected a valid sealed {object_type}")
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def reconstruct_schedule_derivation_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require_exact_fields(payload, _SCHEDULE_EVIDENCE_FIELDS, "ScheduleDerivationEvidence")
    for field in (
        "trusted_manifest_ref",
        "issuance_schedule_policy_ref",
        "target_ref",
        "schedule_source_ref",
        "schedule_artifact_ref",
        "tzdb_artifact_ref",
    ):
        _require_ref(payload[field], field)
    _require_sha256(payload["schedule_artifact_sha256"], "schedule_artifact_sha256")
    for field in (
        "parser_id",
        "parser_version",
        "iana_tzdb_version",
        "parsed_release_identifier",
        "reference_period",
        "published_timezone",
    ):
        _require_token(payload[field], field)
    if payload["published_timezone"] != "America/New_York":
        _fail("published_timezone must be America/New_York")
    _require_local_date(payload["published_local_date"], "published_local_date")
    _require_local_time(payload["published_local_time"], "published_local_time")
    for field in (
        "retrieved_at",
        "authoritative_release_time",
        "plan_commitment_deadline",
        "information_cutoff",
        "execution_window_open",
        "execution_window_close",
        "external_proof_deadline",
        "durability_completion_deadline",
        "resolution_deadline",
    ):
        _require_utc(payload[field], field)
    if payload["information_cutoff"] != payload["execution_window_open"]:
        _fail("information_cutoff must equal execution_window_open")
    if not (
        payload["plan_commitment_deadline"]
        < payload["information_cutoff"]
        < payload["execution_window_close"]
        < payload["external_proof_deadline"]
        < payload["authoritative_release_time"]
        < payload["resolution_deadline"]
    ):
        _fail("ScheduleDerivationEvidence timestamp ordering is invalid")
    if payload["durability_completion_deadline"] != payload["authoritative_release_time"]:
        _fail("durability_completion_deadline must equal authoritative_release_time")
    context = (
        f"genesis-schedule-derivation:{payload['target_ref']['object_id']}:"
        f"{payload['reference_period']}:{payload['schedule_artifact_sha256']}"
    )
    return _seal(payload, object_type="ScheduleDerivationEvidence", stable_context=context)


def reconstruct_target_instance(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require_exact_fields(payload, _TARGET_INSTANCE_FIELDS, "TargetInstance")
    for field in (
        "trusted_manifest_ref",
        "issuance_schedule_policy_ref",
        "target_ref",
        "schedule_source_ref",
        "measurement_source_ref",
        "schedule_derivation_evidence_ref",
    ):
        _require_ref(payload[field], field)
    _require_token(payload["reference_period"], "reference_period")
    _require_token(payload["release_identifier"], "release_identifier")
    for field in ("outcome_information_barrier", "information_cutoff", "resolution_deadline"):
        _require_utc(payload[field], field)
    if not payload["information_cutoff"] < payload["outcome_information_barrier"] < payload["resolution_deadline"]:
        _fail("TargetInstance timestamp ordering is invalid")
    context = f"genesis-target-instance:{payload['target_ref']['object_id']}:{payload['reference_period']}"
    return _seal(payload, object_type="TargetInstance", stable_context=context)


def reconstruct_forecast_slot(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require_exact_fields(payload, _FORECAST_SLOT_FIELDS, "ForecastSlot")
    for field in (
        "trusted_manifest_ref",
        "issuance_schedule_policy_ref",
        "target_instance_ref",
        "schedule_derivation_evidence_ref",
        "method_ref",
    ):
        _require_ref(payload[field], field)
    _require_ref_array(payload["source_contract_refs"], "source_contract_refs", minimum=2, maximum=2)
    _require_utc(payload["information_cutoff"], "information_cutoff")
    _require_token(payload["output_schema"], "output_schema")
    _require_token(payload["selection_control_class"], "selection_control_class")
    if payload["output_schema"] != "continuous_scalar_forecast_v1":
        _fail("Genesis v1 ForecastSlot output_schema is fixed")
    if payload["selection_control_class"] != "DETERMINISTIC_REPLAY":
        _fail("Genesis v1 ForecastSlot selection_control_class is fixed")
    if payload["forecast_cardinality"] != 1:
        _fail("Genesis v1 ForecastSlot forecast_cardinality must be 1")
    context = (
        f"genesis-forecast-slot:{payload['target_instance_ref']['object_id']}:"
        f"{payload['method_ref']['object_id']}"
    )
    return _seal(payload, object_type="ForecastSlot", stable_context=context)


def reconstruct_issuance_cycle_plan(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require_exact_fields(payload, _CYCLE_PLAN_FIELDS, "IssuanceCyclePlan")
    for field in (
        "trusted_manifest_ref",
        "schedule_policy_ref",
        "schedule_derivation_evidence_ref",
        "target_instance_ref",
        "retry_policy_ref",
        "omission_policy_ref",
    ):
        _require_ref(payload[field], field)
    _require_ref_array(payload["method_refs"], "method_refs", minimum=1)
    _require_ref_array(payload["expected_slots"], "expected_slots", minimum=1)
    for field in (
        "information_cutoff",
        "plan_commitment_deadline",
        "execution_window_open",
        "execution_window_close",
        "external_proof_deadline",
        "durability_completion_deadline",
    ):
        _require_utc(payload[field], field)
    if payload["information_cutoff"] != payload["execution_window_open"]:
        _fail("information_cutoff must equal execution_window_open")
    if not (
        payload["plan_commitment_deadline"]
        < payload["execution_window_open"]
        < payload["execution_window_close"]
        < payload["external_proof_deadline"]
        < payload["durability_completion_deadline"]
    ):
        _fail("IssuanceCyclePlan timestamp ordering is invalid")
    context = f"genesis-issuance-cycle-plan:{payload['target_instance_ref']['object_id']}"
    return _seal(payload, object_type="IssuanceCyclePlan", stable_context=context)


def _require_empty(row: Mapping[str, Any], fields: Sequence[str], reason: str) -> None:
    if any(row[field] for field in fields):
        _fail(reason)


def _validate_accounting_row(row: Any) -> None:
    if not isinstance(row, Mapping) or set(row) != _ACCOUNTING_FIELDS:
        _fail("slot_accounting row fields invalid")
    _require_ref(row["slot_ref"], "slot_accounting.slot_ref")
    for field in _ACCOUNTING_REF_ARRAYS:
        _require_ref_array(row[field], f"slot_accounting.{field}")
    outcome = row["issuance_outcome"]
    eligibility = row["eligibility_state"]
    withdrawal = row["withdrawal_state"]
    if outcome not in {"EXPECTED", "ISSUED", "FAILED", "OMITTED"}:
        _fail("slot_accounting issuance_outcome invalid")
    if eligibility not in {
        "NOT_YET_DETERMINED",
        "ELIGIBLE",
        "INELIGIBLE",
        "UNRESOLVED",
        "NOT_APPLICABLE",
    }:
        _fail("slot_accounting eligibility_state invalid")
    if withdrawal not in {"ACTIVE", "WITHDRAWN"}:
        _fail("slot_accounting withdrawal_state invalid")

    if outcome == "EXPECTED":
        if eligibility != "NOT_YET_DETERMINED" or withdrawal != "ACTIVE":
            _fail("EXPECTED slot state combination invalid")
        _require_empty(row, _ACCOUNTING_REF_ARRAYS, "EXPECTED slot cannot contain lifecycle refs")
        return
    if outcome == "FAILED":
        if eligibility != "NOT_APPLICABLE" or withdrawal != "ACTIVE":
            _fail("FAILED slot state combination invalid")
        if not row["attempt_refs"] or not row["failure_record_refs"]:
            _fail("FAILED slot requires attempts and failure records")
        _require_empty(
            row,
            (
                "issued_forecast_refs",
                "omission_evidence_refs",
                "ineligibility_evidence_refs",
                "unresolved_evidence_refs",
                "withdrawal_refs",
                "correction_refs",
            ),
            "FAILED slot contains prohibited lifecycle refs",
        )
        return
    if outcome == "OMITTED":
        if eligibility != "NOT_APPLICABLE" or withdrawal != "ACTIVE":
            _fail("OMITTED slot state combination invalid")
        if not row["omission_evidence_refs"]:
            _fail("OMITTED slot requires omission evidence")
        _require_empty(
            row,
            (
                "issued_forecast_refs",
                "ineligibility_evidence_refs",
                "unresolved_evidence_refs",
                "withdrawal_refs",
                "correction_refs",
            ),
            "OMITTED slot contains prohibited lifecycle refs",
        )
        return

    if not row["attempt_refs"] or len(row["issued_forecast_refs"]) != 1:
        _fail("ISSUED slot requires retained attempts and exactly one original forecast")
    if row["omission_evidence_refs"]:
        _fail("ISSUED slot cannot contain omission evidence")
    if eligibility == "INELIGIBLE":
        if not row["ineligibility_evidence_refs"] or row["unresolved_evidence_refs"]:
            _fail("INELIGIBLE slot evidence invalid")
    elif eligibility == "UNRESOLVED":
        if not row["unresolved_evidence_refs"] or row["ineligibility_evidence_refs"]:
            _fail("UNRESOLVED slot evidence invalid")
    elif eligibility in {"ELIGIBLE", "NOT_YET_DETERMINED"}:
        _require_empty(
            row,
            ("ineligibility_evidence_refs", "unresolved_evidence_refs"),
            "eligible or pending slot cannot contain contrary eligibility evidence",
        )
    else:
        _fail("ISSUED slot eligibility_state invalid")
    if withdrawal == "WITHDRAWN":
        if not row["withdrawal_refs"]:
            _fail("WITHDRAWN slot requires additive withdrawal refs")
    elif row["withdrawal_refs"]:
        _fail("ACTIVE slot cannot contain withdrawal refs")


def reconstruct_issuance_cycle_manifest(payload: Mapping[str, Any]) -> dict[str, Any]:
    _require_exact_fields(payload, _CYCLE_MANIFEST_FIELDS, "IssuanceCycleManifest")
    for field in (
        "trusted_manifest_ref",
        "cycle_plan_ref",
        "retry_policy_ref",
        "omission_policy_ref",
        "correction_policy_ref",
        "evaluation_policy_ref",
    ):
        _require_ref(payload[field], field)
    rows = payload["slot_accounting"]
    if not isinstance(rows, list) or not rows:
        _fail("slot_accounting must be a nonempty list")
    for row in rows:
        _validate_accounting_row(row)
    keys = [
        (row["slot_ref"]["object_id"], row["slot_ref"]["content_sha256"])
        for row in rows
    ]
    if keys != sorted(keys):
        _fail("slot_accounting must be sorted by slot_ref")
    if len(keys) != len(set(keys)):
        _fail("slot_accounting slot refs must be unique")
    context = f"genesis-issuance-cycle-manifest:{payload['cycle_plan_ref']['object_id']}"
    return _seal(payload, object_type="IssuanceCycleManifest", stable_context=context)


def require_schedule_derivation_authority(
    evidence: Mapping[str, Any],
    *,
    trusted_manifest: Mapping[str, Any],
    schedule_policy: Mapping[str, Any],
    target_definition: Mapping[str, Any],
    schedule_artifact: Mapping[str, Any],
    tzdb_artifact: Mapping[str, Any],
    validator_contract: Mapping[str, Any],
) -> None:
    """Cross-bind supporting schedule evidence; this does not parse or derive schedule facts."""

    from .claim_authority_trust_root_v1 import (
        derive_genesis_runtime_v1_authority_context,
    )

    try:
        context = derive_genesis_runtime_v1_authority_context(
            trusted_manifest, schedule_policy
        )
    except ValueError as exc:
        _fail(str(exc))
    manifest_ref = _exact_ref(trusted_manifest, "TrustedManifest")
    policy_ref = _exact_ref(schedule_policy, "PolicyDefinition")
    target_ref = _exact_ref(target_definition, "TargetDefinition")
    artifact_ref = _exact_ref(schedule_artifact, "RetainedScheduleArtifact")
    tzdb_ref = _exact_ref(tzdb_artifact, "IanaTzdbArtifact")
    validator_ref = _exact_ref(validator_contract, "ValidatorContract")
    if policy_ref != dict(context.issuance_schedule_policy_ref):
        _fail("schedule policy differs from TrustedManifest authority")
    if target_ref not in [dict(item) for item in context.target_refs]:
        _fail("target differs from TrustedManifest authority")
    if validator_ref != dict(context.validator_contract_ref):
        _fail("validator contract differs from TrustedManifest authority")
    schedule_source_ref = _require_ref(target_definition.get("schedule_source_ref"), "TargetDefinition.schedule_source_ref")
    if schedule_source_ref not in [dict(item) for item in context.source_contract_refs]:
        _fail("target schedule source differs from TrustedManifest authority")
    payload = _payload_from_sealed(evidence, "ScheduleDerivationEvidence")
    if reconstruct_schedule_derivation_evidence(payload) != dict(evidence):
        _fail("ScheduleDerivationEvidence identity was not canonically reconstructed")
    expected = {
        "trusted_manifest_ref": manifest_ref,
        "issuance_schedule_policy_ref": policy_ref,
        "target_ref": target_ref,
        "schedule_source_ref": schedule_source_ref,
        "schedule_artifact_ref": artifact_ref,
        "parser_id": validator_contract.get("schedule_parser_id"),
        "parser_version": validator_contract.get("schedule_parser_version"),
        "published_timezone": schedule_policy.get("normative_timezone"),
        "tzdb_artifact_ref": tzdb_ref,
        "iana_tzdb_version": tzdb_artifact.get("iana_tzdb_version"),
    }
    for field, value in expected.items():
        if evidence.get(field) != value:
            _fail(f"ScheduleDerivationEvidence {field} is not bound to exact authority")
    if evidence["schedule_artifact_sha256"] != schedule_artifact.get("raw_sha256"):
        _fail("ScheduleDerivationEvidence artifact SHA256 differs from retained artifact")
    if validator_contract.get("schedule_parser_id") != schedule_policy.get("schedule_parser_id"):
        _fail("validator parser_id differs from schedule policy authority")


def require_issuance_cycle_manifest_authority(
    payload: Mapping[str, Any],
    *,
    trusted_manifest: Mapping[str, Any],
    schedule_policy: Mapping[str, Any],
    target_definition: Mapping[str, Any],
    forecast_methods: Sequence[Mapping[str, Any]],
    schedule_artifact: Mapping[str, Any],
    tzdb_artifact: Mapping[str, Any],
    validator_contract: Mapping[str, Any],
    schedule_derivation_evidence: Mapping[str, Any],
    target_instance: Mapping[str, Any],
    forecast_slots: Sequence[Mapping[str, Any]],
    issuance_cycle_plan: Mapping[str, Any],
) -> None:
    """Require one exact, manifest-rooted runtime authority chain."""

    from .claim_authority_trust_root_v1 import (
        derive_genesis_runtime_v1_authority_context,
    )

    try:
        context = derive_genesis_runtime_v1_authority_context(
            trusted_manifest, schedule_policy
        )
    except ValueError as exc:
        _fail(str(exc))
    manifest_ref = _exact_ref(trusted_manifest, "TrustedManifest")
    policy_ref = _exact_ref(schedule_policy, "PolicyDefinition")
    target_ref = _exact_ref(target_definition, "TargetDefinition")
    evidence_ref = _exact_ref(schedule_derivation_evidence, "ScheduleDerivationEvidence")
    target_instance_ref = _exact_ref(target_instance, "TargetInstance")
    plan_ref = _exact_ref(issuance_cycle_plan, "IssuanceCyclePlan")

    methods_by_ref: dict[tuple[str, str], Mapping[str, Any]] = {}
    for method in forecast_methods:
        method_payload = _payload_from_sealed(method, "ForecastMethod")
        compatible_target_refs = _require_ref_array(
            method_payload.get("compatible_target_refs"),
            "ForecastMethod.compatible_target_refs",
            minimum=1,
        )
        method_ref = _exact_ref(method, "ForecastMethod")
        method_key = (method_ref["object_id"], method_ref["content_sha256"])
        if method_key in methods_by_ref:
            _fail("ForecastMethod authority inputs must be unique")
        methods_by_ref[method_key] = {
            **method,
            "compatible_target_refs": compatible_target_refs,
        }
    method_refs = sorted_refs(
        {"object_id": key[0], "content_sha256": key[1]}
        for key in methods_by_ref
    )
    if method_refs != [dict(item) for item in context.method_refs]:
        _fail("ForecastMethod objects differ from TrustedManifest authority")
    compatible_method_refs = [
        method_ref
        for method_ref in method_refs
        if target_ref
        in methods_by_ref[(method_ref["object_id"], method_ref["content_sha256"])][
            "compatible_target_refs"
        ]
    ]
    if not compatible_method_refs:
        _fail("no manifest-admitted ForecastMethod compatible_target_refs include target")

    manifest = reconstruct_issuance_cycle_manifest(payload)
    if any(
        row["eligibility_state"] == "ELIGIBLE" for row in manifest["slot_accounting"]
    ):
        _fail("ELIGIBLE slot requires complete authoritative eligibility derivation")
    if manifest.get("cycle_plan_ref") != plan_ref:
        _fail("IssuanceCycleManifest cycle_plan_ref is not bound to exact authority")
    accounted_slots = [row["slot_ref"] for row in manifest["slot_accounting"]]

    require_schedule_derivation_authority(
        schedule_derivation_evidence,
        trusted_manifest=trusted_manifest,
        schedule_policy=schedule_policy,
        target_definition=target_definition,
        schedule_artifact=schedule_artifact,
        tzdb_artifact=tzdb_artifact,
        validator_contract=validator_contract,
    )

    target_payload = _payload_from_sealed(target_instance, "TargetInstance")
    if reconstruct_target_instance(target_payload) != dict(target_instance):
        _fail("TargetInstance identity was not canonically reconstructed")
    target_expected = {
        "trusted_manifest_ref": manifest_ref,
        "issuance_schedule_policy_ref": policy_ref,
        "target_ref": target_ref,
        "schedule_source_ref": target_definition.get("schedule_source_ref"),
        "measurement_source_ref": target_definition.get("measurement_source_ref"),
        "schedule_derivation_evidence_ref": evidence_ref,
        "reference_period": schedule_derivation_evidence.get("reference_period"),
        "release_identifier": schedule_derivation_evidence.get("parsed_release_identifier"),
        "outcome_information_barrier": schedule_derivation_evidence.get("authoritative_release_time"),
        "information_cutoff": schedule_derivation_evidence.get("information_cutoff"),
        "resolution_deadline": schedule_derivation_evidence.get("resolution_deadline"),
    }
    for field, value in target_expected.items():
        if target_instance.get(field) != value:
            _fail(f"TargetInstance {field} is not bound to exact authority")

    authorized_sources = sorted_refs(
        [target_definition.get("schedule_source_ref"), target_definition.get("measurement_source_ref")]
    )
    if len(compatible_method_refs) != 1:
        _fail("Genesis v1 requires exactly one target-compatible ForecastMethod")
    mandatory_method_ref = compatible_method_refs[0]
    mandatory_method = methods_by_ref[
        (mandatory_method_ref["object_id"], mandatory_method_ref["content_sha256"])
    ]
    mandatory_slot = reconstruct_forecast_slot(
        {
            "schema_version": "1.0",
            "trusted_manifest_ref": manifest_ref,
            "issuance_schedule_policy_ref": policy_ref,
            "target_instance_ref": target_instance_ref,
            "schedule_derivation_evidence_ref": evidence_ref,
            "method_ref": mandatory_method_ref,
            "source_contract_refs": authorized_sources,
            "information_cutoff": schedule_derivation_evidence.get("information_cutoff"),
            "output_schema": mandatory_method.get("output_schema"),
            "selection_control_class": mandatory_method.get("selection_control_class"),
            "forecast_cardinality": 1,
        }
    )
    mandatory_slot_refs = [_exact_ref(mandatory_slot, "ForecastSlot")]
    caller_slot_refs = sorted_refs(
        _exact_ref(slot, "ForecastSlot") for slot in forecast_slots
    )
    if issuance_cycle_plan.get("expected_slots") != mandatory_slot_refs:
        _fail("IssuanceCyclePlan expected_slots differs from mandatory ForecastSlot denominator")
    if accounted_slots != mandatory_slot_refs:
        _fail("IssuanceCycleManifest slot_accounting differs from mandatory expected_slots denominator")
    for slot in forecast_slots:
        slot_payload = _payload_from_sealed(slot, "ForecastSlot")
        if reconstruct_forecast_slot(slot_payload) != dict(slot):
            _fail("ForecastSlot identity was not canonically reconstructed")
        if slot.get("trusted_manifest_ref") != manifest_ref:
            _fail("ForecastSlot trusted_manifest_ref is not bound to exact authority")
        if slot.get("issuance_schedule_policy_ref") != policy_ref:
            _fail("ForecastSlot issuance_schedule_policy_ref is not bound to exact authority")
        if slot.get("target_instance_ref") != target_instance_ref:
            _fail("ForecastSlot target_instance_ref is not bound to exact authority")
        if slot.get("schedule_derivation_evidence_ref") != evidence_ref:
            _fail("ForecastSlot schedule_derivation_evidence_ref is not bound to exact authority")
        if slot.get("method_ref") not in compatible_method_refs:
            _fail("ForecastSlot method_ref is absent from ForecastMethod compatible_target_refs")
        method_ref = slot["method_ref"]
        method = methods_by_ref[(method_ref["object_id"], method_ref["content_sha256"])]
        if slot.get("output_schema") != method.get("output_schema"):
            _fail("ForecastSlot output_schema differs from exact ForecastMethod authority")
        if slot.get("selection_control_class") != method.get("selection_control_class"):
            _fail("ForecastSlot selection_control_class differs from exact ForecastMethod authority")
        if slot.get("source_contract_refs") != authorized_sources:
            _fail("ForecastSlot source_contract_refs differ from target source authority")
        if slot.get("information_cutoff") != schedule_derivation_evidence.get("information_cutoff"):
            _fail("ForecastSlot information_cutoff is not bound to schedule authority")
    if caller_slot_refs != mandatory_slot_refs:
        _fail("caller supplied ForecastSlots differ from mandatory ForecastSlot denominator")

    plan_payload = _payload_from_sealed(issuance_cycle_plan, "IssuanceCyclePlan")
    if reconstruct_issuance_cycle_plan(plan_payload) != dict(issuance_cycle_plan):
        _fail("IssuanceCyclePlan identity was not canonically reconstructed")
    plan_expected = {
        "trusted_manifest_ref": manifest_ref,
        "schedule_policy_ref": policy_ref,
        "schedule_derivation_evidence_ref": evidence_ref,
        "target_instance_ref": target_instance_ref,
        "method_refs": compatible_method_refs,
        "information_cutoff": schedule_derivation_evidence.get("information_cutoff"),
        "plan_commitment_deadline": schedule_derivation_evidence.get("plan_commitment_deadline"),
        "execution_window_open": schedule_derivation_evidence.get("execution_window_open"),
        "execution_window_close": schedule_derivation_evidence.get("execution_window_close"),
        "external_proof_deadline": schedule_derivation_evidence.get("external_proof_deadline"),
        "durability_completion_deadline": schedule_derivation_evidence.get("durability_completion_deadline"),
        "expected_slots": mandatory_slot_refs,
        "retry_policy_ref": dict(context.retry_policy_ref),
        "omission_policy_ref": dict(context.omission_policy_ref),
    }
    for field, value in plan_expected.items():
        if issuance_cycle_plan.get(field) != value:
            _fail(f"IssuanceCyclePlan {field} is not bound to exact authority")

    manifest_expected = {
        "trusted_manifest_ref": manifest_ref,
        "cycle_plan_ref": plan_ref,
        "retry_policy_ref": dict(context.retry_policy_ref),
        "omission_policy_ref": dict(context.omission_policy_ref),
        "correction_policy_ref": dict(context.correction_policy_ref),
        "evaluation_policy_ref": dict(context.evaluation_policy_ref),
    }
    for field, value in manifest_expected.items():
        if manifest.get(field) != value:
            _fail(f"IssuanceCycleManifest {field} is not bound to exact authority")

