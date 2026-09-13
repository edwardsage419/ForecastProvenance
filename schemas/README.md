# Schema scope

These JSON Schema files are interoperability descriptions. Python validators remain the executable source for frozen cross-field semantic rules.

No schema in this directory authorizes prospective issuance, production qualification execution, Genesis, or Forecast Ledger creation. The concrete Genesis AnchorScheme and BootstrapGovernanceRoot remain uninstantiated.

## RFC 3161 rehearsal schemas

`rfc3161_qualification_rehearsal_report.schema.json` describes the sealed output of the non-forecast RFC 3161 qualification rehearsal checker. Its closed status vocabulary is `REHEARSAL_VERIFIED`, `REHEARSAL_INCOMPLETE`, and `REHEARSAL_FAILED`; production qualification is intentionally not representable.

`rfc3161_reviewed_semantic_assertion.schema.json` describes the separately reviewed sealed assertion binding policy and accuracy conclusions to retained provider-policy evidence.

## Roughtime rehearsal and verifier-provenance schemas

The Roughtime rehearsal schemas describe the offline plan, separate network authorization, qualifying receipt, final rehearsal report, persistent retry state, verifier dependency lock, offline fixture report, and verifier build profile:

1. `roughtime_rehearsal_plan.schema.json`
2. `roughtime_rehearsal_authorization.schema.json`
3. `roughtime_receipt.schema.json`
4. `roughtime_rehearsal_report.schema.json`
5. `roughtime_retry_state.schema.json`
6. `roughtime_verifier_dependency_lock.schema.json`
7. `roughtime_verifier_fixture_report.schema.json`
8. `roughtime_verifier_build_profile.schema.json`

Current verifier provenance schemas use the vendored offline model:

```text
dependency lock = 1.1
fixture report = 1.1
build profile = 1.2
```

Dependency lock 1.1 binds the exact pinned upstream repository, tag, commit, tag object, verified tag-signature state, the 12 vendored `protocol` compile inputs, each upstream Git blob SHA1, each local SHA256, and the canonical upstream source-tree hash.

Fixture report 1.1 binds `network_used=false`, `vendored_source_verified=true`, `external_modules_used=false`, exact Go 1.27 environment, actual GOROOT tree hash, wrapper source-tree hash, upstream source-tree hash, and the required PASS matrix.

Build profile 1.2 cross-binds the dependency lock, fixture report, Go toolchain distribution and carrier hashes, actual GOROOT tree, wrapper source tree, upstream source tree, frozen build command, produced binary, and profile self hash.

The older Go proxy/module-Zip qualification model is superseded and is not the accepted execution path.

## Roughtime production qualification schemas

The production qualification object model adds seven Draft 2020-12 schemas:

1. `roughtime_production_provider_profile.schema.json`
2. `roughtime_provider_metadata_review.schema.json`
3. `roughtime_qualification_evidence_manifest.schema.json`
4. `roughtime_qualification_review.schema.json`
5. `roughtime_qualification_decision.schema.json`
6. `roughtime_requalification_event.schema.json`
7. `roughtime_qualification_state_report.schema.json`

These schemas describe structure only. Production trust requires the executable semantic validation and hardening path in:

```text
src/forecast_trust_core/_roughtime_production_qualification.py
src/forecast_trust_core/_roughtime_production_qualification_hardening.py
```

The authoritative hardening path requires a real qualification package directory, exact canonical manifest bytes, complete scanned file closure, critical artifact cross-binding, validated verifier build-profile identity, external qualification authority injection, and deterministic state recomputation.

A standalone schema-valid ProviderProfile, QualificationReview, QualificationDecision, or state report does not establish production qualification.

## Production schema meta-validation record

On 2026-09-13, the exact committed bytes of all seven production qualification schemas were checked with `jsonschema 4.26.0` and `Draft202012Validator.check_schema`.

Result:

```text
7 PASS
0 FAIL
```

The checked Git blob SHA1 values are retained in `docs/GEN_001_ROUGHTIME_PRODUCTION_QUALIFICATION_ADVERSARIAL_REVIEW_2026_09_13.md`.

This schema check establishes meta-validity only. The exact current repository-wide pytest regression remains a separate required gate.
