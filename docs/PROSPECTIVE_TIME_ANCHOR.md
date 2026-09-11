# Prospective Time Anchor

Status: Selected for Genesis acceptance testing
Scheme: OTS_BTC_BATCH_V1

## Design choice

Use OpenTimestamps with Bitcoin attestation as the primary external existence proof.

The project will not rely on local wall clock time, filesystem metadata, operator controlled Git author or committer time, UUID time components, or a digital signature without an independent time source as the sole proof of prospective existence.

## Batch object

For each issuance cycle, create one deterministic canonical issuance manifest containing the ordered list of issued forecast identities and substantive SHA256 hashes plus the active Genesis protocol identity.

The manifest itself is content addressed and timestamped with OpenTimestamps.

The initial OpenTimestamps proof may be pending. It must be retained and later upgraded to include the Bitcoin attestation.

## Time semantics

The Bitcoin attestation is conservative evidence that the anchored content existed by the accepted block attestation boundary. It is not treated as exact second level issuance time.

Genesis targets must have horizons and timing rules compatible with this precision limitation.

## Verification states

1. NOT_SUBMITTED.
2. PENDING_BITCOIN.
3. VERIFIED_BITCOIN.
4. FAILED_ANCHOR.
5. LATE_OR_INELIGIBLE.

## Genesis acceptance requirements

Before first prospective issuance, testing must demonstrate deterministic manifest creation, successful timestamp submission, proof retention, later proof upgrade, independent verification, mutation detection, missing proof handling, and failure state handling.

Genesis must also define maximum acceptable latency and whether a late proof excludes a forecast from confirmatory prospective cohorts.

## External references

https://opentimestamps.org/
https://github.com/opentimestamps/opentimestamps-client
