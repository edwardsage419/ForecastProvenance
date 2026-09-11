# Genesis External Readiness Runbook

Version: 0.2
Status: OWNER ACTION REQUIRED

This runbook performs only non-forecast Genesis readiness rehearsals.

None of the outputs are native prospective evidence and none create Forecast Ledger Genesis.

The authoritative closure checklist is `docs/GENESIS_READINESS_EVIDENCE_MATRIX.md`.

## Safety boundary

Never use a real forecast, unreleased forecast value, future production cycle artifact, or production manifest as a rehearsal subject.

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

For OpenTimestamps, install `opentimestamps-client` in an isolated environment according to your local Python tooling policy.

For strong final OTS verification, run a locally controlled Bitcoin Core node. The selected Genesis verifier profile will freeze the exact client and node versions used by the accepted rehearsal.

## Step 1 Create a synthetic rehearsal subject

From outside any future production data directory:

```bash
mkdir -p ~/fpp-genesis-rehearsal
printf '%s\n' 'FORECAST_PROVENANCE_GEN001_REHEARSAL_ONLY' > ~/fpp-genesis-rehearsal/subject.txt
sha256sum ~/fpp-genesis-rehearsal/subject.txt
```

Do not change the subject between providers when comparing receipt bindings.

This step prepares evidence for GR005, GR006, GR008, and GR009.

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

The private PEM stays outside the repository permanently.

The public PEM and its SHA256 are the only key artifacts later supplied to the project.

This step supplies GR011 evidence. It does not yet close GR032 because BootstrapGovernanceRoot is sealed only after all required governance inputs are final.

## Step 3 Run RFC 3161 provider rehearsals

The current design snapshot is recorded in `docs/GENESIS_PROVIDER_SNAPSHOT_2026_09_11.md`.

Genesis version 1 currently plans to qualify two independent RFC 3161 provider groups. Cloudflare Roughtime is optional and does not need to be enabled if both RFC 3161 groups qualify.

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

The rehearsal script records raw request and response bytes, parsed request and response text, HTTP headers, tool versions, hashes, and operational metadata.

A successful HTTP response is not yet a qualifying Genesis receipt.

For each provider, review must freeze:

1. exact signer certificate;
2. required chain;
3. token policy OID;
4. token accuracy or exact hashed provider accuracy policy;
5. nonce behavior and verification;
6. required CRL or OCSP evidence;
7. OpenSSL verifier result;
8. provider profile version;
9. exact tool versions used to parse and verify the token;
10. provider-group independence classification.

If a provider cannot supply a defensible conservative upper time bound, it cannot count toward `DEADLINE_RECEIPT_QUORUM_V1`.

These steps are intended to close GR005 and GR006 after artifact review.

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

The final Genesis review retains the exact OTS proof bytes and strong-verification output.

A remote explorer-only check is insufficient for the strong Genesis verification record.

These steps are intended to close GR008 and GR009 after independent review.

## Step 5 Capture retrospective official source fixtures

These fixtures are historical source-adapter rehearsals. They are permanently non-prospective.

From the repository working tree, run:

```bash
mkdir -p ~/fpp-genesis-source-fixtures

PYTHONPATH=src python3 scripts/genesis/fetch_retrospective_source_fixture.py \
  bls_cpi_2026_07_first_release \
  ~/fpp-genesis-source-fixtures

PYTHONPATH=src python3 scripts/genesis/fetch_retrospective_source_fixture.py \
  bls_u3_2026_08_first_release \
  ~/fpp-genesis-source-fixtures

PYTHONPATH=src python3 scripts/genesis/fetch_retrospective_source_fixture.py \
  bea_gdp_2026_q2_advance \
  ~/fpp-genesis-source-fixtures
```

Each fixture directory contains `artifact.html` and `metadata.json` with raw SHA256, retrieval time, resolved official URL, HTTP metadata, and the frozen expected target semantics.

Do not edit the downloaded HTML before hashing or adapter testing.

These artifacts are intended to close GR017, GR018, and GR019 after the source adapters produce the expected unique semantic records and the retained bytes pass review.

## Step 6 Materialize the current candidate inventory

This step is local and non-prospective. It does not create a Genesis manifest.

```bash
PYTHONPATH=src python3 scripts/genesis/materialize_candidate.py \
  --output ~/fpp-genesis-rehearsal/effective_candidate_inventory_v0_3.json
sha256sum ~/fpp-genesis-rehearsal/effective_candidate_inventory_v0_3.json
```

The materializer validates base and patch lineage, object seals, predecessor hashes, effective object count, and full dependency closure before emitting the deterministic inventory.

## Step 7 Preserve rehearsal packages

Keep the full directories:

```text
~/fpp-genesis-rehearsal/
~/fpp-genesis-source-fixtures/
~/fpp-genesis-private/
```

The private-key directory remains separate from every package that may be shared or committed.

Do not delete failed attempts. Failures can be scientific evidence about provider eligibility, tooling assumptions, or operational abort conditions.

Before any artifacts enter the repository, inspect them for secrets and confirm that the bootstrap private key directory is not included.

The project may receive only:

1. bootstrap public key and its SHA256;
2. non-secret RFC 3161 request and response artifacts;
3. provider public certificates and policy or revocation evidence;
4. OTS subject copy, proof, info, upgrade, and verification records;
5. retrospective BLS and BEA fixture bytes and metadata;
6. rehearsal metadata, tool versions, reports, and hashes.

## Acceptance status after runbook

Completing this runbook still does not create Genesis.

The project must independently verify every artifact, freeze qualifying ProviderProfile and verifier objects, insert the exact public key into BootstrapGovernanceRoot, bind the final validator implementation, construct the candidate Genesis TrustedManifest, run final adversarial review, sign ManifestAcceptance, externally evidence that acceptance, and pass the separate Genesis acceptance gate.

## Abort rule

If any command exposes a private key, produces an unexpected subject hash, overwrites prior proof material, redirects an official fixture outside its admitted host, or cannot be independently verified, stop that rehearsal and preserve the failed artifacts for review.