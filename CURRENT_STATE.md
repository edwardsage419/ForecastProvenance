# Current State

Date: 2026-09-16
Project: Forecast Provenance Project
State: PRE_GENESIS_ARCHITECTURE_COMPRESSION_REPAIR

```text
branch = design/gen-001
architecture_compression_basis_commit = 9790e323a519558b92b7d6c1324b3bd847cfacfe
```

The commit containing this file is identified from Git metadata and is not self-embedded. Dynamic branch HEAD, PR mergeability and local execution state must be rechecked when needed.

## Architecture Compression sequence

```text
P0  project-control transition                                      COMPLETE
P1  Genesis final-acceptance anchoring reconciliation               COMPLETE
P2  temporal/durability claim separation                            IMPLEMENTED_REPAIR_PENDING_FRESH_REGRESSION
P3  Genesis v1 dependency/review/evaluation compression             COMPLETE
P4  provider-qualification complexity firewall                      COMPLETE_HARDENED
P5  consolidated versioned implementation of P1-P4                  POST_P6_REPAIR_PENDING_FRESH_REGRESSION
P6  complete offline regression and synthetic adversarial suite     HISTORICAL_PASS / FRESH_REGRESSION_REQUIRED
P7  reconsider need for Roughtime production qualification          PAUSED_FOR_POST_P6_REPAIR
P8  separate final pre-Genesis high-level review                    PENDING
P9  separate explicit Genesis authorization                         PENDING
```

P6 historically restarted from zero on the exact final repaired HEAD used for that execution. No result from any earlier HEAD was carried forward. That historical P6 execution passed. Post-P6 review later found additional correctness gaps in evidence-object contract enforcement and production receipt admission. The historical PASS remains preserved, but it is not valid regression evidence for the repaired source tree. P7 is paused until a fresh complete P6 regression passes on one exact final repair HEAD.

## Controlling records

```text
docs/GEN_001_GENESIS_ANCHORING_RECONCILIATION_V1.md
docs/GEN_001_TEMPORAL_CLAIM_SEPARATION_V1.md
docs/GEN_001_GENESIS_V1_DEPENDENCY_COMPRESSION_V1.md
docs/GEN_001_PROVIDER_QUALIFICATION_COMPLEXITY_FIREWALL_V1.md
docs/GEN_001_ARCHITECTURE_COMPRESSION_P5_IMPLEMENTATION_REVIEW.md
docs/GEN_001_ARCHITECTURE_COMPRESSION_P6_STATIC_REVIEW_AND_P5_HARDENING_2026_09_14.md
docs/GEN_001_P6_FINDING_3_CLAIM_AUTHORITY_BOUNDARY_2026_09_14.md
docs/GEN_001_POST_P6_CORRECTNESS_REPAIR_2026_09_16.md
```

Finding 3 received its earlier implementation repair and was subsequently closed by the historical successful P6 execution on its exact HEAD. The later post-P6 findings do not rewrite that history; they require a new regression result for the current repaired implementation.

## Effective candidate

Current effective candidate lineage remains:

```text
candidate_object_set_v0_2.json
+ candidate_patch_v0_3.json
+ candidate_patch_v0_4.json
+ candidate_patch_v0_5.json
+ candidate_patch_v0_6.json
```

Effective object count remains 21.

`candidate_patch_v0_6.json` retires by exact predecessor hash:

```text
policy:genesis-acceptance:v1
policy:genesis-evaluation:v1
policy:genesis-human-review:v1
```

and adds:

```text
policy:genesis-acceptance:v2
policy:genesis-evaluation:v2
```

Historical v0.2 through v0.5 candidate bytes remain unchanged. The post-P6 correctness repair does not change candidate bytes or candidate lineage.

## P1 state

ManifestAcceptance v2 remains noncircular. Final external evidence is created after signing, supplied separately to independent final validation, and must bind the exact signed ManifestAcceptance.

The historical/low-level `validate_final_genesis_acceptance` helper remains non-authoritative because it accepts derived state values. The successor authoritative path wraps it only after independently recomputing the exact wall-clock and Bitcoin claims from retained evidence under the TrustedManifest-bound contracts.

