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
mkdir -p "$OUTDIR"

COPY="$OUTDIR/subject.bin"
PROOF="$COPY.ots"

case "$MODE" in
  stamp)
    if [[ -e "$PROOF" ]]; then
      echo "Refusing to overwrite existing OTS proof" >&2
      exit 2
    fi
    cp "$SUBJECT" "$COPY"
    sha256sum "$COPY" > "$OUTDIR/subject.sha256"
    ots stamp "$COPY"
    ots info "$PROOF" > "$OUTDIR/ots_info_after_stamp.txt"
    ;;
  upgrade)
    [[ -f "$PROOF" ]] || { echo "Missing proof: $PROOF" >&2; exit 2; }
    ots upgrade "$PROOF" | tee "$OUTDIR/ots_upgrade.txt"
    ots info "$PROOF" > "$OUTDIR/ots_info_after_upgrade.txt"
    ;;
  verify)
    [[ -f "$PROOF" ]] || { echo "Missing proof: $PROOF" >&2; exit 2; }
    ots verify "$PROOF" | tee "$OUTDIR/ots_verify.txt"
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
  echo "captured_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "Strong Genesis verification requires the accepted verifier contract"
  echo "and an owner-controlled Bitcoin Core node."
} > "$OUTDIR/rehearsal_state.txt"
