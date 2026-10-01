from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

import pytest

import forecast_trust_core.qualification_state_package_v2 as phase4d
import forecast_trust_core.qualification_validation_v1 as phase4e
from forecast_trust_core.canonical import canonical_json, seal_object
from forecast_trust_core.qualification_admission_v1 import (
    QualificationAdmissionError,
    require_qualification_admission,
)
from forecast_trust_core.qualification_validation_contracts_v1 import (
    build_qualification_validation_result,
)


AUTH_FAILURE = "RESULT_UNAVAILABLE_OR_UNAUTHENTICATED"
DEADLINE = "2026-09-20T00:00:00Z"
EARLIER = "2026-09-19T23:59:59Z"
LATER = "2026-09-20T00:00:01Z"


def exact_ref(object_id: str, digit: str) -> dict[str, str]:
    return {"object_id": object_id, "content_sha256": digit * 64}


CONTRACT_REF = exact_ref("qualification-validation-contract:test:v1", "1")
INVOCATION_REF = exact_ref("qualification-validation-invocation:test:v1", "2")
PACKAGE_REF = exact_ref("qualification-state-package:test:v2", "3")
PROFILE_REF = exact_ref("provider-profile:test:v1", "4")
DECISION_REF = exact_ref("qualification-decision:test:v1", "5")
HISTORY_REF = exact_ref("qualification-history:test:v1", "6")


def ref(obj: Mapping[str, Any]) -> dict[str, str]:
    return {
        "object_id": obj["object_id"],
        "content_sha256": obj["content_sha256"],
    }


def valid_result(
    *,
    state: str = "PRODUCTION_QUALIFIED",
    deadline: str = DEADLINE,
    contract_ref: Mapping[str, str] = CONTRACT_REF,
    profile_ref: Mapping[str, str] = PROFILE_REF,
    decision_ref: Mapping[str, str] = DECISION_REF,
    history_ref: Mapping[str, str] = HISTORY_REF,
    report_hash: str = "7" * 64,
) -> dict[str, Any]:
    return build_qualification_validation_result(
        {
            "schema_version": "1.0",
            "qualification_validation_contract_ref": dict(contract_ref),
            "qualification_validation_invocation_ref": dict(INVOCATION_REF),
            "qualification_state_package_ref": dict(PACKAGE_REF),
            "validation_status": "VALID",
            "provider_profile_ref": dict(profile_ref),
            "qualification_decision_ref": dict(decision_ref),
            "qualification_state_history_snapshot_ref": dict(history_ref),
            "as_of_utc": deadline,
            "qualification_state": state,
            "derived_state_report_semantic_sha256": report_hash,
        }
    )


def invalid_result() -> dict[str, Any]:
    return build_qualification_validation_result(
        {
            "schema_version": "1.0",
            "qualification_validation_contract_ref": dict(CONTRACT_REF),
            "qualification_validation_invocation_ref": dict(INVOCATION_REF),
            "qualification_state_package_ref": dict(PACKAGE_REF),
            "validation_status": "INVALID",
            "primary_invalid_reason_code": "QUALIFICATION_STATE_DERIVATION_INVALID",
        }
    )


def resolver_for(result: Mapping[str, Any]):
    serialized = canonical_json(result)

    def resolve(_result_ref: Mapping[str, str]) -> bytes:
        return serialized

    return resolve


def admit(
    result: Mapping[str, Any],
    *,
    result_ref: Any = None,
    resolve_result=None,
    expected_contract_ref: Any = CONTRACT_REF,
    expected_profile_ref: Any = PROFILE_REF,
    expected_decision_ref: Any = DECISION_REF,
    expected_history_ref: Any = HISTORY_REF,
    frozen_deadline_utc: Any = DEADLINE,
) -> dict[str, Any]:
    return require_qualification_admission(
        ref(result) if result_ref is None else result_ref,
        resolve_result=resolve_result or resolver_for(result),
        expected_qualification_validation_contract_ref=expected_contract_ref,
        expected_provider_profile_ref=expected_profile_ref,
        expected_qualification_decision_ref=expected_decision_ref,
        expected_qualification_state_history_snapshot_ref=expected_history_ref,
        frozen_deadline_utc=frozen_deadline_utc,
    )


