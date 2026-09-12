from __future__ import annotations

import json
from pathlib import Path

import pytest

from forecast_trust_core._roughtime_qualification import (
    MAIN_MODULE,
    REQUIRED_FIXTURE_TESTS,
    WRAPPER_SOURCE_FILES,
    compute_directory_tree_sha256,
    compute_wrapper_source_tree_sha256,
    make_dependency_lock,
    make_fixture_report,
    make_verifier_build_profile,
    offline_go_env,
    parse_module_download_json,
    parse_module_graph,
    validate_dependency_lock,
    validate_dependency_lock_material,
    validate_fixture_report,
)

UPSTREAM_MODULE_SUM = "h1:" + "A" * 43 + "="
UPSTREAM_GOMOD_SUM = "h1:" + "B" * 43 + "="


def graph_text() -> str:
    return "\n".join(
        [
            f"{MAIN_MODULE}\tMAIN\tNONE",
            "github.com/tannerryan/roughtime\tv1.27.0\tNONE",
            "go.uber.org/multierr\tv1.11.0\tNONE",
            "go.uber.org/zap\tv1.28.0\tNONE",
            "golang.org/x/net\tv0.58.0\tNONE",
            "golang.org/x/sys\tv0.47.0\tNONE",
        ]
    ) + "\n"


def go_sum_bytes() -> bytes:
    return (
        f"github.com/tannerryan/roughtime v1.27.0 {UPSTREAM_MODULE_SUM}\n"
        f"github.com/tannerryan/roughtime v1.27.0/go.mod {UPSTREAM_GOMOD_SUM}\n"
        "golang.org/x/sys v0.47.0 h1:" + "C" * 43 + "=\n"
    ).encode()


def go_test_json(*, omit: str | None = None, fail: str | None = None) -> bytes:
    lines: list[str] = []
    for name in sorted(REQUIRED_FIXTURE_TESTS):
        if name == omit:
            continue
        action = "fail" if name == fail else "pass"
        lines.append(json.dumps({"Action": action, "Package": "fixture", "Test": name}))
    lines.append(json.dumps({"Action": "fail" if fail else "pass", "Package": "fixture"}))
    return ("\n".join(lines) + "\n").encode()


def make_wrapper(dir_path: Path) -> None:
    dir_path.mkdir()
    for index, name in enumerate(WRAPPER_SOURCE_FILES):
        (dir_path / name).write_text(f"file {index}: {name}\n", encoding="utf-8")


def test_module_graph_is_sorted_and_marks_main():
    modules = parse_module_graph(graph_text())
    assert modules[0] == {"path": MAIN_MODULE, "version": "MAIN"}
    assert [m["path"] for m in modules] == sorted(m["path"] for m in modules)


def test_module_graph_rejects_duplicate_path():
    with pytest.raises(ValueError):
        parse_module_graph(graph_text() + "golang.org/x/sys\tv0.47.0\tNONE\n")




def test_module_graph_rejects_replacement_and_wrong_upstream_version():
    with pytest.raises(ValueError):
        parse_module_graph(graph_text().replace("github.com/tannerryan/roughtime\tv1.27.0\tNONE", "github.com/tannerryan/roughtime\tv1.27.0\t../local@"))
    with pytest.raises(ValueError):
        parse_module_graph(graph_text().replace("github.com/tannerryan/roughtime\tv1.27.0\tNONE", "github.com/tannerryan/roughtime\tv1.26.0\tNONE"))

def test_dependency_lock_round_trip_and_material_binding():
    go_mod = b"module x\n"
    go_sum = go_sum_bytes()
    lock = make_dependency_lock(go_mod, go_sum, graph_text())
    assert validate_dependency_lock(lock) == lock["lock_sha256"]
    assert lock["upstream_module_sum"] == UPSTREAM_MODULE_SUM
    assert lock["upstream_go_mod_sum"] == UPSTREAM_GOMOD_SUM
    validate_dependency_lock_material(lock, go_mod, go_sum, graph_text())


