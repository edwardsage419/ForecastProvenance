# Current State

Date: 2026-09-14
Project: Forecast Provenance Project
State: PRE_GENESIS_ARCHITECTURE_COMPRESSION

Current formal branch and Architecture Compression basis:

```text
branch = design/gen-001
architecture_compression_basis_commit = 9790e323a519558b92b7d6c1324b3bd847cfacfe
```

The commit containing this file must be identified from Git metadata. This document does not embed its own commit SHA.

## Active workstream

The active pre-Genesis mainline is **Pre-Genesis Architecture Compression**.

Roughtime production qualification remains paused as the active mainline. Existing frozen criteria, schemas, validators, evidence packages, reviews, and historical rehearsal classifications remain retained supporting evidence.

No live provider execution or qualification execution is authorized by the current workstream.

## Architecture Compression sequence

```text
P0  project-control transition and non-normative review record                 COMPLETE
P1  reconcile Genesis anchoring requirements and single-anchor candidate       COMPLETE
P2  separate temporal and durability claims from derived eligibility           NEXT
P3  remove unused Genesis v1 dependencies and reduce review/evaluation surface PENDING
P4  establish provider-qualification complexity firewall                       PENDING
P5  update candidate objects, schemas, validators, tests, readiness controls   PENDING
P6  rerun complete offline regression and synthetic adversarial suite           PENDING
P7  reconsider need for Roughtime production qualification only after refreeze PENDING
P8  separate final pre-Genesis high-level review                               PENDING
P9  separate explicit Genesis authorization                                    PENDING
```

## P0 control record

The workstream transition is recorded in:

`docs/GEN_001_PRE_GENESIS_ARCHITECTURE_COMPRESSION_REVIEW_2026_09_14.md`

P0 changed project control state only and preserved all historical semantics.

## P1 Genesis anchoring reconciliation

P1 is complete at the design-control level.

The controlling P1 record is:

`docs/GEN_001_GENESIS_ANCHORING_RECONCILIATION_V1.md`

The successor Genesis anchoring topology is:

```text
BootstrapGovernanceRoot
→ TrustedManifest
→ Validation Reports
→ owner-signed ManifestAcceptance
→ one final external time/durability evidence package
→ independent final validation
→ separate explicit Genesis authorization
```

For the successor compressed profile, standalone external anchoring of the bootstrap root, a containing governance envelope, or the candidate manifest is `OPTIONAL_AUDIT_EVIDENCE`.

The mandatory final external evidence subject is the exact signed `ManifestAcceptance`.

The final evidence package is supplied separately to independent final validation. It is not a required self-reference inside the signed `ManifestAcceptance`.

This topology preserves the external trust-root boundary, exact manifest and validation-report binding, owner signature verification, immutable final commitment, independent final validation, and a separate Genesis authorization gate.

## P1 implementation boundary

P1 did not modify historical candidate objects, schemas, validators, readiness matrix entries, or abort conditions.

The current effective candidate lineage remains:

```text
candidate_object_set_v0_2.json
+ candidate_patch_v0_3.json
+ candidate_patch_v0_4.json
+ candidate_patch_v0_5.json
```

Its existing `policy:genesis-acceptance:v1` and the current `validate_manifest_acceptance` semantics are not the successor compressed profile.

P5 must create a new versioned acceptance policy and align candidate objects, validation semantics, readiness controls, abort conditions, and tests. No historical object may be edited or reclassified.

Current alignment state:

```text
P1_ANCHORING_RECONCILIATION = COMPLETE
CURRENT_V0_5_CANDIDATE_ALIGNED = NO
CURRENT_VALIDATOR_ALIGNED = NO
CURRENT_READINESS_MATRIX_ALIGNED = NO
P5_VERSIONED_IMPLEMENTATION_REQUIRED = YES
GENESIS_READY = NO
```

## P2 temporal claim target

P2 must separate the currently coupled time and durability conclusions into explicit independently verifiable claims.

At minimum P2 will review:

```text
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

A timely existence proof must remain a true historical fact even if durable anchoring completes too late for a stronger cohort claim.

Bitcoin durability strengthens resistance to historical rewriting. Bitcoin block header time remains ineligible as a precise civil-time upper bound.

Roughtime and any other wall-clock provider retain their key, operator, and governance trust assumptions. Those assumptions must remain explicit.

## Genesis v1 minimum direction

The intended minimum profile remains limited to capabilities used at Genesis:

1. a small number of low-frequency targets with reconstructable official schedules;
2. deterministic issuance schedules and mandatory cycle universe;
3. deterministic or fully auditable execution with a minimal initial method surface;
4. point-in-time `SourceContract` inputs;
5. complete attempt, retry, failure, and omission accounting;
6. immutable forecast, correction, resolution, and evaluation-cohort records;
7. deadline-existence evidence;
8. durable public anchoring;
9. exact `ValidatorContract`;
10. `BootstrapGovernanceRoot`, `TrustedManifest`, and `ManifestAcceptance`.

Unused stochastic execution, public randomness, `FittedState`, closed-model strong-confirmatory support, custom transparency logging, complex identity systems, additional time protocols, and new recurring paid infrastructure remain deferred.

## Retained production qualification state

```text
PRODUCTION_QUALIFICATION_CRITERIA = FROZEN_V1
criteria_id = FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1
criteria_sha256 = 88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
ACTIVE_MAINLINE = PAUSED
```

Retained provider rehearsal evidence remains:

```text
classification = NON_FORECAST_REHEARSAL
prospective_eligible = false
```

No retained result is upgraded by Architecture Compression.

## Repository and PR control

PR #6 remains the active design PR and must remain Draft, open, and unmerged unless separately authorized.

## Network boundary

```text
network_authorized = false
Roughtime provider requests authorized by this state = 0
RFC3161 requests authorized by this state = 0
```

No prior rehearsal or qualification authorization may be reused.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
production forecasting = PROHIBITED
network_authorized = false
```

The Genesis Ed25519 private key remains outside repository, GitHub, CI, ChatGPT, Codex, logs, prompts, fixtures, and third-party systems. Only the public key may enter project objects at a later authorized governance step.
