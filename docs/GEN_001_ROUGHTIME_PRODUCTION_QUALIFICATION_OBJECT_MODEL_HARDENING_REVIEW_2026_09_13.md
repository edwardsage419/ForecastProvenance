# GEN_001 Roughtime Production Qualification Object Model Hardening Review

Date: 2026-09-13
Status: IMPLEMENTATION HARDENING
Scope: fail-closed cross-binding and derived-state authority rules

## Safety boundary

This review does not execute production qualification, create a production ProviderProfile, create a QualificationDecision, authorize provider traffic, authorize RFC 3161 traffic, start Genesis, create Forecast Ledger state, or create a prospective forecast.

The required state remains:

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
network_authorized = false
```

## Review basis

The first object-model implementation introduced schemas and low-level semantic validation for production ProviderProfile candidates, evidence manifests, metadata reviews, independent qualification reviews, qualification decisions, requalification events, and derived qualification state reports.

A post-commit static review identified four cross-binding gaps that must be closed before repository regression can be treated as qualification-readiness evidence.

## Finding 1: criterion evidence retention binding

Severity: BLOCKING FOR QUALIFICATION EXECUTION
Disposition: REMEDIATED IN HARDENING LAYER

The low-level independent-review validator checked the complete evidence-manifest SHA256 and each criterion evidence digest format. It did not require each cited criterion evidence digest to correspond to an artifact entry in the complete manifest.

That permits an internally consistent review record to cite an evidence hash whose bytes are not retained by the qualification package.

The hardening layer now requires every `criteria_checks[].evidence_sha256s` value to appear as an exact artifact SHA256 in the bound complete evidence manifest.

This creates an explicit retained-bytes path for every applicable criterion assertion.

## Finding 2: execution and independent-review event separation

Severity: BLOCKING FOR QUALIFICATION EXECUTION
Disposition: REMEDIATED IN HARDENING LAYER

The frozen criteria allow the same project owner to perform both activities under the zero-cost model, while requiring them to be separate recorded events using independently reconstructed inputs.

The low-level validator required nonempty `executor_id` and `reviewer_id` values but did not require different event identities.

The hardening layer now rejects equality between `executor_id` and `reviewer_id`.

This rule separates events rather than people. The same human owner remains permitted when the events are independently recorded.

## Finding 3: metadata capture chronology

Severity: FAIL-CLOSED CORRECTNESS
Disposition: REMEDIATED IN HARDENING LAYER

A metadata review may only rely on evidence that existed by the review event.

The low-level validator checked timestamp syntax and required the qualification review to be no earlier than the metadata review. It did not compare each source capture retrieval time with the qualification review time.

The hardening layer now rejects any metadata source capture whose `retrieved_at` is later than the qualification review `reviewed_at`.

This prevents a later capture from being used as if it supported an earlier review event.

## Finding 4: derived state report authority

Severity: BLOCKING FOR TRUST INTERPRETATION
Disposition: REMEDIATED IN AUTHORITATIVE INTERFACE

A `RoughtimeQualificationStateReport` is deterministic derived output. Its self hash proves only integrity of that report's own fields.

The low-level structural validator can therefore validate a correctly hashed report without proving that its claimed state was derived from valid immutable inputs. Treating that structural validation as qualification authority would create a self-assertion path.

The hardening layer defines the authoritative rule:

1. recompute state from ProviderProfile, complete manifest, independent review, externally rooted signed QualificationDecision, metadata reviews, requalification events, and explicit `as_of_utc`;
2. compare the supplied report byte-for-byte at the object level with the deterministic recomputation;
3. reject any difference.

The low-level state-report validator remains a structural helper only. It must never be used alone to establish provider qualification.

## Authoritative interface

For production qualification interpretation, callers must use the hardening interface in:

`src/forecast_trust_core/_roughtime_production_qualification_hardening.py`

The relevant functions are:

```text
validate_bound_qualification_review
validate_bound_qualification_decision
derive_authoritative_qualification_state
validate_qualification_state_by_recomputation
```

The lower-level module remains useful for schema-adjacent primitives and deterministic component checks. Its standalone state-report structural validation is not an authority decision.

## Test evidence completed in isolation

The hardening functions were exercised in an isolated local package against the four identified failure paths.

Observed pytest result:

```text
4 passed
```

The tests demonstrated rejection of:

1. criterion evidence hashes absent from the complete manifest;
2. identical execution and independent-review event identities;
3. metadata captures retrieved after the qualification review event;
4. a forged qualification state report whose self hash is internally valid but whose state differs from deterministic recomputation.

The isolated test run is development evidence only. It is not a complete repository regression result and does not close the frozen `SCHEMA_VALIDATOR_REGRESSION` criterion.

## Remaining blockers

Production qualification execution remains `NOT_READY`.

Before execution can be considered, the project still requires:

1. full repository regression against the exact committed bytes;
2. validation of all new JSON Schemas against the repository schema tooling;
3. adversarial review of the complete object model after hardening;
4. a concrete, separately reviewed Ed25519 verification backend with positive and negative offline fixtures;
5. exact external qualification authority public-key identity when the owner governance instance is prepared;
6. qualification evidence satisfying the already frozen provider criteria.

No live provider request is authorized by this review.