Separate explicit Genesis authorization remains mandatory after successful independent final validation.

## P2 state and claim authority

The claim vocabulary remains:

```text
EXTERNAL_EXISTENCE_BOUND_VERIFIED
DEADLINE_EXISTENCE_VERIFIED
BITCOIN_DURABILITY_VERIFIED
PRE_OUTCOME_DURABILITY_VERIFIED
CONFIRMATORY_PROSPECTIVE_ELIGIBLE
```

with states:

```text
VERIFIED
FAILED
UNRESOLVED
NOT_APPLICABLE
```

P6 Finding 1 was repaired by exact lower-claim type/subject binding.

P6 Finding 3 was repaired at implementation level by the successor authority chain:

```text
exact sealed TrustedManifest
+ independently supplied accepted bootstrap/governance authority public-key bytes where required
+ exact retained evidence
+ exact frozen policies/provider state
+ exact ValidatorContract and supporting verifier contracts
→ deterministic verifier execution
→ deterministic P2 claims
→ deterministic ValidationReport v2
→ exact persisted/recomputed equality where applicable
→ stronger claim/readiness decision
```

Post-P6 review found that `verify_sealed_object` plus selected semantic checks did not by itself prove that every directly consumed evidence object satisfied its exact normative object contract. The repair adds a narrow exact-contract authority layer for:

```text
ExternalTimeEvidenceBundle
RoughtimeProductionReceiptEvidence
OpenTimestampsProofArtifact
DurabilityVerificationRecord
StrongBitcoinVerifierContract
```

These checks now gate authority before the existing cryptographic replay and exact-reference checks. The repaired implementation remains pending fresh full regression.

Authoritative implementation surfaces include:

```text
src/forecast_trust_core/claim_authority_v1.py
src/forecast_trust_core/claim_authority_trust_root_v1.py
src/forecast_trust_core/production_evidence_contracts_v1.py
```

Wall-clock authority replays exact retained Roughtime request/response evidence through the strict verifier, reconstructs exact provider admission at the frozen deadline and derives the conservative quorum upper bound.

Bitcoin durability executes the exact hash-pinned local verifier over exact ExternalTimeEvidenceBundle and OTS proof bytes. Persisted strong-verification reports are audit outputs only.

Final-acceptance, cycle-plan, pre-outcome and confirmatory successor paths derive their temporal claims from evidence rather than caller-supplied claim mappings or `VERIFIED` strings.

Production readiness wrappers require the admitted operational evidence class. Synthetic fixtures remain non-prospective test material and cannot close readiness.

## P3 state

Genesis v1 does not instantiate scientific Human Review authority. Official ambiguity remains `REVIEW_REQUIRED` or `UNRESOLVED` without operator value selection.

Minimum normative numerical evaluation remains:

```text
resolved_outcome
forecast_value
absolute_error
squared_error
```

Cohort reporting preserves at least:

```text
expected
issued
failed
omitted
ineligible
unresolved
withdrawn
```

Deferred randomness, FittedState, stochastic/closed-model, multi-method and leaderboard surfaces remain outside Genesis v1 readiness.

## P4 state and authority hardening

TrustedManifest provider/claim authority boundary includes:

```text
deadline_receipt_quorum_policy_ref
provider_profile_refs
qualification_decision_refs
qualification_verifier_contract_ref
validator_contract_ref
strong_bitcoin_verifier_contract_ref
```

For each consequential deadline event:

```text
as_of_utc = frozen_deadline_utc
```

All three manifest-admitted providers must be authoritatively `PRODUCTION_QUALIFIED` before receipt quorum can operate as two-of-three under the current v0.6 policy.

P6 Finding 2 was repaired by fail-closed state-store collection, exact metadata/requalification closure, deterministic `derive_authoritative_qualification_state`, and exact state/report equality.

