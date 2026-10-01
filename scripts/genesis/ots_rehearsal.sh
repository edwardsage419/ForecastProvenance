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
HASHFILE="$OUTDIR/subject.sha256"
EVENTS="$OUTDIR/events"
mkdir -p "$EVENTS"

next_event_dir() {
  local n=1
  while [[ -e "$EVENTS/$(printf '%04d' "$n")-$MODE" ]]; do
    n=$((n + 1))
  done
  printf '%s\n' "$EVENTS/$(printf '%04d' "$n")-$MODE"
}

EVENT="$(next_event_dir)"
mkdir "$EVENT"

{
  ots --version 2>&1 || true
  python3 --version 2>&1
} > "$EVENT/tool_versions.txt"

write_subject_hash() {
  local digest
  digest="$(sha256sum "$COPY" | awk '{print $1}')"
  printf '%s  subject.bin\n' "$digest" > "$HASHFILE"
}

check_subject_hash() {
  (cd "$OUTDIR" && sha256sum --check subject.sha256)
}

record_state() {
  local exit_status="$1"
  {
    echo "classification=NON_FORECAST_REHEARSAL"
    echo "prospective_eligible=false"
    echo "mode=$MODE"
    echo "exit_status=$exit_status"
    if [[ -f "$COPY" ]]; then
      echo "subject_sha256=$(sha256sum "$COPY" | awk '{print $1}')"
    elif [[ -f "$EVENT/subject.bin" ]]; then
      echo "subject_sha256=$(sha256sum "$EVENT/subject.bin" | awk '{print $1}')"
    fi
    echo "tool_versions_sha256=$(sha256sum "$EVENT/tool_versions.txt" | awk '{print $1}')"
    echo "captured_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    if [[ "$MODE" == "verify" ]]; then
      echo "bitcoin_verification_mode=EXPLICIT_OWNER_CONTROLLED_BITCOIN_CORE_RPC"
      echo "bitcoin_rpc_credentials_retained=false"
    else
      echo "bitcoin_verification_mode=NOT_APPLICABLE_IN_THIS_STEP"
    fi
  } > "$EVENT/state.txt"
}

# Record the final script status, including failures after the external command.
trap 'status=$?; record_state "$status"' EXIT

run_logged() {
  set +e
  "$@" >"$EVENT/stdout.txt" 2>"$EVENT/stderr.txt"
  local status=$?
  set -e
  cat "$EVENT/stdout.txt"
  cat "$EVENT/stderr.txt" >&2
  return "$status"
}

case "$MODE" in
  stamp)
    if [[ -e "$PROOF" || -e "$COPY" || -e "$HASHFILE" ]]; then
      echo "Refusing to overwrite existing successful OTS rehearsal material" >&2
      exit 2
    fi
    # Work only inside the append-only event directory until stamping succeeds.
    cp "$SUBJECT" "$EVENT/subject.bin"
    sha256sum "$EVENT/subject.bin" > "$EVENT/subject.sha256"
    run_logged ots stamp "$EVENT/subject.bin"
    [[ -f "$EVENT/subject.bin.ots" ]] || { echo "OTS stamp succeeded without producing proof" >&2; exit 2; }
    ots info "$EVENT/subject.bin.ots" > "$EVENT/ots_info_after_stamp.txt"
    sha256sum "$EVENT/subject.bin.ots" > "$EVENT/proof_after.sha256"
    # Publish canonical material only after the complete event succeeds.
    cp "$EVENT/subject.bin" "$COPY"
    cp "$EVENT/subject.bin.ots" "$PROOF"
    write_subject_hash
    ;;
  upgrade)
    [[ -f "$COPY" && -f "$PROOF" && -f "$HASHFILE" ]] || { echo "Missing retained OTS rehearsal material" >&2; exit 2; }
    check_subject_hash > "$EVENT/subject_check.txt"
    cp "$COPY" "$EVENT/subject.bin"
    cp "$PROOF" "$EVENT/subject.bin.ots"
    sha256sum "$EVENT/subject.bin.ots" > "$EVENT/proof_before.sha256"
    cp "$EVENT/subject.bin.ots" "$EVENT/proof_before.ots"
    # Upgrade an event-local copy so a failed upgrade cannot corrupt the last good canonical proof.
    run_logged ots upgrade "$EVENT/subject.bin.ots"
    ots info "$EVENT/subject.bin.ots" > "$EVENT/ots_info_after_upgrade.txt"
    sha256sum "$EVENT/subject.bin.ots" > "$EVENT/proof_after.sha256"
    cp "$EVENT/subject.bin.ots" "$EVENT/proof_after.ots"
    PUBLISH_TMP="$OUTDIR/.subject.bin.ots.publish.$$"
    cp "$EVENT/subject.bin.ots" "$PUBLISH_TMP"
    mv -f "$PUBLISH_TMP" "$PROOF"
    ;;
  verify)
    [[ -f "$COPY" && -f "$PROOF" && -f "$HASHFILE" ]] || { echo "Missing retained OTS rehearsal material" >&2; exit 2; }
    check_subject_hash > "$EVENT/subject_check.txt"
    [[ -n "${OTS_BITCOIN_NODE:-}" ]] || { echo "verify requires OTS_BITCOIN_NODE for owner-controlled Bitcoin Core RPC" >&2; exit 2; }
    # Verify an event-local snapshot so the exact checked bytes remain replayable.
    cp "$COPY" "$EVENT/subject.bin"
    cp "$PROOF" "$EVENT/subject.bin.ots"
    sha256sum "$EVENT/subject.bin.ots" > "$EVENT/proof_before.sha256"
    run_logged ots --bitcoin-node "$OTS_BITCOIN_NODE" verify "$EVENT/subject.bin.ots"
    ots info "$EVENT/subject.bin.ots" > "$EVENT/ots_info_verified.txt"
    sha256sum "$EVENT/subject.bin.ots" > "$EVENT/proof_after.sha256"
    ;;
  *)
    echo "mode must be stamp, upgrade, or verify" >&2
    exit 2
    ;;
esac
