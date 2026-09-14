# Next Accepted Task

Task ID: GEN_001-AC-P5
State: PRE_GENESIS ARCHITECTURE COMPRESSION; P5 CONSOLIDATED VERSIONED IMPLEMENTATION; NETWORK REQUEST NOT AUTHORIZED

## Objective

Implement the accepted P1 through P4 Architecture Compression decisions as one coherent versioned successor Genesis candidate.

P5 is the first implementation phase after the design-control sequence. It must update candidate objects, schemas, validators, readiness controls, abort conditions, tests, and adversarial review together so the resulting compressed profile has one internally consistent security meaning.

P5 remains pre-Genesis and offline. It does not execute production provider qualification, authorize a provider request, create Genesis, create Forecast Ledger state, or issue a prospective forecast.

## Controlling design records

P1:

`docs/GEN_001_GENESIS_ANCHORING_RECONCILIATION_V1.md`

P2:

`docs/GEN_001_TEMPORAL_CLAIM_SEPARATION_V1.md`

P3:

`docs/GEN_001_GENESIS_V1_DEPENDENCY_COMPRESSION_V1.md`

P4:

`docs/GEN_001_PROVIDER_QUALIFICATION_COMPLEXITY_FIREWALL_V1.md`

P5 must preserve every accepted security property in these records.

## Historical candidate boundary

The current effective historical candidate remains:

```text
candidate_object_set_v0_2.json
+ candidate_patch_v0_3.json
+ candidate_patch_v0_4.json
+ candidate_patch_v0_5.json
```

Current effective object count:

```text
22
```

These files are immutable historical candidate material.

P5 must create explicit successor patch material. It must not edit, replace in place, or silently reinterpret any predecessor object.

Retirement and replacement must bind exact predecessor `content_sha256` values.

## P1 implementation requirements

### Acceptance policy

Create a successor AcceptancePolicy with a new semantic policy ID/version.

The successor policy must encode at least:

```text
intermediate_anchor_rule = OPTIONAL_AUDIT_ONLY
final_external_evidence_required = true
final_external_evidence_subject = SIGNED_MANIFEST_ACCEPTANCE
final_external_evidence_role = EXTERNAL_FINAL_VALIDATION_INPUT
bootstrap_root_source = EXTERNAL_TO_CANDIDATE_MANIFEST_GRAPH
blocking_findings_rule = MUST_BE_EMPTY_FOR_ACCEPT
first_execution_rule = STRICTLY_AFTER_FINAL_VALIDATION_AND_EXPLICIT_GENESIS_AUTHORIZATION
```

Retire or replace historical `policy:genesis-acceptance:v1` by exact predecessor hash.

### ManifestAcceptance

Version the ManifestAcceptance schema/validator so the signed object does not require a self-reference to the later final evidence package.

The signed acceptance must bind at least:

```text
candidate_manifest_ref
bootstrap_governance_root_ref
acceptance_rule_ref
required_validation_report_refs
authority_ref
decision
reason_codes
blocking_finding_refs_or_empty
signature_or_signature_ref
```

Independent final validation receives the final external evidence package separately and requires:

```text
final_evidence_subject_ref == signed_manifest_acceptance_ref
```

Optional intermediate bootstrap or manifest anchors cannot satisfy a missing final acceptance anchor.

## P2 implementation requirements

Implement independent derived claims:

