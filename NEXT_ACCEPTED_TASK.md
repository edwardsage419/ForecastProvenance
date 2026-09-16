# Next Accepted Task

Task ID: GEN_001-POST-P6-CORRECTNESS-REPAIR-REGRESSION
State: PRE_GENESIS ARCHITECTURE COMPRESSION REPAIR; HISTORICAL P6 PASS PRESERVED; POST-P6 REPAIR IMPLEMENTED; FRESH P6 REQUIRED; P7 PAUSED; PROVIDER NETWORK REQUEST NOT AUTHORIZED

## Objective

Complete and validate the post-P6 correctness repair recorded in:

```text
docs/GEN_001_POST_P6_CORRECTNESS_REPAIR_2026_09_16.md
```

The next accepted execution is a fresh complete offline P6 regression from zero on one exact final repair HEAD.

P7 dependency reevaluation remains paused until that regression passes. No production qualification execution or provider request is part of this task.

## Historical fact preservation

The prior P6 execution remains retained historical provenance:

```text
historical P6 exact HEAD = 70dc89f187842d8dcc6ba428241aae614d520bd4
historical P6 evidence manifest SHA256 = a330a3952b55ce0f4415f25c5580ad2cdf53c05801e78f728239ab73caa8bb5d
historical result = PASS
```

Post-P6 review found additional correctness gaps after that execution. The historical PASS is not regression evidence for the repaired source tree.

No historical P6 artifact, result or candidate byte may be silently rewritten.

## Current repaired surfaces

The repair includes at minimum:

```text
src/forecast_trust_core/production_evidence_contracts_v1.py
src/forecast_trust_core/production_receipt_admission_v1.py
src/forecast_trust_core/claim_authority_v1.py
tests/test_production_receipt_admission_v1.py
tests/test_claim_authority_v1.py
tests/test_production_evidence_contracts_v1.py
```

Control documentation is updated to preserve the distinction between the historical P6 result and the current repaired implementation.

Candidate lineage remains v0.6 with 21 effective objects. Candidate bytes are not changed by this repair.

## Open finding that is not closed by this repair

```text
P7_F1 = PRODUCTION_WALL_CLOCK_CLAIM_DOES_NOT_BIND_COMPLETE_FROZEN_PROVIDER_EXECUTION_ACCOUNTING
status = OPEN
```

The current `policy:deadline-receipt-quorum:v3` attempt-all-three semantic must not be silently removed or reinterpreted.

No `NON_FORECAST_REHEARSAL` execution report may be promoted to production evidence.

A successor policy change or a new production execution-accounting authority requires later P7 design review after fresh P6 passes.

## Repository safety precheck

Before any test execution or further repair, dynamically establish:

```text
repository = edwardsage419/ForecastProvenance
intended branch / checkout = exact repair tree under review
PR #6 = Draft / open / unmerged
remote design/gen-001 history = no unexpected movement relative to the reviewed base
```

Required local proof:

```text
git rev-parse HEAD == exact intended repair HEAD
git status --short == empty
```

Unknown tracked modifications, unexpected commits, remote history movement, branch mismatch, or inability to identify the exact tree requires a safety stop.

Do not use `reset --hard`, rebase, merge, force push or deletion of unknown files to manufacture a clean state.

## Fresh P6 execution rule

P6 is validation only.

Once the exact final repair HEAD is selected, do not modify Trust Core source, schemas, candidate bytes, tests or normative controls while accumulating a PASS result.

If any correctness/security failure requires a code/schema/test correction:

```text
fresh P6 = FAILED / INVALIDATED
repair root cause
create a new exact HEAD
restart every mandatory P6 execution step from zero
```

Passing subsets from an earlier repair HEAD cannot be combined with a later repaired HEAD.

## Required execution scope

### 1. Environment capture

Record at minimum:

```text
exact Git commit SHA
Python version
platform
pytest version
jsonschema version
relevant declared dependency versions
```

Retain exact commands and exit codes.

### 2. Python compile/import checks

Compile/import the complete Trust Core and Genesis helper surface, including:

```text
forecast_trust_core.architecture_compression_v1
forecast_trust_core.architecture_compression_v1_hardening
forecast_trust_core.production_evidence_contracts_v1
forecast_trust_core.production_receipt_admission_v1
forecast_trust_core.claim_authority_v1
forecast_trust_core.claim_authority_trust_root_v1
```

Any syntax/import failure blocks P6.

### 3. JSON Schema Draft 2020-12 meta-validation

Run the repository-equivalent Draft 2020-12 schema validation over every schema in `schemas/`.

