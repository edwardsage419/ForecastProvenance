# GEN_001 P6 Finding 3: Claim Authority Boundary

Date: 2026-09-14
Status: IMPLEMENTATION REPAIRED PENDING REGRESSION
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

The remaining defect was that structurally valid claim records or caller-supplied state values could still be treated as if they were the deterministic output of the exact ValidatorContract.

Three initial manifestations were identified.

### 1. Final Genesis acceptance trusted caller-supplied states

`validate_final_genesis_acceptance` accepts:

```text
external_existence_state
bitcoin_durability_state
```

as plain strings and checks only whether each equals `VERIFIED`.

Therefore the function can return valid without independently proving that the exact signed ManifestAcceptance produced those claims from retained external time evidence and Bitcoin durability evidence.

This function is classified as a low-level structural helper only. It is not an authoritative Genesis-final-validation entry point.

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

The repository contains a strict Roughtime rehearsal receipt validator and schema. Those historical artifacts are explicitly constrained to:

```text
classification = NON_FORECAST_REHEARSAL
prospective_eligible = false
```

They cannot be silently promoted into a production claim-authority path.

`production_receipt_admission_v1.py` verifies exact ProviderProfile / QualificationDecision / state-package field binding, but that binding layer does not by itself perform the complete production receipt cryptographic verification or derive the wall-clock claim.

The Genesis time-evidence design defines the required evidence chain:

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
caller-selected verifier authority
caller-selected signature-verification callback
```

The authoritative validator reconstructs the applicable claim from exact retained inputs under the exact frozen ValidatorContract, or verifies exact equality between a persisted report and a deterministic report recomputed by that same contract from those inputs.

## Implemented P5 claim-authority closure

The successor repair now provides the following layers.

### Evidence to claim recomputation

`src/forecast_trust_core/claim_authority_v1.py` provides the authoritative evidence-recomputation primitives.

Wall-clock claims replay exact retained request/response bytes through the strict Roughtime verifier, recompute historical provider admission, enforce exact subject binding and frozen deadline/quorum semantics, and derive the conservative upper bound. The authoritative production wrappers require `LIVE_OPERATIONAL` evidence; synthetic evidence remains usable only for tests and cannot satisfy production readiness.

Bitcoin durability executes a hash-pinned local strong-verification contract over the exact ExternalTimeEvidenceBundle and OTS proof bytes. Persisted strong-verification reports are equality-audit outputs only. Bitcoin block-header time remains durability evidence only and is never used as a precise civil-time upper bound.

DurabilityVerificationRecord and confirmatory-eligibility paths reconstruct their prerequisite claims from exact evidence rather than caller-provided claim mappings.

### ValidationReport authority

Successor report validation internally recomputes the claims and deterministic report from raw evidence and then requires exact equality with the persisted ValidationReport v2. A persisted report cannot authorize itself.

### TrustedManifest trust root

`src/forecast_trust_core/claim_authority_trust_root_v1.py` makes the exact sealed TrustedManifest the source of expected refs for:

```text
ValidatorContract
deadline receipt quorum policy
three ProviderProfiles
three QualificationDecisions
qualification verifier contract
strong Bitcoin verifier contract
```

The caller cannot replace a verifier and simultaneously replace its expected ref.

### Qualification-signature authority hardening

A final static adversarial pass found a fourth manifestation inside the same Finding 3 root cause: provider-state recomputation still accepted a caller-provided `signature_verifier` callback plus authority fields. A callback that always returned true could otherwise bypass real QualificationDecision signature verification.

This path is now repaired.

The manifest-bound `RoughtimeQualificationVerifierContract` freezes:

```text
frozen criteria ID/hash
main ValidatorContract ref
QualificationDecision signature projection
signature algorithm = ED25519
qualification authority ID
qualification authority public-key SHA256
Ed25519 verifier build-profile SHA256
Ed25519 verifier binary SHA256
```

The high-level trust-root adapter validates the exact contract, validates the exact Ed25519 build profile, verifies the executable hash, and constructs `PinnedEd25519Verifier` itself. Provider runtime inputs are prohibited from supplying `expected_authority_id`, `expected_authority_public_key`, or `signature_verifier`.

The external authority public-key bytes remain an independent validation input. For Genesis they must come from the independently supplied accepted BootstrapGovernanceRoot/governance context. They are checked against the hash frozen in the manifest-bound qualification verifier contract. The private key is never an input to this path.

The provider runtime input key set and state-package provider identity set must exactly equal the three manifest-admitted provider identities. Extra, missing, duplicate, or substituted provider authority inputs fail closed.

Schema:

```text
schemas/roughtime_qualification_verifier_contract_v1.schema.json
```

Focused adversarial tests:

```text
tests/test_claim_authority_v1.py
tests/test_claim_authority_trust_root_v1.py
tests/test_claim_authority_qualification_root_v1.py
```

The tests are committed but have not yet been executed on the final repaired exact HEAD. Their presence is not a PASS result.

## Historical compatibility

Historical low-level validators remain available under their historical contracts. The successor authority entry points are the only paths allowed to establish P2 claims or Genesis readiness under the compressed candidate. No historical candidate bytes were rewritten by this repair.

## Explicit non-goals

This repair does not authorize or require:

```text
live Roughtime provider requests
production qualification execution
provider-criteria changes
new time protocols
new RFC3161 engineering
Genesis private-key access
Genesis acceptance
Forecast Ledger creation
prospective forecast issuance
```

It may use synthetic, locally generated and retained fixtures to prove fail-closed deterministic behavior.

## Stage disposition

```text
P5_CLAIM_AUTHORITY_IMPLEMENTATION = REPAIRED_PENDING_REGRESSION
P6_FINDING_3 = REPAIRED_PENDING_REGRESSION
P6_FULL_REGRESSION = NOT_YET_RESTARTED
P6_PASS = NO
P7 = PROHIBITED
GENESIS_READY = NO
```

Finding 3 may be considered closed only after a fresh P6 run on the exact final repaired HEAD executes the required compile/import checks, schema meta-validation, historical and successor regressions, focused claim-authority tests, full pytest and synthetic adversarial suite without a correctness/security failure.

Any consequential code/schema change after the P6 input HEAD is frozen invalidates earlier P6 execution evidence and requires a fresh run.

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
