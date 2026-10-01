from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping, Protocol, runtime_checkable

from .canonical import (
    CanonicalizationError,
    canonical_json,
    parse_json_strict,
    require_ascii_token,
    validate_ref,
    verify_sealed_object,
)


PARSE_FAILURE = "PARSE_FAILURE"
SCHEMA_FAILURE = "SCHEMA_FAILURE"
REFERENCE_FAILURE = "REFERENCE_FAILURE"
HASH_FAILURE = "HASH_FAILURE"
GRAPH_FAILURE = "GRAPH_FAILURE"
SEMANTIC_FAILURE = "SEMANTIC_FAILURE"
EVIDENCE_FAILURE = "EVIDENCE_FAILURE"
NO_AUTHORITATIVE_RESULT = "NO_AUTHORITATIVE_RESULT"

GENERIC_FAILURE_CODES = (
    PARSE_FAILURE,
    SCHEMA_FAILURE,
    REFERENCE_FAILURE,
    HASH_FAILURE,
    GRAPH_FAILURE,
    SEMANTIC_FAILURE,
    EVIDENCE_FAILURE,
    NO_AUTHORITATIVE_RESULT,
)

_GENERIC_FAILURE_CODE_SET = frozenset(GENERIC_FAILURE_CODES)
_PROJECTION_DOMAIN = b"FPP_PROJECTION_SHA256_V1\x00"
_CANONICALIZATION_PROFILE = "FPP_JCS_1"


class AuthorityPrimitiveError(ValueError):
    def __init__(self, code: str) -> None:
        if code not in _GENERIC_FAILURE_CODE_SET:
            raise ValueError("unknown authority primitive failure code")
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise AuthorityPrimitiveError(code)


@dataclass(frozen=True)
class ExactRef:
    object_id: str
    content_sha256: str

    def __post_init__(self) -> None:
        try:
            validate_ref(self.to_dict())
        except (CanonicalizationError, KeyError, TypeError, ValueError) as exc:
            raise AuthorityPrimitiveError(REFERENCE_FAILURE) from exc

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ExactRef:
        if not isinstance(value, Mapping) or set(value) != {
            "object_id",
            "content_sha256",
        }:
            _fail(REFERENCE_FAILURE)
        try:
            return cls(
                object_id=value["object_id"],
                content_sha256=value["content_sha256"],
            )
        except AuthorityPrimitiveError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise AuthorityPrimitiveError(REFERENCE_FAILURE) from exc

    def to_dict(self) -> dict[str, str]:
        return {
            "object_id": self.object_id,
            "content_sha256": self.content_sha256,
        }


@dataclass(frozen=True)
class RoleBinding:
    role_id: str
    object_type: str
    schema_version: str
    schema_ref: ExactRef | None = None

    def __post_init__(self) -> None:
        try:
            require_ascii_token(self.role_id, "role_id")
            require_ascii_token(self.object_type, "object_type")
            require_ascii_token(self.schema_version, "schema_version")
        except (CanonicalizationError, TypeError) as exc:
            raise AuthorityPrimitiveError(SCHEMA_FAILURE) from exc
        if self.schema_ref is not None and not isinstance(self.schema_ref, ExactRef):
            _fail(SCHEMA_FAILURE)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> RoleBinding:
        if not isinstance(value, Mapping):
            _fail(SCHEMA_FAILURE)
        required = {"role_id", "object_type", "schema_version"}
        if not required.issubset(value) or not set(value).issubset(
            required | {"schema_ref"}
        ):
            _fail(SCHEMA_FAILURE)
        try:
            schema_ref = (
                ExactRef.from_mapping(value["schema_ref"])
                if "schema_ref" in value
                else None
            )
            return cls(
                role_id=value["role_id"],
                object_type=value["object_type"],
                schema_version=value["schema_version"],
                schema_ref=schema_ref,
            )
        except AuthorityPrimitiveError as exc:
            raise AuthorityPrimitiveError(SCHEMA_FAILURE) from exc
        except (KeyError, TypeError, ValueError) as exc:
            raise AuthorityPrimitiveError(SCHEMA_FAILURE) from exc

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "role_id": self.role_id,
            "object_type": self.object_type,
            "schema_version": self.schema_version,
        }
        if self.schema_ref is not None:
            result["schema_ref"] = self.schema_ref.to_dict()
        return result


