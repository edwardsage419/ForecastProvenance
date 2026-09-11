# Supporting Normative Contracts

Version: 0.3 candidate
Status: FTC_001 FREEZE CANDIDATE

These objects are first class normative dependencies of Forecast Trust Core. They create no prospective history by themselves.

## SourceContract

Required substantive fields:

```text
source_contract_id
source_contract_version
source_identity
access_mode
artifact_identity_rule
availability_rule
publication_rule
revision_rule
retention_class
failure_semantics
```

The availability rule defines how `available_at` is established. Retrieval time cannot silently substitute for historical availability.

## TransformationDefinition

Required substantive fields:

```text
transformation_id
transformation_version
implementation_ref
parameters_ref
state_class
input_contracts
output_contract
determinism_policy
```

`state_class` is `STATELESS` or `FITTED`.

## FittedState

Required substantive fields:

```text
fitted_state_id
transformation_ref
fit_information_cutoff
fit_window
fit_snapshot_refs
configuration_ref
state_artifact_ref
```

Every consequential fit input must satisfy its applicable point in time rule.

## ReviewDecision

Required substantive fields:

```text
review_decision_id
review_rule_ref
subject_ref
reviewer_authority_ref
evidence_refs
decision
reason_codes
rationale
supersedes_or_none
```

ReviewDecision is immutable. Human review cannot override a cryptographic mismatch, known future information use, or a rule that does not authorize human discretion.

## ManifestAcceptance

Required substantive fields:

```text
manifest_acceptance_id
candidate_manifest_ref
external_anchor_evidence_ref
acceptance_rule_ref
authority_ref
bootstrap_root_ref_or_predecessor_acceptance_ref
decision
reason_codes
```

Genesis validation receives a `BootstrapGovernanceRoot` from outside the candidate manifest graph. Later acceptances bind the predecessor accepted governance state. A candidate manifest never grants itself authority.

## IssuanceCyclePlan

Required substantive fields:

```text
cycle_plan_id
protocol_id
trusted_manifest_ref
cycle_label
information_cutoff
execution_window_open
execution_window_close
plan_commitment_deadline
external_proof_deadline
expected_slots
retry_policy_ref
omission_policy_ref
```

Rules:

1. `plan_commitment_deadline <= execution_window_open`.
2. The exact plan must obtain accepted external existence evidence whose verified bound is at or before `plan_commitment_deadline`.
3. Local attempt timestamps do not establish valid precommitment.
4. Any substantive plan change creates a new plan ID and requires a new external precommitment before its execution window.
5. A version 1 expected slot has `forecast_cardinality = 1` and binds exact target instance, method, output schema, horizon, evidence contract, and deterministic slot ID.

## IssuanceCycleManifest

Required substantive fields:

```text
cycle_manifest_id
cycle_plan_ref
slot_accounting
attempt_refs
issued_forecast_refs
omission_records
```

The manifest contains no self referential anchor hash. Its final `content_sha256` is the subject referenced by anchor evidence.

Every planned slot appears exactly once in slot accounting. Allowed terminal outcomes are `ISSUED`, `FAILED`, `INELIGIBLE_INPUT`, `OMITTED_BY_PRECOMMITTED_RULE`, and `INFRASTRUCTURE_ABORT`.

## AnchorEvidenceEvent

Anchor evidence is an immutable DAG.

Required substantive fields:

```text
anchor_event_id
anchor_scheme_ref
anchored_subject_ref
event_type
proof_artifact_ref_or_none
external_attestation_or_none
predecessor_event_refs
operational_record_ref_or_none
```

Allowed scientific event types are `SUBMISSION_EVIDENCE`, `PROOF_UPGRADE`, and `VERIFICATION_EVIDENCE`.

Local operational failure reports are separate operational records and do not prove external service failure.

Multiple proof branches may coexist only when each independently validates the same anchored subject. Conflicting subject identity, malformed proof, or incompatible scheme claims fail closed. Local sequence numbers do not establish external chronology.

## ValidationReport

Deterministic scientific validation output:

```text
validation_report_id
validator_contract_ref
trusted_manifest_ref
manifest_acceptance_ref
candidate_object_ref
dependency_refs
historical_validation_result
checks
```

`dependency_refs` is a deterministically sorted array of full object references. Version 1 has no undefined dependency root.

Runtime execution time is excluded. `historical_validation_result` is immutable for the exact retained inputs and validator contract.

## CurrentVerifiabilityReport

A separate derived report states whether the bytes and proofs needed for independent verification are currently available.

Loss of retained evidence can degrade current verifiability to `PARTIAL` or `UNVERIFIABLE` without rewriting a prior ValidationReport.

## Retention classes

`INLINE_CONTENT`: canonical bytes retained by the project.

`CONTENT_ADDRESSED_LOCAL`: bytes retained in a content addressed project artifact store.

`EXTERNAL_REPRODUCIBLE`: bytes may be external when a frozen acquisition rule and full hash permit reproducible recovery.

`EXTERNAL_FRAGILE`: insufficient for a durable high trust claim unless separately archived.

Current verifiability degrades when required bytes are unavailable.