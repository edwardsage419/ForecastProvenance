from __future__ import annotations

import base64
import hashlib
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any, Mapping

from .canonical import canonical_json, parse_json_strict
from ._roughtime_profile import PROVIDERS, VERIFIER_COMMIT, VERIFIER_REPOSITORY, VERIFIER_TAG

VERIFIER_TAG_OBJECT_SHA = "e1ae332e5920429b11ec4f10a7dda399ebeb6df8"
BUILD_COMMAND = "go build -trimpath -buildvcs=false -ldflags=-buildid= -o fpp-roughtime-strict ."
RETRY_STATE_SCHEMA_VERSION = "1.0"
BUILD_PROFILE_SCHEMA_VERSION = "1.2"
RETRY_STATE_OBJECT_TYPE = "RoughtimeRetryState"
RETRY_STATE_CLASSIFICATION = "CONTROL_STATE_NON_TIME_EVIDENCE"
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
GO127_RE = re.compile(r"^go1\.27\.\d+$")

_BUILD_PROFILE_KEYS = frozenset({
    "schema_version",
    "upstream_repository",
    "upstream_tag",
    "upstream_commit",
    "upstream_tag_object_sha",
    "upstream_tag_signature_verified",
    "go_version",
    "goos",
    "goarch",
    "go_toolchain_tree_sha256",
    "go_toolchain_distribution_source",
    "go_toolchain_distribution_sha256",
    "go_toolchain_carrier_sha256",
    "cgo_enabled",
    "dependency_lock_sha256",
    "wrapper_source_tree_sha256",
    "upstream_source_tree_sha256",
    "verifier_source_bundle_sha256",
    "build_command",
    "binary_sha256",
    "fixture_report_sha256",
    "profile_sha256",
})

_RETRY_STATE_KEYS = frozenset({
    "schema_version",
    "object_type",
    "classification",
    "prospective_eligible",
    "root_states",
    "state_sha256",
})
_ROOT_STATE_KEYS = frozenset({
    "root_public_key_sha256",
    "consecutive_failures",
    "last_failure_unix_ms",
    "next_eligible_unix_ms",
})


def _require_exact_keys(value: Mapping[str, Any], keys: frozenset[str], name: str) -> None:
    actual = frozenset(value.keys())
    if actual != keys:
        missing = sorted(keys - actual)
        extra = sorted(actual - keys)
        raise ValueError(f"{name} keys invalid; missing={missing} extra={extra}")


def _require_hex64(value: Any, name: str) -> str:
    if not isinstance(value, str) or HEX64_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be 64 lowercase hex characters")
    return value


def _self_hash(value: Mapping[str, Any], field: str) -> str:
    core = dict(value)
    core.pop(field, None)
    return hashlib.sha256(canonical_json(core)).hexdigest()


def load_strict_json_file(path: Path) -> dict[str, Any]:
    obj = parse_json_strict(path.read_bytes())
    if not isinstance(obj, dict):
        raise ValueError(f"{path}: top-level JSON value must be an object")
    return obj


def expected_root_hashes() -> tuple[str, ...]:
    out: list[str] = []
    for provider in PROVIDERS:
        raw = base64.b64decode(provider.root_public_key_base64, validate=True)
        if len(raw) != 32:
            raise ValueError(f"frozen root for {provider.provider_id} is not 32 bytes")
        out.append(hashlib.sha256(raw).hexdigest())
    return tuple(sorted(out))


def make_initial_retry_state() -> dict[str, Any]:
    core: dict[str, Any] = {
        "schema_version": RETRY_STATE_SCHEMA_VERSION,
        "object_type": RETRY_STATE_OBJECT_TYPE,
        "classification": RETRY_STATE_CLASSIFICATION,
        "prospective_eligible": False,
        "root_states": [
            {
                "root_public_key_sha256": digest,
                "consecutive_failures": 0,
                "last_failure_unix_ms": 0,
                "next_eligible_unix_ms": 0,
            }
            for digest in expected_root_hashes()
        ],
    }
    state = dict(core)
    state["state_sha256"] = hashlib.sha256(canonical_json(core)).hexdigest()
    validate_retry_state(state)
    return state