def test_dependency_lock_rejects_go_sum_drift():
    lock = make_dependency_lock(b"module x\n", go_sum_bytes(), graph_text())
    drift = go_sum_bytes().replace(UPSTREAM_MODULE_SUM.encode(), ("h1:" + "D" * 43 + "=").encode())
    with pytest.raises(ValueError):
        validate_dependency_lock_material(lock, b"module x\n", drift, graph_text())


def test_dependency_lock_rejects_missing_or_duplicate_upstream_sum():
    with pytest.raises(ValueError):
        make_dependency_lock(b"module x\n", b"golang.org/x/sys v0.47.0 h1:" + b"C" * 43 + b"=\n", graph_text())
    duplicated = go_sum_bytes() + f"github.com/tannerryan/roughtime v1.27.0 {UPSTREAM_MODULE_SUM}\n".encode()
    with pytest.raises(ValueError):
        make_dependency_lock(b"module x\n", duplicated, graph_text())


def test_wrapper_source_hash_uses_frozen_source_allowlist(tmp_path: Path):
    wrapper = tmp_path / "wrapper"
    make_wrapper(wrapper)
    first = compute_wrapper_source_tree_sha256(wrapper)
    (wrapper / "generated.bin").write_bytes(b"ignored output")
    assert compute_wrapper_source_tree_sha256(wrapper) == first
    (wrapper / WRAPPER_SOURCE_FILES[0]).write_text("changed\n", encoding="utf-8")
    assert compute_wrapper_source_tree_sha256(wrapper) != first


def test_toolchain_tree_hash_binds_files_and_symlinks(tmp_path: Path):
    root = tmp_path / "goroot"
    root.mkdir()
    (root / "VERSION").write_text("go1.27.1\n", encoding="utf-8")
    bindir = root / "bin"
    bindir.mkdir()
    (bindir / "go").write_bytes(b"go binary")
    (root / "go-link").symlink_to("bin/go")
    first = compute_directory_tree_sha256(root)
    (bindir / "go").write_bytes(b"changed")
    assert compute_directory_tree_sha256(root) != first
    (bindir / "go").write_bytes(b"go binary")
    (root / "go-link").unlink()
    (root / "go-link").symlink_to("VERSION")
    assert compute_directory_tree_sha256(root) != first


def test_module_download_json_binds_sums_and_zip(tmp_path: Path):
    archive = tmp_path / "module.zip"
    archive.write_bytes(b"module zip")
    lock = make_dependency_lock(b"module x\n", go_sum_bytes(), graph_text())
    payload = json.dumps(
        {
            "Path": "github.com/tannerryan/roughtime",
            "Version": "v1.27.0",
            "Sum": UPSTREAM_MODULE_SUM,
            "GoModSum": UPSTREAM_GOMOD_SUM,
            "Zip": str(archive),
        }
    ).encode()
    assert parse_module_download_json(payload, lock) == archive
    bad = json.loads(payload)
    bad["Sum"] = "h1:" + "Z" * 43 + "="
    with pytest.raises(ValueError):
        parse_module_download_json(json.dumps(bad).encode(), lock)


def test_fixture_report_requires_complete_pass_matrix():
    report = make_fixture_report(
        go_test_json(),
        go_version="go1.27.1",
        goos="linux",
        goarch="amd64",
        go_toolchain_tree_sha256="77" * 32,
        wrapper_source_tree_sha256="11" * 32,
    )
    assert validate_fixture_report(report) == report["report_sha256"]
    assert report["network_used"] is False
    assert report["module_verify_passed"] is True


def test_fixture_report_rejects_missing_required_test():
    missing = sorted(REQUIRED_FIXTURE_TESTS)[0]
    with pytest.raises(ValueError):
        make_fixture_report(
            go_test_json(omit=missing),
            go_version="go1.27.1",
            goos="linux",
            goarch="amd64",
            go_toolchain_tree_sha256="77" * 32,
            wrapper_source_tree_sha256="11" * 32,
        )


def test_fixture_report_rejects_failed_test():
    failed = sorted(REQUIRED_FIXTURE_TESTS)[0]
    with pytest.raises(ValueError):
        make_fixture_report(
            go_test_json(fail=failed),
            go_version="go1.27.1",
            goos="linux",
            goarch="amd64",
            go_toolchain_tree_sha256="77" * 32,
            wrapper_source_tree_sha256="11" * 32,
        )


