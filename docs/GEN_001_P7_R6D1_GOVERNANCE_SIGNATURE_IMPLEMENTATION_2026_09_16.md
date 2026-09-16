# GEN_001 P7 R6-D1 Governance Signature Implementation — 2026-09-16

Status: IMPLEMENTED_PENDING_LOCAL_REGRESSION
Classification: PRE_GENESIS_NON_FORECAST_IMPLEMENTATION_RECORD
Prospective eligible: false
Genesis effect: none
Network authorization: none
Basis branch: `design/p7-v4-r6`
Implementation basis HEAD before this record: `4e8fdbba8501699ae727e43f32068c6407e16589`

## Scope

R6-D1 implements the owner-authenticated Genesis governance-signature boundary required before final Genesis acceptance can be treated as authoritative.

This record does not authorize Genesis, create a GenesisAuthorization, access or use the Genesis private key, qualify any provider, authorize a network request, freeze candidate v0.7, create a Forecast Ledger, or permit prospective forecasting.

## Implemented machine contracts

D1 adds exact schemas for:

- `BootstrapGovernanceRoot`;
- `GenesisGovernanceSignature`;
- `GenesisGovernanceSignatureVerifierContract`.

The hardened BootstrapGovernanceRoot profile requires:

```text
project_id = forecast-provenance-project
authority_key_type = ED25519
canonicalization_scheme = FPP_JCS_1
hash_algorithm = SHA-256
bootstrap_version = 1
```

Only the public Ed25519 key is a machine input. The Genesis private key remains prohibited from repository, fixtures, connected tools, ChatGPT, logs, and validator inputs.

The governance verifier contract requires the exact frozen projection set:

```text
FPP_GENESIS_AUTHORIZATION_V1
FPP_MANIFEST_ACCEPTANCE_V2
```

and binds the main ValidatorContract, bootstrap authority identity/public-key hash, qualified Ed25519 verifier build-profile hash, and qualified verifier binary hash.

## Non-circular ManifestAcceptance signature projection

`ManifestAcceptance` contains `signature_ref`; signing the complete sealed object would create a signature/hash cycle.

D1 therefore uses `GenesisGovernanceSignature` with the domain-separated `FPP_MANIFEST_ACCEPTANCE_V2` projection. The signing payload is deterministically reconstructed from the substantive acceptance fields while excluding `signature_ref` and the acceptance object's seal hashes.

The validator requires exact signed-payload equality before executing the hash-pinned Ed25519 verifier.

Caller-supplied signature callbacks are not accepted by the production authority API.

## Manifest-bound governance authority

D1 adds `genesis_governance_signature_verifier_contract_ref` to the Genesis-v1 TrustedManifest authority surface used by final acceptance validation.

The final acceptance orchestration requires:

```text
ManifestAcceptance.candidate_manifest_ref == exact TrustedManifest ref
ManifestAcceptance.acceptance_rule_ref == TrustedManifest.acceptance_rule_ref
supplied GenesisGovernanceSignatureVerifierContract ref == TrustedManifest.genesis_governance_signature_verifier_contract_ref
```

The independently supplied BootstrapGovernanceRoot remains outside the candidate manifest graph. The governance signature validator additionally requires:

```text
ManifestAcceptance.bootstrap_governance_root_ref == exact supplied BootstrapGovernanceRoot ref
ManifestAcceptance.authority_ref == exact supplied BootstrapGovernanceRoot ref
ManifestAcceptance.acceptance_rule_ref == BootstrapGovernanceRoot.acceptance_rule_ref
```

This prevents the candidate manifest, runtime caller, or acceptance object from silently substituting authority key material, signing policy, verifier binary identity, or signature projection.

## Final acceptance low-level hardening

`claim_authority_v1.validate_final_genesis_acceptance_authoritatively` now requires governance-signature authority in addition to the retained final wall-clock and Bitcoin evidence.

The historical fail-closed ordering is preserved for wrong final subject, wall/Bitcoin evidence splicing, and non-live production-readiness evidence.

Before final temporal/durability recomputation can succeed, the path now also requires:

```text
ManifestAcceptance exact v2 contract
ManifestAcceptance.decision == ACCEPT
ManifestAcceptance.blocking_finding_refs == []
wall and Bitcoin ValidatorContract refs identical
owner governance signature verified under the manifest-bound verifier contract and independent bootstrap root
```

Missing governance-signature inputs fail closed.

