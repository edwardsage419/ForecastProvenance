from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from forecast_trust_core import _roughtime_qualification_vendored as q


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def go_test_json(*, omit: str | None = None, fail: str | None = None) -> bytes:
    lines: list[str] = []
    for name in sorted(q.REQUIRED_FIXTURE_TESTS):
        if name == omit:
            continue
        lines.append(json.dumps({"Action": "fail" if name == fail else "pass", "Package": "fixture", "Test": name}))
    lines.append(json.dumps({"Action": "fail" if fail else "pass", "Package": "fixture", "Elapsed": 0.1}))
    return ("\n".join(lines) + "\n").encode()


def make_wrapper(root: Path) -> Path:
    wrapper = root / "wrapper"
    wrapper.mkdir()
    for index, name in enumerate(q.WRAPPER_SOURCE_FILES):
        (wrapper / name).write_text(f"wrapper {index}: {name}\n", encoding="utf-8")
    protocol = wrapper / "pinned" / "roughtime" / "protocol"
    protocol.mkdir(parents=True)
    files = []
    for index, name in enumerate(q.PINNED_PROTOCOL_FILES):
        data = f"package protocol\n// {index}: {name}\n".encode()
        (protocol / name).write_bytes(data)
        files.append({"path": f"protocol/{name}", "git_blob_sha1": git_blob_sha1(data)})
    provenance = {
        "schema_version": "1.0",
        "object_type": "PinnedRoughtimeProtocolSource",
        "upstream_repository": q.VERIFIER_REPOSITORY,
        "upstream_tag": q.VERIFIER_TAG,
        "upstream_commit": q.VERIFIER_COMMIT,
        "upstream_tag_object_sha": q.VERIFIER_TAG_OBJECT_SHA,
        "upstream_tag_signature_verified": True,
        "source_scope": "protocol package compile inputs only",
        "files": files,
    }
    (wrapper / "pinned" / "roughtime" / "SOURCE_PROVENANCE.json").write_text(json.dumps(provenance), encoding="utf-8")
    return wrapper


def test_dependency_lock_round_trip(tmp_path: Path):
    wrapper = make_wrapper(tmp_path)
    lock = q.make_dependency_lock(wrapper)
    assert q.validate_dependency_lock(lock) == lock["lock_sha256"]
    assert len(lock["files"]) == 12
    q.validate_dependency_lock_material(lock, wrapper)


def test_dependency_lock_rejects_vendored_byte_drift(tmp_path: Path):
    wrapper = make_wrapper(tmp_path)
    lock = q.make_dependency_lock(wrapper)
    (wrapper / "pinned" / "roughtime" / "protocol" / "cert.go").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ValueError):
        q.validate_dependency_lock_material(lock, wrapper)


def test_dependency_lock_rejects_provenance_blob_drift(tmp_path: Path):
    wrapper = make_wrapper(tmp_path)
    provenance_path = wrapper / "pinned" / "roughtime" / "SOURCE_PROVENANCE.json"
    provenance = json.loads(provenance_path.read_text())
    provenance["files"][0]["git_blob_sha1"] = "0" * 40
    provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
    with pytest.raises(ValueError):
        q.make_dependency_lock(wrapper)


def test_wrapper_source_hash_ignores_generated_binary(tmp_path: Path):
    wrapper = make_wrapper(tmp_path)
    first = q.compute_wrapper_source_tree_sha256(wrapper)
    (wrapper / "fpp-roughtime-strict").write_bytes(b"generated")
    assert q.compute_wrapper_source_tree_sha256(wrapper) == first
    (wrapper / q.WRAPPER_SOURCE_FILES[0]).write_text("changed\n", encoding="utf-8")
    assert q.compute_wrapper_source_tree_sha256(wrapper) != first


def test_toolchain_tree_hash_binds_symlink_target(tmp_path: Path):
    root = tmp_path / "goroot"
    root.mkdir()
    (root / "VERSION").write_text("go1.27.1\n", encoding="utf-8")
    (root / "bin").mkdir()
    (root / "bin" / "go").write_bytes(b"go")
    try:
        (root / "link").symlink_to("bin/go")
    except OSError:
        pytest.skip("symlink creation is unavailable in this execution environment")
    first = q.compute_directory_tree_sha256(root)
    (root / "link").unlink()
    (root / "link").symlink_to("VERSION")
    assert q.compute_directory_tree_sha256(root) != first