def validate_retry_state(state: Mapping[str, Any]) -> str:
    if not isinstance(state, Mapping):
        raise ValueError("retry state must be an object")
    _require_exact_keys(state, _RETRY_STATE_KEYS, "retry state")
    if state["schema_version"] != RETRY_STATE_SCHEMA_VERSION:
        raise ValueError("retry state schema_version mismatch")
    if state["object_type"] != RETRY_STATE_OBJECT_TYPE:
        raise ValueError("retry state object_type mismatch")
    if state["classification"] != RETRY_STATE_CLASSIFICATION:
        raise ValueError("retry state classification mismatch")
    if state["prospective_eligible"] is not False:
        raise ValueError("retry state prospective_eligible must be false")
    root_states = state["root_states"]
    if not isinstance(root_states, list) or len(root_states) != 3:
        raise ValueError("retry state must contain exactly three root states")
    seen: list[str] = []
    for index, item in enumerate(root_states):
        if not isinstance(item, Mapping):
            raise ValueError(f"root_states[{index}] must be an object")
        _require_exact_keys(item, _ROOT_STATE_KEYS, f"root_states[{index}]")
        root_hash = _require_hex64(item["root_public_key_sha256"], f"root_states[{index}].root_public_key_sha256")
        seen.append(root_hash)
        for field in ("consecutive_failures", "last_failure_unix_ms", "next_eligible_unix_ms"):
            value = item[field]
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise ValueError(f"root_states[{index}].{field} must be a nonnegative integer")
        if item["consecutive_failures"] == 0:
            if item["last_failure_unix_ms"] != 0 or item["next_eligible_unix_ms"] != 0:
                raise ValueError("zero-failure root state must have zero timestamps")
        elif item["next_eligible_unix_ms"] <= item["last_failure_unix_ms"]:
            raise ValueError("failed root state must have next_eligible_unix_ms after last_failure_unix_ms")
    if tuple(sorted(seen)) != expected_root_hashes() or len(set(seen)) != 3:
        raise ValueError("retry state root set does not match the frozen provider roots")
    supplied = _require_hex64(state["state_sha256"], "state_sha256")
    computed = _self_hash(state, "state_sha256")
    if supplied != computed:
        raise ValueError("retry state content hash mismatch")
    return computed


def backoff_delay_ms(consecutive_failures: int) -> int:
    if not isinstance(consecutive_failures, int) or isinstance(consecutive_failures, bool) or consecutive_failures < 1:
        raise ValueError("consecutive_failures must be a positive integer")
    # Frozen schedule: 1s * 1.5^(n-1), rounded upward to an integer millisecond,
    # saturating at 24 hours. Avoid enormous exponentiation for corrupt input.
    if consecutive_failures >= 30:
        return 86_400_000
    value = math.ceil(1000 * (1.5 ** (consecutive_failures - 1)))
    return min(value, 86_400_000)


def record_failure(state: Mapping[str, Any], root_public_key_sha256: str, now_unix_ms: int) -> dict[str, Any]:
    validate_retry_state(state)
    if not isinstance(now_unix_ms, int) or isinstance(now_unix_ms, bool) or now_unix_ms < 0:
        raise ValueError("now_unix_ms must be a nonnegative integer")
    target = _require_hex64(root_public_key_sha256, "root_public_key_sha256")
    core = {k: v for k, v in state.items() if k != "state_sha256"}
    roots = [dict(item) for item in core["root_states"]]
    found = False
    for item in roots:
        if item["root_public_key_sha256"] != target:
            continue
        found = True
        if now_unix_ms < item["next_eligible_unix_ms"]:
            raise ValueError("cannot record network failure while protocol backoff is active")
        failures = item["consecutive_failures"] + 1
        item["consecutive_failures"] = failures
        item["last_failure_unix_ms"] = now_unix_ms
        item["next_eligible_unix_ms"] = now_unix_ms + backoff_delay_ms(failures)
        break
    if not found:
        raise ValueError("root is outside the frozen provider root set")
    core["root_states"] = roots
    updated = dict(core)
    updated["state_sha256"] = hashlib.sha256(canonical_json(core)).hexdigest()
    validate_retry_state(updated)
    return updated


