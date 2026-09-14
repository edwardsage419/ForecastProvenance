# GEN_001 Temporal Claim Separation V1

Date: 2026-09-14
Status: ARCHITECTURE_COMPRESSION_P2_DESIGN_CONTROL
Classification: PRE_GENESIS_DESIGN
Prospective eligible: false
Genesis effect: none
Network authorization: none
Basis commit: `58b6a42913ad2a899529d55050335bded579e63a`

## Purpose

This record closes Architecture Compression P2 at the design level.

It separates externally verified wall clock existence, Bitcoin durability, pre outcome durability, and confirmatory prospective eligibility into independently derived claims. A later stronger claim can fail without rewriting a weaker fact that was already validly established.

Historical candidate objects, existing validators, historical reports, rehearsals, and prior classifications retain their original semantics. P5 must implement this design with explicit versioned changes. Until then, the current v0.5 candidate lineage and current validator must not be represented as implementing the P2 claim model.

## Current coupling that requires correction

The current repository already distinguishes wall clock evidence from Bitcoin durability conceptually, yet several surfaces collapse their validation result or downstream consequence.

1. `docs/PROSPECTIVE_TIME_SEMANTICS.md` maps a late external bound directly to `LATE_OR_INELIGIBLE` and an unverifiable bound to `INELIGIBLE_TRUST_UNKNOWN`. This combines a temporal fact with a downstream eligibility conclusion.
2. `docs/TRUST_CORE_CONTRACTS.md` exposes a single derived lifecycle containing `PROSPECTIVE_ELIGIBLE`, `ANCHOR_FAILED`, `LATE_OR_INELIGIBLE`, and `TRUST_UNKNOWN` rather than independent temporal and durability claims.
3. `src/forecast_trust_core/core.py` defines the same aggregate result vocabulary. `validate_external_deadline` returns `PENDING_EXTERNAL_ANCHOR` or `LATE_OR_INELIGIBLE` instead of a deadline existence claim with its own evidence state.
4. `validate_cycle_plan` consumes a raw `verified_plan_existence_bound` directly. The bound is not represented as a separately auditable derived claim.
5. `docs/GENESIS_TIME_EVIDENCE.md` states that final prospective eligibility requires wall clock quorum and Bitcoin durability, then lists both wall clock and durability failures under one final prospective status.
6. `docs/GENESIS_TIME_EVIDENCE.md` correctly requires a separately receipted `DurabilityVerificationRecord` before the outcome information barrier, but the repository does not expose that result as an independent `PRE_OUTCOME_DURABILITY_VERIFIED` claim.
7. `docs/GENESIS_ABORT_CONDITIONS.md` preserves late durability as historical evidence, yet it expresses the operational consequence mainly as exclusion from the confirmatory cohort rather than preserving a full claim vector.
8. `docs/GENESIS_EVALUATION_POLICY.md` has `PROSPECTIVE_ELIGIBILITY_FAILED` as one nonscorable state and reports `prospective_eligible_slots`, but it does not separately expose deadline existence, Bitcoin durability, or pre outcome durability status.
9. `policy:genesis-issuance-schedule:v1` freezes `durability_completion_deadline = OUTCOME_INFORMATION_BARRIER`, but the current candidate lineage has no explicit claim derivation object or result structure for that deadline.
10. `docs/GENESIS_READINESS_EVIDENCE_MATRIX.md` treats the dual time architecture as one closed design item and currently combines manifest and acceptance external time evidence in GR037. P1 already requires that Genesis acceptance anchoring be changed to one final signed acceptance evidence package. P2 adds the requirement that existence and durability results within that package remain distinct.
11. `policy:deadline-receipt-quorum:v3` is a valid input to deadline existence verification. It must remain a receipt qualification policy rather than becoming a general prospective eligibility policy.

## P2 claim model

The successor validator produces a claim vector. Temporal facts are derived outputs and are not stored as mutable trust fields inside `IssuedForecast`, `IssuanceCyclePlan`, `IssuanceCycleManifest`, or `ManifestAcceptance`.

P2 requires these claim types:

