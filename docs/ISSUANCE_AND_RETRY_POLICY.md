# Issuance Completeness, Retry, Correction, and Withdrawal Policy

Version: 0.2 candidate
Status: FTC_001 REMEDIATION CANDIDATE

## Precommitment

Every confirmatory issuance cycle begins with an IssuanceCyclePlan committed before eligible forecast outputs are inspected.

The plan fixes expected slots, target and method bindings, information cutoff, retry policy, omission policy, and external proof deadline.

A later cycle manifest must account for every planned slot.

## Retry policy

Each method and slot has a precommitted maximum attempt count.

Retries are permitted only for enumerated failure codes that are independent of forecast desirability.

The policy must define:

1. maximum attempts.
2. retry eligible failure codes.
3. whether randomness is reused or deterministically advanced.
4. which successful attempt is issuance eligible.
5. infrastructure timeout treatment.
6. treatment when the retry budget is exhausted.

Default selection rule: the first successful attempt reached under the precommitted retry rule is issuance eligible. A later success cannot replace it because its forecast is more desirable.

Every attempt is retained and bound into cycle accounting.

## Omission policy

A planned slot cannot disappear.

An omission requires a precommitted reason code. Operator discretion after inspecting a prediction is prohibited.

## Correction policy

ForecastCorrection records facts. It does not choose its own scoring treatment.

The active trusted manifest binds a CorrectionPolicy. Evaluation derives scoring consequences from that precommitted policy.

Probability, target, horizon, method, information cutoff, substantive evidence, or resolution rule changes require a new forecast object.

## Withdrawal policy

Withdrawal never deletes or rewrites the issued forecast.

Default confirmatory rule: an issued forecast remains in its original confirmatory cohort after withdrawal.

A protocol may define a narrower exception only before issuance and only for an independently observable reason unrelated to forecast performance. The exception and evidence requirements must be bound in the trusted manifest.

## Prospective classification

Prospective eligibility is derived by validation. It is never asserted by an IssuedForecast field.

A confirmatory forecast requires:

1. an accepted trusted manifest.
2. a valid precommitted cycle plan.
3. complete slot and attempt accounting.
4. valid point in time evidence.
5. an immutable issued forecast.
6. an accepted external existence proof satisfying the target's external proof deadline.
