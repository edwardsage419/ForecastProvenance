# Genesis Manifest and Acceptance Procedure

Version: 0.2 candidate
Status: GEN_001 REVIEW CANDIDATE

## Candidate Genesis manifest

The Genesis TrustedManifest is the first authoritative protocol state of the project.

It must bind exact object IDs and full SHA256 hashes for every consequential normative dependency.

The current base candidate lineage is materialized deterministically from:

```text
genesis/candidate/objects/candidate_object_set_v0_2.json
genesis/candidate/objects/candidate_patch_v0_3.json
```

The effective inventory is produced with:

```text
PYTHONPATH=src python3 scripts/genesis/materialize_candidate.py
```

The inventory itself is non-prospective review evidence. It is not the TrustedManifest.

## Required manifest dependency classes

The final candidate manifest binds exact full-hash references for:

1. Genesis Protocol version and accepted scientific invariants.
2. FPP_JCS_1 canonicalization contract.
3. Exact ValidatorContract and implementation version.
4. BootstrapGovernanceRoot.
5. AcceptancePolicy.
6. External time evidence policy, quorum policy, qualifying ProviderProfiles, OTS Bitcoin verifier profile, and durability semantics.
7. Initial TargetDefinition objects.
8. ResolutionRule and resolution evidence policy objects.
9. ForecastMethod objects and transparent baselines.
10. SourceContract objects.
11. TransformationDefinition and FittedState objects where applicable.
12. IssuanceSchedulePolicy.
13. RetryPolicy.
14. OmissionPolicy.
15. CorrectionPolicy.
16. RetentionPolicy.
17. EvaluationPolicy and scoring rules.
18. HumanReviewPolicy.
19. Project cost doctrine and allowed operational dependencies.
20. Required source-adapter and external-evidence verifier contract versions.

No reference is valid by semantic ID alone.

## Exact validator binding

Before candidate manifest construction, generate the final ValidatorContract from the exact candidate commit and final test report:

```text
PYTHONPATH=src python3 scripts/genesis/build_validator_binding.py \
  --git-commit <40-lowercase-hex-commit> \
  --test-report <final-test-report> \
  --output <validator-contract.json>
```

The builder binds the Trust Core Python source files, schemas, `pyproject.toml`, commit ID, runtime dependency declaration, and final test report SHA256.

Any consequential implementation change after this step invalidates the candidate validator binding and requires a new candidate manifest.

## Genesis sequence

### G0 Freeze normative candidate set

Every referenced object is sealed and hash verified. No production forecast is run.

Materialize the effective candidate inventory and retain its SHA256.

### G1 Freeze bootstrap governance root

The exact owner-generated Ed25519 public key is inserted into BootstrapGovernanceRoot and the root is sealed.

The private key never enters GitHub, CI, repository fixtures, rehearsal bundles, or ChatGPT-managed artifacts.

Retain the exact BootstrapGovernanceRoot bytes and SHA256 independently of the candidate manifest graph so independent validation can receive the root as an external trust input.

Standalone external anchoring of the BootstrapGovernanceRoot is optional audit evidence and is not a Genesis readiness requirement.

### G2 Freeze external provider and verifier profiles

Only successful retained rehearsals and qualification evidence admitted by the frozen provider-qualification criteria can produce production ProviderProfile and QualificationDecision dependencies.

A dated provider website snapshot is insufficient.

Each accepted profile binds the exact provider identity, signer or root key material, policy semantics, time-bound calculation, verifier version, and retained evidence required by the protocol.

### G3 Freeze source-adapter evidence

Retain the three selected retrospective official first-release byte fixtures, raw SHA256 values, retrieval metadata, and successful adapter reports.

These are permanently retrospective and never become forecast history.

### G4 Freeze exact validator contract

Run the complete test suite under the final candidate code, retain the final test report, and build the exact ValidatorContract using the final candidate commit.

