# Decisions

## D001 New project identity

Status: ACCEPTED FOR DESIGN BASELINE
Date: 2026-09-11

Formal name: Forecast Provenance Project
Recommended repository slug: forecast_provenance

Reason: The name describes the durable asset directly, remains model neutral, and does not constrain the project to one ledger implementation or one forecast method.

## D002 Predecessor boundary

Status: ACCEPTED

Psychohistory is archived predecessor provenance. GKG, historical phases, frozen samples, old research state, old schemas, and old current state are excluded from native project evidence.

## D003 First phase

Status: ACCEPTED

Forecast Trust Core is the first implementation phase. Prospective forecasting is blocked until Trust Core and adversarial review are accepted.

## D004 Primary prospective time anchor

Status: SELECTED FOR GENESIS ACCEPTANCE TEST

Scheme name: OTS_BTC_BATCH_V1

The project will anchor a deterministic issuance batch manifest with OpenTimestamps and retain the proof material until it is upgraded to a Bitcoin attestation.

The Bitcoin attestation is treated as conservative external existence evidence. It does not establish an exact claimed issuance second.

A forecast does not enter final genuine prospective classification while its required proof remains unverified.

Genesis must define acceptable anchor latency and failure handling before issuance begins.

## D005 Cost doctrine

Status: ACCEPTED

Recurring cash cost target is zero. Public Git hosting and bounded free CI may be used while available. Paid infrastructure requires a separate accepted decision.

## D006 Canonicalization candidate

Status: FTC_001 REVIEW CANDIDATE
Date: 2026-09-11

Scheme ID: FPP_JCS_1

Use RFC 8785 JCS over a restricted project JSON data model.

Consequential scientific decimal values are encoded as canonical decimal strings. JSON floating point values are prohibited in normative scientific objects.

Reason: deterministic hashing must survive language and runtime differences without allowing implicit numeric reinterpretation.

## D007 Dependency identity rule

Status: FTC_001 REVIEW CANDIDATE
Date: 2026-09-11

Every consequential dependency binds both semantic object ID and full SHA256 content hash.

Semantic identity alone cannot establish content identity.

Reason: this prevents a changed upstream object from inheriting trust merely because its human readable ID was preserved.

## D008 Explicit trusted manifest rule

Status: FTC_001 REVIEW CANDIDATE
Date: 2026-09-11

Validators receive the trusted manifest as an external input.

Candidate objects and their dependency graph cannot select or regenerate the trust root used to validate themselves.

Reason: this prevents circular trust in which altered upstream objects and recomputed downstream hashes form a fully consistent but unauthorized alternate history.
