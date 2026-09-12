# GEN_001 Roughtime strict verifier and control state freeze

Date: 2026-09-12
Status: OFFLINE TOOLING AND QUALIFICATION HARNESS CANDIDATE READY; GO 1.27 EXECUTION OPEN

## Safety boundary

This work creates offline tooling and a dependency-acquisition harness only. It does not authorize a Roughtime provider packet, an RFC 3161 POST, prospective forecasting, Forecast Ledger creation, Forecast Ledger Genesis, or Genesis.

```text
classification = NON_FORECAST_REHEARSAL
prospective_eligible = false
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```

## Pinned upstream

```text
repository = github.com/tannerryan/roughtime
tag = v1.27.0
tag object = e1ae332e5920429b11ec4f10a7dda399ebeb6df8
tag signature verification = verified
commit = 56b346a16cd7e8317bb0d24f1ec15549cf93a4c9
upstream Go requirement = 1.27.0
```

The strict project wrapper is under `scripts/genesis/roughtime_strict_verifier/`. Its project CLI exposes only `build-request` and `verify-response`. It contains no DNS, UDP, TCP, HTTP, provider-query, or socket execution path.

The Go 1.27 adapter uses only the pinned low-level `protocol` package. Request construction uses one offered version, `0x8000000c`, a caller-supplied 32-byte nonce, SRV derived from the frozen root, the frozen TYPE profile, and standard 1024-byte message-body framing. The expected framed request is 1036 bytes. Legacy 1024-byte total packets fail closed.

Verification binds the retained request bytes, exact nonce, exact frozen root, SRV, TYPE profile, signatures, delegation, signed version information, timestamp, radius, and Merkle proof through the pinned low-level verifier. Typed shared-wire providers accept either authenticated draft 14/15 node-first or draft 16 through 19 hash-first Merkle convention. The shared wire version does not identify an exact draft.

## Go toolchain split

Go 1.23 core-only tests exercise project CLI and fail-closed input guards without compiling the cryptographic adapter. The real adapter and synthetic cryptographic fixtures are guarded by `//go:build go1.27`.

A Go 1.23 core test result is never verifier qualification.

Final cryptographic execution requires an exact Go 1.27.x patch release. Qualification binds both the reported version and a deterministic SHA256 manifest of the actual `GOROOT` tree used for tests and build. Regular-file contents and symlink targets are included. Directories and timestamps are excluded. Unsupported special filesystem entries fail closed.

The frozen build command is:

```text
go build -trimpath -buildvcs=false -ldflags=-buildid= -o fpp-roughtime-strict .
```

## Two-stage qualification harness

`scripts/genesis/qualify_roughtime_verifier.py` separates dependency acquisition from final qualification.

Stage 1, `freeze-dependencies`, may access normal Go module infrastructure. It runs under:

```text
GOTOOLCHAIN=local
CGO_ENABLED=0
GOFLAGS=
GOPROXY=https://proxy.golang.org,direct
GOSUMDB=sum.golang.org
```

It downloads the resolved modules, freezes the exact `go.mod` and `go.sum` hashes, freezes the sorted resolved module set with module replacements prohibited, records the pinned upstream module and `go.mod` h1 checksums, and retains the exact Go module Zip returned for `github.com/tannerryan/roughtime@v1.27.0`. The Zip is accepted only when `go mod download -json` reports the same h1 checksums as the dependency lock.

Stage 2, `qualify-offline`, forces:

```text
GOTOOLCHAIN=local
CGO_ENABLED=0
GOFLAGS=-mod=readonly
GOPROXY=off
GOSUMDB=off
```

It runs `go mod verify`, recomputes the dependency lock from local material, confirms the retained upstream Zip is byte-identical to the cached module Zip actually used by Go, hashes the actual GOROOT tree and wrapper source tree, runs the complete required Go fixture matrix, builds the frozen binary, and emits the fixture report and build profile. Any missing cache content therefore fails instead of silently contacting a network service.

No provider endpoint is contacted by either stage.

## Frozen hash rules

The dependency lock contains exactly:

```text
schema_version
object_type
go_mod_sha256
go_sum_sha256
upstream_module_sum
upstream_go_mod_sum
modules
lock_sha256
```

`modules` is the unique sorted result of the frozen `go list -m` format, with the project module represented as `MAIN`. `lock_sha256` is SHA256 of canonical JSON for all preceding fields.

The wrapper source-tree hash uses an explicit allowlist of source inputs:

```text
adapter_go127.go
adapter_go127_test.go
adapter_pre127.go
core.go
core_test.go
go.mod
main.go
```

