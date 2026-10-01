# GEN-001 Roughtime execution orchestrator design and review

Date: 2026-09-13

## Scope and safety boundary

This change adds the missing repository-owned UDP execution layer for a future,
separately authorized `NON_FORECAST_REHEARSAL`. It does not authorize a network
operation, alter a frozen provider profile, execute Genesis, or qualify a
provider for production. The CLI refuses to construct the real transport unless
the operator supplies `--execute-network`; the orchestrator then independently
requires a valid exact-plan authorization with `network_authorized=true`.

No real Roughtime packet was sent during development or qualification. No
RFC3161 request was sent. Every execution test uses an injected transport. The
focused suite replaces both DNS lookup and socket construction with guards that
fail immediately if accidentally reached.

The pre-existing plan
`99ae0b4ce62d106f9ca0cc049f3766a3a39dd28c3d788d134d7f8923c6e278cd`
was historical input only. It was not executed, no authorization record was
created for it, and it is `NOT EXECUTED / SUPERSEDED FOR FUTURE NETWORK
EXECUTION`.

## Architecture

The qualified strict verifier builds and validates the exact 1036-byte request.
The orchestrator validates controls, sequences all three frozen providers,
persists evidence, invokes an injected UDP transport, manages retry state,
invokes the strict verifier, and materializes the transcript and report. The
strict verifier alone performs wire/profile, TYPE, SRV, root, delegation,
signature, nonce, Merkle, midpoint, and authenticated-radius validation.
The orchestrator accepts a successful verifier result only when its JSON object
has the exact frozen field set and exact bound values. Missing fields, wrong
types, extra fields, and alternate or duplicate semantic representations fail
closed as `VERIFIER_ERROR`.

`RealUDPTransport` resolves a provider once, deterministically selects one
numeric UDP destination, connects one socket to that IP and frozen port, and
accepts a response only when its observed source equals that destination. There
is no provider, hostname, address, port, transport, wire-version, TYPE, SRV, or
packet-profile fallback.

The transport and verifier are injected protocols. Tests use `FakeTransport`
and `FakeVerifier`; no test supplies the CLI network acknowledgement.

## Send-safety gate and authorization binding

Before event creation or transport preparation, the orchestrator validates the
plan, exact authorization, build profile, retry-state snapshot, cross-object
hashes, frozen provider order and fields, classification boundary, subject,
deadline, and qualified verifier binary hash. Any failed gate produces no send.

The authorization SHA-256 identifies a fixed event directory and a fixed
consumption marker. Both use exclusive creation. An existing event or consumed
marker refuses execution, so one exact authorization cannot be reused within an
execution root.

## Evidence ordering

Before each possible send the orchestrator:

1. Persists the exact plan, authorization, build profile, and retry-state-before.
2. Persists the authorization consumption marker.
3. Builds once and persists the request bytes, digest, and builder transcript.
4. Resolves exactly one destination and persists `SEND_RESERVED` metadata.
5. Persists a conservative failure/backoff state transition.
6. Rechecks the frozen deadline immediately before the injected send call.

Any datagram, including empty, malformed, or unexpected-source data, is written
with its digest and source metadata before verification. A timeout does not
create fake response bytes. Files are exclusively created and fsynced; a partial
failed file is removed and never treated as evidence. Retry-state-after, the
content-addressed execution transcript, and the sealed report are new files.
The report must pass the existing semantic validator and the cross-artifact
`validate_report_control_binding` check before publication. That final check
binds the exact plan, authorization, qualified build profile, retry state before,
and retry state after. A mismatch aborts before `report.json` is created.

## Retry semantics

The validated plan supplies attempts, timeout, and backoff. A request is built
once per provider and reused byte-for-byte, including its nonce, on retry. All
three providers are evaluated in frozen order even after quorum is reached.
`BACKOFF_ACTIVE` creates no network attempt.

