# GEN_001 P7 Post-P6 Repair Findings

Date: 2026-09-16
Status: PRE_GENESIS_REPAIR_CONTROL
Classification: PRE_GENESIS_DESIGN_AND_IMPLEMENTATION_REPAIR
Prospective eligible: false
Genesis effect: none
Network authorization: none
Basis commit: `aa453268e4420dff6ea5ba3208e286d158f52e32`
Repair branch: `repair/p7-authority-contracts`

## Purpose

This record preserves newly discovered correctness and specification findings identified after the successful historical P6 execution. It does not rewrite the historical fact that P6 passed on its recorded exact input HEAD. It records that later static review found authority-boundary gaps not covered by that execution and pauses P7 architectural decisions until the repair receives fresh regression.

The project remains pre-Genesis. No provider request, production qualification execution, Genesis authorization, Forecast Ledger creation, prospective forecast, merge, rebase, or force push is authorized by this record.

## Historical P6 result versus current repair state

The retained historical fact remains:

```text
HISTORICAL_P6_EXECUTION_RESULT = PASS
P6 exact execution HEAD = 70dc89f187842d8dcc6ba428241aae614d520bd4
```

The current post-P6 review state is:

```text
NEW_POST_P6_CORRECTNESS_FINDINGS = OPEN_REPAIR
CURRENT_V0_6_ALIGNMENT_CONFIDENCE = WITHDRAWN_PENDING_REPAIR_AND_FRESH_P6
P7_ARCHITECTURE_DECISION = PAUSED_FOR_CORRECTNESS_REPAIR
GENESIS_READY = NO
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
```

A future successful repair does not permit reuse of the historical P6 PASS as validation of modified source. Any consequential source, schema, candidate, validator, or test change requires a fresh complete P6 execution on the exact repaired HEAD.

## Finding R1: production receipt admission/schema mismatch

The prior `production_receipt_admission_v1` helper expected provider operational and cryptographic fields to be copied directly into a production receipt. The normative `RoughtimeProductionReceiptEvidence` schema instead binds those facts through exact `provider_profile_ref` and `qualification_state_package_ref` fields and prohibits additional properties.

The two contracts were therefore incompatible.

Repair direction:

1. the normative receipt schema remains controlling;
2. the receipt binds the exact admitted ProviderProfile by full reference;
3. the receipt binds the exact qualification state package by full reference;
4. the state package binds the QualificationDecision and ProviderProfile;
5. provider identity and verifier build identity must agree across the exact objects;
6. no fallback remains required by the ProviderProfile;
7. copied ProviderProfile fields are not added to the receipt merely to satisfy an obsolete helper.

This repair reduces duplicate representations rather than weakening the binding.

## Finding R2: authoritative evidence accepted sealed but contract-invalid objects

The previous claim-authority implementation relied heavily on `verify_sealed_object`. A valid seal proves internal content hashing, but it does not prove that an object satisfies its normative schema or exact allowed field set.

This left an authority gap for sealed objects with, for example:

```text
wrong schema_version
unexpected additional fields
wrong origin_class where the object schema narrows it
wrong prospective_eligible value
malformed or substituted references
otherwise invalid normative object shape
```

The repair adds an explicit exact object contract gate in front of authoritative claim entry points while preserving the prior claim derivation implementation behind that gate.

Objects covered by the repair now include:

```text
ExternalTimeEvidenceBundle
RoughtimeProductionReceiptEvidence
RoughtimeProviderQualificationStatePackage
OpenTimestampsProofArtifact
DurabilityVerificationRecord
StrongBitcoinVerifierContract
StrongBitcoinVerificationReport
ManifestAcceptance V2
```

The gate is intentionally narrow. It does not introduce a runtime dependency on the JSON Schema package and does not change historical object interpretation.

### R2.a Qualification state package exact-contract gap

The provider admission firewall already recomputed qualification state from retained authoritative inputs and rejected self-asserted state. However, the state package object itself could still be hash-sealed while carrying fields outside its normative `additionalProperties=false` schema.

The repair therefore validates the exact `RoughtimeProviderQualificationStatePackage` contract before the existing authoritative state recomputation. This does not make the package's stored `qualification_state` authoritative; recomputation remains mandatory.

### R2.b ManifestAcceptance V2 exact-contract gap

The final Genesis authority path previously required a sealed `ManifestAcceptance` object of the correct object type, but that alone did not enforce the normative V2 contract. In particular, the final path must reject a hash-consistent acceptance object with the wrong schema version or unexpected fields.

The repair requires the exact `ManifestAcceptance V2` contract for any object that reaches final Genesis authority. Existing earlier rejection classes remain ordered before that check where appropriate: wrong final subject, wall/Bitcoin evidence splicing, and non-live readiness evidence still fail closed before deeper final-object validation.

### R2.c Strong Bitcoin verification report postcondition

The strong Bitcoin verifier inputs are not the only authority boundary. The deterministic `StrongBitcoinVerificationReport` produced by the accepted verifier path is also validated against its exact object contract before its result can be returned through the repaired authoritative path. A supplied persisted strong report is checked before use as well.

### R2.d Confirmatory aggregation must not bypass the gate

The pre-repair confirmatory helper could validate high-level component inputs and then delegate to an implementation that internally invoked the ungated recomputation functions. The repaired public confirmatory path recomputes each wall-clock, Bitcoin, and pre-outcome component through the gated public authoritative functions before strict claim aggregation.

This closes an internal bypass without changing the claim vocabulary or eligibility semantics.

### Synthetic Bitcoin-only fixture compatibility boundary

Historical low-level tests contain a `SYNTHETIC`, `prospective_eligible=false` Bitcoin-only fixture whose `ExternalTimeEvidenceBundle` keeps the normative field names but does not populate the production Roughtime receipt/profile/state-package cardinalities.

