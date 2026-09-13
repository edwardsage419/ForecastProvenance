# Current State

Date: 2026-09-13
Project: Forecast Provenance Project
State: GENESIS_READINESS_DESIGN

Current formal branch and state snapshot basis:

```text
branch = design/gen-001
snapshot_basis_commit = cd970120283d2d5efa32f47f95e38d68ce796292
```

The commit containing `CURRENT_STATE.md` must be identified from Git metadata; this document does not embed its own commit SHA.

## Native scientific state

```text
Native prospective forecasts = 0
Native outcome resolutions = 0
Native evaluation results = 0
Native failure records = 0
Accepted Genesis anchors = 0
Forecast Ledger = NOT CREATED
Forecast Ledger Genesis = NOT CREATED
```

## Trust Core

FTC_001 normative design: FROZEN, version 0.4.

FTC_002 synthetic implementation: COMPLETE AND MERGED.

ADV001 through ADV096 remain the synthetic adversarial baseline.

## GEN_001

PR #6 remains Draft and unmerged.

Current repository-side design target:

```text
zero recurring cash cost minimum profile
FPP_TIME_EVIDENCE_V1
policy:deadline-receipt-quorum:v3
2 of 3 frozen independent Roughtime groups
OpenTimestamps + Bitcoin durability
owner Ed25519 bootstrap authority
RFC3161 = OPTIONAL_AUXILIARY
```

Current effective candidate lineage:

```text
v0.2 base
+ v0.3 patch
+ v0.4 patch
+ v0.5 patch
```

Effective object count remains 22.

## Roughtime pool and completed non-forecast rehearsal

Current pool:

1. `roughtime.se`
2. `time.txryan.com`
3. `TimeNL-Roughtime`

Cloudflare-Roughtime-2 remains removed from the current pool after an unresolved IETF interoperability issue was identified. It remains historical review evidence only.

One separately authorized `NON_FORECAST_REHEARSAL` has completed against the frozen pool. All three providers returned a qualifying first-attempt response. The retained report status and independent review state are:

```text
REHEARSAL_VERIFIED = YES
REHEARSAL_EVIDENCE_REVIEW = PASS
qualifying provider results = 3 of 3
classification = NON_FORECAST_REHEARSAL
prospective_eligible = false
```

The executed plan hash is `d307402fafa351aded623f701ab7736fd2658756a0e10d04de61a92e38888d8d`. Its exact authorization hash, `293979744f5d3494f7b270a1f100020b916971f802f52eab09390470a15a8347`, was consumed and cannot be reused.

The older plan `99ae0b4ce62d106f9ca0cc049f3766a3a39dd28c3d788d134d7f8923c6e278cd` remains `NOT EXECUTED / SUPERSEDED FOR FUTURE NETWORK EXECUTION`; no authorization was created for it.

No new provider request is authorized. Repository development-time `network_authorized` remains false.

## Protocol freeze

Current nonce profile is `FPP_ROUGHTIME_NONCE_V2`.

Current request profile remains:

```text
STANDARD_1024_BODY
UDP_ONLY
2 receipts required
protocol fallback prohibited
packet fallback prohibited
transport fallback prohibited
maximum 2 attempts per provider
persistent exponential retry state per root
```

The current pinned strict Roughtime verifier lineage remains:

```text
github.com/tannerryan/roughtime
tag v1.27.0
commit 56b346a16cd7e8317bb0d24f1ec15549cf93a4c9
```

The vendored strict low-level wrapper was qualified offline under Go 1.27.x before the retained rehearsal. The Merkle fixture engineering gap remains closed with deterministic multi-leaf coverage for typed hash-first, typed node-first, untyped draft-12 node-first, and negative wrong-order rejection.

## OpenTimestamps

OTS remains the Bitcoin durability layer.

Strong verification still requires owner-controlled Bitcoin Core. RPC credentials remain local and are never retained.

## RFC 3161

Checker version 1.3 and report schema 1.2 remain closed absent a concrete new correctness or security defect.

Commercial Sectigo and Signicat qualification work remains paused for the zero-cost Genesis minimum profile.

## Roughtime production qualification

```text
PRODUCTION_QUALIFICATION_CRITERIA = FROZEN_V1
criteria_id = FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1
criteria_sha256 = 88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e
PRODUCTION_QUALIFICATION_OBJECT_MODEL = PUBLISHED_HARDENED_CANDIDATE
PRODUCTION_QUALIFICATION_SCHEMA_META_VALIDATION = PASS_7_OF_7
PRODUCTION_QUALIFICATION_ADVERSARIAL_HARDENING = CURRENT_KNOWN_FINDINGS_CLOSED
PRODUCTION_QUALIFICATION_REPOSITORY_REGRESSION = PENDING
PRODUCTION_QUALIFICATION_SIGNATURE_BACKEND = PUBLISHED_CANDIDATE_NOT_FINAL_QUALIFIED
PRODUCTION_QUALIFICATION_SIGNATURE_BACKEND_QUALIFICATION_HARNESS = PUBLISHED_CANDIDATE
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```

The governance criteria are frozen by `docs/GEN_001_ROUGHTIME_PRODUCTION_QUALIFICATION_GOVERNANCE_FREEZE_V1.md`.

The production qualification object model covers production ProviderProfile candidates, complete evidence manifests, operator metadata reviews, independent qualification reviews, owner-authorized QualificationDecision records, append-only requalification events, and deterministic qualification state reports.

