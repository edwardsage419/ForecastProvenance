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
P2  separate temporal and durability claims from derived eligibility           COMPLETE
P3  remove unused Genesis v1 dependencies and reduce review/evaluation surface NEXT
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

P1 design control is recorded in:

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

Standalone bootstrap governance and candidate manifest anchoring are optional audit evidence in the successor compressed profile. The mandatory final external evidence subject is the exact signed `ManifestAcceptance`.

The final evidence package is supplied separately to independent final validation and is not a required self reference inside the signed acceptance.

## P2 temporal claim separation

P2 design control is recorded in:

`docs/GEN_001_TEMPORAL_CLAIM_SEPARATION_V1.md`

The successor validator must expose independently derived claims:

```text
EXTERNAL_EXISTENCE_BOUND_VERIFIED
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

Claim states are:

```text
VERIFIED
FAILED
UNRESOLVED
NOT_APPLICABLE
```

A stronger claim failure never rewrites a weaker verified fact. Missing evidence remains unresolved and fails closed for stronger cohort inclusion.

Bitcoin block header time remains outside the precise civil time upper bound role.

### Genesis governance mapping

The exact signed `ManifestAcceptance` is the direct final Genesis evidence subject.

Final validation requires separate verified existence and Bitcoin durability facts for that acceptance. The compressed Genesis governance profile has no scientific outcome barrier, so `PRE_OUTCOME_DURABILITY_VERIFIED` and `CONFIRMATORY_PROSPECTIVE_ELIGIBLE` are not applicable to `ManifestAcceptance`.

### Forecast cycle mapping

Genesis v1 uses these direct temporal subjects:

```text
IssuanceCyclePlan
IssuanceCycleManifest
DurabilityVerificationRecord
```

The exact `IssuanceCyclePlan` must satisfy deadline existence against `plan_commitment_deadline`.

The exact `IssuanceCycleManifest` is the Genesis v1 forecast deadline subject and must satisfy deadline existence against the frozen `external_proof_deadline`. The manifest binds complete slot accounting and exact issued forecast full references, so Genesis v1 does not require a separate wall clock provider request for each individual `IssuedForecast` when the forecast is correctly bound into the verified manifest.

The exact `DurabilityVerificationRecord` is independently wall clock evidenced against the frozen `outcome_information_barrier`. That result, together with independently verified Bitcoin durability, derives `PRE_OUTCOME_DURABILITY_VERIFIED`.

## P1 and P2 implementation boundary

P1 and P2 changed design control only. Historical candidate objects, schemas, validators, readiness matrix entries, abort conditions, and evaluation policy remain unchanged until consolidated P5 implementation.

The current effective candidate lineage remains:

```text
candidate_object_set_v0_2.json
+ candidate_patch_v0_3.json
+ candidate_patch_v0_4.json
+ candidate_patch_v0_5.json
```

Current alignment state:

```text
P1_ANCHORING_RECONCILIATION = COMPLETE
P2_TEMPORAL_CLAIM_SEPARATION = COMPLETE
CURRENT_V0_5_CANDIDATE_ALIGNED = NO
CURRENT_VALIDATOR_ALIGNED = NO
CURRENT_READINESS_MATRIX_ALIGNED = NO
CURRENT_EVALUATION_REPORTING_ALIGNED = NO
P5_VERSIONED_IMPLEMENTATION_REQUIRED = YES
GENESIS_READY = NO
```

`Result.LATE_OR_INELIGIBLE`, the current raw bound handling in `validate_external_deadline` and `validate_cycle_plan`, and the current single prospective eligibility reporting surface are historical implementation semantics. P5 must version their successor behavior rather than silently reinterpret them.

## P3 next gate

P3 must identify Genesis v1 dependencies that are not used by the actual initial method and target profile, and reduce the human review and evaluation surface without weakening cohort integrity, mandatory cycle accounting, point in time evidence, temporal claims, or immutable historical records.

The review must specifically test whether unused stochastic execution, public randomness, `FittedState`, broad human review capabilities, baseline comparison requirements, complex aggregation, and other unused Trust Core dependencies can be removed from the Genesis v1 instantiated profile while remaining available for successor manifests.

Any normative removal or replacement remains deferred to P5 versioned implementation.

## Genesis v1 minimum direction

The intended minimum profile remains limited to capabilities used at Genesis:

1. a small number of low-frequency targets with reconstructable official schedules;
2. deterministic issuance schedules and mandatory cycle universe;
3. deterministic or fully auditable execution with a minimal initial method surface;
4. point-in-time `SourceContract` inputs;
5. complete attempt, retry, failure, and omission accounting;
6. immutable forecast, correction, resolution, and evaluation cohort records;
7. deadline existence evidence;
8. durable public anchoring;
9. exact `ValidatorContract`;
10. `BootstrapGovernanceRoot`, `TrustedManifest`, and `ManifestAcceptance`.

Unused capabilities remain deferred until a real successor use case requires them.

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
