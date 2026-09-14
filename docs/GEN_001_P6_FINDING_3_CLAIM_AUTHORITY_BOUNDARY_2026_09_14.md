# GEN_001 P6 Finding 3: Claim Authority Boundary

Date: 2026-09-14
Status: PRE_GENESIS BLOCKING CORRECTNESS FINDING
Classification: NON_FORECAST_REVIEW
Prospective eligible: false
Network authorization: none

## Scope

This record extends the P6 static review after the first two P5 correctness defects were repaired.

The reviewed repository basis before this finding was:

```text
repository = edwardsage419/ForecastProvenance
branch = design/gen-001
HEAD = 5e8e00f3dc901fb6127be341ff534374312fc6e0
PR #6 = Draft / open / unmerged
```

No provider request, production qualification execution, Genesis action, private-key handling, merge, rebase, force push, or forecast issuance occurred.

## Finding

Severity: BLOCKING FOR P2 CLAIM AUTHORITY AND GENESIS FINAL VALIDATION

P5 and the first P6 hardening pass correctly improved exact claim-type and subject binding, but they did not close the provenance boundary between raw retained evidence and a derived claim marked `VERIFIED`.

The remaining defect is that structurally valid claim records or caller-supplied state values can still be treated as if they were the deterministic output of the exact ValidatorContract.

Three concrete manifestations were identified.

### 1. Final Genesis acceptance trusted caller-supplied states

`validate_final_genesis_acceptance` accepts:

```text
external_existence_state
bitcoin_durability_state
```

as plain strings and checks only whether each equals `VERIFIED`.

Therefore the function can return valid without independently proving that the exact signed ManifestAcceptance produced those claims from retained external time evidence and Bitcoin durability evidence.

This function is henceforth classified as a low-level structural helper only. It is not an authoritative Genesis-final-validation entry point.

### 2. Cycle-plan validation retained an untyped raw time bound

The historical `core.validate_cycle_plan` path still accepts a raw:

```text
verified_plan_existence_bound
```

plus an optional plan reference.

P2 explicitly required the successor path to consume a verified claim or independently reconstructible claim evidence rather than an untyped caller-supplied bound.

The historical function remains available for its historical contract, but it cannot establish successor P2 claim authority.

### 3. ValidationReport v2 freezes claim structure, not derivation truth

`validation_report_v2.schema.json` constrains the claim vocabulary, state vocabulary, references and array structure. That is necessary for interoperability but is not proof that `derived_claims` were actually recomputed from retained evidence under the exact ValidatorContract.

A content hash or structurally valid sealed object prevents silent byte mutation. It does not by itself prove semantic derivation correctness.

A downstream consumer must not treat a reported `VERIFIED` claim as authoritative merely because the report validates structurally, is content addressed, or names the expected validator contract.

## Controlling P2 requirement

`docs/GEN_001_TEMPORAL_CLAIM_SEPARATION_V1.md` already requires:

1. `ValidationReport` claims to be deterministic derived outputs;
2. cycle-plan validation to consume a verified claim or independently reconstructible claim evidence;
3. Bitcoin durability to derive from exact OTS bundle binding plus strong Bitcoin verification;
4. pre-outcome durability to derive from the exact bound DurabilityVerificationRecord and wall-clock evidence;
5. confirmatory eligibility to derive from the full required claim/check set.

Finding 3 is therefore an implementation-alignment defect, not a change to P2 semantics.

## Existing evidence implementation boundary

The repository currently contains a strict Roughtime rehearsal receipt validator and schema. Those artifacts are explicitly constrained to:

```text
classification = NON_FORECAST_REHEARSAL
prospective_eligible = false
```

They cannot be silently promoted into a production claim-authority path.

`production_receipt_admission_v1.py` currently verifies exact ProviderProfile / QualificationDecision / state-package field binding, but that binding layer does not by itself perform the complete production receipt cryptographic verification or derive the wall-clock claim.

The Genesis time-evidence design already defines the required evidence chain:

```text
exact sealed subject
→ qualifying subject-bound Roughtime receipts
→ exact two-of-three quorum at frozen deadline
→ ExternalTimeEvidenceBundle
→ exact OTS proof binding
→ strong Bitcoin verification
→ DurabilityVerificationRecord where applicable
→ deterministic P2 claim vector
```

P5 must implement the minimum authoritative offline reconstruction path for that chain before P6 may resume.

## Repair rule

The repair must not rely on any of the following as trust authority:

```text
caller-supplied "VERIFIED" strings
caller-supplied booleans such as claims_recomputed=true
opaque Python object identity
schema validity alone
content addressing alone
report signature or seal alone
self-asserted ValidationReport derived_claims
```

The authoritative validator must reconstruct the applicable claim from exact retained inputs under the exact frozen ValidatorContract, or verify exact equality between a persisted report and a deterministic report recomputed by that same contract from those inputs.

## Minimum P5 claim-authority closure

P5 is reopened with the following minimum scope.

1. Define the production-shaped external-time evidence input contract needed for deterministic offline verification. Synthetic fixtures are allowed; live provider traffic is not.
2. Implement an authoritative subject-existence derivation path that verifies exact subject binding, exact admitted provider state, exact production ProviderProfile binding, frozen quorum policy and conservative upper bound before producing `EXTERNAL_EXISTENCE_BOUND_VERIFIED` or `DEADLINE_EXISTENCE_VERIFIED`.
3. Implement an authoritative Bitcoin-durability derivation path that verifies exact ExternalTimeEvidenceBundle binding and exact strong-verification report/proof binding before producing `BITCOIN_DURABILITY_VERIFIED`.
4. Implement exact DurabilityVerificationRecord binding and deadline recomputation for `PRE_OUTCOME_DURABILITY_VERIFIED` where applicable.
5. Make confirmatory eligibility consume only claims produced through the authoritative recomputation path plus exact non-temporal Trust Core checks.
6. Make final Genesis acceptance validation consume the exact recomputed external-existence and Bitcoin-durability claims for the exact signed ManifestAcceptance, never state strings.
7. Add a successor cycle-plan validator that consumes authoritative claim evidence rather than the historical raw bound interface.
8. Add deterministic ValidationReport v2 recomputation/equality validation so persisted derived claims are audit outputs, not trust inputs.
9. Preserve all historical validator behavior under historical contracts without reinterpretation.
10. Add adversarial tests for forged VERIFIED state, forged report claim, wrong ValidatorContract, correct subject with fabricated state, wrong evidence refs, omitted evidence, and report/recomputation mismatch.

## Explicit non-goals

This repair does not authorize or require:

```text
live Roughtime provider requests
production qualification execution
provider-criteria changes
new time protocols
new RFC3161 engineering
Genesis key access
Genesis acceptance
Forecast Ledger creation
prospective forecast issuance
```

It may use synthetic, locally generated and retained fixtures to prove fail-closed deterministic behavior.

## Stage disposition

```text
P5_VERSIONED_IMPLEMENTATION = REOPENED_FOR_CLAIM_AUTHORITY_CLOSURE
P6_STATIC_REVIEW = THIRD_BLOCKING_FINDING_FOUND
P6_FULL_REGRESSION = STOPPED
P6_PASS = NO
P7 = PROHIBITED
GENESIS_READY = NO
```

P6 may restart only after the P5 claim-authority repair is implemented, adversarially reviewed, and the exact new HEAD is frozen for regression.

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
