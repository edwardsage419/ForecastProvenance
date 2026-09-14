# Current State

Date: 2026-09-14
Project: Forecast Provenance Project
State: PRE_GENESIS_ARCHITECTURE_COMPRESSION

Current formal branch and transition basis:

```text
branch = design/gen-001
transition_basis_commit = b8356f70844034fa7c448be30f39312ef95907cc
```

The commit containing this file must be identified from Git metadata. This document does not embed its own commit SHA.

## Current project direction

The active pre-Genesis workstream is **Pre-Genesis Architecture Compression**.

The immediate objective is to reduce Genesis v1 to the smallest credible trust core that can establish a genuine prospective history while preserving independent auditability of mandatory cycles, attempts, failures, omissions, information cutoffs, execution, resolution, and evaluation cohorts.

The previous Roughtime production qualification workstream is paused as the active mainline. Existing qualification criteria, evidence, schemas, validators, reports, and historical rehearsal classifications remain retained evidence and are not reinterpreted or deleted.

No further production qualification governance expansion or live provider execution is part of the current workstream unless a new correctness or security defect requires it or a later project-control decision explicitly reopens it.

## Architecture Compression sequence

```text
P0  project-control transition and non-normative review record                COMPLETE
P1  reconcile Genesis anchoring requirements and single-anchor candidate      NEXT
P2  separate temporal and durability claims from derived eligibility          PENDING
P3  remove unused Genesis v1 dependencies and reduce review/evaluation surface PENDING
P4  establish provider-qualification complexity firewall                      PENDING
P5  update candidate objects, schemas, validators, tests, readiness controls  PENDING
P6  rerun complete offline regression and synthetic adversarial suite          PENDING
P7  reconsider need for Roughtime production qualification only after refreeze PENDING
P8  separate final pre-Genesis high-level review                              PENDING
P9  separate explicit Genesis authorization                                  PENDING
```

## P0 control decision

P0 records the workstream transition without changing Genesis candidate semantics.

The controlling non-normative review record is:

`docs/GEN_001_PRE_GENESIS_ARCHITECTURE_COMPRESSION_REVIEW_2026_09_14.md`

The transition establishes these control rules:

1. Architecture Compression is the active repository mainline.
2. Production qualification remains a supporting subsystem rather than the active Trust Core development track.
3. The Trust Core may consume frozen `ProviderProfile`, `QualificationDecision`, criteria version, and evidence-package hash after those inputs satisfy their own subsystem rules.
4. Existing production qualification evidence remains historically classified exactly as recorded.
5. P1 through P5 must use explicit versioned changes where normative semantics change. No existing candidate is silently reinterpreted.
6. P6 is an offline validation gate. Network provider requests remain unauthorized.

## Current Genesis v1 design direction

The intended minimum Genesis v1 profile remains limited to capabilities actually used at Genesis:

1. a small number of low-frequency targets whose official schedules can be reconstructed;
2. deterministic issuance schedules and mandatory cycle universe;
3. deterministic or fully auditable execution, with the initial method surface kept minimal;
4. point-in-time `SourceContract` inputs;
5. complete attempt, retry, failure, and omission accounting;
6. immutable forecast, correction, resolution, and evaluation cohort records;
7. external deadline-existence evidence;
8. durable public anchoring;
9. exact `ValidatorContract`;
10. `BootstrapGovernanceRoot`, `TrustedManifest`, and `ManifestAcceptance`.

Unused stochastic execution, public randomness, `FittedState`, closed-model strong-confirmatory support, custom transparency logging, complex identity systems, and additional time protocols remain deferred until a real use case requires them.

## Genesis anchoring review target

P1 must reconcile the current specification inconsistency between multi-stage anchoring requirements and the acceptance/readiness controls.

The current design direction to review is:

```text
BootstrapGovernanceRoot
→ TrustedManifest
→ Validation Reports
→ owner-signed ManifestAcceptance
→ one final external time/durability evidence package
→ independent final validation
→ separate explicit Genesis authorization
```

This is a review target only. P0 does not change the current normative anchoring requirements.

## Temporal claim separation target

P2 will explicitly separate at least these claims:

```text
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

P0 does not alter any current validator result or historical classification.

## Evaluation direction

Genesis v1 evaluation should prioritize cohort integrity. The minimum scoring surface may be limited to resolved outcome, forecast value, absolute error, and squared error while preserving expected, issued, failed, omitted, ineligible, unresolved, and withdrawn denominators.

Any removal of existing candidate evaluation requirements requires a versioned P3 or P5 change and review.

## Retained production qualification state

The production qualification subsystem remains historically retained with its existing frozen criteria and evidence.

```text
PRODUCTION_QUALIFICATION_CRITERIA = FROZEN_V1
criteria_id = FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1
criteria_sha256 = 88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
ACTIVE_MAINLINE = PAUSED
```

The retained rehearsal remains:

```text
classification = NON_FORECAST_REHEARSAL
prospective_eligible = false
```

No rehearsal result is upgraded by this transition.

## Repository and PR control

PR #6 remains the active design PR and must remain Draft, open, and unmerged unless separately authorized.

The PR description should describe Architecture Compression as the active workstream while retaining the historical production-qualification evidence as supporting context.

## Network boundary

```text
network_authorized = false
Roughtime provider requests authorized by this state = 0
RFC3161 requests authorized by this state = 0
```

No new live provider request is authorized by Architecture Compression P0 through P6 unless the owner separately grants exact authorization.

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

The Genesis Ed25519 private key remains outside the repository, GitHub, CI, ChatGPT, Codex, logs, prompts, fixtures, and third-party systems. Only the public key may become a project object when the appropriate later governance step is reached.
