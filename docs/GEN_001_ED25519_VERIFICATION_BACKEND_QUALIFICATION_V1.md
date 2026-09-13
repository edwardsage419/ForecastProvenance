# GEN_001 Ed25519 Verification Backend Qualification V1

Date: 2026-09-13
Status: QUALIFICATION PROCEDURE CANDIDATE
Scope: offline public-key signature verification backend only

## Safety boundary

This procedure does not sign anything and accepts no private key material. It does not execute Roughtime or RFC 3161 provider requests and does not perform production provider qualification. The Genesis Ed25519 private key remains outside repository, GitHub, CI, ChatGPT, Codex, logs, prompts, and third-party services.

## Qualified source boundary

The verifier source tree is closed to exactly:

```text
go.mod
main.go
main_test.go
```

Symlinks, directories, extra files, and special files are rejected. During the build phase the only additional allowed file is the generated verifier binary.

The build profile records the SHA256 of each source file and a canonical source-tree SHA256 over the ordered source manifest.

## Toolchain boundary

Final qualification requires an exact Go 1.27.x patch release. The selected `go` executable must resolve to the same file as `GOROOT/bin/go`. The qualification record binds:

```text
go_version
goos
goarch
go_toolchain_tree_sha256
go_toolchain_distribution_source
go_toolchain_distribution_sha256
go_toolchain_carrier_sha256
```

The environment is fail closed with `GOTOOLCHAIN=local`, `CGO_ENABLED=0`, `GOENV=off`, `GOWORK=off`, `GOPROXY=off`, and `GOSUMDB=off`. The module graph must contain only `forecastprovenance/ed25519_verify`.

## Required verification tests

The exact required PASS set is:

```text
TestDuplicateFieldRejected
TestJSONTagsMatchProtocol
TestMutationsReject
TestNoncanonicalAndWrongLengthBase64Rejected
TestNullAndTrailingDataRejected
TestOversizeRequestRejected
TestRFC8032Vectors
TestRunOutputIsClosedResult
TestStrictRequestRoundTrip
TestUnknownFieldRejected
```

The parser consumes `go test -count=1 -json ./...`, rejects missing, failed, or skipped required tests, and requires a package PASS event.

RFC 8032 public verification vectors are sufficient for this backend because no signing or secret-key operation exists in the qualified interface.

## Reproducible build rule

The frozen build command is:

```text
go build -trimpath -buildvcs=false -ldflags=-buildid= -o fpp-ed25519-verify .
```

Two builds are performed with distinct Go build caches. The two binaries must be byte-for-byte identical. The final build profile records the resulting binary SHA256 and `reproducible_build=true`.

## Build profile identity

The build profile schema is `ed25519_verifier_build_profile.schema.json` version 1.0. Its `profile_sha256` is SHA256 over the canonical JSON object with `profile_sha256` omitted.

A development binary hash does not become the final verifier identity. Final acceptance requires a build profile produced under the accepted Go 1.27.x toolchain and retained with the qualification evidence.

## Current boundary

Publishing this procedure does not change any provider qualification state. Until the exact current repository regression and final Go 1.27.x build qualification both pass:

```text
PRODUCTION_QUALIFICATION_SIGNATURE_BACKEND = PUBLISHED_CANDIDATE_NOT_FINAL_QUALIFIED
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
network_authorized = false
```
