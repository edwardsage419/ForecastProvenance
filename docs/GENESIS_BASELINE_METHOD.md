# Genesis Transparent Baseline Method

Version: 0.1 candidate
Status: GEN_001 REVIEW CANDIDATE

Method ID: `method:last-observed-value:v1`

## Purpose

Genesis requires a transparent deterministic reference forecast for every initial target.

The baseline is intentionally simple. Its role is to make future method comparisons interpretable under the same point-in-time evidence rules.

## General algorithm

For target instance `t`:

1. Identify the immediately preceding reference period of the same target definition.
2. Locate the authoritative first-release outcome artifact for that preceding period under the target's frozen SourceContract.
3. Verify that the artifact was available by the current forecast information cutoff.
4. Parse the exact first-release value under the same canonical decimal and unit semantics used for resolution.
5. Emit that value unchanged as the baseline point forecast.

The method is deterministic and uses no randomness.

## Point-in-time rule

The baseline must use only a preceding-period first-release artifact whose defensible availability is at or before the current information cutoff.

A current historical database containing later revisions is not an admissible substitute.

If the required first-release artifact cannot be retrieved, hash verified, or shown to have been available by the cutoff, the baseline attempt is `INELIGIBLE_INPUT`.

The protocol does not reconstruct a missing first-release value from a later revised series.

## CPI baseline

Target:

```text
target:us-cpi-all-items-mom-sa:v1
```

Baseline value:

The seasonally adjusted monthly percent change in CPI-U all items from the archived first CPI release for the immediately preceding reference month.

Example semantic relation:

A forecast for the August reference-month CPI monthly change uses the first-release July monthly change when that July release was available by the August forecast information cutoff.

Later seasonal-adjustment revisions do not alter the baseline input.

## U-3 unemployment baseline

Target:

```text
target:us-unemployment-rate-u3-sa:v1
```

Baseline value:

The official seasonally adjusted U-3 unemployment rate from Table A-1 of the archived first Employment Situation release for the immediately preceding reference month.

Later population-control or seasonal revisions do not replace the first-release value.

## Real GDP advance baseline

Target:

```text
target:us-real-gdp-qoq-saar-advance:v1
```

Baseline value:

The real GDP percent change from preceding quarter published in the Advance Estimate for the immediately preceding reference quarter, provided that advance release was available by the current information cutoff.

Second Estimate, Third Estimate, annual update, and current interactive-table revisions are not admissible baseline inputs.

## EvidenceSnapshot binding

Each baseline run binds:

```text
method_ref
current_target_instance_ref
information_cutoff
preceding_target_instance_ref
preceding_first_release_source_contract_ref
preceding_release_artifact_ref
preceding_release_artifact_sha256
parsed_decimal_value
parser_version
```

The baseline forecast cannot be reproduced from a semantic target ID alone.

## Method output

Output schema:

```text
continuous_scalar_forecast_v1
```

Output field:

```text
point_forecast_decimal
```

The output is exactly the canonical decimal parsed from the admissible preceding first-release artifact.

## Failure handling

The method fails closed when:

1. the immediately preceding target period cannot be determined;
2. the first-release artifact is unavailable;
3. source identity or artifact hash cannot be verified;
4. the artifact became available after the current information cutoff;
5. the parser cannot uniquely identify the required target field;
6. the parsed value violates the target unit or decimal contract.

A failed baseline attempt remains in attempt accounting.

## No fallback to a different baseline

Genesis version 1 does not switch from last-observed-value to mean, median, consensus, market, or another baseline because the required artifact is inconvenient or produces an unfavorable comparison.

A future additional baseline is a separately versioned ForecastMethod bound before its prospective cohort begins.

## Baseline scientific interpretation

Beating this baseline can show improvement relative to a persistence-style reference under the same target semantics and evidence cutoff.

It does not by itself establish broad forecasting skill, causal insight, calibration, or superiority to professional consensus forecasts.

## Implementation gate

Before Genesis acceptance, synthetic and archived non-production fixtures must demonstrate:

1. exact first-release artifact selection;
2. rejection of a later revised artifact;
3. information-cutoff enforcement;
4. target-specific parser binding;
5. deterministic output reproduction;
6. fail-closed behavior when the first-release artifact is missing or ambiguous.