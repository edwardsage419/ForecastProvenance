# Genesis Issuance Schedule Policy

Version: 0.4 successor candidate
Status: GEN_001 REVIEW CANDIDATE

Policy ID: `policy:genesis-issuance-schedule:v3`

Version 3 supersedes v2 for successor candidate v0.9. Historical v1 and v2 bytes remain immutable and continue to govern any history created under those versions. Candidate v0.9 is not accepted or effective and remains non-prospective.

## Purpose

The schedule policy prevents operator discretion over which official target instances enter prospective history and gives every cycle one unambiguous information cutoff and execution window.

## Cycle identity

Genesis version 1 uses one issuance cycle per official target release instance.

A cycle contains exactly one TargetDefinition instance and every ForecastMethod admitted by the active trusted manifest that is compatible with that target.

This avoids combining CPI, Employment Situation, and GDP releases with different information barriers inside one cycle.

At initial Genesis, only `method:last-observed-value:v1` is proposed for admission, so each release cycle initially has one expected forecast slot.

A later accepted manifest can add model methods. From its effective date, every compatible method becomes an expected slot in future cycles under the same schedule rule.

## Mandatory release-instance coverage

After Genesis acceptance, every official release instance of an accepted target is mandatory when its outcome information barrier is at least eight calendar days after the Genesis acceptance completion time.

A missing cycle plan for a mandatory release instance is a protocol-visible `MISSING_CYCLE_PLAN` operational failure. The absence cannot be treated as if the target instance never existed.

Auditors can reconstruct expected cycle instances from the accepted target set, official content-addressed schedule snapshots, and this policy.

## Schedule source

Each target definition identifies an official release-calendar SourceContract.

The schedule snapshot is captured before cycle-plan construction and contains:

```text
source_contract_ref
retrieved_at
raw_artifact_ref
artifact_sha256
parsed_release_identifier
reference_period
published_release_date
published_release_time
published_timezone
parser_version
```

The raw official schedule artifact is retained by content.

## Time-zone conversion

All normative cycle times are stored as UTC whole-second timestamps.

An official local release time is converted to UTC using the IANA zone `America/New_York` for the current initial target set.

A fixed numeric UTC offset is prohibited because target instances can cross daylight-saving transitions.

The schedule derivation report records the time-zone database version.

If the local time is ambiguous or nonexistent under the frozen time-zone rules, cycle construction fails closed.

## Deterministic relative timing

Let the official schedule supply a local release datetime `L` in the target schedule contract's IANA zone, currently `America/New_York`. The schedule derivation evidence binds the exact IANA time-zone database version used.

For offsets expressed in calendar days, subtraction is performed on `L` in the local calendar while preserving the local wall-clock fields. The resulting local datetime is then resolved under the same bound IANA rules and converted to canonical UTC. Ambiguous or nonexistent resulting local times fail closed.

Let `B` be the UTC instant obtained from `L`. Genesis version 1 derives:

```text
plan_commitment_deadline = local_calendar(L - 8 days) -> UTC
information_cutoff = local_calendar(L - 7 days) -> UTC
execution_window_open = local_calendar(L - 7 days) -> UTC
execution_window_close = local_calendar(L - 6 days) -> UTC
external_proof_deadline = B - 24 elapsed hours
durability_completion_deadline = B
```

Calendar-day offsets therefore preserve the official local release clock across daylight-saving transitions. The 24-hour external-proof margin is an elapsed duration from the UTC barrier, not a local-calendar subtraction.

The plan must obtain valid FPP_TIME_EVIDENCE_V1 deadline quorum by `plan_commitment_deadline`.

Forecast execution may begin only at or after `execution_window_open` and must use evidence whose `available_at` is at or before `information_cutoff`.

A forecast execution after `execution_window_close` is an execution failure for Genesis version 1 even if the external proof deadline has not yet arrived.

The longer interval between execution and `external_proof_deadline` exists for anchor recovery and does not authorize later information.

## Expected slot generation

For one target release instance, the expected slot set is the deterministic sorted set of all ForecastMethod objects that:

1. are admitted by the historical trusted manifest applicable to the cycle;
2. bind the target as compatible by full object ID and SHA256;
3. are eligible for confirmatory use under the frozen selection-control policy.

Operators cannot remove an inconvenient method or add an unaccepted method after outputs are known.

### Deterministic runtime object identity

Genesis v1 recomputes runtime identities with the project `seal_object` algorithm and does not accept caller-selected semantic IDs.

TargetInstance stable context:

```text
genesis-target-instance:{target_object_id}:{reference_period}
```

ForecastSlot stable context:

```text
genesis-forecast-slot:{target_instance_object_id}:{method_object_id}
```

The validator reconstructs the canonical runtime payload, calls `seal_object` without a semantic ID override, and requires the resulting full object reference to equal the reference present in the cycle plan.