def test_fixture_report_requires_complete_pass_matrix(tmp_path: Path):
    wrapper = make_wrapper(tmp_path)
    lock = q.make_dependency_lock(wrapper)
    report = q.make_fixture_report(
        go_test_json(),
        go_version="go1.27.1",
        goos="linux",
        goarch="amd64",
        go_toolchain_tree_sha256="77" * 32,
        wrapper_source_tree_sha256=q.compute_wrapper_source_tree_sha256(wrapper),
        upstream_source_tree_sha256=lock["upstream_source_tree_sha256"],
    )
    assert q.validate_fixture_report(report) == report["report_sha256"]
    assert report["network_used"] is False
    assert report["vendored_source_verified"] is True
    assert report["external_modules_used"] is False


def test_fixture_report_rejects_missing_or_failed_required_test(tmp_path: Path):
    wrapper = make_wrapper(tmp_path)
    lock = q.make_dependency_lock(wrapper)
    kwargs = dict(
        go_version="go1.27.1", goos="linux", goarch="amd64",
        go_toolchain_tree_sha256="77" * 32,
        wrapper_source_tree_sha256=q.compute_wrapper_source_tree_sha256(wrapper),
        upstream_source_tree_sha256=lock["upstream_source_tree_sha256"],
    )
    with pytest.raises(ValueError):
        q.make_fixture_report(go_test_json(omit=sorted(q.REQUIRED_FIXTURE_TESTS)[0]), **kwargs)
    with pytest.raises(ValueError):
        q.make_fixture_report(go_test_json(fail=sorted(q.REQUIRED_FIXTURE_TESTS)[0]), **kwargs)


def test_fixture_report_rejects_any_failed_package_even_if_later_package_passes(tmp_path: Path):
    wrapper = make_wrapper(tmp_path)
    lock = q.make_dependency_lock(wrapper)
    lines = [
        json.dumps({"Action": "pass", "Package": "fixture", "Test": name})
        for name in sorted(q.REQUIRED_FIXTURE_TESTS)
    ]
    lines.extend((
        json.dumps({"Action": "fail", "Package": "fixture/failed-package"}),
        json.dumps({"Action": "pass", "Package": "fixture/passing-package"}),
    ))
    with pytest.raises(ValueError, match="package did not finish with PASS"):
        q.make_fixture_report(
            ("\n".join(lines) + "\n").encode(),
            go_version="go1.27.1",
            goos="linux",
            goarch="amd64",
            go_toolchain_tree_sha256="77" * 32,
            wrapper_source_tree_sha256=q.compute_wrapper_source_tree_sha256(wrapper),
            upstream_source_tree_sha256=lock["upstream_source_tree_sha256"],
        )


def test_build_profile_cross_binds_source_and_toolchain(tmp_path: Path):
    wrapper = make_wrapper(tmp_path)
    lock = q.make_dependency_lock(wrapper)
    wrapper_hash = q.compute_wrapper_source_tree_sha256(wrapper)
    toolchain_hash = "77" * 32
    report = q.make_fixture_report(
        go_test_json(), go_version="go1.27.1", goos="linux", goarch="amd64",
        go_toolchain_tree_sha256=toolchain_hash,
        wrapper_source_tree_sha256=wrapper_hash,
        upstream_source_tree_sha256=lock["upstream_source_tree_sha256"],
    )
    binary = wrapper / "fpp-roughtime-strict"
    binary.write_bytes(b"binary")
    profile = q.make_verifier_build_profile(
        dependency_lock=lock, fixture_report=report, wrapper_dir=wrapper, binary=binary,
        go_version="go1.27.1", goos="linux", goarch="amd64",
        go_toolchain_tree_sha256=toolchain_hash,
        go_toolchain_distribution_source="actions/go-versions release 1.27.1 linux-x64",
        go_toolchain_distribution_sha256="88" * 32,
        go_toolchain_carrier_sha256="99" * 32,
    )
    assert profile["schema_version"] == "1.2"
    assert profile["dependency_lock_sha256"] == lock["lock_sha256"]
    assert profile["fixture_report_sha256"] == report["report_sha256"]
    assert profile["binary_sha256"] == hashlib.sha256(b"binary").hexdigest()


def test_offline_go_env_disables_module_network(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GOPROXY", "https://proxy.example")
    env = q.offline_go_env()
    assert env["GOTOOLCHAIN"] == "local"
    assert env["CGO_ENABLED"] == "0"
    assert env["GOENV"] == "off"
    assert env["GOWORK"] == "off"
    assert env["GOFLAGS"] == "-mod=readonly"
    assert env["GOPROXY"] == "off"
    assert env["GOSUMDB"] == "off"
    assert env["GOPRIVATE"] == ""


def test_verify_main_module_only_rejects_external_modules(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(
        q,
        "run_checked",
        lambda *a, **k: b"forecastprovenance/roughtime_strict_verifier\nexample.com/external v1.0.0\n",
    )
    with pytest.raises(ValueError):
        q.verify_main_module_only(tmp_path, {})
