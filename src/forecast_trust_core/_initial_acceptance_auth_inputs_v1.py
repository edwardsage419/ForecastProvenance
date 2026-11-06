"""Internal finite byte snapshots, never authority or public authentication.

No file, resolver, backend, native or message operations. Developer comparisons
do not establish the independently required input universe or applicability.
The limits below are development limits, not an adopted project contract.
"""
from dataclasses import dataclass

from .canonical import parse_json_strict, require_ascii_token, validate_ref, verify_sealed_object
import hashlib


_JSON_BYTES = 1048576
_TOTAL_BYTES = 67108864
_DEPTH = 64
_INPUT_COUNT = 2048


@dataclass(frozen=True)
class InputSpec:
    role: str
    data_format: str
    expected_bytes: int
    raw_sha256: str
    object_ref: tuple[str, str] | None = None
    object_type: str | None = None
    schema_version: str | None = None


@dataclass(frozen=True)
class InputSnapshot:
    role: str
    raw: bytes
    object_ref: tuple[str, str] | None
    data_format: str


@dataclass(frozen=True)
class InputSnapshots:
    items: tuple[InputSnapshot, ...] = ()
    failures: tuple[tuple[str, str], ...] = ()
    missing: tuple[str, ...] = ()
    total_bytes_supplied: int = 0
    retained_bytes: int = 0

    @property
    def status(self):
        return 'REJECTED' if self.failures else 'MISSING' if self.missing else 'OBSERVED'

    @property
    def public_authentication(self):
        return 'NOT_ESTABLISHED'


def _digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def _valid_spec(spec):
    if type(spec) is not InputSpec:
        return False
    if (type(spec.role) is not str or type(spec.expected_bytes) is not int
            or spec.expected_bytes < 0 or not _digest(spec.raw_sha256)
            or type(spec.data_format) is not str):
        return False
    try:
        require_ascii_token(spec.role)
        if spec.data_format == 'BYTES':
            return spec.object_ref is None and spec.object_type is None and spec.schema_version is None
        if spec.data_format != 'SEALED_JSON':
            return False
        ref = spec.object_ref
        if (type(ref) is not tuple or len(ref) != 2 or any(type(v) is not str for v in ref)
                or type(spec.object_type) is not str or type(spec.schema_version) is not str):
            return False
        validate_ref({'object_id': ref[0], 'content_sha256': ref[1]})
        require_ascii_token(spec.object_type)
        require_ascii_token(spec.schema_version)
    except (ValueError, TypeError):
        return False
    return True


def _within_depth(raw):
    depth, quoted, escaped = 0, False, False
    for char in raw:
        if quoted:
            if escaped:
                escaped = False
            elif char == 92:
                escaped = True
            elif char == 34:
                quoted = False
        elif char == 34:
            quoted = True
        elif char in (123, 91):
            depth += 1
            if depth > _DEPTH:
                return False
        elif char in (125, 93):
            depth -= 1
    return True  # Syntax/encoding correctness belongs to the strict parser.


