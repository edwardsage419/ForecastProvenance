# Forecast Trust Core Normative Contracts

Version: 0.4 candidate
Status: FTC_001 FINAL FREEZE CANDIDATE

All consequential references bind semantic identity plus full SHA256 content identity.

## Shared semantics

`object_role` and stored origin class are separate.

Definition, policy, and governance objects use `object_role = NORMATIVE`.

Evidence bearing objects may persist only an origin classification such as `SYNTHETIC`, `RETROSPECTIVE`, or `LIVE_OPERATIONAL`. `LIVE_OPERATIONAL` states where an object originated and grants no prospective trust status. Prospective eligibility is derived only by ValidationReport under the applicable trusted manifest, acceptance state, anchor evidence, and protocol.

All machine identifiers are ASCII.

## Core object families

### TargetDefinition

Required fields include target identity and version, forecast class, question, outcome type, unit, entity and geography scope, reference period rule, horizon rule, measurement source rule, vintage policy, ambiguity policy, unresolved policy, resolution deadline rule, compatible resolution rules, `external_proof_deadline_rule`, and `outcome_information_barrier_rule`.

Both deadline rules must be determinable before forecast output inspection.

For confirmatory prospective use, every instantiated slot must satisfy:

```text
external_proof_deadline <= outcome_information_barrier
```

The barrier is an ex ante protocol boundary indicating when outcome information is considered potentially available for the target class. It is not inferred from the realized outcome.

### ResolutionRule

Binds compatible targets, ordered source priority, vintage selection, conflict policy, evidence sufficiency, allowed resolution states, ambiguity policy, resolution deadline, ResolutionEvidencePolicy, and any authorized human review rule.

Forecast information cutoff rules do not govern outcome resolution evidence.

### EvidenceSnapshot

Binds information cutoff, closure metadata, deterministically sorted member references, SourceContract references, TransformationDefinition references, FittedState references where applicable, and upstream snapshots.

Each consequential member binds exact content identity, availability claim, source contract, and revision identity. Source artifact selection must comply with the bound SourceContract.

### ForecastMethod

Binds method version, family, compatible targets, required inputs, implementation, model identity, fitted state, prompt or configuration, retrieval policy, randomness policy, output semantics, probability semantics, known limitations, `evidence_observability_class`, and `selection_control_class`.

Confirmatory eligibility for stochastic or opaque execution is governed by `EXECUTION_SELECTION_CONTROL.md`. A method with uncontrolled nondeterminism cannot gain a confirmatory prospective claim merely because one recorded run exists.

### ForecastRunAttempt

One execution is one immutable attempt.

Required fields bind method, target instance, planned slot, information cutoff, input snapshots, runtime configuration, randomness evidence where applicable, retrieval log, terminal status, failure code, output artifact, attempt sequence, and predecessor attempt.

Local `started_at` and `ended_at` may be retained as operational metadata. They do not prove cycle precommitment ordering.

### IssuedForecast

IssuedForecast is immutable.

Required fields bind target instance, resolution rule, method, successful issuance eligible run attempt, evidence snapshots, information cutoff, forecast horizon, prediction, operational claimed issuance time, cycle plan, correction policy, retry policy, and protocol.

It contains no mutable trust status and no self asserted prospective flag.

### AnchorReceipt

The mutable AnchorReceipt design is retired.

Trust Core uses immutable `AnchorEvidenceEvent` objects. Anchor state is derived from a validated event DAG under an admitted AnchorScheme and validator contract.

### ForecastCorrection

ForecastCorrection is immutable and records original forecast, correction type, reason, affected fields, replacement forecast when required, authority, and evidence.

It cannot select its own scoring consequence. Evaluation treatment comes from the precommitted CorrectionPolicy and EvaluationPolicy.

## Supporting first class normative contracts

Trust Core also depends on:

1. SourceContract.
2. TransformationDefinition.
3. FittedState.
4. ReviewDecision.
5. ManifestAcceptance.
6. IssuanceCyclePlan.
7. IssuanceCycleManifest.
8. AnchorEvidenceEvent.
9. ValidationReport.
10. CurrentVerifiabilityReport.
11. BootstrapGovernanceRoot.
12. PolicyDefinition subtypes defined in `POLICY_CONTRACTS.md`.
13. Execution selection control rules defined in `EXECUTION_SELECTION_CONTROL.md`.
14. Resolution evidence semantics defined in `RESOLUTION_EVIDENCE_SEMANTICS.md`.

## Deterministic schedule requirement

Confirmatory IssuanceCyclePlan objects must be the deterministic output of the IssuanceSchedulePolicy bound by the applicable trusted manifest.

Target and method inclusion is therefore a protocol decision made before cycle outputs exist, rather than an operator selection at issuance time.

Historical cycle validation always uses the exact schedule policy version bound by that historical manifest.

## Derived lifecycle

Lifecycle is validator output over immutable objects and evidence.

An IssuedForecast may derive to:

```text
INTERNALLY_VALID
PENDING_EXTERNAL_PROOF
PROSPECTIVE_ELIGIBLE
ANCHOR_FAILED
LATE_OR_INELIGIBLE
TRUST_UNKNOWN
```

No derived lifecycle transition rewrites IssuedForecast.

## Validation results

Required checks use `PASS`, `FAIL`, or `UNKNOWN`. `UNKNOWN` on a required trust condition cannot aggregate into a stronger valid trust claim.

ValidationReport contains deterministic scientific validation content. Runtime execution metadata is separate.

Historical validation and current verifiability are separate claims. Loss of evidence bytes can degrade current verifiability without rewriting an earlier immutable report.

## Human review

Human discretion exists only where an accepted ReviewRule explicitly authorizes it. ReviewDecision binds authority, evidence, rule, decision, and rationale.

Human review cannot override cryptographic mismatch, known future information leakage, or other hard prohibitions defined by the active contract.

## Array semantics

Priority arrays preserve declared order.

Set like dependency arrays sort by object ID and full hash.

Attempt and anchor evidence relationships use explicit immutable references. Local sequence numbers do not establish external chronology.

Any normative schema that omits array semantics is incomplete.