def reset_root_state(state: Mapping[str, Any], root_public_key_sha256: str) -> dict[str, Any]:
    validate_retry_state(state)
    target = _require_hex64(root_public_key_sha256, "root_public_key_sha256")
    core = {k: v for k, v in state.items() if k != "state_sha256"}
    roots = [dict(item) for item in core["root_states"]]
    found = False
    for item in roots:
        if item["root_public_key_sha256"] == target:
            found = True
            item["consecutive_failures"] = 0
            item["last_failure_unix_ms"] = 0
            item["next_eligible_unix_ms"] = 0
            break
    if not found:
        raise ValueError("root is outside the frozen provider root set")
    core["root_states"] = roots
    updated = dict(core)
    updated["state_sha256"] = hashlib.sha256(canonical_json(core)).hexdigest()
    validate_retry_state(updated)
    return updated


def write_retry_state_atomic(path: Path, state: Mapping[str, Any]) -> None:
    validate_retry_state(state)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = canonical_json(dict(state)) + b"\n"
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def write_retry_snapshot(snapshot_dir: Path, state: Mapping[str, Any]) -> Path:
    digest = validate_retry_state(state)
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    target = snapshot_dir / f"{digest}.json"
    payload = canonical_json(dict(state)) + b"\n"
    if target.exists():
        if target.read_bytes() != payload:
            raise ValueError("existing retry-state snapshot bytes do not match content address")
        return target
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(target, flags, 0o644)
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    return target


def compute_source_bundle_sha256(upstream_source_tree_sha256: str, wrapper_source_tree_sha256: str) -> str:
    upstream = bytes.fromhex(_require_hex64(upstream_source_tree_sha256, "upstream_source_tree_sha256"))
    wrapper = bytes.fromhex(_require_hex64(wrapper_source_tree_sha256, "wrapper_source_tree_sha256"))
    return hashlib.sha256(upstream + wrapper).hexdigest()


def validate_verifier_build_profile(profile: Mapping[str, Any]) -> str:
    if not isinstance(profile, Mapping):
        raise ValueError("verifier build profile must be an object")
    _require_exact_keys(profile, _BUILD_PROFILE_KEYS, "verifier build profile")
    if profile["schema_version"] != BUILD_PROFILE_SCHEMA_VERSION:
        raise ValueError("verifier build profile schema_version mismatch")
    expected = {
        "upstream_repository": VERIFIER_REPOSITORY,
        "upstream_tag": VERIFIER_TAG,
        "upstream_commit": VERIFIER_COMMIT,
        "upstream_tag_object_sha": VERIFIER_TAG_OBJECT_SHA,
        "upstream_tag_signature_verified": True,
        "cgo_enabled": False,
        "build_command": BUILD_COMMAND,
    }
    for key, value in expected.items():
        if profile[key] != value:
            raise ValueError(f"verifier build profile {key} mismatch")
    if not isinstance(profile["go_version"], str) or GO127_RE.fullmatch(profile["go_version"]) is None:
        raise ValueError("go_version must be an exact go1.27.x patch release")
    for field in ("goos", "goarch"):
        if not isinstance(profile[field], str) or not profile[field] or any(ch.isspace() for ch in profile[field]):
            raise ValueError(f"{field} must be a nonempty token")
    source = profile["go_toolchain_distribution_source"]
    if not isinstance(source, str) or not source.strip() or "\n" in source or "\r" in source:
        raise ValueError("go_toolchain_distribution_source must be a nonempty single-line string")
    for field in (
        "go_toolchain_tree_sha256",
        "go_toolchain_distribution_sha256",
        "go_toolchain_carrier_sha256",
        "dependency_lock_sha256",
        "wrapper_source_tree_sha256",
        "upstream_source_tree_sha256",
        "verifier_source_bundle_sha256",
        "binary_sha256",
        "fixture_report_sha256",
        "profile_sha256",
    ):
        _require_hex64(profile[field], field)
    expected_bundle = compute_source_bundle_sha256(
        profile["upstream_source_tree_sha256"], profile["wrapper_source_tree_sha256"]
    )
    if profile["verifier_source_bundle_sha256"] != expected_bundle:
        raise ValueError("verifier_source_bundle_sha256 mismatch")
    computed = _self_hash(profile, "profile_sha256")
    if profile["profile_sha256"] != computed:
        raise ValueError("verifier build profile content hash mismatch")
    return computed


