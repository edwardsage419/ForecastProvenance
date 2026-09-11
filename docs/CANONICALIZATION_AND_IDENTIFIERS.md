# Canonicalization and Identifiers

Version: 0.2 candidate
Status: FTC_001 REMEDIATION CANDIDATE

## Canonicalization scheme

Scheme ID: FPP_JCS_1

FPP_JCS_1 uses RFC 8785 JCS over a restricted project data model.

Requirements:

1. UTF 8 only and no byte order mark.
2. Duplicate object keys are rejected before canonicalization.
3. Arbitrary scientific text is not Unicode normalized.
4. Machine identifiers, field names, enum tokens, reason codes, and protocol tokens are ASCII only.
5. JSON null and JSON floating point numbers are prohibited in consequential normative content.
6. Scientific decimals use canonical decimal strings.
7. Normative timestamps use whole second UTC strings `YYYY-MM-DDTHH:MM:SSZ`.
8. Unknown extension fields are rejected unless the active schema explicitly defines an extension container.
9. Every array field must declare ordered semantics or a deterministic sort key.

## Decimal strings

No plus sign, exponent notation, leading zeroes, trailing fractional zeroes, or negative zero. Probability values lie from `"0"` through `"1"`.

## Two stage identity

Version 0.1 contained a circular construction for content derived event IDs. Version 0.2 removes it.

Each immutable object has a `payload_projection_v1` that excludes both `object_id` and `content_sha256`.

```text
payload_bytes = FPP_JCS_1(payload_projection_v1(object))
payload_sha256 = lowercase_hex(SHA256(payload_bytes))
object_id = derive_id(object_type, stable_context, payload_sha256)
```

The final content projection includes the derived object ID and payload hash, while excluding only `content_sha256`.

```text
content_bytes = FPP_JCS_1(content_projection_v1(object))
content_sha256 = lowercase_hex(SHA256(content_bytes))
```

This produces a non circular final content identity.

Stable versioned definition objects may use semantic IDs such as `target:us-cpi-yoy:v1`. Immutable event objects use an ASCII type prefix, stable context slug, and a suffix derived from `payload_sha256`.

Short hash suffixes are display identifiers only. Dependency validation always binds the full final `content_sha256`.

## Dependency references

Every consequential reference contains:

```text
object_id
content_sha256
```

Both must match.

## Array rules

Set like reference arrays are sorted lexicographically by `object_id`, then `content_sha256`.

Chronological event arrays are ordered by their explicit sequence field. Wall clock time is not used as a tie breaker.

Priority arrays, such as resolution source priority, preserve declared order because order is substantive.

Schemas must identify which rule applies to every array.

## Hash algorithm

Version 1 freezes SHA256. Algorithm migration requires new canonical reference, manifest, and affected object schema versions. A verifier never infers algorithm migration.

## Schema evolution

A field capable of changing interpretation, validation, resolution, scoring, time eligibility, or trust requires a schema version change.

A verifier never guesses an upgrade.

Reference: RFC 8785.