@runtime_checkable
class ExactRefResolver(Protocol):
    def resolve_exact(self, ref: ExactRef) -> bytes | None:
        ...


def extract_identity(value: Mapping[str, Any]) -> ExactRef:
    if not isinstance(value, Mapping):
        _fail(REFERENCE_FAILURE)
    try:
        return ExactRef(
            object_id=value["object_id"],
            content_sha256=value["content_sha256"],
        )
    except AuthorityPrimitiveError:
        raise
    except (KeyError, TypeError, ValueError) as exc:
        raise AuthorityPrimitiveError(REFERENCE_FAILURE) from exc


def exact_ref_equal(
    left: ExactRef | Mapping[str, Any],
    right: ExactRef | Mapping[str, Any],
) -> bool:
    try:
        left_ref = left if isinstance(left, ExactRef) else ExactRef.from_mapping(left)
        right_ref = right if isinstance(right, ExactRef) else ExactRef.from_mapping(right)
    except AuthorityPrimitiveError:
        return False
    return left_ref == right_ref


def verify_sealed_identity(
    value: Mapping[str, Any],
    expected_ref: ExactRef | Mapping[str, Any] | None = None,
) -> ExactRef:
    identity = extract_identity(value)
    if expected_ref is not None and not exact_ref_equal(identity, expected_ref):
        _fail(REFERENCE_FAILURE)
    if not verify_sealed_object(value):
        _fail(HASH_FAILURE)
    return identity


def resolve_exact(ref: ExactRef, resolver: ExactRefResolver) -> dict[str, Any]:
    if not isinstance(ref, ExactRef):
        _fail(REFERENCE_FAILURE)
    try:
        raw = resolver.resolve_exact(ref)
    except Exception as exc:
        raise AuthorityPrimitiveError(NO_AUTHORITATIVE_RESULT) from exc
    if raw is None:
        _fail(NO_AUTHORITATIVE_RESULT)
    if not isinstance(raw, bytes):
        _fail(REFERENCE_FAILURE)
    try:
        value = parse_json_strict(raw)
    except CanonicalizationError as exc:
        raise AuthorityPrimitiveError(PARSE_FAILURE) from exc
    if not isinstance(value, Mapping):
        _fail(SCHEMA_FAILURE)
    resolved = dict(value)
    if not exact_ref_equal(extract_identity(resolved), ref):
        _fail(REFERENCE_FAILURE)
    verify_sealed_identity(resolved, ref)
    return resolved


def verify_role_binding(
    value: Mapping[str, Any],
    binding: RoleBinding,
    *,
    role_id: str,
    schema_ref: ExactRef | Mapping[str, Any] | None = None,
) -> ExactRef:
    if not isinstance(binding, RoleBinding):
        _fail(SCHEMA_FAILURE)
    try:
        require_ascii_token(role_id, "role_id")
    except (CanonicalizationError, TypeError) as exc:
        raise AuthorityPrimitiveError(SCHEMA_FAILURE) from exc
    if role_id != binding.role_id:
        _fail(SEMANTIC_FAILURE)
    if not isinstance(value, Mapping):
        _fail(SCHEMA_FAILURE)
    if (
        value.get("object_type") != binding.object_type
        or value.get("schema_version") != binding.schema_version
    ):
        _fail(SCHEMA_FAILURE)
    if binding.schema_ref is not None:
        if schema_ref is None or not exact_ref_equal(binding.schema_ref, schema_ref):
            _fail(REFERENCE_FAILURE)
    elif schema_ref is not None:
        _fail(REFERENCE_FAILURE)
    return verify_sealed_identity(value)


