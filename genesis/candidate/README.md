# Genesis Candidate Objects

Status: GEN_001 only

This directory contains candidate normative objects prepared for Genesis readiness review.

It does not contain Forecast Ledger history and does not authorize prospective forecasting.

## Current effective candidate lineage

The current effective candidate is constructed from:

```text
objects/candidate_object_set_v0_2.json
    + objects/candidate_patch_v0_3.json
    + objects/candidate_patch_v0_4.json
```

Version 0.2 supplies the sealed base object set.

Version 0.3 replaces the issuance schedule policy and adds the operational policies required for Genesis readiness.

Version 0.4 preserves the earlier files as append-only review history, retires `policy:deadline-receipt-quorum:v1` by exact predecessor content hash, and adds `policy:deadline-receipt-quorum:v2`.

The effective version 0.4 candidate contains 22 sealed normative objects:

1. Three TargetDefinition objects.
2. Three ResolutionRule objects.
3. Six SourceContract objects.
4. One IssuanceSchedule PolicyDefinition.
5. One Evaluation PolicyDefinition.
6. One Deadline Receipt Quorum PolicyDefinition, version 2.
7. One transparent ForecastMethod baseline.
8. One Retry PolicyDefinition.
9. One Omission PolicyDefinition.
10. One Correction PolicyDefinition.
11. One Retention PolicyDefinition.
12. One Human Review PolicyDefinition.
13. One Acceptance PolicyDefinition.

The current Deadline Receipt Quorum candidate requires two independently qualifying Roughtime provider groups from an exactly three profile frozen pool. RFC 3161 is optional auxiliary evidence and is not required by the candidate minimum profile.

The materializer applies the predecessor patch chain in order. A retirement or replacement must bind the exact predecessor content hash. Repository tests require the effective object count, sealed object validity, retirement and replacement predecessor hashes, full dependency closure, one cycle per release semantics, operational policy presence, and the fail closed zero recurring cash cost time quorum semantics.

## Initial method set

The initial Genesis candidate admits only the transparent method:

```text
method:last-observed-value:v1
```

This is deliberate. The first genuine history, if later authorized by a separate Genesis acceptance decision, is intended to validate provenance, external time evidence, completeness accounting, official source resolution, evaluation, and Failure Corpus mechanics before adding more complex forecasting methods.

Any later model or additional method requires an accepted successor manifest and cannot be inserted retrospectively into Genesis history.

## Superseded review artifacts

`objects/candidate_object_set.json` is the original object set review artifact.

`objects/candidate_object_set_v0_2.json` corrected full hash bindings and remains the base of the current lineage.

`objects/candidate_patch_v0_3.json` remains the immutable predecessor patch for the current v0.4 candidate.

`policy:deadline-receipt-quorum:v1` remains preserved inside the v0.2 base as historical candidate content. It is retired only in v0.4 effective materialization. The historical object is never rewritten.

All earlier artifacts are permanently non prospective and must never be treated as an accepted Genesis manifest.

## Still missing before final Genesis candidate construction

The effective object set is intentionally incomplete for Genesis acceptance. The remaining external or evidence bound dependencies are:

1. Final BootstrapGovernanceRoot containing the owner generated Ed25519 public key.
2. Three frozen Roughtime provider profiles with successful separately authorized non forecast rehearsals, allowing a two of three deadline receipt quorum.
3. Final OTS Bitcoin verifier profile and strong rehearsal evidence.
4. Exact validator implementation binding for Genesis acceptance.
5. Content addressed real BLS and BEA archive and parser rehearsal artifacts.
6. Final Genesis TrustedManifest constructed only after the preceding dependencies are fixed.
7. Signed ManifestAcceptance and its external time evidence.
8. Final readiness adversarial review with no blocking finding.

These omissions remain explicit GEN_001 blockers.

## Scientific boundary

No file in this directory is prospective evidence.

No candidate object, patch, rehearsal artifact, or test output can create Forecast Ledger Genesis or authorize a genuine forecast by its presence in the repository.
