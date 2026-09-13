from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping

from .canonical import canonical_json

SCHEMA_VERSION = "1.0"
OBJECT_TYPE = "Ed25519VerifierBuildProfile"
MAIN_MODULE = "forecastprovenance/ed25519_verify"
SOURCE_FILES = ("go.mod", "main.go", "main_test.go")
REQUIRED_TESTS = (
    "TestDuplicateFieldRejected",
    "TestJSONTagsMatchProtocol",
    "TestMutationsReject",
    "TestNoncanonicalAndWrongLengthBase64Rejected",
    "TestNullAndTrailingDataRejected",
    "TestOversizeRequestRejected",
    "TestRFC8032Vectors",
    "TestRunOutputIsClosedResult",
    "TestStrictRequestRoundTrip",
    "TestUnknownFieldRejected",
)
TEST_COMMAND = "go test -count=1 -json ./..."
BUILD_COMMAND = "go build -trimpath -buildvcs=false -ldflags=-buildid= -o fpp-ed25519-verify.exe ."
GO127_RE = re.compile(r"^go1\.27\.[0-9]+$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
PROFILE_KEYS = frozenset({
    "schema_version", "object_type", "source_files", "source_tree_sha256",
    "main_module", "go_version", "goos", "goarch", "go_toolchain_tree_sha256",
    "go_toolchain_distribution_source", "go_toolchain_distribution_sha256",
    "go_toolchain_carrier_sha256", "cgo_enabled", "network_used",
    "external_modules_used", "test_command", "required_tests", "fixture_tests",
    "build_command", "reproducible_build", "binary_sha256", "profile_sha256",
})
SOURCE_FILE_KEYS = frozenset({"path", "sha256"})
TEST_RESULT_KEYS = frozenset({"name", "result"})


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hex64(value: Any, name: str) -> str:
    if not isinstance(value, str) or HEX64_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be 64 lowercase hex characters")
    return value


def _exact_keys(value: Mapping[str, Any], expected: frozenset[str], name: str) -> None:
    actual = frozenset(value.keys())
    if actual != expected:
        raise ValueError(
            f"{name} keys invalid; missing={sorted(expected - actual)} extra={sorted(actual - expected)}"
        )


def _self_hash(value: Mapping[str, Any], field: str) -> str:
    core = dict(value)
    core.pop(field, None)
    return _sha256(canonical_json(core))


def source_manifest(source_dir: Path) -> list[dict[str, str]]:
    root = source_dir.resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Ed25519 verifier source_dir must be a directory")
    entries: list[dict[str, str]] = []
    for name in SOURCE_FILES:
        path = root / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"Ed25519 verifier source missing regular file: {name}")
        entries.append({"path": name, "sha256": _sha256(path.read_bytes())})
    return entries


def validate_source_tree(source_dir: Path, *, allow_binary: bool = False) -> list[dict[str, str]]:
    root = source_dir.resolve(strict=True)
    expected = set(SOURCE_FILES)
    binary_name = "fpp-ed25519-verify.exe"
    if allow_binary:
        expected.add(binary_name)
    seen: set[str] = set()
    for path in root.iterdir():
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ValueError(f"Ed25519 verifier source tree contains prohibited symlink: {path.name}")
        if not stat.S_ISREG(mode):
            raise ValueError(f"Ed25519 verifier source tree contains unsupported entry: {path.name}")
        seen.add(path.name)
    if seen != expected:
        raise ValueError(
            f"Ed25519 verifier source tree allowlist mismatch; missing={sorted(expected-seen)} extra={sorted(seen-expected)}"
        )
    return source_manifest(root)


def compute_source_tree_sha256(entries: list[dict[str, str]]) -> str:
    if [item.get("path") for item in entries] != list(SOURCE_FILES):
        raise ValueError("Ed25519 verifier source manifest path order mismatch")
    for index, item in enumerate(entries):
        if not isinstance(item, Mapping):
            raise ValueError(f"source_files[{index}] must be an object")
        _exact_keys(item, SOURCE_FILE_KEYS, f"source_files[{index}]")
        _hex64(item["sha256"], f"source_files[{index}].sha256")
    return _sha256(canonical_json(entries))


