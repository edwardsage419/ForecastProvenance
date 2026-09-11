# Genesis Evaluation Policy

Version: 0.1 candidate
Status: GEN_001 REVIEW CANDIDATE

Policy ID: `policy:genesis-evaluation:v1`

## Scope

Genesis version 1 evaluates continuous scalar point forecasts only.

The policy does not claim probabilistic calibration, interval coverage, distributional skill, causal accuracy, or universal cross-domain forecast quality.

## Forecast output contract

Every confirmatory forecast uses:

```text
output_schema = continuous_scalar_forecast_v1
point_forecast_decimal = canonical decimal string
```

The forecast value is interpreted in the exact unit of its bound TargetDefinition.

No hidden extra precision is inferred from model internals or source databases.

## Resolution value

The authoritative outcome is the canonical decimal parsed from the frozen first-release official artifact under the target ResolutionRule and SourceContract.

The released display precision is authoritative for Genesis version 1.

Later revised values cannot replace the resolved outcome.

## Per-forecast metrics

For forecast value `f` and resolved outcome `y`:

```text
absolute_error = abs(f - y)
squared_error = (f - y)^2
```

Calculations use an exact decimal arithmetic implementation with a frozen precision and rounding contract. Binary floating point is not authoritative.

Metric outputs are canonical decimal strings.

## Transparent baseline comparison

Every confirmatory target-method forecast is paired with the bound transparent baseline defined in `GENESIS_BASELINE_METHOD.md`.

Derived baseline comparison fields are:

```text
absolute_error_delta = method_absolute_error - baseline_absolute_error
squared_error_delta = method_squared_error - baseline_squared_error
```

Negative delta means the method had lower error than the baseline for that forecast.

These deltas are descriptive evaluation outputs. They are not converted into a universal trust score.

## Cohort definition

A confirmatory evaluation cohort is generated from the accepted IssuanceCyclePlan and IssuanceCycleManifest rather than from a later list of successful forecasts.

Every expected slot remains accounted for with one of the precommitted terminal states.

Issued forecasts remain in cohort accounting after withdrawal unless the frozen CorrectionPolicy and EvaluationPolicy provide an independently observable pre-issuance exception.

Failed attempts, omitted slots, ineligible slots, unresolved outcomes, withdrawn forecasts, and anchor failures are retained in cohort accounting.

Only slots whose protocol-defined scoring status is `SCORABLE` contribute numerical error metrics.

## Non-scorable states

A slot can be non-scorable only under a precommitted reason such as:

```text
NO_VALID_FORECAST_ISSUED
TARGET_UNRESOLVED
PROSPECTIVE_ELIGIBILITY_FAILED
PROTOCOL_INVALIDATED
```

The non-scorable record remains in the denominator of operational completeness reporting.

A poor forecast outcome is never a valid non-scorable reason.

## Reporting denominators

Every evaluation report contains at least:

```text
expected_slots
issued_slots
prospective_eligible_slots
resolved_slots
scorable_slots
unresolved_slots
failed_slots
omitted_slots
withdrawn_slots
```

Counts are derived from immutable ledger objects and policies.

A score table without these denominators is incomplete for confirmatory reporting.

## Aggregation

### Within one target definition

For a declared cohort window, the project may report:

```text
mean_absolute_error
root_mean_squared_error
mean_absolute_error_delta_vs_baseline
mean_squared_error_delta_vs_baseline
```

The exact cohort start, end, target version, method version, baseline version, and number of scorable observations are always shown.

### Across target definitions

Genesis version 1 prohibits an authoritative single aggregate score across CPI monthly change, unemployment rate, and GDP annualized growth.

These outcomes have different scales, variances, release frequencies, and operational regimes.

A later protocol can introduce a normalized cross-target score only after its normalization rule is frozen prospectively and scientifically justified.

## Method comparison

Two methods are compared only on the intersection of target instances for which both methods had protocol-valid expected slots under compatible information cutoffs and source contracts.

Pairwise comparison cannot silently discard instances where one method failed to produce a forecast.

If method failure itself is scientifically relevant, it is reported separately as availability or execution failure rather than converted into a favorable scoring omission.

## Corrections and withdrawals

ForecastCorrection never edits a scored forecast value.

A substantive correction creates a replacement forecast under the frozen correction rule.

Evaluation treatment is determined from the policy that was active before issuance.

A withdrawal does not erase the original issued value or its cohort membership.

## Resolution corrections

If an official source artifact was parsed incorrectly, the original Resolution object remains retained and a correction record explains the parser or evidence error.

A corrected evaluation is a new versioned Evaluation record. Prior published evaluation records remain addressable and are never silently overwritten.

## Publication threshold

The project may publish individual resolved forecast results immediately after valid resolution.

Claims about comparative skill require a declared minimum sample count. Genesis version 1 sets no universal statistical significance threshold and must avoid claims of stable method superiority from a very small cohort.

The Trust Layer can establish protocol integrity before there is enough elapsed history to establish predictive skill.

## Frozen arithmetic requirements

Before Genesis acceptance, implementation tests must freeze:

1. Decimal parsing.
2. Subtraction and absolute value behavior.
3. Squaring precision.
4. Mean calculation precision.
5. Square-root calculation and rounding for RMSE.
6. Canonical decimal serialization.

Any arithmetic change capable of altering a reported metric requires a new EvaluationPolicy version.