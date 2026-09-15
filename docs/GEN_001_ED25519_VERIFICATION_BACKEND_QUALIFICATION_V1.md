# GEN_001 Ed25519 Verification Backend Qualification V1

Date: 2026-09-13
Status: FINAL QUALIFIED
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

The build profile records the exact repository commit SHA, each source file Git blob SHA1 and SHA256, and a canonical source-tree SHA256 over the ordered source manifest. Qualification rejects any source file whose current bytes do not match the blob recorded at repository HEAD.

## Toolchain boundary

Final qualification requires an exact Go 1.27.x patch release. The selected `go` executable must resolve to the same file as `GOROOT/bin/go`. The qualification record also binds:

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
go build -trimpath -buildvcs=false -ldflags=-buildid= -o fpp-ed25519-verify.exe .
```

Two builds are performed with distinct Go build caches. The two binaries must be byte-for-byte identical. The final build profile records the resulting binary SHA256 and `reproducible_build=true`.

## Build profile identity

The build profile schema is `ed25519_verifier_build_profile.schema.json` version 1.0. Its `profile_sha256` is SHA256 over the canonical JSON object with `profile_sha256` omitted.

A development binary hash does not become the final verifier identity. Final acceptance requires a build profile produced under the accepted Go 1.27.x toolchain and retained with the qualification evidence.

## Final qualification record

Final offline qualification completed on 2026-09-13 with the following frozen evidence:

```text
repository_commit_sha = 9ff58689992cf48b18a9f52e89f9e395271ade2c
go_toolchain_distribution_source = https://go.dev/dl/go1.27.1.windows-amd64.zip
go_toolchain_distribution_sha256 = a3911b5e0e1b1053f25ed0675f4c1c6aad1e2bfcf253df2b9be4caabd2edd95d
go_toolchain_carrier_sha256 = a3911b5e0e1b1053f25ed0675f4c1c6aad1e2bfcf253df2b9be4caabd2edd95d
go_version = go1.27.1
goos = windows
goarch = amd64
go_toolchain_tree_sha256 = b42ecca624e9a4041ca88c7d574f1c2c435b5388e379e94f71e8d1d0eab8bcbb
source_tree_sha256 = 7e688acfa237a2da6891387e90c897b97c381dd89b6d11cffa8cbcea27406b5d
binary_sha256 = 53d3d98e14dca206c64fb770417b701c74d295e34066ab35d8421bcf98b0053a
profile_sha256 = f2b7f746c44a8c38011484113b15227a2e92e647b5b14928c8c852e17aec24d5
cgo_enabled = false
network_used = false
external_modules_used = false
required_tests = PASS_10_OF_10
reproducible_build = PASS
adversarial_checks = PASS_20_OF_20
```

The official Go reproducible-build report recorded PASS for `go1.27.1.windows-amd64.zip`. The qualification trust record remains bound to the locally downloaded ZIP bytes and their SHA256, not to the webpage. Independent recomputation matched all source-file Git blob SHA1 values and SHA256 values, the canonical source tree, extracted GOROOT tree, retained binary, and build-profile self-hash. JSON Schema and semantic validation both passed. The post-qualification repository regression completed with compileall PASS, 290 pytest tests passed, 8 skipped, and 188 subtests passed.

## Current boundary

Final qualification changes only the public verification signature-backend state. It does not qualify a provider or authorize production qualification execution:

```text
PRODUCTION_QUALIFICATION_SIGNATURE_BACKEND = FINAL_QUALIFIED
PRODUCTION_QUALIFICATION_EXECUTION = NOT_READY
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
network_authorized = false
```
