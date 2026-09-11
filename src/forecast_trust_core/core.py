from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Sequence

from .canonical import CanonicalizationError, require_decimal_string, require_utc_timestamp, sorted_refs, timestamp_le, validate_ref, verify_sealed_object


class Result(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    INELIGIBLE_TRUST_UNKNOWN = "INELIGIBLE_TRUST_UNKNOWN"
    PENDING_EXTERNAL_ANCHOR = "PENDING_EXTERNAL_ANCHOR"
    VALID_NON_PROSPECTIVE = "VALID_NON_PROSPECTIVE"
    LATE_OR_INELIGIBLE = "LATE_OR_INELIGIBLE"


@dataclass(frozen=True)
class Check:
    check_id: str
    status: str
    reason_code: str


@dataclass(frozen=True)
class Validation:
    result: Result
    checks: tuple[Check, ...]

    @property
    def valid(self) -> bool:
        return self.result == Result.VALID


def _check(check_id: str, passed: bool | None, reason: str) -> Check:
    return Check(check_id, "PASS" if passed is True else "UNKNOWN" if passed is None else "FAIL", reason)


def aggregate(checks: Sequence[Check], *, pending_anchor: bool = False, non_prospective: bool = False) -> Validation:
    if any(c.status == "FAIL" for c in checks):
        return Validation(Result.INVALID, tuple(checks))
    if any(c.status == "UNKNOWN" for c in checks):
        return Validation(Result.INELIGIBLE_TRUST_UNKNOWN, tuple(checks))
    if pending_anchor:
        return Validation(Result.PENDING_EXTERNAL_ANCHOR, tuple(checks))
    if non_prospective:
        return Validation(Result.VALID_NON_PROSPECTIVE, tuple(checks))
    return Validation(Result.VALID, tuple(checks))


def validate_dependency(ref: Mapping[str, Any], store: Mapping[str, Mapping[str, Any]], allowed_refs: Sequence[Mapping[str, str]]) -> Check:
    try:
        validate_ref(ref)
    except CanonicalizationError:
        return _check("dependency_ref", False, "MALFORMED_REFERENCE")
    allowed = {(r["object_id"], r["content_sha256"]) for r in allowed_refs}
    pair = (ref["object_id"], ref["content_sha256"])
    if pair not in allowed:
        return _check("dependency_ref", False, "NOT_ADMITTED_BY_TRUST_ROOT")
    candidate = store.get(ref["object_id"])
    if candidate is None:
        return _check("dependency_ref", None, "DEPENDENCY_MISSING")
    if candidate.get("content_sha256") != ref["content_sha256"]:
        return _check("dependency_ref", False, "DEPENDENCY_HASH_MISMATCH")
    if not verify_sealed_object(candidate):
        return _check("dependency_ref", False, "DEPENDENCY_OBJECT_INVALID")
    return _check("dependency_ref", True, "OK")


def validate_point_in_time(members: Sequence[Mapping[str, Any]], information_cutoff: str) -> Validation:
    checks: list[Check] = []
    try:
        require_utc_timestamp(information_cutoff)
    except CanonicalizationError:
        return aggregate([_check("information_cutoff", False, "INVALID_TIMESTAMP")])
    for idx, member in enumerate(members):
        available = member.get("available_at")
        if available is None:
            checks.append(_check(f"member_{idx}_availability", None, "AVAILABILITY_UNKNOWN"))
            continue
        try:
            eligible = timestamp_le(available, information_cutoff)
        except CanonicalizationError:
            checks.append(_check(f"member_{idx}_availability", False, "INVALID_TIMESTAMP"))
        else:
            checks.append(_check(f"member_{idx}_availability", eligible, "OK" if eligible else "FUTURE_INFORMATION"))
    return aggregate(checks)


def validate_probability(value: Any) -> Check:
    try:
        require_decimal_string(value, probability=True)
    except CanonicalizationError:
        return _check("prediction_probability", False, "NONCANONICAL_PROBABILITY")
    return _check("prediction_probability", True, "OK")


def validate_cycle_plan(plan: Mapping[str, Any], *, verified_plan_existence_bound: str | None, required_slots: Sequence[Mapping[str, Any]]) -> Validation:
    checks: list[Check] = []
    if not verify_sealed_object(plan):
        return aggregate([_check("plan_seal", False, "INVALID_SEAL")])
    for field in ("plan_commitment_deadline", "execution_window_open", "execution_window_close"):
        try:
            require_utc_timestamp(plan[field])
            checks.append(_check(field, True, "OK"))
        except (KeyError, CanonicalizationError):
            checks.append(_check(field, False, "INVALID_OR_MISSING_TIMESTAMP"))
    if any(c.status == "FAIL" for c in checks):
        return aggregate(checks)
    checks.append(_check("deadline_before_window", plan["plan_commitment_deadline"] < plan["execution_window_open"], "PLAN_DEADLINE_NOT_BEFORE_WINDOW"))
    if verified_plan_existence_bound is None:
        checks.append(_check("plan_external_precommitment", None, "PLAN_EXISTENCE_BOUND_UNKNOWN"))
    else:
        try:
            ok = timestamp_le(verified_plan_existence_bound, plan["plan_commitment_deadline"])
        except CanonicalizationError:
            ok = False
        checks.append(_check("plan_external_precommitment", ok, "PLAN_COMMITTED_LATE" if not ok else "OK"))
    expected = plan.get("expected_slots", [])
    try:
        normalized_expected = sorted_refs(expected)
        normalized_required = sorted_refs(required_slots)
        checks.append(_check("slot_order", expected == normalized_expected, "UNSORTED_SLOT_SET"))
        checks.append(_check("deterministic_slots", normalized_expected == normalized_required, "SLOT_SET_MISMATCH"))
    except CanonicalizationError:
        checks.append(_check("deterministic_slots", False, "INVALID_SLOT_REFERENCE"))
    return aggregate(checks)


def validate_cycle_manifest(plan: Mapping[str, Any], manifest: Mapping[str, Any]) -> Validation:
    checks: list[Check] = []
    if not verify_sealed_object(manifest):
        return aggregate([_check("manifest_seal", False, "INVALID_SEAL")])
    if "anchor_subject_hash" in manifest:
        checks.append(_check("anchor_self_reference", False, "ANCHOR_SUBJECT_SELF_REFERENCE"))
    expected_ids = [r["object_id"] for r in plan.get("expected_slots", [])]
    accounting = manifest.get("slot_accounting", [])
    seen = [row.get("slot_ref", {}).get("object_id") for row in accounting]
    checks.append(_check("slot_completeness", sorted(seen) == sorted(expected_ids) and len(seen) == len(set(seen)), "INCOMPLETE_OR_DUPLICATE_SLOT_ACCOUNTING"))
    cardinality_ok = True
    for row in accounting:
        if row.get("outcome") == "ISSUED":
            refs = row.get("issued_forecast_refs", [])
            if not isinstance(refs, list) or len(refs) != 1:
                cardinality_ok = False
    checks.append(_check("slot_cardinality", cardinality_ok, "VERSION1_SLOT_CARDINALITY_NOT_ONE"))
    return aggregate(checks)


def validate_selection_control(method: Mapping[str, Any], run: Mapping[str, Any]) -> Validation:
    klass = method.get("selection_control_class")
    if klass == "DETERMINISTIC_REPLAY":
        return aggregate([_check("selection_control", run.get("replay_verified") is True, "DETERMINISTIC_REPLAY_NOT_VERIFIED")])
    if klass == "PRECOMMITTED_RANDOMNESS":
        return aggregate([_check("selection_control", isinstance(run.get("public_randomness_ref"), dict), "PUBLIC_RANDOMNESS_NOT_BOUND")])
    if klass == "EXTERNALLY_AUDITED_ATTEMPTS":
        return aggregate([_check("selection_control", run.get("complete_request_accounting") is True, "REQUEST_ACCOUNTING_INCOMPLETE")])
    if klass == "UNCONTROLLED_NONDETERMINISM":
        return aggregate([_check("selection_control", False, "UNCONTROLLED_NONDETERMINISM")])
    return aggregate([_check("selection_control", None, "SELECTION_CONTROL_UNKNOWN")])


def validate_external_deadline(existence_bound: str | None, deadline: str) -> Validation:
    if existence_bound is None:
        return Validation(Result.PENDING_EXTERNAL_ANCHOR, (_check("external_proof", None, "PENDING_EXTERNAL_PROOF"),))
    try:
        ok = timestamp_le(existence_bound, deadline)
    except CanonicalizationError:
        return aggregate([_check("external_proof", False, "INVALID_EXTERNAL_TIME")])
    if ok:
        return aggregate([_check("external_proof", True, "OK")])
    return Validation(Result.LATE_OR_INELIGIBLE, (_check("external_proof", False, "EXTERNAL_PROOF_AFTER_DEADLINE"),))
