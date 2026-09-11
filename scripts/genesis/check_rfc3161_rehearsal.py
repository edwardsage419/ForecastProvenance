#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from forecast_trust_core.canonical import parse_json_strict
from forecast_trust_core.rfc3161_rehearsal import OpenSSLBackend, RehearsalEvidenceError, check_rehearsal


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify and materialize a non-forecast RFC 3161 provider qualification rehearsal."
    )
    parser.add_argument("--evidence-dir", required=True, type=Path)
    parser.add_argument("--provider-profile", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--openssl", default="openssl")
    args = parser.parse_args()

    try:
        profile = parse_json_strict(args.provider_profile.read_text(encoding="utf-8"))
        if not isinstance(profile, dict):
            raise RehearsalEvidenceError("provider profile must be a JSON object")
        report = check_rehearsal(
            args.evidence_dir,
            profile,
            backend=OpenSSLBackend(args.openssl),
        )
    except (OSError, RehearsalEvidenceError, ValueError) as exc:
        print(f"RFC 3161 rehearsal check failed closed: {exc}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists():
        print(f"refusing to overwrite existing report: {args.output}", file=sys.stderr)
        return 2
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    with args.output.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(rendered)
    print(f"{report['provider_id']}: {report['final_rehearsal_status']}")
    print(f"Report: {args.output}")
    return 0 if report["final_rehearsal_status"] == "REHEARSAL_VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