def freeze_inputs(specs, supplied):
    """Check supplied finite roles; retain bytes, never a mutable parsed tree.

    Only exact tuple/spec/dict/bytes containers are consumed. No discovery or
    I/O callback exists. Every supplied occurrence for a declared role is charged
    to the work budget; successful identical bytes share one retained snapshot.
    Observed means these local comparisons matched, never independent admission.
    """
    if type(specs) is not tuple:
        return InputSnapshots(failures=(('#specs', 'INVALID_EXPECTED_INPUTS'),))
    if len(specs) > _INPUT_COUNT:
        return InputSnapshots(failures=(('#specs', 'INPUT_COUNT_LIMIT'),))
    if type(supplied) is not dict:
        return InputSnapshots(failures=(('#inputs', 'INVALID_SUPPLIED_INPUTS'),))
    if len(supplied) > _INPUT_COUNT:
        return InputSnapshots(failures=(('#inputs', 'INPUT_COUNT_LIMIT'),))
    if any(type(role) is not str for role in supplied):
        # A non-string key can execute its own equality in dict.get(str_role).
        return InputSnapshots(failures=(('#inputs', 'INVALID_SUPPLIED_ROLE'),))
    errors, missing, items = [], [], []
    total = 0
    roles, references, conflicted_refs, raw_cache = set(), {}, set(), {}

    def fail(role, code):
        if (role, code) not in errors:
            errors.append((role, code))

    if not specs:
        missing.append('expected_inputs')
    declared_roles = {s.role for s in specs if type(s) is InputSpec and type(s.role) is str}
    for role in supplied:
        if role not in declared_roles:
            fail(role, 'UNEXPECTED_ROLE')  # Its value is deliberately never accessed.

    for index, spec in enumerate(specs):
        role = spec.role if type(spec) is InputSpec and type(spec.role) is str else '#' + str(index)
        if not _valid_spec(spec):
            fail(role, 'INVALID_SPEC')
            continue
        if role in roles:
            fail(role, 'DUPLICATE_ROLE')
        roles.add(role)
        if spec.object_ref is not None:
            declared_identity = (spec.expected_bytes, spec.raw_sha256)
            previous = references.get(spec.object_ref)
            if previous is not None and previous[:2] != declared_identity:
                fail(previous[2], 'FULL_REF_RAW_CONFLICT')
                conflicted_refs.add(spec.object_ref)
            references.setdefault(spec.object_ref, (*declared_identity, role))
            if spec.object_ref in conflicted_refs:
                fail(role, 'FULL_REF_RAW_CONFLICT')
        raw = supplied.get(role)
        if raw is None:
            if role not in missing:
                missing.append(role)
            continue
        if type(raw) is not bytes:
            fail(role, 'INPUT_BYTES_REQUIRED')
            continue
        total += len(raw)
        if len(raw) != spec.expected_bytes:
            fail(role, 'RAW_SIZE_MISMATCH')
        if total > _TOTAL_BYTES:
            fail(role, 'TOTAL_BYTE_LIMIT')
            continue
        if spec.data_format == 'SEALED_JSON' and len(raw) > _JSON_BYTES:
            fail(role, 'JSON_BYTE_LIMIT')
            continue
        if hashlib.sha256(raw).hexdigest() != spec.raw_sha256:
            fail(role, 'RAW_SHA256_MISMATCH')
        if spec.data_format == 'SEALED_JSON':
            if not _within_depth(raw):
                fail(role, 'JSON_DEPTH_LIMIT')
                continue
            try:
                obj = parse_json_strict(raw)
            except (ValueError, TypeError, RecursionError):
                fail(role, 'JSON_INVALID')
                continue
            if type(obj) is not dict:
                fail(role, 'JSON_OBJECT_REQUIRED')
                continue
            if not verify_sealed_object(obj):
                fail(role, 'SEALED_IDENTITY_INVALID')
            if (obj.get('object_id'), obj.get('content_sha256')) != spec.object_ref:
                fail(role, 'FULL_REF_MISMATCH')
            if obj.get('object_type') != spec.object_type:
                fail(role, 'OBJECT_TYPE_MISMATCH')
            if obj.get('schema_version') != spec.schema_version:
                fail(role, 'SCHEMA_VERSION_MISMATCH')
        if any(label == role for label, _ in errors):
            continue
        shared = raw_cache.setdefault((spec.raw_sha256, len(raw)), raw)
        items.append(InputSnapshot(role, shared, spec.object_ref, spec.data_format))

    bad_roles = {role for role, _ in errors}
    items = tuple(item for item in items if item.role not in bad_roles and item.object_ref not in conflicted_refs)
    retained = {id(item.raw): item.raw for item in items}
    return InputSnapshots(items, tuple(errors), tuple(missing), total,
                          sum(len(raw) for raw in retained.values()))
