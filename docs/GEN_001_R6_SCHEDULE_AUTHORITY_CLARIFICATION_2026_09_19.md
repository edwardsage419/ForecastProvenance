# GEN_001 R6 Schedule Authority Clarification

Date:
2026-09-19

## Scope

This record closes the schedule-derivation ambiguity found during the read-only R6 confirmatory authority composition review.

It remains pre-Genesis design work. It does not authorize Genesis, Forecast Ledger creation, prospective forecasting, production qualification, provider network requests, or candidate acceptance.

## Finding

The v1 issuance schedule described plan and execution offsets as calendar days while also requiring America/New_York time-zone conversion.

Across daylight-saving transitions, subtracting elapsed UTC hours and subtracting local calendar days can differ by one hour. The prior candidate did not freeze which operation controlled.

The prior candidate also did not freeze deterministic runtime identity derivation for TargetInstance and ForecastSlot objects, leaving authoritative mandatory-slot reconstruction under-specified.

## Decision

Successor candidate v0.8 retires policy:genesis-issuance-schedule:v1 by exact content hash and introduces policy:genesis-issuance-schedule:v2.

Version 2 freezes:

1. America/New_York as the initial normative schedule zone.
2. Exact IANA time-zone database version binding in schedule derivation evidence.
3. Local calendar subtraction before UTC conversion for calendar-day offsets.
4. Fail-closed handling for ambiguous or nonexistent resulting local times.
5. Twenty-four-hour external-proof margin as elapsed UTC duration.
6. Deterministic TargetInstance and ForecastSlot identity reconstruction using seal_object without semantic-ID override and frozen stable-context templates.

## Candidate lifecycle

CURRENT_EFFECTIVE_CANDIDATE = V0_6

CANDIDATE_V0_7 = CREATED_AND_VALIDATED

CANDIDATE_V0_7_ACCEPTANCE = NOT_YET_PERFORMED

CANDIDATE_V0_8 = CREATED_PENDING_REGRESSION

CANDIDATE_V0_8_ACCEPTANCE = NOT_YET_PERFORMED

Creating v0.8 does not make it effective.

## R6 effect

The clarification removes two authority-substitution ambiguities required before the R6 positive confirmatory path can be implemented.

The existing FULL_TRUST_CORE_CHECK_AUTHORITY_NOT_IMPLEMENTED gate remains mandatory until the complete R6 non-temporal authority reconstruction is implemented and passes regression.

## Safety state

Genesis = NOT STARTED

Forecast Ledger Genesis = NOT CREATED

Forecast Ledger = NOT CREATED

prospective forecast count = 0

production qualified provider count = 0

PRODUCTION_QUALIFIED = NO
