#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import secrets
import sys
from pathlib import Path

from forecast_trust_core.canonical import canonical_json
from forecast_trust_core._roughtime_control import (
    load_strict_json_file,
    validate_retry_state,
    validate_verifier_build_profile,
)
from forecast_trust_core.roughtime_rehearsal import (
    MAX_ATTEMPTS_PER_PROVIDER,
    PACKET_PROFILE,
    PROVIDERS,
    RETRY_BACKOFF_FACTOR,
    RETRY_BACKOFF_INITIAL_SECONDS,
    RETRY_BACKOFF_MAX_SECONDS,
    TIMEOUT_PER_ATTEMPT_SECONDS,
    TRANSPORT_PROFILE,
    VERIFIER_COMMIT,
    VERIFIER_REPOSITORY,
    VERIFIER_TAG,
    derive_nonce_v2_hex,
    validate_plan,
)


def build_plan(subject_sha256: str, subject_label: str, frozen_deadline_utc: str, verifier_build_profile_sha256: str, retry_state_snapshot_sha256: str) -> dict:
    providers = []
    for provider in PROVIDERS:
        client_random = secrets.token_bytes(32).hex()
        providers.append(
            {
                **provider.__dict__,
                "packet_profile": PACKET_PROFILE,
                "transport_profile": TRANSPORT_PROFILE,
                "client_random_hex": client_random,
                "nonce_profile": "FPP_ROUGHTIME_NONCE_V2",
                "nonce_hex": derive_nonce_v2_hex(subject_sha256, client_random),
                "maximum_attempts": MAX_ATTEMPTS_PER_PROVIDER,
                "timeout_per_attempt_seconds": TIMEOUT_PER_ATTEMPT_SECONDS,
                "retry_backoff_initial_seconds": RETRY_BACKOFF_INITIAL_SECONDS,
                "retry_backoff_factor": RETRY_BACKOFF_FACTOR,
                "retry_backoff_max_seconds": RETRY_BACKOFF_MAX_SECONDS,
                "retry_request_rule": "same_exact_request_bytes",
                "network_authorized": False,
            }
        )
    core = {
        "schema_version": "1.1",
        "classification": "NON_FORECAST_REHEARSAL",
        "prospective_eligible": False,
        "network_authorized": False,
        "subject_label": subject_label,
        "subject_sha256": subject_sha256,
        "frozen_deadline_utc": frozen_deadline_utc,
        "nonce_profile": "FPP_ROUGHTIME_NONCE_V2",
        "packet_profile": PACKET_PROFILE,
        "transport_profile": TRANSPORT_PROFILE,
        "provider_attempt_rule": "evaluate_all_three_frozen_providers_in_frozen_order_attempt_each_when_retry_eligible",
        "quorum_threshold": 2,
        "retry_state_rule": "persist_per_root_until_properly_signed_response",
        "backoff_block_rule": "backoff_active_counts_nonqualifying_no_network_attempt",
        "verifier_repository": VERIFIER_REPOSITORY,
        "verifier_tag": VERIFIER_TAG,
        "verifier_commit": VERIFIER_COMMIT,
        "verifier_build_profile_sha256": verifier_build_profile_sha256,
        "retry_state_snapshot_sha256": retry_state_snapshot_sha256,
        "providers": providers,
    }
    plan = dict(core)
    plan["plan_sha256"] = hashlib.sha256(canonical_json(core)).hexdigest()
    validate_plan(plan)
    return plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare an offline Roughtime rehearsal plan. No packets are sent.")
    parser.add_argument("--subject-sha256", required=True)
    parser.add_argument("--subject-label", required=True)
    parser.add_argument("--frozen-deadline-utc", required=True)
    parser.add_argument("--verifier-build-profile", type=Path, required=True)
    parser.add_argument("--retry-state", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        print(f"refusing to overwrite existing output: {args.output}", file=sys.stderr)
        return 2
    try:
        profile = load_strict_json_file(args.verifier_build_profile)
        retry_state = load_strict_json_file(args.retry_state)
        profile_hash = validate_verifier_build_profile(profile)
        retry_hash = validate_retry_state(retry_state)
        plan = build_plan(args.subject_sha256, args.subject_label, args.frozen_deadline_utc, profile_hash, retry_hash)
    except Exception as exc:
        print(f"Roughtime rehearsal plan preparation failed: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
