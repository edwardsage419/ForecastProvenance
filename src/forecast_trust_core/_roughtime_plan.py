from __future__ import annotations

from typing import Any, Mapping

from forecast_trust_core._roughtime_profile import (
    MAX_ATTEMPTS_PER_PROVIDER, NONCE_PROFILE, PACKET_PROFILE, PROVIDERS, PROVIDER_ORDER,
    RETRY_BACKOFF_FACTOR, RETRY_BACKOFF_INITIAL_SECONDS, RETRY_BACKOFF_MAX_SECONDS,
    TIMEOUT_PER_ATTEMPT_SECONDS, TRANSPORT_PROFILE, VERIFIER_COMMIT, VERIFIER_REPOSITORY, VERIFIER_TAG,
)
from forecast_trust_core._roughtime_support import (
    AUTHORIZATION_KEYS, PLAN_KEYS, PROVIDER_PLAN_KEYS, _content_hash_without, _lower_hex_32,
    _parse_utc, _provider_public_fields, _require_exact_keys, derive_nonce_v2_hex,
    validate_provider_attempt_order,
)

def validate_plan(plan: Mapping[str, Any]) -> None:
    _require_exact_keys(plan, PLAN_KEYS, "plan")
    if plan.get("schema_version") != "1.1":
        raise ValueError("unsupported rehearsal plan schema_version")
    if plan.get("classification") != "NON_FORECAST_REHEARSAL":
        raise ValueError("plan classification mismatch")
    if plan.get("prospective_eligible") is not False or plan.get("network_authorized") is not False:
        raise ValueError("offline plan cannot be prospective or network-authorizing")
    _lower_hex_32(plan.get("subject_sha256", ""), "subject_sha256")
    _parse_utc(plan.get("frozen_deadline_utc", ""), "frozen_deadline_utc")
    if plan.get("nonce_profile") != NONCE_PROFILE:
        raise ValueError("plan nonce profile mismatch")
    if plan.get("packet_profile") != PACKET_PROFILE:
        raise ValueError("plan packet profile mismatch")
    if plan.get("transport_profile") != TRANSPORT_PROFILE:
        raise ValueError("plan transport profile mismatch")
    if plan.get("provider_attempt_rule") != "evaluate_all_three_frozen_providers_in_frozen_order_attempt_each_when_retry_eligible":
        raise ValueError("provider attempt rule mismatch")
    if plan.get("retry_state_rule") != "persist_per_root_until_properly_signed_response":
        raise ValueError("retry state rule mismatch")
    if plan.get("backoff_block_rule") != "backoff_active_counts_nonqualifying_no_network_attempt":
        raise ValueError("backoff block rule mismatch")
    if plan.get("quorum_threshold") != 2:
        raise ValueError("plan quorum threshold mismatch")
    if (
        plan.get("verifier_repository") != VERIFIER_REPOSITORY
        or plan.get("verifier_tag") != VERIFIER_TAG
        or plan.get("verifier_commit") != VERIFIER_COMMIT
    ):
        raise ValueError("plan verifier pin mismatch")
    _lower_hex_32(plan.get("verifier_build_profile_sha256", ""), "verifier_build_profile_sha256")
    _lower_hex_32(plan.get("retry_state_snapshot_sha256", ""), "retry_state_snapshot_sha256")
    providers = plan.get("providers")
    if not isinstance(providers, list) or len(providers) != 3:
        raise ValueError("plan must contain exactly three providers")
    validate_provider_attempt_order([item.get("provider_id") for item in providers])
    randoms: set[str] = set()
    nonces: set[str] = set()
    for provider, item in zip(PROVIDERS, providers):
        _require_exact_keys(item, PROVIDER_PLAN_KEYS, f"plan provider {provider.provider_id}")
        for key, value in _provider_public_fields(provider).items():
            if item.get(key) != value:
                raise ValueError(f"provider plan mismatch: {provider.provider_id}.{key}")
        if item.get("packet_profile") != PACKET_PROFILE or item.get("transport_profile") != TRANSPORT_PROFILE:
            raise ValueError("provider packet/transport profile mismatch")
        if item.get("maximum_attempts") != MAX_ATTEMPTS_PER_PROVIDER:
            raise ValueError("provider attempt limit mismatch")
        if item.get("timeout_per_attempt_seconds") != TIMEOUT_PER_ATTEMPT_SECONDS:
            raise ValueError("provider timeout mismatch")
        if item.get("retry_backoff_initial_seconds") != RETRY_BACKOFF_INITIAL_SECONDS:
            raise ValueError("provider retry initial backoff mismatch")
        if item.get("retry_backoff_factor") != RETRY_BACKOFF_FACTOR:
            raise ValueError("provider retry backoff factor mismatch")
        if item.get("retry_backoff_max_seconds") != RETRY_BACKOFF_MAX_SECONDS:
            raise ValueError("provider retry maximum backoff mismatch")
        if item.get("retry_request_rule") != "same_exact_request_bytes":
            raise ValueError("provider retry request rule mismatch")
        if item.get("network_authorized") is not False:
            raise ValueError("provider plan must remain network_authorized=false")
        client_random = item.get("client_random_hex", "")
        nonce = item.get("nonce_hex", "")
        _lower_hex_32(client_random, "client_random_hex")
        _lower_hex_32(nonce, "nonce_hex")
        if nonce != derive_nonce_v2_hex(plan["subject_sha256"], client_random):
            raise ValueError("provider nonce does not match FPP_ROUGHTIME_NONCE_V2")
        randoms.add(client_random)
        nonces.add(nonce)
    if len(randoms) != 3 or len(nonces) != 3:
        raise ValueError("each provider must receive independent client randomness and nonce")
    if plan.get("plan_sha256") != _content_hash_without(plan, "plan_sha256"):
        raise ValueError("plan_sha256 mismatch")