For each file it hashes raw bytes, constructs a path-sorted canonical JSON manifest, then hashes that manifest. Generated binaries, `go.sum`, caches, and unrelated directory contents cannot silently enter the wrapper source identity. `go.sum` is separately bound by the dependency lock.

The fixture report records `network_used=false`, `module_verify_passed=true`, exact Go version, GOOS, GOARCH, GOROOT tree hash, `CGO_ENABLED=false`, the exact test command, wrapper source-tree hash, required test PASS results, and its self hash.

## Verifier build profile

`roughtime_verifier_build_profile.schema.json` version 1.1 and executable validation bind exactly:

```text
schema_version
upstream_repository
upstream_tag
upstream_commit
upstream_tag_object_sha
upstream_tag_signature_verified
go_version
goos
goarch
go_toolchain_tree_sha256
cgo_enabled
dependency_lock_sha256
wrapper_source_tree_sha256
upstream_source_archive_sha256
verifier_source_bundle_sha256
build_command
binary_sha256
fixture_report_sha256
profile_sha256
```

`upstream_source_archive_sha256` is the raw SHA256 of the exact h1-checked Go module Zip retained by Stage 1 and matched to the local module cache in Stage 2.

`verifier_source_bundle_sha256` is SHA256 of the raw 32-byte `upstream_source_archive_sha256` digest followed by the raw 32-byte `wrapper_source_tree_sha256` digest.

Every retained receipt in a checked rehearsal package must use:

```text
verifier_source_sha256 = verifier_source_bundle_sha256
verifier_binary_sha256 = binary_sha256
```

No real build profile is claimed by this change because the exact Go 1.27 execution remains open in an environment able to acquire that toolchain.

## Persistent retry state

`RoughtimeRetryState` is operational control state:

```text
classification = CONTROL_STATE_NON_TIME_EVIDENCE
prospective_eligible = false
```

State is keyed by SHA256 of the frozen root public key. Hostname changes therefore cannot bypass backoff for an unchanged trust root.

The frozen backoff schedule starts at one second, multiplies by 1.5, rounds upward to an integer millisecond, and saturates at 86400 seconds. A network failure cannot be recorded while the root is still in active backoff. A properly signed verified response resets the root state even when project policy later classifies the response as `VERIFIED_NONQUALIFYING_RESPONSE`.

The local clock controls request rate only. It is never trusted deadline evidence. Mutable retry state is written atomically. Evidence snapshots use immutable content-addressed filenames and bind the exact pre-run and post-run states.

## Control artifact binding

The plan tool requires the actual verifier build profile JSON and retry-state JSON. Both are parsed with duplicate-key rejection, semantically validated, and hashed by the program before their hashes enter the plan.

The authorization tool reads and validates the same artifacts again and requires exact equality with the plan bindings.

The final offline checker requires plan, authorization, report, verifier build profile, retry state before, and retry state after. It performs the rehearsal semantic validation and additionally validates all control-artifact hashes and receipt source/binary hashes.

JSON Schema remains descriptive interoperability validation. It does not replace executable semantic validation or cryptographic replay.

## Offline checks executed for this candidate

```text
Python control tests = 18 PASS
Python qualification-harness tests = 15 PASS
Python combined focused tests = 33 PASS
Go 1.23 core-only strict-wrapper tests = 8 PASS
Roughtime control/qualification JSON Schemas = 4 VALID
Python compile = PASS
offline static network guard for strict wrapper = PASS
```

Go 1.27 cryptographic fixture source is checked in at `scripts/genesis/roughtime_strict_verifier/adapter_go127_test.go`, but those fixtures are NOT RUN in this environment. The matrix covers both frozen typed provider IDs, typed hash-first, typed node-first, untyped draft 12, wrong root, mutated response, wrong nonce, and packet/profile rejection using deterministic synthetic keys only.

No provider packet and no RFC 3161 POST were sent by these checks. No GitHub-hosted workflow was triggered by the published tooling commits.

## Remaining gate before any network rehearsal

1. Acquire an exact Go 1.27.x toolchain in a zero-cash owner-controlled or otherwise explicitly accepted environment.
2. Run `freeze-dependencies` to retain the h1-checked upstream module Zip and dependency lock.
3. Run `qualify-offline` with Go module networking disabled.
4. Require all Go 1.27 fixtures, `go mod verify`, source/archive/cache matching, frozen build, fixture report, and build-profile validation to pass.
5. Run the complete repository test suite.
6. Perform final offline adversarial review.
7. Recheck provider endpoints, roots, operator evidence, and standards-transition status immediately before any later network authorization.
8. Obtain a separate exact `NON_FORECAST_REHEARSAL` network authorization before sending any provider packet.

GitHub-hosted Actions are not required for this gate and are not authorized by this document.
