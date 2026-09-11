from __future__ import annotations

from typing import Any, Mapping

from forecast_trust_core.canonical import verify_sealed_object
from forecast_trust_core._roughtime_profile import (
    NONCE_PROFILE, PACKET_PROFILE, PROVIDER_BY_ID, TRANSPORT_PROFILE, VERIFIER_COMMIT, VERIFIER_REPOSITORY, VERIFIER_TAG,
)
from forecast_trust_core._roughtime_support import (
    RECEIPT_KEYS, _decode_base64, _lower_hex_32, _parse_utc, _provider_public_fields,
    _require_exact_keys, _sha256_hex, derive_nonce_v2_hex, upper_bound_utc,
)
from forecast_trust_core._roughtime_plan import validate_authorization_record, validate_plan

def validate_receipt(
    receipt: Mapping[str, Any],
    *,
    plan: Mapping[str, Any],
    authorization: Mapping[str, Any],
) -> None:
    validate_plan(plan)
    validate_authorization_record(authorization, plan)
    _require_exact_keys(receipt, RECEIPT_KEYS, "receipt")
    if receipt.get("schema_version") != "1.1":
        raise ValueError("unsupported receipt schema_version")
    if not verify_sealed_object(receipt):
        raise ValueError("receipt seal invalid")
    if receipt.get("object_type") != "RoughtimeReceipt":
        raise ValueError("receipt object_type mismatch")
    if receipt.get("classification") != "NON_FORECAST_REHEARSAL" or receipt.get("prospective_eligible") is not False:
        raise ValueError("receipt classification boundary violated")
    if receipt.get("rehearsal_plan_sha256") != plan["plan_sha256"]:
        raise ValueError("receipt plan binding mismatch")
    if receipt.get("authorization_record_sha256") != authorization["authorization_sha256"]:
        raise ValueError("receipt authorization binding mismatch")
    provider_id = receipt.get("provider_id")
    provider = PROVIDER_BY_ID.get(provider_id)
    if provider is None:
        raise ValueError("receipt provider is outside frozen pool")
    plan_item = next(item for item in plan["providers"] if item["provider_id"] == provider_id)
    for key, value in _provider_public_fields(provider).items():
        if receipt.get(key) != value:
            raise ValueError(f"receipt provider field mismatch: {key}")
    if receipt.get("packet_profile") != PACKET_PROFILE or receipt.get("transport_profile") != TRANSPORT_PROFILE:
        raise ValueError("receipt packet/transport profile mismatch")
    if receipt.get("subject_sha256") != plan["subject_sha256"]:
        raise ValueError("receipt subject mismatch")
    if receipt.get("client_random_hex") != plan_item["client_random_hex"]:
        raise ValueError("receipt client random mismatch")
    expected_nonce = derive_nonce_v2_hex(plan["subject_sha256"], plan_item["client_random_hex"])
    if receipt.get("nonce_profile") != NONCE_PROFILE or receipt.get("nonce_hex") != expected_nonce:
        raise ValueError("receipt nonce binding mismatch")
    request = _decode_base64(receipt.get("request_base64", ""), "request_base64")
    response = _decode_base64(receipt.get("response_base64", ""), "response_base64")
    if receipt.get("request_sha256") != _sha256_hex(request):
        raise ValueError("receipt request_sha256 mismatch")
    if receipt.get("response_sha256") != _sha256_hex(response):
        raise ValueError("receipt response_sha256 mismatch")
    if (
        receipt.get("verifier_repository") != VERIFIER_REPOSITORY
        or receipt.get("verifier_tag") != VERIFIER_TAG
        or receipt.get("verifier_commit") != VERIFIER_COMMIT
    ):
        raise ValueError("receipt verifier pin mismatch")
    _lower_hex_32(receipt.get("verifier_source_sha256", ""), "verifier_source_sha256")
    _lower_hex_32(receipt.get("verifier_binary_sha256", ""), "verifier_binary_sha256")
    if receipt.get("verifier_build_profile_sha256") != plan["verifier_build_profile_sha256"]:
        raise ValueError("receipt verifier build profile mismatch")
    _lower_hex_32(receipt.get("verification_transcript_sha256", ""), "verification_transcript_sha256")
    midpoint = _parse_utc(receipt.get("midpoint_utc", ""), "midpoint_utc")
    deadline = _parse_utc(plan["frozen_deadline_utc"], "frozen_deadline_utc")
    radius = receipt.get("radius_seconds")
    computed_upper = upper_bound_utc(midpoint, radius)
    if receipt.get("verified_receipt_upper_bound_utc") != computed_upper.strftime("%Y-%m-%dT%H:%M:%SZ"):
        raise ValueError("receipt upper bound does not equal midpoint + radius")
    if receipt.get("frozen_deadline_utc") != plan["frozen_deadline_utc"]:
        raise ValueError("receipt frozen deadline mismatch")
    required_true = (
        "root_key_match",
        "wire_profile_match",
        "delegation_verified",
        "signature_verified",
        "nonce_verified",
        "merkle_proof_verified",
        "midpoint_inside_delegation",
        "upper_bound_at_or_before_deadline",
        "qualifies",
    )
    if any(receipt.get(field) is not True for field in required_true):
        raise ValueError("qualifying receipt contains a failed verification predicate")
    if computed_upper > deadline:
        raise ValueError("receipt upper bound is after frozen deadline")


