# Genesis Abort Conditions

Version: 0.2 candidate
Status: GEN_001 REVIEW CANDIDATE

Genesis readiness, acceptance, and early operation fail closed.

An abort condition preserves evidence and stops progression to a stronger trust state. It can be cleared only through new evidence or a versioned governance decision consistent with the Scientific Invariants.

## Readiness abort conditions

GEN_001 cannot exit while any selected required item in `GENESIS_READINESS_EVIDENCE_MATRIX.md` remains open.

Specific readiness abort conditions include:

1. Fewer than two independent wall-clock provider groups qualify under the selected Genesis profile.
2. No qualifying RFC 3161 provider exists.
3. A selected time provider lacks a defensible conservative upper time bound.
4. The owner bootstrap public key is missing, malformed, or cannot be tied to an owner-controlled private key kept outside project systems.
5. Strong OpenTimestamps verification cannot be completed against owner-controlled Bitcoin Core.
6. Any initial target lacks a retained official first-release source fixture and successful semantic adapter report.
7. Candidate object dependency closure fails.
8. Effective candidate materialization is nondeterministic.
9. Exact Genesis validator implementation cannot be content bound.
10. Final readiness adversarial review contains an unresolved blocking finding.

## Candidate manifest construction abort conditions

Construction stops if:

1. Any manifest dependency is referenced by semantic ID without the expected full content hash.
2. Candidate object lineage contains an unverified replacement predecessor.
3. A ProviderProfile is built from a design snapshot without successful live rehearsal evidence.
4. BootstrapGovernanceRoot is derived from or authorized solely by the candidate manifest it will accept.
5. Manifest references rehearsal artifacts as native prospective evidence.
6. Final validator contract does not match the source or executable artifact used for acceptance validation.
7. Any required target, method, source, schedule, retry, omission, correction, retention, human-review, evaluation, time-evidence, or acceptance policy is absent.

## Manifest acceptance abort conditions

ManifestAcceptance is rejected if:

1. Owner signature does not verify against the exact BootstrapGovernanceRoot public key.
2. Signature subject does not bind the exact candidate TrustedManifest full hash.
3. Candidate manifest changes after signing.
4. Required validation reports are missing or contain blocking failures.
5. Manifest or ManifestAcceptance external time evidence fails quorum.
6. Acceptance evidence is incomplete, late, or bound to a different subject hash.
7. Private key material appears in repository, CI, logs, issue comments, rehearsal packages, or ChatGPT-managed artifacts.

Any suspected private-key exposure invalidates that bootstrap key for Genesis use and requires a new key before another acceptance attempt.

## Cycle-plan abort conditions after separate Genesis acceptance

These rules are defined for future use and do not authorize cycles during GEN_001.

A target release instance does not execute when:

1. Official schedule artifact cannot be retained and content addressed before plan construction.
2. Deterministic schedule derivation cannot uniquely identify the release instance and outcome information barrier.
3. Cycle-plan external precommitment quorum is missing or late.
4. Plan proof subject hash differs from the exact sealed plan.
5. Required source or baseline first-release evidence is unavailable by information cutoff.
6. Official schedule advances in a way that triggers the precommitted omission policy before execution.
7. A required operational dependency fails and the retry policy is exhausted.

The release instance remains visible in operational completeness accounting even when no forecast is issued.

## Issuance abort conditions after separate Genesis acceptance

Issuance fails closed when:

1. Expected slot set differs from deterministic schedule output.
2. Forecast method or target is not admitted by the historical trusted manifest.
3. Evidence includes information after cutoff or required availability is unknown.
4. Selection control is not satisfied.
5. Attempt count exceeds retry policy.
6. First successful attempt is replaced by a later output.
7. Issued forecast seal or dependency binding fails.
8. Deadline receipt quorum is absent or late.

## Durability abort conditions

A record cannot enter the initial confirmatory prospective cohort when:

1. OTS proof does not bind the exact ExternalTimeEvidenceBundle.
2. Strong Bitcoin verification fails.
3. Proof bytes or required verifier evidence are unavailable.
4. DurabilityVerificationRecord external receipt quorum is absent or occurs after the target outcome information barrier.

A late durability completion may remain historical operational evidence. It cannot be promoted retrospectively into the initial confirmatory cohort.

## Resolution abort conditions

Outcome resolution becomes `REVIEW_REQUIRED` or `UNRESOLVED` when:

1. Official first-release artifact cannot be content addressed.
2. Semantic adapter does not produce exactly one target-compatible record.
3. Artifact represents a later revision or wrong estimate stage.
4. Official sources conflict under the frozen ResolutionRule.
5. Display precision or unit cannot be established from accepted evidence.

Human review cannot override a hash mismatch, future-information violation, missing time quorum, incomplete cycle accounting, output-selection violation, or an unaccepted target or method.

## Evaluation abort conditions

Evaluation stops or marks the affected record nonscorable under precommitted policy when:

1. Resolution is unresolved under the frozen rule.
2. Cohort construction omits an issued, failed, omitted, or unresolved record that policy requires to remain visible.
3. Baseline uses revised database data instead of the retained preceding first-release artifact.
4. Metric implementation differs from the accepted EvaluationPolicy.
5. A correction or withdrawal attempts to erase original cohort membership.

## Cost and infrastructure abort conditions

No Genesis readiness or operation may silently introduce a recurring paid dependency.

If a selected provider, hosting service, data source, or verifier becomes paid or requires an unacceptable recurring commitment, the dependency is ineligible until a separate governance decision evaluates alternatives, expected cost, reproducibility, and exit path.

## Abort record

Every aborted Genesis candidate receives an immutable abort record containing:

```text
candidate_manifest_ref_or_none
abort_stage
reason_codes
evidence_refs
recorded_by
replacement_candidate_ref_or_none
```

An abort record is administrative scientific history and is never prospective forecast history.

Failed candidates, rehearsal anchors, source fixtures, and abort records never count toward the native Forecast Ledger.

## Recovery rule

The project never weakens a trust requirement solely to keep a cycle, provider, target, schedule, or candidate alive.