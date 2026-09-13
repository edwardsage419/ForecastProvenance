# GEN_001 Ed25519 Verification Backend Candidate

Date: 2026-09-13
Status: IMPLEMENTATION CANDIDATE, NOT PRODUCTION QUALIFIED
Scope: public-key signature verification only

## Purpose

`RoughtimeQualificationDecision` requires an injected Ed25519 signature verifier. This candidate supplies that verification path without adding a Python cryptography runtime dependency and without implementing Ed25519 arithmetic in project code.

The cryptographic primitive is Go standard-library `crypto/ed25519.Verify`.

No signing API exists in this backend. No private key is accepted by its wire format, Python adapter, tests, or build path.

## Components

1. `scripts/genesis/ed25519_verify/` contains a small offline verifier using only the Go standard library.
2. `src/forecast_trust_core/_ed25519_verifier.py` provides a pinned-binary adapter implementing the signature-verifier callable expected by the production qualification semantic validator.
3. `tests/test_ed25519_verifier.py` builds the verifier with networking disabled when a Go toolchain is available and exercises the pinned adapter.

## Request boundary

The verifier accepts exactly one JSON object on standard input with these fields:

```text
schema_version = 1.0
object_type = Ed25519VerificationRequest
public_key_base64
message_base64
signature_base64
```

The parser rejects duplicate fields, unknown fields, JSON null, non-string values, trailing JSON, oversized input, noncanonical Base64, wrong public-key length, wrong signature length, and messages larger than 1 MiB.

Cryptographically invalid signatures are represented as a successful verifier invocation with `valid = false`. Malformed verification requests fail closed with a nonzero process exit.

The output object has exactly:

```text
schema_version
object_type = Ed25519VerificationResult
valid
```

## Pinned binary boundary

The Python adapter requires the expected verifier binary SHA256 from outside the signed decision. It rejects a symlink or non-file path, recomputes the binary SHA256 before invocation, and recomputes it after invocation.

The qualification decision still receives its expected authority ID and exact public key from outside the decision object. This backend does not permit a QualificationDecision to select either its trust root or verifier binary identity.

## Offline test basis

The Go verifier tests use the public key, message, and signature components of RFC 8032 Section 7.1 Ed25519 verification vectors. Secret-key material is unnecessary and is not retained in the project tests.

Tests also mutate the message, public key, and signature and require rejection, and exercise strict JSON and Base64 parser failures.

## Build boundary

The source module has no third-party Go dependency.

Development and later qualification builds use fail-closed environment controls including:

```text
GOTOOLCHAIN=local
CGO_ENABLED=0
GOENV=off
GOWORK=off
GOPROXY=off
GOSUMDB=off
```

`-trimpath` is required for the verifier build.

A development build hash is not a frozen production verifier identity. The final accepted backend still requires an exact qualified build under the project's frozen Go toolchain and a content-addressed build record.

## Remaining qualification gate

Publishing this candidate does not make `PRODUCTION_QUALIFICATION_EXECUTION` ready.

Remaining work includes:

1. complete repository regression at the exact branch HEAD;
2. JSON Schema validation for the production qualification object model;
3. adversarial review of the object model plus this backend;
4. a final content-addressed Ed25519 verifier build profile under the accepted toolchain;
5. actual owner public-key identity when the Genesis governance instance is prepared.

The Genesis Ed25519 private key remains entirely outside this implementation boundary.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
network_authorized = false
```

This candidate does not authorize live provider traffic, production qualification execution, Genesis, Ledger creation, or prospective forecasting.
