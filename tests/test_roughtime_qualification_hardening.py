from __future__ import annotations

import os
from pathlib import Path

import pytest

from forecast_trust_core import _roughtime_qualification_hardening as h
from forecast_trust_core import _roughtime_qualification_vendored as q


def make_wrapper(root: Path) -> Path:
    wrapper = root / "wrapper"
    wrapper.mkdir()
    for name in q.WRAPPER_SOURCE_FILES:
        (wrapper / name).write_text("x\n", encoding="utf-8")
    protocol = wrapper / "pinned" / "roughtime" / "protocol"
    protocol.mkdir(parents=True)
    (wrapper / "pinned" / "roughtime" / "LICENSE").write_text("license\n", encoding="utf-8")
    (wrapper / "pinned" / "roughtime" / "SOURCE_PROVENANCE.json").write_text("{}\n", encoding="utf-8")
    for name in q.PINNED_PROTOCOL_FILES:
        (protocol / name).write_text("package protocol\n", encoding="utf-8")
    return wrapper


def test_tree_allowlist_rejects_extra_compile_input(tmp_path: Path):
    wrapper = make_wrapper(tmp_path)
    h.validate_frozen_wrapper_tree(wrapper)
    (wrapper / "injected.go").write_text("package main\n", encoding="utf-8")
    with pytest.raises(ValueError, match="extra_files"):
        h.validate_frozen_wrapper_tree(wrapper)


def test_tree_allowlist_rejects_symlinked_protocol_dir(tmp_path: Path):
    wrapper = make_wrapper(tmp_path)
    protocol = wrapper / "pinned" / "roughtime" / "protocol"
    external = tmp_path / "external"
    protocol.rename(external)
    try:
        protocol.symlink_to(external, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation is unavailable in this execution environment")
    with pytest.raises(ValueError, match="symlink"):
        h.validate_frozen_wrapper_tree(wrapper)


def test_generated_binary_is_only_allowed_when_explicit(tmp_path: Path):
    wrapper = make_wrapper(tmp_path)
    binary = h.verifier_binary_path(wrapper)
    binary.write_bytes(b"x")
    with pytest.raises(ValueError):
        h.validate_frozen_wrapper_tree(wrapper)
    h.validate_frozen_wrapper_tree(wrapper, allow_generated_binary=True)


def test_hardened_env_drops_unbound_go_inputs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    env = h.hardened_go_env(
        {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(tmp_path),
            "GOAMD64": "v4",
            "GOFLAGS": "-tags=evil",
            "GOEXPERIMENT": "fieldtrack",
            "CC": "/tmp/evil-cc",
        },
        scratch_dir=tmp_path / "scratch",
    )
    assert "GOAMD64" not in env
    assert "CC" not in env
    assert env["GOEXPERIMENT"] == ""
    assert env["GOFLAGS"] == "-mod=readonly -buildvcs=false"
    assert env["CGO_ENABLED"] == "0"
    assert env["HOME"].startswith(str((tmp_path / "scratch").resolve()))


def _write_fake_go(path: Path, body: str) -> None:
    path.write_text("#!/bin/sh\nset -eu\n" + body, encoding="utf-8")
    path.chmod(0o755)


@pytest.mark.skipif(os.name == "nt", reason="POSIX shell fixture is not executable on Windows")
def test_resolve_go_requires_path_binary_to_match_goroot(tmp_path: Path):
    goroot = tmp_path / "goroot"
    bindir = goroot / "bin"
    bindir.mkdir(parents=True)
    real_go = bindir / "go"
    _write_fake_go(real_go, f'if [ "$1" = env ] && [ "$2" = GOROOT ]; then printf "%s\\n" "{goroot}"; exit 0; fi\nexit 2\n')
    wrapper = make_wrapper(tmp_path)
    candidate, resolved_root = h.resolve_pinned_go_binary(wrapper, {"PATH": str(bindir)})
    assert candidate.samefile(real_go)
    assert resolved_root == goroot.resolve()

    shimdir = tmp_path / "shim"
    shimdir.mkdir()
    shim = shimdir / "go"
    _write_fake_go(shim, f'if [ "$1" = env ] && [ "$2" = GOROOT ]; then printf "%s\\n" "{goroot}"; exit 0; fi\nexit 2\n')
    with pytest.raises(ValueError, match="does not match"):
        h.resolve_pinned_go_binary(wrapper, {"PATH": str(shimdir)})


@pytest.mark.skipif(os.name == "nt", reason="POSIX shell fixture is not executable on Windows")
def test_reproducible_build_detects_nondeterminism(tmp_path: Path):
    wrapper = make_wrapper(tmp_path)
    goroot = tmp_path / "goroot2"
    bindir = goroot / "bin"
    bindir.mkdir(parents=True)
    go = bindir / "go"
    counter = tmp_path / "counter"
    _write_fake_go(
        go,
        f'if [ "$1" = build ]; then n=0; [ -f "{counter}" ] && n=$(cat "{counter}"); n=$((n+1)); printf "%s" "$n" > "{counter}"; printf "build%s" "$n" > fpp-roughtime-strict; exit 0; fi\nexit 2\n',
    )
    env = h.hardened_go_env({"PATH": str(bindir) + os.pathsep + os.environ.get("PATH", ""), "HOME": str(tmp_path)}, scratch_dir=tmp_path / "scratch")
    with pytest.raises(ValueError, match="not byte-for-byte reproducible"):
        h.run_reproducible_build(go, wrapper, env, scratch_dir=tmp_path / "scratch-build")
    assert not h.verifier_binary_path(wrapper).exists()


@pytest.mark.skipif(os.name == "nt", reason="POSIX shell fixture is not executable on Windows")
def test_reproducible_build_retains_verified_binary(tmp_path: Path):
    wrapper = make_wrapper(tmp_path)
    goroot = tmp_path / "goroot3"
    bindir = goroot / "bin"
    bindir.mkdir(parents=True)
    go = bindir / "go"
    _write_fake_go(
        go,
        'if [ "$1" = build ]; then printf "stable" > fpp-roughtime-strict; exit 0; fi\nexit 2\n',
    )
    env = h.hardened_go_env(
        {"PATH": str(bindir) + os.pathsep + os.environ.get("PATH", "")},
        scratch_dir=tmp_path / "scratch-stable",
    )
    digest = h.run_reproducible_build(
        go, wrapper, env, scratch_dir=tmp_path / "scratch-build-stable"
    )
    binary = h.verifier_binary_path(wrapper)
    assert binary.read_bytes() == b"stable"
    assert len(digest) == 64


def test_exclusive_json_write_rejects_dangling_symlink(tmp_path: Path):
    output = tmp_path / "profile.json"
    target = tmp_path / "missing-target.json"
    try:
        output.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation is unavailable in this execution environment")
    with pytest.raises(ValueError, match="refusing to overwrite"):
        h.write_new_json_exclusive(output, {"x": 1})
    assert not target.exists()


def test_exclusive_json_write_preserves_existing_file(tmp_path: Path):
    output = tmp_path / "profile.json"
    output.write_text("keep\n", encoding="utf-8")
    with pytest.raises(ValueError, match="refusing to overwrite"):
        h.write_new_json_exclusive(output, {"x": 1})
    assert output.read_text(encoding="utf-8") == "keep\n"
