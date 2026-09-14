# Next Accepted Task

Task ID: GEN_001-AC-P3
State: PRE_GENESIS ARCHITECTURE COMPRESSION; P3 GENESIS V1 DEPENDENCY AND REVIEW SURFACE REDUCTION; NETWORK REQUEST NOT AUTHORIZED

## Objective

Reduce the instantiated Genesis v1 dependency set to capabilities actually used by the initial target and method profile, and reduce human review and evaluation surface while preserving provenance, mandatory cycle accounting, temporal claims, immutable history, and cohort integrity.

P3 is a design and dependency reconciliation task. Candidate objects, schemas, validator implementation, readiness matrix, abort conditions, and full tests are updated together later in P5.

## P1 and P2 boundary already established

P1 design control is recorded in:

`docs/GEN_001_GENESIS_ANCHORING_RECONCILIATION_V1.md`

P2 design control is recorded in:

`docs/GEN_001_TEMPORAL_CLAIM_SEPARATION_V1.md`

The successor Genesis governance path uses one mandatory final external evidence package over the exact signed `ManifestAcceptance`.

The successor temporal model separately derives:

```text
EXTERNAL_EXISTENCE_BOUND_VERIFIED
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

P3 must preserve these P1 and P2 properties.

## Initial Genesis profile to audit

The current initial method is:

```text
method:last-observed-value:v1
selection_control_class = DETERMINISTIC_REPLAY
randomness_policy = NONE
```

The initial target set remains the three reconstructable low frequency official release targets already selected for GEN_001.

The initial method does not require stochastic execution, public randomness, model fitted state, hidden model retrieval, closed model observability, or multi method selection.

The current evaluation design also compares forecasts to `method:last-observed-value:v1` as a transparent baseline even though that same method is the only admitted Genesis method. P3 must determine whether that comparison is redundant and should be deferred until a distinct method exists.

## Accepted P3 execution

1. Build an exact inventory of current Trust Core and GEN_001 dependencies that the initial method, targets, schedule, source contracts, time evidence, resolution, correction, retention, and evaluation path actually consume.
2. Identify generic Trust Core interfaces that may remain available for successor manifests without becoming Genesis v1 readiness blockers or mandatory manifest dependencies.
3. Review stochastic execution, `PublicRandomnessPolicy`, `FittedState`, closed model observability, retrieval accounting, transformation state, and similar unused capabilities for removal from the instantiated Genesis profile.
4. Review the current human review policy and determine whether Genesis v1 needs any human semantic override capability. Prefer deterministic fail closed `UNRESOLVED` or `REVIEW_REQUIRED` handling when human discretion adds no necessary provenance value.
5. Review the current evaluation policy and reduce it to the smallest surface needed to preserve cohort integrity and basic point forecast scoring.
6. Specifically review transparent baseline deltas, method comparison, within target aggregation, cross target aggregation, significance claims, and other metrics that have no value with only one admitted method.
7. Preserve expected, issued, failed, omitted, ineligible, unresolved, withdrawn, and temporal claim denominators even if scoring metrics are reduced.
8. Identify every current candidate object, policy field, manifest dependency, readiness item, abort condition, validator path, schema, and test affected by the proposed compression.
9. Define successor semantics without editing or reinterpreting historical candidate objects.
10. Keep all work offline.

## Required P3 properties

The P3 candidate must preserve at least these properties:

1. deterministic mandatory cycle and slot construction;
2. complete attempt, retry, failure, omission, and withdrawal accounting;
3. point in time source evidence and frozen information cutoffs;
4. exact target, method, source, schedule, and resolution bindings;
5. P2 temporal and durability claim separation;
6. immutable forecast, correction, resolution, and evaluation history;
7. cohort inclusion derived from expected slots rather than successful forecast selection;
8. unresolved outcomes and failed temporal claims remain visible in denominators;
9. no human review may override cryptographic mismatch, future information, missing mandatory cycle evidence, output selection violation, or failed required time claims;
10. future capabilities may be added through successor manifests without reinterpreting Genesis history.

## Design questions P3 must answer

1. Can `PublicRandomnessPolicy` be completely absent from the Genesis v1 manifest and cycle plan when every admitted method declares `randomness_policy = NONE`?
2. Can `FittedState` and fitted transformation requirements be absent when the initial method performs no fitting?
3. Can closed model observability and retrieval accounting remain dormant Trust Core interfaces rather than Genesis blockers?
4. Can human review be removed from Genesis v1 resolution and replaced by deterministic unresolved semantics for official source ambiguity or layout change?
5. Should `policy:genesis-human-review:v1` be retired from the successor Genesis candidate if no unavoidable human review case remains?
6. Should transparent baseline comparison be removed because the only admitted method is itself the transparent baseline?
7. Should Genesis v1 evaluation retain only resolved outcome, forecast value, absolute error, squared error, and complete denominator accounting?
8. Should aggregate MAE, RMSE, baseline deltas, pairwise method comparison, probabilistic scoring, calibration, and leaderboard semantics be deferred until a real second method or forecast class exists?
9. Which generic interfaces should remain in the frozen Trust Core contract while being omitted from the Genesis v1 instantiated dependency graph?

## Out of scope for P3

P3 does not reopen Genesis anchoring topology, temporal claim semantics, provider selection, production qualification criteria, Roughtime transport or wire semantics, RFC3161 engineering, target selection, schedule timing margins, or product layer functionality except where an unused direct dependency is identified.

P4 will establish the provider qualification complexity firewall. P5 will perform the consolidated versioned implementation of accepted P1 through P4 changes.

## Network boundary

```text
network_authorized = false
Roughtime provider requests authorized by this task = 0
RFC3161 requests authorized by this task = 0
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

The Genesis Ed25519 private key must not be accessed, read, copied, displayed, uploaded, transmitted, logged, referenced, or processed. Only the public key may enter project objects at a later authorized governance step.
