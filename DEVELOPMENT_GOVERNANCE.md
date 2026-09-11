# Development Governance

Version: 1.0 draft
Status: PRE_GENESIS_DESIGN

## Governance objective

Preserve scientific integrity under a single operator, low maintenance project without relying on informal memory.

## Project lifecycle states

1. PRE_GENESIS_DESIGN.
2. TRUST_CORE_BUILD.
3. ADVERSARIAL_REVIEW.
4. GENESIS_READY.
5. PROSPECTIVE_ACTIVE.
6. EVALUATION_ACTIVE.

State transitions require a recorded decision and explicit acceptance criteria.

## Decision classes

### Scientific contract decision

Required for invariant changes, point in time semantics, target semantics, resolution semantics, scoring semantics, trust root design, canonicalization, anchor semantics, and evidence admission rules.

### Operational decision

Required for dependencies, CI, storage, publication, cadence, and automation that can affect reproducibility or cost.

### Mechanical change

Formatting, typo correction, and documentation clarification may be lighter weight only when substantive semantics cannot change.

## Genesis gate

No genuine prospective forecast may be issued until all of the following are accepted:

1. Trust Core contract implementation.
2. Adversarial review suite.
3. Initial target set and versions.
4. Resolution rules.
5. Evidence cutoff policy.
6. Issuance cadence.
7. Forecast methods and transparent baselines.
8. Retry policy.
9. Correction policy.
10. External time anchor scheme.
11. Anchor failure policy.
12. Evaluation plan.
13. Publication and retention policy.
14. Genesis trusted manifest.

## Adversarial review minimum

Trust Core must be attacked for point in time leakage, circular trust roots, local backdating, resealing after mutation, forecast mutation, correction abuse, retry selection bias, unknown availability, synthetic contamination, false prospective classification, altered upstream objects with recomputed downstream hashes, anchor loss, and ambiguous resolution.

A known failure blocks Genesis until disposition is documented.

## Evidence admission

Psychohistory material can enter a future experiment only through the same explicit evidence admission process used for any external source. Original provenance must be preserved. Imported predecessor evidence never acquires native historical status by location in the repository.

## Correction governance

Probability, target, horizon, or substantive method changes require a replacement forecast or other protocol defined substantive record. They cannot be represented as metadata corrections.

## Cost governance

Recurring cash cost target is zero.

Any proposed recurring paid dependency requires a decision record containing the scientific need, free alternatives considered, expected annual cost, exit path, and effect on reproducibility.

## Dependency governance

Prefer stable standard library functionality and small open source dependencies. Pin consequential versions. Avoid always on infrastructure.

## Repository governance

The Psychohistory repository is read only predecessor provenance for this project. New development occurs only in the successor repository.
