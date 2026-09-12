from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from forecast_trust_core.canonical import canonical_json
from forecast_trust_core._roughtime_control import (
    BUILD_COMMAND,
    VERIFIER_TAG_OBJECT_SHA,
    backoff_delay_ms,
    compute_source_bundle_sha256,
    expected_root_hashes,
    load_strict_json_file,
    make_initial_retry_state,
    record_failure,
    reset_root_state,
    validate_control_binding,
    validate_report_control_binding,
    validate_retry_state,
    validate_verifier_build_profile,
    write_retry_snapshot,
    write_retry_state_atomic,
)
from forecast_trust_core._roughtime_profile import VERIFIER_COMMIT, VERIFIER_REPOSITORY, VERIFIER_TAG


def profile() -> dict:
    upstream = "11" * 32
    wrapper = "22" * 32
    core = {
        "schema_version": "1.2",
        "upstream_repository": VERIFIER_REPOSITORY,
        "upstream_tag": VERIFIER_TAG,
        "upstream_commit": VERIFIER_COMMIT,
        "upstream_tag_object_sha": VERIFIER_TAG_OBJECT_SHA,
        "upstream_tag_signature_verified": True,
        "go_version": "go1.27.1",
        "goos": "linux",
        "goarch": "amd64",
        "go_toolchain_tree_sha256": "77" * 32,
        "go_toolchain_distribution_source": "actions/go-versions release 1.27.1 linux-x64",
        "go_toolchain_distribution_sha256": "88" * 32,
        "go_toolchain_carrier_sha256": "99" * 32,
        "cgo_enabled": False,
        "dependency_lock_sha256": "33" * 32,
        "wrapper_source_tree_sha256": wrapper,
        "upstream_source_tree_sha256": upstream,
        "verifier_source_bundle_sha256": compute_source_bundle_sha256(upstream, wrapper),
        "build_command": BUILD_COMMAND,
        "binary_sha256": "44" * 32,
        "fixture_report_sha256": "55" * 32,
    }
    out = dict(core)
    out["profile_sha256"] = hashlib.sha256(canonical_json(core)).hexdigest()
    return out


def rehash_state(state: dict) -> dict:
    core = {k: v for k, v in state.items() if k != "state_sha256"}
    state["state_sha256"] = hashlib.sha256(canonical_json(core)).hexdigest()
    return state


def test_initial_retry_state_validates():
    state = make_initial_retry_state()
    assert validate_retry_state(state) == state["state_sha256"]


def test_retry_state_is_keyed_by_exact_frozen_root_set():
    state = make_initial_retry_state()
    assert tuple(sorted(x["root_public_key_sha256"] for x in state["root_states"])) == expected_root_hashes()


def test_retry_state_rejects_duplicate_root():
    state = make_initial_retry_state()
    state["root_states"][1]["root_public_key_sha256"] = state["root_states"][0]["root_public_key_sha256"]
    rehash_state(state)
    with pytest.raises(ValueError):
        validate_retry_state(state)


def test_retry_state_rejects_zero_failure_with_nonzero_clock():
    state = make_initial_retry_state()
    state["root_states"][0]["last_failure_unix_ms"] = 1
    rehash_state(state)
    with pytest.raises(ValueError):
        validate_retry_state(state)


def test_retry_state_rejects_hash_tamper():
    state = make_initial_retry_state()
    state["state_sha256"] = "00" * 32
    with pytest.raises(ValueError):
        validate_retry_state(state)


def test_backoff_first_failure_is_one_second():
    assert backoff_delay_ms(1) == 1000


def test_backoff_second_failure_is_one_point_five_seconds():
    assert backoff_delay_ms(2) == 1500


def test_backoff_saturates_at_one_day():
    assert backoff_delay_ms(1000) == 86_400_000


def test_record_failure_updates_only_selected_root():
    state = make_initial_retry_state()
    root = expected_root_hashes()[0]
    updated = record_failure(state, root, 10_000)
    selected = next(x for x in updated["root_states"] if x["root_public_key_sha256"] == root)
    assert selected["consecutive_failures"] == 1
    assert selected["next_eligible_unix_ms"] == 11_000


def test_record_failure_rejects_active_backoff():
    state = record_failure(make_initial_retry_state(), expected_root_hashes()[0], 10_000)
    with pytest.raises(ValueError):
        record_failure(state, expected_root_hashes()[0], 10_500)


def test_verified_response_reset_clears_backoff():
    root = expected_root_hashes()[0]
    state = record_failure(make_initial_retry_state(), root, 10_000)
    reset = reset_root_state(state, root)
    selected = next(x for x in reset["root_states"] if x["root_public_key_sha256"] == root)
    assert selected["consecutive_failures"] == 0
    assert selected["next_eligible_unix_ms"] == 0


def test_retry_snapshot_is_content_addressed_and_immutable(tmp_path: Path):
    state = make_initial_retry_state()
    first = write_retry_snapshot(tmp_path, state)
    second = write_retry_snapshot(tmp_path, state)
    assert first == second
    assert first.name == state["state_sha256"] + ".json"


def test_retry_state_atomic_write_round_trips(tmp_path: Path):
    state = make_initial_retry_state()
    target = tmp_path / "state.json"
    write_retry_state_atomic(target, state)
    loaded = load_strict_json_file(target)
    assert validate_retry_state(loaded) == state["state_sha256"]


def test_verifier_build_profile_validates():
    value = profile()
    assert validate_verifier_build_profile(value) == value["profile_sha256"]


def test_verifier_build_profile_rejects_wrong_upstream_pin():
    value = profile()
    value["upstream_commit"] = "00" * 20
    with pytest.raises(ValueError):
        validate_verifier_build_profile(value)


def test_verifier_build_profile_rejects_bundle_drift():
    value = profile()
    value["verifier_source_bundle_sha256"] = "66" * 32
    core = {k: v for k, v in value.items() if k != "profile_sha256"}
    value["profile_sha256"] = hashlib.sha256(canonical_json(core)).hexdigest()
    with pytest.raises(ValueError):
        validate_verifier_build_profile(value)


def test_strict_json_rejects_duplicate_keys(tmp_path: Path):
    path = tmp_path / "dup.json"
    path.write_text('{"a":1,"a":2}', encoding="utf-8")
    with pytest.raises(ValueError):
        load_strict_json_file(path)


def test_plan_and_report_bind_actual_control_artifacts():
    p = profile()
    before = make_initial_retry_state()
    after = record_failure(before, expected_root_hashes()[0], 1000)
    plan = {
        "verifier_build_profile_sha256": p["profile_sha256"],
        "retry_state_snapshot_sha256": before["state_sha256"],
    }
    validate_control_binding(plan, p, before)
    auth = {
        "verifier_build_profile_sha256": p["profile_sha256"],
        "retry_state_snapshot_sha256": before["state_sha256"],
    }
    report = {
        "verifier_build_profile_sha256": p["profile_sha256"],
        "retry_state_before_sha256": before["state_sha256"],
        "retry_state_after_sha256": after["state_sha256"],
        "provider_results": [
            {
                "receipt": {
                    "verifier_source_sha256": p["verifier_source_bundle_sha256"],
                    "verifier_binary_sha256": p["binary_sha256"],
                }
            }
        ],
    }
    validate_report_control_binding(report, plan, auth, p, before, after)