def test_build_profile_cross_binds_lock_fixture_source_archive_binary_and_toolchain(tmp_path: Path):
    wrapper = tmp_path / "wrapper"
    make_wrapper(wrapper)
    wrapper_hash = compute_wrapper_source_tree_sha256(wrapper)
    lock = make_dependency_lock(b"module x\n", go_sum_bytes(), graph_text())
    toolchain_hash = "77" * 32
    report = make_fixture_report(
        go_test_json(),
        go_version="go1.27.1",
        goos="linux",
        goarch="amd64",
        go_toolchain_tree_sha256=toolchain_hash,
        wrapper_source_tree_sha256=wrapper_hash,
    )
    archive = tmp_path / "upstream.zip"
    archive.write_bytes(b"pinned module zip")
    binary = tmp_path / "fpp-roughtime-strict"
    binary.write_bytes(b"binary")
    profile = make_verifier_build_profile(
        dependency_lock=lock,
        fixture_report=report,
        wrapper_dir=wrapper,
        upstream_source_archive=archive,
        binary=binary,
        go_version="go1.27.1",
        goos="linux",
        goarch="amd64",
        go_toolchain_tree_sha256=toolchain_hash,
    )
    assert profile["dependency_lock_sha256"] == lock["lock_sha256"]
    assert profile["fixture_report_sha256"] == report["report_sha256"]
    assert profile["wrapper_source_tree_sha256"] == wrapper_hash
    assert profile["go_toolchain_tree_sha256"] == toolchain_hash


def test_build_profile_rejects_fixture_for_different_wrapper_or_toolchain(tmp_path: Path):
    wrapper = tmp_path / "wrapper"
    make_wrapper(wrapper)
    lock = make_dependency_lock(b"module x\n", go_sum_bytes(), graph_text())
    archive = tmp_path / "upstream.zip"
    archive.write_bytes(b"source")
    binary = tmp_path / "binary"
    binary.write_bytes(b"binary")

    wrong_wrapper = make_fixture_report(
        go_test_json(),
        go_version="go1.27.1",
        goos="linux",
        goarch="amd64",
        go_toolchain_tree_sha256="77" * 32,
        wrapper_source_tree_sha256="11" * 32,
    )
    with pytest.raises(ValueError):
        make_verifier_build_profile(
            dependency_lock=lock,
            fixture_report=wrong_wrapper,
            wrapper_dir=wrapper,
            upstream_source_archive=archive,
            binary=binary,
            go_version="go1.27.1",
            goos="linux",
            goarch="amd64",
            go_toolchain_tree_sha256="77" * 32,
        )

    wrapper_hash = compute_wrapper_source_tree_sha256(wrapper)
    wrong_toolchain = make_fixture_report(
        go_test_json(),
        go_version="go1.27.1",
        goos="linux",
        goarch="amd64",
        go_toolchain_tree_sha256="88" * 32,
        wrapper_source_tree_sha256=wrapper_hash,
    )
    with pytest.raises(ValueError):
        make_verifier_build_profile(
            dependency_lock=lock,
            fixture_report=wrong_toolchain,
            wrapper_dir=wrapper,
            upstream_source_archive=archive,
            binary=binary,
            go_version="go1.27.1",
            goos="linux",
            goarch="amd64",
            go_toolchain_tree_sha256="77" * 32,
        )


def test_offline_go_env_disables_module_network(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOPROXY", "https://proxy.example")
    env = offline_go_env()
    assert env["GOTOOLCHAIN"] == "local"
    assert env["CGO_ENABLED"] == "0"
    assert env["GOENV"] == "off"
    assert env["GOWORK"] == "off"
    assert env["GO111MODULE"] == "on"
    assert env["GOFLAGS"] == "-mod=readonly"
    assert env["GOPROXY"] == "off"
    assert env["GOSUMDB"] == "off"
    assert env["GOPRIVATE"] == ""
    assert env["GONOPROXY"] == ""
    assert env["GONOSUMDB"] == ""
    assert env["GOINSECURE"] == ""
