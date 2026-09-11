# FTC_001 Second Adversarial Scientific Design Review

Date: 2026-09-11
Disposition: BLOCKING FINDINGS REMAIN

## R2-B01 Precommitment lacks an external existence deadline

Severity: BLOCKING

IssuanceCyclePlan is externally committed before outputs are inspected, while the contract does not define a verifiable deadline for that commitment.

Required repair: define plan_commitment_deadline and require verified_plan_existence_bound less than or equal to plan_commitment_deadline. The deadline must precede the fixed execution window.

## R2-B02 Attempt start time remains locally asserted

Severity: BLOCKING

Local started_at can be backdated, so it cannot establish that plan commitment preceded execution.

Required repair: use a fixed cycle execution window. The plan must have external existence proof before that window opens. Local attempt times remain operational metadata.

## R2-B03 ManifestAcceptance bootstrap authority is underspecified

Severity: BLOCKING FOR GENESIS

The first accepted manifest cannot derive its authority solely from itself.

Required repair: Genesis must define an out of graph bootstrap governance root with exact authority identity, acceptance rule identity, retained bytes, and external anchoring.

## R2-B04 Anchor scheme semantics remain a placeholder

Severity: BLOCKING FOR GENESIS, NONBLOCKING FOR SYNTHETIC TRUST CORE

The external time inequality is sound in form, while the exact OTS Bitcoin conservative bound is not frozen.

Required repair before Genesis: define proof parsing, accepted attestations, conservative time bound construction, confirmation policy, verifier version, and malformed proof behavior.

## R2-B05 IssuanceCycleManifest has anchor hash self reference risk

Severity: BLOCKING

If anchor_subject_hash is inside the manifest whose hash becomes the anchor subject, hash recursion returns.

Required repair: remove anchor_subject_hash. The final manifest content_sha256 is the anchor subject.

## R2-B06 Consequential policy objects lack normative schemas

Severity: BLOCKING

CorrectionPolicy, RetryPolicy, OmissionPolicy, EvaluationPolicy, RetentionPolicy, ReviewRule, and AcceptanceRule affect trust outcomes but have no minimum schemas.

Required repair: define first class PolicyDefinition contracts with ID, version, full hash, scope, deterministic rules, and change semantics.

## R2-B07 Slot cardinality is underspecified

Severity: HIGH

Each expected slot must bind exactly one target instance, method, output schema, horizon, and forecast cardinality for version 1.

## R2-B08 Plan replacement semantics are implicit

Severity: HIGH

Any changed plan must be a new object and requires a new external precommitment before its execution window.

## R2-B09 Anchor event ordering can fork

Severity: HIGH

Anchor evidence should be treated as a DAG. Multiple valid proof paths can coexist only when they attest the same subject. Sequence integers cannot establish external chronology.

## R2-B10 FailureEvidence can overclaim external failure

Severity: HIGH

Operator failure records are operational. Scientific trust state derives from required proof presence, validity, and deadline compliance.

## R2-B11 Retention degradation conflates historical validity and current verifiability

Severity: HIGH

Loss of bytes should degrade current verifiability without rewriting a prior immutable ValidationReport.

## R2-B12 evidence_class can still invite prospective self labeling

Severity: MEDIUM

Stored classes should represent origin only. Prospective eligibility remains derived.

## R2-B13 FULL_EXTERNAL is too broad

Severity: MEDIUM

Rename it to FULL_DECLARED_EXTERNAL_INPUTS and limit the claim to declared information inputs.

## R2-B14 Resolution evidence needs explicit admissibility semantics

Severity: HIGH

Define publication, retrieval, vintage selection, conflict, sufficiency, and resolution deadline semantics independently from forecast information cutoff.

## R2-B15 ValidationReport dependency_root is undefined

Severity: HIGH

Remove dependency_root for version 1 or define a canonical construction. Prefer a deterministically sorted dependency reference array.

## Disposition

The repaired design is materially stronger. FTC_001 is still not ready to freeze.

R2-B01, R2-B02, R2-B03, R2-B05, and R2-B06 are blocking at the contract level.

R2-B04 is deferred explicitly to the Genesis gate and need not block later synthetic Trust Core implementation once the abstract anchor interface freezes.

No implementation is authorized yet.
