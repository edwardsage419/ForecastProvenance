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
manifest_anchor_evidence
manifest_acceptance
required_validation_reports
dependency_store
```

The candidate manifest cannot modify, replace, or self select the bootstrap root.

## Authority semantics

FTC_001 freezes the structure and verification boundary. Genesis must freeze the exact authority key and exact acceptance rule bytes before Genesis acceptance.

The initial authority key may be controlled by the project owner under the zero cost operating model. Key rotation after Genesis requires a rule already authorized by the accepted governance state and an append only successor record.

## External retention

Before Genesis acceptance, the exact bootstrap root bytes and their SHA256 must be retained independently of the candidate manifest. Genesis Protocol must externally anchor the bootstrap root or a containing Genesis governance manifest before it is relied on for prospective trust.

## Separation of claims

External anchoring proves content existence by a conservative external time bound.

A valid authority signature or equivalent accepted governance proof establishes project approval under the bootstrap rule.

Neither claim substitutes for the other.

## Genesis blocker

The contract interface can freeze during FTC_001. Genuine Genesis remains prohibited until the exact authority key, acceptance rule, bootstrap bytes, and external proof are instantiated and independently verified.