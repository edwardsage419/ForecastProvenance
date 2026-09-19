# Genesis Official Source Contracts

Version: 0.1 candidate
Status: GEN_001 REVIEW CANDIDATE

These source contracts cover the initial target candidate set only.

## Shared rules

Every consequential HTTP artifact is represented by:

```text
source_contract_ref
requested_url
resolved_url
retrieved_at
http_status
content_type
raw_sha256
raw_artifact_ref
parser_version
```

Normative source content is the retained raw bytes or an exact content-addressed archival copy, not a later refetch of the same URL.

Redirect targets are recorded.

A parser never accepts an artifact solely because the hostname matches an official domain. Expected document identity, reference period, table labels, units, and release metadata must also validate.

## SC1 BLS CPI release schedule

Source contract ID:

```text
source:bls-cpi-release-schedule:v1
```

Primary URL:

```text
https://www.bls.gov/schedule/news_release/cpi.htm
```

Required parsed fields:

```text
reference_month
release_date
release_time
published_timezone = America/New_York
release_title = Consumer Price Index
```

The schedule artifact is captured before cycle-plan construction.

A later version of the page cannot replace the historical schedule snapshot.

## SC2 BLS CPI first-release outcome

Source contract ID:

```text
source:bls-cpi-first-release:v1
```

Discovery source:

```text
https://www.bls.gov/bls/news-release/cpi.htm
```

The archive index is used to locate the official archived release for the target reference month.

Required document checks:

1. Official BLS domain.
2. CPI release identity.
3. Reference month matches target instance.
4. Table 1 is present or an accepted equivalent official representation is present.
5. Row identity is `All items`.
6. Value is taken from seasonally adjusted percent change from the immediately preceding month.
7. Released precision is retained exactly as displayed.

Resolution stores the archived release artifact SHA256 and the extracted canonical decimal.

Current BLS database values and later releases cannot replace the archived first-release artifact.

## SC3 BLS Employment Situation release schedule

Source contract ID:

```text
source:bls-employment-situation-schedule:v1
```

Primary URL:

```text
https://www.bls.gov/schedule/news_release/empsit.htm
```

Required parsed fields:

```text
reference_month
release_date
release_time
published_timezone = America/New_York
release_title = Employment Situation
```

## SC4 BLS U-3 first-release outcome

Source contract ID:

```text
source:bls-u3-first-release:v1
```

Discovery source:

```text
https://www.bls.gov/bls/news-release/empsit.htm
```

Required document checks:

1. Official BLS domain.
2. Employment Situation release identity.
3. Reference month matches target instance.
4. Table A-1 is present or an accepted equivalent official representation is present.
5. Population scope is TOTAL.
6. Field is `Unemployment rate`.
7. Column is seasonally adjusted for the reference month.
8. Released precision is retained exactly as displayed.

Alternative U-1, U-2, U-4, U-5, U-6, unadjusted values, subgroup values, and later revised releases are rejected.

## SC5 BEA GDP release schedule

Source contract ID:

```text
source:bea-gdp-release-schedule:v1
```

Primary URL:

```text
https://www.bea.gov/news/schedule
```

Required parsed fields:

```text
reference_quarter
estimate_type = Advance Estimate
release_date
release_time
published_timezone = America/New_York
```

The exact schedule artifact is retained because BEA can revise release dates.

## SC6 BEA real GDP advance first-release outcome

Source contract ID:

```text
source:bea-real-gdp-advance:v1
```

Primary release family:

```text
https://www.bea.gov/news/
```

Required document checks:

1. Official BEA domain.
2. Release identifies `GDP (Advance Estimate)` for the target reference quarter.
3. Outcome is real GDP percent change from the preceding period.
4. The source corresponds to NIPA Table 1.1.1 or an official release representation of that exact measure.
5. The estimate is the Advance Estimate, not Second Estimate or Third Estimate.
6. Released precision is retained exactly as published.

The source contract must retain the original release artifact or an official BEA Data Archive artifact because later releases supersede current interactive values.

## Archive fallback rule

An official archive artifact is preferred when one exists.

If the primary official page is mutable and no archived byte artifact can be obtained, the resolver must obtain an independent second official representation such as an agency PDF, XLSX, API vintage, or Data Archive item.

If two official representations conflict materially, the outcome becomes `RESOLUTION_REVIEW_REQUIRED` under the frozen ResolutionEvidencePolicy. Operator preference cannot select the more favorable value.

## HTTP and transport metadata

TLS validity and successful HTTP retrieval are operational transport checks, not evidence that the page existed at the target release time.

For resolution provenance, the authoritative claim is that these exact official bytes were retrieved at the recorded retrieval time and match the frozen resolution rule.

Where the agency itself exposes publication timestamps or immutable archive identifiers, those fields are also retained.

## Source unavailability

If the official source cannot be retrieved by the resolution deadline:

1. attempt the precommitted official fallback sources in fixed order;
2. retain every failed attempt;
3. never switch to media or commercial sources unless the ResolutionRule already admitted them;
4. resolve to the precommitted unresolved state when evidence remains insufficient.