def _validate_projection_fields(
    fields: tuple[str, ...] | None,
) -> tuple[str, ...] | None:
    if fields is None:
        return None
    if not isinstance(fields, tuple) or not fields:
        _fail(SCHEMA_FAILURE)
    for field in fields:
        try:
            require_ascii_token(field, "projection field")
        except (CanonicalizationError, TypeError) as exc:
            raise AuthorityPrimitiveError(SCHEMA_FAILURE) from exc
    if len(fields) != len(set(fields)):
        _fail(SCHEMA_FAILURE)
    return tuple(sorted(fields))


@dataclass(frozen=True)
class ProjectionProfile:
    profile_id: str
    canonicalization_profile: str
    included_fields: tuple[str, ...] | None = None
    excluded_fields: tuple[str, ...] | None = None

    def __post_init__(self) -> None:
        try:
            require_ascii_token(self.profile_id, "profile_id")
        except (CanonicalizationError, TypeError) as exc:
            raise AuthorityPrimitiveError(SCHEMA_FAILURE) from exc
        if self.canonicalization_profile != _CANONICALIZATION_PROFILE:
            _fail(SCHEMA_FAILURE)
        included = _validate_projection_fields(self.included_fields)
        excluded = _validate_projection_fields(self.excluded_fields)
        if (included is None) == (excluded is None):
            _fail(SCHEMA_FAILURE)
        object.__setattr__(self, "included_fields", included)
        object.__setattr__(self, "excluded_fields", excluded)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> ProjectionProfile:
        if not isinstance(value, Mapping):
            _fail(SCHEMA_FAILURE)
        required = {"profile_id", "canonicalization_profile"}
        allowed = required | {"included_fields", "excluded_fields"}
        if not required.issubset(value) or not set(value).issubset(allowed):
            _fail(SCHEMA_FAILURE)
        try:
            included_value = value.get("included_fields")
            excluded_value = value.get("excluded_fields")
            if included_value is not None and not isinstance(
                included_value, (list, tuple)
            ):
                _fail(SCHEMA_FAILURE)
            if excluded_value is not None and not isinstance(
                excluded_value, (list, tuple)
            ):
                _fail(SCHEMA_FAILURE)
            return cls(
                profile_id=value["profile_id"],
                canonicalization_profile=value["canonicalization_profile"],
                included_fields=(
                    tuple(included_value)
                    if "included_fields" in value
                    else None
                ),
                excluded_fields=(
                    tuple(excluded_value)
                    if "excluded_fields" in value
                    else None
                ),
            )
        except AuthorityPrimitiveError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise AuthorityPrimitiveError(SCHEMA_FAILURE) from exc

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "profile_id": self.profile_id,
            "canonicalization_profile": self.canonicalization_profile,
        }
        if self.included_fields is not None:
            result["included_fields"] = list(self.included_fields)
        if self.excluded_fields is not None:
            result["excluded_fields"] = list(self.excluded_fields)
        return result


def projection_sha256(value: Mapping[str, Any], profile: ProjectionProfile) -> str:
    if not isinstance(value, Mapping) or not isinstance(profile, ProjectionProfile):
        _fail(SCHEMA_FAILURE)
    keys = set(value)
    selected_fields = (
        profile.included_fields
        if profile.included_fields is not None
        else profile.excluded_fields
    )
    assert selected_fields is not None
    if not set(selected_fields).issubset(keys):
        _fail(SCHEMA_FAILURE)
    if profile.included_fields is not None:
        projection = {field: value[field] for field in profile.included_fields}
    else:
        excluded = set(profile.excluded_fields or ())
        projection = {
            field: member for field, member in value.items() if field not in excluded
        }
    try:
        encoded = canonical_json(
            {"profile": profile.to_dict(), "projection": projection}
        )
    except CanonicalizationError as exc:
        raise AuthorityPrimitiveError(SCHEMA_FAILURE) from exc
    return hashlib.sha256(_PROJECTION_DOMAIN + encoded).hexdigest()
