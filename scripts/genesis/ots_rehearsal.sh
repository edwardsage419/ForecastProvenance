#!/usr/bin/env bash
set -euo pipefail
umask 077

if [[ $# -lt 2 || $# -gt 3 ]]; then
  echo "usage: $0 stamp|upgrade|verify SUBJECT_FILE [OUTDIR]" >&2
  exit 2
fi

MODE="$1"
SUBJECT="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$2")"
OUTDIR="${3:-$(dirname "$SUBJECT")/ots_rehearsal}"

command -v ots >/dev/null
command -v sha256sum >/dev/null
command -v python3 >/dev/null
mkdir -p "$OUTDIR"

COPY="$OUTDIR/subject.bin"
PROOF="$COPY.ots"
STATE="$OUTDIR/rehearsal_state.txt"
TOOL_VERSIONS="$OUTDIR/tool_versions.txt"

{
  ots --version 2>&1 || true
  python3 --version 2>&1
} > "$TOOL_VERSIONS"

case "$MODE" in
  stamp)
    if [[ -e "$PROOF" || -e "$COPY" ]]; then
      echo "Refusing to overwrite existing OTS rehearsal material" >&2
      exit 2
    fi
    cp "$SUBJECT" "$COPY"
    sha256sum "$COPY" > "$OUTDIR/subject.sha256"
    ots stamp "$COPY" | tee "$OUTDIR/ots_stamp.txt"
    ots info "$PROOF" > "$OUTDIR/ots_info_after_stamp.txt"
    ;;
  upgrade)
    [[ -f "$COPY" ]] || { echo "Missing retained subject copy: $COPY" >&2; exit 2; }
    [[ -f "$PROOF" ]] || { echo "Missing proof: $PROOF" >&2; exit 2; }
    sha256sum --check "$OUTDIR/subject.sha256"
    sha256sum "$PROOF" > "$OUTDIR/proof_before_upgrade.sha256"
    ots upgrade "$PROOF" | tee "$OUTDIR/ots_upgrade.txt"
    ots info "$PROOF" > "$OUTDIR/ots_info_after_upgrade.txt"
    sha256sum "$PROOF" > "$OUTDIR/proof_after_upgrade.sha256"
    ;;
  verify)
    [[ -f "$COPY" ]] || { echo "Missing retained subject copy: $COPY" >&2; exit 2; }
    [[ -f "$PROOF" ]] || { echo "Missing proof: $PROOF" >&2; exit 2; }
    [[ -f "$OUTDIR/subject.sha256" ]] || { echo "Missing subject hash record" >&2; exit 2; }
    sha256sum --check "$OUTDIR/subject.sha256"
    if [[ -z "${OTS_BITCOIN_NODE:-}" ]]; then
      echo "verify requires OTS_BITCOIN_NODE pointing to the owner-controlled Bitcoin Core RPC endpoint" >&2
      echo "Example: export OTS_BITCOIN_NODE='http://USER:PASS@127.0.0.1:8332/'" >&2
      exit 2
    fi
    # Do not echo or persist OTS_BITCOIN_NODE because it may contain RPC credentials.
    ots --bitcoin-node "$OTS_BITCOIN_NODE" verify "$PROOF" | tee "$OUTDIR/ots_verify_owner_bitcoin_core.txt"
    ots info "$PROOF" > "$OUTDIR/ots_info_verified.txt"
    sha256sum "$PROOF" > "$OUTDIR/proof.sha256"
    ;;
  *)
    echo "mode must be stamp, upgrade, or verify" >&2
    exit 2
    ;;
esac

{
  echo "classification=NON_FORECAST_REHEARSAL"
  echo "prospective_eligible=false"
  echo "mode=$MODE"
  echo "subject_sha256=$(sha256sum "$COPY" | awk '{print $1}')"
  echo "tool_versions_sha256=$(sha256sum "$TOOL_VERSIONS" | awk '{print $1}')"
  echo "captured_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if [[ "$MODE" == "verify" ]]; then
    echo "bitcoin_verification_mode=EXPLICIT_OWNER_CONTROLLED_BITCOIN_CORE_RPC"
    echo "bitcoin_rpc_credentials_retained=false"
  else
    echo "bitcoin_verification_mode=NOT_APPLICABLE_IN_THIS_STEP"
  fi
  echo "Strong Genesis verification remains subject to the frozen verifier contract and retained proof review."
} > "$STATE"
