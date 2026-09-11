# GEN_001 Roughtime Rehearsal Entry Review

Date: 2026-09-11
Status: READ ONLY ENTRY REVIEW CLOSED

## Decision

The three provider candidates selected by `policy:deadline-receipt-quorum:v2` have sufficient public evidence for non forecast rehearsal entry.

Current entry status:

```text
roughtime.se = READY FOR NON_FORECAST_REHEARSAL
time.txryan.com = READY FOR NON_FORECAST_REHEARSAL
Cloudflare-Roughtime-2 = READY FOR NON_FORECAST_REHEARSAL
```

This status does not authorize any network request.

A separate task must authorize the exact synthetic subject, exact provider set, exact verifier commit, and exact request protocol versions before any UDP packet is sent.

## Common frozen rehearsal verifier candidate

Repository:

`github.com/tannerryan/roughtime`

Exact commit:

`56b346a16cd7e8317bb0d24f1ec15549cf93a4c9`

License:

`BSD-2-Clause`

The pinned source states support for Google Roughtime and IETF drafts 01 through 19. Its verifier checks negotiated versions, signed version lists, server binding, delegation validity, signatures, nonces, timestamps, and Merkle proofs.

The pinned ecosystem file contains all three selected providers with the same public keys reviewed below.

The final project verifier profile remains subject to separately retained build metadata and offline fixture tests. Rehearsal entry readiness does not freeze a production ProviderProfile.

## Common subject binding and retention rules

The project rehearsal request must use the existing subject bound nonce construction defined by the Genesis time evidence design.

The exact subject must be synthetic and permanently classified:

`NON_FORECAST_REHEARSAL`

For every provider attempt retain at minimum:

```text
provider_id
provider_endpoint
requested_protocol_version
root_public_key
subject_sha256
client_random
derived_nonce
raw_request_bytes
raw_response_bytes_or_failure
request_sha256
response_sha256_or_none
midpoint_or_none
radius_or_none
verified_receipt_upper_bound_or_none
delegation_verification
signature_verification
nonce_verification
verifier_repository
verifier_commit
toolchain_version
attempt_timestamp_metadata
failure_code_or_success
prospective_eligible=false
```

The qualifying deadline rule remains:

`verified_receipt_upper_bound = midpoint + radius`

A provider receipt qualifies only when the cryptographic verification succeeds and that upper bound is at or before the frozen deadline.

## Provider entry profile A: roughtime.se

```text
provider_id = roughtime.se
operator_identity = Marcus Dansarie service, hosted by STUPI AB
endpoint = roughtime.se:2002/udp
protocol_version = draft-ietf-ntp-roughtime-15
root_public_key = S3AzfZJ5CjSdkJ21ZJGbxqdYP/SoE8fXKY0+aicsehI=
usage_authorization_basis = operator site explicitly permits time synchronization, timestamping, testing, and software development
time_source_disclosure = stratum 1, directly connected to atomic clocks tracking UTC
verifier = tannerryan/roughtime at 56b346a16cd7e8317bb0d24f1ec15549cf93a4c9
upper_bound_rule = midpoint + radius
key_rotation_rule = any root key change requires a new reviewed ProviderProfile and accepted manifest change before qualification
independence_classification = independent operational trust authority from Tanner Ryan and Cloudflare
status = READY FOR NON_FORECAST_REHEARSAL
```

Authoritative public evidence states the service implements draft 15, is hosted by STUPI AB, is directly connected to atomic clocks tracking UTC, publishes the listed long term public key, and permits use for time synchronization, timestamping, testing, and Roughtime development.

The service provides no availability guarantee. Outage therefore remains an operational omission risk and never lowers quorum.

## Provider entry profile B: time.txryan.com

```text
provider_id = time.txryan.com
operator_identity = Tanner Ryan
endpoint = time.txryan.com:2002/udp
protocol_version = draft-ietf-ntp-roughtime-19
root_public_key = iBVjxg/1j7y1+kQUTBYdTabxCppesU/07D4PMDJk2WA=
usage_authorization_basis = operator site explicitly says individual users may use the public server without asking
time_source_disclosure = stratum 2, synchronized to stratum 1 upstreams backed by GNSS receivers and national metrology institutes including NIST and NRC
verifier = tannerryan/roughtime at 56b346a16cd7e8317bb0d24f1ec15549cf93a4c9
upper_bound_rule = midpoint + radius
key_rotation_rule = any root key change requires a new reviewed ProviderProfile and accepted manifest change before qualification
independence_classification = independent operational trust authority from roughtime.se and Cloudflare
status = READY FOR NON_FORECAST_REHEARSAL
```

