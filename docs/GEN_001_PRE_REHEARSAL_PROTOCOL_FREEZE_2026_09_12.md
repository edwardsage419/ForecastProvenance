# GEN_001 Pre-Rehearsal Protocol Freeze Review

Date: 2026-09-12
Status: OFFLINE DEFECT REVIEW CLOSED, NETWORK GATE STILL CLOSED

## Control precedence

This dated review is the controlling addendum for the Roughtime nonce, version-offer, wire/TYPE/Merkle acceptance, retry/backoff, evidence-validation, verifier-build binding, retry-state binding, provider-attempt, OTS failure-recovery, and provider/verifier freeze-order rules below. Until deliberate consolidation, it supersedes only conflicting Roughtime clauses in `GENESIS_TIME_EVIDENCE.md` and the conflicting provider/verifier versus external-evidence ordering in `GENESIS_MANIFEST_PROCEDURE.md`. Unrelated historical requirements remain in force.

## Conclusion

No defect found in this review requires abandoning the zero-recurring-cash-cost architecture.

The following defects were identified before network execution and are addressed by candidate v0.5 / quorum v3 design.

## Closed design defects

1. **64-byte nonce mismatch.** Historical FPP_ROUGHTIME_V1 SHA-512 output is incompatible with the current IETF 32-byte nonce profile. Replaced by `FPP_ROUGHTIME_NONCE_V2`.
2. **False draft precision.** Drafts 12-19 share a testing wire version. Provider metadata now separates operator-declared protocol from verifiable wire profile.
3. **High-level automatic negotiation.** Qualifying tooling must use explicit low-level request/verify semantics and may not broaden versions automatically. Every provider offer is a singleton frozen wire version.
4. **Packet fallback ambiguity.** Current profile is `STANDARD_1024_BODY` only.
5. **Transport ambiguity.** Current profile is UDP only. Transport fallback inside a deadline event is prohibited.
6. **Operator retry discretion.** Attempt limit, timeout, exact-byte retry, exponential backoff, persistent per-root state, and first-valid-response stopping rule are frozen.
7. **Selective provider querying.** Every event evaluates all three providers in frozen order. A provider is attempted only when persistent per-root retry state permits it; active backoff is recorded as non-qualifying and quorum remains 2-of-3.
8. **Causal-chain coupling.** Each provider receives an independent subject-bound nonce. Deadline receipts do not use causal chaining.
9. **Schema-only acceptance.** JSON Schema is descriptive only; an executable semantic validator recomputes all cross-field trust decisions. Semantic validation alone is insufficient for cryptographic qualification: raw request/response/nonce/profile evidence must replay through the pinned low-level verifier.
10. **Raw failure evidence gaps.** Every attempt retains exact request bytes; any received response bytes are retained even when invalid.
11. **Unbound deadline.** The frozen deadline is part of the offline plan before any request.
12. **Unbound authorization.** A separate authorization record binds one exact plan SHA256. Reports and receipts cannot self-authorize.
13. **Zero/invalid radius.** A qualifying receipt requires a strictly positive authenticated radius and recomputed midpoint-plus-radius upper bound.
14. **Boolean confusion.** Quorum booleans require actual JSON/Python booleans; numeric `1/0` are rejected by executable semantics.
15. **Opaque endpoints.** Provider identity uses structured host, port, transport and root-key fields.
16. **Genesis dependency inversion.** Provider/verifier profiles are frozen before bootstrap governance is externally evidenced.
17. **OTS evidence overwrite.** Stamp/upgrade/verify actions use append-only event directories and successful proof publication uses same-filesystem atomic replacement so a failed upgrade cannot corrupt the last canonical proof.
18. **Provider interoperability risk.** Cloudflare-Roughtime-2 was removed from the current pool after a concrete unresolved IETF interoperability finding; TimeNL-Roughtime is the current replacement candidate.
19. **Shared typed-wire Merkle ambiguity.** Drafts 14-15 and 16-19 use opposite Merkle child ordering under the same version/TYPE identifiers. The pinned verifier intentionally verifies both conventions; the frozen typed profile records that exact acceptance set rather than pretending the wire can distinguish the draft generation.
20. **Unbound verifier build.** Every rehearsal plan now binds a content-addressed verifier build profile covering exact source/toolchain/wrapper/build artifacts.
21. **Unbound persistent retry state.** Every rehearsal plan/authorization binds the pre-attempt retry-state snapshot; every report retains the post-attempt snapshot hash.
22. **Opaque verification execution.** Every qualifying receipt requires a verification transcript hash and the report requires an execution transcript hash.
23. **Verified-but-nonqualifying retry ambiguity.** A properly signed response that fails only project qualification, such as positive-radius policy or the frozen deadline, terminates retries and resets protocol backoff even though it does not count toward quorum. The report distinguishes this from a cryptographic/transport failure.
24. **Standards transition.** RFC publication or wire/profile changes trigger a new read-only review and versioned profile change. Automatic migration is prohibited.

## Offline test evidence in this review

Focused Roughtime semantic tests:

```text
9 tests passed
```

Offline plan/authorization/schema tests:

```text
3 tests passed
```

OTS failure-recovery regression test:

```text
1 test passed
```

Schema definition check:

```text
4 Draft 2020-12 schemas valid
```

OTS shell syntax and failure recovery:

```text
bash -n PASS
atomic failed-upgrade preservation test PASS
```

These focused checks are not a substitute for the final complete repository test suite.

## Remaining blocker

The pinned verifier still requires a reproducible Go 1.27.x build and a project-controlled strict low-level wrapper with offline fixtures. The current execution environment could not resolve external download hosts, so that build was not falsely reported as complete.

Official Go releases show Go 1.27.x exists; the remaining work is an owner/development-environment reproducibility task.

## Network boundary

No Roughtime or RFC3161 request was sent.

A network rehearsal remains prohibited until the strict wrapper, persistent retry-state handling, exact plan, exact separate authorization, and immediate provider/standards preflight all pass.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```