The repair must not alter historical schema bytes unless a separately identified schema defect requires a versioned repair. The current repair intentionally aligns implementation to existing normative schemas.

### 4. Candidate lineage and historical regression

Verify deterministic materialization of:

```text
candidate_object_set_v0_2.json
+ candidate_patch_v0_3.json
+ candidate_patch_v0_4.json
+ candidate_patch_v0_5.json
+ candidate_patch_v0_6.json
```

Required facts include:

```text
effective object count = 21
historical v0.2-v0.5 bytes unchanged
v0.6 exact predecessor retirements unchanged
no new candidate object introduced by the post-P6 correctness repair
```

Run the historical Trust Core, source, rehearsal, qualification and verifier regressions required by the repository.

### 5. Exact production evidence contract regression

Run focused coverage proving exact contract enforcement for:

```text
ExternalTimeEvidenceBundle
RoughtimeProductionReceiptEvidence
OpenTimestampsProofArtifact
DurabilityVerificationRecord
StrongBitcoinVerifierContract
```

Required negatives include at least:

```text
sealed object with unexpected field
wrong schema_version
wrong object_type
invalid origin_class
invalid prospective_eligible value
missing required field
malformed reference
invalid cardinality where specified
```

A hash-consistent sealed object that violates its normative object contract must fail closed before granting authoritative claim state.

### 6. Production receipt admission regression

Verify that a schema-conforming `RoughtimeProductionReceiptEvidence` can pass exact profile/state binding without copying ProviderProfile fields into the receipt.

Verify rejection of:

```text
wrong provider_profile_ref
wrong qualification_state_package_ref
provider identity mismatch
verifier build profile mismatch
invalid production receipt contract
provider profile with fallback permitted
```

### 7. Claim-authority regression

Exercise at least:

```text
exact claim type/subject binding
exact evidence-object contract before authority
wall-clock strict Roughtime replay
wrong/spliced evidence refs
raw bound/state-string injection rejected
persisted ValidationReport equality
synthetic evidence cannot satisfy production readiness
schema-invalid sealed Bitcoin bundle cannot produce VERIFIED durability
schema-invalid sealed DVR cannot produce VERIFIED pre-outcome durability
```

### 8. Provider qualification firewall and signature authority regression

Verify the existing content-closed provider-state reconstruction and exact qualification authority path, including:

```text
omitted metadata/requalification event fails closed
self-asserted qualification state rejected
three-provider admitted-pool rule remains unchanged
caller signature_verifier rejected
caller authority substitution rejected
wrong independent authority public key rejected
wrong Ed25519 build profile/binary rejected
```

No qualification criteria may be weakened to obtain PASS.

### 9. Roughtime execution/verifier regression

Run existing offline execution-orchestrator and strict-verifier regression suites.

No live provider request is authorized.

The historical rehearsal classification remains `NON_FORECAST_REHEARSAL` and `prospective_eligible=false`.

### 10. Bitcoin durability regression

Verify the exact strong Bitcoin verifier contract and hash-pinned local executable path with synthetic/local fixtures.

No live OpenTimestamps submission or Bitcoin network anchoring action is required by this regression.

### 11. Full repository pytest and synthetic adversarial suite

Run the complete repository pytest suite and the complete synthetic adversarial suite, not only focused tests.

Record pass/fail/skip counts and exit codes.

### 12. Final tree review

Run at minimum:

```text
git diff --check
```

Review the exact diff for:

```text
accidental scope expansion
historical semantic rewrite
Genesis boundary changes
provider qualification state changes
private-key references
live network authorization
weakened fail-closed behavior
new unnecessary dependencies
new recurring paid dependencies
```

## Stop conditions

Immediately stop the related operation if:

1. repository/branch/HEAD/working-tree safety cannot be established;
2. a test reveals a correctness/security defect;
3. the repair would require weakening an existing frozen criterion;
4. a repair would cross the Genesis boundary;
5. the Genesis private key would be accessed or required;
6. live provider traffic would be required;
7. production qualification state would change;
8. an unexpected Git history or remote state appears.

## Completion condition

P7 may resume only after one exact final repair HEAD completes the full fresh P6 regression with no blocking correctness/security finding.

A fresh P6 PASS does not itself authorize Genesis, provider qualification execution, provider requests, Forecast Ledger creation or prospective forecasting.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
production forecasting = PROHIBITED
network_authorized = false
Roughtime provider requests authorized = 0
RFC3161 requests authorized = 0
production qualification requests authorized = 0
P7 = PAUSED_PENDING_FRESH_P6
```

The Genesis Ed25519 private key must remain outside repository, GitHub, CI, ChatGPT, Codex, logs, prompts, fixtures and third-party systems.
