# Forecast Trust Core Normative Contracts

Version: 0.2 candidate
Status: FTC_001 REMEDIATION CANDIDATE

All consequential references bind semantic identity plus full SHA256 content identity.

## Shared semantics

`object_role` and `evidence_class` are separate.

Definition and policy objects use `object_role = NORMATIVE`.

Evidence bearing objects use `evidence_class = SYNTHETIC`, `RETROSPECTIVE`, or after Genesis eligibility validation, a derived prospective classification. Prospective status is never self asserted in the immutable forecast payload.

All machine identifiers are ASCII.

## Core object families

### TargetDefinition

Required fields include target identity and version, forecast class, question, outcome type, unit, entity and geography scope, reference period rule, horizon rule, measurement source rule, vintage policy, ambiguity policy, unresolved policy, resolution deadline rule, compatible resolution rules, and `external_proof_deadline_rule`.

The deadline rule must be determinable before forecast output inspection.

Set like compatible reference arrays use deterministic reference sorting.

### ResolutionRule

Binds compatible targets, ordered source priority, vintage selection, conflict policy, evidence sufficiency, allowed resolution states, ambiguity policy, resolution deadline, and any authorized human review rule.

Forecast point in time evidence rules are not reused as outcome resolution admissibility rules.

### EvidenceSnapshot

Binds information cutoff, closure metadata, deterministically sorted member references, SourceContract references, TransformationDefinition references, FittedState references where applicable, and upstream snapshots.

Each member binds exact content hash, available_at claim, source contract, and revision identity.

### ForecastMethod

Binds method version, family, compatible targets, required inputs, implementation, model identity, fitted state, prompt or configuration, retrieval policy, randomness policy, output semantics, probability semantics, known limitations, and `evidence_observability_class`.

### ForecastRunAttempt

One execution is one immutable attempt.

Required fields bind method, target, planned slot, information cutoff, input snapshots, runtime configuration, randomness, retrieval log, terminal status, failure code, output artifact, attempt sequence, and predecessor attempt.

Terminal attempt objects never mutate.

### IssuedForecast

IssuedForecast is immutable.

Required fields bind target, resolution rule, method, successful issuance eligible run attempt, evidence snapshots, information cutoff, forecast horizon, prediction, operational claimed issuance time, cycle plan, correction policy, retry policy, and protocol.

It contains no mutable trust status.

### AnchorReceipt

The previous mutable AnchorReceipt design is retired.

Version 0.2 uses immutable `AnchorEvidenceEvent` objects defined in SUPPORTING_NORMATIVE_CONTRACTS.md. Anchor state is derived from the ordered event graph under the active validator contract.

### ForecastCorrection

ForecastCorrection is immutable and records original forecast, correction type, reason, affected fields, replacement forecast when required, authority, and evidence.

It does not contain a self selected scoring consequence. Evaluation derives treatment from the precommitted CorrectionPolicy.

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

Their schemas are defined in SUPPORTING_NORMATIVE_CONTRACTS.md.

## Derived lifecycle

Lifecycle is validator output over immutable objects and events.

An IssuedForecast can be derived as:

```text
INTERNALLY_VALID
PENDING_EXTERNAL_PROOF
PROSPECTIVE_ELIGIBLE
ANCHOR_FAILED
LATE_OR_INELIGIBLE
TRUST_UNKNOWN
```

No lifecycle transition rewrites IssuedForecast.

## Validation results

Core aggregate results are:

```text
VALID
INVALID
INELIGIBLE_TRUST_UNKNOWN
PENDING_EXTERNAL_ANCHOR
VALID_NON_PROSPECTIVE
```

Required checks use PASS, FAIL, or UNKNOWN. UNKNOWN cannot aggregate into VALID.

ValidationReport excludes runtime validation timestamps from deterministic scientific content.

## Human review

Human discretion exists only where an accepted normative rule explicitly authorizes it. ReviewDecision binds authority, evidence, rule, decision, and rationale.

Human review cannot override cryptographic mismatch or known future information leakage.

## Array semantics

Priority arrays preserve declared order.

Set like dependency arrays sort by object ID and full hash.

Attempt and anchor event sequences use explicit integer sequence fields.

Any schema that omits array semantics is incomplete and fails design acceptance.
