# GEN_001 Roughtime Provider Pool Revision

Date: 2026-09-12
Status: READ-ONLY POOL REVISION

This document supersedes the 2026-09-11 Roughtime entry review only for current pool selection. Historical review evidence remains retained.

## Decision

Current pool:

```text
roughtime.se
time.txryan.com
TimeNL-Roughtime
```

Cloudflare-Roughtime-2 is removed from the current pool.

No network request was sent during this revision.

## Why Cloudflare was removed

A concrete unresolved interoperability report in the Cloudflare Roughtime repository shows the public `roughtime.cloudflare.com:2003` endpoint succeeding with a Google-Roughtime probe while the configured IETF-Roughtime probe fails with a missing `NONC` response error.

The project does not reinterpret that endpoint or silently change to a 64-byte Google-Roughtime nonce profile. Doing so would fragment the current 32-byte IETF evidence design and would require separate review.

Cloudflare remains useful historical/auxiliary research evidence and may be reconsidered through a future versioned governance change.

## TimeNL replacement

TimeNL publicly offers a Roughtime pilot:

```text
provider_id = TimeNL-Roughtime
operator = SIDN Labs / TimeNL
endpoint = rough.time.nl:2002/udp
root key = v2CievhgKsxzlWPwIkYFUXeA51Akhkv5uhJCj1/kbiY=
operator implementation statement = draft-ietf-ntp-roughtime-12
```

TimeNL explicitly describes the service as a pilot/experiment, warns that details such as the port may change, and recommends using at least two other Roughtime servers.

That status is compatible with a non-forecast rehearsal candidate but requires a fail-closed preflight recheck immediately before any rehearsal and again before final ProviderProfile freeze.

## Frozen wire acceptance profiles

The current provider profiles all offer only the singleton wire version `0x8000000c`.

`roughtime.se` and `time.txryan.com` require TYPE and use the profile `IETF_D14_D19_TYPED_SHARED_WIRE_ACCEPT_BOTH_MERKLE_ORDERS`. The shared TYPE wire identifiers cannot distinguish drafts 14-15 from drafts 16-19, whose Merkle child ordering differs. The pinned verifier explicitly tries both authenticated conventions for this ambiguous typed group, so the profile records that acceptance set instead of claiming false draft precision.

`TimeNL-Roughtime` omits TYPE and uses `IETF_D12_D13_UNTYPED_SHARED_WIRE_NODE_FIRST`, consistent with its public draft-12 pilot statement.

Any change to offered version, TYPE behavior, Merkle acceptance semantics, SRV handling, root key, endpoint, or transport requires reviewed profile versioning before qualification.

## Independence

The current operational authorities are:

1. roughtime.se / Marcus Dansarie, hosted by STUPI AB;
2. time.txryan.com / Tanner Ryan;
3. TimeNL / SIDN Labs.

No reviewed evidence shows shared signing-key control or common issuance authority.

TimeNL and time.txryan.com use software from the Tanner Ryan Roughtime implementation family. This is a correlated software dependency and must be recorded. Under the current project definition, shared software alone does not merge operational provider groups. A shared signing root, root-secret control, or common issuance authority would be blocking.

## Current entry state

```text
roughtime.se = PUBLIC ENTRY EVIDENCE READY
time.txryan.com = PUBLIC ENTRY EVIDENCE READY
TimeNL-Roughtime = PUBLIC ENTRY EVIDENCE READY
```

This does not mean rehearsal verified, provider qualified, or network authorized.

All three remain blocked on strict-wrapper/toolchain freeze and a separate exact rehearsal authorization.

## Safety

```text
classification of any future rehearsal = NON_FORECAST_REHEARSAL
prospective_eligible = false
network requests sent by this review = 0
```
