# GEN_001 Roughtime Preflight Recheck

Date: 2026-09-13
Status: READ-ONLY PREFLIGHT BLOCKER

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

Current TimeNL operator material publishes:

```text
provider = TimeNL-Roughtime
endpoint = rough.time.nl:2002/udp
public key = v2CievhgKsxzlWPwIkYFUXeA51Akhkv5uhJCj1/kbiY=
version = 1
service status = pilot
```

The currently published project profile still records:

```text
operator_declared_protocol = draft-ietf-ntp-roughtime-12 pilot
wire_profile = IETF_D12_D13_UNTYPED_SHARED_WIRE_NODE_FIRST
require_type = false
require_srv = true
```

This is no longer sufficiently supported by current operator documentation.

The current IETF Roughtime draft defines version 1 requests as containing VER, NONC, and TYPE, with TYPE mandatory and SRV recommended. The testing wire version remains 0x8000000c while the document is in the RFC Editor queue.

Therefore the current TimeNL profile has a public-evidence drift on protocol/version semantics and TYPE behavior.

## Decision

```text
roughtime.se preflight = PASS ON PUBLIC EVIDENCE
time.txryan.com preflight = PASS ON PUBLIC EVIDENCE
TimeNL-Roughtime preflight = BLOCKED
provider set preflight = BLOCKED
network_authorized = false
```

No network rehearsal is authorized.

The blocker must not be bypassed by silently sending the existing untyped draft-12/13 request or by silently changing the request to a typed version-1 request.

The existing pool revision explicitly requires reviewed profile versioning before qualification when offered version, TYPE behavior, Merkle semantics, SRV handling, root key, endpoint, or transport changes.

## Required next work

1. Reconcile TimeNL's current operator-published version-1 profile with the project verifier and request builder.
2. Decide whether TimeNL remains in the frozen provider pool.
3. If retained, introduce a reviewed, versioned TimeNL provider profile rather than mutating the prior frozen profile in place.
4. Add or update offline fixtures for the selected TYPE and Merkle semantics.
5. Re-run the affected strict-wrapper tests, qualification, repository tests, and schema checks.
6. Repeat the read-only provider preflight after publication.
7. Obtain a new explicit, bounded NON_FORECAST_REHEARSAL authorization before sending any provider packet.

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
