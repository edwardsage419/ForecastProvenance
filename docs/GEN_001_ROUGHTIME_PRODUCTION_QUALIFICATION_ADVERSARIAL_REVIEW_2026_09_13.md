# GEN_001 Roughtime Production Qualification Adversarial Review

Date: 2026-09-13
Status: REPOSITORY HARDENING REVIEW COMPLETE, FULL REGRESSION PENDING
Scope: production qualification object model, evidence closure, derived state, and Ed25519 verification backend candidate

## Safety boundary

This review is repository engineering only.

It does not qualify a provider, create a production ProviderProfile, create a QualificationDecision, authorize a Roughtime request, authorize RFC 3161 traffic, start Genesis, create Forecast Ledger state, or create a prospective forecast.

The safety state remains:

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
network_authorized = false
```

No Genesis private key was accessed or required. The Ed25519 candidate exposes verification only.

## Snapshot basis

```text
repository = edwardsage419/ForecastProvenance
branch = design/gen-001
snapshot_basis_commit = 394fae9a08d10f72b12716c84cb4f6752fd389e3
criteria_id = FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1
criteria_sha256 = 88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e
```

The commit containing this review is identified from Git metadata. This document does not embed its own resulting commit SHA.

## Review result

No known repository-level design finding from this review remains silently bypassed.

The implementation remains ineligible for production qualification execution until the exact committed tree passes the full repository regression, the Ed25519 verification backend receives its final content-addressed build qualification under the accepted Go 1.27.x toolchain, and the required external authority public-key identity exists.

Provider-specific qualification evidence remains entirely unexecuted.

## Findings and dispositions

### AR-PQ-001 Manifest canonicalization conflict

Earlier draft language permitted JSON `null` for non-applicable manifest entry fields while `FPP_JCS_1` rejects JSON null.

Disposition: CLOSED.

V1 requires `provider_id` and `attempt_number` when applicable and omission when not applicable. Manifest entry order is canonical ASCII `relative_path` order.

### AR-PQ-002 Review evidence could reference hashes outside the complete manifest

A PASS review could list criterion evidence SHA256 values without proving that those hashes were retained by the complete evidence package.

Disposition: CLOSED.

The hardening validator requires every `criteria_checks[*].evidence_sha256s` value to exist in the complete manifest.

### AR-PQ-003 Executor and reviewer event identity were not separated

The zero-cost owner-review model permits the same human owner to perform both activities, while the activities must remain separate recorded events.

Disposition: CLOSED.

The semantic validator rejects identical `executor_id` and `reviewer_id` values.

### AR-PQ-004 Derived state could be treated as self-asserted authority

A structurally valid state report could otherwise be mistaken for qualification authority.

Disposition: CLOSED.

Authoritative state validation requires exact deterministic recomputation from immutable qualification inputs. A standalone state-report structural validation is not an authority decision.

### AR-PQ-005 Ed25519 executable path substitution

The first pinned-binary adapter version could hash a relative current-directory path while process execution of a bare filename could resolve through `PATH` to a different executable.

Disposition: CLOSED.

The adapter now resolves the accepted executable to an absolute canonical path before invocation, rejects a final-component symlink or non-file path, and recomputes the expected binary SHA256 before and after execution.

### AR-PQ-006 Manifest closure initially trusted caller-supplied artifact bytes

Passing an arbitrary in-memory `artifact_bytes` mapping could demonstrate consistency only relative to that caller-selected mapping. It did not prove that the mapping represented the complete retained qualification directory.

Disposition: CLOSED.

The authoritative hardening path now accepts a qualification package root and scans the real directory itself. The scan rejects path ambiguity, unexpected files through manifest closure, symlinks, special files, size mismatch, and SHA256 mismatch.

The manifest file must physically exist at the declared manifest path and its bytes must equal exact `FPP_JCS_1` canonical bytes for the supplied manifest object. The manifest file remains excluded from its own entry list.

### AR-PQ-007 Critical review identities were not all tied to retained package artifacts

The review contains `execution_report_sha256`, `verifier_build_profile_sha256`, `verifier_binary_sha256`, and `review_basis_sha256` with different hash semantics.

Disposition: CLOSED WITH EXPLICIT SEMANTICS.

The implementation uses these meanings:

```text
execution_report_sha256 = exact retained execution-report file bytes SHA256
verifier_binary_sha256 = exact retained verifier binary bytes SHA256
review_basis_sha256 = exact retained independent-review-basis file bytes SHA256
verifier_build_profile_sha256 = validated verifier build profile internal profile_sha256
```

The first three raw artifact hashes must appear directly in the complete evidence manifest.

The verifier build profile must be supplied as an actual validated object, its internal `profile_sha256` must match both ProviderProfile and QualificationReview, its `binary_sha256` must match the review binary identity, and an exact JSON representation of that build profile object must actually be retained inside the scanned evidence package.

### AR-PQ-008 Metadata capture time could exceed metadata review time

A metadata review used for qualification freshness must not claim knowledge of a source capture obtained after the review event.

Disposition: CLOSED IN THE AUTHORITATIVE PATH.

Every metadata review supplied to authoritative qualification-state derivation is checked so each source-capture `retrieved_at` is at or before the metadata `reviewed_at` time.

### AR-PQ-009 Review-ready state could be derived before the review event

The lower-level state helper did not itself prohibit an `as_of_utc` earlier than a supplied independent review timestamp on the no-decision path.

Disposition: CLOSED IN THE AUTHORITATIVE PATH.

`derive_authoritative_qualification_state` rejects `as_of_utc` earlier than `review.reviewed_at` before producing `QUALIFICATION_REVIEW_READY` or `QUALIFICATION_BLOCKED`.

Qualification execution must use the authoritative hardening path rather than the lower-level convenience state helper directly.

## Production schema validation

The seven production qualification schemas were read from exact committed repository bytes and their Git blob SHA1 values were checked before schema validation.

`jsonschema 4.26.0` `Draft202012Validator.check_schema` returned PASS for all seven:

| Schema | Git blob SHA1 |
| --- | --- |
| `roughtime_production_provider_profile.schema.json` | `9e23151c8f5f7a189a93b428f6c163c8da7f606f` |
| `roughtime_provider_metadata_review.schema.json` | `b2771f0147a358fe1bd1f78f7968579b5c530f35` |
| `roughtime_qualification_decision.schema.json` | `081e74bef41daf234ee1cbfc4d5772c715edcab3` |
| `roughtime_qualification_evidence_manifest.schema.json` | `58d3c583d1b539a60d80cb2206b76ac0de093729` |
| `roughtime_qualification_review.schema.json` | `9615de29a4fc547f82d9f19e939480d60b6d72cb` |
| `roughtime_qualification_state_report.schema.json` | `0d06e1d1b7aa9abb3cc1c9a51205f879882b6315` |
| `roughtime_requalification_event.schema.json` | `691ff3d22a6398f519d728877f367b258e2d18ac` |

This proves Draft 2020-12 schema meta-validity for those exact files. It does not substitute for executable semantic validation or the full repository regression.

## Ed25519 verification backend review

The candidate uses Go standard-library `crypto/ed25519.Verify` and has no private-key or signing interface.

Development-only validation included public RFC 8032 Ed25519 verification vectors, mutation rejection, strict JSON and Base64 failures, binary SHA256 substitution rejection, `go vet`, and same-environment reproducible builds.

Observed development environment:

```text
go_version = go1.23.2
goos = linux
goarch = amd64
development_binary_sha256 = 592089f9f216e22d3e6eec63c836922fc628a91aebfc55d4829ec70fb70c99e9
```

That binary hash is development evidence only. It is not the final production verifier identity.

The final accepted backend still requires a content-addressed build record under the project's accepted Go 1.27.x toolchain and exact committed source tree.

## Regression status

Focused isolated tests exercised the discovered failure paths during repair. They are development evidence.

The exact current branch HEAD has not completed the repository-wide pytest regression in the isolated execution environment because the environment could not resolve `github.com` during the controlled repository access check.

No full-regression PASS claim is made.

The repository-wide regression therefore remains a blocking gate before production qualification execution can become ready.

## Cost and dependency impact

The hardening adds no recurring paid service.

The Ed25519 verifier uses the Go standard library. Python production runtime dependencies remain unchanged. Pytest and jsonschema are development and validation tooling, with no provider or paid-service lock-in introduced by these changes.

## Remaining blockers

Production qualification execution remains `NOT_READY` until at least:

1. the exact committed branch tree passes the complete repository regression and required compile/schema checks;
2. the final Ed25519 verification backend is content-addressed and qualified under the accepted Go 1.27.x toolchain;
3. the external owner authority public-key identity exists without exposing the private key;
4. retained rehearsal evidence is evaluated against the frozen criteria;
5. any required future live repeatability event receives a new exact plan and separate authorization;
6. all three frozen providers independently satisfy the complete frozen qualification criteria;
7. three final ProviderProfiles and their owner-authorized QualificationDecisions are separately reviewed and sealed.

Nothing in this review authorizes any of those execution steps.