```text
EXTERNAL_EXISTENCE_BOUND_VERIFIED
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

Claim states:

```text
VERIFIED
FAILED
UNRESOLVED
NOT_APPLICABLE
```

A stronger claim failure must never rewrite a weaker verified historical fact.

Missing or pending evidence remains `UNRESOLVED` until the applicable frozen rule makes the claim deterministically decidable.

Bitcoin block header time must not become a precise civil-time upper bound.

### Genesis governance mapping

The exact signed ManifestAcceptance is the final governance evidence subject.

Genesis governance final validation requires separate verified external existence and Bitcoin durability facts.

`PRE_OUTCOME_DURABILITY_VERIFIED` and `CONFIRMATORY_PROSPECTIVE_ELIGIBLE` are `NOT_APPLICABLE` to ManifestAcceptance.

### Forecast-cycle mapping

Direct Genesis v1 temporal subjects are:

```text
IssuanceCyclePlan
IssuanceCycleManifest
DurabilityVerificationRecord
```

The exact IssuanceCycleManifest is the forecast-deadline subject and binds complete slot accounting plus exact issued-forecast references.

## P3 implementation requirements

### Dormant unused capability

Do not instantiate Genesis v1 dependencies for:

```text
PublicRandomnessPolicy
FittedState
fitted model state
POSTCOMMIT_PUBLIC_RANDOMNESS
EXTERNALLY_AUDITED_ATTEMPTS
closed-model observability/retrieval paths
multi-method comparison machinery
```

Generic Trust Core interfaces may remain for successor manifests.

### Human review

Retire historical `policy:genesis-human-review:v1` by exact predecessor hash from the successor effective Genesis profile.

Genesis v1 official-source conflict or semantic ambiguity produces deterministic `REVIEW_REQUIRED` or `UNRESOLVED` states. No ReviewDecision may select a resolved value under the compressed Genesis v1 profile.

### Evaluation

Replace `policy:genesis-evaluation:v1` with a minimal successor evaluation policy.

Minimum normative numerical output:

```text
resolved_outcome
forecast_value
absolute_error
squared_error
```

Do not include baseline delta, method comparison, aggregate predictive-skill claims, significance, calibration, or leaderboard semantics.

Cohort accounting must preserve at least:

```text
expected
issued
failed
omitted
ineligible
unresolved
withdrawn
```

P2 temporal claim states remain separately reportable.

### Candidate cardinality

P3 design target is 21 effective objects if P5 introduces no additional Genesis-specific normative policy object.

P5 must recompute exact dependency closure and object count rather than force the target. A different count is acceptable only when justified by an actual required object.

## P4 implementation requirements

### TrustedManifest provider boundary

Add exact bindings for:

```text
deadline_receipt_quorum_policy_ref
provider_profile_refs
qualification_decision_refs
qualification_verifier_contract_ref
```

Genesis v1 requires exactly three ProviderProfiles and three matching QualificationDecisions.

The manifest must not enumerate individual qualification research captures, criteria checks, execution artifacts, or workflow records.

### Qualification decision transitive binding

The pinned qualification verifier must verify through each signed QualificationDecision:

```text
frozen criteria identity and SHA256
exact ProviderProfile
qualification evidence-manifest SHA256
verifier build and binary identity
independent qualification review
metadata-review basis
authority identity and signature
decision_result
```

The Trust Core manifest need not duplicate those fields when the transitive validation is exact and fail-closed.

### Dynamic qualification-state package

Add a content-closed supporting provider-state package boundary.

Working semantic requirements:

```text
provider_id
as_of_utc
provider_profile_ref
qualification_decision_ref
qualification_evidence_manifest_sha256
qualification_verifier_contract_ref
qualification_state_report_sha256
complete metadata-review state inputs through as_of_utc
complete requalification-event state inputs through as_of_utc
content-closed package manifest SHA256
```

The authoritative collector must scan the deterministic retained provider-state store. Caller-selected event subsets are not an authoritative input.

The package/verifier must reject missing, unexpected, duplicate, mismatched, or hash-invalid retained state events.

The package is supporting evidence, not an authority or policy object. It cannot grant qualification by its presence or by a self-asserted state.

No custom transparency log is introduced.

### Provider state at a deadline event

For every consequential wall-clock event:

```text
as_of_utc = frozen_deadline_utc
```

All three manifest-admitted provider states must recompute to:

```text
PRODUCTION_QUALIFIED
```

before the event can use the frozen production-ready three-provider pool.

The receipt quorum remains:

```text
at_least_two_of_three_qualifying_receipts
```

One provider outage never lowers the threshold.

A non-qualified third provider cannot be silently ignored to create an operational two-of-two qualified pool.

### Production receipt validation

Scientific receipt validation must use the exact manifest-admitted ProviderProfile rather than mutable current provider metadata or provider ID alone.

Validate all profile-dependent receipt facts including root key, wire/version semantics, packet/transport/nonce profile, verifier identity, and no-fallback rule.

The profile used by the receipt must equal the profile bound by its QualificationDecision and dynamic qualification-state package.

### Qualification package terminology

Preserve executable ordering:

```text
QualificationEvidencePackage
→ independent review
→ signed QualificationDecision
→ later QualificationRecordSet and dynamic state history
```

The signed decision binds the pre-decision evidence-manifest SHA256. Do not create a circular requirement that the same manifest also cover the later decision bytes.

This is a correctness clarification of package boundaries, not a weakening of `FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1`.

## Schemas and validator surfaces

P5 must identify and version every schema or validation path whose semantics change.

At minimum review and update where applicable:

```text
ManifestAcceptance
TrustedManifest
ValidationReport / temporal claim result structure
Evaluation output/cohort reporting
provider qualification-state package
production Roughtime receipt/admission path
candidate materialization and exact dependency closure
```

Historical schema versions remain retained.

Any change to an existing qualification-supporting schema or validator must be explicitly compatibility-scoped. No production QualificationDecision currently exists, so a concrete correctness repair may introduce a successor schema/contract without migrating a production-qualified provider, but the frozen qualification criteria must not be weakened.

## Readiness matrix

Update readiness controls so the compressed profile closes the actual required gates without resurrecting dormant capability.

At minimum retain independent closure for:

```text
BootstrapGovernanceRoot
TrustedManifest
ValidatorContract
required validation reports
owner signature
final signed-ManifestAcceptance external evidence
independent final validation
separate Genesis authorization gate
three exact ProviderProfiles
three valid signed QualificationDecisions
qualification-verifier contract
qualification evidence-package retention
provider-state package recomputation
initial target/source/parser readiness
OTS Bitcoin strong verification readiness
```

Do not create readiness rows for unused randomness, FittedState, closed-model, multi-method, or scientific human-review capability.

## Abort conditions

Update abort controls to fail closed on at least:

```text
missing/invalid/wrong-subject final ManifestAcceptance evidence
bootstrap/manifest/acceptance/report binding mismatch
P2 required temporal claim FAILED or UNRESOLVED where stronger eligibility requires VERIFIED
missing mandatory cycle or incomplete slot accounting
future information or point-in-time violation
provider profile/decision mismatch
qualification criteria/evidence binding mismatch
provider non-PRODUCTION_QUALIFIED at applicable as_of
qualification-state package incompleteness
wrong provider root/wire/verifier identity
frozen three-provider set not established
```

Optional intermediate Genesis audit anchor failure must not block the compressed profile.

## Required P5 tests

Add focused tests for all new semantics before P6 full regression.

At minimum include:

```text
noncircular ManifestAcceptance final evidence path
wrong final evidence subject rejection
optional intermediate anchor cannot substitute for final evidence
weaker P2 claim preserved when stronger claim fails
UNRESOLVED evidence cannot aggregate to stronger VERIFIED claim
Bitcoin block time rejected as civil-time upper bound
cycle-manifest deadline subject binding
retired Human Review Policy absent from effective successor candidate
ambiguous resolution remains unresolved/review-required without value selection
minimal evaluation exact errors and denominator preservation
candidate dependency closure and exact predecessor retire/replace hashes
three-provider admission plus two-of-three receipt quorum
rehearsal-only provider cannot qualify
expired provider blocks new event
requalification trigger before as_of blocks event
later trigger does not rewrite earlier state
future clean metadata review cannot rescue earlier as_of
omitted retained qualification-state event rejected
forged qualification state report rejected
profile/decision/criteria/evidence hash mismatch rejection
wrong provider root/wire/verifier rejection
duplicate provider identity cannot count twice
one non-qualified provider prevents production-ready three-member set
```

P6 remains responsible for the complete repository regression and synthetic adversarial suite after P5 implementation stabilizes.

## P5 completion conditions

P5 is complete only when:

1. successor candidate material is explicit and append-only;
2. P1 through P4 semantics are implemented consistently across objects, schemas, validators, readiness controls, abort conditions, and focused tests;
3. no historical candidate object is silently reinterpreted;
4. exact dependency closure passes targeted offline validation;
5. P6 can run the full regression without unresolved design ambiguity;
6. Genesis remains not started and provider qualification remains unexecuted.

## Out of scope

P5 does not:

1. execute production provider qualification;
2. request Roughtime or RFC3161 traffic;
3. qualify any provider;
4. create the final owner ProviderProfile or QualificationDecision;
5. access the Genesis private key;
6. construct or authorize Forecast Ledger Genesis;
7. issue a prospective forecast;
8. merge PR #6;
9. change the frozen provider criteria to make qualification easier;
10. reopen deferred stochastic, closed-model, universal forecasting, or Product Layer features.

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

## Network boundary

```text
network_authorized = false
Roughtime provider requests authorized by this task = 0
RFC3161 requests authorized by this task = 0
production qualification requests authorized by this task = 0
```

No prior rehearsal or qualification authorization may be reused.

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

The Genesis Ed25519 private key must not be accessed, read, copied, displayed, uploaded, transmitted, logged, referenced, or processed. Only the public key may enter project objects at a later separately authorized governance step.
