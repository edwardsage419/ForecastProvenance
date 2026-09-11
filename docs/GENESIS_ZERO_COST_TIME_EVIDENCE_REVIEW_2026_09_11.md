# Genesis Zero Cost Time Evidence Review

Date: 2026-09-11
Status: CURRENT READ ONLY ARCHITECTURE REVIEW

## Decision

The Genesis minimum time evidence profile uses a zero recurring cash cost candidate:

```text
FPP_TIME_EVIDENCE_V1
+
DEADLINE_RECEIPT_QUORUM_V2
+
2 of 3 frozen independent Roughtime provider groups
+
OpenTimestamps Bitcoin durability
+
owner Ed25519 identity
```

RFC 3161 remains optional auxiliary evidence.

Commercial QTSP qualification is paused for the Genesis minimum profile.

This review does not authorize any provider request.

## Current Roughtime rehearsal entry state

The provider entry review in `GEN_001_ROUGHTIME_REHEARSAL_ENTRY_REVIEW_2026_09_11.md` closes the public evidence gate for the selected pool.

```text
roughtime.se = READY FOR NON_FORECAST_REHEARSAL
time.txryan.com = READY FOR NON_FORECAST_REHEARSAL
Cloudflare-Roughtime-2 = READY FOR NON_FORECAST_REHEARSAL
```

The exact rehearsal protocols are draft 15, draft 19, and draft 08 respectively.

The common verifier candidate is `github.com/tannerryan/roughtime` at exact commit `56b346a16cd7e8317bb0d24f1ec15549cf93a4c9`.

Entry readiness does not authorize a network request.

## VERIFIED FACT

The existing `FPP_TIME_EVIDENCE_V1` separates signed wall clock deadline evidence from OpenTimestamps and Bitcoin durability evidence.

The Roughtime deadline upper bound remains:

`verified_receipt_upper_bound = midpoint + radius`

The selected quorum object is `policy:deadline-receipt-quorum:v2`, created as a successor rather than rewriting historical v1.

The selected public provider pool contains three distinct operational candidates:

1. `roughtime.se`
2. `time.txryan.com`
3. `Cloudflare-Roughtime-2`

Public evidence identifies distinct operators and distinct root signing keys.

The pinned Tanner Ryan verifier source supports IETF Roughtime drafts 01 through 19 and includes all three selected provider roots in its ecosystem file.

OpenTimestamps remains the durability layer.

The historical RFC 3161 checker remains version 1.3 with report schema 1.2 and is closed absent a new concrete correctness or security defect.

## INFERENCE

A two of three frozen Roughtime pool fits the project's zero recurring cash cost constraint better than requiring commercial qualified timestamp providers.

The seven day information horizon and 24 hour external proof margin make second level uncertainty operationally acceptable for the initial target set when every accepted receipt independently satisfies its conservative upper bound.

Keeping RFC 3161 as auxiliary evidence preserves the completed engineering and retained rehearsals without making commercial entitlement a Genesis blocker.

Provider key rotation must fail closed. A changed root key cannot silently replace the key frozen in a ProviderProfile.

## UNKNOWN

No selected Roughtime provider is yet rehearsal verified.

No Roughtime request has been sent.

Live rehearsal must still establish:

1. Endpoint reachability from the owner controlled environment.
2. Exact negotiated response compatibility with the frozen requested draft.
3. Delegation verification.
4. Response signature verification.
5. Subject bound nonce inclusion.
6. Observed midpoint and radius behavior.
7. Raw request and response retention.
8. Final provider independence review against observed evidence.
9. Exact build and toolchain reproducibility for the pinned verifier.

Strong OpenTimestamps verification against owner controlled Bitcoin Core also remains open.

## RFC 3161 boundary

FreeTSA, DigiCert, Sectigo ordinary, Sectigo Qualified, Signicat, and other RFC 3161 services are outside the minimum Genesis provider requirement unless a later versioned governance decision changes the profile.

Retained RFC 3161 evidence remains historical and may be used as auxiliary corroboration.

No paid contract or subscription is required for the current Genesis minimum profile.

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```

The Genesis Ed25519 private key remains outside repository, GitHub, CI, connected tools, and ChatGPT managed artifacts.
