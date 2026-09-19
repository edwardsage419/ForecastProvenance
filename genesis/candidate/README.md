# Genesis Candidate Objects

Status: GEN_001 only

This directory contains candidate normative objects prepared for Genesis readiness review. It does not contain Forecast Ledger history and does not authorize prospective forecasting.

## Current effective candidate lineage

The current effective candidate is constructed from:

```text
objects/candidate_object_set_v0_2.json
    + objects/candidate_patch_v0_3.json
    + objects/candidate_patch_v0_4.json
    + objects/candidate_patch_v0_5.json
    + objects/candidate_patch_v0_6.json
```

Versions 0.2 through 0.5 remain immutable historical candidate material.

Version 0.6 is the Architecture Compression P1 through P4 successor patch. It retires, by exact predecessor content hash:

```text
policy:genesis-acceptance:v1
policy:genesis-evaluation:v1
policy:genesis-human-review:v1
```

It adds:

```text
policy:genesis-acceptance:v2
policy:genesis-evaluation:v2
```

The effective version 0.6 candidate therefore contains 21 sealed normative objects:

1. Three TargetDefinition objects.
2. Three ResolutionRule objects.
3. Six SourceContract objects.
4. One IssuanceSchedule PolicyDefinition.
5. One minimal Evaluation PolicyDefinition v2.
6. One Deadline Receipt Quorum PolicyDefinition v3.
7. One deterministic ForecastMethod, `method:last-observed-value:v1`.
8. One Retry PolicyDefinition.
9. One Omission PolicyDefinition.
10. One Correction PolicyDefinition.
11. One Retention PolicyDefinition.
12. One Acceptance PolicyDefinition v2.

Genesis v1 no longer instantiates a scientific Human Review Policy. Official-source conflict or semantic ambiguity remains `REVIEW_REQUIRED` or `UNRESOLVED`; there is no Genesis v1 ReviewDecision path that selects a resolved value.

The EvaluationPolicy v2 retains only point-forecast values needed for minimal scoring and cohort integrity:

```text
resolved_outcome
forecast_value
absolute_error
squared_error
```

Baseline delta, pairwise method comparison, aggregate predictive-skill claims, probabilistic scoring, significance claims, and leaderboard semantics remain deferred until a distinct second method or forecast class is admitted by a successor manifest.

The AcceptancePolicy v2 requires final external evidence over the exact signed ManifestAcceptance as a separate final-validation input. Intermediate bootstrap or candidate-manifest anchors are optional audit evidence and cannot substitute for the final acceptance evidence.

## Initial method set

The initial Genesis candidate admits only:

```text
method:last-observed-value:v1
selection_control_class = DETERMINISTIC_REPLAY
randomness_policy = NONE
```

PublicRandomnessPolicy, FittedState, closed-model observability and retrieval paths, stochastic selection control, externally audited attempts, and multi-method comparison remain dormant Trust Core interfaces rather than Genesis v1 dependencies.

## Provider qualification boundary

The candidate policy set continues to require `policy:deadline-receipt-quorum:v3`.

The final TrustedManifest is expected to bind the exact three production ProviderProfiles, matching signed QualificationDecisions, and exact qualification verifier contract. Dynamic provider state at each consequential deadline is reconstructed at:

```text
as_of_utc = frozen_deadline_utc
```

All three admitted providers must remain `PRODUCTION_QUALIFIED` at that historical as-of before the event may use the frozen production-ready three-provider pool. Receipt quorum then remains two-of-three and provider outage never lowers the threshold.

Provider qualification workflow internals remain supporting-subsystem evidence rather than candidate policy objects.

## Historical preservation

Earlier candidate objects and patches are never rewritten. Retirement or replacement in v0.6 binds the exact predecessor `content_sha256`; historical validators and historical reports retain their original semantics.

No v0.6 object is an accepted Genesis manifest merely because it exists in the repository.

## Still missing before final Genesis acceptance

The effective object set remains pre-Genesis. External and final-freeze blockers include:

1. final BootstrapGovernanceRoot containing the owner-generated Ed25519 public key;
2. three production-qualified Roughtime ProviderProfiles and matching QualificationDecisions;
3. final qualification verifier contract and content-closed qualification-state package semantics;
4. final OTS Bitcoin verifier profile and strong rehearsal evidence;
5. exact final Genesis ValidatorContract binding;
6. retained real BLS and BEA archive/parser evidence;
7. final TrustedManifest constructed after all dependencies are fixed;
8. owner-signed ManifestAcceptance;
9. final external existence and Bitcoin durability evidence over that exact signed ManifestAcceptance;
10. independent final validation and final readiness adversarial review with no blocking finding;
11. separate explicit Genesis authorization.

## Scientific boundary

No file in this directory is prospective evidence.

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
production forecasting = PROHIBITED
```
