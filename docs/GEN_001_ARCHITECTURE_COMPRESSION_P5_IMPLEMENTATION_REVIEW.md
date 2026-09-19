# GEN_001 Architecture Compression P5 Implementation Review

Date: 2026-09-14
Status: PRE_GENESIS IMPLEMENTATION COMPLETE WITH CLAIM-AUTHORITY HARDENING; PENDING P6 REGRESSION
Classification: NON_FORECAST_REVIEW
Prospective eligible: false
Network authorization: none

## Scope

This review records the consolidated P5 implementation of the accepted P1 through P4 Architecture Compression decisions plus correctness hardening discovered during the first P6 static review.

P5 does not execute production qualification, contact a time provider, access a Genesis private key, create Forecast Ledger Genesis, create Forecast Ledger state, or issue a prospective forecast.

## Implemented successor candidate

`candidate_patch_v0_6.json` extends the historical v0.2 through v0.5 lineage without editing predecessor bytes.

It retires by exact predecessor content hash:

```text
policy:genesis-acceptance:v1
policy:genesis-evaluation:v1
policy:genesis-human-review:v1
```

It adds sealed:

```text
policy:genesis-acceptance:v2
policy:genesis-evaluation:v2
```

Effective candidate object count is 21.

Claim-authority hardening did not change candidate bytes or object count.

## P1 implementation

ManifestAcceptance v2 no longer requires a reference to final external evidence created only after signing.

The signed acceptance binds the exact candidate manifest, external BootstrapGovernanceRoot reference, AcceptancePolicy v2, required validation reports, authority, decision, reason codes, blocking findings and signature reference.

Final external evidence is supplied separately to independent final validation and must bind the exact signed ManifestAcceptance.

The successor authoritative final-validation entry point recomputes the required external-existence and Bitcoin-durability claims from exact retained evidence before invoking the low-level structural acceptance checks.

## P2 implementation and hardening

The Architecture Compression validator implements independent derived claims:

```text
EXTERNAL_EXISTENCE_BOUND_VERIFIED
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

Claim states are:

```text
VERIFIED
FAILED
UNRESOLVED
NOT_APPLICABLE
```

The implementation preserves weaker verified historical claims when a stronger claim fails later. Bitcoin durability cannot repair a missed wall-clock deadline and Bitcoin header time is not used as precise civil time.

P6 static review identified and P5 repaired exact lower-claim type/subject substitution plus the deeper claim-authority boundary. The successor authority chain now runs from exact retained evidence and exact TrustedManifest-bound authority refs to deterministic verifier execution, P2 claims and deterministic ValidationReport v2 output.

Persisted claims and reports are audit outputs. They cannot authorize themselves.

## P3 implementation

Genesis v1 no longer instantiates scientific Human Review policy authority.

EvaluationPolicy v2 retains only:

```text
resolved_outcome
forecast_value
absolute_error
squared_error
```

Baseline deltas, pairwise method comparison, aggregate predictive-skill metrics, probabilistic scoring, significance claims and leaderboards are deferred.

Dormant randomness/fitted-state/closed-model interfaces remain available for successors but are not Genesis v1 dependencies.

## P4 implementation and hardening

The supporting provider-state package contract and collector close the state-input enumeration boundary identified in P4.

The validator scans a fixed retained qualification record root and requires exact equality between package refs and the metadata-review and requalification-event objects relevant through the package `as_of_utc`.

Provider admission requires three unique manifest-admitted providers, exact profile and decision sets, exact frozen deadline as-of, and `PRODUCTION_QUALIFIED` for all three before receipt quorum is evaluated.

P6 static review also identified that a runtime caller could otherwise supply a signature-verification callback and authority fields to the low-level qualification-state recomputation path. P5 now closes that path through a manifest-bound `RoughtimeQualificationVerifierContract` and an internally constructed hash-pinned `PinnedEd25519Verifier`.

The qualification verifier contract freezes:

```text
frozen criteria ID/hash
main ValidatorContract ref
QualificationDecision signature projection
ED25519 signature algorithm
accepted authority ID/public-key SHA256
Ed25519 verifier build-profile SHA256
Ed25519 verifier binary SHA256
```

For Genesis, the authority public-key bytes remain an independent input from the accepted BootstrapGovernanceRoot/governance context and must match the contract hash. The private key is never a verification input.

The runtime provider-authority input set must exactly equal the same three provider identities admitted by the exact manifest-bound ProviderProfiles/state packages. Extra or substituted inputs fail closed.

The frozen production qualification criteria are unchanged.

## Claim-authority implementation surfaces

```text
src/forecast_trust_core/architecture_compression_v1_hardening.py
src/forecast_trust_core/claim_authority_v1.py
src/forecast_trust_core/claim_authority_trust_root_v1.py
src/forecast_trust_core/production_receipt_admission_v1.py
```

The low-level historical helpers remain available for historical contracts but are not successor readiness-authority entry points.

## Schemas added or versioned

```text
schemas/manifest_acceptance_v2.schema.json
schemas/validation_report_v2.schema.json
schemas/roughtime_provider_qualification_state_package.schema.json
schemas/roughtime_qualification_verifier_contract_v1.schema.json
schemas/external_time_evidence_bundle_v1.schema.json
schemas/roughtime_production_receipt_evidence_v1.schema.json
schemas/open_timestamps_proof_artifact_v1.schema.json
schemas/strong_bitcoin_verifier_contract_v1.schema.json
schemas/strong_bitcoin_verification_report_v1.schema.json
schemas/durability_verification_record_v1.schema.json
```

Schemas describe interoperability structure. Executable cross-field trust remains in Python validators.

## Focused tests added

```text
tests/test_architecture_compression_p5.py
tests/test_architecture_compression_p5_hardening.py
tests/test_genesis_candidate_patch_v06.py
tests/test_production_receipt_admission_v1.py
tests/test_claim_authority_v1.py
tests/test_claim_authority_trust_root_v1.py
tests/test_claim_authority_qualification_root_v1.py
```

Coverage includes candidate v0.6 exact retirement/materialization, noncircular acceptance, separated claims, state-event completeness, provider admission, evidence/report authority reconstruction, verifier/expected-ref substitution, runtime signature-callback substitution, authority-key substitution, provider-input-set closure and strong Bitcoin evidence binding.

These tests are committed but have not yet been executed on the final repaired exact HEAD.

## Validation execution status

No complete P6 regression exists for the final repaired P5 tree.

An earlier ChatGPT execution container could not establish a local GitHub checkout; later user-side diagnostics showed that the native development network itself can access GitHub and that the earlier `Bad access` observations came from a restricted command sandbox. That infrastructure detour is not a repository or protocol finding.

No test result from an earlier pre-repair HEAD is treated as current evidence. P6 remains the mandatory executable gate.

## Static implementation review findings

The initial P6 static review found three correctness classes before full regression:

1. exact lower-claim type/subject substitution;
2. self-asserted qualification state without mandatory authoritative recomputation;
3. incomplete claim-authority boundary, including verifier/expected-ref, persisted-report and qualification signature-callback/authority substitution paths.

Repository-level repairs now exist for all three classes. The latest static adversarial pass found no additional blocking authority-substitution path after exact provider-input closure was added.

This statement is a static review conclusion only. It is not a P6 PASS.

No P5 repair lowered a frozen qualification criterion, receipt threshold, target/source rule, provenance requirement, or Genesis authorization gate.

Historical candidate v0.2 through v0.5 files were not modified.

No production ProviderProfile or QualificationDecision was created.

No final BootstrapGovernanceRoot or owner public key was instantiated.

No Genesis private key material was requested or handled.

## P6 required execution

P6 must run from a fresh clean exact checkout of the final P5 HEAD and include at least:

```text
Python compile/import checks
JSON Schema Draft 2020-12 meta-validation over the complete current schema set
historical candidate/materializer regression
candidate v0.6 regression
Architecture Compression P1/P2/P4 regression
claim-authority and qualification-signature-authority focused tests
production receipt/profile admission tests
strong Bitcoin verifier authority tests
complete repository pytest suite
complete synthetic adversarial suite
```

Any failure that affects security semantics returns the project to P5 for root-cause repair. Tests or standards must not be weakened to obtain a PASS, and a repaired HEAD requires P6 to restart from zero.

## Stage disposition

```text
P5_IMPLEMENTATION = COMPLETE_WITH_CLAIM_AUTHORITY_HARDENING_PENDING_REGRESSION
P6 = NEXT / RESTART_REQUIRED_ON_FINAL_EXACT_HEAD
P6_PASS = NO
P7 = PROHIBITED_UNTIL_P6_PASS
GENESIS_READY = NO
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