A final P5 static adversarial pass found and repaired a related authority-substitution path: provider-state reconstruction previously accepted a runtime `signature_verifier` callback and authority fields. The successor trust-root adapter now prohibits those caller inputs and internally constructs `PinnedEd25519Verifier` from the exact manifest-bound `RoughtimeQualificationVerifierContract`.

The qualification verifier contract binds:

```text
frozen criteria ID/hash
main ValidatorContract ref
QualificationDecision signature projection
ED25519 signature algorithm
accepted authority ID/public-key SHA256
qualified Ed25519 verifier build-profile SHA256
qualified Ed25519 verifier binary SHA256
```

For Genesis, accepted authority public-key bytes remain an independent input from the BootstrapGovernanceRoot/governance context and must match the manifest-bound contract hash. The private key is never an input.

The provider runtime input key set, ProviderProfile IDs and state-package provider IDs must form the same exact three-provider set. Extra or substituted authority inputs fail closed.

Provider independence evidence remains in the qualification evidence/review/decision chain. ProviderProfile remains the frozen operational and cryptographic identity object.

## P7 open finding

The current `policy:deadline-receipt-quorum:v3` requires all three frozen providers to be evaluated in frozen order and attempted when retry-eligible. The rehearsal execution layer records that complete attempt history. The production wall-clock claim authority currently consumes the admitted three-provider state and the retained qualifying production receipt set, but does not bind an authoritative production event record proving complete attempt-all-three execution accounting.

Current identifier:

```text
P7_F1 = PRODUCTION_WALL_CLOCK_CLAIM_DOES_NOT_BIND_COMPLETE_FROZEN_PROVIDER_EXECUTION_ACCOUNTING
P7_F1_STATUS = OPEN
```

This repair does not silently remove the v3 attempt rule, reuse rehearsal evidence as production evidence, or invent a new Trust Core object. P7 must decide the minimum correct successor semantics after fresh P6 regression.

## Successor implementation surfaces

Current Architecture Compression successor surfaces include:

```text
src/forecast_trust_core/architecture_compression_v1.py
src/forecast_trust_core/architecture_compression_v1_hardening.py
src/forecast_trust_core/production_evidence_contracts_v1.py
src/forecast_trust_core/production_receipt_admission_v1.py
src/forecast_trust_core/claim_authority_v1.py
src/forecast_trust_core/claim_authority_trust_root_v1.py
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
tests/test_architecture_compression_p5.py
tests/test_architecture_compression_p5_hardening.py
tests/test_claim_authority_v1.py
tests/test_claim_authority_trust_root_v1.py
tests/test_claim_authority_qualification_root_v1.py
tests/test_genesis_candidate_patch_v06.py
tests/test_production_evidence_contracts_v1.py
tests/test_production_receipt_admission_v1.py
```

Historical validators remain available under their historical contracts and do not acquire successor authority semantics.

## P6 execution status

Historical P6 execution was bound to:

```text
P6 exact execution HEAD = 70dc89f187842d8dcc6ba428241aae614d520bd4
P6 evidence manifest SHA256 = a330a3952b55ce0f4415f25c5580ad2cdf53c05801e78f728239ab73caa8bb5d
HISTORICAL_P6_EXECUTION_RESULT = PASS
```

Before that execution, static review had found three blocking correctness classes:

1. lower-claim type/subject substitution;
2. self-asserted qualification state without mandatory authoritative recomputation;
3. incomplete evidence-to-claim authority boundary, later including runtime signature-verifier/authority substitution.

Those findings received repository-level repairs and were closed for that exact historical P6 tree.

Post-P6 review later found the additional correctness gaps recorded in `docs/GEN_001_POST_P6_CORRECTNESS_REPAIR_2026_09_16.md`.

Current disposition:

```text
HISTORICAL_P6_EXECUTION_RESULT = PASS
POST_P6_CORRECTNESS_FINDINGS = REPAIR_IMPLEMENTED_PENDING_REGRESSION
P6_FOR_CURRENT_REPAIR_HEAD = NOT_RUN
P6_RESTART_REQUIRED = YES
P7 = PAUSED_PENDING_FRESH_P6
```

