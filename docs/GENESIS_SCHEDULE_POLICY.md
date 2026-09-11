# Genesis Issuance Schedule Policy

Version: 0.1 candidate
Status: GEN_001 REVIEW CANDIDATE

Policy ID: `policy:genesis-issuance-schedule:v1`

## Purpose

The schedule policy prevents operator discretion over which target instances enter a cycle and prevents release-time changes from being handled retrospectively.

## Schedule source

Each target definition identifies an official release-calendar source contract.

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

The raw official schedule artifact is retained or content addressed.

## Time-zone conversion

All normative cycle times are stored as UTC whole-second timestamps.

An official local release time is converted to UTC using an IANA time-zone identifier frozen in the target schedule contract, such as `America/New_York`.

A fixed numeric UTC offset is prohibited for recurring targets that can cross daylight-saving transitions.

The conversion library and time-zone database version are recorded in the schedule derivation report.

If the local time is ambiguous or nonexistent under the frozen time-zone rules, cycle construction fails closed.

## Cycle instance generation

For each accepted target definition, the schedule policy deterministically selects the next official release instance whose outcome information barrier is far enough in the future to satisfy:

```text
information_cutoff <= outcome_information_barrier - 7 calendar days
external_proof_deadline <= outcome_information_barrier - 24 hours
```

Version 1 creates exactly one expected slot for each accepted target-method pair.

Operators cannot remove an inconvenient target or add an unscheduled target after observing method outputs.

## Cycle-plan precommitment

The cycle plan binds:

```text
schedule_policy_ref
schedule_snapshot_refs
target_instance_refs
method_refs
information_cutoff
plan_commitment_deadline
execution_window_open
execution_window_close
external_proof_deadlines
expected_slots
retry_policy_ref
omission_policy_ref
```

The plan must receive FPP_TIME_EVIDENCE_V1 deadline receipt quorum before `plan_commitment_deadline`.

The execution window opens only after the precommitment deadline and after successful plan evidence validation.

## Schedule changes before plan precommitment

If the official agency changes a release schedule before the plan is externally precommitted, a new schedule snapshot is captured and deterministic cycle derivation uses the updated official schedule.

The old snapshot remains retained as provenance.

## Schedule changes after plan precommitment

The frozen outcome information barrier is never moved later for an already precommitted slot.

### Official release moved later

The original frozen barrier and all issuance deadlines remain unchanged.

The forecast can remain eligible if it was issued under the original rules. Resolution waits for the eventual first release subject to the frozen ResolutionRule.

### Official release moved earlier

If the new official release time is still later than the frozen outcome information barrier, the frozen earlier barrier remains controlling.

If the new official release time is earlier than the frozen barrier, the slot becomes `SCHEDULE_ADVANCED_AFTER_PLAN`.

If detection occurs before forecast execution, the slot is omitted under the precommitted omission rule.

If a forecast has already been issued and the earlier release creates any possibility that outcome information became public before the accepted forecast time evidence completed, confirmatory eligibility fails closed.

The operator cannot shorten the historical barrier after seeing the forecast value merely to preserve eligibility.

### Unscheduled early publication

If outcome information is observably published before the frozen barrier, the slot becomes `EARLY_OUTCOME_DISCLOSURE`.

Any forecast whose deadline evidence did not complete before the actual observed disclosure time is ineligible.

Because discovery time can differ from publication time, initial Genesis targets are admitted only when early publication is sufficiently rare and official release artifacts expose a defensible publication timestamp or other review evidence.

## Government shutdown or agency disruption

A shutdown or disruption does not authorize an ad hoc schedule rewrite.

If an agency officially publishes a revised schedule before plan precommitment, the updated schedule can be used.

After plan precommitment, the frozen barrier remains unchanged under the delay rule.

If the release is canceled or the required first-release statistic is not produced, the target resolves to the precommitted unresolved state.

## Missing schedule artifact

If the official schedule cannot be retrieved or archived with a verified content hash before cycle-plan construction, that target instance is omitted before outputs are generated.

A manually remembered release date is not admissible.

## No forecast-informed schedule choice

Forecast values, model confidence, market movement, or expected score cannot influence schedule snapshot selection, target instance inclusion, cutoff time, or release barrier.

Any evidence that schedule choices were made after output inspection invalidates the cycle for confirmatory accounting.