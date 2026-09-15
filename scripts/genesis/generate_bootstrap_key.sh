#!/usr/bin/env bash
set -euo pipefail
umask 077

if [[ $# -ne 1 ]]; then
  echo "usage: $0 /absolute/path/outside/repository" >&2
  exit 2
fi

OUTDIR="$1"
if [[ "$OUTDIR" != /* ]]; then
  echo "OUTDIR must be an absolute path outside the repository" >&2
  exit 2
fi

if command -v git >/dev/null 2>&1; then
  REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
  if [[ -n "$REPO_ROOT" ]]; then
    REAL_OUT="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$OUTDIR")"
    REAL_REPO="$(python3 -c 'import os,sys; print(os.path.realpath(sys.argv[1]))' "$REPO_ROOT")"
    case "$REAL_OUT/" in
      "$REAL_REPO/"*)
        echo "Refusing to create bootstrap private key inside repository" >&2
        exit 2
        ;;
    esac
  fi
fi

command -v openssl >/dev/null
command -v sha256sum >/dev/null

mkdir -p "$OUTDIR"
PRIVATE="$OUTDIR/bootstrap_ed25519_private.pem"
PUBLIC="$OUTDIR/bootstrap_ed25519_public.pem"

if [[ -e "$PRIVATE" || -e "$PUBLIC" ]]; then
  echo "Refusing to overwrite existing bootstrap key material" >&2
  exit 2
fi

openssl genpkey -algorithm ED25519 -out "$PRIVATE"
chmod 600 "$PRIVATE"
openssl pkey -in "$PRIVATE" -pubout -out "$PUBLIC"
chmod 644 "$PUBLIC"
sha256sum "$PUBLIC" > "$OUTDIR/bootstrap_ed25519_public.pem.sha256"

echo "Bootstrap key generated."
echo "PRIVATE KEY: $PRIVATE"
echo "PUBLIC KEY:  $PUBLIC"
echo "Do not commit, upload, email, or paste the private key."
echo "Only the public key and its SHA256 should enter Genesis project artifacts."
