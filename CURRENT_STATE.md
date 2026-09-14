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
P3  remove unused Genesis v1 dependencies and reduce review/evaluation surface COMPLETE
P4  establish provider-qualification complexity firewall                       NEXT
P5  update candidate objects, schemas, validators, tests, readiness controls   PENDING
P6  rerun complete offline regression and synthetic adversarial suite           PENDING
P7  reconsider need for Roughtime production qualification only after refreeze PENDING
P8  separate final pre-Genesis high-level review                               PENDING
P9  separate explicit Genesis authorization                                    PENDING
```

## P0 control record

The workstream transition is recorded in:

`docs/GEN_001_PRE_GENESIS_ARCHITECTURE_COMPRESSION_REVIEW_2026_09_14.md`

P0 changed project control state only and preserved historical semantics.

## P1 Genesis anchoring reconciliation

P1 design control is recorded in:

`docs/GEN_001_GENESIS_ANCHORING_RECONCILIATION_V1.md`

The successor Genesis governance path is:

```text
BootstrapGovernanceRoot
→ TrustedManifest
→ Validation Reports
→ owner-signed ManifestAcceptance
→ one final external time/durability evidence package
→ independent final validation
→ separate explicit Genesis authorization
```

Standalone bootstrap-governance and candidate-manifest anchors are optional audit evidence in the compressed successor design. The mandatory final external evidence subject is the exact signed `ManifestAcceptance`.

P5 must implement the P1 topology with a new versioned acceptance policy and a noncircular final-validation interface.

## P2 temporal claim separation

P2 design control is recorded in:

`docs/GEN_001_TEMPORAL_CLAIM_SEPARATION_V1.md`

The successor validator separately derives:

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

A stronger claim failure never rewrites a weaker verified historical fact. Bitcoin block header time remains outside the precise civil-time upper-bound role.

For Genesis governance, the exact signed `ManifestAcceptance` is the direct final evidence subject. For Genesis forecast cycles, the direct temporal subjects are the exact `IssuanceCyclePlan`, exact `IssuanceCycleManifest`, and exact `DurabilityVerificationRecord` under the P2 rules.

## P3 Genesis v1 dependency compression

P3 design control is recorded in:

`docs/GEN_001_GENESIS_V1_DEPENDENCY_COMPRESSION_V1.md`

The current v0.5 effective candidate contains 22 normative objects. The compressed successor profile keeps the capabilities actually consumed by the initial deterministic method and selected targets while leaving unused generic Trust Core interfaces dormant.

### Dormant Genesis v1 capabilities

These capabilities are not instantiated Genesis v1 dependencies or readiness blockers:

```text
PublicRandomnessPolicy
FittedState
fitted transformation state
POSTCOMMIT_PUBLIC_RANDOMNESS execution
EXTERNALLY_AUDITED_ATTEMPTS execution
closed-model observability paths
model TrustReport
model retrieval-accounting paths
multi-method comparison policy
```

The generic Trust Core interfaces remain available for successor manifests.

### Human review reduction

Genesis v1 does not instantiate a scientific Human Review Policy.

Official-source conflict, changed layout ambiguity, or insufficient semantic evidence produces `REVIEW_REQUIRED` or `UNRESOLVED`. `REVIEW_REQUIRED` is diagnostic and does not authorize an operator or ReviewDecision to select a resolved value.

P5 must retire historical candidate object `policy:genesis-human-review:v1` by exact predecessor hash in the successor candidate lineage. The historical object remains immutable.

### Evaluation reduction

The only initial method is:

```text
method:last-observed-value:v1
selection_control_class = DETERMINISTIC_REPLAY
randomness_policy = NONE
```

Because this same method is the current evaluation baseline, baseline deltas are tautologically zero in a one-method Genesis. P3 therefore defers baseline comparison, method comparison, aggregation, significance claims, and similar predictive-skill surfaces until a distinct second method exists.

The minimum Genesis v1 numerical evaluation is:

```text
resolved_outcome
forecast_value
absolute_error
squared_error
```

Cohort integrity remains mandatory. At minimum these denominator classes remain visible:

```text
expected
issued
failed
omitted
ineligible
unresolved
withdrawn
```

P2 temporal claim states remain separately inspectable and cannot be hidden inside a generic nonscorable label.

### Successor object-count target

If P1, P2, and P3 are implemented without another Genesis-specific policy object, the expected compressed candidate count after P5 is 21. This is a P3 design target, not a frozen P5 result.

The reduction comes from retiring the instantiated Human Review Policy. EvaluationPolicy and AcceptancePolicy are replaced by successor versions and therefore do not reduce cardinality.

## Current implementation alignment

```text
P1_ANCHORING_RECONCILIATION = COMPLETE
P2_TEMPORAL_CLAIM_SEPARATION = COMPLETE
P3_DEPENDENCY_COMPRESSION = COMPLETE
CURRENT_V0_5_CANDIDATE_ALIGNED = NO
CURRENT_VALIDATOR_ALIGNED = NO
CURRENT_READINESS_MATRIX_ALIGNED = NO
CURRENT_EVALUATION_REPORTING_ALIGNED = NO
P5_VERSIONED_IMPLEMENTATION_REQUIRED = YES
GENESIS_READY = NO
```

P1 through P3 are design controls. Historical candidate files, validators, readiness entries, abort conditions, and tests retain their historical behavior until P5 performs the consolidated versioned implementation.

## P4 next gate

P4 establishes the provider-qualification complexity firewall.

The intended boundary is that Forecast Trust Core consumes only a small frozen qualification interface, including exact provider identity/profile, exact qualification decision, qualification criteria identity/version, and retained evidence-package content identity.

Qualification execution, evidence collection, transport diagnostics, governance review mechanics, requalification workflow, and other supporting internals remain outside the core forecast-validation dependency graph unless a concrete security property requires otherwise.

P4 does not reopen provider selection, lower qualification criteria, authorize a live provider request, or create a production qualification decision.

## Genesis v1 minimum direction

The intended minimum profile remains:

1. a small number of low-frequency targets with reconstructable official schedules;
2. deterministic issuance schedules and mandatory cycle universe;
3. one deterministic replayable initial method;
4. point-in-time `SourceContract` inputs;
5. complete attempt, retry, failure, and omission accounting;
6. immutable forecast, correction, resolution, and evaluation-cohort records;
7. deadline-existence evidence;
8. durable public anchoring;
9. exact `ValidatorContract`;
10. `BootstrapGovernanceRoot`, `TrustedManifest`, and `ManifestAcceptance`;
11. minimal per-forecast absolute and squared error scoring plus complete denominators.

Unused future capabilities remain available only through successor manifests and versioned policies.

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

PR mergeability is dynamic and must be rechecked before any later integration action.

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

The Genesis Ed25519 private key remains outside repository, GitHub, CI, ChatGPT, Codex, logs, prompts, fixtures, and third-party systems. Only the public key may enter project objects at a later separately authorized governance step.
