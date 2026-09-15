#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from forecast_trust_core.canonical import seal_object


ROOT = Path(__file__).resolve().parents[2]
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def implementation_files() -> list[Path]:
    files = sorted((ROOT / "src" / "forecast_trust_core").glob("*.py"))
    files.extend(sorted((ROOT / "schemas").glob("*.json")))
    files.append(ROOT / "pyproject.toml")
    missing = [path for path in files if not path.is_file()]
    if missing:
        raise ValueError(f"validator implementation file missing: {missing}")
    return sorted(set(files))


def build_contract(git_commit: str, test_report: Path) -> dict:
    if not HEX40.fullmatch(git_commit):
        raise ValueError("git commit must be exactly 40 lowercase hexadecimal characters")
    if not test_report.is_file():
        raise ValueError("test report does not exist")

    source_files = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "sha256": sha256_file(path),
        }
        for path in implementation_files()
    ]
    test_report_sha = sha256_file(test_report)
    if not HEX64.fullmatch(test_report_sha):
        raise ValueError("unexpected test report SHA256")

    payload = {
        "schema_version": "1.0",
        "object_role": "NORMATIVE",
        "validator_version": "GENESIS_V1",
        "git_commit": git_commit,
        "implementation_language": "PYTHON",
        "python_requirement": ">=3.11",
        "runtime_dependencies": [],
        "source_files": source_files,
        "test_report": {
            "filename": test_report.name,
            "sha256": test_report_sha,
        },
        "required_test_scope": [
            "TRUST_CORE_ADVERSARIAL_MATRIX",
            "GENESIS_CANDIDATE_OBJECTS",
            "GENESIS_SOURCE_PARSER",
            "GENESIS_READINESS_VALIDATORS",
        ],
        "change_policy": "ANY_CONSEQUENTIAL_FILE_OR_RUNTIME_CHANGE_REQUIRES_NEW_VALIDATOR_CONTRACT",
    }
    return seal_object(
        payload,
        object_type="ValidatorContract",
        stable_context="forecast-trust-core-genesis-v1",
        semantic_id="validator:forecast-trust-core-genesis:v1",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the exact final Genesis validator binding.")
    parser.add_argument("--git-commit", required=True)
    parser.add_argument("--test-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        contract = build_contract(args.git_commit, args.test_report)
    except Exception as exc:
        print(f"validator binding failed: {exc}", file=sys.stderr)
        return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
