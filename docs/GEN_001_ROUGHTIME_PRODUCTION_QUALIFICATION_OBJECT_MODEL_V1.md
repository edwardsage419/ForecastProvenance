# GEN_001 Roughtime Production Qualification Object Model V1

Date: 2026-09-13
Status: IMPLEMENTATION CANDIDATE
Scope: schemas, deterministic semantic validation, signature projection, and derived qualification state only

## Safety boundary

This object model does not execute production qualification, issue a production ProviderProfile, create a QualificationDecision, authorize provider traffic, authorize RFC 3161 traffic, start Genesis, create Forecast Ledger state, or create a prospective forecast.

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

## Evidence manifest

The manifest is intentionally not a normal self-sealed object.

Its canonical `FPP_JCS_1` bytes are hashed externally with SHA256. The manifest file is excluded from its own artifact closure.

The semantic validator requires:

1. ASCII canonical POSIX relative paths;
2. no absolute paths, traversal, backslashes, duplicate paths, symlinks, or special files;
3. deterministic lexicographic path order;
4. exact file-set closure;
5. recomputed byte length and SHA256 for every retained artifact;
6. `provider_id` only when present and equal to the manifest provider;
7. `attempt_number` only with a provider identity and only within the frozen two-attempt limit.

JSON null is never used.

## ProviderProfile

A production ProviderProfile candidate must exactly match one member of the frozen provider pool and the repository-owned frozen protocol profile.

The validator rejects changes to endpoint, port, root key, wire version, wire profile, TYPE behavior, SRV behavior, packet profile, transport profile, nonce profile, verifier repository, verifier tag, verifier commit, service classification, or no-fallback rule.

A ProviderProfile is still only a candidate until a valid QualificationDecision exists.

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

The semantic validator requires an injected signature verifier. A decision cannot validate when the external authority key or cryptographic verifier is absent.

## Metadata review and expiration

Metadata reviews are append-only.

A clean review records active service status, affirmative production-use permission, unchanged endpoint and root identity, unchanged protocol status, and the expected standard or pilot lifecycle classification.

A qualification-relevant metadata change is retained rather than overwriting prior evidence.

The state derivation uses an explicit `as_of_utc` input. It never reads the runtime clock.

For a valid signed production qualification:

1. any post-decision `RoughtimeRequalificationEvent` produces `REQUALIFICATION_REQUIRED`;
2. any post-decision qualification-relevant metadata change produces `REQUALIFICATION_REQUIRED`;
3. a clean latest metadata review older than 90 days produces `QUALIFICATION_EXPIRED`;
4. otherwise the derived state is `PRODUCTION_QUALIFIED`.

A later clean metadata review does not erase a previously observed requalification trigger. A new qualification decision is required after requalification.

## Rehearsal isolation

`REHEARSAL_VERIFIED` can be represented only as derived prequalification state.

Rehearsal evidence cannot produce `PRODUCTION_QUALIFIED`.

A PASS independent review without a signed decision produces `QUALIFICATION_REVIEW_READY`.

This keeps historical `NON_FORECAST_REHEARSAL` classification unchanged.

## Remaining blocker before qualification execution

This change freezes the decision signature projection and the validator interface. It deliberately does not add a home-grown Ed25519 implementation.

Before `PRODUCTION_QUALIFICATION_EXECUTION` can become ready, the project still requires:

1. a separately reviewed concrete Ed25519 verification backend or pinned system verifier;
2. offline regression of that backend against positive and negative fixtures;
3. schema validation and repository regression for the complete object model;
4. adversarial review of cross-binding, state derivation, authority injection, and evidence closure;
5. the actual owner public key identity when the Genesis governance instance is prepared.

No private key may enter repository tooling during any of these steps.
