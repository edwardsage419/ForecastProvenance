# Genesis Bootstrap Governance Instance

Version: 0.1 candidate
Status: GEN_001 REVIEW CANDIDATE

## Purpose

The first accepted trusted manifest requires an authority that exists outside the manifest it will accept.

Genesis therefore instantiates BootstrapGovernanceRoot as an external immutable object.

## Authority model

Version 1 uses a single owner controlled Ed25519 signing key.

This choice minimizes cost and operational dependencies while keeping the acceptance act cryptographically separate from GitHub account state, repository history, or the candidate Genesis manifest.

The bootstrap private key must never be committed to the repository, uploaded into CI, stored in project fixtures, or generated as part of automated repository tests.

The private key should be generated and retained offline by the project owner before Genesis acceptance.

## Bootstrap root candidate

The final Genesis instance will contain:

```text
bootstrap_root_id = bootstrap:fpp-genesis:v1
project_id = forecast-provenance-project
authority_id = authority:genesis-owner:v1
authority_key_type = ED25519
authority_public_key = PENDING_OWNER_OFFLINE_KEY_GENERATION
acceptance_rule_ref = policy:genesis-acceptance:v1
canonicalization_scheme = FPP_JCS_1
hash_algorithm = SHA-256
bootstrap_version = 1
content_sha256 = derived
```

The unresolved public key is a Genesis blocker. GEN_001 cannot reach final acceptance while this field remains pending.

## Key generation boundary

The recommended procedure is:

1. Generate the Ed25519 key pair on an owner controlled offline or local machine.
2. Retain the private key outside GitHub and outside ChatGPT managed artifacts.
3. Export only the raw or standard encoded public key.
4. Insert the public key into the BootstrapGovernanceRoot candidate.
5. Seal the exact bootstrap root bytes.
6. Obtain deadline receipt quorum and an OTS Bitcoin durability proof for a GenesisGovernanceEnvelope containing the root and acceptance policy hashes.
7. Independently verify the evidence before relying on the root.

## Genesis acceptance rule

Policy ID: `policy:genesis-acceptance:v1`

A valid ManifestAcceptance must bind:

```text
candidate_manifest_ref
bootstrap_root_ref
manifest_time_evidence_ref
required_validation_report_refs
required_rehearsal_report_refs
blocking_findings = []
decision = ACCEPT
authority_signature
```

The authority signature covers the canonical acceptance payload and cannot be copied to a different manifest hash.

Acceptance is invalid when any required validation or rehearsal report is missing, any blocking finding remains open, or the candidate manifest hash differs from the signed payload.

## Acceptance record time evidence

ManifestAcceptance itself must receive FPP_TIME_EVIDENCE_V1 evidence before the first production issuance cycle can open.

This prevents a later acceptance record from being backdated into an already running prospective history.

The first allowed execution window must begin after final verification of the exact ManifestAcceptance evidence bundle under the frozen Genesis rule.

## Key rotation

Bootstrap authority cannot be silently rotated.

After Genesis, any successor governance key must be authorized by the previously accepted governance policy and represented as an append only successor governance object.

Loss of the bootstrap private key before Genesis aborts Genesis and requires a new bootstrap root version.

Loss of the key after Genesis follows the already accepted recovery policy. No recovery policy can be invented retrospectively.

## Repository role

The private ForecastProvenance repository can retain public governance objects and signatures.

Repository commit time, branch protection, GitHub account ownership, or GitHub authentication do not replace the Ed25519 authority signature.