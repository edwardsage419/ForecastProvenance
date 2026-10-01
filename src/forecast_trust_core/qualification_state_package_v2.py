from __future__ import annotations

from contextlib import contextmanager
import base64
import binascii
import hashlib
import os
from dataclasses import dataclass
from enum import Enum
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Callable, Mapping

from ._roughtime_production_qualification import (
    DECISION_KEYS,
    DECISION_SIGNATURE_PROJECTION,
    METADATA_KEYS,
    PROFILE_KEYS,
    REQUALIFICATION_KEYS,
    REVIEW_KEYS,
    qualification_decision_signing_bytes,
    validate_production_provider_profile,
    validate_provider_metadata_review,
    validate_qualification_review,
    validate_qualification_state_report,
    validate_requalification_event,
)
from .canonical import (
    CanonicalizationError,
    canonical_json,
    content_hash,
    parse_json_strict,
    require_ascii_token,
    require_utc_timestamp,
    seal_object,
    validate_ref,
    verify_sealed_object,
)
from .qualification_validation_contracts_v1 import (
    qualification_state_history_snapshot_signed_projection,
    validate_qualification_state_history_snapshot,
)


SCHEMA_VERSION = "2.0"
OBJECT_TYPE = "DynamicQualificationStatePackage"
STABLE_CONTEXT = "v2"
_DIGEST_CHARS = frozenset("0123456789abcdef")
_METADATA_FIELDS = {
    "schema_version",
    "provider_profile_ref",
    "qualification_decision_ref",
    "qualification_state_history_snapshot_ref",
    "state_report_member_sha256",
    "as_of_utc",
}
_PAYLOAD_FIELDS = _METADATA_FIELDS | {"members"}
_PACKAGE_FIELDS = _PAYLOAD_FIELDS | {
    "object_type",
    "object_id",
    "payload_sha256",
    "content_sha256",
}
_MEMBER_FIELDS = {"role", "relative_path", "byte_length", "sha256"}
_RESERVED_PACKAGE_NAMES = {
    "dynamic_qualification_state_package_v2.json",
    "qualification_state_package_v2.json",
}
_PROFILE_TYPE = "RoughtimeProductionProviderProfile"
_DECISION_TYPE = "RoughtimeQualificationDecision"
_REVIEW_TYPE = "RoughtimeQualificationReview"
_METADATA_TYPE = "RoughtimeProviderMetadataReview"
_EVENT_TYPE = "RoughtimeRequalificationEvent"
_HISTORY_TYPE = "QualificationStateHistorySnapshot"
_STATE_REPORT_TYPE = "RoughtimeQualificationStateReport"
_FAMILY_KEYS = {
    _PROFILE_TYPE: PROFILE_KEYS,
    _DECISION_TYPE: DECISION_KEYS,
    _REVIEW_TYPE: REVIEW_KEYS,
    _METADATA_TYPE: METADATA_KEYS,
    _EVENT_TYPE: REQUALIFICATION_KEYS,
}


class QualificationStatePackageStage(str, Enum):
    PACKAGE_SCHEMA_INVALID = "PACKAGE_SCHEMA_INVALID"
    PACKAGE_SEALED_IDENTITY_OR_REFERENCE_INVALID = (
        "PACKAGE_SEALED_IDENTITY_OR_REFERENCE_INVALID"
    )
    PACKAGE_MEMBER_MANIFEST_INVALID = "PACKAGE_MEMBER_MANIFEST_INVALID"
    PACKAGE_MEMBER_CLOSURE_INVALID = "PACKAGE_MEMBER_CLOSURE_INVALID"
    QUALIFICATION_INPUT_SCHEMA_INVALID = "QUALIFICATION_INPUT_SCHEMA_INVALID"
    STATE_REPORT_MEMBER_INVALID = "STATE_REPORT_MEMBER_INVALID"
    HISTORY_CUTOFF_INVALID = "HISTORY_CUTOFF_INVALID"
    HISTORY_SUCCESSION_INVALID = "HISTORY_SUCCESSION_INVALID"
    HISTORY_COMPLETENESS_INVALID = "HISTORY_COMPLETENESS_INVALID"


class QualificationStatePackageError(ValueError):
    """The supplied root or package does not form an exact v2 content closure."""

    def __init__(
        self,
        message: str,
        *,
        stage: QualificationStatePackageStage | None = None,
    ) -> None:
        super().__init__(message)
        self.stage = stage


@contextmanager
def _failure_stage(stage: QualificationStatePackageStage):
    try:
        yield
    except QualificationStatePackageError as exc:
        if exc.stage is not None:
            raise
        raise QualificationStatePackageError(str(exc), stage=stage) from exc



def _fail(
    message: str, *, stage: QualificationStatePackageStage | None = None
) -> None:
    raise QualificationStatePackageError(message, stage=stage)


def _digest(value: Any, field: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(char not in _DIGEST_CHARS for char in value)
    ):
        _fail(f"{field} must be 64 lowercase hexadecimal characters")
    return value


def _relative_path(value: Any) -> str:
    if not isinstance(value, str) or not value or value == "." or "\\" in value:
        _fail("relative_path must be a non-empty POSIX path")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or any(
        part in {"", ".", ".."} for part in path.parts
    ):
        _fail("path traversal is prohibited")
    if path.name in _RESERVED_PACKAGE_NAMES:
        _fail("package definition cannot be included as a member")
    return value


def _metadata(
    *,
    provider_profile_ref: Mapping[str, Any],
    qualification_decision_ref: Mapping[str, Any],
    qualification_state_history_snapshot_ref: Mapping[str, Any],
    state_report_member_sha256: str,
    as_of_utc: str,
) -> dict[str, Any]:
    try:
        validate_ref(provider_profile_ref)
        validate_ref(qualification_decision_ref)
        validate_ref(qualification_state_history_snapshot_ref)
        require_utc_timestamp(as_of_utc)
        normalized_refs = (
            dict(provider_profile_ref),
            dict(qualification_decision_ref),
            dict(qualification_state_history_snapshot_ref),
        )
    except (CanonicalizationError, KeyError, TypeError, ValueError) as exc:
        raise QualificationStatePackageError(f"invalid package metadata: {exc}") from exc
    return {
        "schema_version": SCHEMA_VERSION,
        "provider_profile_ref": normalized_refs[0],
        "qualification_decision_ref": normalized_refs[1],
        "qualification_state_history_snapshot_ref": normalized_refs[2],
        "state_report_member_sha256": _digest(
            state_report_member_sha256,
            "state_report_member_sha256",
        ),
        "as_of_utc": as_of_utc,
    }