def parse_go_test_json(data: bytes) -> list[dict[str, str]]:
    passed: set[str] = set()
    failed: set[str] = set()
    skipped: set[str] = set()
    package_pass = False
    package_fail = False
    for line_number, raw in enumerate(data.splitlines(), 1):
        if not raw.strip():
            continue
        def pairs_hook(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            event: dict[str, Any] = {}
            for key, value in pairs:
                if key in event:
                    raise ValueError(f"go test JSON line {line_number} has duplicate key: {key}")
                event[key] = value
            return event
        try:
            event = json.loads(
                raw.decode("utf-8"),
                object_pairs_hook=pairs_hook,
                parse_constant=lambda value: (_ for _ in ()).throw(
                    ValueError(f"non-standard JSON constant: {value}")
                ),
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"invalid go test JSON line {line_number}") from exc
        if not isinstance(event, dict):
            raise ValueError(f"go test JSON line {line_number} is not an object")
        action = event.get("Action")
        test = event.get("Test")
        if action is not None and not isinstance(action, str):
            raise ValueError(f"go test JSON line {line_number} Action is not a string")
        if test is not None and not isinstance(test, str):
            raise ValueError(f"go test JSON line {line_number} Test is not a string")
        if test is None:
            if action == "pass":
                package_pass = True
            elif action == "fail":
                package_fail = True
            continue
        if not test.startswith("Test"):
            continue
        if action == "pass":
            passed.add(test)
        elif action == "fail":
            failed.add(test)
        elif action == "skip":
            skipped.add(test)
    bad = sorted((failed | skipped) & set(REQUIRED_TESTS))
    if bad:
        raise ValueError(f"required Ed25519 verifier tests failed or skipped: {bad}")
    missing = sorted(set(REQUIRED_TESTS) - passed)
    if missing:
        raise ValueError(f"required Ed25519 verifier tests missing PASS events: {missing}")
    if not package_pass or package_fail:
        raise ValueError("Ed25519 verifier go test package did not finish with PASS")
    return [{"name": name, "result": "PASS"} for name in REQUIRED_TESTS]


def compute_directory_tree_sha256(root: Path) -> str:
    resolved = root.resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError("toolchain root must be a directory")
    manifest: list[dict[str, str]] = []
    for path in sorted(resolved.rglob("*"), key=lambda item: item.relative_to(resolved).as_posix()):
        rel = path.relative_to(resolved).as_posix()
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            continue
        if stat.S_ISREG(mode):
            manifest.append({"path": rel, "type": "file", "sha256": _sha256(path.read_bytes())})
        elif stat.S_ISLNK(mode):
            manifest.append({"path": rel, "type": "symlink", "target": os.readlink(path)})
        else:
            raise ValueError(f"toolchain tree contains unsupported special entry: {rel}")
    if not manifest:
        raise ValueError("toolchain tree is empty")
    return _sha256(canonical_json(manifest))


def make_build_profile(
    *,
    source_dir: Path,
    binary: Path,
    go_test_json: bytes,
    go_version: str,
    goos: str,
    goarch: str,
    go_toolchain_tree_sha256: str,
    go_toolchain_distribution_source: str,
    go_toolchain_distribution_sha256: str,
    go_toolchain_carrier_sha256: str,
) -> dict[str, Any]:
    entries = validate_source_tree(source_dir, allow_binary=True)
    if GO127_RE.fullmatch(go_version) is None:
        raise ValueError("Ed25519 verifier qualification requires exact go1.27.x")
    for value, name in ((goos, "goos"), (goarch, "goarch")):
        if not isinstance(value, str) or not value or any(ch.isspace() for ch in value):
            raise ValueError(f"{name} must be a nonempty token")
    for value, name in (
        (go_toolchain_tree_sha256, "go_toolchain_tree_sha256"),
        (go_toolchain_distribution_sha256, "go_toolchain_distribution_sha256"),
        (go_toolchain_carrier_sha256, "go_toolchain_carrier_sha256"),
    ):
        _hex64(value, name)
    if (
        not isinstance(go_toolchain_distribution_source, str)
        or not go_toolchain_distribution_source.strip()
        or "\n" in go_toolchain_distribution_source
        or "\r" in go_toolchain_distribution_source
    ):
        raise ValueError("go_toolchain_distribution_source must be a nonempty single-line string")
    if not binary.is_file() or binary.is_symlink():
        raise ValueError("Ed25519 verifier binary must be a regular file")
    fixture_tests = parse_go_test_json(go_test_json)
    core: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "object_type": OBJECT_TYPE,
        "source_files": entries,
        "source_tree_sha256": compute_source_tree_sha256(entries),
        "main_module": MAIN_MODULE,
        "go_version": go_version,
        "goos": goos,
        "goarch": goarch,
        "go_toolchain_tree_sha256": go_toolchain_tree_sha256,
        "go_toolchain_distribution_source": go_toolchain_distribution_source,
        "go_toolchain_distribution_sha256": go_toolchain_distribution_sha256,
        "go_toolchain_carrier_sha256": go_toolchain_carrier_sha256,
        "cgo_enabled": False,
        "network_used": False,
        "external_modules_used": False,
        "test_command": TEST_COMMAND,
        "required_tests": list(REQUIRED_TESTS),
        "fixture_tests": fixture_tests,
        "build_command": BUILD_COMMAND,
        "reproducible_build": True,
        "binary_sha256": _sha256(binary.read_bytes()),
    }
    profile = dict(core)
    profile["profile_sha256"] = _sha256(canonical_json(core))
    validate_build_profile(profile)
    return profile


