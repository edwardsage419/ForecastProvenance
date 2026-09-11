# Minimal Repository Structure

Status: DESIGN ONLY

## Stage A Pre Genesis design repository

```text
forecast_provenance/
    README.md
    PROJECT_VISION.md
    SCIENTIFIC_INVARIANTS.md
    ARCHITECTURE.md
    DEVELOPMENT_GOVERNANCE.md
    CURRENT_STATE.md
    DECISIONS.md
    NEXT_ACCEPTED_TASK.md
    docs/
        POINT_IN_TIME_RULES.md
        FORECAST_TRUST_CORE.md
        TRUST_CORE_CONTRACTS.md
        CANONICALIZATION_AND_IDENTIFIERS.md
        TRUSTED_MANIFEST.md
        ADVERSARIAL_REVIEW_MATRIX.md
        PROSPECTIVE_TIME_ANCHOR.md
        GENESIS_PROTOCOL.md
```

No data directory, forecast ledger, outcomes directory, frontend, API, live model module, database, or GKG module exists at this stage.

## Stage B Trust Core build

Add only when Stage A documents are accepted:

```text
    schemas/
    fixtures/
        synthetic/
    tests/
    src/
```

Synthetic fixtures must carry an unmistakable non prospective classification.

## Stage C After Genesis acceptance

Only after the Genesis gate passes, add the authoritative prospective record locations defined by the accepted Genesis Protocol.

The repository layout should not imply prospective history before genuine prospective history exists.
