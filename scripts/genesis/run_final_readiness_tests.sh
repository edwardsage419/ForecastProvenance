#!/usr/bin/env bash
set -euo pipefail
umask 077

if [[ $# -ne 1 ]]; then
  echo "usage: $0 OUTDIR" >&2
  exit 2
fi

OUTDIR="$1"

command -v git >/dev/null
command -v python3 >/dev/null
command -v sha256sum >/dev/null

if [[ -n "$(git status --porcelain)" ]]; then
  echo "final readiness tests require a clean Git working tree" >&2
  exit 2
fi

COMMIT="$(git rev-parse HEAD)"
if [[ ! "$COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
  echo "could not resolve a canonical 40-hex Git commit" >&2
  exit 2
fi

if ! PYTHONPATH=src python3 -m pytest --version >/dev/null 2>&1; then
  echo "pytest is required for the complete repository regression; install the pinned test extra" >&2
  exit 2
fi

PYTEST_VERSION="$(PYTHONPATH=src python3 -m pytest --version 2>&1 | head -n 1)"

mkdir -p "$OUTDIR"
REPORT="$OUTDIR/final_readiness_test_report.txt"

{
  echo "classification=NON_FORECAST_VALIDATION_REPORT"
  echo "prospective_eligible=false"
  echo "git_commit=$COMMIT"
  echo "captured_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "python_version=$(python3 --version 2>&1)"
  echo "runtime_dependencies=NONE"
  echo "test_runner=$PYTEST_VERSION"
  echo
  echo "== compileall =="
} > "$REPORT"

PYTHONPATH=src python3 -m compileall -q src scripts tests 2>&1 | tee -a "$REPORT"

{
  echo
  echo "== pytest =="
} >> "$REPORT"

set +e
PYTHONPATH=src python3 -m pytest -q 2>&1 | tee -a "$REPORT"
TEST_STATUS=${PIPESTATUS[0]}
set -e

{
  echo
  echo "test_exit_status=$TEST_STATUS"
  echo "report_sha256_pending=self_hash_recorded_in_sidecar"
} >> "$REPORT"

sha256sum "$REPORT" > "$REPORT.sha256"

if [[ $TEST_STATUS -ne 0 ]]; then
  echo "readiness tests failed; preserve report and do not build final ValidatorContract" >&2
  exit "$TEST_STATUS"
fi

echo "Final readiness tests passed for commit $COMMIT"
echo "Report: $REPORT"
echo "SHA256: $REPORT.sha256"
