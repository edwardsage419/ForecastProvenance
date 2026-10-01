# GEN_001 Roughtime Production Qualification Object Model V1

Date: 2026-09-13
Status: HARDENED IMPLEMENTATION CANDIDATE
Scope: schemas, deterministic semantic validation, signature projection, evidence-package closure, and derived qualification state only

## Safety boundary

This object model does not execute production qualification, issue a production ProviderProfile, create an owner-authorized QualificationDecision, authorize provider traffic, authorize RFC 3161 traffic, start Genesis, create Forecast Ledger state, or create a prospective forecast.

The state remains:

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
network_authorized = false
```

## Frozen criteria binding

All production qualification objects bind:

```text
criteria_id = FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1
criteria_sha256 = 88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e
```

A criteria hash mismatch fails closed.

## Object separation

The implementation uses seven structures.

1. `RoughtimeProductionProviderProfile` freezes the exact provider protocol identity and qualified verifier build identity. It does not carry mutable qualification state.
2. `RoughtimeQualificationEvidenceManifest` closes the retained qualification package by canonical relative path, byte length, SHA256, artifact classification, provider identity when applicable, and attempt number when applicable.
3. `RoughtimeProviderMetadataReview` records each read-only operator metadata review as an immutable sealed event.
4. `RoughtimeQualificationReview` records the separate independent review event and complete frozen-criteria review matrix.
5. `RoughtimeQualificationDecision` records the owner-authorized signed decision.
6. `RoughtimeRequalificationEvent` records a qualification-invalidating trigger without rewriting historical decisions.
7. `RoughtimeQualificationStateReport` is deterministic derived output. It is not an authority object and cannot grant qualification by itself.

This preserves the project rule that lifecycle and eligibility state are derived from immutable evidence.

## Evidence package and manifest

The manifest is intentionally not a normal self-sealed object.

Its exact `FPP_JCS_1` canonical bytes are hashed externally with SHA256. The manifest file is excluded from its own artifact entry list.

The authoritative validation path receives a qualification package root and scans the directory itself. It does not trust a caller-selected in-memory file inventory as proof of package completeness.

The package validation requires:

1. a real manifest file at the declared canonical relative path;
2. manifest file bytes exactly equal to `FPP_JCS_1(manifest)`;
3. ASCII canonical POSIX relative paths;
4. no absolute paths, traversal, backslashes, duplicate paths, symlinks, or special files;
5. deterministic lexicographic path order;
6. exact physical file-set closure after excluding the manifest file itself;
7. recomputed byte length and SHA256 for every retained artifact;
8. rejection of every missing, unexpected, or hash-mismatched artifact;
9. `provider_id` only when present and equal to the manifest provider;
10. `attempt_number` only with provider identity and only within the frozen two-attempt limit.

JSON null is never used.

## ProviderProfile

A production ProviderProfile candidate must exactly match one member of the frozen provider pool and the repository-owned frozen protocol profile.

The validator rejects changes to endpoint, port, root key, wire version, wire profile, TYPE behavior, SRV behavior, packet profile, transport profile, nonce profile, verifier repository, verifier tag, verifier commit, service classification, or no-fallback rule.

A ProviderProfile remains only a candidate until a valid owner-authorized QualificationDecision exists.

## Independent review

The independent review record binds:

```text
ProviderProfile
complete evidence manifest SHA256
qualification execution report SHA256
qualified verifier build profile SHA256
verifier binary SHA256
current metadata review
review basis SHA256
executor event identity
reviewer event identity
complete criteria check matrix
```

The frozen check matrix covers cryptography, protocol stability, production-use permission, repeatability, pilot policy, operations, independence, common dependencies, provenance, evidence closure, freshness, failure paths, Merkle coverage, standards transition, and schema/validator regression.

A PASS requires complete evidence, deterministic validation PASS, strict replay PASS, no blocking findings, and no failed applicable criterion.

The zero-cost owner-review model remains permitted, while executor and reviewer activities must be separate recorded events.

Every criterion evidence SHA256 must be retained by the scanned evidence package.

## Critical artifact hash semantics

The review fields use explicit hash meanings:

```text
execution_report_sha256 = exact retained execution-report file bytes SHA256
verifier_binary_sha256 = exact retained verifier binary bytes SHA256
review_basis_sha256 = exact retained independent-review-basis file bytes SHA256
verifier_build_profile_sha256 = verifier build profile internal profile_sha256
```

The three raw artifact hashes must appear directly in the complete evidence manifest.

The verifier build profile is separately validated under the existing Roughtime verifier-build rules. Its internal `profile_sha256` must match both the ProviderProfile and QualificationReview. Its `binary_sha256` must match the QualificationReview binary identity. An exact JSON representation of the validated build profile must be physically retained inside the scanned evidence package.

## QualificationDecision signature projection

The decision signature projection is:

```text
FPP_ROUGHTIME_QUALIFICATION_DECISION_V1
```

The exact Ed25519 message bytes are:

```text
ASCII("FPP_ROUGHTIME_QUALIFICATION_DECISION_V1") || 0x00 ||
FPP_JCS_1(signed_payload)
```

The signed payload binds:

```text
criteria_id
criteria_sha256
provider_id
provider_profile_ref
evidence_manifest_sha256
verifier_build_profile_sha256
verifier_binary_sha256
independent_review_ref
metadata_review_ref
decision_result
decision_timestamp
authority_id
authority_public_key_sha256
```

The validator receives the expected authority ID and exact 32-byte Ed25519 public key from outside the decision object. The decision cannot select its own trust root.

The private key is outside this implementation boundary. No signing function is provided.

## Ed25519 verification backend candidate

The repository contains a verification-only backend candidate using Go standard-library `crypto/ed25519.Verify` plus a Python adapter that pins the executable by SHA256.

The adapter resolves the accepted executable to an absolute canonical path before execution so PATH lookup cannot substitute a different binary. It performs pre-execution and post-execution binary SHA256 checks.

The candidate has development-only RFC 8032 positive and mutation-negative evidence. It has not yet received its final project build qualification under the accepted Go 1.27.x toolchain.

No private-key input or signing operation exists in this backend.

## Metadata review and temporal causality

Metadata reviews are append-only.

Every metadata source capture used by the authoritative qualification path must satisfy:

```text
capture.retrieved_at <= metadata_review.reviewed_at
```

The qualification review itself must not predate its bound metadata review.

The authoritative state derivation uses an explicit `as_of_utc` input and never reads the runtime clock. It rejects an `as_of_utc` earlier than the supplied independent qualification review.

For a valid signed production qualification:

1. any post-decision `RoughtimeRequalificationEvent` produces `REQUALIFICATION_REQUIRED`;
2. any post-decision qualification-relevant metadata change produces `REQUALIFICATION_REQUIRED`;
3. a clean latest metadata review older than 90 days produces `QUALIFICATION_EXPIRED`;
4. otherwise the derived state is `PRODUCTION_QUALIFIED`.

A later clean metadata review does not erase a previously observed requalification trigger. A new qualification decision is required after requalification.

## Authority boundary for derived state

`RoughtimeQualificationStateReport` is never self-authorizing.

The authoritative validation path recomputes the complete state from the actual evidence package, ProviderProfile, verified build profile, metadata reviews, independent review, signed decision when present, requalification events, and externally supplied authority inputs.

The supplied state report must equal that deterministic recomputation exactly.

Lower-level structural or convenience helpers are not a production qualification authority by themselves.

## Rehearsal isolation

`REHEARSAL_VERIFIED` can be represented only as derived prequalification state.

Rehearsal evidence cannot produce `PRODUCTION_QUALIFIED`.

A PASS independent review without a signed decision can produce only `QUALIFICATION_REVIEW_READY` after the review event time has been reached.

Historical `NON_FORECAST_REHEARSAL` classification never changes.

## Schema status

The seven production qualification schemas are Draft 2020-12 interoperability descriptions.

Their exact committed bytes completed `Draft202012Validator.check_schema` with:

```text
7 PASS
0 FAIL
```

Cross-field trust remains executable semantic validation.

## Remaining blockers before qualification execution

`PRODUCTION_QUALIFICATION_EXECUTION` remains `NOT_READY`.

Remaining blockers include:

1. complete repository regression against the exact committed branch HEAD;
2. final content-addressed Ed25519 verifier build qualification under the accepted Go 1.27.x toolchain;
3. actual external owner authority public-key identity when the governance instance is prepared;
4. independent frozen-criteria review of retained rehearsal evidence;
5. separately authorized future live repeatability evidence when required;
6. provider-specific permission, continuity, independence, freshness, and operational evidence;
7. final separately reviewed ProviderProfile and QualificationDecision records for all three providers.

No private key may enter repository tooling during any of these steps.
