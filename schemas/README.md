# Schema scope

These JSON Schema files are interoperability descriptions for the synthetic implementation. Python validators remain the executable source for frozen semantic rules.

No schema in this directory authorizes prospective issuance. The concrete Genesis AnchorScheme and BootstrapGovernanceRoot remain uninstantiated.

`rfc3161_qualification_rehearsal_report.schema.json` describes the sealed output of the non-forecast RFC 3161 qualification rehearsal checker. Its closed status vocabulary is `REHEARSAL_VERIFIED`, `REHEARSAL_INCOMPLETE`, and `REHEARSAL_FAILED`; production qualification is intentionally not representable.

`rfc3161_reviewed_semantic_assertion.schema.json` describes the separately reviewed sealed assertion binding policy and accuracy conclusions to retained provider-policy evidence.

The Roughtime pre-rehearsal schemas describe the offline plan, separate network authorization, qualifying receipt, final rehearsal report, persistent retry state, verifier dependency lock, offline fixture report, and verifier build profile:

1. `roughtime_rehearsal_plan.schema.json`
2. `roughtime_rehearsal_authorization.schema.json`
3. `roughtime_receipt.schema.json`
4. `roughtime_rehearsal_report.schema.json`
5. `roughtime_retry_state.schema.json`
6. `roughtime_verifier_dependency_lock.schema.json`
7. `roughtime_verifier_fixture_report.schema.json`
8. `roughtime_verifier_build_profile.schema.json`

These schemas are descriptive interoperability constraints. Cross-field trust decisions remain executable semantic validation, and cryptographic qualification requires replay through the separately pinned low-level verifier and exact retained build profile.

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
