# Genesis Evaluation Policy

Version: 0.2 candidate
Status: GEN_001 ARCHITECTURE COMPRESSION P5

Policy ID: `policy:genesis-evaluation:v2`

## Scope

Genesis v1 evaluates continuous scalar point forecasts only. The sole admitted initial method is `method:last-observed-value:v1`.

Genesis v1 does not make normative claims about probabilistic calibration, interval coverage, distributional skill, statistical significance, method superiority, or a universal cross-target score.

## Normative per-forecast output

For forecast value `f` and resolved first-release outcome `y`, the normative numerical evaluation surface is exactly:

```text
resolved_outcome
forecast_value
absolute_error
squared_error
```

with:

```text
absolute_error = abs(f - y)
squared_error = (f - y)^2
```

Authoritative arithmetic uses canonical decimal semantics. Binary floating point is not authoritative.

## Baseline and method-comparison rule

The only Genesis v1 method is itself the historical transparent persistence baseline. Comparing it with itself would produce tautological zero deltas.

Genesis v1 therefore does not define normative:

```text
absolute_error_delta
squared_error_delta
mean_absolute_error_delta_vs_baseline
mean_squared_error_delta_vs_baseline
pairwise_method_comparison
```

A distinct second method or forecast class may introduce comparison through a successor EvaluationPolicy and successor manifest. Historical Genesis evaluation is never reinterpreted under that later policy.

## Aggregation rule

Genesis v1 normative evaluation does not require MAE, RMSE, cross-target aggregation, significance tests, or leaderboard ranking.

Those reports may be added later only after their cohort and arithmetic semantics are prospectively versioned. Per-forecast absolute and squared error remain sufficient for the minimum Genesis scientific record.

## Cohort integrity

The evaluation cohort is derived from deterministic expected slots and immutable lifecycle records rather than a later list of successful forecasts.

At minimum reporting preserves these denominator classes:

```text
expected
issued
failed
omitted
ineligible
unresolved
withdrawn
```

A poor outcome is never a valid reason to remove a slot from the denominator.

Withdrawals and substantive corrections do not erase the original issued forecast or its historical cohort membership.

## P2 temporal claim reporting

Temporal and durability state is not collapsed into a generic nonscorable label.

Evaluation/reporting must retain or reconstruct the independent claim vector:

```text
EXTERNAL_EXISTENCE_BOUND_VERIFIED
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

with states:

```text
VERIFIED
FAILED
UNRESOLVED
NOT_APPLICABLE
```

A later durability failure does not rewrite a previously verified deadline-existence fact.

Only `CONFIRMATORY_PROSPECTIVE_ELIGIBLE = VERIFIED` permits inclusion in the strong confirmatory prospective cohort. Failed and unresolved slots remain visible in denominator reporting.

## Resolution rule

The authoritative outcome remains the canonical decimal parsed from the frozen first-release official artifact under the target ResolutionRule and SourceContract.

`REVIEW_REQUIRED` and `UNRESOLVED` do not authorize owner value selection under compressed Genesis v1. An unresolved outcome remains visible and has no numerical error score until deterministically resolved under an admitted rule.

## Corrections

A ForecastCorrection never edits historical forecast or evaluation bytes.

A substantive forecast replacement is a new IssuedForecast. A resolution/parser correction creates a new versioned Resolution/Evaluation record while retaining the prior record and reason evidence.

## Successor boundary

The following surfaces are explicitly deferred:

```text
baseline delta
pairwise method comparison
MAE/RMSE normative aggregation
probabilistic scoring
calibration
significance claims
leaderboards
cross-target universal score
```

Introducing any of them requires a new versioned EvaluationPolicy when an actual scientific use case exists.
