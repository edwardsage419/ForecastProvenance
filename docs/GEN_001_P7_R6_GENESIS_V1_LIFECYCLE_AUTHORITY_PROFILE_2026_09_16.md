# GEN_001 P7 R6 Genesis v1 Lifecycle Authority Profile — 2026-09-16

Status: PRE-GENESIS IMPLEMENTATION DESIGN CANDIDATE
Classification: NON_FORECAST_REVIEW
Prospective eligible: false
Network authorization: none

This profile defines the smallest successor machine contract required to close the non-temporal side of R6 for the initial Genesis v1 profile. It does not reinterpret historical objects, freeze candidate v0.7, authorize Genesis, qualify a provider, or permit a positive confirmatory claim before all authority layers below are implemented and regression-tested.

## Scope compression

The initial Genesis v1 profile is intentionally narrow:

- one official target release instance per issuance cycle;
- one admitted method: `method:last-observed-value:v1`;
- one expected slot per cycle;
- deterministic replay selection control;
- no fitted state;
- no public randomness;
- no closed-model execution;
- no externally audited attempt set;
- at most two forecast attempts under `policy:genesis-retry:v1`;
- point forecast output only.

A successor manifest that adds a second method, stochastic execution, fitted state, probabilistic output, or a different selection-control class requires a successor lifecycle authority profile rather than silently widening this one.

## Why this profile is required

The historical generic `issuance_cycle_plan.schema.json` and `core.validate_cycle_plan` do not bind the full Genesis schedule/lifecycle contract. Positive `CONFIRMATORY_PROSPECTIVE_ELIGIBLE` therefore cannot rely on those historical helpers alone.

R6 requires the authoritative validator to reconstruct, from exact retained inputs and manifest-bound authority:

1. the mandatory target instance;
2. its frozen schedule and outcome-information barrier;
3. the exact cycle plan and sole expected slot;
4. the point-in-time baseline evidence snapshot;
5. the complete retry/attempt chain;
6. the deterministic baseline output;
7. the immutable IssuedForecast;
8. complete cycle-manifest accounting;
9. the required separated temporal/durability claims;
10. the final confirmatory eligibility state.

Caller-supplied booleans, reason codes, precomputed `VERIFIED` states, or arbitrary required-slot refs are not authority.

## Dynamic machine objects

The following are successor Genesis-v1 dynamic contracts. Exact field-set validation belongs in the manifest-bound ValidatorContract implementation. Historical generic validators remain unchanged.

### SourceArtifactEvidence

Exact substantive fields:

```text
source_contract_ref
resolved_url
retrieved_at
http_status
raw_sha256
raw_artifact_ref
```

The validator must receive the retained raw bytes separately, recompute SHA256, require equality with `raw_sha256`, validate the URL/host and HTTP result under the exact manifest-admitted SourceContract, and use `retrieved_at` only as project retrieval evidence. It must not convert retrieval time into a claim about an earlier historical availability time.

For initial Genesis operation, the preceding first-release baseline artifact is retrieved and retained before the forecast information cutoff. Therefore a successful project retrieval at or before cutoff is sufficient to establish that this exact retained artifact was available to the project by cutoff. A later retrieval cannot be backdated.

### ScheduleSnapshot

Exact substantive fields:

```text
schedule_source_contract_ref
source_artifact_evidence_ref
parsed_release_identifier
reference_period
published_release_date
published_release_time
published_timezone
parser_version
```

The raw official schedule bytes are retained through `SourceArtifactEvidence`.

The schedule parser must deterministically reproduce these parsed fields from those bytes. A caller-provided parsed release date/time is not authority.

### TargetInstance

Exact substantive fields:

```text
target_definition_ref
resolution_rule_ref
schedule_snapshot_ref
reference_period
outcome_information_barrier
```

The target definition and resolution rule must be admitted by the exact TrustedManifest. The reference period must equal the schedule snapshot reference period. The outcome-information barrier must be deterministically derived from the parsed official schedule time under the frozen `America/New_York` timezone rule and the applicable schedule policy.

### IssuanceCyclePlan

Exact substantive fields:

