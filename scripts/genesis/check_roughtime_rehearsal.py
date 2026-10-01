#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from forecast_trust_core._roughtime_control import load_strict_json_file, validate_report_control_binding
from forecast_trust_core.roughtime_rehearsal import validate_rehearsal_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline semantic validation of a retained Roughtime rehearsal evidence package.")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--verifier-build-profile", type=Path, required=True)
    parser.add_argument("--retry-state-before", type=Path, required=True)
    parser.add_argument("--retry-state-after", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = load_strict_json_file(args.plan)
        authorization = load_strict_json_file(args.authorization)
        report = load_strict_json_file(args.report)
        profile = load_strict_json_file(args.verifier_build_profile)
        retry_before = load_strict_json_file(args.retry_state_before)
        retry_after = load_strict_json_file(args.retry_state_after)
        validate_rehearsal_report(report, plan=plan, authorization=authorization)
        validate_report_control_binding(report, plan, authorization, profile, retry_before, retry_after)
    except Exception as exc:
        print(f"Roughtime rehearsal semantic validation failed: {exc}", file=sys.stderr)
        return 2
    print("ROUGHTIME_REHEARSAL_SEMANTIC_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
