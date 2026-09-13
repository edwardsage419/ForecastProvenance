# Current State

Date: 2026-09-13
Project: Forecast Provenance Project
State: GENESIS_READINESS_DESIGN

Current formal branch and state snapshot basis:

```text
branch = design/gen-001
snapshot_basis_commit = d72608944cf89df113e7a8abae101159a591ceb7
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

Cloudflare-Roughtime-2 is removed from the current pool after a concrete unresolved IETF interoperability issue was identified. It remains historical review evidence only.

The repository-owned execution orchestrator is published and its offline control, failure-path, schema, and regression checks passed before the retained rehearsal.

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

Current nonce profile:

`FPP_ROUGHTIME_NONCE_V2`

It produces an exact 32-byte SHA-256 nonce from the raw 32-byte subject SHA256 and fresh 32-byte provider-specific client randomness.

Current request profile:

```text
STANDARD_1024_BODY
UDP_ONLY
all three providers evaluated; each is attempted only when persistent retry state permits
2 receipts required
protocol fallback prohibited
packet fallback prohibited
transport fallback prohibited
maximum 2 attempts per provider
persistent exponential retry state per root
properly signed but project-nonqualifying response stops retry and resets protocol backoff
```

Draft labels and verifiable wire profiles are recorded separately because drafts 12 through 19 share the testing wire version `0x8000000c`.

The current pinned verifier candidate is:

```text
github.com/tannerryan/roughtime
tag v1.27.0
commit 56b346a16cd7e8317bb0d24f1ec15549cf93a4c9
```

The vendored strict low-level wrapper was qualified offline under Go 1.27.x and the executed rehearsal bound its exact content-addressed verifier build profile and pre-attempt retry-state snapshot. Future events must independently repeat the required freshness checks and bind their own exact plan, authorization, build profile, and retry-state snapshot.

The Merkle fixture engineering gap is closed. Effective deterministic offline multi-leaf coverage exists for typed hash-first, typed node-first, untyped draft-12 node-first, and negative wrong-order rejection. Each positive ordering fixture uses a two-leaf tree and demonstrates a PATH of exactly 1 hash / 32 bytes. This fixture completion did not itself qualify a provider.

## Evidence validation

Roughtime JSON Schemas are descriptive interoperability constraints.

Cross-field acceptance is controlled by the executable semantic validator, which recomputes:

```text
plan and authorization content hashes
nonce derivation
raw request and response hashes
midpoint + radius upper bound
retry request-byte identity
provider qualification count
final quorum status
sealed report and receipt hashes
```

Schema-valid but semantically inconsistent evidence fails closed. Semantic validation is not a substitute for cryptographic replay: every qualifying raw request/response/nonce/profile tuple must also replay successfully through the pinned low-level verifier, and each qualifying receipt must bind a verification transcript hash.

## OpenTimestamps

OTS remains the Bitcoin durability layer.

The rehearsal script uses append-only event directories for stamp, upgrade and verify steps so tool versions, output, proof hashes and failed attempts are not overwritten.

Strong verification still requires owner-controlled Bitcoin Core. RPC credentials remain local and are never retained.

## RFC 3161

Checker version 1.3 / report schema 1.2 remain closed absent a concrete new correctness or security defect.

Retained historical reports remain unchanged.

Commercial Sectigo and Signicat qualification work remains paused for the zero-cost Genesis minimum profile.

## Roughtime production qualification

```text
PRODUCTION_QUALIFICATION_CRITERIA = FROZEN_V1
criteria_id = FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1
criteria_sha256 = 88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```

The governance freeze is recorded in `docs/GEN_001_ROUGHTIME_PRODUCTION_QUALIFICATION_GOVERNANCE_FREEZE_V1.md`. It resolves pilot admissibility, SLA policy, production-use permission evidence, 30-day live freshness, two-event repeatability separated by at least seven days, 90-day metadata review, positive root/issuance independence evidence, the two-vote common-dependency threshold, and manifest sealing plus qualification authority.

The complete evidence manifest uses `FPP_JCS_1` and omits non-applicable optional fields instead of using JSON null. The manifest excludes itself and is sealed by an external SHA256 bound by the final QualificationDecision.

Qualification execution remains blocked until separately reviewed schemas and validators exist for production ProviderProfile, qualification decision/state, complete evidence manifest, and independent qualification review records. The required owner public-key identity must also exist before an owner-authorized QualificationDecision can be issued.

Retained rehearsal evidence may later be evaluated against the frozen criteria. It remains `NON_FORECAST_REHEARSAL`, `prospective_eligible = false`, and cannot automatically qualify any provider.

## Other external blockers

Still required:

1. owner-generated bootstrap Ed25519 public key only;
2. production ProviderProfile, qualification decision/state, complete evidence manifest, and independent review schemas plus validators;
3. independent frozen-criteria production qualification of the three current Roughtime providers and final sealed ProviderProfiles;
4. OTS/Bitcoin strong rehearsal and final verifier profile;
5. three retrospective official BLS/BEA fixture byte sets and adapter reports;
6. final clean test report and ValidatorContract;
7. final BootstrapGovernanceRoot, TrustedManifest, ManifestAcceptance, external evidence and adversarial review.

## Standards-transition gate

Roughtime draft-19 is in the RFC publication process with intended Experimental status. Any change in final wire version, provider protocol profile, endpoint, key, TYPE behavior, transport requirement or verifier semantics before final freeze requires read-only re-review and a versioned profile change. No automatic migration is permitted.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
network_authorized = false
```

No Roughtime request, RFC3161 request, prospective forecast, production ProviderProfile, QualificationDecision, Genesis acceptance or Forecast Ledger creation is authorized by this state.
