# Issuance Completeness, Retry, Correction, and Withdrawal Policy

Version: 0.3 candidate
Status: FTC_001 FREEZE CANDIDATE

## Cycle precommitment

Every confirmatory issuance cycle begins with an immutable `IssuanceCyclePlan`.

The plan fixes the execution window, expected slots, exact target and method bindings, output schema, forecast cardinality, information cutoff, retry policy, omission policy, plan commitment deadline, and forecast external proof deadline.

The exact plan must have accepted external existence evidence satisfying:

```text
verified_plan_existence_bound <= plan_commitment_deadline <= execution_window_open
```

The protocol does not use local attempt start timestamps to prove precommitment ordering.

Any substantive plan change creates a new plan and requires a new external precommitment. A changed plan cannot inherit the prior plan proof.

## Expected slots

Version 1 uses one forecast artifact per slot.

Each slot binds:

```text
slot_id
target_instance_ref
method_ref
output_schema_ref
forecast_horizon
evidence_contract_refs
forecast_cardinality = 1
```

Every slot must later appear exactly once in cycle accounting.

## Retry policy

Each slot has a precommitted maximum attempt count.

Retries are permitted only for enumerated failure codes independent of forecast desirability.

The policy fixes maximum attempts, retry eligible failures, randomness handling, infrastructure timeout treatment, exhausted retry treatment, and the issuance eligible success selection rule.

Default rule: the first successful attempt reached under the precommitted retry algorithm is issuance eligible.

Every attempt is retained and referenced by the cycle manifest.

## Omission policy

A planned slot cannot disappear.

An omission requires a reason code admitted by the precommitted OmissionPolicy and evidence required by that policy. Operator discretion after inspecting a prediction is prohibited.

## Cycle manifest

The immutable `IssuanceCycleManifest` accounts for every expected slot, every attempt, every issued forecast, and every permitted omission.

Its own final `content_sha256` is the anchor subject. No `anchor_subject_hash` is embedded in the manifest.

## Correction policy

ForecastCorrection records facts and references the applicable CorrectionPolicy. It does not select its own scoring consequence.

Probability, target, horizon, method, information cutoff, substantive evidence, or resolution rule changes require a new forecast object.

## Withdrawal policy

Withdrawal never deletes or rewrites the issued forecast.

Default confirmatory rule: an issued forecast remains in its original confirmatory cohort after withdrawal.

Any exception must be precommitted in EvaluationPolicy and CorrectionPolicy before issuance, depend on independently observable conditions unrelated to forecast desirability, and remain auditable.

## Prospective eligibility

A confirmatory prospective forecast requires an accepted trusted manifest, valid externally precommitted cycle plan, complete slot and attempt accounting, valid point in time evidence, immutable issued forecast, and accepted external existence proof for the cycle manifest satisfying the frozen external proof deadline.

Prospective eligibility is derived by ValidationReport and is never asserted by the forecast payload.