```text
EXTERNAL_EXISTENCE_BOUND_VERIFIED
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

`EXTERNAL_EXISTENCE_BOUND_VERIFIED` is the base wall clock claim. It is added because Genesis final acceptance needs an externally verified existence bound even when no scientific outcome deadline applies.

The four claims named by the P2 task remain mandatory outputs where applicable:

```text
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

## Claim state vocabulary

Each claim has exactly one state:

```text
VERIFIED
FAILED
UNRESOLVED
NOT_APPLICABLE
```

`VERIFIED` means every required condition for that exact claim passes under the frozen policy and exact retained evidence.

`FAILED` means available retained evidence deterministically violates a mandatory condition for the claim. For an existence claim, `FAILED` means the protocol verification requirement failed. It does not assert the physical nonexistence of the subject before the deadline.

`UNRESOLVED` means evidence is missing, pending, unavailable, or otherwise insufficient to decide the claim under the frozen validator. It cannot aggregate into a stronger verified claim.

`NOT_APPLICABLE` means the active protocol does not require that claim for the subject class. It must never be treated as `VERIFIED`.

Missing evidence therefore fails closed for stronger trust claims while preserving the distinction between known failure and unresolved evidence.

## Minimal deterministic claim record

P5 should version `ValidationReport` semantics to carry a deterministic `derived_claims` structure rather than creating mutable status fields on scientific objects.

Each derived claim entry should bind at least:

```text
claim_type
subject_ref
state
policy_refs
evidence_refs
reason_codes
```

When a valid wall clock upper bound exists, an existence claim may additionally contain:

```text
verified_upper_bound
frozen_deadline
```

Fields that do not apply are omitted. JSON null remains prohibited under the restricted project canonical model.

The claim array must have deterministic ordering. P5 should sort by claim type, subject object ID, and subject full hash.

The existing top level validation summary may remain for implementation validity, but it must not substitute for the claim vector and must not silently collapse the claim states into one lifecycle label.

## EXTERNAL_EXISTENCE_BOUND_VERIFIED

This claim applies to an exact content addressed subject for which an accepted wall clock receipt policy produces a conservative externally verified upper bound.

For Genesis v1 Roughtime evidence, the claim is `VERIFIED` only when all of the following hold:

1. The evidence bundle binds the exact subject full hash.
2. The frozen receipt quorum policy is the policy admitted by the applicable trusted manifest or Genesis final validation basis.
3. At least the required number of independently controlled frozen provider groups produce qualifying receipts.
4. Every counted receipt validates its subject bound nonce, delegation, response signature, nonce inclusion, provider profile, and conservative midpoint plus radius calculation.
5. Required raw request, response, client random, profile, and verifier evidence are retained sufficiently for independent replay.
6. No unlisted provider is substituted and provider outage does not lower the threshold.

The output includes the conservative verified upper bound admitted by the frozen wall clock policy.

Roughtime provider keys, provider operations, provider time accuracy within the authenticated radius, group independence, hash security, and the frozen verifier remain explicit trust assumptions.

## DEADLINE_EXISTENCE_VERIFIED

This claim is derived only when a frozen protocol deadline exists for the exact subject.

Let `U` be the conservative upper bound from a `VERIFIED` `EXTERNAL_EXISTENCE_BOUND_VERIFIED` claim and let `D` be the frozen deadline bound before output inspection.

```text
DEADLINE_EXISTENCE_VERIFIED = VERIFIED
iff
EXTERNAL_EXISTENCE_BOUND_VERIFIED = VERIFIED
and U <= D
```

If the wall clock claim is verified and `U > D`, the deadline claim is `FAILED`.

If the wall clock claim is `UNRESOLVED`, the deadline claim is `UNRESOLVED`.

If no deadline applies to the subject class, the deadline claim is `NOT_APPLICABLE`.

A later durability result cannot change this claim.

## BITCOIN_DURABILITY_VERIFIED

This claim answers whether the exact external time evidence bundle for a subject is durably committed under the frozen OpenTimestamps and Bitcoin verifier contract.

For a primary subject `S`, let `B` be the exact `ExternalTimeEvidenceBundle` whose `subject_ref` is `S`.

