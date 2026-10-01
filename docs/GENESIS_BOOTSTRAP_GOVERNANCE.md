# Genesis Bootstrap Governance Boundary

Version: 0.3 candidate
Status: FTC_001 FREEZE CANDIDATE

## Purpose

The first trusted manifest cannot derive its authority from itself. Genesis therefore uses a bootstrap governance root supplied to the validator from outside the candidate manifest graph.

## BootstrapGovernanceRoot schema

Required substantive fields:

```text
bootstrap_root_id
project_id
authority_id
authority_key_type
authority_public_key
acceptance_rule_ref_or_embedded_hash
canonicalization_scheme
hash_algorithm
bootstrap_version
content_sha256
```

The root is immutable once used for Genesis acceptance.

## Validation input

Genesis manifest acceptance receives these independent inputs:

```text
bootstrap_governance_root
candidate_manifest
manifest_acceptance
required_validation_reports
final_external_evidence
dependency_store
```

The candidate manifest cannot modify, replace, or self select the bootstrap root.

The exact BootstrapGovernanceRoot is supplied independently to validation and remains outside the candidate manifest authority graph even when the TrustedManifest binds its exact reference.

## Authority semantics

FTC_001 freezes the structure and verification boundary. Genesis must freeze the exact authority key and exact acceptance rule bytes before Genesis acceptance.

The initial authority key may be controlled by the project owner under the zero cost operating model. Key rotation after Genesis requires a rule already authorized by the accepted governance state and an append only successor record.

## External retention

Before Genesis acceptance, the exact bootstrap root bytes and their SHA256 must be retained independently of the candidate manifest for the life of the project.

A standalone external anchor over the BootstrapGovernanceRoot or a containing governance envelope may be retained as optional audit evidence. It is not a mandatory Genesis readiness gate and cannot substitute for final external evidence over the exact signed ManifestAcceptance.

## Separation of claims

Final external anchoring over the exact signed ManifestAcceptance establishes the externally verified existence and durability claims required by the Genesis acceptance path under the frozen time evidence policy.

A valid authority signature or equivalent accepted governance proof establishes project approval under the bootstrap rule.

The independently supplied BootstrapGovernanceRoot establishes which authority and acceptance rule are trusted. The final external evidence establishes the required existence and durability facts for the signed acceptance. Each claim is validated under its own frozen contract.

## Genesis blocker

The contract interface can freeze during FTC_001. Genuine Genesis remains prohibited until the exact authority key, acceptance rule, bootstrap bytes, signed ManifestAcceptance, required final external evidence, and independent final validation are instantiated and verified, followed by separate explicit Genesis authorization.