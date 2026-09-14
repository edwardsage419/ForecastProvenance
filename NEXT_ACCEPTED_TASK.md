# Next Accepted Task

Task ID: GEN_001-AC-P6-RESTART
State: PRE_GENESIS ARCHITECTURE COMPRESSION; P6 FULL OFFLINE REGRESSION NEXT; PROVIDER NETWORK REQUEST NOT AUTHORIZED

## Objective

Restart P6 from zero against the exact final P5 claim-authority-hardened HEAD and determine whether the compressed Genesis v1 implementation passes complete offline regression and synthetic adversarial execution.

P5 implementation repair is complete at repository level but has not yet earned a regression PASS. P6 is the gate that tests the repair.

The P6 input commit is the exact `design/gen-001` HEAD containing this project-control transition after all P5 code/schema/docs changes. Resolve that SHA from Git/GitHub immediately before creating the validation checkout; do not self-embed or infer it from an earlier message.

## Controlling records

```text
docs/GEN_001_GENESIS_ANCHORING_RECONCILIATION_V1.md
docs/GEN_001_TEMPORAL_CLAIM_SEPARATION_V1.md
docs/GEN_001_GENESIS_V1_DEPENDENCY_COMPRESSION_V1.md
docs/GEN_001_PROVIDER_QUALIFICATION_COMPLEXITY_FIREWALL_V1.md
docs/GEN_001_ARCHITECTURE_COMPRESSION_P5_IMPLEMENTATION_REVIEW.md
docs/GEN_001_ARCHITECTURE_COMPRESSION_P6_STATIC_REVIEW_AND_P5_HARDENING_2026_09_14.md
docs/GEN_001_P6_FINDING_3_CLAIM_AUTHORITY_BOUNDARY_2026_09_14.md
```

Finding 3 status before execution:

```text
IMPLEMENTATION_REPAIRED_PENDING_REGRESSION
```

It does not become closed until this P6 execution passes.

## Repository safety precheck

Before running tests, dynamically establish:

```text
repository = edwardsage419/ForecastProvenance
branch remote = design/gen-001
PR #6 = Draft / open / unmerged
remote design/gen-001 HEAD = exact intended P6 input SHA
remote main ancestry = no unexpected divergence
```

Use a fresh clean validation checkout when practical. Checkout the exact commit in detached mode or otherwise prove that local HEAD equals the exact frozen P6 input SHA.

Required local proof before execution:

```text
git rev-parse HEAD == exact frozen P6 input SHA
git status --short == empty
```

Unknown tracked modifications, unexpected commits, remote history movement, branch mismatch, or an inability to identify the exact tree requires a safety stop.

Do not use `reset --hard`, rebase, merge, force push, or deletion of unknown files to manufacture a clean state.

## P6 execution rule

P6 is validation only. Do not modify Trust Core source, schemas, candidate bytes, tests or normative controls while accumulating a PASS result.

If any correctness/security failure requires a code/schema/test correction:

```text
P6 = FAILED / INVALIDATED
return to P5 repair
create a new exact HEAD
restart all mandatory P6 execution from zero
```

Passing subsets from an earlier HEAD cannot be combined with a later repaired HEAD.

## Required execution scope

### 1. Environment capture

Record at minimum:

```text
exact Git commit SHA
Python version
platform
pytest version
jsonschema version
relevant declared dependency versions
```

Retain exact commands and exit codes.

### 2. Python compile/import checks

Compile/import the complete Trust Core and Genesis helper surface required by the repository.

At minimum include the new successor modules:

```text
forecast_trust_core.architecture_compression_v1
forecast_trust_core.architecture_compression_v1_hardening
forecast_trust_core.claim_authority_v1
forecast_trust_core.claim_authority_trust_root_v1
forecast_trust_core.production_receipt_admission_v1
```

Any syntax/import failure blocks P6.

### 3. JSON Schema Draft 2020-12 meta-validation

Run `Draft202012Validator.check_schema` or the repository-equivalent check over every JSON Schema in `schemas/`, including the Architecture Compression additions:

```text
manifest_acceptance_v2.schema.json
validation_report_v2.schema.json
roughtime_provider_qualification_state_package.schema.json
roughtime_qualification_verifier_contract_v1.schema.json
external_time_evidence_bundle_v1.schema.json
roughtime_production_receipt_evidence_v1.schema.json
open_timestamps_proof_artifact_v1.schema.json
strong_bitcoin_verifier_contract_v1.schema.json
strong_bitcoin_verification_report_v1.schema.json
durability_verification_record_v1.schema.json
```

Historical seven-schema meta-validation does not substitute for this fresh current-tree check.

### 4. Candidate lineage and materialization regression

Verify deterministic materialization of:

```text
candidate_object_set_v0_2.json
+ candidate_patch_v0_3.json
+ candidate_patch_v0_4.json
+ candidate_patch_v0_5.json
+ candidate_patch_v0_6.json
```

Required successor facts include:

```text
effective object count = 21
Acceptance v1 exact predecessor retired
Evaluation v1 exact predecessor retired
Human Review v1 exact predecessor retired
Acceptance v2 sealed and active
Evaluation v2 sealed and active
historical v0.2-v0.5 bytes unchanged
```

### 5. Historical regression

