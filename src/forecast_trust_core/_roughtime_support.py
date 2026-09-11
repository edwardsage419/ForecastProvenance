from __future__ import annotations

import base64
import hashlib
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping, Sequence

from forecast_trust_core.canonical import canonical_json
from forecast_trust_core._roughtime_profile import (
    CLIENT_RANDOM_LENGTH, NONCE_DOMAIN, NONCE_LENGTH, PROVIDER_ORDER, RoughtimeProvider,
)

PLAN_KEYS = frozenset({
    "schema_version", "classification", "prospective_eligible", "network_authorized",
    "subject_label", "subject_sha256", "frozen_deadline_utc", "nonce_profile",
    "packet_profile", "transport_profile", "provider_attempt_rule", "quorum_threshold",
    "retry_state_rule", "backoff_block_rule", "verifier_repository", "verifier_tag",
    "verifier_commit", "verifier_build_profile_sha256", "retry_state_snapshot_sha256", "providers", "plan_sha256",
})
PROVIDER_PLAN_KEYS = frozenset({
    "provider_id", "operator_identity", "host", "port", "transport",
    "operator_declared_protocol", "wire_version_hex", "offered_version_hex", "wire_profile",
    "require_type", "require_srv", "root_public_key_base64", "packet_profile",
    "transport_profile", "client_random_hex", "nonce_profile", "nonce_hex",
    "maximum_attempts", "timeout_per_attempt_seconds", "retry_backoff_initial_seconds",
    "retry_backoff_factor", "retry_backoff_max_seconds", "retry_request_rule",
    "network_authorized",
})
AUTHORIZATION_KEYS = frozenset({
    "schema_version", "classification", "prospective_eligible", "network_authorized",
    "rehearsal_plan_sha256", "subject_sha256", "frozen_deadline_utc",
    "provider_order", "verifier_commit", "verifier_build_profile_sha256", "retry_state_snapshot_sha256", "authorized_by", "authorized_at_utc",
    "authorization_scope", "authorization_sha256",
})
RECEIPT_KEYS = frozenset({
    "schema_version", "classification", "prospective_eligible", "rehearsal_plan_sha256",
    "authorization_record_sha256", "provider_id", "operator_identity", "host", "port",
    "transport", "operator_declared_protocol", "wire_version_hex", "offered_version_hex", "wire_profile",
    "require_type", "require_srv", "root_public_key_base64", "packet_profile",
    "transport_profile", "subject_sha256", "client_random_hex", "nonce_profile",
    "nonce_hex", "request_sha256", "request_base64", "response_sha256",
    "response_base64", "verifier_repository", "verifier_tag", "verifier_commit",
    "verifier_source_sha256", "verifier_binary_sha256", "verifier_build_profile_sha256", "verification_transcript_sha256", "midpoint_utc", "radius_seconds",
    "verified_receipt_upper_bound_utc", "frozen_deadline_utc", "root_key_match",
    "wire_profile_match", "delegation_verified", "signature_verified", "nonce_verified",
    "merkle_proof_verified", "midpoint_inside_delegation",
    "upper_bound_at_or_before_deadline", "qualifies", "object_type", "object_id",
    "payload_sha256", "content_sha256",
})
REPORT_KEYS = frozenset({
    "schema_version", "classification", "prospective_eligible", "network_authorized_by_report",
    "rehearsal_plan_sha256", "authorization_record_sha256", "subject_sha256",
    "provider_attempt_order", "quorum_threshold", "verifier_repository", "verifier_tag",
    "verifier_commit", "verifier_build_profile_sha256", "retry_state_before_sha256", "retry_state_after_sha256", "execution_transcript_sha256", "provider_results", "qualifying_provider_count",
    "final_rehearsal_status", "object_type", "object_id", "payload_sha256", "content_sha256",
})
ATTEMPT_KEYS_REQUIRED = frozenset({"attempt_number", "request_sha256", "request_base64", "outcome"})
ATTEMPT_KEYS_OPTIONAL = frozenset({"response_sha256", "response_base64", "failure_code", "detail"})


