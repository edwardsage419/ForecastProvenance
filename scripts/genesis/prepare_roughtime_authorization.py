#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from forecast_trust_core.canonical import canonical_json
from forecast_trust_core._roughtime_control import (
    load_strict_json_file,
    validate_authorization_control_binding,
    validate_retry_state,
    validate_verifier_build_profile,
)
from forecast_trust_core.roughtime_rehearsal import PROVIDER_ORDER, VERIFIER_COMMIT, validate_authorization_record, validate_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an offline authorization record for one exact NON_FORECAST_REHEARSAL plan. This tool sends no packets.")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--verifier-build-profile", type=Path, required=True)
    parser.add_argument("--retry-state", type=Path, required=True)
    parser.add_argument("--authorized-by", required=True)
    parser.add_argument("--authorized-at-utc", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--explicit-operator-authorization", action="store_true")
    args = parser.parse_args()
    if not args.explicit_operator_authorization:
        print("refusing to create authorization without --explicit-operator-authorization", file=sys.stderr)
        return 2
    if args.output.exists():
        print(f"refusing to overwrite existing output: {args.output}", file=sys.stderr)
        return 2
    try:
        plan = load_strict_json_file(args.plan)
        profile = load_strict_json_file(args.verifier_build_profile)
        retry_state = load_strict_json_file(args.retry_state)
        validate_plan(plan)
        profile_hash = validate_verifier_build_profile(profile)
        retry_hash = validate_retry_state(retry_state)
        core = {
            "schema_version": "1.0",
            "classification": "NON_FORECAST_REHEARSAL",
            "prospective_eligible": False,
            "network_authorized": True,
            "rehearsal_plan_sha256": plan["plan_sha256"],
            "subject_sha256": plan["subject_sha256"],
            "frozen_deadline_utc": plan["frozen_deadline_utc"],
            "provider_order": list(PROVIDER_ORDER),
            "verifier_commit": VERIFIER_COMMIT,
            "verifier_build_profile_sha256": profile_hash,
            "retry_state_snapshot_sha256": retry_hash,
            "authorized_by": args.authorized_by,
            "authorized_at_utc": args.authorized_at_utc,
            "authorization_scope": "exact_plan_only_no_prospective_use",
        }
        auth = dict(core)
        auth["authorization_sha256"] = hashlib.sha256(canonical_json(core)).hexdigest()
        validate_authorization_record(auth, plan)
        validate_authorization_control_binding(auth, plan, profile, retry_state)
    except Exception as exc:
        print(f"authorization preparation failed: {exc}", file=sys.stderr)
        return 2
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(auth, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
