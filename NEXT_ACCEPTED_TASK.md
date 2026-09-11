# Next Accepted Task

Task ID: FTC_002
State: IMPLEMENTATION REVIEW OPEN

## Objective

Review the first synthetic implementation of Forecast Trust Core version 0.4 and close remaining implementation defects before merge.

## Delivered implementation candidate

1. Minimal `src/`, `schemas/`, `tests/`, and `fixtures/synthetic/` structure.
2. Restricted FPP_JCS_1 canonicalization for the frozen v0.4 domain.
3. Two stage object identity and SHA256 content sealing.
4. Full object ID plus hash dependency validation.
5. Point in time validation with explicit UNKNOWN handling.
6. Cycle plan external precommitment validation.
7. Exact cycle plan binding, full slot hash accounting, and version 1 slot cardinality checks.
8. Selection control primitives.
9. External proof deadline state handling.
10. ADV001 through ADV096 coverage registry with explicit automation boundaries.

## Current evidence

Local test command: `PYTHONPATH=src python -m unittest discover -s tests -v`

Current result: 18 tests passed.

21 adversarial cases are directly executable in the primitive layer. 60 are explicit object or governance design boundaries. 15 require concrete Genesis external proof or bootstrap instances.

## Allowed work during review

1. Inspect implementation against frozen v0.4 contracts.
2. Add regression tests for implementation defects.
3. Tighten fail closed behavior.
4. Refine synthetic schemas and fixtures without changing frozen scientific semantics.
5. Reclassify an adversarial boundary only when executable evidence justifies the change.
6. Prepare FTC_002 acceptance or blocking finding record.

## Prohibited work

1. Genuine prospective forecast issuance.
2. Forecast Ledger Genesis creation.
3. Production target selection.
4. Psychohistory research artifacts as native evidence.
5. Production model or LLM forecast execution.
6. Real OpenTimestamps Genesis anchoring.
7. Paid infrastructure.
8. Frontend, hosted API, persistent service, or production database work.

## Exit criteria

FTC_002 exits when repository level implementation review has no unresolved blocking defect, directly executable adversarial cases fail closed as specified, all remaining boundary cases are explicitly classified, and the synthetic implementation is reproducible from the repository alone.

FTC_002 completion does not authorize genuine prospective forecasting. Genesis readiness remains a separate gated task.
