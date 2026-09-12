# Next Accepted Task

Task ID: GEN_001
State: GO 1.27 OFFLINE CRYPTOGRAPHIC VERIFIER GATE REQUIRED; NETWORK REQUEST NOT AUTHORIZED

## Objective

Close the remaining offline Roughtime verifier build and fixture gate without creating Forecast Ledger history, sending provider requests, or introducing a paid dependency.

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

The repository contains a project-controlled strict wrapper candidate with only `build-request` and `verify-response`, persistent per-root retry state, exact build-profile schema and semantic validation, actual artifact binding in plan and authorization tooling, duplicate-key-rejecting control JSON parsing, and full six-artifact final checker binding.

The Go 1.23 test path validates project core guards only. It does not establish cryptographic qualification.

## Next accepted work

1. Acquire the exact pinned `github.com/tannerryan/roughtime` source for tag `v1.27.0`, commit `56b346a16cd7e8317bb0d24f1ec15549cf93a4c9`, and retain its source archive bytes.
2. Acquire an exact Go 1.27.x patch release in a zero-cash owner-controlled or otherwise explicitly accepted environment.
3. Freeze dependency lock bytes and compute `dependency_lock_sha256`.
4. Compute `upstream_source_archive_sha256` and the project wrapper source tree hash.
5. Run the Go 1.27 offline fixture matrix covering typed hash-first, typed node-first, untyped draft 12, wrong root, mutated response, wrong nonce, and wrong packet/profile rejection.
6. Build with `go build -trimpath -buildvcs=false -ldflags=-buildid= -o fpp-roughtime-strict .` under `CGO_ENABLED=0` and hash the produced binary.
7. Produce and validate the complete content-addressed verifier build profile.
8. Run the complete repository test suite.
9. Perform final offline adversarial review.
10. Recheck provider endpoint, root, operator, and standards-transition evidence immediately before any later network authorization.

No provider packet is authorized by this task.

## Later network boundary

A first network rehearsal still requires a separate exact authorization binding the synthetic subject bytes and SHA256, frozen deadline, three-provider pool, plan SHA256, authorization SHA256, pinned verifier commit, verifier build profile, retry-state snapshot, exact wire/TYPE/SRV/packet profiles, attempt limits, timeout/backoff, evidence directory, `classification = NON_FORECAST_REHEARSAL`, and `prospective_eligible = false`.

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
