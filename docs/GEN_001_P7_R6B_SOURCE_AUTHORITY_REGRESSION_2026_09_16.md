# GEN_001 P7 R6-B Source Authority Regression

Date: 2026-09-16
Status: REGRESSION CONFIRMED ON EXACT IMPLEMENTATION HEAD
Classification: NON_FORECAST_REVIEW
Prospective eligible: false
Network authorization: none

## Exact tested repository state

```text
repository = edwardsage419/ForecastProvenance
branch = design/p7-v4-r6
exact_tested_head = 15c4cbaa53fe9c84b56293b5022510f28378a281
working_tree = clean
```

The user executed the regression from a detached clean worktree after confirming `origin/design/p7-v4-r6` exactly matched the expected HEAD.

## Execution results

```text
compileall = PASS
R6-B source authority = 31 passed
R6-A lifecycle regression = 13 passed
v0.7 candidate regression = 28 passed, 70 subtests passed
existing confirmatory fail-closed / claim-authority regression = 37 passed
full repository pytest = 442 passed, 188 subtests passed
git diff --check = PASS
working tree after tests = clean
historical candidate byte check v0.2-v0.6 = PASS
historical_candidate_diff_exit = 0
```

The historical byte check compared the tested implementation HEAD against `48010436ab234dca012810ba1c0154e1f2aec9e5` for:

```text
genesis/candidate/objects/candidate_object_set_v0_2.json
genesis/candidate/objects/candidate_patch_v0_3.json
genesis/candidate/objects/candidate_patch_v0_4.json
genesis/candidate/objects/candidate_patch_v0_5.json
genesis/candidate/objects/candidate_patch_v0_6.json
```

No differences were observed.

## What this closes

R6-B deterministic schedule/source/baseline replay authority is regression-confirmed for the tested HEAD.

The focused source-authority regression covers the initial Genesis target set and includes:

- retained raw-byte SHA256 binding;
- exact SourceContract and allowed-host binding;
- CPI and Employment Situation BLS schedule parsing;
- BEA GDP Advance Estimate schedule parsing;
- duplicate/ambiguous schedule rejection;
- America/New_York schedule time to UTC barrier derivation;
- calendar-day deadline derivation across DST transitions;
- immediately preceding month/quarter derivation;
- CPI, U-3 and real-GDP target-specific first-release replay;
- baseline project retrieval at-or-before information cutoff;
- parsed-value substitution rejection;
- wrong-source and tampered-byte rejection.

## What this does not close

This regression does not authorize positive confirmatory eligibility.

The remaining R6 work is:

```text
R6-C = TrustedManifest-rooted lifecycle dependency binding and high-level non-temporal orchestration
R6-D = integration with separated temporal/durability claims and final confirmatory eligibility derivation
AUTHORITATIVE_CONFIRMATORY_VERIFIED = PROHIBITED
```

A sealed object, caller-supplied ref set, caller-supplied success boolean, or precomputed VERIFIED state must not substitute for accepted-manifest authority.

The existing `FULL_TRUST_CORE_CHECK_AUTHORITY_NOT_IMPLEMENTED` downgrade remains required until the complete positive authority chain is implemented and regression-confirmed.

## Candidate status

```text
candidate v0.7 = CREATED / NOT FROZEN
prospective_eligible = false
Genesis ready = NO
```

No historical candidate bytes were rewritten.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production qualified provider count = 0
PRODUCTION_QUALIFIED = NO
production forecasting = PROHIBITED
network_authorized = false
```

No provider request, production qualification execution, Genesis action, Genesis private-key handling, forecast issuance, merge, rebase, or force push occurred as part of this regression.