### G5 Freeze candidate Genesis TrustedManifest

The manifest references only already frozen normative objects, the exact BootstrapGovernanceRoot reference, qualifying provider and verifier dependencies, exact source and adapter contracts, and exact ValidatorContract.

Any missing required dependency blocks construction.

Standalone external anchoring of the candidate TrustedManifest is optional audit evidence. It cannot substitute for final external evidence over the signed ManifestAcceptance.

### G6 Run Genesis validation suite

Run the frozen Trust Core tests, Genesis-specific adversarial suite, schema verification, dependency closure, candidate inventory reproducibility, provider-profile verification, source-fixture checks, and manifest reproducibility checks.

All required reports are content addressed.

### G7 Resolve findings

Every blocking finding must be resolved or Genesis is aborted.

A correction to a substantive manifest dependency creates a new candidate and invalidates downstream acceptance material that bound the prior candidate.

### G8 Create ManifestAcceptance v2

ManifestAcceptance v2 binds the exact candidate TrustedManifest, exact BootstrapGovernanceRoot, exact AcceptancePolicy, required validation-report references, authority reference, decision, reason codes, blocking findings, and signature reference.

It does not contain a required reference to external evidence that can exist only after the acceptance object is signed.

The owner signs the canonical acceptance payload using the bootstrap Ed25519 key outside repository and remote systems.

### G9 Create final external evidence

Create FPP_TIME_EVIDENCE_V1 wall-clock evidence over the exact signed ManifestAcceptance and retain the exact ExternalTimeEvidenceBundle.

Create OpenTimestamps proof material over that same exact evidence bundle and complete strong Bitcoin verification under the frozen verifier contract.

The final evidence package is supplied separately to independent final validation.

### G10 Independent final Genesis validation

An independent validation run verifies at least:

```text
bootstrap root independently supplied and valid
candidate TrustedManifest valid
provider and verifier dependencies valid
source fixture and adapter reports valid
exact ValidatorContract binding valid
all required validation reports valid
owner signature valid
final evidence subject is the exact signed ManifestAcceptance
EXTERNAL_EXISTENCE_BOUND_VERIFIED == VERIFIED
BITCOIN_DURABILITY_VERIFIED == VERIFIED
blocking findings empty
```

Standalone bootstrap-root or candidate-manifest anchors may be retained for audit. They cannot close a missing final ManifestAcceptance evidence requirement.

Successful final validation does not itself create Genesis.

### G11 Separate explicit Genesis authorization

Only after every required readiness condition closes and independent final validation succeeds may the owner separately and explicitly authorize Genesis.

No design document, test result, signed ManifestAcceptance, external evidence artifact, or successful final validation substitutes for that authorization.

### G12 First issuance cycle

The first IssuanceCyclePlan must be derived from the already accepted IssuanceSchedulePolicy and must have an execution window strictly later than the separate explicit Genesis authorization.

No pre-Genesis output can be imported into that cycle.

## Abort and restart semantics

A changed candidate TrustedManifest after ManifestAcceptance has been signed invalidates that acceptance and requires a new acceptance record plus new final external evidence.

A changed BootstrapGovernanceRoot after downstream objects bind it creates a new bootstrap version and requires regeneration of affected downstream acceptance material.

A changed ProviderProfile, QualificationDecision, or verifier dependency requires revalidation of every downstream object that references it.

A changed source adapter or ValidatorContract after G4 requires a new candidate manifest.

A failed rehearsal or qualification attempt cannot be omitted from the retained review history when it materially informs provider eligibility or an abort condition.

A failed or aborted Genesis attempt never becomes native prospective history.

## Genesis identity

The term `Genesis` is reserved for the first accepted protocol and ledger state created only after successful final validation and separate explicit Genesis authorization.

Design branches, rehearsal commits, candidate objects, test fixtures, and failed acceptance attempts must not use tags or labels that imply Genesis acceptance.