`BITCOIN_DURABILITY_VERIFIED(S)` is `VERIFIED` only when:

1. `B` validly binds `S`, its applicable wall clock evidence, provider profile references, and quorum policy reference.
2. The OpenTimestamps proof binds the exact full hash of `B`.
3. The accepted strong Bitcoin verification path validates the proof under the frozen verifier contract.
4. The retained proof and strong verification evidence are sufficient for independent replay under the accepted retention rule.

A pending or incomplete OpenTimestamps proof produces `UNRESOLVED` while the required proof evidence remains incomplete.

A subject mismatch, proof mismatch, invalid Bitcoin attestation, or failed strong verification produces `FAILED`.

Bitcoin block header time is never interpreted as a precise civil time upper bound for this claim. This claim establishes durability under the accepted Bitcoin trust model. It does not establish that the durable commitment completed before a forecast outcome barrier.

Trust assumptions include the frozen OpenTimestamps proof semantics, Bitcoin consensus and chain security, owner controlled strong verifier behavior, verifier implementation identity, retained proof bytes, and the security of the cryptographic hashes used to bind the evidence package.

## PRE_OUTCOME_DURABILITY_VERIFIED

This claim applies to forecast cycle subjects whose active protocol requires durable commitment to be independently shown complete before the frozen target outcome information barrier.

For a primary subject `S` with external time evidence bundle `B`:

1. `BITCOIN_DURABILITY_VERIFIED(S)` must be `VERIFIED`.
2. A `DurabilityVerificationRecord` must bind `B`, the exact OpenTimestamps proof, and the exact strong Bitcoin verification report.
3. The exact `DurabilityVerificationRecord` is itself a wall clock subject.
4. Its `DEADLINE_EXISTENCE_VERIFIED` claim uses the frozen target `outcome_information_barrier` as the deadline.

The result is:

```text
PRE_OUTCOME_DURABILITY_VERIFIED(S) = VERIFIED
iff
BITCOIN_DURABILITY_VERIFIED(S) = VERIFIED
and
DEADLINE_EXISTENCE_VERIFIED(DurabilityVerificationRecord, outcome_information_barrier) = VERIFIED
```

If Bitcoin durability later becomes verified but the `DurabilityVerificationRecord` has a verified wall clock upper bound later than the frozen outcome information barrier, `PRE_OUTCOME_DURABILITY_VERIFIED` is `FAILED`.

If the required durability evidence or completion evidence remains unavailable or indeterminate, the claim is `UNRESOLVED` and the record remains excluded from the confirmatory cohort.

This rule uses signed wall clock evidence to establish completion before the outcome barrier. Bitcoin block time is not used for that comparison.

## CONFIRMATORY_PROSPECTIVE_ELIGIBLE

This is a stronger derived scientific trust claim for an expected forecast slot and its issued forecast when one exists.

It is never authored by the forecast producer and never stored as a mutable field on `IssuedForecast`.

The claim is `VERIFIED` only when every Trust Core requirement applicable to that slot is verified, including at least:

1. The cycle occurs under an accepted historical trusted manifest and an authorized post Genesis protocol state.
2. The target, method, source contracts, schedule policy, retry policy, omission policy, correction policy, evaluation policy, time evidence policy, and validator contract are admitted by the historical trusted state.
3. The deterministic mandatory cycle and slot construction validates.
4. The exact `IssuanceCyclePlan` satisfies its required plan deadline existence claim.
5. Point in time evidence and information cutoff checks pass.
6. Selection control, attempt accounting, retry behavior, first success selection, and immutable output binding pass.
7. The exact issued forecast full reference appears in the correct mandatory slot accounting of the exact `IssuanceCycleManifest`.
8. The exact `IssuanceCycleManifest` satisfies its forecast deadline existence claim.
9. Every Bitcoin durability claim required by the active Genesis v1 time policy is `VERIFIED`.
10. Every pre outcome durability claim required by the active Genesis v1 time policy is `VERIFIED`.
11. No hard protocol invalidation applies.

If any required input claim is `FAILED` or any hard Trust Core check fails, `CONFIRMATORY_PROSPECTIVE_ELIGIBLE` is `FAILED`.

