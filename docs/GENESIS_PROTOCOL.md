# Forecast Ledger Genesis Protocol

Version: 0.2 readiness candidate
Status: NOT ACCEPTED

No genuine prospective forecast may be issued under this draft.

## Genesis purpose

Genesis is the first accepted protocol state from which native prospective history can begin.

It is not a software release milestone and is not inferred from repository age, branch names, tags, or successful tests.

## Genesis must freeze

1. Genesis protocol identity and version.
2. BootstrapGovernanceRoot exact public key and acceptance policy.
3. FPP_TIME_EVIDENCE_V1 policies and accepted provider profiles.
4. OTS_BTC_BUNDLE_V1 verifier contract.
5. Initial target set and target versions.
6. Resolution rule versions and archive procedures.
7. Evidence SourceContracts and information-cutoff policy.
8. IssuanceSchedulePolicy and schedule-snapshot rules.
9. Forecast methods and transparent baselines.
10. Run retry policy.
11. Omission policy.
12. Correction and withdrawal policy.
13. Evaluation cohort and scoring policy.
14. Publication and retention policy.
15. Trusted manifest identity.
16. Validator version and implementation hash.
17. Cost budget and operational cadence.
18. Genesis abort conditions.

## Genesis readiness sequence

1. Freeze candidate normative and target objects.
2. Generate owner controlled Ed25519 bootstrap key outside the repository and insert only its public key into BootstrapGovernanceRoot.
3. Freeze the exact BootstrapGovernanceRoot and retain its bytes and SHA256 independently of the candidate manifest graph.
4. Freeze external provider and verifier profiles required by the admitted Genesis v1 evidence path.
5. Freeze the exact ValidatorContract from the final candidate code and retained validation report.
6. Freeze the candidate Genesis TrustedManifest.
7. Run the frozen Trust Core suite, Genesis specific adversarial suite, schema checks, dependency closure, provider-profile verification, source-fixture checks, and manifest reproducibility checks.
8. Resolve every blocking readiness finding.
9. Create and owner-sign ManifestAcceptance v2 for the exact candidate TrustedManifest and exact BootstrapGovernanceRoot.
10. Create final external wall-clock evidence over the exact signed ManifestAcceptance.
11. Create and strongly verify Bitcoin durability evidence over the exact final evidence bundle.
12. Run an independent final Genesis validation over the independently supplied BootstrapGovernanceRoot, exact TrustedManifest, required reports, owner signature, final external existence evidence, and Bitcoin durability evidence.
13. Only after every readiness gate passes may the owner issue a separate explicit Genesis authorization.
14. Only after that authorization may the first deterministic IssuanceCyclePlan be constructed for a future execution window.

Standalone external anchors for the BootstrapGovernanceRoot or candidate TrustedManifest may be retained as optional audit evidence. They are not mandatory readiness gates and cannot substitute for final external evidence over the exact signed ManifestAcceptance.

## Initial target policy

Genesis version 1 uses a minimal low-frequency target set.

The current candidate set is defined in `GENESIS_INITIAL_TARGET_SET_CANDIDATE.md` and remains subject to source-contract and parser review.

Every initial target must satisfy:

```text
forecast_horizon >= 7 calendar days
external_proof_deadline <= outcome_information_barrier - 24 hours
```

Intraday and same-day targets are excluded.

## Time evidence policy

Precise deadline evidence and Bitcoin durability evidence are separate.

Signed external wall-clock receipt quorum proves the subject existed before the frozen deadline.

OpenTimestamps plus Bitcoin provides durable append-only anchoring of the evidence bundle.

Final initial-cohort prospective eligibility additionally requires timely DurabilityVerificationRecord evidence before the target outcome information barrier.

The detailed contract is `GENESIS_TIME_EVIDENCE.md`.

## Schedule policy

Cycle inclusion is derived deterministically from frozen target definitions and official content-addressed schedule snapshots under `GENESIS_SCHEDULE_POLICY.md`.

Schedule delays after plan precommitment never move the historical outcome information barrier later.

Early-release risk fails closed under the frozen policy.

## Genesis state transition

The repository may transition from `TRUST_CORE_BUILD` to `GENESIS_ACCEPTED` only through an accepted ManifestAcceptance, successful independent final validation, and separate explicit Genesis authorization.

A design document, pull request merge, rehearsal success, successful final validation, or repository state change by itself cannot create Genesis.

## Contamination prohibition

Synthetic fixtures, retrospective experiments, rehearsal artifacts, failed Genesis candidates, and external or predecessor artifacts are permanently excluded from native prospective Genesis history.

No forecast output produced before Genesis acceptance can be copied into the first prospective cycle.