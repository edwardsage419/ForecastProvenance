# Next Accepted Task

Task ID: FTC_002
State: AUTHORIZED, NOT STARTED

## Objective

Implement Forecast Trust Core version 0.4 against synthetic fixtures only, then execute the adversarial matrix.

## Allowed work

1. Create the minimal `src/`, `schemas/`, `tests/`, and `fixtures/synthetic/` structure.
2. Implement FPP_JCS_1 canonicalization and two stage object identity.
3. Implement dependency reference validation.
4. Implement TrustedManifest and BootstrapGovernanceRoot interfaces using synthetic keys and fixtures.
5. Implement SourceContract, TransformationDefinition, FittedState, policy, cycle plan, cycle manifest, anchor evidence, correction, review, and validation schemas.
6. Implement point in time checks and derived lifecycle rules.
7. Implement deterministic cycle slot generation from synthetic IssuanceSchedulePolicy fixtures.
8. Implement selection control validation using synthetic deterministic, public randomness, and externally audited examples.
9. Implement all adversarial cases in `ADVERSARIAL_REVIEW_MATRIX.md` as tests or explicit review fixtures.
10. Use only synthetic or retrospective test material clearly marked as non prospective.

## Prohibited work

1. Genuine prospective forecast issuance.
2. Forecast Ledger Genesis creation.
3. Real target selection for production forecasting.
4. Import of Psychohistory research artifacts as native evidence.
5. Production model or LLM forecast execution.
6. Real OpenTimestamps Genesis anchoring.
7. Paid infrastructure.
8. Frontend, hosted API, persistent service, or production database work.

## Exit criteria

FTC_002 exits when the frozen version 0.4 contracts have executable validation coverage, all deterministic adversarial cases produce the expected fail closed behavior, non automatable review cases have explicit testable boundaries, and there are no unresolved blocking implementation findings.

Completion of FTC_002 still does not authorize genuine prospective forecasting. A separate adversarial implementation review and Genesis readiness decision are required.