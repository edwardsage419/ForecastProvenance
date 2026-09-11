# Trusted Manifest Contract

Version: 0.1 candidate
Status: FTC_001 REVIEW CANDIDATE

## 1. Purpose

The trusted manifest is the explicit trust root for a declared protocol state.

A validator receives a trusted manifest from outside the scientific object graph. The object graph cannot select, modify, or regenerate the trust root it is being evaluated against.

## 2. Manifest object

Object type: TrustedManifest

Required fields:

```text
object_type
schema_version
manifest_id
protocol_id
manifest_sequence
effective_from
canonicalization_scheme
hash_algorithm
validator_contract
targets
resolution_rules
methods
source_contracts
anchor_schemes
correction_policy
retry_policy
evaluation_policy
previous_manifest
status
content_sha256
```

## 3. Field semantics

### manifest_id

Stable identity of this exact accepted manifest version.

### protocol_id

Genesis or later protocol state under which the manifest is authoritative.

### manifest_sequence

Monotonically increasing integer within one protocol lineage.

### effective_from

Claimed administrative activation time. It is metadata until the manifest has the external proof required by the active protocol.

### canonicalization_scheme

Must identify an accepted scheme such as `FPP_JCS_1`.

### hash_algorithm

Version 1 requires `SHA-256`.

### validator_contract

Binds the normative validator specification identity and content hash. Later executable validator packages can be additionally bound once implementation begins.

### targets

Sorted list of accepted TargetDefinition references.

### resolution_rules

Sorted list of accepted ResolutionRule references.

### methods

Sorted list of accepted ForecastMethod references.

### source_contracts

Sorted list of accepted evidence source contract references.

### anchor_schemes

Sorted list of accepted time anchor scheme references.

### correction_policy

Content bound reference to the active correction policy.

### retry_policy

Content bound reference to the active retry policy.

### evaluation_policy

Content bound reference when confirmatory evaluation is in scope.

### previous_manifest

Full reference to the prior accepted manifest. Genesis uses explicit string `"NONE"`.

### status

Allowed design values are `CANDIDATE`, `ACCEPTED`, and `RETIRED`.

Only an externally accepted manifest can serve as a validator trust root.

## 4. Manifest acceptance

Before Genesis:

1. A candidate is constructed deterministically.
2. All referenced normative objects are available and hash verified.
3. Adversarial review passes.
4. Candidate hash is externally time anchored under the accepted Genesis procedure.
5. External proof is independently verified.
6. A Genesis acceptance decision records the exact full manifest hash.
7. The manifest status becomes accepted through an append only acceptance record.

After Genesis, a successor manifest must bind the previous accepted manifest and follow the active change policy.

## 5. Validator input rule

A validation call has three logically separate inputs:

```text
trusted_manifest
candidate_object
dependency_store
```

The validator may fetch dependency objects from the dependency store, but acceptance is determined against identities and hashes allowed by `trusted_manifest`.

A candidate object containing a field named `trusted_manifest` or similar does not control the trust root.

## 6. Circular trust prohibition

The following pattern is invalid:

1. Modify a target definition.
2. Recompute its hash.
3. Recompute every downstream forecast hash.
4. Build a new manifest containing the modified hashes.
5. Ask the validator to trust that manifest because the candidate object points to it.

A manifest becomes authoritative only through the protocol's external acceptance path.

## 7. Manifest loss and ambiguity

If the exact trusted manifest required for a trust claim cannot be produced and hash verified, the result is `INELIGIBLE_TRUST_UNKNOWN`.

A verifier must not substitute the newest manifest.

## 8. Minimal long term retention

Retain forever:

1. Canonical manifest bytes.
2. Full SHA256.
3. Every referenced normative object or durable reproducible reference.
4. External anchor proof material.
5. Acceptance decision.
6. Successor and retirement records.

The format is deliberately static file friendly.