The repair temporarily permits this cardinality relaxation only inside the low-level Bitcoin input gate when all of the following are true:

```text
origin_class = SYNTHETIC
prospective_eligible = false
caller is the Bitcoin-only authority input validator
```

The same object does not pass strict wall-clock bundle validation. `LIVE_OPERATIONAL` evidence never receives this exception. Final Genesis readiness and confirmatory prospective eligibility already require LIVE evidence, so this compatibility path cannot create a production or prospective claim.

This is a test-harness compatibility boundary, not a production protocol rule. The preferred later cleanup is to normalize the old synthetic Bitcoin fixture and remove the exception after fresh regression confirms that no historical test intent depends on it.

## Finding R3: DurabilityVerificationRecord authority boundary incomplete

A valid `DurabilityVerificationRecord` used by successor authoritative pre-outcome derivation must satisfy its exact object contract before its references can contribute to `PRE_OUTCOME_DURABILITY_VERIFIED`.

Required checks include:

```text
schema_version == 1.0
object_type == DurabilityVerificationRecord
origin_class in {SYNTHETIC, LIVE_OPERATIONAL}
prospective_eligible == false
exact required field set
no additional fields
primary_subject_ref valid
external_time_evidence_bundle_ref valid
ots_proof_ref valid
strong_verification_report_ref valid
outcome_information_barrier canonical UTC
valid object seal
```

Exact cross-object equality remains enforced by the retained derivation implementation after the contract gate.

A sealed but contract-invalid DVR must fail before it can contribute to a verified pre-outcome claim.

## Finding R4: provider independence evidence authority location

An older sentence in `GENESIS_TIME_EVIDENCE.md` states that final ProviderProfiles must record the reviewed independence basis. The implemented qualification model places independence review in the qualification evidence/review/decision authority chain instead.

For the current v0.6 architecture, the controlling interpretation is:

```text
ProviderProfile
    freezes provider operational and cryptographic identity

Qualification evidence package
    retains evidence used to assess independence and common dependencies

RoughtimeQualificationReview
    must cover the frozen INDEPENDENCE and COMMON_DEPENDENCY criteria

QualificationDecision
    binds the accepted review and ProviderProfile under the frozen criteria

QualificationStatePackage
    reconstructs whether that accepted qualification remains admissible at as_of_utc
```

The ProviderProfile is not expanded merely to duplicate the independence evidence already controlled by the qualification authority chain.

The stale sentence in the older design document is superseded for the current successor architecture by this record. Historical documents remain preserved rather than silently rewritten.

## Finding R5 / P7_F1: provider attempt completeness is not bound to production wall-clock authority

`policy:deadline-receipt-quorum:v3` freezes a three-provider pool and requires all three frozen providers to be evaluated in frozen order, with every provider attempted when retry eligible even after receipt quorum has already been reached.

The repository-owned rehearsal execution path records complete three-provider execution accounting, including attempts, failures, backoff and qualifying results.

The current production claim-authority evidence path, however, derives the wall-clock claim from the admitted provider set plus the retained qualifying receipt evidence. It does not bind a normative production execution record proving that every required provider was evaluated and that all required attempts/failures were retained.

Therefore the current repair state is:

```text
P7_F1 = OPEN_BLOCKER
reason = COMPLETE_FROZEN_PROVIDER_EXECUTION_ACCOUNTING_NOT_BOUND_TO_PRODUCTION_WALL_CLOCK_CLAIM
```

This finding does not mean that two independently valid subject-bound Roughtime receipts fail to establish their individual signed time bounds. It means the stronger v3 execution claim cannot be independently verified from the current production authority package.

No `NON_FORECAST_REHEARSAL` report may be reused as production evidence.

No new production execution object is introduced in this repair solely to make the blocker disappear. P7 must first decide whether the attempt-all-three rule remains necessary for the minimal Genesis v1 policy. If retained, the successor production evidence design must bind complete attempt accounting. If removed, removal requires a versioned successor policy and must not reinterpret v3.

## Repair implementation strategy

To minimize implementation risk, the pre-repair `claim_authority_v1.py` implementation is retained byte-for-byte as an internal implementation module on the repair branch. Its blob identity remains available for direct comparison with the original implementation.

The public `claim_authority_v1.py` surface is a thin authority wrapper that performs exact contract checks and then delegates to the retained implementation. Public TrustedManifest-facing authority code imports these public entry points rather than the retained implementation module directly.

This organization is a repair-branch implementation technique, not a new governance layer or new Trust Core claim type.

## Required regression before acceptance

The repair cannot be accepted from static review alone.

Before any repaired source reaches `design/gen-001`, a clean local checkout of the exact repair HEAD must run at least:

```text
Python compile/import checks
Draft 2020-12 schema meta-validation
production receipt admission tests
claim authority tests
new exact-contract gate adversarial tests
provider qualification/firewall tests
Roughtime strict verifier tests
Architecture Compression focused tests
complete repository pytest
synthetic adversarial suite
git diff --check
```

Existing tests must not be weakened merely to accommodate the repair. If older synthetic fixtures violate the normative schema, they should be repaired or explicitly scoped as non-authoritative test helpers; production authority must remain fail closed.

Any further correctness/security defect returns the work to repair before a fresh P6 result can be accepted.

## Project control after this record

Until a fresh exact-head regression closes the repairs:

```text
P7 = PAUSED_FOR_REPAIR
P7_FINAL_DECISION = NOT_REACHED
candidate v0.7 = NOT CREATED
v0.6 historical candidate bytes = UNCHANGED
PRODUCTION_QUALIFIED = NO
production-qualified provider count = 0
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
network_authorized = false
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
```

PR #6 remains Draft, open and unmerged unless separately authorized.