If no required input has failed but at least one required claim or Trust Core check is `UNRESOLVED`, `CONFIRMATORY_PROSPECTIVE_ELIGIBLE` is `UNRESOLVED`.

Only `VERIFIED` enters the confirmatory prospective cohort. `FAILED` and `UNRESOLVED` remain visible in the mandatory denominator and operational completeness history.

## Genesis governance subject mapping

The compressed P1 Genesis governance path has different semantics from a forecast cycle.

The direct final evidence subject is the exact signed `ManifestAcceptance`.

The final evidence package must establish:

```text
EXTERNAL_EXISTENCE_BOUND_VERIFIED(ManifestAcceptance) = VERIFIED
BITCOIN_DURABILITY_VERIFIED(ManifestAcceptance) = VERIFIED
```

The compressed Genesis profile does not invent an outcome information barrier for governance acceptance. Therefore:

```text
PRE_OUTCOME_DURABILITY_VERIFIED(ManifestAcceptance) = NOT_APPLICABLE
CONFIRMATORY_PROSPECTIVE_ELIGIBLE(ManifestAcceptance) = NOT_APPLICABLE
```

`DEADLINE_EXISTENCE_VERIFIED(ManifestAcceptance)` is `NOT_APPLICABLE` unless the successor acceptance policy explicitly freezes a final acceptance evidence deadline before signing. P1 does not require such a deadline.

Independent final Genesis validation consumes the verified external existence fact and verified Bitcoin durability fact as separate inputs. Separate explicit Genesis authorization remains a later gate.

This preserves the exact existence and durability evidence without creating a scientifically meaningless outcome deadline for Genesis governance.

## Forecast cycle subject mapping

Genesis v1 uses three direct temporal subject classes for one target release cycle.

### IssuanceCyclePlan

The exact sealed `IssuanceCyclePlan` is the direct plan precommitment subject.

Its deadline is:

```text
plan_commitment_deadline
```

The plan must have:

```text
DEADLINE_EXISTENCE_VERIFIED(IssuanceCyclePlan) = VERIFIED
```

before the cycle can satisfy confirmatory eligibility.

### IssuanceCycleManifest

The exact sealed `IssuanceCycleManifest` is the direct forecast deadline subject for Genesis v1.

Its deadline is the cycle plan's frozen:

```text
external_proof_deadline
```

The manifest binds complete slot accounting, attempt references, omission records, and exact full references to issued forecasts. A verified external existence commitment to the manifest therefore commits the complete cycle accounting and exact issued forecast identities under the project's hash security assumptions.

Genesis v1 does not require a separate wall clock provider request for each individual `IssuedForecast` when the forecast's exact full reference is correctly bound into the verified cycle manifest.

An `IssuedForecast` derives its forecast deadline condition through its exact membership in the correct mandatory slot of a cycle manifest whose `DEADLINE_EXISTENCE_VERIFIED` claim is `VERIFIED`.

This reduces repeated external requests while preserving exact forecast content binding and complete cycle accounting.

### DurabilityVerificationRecord

The exact `DurabilityVerificationRecord` is the direct wall clock subject used to prove that Bitcoin durability verification had completed before the frozen outcome information barrier.

Its deadline is:

```text
outcome_information_barrier
```

Its wall clock deadline claim is an input to `PRE_OUTCOME_DURABILITY_VERIFIED` for the corresponding plan or cycle manifest evidence bundle as required by the active time policy.

## Required state preservation examples

A valid timely forecast evidence subject whose Bitcoin commitment is verified only after the outcome barrier can produce:

```text
EXTERNAL_EXISTENCE_BOUND_VERIFIED = VERIFIED
DEADLINE_EXISTENCE_VERIFIED = VERIFIED
BITCOIN_DURABILITY_VERIFIED = VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED = FAILED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE = FAILED
```

A pending Bitcoin proof can produce:

```text
DEADLINE_EXISTENCE_VERIFIED = VERIFIED
BITCOIN_DURABILITY_VERIFIED = UNRESOLVED
PRE_OUTCOME_DURABILITY_VERIFIED = UNRESOLVED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE = UNRESOLVED
```