def validate_build_profile(profile: Mapping[str, Any]) -> str:
    if not isinstance(profile, Mapping):
        raise ValueError("Ed25519 verifier build profile must be an object")
    _exact_keys(profile, PROFILE_KEYS, "Ed25519 verifier build profile")
    expected = {
        "schema_version": SCHEMA_VERSION,
        "object_type": OBJECT_TYPE,
        "main_module": MAIN_MODULE,
        "cgo_enabled": False,
        "network_used": False,
        "external_modules_used": False,
        "test_command": TEST_COMMAND,
        "build_command": BUILD_COMMAND,
        "reproducible_build": True,
    }
    for key, wanted in expected.items():
        if profile[key] != wanted:
            raise ValueError(f"Ed25519 verifier build profile {key} mismatch")
    if not isinstance(profile["go_version"], str) or GO127_RE.fullmatch(profile["go_version"]) is None:
        raise ValueError("Ed25519 verifier build profile go_version must be exact go1.27.x")
    for field in ("goos", "goarch"):
        value = profile[field]
        if not isinstance(value, str) or not value or any(ch.isspace() for ch in value):
            raise ValueError(f"Ed25519 verifier build profile {field} invalid")
    source_files = profile["source_files"]
    if not isinstance(source_files, list):
        raise ValueError("source_files must be an array")
    computed_source_tree = compute_source_tree_sha256(source_files)
    if profile["source_tree_sha256"] != computed_source_tree:
        raise ValueError("Ed25519 verifier source_tree_sha256 mismatch")
    source = profile["go_toolchain_distribution_source"]
    if not isinstance(source, str) or not source.strip() or "\n" in source or "\r" in source:
        raise ValueError("go_toolchain_distribution_source invalid")
    for field in (
        "go_toolchain_tree_sha256", "go_toolchain_distribution_sha256",
        "go_toolchain_carrier_sha256", "binary_sha256", "profile_sha256",
    ):
        _hex64(profile[field], field)
    if profile["required_tests"] != list(REQUIRED_TESTS):
        raise ValueError("Ed25519 verifier required_tests mismatch")
    tests = profile["fixture_tests"]
    if not isinstance(tests, list) or len(tests) != len(REQUIRED_TESTS):
        raise ValueError("Ed25519 verifier fixture_tests mismatch")
    expected_tests = [{"name": name, "result": "PASS"} for name in REQUIRED_TESTS]
    if tests != expected_tests:
        raise ValueError("Ed25519 verifier fixture_tests must exactly match required PASS set")
    supplied = _hex64(profile["profile_sha256"], "profile_sha256")
    computed = _self_hash(profile, "profile_sha256")
    if supplied != computed:
        raise ValueError("Ed25519 verifier build profile content hash mismatch")
    return computed


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
        "TEMP": str(scratch / "tmp"),
        "TMP": str(scratch / "tmp"),
    })
    for field in ("GOCACHE", "GOMODCACHE", "TMPDIR"):
        Path(env[field]).mkdir(parents=True, exist_ok=True)
    return env


def run_checked(argv: list[str], *, cwd: Path, env: Mapping[str, str]) -> bytes:
    proc = subprocess.run(
        argv, cwd=cwd, env=dict(env), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
    )
    if proc.returncode != 0:
        raise ValueError(
            f"command failed ({proc.returncode}): {' '.join(argv)}\n{proc.stderr.decode(errors='replace')}"
        )
    return proc.stdout


