# Genesis Candidate Objects

Status: GEN_001 only

This directory contains candidate normative objects prepared for Genesis readiness review.

It does not contain Forecast Ledger history and does not authorize prospective forecasting.

## Current candidate

`objects/candidate_object_set_v0_2.json` is the current object-set candidate.

It contains 16 sealed objects:

1. Three TargetDefinition objects.
2. Three ResolutionRule objects.
3. Six SourceContract objects.
4. One IssuanceSchedule PolicyDefinition.
5. One Evaluation PolicyDefinition.
6. One Deadline Receipt Quorum PolicyDefinition.
7. One transparent ForecastMethod baseline.

Every object uses the frozen Trust Core sealing rules and all full dependency references close exactly within the set.

## Superseded review artifact

`objects/candidate_object_set.json` is retained as an earlier review artifact.

It was superseded because its EvaluationPolicy referred to the baseline only by semantic ID and its baseline method did not bind the three compatible target hashes.

Those omissions were found during dependency-closure review before Genesis. Version 0.2 corrects both bindings.

The earlier object set is permanently non-prospective and must never be used as a Genesis manifest dependency.

## Still missing from the final Genesis manifest

The object set is intentionally incomplete for Genesis acceptance. It does not yet contain:

1. Final BootstrapGovernanceRoot with owner-generated Ed25519 public key.
2. Frozen wall-clock provider profiles proven by live rehearsal.
3. Final OTS Bitcoin verifier profile and rehearsal evidence.
4. Exact validator implementation binding for Genesis acceptance.
5. Final retry, omission, correction, retention, acceptance, and human-review policy objects required by the Genesis manifest.
6. Content-addressed real official archive/parser rehearsal artifacts.
7. Candidate Genesis manifest or ManifestAcceptance.

These omissions remain explicit GEN_001 blockers.