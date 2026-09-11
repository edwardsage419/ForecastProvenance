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

DEADLINE_RECEIPT_QUORUM_V1 requires at least two qualifying signed receipts from distinct provider groups and at least one RFC 3161 receipt.

Each receipt must bind the exact subject SHA256 and supply a defensible conservative upper time bound at or before the frozen deadline.

RFC 3161 and optional Roughtime receipt semantics are specified in `GENESIS_TIME_EVIDENCE.md`.

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

Initial candidates include FreeTSA RFC 3161, DigiCert RFC 3161, and Cloudflare Roughtime.

A candidate provider cannot count toward quorum until its exact trust roots, token or protocol semantics, accuracy rule, verifier version, and successful non-forecast rehearsal are frozen.

## Rehearsal status

Owner-controlled non-forecast FreeTSA, DigiCert, and Sectigo requests reached the
providers on 2026-09-11. The sealed checker reports remain
`REHEARSAL_INCOMPLETE` and permanently `prospective_eligible=false`.

FreeTSA cryptographic, independent-certificate, trust-anchor, and CRL checks
succeed, but `tsa_policy1` semantics and a conservative accuracy bound remain
undocumented. DigiCert and Sectigo still lack independent signer, trust-anchor,
revocation, applicable policy, and accuracy evidence. No provider is production
qualified or eligible for receipt quorum.

## Detailed contract

The normative readiness candidate is `GENESIS_TIME_EVIDENCE.md`.
