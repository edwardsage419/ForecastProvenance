# Canonicalization and Identifiers

Version: 0.1 candidate
Status: FTC_001 REVIEW CANDIDATE

## 1. Purpose

This contract defines the exact bytes used for scientific object identity and dependency binding.

The canonical bytes are the scientific truth for hashing. Human formatted JSON is a presentation form only.

## 2. Canonicalization scheme

Scheme ID: FPP_JCS_1

FPP_JCS_1 uses RFC 8785 JSON Canonicalization Scheme over a restricted project data model.

Requirements:

1. UTF 8 only.
2. No byte order mark.
3. No duplicate object keys.
4. Object members are serialized according to RFC 8785 ordering.
5. No insignificant whitespace is emitted.
6. Strings are preserved exactly and are not Unicode normalized during hashing.
7. JSON null is prohibited in consequential scientific objects. Absence and explicit unknown states use schema defined fields.
8. JSON floating point numbers are prohibited in consequential scientific objects.
9. Integers are permitted only where the schema defines bounded integer semantics and the value is within the interoperable integer range.
10. Scientific decimal quantities use canonical decimal strings.
11. Timestamps use canonical UTC strings defined below.
12. Arrays preserve declared order. A schema must state when array order is scientifically meaningful.
13. Map like collections whose order is not meaningful must be represented as objects keyed by stable identifiers or sorted before object construction according to the schema.
14. Unknown extension fields are rejected by default for normative objects.

## 3. Canonical decimal string

Type name: decimal_string_v1

Accepted grammar:

```text
0
-?[1-9][0-9]*(\.[0-9]+)?
0\.[0-9]+
-0\.[0-9]+
```

Additional rules:

1. No leading plus sign.
2. No exponent notation.
3. No leading zeroes except the single integer zero.
4. No trailing zeroes after the decimal point.
5. A decimal point must be followed by at least one digit.
6. Negative zero is prohibited.
7. Values that mathematically equal zero canonicalize to `"0"`.
8. Schema specific precision limits apply before canonicalization.
9. Probability strings must lie in the closed interval from `"0"` through `"1"`.
10. Quantization policy belongs to the field schema and must never be inferred during verification.

Examples:

```text
"0"
"1"
"0.5"
"0.125"
"-12.75"
```

Invalid examples include `"01"`, `"+1"`, `"1.0"`, `"1e-3"`, and `"-0"`.

## 4. Canonical timestamps

Type name: utc_timestamp_v1

Format:

```text
YYYY-MM-DDTHH:MM:SSZ
```

Rules:

1. UTC only.
2. Literal `Z` suffix.
3. Whole second precision only in version 1 normative objects.
4. No timezone offsets.
5. No fractional seconds.
6. Calendar validity must be checked.
7. Claimed local wall clock timestamps have no external trust status merely because they satisfy this format.

If future protocols require subsecond precision, they require a new timestamp type version.

## 5. Hash envelope

Each normative object contains:

```json
{
  "object_type": "IssuedForecast",
  "schema_version": "1.0",
  "object_id": "forecast:...",
  "content_sha256": "..."
}
```

The `content_sha256` field is excluded from the hashed projection.

Every schema defines a function named `substantive_projection_v1`. The projection includes every field capable of changing scientific interpretation, dependency binding, lifecycle meaning, trust classification, or scoring consequence.

Metadata excluded from the substantive projection must be explicitly listed in the schema. Unlisted fields cannot be silently excluded.

Hash construction:

```text
canonical_bytes = FPP_JCS_1(substantive_projection_v1(object))
content_sha256 = lowercase_hex(SHA256(canonical_bytes))
```

## 6. Object identifiers

Object IDs are stable semantic handles. Hashes provide content identity.

Format:

```text
<type-prefix>:<slug>:v<version>
```

Examples:

```text
target:us-cpi-yoy:v1
resolution:us-cpi-yoy:v1
method:transparent-baseline:v1
```

Immutable event objects that can have multiple occurrences use a content derived suffix:

```text
attempt:<method-slug>:<12-hex-hash>
forecast:<target-slug>:<12-hex-hash>
anchor:<scheme-slug>:<12-hex-hash>
correction:<forecast-short-id>:<12-hex-hash>
```

The suffix is derived from the full `content_sha256`. Short IDs are presentation conveniences. Validation always compares full hashes.

## 7. Dependency references

A consequential dependency reference contains both semantic identity and expected full content hash:

```json
{
  "object_id": "target:us-cpi-yoy:v1",
  "content_sha256": "64-lowercase-hex"
}
```

A matching semantic ID with a different hash is a dependency mismatch and fails closed.

## 8. Hash recursion rule

Self hashes are excluded from their own projection.

Downstream objects include upstream full hashes.

No object is permitted to establish the trustworthiness of an upstream object merely because all downstream hashes were recomputed consistently.

Trust status is determined against an externally supplied trusted manifest.

## 9. Schema evolution

A field addition is substantive when it changes validation, interpretation, resolution, scoring, time eligibility, or trust.

Substantive schema changes require a new schema version.

A verifier must never guess how to upgrade an old object to a new schema.

## 10. Reference

RFC 8785, JSON Canonicalization Scheme:
https://www.rfc-editor.org/rfc/rfc8785.html
