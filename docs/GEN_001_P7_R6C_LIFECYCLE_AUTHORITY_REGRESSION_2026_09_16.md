# GEN_001 P7 R6-C Lifecycle Authority Regression — 2026-09-16

Status: REGRESSION_CONFIRMED
Classification: NON_FORECAST_REVIEW
Prospective eligible: false
Genesis effect: none
Network authorization: none

## Exact tested source

```text
branch under review = design/p7-v4-r6
exact tested HEAD = 462d7d4ecde6df38dcffe15277240e0faaea2d0b
```

The owner executed the regression from a clean detached worktree at the exact HEAD above. The remote branch HEAD matched the expected commit before execution.

## Results

```text
compileall = PASS
R6-C manifest-rooted lifecycle authority = 15 passed
R6-B source authority regression = 31 passed
R6-A lifecycle contract regression = 13 passed
candidate v0.7 focused regression = 28 passed + 70 subtests
existing confirmatory fail-closed regression = 37 passed
full repository pytest = 457 passed + 188 subtests
git diff --check = PASS
working tree after execution = clean
historical candidate v0.2-v0.6 byte diff exit = 0
```

No failure, error, skip, dirty-tree condition, network authorization, provider request, Genesis action, or prospective forecast execution was reported by this run.

## R6-C conclusion

R6-C is regression-confirmed at the exact tested HEAD.

The confirmed authority closure reconstructs the initial Genesis-v1 deterministic lifecycle from the exact sealed TrustedManifest through target/method/source/policy admission, retained source replay, schedule-derived cycle barriers, exact plan/slot construction, point-in-time baseline evidence, retry/first-success accounting, deterministic prediction replay, immutable IssuedForecast binding, and complete cycle-manifest membership/accounting.

R6-C does **not** establish that the TrustedManifest is accepted, that Genesis has been authorized, or that a forecast is confirmatory-prospective eligible. A successful R6-C result is only a non-temporal lifecycle authority closure.

## Remaining R6-D boundary

R6-D must close the governance and temporal authority layers before any positive confirmatory claim is possible. At minimum it must establish from exact retained inputs:

1. owner-authenticated ManifestAcceptance under the independently supplied BootstrapGovernanceRoot;
2. successful final acceptance existence and Bitcoin durability verification for that exact signed acceptance;
3. a separate machine-verifiable explicit Genesis authorization bound to the same manifest/acceptance/root;
4. cycle execution under that authorization;
5. plan and cycle-manifest deadline existence claims;
6. required Bitcoin durability and pre-outcome durability claims;
7. exact aggregation into `CONFIRMATORY_PROSPECTIVE_ELIGIBLE` only after all structural and temporal requirements pass.

The existing generic confirmatory path remains deliberately fail-closed.

## Safety state

```text
R6-A = REGRESSION_CONFIRMED
R6-B = REGRESSION_CONFIRMED
R6-C = REGRESSION_CONFIRMED
R6-D = OPEN
AUTHORITATIVE_CONFIRMATORY_VERIFIED = PROHIBITED
candidate v0.7 = CREATED / NOT FROZEN
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production qualified provider count = 0
PRODUCTION_QUALIFIED = NO
network_authorized = false
```
