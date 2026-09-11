# GEN_001 Owner Action Packet

Date: 2026-09-11
Status: OWNER ACTION REQUIRED

This is the concise execution packet for the remaining owner-controlled GEN_001 evidence.

If an older runbook command conflicts with this packet or with a script's fail-closed checks, this packet and the current script behavior control.

All outputs are non-forecast readiness evidence. None create Forecast Ledger Genesis.

## Safety rules

1. Work from `design/gen-001` or a later reviewed descendant.
2. Never use a real or unreleased forecast as a rehearsal subject.
3. Never upload, commit, paste, or send the bootstrap private key.
4. Keep `~/fpp-genesis-private/` outside the repository and outside every package you share.
5. Preserve failed attempts as well as successful attempts.
6. Do not weaken provider quorum when a provider fails.

## A. Prepare one synthetic subject

```bash
mkdir -p ~/fpp-genesis-rehearsal
printf '%s\n' 'FORECAST_PROVENANCE_GEN001_REHEARSAL_ONLY' > ~/fpp-genesis-rehearsal/subject.txt
sha256sum ~/fpp-genesis-rehearsal/subject.txt
```

Use this exact subject for all wall-clock and OpenTimestamps rehearsals.

## B. Generate the bootstrap key locally

```bash
bash scripts/genesis/generate_bootstrap_key.sh ~/fpp-genesis-private
```

Keep private:

```text
~/fpp-genesis-private/bootstrap_ed25519_private.pem
```

Safe to provide later after inspection:

```text
~/fpp-genesis-private/bootstrap_ed25519_public.pem
~/fpp-genesis-private/bootstrap_ed25519_public.pem.sha256
```

## C. Run RFC 3161 rehearsals

Primary candidate 1:

```bash
bash scripts/genesis/rfc3161_rehearsal.sh \
  ~/fpp-genesis-rehearsal/subject.txt \
  https://freetsa.org/tsr \
  ~/fpp-genesis-rehearsal/freetsa
```

Primary candidate 2:

```bash
bash scripts/genesis/rfc3161_rehearsal.sh \
  ~/fpp-genesis-rehearsal/subject.txt \
  http://timestamp.digicert.com \
  ~/fpp-genesis-rehearsal/digicert
```

Recommended backup candidate:

```bash
bash scripts/genesis/rfc3161_rehearsal.sh \
  ~/fpp-genesis-rehearsal/subject.txt \
  http://timestamp.sectigo.com \
  ~/fpp-genesis-rehearsal/sectigo
```

A successful response remains unqualified until final review verifies subject imprint, nonce, signer and chain, policy OID, conservative time bound, revocation evidence, and tool behavior.

## D. Run OpenTimestamps rehearsal

Stamp:

```bash
bash scripts/genesis/ots_rehearsal.sh \
  stamp \
  ~/fpp-genesis-rehearsal/subject.txt \
  ~/fpp-genesis-rehearsal/ots
```

After Bitcoin confirmation is available, upgrade:

```bash
bash scripts/genesis/ots_rehearsal.sh \
  upgrade \
  ~/fpp-genesis-rehearsal/subject.txt \
  ~/fpp-genesis-rehearsal/ots
```

Strong verification requires explicit owner-controlled Bitcoin Core RPC.

Set `OTS_BITCOIN_NODE` locally. The script does not persist the value because it may contain credentials.

```bash
export OTS_BITCOIN_NODE='http://USER:PASS@127.0.0.1:8332/'

bash scripts/genesis/ots_rehearsal.sh \
  verify \
  ~/fpp-genesis-rehearsal/subject.txt \
  ~/fpp-genesis-rehearsal/ots

unset OTS_BITCOIN_NODE
```

Prefer a credential-entry method that does not leave the RPC secret in shell history.

If `OTS_BITCOIN_NODE` is absent, current script behavior must fail closed.

## E. Retrieve the three official retrospective source fixtures

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

Then validate the raw bytes through the fail-closed adapters:

```bash
PYTHONPATH=src python3 scripts/genesis/validate_retrospective_source_fixture.py \
  ~/fpp-genesis-source-fixtures/bls_cpi_2026_07_first_release \
  --output ~/fpp-genesis-source-fixtures/bls_cpi_2026_07_first_release/adapter_report.json

PYTHONPATH=src python3 scripts/genesis/validate_retrospective_source_fixture.py \
  ~/fpp-genesis-source-fixtures/bls_u3_2026_08_first_release \
  --output ~/fpp-genesis-source-fixtures/bls_u3_2026_08_first_release/adapter_report.json

PYTHONPATH=src python3 scripts/genesis/validate_retrospective_source_fixture.py \
  ~/fpp-genesis-source-fixtures/bea_gdp_2026_q2_advance \
  --output ~/fpp-genesis-source-fixtures/bea_gdp_2026_q2_advance/adapter_report.json
```

Every resulting report must remain `prospective_eligible=false`.

## F. Materialize the current candidate inventory

```bash
PYTHONPATH=src python3 scripts/genesis/materialize_candidate.py \
  --output ~/fpp-genesis-rehearsal/effective_candidate_inventory_v0_3.json
```

This validates v0.2 base plus v0.3 patch and emits the deterministic 22-object inventory.

## G. Final repository test and validator binding

Do this only after all intended repository changes are committed and the working tree is clean.

```bash
bash scripts/genesis/run_final_readiness_tests.sh \
  ~/fpp-genesis-rehearsal/final-tests
```

If tests pass:

```bash
COMMIT="$(git rev-parse HEAD)"

PYTHONPATH=src python3 scripts/genesis/build_validator_binding.py \
  --git-commit "$COMMIT" \
  --test-report ~/fpp-genesis-rehearsal/final-tests/final_readiness_test_report.txt \
  --output ~/fpp-genesis-rehearsal/validator_contract.json
```

Do not build the final ValidatorContract after a failed test run or from a dirty working tree.

## H. What to provide back for project review

Do not provide the private key.

The review package may contain:

1. bootstrap public key and SHA256;
2. FreeTSA, DigiCert, and optional Sectigo rehearsal directories;
3. OpenTimestamps rehearsal directory;
4. three retrospective official fixture directories with adapter reports;
5. effective candidate inventory;
6. final readiness test report and sidecar SHA256;
7. ValidatorContract candidate.

Before transfer, inspect the package for secrets.

## Completion boundary

Returning this evidence does not create Genesis.

The project must still qualify ProviderProfiles, freeze the OTS verifier profile and BootstrapGovernanceRoot, build the final candidate TrustedManifest, complete final adversarial review, sign ManifestAcceptance, externally evidence it, and pass a separate explicit Genesis acceptance decision.