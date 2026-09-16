# GEN_001 Post-P6 Correctness Repair

Date: 2026-09-16
Status: PRE_GENESIS_REPAIR_PENDING_FRESH_REGRESSION
Classification: PRE_GENESIS_DESIGN_AND_IMPLEMENTATION_REPAIR
Prospective eligible: false
Genesis effect: none
Network authorization: none
Basis commit: `aa453268e4420dff6ea5ba3208e286d158f52e32`

## Purpose

This record preserves a set of correctness findings discovered after the historical P6 exact-head regression had passed and records the narrow repair applied on the isolated repair branch.

The historical P6 result remains a historical fact. These later findings show that its test surface did not cover every current evidence-to-claim contract boundary. Because source and tests changed after the P6 input HEAD, the repaired tree requires a fresh full P6 regression from zero before P7 dependency reevaluation may resume.

This work does not authorize Genesis, create a Forecast Ledger, create a prospective forecast, qualify a provider, send a Roughtime/RFC3161/OpenTimestamps request, or change any provider qualification state.

## Historical P6 preservation

The retained historical execution remains:

```text
P6 exact execution HEAD = 70dc89f187842d8dcc6ba428241aae614d520bd4
P6 evidence manifest SHA256 = a330a3952b55ce0f4415f25c5580ad2cdf53c05801e78f728239ab73caa8bb5d
historical execution result = PASS
```

This record does not rewrite that result. It withdraws any claim that the historical PASS is sufficient evidence for the repaired source tree.

## Finding F1: production wall-clock execution accounting is not claim-authority input

Identifier:

```text
P7_F1 = PRODUCTION_WALL_CLOCK_CLAIM_DOES_NOT_BIND_COMPLETE_FROZEN_PROVIDER_EXECUTION_ACCOUNTING
```

`policy:deadline-receipt-quorum:v3` requires all three frozen providers to be evaluated in frozen order and attempted when retry-eligible, even after quorum has already been reached.

The repository-owned rehearsal execution layer records three ordered provider results and complete attempt/failure evidence. The current production `ExternalTimeEvidenceBundle` and authoritative wall-clock recomputation consume the qualifying production receipt set and the three-provider qualification/admission set, but do not bind an authoritative production event record proving that every required provider attempt was performed and retained.

This finding remains OPEN. The repair does not silently reinterpret v3, does not reuse `NON_FORECAST_REHEARSAL` reports as production evidence, and does not invent a new Trust Core object merely to close the finding.

P7 must later decide whether the attempt-all-three semantic remains necessary. Removing it requires a successor versioned policy. If it remains necessary, the smallest production execution-accounting authority must be designed and reviewed before Genesis readiness can close.

## Finding F2: production receipt admission expected fields prohibited by the receipt schema

The previous `production_receipt_admission_v1` helper compared a production receipt against a list of ProviderProfile fields such as host, root key, protocol and operator identity.

The normative `RoughtimeProductionReceiptEvidence` schema does not contain those copied fields and prohibits additional properties. A schema-conforming receipt therefore could not satisfy the helper, while a helper-conforming receipt could not satisfy the schema.

Repair:

1. The receipt itself is now checked against the exact normative production receipt contract.
2. Provider binding uses the receipt's exact `provider_profile_ref`.
3. Qualification-state binding uses the exact `qualification_state_package_ref`.
4. The state package remains bound to the exact QualificationDecision and ProviderProfile.
5. Provider identity and verifier-build-profile identity must agree across the bound objects.
6. ProviderProfile `no_fallback=true` remains required.
7. Profile fields are not redundantly copied into the receipt.
8. The bound Profile, Decision and StatePackage must at least be correctly typed sealed v1 objects before their refs can satisfy the binding helper.

Regression coverage now constructs a schema-conforming production receipt and includes wrong exact-ref, extra-field, verifier-build mismatch, fallback-enabled profile and wrong-object-type negatives.

## Finding F3: sealed evidence could bypass the exact normative object contract

The successor claim-authority implementation previously used `verify_sealed_object` plus selected semantic checks. A sealed object with internally correct content hashes could therefore still violate its normative JSON object contract through an unexpected field, missing schema field, or disallowed object-class value.

Repair:

A narrow `production_evidence_contracts_v1` module now enforces the exact current contract for evidence objects consumed directly by authoritative temporal/durability recomputation:

```text
ExternalTimeEvidenceBundle
RoughtimeProductionReceiptEvidence
OpenTimestampsProofArtifact
DurabilityVerificationRecord
StrongBitcoinVerifierContract
```

