from __future__ import annotations

from typing import Any, Callable, Mapping

from .canonical import (
    parse_json_strict,
    require_utc_timestamp,
    validate_ref,
)
from .qualification_validation_contracts_v1 import (
    validate_qualification_validation_result,
)


ADMISSION_REASON_CODES = (
    "RESULT_UNAVAILABLE_OR_UNAUTHENTICATED",
    "VALIDATION_STATUS_NOT_VALID",
    "VALIDATION_CONTRACT_REF_MISMATCH",
    "PROVIDER_PROFILE_REF_MISMATCH",
    "QUALIFICATION_DECISION_REF_MISMATCH",
    "HISTORY_SNAPSHOT_REF_MISMATCH",
    "DEADLINE_MISMATCH",
    "QUALIFICATION_STATE_NOT_PRODUCTION_QUALIFIED",
)


class QualificationAdmissionError(ValueError):
    """An exact qualification validation result is not admission eligible."""

    def __init__(self, reason: str) -> None:
        if reason not in ADMISSION_REASON_CODES:
            raise ValueError("unknown qualification admission reason")
        self.reason = reason
        super().__init__("qualification admission failed")


def _authenticate_result(
    expected_result_ref: Mapping[str, Any],
    resolve_result: Callable[[Mapping[str, str]], bytes | bytearray | str],
) -> dict[str, Any]:
    try:
        validate_ref(expected_result_ref)
        exact_expected_ref = dict(expected_result_ref)
        candidate = resolve_result(dict(exact_expected_ref))
        if isinstance(candidate, bytearray):
            candidate = bytes(candidate)
        if not isinstance(candidate, (bytes, str)):
            raise TypeError("result resolver must return stable serialized bytes or text")
        parsed = parse_json_strict(candidate)
        actual_ref = validate_qualification_validation_result(parsed)
        if actual_ref != exact_expected_ref:
            raise ValueError("resolved result reference mismatch")
        return dict(parsed)
    except Exception as exc:
        raise QualificationAdmissionError(
            "RESULT_UNAVAILABLE_OR_UNAUTHENTICATED"
        ) from exc


def _require_expected_ref(
    value: Mapping[str, Any],
    *,
    mismatch_reason: str,
) -> dict[str, str]:
    try:
        validate_ref(value)
        return dict(value)
    except Exception as exc:
        raise QualificationAdmissionError(mismatch_reason) from exc


def _require_deadline(value: str) -> str:
    try:
        return require_utc_timestamp(value)
    except Exception as exc:
        raise QualificationAdmissionError("DEADLINE_MISMATCH") from exc


def require_qualification_admission(
    expected_result_ref: Mapping[str, Any],
    *,
    resolve_result: Callable[[Mapping[str, str]], bytes | bytearray | str],
    expected_qualification_validation_contract_ref: Mapping[str, Any],
    expected_provider_profile_ref: Mapping[str, Any],
    expected_qualification_decision_ref: Mapping[str, Any],
    expected_qualification_state_history_snapshot_ref: Mapping[str, Any],
    frozen_deadline_utc: str,
) -> dict[str, Any]:
    """Return the exact authenticated result iff every admission predicate holds."""

    result = _authenticate_result(expected_result_ref, resolve_result)

    if result["validation_status"] != "VALID":
        raise QualificationAdmissionError("VALIDATION_STATUS_NOT_VALID")

    expected_contract_ref = _require_expected_ref(
        expected_qualification_validation_contract_ref,
        mismatch_reason="VALIDATION_CONTRACT_REF_MISMATCH",
    )
    if result["qualification_validation_contract_ref"] != expected_contract_ref:
        raise QualificationAdmissionError("VALIDATION_CONTRACT_REF_MISMATCH")

    expected_profile_ref = _require_expected_ref(
        expected_provider_profile_ref,
        mismatch_reason="PROVIDER_PROFILE_REF_MISMATCH",
    )
    if result["provider_profile_ref"] != expected_profile_ref:
        raise QualificationAdmissionError("PROVIDER_PROFILE_REF_MISMATCH")

    expected_decision_ref = _require_expected_ref(
        expected_qualification_decision_ref,
        mismatch_reason="QUALIFICATION_DECISION_REF_MISMATCH",
    )
    if result["qualification_decision_ref"] != expected_decision_ref:
        raise QualificationAdmissionError("QUALIFICATION_DECISION_REF_MISMATCH")

    expected_history_ref = _require_expected_ref(
        expected_qualification_state_history_snapshot_ref,
        mismatch_reason="HISTORY_SNAPSHOT_REF_MISMATCH",
    )
    if result["qualification_state_history_snapshot_ref"] != expected_history_ref:
        raise QualificationAdmissionError("HISTORY_SNAPSHOT_REF_MISMATCH")

    exact_deadline = _require_deadline(frozen_deadline_utc)
    if result["as_of_utc"] != exact_deadline:
        raise QualificationAdmissionError("DEADLINE_MISMATCH")

    if result["qualification_state"] != "PRODUCTION_QUALIFIED":
        raise QualificationAdmissionError(
            "QUALIFICATION_STATE_NOT_PRODUCTION_QUALIFIED"
        )

    return result
