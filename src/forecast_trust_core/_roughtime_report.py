from __future__ import annotations

from typing import Any, Mapping

from forecast_trust_core.canonical import verify_sealed_object
from forecast_trust_core._roughtime_profile import (
    FAILURE_CODES, MAX_ATTEMPTS_PER_PROVIDER, PROVIDER_ORDER, VERIFIED_NONQUALIFYING_CODES, VERIFIER_COMMIT, VERIFIER_REPOSITORY, VERIFIER_TAG,
)
from forecast_trust_core._roughtime_support import (
    ATTEMPT_KEYS_OPTIONAL, ATTEMPT_KEYS_REQUIRED, REPORT_KEYS, _decode_base64, _lower_hex_32, _require_allowed_keys,
    _require_exact_keys, _sha256_hex,
)
from forecast_trust_core._roughtime_plan import validate_authorization_record, validate_plan
from forecast_trust_core._roughtime_receipt import validate_receipt

def validate_rehearsal_report(
    report: Mapping[str, Any],
    *,
    plan: Mapping[str, Any],
    authorization: Mapping[str, Any],
) -> None:
    validate_plan(plan)
    validate_authorization_record(authorization, plan)
    _require_exact_keys(report, REPORT_KEYS, "report")
    if report.get("schema_version") != "1.1":
        raise ValueError("unsupported report schema_version")
    if not verify_sealed_object(report):
        raise ValueError("rehearsal report seal invalid")
    if report.get("object_type") != "RoughtimeRehearsalReport":
        raise ValueError("report object_type mismatch")
    if report.get("classification") != "NON_FORECAST_REHEARSAL" or report.get("prospective_eligible") is not False:
        raise ValueError("report classification boundary violated")
    if report.get("network_authorized_by_report") is not False:
        raise ValueError("report cannot itself authorize network action")
    if report.get("rehearsal_plan_sha256") != plan["plan_sha256"]:
        raise ValueError("report plan binding mismatch")
    if report.get("authorization_record_sha256") != authorization["authorization_sha256"]:
        raise ValueError("report authorization binding mismatch")
    if report.get("subject_sha256") != plan["subject_sha256"]:
        raise ValueError("report subject mismatch")
    if tuple(report.get("provider_attempt_order", [])) != PROVIDER_ORDER:
        raise ValueError("report provider order mismatch")
    if report.get("quorum_threshold") != 2:
        raise ValueError("report quorum threshold mismatch")
    if (
        report.get("verifier_repository") != VERIFIER_REPOSITORY
        or report.get("verifier_tag") != VERIFIER_TAG
        or report.get("verifier_commit") != VERIFIER_COMMIT
    ):
        raise ValueError("report verifier pin mismatch")
    if report.get("verifier_build_profile_sha256") != plan["verifier_build_profile_sha256"]:
        raise ValueError("report verifier build profile mismatch")
    if report.get("retry_state_before_sha256") != plan["retry_state_snapshot_sha256"]:
        raise ValueError("report retry state before hash mismatch")
    _lower_hex_32(report.get("retry_state_after_sha256", ""), "retry_state_after_sha256")
    _lower_hex_32(report.get("execution_transcript_sha256", ""), "execution_transcript_sha256")
    results = report.get("provider_results")
    if not isinstance(results, list) or len(results) != 3:
        raise ValueError("report must contain exactly three provider results")
    if [result.get("provider_id") for result in results] != list(PROVIDER_ORDER):
        raise ValueError("provider results are not in frozen order")
    qualifying = 0
    for result in results:
        if not isinstance(result, Mapping):
            raise ValueError("provider result must be an object")
        qualifies = result.get("qualifies")
        if type(qualifies) is not bool:
            raise ValueError("provider result qualifies must be boolean")
        expected_result_keys = {"provider_id", "attempts", "qualifies"}
        if qualifies:
            expected_result_keys.add("receipt")
        else:
            expected_result_keys.add("final_failure_code")
        _require_exact_keys(result, frozenset(expected_result_keys), "provider result")

        attempts = result.get("attempts")
        if not isinstance(attempts, list) or len(attempts) > MAX_ATTEMPTS_PER_PROVIDER:
            raise ValueError("invalid provider attempt count")
        final_failure = result.get("final_failure_code")
        if not attempts:
            if qualifies or final_failure != "BACKOFF_ACTIVE":
                raise ValueError("zero network attempts are allowed only for BACKOFF_ACTIVE")
            continue

        request_hashes: list[str] = []
        terminal_verified_outcome: str | None = None
        last_failure_code: str | None = None
        for index, attempt in enumerate(attempts, 1):
            _require_allowed_keys(attempt, ATTEMPT_KEYS_REQUIRED, ATTEMPT_KEYS_OPTIONAL, "attempt")
            if attempt.get("attempt_number") != index:
                raise ValueError("attempt numbers must be contiguous from one")
            request = _decode_base64(attempt.get("request_base64", ""), "attempt.request_base64")
            request_hash = _sha256_hex(request)
            if attempt.get("request_sha256") != request_hash:
                raise ValueError("attempt request hash mismatch")
            request_hashes.append(request_hash)
            outcome = attempt.get("outcome")
            response_b64 = attempt.get("response_base64")
            response_sha = attempt.get("response_sha256")
            if response_b64 is not None:
                response = _decode_base64(response_b64, "attempt.response_base64")
                if response_sha != _sha256_hex(response):
                    raise ValueError("attempt response hash mismatch")
            elif response_sha is not None:
                raise ValueError("response_sha256 present without response bytes")

            if outcome == "QUALIFYING_VERIFIED_RESPONSE":
                if terminal_verified_outcome is not None or index != len(attempts):
                    raise ValueError("no attempt may follow a properly verified response")
                if response_b64 is None or attempt.get("failure_code") is not None:
                    raise ValueError("qualifying verified response attempt is malformed")
                terminal_verified_outcome = outcome
                last_failure_code = None
            elif outcome == "VERIFIED_NONQUALIFYING_RESPONSE":
                failure_code = attempt.get("failure_code")
                if terminal_verified_outcome is not None or index != len(attempts):
                    raise ValueError("no attempt may follow a properly verified response")
                if response_b64 is None or failure_code not in VERIFIED_NONQUALIFYING_CODES:
                    raise ValueError("verified nonqualifying response is malformed")
                terminal_verified_outcome = outcome
                last_failure_code = failure_code
            elif outcome == "FAILED":
                failure_code = attempt.get("failure_code")
                if failure_code not in FAILURE_CODES or failure_code in VERIFIED_NONQUALIFYING_CODES or failure_code == "BACKOFF_ACTIVE":
                    raise ValueError("failed network attempt uses invalid failure code")
                last_failure_code = failure_code
            else:
                raise ValueError("unknown attempt outcome")
        if len(set(request_hashes)) != 1:
            raise ValueError("retries must use identical request bytes")

        receipt = result.get("receipt")
        if qualifies:
            if terminal_verified_outcome != "QUALIFYING_VERIFIED_RESPONSE" or not isinstance(receipt, dict):
                raise ValueError("qualifying provider must have a qualifying verified response and receipt")
            validate_receipt(receipt, plan=plan, authorization=authorization)
            if receipt.get("provider_id") != result.get("provider_id"):
                raise ValueError("receipt/provider result mismatch")
            last = attempts[-1]
            if receipt.get("request_sha256") != last.get("request_sha256") or receipt.get("response_sha256") != last.get("response_sha256"):
                raise ValueError("receipt does not bind the verified attempt bytes")
            qualifying += 1
        else:
            if terminal_verified_outcome == "QUALIFYING_VERIFIED_RESPONSE":
                raise ValueError("qualifying verified response cannot be reported as non-qualifying")
            if final_failure not in FAILURE_CODES or final_failure == "BACKOFF_ACTIVE":
                raise ValueError("non-qualifying attempted provider requires final failure code")
            if final_failure != last_failure_code:
                raise ValueError("final_failure_code must equal the last terminal attempt result")
    if report.get("qualifying_provider_count") != qualifying:
        raise ValueError("qualifying_provider_count does not match provider results")
    expected_status = "REHEARSAL_VERIFIED" if qualifying >= 2 else "REHEARSAL_FAILED"
    if report.get("final_rehearsal_status") != expected_status:
        raise ValueError("final rehearsal status does not match quorum result")
