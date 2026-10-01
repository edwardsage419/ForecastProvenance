from __future__ import annotations

import hashlib
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any, Mapping

from forecast_trust_core.canonical import canonical_json, parse_json_strict
from forecast_trust_core._roughtime_control import (
    BUILD_COMMAND,
    VERIFIER_TAG_OBJECT_SHA,
    compute_source_bundle_sha256,
    validate_verifier_build_profile,
)
from forecast_trust_core._roughtime_profile import VERIFIER_COMMIT, VERIFIER_REPOSITORY, VERIFIER_TAG

DEPENDENCY_LOCK_SCHEMA_VERSION = "1.0"
DEPENDENCY_LOCK_OBJECT_TYPE = "RoughtimeVerifierDependencyLock"
FIXTURE_REPORT_SCHEMA_VERSION = "1.0"
FIXTURE_REPORT_OBJECT_TYPE = "RoughtimeVerifierFixtureReport"
FIXTURE_COMMAND = "go test -count=1 -json ./..."
MAIN_MODULE = "forecastprovenance/roughtime_strict_verifier"
GO127_RE = re.compile(r"^go1\.27\.\d+$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
H1_RE = re.compile(r"^h1:[A-Za-z0-9+/]{43}=$")

WRAPPER_SOURCE_FILES = (
    "adapter_go127.go",
    "adapter_go127_test.go",
    "adapter_pre127.go",
    "core.go",
    "core_test.go",
    "go.mod",
    "main.go",
)

REQUIRED_FIXTURE_TESTS = frozenset(
    {
        "TestFrozenProviderPool",
        "TestStrictJSONRejectsUnknownAndTrailing",
        "TestValidateInputRejectsUppercaseNonce",
        "TestValidateInputRejectsUnknownProvider",
        "TestBuildInputRejectsEvidenceFields",
        "TestVerifyInputRequiresBothPackets",
        "TestStandardPacketGuard",
        "TestRefuseOutputOverwrite",
        "TestGo127TypedHashFirstFixtures",
        "TestGo127TypedNodeFirstFixture",
        "TestGo127UntypedDraft12Fixture",
        "TestGo127RejectsWrongRoot",
        "TestGo127RejectsMutatedResponse",
        "TestGo127RejectsWrongNonce",
        "TestGo127RejectsPacketAndTypeProfileMismatch",
    }
)

_DEPENDENCY_LOCK_KEYS = frozenset(
    {
        "schema_version",
        "object_type",
        "go_mod_sha256",
        "go_sum_sha256",
        "upstream_module_sum",
        "upstream_go_mod_sum",
        "modules",
        "lock_sha256",
    }
)
_MODULE_KEYS = frozenset({"path", "version"})
_FIXTURE_REPORT_KEYS = frozenset(
    {
        "schema_version",
        "object_type",
        "network_used",
        "module_verify_passed",
        "go_version",
        "goos",
        "goarch",
        "go_toolchain_tree_sha256",
        "cgo_enabled",
        "command",
        "wrapper_source_tree_sha256",
        "tests",
        "overall",
        "report_sha256",
    }
)
_TEST_RESULT_KEYS = frozenset({"name", "result"})


def _exact_keys(value: Mapping[str, Any], expected: frozenset[str], name: str) -> None:
    actual = frozenset(value.keys())
    if actual != expected:
        raise ValueError(f"{name} keys invalid; missing={sorted(expected - actual)} extra={sorted(actual - expected)}")


def _hex64(value: Any, name: str) -> str:
    if not isinstance(value, str) or HEX64_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be 64 lowercase hex characters")
    return value


def _h1(value: Any, name: str) -> str:
    if not isinstance(value, str) or H1_RE.fullmatch(value) is None:
        raise ValueError(f"{name} must be a Go h1 checksum")
    return value


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _self_hash(value: Mapping[str, Any], field: str) -> str:
    core = dict(value)
    core.pop(field, None)
    return _sha256(canonical_json(core))


def strict_json_file(path: Path) -> dict[str, Any]:
    value = parse_json_strict(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return value


def compute_wrapper_source_tree_sha256(wrapper_dir: Path) -> str:
    manifest: list[dict[str, str]] = []
    for name in WRAPPER_SOURCE_FILES:
        path = wrapper_dir / name
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"wrapper source missing regular file: {name}")
        manifest.append({"path": name, "sha256": _sha256(path.read_bytes())})
    return _sha256(canonical_json(manifest))


def compute_directory_tree_sha256(root: Path) -> str:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError(f"toolchain root is not a directory: {root}")
    manifest: list[dict[str, str]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix()
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


def parse_module_graph(text: str) -> list[dict[str, str]]:
    modules: list[dict[str, str]] = []
    seen: set[str] = set()
    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        parts = line.split("\t")
        if len(parts) != 3 or not parts[0] or not parts[1] or not parts[2]:
            raise ValueError(f"module graph line {line_number} must be PATH<TAB>VERSION<TAB>REPLACEMENT")
        path, version, replacement = parts
        if any(ch.isspace() for ch in path) or any(ch.isspace() for ch in version):
            raise ValueError(f"module graph line {line_number} contains whitespace in path/version token")
        if replacement != "NONE":
            raise ValueError(f"module replacement is prohibited: {path} -> {replacement}")
        if path in seen:
            raise ValueError(f"duplicate module path: {path}")
        seen.add(path)
        modules.append({"path": path, "version": version})
    modules.sort(key=lambda item: item["path"])
    main = [item for item in modules if item["version"] == "MAIN"]
    if main != [{"path": MAIN_MODULE, "version": "MAIN"}]:
        raise ValueError("module graph must contain exactly the frozen main module marked MAIN")
    upstream = [item for item in modules if item["path"] == VERIFIER_REPOSITORY]
    if upstream != [{"path": VERIFIER_REPOSITORY, "version": VERIFIER_TAG}]:
        raise ValueError("module graph must resolve the frozen upstream module at the frozen tag")
    return modules

def upstream_sums_from_go_sum(go_sum: bytes) -> tuple[str, str]:
    try:
        text = go_sum.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("go.sum must be UTF-8") from exc
    module_key = f"{VERIFIER_REPOSITORY} {VERIFIER_TAG}"
    mod_key = f"{module_key}/go.mod"
    module_sums: list[str] = []
    mod_sums: list[str] = []
    for raw in text.splitlines():
        parts = raw.split()
        if len(parts) != 3:
            continue
        key = f"{parts[0]} {parts[1]}"
        if key == module_key:
            module_sums.append(parts[2])
        elif key == mod_key:
            mod_sums.append(parts[2])
    if len(module_sums) != 1 or len(mod_sums) != 1:
        raise ValueError("go.sum must contain exactly one pinned upstream module and go.mod checksum")
    return _h1(module_sums[0], "upstream_module_sum"), _h1(mod_sums[0], "upstream_go_mod_sum")


def make_dependency_lock(go_mod: bytes, go_sum: bytes, module_graph_text: str) -> dict[str, Any]:
    if not go_mod or not go_sum:
        raise ValueError("go.mod and go.sum must both be nonempty")
    upstream_module_sum, upstream_go_mod_sum = upstream_sums_from_go_sum(go_sum)
    core: dict[str, Any] = {
        "schema_version": DEPENDENCY_LOCK_SCHEMA_VERSION,
        "object_type": DEPENDENCY_LOCK_OBJECT_TYPE,
        "go_mod_sha256": _sha256(go_mod),
        "go_sum_sha256": _sha256(go_sum),
        "upstream_module_sum": upstream_module_sum,
        "upstream_go_mod_sum": upstream_go_mod_sum,
        "modules": parse_module_graph(module_graph_text),
    }
    lock = dict(core)
    lock["lock_sha256"] = _sha256(canonical_json(core))
    validate_dependency_lock(lock)
    return lock


def validate_dependency_lock(lock: Mapping[str, Any]) -> str:
    if not isinstance(lock, Mapping):
        raise ValueError("dependency lock must be an object")
    _exact_keys(lock, _DEPENDENCY_LOCK_KEYS, "dependency lock")
    if lock["schema_version"] != DEPENDENCY_LOCK_SCHEMA_VERSION:
        raise ValueError("dependency lock schema_version mismatch")
    if lock["object_type"] != DEPENDENCY_LOCK_OBJECT_TYPE:
        raise ValueError("dependency lock object_type mismatch")
    _hex64(lock["go_mod_sha256"], "go_mod_sha256")
    _hex64(lock["go_sum_sha256"], "go_sum_sha256")
    _h1(lock["upstream_module_sum"], "upstream_module_sum")
    _h1(lock["upstream_go_mod_sum"], "upstream_go_mod_sum")
    modules = lock["modules"]
    if not isinstance(modules, list) or not modules:
        raise ValueError("dependency lock modules must be a nonempty array")
    paths: list[str] = []
    for index, item in enumerate(modules):
        if not isinstance(item, Mapping):
            raise ValueError(f"modules[{index}] must be an object")
        _exact_keys(item, _MODULE_KEYS, f"modules[{index}]")
        path, version = item["path"], item["version"]
        if not isinstance(path, str) or not path or any(ch.isspace() for ch in path):
            raise ValueError(f"modules[{index}].path invalid")
        if not isinstance(version, str) or not version or any(ch.isspace() for ch in version):
            raise ValueError(f"modules[{index}].version invalid")
        paths.append(path)
    if paths != sorted(paths) or len(set(paths)) != len(paths):
        raise ValueError("dependency lock modules must be unique and sorted by path")
    main = [dict(item) for item in modules if item["version"] == "MAIN"]
    if main != [{"path": MAIN_MODULE, "version": "MAIN"}]:
        raise ValueError("dependency lock main module mismatch")
    upstream = [dict(item) for item in modules if item["path"] == VERIFIER_REPOSITORY]
    if upstream != [{"path": VERIFIER_REPOSITORY, "version": VERIFIER_TAG}]:
        raise ValueError("dependency lock frozen upstream module mismatch")
    supplied = _hex64(lock["lock_sha256"], "lock_sha256")
    computed = _self_hash(lock, "lock_sha256")
    if supplied != computed:
        raise ValueError("dependency lock content hash mismatch")
    return computed


def validate_dependency_lock_material(lock: Mapping[str, Any], go_mod: bytes, go_sum: bytes, module_graph_text: str) -> None:
    validate_dependency_lock(lock)
    recomputed = make_dependency_lock(go_mod, go_sum, module_graph_text)
    if dict(lock) != recomputed:
        raise ValueError("dependency lock does not match current go.mod, go.sum, and module graph")


def parse_module_download_json(data: bytes, dependency_lock: Mapping[str, Any]) -> Path:
    value = parse_json_strict(data)
    if not isinstance(value, dict):
        raise ValueError("go mod download JSON must be an object")
    if value.get("Path") != VERIFIER_REPOSITORY or value.get("Version") != VERIFIER_TAG:
        raise ValueError("go mod download did not resolve the frozen upstream module")
    if value.get("Sum") != dependency_lock.get("upstream_module_sum"):
        raise ValueError("go mod download module checksum does not match dependency lock")
    if value.get("GoModSum") != dependency_lock.get("upstream_go_mod_sum"):
        raise ValueError("go mod download go.mod checksum does not match dependency lock")
    zip_path = value.get("Zip")
    if not isinstance(zip_path, str) or not zip_path:
        raise ValueError("go mod download JSON missing Zip path")
    path = Path(zip_path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("resolved upstream module Zip is not a regular file")
    return path


def parse_go_test_json(data: bytes) -> tuple[list[dict[str, str]], bool]:
    passed: set[str] = set()
    failed: set[str] = set()
    skipped: set[str] = set()
    package_pass = False
    for line_number, raw in enumerate(data.splitlines(), 1):
        if not raw.strip():
            continue
        event = parse_json_strict(raw)
        if not isinstance(event, dict):
            raise ValueError(f"go test JSON line {line_number} is not an object")
        action = event.get("Action")
        test = event.get("Test")
        if test is None:
            if action == "pass":
                package_pass = True
            elif action == "fail":
                package_pass = False
            continue
        if not isinstance(test, str) or not test.startswith("Test"):
            continue
        if action == "pass":
            passed.add(test)
        elif action == "fail":
            failed.add(test)
        elif action == "skip":
            skipped.add(test)
    bad = sorted(failed | skipped)
    if bad:
        raise ValueError(f"fixture tests failed or skipped: {bad}")
    missing = sorted(REQUIRED_FIXTURE_TESTS - passed)
    if missing:
        raise ValueError(f"required fixture tests missing PASS events: {missing}")
    tests = [{"name": name, "result": "PASS"} for name in sorted(passed)]
    return tests, package_pass


def make_fixture_report(
    go_test_json: bytes,
    *,
    go_version: str,
    goos: str,
    goarch: str,
    go_toolchain_tree_sha256: str,
    wrapper_source_tree_sha256: str,
) -> dict[str, Any]:
    if GO127_RE.fullmatch(go_version) is None:
        raise ValueError("fixture report go_version must be exact go1.27.x")
    for value, name in ((goos, "goos"), (goarch, "goarch")):
        if not value or any(ch.isspace() for ch in value):
            raise ValueError(f"fixture report {name} invalid")
    _hex64(go_toolchain_tree_sha256, "go_toolchain_tree_sha256")
    _hex64(wrapper_source_tree_sha256, "wrapper_source_tree_sha256")
    tests, package_pass = parse_go_test_json(go_test_json)
    if not package_pass:
        raise ValueError("go test package did not finish with PASS")
    core: dict[str, Any] = {
        "schema_version": FIXTURE_REPORT_SCHEMA_VERSION,
        "object_type": FIXTURE_REPORT_OBJECT_TYPE,
        "network_used": False,
        "module_verify_passed": True,
        "go_version": go_version,
        "goos": goos,
        "goarch": goarch,
        "go_toolchain_tree_sha256": go_toolchain_tree_sha256,
        "cgo_enabled": False,
        "command": FIXTURE_COMMAND,
        "wrapper_source_tree_sha256": wrapper_source_tree_sha256,
        "tests": tests,
        "overall": "PASS",
    }
    report = dict(core)
    report["report_sha256"] = _sha256(canonical_json(core))
    validate_fixture_report(report)
    return report


def validate_fixture_report(report: Mapping[str, Any]) -> str:
    if not isinstance(report, Mapping):
        raise ValueError("fixture report must be an object")
    _exact_keys(report, _FIXTURE_REPORT_KEYS, "fixture report")
    if report["schema_version"] != FIXTURE_REPORT_SCHEMA_VERSION:
        raise ValueError("fixture report schema_version mismatch")
    if report["object_type"] != FIXTURE_REPORT_OBJECT_TYPE:
        raise ValueError("fixture report object_type mismatch")
    if report["network_used"] is not False or report["module_verify_passed"] is not True or report["cgo_enabled"] is not False:
        raise ValueError("fixture report control booleans mismatch")
    if not isinstance(report["go_version"], str) or GO127_RE.fullmatch(report["go_version"]) is None:
        raise ValueError("fixture report go_version must be exact go1.27.x")
    for field in ("goos", "goarch"):
        value = report[field]
        if not isinstance(value, str) or not value or any(ch.isspace() for ch in value):
            raise ValueError(f"fixture report {field} invalid")
    if report["command"] != FIXTURE_COMMAND:
        raise ValueError("fixture report command mismatch")
    _hex64(report["go_toolchain_tree_sha256"], "go_toolchain_tree_sha256")
    _hex64(report["wrapper_source_tree_sha256"], "wrapper_source_tree_sha256")
    if report["overall"] != "PASS":
        raise ValueError("fixture report overall must be PASS")
    tests = report["tests"]
    if not isinstance(tests, list) or not tests:
        raise ValueError("fixture report tests must be nonempty")
    names: list[str] = []
    for index, item in enumerate(tests):
        if not isinstance(item, Mapping):
            raise ValueError(f"tests[{index}] must be an object")
        _exact_keys(item, _TEST_RESULT_KEYS, f"tests[{index}]")
        if item["result"] != "PASS" or not isinstance(item["name"], str) or not item["name"].startswith("Test"):
            raise ValueError(f"tests[{index}] invalid")
        names.append(item["name"])
    if names != sorted(names) or len(set(names)) != len(names):
        raise ValueError("fixture report tests must be unique and sorted")
    if not REQUIRED_FIXTURE_TESTS.issubset(names):
        raise ValueError("fixture report missing required tests")
    supplied = _hex64(report["report_sha256"], "report_sha256")
    computed = _self_hash(report, "report_sha256")
    if supplied != computed:
        raise ValueError("fixture report content hash mismatch")
    return computed


def make_verifier_build_profile(
    *,
    dependency_lock: Mapping[str, Any],
    fixture_report: Mapping[str, Any],
    wrapper_dir: Path,
    upstream_source_archive: Path,
    binary: Path,
    go_version: str,
    goos: str,
    goarch: str,
    go_toolchain_tree_sha256: str,
) -> dict[str, Any]:
    dependency_hash = validate_dependency_lock(dependency_lock)
    fixture_hash = validate_fixture_report(fixture_report)
    wrapper_hash = compute_wrapper_source_tree_sha256(wrapper_dir)
    _hex64(go_toolchain_tree_sha256, "go_toolchain_tree_sha256")
    if fixture_report["wrapper_source_tree_sha256"] != wrapper_hash:
        raise ValueError("fixture report wrapper source tree does not match current wrapper")
    if fixture_report["go_toolchain_tree_sha256"] != go_toolchain_tree_sha256:
        raise ValueError("fixture report toolchain tree does not match build toolchain")
    if fixture_report["go_version"] != go_version or fixture_report["goos"] != goos or fixture_report["goarch"] != goarch:
        raise ValueError("fixture report toolchain environment does not match build profile")
    if not upstream_source_archive.is_file() or upstream_source_archive.is_symlink():
        raise ValueError("upstream source archive must be a regular file")
    if not binary.is_file() or binary.is_symlink():
        raise ValueError("verifier binary must be a regular file")
    upstream_hash = _sha256(upstream_source_archive.read_bytes())
    core: dict[str, Any] = {
        "schema_version": "1.1",
        "upstream_repository": VERIFIER_REPOSITORY,
        "upstream_tag": VERIFIER_TAG,
        "upstream_commit": VERIFIER_COMMIT,
        "upstream_tag_object_sha": VERIFIER_TAG_OBJECT_SHA,
        "upstream_tag_signature_verified": True,
        "go_version": go_version,
        "goos": goos,
        "goarch": goarch,
        "go_toolchain_tree_sha256": go_toolchain_tree_sha256,
        "cgo_enabled": False,
        "dependency_lock_sha256": dependency_hash,
        "wrapper_source_tree_sha256": wrapper_hash,
        "upstream_source_archive_sha256": upstream_hash,
        "verifier_source_bundle_sha256": compute_source_bundle_sha256(upstream_hash, wrapper_hash),
        "build_command": BUILD_COMMAND,
        "binary_sha256": _sha256(binary.read_bytes()),
        "fixture_report_sha256": fixture_hash,
    }
    profile = dict(core)
    profile["profile_sha256"] = _sha256(canonical_json(core))
    validate_verifier_build_profile(profile)
    return profile


def run_checked(command: list[str], *, cwd: Path, env: Mapping[str, str]) -> bytes:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=dict(env),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace")
        raise RuntimeError(f"command failed ({completed.returncode}): {' '.join(command)}\n{stderr}")
    return completed.stdout


def base_go_env() -> dict[str, str]:
    env = dict(os.environ)
    env.update(
        {
            "GOTOOLCHAIN": "local",
            "CGO_ENABLED": "0",
            "GOENV": "off",
            "GOWORK": "off",
            "GO111MODULE": "on",
            "GOFLAGS": "",
            "GOPROXY": "https://proxy.golang.org,direct",
            "GOSUMDB": "sum.golang.org",
            "GOPRIVATE": "",
            "GONOPROXY": "",
            "GONOSUMDB": "",
            "GOINSECURE": "",
        }
    )
    return env


def offline_go_env() -> dict[str, str]:
    env = base_go_env()
    env.update({"GOFLAGS": "-mod=readonly", "GOPROXY": "off", "GOSUMDB": "off"})
    return env


def module_graph_command() -> list[str]:
    template = "{{.Path}}\t{{if .Main}}MAIN{{else}}{{.Version}}{{end}}\t{{if .Replace}}{{.Replace.Path}}@{{.Replace.Version}}{{else}}NONE{{end}}"
    return ["go", "list", "-m", "-f", template, "all"]


def upstream_download_command() -> list[str]:
    return ["go", "mod", "download", "-json", f"{VERIFIER_REPOSITORY}@{VERIFIER_TAG}"]
