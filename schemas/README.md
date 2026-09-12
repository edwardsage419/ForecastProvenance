# Schema scope

These JSON Schema files are interoperability descriptions for the synthetic implementation. The Python validators remain the executable source for frozen semantic rules.

No schema in this directory authorizes prospective issuance. The concrete Genesis AnchorScheme and BootstrapGovernanceRoot remain uninstantiated.

`rfc3161_qualification_rehearsal_report.schema.json` describes the sealed output of the non-forecast RFC 3161 qualification rehearsal checker. Its closed status vocabulary is `REHEARSAL_VERIFIED`, `REHEARSAL_INCOMPLETE`, and `REHEARSAL_FAILED`; production qualification is intentionally not representable.

`rfc3161_reviewed_semantic_assertion.schema.json` describes the separately reviewed, sealed assertion that binds policy and accuracy conclusions to the exact retained provider-policy SHA256 and observed token policy OID. Provider profile booleans cannot substitute for this assertion. Version 1.1 also requires reviewer provenance and binds the exact normalized observed token accuracy; the provenance fields do not claim cryptographic reviewer authentication.

The Roughtime pre-rehearsal schemas describe the offline plan, separate network authorization, qualifying receipt, final rehearsal report, persistent retry state, verifier dependency lock, offline fixture report, and verifier build profile:

1. `roughtime_rehearsal_plan.schema.json`
2. `roughtime_rehearsal_authorization.schema.json`
3. `roughtime_receipt.schema.json`
4. `roughtime_rehearsal_report.schema.json`
5. `roughtime_retry_state.schema.json`
6. `roughtime_verifier_dependency_lock.schema.json`
7. `roughtime_verifier_fixture_report.schema.json`
8. `roughtime_verifier_build_profile.schema.json`

These Roughtime schemas are descriptive interoperability constraints only. Cross-field trust decisions are enforced by executable semantic validation, and cryptographic qualification still requires raw-evidence replay through the separately pinned low-level verifier and exact retained verifier build profile.

Verifier build profile version 1.1 adds direct Go toolchain-tree binding. The verifier qualification artifacts use frozen executable hash rules. The dependency lock binds the exact `go.mod`, `go.sum`, pinned upstream module and `go.mod` h1 checksums, and sorted resolved module set with module replacements prohibited. The fixture report binds the actual Go 1.27 toolchain tree, wrapper source tree, offline `go mod verify`, and required test matrix. The build profile cross-binds those artifacts, the retained sum-verified upstream module Zip, the frozen build command, and the produced binary.
