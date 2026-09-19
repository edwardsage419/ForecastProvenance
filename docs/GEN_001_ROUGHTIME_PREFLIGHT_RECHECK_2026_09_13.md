# GEN_001 Roughtime Preflight Recheck

Date: 2026-09-13
Status: READ-ONLY PREFLIGHT RECONCILED; NETWORK GATE STILL CLOSED

## Scope

This review rechecks current public provider and protocol evidence before any Roughtime network authorization.

No Roughtime provider packet was sent.
No RFC 3161 request was sent.

## Current formal repository state reviewed

```text
formal branch = design/gen-001
formal HEAD before this review = 3cd151e9b9ce506267a5764bc3159dd06a900929
formal tree = d30879c099ba5d3d20444a20be1d18b01cec6be2
network_authorized = false
```

The published offline qualification and repository tests remain valid for that source tree.

## Provider recheck

### roughtime.se

Current operator material continues to publish:

```text
endpoint = roughtime.se:2002/udp
operator-declared protocol = draft-ietf-ntp-roughtime-15
root public key = S3AzfZJ5CjSdkJ21ZJGbxqdYP/SoE8fXKY0+aicsehI=
```

This remains consistent with the existing typed shared-wire acceptance profile.

### time.txryan.com

Current operator material continues to publish:

```text
endpoint = time.txryan.com:2002
root public key = iBVjxg/1j7y1+kQUTBYdTabxCppesU/07D4PMDJk2WA=
protocol family = IETF Roughtime
supported drafts = 00 through 19
```

This remains compatible with the existing typed shared-wire acceptance profile, subject to the existing fail-closed rehearsal controls.

### TimeNL-Roughtime

Current TimeNL operator material publishes the following server-list entry:

```text
provider = TimeNL-Roughtime
endpoint = rough.time.nl:2002/udp
public key = v2CievhgKsxzlWPwIkYFUXeA51Akhkv5uhJCj1/kbiY=
version = 1
service status = pilot
```

The operator's dedicated TimeNL service page also states, specifically for
this Roughtime server:

```text
implemented document = draft-ietf-ntp-roughtime-12
operator-identified implementation = github.com/tannerryan/roughtime v1.14.0
```

The generic server-list field `version = 1` and the more specific
implementation statement are not conflicting version identifiers.
`draft-ietf-ntp-roughtime-12` itself names the protocol it specifies as
Roughtime version 1 and assigns `0x8000000c` for testing that draft.

The currently published project profile still records:

```text
operator_declared_protocol = draft-ietf-ntp-roughtime-12 pilot
wire_profile = IETF_D12_D13_UNTYPED_SHARED_WIRE_NODE_FIRST
require_type = false
require_srv = true
```

This remains supported by the operator's current dedicated documentation and
the exact referenced IETF draft:

```text
wire version = 0x8000000c
request TYPE = absent
response TYPE = absent
request SRV = H(0xff || long-term Ed25519 public key), SHA-512 truncated to 32 bytes
Merkle leaf = full request packet including ROUGHTIM header
Merkle bit-0 step = H(0x01 || sibling node || running hash)
```

The strict wrapper implements that acceptance boundary without fallback. It
offers only `0x8000000c`, omits TYPE for TimeNL, includes and validates the
root-derived SRV value, rejects a response whose TYPE presence differs from
the frozen profile, binds the full request packet into the Merkle leaf, and
uses only the draft-12/13 node-first Merkle convention for an untyped reply.

The current upstream repository no longer enumerates the operator-cited
`v1.14.0` tag through its public Git tag list. That limits independent source
reconstruction of the named historical deployment version, but it does not
create a wire-profile ambiguity here: the operator separately identifies the
implemented standards revision, and that authoritative draft remains
available. This limitation must still be rechecked before final provider
freeze and keeps this pilot outside production qualification.

The latest IETF Roughtime draft defines a typed version-1 request and a
hash-first Merkle convention. That is standards-transition evidence, not
provider-specific evidence that TimeNL changed away from its explicitly
published draft-12 deployment. It therefore cannot silently replace the
current TimeNL profile.