Any consequential source/schema/candidate modification after the historical P6 input HEAD invalidates that earlier execution as evidence for the modified tree and requires a fresh P6 run from zero.

## Fresh P6 required execution scope

The next P6 execution must cover at minimum:

```text
Python compile/import checks
Draft 2020-12 JSON Schema meta-validation
historical candidate/object regression
v0.6 successor materialization and retirement regression
P1 noncircular ManifestAcceptance tests
P2 claim separation and exact evidence-contract authority tests
P4 qualification firewall/state closure tests
qualification signature-authority substitution tests
production receipt/profile admission tests
strong Bitcoin verifier contract tests
Roughtime verifier/execution regression
full repository pytest
synthetic adversarial suite
git diff --check and final scope review
```

Any correctness/security failure returns the project to repair. Standards are not lowered to obtain PASS.

## Implementation alignment

```text
P1_ANCHORING_RECONCILIATION = COMPLETE_IMPLEMENTED
P2_TEMPORAL_CLAIM_SEPARATION = IMPLEMENTED_REPAIR_PENDING_REGRESSION
P3_DEPENDENCY_COMPRESSION = COMPLETE
P4_PROVIDER_QUALIFICATION_COMPLEXITY_FIREWALL = COMPLETE_HARDENED
P5_VERSIONED_IMPLEMENTATION = POST_P6_REPAIR_PENDING_REGRESSION
CURRENT_EFFECTIVE_CANDIDATE = V0_6
CURRENT_EFFECTIVE_OBJECT_COUNT = 21
CURRENT_V0_6_CANDIDATE_DESIGN_ALIGNED = PENDING_FRESH_REGRESSION
CURRENT_SUCCESSOR_LOW_LEVEL_CLAIM_HELPERS = NON_AUTHORITATIVE
CURRENT_FINAL_GENESIS_AUTHORITY_PATH_IMPLEMENTED = YES_PENDING_FRESH_REGRESSION
CURRENT_CYCLE_PLAN_SUCCESSOR_CLAIM_INPUT_ALIGNED = YES_PENDING_FRESH_REGRESSION
CURRENT_VALIDATION_REPORT_CLAIM_AUTHORITY_CLOSED = PENDING_FRESH_REGRESSION
CURRENT_PROVIDER_ADMISSION_FIREWALL_ALIGNED = YES_FOR_QUALIFICATION_STATE_BOUNDARY
CURRENT_WALL_CLOCK_EXECUTION_ACCOUNTING_BOUND = NO_P7_F1_OPEN
CURRENT_QUALIFICATION_SIGNATURE_AUTHORITY_PINNED = YES
CURRENT_READINESS_MATRIX_ALIGNED = YES_CURRENT_CONTROL_ALIGNED
CURRENT_ABORT_CONDITIONS_ALIGNED = YES_CURRENT_CONTROL_ALIGNED
P5_CLAIM_AUTHORITY_REPAIR_REQUIRED = IMPLEMENTED_PENDING_REGRESSION
P6_REGRESSION_REQUIRED = YES
GENESIS_READY = NO
```

## Retained production qualification state

```text
PRODUCTION_QUALIFICATION_CRITERIA = FROZEN_V1
criteria_id = FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1
criteria_sha256 = 88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
ACTIVE_MAINLINE = POST_P6_CORRECTNESS_REPAIR
```

Historical provider rehearsal evidence remains `NON_FORECAST_REHEARSAL` with `prospective_eligible=false`.

## Repository and PR control

PR #6 must remain Draft, open, and unmerged unless separately authorized. No force push, rebase or history rewrite is authorized.

## Network boundary

```text
network_authorized = false
Roughtime provider requests authorized = 0
RFC3161 requests authorized = 0
production qualification requests authorized = 0
```

Repository/test access is ordinary development network use and does not authorize protocol-provider traffic.

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

The Genesis Ed25519 private key remains outside repository, GitHub, CI, ChatGPT, Codex, logs, prompts, fixtures and third-party systems.
