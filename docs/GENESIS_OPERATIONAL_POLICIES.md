# Genesis Operational Policies

Version: 0.1 candidate
Status: GEN_001 REVIEW CANDIDATE

These policies are deliberately narrow because Genesis version 1 begins with a deterministic transparent baseline method only.

## Initial method admission

Genesis version 1 proposes exactly one ForecastMethod:

```text
method:last-observed-value:v1
```

Purpose:

1. Start genuine elapsed prospective history with the smallest execution surface.
2. Exercise time provenance, schedule completeness, resolution, evaluation, and Failure Corpus pathways without model cost.
3. Avoid delaying the time moat while a more complex model method is still under development.
4. Preserve model neutrality by adding later methods only through successor trusted manifests.

A baseline-only Genesis does not claim model superiority or predictive innovation.

## RetryPolicy

Policy ID: `policy:genesis-retry:v1`

Rules:

```text
max_attempts = 2
issuance_eligible_success_rule = FIRST_SUCCESS_ONLY
randomness_progression_rule = NONE_FOR_INITIAL_METHOD
```

Retry-eligible failure codes:

```text
LOCAL_IO_TRANSIENT
PROCESS_CRASH
EXECUTION_TIMEOUT
```

Ineligible retry reasons include forecast value, forecast direction, expected score, operator preference, and any error discovered only by inspecting the prediction.

Both attempts bind identical target, information cutoff, EvidenceSnapshot, method hash, configuration, and output schema.

The second attempt is permitted only when the first terminates with an admitted technical failure code.

If the first attempt succeeds, no second confirmatory attempt is permitted.

If both attempts fail, the expected slot remains a failed slot in cohort accounting.

## OmissionPolicy

Policy ID: `policy:genesis-omission:v1`

Allowed pre-output cycle or slot omission codes:

```text
MISSING_SCHEDULE_ARTIFACT
MISSING_REQUIRED_EVIDENCE
PLAN_TIME_EVIDENCE_FAILED
SCHEDULE_ADVANCED_AFTER_PLAN
EARLY_OUTCOME_DISCLOSURE_BEFORE_EXECUTION
GENESIS_OPERATIONAL_ABORT
```

Every omission binds evidence supporting the reason code.

Operator discretion after forecast output inspection is prohibited.

A mandatory release instance with no cycle plan receives `MISSING_CYCLE_PLAN` and remains visible in operational completeness reporting.

## CorrectionPolicy

Policy ID: `policy:genesis-correction:v1`

Allowed correction types:

```text
METADATA_NON_SUBSTANTIVE
WITHDRAWAL
SUBSTANTIVE_REPLACEMENT
ADMINISTRATIVE_STATUS
```

Non-substantive metadata correction cannot change:

```text
target
reference_period
information_cutoff
prediction
method
EvidenceSnapshot
resolution_rule
cycle_plan
```

A substantive change creates a new IssuedForecast and preserves the original.

A replacement receives prospective eligibility only if it independently satisfies the original frozen cycle deadlines. It cannot inherit the original forecast's time evidence.

Withdrawal never deletes the original forecast and never removes it from confirmatory cohort accounting.

## RetentionPolicy

Policy ID: `policy:genesis-retention:v1`

Retain indefinitely by content:

1. Accepted normative objects and trusted manifests.
2. Bootstrap governance root, public keys, signatures, and ManifestAcceptance objects.
3. IssuanceCyclePlans, attempts, IssuedForecast objects, corrections, and cycle manifests.
4. External wall-clock requests, responses, certificates, provider policies, and required revocation material.
5. OpenTimestamps proof bytes and strong Bitcoin verification records.
6. EvidenceSnapshots and consequential compact source artifacts required for independent verification.
7. Official resolution artifacts and parser derivation reports.
8. Resolution and Evaluation records.
9. Failure Corpus records and abort records.

Compact authoritative artifacts are retained in the repository or another content-addressed project store with SHA256 identity.

A second owner-controlled offline copy of Genesis critical cryptographic and scientific artifacts is required before Genesis acceptance.

The retention policy does not require a paid hosted service.

Loss of a required artifact changes current verifiability and does not rewrite a prior immutable validation record.

## Human ReviewRule

Policy ID: `policy:genesis-human-review:v1`

Human review is allowed only for predeclared evidence ambiguity such as conflicting official artifacts or an official layout change that preserves target semantics but defeats the frozen automatic extractor.

Human review cannot override:

1. hash mismatch;
2. future-information violation;
3. missed external deadline;
4. missing required time quorum;
5. unaccepted method or target;
6. incomplete cycle accounting;
7. output-selection violation.

A ReviewDecision binds reviewer authority, exact evidence hashes, allowed review rule, decision, reason codes, and rationale.

## Failure Corpus entry rule

Every failed mandatory cycle, failed attempt, time-evidence failure, parser ambiguity, unresolved outcome, correction, and protocol invalidation produces or contributes to an append-only failure record.

Failure attribution remains `UNKNOWN` when the retained evidence cannot support a narrower cause.

The Failure Corpus is never filtered to retain only diagnostically clean cases.

## Cost policy

Genesis version 1 has recurring cash budget zero.

Initial forecast execution is local and deterministic. External time providers and official data sources must have no recurring charge under the accepted profiles.

A future paid dependency requires a separate accepted decision and cannot be inserted silently into a Genesis policy.