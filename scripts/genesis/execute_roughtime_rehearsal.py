#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from forecast_trust_core._roughtime_control import load_strict_json_file
from forecast_trust_core._roughtime_execution import QualifiedVerifierBackend, RealUDPTransport, execute_rehearsal


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Execute one explicitly authorized NON_FORECAST_REHEARSAL through the fail-closed UDP orchestrator."
    )
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--authorization", required=True, type=Path)
    parser.add_argument("--verifier-build-profile", required=True, type=Path)
    parser.add_argument("--verifier-binary", required=True, type=Path)
    parser.add_argument("--retry-state-before", required=True, type=Path)
    parser.add_argument("--evidence-root", required=True, type=Path)
    parser.add_argument(
        "--execute-network", action="store_true",
        help="Required explicit process-level acknowledgement that this invocation may send UDP packets.",
    )
    args = parser.parse_args()
    if not args.execute_network:
        print("refusing network execution without --execute-network", file=sys.stderr)
        return 2
    try:
        plan = load_strict_json_file(args.plan)
        authorization = load_strict_json_file(args.authorization)
        build_profile = load_strict_json_file(args.verifier_build_profile)
        retry_state = load_strict_json_file(args.retry_state_before)
        verifier = QualifiedVerifierBackend(args.verifier_binary, build_profile)
        report, state, event = execute_rehearsal(
            plan=plan, authorization=authorization, build_profile=build_profile,
            retry_state_before=retry_state, evidence_root=args.evidence_root,
            verifier=verifier, transport=RealUDPTransport(),
        )
    except BaseException as exc:
        print(f"Roughtime rehearsal execution failed closed: {exc}", file=sys.stderr)
        return 2
    print(f"ROUGHTIME_REHEARSAL_EVENT={event}")
    print(f"ROUGHTIME_REHEARSAL_REPORT_SHA256={report['content_sha256']}")
    print(f"ROUGHTIME_RETRY_STATE_AFTER_SHA256={state['state_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
