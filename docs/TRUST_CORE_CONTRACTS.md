# Forecast Trust Core Normative Contracts

Version: 0.1 candidate
Status: FTC_001 REVIEW CANDIDATE

This document defines the minimum normative fields and validation rules for the eight Trust Core object families.

All references use semantic object identity plus full SHA256 content identity.

## 1. Shared envelope

Every normative object contains:

```text
object_type
schema_version
object_id
classification
content_sha256
```

Allowed `classification` values before Genesis:

```text
NORMATIVE
SYNTHETIC
RETROSPECTIVE
```

`PROSPECTIVE` is reserved and invalid before Genesis acceptance.

## 2. TargetDefinition

Required substantive fields:

```text
target_id
target_version
forecast_class
question
outcome_type
unit
entity_scope
geography_scope
reference_period_rule
forecast_horizon_rule
measurement_source_rule
vintage_policy
ambiguity_policy
unresolved_policy
resolution_deadline_rule
compatible_resolution_rule_ids
```

Validation:

1. ID and version are well formed.
2. Outcome type is supported by the schema.
3. Unit and scope are explicit.
4. Horizon and reference period are determinable without observing the outcome.
5. Resolution compatibility is explicit.
6. Ambiguity and unresolved policies are present.
7. Any semantic change requires a new target version.

## 3. ResolutionRule

Required substantive fields:

```text
resolution_rule_id
resolution_rule_version
compatible_target_refs
source_priority
vintage_selection
conflict_policy
evidence_sufficiency
allowed_resolution_states
ambiguity_policy
resolution_deadline_rule
```

Validation:

1. Every target reference hash matches the dependency store.
2. The rule cannot select sources based on which outcome is more favorable to a forecast.
3. Conflict handling is deterministic or explicitly human reviewed.
4. Allowed resolution states include an unresolved state.
5. Changes capable of changing an outcome require a new rule version.

## 4. EvidenceSnapshot

Required substantive fields:

```text
snapshot_id
information_cutoff
snapshot_closed_at
members
source_contract_refs
transformation_refs
upstream_snapshot_refs
```

Each member includes:

```text
evidence_id
content_sha256
available_at
source_contract_ref
revision_id_or_state
```

Validation:

1. Member identities are unique.
2. Every member hash resolves.
3. Every required member passes point in time eligibility.
4. Snapshot closure time is not used as a substitute for member availability.
5. Transform dependencies resolve.
6. Fitted transforms pass fit cutoff rules.
7. Snapshot identity is deterministic from substantive content.

## 5. ForecastMethod

Required substantive fields:

```text
method_id
method_version
method_family
compatible_target_refs
required_input_contracts
implementation_ref
model_ref_or_none
fitted_state_ref_or_none
prompt_or_configuration_ref_or_none
retrieval_policy
randomness_policy
output_semantics
probability_semantics
known_limitations
```

Validation:

1. All consequential implementation and configuration inputs are content bound.
2. Randomness policy is explicit.
3. Retrieval capability is explicit.
4. Probability semantics are explicit when probabilistic output is produced.
5. Model identity alone is insufficient when prompt, adapter, fitted state, tools, or configuration can change output.
6. A substantive method change requires a new method version.

## 6. ForecastRunAttempt

Required substantive fields:

```text
attempt_id
method_ref
target_ref
information_cutoff
started_at
ended_at
input_snapshot_refs
runtime_configuration_ref
randomness_record
retrieval_log_ref_or_none
terminal_status
failure_code_or_none
output_artifact_ref_or_none
retry_of_or_none
```

Allowed terminal statuses:

```text
SUCCEEDED
FAILED
ABORTED
INELIGIBLE_INPUT
```

Validation:

1. One execution equals one attempt.
2. Every retry receives a new attempt ID.
3. Attempts cannot be deleted from confirmatory attempt accounting.
4. A successful attempt must bind an output artifact.
5. A failed attempt cannot silently become the issued attempt.
6. Retry lineage is acyclic.
7. A retry policy in the trusted manifest determines issuance eligibility.

## 7. IssuedForecast

Required substantive fields:

