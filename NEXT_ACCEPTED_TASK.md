# Next Accepted Task

Task ID: GEN_001
State: GO 1.27 OFFLINE QUALIFICATION EXECUTION REQUIRED; NETWORK REQUEST NOT AUTHORIZED

## Objective

Execute the now-frozen Roughtime verifier qualification harness in a zero-cash environment with an exact Go 1.27.x toolchain, without creating Forecast Ledger history or sending provider requests.

## Frozen design retained

```text
FPP_TIME_EVIDENCE_V1
policy:deadline-receipt-quorum:v3
FPP_ROUGHTIME_NONCE_V2
candidate lineage v0.2 + v0.3 + v0.4 + v0.5
provider pool = roughtime.se, time.txryan.com, TimeNL-Roughtime
packet profile = STANDARD_1024_BODY
transport profile = UDP_ONLY
quorum = 2-of-3
```

Cloudflare-Roughtime-2 remains historical only.

## Offline tooling now frozen as candidate

The repository contains the strict offline wrapper, deterministic Go 1.27 synthetic cryptographic fixtures, persistent per-root retry state, artifact-bound plan and authorization tooling, dependency-lock and fixture-report validators, verifier build-profile validation, and a two-stage qualification harness.

The current execution environment can run the Go 1.23 core path and Python control tests, but cannot acquire a Go 1.27 toolchain because outbound Go toolchain/module download is blocked. This is an execution-environment gate.

## Next accepted execution

1. Install or otherwise provide an exact Go 1.27.x patch release in an owner-controlled or otherwise explicitly accepted zero-cash environment.
2. Run `scripts/genesis/qualify_roughtime_verifier.py freeze-dependencies` against `scripts/genesis/roughtime_strict_verifier/`. This stage may use standard Go module infrastructure and must retain both the dependency-lock JSON and exact pinned upstream Go module Zip.
3. Transfer or retain those artifacts unchanged for the final stage.
4. Run `scripts/genesis/qualify_roughtime_verifier.py qualify-offline`. This stage freezes `GOTOOLCHAIN=local`, `CGO_ENABLED=0`, `GOFLAGS=-mod=readonly`, `GOPROXY=off`, and `GOSUMDB=off`.
5. Require `go mod verify` to pass and require the retained upstream module Zip to be byte-identical to the cached h1-checked Zip used by Go.
6. Require the exact GOROOT tree hash, wrapper source-tree hash, dependency lock, fixture report, frozen build command, produced binary hash, and final verifier build profile to cross-bind.
7. Require every Go 1.27 fixture to pass, including typed hash-first, typed node-first, untyped draft 12, wrong root, mutated response, wrong nonce, and packet/profile rejection.
8. Run the complete repository test suite.
9. Perform final offline adversarial review.
10. Recheck provider endpoint, root, operator, and standards-transition evidence immediately before any later network authorization.

No provider packet is authorized by this task.

## Later network boundary

A first network rehearsal still requires a separate exact authorization binding the synthetic subject bytes and SHA256, frozen deadline, three-provider pool, plan SHA256, authorization SHA256, pinned verifier commit, validated verifier build profile, retry-state snapshot, exact wire/TYPE/SRV/packet profiles, attempt limits, timeout/backoff, evidence directory, `classification = NON_FORECAST_REHEARSAL`, and `prospective_eligible = false`.

The offline plan remains `network_authorized=false`.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
Roughtime provider requests sent by this work = 0
RFC3161 requests sent by this work = 0
```
