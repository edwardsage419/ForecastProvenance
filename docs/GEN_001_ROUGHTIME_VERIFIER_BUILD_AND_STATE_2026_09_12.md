# GEN_001 Roughtime strict verifier and control state freeze

Date: 2026-09-12
Status: OFFLINE TOOLING CANDIDATE READY FOR REVIEW; GO 1.27 CRYPTOGRAPHIC BUILD OPEN

## Safety boundary

This change creates offline tooling only. It does not authorize a Roughtime packet, an RFC 3161 POST, prospective forecasting, Forecast Ledger creation, Forecast Ledger Genesis, or Genesis.

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

The strict project wrapper is under `scripts/genesis/roughtime_strict_verifier/`. Its project CLI exposes only `build-request` and `verify-response`. It contains no DNS, UDP, TCP, HTTP, provider query, or socket execution path.

The Go 1.27 adapter uses only the pinned low-level `protocol` package. Request construction uses one offered version, `0x8000000c`, a caller supplied 32 byte nonce, SRV derived from the frozen root, the frozen TYPE profile, and standard 1024 byte message body framing. The expected framed request is 1036 bytes. Legacy 1024 byte total packets fail closed.

Verification binds the retained request bytes, exact nonce, exact frozen root, SRV, TYPE profile, signatures, delegation, signed version information, timestamp, radius, and Merkle proof through the pinned low-level verifier. Typed shared-wire providers accept either authenticated draft 14/15 node-first or draft 16 through 19 hash-first Merkle convention. This does not identify an exact draft from the shared wire version.

## Go toolchain split

Go 1.23 core-only tests exercise project CLI and fail-closed input guards without compiling the cryptographic adapter. The real adapter is guarded by `//go:build go1.27`.

A Go 1.23 core test result is never verifier qualification.

Final cryptographic execution still requires an exact Go 1.27.x patch release, the pinned upstream source bytes, dependency lock material, and offline cryptographic fixtures. The frozen build command is:

```text
go build -trimpath -buildvcs=false -ldflags=-buildid= -o fpp-roughtime-strict .
```

## Verifier build profile

`roughtime_verifier_build_profile.schema.json` and the executable validator bind exactly:

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

`verifier_source_bundle_sha256` is deterministically computed as SHA256 of the raw 32 byte `upstream_source_archive_sha256` digest followed by the raw 32 byte `wrapper_source_tree_sha256` digest.

Every retained receipt that exists in a checked rehearsal package must use:

```text
verifier_source_sha256 = verifier_source_bundle_sha256
verifier_binary_sha256 = binary_sha256
```

No real build profile is claimed by this change because the exact Go 1.27 build and fixture execution remain open.

## Persistent retry state

`RoughtimeRetryState` is operational control state:

```text
classification = CONTROL_STATE_NON_TIME_EVIDENCE
prospective_eligible = false
```

State is keyed by SHA256 of the frozen root public key. Hostname changes therefore cannot bypass backoff for an unchanged trust root.

The frozen backoff schedule starts at one second, multiplies by 1.5, rounds upward to an integer millisecond, and saturates at 86400 seconds. A network failure cannot be recorded while the root is still in active backoff. A properly signed verified response resets the root state even when project policy later classifies the response as `VERIFIED_NONQUALIFYING_RESPONSE`.

The local clock controls request rate only. It is never trusted deadline evidence.

Mutable retry state is written atomically. Evidence snapshots use immutable content-addressed filenames and bind the exact pre-run and post-run states.

## Control artifact binding

The plan tool requires the actual verifier build profile JSON and retry state JSON. Both are parsed with duplicate-key rejection, semantically validated, and hashed by the program before their hashes enter the plan.

The authorization tool reads and validates the same artifacts again and requires exact equality with the plan bindings.

The final offline checker requires all six retained objects:

```text
plan
authorization
report
verifier build profile
retry state before
retry state after
```

It performs the existing rehearsal semantic validation and additionally validates all control-artifact hashes and receipt source/binary hashes.

JSON Schema remains descriptive interoperability validation. It does not replace executable semantic validation or cryptographic replay.

## Offline checks executed for this candidate

```text
Python/control tests = 18 PASS
Go 1.23 core-only strict-wrapper tests = 8 PASS
new JSON Schemas = VALID
Python compile = PASS
offline static network guard = PASS
```

Go 1.27 cryptographic fixtures are NOT RUN. No provider packet and no RFC 3161 POST were sent by these checks.

## Remaining gate before any network rehearsal

1. Acquire exact Go 1.27.x in a zero-cash owner-controlled or otherwise explicitly accepted environment.
2. Retain the exact pinned upstream source archive and compute its SHA256.
3. Freeze the dependency lock and compute its SHA256.
4. Run offline Go 1.27 fixtures for typed hash-first, typed node-first, untyped draft 12, wrong root, mutated response, wrong nonce, and wrong packet/profile rejection.
5. Build the strict verifier with the frozen command and hash the binary.
6. Produce a complete validated verifier build profile.
7. Run the complete repository test suite.
8. Perform final offline adversarial review.
9. Obtain a separate exact network rehearsal authorization before sending any packet.

GitHub-hosted Actions are not required for this gate and are not authorized by this document.
