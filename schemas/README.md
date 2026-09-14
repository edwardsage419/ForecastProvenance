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

The production qualification supporting object model includes the following Draft 2020-12 schemas:

1. `roughtime_production_provider_profile.schema.json`
2. `roughtime_provider_metadata_review.schema.json`
3. `roughtime_qualification_evidence_manifest.schema.json`
4. `roughtime_qualification_review.schema.json`
5. `roughtime_qualification_decision.schema.json`
6. `roughtime_requalification_event.schema.json`
7. `roughtime_qualification_state_report.schema.json`
8. `roughtime_provider_qualification_state_package.schema.json`
9. `roughtime_qualification_verifier_contract_v1.schema.json`

These schemas describe structure only. Production trust requires executable semantic validation and the successor claim-authority hardening path in:

```text
src/forecast_trust_core/_roughtime_production_qualification.py
src/forecast_trust_core/_roughtime_production_qualification_hardening.py
src/forecast_trust_core/architecture_compression_v1_hardening.py
src/forecast_trust_core/claim_authority_v1.py
src/forecast_trust_core/claim_authority_trust_root_v1.py
```

The authoritative path requires a real qualification package directory, exact canonical manifest bytes, complete scanned file closure, critical artifact cross-binding, validated verifier build-profile identity, independently supplied accepted authority public-key bytes, hash-pinned Ed25519 signature verification, and deterministic state recomputation.

`roughtime_qualification_verifier_contract_v1.schema.json` freezes the criteria identity, main ValidatorContract ref, QualificationDecision signature projection, accepted qualification-authority ID/public-key hash, and exact Ed25519 verifier build/binary hashes. The schema does not make those facts true by itself; the executable validator checks the exact sealed contract and reconstructs the pinned verifier.

A standalone schema-valid ProviderProfile, QualificationReview, QualificationDecision, state report, state package, or qualification-verifier contract does not establish production qualification.

## Production schema meta-validation record

On 2026-09-13, the then-current exact committed bytes of the seven original production qualification schemas were checked with `jsonschema 4.26.0` and `Draft202012Validator.check_schema`.

Result for that historical check:

```text
7 PASS
0 FAIL
```

The checked Git blob SHA1 values are retained in `docs/GEN_001_ROUGHTIME_PRODUCTION_QUALIFICATION_ADVERSARIAL_REVIEW_2026_09_13.md`.

Schemas added during Architecture Compression P5, including the qualification state package and qualification verifier contract, require fresh schema meta-validation in P6. They are not covered by the historical seven-schema result.

Schema meta-validity alone is never a production-qualification or claim-authority result.

## Claim-authority supporting schemas

Architecture Compression P5 also defines production-shaped supporting schemas for deterministic evidence reconstruction:

```text
external_time_evidence_bundle_v1.schema.json
roughtime_production_receipt_evidence_v1.schema.json
open_timestamps_proof_artifact_v1.schema.json
strong_bitcoin_verifier_contract_v1.schema.json
strong_bitcoin_verification_report_v1.schema.json
durability_verification_record_v1.schema.json
manifest_acceptance_v2.schema.json
validation_report_v2.schema.json
```

These schemas freeze interoperable structure. Authoritative P2 claim states are produced only by exact evidence recomputation under the manifest-bound validator/verifier contracts.

## Ed25519 qualification build profile

`ed25519_verifier_build_profile.schema.json` describes the content-addressed build qualification record for the verification-only Ed25519 backend used by `RoughtimeQualificationDecision` validation.

Executable qualification semantics live in:

```text
src/forecast_trust_core/_ed25519_qualification.py
scripts/genesis/qualify_ed25519_verifier.py
```

The final profile requires an exact Go 1.27.x toolchain, the exact repository commit SHA, Git blob SHA1 plus SHA256 for each of the three closed source files, no external modules, `CGO_ENABLED=0`, the frozen required test PASS set, two byte-for-byte reproducible builds with separate Go build caches, the toolchain and distribution hashes, the verifier binary SHA256, and the build-profile self hash. Qualification rejects working-tree source bytes that differ from repository HEAD.

The schema and harness do not provide signing functionality and accept no private key. Publication of the harness does not mean the Ed25519 backend is final qualified.