A subject with valid Bitcoin durability but a late wall clock deadline proof can produce:

```text
DEADLINE_EXISTENCE_VERIFIED = FAILED
BITCOIN_DURABILITY_VERIFIED = VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED = VERIFIED or NOT_APPLICABLE according to subject scope
CONFIRMATORY_PROSPECTIVE_ELIGIBLE = FAILED
```

The last case demonstrates that durability cannot repair a missed wall clock deadline.

## Historical fact preservation

Once a deterministic ValidationReport under an exact ValidatorContract has established a weaker claim from retained evidence, a later stronger claim failure does not rewrite it.

Examples:

1. Late Bitcoin completion does not erase a previously verified forecast deadline existence claim.
2. Loss of evidence bytes later may degrade current verifiability without rewriting the historical claim report that was valid under the retained inputs at that time.
3. A later provider key rotation does not alter a historical receipt that validly verified under the historical frozen ProviderProfile.
4. A later policy version does not reinterpret earlier claim derivation.
5. A failed or unresolved confirmatory eligibility claim does not delete the issued forecast, failed slot, omitted slot, or time evidence from cohort accounting.

## P5 candidate and policy changes required

P5 must implement the P2 design through versioned successor material.

At minimum:

1. Keep `policy:deadline-receipt-quorum:v3` focused on receipt qualification unless P3 or P4 creates a concrete reason for a successor version.
2. Create or version the Genesis time evidence policy so the direct subject classes, claim derivation rules, durability relation, and claim state vocabulary are explicit.
3. Align the successor Genesis acceptance policy from P1 so final signed `ManifestAcceptance` existence and Bitcoin durability are independent final validation inputs.
4. Preserve `policy:genesis-issuance-schedule:v1` historically. If claim semantics require a candidate policy change, use predecessor bound successor versioning rather than editing v1.
5. Keep all historical candidate patches immutable.

## P5 ValidationReport and validator changes required

P5 must update validation semantics so that:

1. `ValidationReport` carries deterministic `derived_claims` for the applicable subject.
2. `Result.LATE_OR_INELIGIBLE` is no longer the authoritative representation of both lateness and prospective eligibility.
3. `validate_external_deadline` is replaced or wrapped by separate existence bound and deadline claim derivation.
4. `validate_cycle_plan` consumes a verified claim or independently reconstructible claim evidence rather than an untyped raw bound with no claim identity.
5. Strong OpenTimestamps and Bitcoin verification produces `BITCOIN_DURABILITY_VERIFIED` independently of wall clock deadline results.
6. `PRE_OUTCOME_DURABILITY_VERIFIED` is derived only from verified Bitcoin durability plus wall clock deadline evidence over the exact bound `DurabilityVerificationRecord`.
7. `CONFIRMATORY_PROSPECTIVE_ELIGIBLE` is a separate final derivation over the full required claim and Trust Core check set.
8. `UNKNOWN` or unresolved required evidence never becomes a verified stronger claim.
9. `NOT_APPLICABLE` never satisfies a required claim.
10. Historical validator behavior remains testable under its historical contract and is not silently reinterpreted.

## P5 schema and report changes required

The current schema directory has no dedicated interoperability schema for the P2 claim vector.

P5 should add a versioned schema for the deterministic derived claim structure or for the successor ValidationReport containing that structure.

The schema must freeze:

```text
claim_type vocabulary
claim state vocabulary
subject full reference
policy full references
evidence full references
reason code vocabulary or contract
optional verified upper bound semantics
optional frozen deadline semantics
deterministic array ordering
```

No claim record may contain a self asserted prospective eligibility value copied from an `IssuedForecast` or operator input.

## P5 readiness changes required

The successor readiness matrix must expose final acceptance existence and Bitcoin durability as distinct closure facts.

For forecast operation readiness, the matrix and final adversarial review must demonstrate that the validator can preserve all P2 claim combinations, including timely existence plus late durability.

Current GR003 and GR037 wording must not be silently reinterpreted. P5 must version or update the active readiness control with an explicit reference to this successor design.

## P5 abort condition changes required

Abort and exclusion rules must name the failed claim rather than collapsing all time failures into one label.