def _require_exact_keys(value: Mapping[str, Any], expected: frozenset[str], field: str) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    actual = set(value)
    if actual != set(expected):
        missing = sorted(set(expected) - actual)
        extra = sorted(actual - set(expected))
        raise ValueError(f"{field} key mismatch: missing={missing} extra={extra}")


def _require_allowed_keys(
    value: Mapping[str, Any], required: frozenset[str], optional: frozenset[str], field: str
) -> None:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field} must be an object")
    actual = set(value)
    missing = sorted(set(required) - actual)
    extra = sorted(actual - set(required) - set(optional))
    if missing or extra:
        raise ValueError(f"{field} key mismatch: missing={missing} extra={extra}")


def _lower_hex_32(value: str, field: str) -> bytes:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or value != value.lower()
        or any(ch not in "0123456789abcdef" for ch in value)
    ):
        raise ValueError(f"{field} must be 64 lowercase hex characters")
    raw = bytes.fromhex(value)
    if len(raw) != 32:
        raise ValueError(f"{field} must decode to exactly 32 bytes")
    return raw


def _sha256_hex(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _decode_base64(value: str, field: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be non-empty base64")
    try:
        raw = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise ValueError(f"{field} must be canonical base64") from exc
    if base64.b64encode(raw).decode("ascii") != value:
        raise ValueError(f"{field} must be canonical base64")
    return raw


def _parse_utc(value: str, field: str) -> datetime:
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise ValueError(f"{field} must use YYYY-MM-DDTHH:MM:SSZ")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ValueError(f"{field} is not a valid whole-second UTC timestamp") from exc
    if parsed.strftime("%Y-%m-%dT%H:%M:%SZ") != value:
        raise ValueError(f"{field} is not canonical UTC")
    return parsed


def _content_hash_without(instance: Mapping[str, Any], field: str) -> str:
    core = {k: v for k, v in instance.items() if k != field}
    return _sha256_hex(canonical_json(core))


def derive_nonce_v2(subject_sha256: bytes, client_random: bytes) -> bytes:
    if len(subject_sha256) != 32:
        raise ValueError("subject_sha256 must be exactly 32 bytes")
    if len(client_random) != CLIENT_RANDOM_LENGTH:
        raise ValueError("client_random must be exactly 32 bytes")
    nonce = hashlib.sha256(NONCE_DOMAIN + subject_sha256 + client_random).digest()
    if len(nonce) != NONCE_LENGTH:
        raise AssertionError("FPP_ROUGHTIME_NONCE_V2 must be exactly 32 bytes")
    return nonce


def derive_nonce_v2_hex(subject_sha256_hex: str, client_random_hex: str) -> str:
    subject = _lower_hex_32(subject_sha256_hex, "subject_sha256")
    client_random = _lower_hex_32(client_random_hex, "client_random")
    return derive_nonce_v2(subject, client_random).hex()


def upper_bound_utc(midpoint: datetime, radius_seconds: int) -> datetime:
    if midpoint.tzinfo is None or midpoint.utcoffset() != timedelta(0):
        raise ValueError("midpoint must be timezone-aware UTC")
    if type(radius_seconds) is not int or not (1 <= radius_seconds <= 2**32 - 1):
        raise ValueError("radius_seconds must be an integer from 1 through 2^32-1")
    return midpoint.astimezone(timezone.utc) + timedelta(seconds=radius_seconds)


def validate_provider_attempt_order(provider_ids: Sequence[str]) -> None:
    if tuple(provider_ids) != PROVIDER_ORDER:
        raise ValueError("all three frozen providers must be evaluated in frozen order")


def validate_quorum_results(results: Mapping[str, bool]) -> bool:
    if set(results) != set(PROVIDER_ORDER):
        raise ValueError("quorum results must contain exactly the frozen provider pool")
    if any(type(value) is not bool for value in results.values()):
        raise ValueError("quorum result values must be booleans")
    return sum(results.values()) >= 2


def _provider_public_fields(provider: RoughtimeProvider) -> dict[str, Any]:
    return asdict(provider)


