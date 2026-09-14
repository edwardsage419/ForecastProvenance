# Next Accepted Task

Task ID: GEN_001-AC-P5-CLAIM-AUTHORITY-CLOSURE
State: PRE_GENESIS ARCHITECTURE COMPRESSION; P5 REOPENED FOR P2 CLAIM AUTHORITY CLOSURE; NETWORK REQUEST NOT AUTHORIZED

## Objective

Close P6 Finding 3 by implementing the minimum authoritative offline evidence-to-claim reconstruction path required by P2.

The repair must ensure that no Genesis readiness decision, cycle deadline decision, durability decision, confirmatory eligibility decision, or final ManifestAcceptance validation can be established from caller-supplied claim states, booleans, untyped time bounds, or self-asserted `ValidationReport.derived_claims`.

This is a P5 correctness repair. P6 is stopped and must restart only after this repair is complete and the exact new HEAD is frozen for regression.

## Controlling finding

`docs/GEN_001_P6_FINDING_3_CLAIM_AUTHORITY_BOUNDARY_2026_09_14.md`

Retained controlling designs:

```text
docs/GEN_001_GENESIS_ANCHORING_RECONCILIATION_V1.md
docs/GEN_001_TEMPORAL_CLAIM_SEPARATION_V1.md
docs/GEN_001_PROVIDER_QUALIFICATION_COMPLEXITY_FIREWALL_V1.md
docs/GENESIS_TIME_EVIDENCE.md
```

The repair implements those semantics. It does not reopen their substantive policy decisions.

## Repository safety precheck

Before any write or test conclusion, recheck dynamically:

```text
repository = edwardsage419/ForecastProvenance
branch = design/gen-001
PR #6 = Draft / open / unmerged
HEAD = exact current commit
main ancestry = no unexpected divergence
```

Unexpected branch movement, unknown history, conflicting writes, or an inability to identify exact input bytes requires a safety stop before repository mutation.

## Required repair architecture

The authoritative path must have this direction of trust:

```text
exact retained evidence bytes / sealed evidence objects
+ exact frozen policy and ValidatorContract refs
+ exact subject ref
→ deterministic evidence verification
→ deterministic P2 claim derivation
→ deterministic ValidationReport v2
→ exact report/recomputation equality when a persisted report is consumed
→ stronger claim or final readiness decision
```

The reverse direction is prohibited. A reported claim cannot prove the evidence from which it says it was derived.

## P5 repair work

Implement at least the following.

### 1. Claim derivation authority boundary

Define a successor authoritative API whose inputs are exact reconstructible evidence and frozen refs, not claim state strings.

The API must fail closed on malformed, missing, extra, substituted or hash-mismatched evidence.

Do not treat Python object identity, schema validity, content addressing, a self-asserted flag, or a claim mapping supplied by the caller as proof of semantic verification.

### 2. Wall-clock existence reconstruction

Implement a production-shaped offline verification path for external existence using synthetic/local fixtures only.

It must verify enough of the frozen Genesis v1 contract to derive the claim deterministically, including:

```text
exact subject binding
exact frozen deadline where applicable
exact admitted ProviderProfile binding
exact matching QualificationDecision/state-package binding
provider authoritative state at exact as_of deadline
receipt cryptographic-verification evidence or exact retained verifier output under the frozen verifier contract
conservative receipt upper bound
exact two-of-three quorum
no outage threshold reduction
```

The result may then derive:

```text
EXTERNAL_EXISTENCE_BOUND_VERIFIED
DEADLINE_EXISTENCE_VERIFIED
```

The existing rehearsal-only Roughtime receipt contract must not be relabeled or reused as production evidence without an explicit versioned successor contract.

### 3. Bitcoin durability reconstruction

Implement an offline production-shaped path that deterministically verifies or binds the exact inputs needed to derive:

`BITCOIN_DURABILITY_VERIFIED`

At minimum it must fail closed on:

```text
wrong primary subject
wrong ExternalTimeEvidenceBundle
wrong bundle hash
wrong OTS proof binding
missing or failed strong Bitcoin verification report
wrong verifier contract
```

Do not use Bitcoin block header time as a precise civil-time upper bound.

### 4. Pre-outcome durability reconstruction

For scientific forecast subjects, derive `PRE_OUTCOME_DURABILITY_VERIFIED` only from:

```text
verified Bitcoin durability for exact primary subject
+ exact DurabilityVerificationRecord binding
+ exact wall-clock deadline verification over that record
+ frozen outcome_information_barrier
```

Genesis ManifestAcceptance remains `NOT_APPLICABLE` for pre-outcome durability unless a successor policy explicitly creates such a barrier.

### 5. Cycle-plan successor validation

