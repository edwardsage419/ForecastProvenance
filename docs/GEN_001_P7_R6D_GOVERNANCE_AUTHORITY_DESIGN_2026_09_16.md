# GEN_001 P7 R6-D Governance Authority Design — 2026-09-16

Status: PRE-GENESIS IMPLEMENTATION DESIGN CANDIDATE
Classification: NON_FORECAST_REVIEW
Prospective eligible: false
Genesis effect: none
Network authorization: none

## Purpose

R6-A through R6-C now provide regression-confirmed exact lifecycle and source authority for the initial deterministic Genesis-v1 profile. R6-D must add the remaining governance and temporal authority before any positive `CONFIRMATORY_PROSPECTIVE_ELIGIBLE` result is possible.

This record does not authorize Genesis, instantiate a production GenesisAuthorization, access the Genesis private key, qualify a provider, authorize a network request, freeze candidate v0.7, or permit prospective forecasting.

## New correctness finding: ManifestAcceptance signature authenticity is not yet enforced

The current candidate acceptance policy requires `BOOTSTRAP_ED25519_SIGNATURE`, and the single-final-anchor design requires the owner signature to verify against the independently supplied BootstrapGovernanceRoot.

The current implementation is incomplete at this boundary:

- ManifestAcceptance v2 exact-contract validation requires a `signature_ref`;
- manifest/bootstrap/rule/report bindings, `decision = ACCEPT`, and empty blockers are checked;
- final wall-clock existence and Bitcoin durability over the exact ManifestAcceptance are authoritatively recomputed;
- but the current final-acceptance path does not cryptographically verify the referenced owner Ed25519 signature.

Therefore a syntactically valid `signature_ref` is not yet proof of owner acceptance.

This is an R6-D correctness/security blocker. Positive confirmatory authority remains prohibited until the owner-signature path is implemented and regression-tested.

## Second correctness gap: no machine-verifiable GenesisAuthorization object exists

The protocol requires a separate explicit Genesis authorization after independent final Genesis validation. Repository procedure and policy text describe that gate, but the current Trust Core does not define a machine object or validator that can independently prove which exact authorization applies to a forecast cycle.

A caller boolean, chat message, repository branch state, GitHub timestamp, or mutable `status = AUTHORIZED` field is not authority.

R6-D therefore needs an exact owner-authenticated authorization record before the first prospective cycle can be considered confirmatory-eligible.

## D1 — owner-signature authority

### BootstrapGovernanceRoot exact machine profile

The independently supplied bootstrap root is the external governance trust input. The initial Genesis-v1 machine profile should validate an exact sealed object containing at least:

```text
schema_version = 1.0
object_type = BootstrapGovernanceRoot
project_id = forecast-provenance-project
authority_id
authority_key_type = ED25519
authority_public_key_base64
acceptance_rule_ref
canonicalization_scheme = FPP_JCS_1
hash_algorithm = SHA-256
bootstrap_version = 1
object_id
payload_sha256
content_sha256
```

The validator decodes a canonical 32-byte Ed25519 public key and derives its SHA256. The private key is never a validator input, repository object, test fixture, connected-tool input, or ChatGPT input.

### GenesisGovernanceSignatureVerifierContract

R6-D should add a supporting verifier contract, bound by the final TrustedManifest, for Genesis governance signatures. It is not a new scientific policy object.

The contract should bind at least:

```text
schema_version
object_type = GenesisGovernanceSignatureVerifierContract
validator_contract_ref
signature_algorithm = ED25519
authority_id
authority_public_key_sha256
ed25519_verifier_build_profile_sha256
ed25519_verifier_binary_sha256
allowed_signature_projections = [
  FPP_MANIFEST_ACCEPTANCE_V2,
  FPP_GENESIS_AUTHORIZATION_V1
]
object_id
payload_sha256
content_sha256
```

The production verifier must construct the already-qualified pinned Ed25519 verifier from the exact contract/build profile/binary identity. The runtime caller must not be able to substitute a verification callback, authority key, binary hash, or signature projection.

### Non-circular governance signature evidence

ManifestAcceptance v2 contains `signature_ref`; signing the complete sealed acceptance object would therefore create a circular dependency between the acceptance hash and the signature object.

R6-D must use an explicit non-circular signing projection.

A `GenesisGovernanceSignature` evidence object should bind:

```text
schema_version
object_type = GenesisGovernanceSignature
signature_projection
signed_payload
signed_payload_sha256
signature_algorithm = ED25519
authority_signature_base64
object_id
payload_sha256
content_sha256
```

For `FPP_MANIFEST_ACCEPTANCE_V2`, the validator deterministically reconstructs `signed_payload` from the exact ManifestAcceptance substantive acceptance fields, excluding `signature_ref` and the acceptance object's seal hashes. The signature evidence must match that reconstructed projection exactly before the Ed25519 signature is verified.

This preserves exact acceptance binding without circular content addressing.

The same mechanism may later be reused for `FPP_GENESIS_AUTHORIZATION_V1`.

## D2 — explicit Genesis authorization

