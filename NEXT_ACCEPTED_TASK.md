# Next Accepted Task

Task ID: FTC_001
State: DESIGN REVIEW OPEN

## Objective

Freeze the Forecast Trust Core normative contract specification and adversarial test matrix before implementation.

## Review candidate delivered

The current review branch defines:

1. Exact field semantics for the eight Trust Core object families.
2. FPP_JCS_1 canonicalization and content hash coverage.
3. Trusted manifest semantics and validator trust root inputs.
4. Lifecycle state machines.
5. Point in time eligibility checks.
6. Correction and retry rules.
7. Anchor receipt verification states.
8. Forty synthetic adversarial cases with expected outcomes.

## Allowed work during review

1. Inspect scientific completeness and internal consistency.
2. Tighten field semantics.
3. Add missing attack cases.
4. Resolve ambiguities in validation outcomes.
5. Record design decisions.
6. Prepare the acceptance decision.

## Prohibited work

1. Genuine prospective forecast issuance.
2. Creation of Forecast Ledger Genesis history.
3. Import of Psychohistory research artifacts as native evidence.
4. Live model execution for production forecasts.
5. Paid infrastructure.
6. Frontend, API, database, or high volume ingestion work.
7. Trust Core implementation before design acceptance.

## Exit criteria

FTC_001 exits when every consequential Trust Core claim has a deterministic validation rule or an explicit non automatable review rule, the adversarial matrix covers the accepted threat model, and the review has no unresolved blocking scientific finding.

After acceptance, the next task may authorize synthetic Trust Core implementation. That future authorization does not authorize prospective forecasting.
