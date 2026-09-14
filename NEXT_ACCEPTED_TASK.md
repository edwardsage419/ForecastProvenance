# Next Accepted Task

Task ID: GEN_001-AC-P6
State: PRE_GENESIS ARCHITECTURE COMPRESSION; P6 COMPLETE OFFLINE REGRESSION AND SYNTHETIC ADVERSARIAL SUITE; NETWORK REQUEST NOT AUTHORIZED

## Objective

Run the complete offline regression and synthetic adversarial suite against the exact final P5 HEAD.

P6 verifies that candidate v0.6, successor schemas, Architecture Compression validators, provider-admission firewall, readiness controls and historical compatibility all pass together without weakening any frozen standard.

P6 is execution/verification only. It does not execute production qualification, request provider traffic, create Genesis, create Forecast Ledger state, access the Genesis private key, or issue a prospective forecast.

## Required repository basis

Before execution, recheck:

```text
repository = edwardsage419/ForecastProvenance
branch = design/gen-001
PR #6 = Draft / open / unmerged
working tree = clean except explicitly understood local test artifacts
HEAD = dynamically re-fetched exact P5 final commit
```

Unexpected branch movement, unknown local modifications, or remote history divergence requires a safety stop before test conclusions.

## Required P6 execution

Run at least:

```text
python compile/import checks
Draft 2020-12 JSON Schema meta-validation for all schemas
historical candidate v0.2-v0.5 tests
candidate v0.6 materialization and exact retirement/hash tests
Architecture Compression P1/P2/P4 focused tests
production receipt exact-profile admission tests
qualification supporting-subsystem regression
complete repository pytest suite
complete synthetic adversarial suite
```

The exact existing project commands should be used where already defined. Do not invent a weaker substitute when a frozen harness exists.

## Required Architecture Compression cases

P6 must confirm at least:

1. ManifestAcceptance v2 has no final-evidence self-reference requirement.
2. Wrong final evidence subject fails.
3. Verified wall-clock deadline existence remains verified when stronger durability later fails.
4. Pending Bitcoin evidence remains UNRESOLVED.
5. Bitcoin durability cannot repair missed wall-clock deadline evidence.
6. Genesis governance maps pre-outcome durability and scientific eligibility to NOT_APPLICABLE.
7. candidate v0.6 materializes to 21 exact objects.
8. Human Review v1 is absent from the effective successor candidate while historical bytes remain retained.
9. EvaluationPolicy v2 has no self-baseline delta or normative aggregation surface.
10. caller-selected qualification-state event subsets are rejected.
11. a requalification event through the historical as-of cannot be omitted.
12. all three provider states must be PRODUCTION_QUALIFIED at the frozen deadline.
13. duplicate provider identity cannot count twice.
14. exact ProviderProfile/QualificationDecision/state-package binding is required for a production receipt.
15. root/wire/verifier/profile mismatch fails closed.
16. historical qualification/rehearsal semantics remain unchanged.

## Failure handling

Any failure with security or correctness significance returns the project to P5 for root-cause repair.

Do not:

1. lower test expectations;
2. weaken frozen provider qualification criteria;
3. loosen receipt quorum;
4. reinterpret historical candidate objects;
5. mark a failed claim as NOT_APPLICABLE merely to obtain a pass;
6. skip a failing security test without a documented reason and owner review.

Infrastructure-only failures must be distinguished from implementation failures and retained in the P6 execution record.

## P6 completion output

Record:

```text
exact tested HEAD
commands executed
tool/runtime versions
test and subtest counts
schema meta-validation counts
synthetic adversarial counts
failures/skips with reason
changed files if any repair was required
final P6 disposition
```

If repair changes repository bytes, the exact new HEAD must be retested; an earlier PASS cannot be carried forward to changed bytes.

## P7 gate

Only after P6 passes against the exact compressed-profile HEAD may the project reconsider whether further Roughtime production qualification work is actually required before Genesis readiness can progress.

P6 itself does not authorize P7 network activity.

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

The Genesis Ed25519 private key must not be accessed, read, copied, displayed, uploaded, transmitted, logged, referenced, or processed.