## Genesis runtime contract v1

Schedule policy v3 binds the exact file SHA256 values of these closed Draft 2020-12 schemas:

```text
target_instance_v1.schema.json
forecast_slot_v1.schema.json
schedule_derivation_evidence_v1.schema.json
issuance_cycle_plan_v1.schema.json
issuance_cycle_manifest_v1.schema.json
```

For each object below, `schema_version = "1.0"`; every listed payload field is required and non-null; there are no optional or nullable payload fields. This is an object-specific decision, not a general claim that every project schema prohibits null. No pre-existing normative null meaning is changed. Unknown fields are rejected.

References contain exactly `object_id` and `content_sha256`. Set-like reference arrays are sorted by `object_id`, then `content_sha256`, and duplicates are rejected. Normative UTC timestamps use `YYYY-MM-DDTHH:MM:SSZ`. Published local schedule dates and times use `YYYY-MM-DD` and `HH:MM:SS` and are meaningful only with the exact bound IANA zone and tzdb artifact.

The payload supplied to `seal_object` is exactly the required field set listed below, excluding only the derived `object_type`, `object_id`, `payload_sha256`, and `content_sha256`. Runtime objects are sealed without `semantic_id`. Authoritative validation reconstructs the object using the frozen stable context and requires equality of the complete `{object_id, content_sha256}` reference. A caller-selected semantic ID or stable context is never equivalent authority.

### ScheduleDerivationEvidence

Exact object type: `ScheduleDerivationEvidence`.

Required payload fields:

```text
schema_version
trusted_manifest_ref
issuance_schedule_policy_ref
target_ref
schedule_source_ref
schedule_artifact_ref
schedule_artifact_sha256
parser_id
parser_version
iana_tzdb_version
tzdb_artifact_ref
retrieved_at
parsed_release_identifier
reference_period
published_local_date
published_local_time
published_timezone
authoritative_release_time
plan_commitment_deadline
information_cutoff
execution_window_open
execution_window_close
external_proof_deadline
durability_completion_deadline
resolution_deadline
```

Stable context:

```text
genesis-schedule-derivation:{target_object_id}:{reference_period}:{schedule_artifact_sha256}
```

The evidence is supporting evidence, not an authority root. It must be reconstructed exactly and cross-bound to the exact TrustedManifest, its issuance-schedule policy, an admitted TargetDefinition, that target's admitted schedule SourceContract, the retained exact schedule artifact, the policy-selected `GENESIS_SCHEDULE_PARSER_V1`, and the retained exact tzdb artifact/version. Later R6 validation must replay parsing and calendar/time derivation; a sealed evidence object's assertions do not prove themselves.

### TargetInstance

Exact object type: `TargetInstance`.

Required payload fields:

```text
schema_version
trusted_manifest_ref
issuance_schedule_policy_ref
target_ref
schedule_source_ref
measurement_source_ref
schedule_derivation_evidence_ref
reference_period
release_identifier
outcome_information_barrier
information_cutoff
resolution_deadline
```

Stable context:

```text
genesis-target-instance:{target_object_id}:{reference_period}
```

The source refs must equal the schedule and measurement refs in the exact manifest-admitted TargetDefinition. The time and release fields must equal the exact replayed ScheduleDerivationEvidence outputs.

### ForecastSlot

Exact object type: `ForecastSlot`.

Required payload fields:

```text
schema_version
trusted_manifest_ref
issuance_schedule_policy_ref
target_instance_ref
schedule_derivation_evidence_ref
method_ref
source_contract_refs
information_cutoff
output_schema
selection_control_class
forecast_cardinality
```

Genesis v1 freezes exactly two sorted unique SourceContract refs, `output_schema = continuous_scalar_forecast_v1`, `selection_control_class = DETERMINISTIC_REPLAY`, and `forecast_cardinality = 1`.

Stable context:

```text
genesis-forecast-slot:{target_instance_object_id}:{method_object_id}
```

The method and both source contracts must be admitted by the exact TrustedManifest; the method must admit the exact target; and the cutoff and schedule-evidence refs must match the reconstructed TargetInstance cycle.

### IssuanceCyclePlan

Exact object type: `IssuanceCyclePlan`.

Required payload fields:

```text
schema_version
trusted_manifest_ref
schedule_policy_ref
schedule_derivation_evidence_ref
target_instance_ref
method_refs
information_cutoff
plan_commitment_deadline
execution_window_open
execution_window_close
external_proof_deadline
durability_completion_deadline
expected_slots
retry_policy_ref
omission_policy_ref
```

`method_refs` and `expected_slots` are non-empty sorted unique exact-ref arrays. The singular TargetInstance follows the frozen one-release-instance-per-cycle model. The schedule, target, method, slot, retry, and omission values are derived from exact manifest-bound authority; caller-provided `required_schedule_policy_ref` or `required_slots` is not authority.

