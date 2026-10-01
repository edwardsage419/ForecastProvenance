# GEN_001 Roughtime qualification harness hardening

Date: 2026-09-12
Status: OFFLINE HARDENING PUBLISHED CANDIDATE; POST-VENDORING GO 1.27 QUALIFICATION OPEN

## Safety boundary

This change is offline qualification tooling only.

```text
classification = NON_FORECAST_REHEARSAL
prospective_eligible = false
network_authorized = false
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```

It does not authorize a Roughtime provider packet, an RFC 3161 POST, prospective forecasting, Forecast Ledger creation, Forecast Ledger Genesis, or Genesis.

## Verified defects closed by this hardening

The published vendored qualification candidate had three control-plane gaps found during final offline adversarial review.

1. The source hashes used explicit wrapper and vendored-source allowlists, while the qualification command did not reject additional filesystem entries. An extra Go or assembler compile input in a dirty checkout could therefore affect `go test` or `go build` without entering `wrapper_source_tree_sha256` or the dependency lock.
2. The readiness gate required a deterministic binary build, while the qualification command executed only one binary build and therefore did not prove byte-for-byte reproducibility.
3. Qualification JSON output used a check-then-write path. A dangling symlink or concurrent path substitution could bypass the preliminary existence check.

The review also found that Go execution was selected by `PATH` and inherited a broad process environment. Variables outside the previously frozen subset could influence target or experiment selection without being represented in the build profile.

## Hardening controls

The accepted qualification CLI now performs the following additional checks before artifacts can be emitted.

### Exact wrapper tree allowlist

The wrapper directory must contain exactly the frozen wrapper files, the retained upstream license and provenance manifest, the three expected directories, and the twelve pinned `protocol` source files.

Any extra file, extra directory, symlink, or special filesystem entry fails closed. The generated verifier binary is allowed only after the controlled build step.

This closes unbound build-input and path-substitution cases inside the verifier source tree.

### Go executable pinning and environment reduction

The selected `go` executable is resolved once from `PATH`. Qualification obtains `GOROOT` from that executable and requires the selected executable to be the same filesystem object as `GOROOT/bin/go`.

The subprocess environment is reduced to a small explicit set. Go module networking remains disabled. `GOTOOLCHAIN=local`, `CGO_ENABLED=0`, `GOENV=off`, `GOWORK=off`, `GO111MODULE=on`, `GOPROXY=off`, and `GOSUMDB=off` remain mandatory. `GOFLAGS` is fixed to `-mod=readonly -buildvcs=false`. Unbound target, compiler, experiment, and inherited Go flag variables are not carried into qualification. `HOME`, `GOCACHE`, `GOMODCACHE`, and `TMPDIR` are isolated under a private qualification scratch directory.

### Reproducible verifier build

The frozen verifier build is executed twice with the same source and toolchain and with separate Go build caches.

Both outputs must be regular files. Their SHA256 values and full bytes must match exactly. A mismatch fails qualification and removes the failed generated binary.

The frozen build arguments remain:

```text
go build -trimpath -buildvcs=false -ldflags=-buildid= -o fpp-roughtime-strict .
```

### Exclusive qualification artifact creation

Dependency lock, fixture report, and build profile files are created with exclusive-create filesystem semantics. Existing files and dangling symlinks are refused rather than followed or replaced.

The strict verifier's own output handling remains independently protected by exclusive creation.

## Focused validation performed for this hardening

The hardening layer was exercised locally with synthetic filesystem and fake-Go fixtures.

```text
focused hardening tests = 9 PASS
Python compile = PASS
```

The focused tests cover extra compile-input rejection, symlink rejection, controlled generated-binary allowance, removal of unbound Go environment inputs, Go executable to GOROOT binding, nondeterministic-build rejection, successful reproducible-build retention, dangling-symlink output rejection, and existing-output preservation.

These focused tests are implementation checks only. They are not the formal post-vendoring Go 1.27 qualification and they are not the complete repository test suite.

## Remaining gate

The required next execution remains:

1. Obtain a complete checkout at the formal `design/gen-001` HEAD containing this hardening commit.
2. Use the exact approved Go 1.27.x toolchain and recompute its actual GOROOT tree hash.
3. Run the vendored offline qualification command and require all fifteen Go fixture tests to pass.
4. Retain the new dependency lock 1.1, fixture report 1.1, binary SHA256, and build profile 1.2.
5. Run the complete repository test suite.
6. Continue the final offline adversarial review against the retained artifacts.

No CI PASS claim is made. No network rehearsal is authorized by this hardening.
