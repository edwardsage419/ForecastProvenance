#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from forecast_trust_core.roughtime_rehearsal import validate_rehearsal_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline semantic validation of a retained Roughtime rehearsal evidence package.")
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--authorization", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        authorization = json.loads(args.authorization.read_text(encoding="utf-8"))
        report = json.loads(args.report.read_text(encoding="utf-8"))
        validate_rehearsal_report(report, plan=plan, authorization=authorization)
    except Exception as exc:
        print(f"Roughtime rehearsal semantic validation failed: {exc}", file=sys.stderr)
        return 2
    print("ROUGHTIME_REHEARSAL_SEMANTIC_VALIDATION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
