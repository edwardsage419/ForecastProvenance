# Trusted Manifest Contract

Version: 0.5 candidate
Status: GEN_001 ARCHITECTURE COMPRESSION P5

## Purpose

TrustedManifest is the explicit content-addressed protocol trust root for a declared historical project state. Candidate objects cannot select or regenerate their own trust roots.

## Genesis v1 candidate bindings

The compressed Genesis v1 TrustedManifest binds exact full references for the instantiated profile, including:

```text
validator_contract_ref
target_refs
resolution_rule_refs
method_refs
source_contract_refs
issuance_schedule_policy_ref
retry_policy_ref
omission_policy_ref
correction_policy_ref
evaluation_policy_ref
retention_policy_ref
acceptance_rule_ref
deadline_receipt_quorum_policy_ref
provider_profile_refs
qualification_decision_refs
qualification_verifier_contract_ref
anchor/verifier contracts actually used by Genesis v1
```

Set-like arrays are deterministically sorted by object ID and full content hash.

Genesis v1 does not require placeholder manifest dependencies for dormant interfaces such as PublicRandomnessPolicy, FittedState, scientific Human Review, closed-model observability/retrieval accounting, stochastic execution, externally audited attempts, or multi-method comparison.

## Provider qualification firewall

Genesis v1 binds exactly three production ProviderProfiles and exactly three matching signed QualificationDecisions.

The signed QualificationDecision transitively binds the exact frozen qualification criteria, ProviderProfile, initial qualification evidence-manifest SHA256, verifier identity, independent review, decision-bound metadata review, authority, and decision result.

Qualification workflow internals are supporting evidence and are not duplicated into TrustedManifest.

Dynamic historical provider state is reconstructed separately for each consequential deadline with:

```text
as_of_utc = frozen_deadline_utc
```

using the exact `qualification_verifier_contract_ref` and a content-closed qualification-state package. All three admitted providers must be `PRODUCTION_QUALIFIED` at that historical as-of before the deadline event may use the frozen production-ready three-provider pool.

## Genesis acceptance

Genesis authority comes from an out-of-graph `BootstrapGovernanceRoot` supplied independently to validation.

ManifestAcceptance v2 binds the exact candidate manifest, exact bootstrap root, exact AcceptancePolicy v2, required validation reports, authority reference, decision, reason codes, blocking findings, and signature reference.

The signed ManifestAcceptance does not contain a required reference to its later final external evidence package. That would be circular.

After signing, final external evidence is created over the exact signed ManifestAcceptance. Independent final validation receives that evidence separately and requires:

```text
final_evidence_subject_ref == signed_manifest_acceptance_ref
EXTERNAL_EXISTENCE_BOUND_VERIFIED == VERIFIED
BITCOIN_DURABILITY_VERIFIED == VERIFIED
```

Standalone bootstrap-root or candidate-manifest anchors may exist as optional audit evidence but cannot substitute for the final acceptance evidence.

## Genesis authorization boundary

Successful final validation does not itself start Genesis.

A separate explicit Genesis authorization is required after all readiness conditions close. First prospective execution must occur strictly after that authorization.

## Historical manifest selection

A verifier always uses the exact historical manifest and policy versions applicable to the object or cycle being verified. Newer policies or manifests never reinterpret older history.

## Retention

Canonical TrustedManifest bytes, ManifestAcceptance bytes, BootstrapGovernanceRoot bytes, public keys, signatures, final external evidence, referenced normative objects, provider admission objects, and successor lineage records are retained by content for the life of the project.