After D1 passes regression, R6-D should define a minimal exact `GenesisAuthorization` object. The object is designed now but must not be instantiated as a production authorization during pre-Genesis implementation or testing.

Minimum substantive fields:

```text
trusted_manifest_ref
manifest_acceptance_ref
bootstrap_governance_root_ref
authorization_scope = GENESIS_V1_FIRST_EXECUTION
decision = AUTHORIZE_GENESIS
reason_codes = []
signature_ref
```

The owner signature uses the non-circular `FPP_GENESIS_AUTHORIZATION_V1` projection and the same independently supplied bootstrap authority.

A synthetic fixture may test the validator. A real object may exist only after all Genesis readiness conditions close and the owner separately gives explicit Genesis authorization.

## D2 plan binding and chronology without a second mandatory governance anchor

The single-final-anchor Genesis design remains intact.

The successor initial Genesis-v1 exact IssuanceCyclePlan profile should bind:

```text
genesis_authorization_ref = exact GenesisAuthorization ref
```

Every confirmatory Genesis-v1 plan must validate that exact reference against the owner-authenticated authorization supplied to R6-D.

The cycle plan is already a direct wall-clock subject and must satisfy:

```text
DEADLINE_EXISTENCE_VERIFIED(IssuanceCyclePlan) = VERIFIED
```

Because the externally evidenced plan commits the exact content hash of the GenesisAuthorization it references, the plan precommitment also commits the exact authorization identity under the project's hash-security assumptions. GenesisAuthorization therefore does not require a second mandatory standalone external timestamp solely to establish that it preceded the plan commitment.

R6-D must not derive chronology from an unsigned `authorized_at` field. The protocol procedure still requires the owner to create the authorization only after independent final validation.

## Final acceptance condition for authorization

R6-D should not persist or trust a caller assertion that independent final validation passed.

When validating GenesisAuthorization authority, the validator should re-execute the exact final-acceptance authority over the same:

```text
TrustedManifest
ManifestAcceptance
BootstrapGovernanceRoot
final wall-clock evidence
final Bitcoin durability evidence
```

and require the acceptance checks and required final claims to pass. The authorization must bind that exact acceptance and manifest.

This makes the accepted state reproducible from retained evidence rather than depending on a mutable `final_validation_passed = true` flag.

## D3 — final confirmatory orchestration

Only after D1 and D2 close may a new full Genesis-v1 confirmatory authority path combine:

```text
owner-authenticated accepted TrustedManifest basis
+ owner-authenticated GenesisAuthorization
+ R6-C lifecycle authority closure
+ IssuanceCyclePlan deadline existence
+ IssuanceCycleManifest deadline existence
+ required Bitcoin durability
+ required pre-outcome durability
```

The initial forecast's exact IssuedForecast ref must already be proven by R6-C to be the issuance-eligible first success and an exact member of the complete mandatory slot accounting.

The final path must derive the required claim set itself. Caller-supplied claims, caller-supplied hard-invalidation reason codes, persisted `VERIFIED` strings, and mutable prospective flags remain prohibited as authority.

Only this full path may produce:

```text
CONFIRMATORY_PROSPECTIVE_ELIGIBLE = VERIFIED
```

The existing generic confirmatory helper should remain fail-closed until the new full path passes focused regression, adversarial regression, and fresh exact-head P6.

## Candidate-version consequence

This design does not yet require candidate v0.8 solely for machine enforcement:

- AcceptancePolicy v2 already requires bootstrap Ed25519 authority and first execution strictly after final validation plus explicit Genesis authorization.
- `GenesisGovernanceSignatureVerifierContract` is a supporting verifier contract that the final TrustedManifest can bind under its existing verifier-dependency role.
- `GenesisAuthorization` and `genesis_authorization_ref` are dynamic operational authority objects/fields enforcing the already frozen acceptance semantics.

If implementation requires changing a normative candidate policy rather than merely enforcing existing v0.7/v0.6 semantics, a successor candidate patch is mandatory. Historical candidate bytes must not be edited.

## Implementation staging

R6-D is split into smaller fail-closed steps:

```text
R6-D1 = bootstrap/governance-signature exact contracts + ManifestAcceptance signature authenticity
R6-D2 = GenesisAuthorization exact contract/signature + cycle-plan binding
R6-D3 = full lifecycle + temporal/durability confirmatory orchestration
```

D1 must pass focused and full regression before D2 is implemented. D2 must pass before D3 enables any positive confirmatory result.

## Safety state

```text
R6-A = REGRESSION_CONFIRMED
R6-B = REGRESSION_CONFIRMED
R6-C = REGRESSION_CONFIRMED
R6-D1 = OPEN
R6-D2 = NOT IMPLEMENTED
R6-D3 = NOT IMPLEMENTED
AUTHORITATIVE_CONFIRMATORY_VERIFIED = PROHIBITED
candidate v0.7 = CREATED / NOT FROZEN
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production qualified provider count = 0
PRODUCTION_QUALIFIED = NO
network_authorized = false
```
