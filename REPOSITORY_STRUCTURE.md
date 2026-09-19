# Minimal Repository Structure

Status: TRUST_CORE_BUILD AUTHORIZED

## Current design baseline

```text
ForecastProvenance/
    README.md
    PROJECT_VISION.md
    SCIENTIFIC_INVARIANTS.md
    ARCHITECTURE.md
    DEVELOPMENT_GOVERNANCE.md
    CURRENT_STATE.md
    DECISIONS.md
    NEXT_ACCEPTED_TASK.md
    docs/
        FORECAST_TRUST_CORE.md
        TRUST_CORE_CONTRACTS.md
        CANONICALIZATION_AND_IDENTIFIERS.md
        TRUSTED_MANIFEST.md
        POINT_IN_TIME_RULES.md
        SUPPORTING_NORMATIVE_CONTRACTS.md
        POLICY_CONTRACTS.md
        ISSUANCE_AND_RETRY_POLICY.md
        EXECUTION_SELECTION_CONTROL.md
        PROSPECTIVE_TIME_SEMANTICS.md
        PROSPECTIVE_TIME_ANCHOR.md
        MODEL_EVIDENCE_OBSERVABILITY.md
        RESOLUTION_EVIDENCE_SEMANTICS.md
        GENESIS_BOOTSTRAP_GOVERNANCE.md
        GENESIS_PROTOCOL.md
        ADVERSARIAL_REVIEW_MATRIX.md
        INVARIANT_COVERAGE.md
        FTC_001_ADVERSARIAL_DESIGN_REVIEW.md
        FTC_001_REMEDIATION_STATUS.md
        FTC_001_SECOND_ADVERSARIAL_REVIEW.md
        SECOND_REVIEW_REPAIR_PLAN.md
        FTC_001_THIRD_ADVERSARIAL_REVIEW.md
        FTC_001_FREEZE_REVIEW.md
```

## FTC_002 minimal implementation structure

FTC_001 design acceptance authorizes creation of only:

```text
    src/
    schemas/
    tests/
    fixtures/
        synthetic/
```

The implementation should remain file based, deterministic, dependency light, and suitable for local execution and bounded free CI.

Synthetic fixtures must carry `origin_class = SYNTHETIC` and cannot assert prospective eligibility.

## Still prohibited before Genesis

Do not create authoritative prospective forecast, outcome, evaluation, or failure corpus trees yet.

Do not add a production database, hosted API, frontend, live model service, or external project data migration.

The authoritative prospective record structure will be created only after the separate Genesis gate passes.