def assert_rejected(reason: str, result: Mapping[str, Any], **kwargs: Any) -> None:
    with pytest.raises(QualificationAdmissionError) as caught:
        admit(result, **kwargs)
    assert caught.value.reason == reason


def reseal(
    result: Mapping[str, Any],
    *,
    object_type: str = "QualificationValidationResult",
    stable_context: str = "v1",
    semantic_id: str | None = None,
    **updates: Any,
) -> dict[str, Any]:
    payload = {
        key: value
        for key, value in result.items()
        if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
    }
    payload.update(updates)
    return seal_object(
        payload,
        object_type=object_type,
        stable_context=stable_context,
        semantic_id=semantic_id,
    )


MALFORMED_REFS = [
    {"content_sha256": "d" * 64},
    {"object_id": "missing-content:test:v1"},
    {
        "object_id": "extra-field:test:v1",
        "content_sha256": "d" * 64,
        "extra": "forbidden",
    },
    {"object_id": None, "content_sha256": "d" * 64},
    {"object_id": "uppercase-digest:test:v1", "content_sha256": "D" * 64},
]


def test_exact_valid_production_qualified_result_is_returned_unchanged():
    result = valid_result()
    before = deepcopy(result)

    admitted = admit(result)

    assert admitted == before
    assert result == before
    assert set(admitted) == set(before)


@pytest.mark.parametrize(
    "state",
    [
        "QUALIFICATION_BLOCKED",
        "QUALIFICATION_EXPIRED",
        "REQUALIFICATION_REQUIRED",
    ],
)
def test_valid_non_production_state_is_admission_ineligible(state: str):
    assert_rejected(
        "QUALIFICATION_STATE_NOT_PRODUCTION_QUALIFIED",
        valid_result(state=state),
    )


def test_invalid_result_stops_before_reading_valid_only_fields():
    assert_rejected(
        "VALIDATION_STATUS_NOT_VALID",
        invalid_result(),
        expected_contract_ref=object(),
        expected_profile_ref=object(),
        expected_decision_ref=object(),
        expected_history_ref=object(),
        frozen_deadline_utc=object(),
    )


def test_invalid_result_with_forbidden_valid_fields_fails_authentication():
    result = reseal(invalid_result(), provider_profile_ref=dict(PROFILE_REF))

    assert_rejected(AUTH_FAILURE, result)


@pytest.mark.parametrize(
    "candidate",
    [
        b'{"not":"closed"',
        b'{"duplicate":1,"duplicate":2}',
        42,
    ],
    ids=["malformed-json", "duplicate-key", "wrong-transport-type"],
)
def test_malformed_candidate_fails_as_unavailable_or_unauthenticated(candidate: Any):
    result = valid_result()
    assert_rejected(
        AUTH_FAILURE,
        result,
        resolve_result=lambda _ref: candidate,
    )


def test_unavailable_result_fails_as_unavailable_or_unauthenticated():
    result = valid_result()

    def unavailable(_ref: Mapping[str, str]) -> bytes:
        raise FileNotFoundError("synthetic unavailable result")

    assert_rejected(AUTH_FAILURE, result, resolve_result=unavailable)


def test_unknown_result_field_fails_authentication():
    assert_rejected(AUTH_FAILURE, reseal(valid_result(), diagnostics=["forbidden"]))


def test_wrong_schema_version_fails_authentication():
    assert_rejected(AUTH_FAILURE, reseal(valid_result(), schema_version="2.0"))


def test_wrong_object_type_fails_authentication():
    assert_rejected(
        AUTH_FAILURE,
        reseal(valid_result(), object_type="NotQualificationValidationResult"),
    )


@pytest.mark.parametrize("field", ["payload_sha256", "content_sha256"])
def test_bad_standard_seal_hash_fails_authentication(field: str):
    result = valid_result()
    result[field] = "e" * 64

    assert_rejected(AUTH_FAILURE, result)


