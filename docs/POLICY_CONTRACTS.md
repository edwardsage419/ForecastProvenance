# Consequential Policy Contracts

Version: 0.3 candidate
Status: FTC_001 FREEZE CANDIDATE

Every policy capable of changing trust, issuance, omission, correction, evaluation, retention, or review behavior is a first class versioned normative object.

## Shared PolicyDefinition envelope

Required substantive fields:

```text
policy_id
policy_version
policy_type
scope
rules
change_policy
content_sha256
```

A policy change that can alter any scientific outcome requires a new policy version and, where applicable, a successor trusted manifest.

Unknown policy fields are rejected by the active schema.

## RetryPolicy

Required rule fields:

```text
max_attempts
retry_eligible_failure_codes
randomness_progression_rule
issuance_eligible_success_rule
infrastructure_timeout_rule
exhausted_budget_rule
```

Retry eligibility cannot depend on forecast value or desirability.

## OmissionPolicy

Required rule fields:

```text
allowed_omission_codes
required_evidence_by_code
operator_discretion_rule
cohort_accounting_rule
```

Version 1 sets `operator_discretion_rule = PROHIBITED_AFTER_OUTPUT_INSPECTION`.

## CorrectionPolicy

Required rule fields:

```text
correction_types
substantive_field_set
replacement_requirement
withdrawal_rule
scoring_treatment_by_type
```

Scoring treatment is determined here before issuance. ForecastCorrection cannot override it.

## EvaluationPolicy

Required rule fields:

```text
cohort_definition
inclusion_rule
withdrawal_treatment
missing_slot_treatment
unresolved_treatment
scoring_rule_refs
aggregation_rule
```

An issued confirmatory forecast cannot disappear from evaluation because its outcome or score is unfavorable.

## RetentionPolicy

Required rule fields:

```text
artifact_class_rules
minimum_retention_by_class
external_recovery_rule
current_verifiability_rule
```

Loss of required bytes changes current verifiability and does not rewrite immutable historical validation records.

## ReviewRule

Required rule fields:

```text
authorized_subject_types
authorized_decisions
reviewer_authority_requirements
required_evidence
conflict_rule
hard_override_prohibitions
```

Hard cryptographic mismatch and known future information violations are non overridable.

## AcceptanceRule

Required rule fields:

```text
candidate_subject_type
authority_requirement
required_validation_reports
required_external_anchor_evidence
decision_values
predecessor_binding_rule
```

For Genesis, authority is supplied through an out of graph BootstrapGovernanceRoot. After Genesis, successor acceptance follows the previously accepted governance state.

## AnchorScheme

Trust Core freezes the interface, while Genesis freezes a concrete scheme.

Required rule fields:

```text
accepted_subject_types
proof_input_contract
verification_algorithm_contract
existence_bound_output_contract
pending_state_rule
malformed_proof_rule
conflict_rule
```

A real AnchorScheme must return a conservative externally verifiable existence bound or a non verified state. Synthetic implementations may mock this interface and must remain ineligible for prospective status.

## ResolutionEvidencePolicy

Required rule fields:

```text
source_priority
publication_semantics
retrieval_semantics
vintage_selection
conflict_rule
evidence_sufficiency
resolution_deadline_rule
human_review_rule_or_none
```

Resolution evidence is evaluated under this policy and is not constrained by the forecast information cutoff.