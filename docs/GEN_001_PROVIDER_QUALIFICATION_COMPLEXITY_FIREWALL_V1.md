# GEN_001 Provider Qualification Complexity Firewall V1

Date: 2026-09-14
Status: ARCHITECTURE_COMPRESSION_P4_DESIGN_CONTROL
Classification: PRE_GENESIS_DESIGN
Prospective eligible: false
Genesis effect: none
Network authorization: none
Basis commit: `9964f1624096e228cc1789fe2bcb607a0c667ff8`

## Purpose

This record closes Architecture Compression P4 at the design level.

P4 establishes a strict boundary between Forecast Trust Core and the Roughtime provider-qualification supporting subsystem. Forecast Trust Core consumes only the minimum frozen qualification facts needed to decide whether deadline evidence came from an admitted provider state. Qualification research, evidence collection, diagnostics, review mechanics, requalification workflow, and other supporting machinery remain outside the Trust Core dependency graph.

Historical qualification criteria, schemas, validators, rehearsal evidence, and candidate semantics remain unchanged. P4 does not qualify a provider and does not execute a network request. P5 must implement the firewall together with the accepted P1 through P3 changes.

## Retained qualification state

```text
PRODUCTION_QUALIFICATION_CRITERIA = FROZEN_V1
criteria_id = FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1
criteria_sha256 = 88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
ACTIVE_MAINLINE = PAUSED
```

Retained rehearsal evidence remains permanently `NON_FORECAST_REHEARSAL` and `prospective_eligible = false`.

## Existing qualification subsystem

The current supporting subsystem already separates seven structures:

```text
RoughtimeProductionProviderProfile
RoughtimeQualificationEvidenceManifest
RoughtimeProviderMetadataReview
RoughtimeQualificationReview
RoughtimeQualificationDecision
RoughtimeRequalificationEvent
RoughtimeQualificationStateReport
```

The signed `RoughtimeQualificationDecision` transitively binds the exact criteria identity, exact ProviderProfile reference, complete qualification evidence-manifest SHA256, verifier build and binary identity, independent qualification review, decision-bound metadata review, decision result, decision timestamp, and external authority identity.

The current hardening interface correctly treats `RoughtimeQualificationStateReport` as derived output rather than authority. Authoritative state is recomputed from immutable qualification inputs.

## P4 security findings

### 1. Static decision binding is already strong enough for most Trust Core needs

Forecast Trust Core does not need to duplicate the complete criteria check matrix, individual research captures, execution transcripts, retry-state records, diagnostic files, or review notes inside TrustedManifest.

A valid signed `QualificationDecision` plus its exact `ProviderProfile` already gives the qualification verifier a cryptographic path to the frozen criteria, evidence manifest, verifier identity, independent review, and authority decision.

Duplicating those internals in TrustedManifest would increase coupling without adding an independent security fact.

### 2. Qualification state is dynamic after the signed decision

A signed `PRODUCTION_QUALIFIED` decision is not sufficient by itself for a later deadline event.

Under the frozen criteria, a provider can later become:

```text
QUALIFICATION_EXPIRED
REQUALIFICATION_REQUIRED
QUALIFICATION_BLOCKED
```

Metadata review freshness and requalification triggers therefore require an explicit historical `as_of_utc` state derivation for each consequential deadline event.

### 3. Current state recomputation has an input-completeness boundary

The current authoritative state function correctly filters metadata reviews and requalification events to those whose event times are at or before `as_of_utc`. A later clean metadata review cannot retroactively rescue an earlier expired state, and a later requalification event does not rewrite an earlier state before its recorded detection time.

However, the current API receives the metadata-review and requalification-event sequences from its caller. Recomputing a correct result from an incomplete caller-supplied sequence does not prove that the supplied sequence was complete.

A caller that silently omits a retained disqualifying event can therefore create an incomplete recomputation basis unless the state-input set itself is content-closed and independently checked.

P4 treats this as a concrete Trust Core boundary requirement. P5 must close the retained state-input set before a production qualification result can be consumed by Forecast Trust Core.

### 4. Qualification evidence package terminology must avoid a decision self-reference

The signed QualificationDecision binds the qualification evidence-manifest SHA256. Therefore the content-closed evidence-manifest package must be finalized before the signed decision exists.

The later signed decision cannot also be a file covered by that same manifest without circularity.

