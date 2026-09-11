# Supporting Normative Contracts

Version: 0.2 candidate
Status: FTC_001 REMEDIATION CANDIDATE

These contracts are first class normative dependencies of Forecast Trust Core. They do not create additional forecast history.

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

`availability_rule` must state exactly how `available_at` is established. Retrieval time cannot silently substitute for availability time.

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

Every fit input must satisfy `available_at <= fit_information_cutoff`.

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

ReviewDecision is immutable. A later review creates a new object. Human review cannot override a cryptographic mismatch, a known future information violation, or a rule that does not authorize human discretion.

## ManifestAcceptance

Required substantive fields:

```text
manifest_acceptance_id
candidate_manifest_ref
external_anchor_evidence_ref
acceptance_rule_ref
authority_ref
predecessor_acceptance_ref_or_none
decision
reason_codes
```

Only `decision = ACCEPT` under the applicable governance rule can make a candidate manifest an accepted trust root. Candidate manifest fields cannot self declare acceptance.

## IssuanceCyclePlan

This object closes the selective omission gap before forecast outputs are inspected.

Required substantive fields:

```text
cycle_plan_id
protocol_id
trusted_manifest_ref
cycle_label
information_cutoff
external_proof_deadline
expected_slots
retry_policy_ref
omission_policy_ref
```

Each expected slot binds target, method, evidence contract, and deterministic slot identity. The plan is externally committed under the Genesis defined precommitment rule before any eligible method output for the cycle is inspected.

## IssuanceCycleManifest

Required substantive fields:

```text
cycle_manifest_id
cycle_plan_ref
slot_accounting
attempt_refs
issued_forecast_refs
omission_records
anchor_subject_hash
```

Every expected slot appears exactly once in slot accounting. Allowed terminal slot outcomes are `ISSUED`, `FAILED`, `INELIGIBLE_INPUT`, `OMITTED_BY_PRECOMMITTED_RULE`, and `INFRASTRUCTURE_ABORT`.

A cycle with an unexplained missing expected slot is invalid for confirmatory prospective accounting.

## AnchorEvidenceEvent

Anchor evidence is append only.

Required substantive fields:

```text
anchor_event_id
anchor_scheme_ref
anchored_subject_ref
event_type
proof_artifact_ref
external_attestation
predecessor_event_ref_or_none
operational_record_ref_or_none
```

Allowed event types are `SUBMISSION_EVIDENCE`, `PROOF_UPGRADE`, `VERIFICATION_EVIDENCE`, and `FAILURE_EVIDENCE`.

No event mutates an earlier event.

## ValidationReport

Deterministic scientific validation output:

```text
validation_report_id
validator_contract_ref
trusted_manifest_ref
candidate_object_ref
dependency_root
result
checks
```

Runtime execution time is excluded. An optional operational execution record can state when a validator was run.

## Retention classes

`INLINE_CONTENT`: canonical bytes retained by the project.

`CONTENT_ADDRESSED_LOCAL`: bytes retained in a content addressed project artifact store.

`EXTERNAL_REPRODUCIBLE`: external bytes may be omitted only when a frozen acquisition rule and full content hash permit reproducible recovery.

`EXTERNAL_FRAGILE`: insufficient for a durable high trust claim unless separately archived.

If required bytes become unavailable, validation degrades to `INELIGIBLE_TRUST_UNKNOWN` where independent verification is no longer possible.
