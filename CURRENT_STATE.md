# Current State

Date: 2026-09-12
Project: Forecast Provenance Project
State: GENESIS_READINESS_DESIGN

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

## Pre-rehearsal Roughtime pool

Current pool:

1. `roughtime.se`
2. `time.txryan.com`
3. `TimeNL-Roughtime`

Cloudflare-Roughtime-2 is removed from the current pool after a concrete unresolved IETF interoperability issue was identified. It remains historical review evidence only.

Public entry evidence is sufficient to continue tooling qualification for all three current candidates.

No provider request is authorized.

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

A strict low-level wrapper build and offline fixture run under Go 1.27.x is still required before any network authorization. Every future rehearsal plan must bind an exact content-addressed verifier build profile and an exact pre-attempt retry-state snapshot.

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

The rehearsal script now uses append-only event directories for stamp, upgrade and verify steps so tool versions, output, proof hashes and failed attempts are not overwritten.

Strong verification still requires owner-controlled Bitcoin Core. RPC credentials remain local and are never retained.

## RFC 3161

Checker version 1.3 / report schema 1.2 remain closed absent a concrete new correctness or security defect.

Retained historical reports remain unchanged.

Commercial Sectigo and Signicat qualification work remains paused for the zero-cost Genesis minimum profile.

## Other external blockers

Still required:

1. owner-generated bootstrap Ed25519 public key only;
2. pinned Roughtime verifier/toolchain build and strict offline fixtures;
3. separately authorized non-forecast Roughtime rehearsals and final ProviderProfiles;
4. OTS/Bitcoin strong rehearsal and final verifier profile;
5. three retrospective official BLS/BEA fixture byte sets and adapter reports;
6. final clean test report and ValidatorContract;
7. final BootstrapGovernanceRoot, TrustedManifest, ManifestAcceptance, external evidence and adversarial review.

## Standards-transition gate

Roughtime draft-19 is in the RFC publication process. Any change in final wire version, provider protocol profile, endpoint, key, TYPE behavior, transport requirement or verifier semantics before final freeze requires read-only re-review and a versioned profile change. No automatic migration is permitted.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```

No Roughtime request, RFC3161 request, prospective forecast, production ProviderProfile, Genesis acceptance or Forecast Ledger creation is authorized by this state.
