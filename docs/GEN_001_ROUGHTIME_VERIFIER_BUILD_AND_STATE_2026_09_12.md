# GEN_001 Roughtime strict verifier and control state freeze

Date: 2026-09-12
Status: VENDORED OFFLINE QUALIFICATION CANDIDATE PUBLISHED; POST-VENDORING GO 1.27 EXECUTION OPEN

## Safety boundary

This work is offline tooling only. It does not authorize a Roughtime provider packet, an RFC 3161 POST, prospective forecasting, Forecast Ledger creation, Forecast Ledger Genesis, or Genesis.

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

The strict project wrapper is under `scripts/genesis/roughtime_strict_verifier/`. Its CLI exposes only `build-request` and `verify-response`. It contains no DNS, UDP, TCP, HTTP, provider-query, or socket execution path.

The wrapper now vendors only the pinned upstream `protocol` package compile inputs used by the verifier. The 12 vendored Go source files are copied byte-for-byte from the pinned commit and bound by upstream Git blob SHA1 plus local SHA256. The upstream BSD license is retained.

The accepted execution path no longer depends on Go proxy, sumdb, an upstream module Zip, or any external Go module. The previous module-Zip qualification model is superseded. `src/forecast_trust_core/_roughtime_qualification.py` remains only as legacy implementation material; the accepted qualification CLI uses `_roughtime_qualification_vendored.py`.

## Go toolchain

Go 1.27.1 toolchain access was resolved through the connected GitHub `actions/go-versions` release artifact.

Observed provenance for the toolchain used in the successful pre-vendoring execution:

```text
go_version = go1.27.1
goos = linux
goarch = amd64
carrier artifact SHA256 =
e0eb1b4d80fd2c2aeb67889ed0e9e518eb7d6a214aca6abe5347e20cfd8cb2b9
inner go-1.27.1-linux-x64.tar.gz SHA256 =
6f00fbc5b337fbf00581b7ced382fecdc4fa9493aef971277652a25f7aa14c6e
observed GOROOT tree SHA256 =
eba4c6c6f86a5d2555025a9a2d3e5bb4cb1c147831f731e323c2a49ad21cd560
```

These values are retained execution evidence. The post-vendoring run must recompute and bind the actual GOROOT tree used for that run.

The frozen build command remains:

```text
go build -trimpath -buildvcs=false -ldflags=-buildid= -o fpp-roughtime-strict .
```

## Vendored qualification harness

`scripts/genesis/qualify_roughtime_verifier.py` is now a single-stage offline qualification command.

It forces:

```text
GOTOOLCHAIN=local
CGO_ENABLED=0
GOENV=off
GOWORK=off
GO111MODULE=on
GOFLAGS=-mod=readonly
GOPROXY=off
GOSUMDB=off
GOPRIVATE=
GONOPROXY=
GONOSUMDB=
GOINSECURE=
```

The command requires `go list -m all` to contain only:

```text
forecastprovenance/roughtime_strict_verifier
```

Any external Go module fails closed.

Qualification then verifies the checked-in source provenance manifest, recomputes every vendored source Git blob SHA1 and SHA256, computes the upstream source-tree hash and wrapper source-tree hash, computes the actual GOROOT tree hash, runs the full Go test matrix, builds the frozen binary, repeats source and toolchain integrity checks, and emits the dependency lock, fixture report, and verifier build profile.

No provider endpoint is contacted by this command.

## Frozen hash rules

Dependency lock schema version 1.1 binds:

```text
schema_version
object_type
upstream_repository
upstream_tag
upstream_commit
upstream_tag_object_sha
upstream_tag_signature_verified
source_scope
files
upstream_source_tree_sha256
lock_sha256
```

Each file entry contains:

```text
path
git_blob_sha1
sha256
```

`upstream_source_tree_sha256` is SHA256 of canonical JSON over the sorted file entries.

The wrapper source-tree hash uses the explicit allowlist:

```text
adapter_go127.go
adapter_go127_test.go
adapter_pre127.go
core.go
core_test.go
go.mod
main.go
```

Generated binaries and unrelated files do not enter the wrapper source identity.

Fixture report schema version 1.1 binds:

```text
network_used = false
vendored_source_verified = true
external_modules_used = false
exact Go version
GOOS
GOARCH
GOROOT tree hash
CGO_ENABLED = false
exact test command
wrapper source-tree hash
upstream source-tree hash
required PASS matrix
report self hash
```

## Verifier build profile

Build profile schema version 1.2 binds:

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
go_toolchain_distribution_source
go_toolchain_distribution_sha256
go_toolchain_carrier_sha256
cgo_enabled
dependency_lock_sha256
wrapper_source_tree_sha256
upstream_source_tree_sha256
verifier_source_bundle_sha256
build_command
binary_sha256
fixture_report_sha256
profile_sha256
```

`verifier_source_bundle_sha256` is SHA256 of the raw 32-byte upstream source-tree digest followed by the raw 32-byte wrapper source-tree digest.

Every retained receipt in a checked rehearsal package must use:

```text
verifier_source_sha256 = verifier_source_bundle_sha256
verifier_binary_sha256 = binary_sha256
```

The pre-vendoring binary SHA256:

```text
1adbcf4076371742c86d10df14bfdabc55ab610b9d8da44d02dc6350e77cdee7
```

is historical execution evidence only. It must not populate the post-vendoring build profile because the source identity changed when the imports and module structure changed.

## Executed checks

Before vendoring, Go 1.27.1 executed the complete strict-wrapper matrix successfully:

```text
Go 1.27 strict-wrapper tests = 15 PASS
including Go 1.27 cryptographic fixtures = PASS
offline binary build = PASS
```

The fixture matrix includes typed hash-first, typed node-first, untyped draft 12, wrong root, mutated response, wrong nonce, and packet/profile rejection with deterministic synthetic keys.

For the vendored qualification model itself, isolated local validation completed:

```text
vendored qualification focused Python tests = 11 PASS
three revised qualification JSON Schemas = VALID
Python compile = PASS
```

A complete post-vendoring Go 1.27 qualification run has not yet been recorded against a full checkout of the current formal HEAD. The complete repository test suite is also still open. No CI PASS claim is made.

## Persistent retry state and control binding

Retry state remains `CONTROL_STATE_NON_TIME_EVIDENCE`, keyed by SHA256 of the frozen provider root public key. Local time is rate-limiting state only and is never trusted deadline evidence.

Plan, authorization, report, build profile, retry state before, and retry state after remain strictly content-bound. Receipt source and binary hashes must match the retained build profile exactly.

## Remaining gate before any network rehearsal

1. Obtain a full checkout at the current formal `design/gen-001` HEAD.
2. Use an exact Go 1.27.x toolchain and record its distribution and GOROOT tree hashes.
3. Run the single-stage vendored offline qualification command.
4. Require the main-module-only check, vendored Git blob verification, all 15 Go tests, deterministic binary build, dependency lock, fixture report, and build profile cross-binding to pass.
5. Run the complete repository test suite.
6. Perform final offline adversarial review.
7. Recheck provider endpoints, roots, operator evidence, and standards-transition status immediately before any later network authorization.
8. Obtain a separate exact `NON_FORECAST_REHEARSAL` network authorization before sending any provider packet.

GitHub-hosted Actions are not required for this gate and are not authorized by this document.
