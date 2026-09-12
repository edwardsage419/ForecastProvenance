from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Mapping

from ._roughtime_qualification_vendored import (
    MAIN_MODULE,
    PINNED_PROTOCOL_FILES,
    WRAPPER_SOURCE_FILES,
    run_checked,
)

_EXPECTED_DIRS = frozenset({
    "pinned",
    "pinned/roughtime",
    "pinned/roughtime/protocol",
})
_EXPECTED_FILES = frozenset(
    set(WRAPPER_SOURCE_FILES)
    | {"pinned/roughtime/LICENSE", "pinned/roughtime/SOURCE_PROVENANCE.json"}
    | {f"pinned/roughtime/protocol/{name}" for name in PINNED_PROTOCOL_FILES}
)
_GENERATED_BINARY = "fpp-roughtime-strict"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_new_json_exclusive(path: Path, value: dict) -> None:
    payload = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        fd = os.open(path, flags, 0o644)
    except FileExistsError as exc:
        raise ValueError(f"refusing to overwrite existing output: {path}") from exc
    ok = False
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        ok = True
    finally:
        if not ok:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass

def validate_frozen_wrapper_tree(wrapper_dir: Path, *, allow_generated_binary: bool = False) -> None:
    root = wrapper_dir.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("wrapper_dir must resolve to a directory")

    expected_files = set(_EXPECTED_FILES)
    if allow_generated_binary:
        expected_files.add(_GENERATED_BINARY)

    seen_dirs: set[str] = set()
    seen_files: set[str] = set()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ValueError(f"wrapper tree contains prohibited symlink: {rel}")
        if stat.S_ISDIR(mode):
            seen_dirs.add(rel)
        elif stat.S_ISREG(mode):
            seen_files.add(rel)
        else:
            raise ValueError(f"wrapper tree contains unsupported special entry: {rel}")

    extra_dirs = sorted(seen_dirs - _EXPECTED_DIRS)
    missing_dirs = sorted(_EXPECTED_DIRS - seen_dirs)
    extra_files = sorted(seen_files - expected_files)
    missing_files = sorted(expected_files - seen_files)
    if extra_dirs or missing_dirs or extra_files or missing_files:
        raise ValueError(
            "wrapper tree allowlist mismatch; "
            f"missing_dirs={missing_dirs} extra_dirs={extra_dirs} "
            f"missing_files={missing_files} extra_files={extra_files}"
        )


def resolve_pinned_go_binary(wrapper_dir: Path, env: Mapping[str, str]) -> tuple[Path, Path]:
    candidate_text = shutil.which("go", path=env.get("PATH"))
    if not candidate_text:
        raise ValueError("go executable was not found on PATH")
    candidate = Path(candidate_text).resolve(strict=True)
    if not candidate.is_file():
        raise ValueError("resolved go executable is not a regular file")

    goroot_text = run_checked([str(candidate), "env", "GOROOT"], cwd=wrapper_dir, env=env).decode().strip()
    if not goroot_text:
        raise ValueError("go env GOROOT returned an empty path")
    goroot = Path(goroot_text).resolve(strict=True)
    expected = (goroot / "bin" / "go").resolve(strict=True)
    try:
        same = candidate.samefile(expected)
    except OSError as exc:
        raise ValueError("unable to compare selected go executable with GOROOT/bin/go") from exc
    if not same:
        raise ValueError("PATH selected go executable does not match GOROOT/bin/go")
    return candidate, goroot


def hardened_go_env(base_env: Mapping[str, str], *, scratch_dir: Path) -> dict[str, str]:
    scratch = scratch_dir.resolve()
    scratch.mkdir(parents=True, exist_ok=True)
    env: dict[str, str] = {}
    if "PATH" in base_env:
        env["PATH"] = base_env["PATH"]
    home = scratch / "home"
    home.mkdir(parents=True, exist_ok=True)
    env["HOME"] = str(home)
    env.update({
        "GOTOOLCHAIN": "local",
        "CGO_ENABLED": "0",
        "GOENV": "off",
        "GOWORK": "off",
        "GO111MODULE": "on",
        "GOFLAGS": "-mod=readonly -buildvcs=false",
        "GOPROXY": "off",
        "GOSUMDB": "off",
        "GOPRIVATE": "",
        "GONOPROXY": "",
        "GONOSUMDB": "",
        "GOINSECURE": "",
        "GOEXPERIMENT": "",
        "GOCACHE": str(scratch / "gocache"),
        "GOMODCACHE": str(scratch / "gomodcache"),
        "TMPDIR": str(scratch / "tmp"),
    })
    Path(env["GOCACHE"]).mkdir(parents=True, exist_ok=True)
    Path(env["GOMODCACHE"]).mkdir(parents=True, exist_ok=True)
    Path(env["TMPDIR"]).mkdir(parents=True, exist_ok=True)
    return env


def verify_main_module_only_with_binary(go_binary: Path, wrapper_dir: Path, env: Mapping[str, str]) -> None:
    modules = run_checked([str(go_binary), "list", "-m", "all"], cwd=wrapper_dir, env=env).decode("utf-8").splitlines()
    modules = [line.strip() for line in modules if line.strip()]
    if modules != [MAIN_MODULE]:
        raise ValueError(f"external Go modules are prohibited: {modules}")


def run_reproducible_build(
    go_binary: Path, wrapper_dir: Path, env: Mapping[str, str], *, scratch_dir: Path
) -> str:
    binary = wrapper_dir / _GENERATED_BINARY
    if os.path.lexists(binary):
        raise ValueError(f"refusing to overwrite existing output: {binary}")

    command = [
        str(go_binary), "build", "-trimpath", "-buildvcs=false", "-ldflags=-buildid=",
        "-o", _GENERATED_BINARY, ".",
    ]
    run_checked(command, cwd=wrapper_dir, env=env)
    if not binary.is_file() or binary.is_symlink():
        raise ValueError("first frozen build did not create a regular verifier binary")
    first_hash = _sha256_file(binary)

    scratch_dir.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="fpp-roughtime-strict.first.", dir=str(scratch_dir))
    os.close(fd)
    temp = Path(temp_name)
    temp.unlink()
    success = False
    try:
        os.replace(binary, temp)
        second_env = dict(env)
        second_cache = Path(env["GOCACHE"]).parent / "gocache-second-build"
        second_cache.mkdir(parents=True, exist_ok=True)
        second_env["GOCACHE"] = str(second_cache)
        run_checked(command, cwd=wrapper_dir, env=second_env)
        if not binary.is_file() or binary.is_symlink():
            raise ValueError("second frozen build did not create a regular verifier binary")
        second_hash = _sha256_file(binary)
        if first_hash != second_hash or temp.read_bytes() != binary.read_bytes():
            raise ValueError("frozen verifier build is not byte-for-byte reproducible")
        success = True
        return second_hash
    finally:
        try:
            temp.unlink()
        except FileNotFoundError:
            pass
        if not success:
            try:
                binary.unlink()
            except FileNotFoundError:
                pass