```text
forecast_id
target_ref
resolution_rule_ref
method_ref
run_attempt_ref
evidence_snapshot_refs
information_cutoff
forecast_for
prediction
claimed_issued_at
issuance_cycle_id
correction_policy_ref
retry_policy_ref
protocol_id
```

The `prediction` object is target class specific and uses canonical decimal strings for scientific decimals.

Validation:

1. All dependency IDs and hashes match.
2. Target, rule, and method compatibility pass.
3. The bound run attempt is successful and issuance eligible.
4. Every evidence snapshot passes point in time checks.
5. `information_cutoff` is consistent across bound dependencies.
6. Prediction satisfies target outcome semantics.
7. The active trusted manifest admits all consequential dependencies.
8. Before an accepted external anchor, the forecast may be internally valid but remains `PENDING_EXTERNAL_ANCHOR`.
9. A forecast cannot become prospective merely through a claimed issuance timestamp.

## 8. AnchorReceipt

Required substantive fields:

```text
anchor_receipt_id
anchor_scheme_ref
anchored_object_type
anchored_object_ref
submitted_at
proof_artifact_ref
verification_state
verified_at_or_none
external_attestation
verifier_contract_ref
failure_code_or_none
```

Allowed verification states:

```text
NOT_SUBMITTED
PENDING_BITCOIN
VERIFIED_BITCOIN
FAILED_ANCHOR
LATE_OR_INELIGIBLE
```

Validation:

1. Anchored hash equals the target forecast batch manifest hash.
2. Proof bytes are retained or content addressed.
3. Verification follows the admitted anchor scheme.
4. Local timestamps cannot upgrade verification state.
5. A late proof is handled by Genesis policy and cannot be silently accepted.

## 9. ForecastCorrection

Required substantive fields:

```text
correction_id
original_forecast_ref
recorded_at
correction_type
reason
affected_fields
replacement_forecast_ref_or_none
authority_ref
scoring_consequence
```

Correction types:

```text
METADATA_NON_SUBSTANTIVE
WITHDRAWAL
SUBSTANTIVE_REPLACEMENT
ADMINISTRATIVE_STATUS
```

Validation:

1. Original forecast remains immutable.
2. Probability, target, horizon, method, information cutoff, or substantive evidence changes cannot use `METADATA_NON_SUBSTANTIVE`.
3. A substantive replacement points to a new forecast object.
4. Corrections are append only.
5. Scoring consequence is explicit.
6. A correction cannot erase an attempt, issuance, or anchor record.

## 10. Validation result envelope

Every validation produces:

```text
validator_contract_ref
trusted_manifest_ref
candidate_object_ref
result
checks
validated_at
```

Core result values:

```text
VALID
INVALID
INELIGIBLE_TRUST_UNKNOWN
PENDING_EXTERNAL_ANCHOR
VALID_NON_PROSPECTIVE
```

Each check records:

```text
check_id
status
evidence_refs
reason_code
```

Allowed check status values are `PASS`, `FAIL`, and `UNKNOWN`.

`UNKNOWN` on a required trust condition cannot be aggregated upward into `VALID`.

## 11. Lifecycle state machines

### ForecastRunAttempt

```text
CREATED -> RUNNING -> SUCCEEDED
                   -> FAILED
                   -> ABORTED
                   -> INELIGIBLE_INPUT
```

Terminal states are immutable.

### IssuedForecast trust lifecycle

```text
DRAFT
  -> SEALED_INTERNAL
  -> PENDING_EXTERNAL_ANCHOR
  -> PROSPECTIVE_VERIFIED
```

Failure branches:

```text
PENDING_EXTERNAL_ANCHOR -> ANCHOR_FAILED
PENDING_EXTERNAL_ANCHOR -> LATE_OR_INELIGIBLE
```

Before Genesis, transition to `PROSPECTIVE_VERIFIED` is prohibited.

### Correction lifecycle

```text
RECORDED -> EFFECTIVE
```

A rejected correction remains recorded with `REJECTED` disposition and cannot be deleted.

## 12. Non automatable review rules

Automation may return `REQUIRES_REVIEW` inside an individual check only where a normative contract explicitly allows human judgment, such as ambiguous external source conflicts.

Human review must produce an immutable review record with reviewer identity, evidence references, rule identity, decision, and rationale.

Human review cannot override a hard cryptographic mismatch or known future information violation.
