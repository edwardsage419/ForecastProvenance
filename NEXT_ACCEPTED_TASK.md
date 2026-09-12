# Next Accepted Task

Task ID: GEN_001
State: POST-VENDORING GO 1.27 OFFLINE QUALIFICATION REQUIRED; NETWORK REQUEST NOT AUTHORIZED

## Objective

Execute the published vendored Roughtime verifier qualification path against the current formal branch HEAD, then run the complete repository suite and final offline adversarial review.

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

## Current offline state

Go 1.27.1 access is resolved.

The pinned upstream `protocol` compile inputs are vendored byte-for-byte from commit `56b346a16cd7e8317bb0d24f1ec15549cf93a4c9`. Their upstream Git blob SHA1 values are retained in `SOURCE_PROVENANCE.json`.

The accepted qualification path is single-stage and offline. It does not use Go proxy, sumdb, an upstream module Zip, or an external Go module.

The older module-Zip qualification implementation is superseded and is not the accepted execution path.

## Next accepted execution

1. Obtain a full checkout at the current formal `design/gen-001` HEAD.
2. Use exact Go 1.27.x with `GOTOOLCHAIN=local`.
3. Run `scripts/genesis/qualify_roughtime_verifier.py` with new output paths for dependency lock, fixture report, and build profile.
4. Bind the toolchain distribution source, inner distribution SHA256, carrier artifact SHA256, and actual GOROOT tree hash.
5. Require `go list -m all` to contain only `forecastprovenance/roughtime_strict_verifier`.
6. Require all vendored source Git blob SHA1 and SHA256 checks to pass.
7. Require all 15 Go tests to pass, including the Go 1.27 cryptographic fixture matrix.
8. Require the frozen binary build to pass and retain its new post-vendoring SHA256.
9. Require dependency lock 1.1, fixture report 1.1, and build profile 1.2 to cross-bind.
10. Run the complete repository test suite.
11. Perform final offline adversarial review.
12. Recheck provider endpoint, root, operator, and standards-transition evidence immediately before any later network authorization.

The pre-vendoring binary SHA256 is historical evidence and must not be reused in the post-vendoring build profile.

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