P4 uses these terms:

```text
QualificationEvidencePackage
    = pre-decision content-closed evidence set bound by the evidence manifest

QualificationRecordSet
    = QualificationEvidencePackage plus ProviderProfile, independent review,
      signed QualificationDecision, later metadata reviews, requalification events,
      and derived state reports
```

This preserves the frozen requirement that all qualification records are retained while keeping the cryptographic order executable. P5 should align documentation and implementation terminology without weakening any frozen qualification criterion.

## P4 firewall decision

### A. TrustedManifest consumes only the static provider admission boundary

The compressed Genesis TrustedManifest should bind, directly or through an exact manifest section:

```text
deadline_receipt_quorum_policy_ref
provider_profile_refs
qualification_decision_refs
qualification_verifier_contract_ref
```

For Genesis v1:

```text
len(provider_profile_refs) = 3
len(qualification_decision_refs) = 3
```

Each decision must pair exactly with one admitted ProviderProfile.

The Trust Core manifest does not separately duplicate:

```text
qualification criteria check matrix
qualification evidence entry list
independent review fields
metadata source captures
execution orchestration records
rehearsal orchestration records
network diagnostics
operator research notes
requalification scheduling logic
```

Those remain supporting-subsystem evidence.

### B. Criteria and initial evidence identity are transitively verified

TrustedManifest does not need separate top-level copies of `criteria_id`, `criteria_sha256`, or `evidence_manifest_sha256` when all of these conditions hold:

1. the exact signed QualificationDecision is content-bound by TrustedManifest;
2. the QualificationDecision is validated against the exact ProviderProfile;
3. the decision signature is validated against the externally supplied accepted authority;
4. the qualification verifier checks the decision's exact frozen criteria binding;
5. the qualification verifier checks the exact evidence-manifest package closure.

The decision remains the authoritative transitive binding for these facts.

### C. Dynamic provider admission is recomputed at the historical deadline

For each consequential wall-clock deadline event, provider qualification state is evaluated with:

```text
as_of_utc = frozen_deadline_utc
```

This applies to the event's exact frozen deadline, including cycle-plan precommitment, cycle-manifest deadline evidence, and the P2 durability-completion deadline where applicable.

Using the frozen deadline is conservative and deterministic. It does not rely on the local runtime clock or Bitcoin block time.

The qualification verifier ignores state events later than `as_of_utc` when reconstructing the historical provider state.

### D. All three frozen providers must remain admitted for a new Genesis v1 deadline event

The frozen provider-set criteria require all three pool members to be individually production qualified. The receipt threshold then requires two qualifying receipts from that admitted three-member pool.

Therefore the successor Genesis v1 admission rule is:

```text
for each of the three manifest-admitted providers:
    qualification_state(as_of=frozen_deadline_utc) == PRODUCTION_QUALIFIED

then:
    receipt_quorum = at_least_two_of_three_qualifying_receipts
```

A provider outage does not change qualification state and does not lower the receipt threshold.

A provider in `QUALIFICATION_EXPIRED`, `REQUALIFICATION_REQUIRED`, `QUALIFICATION_BLOCKED`, or any non-qualified state prevents a new event from being treated as operating under the frozen production-ready three-provider set.

This avoids silently converting the intended two-of-three system into an operational two-of-two system.

### E. Historical state is immutable with respect to later provider changes

A provider expiration or requalification trigger recorded after a historical event's `as_of_utc` does not rewrite that earlier provider-state conclusion.

A requalification trigger or qualification-relevant metadata change at or before the historical `as_of_utc` must fail closed for that event.

Current provider usability and historical provider admissibility are separate claims.

## Content-closed dynamic state evidence

P5 should add one supporting evidence package boundary for historical provider-state recomputation. It is not a new governance policy and it does not grant qualification by itself.

Working name:

```text
RoughtimeProviderQualificationStatePackage
```

Its exact schema name may change during P5, but the semantic requirements are fixed here.

The package must bind at least:

```text
provider_id
as_of_utc
provider_profile_ref
qualification_decision_ref
qualification_evidence_manifest_sha256
qualification_verifier_contract_ref
qualification_state_report_sha256
complete retained metadata-review set relevant through as_of_utc
complete retained requalification-event set relevant through as_of_utc
content-closed package manifest SHA256
```