Run historical candidate/object, Trust Core, source, rehearsal, qualification and verifier tests required by the repository.

Architecture Compression must not silently reinterpret historical contracts.

### 6. P1 acceptance regression

Exercise at least:

```text
noncircular ManifestAcceptance v2
exact TrustedManifest binding
exact BootstrapGovernanceRoot ref binding where applicable
final evidence supplied after signing
wrong final evidence subject rejected
wall-clock and Bitcoin final evidence bind the same exact subject/bundle as required
```

Low-level caller-supplied final-state strings must not constitute the successor authoritative readiness path.

### 7. P2 claim separation and claim-authority regression

Run all focused claim tests, including:

```text
exact claim type/subject binding
VERIFIED/FAILED/UNRESOLVED/NOT_APPLICABLE propagation
timely existence with late durability
pending Bitcoin durability
missed deadline cannot be repaired by Bitcoin
wrong subject or evidence refs
raw bound/state-string injection rejected
persisted ValidationReport cannot authorize itself
exact persisted/recomputed report equality accepted
synthetic evidence cannot satisfy production readiness
```

Required focused files include:

```text
tests/test_architecture_compression_p5.py
tests/test_architecture_compression_p5_hardening.py
tests/test_claim_authority_v1.py
tests/test_claim_authority_trust_root_v1.py
tests/test_claim_authority_qualification_root_v1.py
```

### 8. P4 provider qualification firewall regression

Verify:

```text
content-closed state-store collection
omitted metadata/requalification event fails closed
self-asserted qualification state rejected
exact historical as_of recomputation
exact ProviderProfile/QualificationDecision binding
three-provider admitted-pool rule
no outage threshold reduction
wrong/stale/requalified provider state rejected
production receipt/profile admission binding
```

### 9. Qualification signature-authority regression

Specifically execute the newly added authority-substitution tests:

```text
caller-injected signature_verifier rejected
caller-injected expected authority fields rejected
wrong independent authority public key rejected
substituted qualification verifier contract rejected
qualification verifier contract binding a different main ValidatorContract rejected
wrong Ed25519 build-profile/binary identity rejected
extra/missing provider authority input rejected
state-package provider identities must match the exact admitted ProviderProfile set
exact binding constructs the pinned verifier internally
```

The accepted public key is verification-only input. The Genesis private key must never be accessed or supplied.

### 10. Bitcoin durability regression

Verify the strong Bitcoin authority boundary with synthetic/local fixtures:

```text
exact StrongBitcoinVerifierContract binding
hash-pinned local executable
exact ExternalTimeEvidenceBundle bytes
exact OTS proof bytes
wrong/spliced bundle or proof rejected
failed strong verification rejected
persisted strong report mismatch rejected
Bitcoin header time not used as civil-time deadline evidence
```

No live Bitcoin anchoring action is required by this P6 regression.

### 11. Full pytest

Run the complete repository pytest suite, not only focused files.

Record:

```text
command
exit code
total passed
failed
skipped/xfailed if any
warnings relevant to correctness
```

Any unexpected skip of a mandatory security test blocks PASS until classified.

### 12. Synthetic adversarial suite

Run the complete synthetic adversarial suite/registry. Explicitly preserve attacks found during P6 static review:

```text
cross-subject claim substitution
self-asserted provider qualification state
omitted requalification event
caller-supplied final VERIFIED state
verifier plus expected-ref simultaneous substitution
runtime signature-callback substitution
authority-key substitution
synthetic/live evidence confusion
wall-clock/Bitcoin evidence splicing
forged persisted ValidationReport
extra unbound provider/evidence input
```

## P6 PASS conditions

P6 may be marked PASS only if all mandatory execution categories above complete successfully against the same exact frozen HEAD and no unresolved correctness/security blocker remains.

A final P6 report must bind at minimum:

```text
exact HEAD
exact commands
relevant environment versions
schema meta-validation result
focused regression result
full pytest result
synthetic adversarial result
failure/skip accounting
report SHA256/content identity
```

Only after that report is independently checked may project control advance to P7.

## P7 boundary

P7 remains prohibited until P6 PASS.

A P6 PASS does not automatically resume production qualification. P7 only reevaluates whether continuing Roughtime production qualification is actually required by the refrozen minimal Genesis profile.

## Retained qualification state

```text
PRODUCTION_QUALIFICATION_CRITERIA = FROZEN_V1
criteria_id = FPP_ROUGHTIME_PRODUCTION_QUALIFICATION_V1
criteria_sha256 = 88cc910fdb7e573f3a84d860ad0cdc5fffc287db18678956c7e50dc52a07639e
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
ACTIVE_MAINLINE = PAUSED
```

P6 does not execute provider qualification and cannot create a QualificationDecision or production ProviderProfile.

## Network boundary

```text
network_authorized = false
Roughtime provider requests authorized by this task = 0
RFC3161 requests authorized by this task = 0
production qualification requests authorized by this task = 0
```

Ordinary Git/GitHub repository access needed to obtain the exact validation checkout is development infrastructure access and does not authorize any protocol-provider request.

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
P6_PASS = NO
P7 = PROHIBITED_UNTIL_P6_PASS
```

The Genesis Ed25519 private key must not be accessed, read, copied, displayed, uploaded, transmitted, logged, referenced or processed.