def _validate_expected_metadata(expected_metadata: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(expected_metadata, Mapping) or set(expected_metadata) != _METADATA_FIELDS:
        _fail("expected metadata field set mismatch")
    if expected_metadata["schema_version"] != SCHEMA_VERSION:
        _fail("metadata mismatch")
    return _metadata(
        provider_profile_ref=expected_metadata["provider_profile_ref"],
        qualification_decision_ref=expected_metadata["qualification_decision_ref"],
        qualification_state_history_snapshot_ref=expected_metadata[
            "qualification_state_history_snapshot_ref"
        ],
        state_report_member_sha256=expected_metadata["state_report_member_sha256"],
        as_of_utc=expected_metadata["as_of_utc"],
    )


_Fingerprint = tuple[int, int, int, int, int, int]
_DIRECTORY_OPEN_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_CLOEXEC", 0)
)
_FILE_OPEN_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_NOFOLLOW", 0)
    | getattr(os, "O_CLOEXEC", 0)
    | getattr(os, "O_NONBLOCK", 0)
)


def _fingerprint(status: os.stat_result) -> _Fingerprint:
    return (
        status.st_dev,
        status.st_ino,
        status.st_mode,
        status.st_size,
        status.st_mtime_ns,
        status.st_ctime_ns,
    )


def _same_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return (left.st_dev, left.st_ino) == (right.st_dev, right.st_ino)


def _open_root(root: Path) -> int:
    if not hasattr(os, "O_NOFOLLOW"):
        _fail("platform cannot enforce no-follow package reads")
    root_path = Path(root)
    try:
        before = root_path.lstat()
    except OSError as exc:
        raise QualificationStatePackageError(f"unable to inspect package root: {exc}") from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        _fail("package root must be a regular directory, not a symlink")
    try:
        root_fd = os.open(root_path, _DIRECTORY_OPEN_FLAGS)
    except OSError as exc:
        raise QualificationStatePackageError(f"unable to open package root: {exc}") from exc
    opened = os.fstat(root_fd)
    if not stat.S_ISDIR(opened.st_mode) or not _same_identity(before, opened):
        os.close(root_fd)
        _fail("package root changed while being opened")
    return root_fd


def _read_member(root_fd: int, relative_path: str) -> tuple[bytes, _Fingerprint]:
    parts = PurePosixPath(relative_path).parts
    directory_fd = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            try:
                next_fd = os.open(
                    part,
                    _DIRECTORY_OPEN_FLAGS,
                    dir_fd=directory_fd,
                )
            except FileNotFoundError:
                _fail(f"missing member: {relative_path}")
            except OSError as exc:
                raise QualificationStatePackageError(
                    f"symlink or invalid member path prohibited: {relative_path}: {exc}"
                ) from exc
            opened_directory = os.fstat(next_fd)
            if not stat.S_ISDIR(opened_directory.st_mode):
                os.close(next_fd)
                _fail(f"non-regular member path prohibited: {relative_path}")
            os.close(directory_fd)
            directory_fd = next_fd

        try:
            member_fd = os.open(
                parts[-1],
                _FILE_OPEN_FLAGS,
                dir_fd=directory_fd,
            )
        except FileNotFoundError:
            _fail(f"missing member: {relative_path}")
        except OSError as exc:
            raise QualificationStatePackageError(
                f"symlink or invalid member prohibited: {relative_path}: {exc}"
            ) from exc
        try:
            before = os.fstat(member_fd)
            if stat.S_ISLNK(before.st_mode):
                _fail(f"symlink member prohibited: {relative_path}")
            if not stat.S_ISREG(before.st_mode):
                _fail(f"non-regular member prohibited: {relative_path}")
            chunks: list[bytes] = []
            while True:
                chunk = os.read(member_fd, 1024 * 1024)
                if not chunk:
                    break
                chunks.append(chunk)
            after = os.fstat(member_fd)
            if _fingerprint(before) != _fingerprint(after):
                _fail(f"member changed during read: {relative_path}")
            return b"".join(chunks), _fingerprint(after)
        finally:
            os.close(member_fd)
    finally:
        os.close(directory_fd)