The package manifest must use deterministic canonical paths, exact file hashes and byte lengths, reject missing or unexpected files, reject symlinks and traversal, and permit independent recomputation of the state report.

The package may reference the already retained initial QualificationEvidencePackage by exact manifest hash instead of duplicating all original live qualification bytes.

The qualification verifier must verify that the dynamic state package corresponds to the exact manifest-admitted ProviderProfile and QualificationDecision before returning an admission result.

## State-input completeness rule

The qualification subsystem must maintain a deterministic retained state-event store for each ProviderProfile.

When constructing a historical state package, the authoritative collector must scan that retained store rather than accept a caller-selected in-memory event subset.

The package must include every retained metadata review and requalification event applicable to the profile whose recorded event time is at or before `as_of_utc`.

The package builder and verifier must fail closed on:

```text
missing retained event
unexpected unclassified state event
duplicate event
profile mismatch
noncanonical ordering
hash mismatch
state-report mismatch
```

This requirement closes omission inside the retained qualification state history. It does not claim omniscience about an external provider change that the project had not yet detected and recorded.

No custom transparency log is introduced by P4.

## Minimal Trust Core qualification result

Forecast Trust Core should consume a small adapter result equivalent to:

```text
provider_profile_ref
qualification_decision_ref
qualification_verifier_contract_ref
qualification_state_package_sha256
as_of_utc
qualification_state
```

For a qualifying Genesis v1 deadline event:

```text
qualification_state = PRODUCTION_QUALIFIED
```

All other states fail closed for provider admission.

The Trust Core validator does not parse the internal criteria matrix or research workflow to reach that state. It invokes the exact pinned qualification verifier contract over the retained supporting evidence and consumes its deterministic result.

## Receipt-validation boundary

The production deadline receipt validator must receive the exact manifest-admitted ProviderProfile rather than resolve provider trust from a mutable current provider registry.

It must verify at least the receipt fields whose trust meaning depends on the ProviderProfile, including:

```text
provider identity
root public key
wire/version profile
TYPE/SRV behavior where applicable
packet profile
transport profile
nonce profile
verifier-build identity
no-fallback rule
```

The receipt provider profile must equal the exact profile used by the corresponding qualification decision and qualification-state package.

Two receipts can count as two quorum votes only when they map to two distinct manifest-admitted provider identities from the frozen three-member set.

The qualification subsystem remains responsible for verifying the frozen `INDEPENDENCE` and `COMMON_DEPENDENCY` criteria that make those provider identities admissible as independent groups. Forecast Trust Core does not duplicate that review matrix.

## Qualification verifier contract

P5 must freeze an exact qualification-verifier contract or implementation binding used by Forecast Trust Core.

That contract must cover at least:

1. ProviderProfile validation;
2. QualificationEvidencePackage closure;
3. independent review cross-binding;
4. QualificationDecision signature and authority validation;
5. criteria identity verification;
6. metadata-review chronology and freshness;
7. requalification-event handling;
8. dynamic state-package completeness;
9. authoritative state recomputation;
10. rejection of a forged standalone state report.

Changing this contract in a way that can alter provider admission requires versioned review and, where the accepted manifest depends on it, a successor manifest.

Internal refactoring that provably preserves the frozen output contract does not automatically expand Forecast Trust Core.

## What remains outside Forecast Trust Core

The following remain supporting-subsystem internals:

```text
provider discovery
metadata research workflow
source-capture acquisition mechanics
network diagnostics
rehearsal orchestration
production qualification execution orchestration
retry-state diagnostics for qualification runs
criterion-by-criterion operator notes
review workflow mechanics
requalification scheduling automation
continuity monitoring implementation
provider-contact workflow
packaging implementation details beyond the frozen package contract
```

These materials remain retained when required by the frozen qualification criteria. Exclusion from Trust Core does not authorize deletion and does not weaken qualification standards.

## Genesis readiness implications

Genesis provider readiness requires all three provider profiles to have:

1. exact sealed ProviderProfile identity;
2. valid signed `PRODUCTION_QUALIFIED` QualificationDecision under the accepted authority;
3. valid transitive binding to the frozen criteria and complete initial evidence package;
4. a passing qualification-state recomputation at the Genesis readiness `as_of_utc` under the pinned qualification verifier contract;
5. no active disqualifying state at that `as_of_utc`.

