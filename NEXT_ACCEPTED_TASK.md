# Next Accepted Task

Task ID: GEN_001-AC-P6-RESTART
State: PRE_GENESIS ARCHITECTURE COMPRESSION; P6 POST-REPAIR COMPLETE OFFLINE REGRESSION AND SYNTHETIC ADVERSARIAL SUITE; NETWORK REQUEST NOT AUTHORIZED

## Objective

Run the complete offline regression and synthetic adversarial suite against the exact post-repair HEAD after P6 static review returned two blocking P5 correctness defects.

P6 is not complete and has no PASS. The defects were repaired without weakening P1 through P4 semantics. Every execution result must now be regenerated from the post-repair bytes.

## Controlling repair record

`docs/GEN_001_ARCHITECTURE_COMPRESSION_P6_STATIC_REVIEW_AND_P5_HARDENING_2026_09_14.md`

The repaired authoritative path is:

`src/forecast_trust_core/architecture_compression_v1_hardening.py`

The earlier `architecture_compression_v1.py` claim-composition and package-state helpers remain low-level primitives and cannot independently establish the stronger P2/P4 claims.

## Pre-execution repository check

Before any test conclusion recheck dynamically:

```text
repository = edwardsage419/ForecastProvenance
branch = design/gen-001
PR #6 = Draft / open / unmerged
HEAD = exact current post-repair commit
local execution tree = exact bytes of that HEAD
working tree = clean except explicitly understood test artifacts
```

Unexpected branch movement, unknown local changes, incomplete checkout, or remote history divergence stops test conclusions.

## Required P6 execution

Run at least:

```text
python compile/import checks
Draft 2020-12 JSON Schema meta-validation for all schemas
historical candidate v0.2-v0.5 tests
candidate v0.6 materialization and exact retirement/hash tests
P1/P2/P4 Architecture Compression tests
P6-discovered hardening adversarial tests
production receipt exact-profile admission tests
qualification supporting-subsystem regression
complete repository pytest suite
complete synthetic adversarial suite
```

Existing frozen harnesses take precedence over ad hoc substitutes.

## Required P6 hardening cases

In addition to the original P6 matrix, verify at least:

1. `DEADLINE_EXISTENCE_VERIFIED(S)` rejects an external-existence claim for any subject other than exact `S`.
2. pre-outcome durability rejects a Bitcoin durability claim for the wrong primary subject.
3. pre-outcome durability rejects a deadline claim for the wrong DurabilityVerificationRecord.
4. the DurabilityVerificationRecord must bind the exact primary subject.
5. confirmatory eligibility accepts only the exact predeclared component claim-type/subject requirement set.
6. unknown claim types are rejected.
7. `CONFIRMATORY_PROSPECTIVE_ELIGIBLE` cannot recursively serve as one of its own component requirements.
8. malformed qualification-state-store JSON fails closed.
9. state-store symlink or unexpected file fails closed.
10. noncanonical metadata/requalification event timestamps fail closed.
11. complete state-event enumeration alone cannot authorize a self-asserted `PRODUCTION_QUALIFIED` state.
12. package state and state-report SHA256 must equal `derive_authoritative_qualification_state` output.
13. authoritative recomputation must bind the exact provider and exact as-of.
14. all three provider packages must pass authoritative recomputation before two-of-three receipt quorum is considered.
15. production receipt profile binding remains required in addition to provider-state admission.

## Original P6 cases retained

P6 must also confirm:

1. ManifestAcceptance v2 has no final-evidence self-reference requirement.
2. wrong final evidence subject fails.
3. verified wall-clock deadline existence remains verified when stronger durability later fails.
4. pending Bitcoin evidence remains UNRESOLVED.
5. Bitcoin durability cannot repair a missed wall-clock deadline.
6. Genesis governance maps pre-outcome durability and scientific eligibility to NOT_APPLICABLE.
7. candidate v0.6 materializes to 21 exact objects.
8. Human Review v1 is absent from the effective successor candidate while historical bytes remain retained.
9. EvaluationPolicy v2 has no self-baseline delta or normative aggregation surface.
10. a requalification event through the historical as-of cannot be omitted.
11. all three provider states must be PRODUCTION_QUALIFIED at the frozen deadline.
12. duplicate provider identity cannot count twice.
13. exact ProviderProfile/QualificationDecision/state-package binding is required.
14. root/wire/verifier/profile mismatch fails closed.
15. historical qualification/rehearsal semantics remain unchanged.

## Failure handling

Any security or correctness failure returns to root-cause repair.

Do not lower expectations, weaken frozen provider qualification criteria, loosen receipt quorum, reinterpret historical candidate objects, convert a failed required claim to NOT_APPLICABLE, or skip a failing security test merely to obtain a PASS.

Infrastructure-only failures must remain distinct from implementation failures.

## Execution-environment status

The previous container could not resolve either `github.com` or `api.github.com`, so no exact local checkout and no full P6 execution occurred.

GitHub connector read access is sufficient for exact static review but is not a substitute for the required offline executable regression.

If this environment limitation persists, P6 remains `IN_PROGRESS_EXECUTION_ENVIRONMENT_BLOCKED`; it does not become PASS by static inspection alone.

## Required P6 completion record

Record:

```text
exact tested HEAD
exact tree acquisition method
commands executed
Python/runtime/tool versions
compile/import result
schema meta-validation counts
pytest pass/fail/skip counts
synthetic adversarial pass/fail counts
all failures/skips and reasons
any repair commits
final P6 disposition
```

If repository bytes change after any test, the new exact HEAD must be retested from the beginning.

## P7 gate

P7 remains prohibited until P6 passes on the exact post-repair HEAD.

P6 itself authorizes no provider network traffic and no production qualification.

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

## Network boundary

```text
network_authorized = false
Roughtime provider requests authorized by this task = 0
RFC3161 requests authorized by this task = 0
production qualification requests authorized by this task = 0
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

The Genesis Ed25519 private key must not be accessed, read, copied, displayed, uploaded, transmitted, logged, referenced or processed.