def validate_authorization_record(auth: Mapping[str, Any], plan: Mapping[str, Any]) -> None:
    validate_plan(plan)
    _require_exact_keys(auth, AUTHORIZATION_KEYS, "authorization")
    if auth.get("schema_version") != "1.0":
        raise ValueError("unsupported authorization schema_version")
    if auth.get("classification") != "NON_FORECAST_REHEARSAL":
        raise ValueError("authorization classification mismatch")
    if auth.get("prospective_eligible") is not False:
        raise ValueError("authorization must remain non-prospective")
    if auth.get("network_authorized") is not True:
        raise ValueError("authorization record must explicitly authorize the rehearsal network action")
    if not isinstance(auth.get("authorized_by"), str) or not auth["authorized_by"].strip():
        raise ValueError("authorization authorized_by must be non-empty")
    authorized_at = _parse_utc(auth.get("authorized_at_utc", ""), "authorized_at_utc")
    deadline = _parse_utc(plan["frozen_deadline_utc"], "frozen_deadline_utc")
    if authorized_at >= deadline:
        raise ValueError("authorization must precede the frozen deadline")
    if auth.get("authorization_scope") != "exact_plan_only_no_prospective_use":
        raise ValueError("authorization scope mismatch")
    if auth.get("rehearsal_plan_sha256") != plan["plan_sha256"]:
        raise ValueError("authorization does not bind exact rehearsal plan")
    if auth.get("subject_sha256") != plan["subject_sha256"]:
        raise ValueError("authorization subject mismatch")
    if auth.get("frozen_deadline_utc") != plan["frozen_deadline_utc"]:
        raise ValueError("authorization deadline mismatch")
    if tuple(auth.get("provider_order", [])) != PROVIDER_ORDER:
        raise ValueError("authorization provider order mismatch")
    if auth.get("verifier_commit") != VERIFIER_COMMIT:
        raise ValueError("authorization verifier commit mismatch")
    if auth.get("verifier_build_profile_sha256") != plan["verifier_build_profile_sha256"]:
        raise ValueError("authorization verifier build profile mismatch")
    if auth.get("retry_state_snapshot_sha256") != plan["retry_state_snapshot_sha256"]:
        raise ValueError("authorization retry state snapshot mismatch")
    if auth.get("authorization_sha256") != _content_hash_without(auth, "authorization_sha256"):
        raise ValueError("authorization_sha256 mismatch")


