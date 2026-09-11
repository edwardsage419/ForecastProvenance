# Genesis Candidate Objects

Status: GEN_001 only

This directory contains candidate normative objects prepared for Genesis readiness review.

It does not contain Forecast Ledger history and does not authorize prospective forecasting.

## Current effective candidate lineage

The current effective candidate is constructed from:

```text
objects/candidate_object_set_v0_2.json
    + objects/candidate_patch_v0_3.json
```

Version 0.2 supplies the sealed base object set. Version 0.3 replaces the issuance schedule policy and adds the operational policies required for Genesis readiness.

The effective version 0.3 candidate contains 22 sealed normative objects:

1. Three TargetDefinition objects.
2. Three ResolutionRule objects.
3. Six SourceContract objects.
4. One IssuanceSchedule PolicyDefinition.
5. One Evaluation PolicyDefinition.
6. One Deadline Receipt Quorum PolicyDefinition.
7. One transparent ForecastMethod baseline.
8. One Retry PolicyDefinition.
9. One Omission PolicyDefinition.
10. One Correction PolicyDefinition.
11. One Retention PolicyDefinition.
12. One Human Review PolicyDefinition.
13. One Acceptance PolicyDefinition.

The candidate patch is append-only review history. It does not silently rewrite version 0.2.

Repository tests require the effective object count, predecessor replacement hash, object seals, full dependency closure, one-cycle-per-release schedule semantics, and presence of the required operational policies.

## Initial method set

The initial Genesis candidate admits only the transparent method:

```text
method:last-observed-value:v1
```

This is deliberate. The first genuine history, if later authorized by a separate Genesis acceptance decision, is intended to validate provenance, external time evidence, completeness accounting, official-source resolution, evaluation, and Failure Corpus mechanics before adding more complex forecasting methods.

Any later model or additional method requires an accepted successor manifest and cannot be inserted retrospectively into Genesis history.

## Superseded review artifacts

`objects/candidate_object_set.json` is the original object-set review artifact.

It was superseded because its EvaluationPolicy referred to the baseline only by semantic ID and its baseline method did not bind the three compatible target hashes.

`objects/candidate_object_set_v0_2.json` corrected those bindings and remains the base of the current lineage.

The earlier artifacts are permanently non-prospective and must never be treated as an accepted Genesis manifest.

## Still missing before final Genesis candidate construction

The effective object set is intentionally incomplete for Genesis acceptance. The remaining external or evidence-bound dependencies are:

1. Final BootstrapGovernanceRoot containing the owner-generated Ed25519 public key.
2. Frozen qualifying wall-clock provider profiles proven by live non-forecast rehearsal.
3. Final OTS Bitcoin verifier profile and strong rehearsal evidence.
4. Exact validator implementation binding for Genesis acceptance.
5. Content-addressed real BLS and BEA archive/parser rehearsal artifacts.
6. Final Genesis TrustedManifest constructed only after the preceding dependencies are fixed.
7. Signed ManifestAcceptance and its external time evidence.
8. Final readiness adversarial review with no blocking finding.

These omissions remain explicit GEN_001 blockers.

## Scientific boundary

No file in this directory is prospective evidence.

No candidate object, patch, rehearsal artifact, or test output can create Forecast Ledger Genesis or authorize a genuine forecast by its presence in the repository.