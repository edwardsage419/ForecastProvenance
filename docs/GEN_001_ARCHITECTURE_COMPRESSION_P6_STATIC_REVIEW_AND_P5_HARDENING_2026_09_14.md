# GEN_001 Architecture Compression P6 Static Review and P5 Hardening

Date: 2026-09-14
Status: PRE_GENESIS CORRECTNESS REPAIR RECORD
Classification: NON_FORECAST_REVIEW
Prospective eligible: false
Network authorization: none

## Scope

P6 began against exact P5 HEAD:

```text
c95a79425eb68e48893f9143eec002344829d3a6
```

A full local checkout could not be created because the available container could not resolve `github.com` or `api.github.com`. This is an execution-environment limitation and is not a test PASS or implementation failure.

GitHub's exact recursive tree for `c95a79425eb68e48893f9143eec002344829d3a6` was available with `truncated = false`, allowing read-only static review of the exact P5 bytes.

That review found two blocking correctness defects. Under the project failure rule, P6 stopped before any PASS conclusion and returned the affected implementation surface to P5 for root-cause repair.

## Finding 1: derived-claim subject substitution

Severity: BLOCKING FOR P2 CLAIM AUTHORITY

The initial P5 composition helpers accepted previously derived claim objects by state but did not always require the claim's exact `claim_type` and `subject_ref` to equal the frozen dependency expected by the stronger claim.

Examples included:

1. `DEADLINE_EXISTENCE_VERIFIED(S)` could consume a verified external-existence claim created for another subject.
2. pre-outcome durability could consume a Bitcoin durability claim for a different primary subject or a deadline claim for the wrong DurabilityVerificationRecord.
3. confirmatory eligibility could aggregate a supplied list of VERIFIED claims without proving that its claim-type/subject set exactly equaled the predeclared required set.

This violates the P2 rule that stronger claims are deterministic functions of exact frozen lower-level claims and bindings.

### Repair

Added:

`src/forecast_trust_core/architecture_compression_v1_hardening.py`

The authoritative successor path now provides:

```text
derive_deadline_existence_claim_strict
derive_pre_outcome_durability_claim_strict
derive_confirmatory_eligibility_strict
```

The strict path requires exact claim type, valid closed claim state, and exact subject reference. Confirmatory aggregation additionally requires exact equality with a predeclared set of component claim-type/subject requirements and rejects unknown or recursively self-referential claim types.

The earlier helpers in `architecture_compression_v1.py` remain low-level composition primitives. They are not authoritative Trust Core entry points after this review.

## Finding 2: qualification-state self-assertion

Severity: BLOCKING FOR P4 PROVIDER ADMISSION

The initial P5 qualification-state package validator proved that the package enumerated the retained metadata-review and requalification-event objects supplied by its state store, but it did not itself recompute qualification state from the frozen qualification subsystem.

`validate_provider_admission_set` then compared the package's own `qualification_state` field with the string `PRODUCTION_QUALIFIED`.

A package could therefore contain a complete disqualifying event set while self-asserting `PRODUCTION_QUALIFIED` unless the caller separately performed authoritative qualification-state recomputation.

This violates the P4 rule that the package is supporting evidence rather than qualification authority.

### Repair

The authoritative hardening path now provides:

```text
collect_qualification_state_objects_strict
validate_qualification_state_package_authoritatively
validate_provider_admission_set_authoritatively
```

The strict collector treats its input as a dedicated provider-state store and fails closed on:

```text
symlink
non-regular file
unexpected non-JSON file
malformed JSON
wrong provider
invalid sealed object
unexpected object type
missing or noncanonical event timestamp
duplicate state-object reference
```

For records at or before the frozen `as_of_utc`, package references must exactly equal the collected metadata-review and requalification-event sets.

The package must also exactly bind:

```text
ProviderProfile
QualificationDecision
qualification evidence-manifest SHA256
qualification-verifier contract
```

The validator then invokes the existing authoritative qualification subsystem:

`derive_authoritative_qualification_state`

from `_roughtime_production_qualification_hardening.py` using the complete collected state inputs. The package's asserted state and state-report SHA256 must exactly equal that deterministic result.

Only after every provider package passes this authoritative recomputation may the three-provider admission-set rule evaluate `PRODUCTION_QUALIFIED` at the exact frozen deadline.

## State-store scope clarification

`record_root` in the authoritative package path is a dedicated retained state-input store for one provider. It is not the broader QualificationRecordSet directory.

The broader record set may contain the evidence package, ProviderProfile, decision, reviews and derived reports. The dedicated state-input store contains only sealed `RoughtimeProviderMetadataReview` and `RoughtimeRequalificationEvent` objects for the named provider.

This avoids silently ignoring unrelated or malformed files while keeping qualification workflow internals outside Forecast Trust Core.

## Adversarial tests added

Added:

`tests/test_architecture_compression_p5_hardening.py`

The new cases cover at least:

1. cross-subject external-existence substitution;
2. cross-subject Bitcoin-durability substitution;
3. confirmatory required-claim subject substitution;
4. unknown or recursive confirmatory claim requirement;
5. self-asserted `PRODUCTION_QUALIFIED` conflicting with authoritative recomputation;
6. exact authoritative state/report acceptance;
7. authoritative provider/as-of substitution;
8. malformed state-store JSON;
9. noncanonical state-event timestamp;
10. state-store symlink rejection.

These tests are added as P5 repair evidence but have not yet been executed in the current environment.

## Repair commits

The repair lineage after the original P5 HEAD includes:

```text
b3fd789d64e54eb5b2c73a7a78b0a84918e13f4d  add authoritative hardening layer
8491c004e034d9f0b3e0a196db97fd6a80bf71c8  add P6-discovered adversarial tests
d2f246225399729d6779257ca21a6a1132d5bbdd  close hardening edge cases
8c03134734bc2ed42dd44c91ca11440f88428c86  align and extend hardening tests
```

The exact final repair HEAD must be dynamically re-read after project-control updates and must receive the full P6 regression. No result from the pre-repair `c95a...` tree can be carried forward as a PASS.

## Authority rule after repair

For Architecture Compression v1, the authoritative validator contract must use the hardening entry points for P2 composed claims and P4 provider-state admission.

The following P5 low-level functions are insufficient by themselves to establish the stronger claim:

```text
derive_deadline_existence_claim
derive_pre_outcome_durability_claim
derive_confirmatory_eligibility
validate_qualification_state_package
validate_provider_admission_set
```

They may remain internal deterministic helpers after their inputs have been authoritatively bound.

Production receipt field/profile binding in `production_receipt_admission_v1.py` remains a separate required check and does not substitute for authoritative provider qualification-state admission.

## P6 disposition

```text
P6_FULL_REGRESSION = NOT_EXECUTED
P6_STATIC_REVIEW = BLOCKING_FINDINGS_FOUND
P5_ROOT_CAUSE_REPAIR = IMPLEMENTED_PENDING_REGRESSION
P6_PASS = NO
```

P6 must restart against the exact post-repair HEAD when an exact offline execution environment is available.

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

No provider request, production qualification, private-key handling, Genesis action, merge, rebase or force push occurred during this review or repair.