def test_nonstandard_object_id_fails_stable_context_authentication():
    result = reseal(valid_result(), semantic_id="qualification-result:wrong-id:v1")

    assert_rejected(AUTH_FAILURE, result)


def test_nonstandard_stable_context_fails_authentication():
    result = reseal(valid_result(), stable_context="not-v1")

    assert_rejected(AUTH_FAILURE, result)


def test_actual_result_ref_must_equal_expected_result_ref():
    result = valid_result()
    wrong_ref = {**ref(result), "content_sha256": "8" * 64}

    assert_rejected(AUTH_FAILURE, result, result_ref=wrong_ref)


def test_authentication_precedes_malformed_later_inputs():
    result = valid_result()
    assert_rejected(
        AUTH_FAILURE,
        result,
        resolve_result=lambda _ref: b"not-json",
        expected_profile_ref={"object_id": None},
        frozen_deadline_utc=object(),
    )


@pytest.mark.parametrize("malformed_ref", MALFORMED_REFS)
def test_malformed_expected_result_ref_fails_authentication(malformed_ref: Any):
    assert_rejected(AUTH_FAILURE, valid_result(), result_ref=malformed_ref)


@pytest.mark.parametrize(
    ("result_kwargs", "reason"),
    [
        (
            {"contract_ref": exact_ref("contract:wrong:v1", "9")},
            "VALIDATION_CONTRACT_REF_MISMATCH",
        ),
        (
            {"profile_ref": exact_ref("profile:wrong:v1", "9")},
            "PROVIDER_PROFILE_REF_MISMATCH",
        ),
        (
            {"decision_ref": exact_ref("decision:wrong:v1", "9")},
            "QUALIFICATION_DECISION_REF_MISMATCH",
        ),
        (
            {"history_ref": exact_ref("history:wrong:v1", "9")},
            "HISTORY_SNAPSHOT_REF_MISMATCH",
        ),
    ],
)
def test_each_authority_ref_must_exactly_match(
    result_kwargs: dict[str, Mapping[str, str]], reason: str
):
    assert_rejected(reason, valid_result(**result_kwargs))


def test_semantically_similar_provider_ref_is_not_equivalent():
    similar_profile_ref = {
        "object_id": PROFILE_REF["object_id"],
        "content_sha256": "a" * 64,
    }

    assert_rejected(
        "PROVIDER_PROFILE_REF_MISMATCH",
        valid_result(profile_ref=similar_profile_ref),
    )


@pytest.mark.parametrize(
    ("expected_kwarg", "reason"),
    [
        ("expected_contract_ref", "VALIDATION_CONTRACT_REF_MISMATCH"),
        ("expected_profile_ref", "PROVIDER_PROFILE_REF_MISMATCH"),
        ("expected_decision_ref", "QUALIFICATION_DECISION_REF_MISMATCH"),
        ("expected_history_ref", "HISTORY_SNAPSHOT_REF_MISMATCH"),
    ],
)
@pytest.mark.parametrize("malformed_ref", MALFORMED_REFS)
def test_malformed_expected_authority_ref_fails_at_its_ordered_predicate(
    expected_kwarg: str, reason: str, malformed_ref: Any
):
    assert_rejected(reason, valid_result(), **{expected_kwarg: malformed_ref})


@pytest.mark.parametrize("result_deadline", [EARLIER, LATER])
def test_deadline_before_or_after_the_frozen_instant_is_rejected(
    result_deadline: str,
):
    assert_rejected("DEADLINE_MISMATCH", valid_result(deadline=result_deadline))


@pytest.mark.parametrize("malformed_deadline", [None, "", "2026-09-20T00:00:00+00:00"])
def test_malformed_trusted_deadline_fails_closed(malformed_deadline: Any):
    assert_rejected(
        "DEADLINE_MISMATCH",
        valid_result(),
        frozen_deadline_utc=malformed_deadline,
    )


