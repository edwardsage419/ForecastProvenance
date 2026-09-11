# Trusted Manifest Contract

Version: 0.4 candidate
Status: FTC_001 FINAL FREEZE CANDIDATE

## Purpose

The trusted manifest is the explicit protocol trust root for a declared project state. It is supplied to the validator from outside the candidate scientific object graph.

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
issuance_schedule_policy
public_randomness_policies
correction_policy
retry_policy
omission_policy
evaluation_policy
retention_policy
acceptance_rule
previous_manifest
content_sha256
```

Set like reference arrays are sorted by object ID and full hash. Consequential policies are first class content bound objects.

A candidate contains no authoritative mutable acceptance status.

## Genesis acceptance

Genesis authority is not derived from the candidate manifest.

The validator receives an out of graph `BootstrapGovernanceRoot` that binds project identity, authority identity and public key, acceptance rule identity, canonicalization scheme, hash algorithm, and bootstrap version.

A Genesis ManifestAcceptance must bind the exact candidate manifest hash, required external anchor evidence, bootstrap root, exact acceptance rule, authority proof, required validation reports, and decision.

FTC_001 freezes this interface. Genesis must instantiate the exact bootstrap key and exact rule bytes before any prospective operation.

## Successor acceptance

After Genesis, a successor manifest binds the prior accepted manifest and prior acceptance object and follows the governance change rule already authorized by the accepted predecessor state.

If two successor acceptances compete for the same predecessor and the predecessor AcceptanceRule does not deterministically resolve that fork, historical trust resolution fails closed until an authorized conflict process resolves it.

## Validator trust inputs

Genesis validation logically receives:

```text
bootstrap_governance_root
trusted_manifest
manifest_acceptance
candidate_object
dependency_store
```

Post Genesis validation uses the accepted governance lineage rooted in Genesis.

Candidate objects cannot select or regenerate these trust roots.

## Schedule and output selection

Every confirmatory issuance cycle must validate against the exact IssuanceSchedulePolicy bound by its historical trusted manifest.

The schedule policy determines the required target and method slots before cycle outputs exist.

Any PublicRandomnessPolicy used by a method is likewise content bound by the trusted manifest. An operator cannot substitute a later randomness source or event after inspecting candidate outputs.

## External anchoring and governance

External time evidence establishes content existence under the AnchorScheme's conservative time semantics.

ManifestAcceptance establishes project governance approval.

Both are required where the active protocol requires both claims.

## Historical manifest selection

A verifier never substitutes the newest manifest or policy version for the exact manifest applicable to a historical object or issuance cycle.

If the required manifest, acceptance object, governance lineage, policy object, or required dependency cannot be produced and verified, the stronger trust claim fails closed.

## Retention

Canonical manifest bytes, acceptance bytes, bootstrap governance root bytes, hashes, external anchor evidence, referenced compact normative objects, and successor lineage records are retained by content for the life of the project.