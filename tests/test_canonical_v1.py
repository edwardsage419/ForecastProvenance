import pytest

from forecast_trust_core.canonical import (
    CanonicalizationError,
    canonical_json,
    content_hash,
    decode_utf8_json,
    parse_json_strict,
    seal_object,
)


@pytest.mark.parametrize(
    "raw",
    [
        b"\xef\xbb\xbf{}",
        b"\xff\xfe{\x00}\x00",
        b"\xfe\xff\x00{\x00}",
        b"\xff\xfe\x00\x00{\x00\x00\x00}\x00\x00\x00",
        b"\x00\x00\xfe\xff\x00\x00\x00{\x00\x00\x00}",
    ],
)
def test_decode_utf8_json_rejects_unicode_boms(raw):
    with pytest.raises(CanonicalizationError):
        decode_utf8_json(raw)


def test_decode_utf8_json_rejects_malformed_utf8():
    with pytest.raises(CanonicalizationError):
        decode_utf8_json(b'{"value":"\xff"}')


def test_parse_json_strict_accepts_bytes_and_rejects_duplicate_keys():
    assert parse_json_strict(b'{"answer":42}') == {"answer": 42}
    with pytest.raises(CanonicalizationError):
        parse_json_strict(b'{"answer":1,"answer":2}')


def test_parse_json_strict_preserves_bytearray_compatibility():
    assert parse_json_strict(bytearray(b'{"answer":42}')) == {"answer": 42}


@pytest.mark.parametrize(
    "source",
    [
        '"\\ud800"',
        '"\\udfff"',
        '"\ud800"',
    ],
)
def test_parse_json_strict_rejects_surrogate_code_points(source):
    with pytest.raises(CanonicalizationError):
        parse_json_strict(source)


def test_parse_json_strict_accepts_a_valid_escaped_surrogate_pair():
    assert parse_json_strict('"\\ud800\\udc00"') == "\U00010000"


@pytest.mark.parametrize(
    "source",
    [
        "-0",
        "01",
        "+1",
        "1.",
        ".1",
        "1e",
        "NaN",
        "Infinity",
        "-Infinity",
        "1.0",
        "1e0",
        str(2**53),
        str(-(2**53)),
    ],
)
def test_parse_json_strict_rejects_noncanonical_or_unsupported_numbers(source):
    with pytest.raises(CanonicalizationError):
        parse_json_strict(source)


@pytest.mark.parametrize("number", [-(2**53 - 1), 0, 2**53 - 1])
def test_parse_json_strict_accepts_interoperable_integer_boundaries(number):
    assert parse_json_strict(str(number)) == number


def test_parse_json_strict_maps_excessive_nesting_to_canonicalization_error():
    source = "[" * 2000 + "0" + "]" * 2000
    with pytest.raises(CanonicalizationError):
        parse_json_strict(source)


def test_canonical_json_preserves_golden_bytes_and_hash():
    value = {"b": 1, "a": "x"}
    assert canonical_json(value) == b'{"a":"x","b":1}'
    assert content_hash(value) == "cdab067e9f3beb32d1252cfd63e492592fecbf591b0d08cadb24bb17f3864246"


def test_sealed_object_preserves_golden_identity_and_bytes():
    obj = seal_object(
        {"schema_version": "1.0", "name": "alpha"},
        object_type="Example",
        stable_context="v1",
    )
    assert obj["object_id"] == "example:v1:a8e8cbadab32"
    assert obj["payload_sha256"] == "a8e8cbadab3250e424c97be3e9e7c0b0be1119d30b27a7b52c40d938c06da6fd"
    assert obj["content_sha256"] == "50b522d430051e805f9ffaa531d062a0aec6f588f333b4bffc65a21af91fc0a5"
    assert canonical_json(obj) == (
        b'{"content_sha256":"50b522d430051e805f9ffaa531d062a0aec6f588f333b4bffc65a21af91fc0a5",'
        b'"name":"alpha","object_id":"example:v1:a8e8cbadab32","object_type":"Example",'
        b'"payload_sha256":"a8e8cbadab3250e424c97be3e9e7c0b0be1119d30b27a7b52c40d938c06da6fd",'
        b'"schema_version":"1.0"}'
    )
