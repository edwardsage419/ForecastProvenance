import hashlib

import pytest

from forecast_trust_core.authority_primitives_v1 import (
    GENERIC_FAILURE_CODES,
    HASH_FAILURE,
    NO_AUTHORITATIVE_RESULT,
    PARSE_FAILURE,
    REFERENCE_FAILURE,
    SCHEMA_FAILURE,
    AuthorityPrimitiveError,
    ExactRef,
    ProjectionProfile,
    RoleBinding,
    exact_ref_equal,
    extract_identity,
    projection_sha256,
    resolve_exact,
    verify_role_binding,
    verify_sealed_identity,
)
from forecast_trust_core.canonical import canonical_json, seal_object


SHA_A = "a" * 64
SHA_B = "b" * 64


def ref_value(**updates):
    value = {"object_id": "example:v1:abc123", "content_sha256": SHA_A}
    value.update(updates)
    return value


@pytest.mark.parametrize(
    "value",
    [
        {"content_sha256": SHA_A},
        {"object_id": "example:v1:abc123"},
        {**ref_value(), "extra": True},
        ref_value(object_id="bad id"),
        ref_value(object_id=7),
        ref_value(content_sha256="A" * 64),
        ref_value(content_sha256="a" * 63),
    ],
)
def test_exact_ref_rejects_missing_extra_or_malformed_fields(value):
    with pytest.raises(AuthorityPrimitiveError) as raised:
        ExactRef.from_mapping(value)
    assert raised.value.code == REFERENCE_FAILURE


def test_identity_extraction_and_exact_comparison_require_both_components():
    obj = {"object_id": "example:v1:abc123", "content_sha256": SHA_A, "payload": 1}
    ref = extract_identity(obj)
    assert ref == ExactRef("example:v1:abc123", SHA_A)
    assert exact_ref_equal(ref, ref_value())
    assert not exact_ref_equal(ref, ref_value(content_sha256=SHA_B))


def sealed_example(*, object_type="Example", **payload_updates):
    payload = {"schema_version": "1.0", "name": "alpha", **payload_updates}
    return seal_object(payload, object_type=object_type, stable_context="v1")


def test_verify_sealed_identity_rejects_hash_and_reference_mismatches():
    obj = sealed_example()
    expected = extract_identity(obj)
    assert verify_sealed_identity(obj, expected) == expected

    changed = dict(obj)
    changed["name"] = "substituted"
    with pytest.raises(AuthorityPrimitiveError) as bad_hash:
        verify_sealed_identity(changed, expected)
    assert bad_hash.value.code == HASH_FAILURE

    wrong_ref = ExactRef(expected.object_id, SHA_B)
    with pytest.raises(AuthorityPrimitiveError) as bad_ref:
        verify_sealed_identity(obj, wrong_ref)
    assert bad_ref.value.code == REFERENCE_FAILURE


def test_verify_sealed_identity_maps_malformed_identity_types_to_stable_code():
    malformed = {**sealed_example(), "object_id": 7}
    with pytest.raises(AuthorityPrimitiveError) as raised:
        verify_sealed_identity(malformed)
    assert raised.value.code == REFERENCE_FAILURE


class RecordingResolver:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def resolve_exact(self, ref):
        self.calls.append(ref)
        return self.result

    def enumerate(self):
        raise AssertionError("exact resolution must never enumerate")


def test_resolve_exact_uses_one_exact_lookup_without_enumeration_or_fallback():
    obj = sealed_example()
    ref = extract_identity(obj)
    resolver = RecordingResolver(canonical_json(obj))
    assert resolve_exact(ref, resolver) == obj
    assert resolver.calls == [ref]


@pytest.mark.parametrize(
    ("result", "code"),
    [
        (None, NO_AUTHORITATIVE_RESULT),
        ("not bytes", REFERENCE_FAILURE),
        (b"not json", PARSE_FAILURE),
    ],
)
def test_resolve_exact_rejects_absent_nonbyte_and_unparseable_results(result, code):
    with pytest.raises(AuthorityPrimitiveError) as raised:
        resolve_exact(ExactRef("example:v1:abc123", SHA_A), RecordingResolver(result))
    assert raised.value.code == code


def test_resolve_exact_rejects_wrong_resolved_identity_without_fallback():
    requested = ExactRef("example:v1:abc123", SHA_A)
    resolver = RecordingResolver(canonical_json(sealed_example(name="other")))
    with pytest.raises(AuthorityPrimitiveError) as raised:
        resolve_exact(requested, resolver)
    assert raised.value.code == REFERENCE_FAILURE
    assert resolver.calls == [requested]


def test_resolve_exact_maps_excessive_json_nesting_to_parse_failure():
    nested = b"[" * 2000 + b"0" + b"]" * 2000
    with pytest.raises(AuthorityPrimitiveError) as raised:
        resolve_exact(ExactRef("example:v1:abc123", SHA_A), RecordingResolver(nested))
    assert raised.value.code == PARSE_FAILURE