def test_exact_deadline_equality_is_accepted():
    assert admit(valid_result(deadline=DEADLINE))["as_of_utc"] == DEADLINE


@pytest.mark.parametrize(
    ("result_kwargs", "call_kwargs", "reason"),
    [
        (
            {
                "contract_ref": exact_ref("contract:wrong:v1", "8"),
                "profile_ref": exact_ref("profile:wrong:v1", "8"),
            },
            {},
            "VALIDATION_CONTRACT_REF_MISMATCH",
        ),
        (
            {
                "profile_ref": exact_ref("profile:wrong:v1", "8"),
                "decision_ref": exact_ref("decision:wrong:v1", "8"),
            },
            {},
            "PROVIDER_PROFILE_REF_MISMATCH",
        ),
        (
            {
                "decision_ref": exact_ref("decision:wrong:v1", "8"),
                "history_ref": exact_ref("history:wrong:v1", "8"),
            },
            {},
            "QUALIFICATION_DECISION_REF_MISMATCH",
        ),
        (
            {
                "history_ref": exact_ref("history:wrong:v1", "8"),
                "deadline": EARLIER,
            },
            {},
            "HISTORY_SNAPSHOT_REF_MISMATCH",
        ),
        (
            {"deadline": EARLIER, "state": "QUALIFICATION_EXPIRED"},
            {},
            "DEADLINE_MISMATCH",
        ),
    ],
)
def test_only_first_failed_admission_predicate_is_reported(
    result_kwargs: dict[str, Any],
    call_kwargs: dict[str, Any],
    reason: str,
):
    assert_rejected(reason, valid_result(**result_kwargs), **call_kwargs)


def test_validation_contract_failure_does_not_require_later_expected_inputs():
    result = valid_result(contract_ref=exact_ref("contract:wrong:v1", "a"))

    assert_rejected(
        "VALIDATION_CONTRACT_REF_MISMATCH",
        result,
        expected_profile_ref=object(),
        expected_decision_ref=object(),
        expected_history_ref=object(),
        frozen_deadline_utc=object(),
    )


def test_authenticated_derived_state_report_hash_has_no_admission_semantics():
    first = valid_result(report_hash="b" * 64)
    second = valid_result(report_hash="c" * 64)

    assert admit(first)["derived_state_report_semantic_sha256"] == "b" * 64
    assert admit(second)["derived_state_report_semantic_sha256"] == "c" * 64


def test_admission_does_not_invoke_rederivation_or_inspection(
    monkeypatch: pytest.MonkeyPatch,
):
    def prohibited(*_args: Any, **_kwargs: Any) -> None:
        raise AssertionError("qualification internals must not run")

    for name in (
        "execute_qualification_validation",
        "_resolve_evidence_manifest",
        "_validate_evidence",
        "validate_bound_qualification_decision",
        "_authenticate_history",
        "collect_manifest_artifacts",
        "derive_authoritative_qualification_state",
        "_derive_state_report",
    ):
        monkeypatch.setattr(phase4e, name, prohibited)
    for name in (
        "build_package_closure",
        "validate_history_completeness",
        "validate_history_cutoff",
        "validate_history_succession",
    ):
        monkeypatch.setattr(phase4d, name, prohibited)

    assert admit(valid_result())["qualification_state"] == "PRODUCTION_QUALIFIED"


def test_only_the_exact_result_is_resolved():
    result = valid_result()
    requested_refs: list[Mapping[str, str]] = []

    def resolve(requested_ref: Mapping[str, str]) -> bytearray:
        requested_refs.append(requested_ref)
        return bytearray(canonical_json(result))

    assert admit(result, resolve_result=resolve) == result
    assert requested_refs == [ref(result)]


def test_exception_reason_is_stable_and_message_text_is_non_authoritative():
    with pytest.raises(QualificationAdmissionError) as caught:
        admit(invalid_result())

    assert caught.value.reason == "VALIDATION_STATUS_NOT_VALID"
    assert str(caught.value) == "qualification admission failed"
    assert caught.value.reason not in str(caught.value)
