#!/usr/bin/env bash
set -euo pipefail
umask 077

if [[ $# -ne 3 ]]; then
  echo "usage: $0 SUBJECT_FILE TSA_URL OUTDIR" >&2
  exit 2
fi

SUBJECT="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$1")"
TSA_URL="$2"
OUTDIR="$3"

command -v openssl >/dev/null
command -v curl >/dev/null
command -v sha256sum >/dev/null
command -v python3 >/dev/null

mkdir -p "$OUTDIR"
QUERY="$OUTDIR/request.tsq"
RESPONSE="$OUTDIR/response.tsr"
QUERY_TEXT="$OUTDIR/request.txt"
RESPONSE_TEXT="$OUTDIR/response.txt"
REPORT="$OUTDIR/rehearsal_report.txt"

openssl ts -query -data "$SUBJECT" -sha256 -cert -out "$QUERY"
openssl ts -query -in "$QUERY" -text -out "$QUERY_TEXT"

curl --fail --silent --show-error \
  -H "Content-Type: application/timestamp-query" \
  -H "Accept: application/timestamp-reply" \
  --data-binary "@$QUERY" \
  "$TSA_URL" \
  -o "$RESPONSE"

openssl ts -reply -in "$RESPONSE" -text -out "$RESPONSE_TEXT"

{
  echo "classification=NON_FORECAST_REHEARSAL"
  echo "prospective_eligible=false"
  echo "tsa_url=$TSA_URL"
  echo "subject_path=$SUBJECT"
  echo "subject_sha256=$(sha256sum "$SUBJECT" | awk '{print $1}')"
  echo "request_sha256=$(sha256sum "$QUERY" | awk '{print $1}')"
  echo "response_sha256=$(sha256sum "$RESPONSE" | awk '{print $1}')"
  echo "captured_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "Verification status is intentionally NOT QUALIFIED yet."
  echo "Freeze and verify provider certificate chain, policy OID, accuracy semantics,"
  echo "nonce behavior, and revocation evidence before this provider can count toward quorum."
} > "$REPORT"

if [[ -n "${TSA_CAFILE:-}" ]]; then
  VERIFY_ARGS=(openssl ts -verify -queryfile "$QUERY" -in "$RESPONSE" -CAfile "$TSA_CAFILE")
  if [[ -n "${TSA_UNTRUSTED:-}" ]]; then
    VERIFY_ARGS+=( -untrusted "$TSA_UNTRUSTED" )
  fi
  "${VERIFY_ARGS[@]}" | tee "$OUTDIR/openssl_verify.txt"
else
  echo "TSA_CAFILE is unset; cryptographic chain verification was not attempted." \
    | tee "$OUTDIR/openssl_verify.txt"
fi

echo "Rehearsal artifacts written to $OUTDIR"
