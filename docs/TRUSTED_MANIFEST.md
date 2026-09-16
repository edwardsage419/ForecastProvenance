# Trusted Manifest Contract

Version: 0.6 candidate
Status: GEN_001 P7 R6-D1 GOVERNANCE-AUTHORITY IMPLEMENTATION PENDING REGRESSION

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
strong_bitcoin_verifier_contract_ref
genesis_governance_signature_verifier_contract_ref
other anchor/verifier contracts actually used by Genesis v1
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

### Qualification-verifier authority binding

`qualification_verifier_contract_ref` points to the exact sealed `RoughtimeQualificationVerifierContract` used by the successor claim-authority path. That supporting contract binds:

```text
frozen qualification criteria ID/hash
main ValidatorContract ref
QualificationDecision signature projection
signature algorithm = ED25519
accepted qualification authority ID
accepted qualification authority public-key SHA256
qualified Ed25519 verifier build-profile SHA256
qualified Ed25519 verifier binary SHA256
```

The runtime caller cannot supply a replacement signature-verification callback or replacement authority fields inside provider evidence inputs. The high-level validator validates the contract and build profile and constructs the hash-pinned Ed25519 verifier itself.

The authority public-key bytes are supplied independently from the accepted BootstrapGovernanceRoot/governance context and must hash to the value frozen in this manifest-bound contract. The private key is never a validator input and never enters project artifacts.

This preserves the bootstrap trust boundary: the candidate manifest binds the verifier/authority identity it expects, while the independent bootstrap root supplies the authority bytes against which that expectation is checked. The candidate cannot self-select a different accepted bootstrap root.

### Bitcoin verifier binding

`strong_bitcoin_verifier_contract_ref` binds the exact strong Bitcoin verification contract consumed by the authoritative durability path. The local executable must match the hash frozen by that contract. Persisted Bitcoin verification reports are audit outputs and cannot substitute for re-execution under the frozen contract.

### Genesis governance-signature verifier binding

`genesis_governance_signature_verifier_contract_ref` binds the exact sealed `GenesisGovernanceSignatureVerifierContract` admitted for Genesis governance signatures. The contract binds:

```text
main ValidatorContract ref
signature algorithm = ED25519
bootstrap authority ID
bootstrap authority public-key SHA256
qualified Ed25519 verifier build-profile SHA256
qualified Ed25519 verifier binary SHA256
allowed signature projections = [
  FPP_GENESIS_AUTHORIZATION_V1,
  FPP_MANIFEST_ACCEPTANCE_V2
]
```

The independent BootstrapGovernanceRoot supplies the exact public-key bytes. The validator requires those bytes to match the contract-bound authority identity and public-key SHA256, then constructs the already-qualified hash-pinned Ed25519 verifier. Caller-supplied signature callbacks, replacement public keys, replacement verifier hashes, or replacement signing projections are not authority.

The BootstrapGovernanceRoot remains external to the candidate manifest graph. The manifest binds the verifier identity and AcceptancePolicy it expects; ManifestAcceptance binds the independently supplied bootstrap root and the exact manifest. This avoids allowing the candidate manifest to select its own trust root.

## Genesis acceptance

Genesis authority comes from an out-of-graph `BootstrapGovernanceRoot` supplied independently to validation.

ManifestAcceptance v2 binds the exact candidate manifest, exact bootstrap root, exact AcceptancePolicy v2, required validation reports, authority reference, decision, reason codes, blocking findings, and signature reference.

The owner signature is represented by an exact `GenesisGovernanceSignature` using the non-circular `FPP_MANIFEST_ACCEPTANCE_V2` projection. The signing payload deterministically contains the substantive ManifestAcceptance fields but excludes `signature_ref` and the acceptance object's seal hashes, preventing a circular signature/hash dependency. Final acceptance authority reconstructs that projection, requires exact payload equality, and verifies Ed25519 against the independently supplied bootstrap public key under the manifest-bound governance verifier contract.

The authoritative final-acceptance path also requires:

```text
ManifestAcceptance.decision == ACCEPT
ManifestAcceptance.blocking_finding_refs == []
ManifestAcceptance.acceptance_rule_ref == TrustedManifest.acceptance_rule_ref
ManifestAcceptance.acceptance_rule_ref == BootstrapGovernanceRoot.acceptance_rule_ref
```

The signed ManifestAcceptance does not contain a required reference to its later final external evidence package. That would be circular.

After signing, final external evidence is created over the exact signed ManifestAcceptance. Independent final validation receives that evidence separately and requires authoritative recomputation of:

```text
final_evidence_subject_ref == signed_manifest_acceptance_ref
EXTERNAL_EXISTENCE_BOUND_VERIFIED == VERIFIED
BITCOIN_DURABILITY_VERIFIED == VERIFIED
```

Caller-supplied claim/state strings and persisted reports do not establish these conditions. Persisted final ValidationReport equality includes the retained governance signature/root/verifier dependencies but still derives temporal and durability claims from raw retained evidence.

Standalone bootstrap-root or candidate-manifest anchors may exist as optional audit evidence but cannot substitute for the final acceptance evidence.

### Required validation-report closure remains a separate final-validation gate

AcceptancePolicy v2 names five required validation-report roles, while the current ValidationReport v2 contract does not encode a report-role field. Therefore an acceptance's own `required_validation_report_refs` list cannot be treated as self-proving that those five semantic roles are complete.

R6-D1 does not silently manufacture that mapping. Independent final Genesis validation must use a deterministic, externally reconstructable role-to-report basis before GR041 can close. Until that basis is implemented and regression-tested, successful owner-signature verification and final time/durability verification are necessary but not sufficient for Genesis readiness.

## Genesis authorization boundary

Successful final validation does not itself start Genesis.

A separate explicit Genesis authorization is required after all readiness conditions close. First prospective execution must occur strictly after that authorization.

R6-D1 does not create or validate a production GenesisAuthorization. `FPP_GENESIS_AUTHORIZATION_V1` is reserved for the subsequent R6-D2 implementation.

## Historical manifest selection

A verifier always uses the exact historical manifest and policy versions applicable to the object or cycle being verified. Newer policies or manifests never reinterpret older history.

## Retention

Canonical TrustedManifest bytes, ManifestAcceptance bytes, BootstrapGovernanceRoot bytes, public keys, governance signature evidence, final external evidence, referenced normative objects, provider admission objects, verifier contracts/build profiles required for independent recomputation, and successor lineage records are retained by content for the life of the project.
