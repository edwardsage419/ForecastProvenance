from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from forecast_trust_core._ed25519_qualification import (
    BUILD_COMMAND,
    MAIN_MODULE,
    REQUIRED_TESTS,
    SOURCE_FILES,
    TEST_COMMAND,
    compute_source_tree_sha256,
    make_build_profile,
    parse_go_test_json,
    source_manifest,
    validate_build_profile,
    validate_repository_binding,
)


def _source_dir(tmp_path: Path) -> Path:
    root = tmp_path / "src"
    root.mkdir()
    for name in SOURCE_FILES:
        (root / name).write_text(f"{name}\n", encoding="utf-8")
    return root


def _go_test_json(*, omit: str | None = None) -> bytes:
    events = []
    for name in REQUIRED_TESTS:
        if name != omit:
            events.append({"Action": "pass", "Test": name})
    events.append({"Action": "pass", "Package": MAIN_MODULE})
    return b"\n".join(json.dumps(item).encode() for item in events) + b"\n"


def test_source_manifest_is_closed_and_content_addressed(tmp_path: Path) -> None:
    root = _source_dir(tmp_path)
    manifest = source_manifest(root)
    assert [item["path"] for item in manifest] == list(SOURCE_FILES)
    assert compute_source_tree_sha256(manifest) == hashlib.sha256(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_required_go_test_pass_set_is_exact() -> None:
    parsed = parse_go_test_json(_go_test_json())
    assert parsed == [{"name": name, "result": "PASS"} for name in REQUIRED_TESTS]
    with pytest.raises(ValueError, match="missing PASS"):
        parse_go_test_json(_go_test_json(omit=REQUIRED_TESTS[0]))


def test_build_profile_binds_source_tests_toolchain_and_binary(tmp_path: Path) -> None:
    root = _source_dir(tmp_path)
    binary = root / "fpp-ed25519-verify.exe"
    binary.write_bytes(b"binary")
    profile = make_build_profile(
        source_dir=root,
        repository_commit_sha="a" * 40,
        binary=binary,
        go_test_json=_go_test_json(),
        go_version="go1.27.1",
        goos="linux",
        goarch="amd64",
        go_toolchain_tree_sha256="1" * 64,
        go_toolchain_distribution_source="official-go-archive",
        go_toolchain_distribution_sha256="2" * 64,
        go_toolchain_carrier_sha256="3" * 64,
    )
    assert profile["main_module"] == MAIN_MODULE
    assert profile["test_command"] == TEST_COMMAND
    assert profile["build_command"] == BUILD_COMMAND
    assert profile["binary_sha256"] == hashlib.sha256(b"binary").hexdigest()
    assert validate_build_profile(profile) == profile["profile_sha256"]


def test_profile_rejects_non_go127_and_tampering(tmp_path: Path) -> None:
    root = _source_dir(tmp_path)
    binary = root / "fpp-ed25519-verify.exe"
    binary.write_bytes(b"binary")
    with pytest.raises(ValueError, match="go1.27.x"):
        make_build_profile(
            source_dir=root,
            repository_commit_sha="a" * 40,
            binary=binary,
            go_test_json=_go_test_json(),
            go_version="go1.23.2",
            goos="linux",
            goarch="amd64",
            go_toolchain_tree_sha256="1" * 64,
            go_toolchain_distribution_source="official-go-archive",
            go_toolchain_distribution_sha256="2" * 64,
            go_toolchain_carrier_sha256="3" * 64,
        )

def test_repository_binding_requires_exact_committed_source(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    source = root / "scripts" / "genesis" / "ed25519_verify"
    source.mkdir(parents=True)
    for name in SOURCE_FILES:
        (source / name).write_text(f"{name}\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.email", "test@example.invalid"], check=True)
    subprocess.run(["git", "-C", str(root), "config", "user.name", "Test"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
    commit = subprocess.check_output(
        ["git", "-C", str(root), "rev-parse", "HEAD"], text=True
    ).strip()
    assert validate_repository_binding(source) == commit
    (source / "main.go").write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="do not match repository HEAD"):
        validate_repository_binding(source)
