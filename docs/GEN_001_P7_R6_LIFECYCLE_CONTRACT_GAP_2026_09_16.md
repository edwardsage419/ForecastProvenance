# GEN_001 P7 R6 Lifecycle Contract Gap

Date: 2026-09-16
Status: PRE_GENESIS_IMPLEMENTATION_FINDING
Classification: PRE_GENESIS_CORRECTNESS_AND_AUTHORITY_GAP
Prospective eligible: false
Genesis effect: none
Network authorization: none
Basis commit: `47126f918392aa174388d3d2b70d198dc92411b3`

## Finding

The P7 architecture decision requires a positive Genesis v1 authority path for `CONFIRMATORY_PROSPECTIVE_ELIGIBLE`. Static implementation review found that the missing work is more fundamental than orchestration alone.

The normative design requires exact lifecycle bindings across:

```text
IssuanceCyclePlan
expected slot
EvidenceSnapshot
ForecastRunAttempt
IssuedForecast
IssuanceCycleManifest
```

but the current repository does not provide machine-exact Genesis-v1 contracts for that complete object chain.

In particular, `schemas/issuance_cycle_plan.schema.json` currently requires only:

```text
plan_commitment_deadline
execution_window_open
execution_window_close
expected_slots
```

while the Genesis schedule contract also requires the plan to bind, at minimum:

```text
schedule_policy_ref
schedule_snapshot_ref
target_instance_ref
method_refs
information_cutoff
plan_commitment_deadline
execution_window_open
execution_window_close
external_proof_deadline
durability_completion_deadline
expected_slots
retry_policy_ref
omission_policy_ref
```

The generic `validate_cycle_plan` additionally checks plan sealing, three timestamps, external precommitment subject/bound, optional schedule-policy binding, and deterministic slot equality. It does not establish the complete Genesis-v1 plan profile above.

The repository also lacks machine-exact schemas for the complete Genesis-v1 expected-slot, EvidenceSnapshot, ForecastRunAttempt, IssuedForecast and IssuanceCycleManifest profiles required for positive confirmatory authority.

## Security consequence

A positive R6 implementation that simply chains the existing generic validators would be incomplete. It could accept a sealed lifecycle object that omits a Genesis-v1 claim-critical binding or carries ambiguous extra structure while still producing passing lower-level validations.

Therefore:

```text
R6_POSITIVE_AUTHORITY = BLOCKED_ON_EXACT_LIFECYCLE_PROFILE
AUTHORITATIVE_CONFIRMATORY_VERIFIED = PROHIBITED
```

The existing repaired fail-closed path remains correct and must not be weakened.

## Repair direction

Historical generic schemas and validators are not retroactively redefined solely to close this finding.

The minimum repair is a Genesis-v1-specific exact authority profile placed at the positive authority boundary, analogous to the post-P6 exact contract gates used for time and durability evidence.

The profile must be derived directly from the already frozen Genesis design documents and existing lifecycle primitives. It must not create a generic universal execution framework.

At minimum, the exact positive-authority profile must define and validate:

1. exact IssuanceCyclePlan field set and reference bindings required by `GENESIS_SCHEDULE_POLICY.md`;
2. exact version-1 expected-slot field set required by `ISSUANCE_AND_RETRY_POLICY.md`;
3. exact baseline EvidenceSnapshot profile required by `GENESIS_BASELINE_METHOD.md`;
4. exact ForecastRunAttempt profile needed by the frozen retry policy and deterministic replay class;
5. exact IssuedForecast profile required by `TRUST_CORE_CONTRACTS.md`;
6. exact IssuanceCycleManifest profile sufficient to prove complete slot, attempt and issued-forecast accounting;
7. deterministic cross-object reference equality across the entire chain;
8. trusted-manifest admission of all normative dependency references;
9. authoritative temporal and durability claims using the repaired public authority paths.

Every object contributing authority must be sealed and must reject unknown claim-critical fields under the Genesis-v1 profile.

## No caller-authored authority

The repair must not accept any of the following as substitutes for reconstructed evidence:

```text
caller-provided replay_verified without deterministic replay evidence
caller-provided complete_attempt_accounting
caller-provided hard_invalidation_reason_codes
caller-provided lifecycle VALID/VERIFIED status
opaque prevalidated object lists
```

Existing generic helper booleans may remain useful in low-level synthetic unit tests but cannot become the positive Genesis-v1 authority root.

## Candidate impact

This finding does not by itself require an additional normative candidate object beyond the already planned v0.7 quorum-policy successor if the exact lifecycle profile is enforced by the frozen ValidatorContract implementation and ValidationReport dependency binding.

If implementation review determines that any lifecycle profile must itself become a first-class normative policy or contract object, that conclusion must be made explicitly before candidate v0.7 is frozen. Object count must not be changed implicitly.

## Sequencing

P7 implementation now proceeds in two independent tracks:

```text
Track A: v4 receipt-quorum policy / P7_F1
Track B: exact Genesis-v1 lifecycle authority profile / R6
```

Track A can be implemented and tested while Track B remains open.

Track B must close before a new full P6-equivalent regression can establish readiness for P8.

## Current state

```text
P7_F1 = OPEN_PENDING_V4_IMPLEMENTATION_AND_REGRESSION
R6 = OPEN_BLOCKED_ON_EXACT_LIFECYCLE_PROFILE_IMPLEMENTATION
AUTHORITATIVE_CONFIRMATORY_VERIFIED = PROHIBITED
CURRENT_DESIGN_EFFECTIVE_CANDIDATE = V0_6
IMPLEMENTATION_BRANCH_CANDIDATE_V0_7 = CREATED_NOT_FROZEN
GENESIS_READY = NO
P8 = PROHIBITED
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
```

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
Roughtime provider requests authorized = 0
RFC3161 requests authorized = 0
production qualification requests authorized = 0
```

No private-key handling is authorized or required by this finding.