This Genesis readiness check does not guarantee future cycle admission. Every future deadline event re-evaluates historical provider state under its own frozen deadline.

## P5 implementation map

P5 must implement P1 through P4 together and should include at least these provider-firewall changes.

### TrustedManifest

Add exact frozen bindings for:

```text
provider_profile_refs
qualification_decision_refs
qualification_verifier_contract_ref
```

Do not add individual metadata reviews, research captures, review matrices, or qualification execution artifacts as top-level manifest dependencies.

### Supporting qualification schemas

Add or version a content-closed dynamic qualification-state package schema and exact collector/verifier contract.

Preserve the current ProviderProfile, QualificationDecision, initial evidence-manifest, review, metadata-review, requalification-event, and state-report schemas as historical supporting-subsystem material unless a concrete correctness repair requires a versioned successor.

### Qualification validator

Add one authoritative adapter callable from Trust Core that validates the exact static decision chain, content-closed dynamic state package, external authority input, and `as_of_utc`, then returns a deterministic provider admission result.

The adapter must not accept caller-selected event subsets as authoritative state evidence.

### Deadline receipt validator

Replace mutable/global provider lookup as the scientific trust basis with exact manifest-admitted ProviderProfile input plus validated provider-admission result.

Historical receipt validation must fail on profile mismatch, decision mismatch, criteria mismatch, unqualified state, wrong root, wrong wire profile, or wrong verifier identity.

### Readiness matrix

Retain provider qualification as an independent supporting subsystem gate. Readiness should require:

```text
three exact ProviderProfiles
three valid signed QualificationDecisions
exact qualification-verifier contract
complete initial qualification evidence packages
passing dynamic state-package recomputation
three-provider set PRODUCTION_QUALIFIED at readiness as_of
```

Do not add every qualification workflow artifact as a separate Trust Core readiness row.

### Abort conditions

Fail closed when:

```text
any required provider decision is absent or invalid
any provider is non-PRODUCTION_QUALIFIED at the applicable as_of
state-input package completeness fails
provider profile differs from manifest
qualification criteria or evidence-manifest binding fails
qualification verifier contract differs from manifest
provider root or wire profile differs from admitted profile
frozen three-provider set cannot be established
```

### Tests

P5/P6 must cover at least:

```text
valid three-provider admission and two-of-three receipt quorum
rehearsal-only evidence cannot qualify
blocked QualificationDecision
expired metadata review
future metadata review cannot retroactively rescue earlier as_of
requalification event before as_of blocks admission
requalification event after as_of does not rewrite historical admission
omitted retained requalification event rejected by state-package closure
forged state report rejected by recomputation
profile/decision cross-binding mismatch
criteria hash mismatch
evidence-manifest hash mismatch
wrong authority signature
wrong provider root/wire/verifier identity
duplicate provider identity cannot count twice
one non-qualified provider prevents production-ready three-provider set
provider outage does not lower two-of-three receipt threshold
```

## P4 completion state

```text
P4_PROVIDER_QUALIFICATION_COMPLEXITY_FIREWALL = COMPLETE
QUALIFICATION_SUBSYSTEM_SEPARATE = YES
TRUST_CORE_DIRECT_QUALIFICATION_WORKFLOW_DEPENDENCY = NO
DYNAMIC_STATE_INPUT_COMPLETENESS_REQUIRED = YES
CURRENT_V0_5_CANDIDATE_ALIGNED = NO
CURRENT_VALIDATOR_ALIGNED = NO
CURRENT_READINESS_MATRIX_ALIGNED = NO
P5_VERSIONED_IMPLEMENTATION_REQUIRED = YES
GENESIS_READY = NO
```

## Network and qualification boundary

P4 performs no provider request and does not reopen production qualification execution.

```text
network_authorized = false
Roughtime provider requests authorized = 0
RFC3161 requests authorized = 0
production qualification requests authorized = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```

## Safety boundary

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production forecasting = PROHIBITED
```

This record does not authorize Genesis, Forecast Ledger creation, forecast issuance, provider qualification execution, or any live provider request.

The Genesis Ed25519 private key remains outside repository, GitHub, CI, ChatGPT, Codex, logs, prompts, fixtures, and third-party systems. Only the public key may enter project objects under a later separately authorized governance step.
