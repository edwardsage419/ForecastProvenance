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
P4  establish provider-qualification complexity firewall                       COMPLETE
P5  consolidated versioned implementation of P1-P4                            NEXT
P6  rerun complete offline regression and synthetic adversarial suite           PENDING
P7  reconsider need for Roughtime production qualification only after refreeze PENDING
P8  separate final pre-Genesis high-level review                               PENDING
P9  separate explicit Genesis authorization                                    PENDING
```

## P1 Genesis anchoring reconciliation

Controlling record:

`docs/GEN_001_GENESIS_ANCHORING_RECONCILIATION_V1.md`

Successor governance path:

```text
BootstrapGovernanceRoot
→ TrustedManifest
→ Validation Reports
→ owner-signed ManifestAcceptance
→ one final external time/durability evidence package
→ independent final validation
→ separate explicit Genesis authorization
```

The exact signed `ManifestAcceptance` is the mandatory final external-evidence subject. Standalone bootstrap-governance and candidate-manifest anchors are optional audit evidence.

## P2 temporal claim separation

Controlling record:

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

## P3 Genesis v1 dependency compression

Controlling record:

`docs/GEN_001_GENESIS_V1_DEPENDENCY_COMPRESSION_V1.md`

Genesis v1 instantiates only capabilities consumed by the initial deterministic method and selected target profile.

Dormant Trust Core interfaces remain available for successor manifests but are not Genesis v1 dependencies or readiness blockers, including:

```text
PublicRandomnessPolicy
FittedState
fitted model state
closed-model observability and retrieval paths
POSTCOMMIT_PUBLIC_RANDOMNESS
EXTERNALLY_AUDITED_ATTEMPTS
multi-method comparison machinery
```

The only initial method remains:

```text
method:last-observed-value:v1
selection_control_class = DETERMINISTIC_REPLAY
randomness_policy = NONE
```

Genesis v1 removes the instantiated scientific Human Review Policy from the successor profile. Official-source conflict or semantic ambiguity remains `REVIEW_REQUIRED` or `UNRESOLVED`; no ReviewDecision may select a resolved value under the compressed profile.

Minimum normative numerical evaluation is:

```text
resolved_outcome
forecast_value
absolute_error
squared_error
```

Cohort accounting preserves at least:

```text
expected
issued
failed
omitted
ineligible
unresolved
withdrawn
```

The current design target after P5 is 21 effective candidate objects if no additional Genesis-specific normative policy object is required. Final cardinality must be recomputed from actual P5 dependency closure.

## P4 provider-qualification complexity firewall

Controlling record:

`docs/GEN_001_PROVIDER_QUALIFICATION_COMPLEXITY_FIREWALL_V1.md`

Forecast Trust Core consumes only a small frozen provider-admission interface. Qualification research and workflow machinery remain a supporting subsystem.

### Static manifest boundary

The successor TrustedManifest should bind:

```text
deadline_receipt_quorum_policy_ref
provider_profile_refs
qualification_decision_refs
qualification_verifier_contract_ref
```

Genesis v1 binds exactly three ProviderProfiles and exactly three matching QualificationDecisions.

A valid signed QualificationDecision transitively binds the exact frozen criteria, ProviderProfile, qualification evidence-manifest SHA256, verifier build identity, independent review, metadata-review basis, authority, and decision result. TrustedManifest therefore does not duplicate the full qualification workflow or criteria matrix.

### Dynamic historical provider state

A signed production qualification decision is not sufficient for every later deadline event because metadata-review expiry and requalification triggers are time-dependent.

For each consequential deadline event, provider state is recomputed with:

```text
as_of_utc = frozen_deadline_utc
```

All three manifest-admitted providers must derive to:

```text
PRODUCTION_QUALIFIED
```

before the event can operate as the frozen production-ready three-provider set. The receipt quorum then remains two-of-three.

A provider outage does not lower the receipt threshold. A provider that is expired, blocked, or requires requalification prevents a new Genesis v1 deadline event from receiving the stronger admitted-provider claim.

### Qualification-state input completeness

P4 identified a concrete boundary gap in the existing authoritative state API: the validator recomputes correctly from supplied metadata-review and requalification-event sequences, but the caller currently supplies those sequences and their completeness is not independently closed.

P5 must add a content-closed supporting qualification-state package and authoritative collector/verifier so a retained disqualifying event cannot be silently omitted from the state basis.

The supporting state package is not a new governance policy and does not grant qualification by itself.

The Trust Core adapter consumes an equivalent minimal result:

```text
provider_profile_ref
qualification_decision_ref
qualification_verifier_contract_ref
qualification_state_package_sha256
as_of_utc
qualification_state
```

Only `qualification_state = PRODUCTION_QUALIFIED` is admissible for a qualifying Genesis v1 deadline event.

### Qualification package terminology

The content-closed initial QualificationEvidencePackage must be finalized before the signed QualificationDecision because the decision binds the evidence-manifest SHA256.

The later signed decision is retained in the broader QualificationRecordSet but cannot also be a file covered by the same pre-decision evidence manifest without circularity.

P5 must align implementation and documentation terminology with this executable ordering without weakening the frozen qualification criteria.

## Current implementation alignment

```text
P1_ANCHORING_RECONCILIATION = COMPLETE
P2_TEMPORAL_CLAIM_SEPARATION = COMPLETE
P3_DEPENDENCY_COMPRESSION = COMPLETE
P4_PROVIDER_QUALIFICATION_COMPLEXITY_FIREWALL = COMPLETE
CURRENT_V0_5_CANDIDATE_ALIGNED = NO
CURRENT_VALIDATOR_ALIGNED = NO
CURRENT_READINESS_MATRIX_ALIGNED = NO
CURRENT_EVALUATION_REPORTING_ALIGNED = NO
CURRENT_PROVIDER_ADMISSION_FIREWALL_ALIGNED = NO
P5_VERSIONED_IMPLEMENTATION_REQUIRED = YES
GENESIS_READY = NO
```

P1 through P4 are design controls. Historical candidate files, validator semantics, readiness entries, abort conditions, and tests retain their historical behavior until P5 performs the consolidated versioned implementation.

## P5 next gate

P5 is the first Architecture Compression implementation phase.

It must implement P1 through P4 together through explicit versioned successor material rather than editing or silently reinterpreting historical candidate objects.

P5 covers at least:

```text
successor candidate patch and exact object retirement/replacement
successor AcceptancePolicy
minimal EvaluationPolicy
retirement of Genesis Human Review Policy
TrustedManifest provider-admission fields
noncircular ManifestAcceptance validation
P2 temporal claim vector and state vocabulary
content-closed provider qualification-state package
qualification-admission adapter
production receipt provider-profile admission checks
readiness matrix
abort conditions
schemas
validators
tests
adversarial review updates
```

The provider-state package is a supporting evidence boundary. P5 must preserve the existing frozen qualification criteria and historical qualification object semantics. Any correctness repair to a supporting schema or validator must be versioned or otherwise explicitly compatibility-scoped; no existing production qualification decision exists to migrate.

P5 remains offline and does not execute production qualification.

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
production qualification requests authorized by this state = 0
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