def _root_entries(root_fd: int) -> dict[str, _Fingerprint]:
    files: dict[str, _Fingerprint] = {}

    def visit(directory_fd: int, prefix: str) -> None:
        before = os.fstat(directory_fd)
        try:
            names = sorted(os.listdir(directory_fd))
        except OSError as exc:
            raise QualificationStatePackageError(
                f"unable to enumerate package root: {prefix or '.'}: {exc}"
            ) from exc
        for name in names:
            relative = f"{prefix}/{name}" if prefix else name
            try:
                observed = os.stat(
                    name,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
            except OSError as exc:
                raise QualificationStatePackageError(
                    f"unable to enumerate package root: {relative}: {exc}"
                ) from exc
            if stat.S_ISLNK(observed.st_mode):
                _fail(f"symlink prohibited: {relative}")
            if stat.S_ISDIR(observed.st_mode):
                try:
                    child_fd = os.open(
                        name,
                        _DIRECTORY_OPEN_FLAGS,
                        dir_fd=directory_fd,
                    )
                except OSError as exc:
                    raise QualificationStatePackageError(
                        f"unable to enumerate package root: {relative}: {exc}"
                    ) from exc
                try:
                    opened = os.fstat(child_fd)
                    if not stat.S_ISDIR(opened.st_mode) or not _same_identity(
                        observed, opened
                    ):
                        _fail(f"package directory changed during enumeration: {relative}")
                    visit(child_fd, relative)
                finally:
                    os.close(child_fd)
                continue
            if not stat.S_ISREG(observed.st_mode):
                _fail(f"non-regular file prohibited: {relative}")
            try:
                member_fd = os.open(
                    name,
                    _FILE_OPEN_FLAGS,
                    dir_fd=directory_fd,
                )
            except OSError as exc:
                raise QualificationStatePackageError(
                    f"unable to enumerate package root: {relative}: {exc}"
                ) from exc
            try:
                opened = os.fstat(member_fd)
                if not stat.S_ISREG(opened.st_mode) or not _same_identity(
                    observed, opened
                ):
                    _fail(f"package member changed during enumeration: {relative}")
                files[relative] = _fingerprint(opened)
            finally:
                os.close(member_fd)
        after = os.fstat(directory_fd)
        if _fingerprint(before) != _fingerprint(after):
            _fail(f"package directory changed during enumeration: {prefix or '.'}")

    duplicate_root_fd = os.dup(root_fd)
    try:
        visit(duplicate_root_fd, "")
    finally:
        os.close(duplicate_root_fd)
    return files


def _validate_snapshot(
    members: list[dict[str, Any]],
    snapshots: Mapping[str, _Fingerprint],
    actual_entries: Mapping[str, _Fingerprint],
) -> None:
    declared_paths = {member["relative_path"] for member in members}
    actual_paths = set(actual_entries)
    extras = sorted(actual_paths - declared_paths)
    if extras:
        _fail(f"unexpected extra file: {extras[0]}")
    missing = sorted(declared_paths - actual_paths)
    if missing:
        _fail(f"missing member: {missing[0]}")
    for relative_path in sorted(declared_paths):
        if snapshots[relative_path] != actual_entries[relative_path]:
            _fail(f"member changed during package snapshot: {relative_path}")


def _validate_manifest(members: Any) -> list[dict[str, Any]]:
    if not isinstance(members, list) or not members:
        _fail("members must be a non-empty array")
    normalized: list[dict[str, Any]] = []
    paths: set[str] = set()
    for member in members:
        if not isinstance(member, dict) or set(member) != _MEMBER_FIELDS:
            _fail("member field set mismatch")
        try:
            role = require_ascii_token(member["role"], "member role")
        except (CanonicalizationError, TypeError) as exc:
            raise QualificationStatePackageError(f"invalid member role: {exc}") from exc
        relative_path = _relative_path(member["relative_path"])
        if relative_path in paths:
            _fail(f"duplicate path: {relative_path}")
        paths.add(relative_path)
        byte_length = member["byte_length"]
        if (
            not isinstance(byte_length, int)
            or isinstance(byte_length, bool)
            or byte_length < 0
        ):
            _fail("byte_length must be a non-negative integer")
        normalized.append(
            {
                "role": role,
                "relative_path": relative_path,
                "byte_length": byte_length,
                "sha256": _digest(member["sha256"], "member sha256"),
            }
        )
    expected = sorted(normalized, key=lambda item: (item["role"], item["relative_path"]))
    if normalized != expected:
        _fail("member ordering is not deterministic")
    return normalized


def _read_raw_members(
    root_fd: int,
    members: list[dict[str, Any]],
    *,
    state_report_member_sha256: str,
) -> tuple[dict[str, bytes], str]:
    snapshots: dict[str, _Fingerprint] = {}
    member_bytes: dict[str, bytes] = {}
    for member in members:
        relative_path = member["relative_path"]
        data, fingerprint = _read_member(root_fd, relative_path)
        snapshots[relative_path] = fingerprint
        if len(data) != member["byte_length"]:
            _fail(f"byte-length mismatch: {relative_path}")
        member_sha256 = hashlib.sha256(data).hexdigest()
        if member_sha256 != member["sha256"]:
            _fail(f"hash mismatch: {relative_path}")
        member_bytes[relative_path] = data
    _validate_snapshot(members, snapshots, _root_entries(root_fd))
    matches = [
        member["relative_path"]
        for member in members
        if member["sha256"] == state_report_member_sha256
    ]
    if len(matches) != 1:
        _fail("exactly one state report member must match state_report_member_sha256")
    return member_bytes, matches[0]


_ExactRef = tuple[str, str]
_TypedMember = tuple[str, dict[str, Any], str]


@dataclass(frozen=True)
class PackageClosureResult:
    package_ref: dict[str, str]
    parsed_package: dict[str, Any]
    typed_exact_ref_member_map: Mapping[_ExactRef, _TypedMember]
    provider_profile: dict[str, Any]
    provider_profile_ref: dict[str, str]
    qualification_decision: dict[str, Any]
    qualification_decision_ref: dict[str, str]
    qualification_review: dict[str, Any]
    qualification_review_ref: dict[str, str]
    selected_history_snapshot: dict[str, Any]
    selected_history_snapshot_ref: dict[str, str]
    ordered_history_snapshot_chain: tuple[dict[str, Any], ...]
    metadata_reviews: tuple[dict[str, Any], ...]
    requalification_events: tuple[dict[str, Any], ...]
    state_report: dict[str, Any]
    state_report_member_sha256: str
    as_of_utc: str
    history_predecessor_cycle: bool = False


def _ref_key(value: Mapping[str, Any], field: str) -> _ExactRef:
    try:
        validate_ref(value)
    except (CanonicalizationError, KeyError, TypeError) as exc:
        raise QualificationStatePackageError(f"{field} must be an ExactRef") from exc
    return value["object_id"], value["content_sha256"]


def _strict_member_json(data: bytes, relative_path: str) -> dict[str, Any]:
    try:
        value = parse_json_strict(data)
    except (CanonicalizationError, UnicodeDecodeError) as exc:
        raise QualificationStatePackageError(
            f"invalid strict member JSON: {relative_path}: {exc}"
        ) from exc
    if not isinstance(value, dict):
        _fail(f"member matching no allowed local family: {relative_path}")
    return value


def _validate_decision_structure(
    decision: Mapping[str, Any],
    *,
    enforce_historical_bindings: bool = True,
) -> None:
    if set(decision) != DECISION_KEYS or not verify_sealed_object(decision):
        _fail("RoughtimeQualificationDecision schema or sealed identity invalid")
    if (
        decision.get("schema_version") != "1.0"
        or decision.get("object_type") != _DECISION_TYPE
        or decision.get("signature_projection") != DECISION_SIGNATURE_PROJECTION
        or decision.get("signature_algorithm") != "ED25519"
    ):
        _fail("RoughtimeQualificationDecision schema invalid")
    try:
        qualification_decision_signing_bytes(decision["signed_payload"])
        if (
            enforce_historical_bindings
            and decision["signed_payload_sha256"]
            != content_hash(decision["signed_payload"])
        ):
            _fail("RoughtimeQualificationDecision signed_payload_sha256 mismatch")
        signature = base64.b64decode(
            decision["authority_signature_base64"],
            validate=True,
        )
    except (binascii.Error, KeyError, TypeError, ValueError) as exc:
        raise QualificationStatePackageError(
            f"RoughtimeQualificationDecision authentication structure invalid: {exc}"
        ) from exc
    if (
        not signature
        or base64.b64encode(signature).decode("ascii")
        != decision["authority_signature_base64"]
    ):
        _fail("RoughtimeQualificationDecision authority signature encoding invalid")


_HISTORY_REQUIRED_PACKAGE_FIELDS = {
    "schema_version",
    "object_type",
    "provider_profile_ref",
    "snapshot_sequence",
    "through_as_of_utc",
    "metadata_review_refs",
    "requalification_event_refs",
    "signed_payload_sha256",
    "authority_signature_base64",
    "object_id",
    "payload_sha256",
    "content_sha256",
}


def _validate_history_snapshot_precedence_boundary(
    snapshot: Mapping[str, Any],
) -> None:
    fields = set(snapshot)
    if not _HISTORY_REQUIRED_PACKAGE_FIELDS.issubset(fields) or fields - (
        _HISTORY_REQUIRED_PACKAGE_FIELDS | {"predecessor_snapshot_ref"}
    ):
        _fail("QualificationStateHistorySnapshot field set invalid")
    if (
        snapshot.get("schema_version") != "1.0"
        or snapshot.get("object_type") != _HISTORY_TYPE
        or not verify_sealed_object(snapshot)
    ):
        _fail("QualificationStateHistorySnapshot schema or sealed identity invalid")
    sequence = snapshot.get("snapshot_sequence")
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 0:
        _fail("QualificationStateHistorySnapshot snapshot_sequence invalid")
    _ref_key(snapshot["provider_profile_ref"], "history provider_profile_ref")
    if "predecessor_snapshot_ref" in snapshot:
        _ref_key(snapshot["predecessor_snapshot_ref"], "history predecessor_snapshot_ref")
    try:
        require_utc_timestamp(snapshot["through_as_of_utc"])
    except (CanonicalizationError, TypeError) as exc:
        raise QualificationStatePackageError(
            "QualificationStateHistorySnapshot cutoff invalid"
        ) from exc
    for field in ("metadata_review_refs", "requalification_event_refs"):
        refs = snapshot[field]
        if not isinstance(refs, list):
            _fail(f"QualificationStateHistorySnapshot {field} must be an array")
        keys = [_ref_key(item, field) for item in refs]
        if keys != sorted(keys) or len(keys) != len(set(keys)):
            _fail(f"QualificationStateHistorySnapshot {field} must be sorted and unique")
    _digest(snapshot["signed_payload_sha256"], "signed_payload_sha256")
    signature_text = snapshot["authority_signature_base64"]
    if not isinstance(signature_text, str) or not signature_text:
        _fail("authority_signature_base64 must be non-empty canonical base64")
    try:
        signature = base64.b64decode(signature_text, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise QualificationStatePackageError(
            "authority_signature_base64 must be non-empty canonical base64"
        ) from exc
    if (
        not signature
        or base64.b64encode(signature).decode("ascii") != signature_text
    ):
        _fail("authority_signature_base64 must be non-empty canonical base64")
    projection = qualification_state_history_snapshot_signed_projection(snapshot)
    if snapshot["signed_payload_sha256"] != content_hash(projection):
        _fail("history signed_payload_sha256 mismatch")

def _classify_local_member(
    value: dict[str, Any],
    relative_path: str,
    *,
    enforce_historical_bindings: bool = True,
) -> str:
    object_type = value.get("object_type")
    matches: list[str] = []
    if object_type == _HISTORY_TYPE:
        _validate_history_snapshot_precedence_boundary(value)
        matches.append(_HISTORY_TYPE)
    expected_keys = _FAMILY_KEYS.get(object_type)
    if expected_keys is not None and set(value) == expected_keys:
        if value.get("schema_version") == "1.0" and verify_sealed_object(value):
            matches.append(object_type)
    if len(matches) != 1:
        if len(matches) > 1:
            _fail(f"member matches multiple allowed local families: {relative_path}")
        _fail(f"member matching no allowed local family: {relative_path}")
    family = matches[0]
    try:
        if family == _PROFILE_TYPE:
            validate_production_provider_profile(value)
        elif family == _DECISION_TYPE:
            _validate_decision_structure(
                value,
                enforce_historical_bindings=enforce_historical_bindings,
            )
    except ValueError as exc:
        raise QualificationStatePackageError(
            f"{family} schema or sealed identity invalid: {exc}"
        ) from exc
    return family


def _validate_state_report_member(
    member_bytes: Mapping[str, bytes],
    state_report_path: str,
) -> dict[str, Any]:
    report = _strict_member_json(member_bytes[state_report_path], state_report_path)
    try:
        validate_qualification_state_report(report)
    except ValueError as exc:
        raise QualificationStatePackageError(f"state report member invalid: {exc}") from exc
    return report


def _discover_semantic_members(
    members: list[dict[str, Any]],
    member_bytes: Mapping[str, bytes],
    state_report_path: str,
    *,
    enforce_historical_bindings: bool = True,
) -> dict[_ExactRef, _TypedMember]:
    semantic: dict[_ExactRef, _TypedMember] = {}
    object_ids: dict[str, str] = {}
    for member in members:
        relative_path = member["relative_path"]
        if relative_path == state_report_path:
            continue
        value = _strict_member_json(member_bytes[relative_path], relative_path)
        family = _classify_local_member(
            value,
            relative_path,
            enforce_historical_bindings=enforce_historical_bindings,
        )
        key = _ref_key(
            {
                "object_id": value.get("object_id"),
                "content_sha256": value.get("content_sha256"),
            },
            f"{relative_path} identity",
        )
        if key in semantic:
            _fail(f"duplicate ExactRef physical member: {relative_path}")
        prior_hash = object_ids.get(key[0])
        if prior_hash is not None and prior_hash != key[1]:
            _fail(f"object_id rebound to different content_sha256: {key[0]}")
        object_ids[key[0]] = key[1]
        semantic[key] = (family, value, relative_path)
    return semantic


def _verify_semantic_closure(
    metadata: Mapping[str, Any],
    members: list[dict[str, Any]],
    member_bytes: Mapping[str, bytes],
    state_report_path: str,
    *,
    enforce_historical_bindings: bool = True,
) -> dict[_ExactRef, _TypedMember]:
    semantic = _discover_semantic_members(
        members,
        member_bytes,
        state_report_path,
        enforce_historical_bindings=enforce_historical_bindings,
    )
    reachable: set[_ExactRef] = set()
    completed: set[_ExactRef] = set()
    active: set[_ExactRef] = set()

    def walk(ref: Mapping[str, Any], expected_family: str, field: str) -> dict[str, Any]:
        key = _ref_key(ref, field)
        typed = semantic.get(key)
        if typed is None:
            _fail(f"missing referenced local object: {field}")
        family, value, _relative_path = typed
        if family != expected_family:
            _fail(
                f"local reference type mismatch: {field} expected {expected_family}, got {family}"
            )
        reachable.add(key)
        if key in completed:
            return value
        if key in active:
            if family == _HISTORY_TYPE:
                return value
            _fail(f"typed semantic graph cycle detected at {field}")
        active.add(key)
        try:
            if family == _PROFILE_TYPE:
                validate_production_provider_profile(value)
            elif family == _METADATA_TYPE:
                profile = walk(
                    value["provider_profile_ref"],
                    _PROFILE_TYPE,
                    "ProviderMetadataReview.provider_profile_ref",
                )
                validate_provider_metadata_review(value, profile=profile)
            elif family == _EVENT_TYPE:
                profile = walk(
                    value["provider_profile_ref"],
                    _PROFILE_TYPE,
                    "RequalificationEvent.provider_profile_ref",
                )
                validate_requalification_event(value, profile=profile)
            elif family == _REVIEW_TYPE:
                profile = walk(
                    value["provider_profile_ref"],
                    _PROFILE_TYPE,
                    "QualificationReview.provider_profile_ref",
                )
                metadata_review = walk(
                    value["metadata_review_ref"],
                    _METADATA_TYPE,
                    "QualificationReview.metadata_review_ref",
                )
                validate_qualification_review(
                    value,
                    profile=profile,
                    metadata_review=metadata_review,
                    evidence_manifest_sha256=value["evidence_manifest_sha256"],
                )
            elif family == _DECISION_TYPE:
                signed = value["signed_payload"]
                profile = walk(
                    signed["provider_profile_ref"],
                    _PROFILE_TYPE,
                    "QualificationDecision.provider_profile_ref",
                )
                review = walk(
                    signed["independent_review_ref"],
                    _REVIEW_TYPE,
                    "QualificationDecision.independent_review_ref",
                )
                metadata_review = walk(
                    signed["metadata_review_ref"],
                    _METADATA_TYPE,
                    "QualificationDecision.metadata_review_ref",
                )
                if enforce_historical_bindings:
                    if signed["provider_id"] != profile["provider_id"]:
                        _fail("QualificationDecision provider mismatch")
                    if signed["evidence_manifest_sha256"] != review["evidence_manifest_sha256"]:
                        _fail("QualificationDecision external evidence binding mismatch")
                    if (
                        signed["verifier_build_profile_sha256"]
                        != review["verifier_build_profile_sha256"]
                        or signed["verifier_binary_sha256"]
                        != review["verifier_binary_sha256"]
                    ):
                        _fail("QualificationDecision static verifier binding mismatch")
                    if metadata_review["provider_profile_ref"] != signed["provider_profile_ref"]:
                        _fail("QualificationDecision metadata provider mismatch")
            elif family == _HISTORY_TYPE:
                _validate_history_snapshot_precedence_boundary(value)
                walk(
                    value["provider_profile_ref"],
                    _PROFILE_TYPE,
                    "HistorySnapshot.provider_profile_ref",
                )
                if (
                    value["snapshot_sequence"] != 0
                    and "predecessor_snapshot_ref" in value
                ):
                    walk(
                        value["predecessor_snapshot_ref"],
                        _HISTORY_TYPE,
                        "HistorySnapshot.predecessor_snapshot_ref",
                    )
                for record_ref in value["metadata_review_refs"]:
                    walk(
                        record_ref,
                        _METADATA_TYPE,
                        "HistorySnapshot.metadata_review_refs[]",
                    )
                for record_ref in value["requalification_event_refs"]:
                    walk(
                        record_ref,
                        _EVENT_TYPE,
                        "HistorySnapshot.requalification_event_refs[]",
                    )
        except QualificationStatePackageError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise QualificationStatePackageError(
                f"{family} semantic validation failed: {exc}"
            ) from exc
        finally:
            active.discard(key)
        completed.add(key)
        return value

    walk(
        metadata["provider_profile_ref"],
        _PROFILE_TYPE,
        "package.provider_profile_ref",
    )
    walk(
        metadata["qualification_decision_ref"],
        _DECISION_TYPE,
        "package.qualification_decision_ref",
    )
    walk(
        metadata["qualification_state_history_snapshot_ref"],
        _HISTORY_TYPE,
        "package.qualification_state_history_snapshot_ref",
    )
    unreachable = set(semantic) - reachable
    early_unreachable = {
        key
        for key in unreachable
        if semantic[key][0] not in {_HISTORY_TYPE, _METADATA_TYPE, _EVENT_TYPE}
    }
    if early_unreachable:
        first = semantic[sorted(early_unreachable)[0]][2]
        _fail(
            f"unreachable package-local member: {first}",
            stage=QualificationStatePackageStage.PACKAGE_MEMBER_CLOSURE_INVALID,
        )
    return semantic


def validate_history_cutoff(closure: PackageClosureResult) -> None:
    with _failure_stage(QualificationStatePackageStage.HISTORY_CUTOFF_INVALID):
        if closure.selected_history_snapshot["through_as_of_utc"] != closure.as_of_utc:
            _fail("selected history snapshot cutoff differs from package cutoff")


def validate_history_succession(closure: PackageClosureResult) -> None:
    with _failure_stage(QualificationStatePackageStage.HISTORY_SUCCESSION_INVALID):
        if closure.history_predecessor_cycle:
            _fail("history predecessor cycle detected")
        chain = closure.ordered_history_snapshot_chain
        if not chain:
            _fail("selected history predecessor chain is empty")
        for index, snapshot in enumerate(chain):
            sequence = snapshot["snapshot_sequence"]
            has_predecessor = "predecessor_snapshot_ref" in snapshot
            if sequence == 0:
                if has_predecessor:
                    _fail("sequence zero prohibits predecessor_snapshot_ref")
                if index != len(chain) - 1:
                    _fail("history predecessor chain continues after sequence zero")
                continue
            if not has_predecessor:
                _fail("successor history snapshot requires predecessor")
            if index + 1 >= len(chain):
                _fail("history predecessor chain does not terminate at sequence zero")
            predecessor = chain[index + 1]
            predecessor_ref = {
                "object_id": predecessor["object_id"],
                "content_sha256": predecessor["content_sha256"],
            }
            if snapshot["predecessor_snapshot_ref"] != predecessor_ref:
                _fail("history predecessor ExactRef mismatch")
            if sequence != predecessor["snapshot_sequence"] + 1:
                _fail("history snapshot sequence gap")
            if snapshot["provider_profile_ref"] != predecessor["provider_profile_ref"]:
                _fail("history snapshot provider mismatch")
            if snapshot["through_as_of_utc"] <= predecessor["through_as_of_utc"]:
                _fail("history snapshot cutoff must strictly increase")
        if chain[-1]["snapshot_sequence"] != 0:
            _fail("history predecessor chain does not terminate at sequence zero")


def validate_history_completeness(closure: PackageClosureResult) -> None:
    with _failure_stage(QualificationStatePackageStage.HISTORY_COMPLETENESS_INVALID):
        chain = closure.ordered_history_snapshot_chain
        semantic = closure.typed_exact_ref_member_map
        for snapshot, predecessor in zip(chain, chain[1:]):
            prior_metadata = {
                _ref_key(item, "predecessor.metadata_review_refs[]")
                for item in predecessor["metadata_review_refs"]
            }
            prior_events = {
                _ref_key(item, "predecessor.requalification_event_refs[]")
                for item in predecessor["requalification_event_refs"]
            }
            current_metadata = {
                _ref_key(item, "metadata_review_refs[]")
                for item in snapshot["metadata_review_refs"]
            }
            current_events = {
                _ref_key(item, "requalification_event_refs[]")
                for item in snapshot["requalification_event_refs"]
            }
            if not prior_metadata.issubset(current_metadata) or not prior_events.issubset(
                current_events
            ):
                _fail("history record removal violates predecessor subset")
            for record_key in (current_metadata - prior_metadata) | (
                current_events - prior_events
            ):
                record = semantic[record_key][1]
                if record["provider_profile_ref"] != snapshot["provider_profile_ref"]:
                    _fail("history record provider mismatch")
                timestamp = record.get("reviewed_at", record.get("detected_at"))
                if not (
                    predecessor["through_as_of_utc"]
                    < timestamp
                    <= snapshot["through_as_of_utc"]
                ):
                    _fail("new history record timestamp outside successor window")

        selected_metadata = {
            _ref_key(item, "selected.metadata_review_refs[]")
            for item in closure.selected_history_snapshot["metadata_review_refs"]
        }
        selected_events = {
            _ref_key(item, "selected.requalification_event_refs[]")
            for item in closure.selected_history_snapshot["requalification_event_refs"]
        }
        package_metadata = {
            (item["object_id"], item["content_sha256"])
            for item in closure.metadata_reviews
        }
        package_events = {
            (item["object_id"], item["content_sha256"])
            for item in closure.requalification_events
        }
        if selected_metadata != package_metadata or selected_events != package_events:
            _fail("selected history cumulative record sets differ from package closure")
        package_history = {
            key
            for key, member in semantic.items()
            if member[0] == _HISTORY_TYPE
        }
        chain_history = {
            (snapshot["object_id"], snapshot["content_sha256"])
            for snapshot in chain
        }
        if package_history != chain_history:
            _fail("selected predecessor chain differs from package history closure")


def _validate_deferred_historical_bindings(
    closure: PackageClosureResult,
) -> None:
    with _failure_stage(
        QualificationStatePackageStage.QUALIFICATION_INPUT_SCHEMA_INVALID
    ):
        signed = closure.qualification_decision["signed_payload"]
        if closure.qualification_decision["signed_payload_sha256"] != content_hash(
            signed
        ):
            _fail("RoughtimeQualificationDecision signed_payload_sha256 mismatch")

        review = closure.qualification_review
        metadata_key = _ref_key(
            signed["metadata_review_ref"],
            "QualificationDecision.metadata_review_ref",
        )
        metadata_review = closure.typed_exact_ref_member_map[metadata_key][1]
        if signed["provider_id"] != closure.provider_profile["provider_id"]:
            _fail("QualificationDecision provider mismatch")
        if signed["evidence_manifest_sha256"] != review["evidence_manifest_sha256"]:
            _fail("QualificationDecision external evidence binding mismatch")
        if (
            signed["verifier_build_profile_sha256"]
            != review["verifier_build_profile_sha256"]
            or signed["verifier_binary_sha256"]
            != review["verifier_binary_sha256"]
        ):
            _fail("QualificationDecision static verifier binding mismatch")
        if (
            metadata_review["provider_profile_ref"]
            != signed["provider_profile_ref"]
        ):
            _fail("QualificationDecision metadata provider mismatch")


def _make_package_closure_result(
    *,
    package_ref: Mapping[str, str],
    parsed_package: Mapping[str, Any],
    metadata: Mapping[str, Any],
    semantic: Mapping[_ExactRef, _TypedMember],
    state_report: Mapping[str, Any],
) -> PackageClosureResult:
    def semantic_member(ref: Mapping[str, Any], field: str) -> dict[str, Any]:
        return semantic[_ref_key(ref, field)][1]

    profile = semantic_member(metadata["provider_profile_ref"], "profile")
    decision = semantic_member(metadata["qualification_decision_ref"], "decision")
    review_ref = decision["signed_payload"]["independent_review_ref"]
    review = semantic_member(review_ref, "review")
    selected_ref = metadata["qualification_state_history_snapshot_ref"]
    selected = semantic_member(selected_ref, "selected history")
    chain: list[dict[str, Any]] = []
    seen_history: set[_ExactRef] = set()
    history_predecessor_cycle = False
    current = selected
    while True:
        current_key = (current["object_id"], current["content_sha256"])
        if current_key in seen_history:
            history_predecessor_cycle = True
            break
        seen_history.add(current_key)
        chain.append(current)
        if (
            current["snapshot_sequence"] == 0
            or "predecessor_snapshot_ref" not in current
        ):
            break
        current = semantic_member(current["predecessor_snapshot_ref"], "predecessor")

    return PackageClosureResult(
        package_ref=dict(package_ref),
        parsed_package=dict(parsed_package),
        typed_exact_ref_member_map=dict(semantic),
        provider_profile=profile,
        provider_profile_ref=dict(metadata["provider_profile_ref"]),
        qualification_decision=decision,
        qualification_decision_ref=dict(metadata["qualification_decision_ref"]),
        qualification_review=review,
        qualification_review_ref=dict(review_ref),
        selected_history_snapshot=selected,
        selected_history_snapshot_ref=dict(selected_ref),
        ordered_history_snapshot_chain=tuple(chain),
        metadata_reviews=tuple(
            item[1]
            for _, item in sorted(semantic.items())
            if item[0] == _METADATA_TYPE
        ),
        requalification_events=tuple(
            item[1]
            for _, item in sorted(semantic.items())
            if item[0] == _EVENT_TYPE
        ),
        state_report=dict(state_report),
        state_report_member_sha256=metadata["state_report_member_sha256"],
        as_of_utc=metadata["as_of_utc"],
        history_predecessor_cycle=history_predecessor_cycle,
    )
def build_dynamic_qualification_state_package(
    root: Path,
    *,
    provider_profile_ref: Mapping[str, Any],
    qualification_decision_ref: Mapping[str, Any],
    qualification_state_history_snapshot_ref: Mapping[str, Any],
    state_report_member_sha256: str,
    as_of_utc: str,
    member_paths: Mapping[str, str],
) -> dict[str, Any]:
    """Build and seal an authenticated exact semantic package closure."""
    metadata = _metadata(
        provider_profile_ref=provider_profile_ref,
        qualification_decision_ref=qualification_decision_ref,
        qualification_state_history_snapshot_ref=(
            qualification_state_history_snapshot_ref
        ),
        state_report_member_sha256=state_report_member_sha256,
        as_of_utc=as_of_utc,
    )
    if not isinstance(member_paths, Mapping) or not member_paths:
        _fail("member_paths must map at least one role to a relative path")

    root_fd = _open_root(root)
    try:
        members: list[dict[str, Any]] = []
        snapshots: dict[str, _Fingerprint] = {}
        member_bytes: dict[str, bytes] = {}
        for role, supplied_path in member_paths.items():
            try:
                normalized_role = require_ascii_token(role, "member role")
            except (CanonicalizationError, TypeError, AttributeError) as exc:
                raise QualificationStatePackageError(
                    f"invalid member role: {exc}"
                ) from exc
            relative_path = _relative_path(supplied_path)
            data, fingerprint = _read_member(root_fd, relative_path)
            snapshots[relative_path] = fingerprint
            member_bytes[relative_path] = data
            members.append(
                {
                    "role": normalized_role,
                    "relative_path": relative_path,
                    "byte_length": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )

        members.sort(key=lambda item: (item["role"], item["relative_path"]))
        members = _validate_manifest(members)
        _validate_snapshot(members, snapshots, _root_entries(root_fd))
        matches = [
            member["relative_path"]
            for member in members
            if member["sha256"] == metadata["state_report_member_sha256"]
        ]
        if len(matches) != 1:
            _fail(
                "exactly one state report member must match "
                "state_report_member_sha256"
            )
        state_report = _validate_state_report_member(member_bytes, matches[0])
        semantic = _verify_semantic_closure(
            metadata, members, member_bytes, matches[0]
        )
    finally:
        os.close(root_fd)

    payload = {**metadata, "members": members}
    try:
        package = seal_object(
            payload,
            object_type=OBJECT_TYPE,
            stable_context=STABLE_CONTEXT,
        )
    except CanonicalizationError as exc:
        raise QualificationStatePackageError(f"unable to seal package: {exc}") from exc
    closure = _make_package_closure_result(
        package_ref={
            "object_id": package["object_id"],
            "content_sha256": package["content_sha256"],
        },
        parsed_package=package,
        metadata=metadata,
        semantic=semantic,
        state_report=state_report,
    )
    validate_history_cutoff(closure)
    validate_history_succession(closure)
    validate_history_completeness(closure)
    return package


def _resolve_strict_package(
    package_ref: Mapping[str, Any],
    resolve_package: Callable[[Mapping[str, str]], bytes | str],
) -> dict[str, Any]:
    try:
        serialized = resolve_package(dict(package_ref))
    except Exception as exc:
        raise QualificationStatePackageError(
            f"unable to resolve exact package reference: {exc}"
        ) from exc
    if not isinstance(serialized, (bytes, bytearray, str)):
        _fail("exact package resolver must return serialized JSON bytes or text")
    try:
        parsed = parse_json_strict(
            bytes(serialized) if isinstance(serialized, bytearray) else serialized
        )
    except (CanonicalizationError, UnicodeDecodeError) as exc:
        raise QualificationStatePackageError(f"invalid strict package JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        _fail("strict package JSON must be an object")
    return parsed


def _verify_standard_identity(
    package: Mapping[str, Any],
    package_ref: Mapping[str, str],
) -> None:
    object_id = package.get("object_id")
    content_sha256 = _digest(package.get("content_sha256"), "content_sha256")
    if object_id != package_ref["object_id"] or content_sha256 != package_ref["content_sha256"]:
        _fail("resolved package does not match exact package reference")

    try:
        expected_content = hashlib.sha256(
            canonical_json(
                {key: value for key, value in package.items() if key != "content_sha256"}
            )
        ).hexdigest()
    except CanonicalizationError as exc:
        raise QualificationStatePackageError(f"invalid sealed package: {exc}") from exc
    if content_sha256 != expected_content:
        _fail("content_sha256 mismatch")

    payload_sha256 = _digest(package.get("payload_sha256"), "payload_sha256")
    try:
        expected_payload = hashlib.sha256(
            canonical_json(
                {
                    key: value
                    for key, value in package.items()
                    if key not in {"object_id", "payload_sha256", "content_sha256"}
                }
            )
        ).hexdigest()
    except CanonicalizationError as exc:
        raise QualificationStatePackageError(f"invalid package payload: {exc}") from exc
    if payload_sha256 != expected_payload:
        _fail("payload_sha256 mismatch")

    try:
        object_type = require_ascii_token(package.get("object_type"), "object_type")
        expected = seal_object(
            {
                key: value
                for key, value in package.items()
                if key not in {"object_type", "object_id", "payload_sha256", "content_sha256"}
            },
            object_type=object_type,
            stable_context=STABLE_CONTEXT,
        )
    except (CanonicalizationError, TypeError) as exc:
        raise QualificationStatePackageError(f"invalid object_type: {exc}") from exc
    if object_id != expected["object_id"]:
        _fail("deterministic object_id mismatch")
    if not verify_sealed_object(package):
        _fail("standard sealed object verification failed")


def build_package_closure(
    package_ref: Mapping[str, Any],
    root: Path,
    *,
    parsed_package: Mapping[str, Any],
) -> PackageClosureResult:
    """Validate and return the typed package-local closure."""
    try:
        validate_ref(package_ref)
        exact_ref = dict(package_ref)
    except (CanonicalizationError, TypeError, ValueError) as exc:
        raise QualificationStatePackageError(
            f"exact package reference required: {exc}"
        ) from exc
    with _failure_stage(QualificationStatePackageStage.PACKAGE_SCHEMA_INVALID):
        if not isinstance(parsed_package, Mapping):
            _fail("strict package JSON must be an object")
        package = dict(parsed_package)
        if package.get("object_type") != OBJECT_TYPE:
            _fail("object_type mismatch")
        if package.get("schema_version") != SCHEMA_VERSION:
            _fail("schema_version mismatch")
        if set(package) != _PACKAGE_FIELDS:
            _fail("package field set mismatch")
        metadata = {field: package[field] for field in _METADATA_FIELDS}
        validated_metadata = _metadata(
            provider_profile_ref=metadata["provider_profile_ref"],
            qualification_decision_ref=metadata["qualification_decision_ref"],
            qualification_state_history_snapshot_ref=metadata[
                "qualification_state_history_snapshot_ref"
            ],
            state_report_member_sha256=metadata["state_report_member_sha256"],
            as_of_utc=metadata["as_of_utc"],
        )
        if metadata != validated_metadata:
            _fail("metadata mismatch")
    with _failure_stage(
        QualificationStatePackageStage.PACKAGE_SEALED_IDENTITY_OR_REFERENCE_INVALID
    ):
        _verify_standard_identity(package, exact_ref)
    with _failure_stage(
        QualificationStatePackageStage.PACKAGE_MEMBER_MANIFEST_INVALID
    ):
        members = _validate_manifest(package["members"])
    root_fd = _open_root(root)
    try:
        with _failure_stage(
            QualificationStatePackageStage.PACKAGE_MEMBER_CLOSURE_INVALID
        ):
            member_bytes, state_report_path = _read_raw_members(
                root_fd,
                members,
                state_report_member_sha256=validated_metadata[
                    "state_report_member_sha256"
                ],
            )
        with _failure_stage(
            QualificationStatePackageStage.QUALIFICATION_INPUT_SCHEMA_INVALID
        ):
            semantic = _verify_semantic_closure(
                validated_metadata,
                members,
                member_bytes,
                state_report_path,
                enforce_historical_bindings=False,
            )
        with _failure_stage(
            QualificationStatePackageStage.STATE_REPORT_MEMBER_INVALID
        ):
            state_report = _validate_state_report_member(
                member_bytes, state_report_path
            )
    finally:
        os.close(root_fd)

    def semantic_member(ref: Mapping[str, Any], field: str) -> dict[str, Any]:
        return semantic[_ref_key(ref, field)][1]

    profile = semantic_member(validated_metadata["provider_profile_ref"], "profile")
    decision = semantic_member(
        validated_metadata["qualification_decision_ref"], "decision"
    )
    review_ref = decision["signed_payload"]["independent_review_ref"]
    review = semantic_member(review_ref, "review")
    selected_ref = validated_metadata["qualification_state_history_snapshot_ref"]
    selected = semantic_member(selected_ref, "selected history")
    chain: list[dict[str, Any]] = []
    seen_history: set[_ExactRef] = set()
    history_predecessor_cycle = False
    current = selected
    while True:
        current_key = (current["object_id"], current["content_sha256"])
        if current_key in seen_history:
            history_predecessor_cycle = True
            break
        seen_history.add(current_key)
        chain.append(current)
        if (
            current["snapshot_sequence"] == 0
            or "predecessor_snapshot_ref" not in current
        ):
            break
        current = semantic_member(current["predecessor_snapshot_ref"], "predecessor")

    return PackageClosureResult(
        package_ref=exact_ref,
        parsed_package=package,
        typed_exact_ref_member_map=dict(semantic),
        provider_profile=profile,
        provider_profile_ref=dict(validated_metadata["provider_profile_ref"]),
        qualification_decision=decision,
        qualification_decision_ref=dict(
            validated_metadata["qualification_decision_ref"]
        ),
        qualification_review=review,
        qualification_review_ref=dict(review_ref),
        selected_history_snapshot=selected,
        selected_history_snapshot_ref=dict(selected_ref),
        ordered_history_snapshot_chain=tuple(chain),
        metadata_reviews=tuple(
            item[1]
            for _, item in sorted(semantic.items())
            if item[0] == _METADATA_TYPE
        ),
        requalification_events=tuple(
            item[1]
            for _, item in sorted(semantic.items())
            if item[0] == _EVENT_TYPE
        ),
        state_report=state_report,
        state_report_member_sha256=validated_metadata[
            "state_report_member_sha256"
        ],
        as_of_utc=validated_metadata["as_of_utc"],
        history_predecessor_cycle=history_predecessor_cycle,
    )


def verify_dynamic_qualification_state_package(
    package_ref: Mapping[str, Any],
    root: Path,
    *,
    resolve_package: Callable[[Mapping[str, str]], bytes | str],
    expected_metadata: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    """Resolve and independently verify an exact v2 package reference."""
    try:
        validate_ref(package_ref)
        exact_ref = dict(package_ref)
    except (CanonicalizationError, TypeError, ValueError) as exc:
        raise QualificationStatePackageError(
            f"exact package reference required: {exc}"
        ) from exc
    if not callable(resolve_package):
        _fail("resolve_package must be callable")

    package = _resolve_strict_package(exact_ref, resolve_package)
    closure = build_package_closure(
        exact_ref,
        root,
        parsed_package=package,
    )
    if expected_metadata is not None:
        validated_expected = _validate_expected_metadata(expected_metadata)
        actual_metadata = {
            field: closure.parsed_package[field] for field in _METADATA_FIELDS
        }
        if validated_expected != actual_metadata:
            _fail("metadata mismatch")
    _validate_deferred_historical_bindings(closure)
    validate_history_cutoff(closure)
    validate_history_succession(closure)
    validate_history_completeness(closure)
    return exact_ref