def resolve_pinned_go_binary(source_dir: Path, env: Mapping[str, str]) -> tuple[Path, Path]:
    candidate_text = shutil.which("go", path=env.get("PATH"))
    if not candidate_text:
        raise ValueError("go executable was not found on PATH")
    candidate = Path(candidate_text).resolve(strict=True)
    if not candidate.is_file():
        raise ValueError("resolved go executable is not a regular file")
    goroot_text = run_checked([str(candidate), "env", "GOROOT"], cwd=source_dir, env=env).decode().strip()
    if not goroot_text:
        raise ValueError("go env GOROOT returned an empty path")
    goroot = Path(goroot_text).resolve(strict=True)
    expected_name = "go.exe" if os.name == "nt" else "go"
    expected = (goroot / "bin" / expected_name).resolve(strict=True)
    try:
        same = candidate.samefile(expected)
    except OSError as exc:
        raise ValueError("unable to compare selected go executable with GOROOT/bin/go") from exc
    if not same:
        raise ValueError("PATH selected go executable does not match GOROOT/bin/go")
    return candidate, goroot


def exact_go_env(go_binary: Path, source_dir: Path, expected_goroot: Path, env: Mapping[str, str]) -> tuple[str, str, str]:
    parts = run_checked([str(go_binary), "version"], cwd=source_dir, env=env).decode().strip().split()
    if len(parts) < 4 or GO127_RE.fullmatch(parts[2]) is None:
        raise ValueError("Ed25519 verifier qualification requires an exact Go 1.27.x toolchain")
    goroot = Path(run_checked([str(go_binary), "env", "GOROOT"], cwd=source_dir, env=env).decode().strip()).resolve(strict=True)
    if goroot != expected_goroot:
        raise ValueError("Go GOROOT changed after executable pinning")
    goos = run_checked([str(go_binary), "env", "GOOS"], cwd=source_dir, env=env).decode().strip()
    goarch = run_checked([str(go_binary), "env", "GOARCH"], cwd=source_dir, env=env).decode().strip()
    if not goos or not goarch:
        raise ValueError("Go environment returned invalid GOOS or GOARCH")
    return parts[2], goos, goarch


def verify_main_module_only(go_binary: Path, source_dir: Path, env: Mapping[str, str]) -> None:
    modules = run_checked([str(go_binary), "list", "-m", "all"], cwd=source_dir, env=env).decode().splitlines()
    modules = [line.strip() for line in modules if line.strip()]
    if modules != [MAIN_MODULE]:
        raise ValueError(f"external Go modules are prohibited: {modules}")


def run_reproducible_build(go_binary: Path, source_dir: Path, env: Mapping[str, str], *, scratch_dir: Path) -> Path:
    binary_name = "fpp-ed25519-verify.exe"
    binary = source_dir / binary_name
    if os.path.lexists(binary):
        raise ValueError(f"refusing to overwrite existing Ed25519 verifier binary: {binary}")
    command = [str(go_binary), "build", "-trimpath", "-buildvcs=false", "-ldflags=-buildid=", "-o", binary_name, "."]
    run_checked(command, cwd=source_dir, env=env)
    if not binary.is_file() or binary.is_symlink():
        raise ValueError("first Ed25519 verifier build did not create a regular binary")
    first = binary.read_bytes()
    scratch_dir.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix="fpp-ed25519-verify.first.", dir=str(scratch_dir))
    os.close(fd)
    temp = Path(temp_name)
    temp.write_bytes(first)
    success = False
    try:
        binary.unlink()
        second_env = dict(env)
        second_cache = Path(env["GOCACHE"]).parent / "gocache-second-build"
        second_cache.mkdir(parents=True, exist_ok=True)
        second_env["GOCACHE"] = str(second_cache)
        run_checked(command, cwd=source_dir, env=second_env)
        if not binary.is_file() or binary.is_symlink():
            raise ValueError("second Ed25519 verifier build did not create a regular binary")
        second = binary.read_bytes()
        if first != second:
            raise ValueError("Ed25519 verifier build is not byte-for-byte reproducible")
        success = True
        return binary
    finally:
        temp.unlink(missing_ok=True)
        if not success:
            binary.unlink(missing_ok=True)