At minimum:

1. Missing or late plan deadline evidence blocks cycle execution or confirmatory status according to the frozen stage rule while preserving its exact claim state.
2. Missing or late cycle manifest deadline evidence blocks confirmatory prospective eligibility while preserving the cycle accounting record.
3. Missing or failed Bitcoin durability blocks the durability claim and stronger eligibility without rewriting deadline existence.
4. Late `DurabilityVerificationRecord` evidence produces `PRE_OUTCOME_DURABILITY_VERIFIED = FAILED` while retaining any valid earlier deadline and Bitcoin durability facts.
5. Unresolved evidence remains visible and fail closed for cohort inclusion.

## P5 evaluation changes required

Evaluation and reporting must retain the claim vector for every expected slot.

At minimum, confirmatory reports must permit independent counts or reconstruction of:

```text
deadline existence verified slots
bitcoin durability verified slots
pre outcome durability verified slots
confirmatory prospective eligible slots
unresolved temporal or durability slots
failed temporal or durability slots
```

P3 may simplify metric breadth, baseline comparison, or aggregation. It must not remove the claim visibility required to audit why an expected slot entered or did not enter the confirmatory cohort.

## P5 test requirements

The consolidated implementation must add deterministic tests for at least these cases:

1. Timely wall clock evidence, Bitcoin durability verified, and pre outcome durability verified.
2. Timely wall clock evidence with Bitcoin proof still pending.
3. Timely wall clock evidence with Bitcoin durability verified only after the outcome barrier.
4. Bitcoin durability verified with a missed forecast wall clock deadline.
5. Missing Roughtime evidence with otherwise valid Bitcoin proof.
6. Exact subject mismatch at the wall clock layer.
7. Exact evidence bundle mismatch at the OpenTimestamps layer.
8. `DurabilityVerificationRecord` bound to the wrong evidence bundle.
9. `DurabilityVerificationRecord` wall clock evidence after the outcome information barrier.
10. Unknown required evidence propagating to unresolved eligibility.
11. `NOT_APPLICABLE` rejected when a claim is required.
12. Cycle manifest membership proving the deadline condition for its exact bound issued forecast without an additional per forecast provider request.
13. A changed issued forecast hash invalidating the cycle manifest binding.
14. Historical claim preservation when later current verifiability degrades.
15. Genesis signed `ManifestAcceptance` final existence and Bitcoin durability validation with pre outcome durability marked `NOT_APPLICABLE`.

The P6 full offline regression and synthetic adversarial suite remains a later gate after P5 implementation.

## Relationship to P3 and P4

P2 freezes claim semantics only.

P3 may remove unused Genesis v1 dependencies and reduce human review or evaluation metric surface. Any such compression must preserve the P2 claim inputs that remain required by the final Genesis profile.

P4 will isolate provider qualification complexity behind frozen supporting outputs. P2 does not reopen provider criteria, provider selection, transport semantics, or wire semantics.

## Current implementation status

```text
P2_TEMPORAL_CLAIM_SEPARATION = COMPLETE
P2_CLAIM_MODEL = COMPLETE
P2_FORECAST_TIME_SUBJECT_MAPPING = COMPLETE
CURRENT_V0_5_CANDIDATE_ALIGNED = NO
CURRENT_VALIDATOR_ALIGNED = NO
CURRENT_READINESS_MATRIX_ALIGNED = NO
CURRENT_EVALUATION_REPORTING_ALIGNED = NO
P5_VERSIONED_IMPLEMENTATION_REQUIRED = YES
GENESIS_READY = NO
```

## Network and qualification boundary

This P2 design requires no provider request and does not reopen production qualification.

```text
network_authorized = false
Roughtime provider requests authorized = 0
RFC3161 requests authorized = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```

No prior rehearsal or qualification authorization may be reused.

## Safety boundary

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production forecasting = PROHIBITED
```

This record does not authorize Genesis, Forecast Ledger creation, forecast issuance, production qualification execution, or any live time provider request.

The Genesis Ed25519 private key remains outside repository and connected tool boundaries. Only the public key may later enter project objects under an authorized governance step.