The checks enforce the exact field set, schema/object identity, allowed origin class, `prospective_eligible` rule, reference shape, UTC deadline shape, digest shape, required cardinality and fixed verifier-contract constants as applicable.

`claim_authority_v1._exact_ref()` dispatches these exact contract checks at the authority choke point before granting a content reference authority. Existing cryptographic replay and exact-reference checks remain in place after contract validation.

A static follow-up found that the wall-clock FAILED path could re-enter `_exact_ref(bundle)` after the first contract failure and re-raise instead of returning a deterministic failed claim. That secondary path was removed: contract-invalid wall evidence now remains fail-closed as `FAILED` without a second authority attempt.

This is intentionally a small in-repository contract layer and adds no runtime JSON Schema dependency or external service dependency.

## Finding F4: DurabilityVerificationRecord contract was incomplete at authority boundary

The earlier pre-outcome recomputation checked the DVR seal, object type, primary subject and evidence refs, but did not require the complete DVR schema contract before deriving the stronger pre-outcome claim.

The authority choke-point repair now requires the exact DVR contract before the DVR can participate in `PRE_OUTCOME_DURABILITY_VERIFIED` derivation.

A sealed DVR with an extra field, wrong schema version, invalid origin class, wrong `prospective_eligible` value, malformed ref or malformed barrier can no longer reach the stronger claim derivation path.

## Finding F5: provider independence evidence location wording was inconsistent

`GENESIS_TIME_EVIDENCE.md` previously said that the final ProviderProfiles themselves must record the reviewed independence basis.

The implemented qualification model instead places the independence/common-dependency review and its retained evidence in the qualification evidence package and `RoughtimeQualificationReview`, which is then bound into the QualificationDecision authority chain.

The minimal repair keeps ProviderProfile focused on frozen operational and cryptographic identity and corrects the prose to identify the qualification evidence/review/decision chain as the authority for independence evidence.

No ProviderProfile schema expansion is introduced.

## Finding F6: DurabilityVerificationRecord prose listed non-schema fields

`GENESIS_TIME_EVIDENCE.md` previously described the DurabilityVerificationRecord as directly containing Bitcoin block height, block hash and a header reference.

The normative `durability_verification_record_v1.schema.json` instead binds:

```text
primary_subject_ref
external_time_evidence_bundle_ref
ots_proof_ref
strong_verification_report_ref
outcome_information_barrier
```

Bitcoin block height, block hash, header digest, node version and verification result belong to the exact bound `StrongBitcoinVerificationReport`. The prose is corrected to match that object model and avoid duplicate Bitcoin fields in the DVR.

No schema or candidate-object bytes are changed.

## Files changed by this repair

Implementation and regression surfaces include:

```text
src/forecast_trust_core/production_evidence_contracts_v1.py
src/forecast_trust_core/production_receipt_admission_v1.py
src/forecast_trust_core/claim_authority_v1.py
tests/test_production_receipt_admission_v1.py
tests/test_claim_authority_v1.py
tests/test_production_evidence_contracts_v1.py
```

Control-document alignment is updated separately in the same repair workstream.

Candidate object bytes, candidate lineage, historical schemas and historical P6 evidence are not rewritten by this repair.

## Regression disposition

At creation of this record, the repair has not yet earned a fresh full P6 regression result.

Required next validation remains:

```text
Python compile/import checks
all JSON Schema Draft 2020-12 meta-validation
focused production evidence contract tests
focused production receipt admission tests
focused claim-authority tests
qualification firewall/signature-authority regression
Roughtime verifier/execution regression
candidate lineage/materialization regression
complete repository pytest
synthetic adversarial suite
git diff --check and final scope review
```

Any correctness/security failure requires root-cause repair followed by another fresh complete regression on one exact final HEAD. Passing subsets from an earlier HEAD cannot be combined with a later repair.

## Current disposition

```text
HISTORICAL_P6_EXECUTION_RESULT = PASS
POST_P6_CORRECTNESS_FINDINGS = REPAIR_IMPLEMENTED_PENDING_REGRESSION
P6_FOR_REPAIRED_HEAD = NOT_RUN
P6_RESTART_REQUIRED = YES
P7_DEPENDENCY_REEVALUATION = PAUSED
P7_F1 = OPEN
GENESIS_READY = NO
PRODUCTION_QUALIFIED = NO
network_authorized = false
```

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

The Genesis Ed25519 private key is not an input to this repair and must remain outside repository, GitHub, CI, ChatGPT, Codex, logs, fixtures and third-party systems.
