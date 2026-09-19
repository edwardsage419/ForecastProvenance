# Prospective Time Evidence

Status: GEN_001 REVIEW CANDIDATE
Primary scheme family: FPP_TIME_EVIDENCE_V1
Durability layer: OTS_BTC_BUNDLE_V1

## Design choice

Prospective status uses two distinct external time mechanisms.

1. Signed wall-clock receipt quorum establishes that the exact subject existed before a frozen deadline.
2. OpenTimestamps with Bitcoin attestation provides durable append-only anchoring of the accepted evidence bundle.

Bitcoin block time is not used as the precise forecast deadline clock.

## Prohibited sole clocks

The project does not use any of these as the sole proof of prospective existence:

1. Local wall clock.
2. Filesystem metadata.
3. Operator controlled Git author or committer time.
4. UUID time components.
5. A local digital signature without an independent time source.
6. A GitHub created_at field without a portable signed receipt over the exact subject and time.
7. Bitcoin block header time interpreted as exact issuance time.

## Wall-clock quorum

DEADLINE_RECEIPT_QUORUM_V3 requires at least two qualifying signed Roughtime receipts from the exactly three-profile frozen pool. The receipts must represent distinct operational provider groups. RFC 3161 remains optional auxiliary evidence and does not reduce or replace the Roughtime threshold.

Each receipt must bind the exact subject SHA256 and supply a defensible conservative upper time bound at or before the frozen deadline.

The current Roughtime receipt semantics and RFC 3161 auxiliary boundary are specified in `GENESIS_TIME_EVIDENCE.md`.

## OpenTimestamps layer

For each externally receipted subject, create an ExternalTimeEvidenceBundle binding the subject, deadline, receipt references, provider profiles, and quorum policy.

Timestamp the canonical evidence bundle with OpenTimestamps.

The initial OTS proof may be pending. It must be retained and later upgraded until a Bitcoin attestation verifies.

The project retains the proof bytes and strong verification report.

## Strong verification

Genesis acceptance requires at least one non-forecast rehearsal verified using a locally controlled Bitcoin Core node. Pruned mode is allowed.

Routine remote explorer checks can support operations but do not substitute for the strong verification record.

## Durability completion

After an OTS proof becomes complete, create a DurabilityVerificationRecord containing the proof reference, Bitcoin block identity, header reference, and strong verification report.

That exact record must receive wall-clock deadline receipt quorum before the target outcome information barrier for initial Genesis confirmatory eligibility.

A later OTS completion remains part of the historical evidence record but is not promoted silently into the initial confirmatory cohort.

## States

Suggested derived states:

1. SUBJECT_SEALED.
2. DEADLINE_QUORUM_PENDING.
3. DEADLINE_QUORUM_VERIFIED.
4. OTS_PENDING_BITCOIN.
5. OTS_BITCOIN_VERIFIED.
6. DURABILITY_COMPLETION_PENDING.
7. PROSPECTIVE_ELIGIBLE.
8. LATE_OR_INELIGIBLE.
9. TRUST_UNKNOWN.

These are derived validation states and do not mutate the immutable issued forecast.

## Provider profiles

The current Roughtime candidates are `roughtime.se`, `time.txryan.com`, and `TimeNL-Roughtime`. Historical RFC 3161 candidates and Cloudflare Roughtime remain non-prospective review evidence only.

A candidate provider cannot count toward quorum until its exact trust roots, token or protocol semantics, accuracy rule, verifier version, and successful non-forecast rehearsal are frozen.

## Rehearsal status

One separately authorized Roughtime `NON_FORECAST_REHEARSAL` completed on
2026-09-13 with three qualifying provider results. Its retained evidence review
passed. The evidence remains permanently non-prospective and supplies inputs to
a later independent qualification review only.

Roughtime production qualification criteria are not yet frozen, qualification
execution is not ready, no production ProviderProfile exists, and no provider
is production qualified. Historical RFC 3161 rehearsal results retain their
recorded classifications and remain auxiliary only.

## Detailed contract

The normative readiness candidate is `GENESIS_TIME_EVIDENCE.md`.