The authoritative hardening path now requires a real qualification evidence package root. It scans the physical package itself, requires an actual manifest file whose bytes are exact `FPP_JCS_1` canonical manifest bytes, and then validates exact file-set closure, file sizes and SHA256 values. A caller-selected in-memory artifact list is insufficient proof of package completeness.

Review cross-binding now requires:

```text
all criterion evidence hashes retained by the complete package
execution_report_sha256 retained as raw file SHA256
verifier_binary_sha256 retained as raw binary SHA256
review_basis_sha256 retained as raw file SHA256
validated verifier build profile internal profile_sha256 bound to ProviderProfile and review
verifier build profile binary_sha256 bound to the retained verifier binary
exact verifier build profile JSON object retained inside the package
executor and reviewer event identities distinct
```

Temporal hardening requires every metadata source capture to exist no later than its metadata review time. The authoritative state path also rejects `as_of_utc` earlier than the independent qualification review.

A state report has no independent authority. Production state is accepted only after exact recomputation through the authoritative hardening path.

The current adversarial review is recorded in `docs/GEN_001_ROUGHTIME_PRODUCTION_QUALIFICATION_ADVERSARIAL_REVIEW_2026_09_13.md`.

## Production schema validation

The exact committed bytes of all seven production qualification schemas completed Draft 2020-12 meta-validation with `jsonschema 4.26.0`:

```text
7 PASS
0 FAIL
```

The checked Git blob identities are retained in the adversarial review document.

This closes schema meta-validity only. It does not replace semantic validation or the exact current-HEAD full repository regression.

## QualificationDecision and Ed25519 verification

The QualificationDecision signature projection is `FPP_ROUGHTIME_QUALIFICATION_DECISION_V1`.

Validation receives the expected authority ID and exact Ed25519 public key from outside the decision object. Repository code contains no signing path and receives no private key.

The verification-only Ed25519 backend candidate uses Go standard-library `crypto/ed25519.Verify` and a Python adapter that pins the executable by SHA256.

A path-substitution review found and repaired a relative executable path issue. The adapter now resolves the accepted executable to an absolute canonical path before invocation and checks its SHA256 both before and after execution.

Development-only validation included RFC 8032 public verification vectors, mutation rejection, strict JSON/Base64 failure paths, binary hash substitution rejection, `go vet`, and same-environment reproducible builds.

Observed development build:

```text
go_version = go1.23.2
goos = linux
goarch = amd64
development_binary_sha256 = 592089f9f216e22d3e6eec63c836922fc628a91aebfc55d4829ec70fb70c99e9
```

This development hash is not a frozen production verifier identity. A dedicated content-addressed qualification harness is now published in `scripts/genesis/qualify_ed25519_verifier.py` with build-profile schema `schemas/ed25519_verifier_build_profile.schema.json`. The harness requires exact Go 1.27.x, a closed three-file verifier source tree, a single-module graph, the frozen required PASS set, two byte-for-byte reproducible builds with distinct caches, and a content-addressed binary/build profile. Current development validation confirmed that Go 1.23.2 fails closed and writes no qualification profile. The qualification harness also binds the exact repository HEAD SHA and each verifier source file Git blob SHA1, rejecting source bytes that do not match the committed tree. Final qualification under the accepted Go 1.27.x toolchain has not been executed.

## Regression state

The final readiness harness uses pytest so unittest-style and pytest-style tests are both collected. Pytest is a pinned test-only dependency. Production runtime dependencies remain empty.

Focused isolated tests were used to reproduce and close the adversarial findings above. These focused results are development evidence only.

The exact current branch HEAD has not completed the full repository-wide regression in the isolated execution environment. The latest controlled direct repository access attempt failed because the environment could not resolve `github.com`. No retry loop was used and no PASS claim is made.

`PRODUCTION_QUALIFICATION_REPOSITORY_REGRESSION` therefore remains `PENDING`.

## Remaining Roughtime production blockers

Before production qualification execution can become ready, the project still requires:

1. complete repository regression and required compile checks on the exact committed branch tree;
2. final content-addressed Ed25519 verification backend build qualification under the accepted Go 1.27.x toolchain;
3. owner-generated bootstrap Ed25519 public key only, with the private key remaining outside repository and connected tooling;
4. frozen-criteria evaluation of retained rehearsal evidence;
5. new separately authorized live repeatability evidence when required by the frozen criteria;
6. current production-use permission, continuity, independence, freshness, operational, and common-dependency evidence for all three providers;
7. final separate independent reviews, ProviderProfiles, and owner-authorized QualificationDecisions for all three providers.

No production ProviderProfile or QualificationDecision has been instantiated.

Retained rehearsal evidence remains `NON_FORECAST_REHEARSAL`, `prospective_eligible = false`, and cannot automatically qualify any provider.

## Other external blockers

Still required outside the Roughtime implementation work:

1. OTS/Bitcoin strong rehearsal and final verifier profile;
2. three retrospective official BLS/BEA fixture byte sets and adapter reports;
3. final clean test report and ValidatorContract;
4. final BootstrapGovernanceRoot, TrustedManifest, ManifestAcceptance, external evidence, and final adversarial review.

## Standards-transition gate

Roughtime draft-19 remains in the RFC publication process with intended Experimental status. Any change in final wire version, provider protocol profile, endpoint, key, TYPE behavior, transport requirement, or verifier semantics before final freeze requires read-only re-review and a versioned profile change. No automatic migration is permitted.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
production forecasting = PROHIBITED
network_authorized = false
```

No Roughtime request, RFC 3161 request, prospective forecast, production ProviderProfile, QualificationDecision, Genesis acceptance, or Forecast Ledger creation is authorized by this state.