```text
trusted_manifest_ref
schedule_policy_ref
schedule_snapshot_ref
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

For the initial Genesis profile:

```text
method_refs = [exact method:last-observed-value:v1 ref]
len(expected_slots) = 1
plan_commitment_deadline = barrier - 8 calendar days
information_cutoff = barrier - 7 calendar days
execution_window_open = barrier - 7 calendar days
execution_window_close = barrier - 6 calendar days
external_proof_deadline = barrier - 24 hours
durability_completion_deadline = barrier
```

The exact plan remains a direct wall-clock subject whose plan-existence deadline is `plan_commitment_deadline`.

### Slot

Exact substantive fields:

```text
target_instance_ref
method_ref
output_schema
forecast_horizon
selection_control_class
forecast_cardinality
```

Initial Genesis values are constrained to:

```text
method_ref = exact manifest-admitted baseline method ref
output_schema = continuous_scalar_forecast_v1
selection_control_class = DETERMINISTIC_REPLAY
forecast_cardinality = 1
```

The slot is derived from the manifest-admitted target/method pair and schedule policy. It is not caller-selected after output inspection.

### EvidenceSnapshot

The initial baseline method uses a compressed method-specific snapshot rather than dormant fitted-state/randomness interfaces.

Exact substantive fields:

```text
method_ref
current_target_instance_ref
information_cutoff
preceding_target_instance_ref
preceding_first_release_source_contract_ref
preceding_source_artifact_evidence_ref
parsed_decimal_value
parser_version
```

Authority requires:

- the exact source contract is manifest-admitted and is the frozen first-release source for the target;
- the exact source artifact evidence binds retained raw bytes;
- project retrieval completed at or before `information_cutoff`;
- the preceding target period is deterministically the immediately preceding period of the same target definition;
- the target-specific parser rerun over the retained raw bytes reproduces `parsed_decimal_value`;
- later revised artifacts are not substituted.

### ForecastRunAttempt

Exact substantive fields:

```text
method_ref
target_instance_ref
slot_ref
information_cutoff
evidence_snapshot_refs
runtime_configuration_ref_or_none
randomness_evidence_ref_or_none
retrieval_log_ref_or_none
terminal_status
failure_code_or_none
output_artifact_ref_or_none
attempt_sequence
retry_of_or_none
issuance_eligible
```

Genesis baseline constraints:

- `runtime_configuration_ref_or_none = NONE` unless a separately frozen configuration object is later introduced;
- `randomness_evidence_ref_or_none = NONE`;
- retrieval authority is carried by the exact bound evidence snapshot/source artifact evidence, so no opaque external retrieval-log assertion may replace those bytes;
- attempt sequence begins at 1 and follows `policy:genesis-retry:v1`;
- no more than two attempts;
- retry is allowed only after a frozen retry-eligible failure;
- the first successful attempt is the only issuance-eligible success;
- later successes cannot be cherry-picked.

Local `started_at`/`ended_at` are operational metadata and are not part of this authoritative field set.

### IssuedForecast

Exact substantive fields:

```text
target_instance_ref
resolution_rule_ref
method_ref
successful_attempt_ref
evidence_snapshot_refs
information_cutoff
forecast_horizon
point_forecast_decimal
claimed_issuance_time
cycle_plan_ref
correction_policy_ref
retry_policy_ref
trusted_manifest_ref
```

The forecast contains no prospective flag and no mutable trust state.

For the deterministic baseline, authoritative replay must reproduce exactly `point_forecast_decimal` from the bound EvidenceSnapshot and retained source bytes. A stored replay boolean is insufficient.

### IssuanceCycleManifest

Exact substantive fields:

```text
cycle_plan_ref
slot_accounting
```

Initial Genesis requires exactly one accounting row for the one expected slot. Each row binds:

```text
slot_ref
attempt_refs
outcome
issued_forecast_ref_or_none
omission_code_or_none
failure_code_or_none
```

The row must contain the complete attempt chain for the slot. `ISSUED` requires exactly one forecast ref and the exact issuance-eligible successful attempt. Failed/omitted states remain visible and cannot be deleted from the denominator.

The exact cycle manifest is the direct forecast-deadline wall-clock subject. An IssuedForecast inherits that deadline only through validated exact membership in the complete slot accounting.

## Manifest-derived authority

A new lifecycle authority context must be derived from the exact sealed TrustedManifest rather than caller inputs. It must supply at least:

```text
trusted_manifest_ref
target_refs
resolution_rule_refs
method_refs
source_contract_refs
issuance_schedule_policy_ref
retry_policy_ref
omission_policy_ref
correction_policy_ref
```

The existing temporal/provider authority context remains unchanged. This avoids breaking historical P5 authority surfaces while adding a separate successor lifecycle authority root.

## Authoritative validation order

Positive confirmatory authority must execute in this order:

1. derive exact lifecycle authority refs from TrustedManifest;
2. validate/replay retained schedule source artifact;
3. derive ScheduleSnapshot and TargetInstance semantics;
4. deterministically derive all cycle deadlines and the sole required slot;
5. validate the exact externally precommitted IssuanceCyclePlan and recompute its temporal claims;
6. validate/replay the retained preceding first-release source artifact;
7. recompute the baseline EvidenceSnapshot parsed value and point-in-time eligibility;
8. validate the complete attempt chain and first-success rule;
9. deterministically replay the baseline prediction;
10. validate the immutable IssuedForecast against the successful attempt, slot, plan, policies and replayed prediction;
11. validate complete IssuanceCycleManifest accounting;
12. recompute the cycle-manifest deadline/existence and durability claims from exact retained evidence;
13. only if every required non-temporal check and required separated claim is authoritative and passing, derive `CONFIRMATORY_PROSPECTIVE_ELIGIBLE = VERIFIED`.

Any missing authority input produces `UNRESOLVED` or the applicable fail-closed state. No caller-selected hard-invalidation list is accepted as authority.

## Implementation staging

R6 is split into three implementation subgates:

```text
R6-A = exact lifecycle object/profile gate
R6-B = schedule/source/parser deterministic replay authority
R6-C = high-level manifest-rooted confirmatory orchestration
```

The existing `FULL_TRUST_CORE_CHECK_AUTHORITY_NOT_IMPLEMENTED` downgrade remains in force until all three subgates pass focused regression, adversarial regression and fresh exact-head P6.

## Candidate/version consequence

This profile does not itself add a new normative candidate object and therefore does not require candidate v0.8 solely for field-contract implementation. The final TrustedManifest/ValidatorContract must bind the exact successor validator/schema/source closure before Genesis acceptance.

If implementation reveals that a candidate policy must change, that change requires a successor candidate patch rather than silently altering v0.7 semantics.

## Current blockers identified

At the time this profile is written:

- R6-A is not yet implemented;
- deterministic production schedule parsing from retained official schedule bytes must be confirmed or implemented for R6-B;
- deterministic baseline replay exists partially in `genesis_sources.py`, but must be connected to exact retained SourceArtifactEvidence and manifest-bound SourceContracts;
- R6-C remains prohibited until R6-A and R6-B are authoritative.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production qualified provider count = 0
PRODUCTION_QUALIFIED = NO
AUTHORITATIVE_CONFIRMATORY_VERIFIED = PROHIBITED
network_authorized = false
```