Transport, attribution, malformed, and cryptographic failures retain the
conservative failure state and may retry under the frozen two-attempt rule. A
properly signed response is terminal and resets its root state. A signed response
that fails radius or deadline qualification remains
`VERIFIED_NONQUALIFYING_RESPONSE` and is not a transport or cryptographic error.

Receipt schema 1.2 adds `radius_nanoseconds` and permits up to nine fractional
UTC digits. Its upper bound is calculated exactly in integer nanoseconds.
Schema 1.1 receipts retain their original whole-second semantics.

Report schema 1.2 is the minimal explicit failure-vocabulary upgrade for this
execution layer. Report 1.1 retains the historical failure-code set. Report 1.2
adds only `RESPONSE_SOURCE_MISMATCH`, for independently auditable transport
attribution failure, and `TYPE_MISMATCH`, for a wire/profile type mismatch.
`SRV_MISMATCH` is not a new code: an SRV-to-frozen-root mismatch uses the
existing `ROOT_KEY_MISMATCH`. Both semantic and JSON Schema validators reject
new codes in 1.1 and unknown codes in every supported version.

## Crash and duplicate execution behavior

The authorization marker is durable before a possible send. `SEND_RESERVED` and
the pessimistic state transition are durable before the transport call. A crash
before send therefore cannot send. A crash at or after the send boundary leaves
an honest record that the packet may or may not have left. Restart with the same
authorization is denied, preventing an unaudited duplicate send.

A crash after the OS receives a datagram but before userspace persists it can
lose those bytes; it cannot cause authorization reuse or duplicate send. The
reservation and conservative state remain. Recovery requires a new plan and a
new independently approved exact authorization, never replay of the old event.

Fault injection covers authorization consumption, request persistence, send
reservation, immediate post-send, post-receive/pre-persistence, post-response
persistence, verifier execution, verification persistence, and pre-publication
of retry-state-after.

## Review, tests, and known limitations

The offline matrix covers authorization and profile mutations, evidence-write
failures, timeout, socket error, source mismatch, empty/malformed response,
cryptographic and wire failures, terminal verified-nonqualifying responses,
retry byte identity, all quorum counts, provider order, active backoff,
authorization reuse, crash boundaries, final control binding, strict verifier
output shape, versioned failure codes, and receipt 1.1 compatibility. It also
exercises the real transport logic with a local socket double only.

Final offline validation after all hardening changes:

- focused execution tests: 76 passed;
- pinned strict Go verifier tests: passed for the main package, with no tests in
  the pinned protocol package;
- combined Roughtime-related regression suite: 120 passed, 7 skipped, 9
  subtests passed;
- JSON Schema validation group: 97 passed, 3 subtests passed;
- complete repository suite: 257 passed, 8 skipped, 188 subtests passed;
- Python compile check: passed.

Backward compatibility is explicit: historical report and receipt 1.1 shapes
remain accepted with their original vocabularies and whole-second timestamp
grammar, while 1.1 rejects the new execution failure codes. The adversarial
review found all three prior blockers closed: final cross-artifact binding is
mandatory, verifier success output is exact-key and exact-type checked, and new
failure codes have a report 1.2 boundary. Reinspection also found no regression
in persist-before-send ordering, retry-byte identity, authorization consumption,
deadline recheck, response attribution, exclusive evidence creation, partial
write handling, crash replay prevention, no-fallback behavior, verifier
enforcement, retry-state consistency, or report/raw-evidence binding.

This is a single-host, local-filesystem consumption mechanism. It does not claim
distributed coordination across multiple evidence roots or hosts. DNS is bound
to one selected address for the event; there is deliberately no address fallback.
The narrow receive-to-persistence crash window is reported conservatively rather
than hidden. A future real rehearsal must first repeat provider preflight,
generate a new plan, obtain independent exact-plan authorization, and use a
reviewed published build containing this orchestrator.

Safety state remains: Genesis not started; Forecast Ledger Genesis and Forecast
Ledger not created; prospective forecast count zero; production-qualified
provider count zero; `PRODUCTION_QUALIFIED=NO`; repository development-time
`network_authorized=false`.
