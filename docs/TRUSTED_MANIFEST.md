# Trusted Manifest Contract

Version: 0.2 candidate
Status: FTC_001 REMEDIATION CANDIDATE

## Purpose

The trusted manifest is the explicit trust root for a declared protocol state. It is supplied to the validator from outside the candidate scientific object graph.

## Candidate manifest

A candidate binds:

```text
manifest_id
protocol_id
manifest_sequence
canonicalization_scheme
hash_algorithm
validator_contract
targets
resolution_rules
methods
source_contracts
transformation_definitions
review_rules
anchor_schemes
correction_policy
retry_policy
omission_policy
evaluation_policy
retention_policy
previous_manifest
content_sha256
```

Set like reference arrays are sorted by object ID and full hash.

A candidate contains no authoritative mutable `status` field.

## Acceptance

Manifest authority is established by a separate immutable ManifestAcceptance object.

A valid acceptance binds the exact candidate manifest hash, required external anchor evidence, acceptance rule, authority, decision, and predecessor acceptance.

A validator trust root is the pair:

```text
accepted_manifest_ref
manifest_acceptance_ref
```

Both objects must validate.

External timestamping proves existence. Governance acceptance proves that the project selected that exact candidate as authoritative. Neither substitutes for the other.

## Validator inputs

```text
trusted_manifest
manifest_acceptance
candidate_object
dependency_store
```

Candidate objects cannot select these trust root inputs.

## Successor manifests

A successor binds the prior accepted manifest and prior ManifestAcceptance. It follows the change policy active before the successor was proposed.

A verifier never substitutes the newest manifest for the manifest applicable to a historical object.

## Loss or ambiguity

If the exact accepted manifest, its acceptance object, or required dependencies cannot be produced and hash verified, the stronger trust claim becomes `INELIGIBLE_TRUST_UNKNOWN`.

## Retention

Canonical manifest bytes, acceptance bytes, hashes, external anchor proof, referenced normative compact objects, and successor records are retained by content for the life of the project.