Add a successor cycle-plan validator that consumes authoritative reconstructed claim evidence.

The historical `core.validate_cycle_plan(... verified_plan_existence_bound=...)` remains available for its historical contract but is not a successor P2 authority path.

The successor validator must reject a raw untyped existence bound supplied without exact claim/evidence reconstruction.

### 6. Final Genesis acceptance validation

Replace or wrap the low-level final-acceptance helper with an authoritative entry point that independently reconstructs the required claims for the exact signed ManifestAcceptance.

It must require:

```text
final evidence subject == exact signed ManifestAcceptance ref
EXTERNAL_EXISTENCE_BOUND_VERIFIED(exact acceptance) == VERIFIED
BITCOIN_DURABILITY_VERIFIED(exact acceptance) == VERIFIED
```

It must not accept `external_existence_state="VERIFIED"` or `bitcoin_durability_state="VERIFIED"` as sufficient authority.

### 7. ValidationReport v2 recomputation

Implement deterministic recomputation/equality verification for persisted ValidationReport v2 claim vectors.

A persisted report may be retained as audit history, but any current trust decision must prove that its applicable `derived_claims` exactly equal the output produced by the exact ValidatorContract from the exact retained dependencies.

Report schema validation alone is insufficient.

### 8. Confirmatory eligibility

The existing strict type/subject/set hardening remains required.

Additionally, the final authoritative eligibility path must accept only claims produced by the authoritative recomputation path plus exact non-temporal Trust Core checks. Caller-constructed VERIFIED claim mappings are not authoritative inputs.

## Required adversarial tests

Add deterministic offline tests for at least:

1. correct subject plus fabricated `VERIFIED` existence claim;
2. correct subject plus fabricated `VERIFIED` Bitcoin claim;
3. persisted ValidationReport with structurally valid but non-recomputed claim state;
4. exact report equality after deterministic recomputation;
5. wrong ValidatorContract ref;
6. correct subject with wrong evidence refs;
7. missing retained receipt/evidence object;
8. extra unbound receipt/evidence object where closure is required;
9. one qualifying receipt only;
10. two qualifying receipts from duplicate provider identity;
11. two valid independent admitted receipts;
12. provider state no longer production-qualified at exact deadline;
13. raw cycle-plan existence-bound injection rejected by successor path;
14. final ManifestAcceptance state-string injection rejected;
15. wrong final evidence subject rejected;
16. wrong ExternalTimeEvidenceBundle / OTS binding rejected;
17. failed strong Bitcoin verification rejected;
18. late DurabilityVerificationRecord preserves weaker claims but fails pre-outcome durability;
19. Genesis final acceptance maps pre-outcome durability and scientific eligibility to NOT_APPLICABLE;
20. historical validator behavior remains unchanged.

## Evidence fixture rule

This task is offline only.

Synthetic or locally generated fixtures may model production-shaped objects and verifier outputs, but must be clearly classified as synthetic/non-forecast and cannot become production ProviderProfiles, QualificationDecisions, receipts, forecasts or Genesis evidence.

No test fixture may contain or derive from the Genesis private key.

## Explicitly prohibited shortcuts

Do not use any of the following to close Finding 3:

```text
claims_recomputed = true
verified = true supplied by caller
opaque in-process token as sole authority
schema-valid claim treated as verified
content hash treated as semantic validation
signed/sealed report treated as semantic validation without recomputation
rehearsal receipt relabeled as production
weakened quorum or qualification criteria
```

## Historical compatibility

Historical candidate objects, historical v0.2-v0.5 patches, historical rehearsal artifacts and historical validator semantics remain unchanged.

If a successor candidate or ValidatorContract version is required, add it by exact predecessor-bound versioning. Do not reinterpret prior bytes.

## P6 gate after repair

Only after claim-authority closure is implemented and adversarially reviewed may P6 restart.

The restarted P6 must run the complete offline compile/import, schema, historical regression, candidate v0.6/successor candidate regression, qualification supporting-subsystem regression, full pytest and synthetic adversarial suites against the exact post-repair HEAD.

No earlier P6 result carries forward across repair commits.

## Retained qualification state

```text
PRODUCTION_QUALIFICATION_CRITERIA = FROZEN_V1
criteria_id = FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1
criteria_sha256 = 88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
ACTIVE_MAINLINE = PAUSED
```

This task does not execute qualification and does not change any qualification disposition.

## Network boundary

```text
network_authorized = false
Roughtime provider requests authorized by this task = 0
RFC3161 requests authorized by this task = 0
production qualification requests authorized by this task = 0
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
```

The Genesis Ed25519 private key must not be accessed, read, copied, displayed, uploaded, transmitted, logged, referenced or processed.