The earlier inference that `version = 1` alone proved profile drift was
incorrect. No current public-evidence drift is established for TimeNL's
protocol, TYPE, SRV, Merkle, root-key, endpoint, or transport semantics.

## Decision

```text
roughtime.se preflight = PASS ON PUBLIC EVIDENCE
time.txryan.com preflight = PASS ON PUBLIC EVIDENCE
TimeNL-Roughtime preflight = PASS ON PUBLIC EVIDENCE
provider set preflight = PASS ON PUBLIC EVIDENCE
network_authorized = false
```

No network rehearsal is authorized.

The existing TimeNL profile is retained unchanged. This is not a new profile,
does not alias a new profile to the old one, and does not rewrite the
historical meaning of the draft-12/13 profile. A typed request, a different
wire version, either typed Merkle convention, a different SRV rule, root key,
endpoint, or transport remains outside the profile and must fail closed.

The existing pool revision explicitly requires reviewed profile versioning before qualification when offered version, TYPE behavior, Merkle semantics, SRV handling, root key, endpoint, or transport changes.

The retained synthetic cryptographic fixture
`TestGo127UntypedDraft12Fixture` exercises the selected untyped draft-12
request and authenticated response path. It is not represented as a live
TimeNL response. The fixture uses a single-leaf Merkle tree, so PATH length is
zero and the fixture does not independently demonstrate node-first child
ordering. A multi-leaf untyped draft-12 node-first fixture is required before
the Merkle-ordering production qualification criterion can be satisfied. This
is an offline coverage requirement and does not require a new live request or
change the retained provider profile.

## Retention versus removal

### Retain the reconciled existing profile

This preserves the exact operator-published endpoint, root, UDP transport,
draft-12 testing wire version, untyped message form, root-derived SRV, and
node-first Merkle semantics. It preserves three independent operational
authorities and the frozen 2-of-3 quorum, tolerates one provider being
nonqualifying, introduces no protocol fallback, and adds no recurring cash
cost. The pilot status and shared Tanner Ryan software-family correlation
remain recorded operational risks.

### Remove TimeNL from the current rehearsal pool

Removing TimeNL would leave only two frozen providers. The current executable
plan, schemas, authorization, report, retry-state root set, provider-attempt
rule, and governance all require exactly three providers and a 2-of-3 quorum.
A two-provider pool would therefore require a separately reviewed governance
and schema revision. A 2-of-2 replacement would also lose one-provider outage
tolerance and would not satisfy TimeNL's recommendation to use at least two
other Roughtime servers.

Because the more specific public evidence supports the existing profile,
removal is less safe operationally and creates substantially more complexity
without improving protocol determinism or provenance.

## Required next work

1. Retain TimeNL in the frozen provider pool under the unchanged
   `IETF_D12_D13_UNTYPED_SHARED_WIRE_NODE_FIRST` profile.
2. Repeat the read-only provider preflight immediately before any future
   rehearsal and again before final ProviderProfile freeze.
3. If operator evidence changes or a response no longer matches the exact
   frozen profile, stop. Do not use protocol, packet, or transport fallback.
4. Introduce a separately reviewed versioned profile and new offline fixture
   evidence before accepting any future semantic change.
5. Obtain a new explicit, bounded NON_FORECAST_REHEARSAL authorization before
   sending any provider packet.

## Evidence reviewed

```text
operator general service page = https://time.nl/index_en.html
operator dedicated service page = https://nts.time.nl/
operator source page = https://github.com/SIDN/TimeNL/blob/master/index_en.html
draft-12 specification = https://datatracker.ietf.org/doc/html/draft-ietf-ntp-roughtime-12
current draft-19 transition reference = https://datatracker.ietf.org/doc/html/draft-ietf-ntp-roughtime-19
evidence review date = 2026-09-13
```

## Safety state

```text
Genesis = NOT STARTED
Forecast Ledger Genesis = NOT CREATED
Forecast Ledger = NOT CREATED
prospective forecast count = 0
production-qualified provider count = 0
PRODUCTION_QUALIFIED = NO
network_authorized = false
prospective_eligible = false
```

No Genesis Ed25519 private key was accessed, read, copied, referenced, uploaded, or processed.
