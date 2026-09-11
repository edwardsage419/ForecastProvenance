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

### G2 Externally evidence bootstrap governance

Create a GenesisGovernanceEnvelope containing the bootstrap root and acceptance policy references.

Obtain FPP_TIME_EVIDENCE_V1 deadline receipt quorum and OTS Bitcoin durability evidence for the envelope.

This step is non-forecast governance evidence.

### G3 Freeze external provider and verifier profiles

Only successful retained rehearsals can produce qualifying ProviderProfile or verifier-profile candidates.

A dated provider website snapshot is insufficient.

Each accepted profile binds the exact provider identity, signer or root key material, policy semantics, time-bound calculation, verifier version, and retained rehearsal evidence required by the protocol.

### G4 Freeze source-adapter evidence

Retain the three selected retrospective official first-release byte fixtures, raw SHA256 values, retrieval metadata, and successful adapter reports.

These are permanently retrospective and never become forecast history.

### G5 Freeze exact validator contract

Run the complete test suite under the final candidate code, retain the final test report, and build the exact ValidatorContract using the final candidate commit.

### G6 Freeze candidate Genesis TrustedManifest

The manifest references only already frozen normative objects, the externally evidenced bootstrap root, qualifying provider/verifier profiles, exact source and adapter contracts, and exact ValidatorContract.

Any missing required dependency blocks construction.

### G7 Externally evidence candidate manifest

Obtain FPP_TIME_EVIDENCE_V1 evidence for the exact candidate manifest hash.

### G8 Run Genesis validation suite

Run the frozen Trust Core tests, Genesis-specific adversarial suite, schema verification, dependency closure, candidate inventory reproducibility, provider-profile verification, source-fixture checks, and manifest reproducibility checks.

All required reports are content addressed.

### G9 Resolve findings

Every blocking finding must be resolved or Genesis is aborted.

A correction to a substantive manifest dependency creates a new candidate and restarts all affected downstream evidence.

### G10 Create ManifestAcceptance

ManifestAcceptance binds the exact candidate manifest, bootstrap root, manifest time evidence, validation reports, rehearsal reports, and empty blocking-finding set.

The owner signs the canonical acceptance payload using the bootstrap Ed25519 key.

### G11 Externally evidence ManifestAcceptance

Obtain FPP_TIME_EVIDENCE_V1 evidence for the exact signed acceptance record.

### G12 Genesis acceptance gate

An independent validation run verifies:

```text
bootstrap root valid
candidate manifest valid
manifest time evidence valid
provider and verifier profiles valid
source fixture and adapter reports valid
exact validator binding valid
all required reports valid
owner signature valid
acceptance time evidence valid
blocking findings empty
```

Only after G12 passes may a separate explicit decision change repository state to `GENESIS_ACCEPTED`.

### G13 First issuance cycle

The first IssuanceCyclePlan must be derived from the already accepted IssuanceSchedulePolicy and must have an execution window strictly later than Genesis acceptance.

No pre-Genesis output can be imported into that cycle.

## Abort and restart semantics

A changed candidate TrustedManifest after external evidence is obtained is a new candidate and requires new time evidence and a new acceptance record.

A changed bootstrap public key creates a new BootstrapGovernanceRoot version and restarts from G1.

A changed ProviderProfile after G3 requires revalidation of every downstream object that references it.

A changed source adapter or ValidatorContract after G5 requires a new candidate manifest.

A failed rehearsal cannot be omitted from the Genesis review record when it materially informs provider eligibility or an abort condition.

A failed or aborted Genesis attempt never becomes native prospective history.

## Genesis identity

The term `Genesis` is reserved for the first accepted protocol and ledger state.

Design branches, rehearsal commits, candidate objects, test fixtures, and failed acceptance attempts must not use tags or labels that imply Genesis acceptance.