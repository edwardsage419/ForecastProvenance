# Genesis Manifest and Acceptance Procedure

Version: 0.1 candidate
Status: GEN_001 REVIEW CANDIDATE

## Candidate Genesis manifest

The Genesis trusted manifest is the first authoritative protocol state of the project.

It must bind exact object IDs and full SHA256 hashes for:

1. Genesis Protocol version.
2. FPP_JCS_1 canonicalization contract.
3. Validator contract and implementation version.
4. Bootstrap governance root.
5. Acceptance policy.
6. External time evidence policies and provider profiles.
7. Initial target definitions.
8. Resolution rules and resolution evidence policies.
9. Forecast methods and transparent baselines.
10. Source contracts.
11. Transformation definitions and fitted states where applicable.
12. IssuanceSchedulePolicy.
13. RetryPolicy.
14. OmissionPolicy.
15. CorrectionPolicy.
16. RetentionPolicy.
17. EvaluationPolicy and scoring rules.
18. Human review rules where applicable.
19. Project cost doctrine and allowed operational dependencies.

No reference is valid by semantic ID alone.

## Genesis sequence

### G0 Freeze normative candidate set

Every referenced object is sealed and hash verified. No production forecast is run.

### G1 Freeze bootstrap governance root

The exact owner generated Ed25519 public key is inserted into BootstrapGovernanceRoot and the root is sealed.

### G2 Externally evidence bootstrap governance

Create a GenesisGovernanceEnvelope containing the bootstrap root and acceptance policy references.

Obtain FPP_TIME_EVIDENCE_V1 deadline receipt quorum and OTS Bitcoin durability evidence for the envelope.

This step is non forecast governance evidence.

### G3 Freeze candidate Genesis manifest

The manifest references only already frozen objects and the externally evidenced bootstrap root.

### G4 Externally evidence candidate manifest

Obtain FPP_TIME_EVIDENCE_V1 evidence for the exact candidate manifest hash.

### G5 Run Genesis validation suite

Run the frozen Trust Core tests, Genesis specific adversarial suite, schema verification, dependency closure checks, and reproducibility checks.

All required reports are content addressed.

### G6 Run non forecast anchor rehearsals

Use synthetic subjects to exercise every configured time provider profile, receipt parser, receipt upper bound calculation, quorum rule, OTS submission, proof upgrade, and strong Bitcoin verification path.

Rehearsal artifacts are permanently classified non prospective.

### G7 Resolve findings

Every blocking finding must be resolved or Genesis is aborted.

### G8 Create ManifestAcceptance

ManifestAcceptance binds the exact candidate manifest, bootstrap root, manifest time evidence, validation reports, rehearsal reports, and empty blocking finding set.

The owner signs the canonical acceptance payload using the bootstrap Ed25519 key.

### G9 Externally evidence ManifestAcceptance

Obtain FPP_TIME_EVIDENCE_V1 evidence for the exact signed acceptance record.

### G10 Genesis acceptance gate

An independent validation run verifies:

```text
bootstrap root valid
candidate manifest valid
manifest time evidence valid
all required reports valid
owner signature valid
acceptance time evidence valid
blocking findings empty
```

Only after G10 passes may the repository state change to GENESIS_ACCEPTED.

### G11 First issuance cycle

The first IssuanceCyclePlan must be derived from the already accepted IssuanceSchedulePolicy and must have an execution window strictly later than Genesis acceptance.

No pre Genesis output can be imported into that cycle.

## Abort and restart semantics

A changed candidate manifest after G4 is a new candidate manifest and requires new time evidence and a new acceptance record.

A changed bootstrap public key creates a new BootstrapGovernanceRoot version and restarts from G1.

A failed rehearsal cannot be omitted from the Genesis review record.

A failed or aborted Genesis attempt never becomes native prospective history.

## Genesis identity

The term `Genesis` is reserved for the first accepted protocol and ledger state.

Design branches, rehearsal commits, test fixtures, and failed candidates must not use tags or labels that imply Genesis acceptance.