def validate_control_binding(plan: Mapping[str, Any], profile: Mapping[str, Any], retry_state: Mapping[str, Any]) -> None:
    profile_hash = validate_verifier_build_profile(profile)
    retry_hash = validate_retry_state(retry_state)
    if plan.get("verifier_build_profile_sha256") != profile_hash:
        raise ValueError("plan verifier_build_profile_sha256 does not match retained build profile")
    if plan.get("retry_state_snapshot_sha256") != retry_hash:
        raise ValueError("plan retry_state_snapshot_sha256 does not match retained retry state")


def validate_authorization_control_binding(
    authorization: Mapping[str, Any],
    plan: Mapping[str, Any],
    profile: Mapping[str, Any],
    retry_state: Mapping[str, Any],
) -> None:
    validate_control_binding(plan, profile, retry_state)
    if authorization.get("verifier_build_profile_sha256") != profile["profile_sha256"]:
        raise ValueError("authorization build profile hash mismatch")
    if authorization.get("retry_state_snapshot_sha256") != retry_state["state_sha256"]:
        raise ValueError("authorization retry state hash mismatch")


def validate_report_control_binding(
    report: Mapping[str, Any],
    plan: Mapping[str, Any],
    authorization: Mapping[str, Any],
    profile: Mapping[str, Any],
    retry_state_before: Mapping[str, Any],
    retry_state_after: Mapping[str, Any],
) -> None:
    validate_authorization_control_binding(authorization, plan, profile, retry_state_before)
    before_hash = validate_retry_state(retry_state_before)
    after_hash = validate_retry_state(retry_state_after)
    if report.get("verifier_build_profile_sha256") != profile["profile_sha256"]:
        raise ValueError("report build profile hash mismatch")
    if report.get("retry_state_before_sha256") != before_hash:
        raise ValueError("report retry_state_before_sha256 mismatch")
    if report.get("retry_state_after_sha256") != after_hash:
        raise ValueError("report retry_state_after_sha256 mismatch")
    source_hash = profile["verifier_source_bundle_sha256"]
    binary_hash = profile["binary_sha256"]
    results = report.get("provider_results")
    if not isinstance(results, list):
        raise ValueError("report provider_results must be a list")
    for result in results:
        if not isinstance(result, Mapping):
            raise ValueError("provider result must be an object")
        receipt = result.get("receipt")
        if receipt is None:
            continue
        if not isinstance(receipt, Mapping):
            raise ValueError("receipt must be an object")
        if receipt.get("verifier_source_sha256") != source_hash:
            raise ValueError("receipt verifier_source_sha256 does not match build profile")
        if receipt.get("verifier_binary_sha256") != binary_hash:
            raise ValueError("receipt verifier_binary_sha256 does not match build profile")