Stable context:

```text
genesis-issuance-cycle-plan:{target_instance_object_id}
```

### IssuanceCycleManifest

Exact object type: `IssuanceCycleManifest`.

Required payload fields:

```text
schema_version
trusted_manifest_ref
cycle_plan_ref
retry_policy_ref
omission_policy_ref
correction_policy_ref
evaluation_policy_ref
slot_accounting
```

`slot_accounting` is sorted by exact `slot_ref`; every mandatory plan slot appears exactly once and duplicates are rejected. Every row requires:

```text
slot_ref
issuance_outcome
eligibility_state
withdrawal_state
attempt_refs
issued_forecast_refs
failure_record_refs
omission_evidence_refs
ineligibility_evidence_refs
unresolved_evidence_refs
withdrawal_refs
correction_refs
```

All row ref arrays are present even when empty, sorted, and duplicate-free. `issuance_outcome` distinguishes `EXPECTED`, `ISSUED`, `FAILED`, and `OMITTED`. `eligibility_state` separately distinguishes `NOT_YET_DETERMINED`, `ELIGIBLE`, `INELIGIBLE`, `UNRESOLVED`, and `NOT_APPLICABLE`. `withdrawal_state` separately distinguishes `ACTIVE` and `WITHDRAWN`.

An issued row retains at least one attempt and exactly one original issued forecast. A failed row retains attempts and failure records. An omitted row retains omission evidence. Ineligibility and unresolved states retain their respective evidence. Withdrawal requires additive withdrawal refs and does not remove the original forecast or attempts. Corrections are additive refs on an issued row and never replace the original forecast, slot, attempts, or accounting history.

Stable context:

```text
genesis-issuance-cycle-manifest:{cycle_plan_object_id}
```

This orthogonal accounting preserves the expected denominator plus issued, failed, omitted, ineligible, unresolved, and withdrawn classifications while retaining correction history. Evaluation aggregation remains outside this contract-freeze patch.

## Cycle-plan precommitment

The cycle plan binds:

```text
trusted_manifest_ref
schedule_policy_ref
schedule_derivation_evidence_ref
target_instance_ref
method_refs
information_cutoff
plan_commitment_deadline
execution_window_open
execution_window_close
external_proof_deadline
durability_completion_deadline
expected_slots
retry_policy_ref
omission_policy_ref
```

The plan must receive FPP_TIME_EVIDENCE_V1 deadline receipt quorum before `plan_commitment_deadline`.

The exact externally receipted plan hash must match the plan used at execution.

## Schedule changes before plan precommitment

If the official agency changes a release schedule before the plan is externally precommitted, a new schedule snapshot is captured and deterministic cycle derivation uses the updated official schedule.

The old snapshot remains retained as provenance.

## Schedule changes after plan precommitment

The frozen outcome information barrier is never moved later for an already precommitted cycle.

### Official release moved later

The original frozen barrier and all issuance deadlines remain unchanged.

The forecast can remain eligible if issued under the original rules. Resolution waits for the eventual first release under the frozen ResolutionRule.

### Official release moved earlier

If the new official release time is still later than the frozen barrier, the frozen earlier barrier remains controlling.

If the new official release time is earlier than the frozen barrier, the cycle becomes `SCHEDULE_ADVANCED_AFTER_PLAN`.

If detected before forecast execution, the planned slot receives the precommitted omission or invalidation treatment.

If a forecast has already been issued and the earlier release creates any possibility that outcome information became public before accepted time evidence completed, confirmatory eligibility fails closed.

The historical barrier cannot be shortened after observing a forecast merely to preserve eligibility.

### Unscheduled early publication

If outcome information is observably published before the frozen barrier, the cycle becomes `EARLY_OUTCOME_DISCLOSURE`.

Any forecast whose qualifying existence evidence did not complete before the actual defensible disclosure bound is ineligible.

## Government shutdown or agency disruption

A shutdown or disruption does not authorize an ad hoc schedule rewrite.

If an agency officially publishes a revised schedule before plan precommitment, the updated content-addressed schedule can be used.

After plan precommitment, the frozen barrier remains unchanged under the delay rule.

If the release is canceled or the required first-release statistic is not produced, the target resolves to the precommitted unresolved state.

## Missing schedule artifact

If the official schedule cannot be retrieved or archived with a verified content hash before `plan_commitment_deadline`, the cycle records `MISSING_SCHEDULE_ARTIFACT` and no forecast output is generated.

A manually remembered release date is not admissible.

## No forecast-informed schedule choice

Forecast values, model confidence, market movement, expected score, or prior model performance cannot influence target-instance inclusion, cutoff time, barrier, or cycle existence.

Any evidence that a mandatory release instance was skipped after output inspection invalidates confirmatory cohort accounting.