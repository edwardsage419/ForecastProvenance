# Genesis Zero Cost Time Evidence Review

Date: 2026-09-11
Status: CURRENT READ ONLY ARCHITECTURE REVIEW

## Decision

The Genesis minimum time evidence profile should pursue zero recurring cash cost.

Commercial QTSP qualification is paused for the Genesis minimum profile.

The preferred candidate is:

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

This review does not authorize any provider request.

## VERIFIED FACT

The existing `FPP_TIME_EVIDENCE_V1` already separates signed wall clock deadline evidence from OpenTimestamps and Bitcoin durability evidence.

The existing Roughtime profile already defines subject bound nonce construction and the conservative upper bound:

```text
verified_receipt_upper_bound = midpoint + radius
```

The current issuance schedule leaves a large safety margin between forecast execution and the external proof deadline.

The current candidate object set contains `policy:deadline-receipt-quorum:v1`, whose own change policy requires a new policy version when quorum or qualification semantics change.

The selected zero cost design therefore uses a new `policy:deadline-receipt-quorum:v2` rather than rewriting v1.

Current public Roughtime review inputs identify three distinct operational candidates:

1. `roughtime.se`
2. `time.txryan.com`
3. `Cloudflare-Roughtime-2`

Current public information indicates distinct operators and distinct signing keys.

OpenTimestamps can create timestamp commitments through public calendars without a user paid Bitcoin transaction.

The OpenTimestamps client supports verification with a local pruned Bitcoin Core node.

The current RFC 3161 checker remains version 1.3 with report schema 1.2 and is closed absent a new concrete correctness or security defect.

## INFERENCE

A two of three frozen Roughtime pool is a better fit for the project's zero recurring cash cost constraint than requiring commercial qualified timestamp providers.

The existing seven day forecast information horizon and 24 hour external proof margin make second level Roughtime uncertainty operationally acceptable for the initial target set when every accepted receipt independently satisfies its conservative upper bound.

Using three frozen providers with a threshold of two improves availability without weakening the quorum requirement.

Keeping RFC 3161 as auxiliary evidence preserves the value of the completed checker and retained rehearsals without making commercial entitlement a Genesis blocker.

Provider key rotation must be fail closed. A changed root key cannot silently replace the key frozen in a ProviderProfile.

## UNKNOWN

No Roughtime provider is yet qualified for Genesis use.

No Roughtime request has been sent under this review.

The following still require separately authorized synthetic rehearsal evidence:

1. Exact protocol compatibility with the selected verifier implementation.
2. Exact root key observed at rehearsal time.
3. Delegation verification.
4. Response signature verification.
5. Subject bound nonce inclusion.
6. Observed midpoint and radius behavior.
7. Raw request and response retention.
8. Operational availability under the project's low request rate.
9. Final provider independence review.
10. Final usage authorization evidence sufficient for the selected low volume non abusive use.

The project also has not yet completed strong OpenTimestamps verification against owner controlled Bitcoin Core.

## RFC 3161 candidates after the architecture review

FreeTSA, DigiCert, Sectigo ordinary, Sectigo Qualified, Sigstore, and any other RFC 3161 service are outside the minimum Genesis provider requirement unless a later versioned governance decision changes the profile.

The retained RFC 3161 evidence remains historical and may be used as auxiliary corroboration.

Sectigo and Signicat commercial qualification work is paused.

No paid contract or subscription should be entered for the current Genesis minimum profile.

## Current candidate provider pool

### roughtime.se

Role: Roughtime candidate group.

Read only evidence indicates a public Stratum 1 Roughtime service with an independently published Ed25519 public key and direct UTC tracking infrastructure.

Status:

`NOT READY FOR NON_FORECAST_REHEARSAL`

### time.txryan.com

Role: Roughtime candidate group.

Read only evidence indicates a public Roughtime service open to individual users, with an independently published Ed25519 public key and support for current IETF Roughtime drafts.

Status:

`NOT READY FOR NON_FORECAST_REHEARSAL`

### Cloudflare-Roughtime-2

Role: Roughtime candidate group.

Read only evidence indicates a public anycast Roughtime service with an independently published Ed25519 root key.

The service is still described as beta and the root key is subject to change.

Status:

`NOT READY FOR NON_FORECAST_REHEARSAL`

## Rehearsal gate

Before any request is sent, a separate review must freeze:

```text
provider_id
operator_identity
endpoint
protocol_version
root_public_key
subject_nonce_construction
verifier_implementation
raw_evidence_retention
upper_bound_rule
usage_authorization_basis
independence_classification
```

Only after those fields are reviewed may a separate task authorize an exact synthetic `NON_FORECAST_REHEARSAL` request.

A successful rehearsal does not authorize Genesis and does not create prospective evidence.

## Safety state

The review preserves:

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```

The Genesis Ed25519 private key remains outside repository, GitHub, CI, connected tools, and ChatGPT managed artifacts.
