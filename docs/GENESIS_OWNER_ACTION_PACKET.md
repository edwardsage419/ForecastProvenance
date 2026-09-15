# GEN_001 Owner Action Packet

Date: 2026-09-13
Status: OWNER ACTION REQUIRED, ALL NEW TIME NETWORK OPERATIONS PAUSED

This is the concise execution packet for remaining owner controlled GEN_001 evidence.

If an older runbook command conflicts with this packet, this packet controls.

All outputs are non forecast readiness evidence. None create Forecast Ledger Genesis.

## Safety rules

1. Work from `design/gen-001` or a later reviewed descendant.
2. Never use a real or unreleased forecast as a rehearsal subject.
3. Never upload, commit, paste, read through connected tools, or send the bootstrap private key.
4. Keep `~/fpp-genesis-private/` outside the repository and outside every package you share.
5. Preserve failed attempts as well as successful attempts.
6. Never weaken deadline receipt quorum because a provider fails.
7. Do not send any Roughtime or RFC 3161 provider request unless a separate task explicitly authorizes the exact request.
8. Do not enter a paid commercial timestamp contract for the current zero cost minimum profile without a separate governance decision.

## A. Prepare one synthetic subject

This local step is allowed:

```bash
mkdir -p ~/fpp-genesis-rehearsal
printf '%s\n' 'FORECAST_PROVENANCE_GEN001_REHEARSAL_ONLY' > ~/fpp-genesis-rehearsal/subject.txt
sha256sum ~/fpp-genesis-rehearsal/subject.txt
```

Use this exact subject only after a future task separately authorizes an external provider rehearsal.

## B. Bootstrap key

The key generation procedure remains defined, but private key handling is a strict owner only action.

Command:

```bash
bash scripts/genesis/generate_bootstrap_key.sh ~/fpp-genesis-private
```

Keep private:

```text
~/fpp-genesis-private/bootstrap_ed25519_private.pem
```

Only these artifacts may later be provided after inspection:

```text
~/fpp-genesis-private/bootstrap_ed25519_public.pem
~/fpp-genesis-private/bootstrap_ed25519_public.pem.sha256
```

This packet does not require generating the key immediately.

## C. Time provider work

The current minimum Genesis candidate no longer requires commercial RFC 3161 qualification.

The active candidate quorum is:

```text
policy:deadline-receipt-quorum:v3
three frozen independent Roughtime provider groups
two independently valid receipts required for each deadline event
```

Current read only candidates:

```text
roughtime.se
time.txryan.com
TimeNL-Roughtime
```

One separately authorized non-forecast rehearsal has completed with three qualifying results and a passing retained-evidence review. The exact authorization was consumed and cannot be reused.

Production qualification criteria remain a draft, production qualification execution is not ready, and no provider is production qualified. Do not query any provider or create another authorization under this packet.

The old RFC 3161 rehearsal commands in earlier runbooks are historical only. Do not execute them for current Genesis minimum qualification.

RFC 3161 checker version 1.3 and retained RFC 3161 rehearsal evidence remain available as auxiliary historical evidence.

## D. OpenTimestamps rehearsal

OpenTimestamps remains part of the selected durability design.

A future owner action may stamp the synthetic subject:

```bash
bash scripts/genesis/ots_rehearsal.sh \
  stamp \
  ~/fpp-genesis-rehearsal/subject.txt \
  ~/fpp-genesis-rehearsal/ots
```

After Bitcoin confirmation is available:

```bash
bash scripts/genesis/ots_rehearsal.sh \
  upgrade \
  ~/fpp-genesis-rehearsal/subject.txt \
  ~/fpp-genesis-rehearsal/ots
```

Strong verification requires explicit owner controlled Bitcoin Core RPC.

A pruned Bitcoin Core node is acceptable if it satisfies the frozen verifier contract.

Set credentials locally and do not persist or share them.

## E. Retrieve the three official retrospective source fixtures

These are already public historical artifacts and remain non prospective.

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

Then validate the retained bytes:

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
  --output ~/fpp-genesis-rehearsal/effective_candidate_inventory_v0_5.json
```

This validates the v0.2 base plus the v0.3, v0.4, and v0.5 patch chain and emits the deterministic 22 object inventory.

## G. Final repository test and validator binding

Do this only after all intended repository changes and external readiness inputs are complete, committed, and reviewed.

```bash
bash scripts/genesis/run_final_readiness_tests.sh \
  ~/fpp-genesis-rehearsal/final-tests
```

Only after a successful clean final run may the exact ValidatorContract be built.

## H. What may be provided back for project review

Do not provide the private key or Bitcoin RPC credentials.

The review package may contain:

1. Bootstrap public key and SHA256.
2. Separately authorized Roughtime rehearsal directories when they later exist.
3. OpenTimestamps rehearsal directory.
4. Three retrospective official fixture directories with adapter reports.
5. Effective candidate inventory.
6. Final readiness test report and sidecar SHA256.
7. ValidatorContract candidate.

Before transfer, inspect the package for secrets.

## Completion boundary

Returning readiness evidence does not create Genesis.

The project must still freeze three qualifying Roughtime ProviderProfiles, freeze the OTS verifier profile and BootstrapGovernanceRoot, build the final candidate TrustedManifest, complete final adversarial review, sign ManifestAcceptance, externally evidence it, and pass a separate explicit Genesis acceptance decision.