def test_role_binding_validates_shape_and_role_type_schema_constraints():
    schema_ref = ExactRef("schema:example:v1", SHA_A)
    binding = RoleBinding.from_mapping(
        {
            "role_id": "primary_input",
            "object_type": "Example",
            "schema_version": "1.0",
            "schema_ref": schema_ref.to_dict(),
        }
    )
    obj = sealed_example()
    assert verify_role_binding(
        obj,
        binding,
        role_id="primary_input",
        schema_ref=schema_ref,
    ) == extract_identity(obj)

    for kwargs in (
        {"role_id": "other", "schema_ref": schema_ref},
        {"role_id": "primary_input", "schema_ref": ExactRef("schema:other:v1", SHA_A)},
    ):
        with pytest.raises(AuthorityPrimitiveError):
            verify_role_binding(obj, binding, **kwargs)

    with pytest.raises(AuthorityPrimitiveError) as wrong_type:
        verify_role_binding(
            sealed_example(object_type="Other"),
            binding,
            role_id="primary_input",
            schema_ref=schema_ref,
        )
    assert wrong_type.value.code == SCHEMA_FAILURE


@pytest.mark.parametrize(
    "value",
    [
        {"role_id": "r", "object_type": "Example", "schema_version": "1.0", "extra": 1},
        {"role_id": "r", "object_type": "Example"},
        {"role_id": "bad role", "object_type": "Example", "schema_version": "1.0"},
    ],
)
def test_role_binding_rejects_unknown_missing_and_invalid_fields(value):
    with pytest.raises(AuthorityPrimitiveError) as raised:
        RoleBinding.from_mapping(value)
    assert raised.value.code == SCHEMA_FAILURE


def test_generic_failure_vocabulary_is_stable_and_complete():
    assert GENERIC_FAILURE_CODES == (
        "PARSE_FAILURE",
        "SCHEMA_FAILURE",
        "REFERENCE_FAILURE",
        "HASH_FAILURE",
        "GRAPH_FAILURE",
        "SEMANTIC_FAILURE",
        "EVIDENCE_FAILURE",
        "NO_AUTHORITATIVE_RESULT",
    )


def profile(**updates):
    values = {
        "profile_id": "example_projection_v1",
        "canonicalization_profile": "FPP_JCS_1",
        "included_fields": ("a", "b"),
    }
    values.update(updates)
    return ProjectionProfile(**values)


def test_projection_hash_is_order_independent_and_domain_separated():
    projection_profile = profile()
    left = projection_sha256({"a": 1, "b": 2}, projection_profile)
    right = projection_sha256({"b": 2, "a": 1}, projection_profile)
    assert left == right
    undomained = hashlib.sha256(canonical_json({"a": 1, "b": 2})).hexdigest()
    assert left != undomained
    undomained_envelope = hashlib.sha256(
        canonical_json(
            {
                "profile": {
                    "canonicalization_profile": "FPP_JCS_1",
                    "included_fields": ["a", "b"],
                    "profile_id": "example_projection_v1",
                },
                "projection": {"a": 1, "b": 2},
            }
        )
    ).hexdigest()
    assert left != undomained_envelope


def test_projection_inclusion_ignores_unselected_fields_but_tracks_selected_fields():
    projection_profile = profile(included_fields=("stable",))
    baseline = projection_sha256({"stable": 1, "noise": 1}, projection_profile)
    assert projection_sha256({"stable": 1, "noise": 2}, projection_profile) == baseline
    assert projection_sha256({"stable": 2, "noise": 1}, projection_profile) != baseline


def test_projection_exclusion_ignores_excluded_fields():
    projection_profile = profile(included_fields=None, excluded_fields=("noise",))
    baseline = projection_sha256({"stable": 1, "noise": 1}, projection_profile)
    assert projection_sha256({"noise": 2, "stable": 1}, projection_profile) == baseline
    assert projection_sha256({"noise": 1, "stable": 2}, projection_profile) != baseline


def test_projection_hash_changes_with_profile_identity():
    value = {"a": 1, "b": 2}
    assert projection_sha256(value, profile()) != projection_sha256(
        value, profile(profile_id="example_projection_v2")
    )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"profile_id": "bad profile"},
        {"canonicalization_profile": "UNKNOWN"},
        {"included_fields": None, "excluded_fields": None},
        {"included_fields": ("a",), "excluded_fields": ("b",)},
        {"included_fields": ("a", "a")},
        {"included_fields": ("non-ascii-é",)},
        {"included_fields": ({},)},
    ],
)
def test_projection_profile_rejects_invalid_configuration(kwargs):
    with pytest.raises(AuthorityPrimitiveError) as raised:
        profile(**kwargs)
    assert raised.value.code == SCHEMA_FAILURE


@pytest.mark.parametrize(
    "value",
    [
        {
            "profile_id": "projection_v1",
            "canonicalization_profile": "FPP_JCS_1",
            "included_fields": ["a"],
            "unknown": True,
        },
        {
            "profile_id": "projection_v1",
            "canonicalization_profile": "FPP_JCS_1",
            "included_fields": "abc",
        },
    ],
)
def test_projection_profile_mapping_rejects_unknown_fields_and_string_lists(value):
    with pytest.raises(AuthorityPrimitiveError) as raised:
        ProjectionProfile.from_mapping(value)
    assert raised.value.code == SCHEMA_FAILURE


def test_projection_rejects_profile_fields_unknown_to_the_value():
    with pytest.raises(AuthorityPrimitiveError) as raised:
        projection_sha256({"a": 1}, profile(included_fields=("a", "missing")))
    assert raised.value.code == SCHEMA_FAILURE