The operator site states that the endpoint supports IETF Roughtime drafts 00 through 19 and publishes the listed Ed25519 root public key. The project freezes draft 19 for the rehearsal rather than allowing runtime selection discretion.

The operator explicitly permits individual use without prior approval and requests contact only for high volume infrastructure deployment. The project rehearsal is a low volume synthetic readiness action.

No formal uptime or accuracy guarantee exists. Outage never lowers quorum.

## Provider entry profile C: Cloudflare-Roughtime-2

```text
provider_id = Cloudflare-Roughtime-2
operator_identity = Cloudflare, Inc.
endpoint = roughtime.cloudflare.com:2003/udp
protocol_version = draft-ietf-ntp-roughtime-08
root_public_key = 0GD7c3yP8xEc4Zl2zeuN2SlLvDVVocjsPSL8/Rl/7zg=
usage_authorization_basis = Cloudflare publicly offers the Roughtime service for free use and publishes client instructions
time_source_disclosure = Cloudflare anycast service; operator architecture states responses use each serving machine system clock and the service clock is tied to Cloudflare certificate validity operations
verifier = tannerryan/roughtime at 56b346a16cd7e8317bb0d24f1ec15549cf93a4c9
upper_bound_rule = midpoint + radius
key_rotation_rule = root key changes fail closed and require a new reviewed ProviderProfile and accepted manifest change before qualification
independence_classification = independent operational trust authority from roughtime.se and Tanner Ryan
status = READY FOR NON_FORECAST_REHEARSAL
```

Cloudflare's current documentation publishes the endpoint and root public key and labels the service beta. Cloudflare's maintained ecosystem description identifies Cloudflare-Roughtime-2 as supporting IETF Roughtime draft 08.

Cloudflare explicitly warns that the root key may change. The project therefore must compare the rehearsal key against this frozen value before request construction and again during evidence review. A changed key aborts the attempt before qualification.

## Independence review

The three selected groups are controlled by distinct operational authorities:

1. Marcus Dansarie and the roughtime.se service hosted by STUPI AB.
2. Tanner Ryan and time.txryan.com.
3. Cloudflare, Inc. and its anycast Roughtime service.

No reviewed evidence shows shared signing key control or common timestamp issuance authority among these three groups.

Shared Internet infrastructure or overlap among upstream UTC references does not by itself merge provider groups under the current policy. Any later evidence of shared signing authority, shared root secret control, or common operational issuance control is blocking.

## Remaining uncertainties

Entry readiness does not establish live compatibility, reachability, observed radius, delegation validity, or response correctness.

Those properties require the separately authorized synthetic rehearsal.

Cloudflare remains beta and may rotate its root key. roughtime.se and time.txryan.com provide no contractual availability guarantee.

The Tanner Ryan verifier candidate requires a current Go 1.27 toolchain according to its pinned README. Final project acceptance must retain the exact toolchain and build metadata used for rehearsal verification.

## Rehearsal authorization boundary

The next networked task, if separately authorized, must name all of the following before execution:

```text
synthetic_subject_bytes
synthetic_subject_sha256
provider_set = exactly the three profiles above
provider_protocol_versions = draft15, draft19, draft08 respectively
verifier_repository = github.com/tannerryan/roughtime
verifier_commit = 56b346a16cd7e8317bb0d24f1ec15549cf93a4c9
maximum_attempts_per_provider
timeout_policy
request_order
raw_evidence_output_directory
prospective_eligible=false
classification=NON_FORECAST_REHEARSAL
```

A separate authorization is required because `READY FOR NON_FORECAST_REHEARSAL` is an entry state only.

## Safety state

This review preserves:

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
```

No Roughtime request was sent during this review.

No RFC 3161 request was sent.

No Genesis Ed25519 private key was accessed, read, copied, referenced, uploaded, or processed.
