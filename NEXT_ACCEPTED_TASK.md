# Next Accepted Task

Task ID: GEN_001-P7-POST-P6-CORRECTNESS-REPAIR-REGRESSION
State: PRE_GENESIS correctness repair; P7 paused; fresh exact-head regression required; provider network requests not authorized

## Objective

Validate the post-P6 correctness repair on `repair/p7-authority-contracts` without changing Genesis, provider qualification state, frozen qualification criteria, candidate lineage, or network authorization.

The repair basis is:

```text
aa453268e4420dff6ea5ba3208e286d158f52e32
```

The controlling repair record is:

```text
docs/GEN_001_P7_POST_P6_REPAIR_FINDINGS_2026_09_16.md
```

The repair addresses:

```text
R1 production receipt admission/schema incompatibility
R2 sealed-but-contract-invalid claim-authority inputs
R3 incomplete DurabilityVerificationRecord contract gate
R4 provider independence evidence authority-location inconsistency
```

`P7_F1` remains intentionally open:

```text
COMPLETE_FROZEN_PROVIDER_EXECUTION_ACCOUNTING_NOT_BOUND_TO_PRODUCTION_WALL_CLOCK_CLAIM
```

Do not close `P7_F1` by reusing rehearsal evidence, inventing hidden production state, or silently weakening `policy:deadline-receipt-quorum:v3`.

## Safety precheck

Before any local test or write, dynamically prove:

```text
repository = edwardsage419/ForecastProvenance
branch = repair/p7-authority-contracts
remote branch HEAD = exact intended repair test HEAD
local HEAD = same exact repair test HEAD
working tree clean
index clean
PR #6 remains Draft / open / unmerged
design/gen-001 has not moved unexpectedly
```

Any mismatch requires a safety stop.

Do not use reset --hard, rebase, force push, merge, or deletion of unknown files to manufacture the expected state.

## Required offline validation

Run from a clean local checkout of the exact repair HEAD.

At minimum record exact commands, exit codes and summaries for:

```text
python --version
pytest --version
python compile/import checks
Draft 2020-12 schema meta-validation
```

Then run focused regression covering:

```text
tests/test_production_receipt_admission_v1.py
tests/test_claim_authority_contract_gate_v1.py
tests/test_claim_authority_v1.py
tests/test_claim_authority_trust_root_v1.py
tests/test_claim_authority_qualification_root_v1.py
tests/test_architecture_compression_p5.py
tests/test_architecture_compression_p5_hardening.py
```

Also run all existing Roughtime qualification/execution/verifier tests and the repository synthetic adversarial suite.

Finally run the complete repository pytest suite.

## Required repair properties

The regression must establish that:

1. a schema-shaped production receipt can bind the exact ProviderProfile and qualification state package without copied profile fields;
2. wrong ProviderProfile/state/verifier bindings fail closed;
3. sealed objects with unexpected fields fail at the authoritative contract gate;
4. wrong schema version/object type/origin/prospective eligibility values fail where prohibited;
5. malformed references fail closed;
6. a contract-invalid ExternalTimeEvidenceBundle cannot produce verified Bitcoin durability;
7. a contract-invalid DurabilityVerificationRecord cannot contribute to verified pre-outcome durability;
8. exact valid retained evidence still follows the pre-repair claim derivation algorithm after passing the gate;
9. provider qualification authority reconstruction remains exact and fail closed;
10. no production readiness result can be produced from synthetic evidence;
11. no candidate bytes or historical objects have been silently changed.

## Compatibility rule

Do not weaken the new gate merely to preserve an old synthetic fixture that violates the normative object contract.

If an older synthetic test fixture is schema-invalid, repair the fixture or explicitly isolate it as a non-authoritative low-level unit fixture. Production and TrustedManifest-facing authority semantics remain controlling.

## P6 restart rule

The historical P6 PASS remains historical evidence only.

After any repair source/test/schema/control modification, a fresh complete P6 run is required on the exact final repaired HEAD before the project may return to P7 dependency reevaluation.

Passing subsets from different repair HEADs cannot be combined into one P6 PASS.

## Prohibited actions

This task does not authorize:

```text
Genesis
Forecast Ledger Genesis creation
Forecast Ledger creation
prospective forecasting
Roughtime provider requests
RFC3161 requests
production qualification execution
OpenTimestamps submission
Bitcoin anchoring action
Genesis private-key access
qualification-criteria weakening
PR #6 merge or conversion from Draft
force push
```

## Completion gate

Only after all mandatory offline checks pass on one exact clean repair HEAD may the repair be proposed for non-force integration into `design/gen-001`.

After integration, project control must record the new exact HEAD and rerun complete P6 from zero before P7 resumes.

Until then:

```text
P5_CLAIM_AUTHORITY_REPAIR_REQUIRED = YES
P6_REGRESSION_REQUIRED = YES
P7 = PAUSED_FOR_REPAIR
P7_FINAL_DECISION = NOT_REACHED
PRODUCTION_QUALIFIED = NO
production-qualified provider count = 0
GENESIS_READY = NO
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
network_authorized = false
```
