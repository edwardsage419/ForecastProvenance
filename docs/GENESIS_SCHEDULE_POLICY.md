# Genesis Issuance Schedule Policy

Version: 0.2 candidate
Status: GEN_001 REVIEW CANDIDATE

Policy ID: `policy:genesis-issuance-schedule:v1`

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

For outcome information barrier `B`, Genesis version 1 derives:

```text
plan_commitment_deadline = B - 8 calendar days
information_cutoff = B - 7 calendar days
execution_window_open = B - 7 calendar days
execution_window_close = B - 6 calendar days
external_proof_deadline = B - 24 hours
durability_completion_deadline = B
```

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

## Cycle-plan precommitment

The cycle plan binds:

```text
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