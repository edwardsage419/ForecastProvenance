# Genesis External Readiness Runbook

Version: 0.1
Status: OWNER ACTION REQUIRED

This runbook performs only non-forecast Genesis readiness rehearsals.

None of the outputs are native prospective evidence and none create Forecast Ledger Genesis.

## Safety boundary

Never use a real forecast, unreleased forecast value, or future production cycle artifact as a rehearsal subject.

Use an obviously synthetic text file.

Never commit, upload, paste, or send the bootstrap private key.

Only the bootstrap public key and its SHA256 enter project artifacts.

## Prerequisites

Owner-controlled networked machine with:

```text
git
python3
openssl
curl
sha256sum
```

For OpenTimestamps:

```text
python3 -m pip install opentimestamps-client
```

For strong final OTS verification, run a locally controlled Bitcoin Core node. OpenTimestamps documents that a pruned node is acceptable.

## Step 1 Create a synthetic rehearsal subject

From outside any future production data directory:

```bash
mkdir -p ~/fpp-genesis-rehearsal
printf '%s\n' 'FORECAST_PROVENANCE_GEN001_REHEARSAL_ONLY' > ~/fpp-genesis-rehearsal/subject.txt
sha256sum ~/fpp-genesis-rehearsal/subject.txt
```

Do not change the subject between providers when comparing receipt bindings.

## Step 2 Generate bootstrap Ed25519 key outside the repository

From the ForecastProvenance working tree:

```bash
bash scripts/genesis/generate_bootstrap_key.sh ~/fpp-genesis-private
```

Expected outputs:

```text
~/fpp-genesis-private/bootstrap_ed25519_private.pem
~/fpp-genesis-private/bootstrap_ed25519_public.pem
~/fpp-genesis-private/bootstrap_ed25519_public.pem.sha256
```

The private PEM stays outside the repository.

The public PEM can later be supplied to the project after you inspect it.

## Step 3 Run RFC 3161 provider rehearsals

### FreeTSA candidate

```bash
bash scripts/genesis/rfc3161_rehearsal.sh \
  ~/fpp-genesis-rehearsal/subject.txt \
  https://freetsa.org/tsr \
  ~/fpp-genesis-rehearsal/freetsa
```

### DigiCert candidate

```bash
bash scripts/genesis/rfc3161_rehearsal.sh \
  ~/fpp-genesis-rehearsal/subject.txt \
  http://timestamp.digicert.com \
  ~/fpp-genesis-rehearsal/digicert
```

The first run intentionally captures raw request, raw response, parsed request, parsed response, hashes, and operational metadata.

A successful HTTP response is not yet a qualifying Genesis receipt.

For each provider, subsequent review must freeze:

1. signer certificate;
2. required chain;
3. policy OID;
4. token accuracy or exact hashed provider accuracy policy;
5. nonce behavior;
6. required CRL or OCSP evidence;
7. OpenSSL verifier result;
8. provider profile version.

If a provider cannot supply a defensible conservative upper time bound, it cannot count toward DEADLINE_RECEIPT_QUORUM_V1.

## Step 4 Run OpenTimestamps rehearsal

Create the initial pending proof:

```bash
bash scripts/genesis/ots_rehearsal.sh \
  stamp \
  ~/fpp-genesis-rehearsal/subject.txt \
  ~/fpp-genesis-rehearsal/ots
```

After Bitcoin confirmation becomes available, upgrade:

```bash
bash scripts/genesis/ots_rehearsal.sh \
  upgrade \
  ~/fpp-genesis-rehearsal/subject.txt \
  ~/fpp-genesis-rehearsal/ots
```

Then verify using the locally controlled Bitcoin Core environment:

```bash
bash scripts/genesis/ots_rehearsal.sh \
  verify \
  ~/fpp-genesis-rehearsal/subject.txt \
  ~/fpp-genesis-rehearsal/ots
```

The final Genesis review must retain the exact OTS proof bytes and strong-verification output.

A remote explorer-only check is insufficient for the strong Genesis verification record.

## Step 5 Preserve the rehearsal package

Keep the full directory:

```text
~/fpp-genesis-rehearsal/
```

Do not delete failed attempts.

Before any artifacts enter the repository, inspect them for secrets and confirm that the bootstrap private key directory is separate.

The project should receive only:

1. bootstrap public key and its SHA256;
2. non-secret RFC 3161 request and response artifacts;
3. provider public certificates and policy or revocation evidence;
4. OTS subject copy, proof, info, upgrade, and verification records;
5. rehearsal metadata and hashes.

## Acceptance status after runbook

Completing this runbook still does not create Genesis.

The project must parse and independently verify every artifact, freeze provider profiles, insert the exact public key into BootstrapGovernanceRoot, construct the candidate Genesis manifest, run final adversarial review, sign ManifestAcceptance, externally evidence that acceptance, and pass the separate Genesis acceptance gate.

## Abort rule

If any command exposes a private key, produces an unexpected subject hash, overwrites prior proof material, or cannot be independently verified, stop that rehearsal and preserve the failed artifacts for review.