Persisted final ValidationReport recomputation includes the governance signature evidence, BootstrapGovernanceRoot, governance verifier contract, and their exact references in dependency closure. Persisted report bytes remain equality-only audit evidence and never replace authoritative recomputation.

## Focused regression added

New regression surfaces include:

- exact bootstrap project identity;
- exact frozen governance projection set and ordering;
- invalid owner signature rejection;
- signing-payload substitution rejection;
- signature-ref substitution rejection;
- bootstrap-root substitution rejection;
- authority-ref/root mismatch rejection;
- acceptance-rule/root mismatch rejection;
- governance verifier build-profile/binary binding;
- caller signature-callback prohibition;
- missing governance-signature inputs fail closed;
- signed `REJECT` decision cannot enter final acceptance;
- non-empty blocking findings cannot enter final acceptance;
- manifest-bound governance verifier cannot be substituted;
- ManifestAcceptance acceptance rule must equal TrustedManifest acceptance rule;
- missing TrustedManifest governance-verifier ref fails closed.

## Remote diff audit

A remote compare from the R6-D design point `0a3d509203e12e4b98b5c8d25c50b305db708f96` through D1 code/test HEAD `cd2e1f647f0157cbaf43701a74fa405f4fe237eb` showed only the expected D1 schemas, authority modules, `claim_authority_v1.py`, and D1 tests.

No candidate v0.2-v0.7 file, provider-qualification implementation, or `claim_authority_v1_legacy.py` was changed by D1.

## Residual final-validation blocker: required report-role authority

AcceptancePolicy v2 names five required validation-report semantic roles:

```text
TRUST_CORE_TEST_REPORT
GENESIS_ADVERSARIAL_REPORT
PROVIDER_REHEARSAL_REPORT
OTS_BITCOIN_STRONG_VERIFICATION_REPORT
TARGET_SOURCE_PARSER_REPORT
```

The current `ValidationReport v2` contract does not carry a `report_role` field, and the repository does not currently expose a machine-level deterministic role-to-exact-report-ref mapping.

Therefore the signed `ManifestAcceptance.required_validation_report_refs` list cannot be treated as self-proving semantic report completeness.

D1 intentionally does not invent a caller boolean, mutable status field, or self-supplied ref list to close this gap. Independent final Genesis validation remains incomplete until a minimal deterministic report-role authority is designed and regression-tested.

This residual blocker does not invalidate D1 owner-signature authenticity; it prevents D1 from being misrepresented as complete G10/GR041 final validation.

## Regression state

No local or CI regression result is claimed by this record.

The connected execution environment could read and write the GitHub repository but could not clone it for local test execution because outbound DNS for the container was unavailable. The repository has no retained CI workflow that can substitute for the owner's local exact-head regression.

Required next execution on an owner-controlled checkout:

```text
python compileall
focused R6-D1 governance/final-acceptance tests
existing claim-authority/trust-root tests
full repository pytest
git diff --check
```

Only after those pass may R6-D1 move from `IMPLEMENTED_PENDING_LOCAL_REGRESSION` to `REGRESSION_CONFIRMED`.

A fresh exact-head P6 run remains required before the broader R6-D profile can be treated as refrozen. P6 success must not be inferred from focused/full pytest alone.

## Safety state

```text
R6-A = REGRESSION_CONFIRMED
R6-B = REGRESSION_CONFIRMED
R6-C = REGRESSION_CONFIRMED
R6-D1 = IMPLEMENTED_PENDING_LOCAL_REGRESSION
R6-D2 = NOT_IMPLEMENTED
R6-D3 = NOT_IMPLEMENTED
FINAL_VALIDATION_REPORT_ROLE_AUTHORITY = OPEN_BLOCKER
AUTHORITATIVE_CONFIRMATORY_VERIFIED = PROHIBITED
candidate_v0_7 = CREATED_NOT_FROZEN
GENESIS_READY = NO
Genesis = NOT_STARTED
Forecast_Ledger_Genesis = NOT_CREATED
Forecast_Ledger = NOT_CREATED
prospective_forecast_count = 0
production_qualified_provider_count = 0
PRODUCTION_QUALIFIED = NO
production_forecasting = PROHIBITED
network_authorized = false
Roughtime_provider_requests_authorized = 0
RFC3161_requests_authorized = 0
production_qualification_requests_authorized = 0
Genesis_private_key_handling = PROHIBITED
```
