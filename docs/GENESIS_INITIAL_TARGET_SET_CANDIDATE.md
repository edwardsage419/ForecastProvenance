# Genesis Initial Target Set Candidate

Version: 0.1 candidate
Status: GEN_001 TARGET REVIEW CANDIDATE

No forecast values may be generated from this document. Target selection is based on source quality, timing clarity, resolution reproducibility, and low operational cost.

## Candidate set

Genesis version 1 candidate set contains three U.S. official macroeconomic targets.

All three are continuous scalar outcomes, have scheduled official release times, have public first release material, and can be resolved from archived official releases.

## T1 CPI all items monthly change

Candidate target ID:

```text
target:us-cpi-all-items-mom-sa:v1
```

Outcome:

Seasonally adjusted percent change from the preceding month in CPI-U, U.S. city average, all items, for the reference month.

Primary authority:

U.S. Bureau of Labor Statistics Consumer Price Index release.

Resolution location:

CPI Table 1, row `All items`, column for the reference month under seasonally adjusted percent change from the immediately preceding month.

Reference series identity:

The BLS seasonally adjusted CPI-U U.S. city average all-items family corresponds to the CPI series coding system using CPI-U, seasonally adjusted, U.S. city average, all items.

Vintage rule:

Resolve on the value displayed in the archived first CPI news release for the reference month. Later seasonal-factor revisions do not replace the first-release outcome.

Outcome information barrier:

The scheduled BLS CPI release time from the frozen official release schedule snapshot.

Schedule handling:

If BLS officially moves the release earlier before cycle-plan precommitment, the deterministic schedule policy uses the updated official time.

After the cycle plan has been externally precommitted, the frozen outcome information barrier is never extended. If an official change creates possible disclosure before the frozen issuance safety requirements can be met, the slot is omitted or becomes ineligible under the precommitted schedule policy.

Current 2026 schedule evidence shows BLS CPI releases at 08:30 AM Eastern Time and publishes upcoming reference-month release dates.

## T2 Official unemployment rate

Candidate target ID:

```text
target:us-unemployment-rate-u3-sa:v1
```

Outcome:

Official U-3 unemployment rate for the reference month, seasonally adjusted, percentage of the civilian labor force.

Primary authority:

U.S. Bureau of Labor Statistics Employment Situation release using Current Population Survey household data.

Resolution location:

Employment Situation Table A-1, TOTAL, seasonally adjusted `Unemployment rate` for the reference month.

Semantic rule:

U-3 is the official unemployment rate. It is the total number of unemployed people as a percentage of the civilian labor force.

Vintage rule:

Resolve on the value displayed in the archived first Employment Situation news release for the reference month. Later annual seasonal adjustment revisions do not replace the first-release outcome.

Outcome information barrier:

The scheduled BLS Employment Situation release time from the frozen official release schedule snapshot.

Schedule handling:

Use the same frozen-barrier and early-reschedule rule as T1.

Current 2026 schedule evidence shows Employment Situation releases at 08:30 AM Eastern Time with upcoming dates published by BLS.

## T3 Real GDP advance estimate growth

Candidate target ID:

```text
target:us-real-gdp-qoq-saar-advance:v1
```

Outcome:

Percent change from the preceding quarter in real U.S. gross domestic product, seasonally adjusted annual rate, as published in the BEA Advance Estimate for the reference quarter.

Primary authority:

U.S. Bureau of Economic Analysis GDP Advance Estimate release.

Resolution location:

BEA National Income and Product Accounts Table 1.1.1, Percent Change From Preceding Period in Real Gross Domestic Product, using the value associated with the Advance Estimate release for the reference quarter.

Vintage rule:

Resolve on the Advance Estimate first-release value. Second Estimate, Third Estimate, annual updates, and later revisions never replace the resolved Genesis outcome.

Archive rule:

Retain or reproducibly reference the BEA release and Data Archive artifact that preserves the advance vintage because the interactive current table is later superseded.

Outcome information barrier:

The scheduled BEA Advance Estimate release time from the frozen official release schedule snapshot.

Current 2026 schedule evidence lists the third-quarter 2026 Advance Estimate for October 29, 2026 at 08:30 AM.

Schedule handling:

BEA may revise release schedules. The schedule snapshot and frozen-barrier policy therefore apply exactly as for BLS targets.

## Shared output schema

Genesis candidate output schema:

```text
continuous_scalar_forecast_v1
```

Required prediction field:

```text
point_forecast_decimal
```

The value is a canonical decimal string in the target unit.

Probabilistic distributions and quantile forecasts are deferred to a later protocol version. Genesis first establishes trustworthy provenance and complete cohort accounting with the smallest scientifically interpretable output surface.

## Candidate evaluation policy

Primary per-forecast metrics:

```text
absolute_error
squared_error
```

Both are retained. No opaque composite score is created.

Cross-target aggregation must normalize or remain target-specific because CPI monthly percent change, unemployment rate, and GDP annualized growth have different scales and error distributions.

Initial public reporting should therefore emphasize target-specific error histories and baseline deltas rather than a single universal leaderboard.

## Baseline requirement

Every target requires at least one deterministic transparent baseline frozen before first issuance.

Candidate baseline family:

```text
method:last-observed-value:v1
```

The baseline uses the most recent admissible previously published value of the same target statistic available by the information cutoff.

For GDP, the previous reference quarter's latest admissible growth estimate under the frozen baseline source rule is used. The exact vintage source must be frozen before Genesis.

A target-specific historical mean or median baseline may be added only when its fitting window and point-in-time data contract are frozen and reproducible.

## Forecast horizon and issuance cadence

The initial cadence is one forecast per target-method pair per official release cycle.

The information cutoff is selected at least seven calendar days before the frozen outcome information barrier.

The external proof deadline is no later than 24 hours before the outcome information barrier.

No ad hoc extra forecast may be inserted after seeing later information.

## Why these targets

The candidate set is deliberately narrow:

1. Two independent official agencies.
2. Monthly and quarterly cadence rather than high frequency operation.
3. Public release schedules.
4. Archived or archivable first-release outcomes.
5. Numeric outcomes with simple resolution semantics.
6. No paid outcome data.
7. Sufficient time for multi-provider receipt quorum and OTS completion.

## Remaining target review blockers

Before this target set can enter the Genesis manifest:

1. Freeze exact SourceContract URLs and archive procedures.
2. Freeze exact schedule snapshot acquisition and hash rules.
3. Confirm time-zone and daylight-saving conversion rules without local-clock ambiguity.
4. Define unexpected early-release and government-shutdown handling as machine-testable schedule policy.
5. Freeze exact baseline method source-vintage rules.
6. Execute target-specific adversarial cases for revisions, rescheduling, archived release mutation, and missing release artifacts.

This document selects a candidate set only. It does not authorize production forecasting.