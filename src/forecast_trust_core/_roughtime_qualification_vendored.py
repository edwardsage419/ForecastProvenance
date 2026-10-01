from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any, Mapping

from .canonical import canonical_json, parse_json_strict
from ._roughtime_control import BUILD_COMMAND, VERIFIER_TAG_OBJECT_SHA, compute_source_bundle_sha256, validate_verifier_build_profile
from ._roughtime_profile import VERIFIER_COMMIT, VERIFIER_REPOSITORY, VERIFIER_TAG

DEPENDENCY_LOCK_SCHEMA_VERSION = "1.1"
DEPENDENCY_LOCK_OBJECT_TYPE = "RoughtimeVerifierDependencyLock"
FIXTURE_REPORT_SCHEMA_VERSION = "1.1"
FIXTURE_REPORT_OBJECT_TYPE = "RoughtimeVerifierFixtureReport"
FIXTURE_COMMAND = "go test -count=1 -json ./..."
MAIN_MODULE = "forecastprovenance/roughtime_strict_verifier"
GO127_RE = re.compile(r"^go1\.27\.\d+$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
HEX40_RE = re.compile(r"^[0-9a-f]{40}$")

WRAPPER_SOURCE_FILES = (
    "adapter_go127.go", "adapter_go127_test.go", "adapter_pre127.go",
    "core.go", "core_test.go", "go.mod", "main.go",
)
PINNED_PROTOCOL_FILES = (
    "cert.go", "codec.go", "merkle.go", "protocol.go", "reply.go", "request.go",
    "signature.go", "tags.go", "timestamp.go", "verify.go", "version.go", "wiregroup.go",
)
REQUIRED_FIXTURE_TESTS = frozenset({
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
})

PROVENANCE_KEYS = frozenset({
    "schema_version", "object_type", "upstream_repository", "upstream_tag",
    "upstream_commit", "upstream_tag_object_sha", "upstream_tag_signature_verified",
    "source_scope", "files",
})
PROVENANCE_FILE_KEYS = frozenset({"path", "git_blob_sha1"})
DEPENDENCY_LOCK_KEYS = frozenset({
    "schema_version", "object_type", "upstream_repository", "upstream_tag",
    "upstream_commit", "upstream_tag_object_sha", "upstream_tag_signature_verified",
    "source_scope", "files", "upstream_source_tree_sha256", "lock_sha256",
})
LOCK_FILE_KEYS = frozenset({"path", "git_blob_sha1", "sha256"})
FIXTURE_REPORT_KEYS = frozenset({
    "schema_version", "object_type", "network_used", "vendored_source_verified",
    "external_modules_used", "go_version", "goos", "goarch", "go_toolchain_tree_sha256",
    "cgo_enabled", "command", "wrapper_source_tree_sha256", "upstream_source_tree_sha256",
    "tests", "overall", "report_sha256",
})
TEST_RESULT_KEYS = frozenset({"name", "result"})

def _exact_keys(value: Mapping[str, Any], expected: frozenset[str], name: str) -> None:
    actual = frozenset(value.keys())
    if actual != expected:
        raise ValueError(f"{name} keys invalid; missing={sorted(expected-actual)} extra={sorted(actual-expected)}")

def _hex(value: Any, regex: re.Pattern[str], name: str) -> str:
    if not isinstance(value, str) or regex.fullmatch(value) is None:
        raise ValueError(f"{name} has invalid hexadecimal form")
    return value

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()

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

def _validated_provenance(wrapper_dir: Path) -> dict[str, Any]:
    value = strict_json_file(wrapper_dir / "pinned" / "roughtime" / "SOURCE_PROVENANCE.json")
    _exact_keys(value, PROVENANCE_KEYS, "source provenance")
    expected = {
        "schema_version": "1.0",
        "object_type": "PinnedRoughtimeProtocolSource",
        "upstream_repository": VERIFIER_REPOSITORY,
        "upstream_tag": VERIFIER_TAG,
        "upstream_commit": VERIFIER_COMMIT,
        "upstream_tag_object_sha": VERIFIER_TAG_OBJECT_SHA,
        "upstream_tag_signature_verified": True,
        "source_scope": "protocol package compile inputs only",
    }
    for key, wanted in expected.items():
        if value[key] != wanted:
            raise ValueError(f"source provenance {key} mismatch")
    files = value["files"]
    if not isinstance(files, list):
        raise ValueError("source provenance files must be an array")
    names: list[str] = []
    for index, item in enumerate(files):
        if not isinstance(item, Mapping):
            raise ValueError(f"source provenance files[{index}] must be an object")
        _exact_keys(item, PROVENANCE_FILE_KEYS, f"source provenance files[{index}]")
        path_text = item["path"]
        if not isinstance(path_text, str) or not path_text.startswith("protocol/"):
            raise ValueError("source provenance path invalid")
        names.append(path_text.removeprefix("protocol/"))
        _hex(item["git_blob_sha1"], HEX40_RE, "git_blob_sha1")
    if names != sorted(PINNED_PROTOCOL_FILES):
        raise ValueError("source provenance file set mismatch")
    return value

def make_dependency_lock(wrapper_dir: Path) -> dict[str, Any]:
    provenance = _validated_provenance(wrapper_dir)
    pinned = wrapper_dir / "pinned" / "roughtime"
    entries: list[dict[str, str]] = []
    for item in provenance["files"]:
        rel = item["path"]
        path = pinned / rel
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"vendored source missing regular file: {rel}")
        data = path.read_bytes()
        sha1 = _git_blob_sha1(data)
        if sha1 != item["git_blob_sha1"]:
            raise ValueError(f"vendored source Git blob mismatch: {rel}")
        entries.append({"path": rel, "git_blob_sha1": sha1, "sha256": _sha256(data)})
    entries.sort(key=lambda item: item["path"])
    source_tree = _sha256(canonical_json(entries))
    core: dict[str, Any] = {
        "schema_version": DEPENDENCY_LOCK_SCHEMA_VERSION,
        "object_type": DEPENDENCY_LOCK_OBJECT_TYPE,
        "upstream_repository": VERIFIER_REPOSITORY,
        "upstream_tag": VERIFIER_TAG,
        "upstream_commit": VERIFIER_COMMIT,
        "upstream_tag_object_sha": VERIFIER_TAG_OBJECT_SHA,
        "upstream_tag_signature_verified": True,
        "source_scope": "protocol package compile inputs only",
        "files": entries,
        "upstream_source_tree_sha256": source_tree,
    }
    lock = dict(core)
    lock["lock_sha256"] = _sha256(canonical_json(core))
    validate_dependency_lock(lock)
    return lock

def validate_dependency_lock(lock: Mapping[str, Any]) -> str:
    if not isinstance(lock, Mapping):
        raise ValueError("dependency lock must be an object")
    _exact_keys(lock, DEPENDENCY_LOCK_KEYS, "dependency lock")
    expected = {
        "schema_version": DEPENDENCY_LOCK_SCHEMA_VERSION,
        "object_type": DEPENDENCY_LOCK_OBJECT_TYPE,
        "upstream_repository": VERIFIER_REPOSITORY,
        "upstream_tag": VERIFIER_TAG,
        "upstream_commit": VERIFIER_COMMIT,
        "upstream_tag_object_sha": VERIFIER_TAG_OBJECT_SHA,
        "upstream_tag_signature_verified": True,
        "source_scope": "protocol package compile inputs only",
    }
    for key, wanted in expected.items():
        if lock[key] != wanted:
            raise ValueError(f"dependency lock {key} mismatch")
    files = lock["files"]
    if not isinstance(files, list) or len(files) != len(PINNED_PROTOCOL_FILES):
        raise ValueError("dependency lock files mismatch")
    paths: list[str] = []
    for index, item in enumerate(files):
        if not isinstance(item, Mapping):
            raise ValueError(f"files[{index}] must be an object")
        _exact_keys(item, LOCK_FILE_KEYS, f"files[{index}]")
        path = item["path"]
        if not isinstance(path, str) or not path.startswith("protocol/"):
            raise ValueError(f"files[{index}].path invalid")
        paths.append(path)
        _hex(item["git_blob_sha1"], HEX40_RE, f"files[{index}].git_blob_sha1")
        _hex(item["sha256"], HEX64_RE, f"files[{index}].sha256")
    if paths != sorted(f"protocol/{name}" for name in PINNED_PROTOCOL_FILES):
        raise ValueError("dependency lock paths mismatch")
    source_tree = _sha256(canonical_json([dict(item) for item in files]))
    if lock["upstream_source_tree_sha256"] != source_tree:
        raise ValueError("dependency lock upstream source tree mismatch")
    _hex(lock["upstream_source_tree_sha256"], HEX64_RE, "upstream_source_tree_sha256")
    supplied = _hex(lock["lock_sha256"], HEX64_RE, "lock_sha256")
    computed = _self_hash(lock, "lock_sha256")
    if supplied != computed:
        raise ValueError("dependency lock content hash mismatch")
    return computed

def validate_dependency_lock_material(lock: Mapping[str, Any], wrapper_dir: Path) -> None:
    validate_dependency_lock(lock)
    if dict(lock) != make_dependency_lock(wrapper_dir):
        raise ValueError("dependency lock does not match vendored source bytes")

def parse_go_test_json(data: bytes) -> tuple[list[dict[str, str]], bool]:
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
                raw.decode("utf-8"), object_pairs_hook=pairs_hook,
                parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"non-standard JSON constant: {value}")),
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
    return [{"name": name, "result": "PASS"} for name in sorted(passed)], package_pass and not package_fail

def make_fixture_report(
    go_test_json: bytes, *, go_version: str, goos: str, goarch: str,
    go_toolchain_tree_sha256: str, wrapper_source_tree_sha256: str,
    upstream_source_tree_sha256: str,
) -> dict[str, Any]:
    if GO127_RE.fullmatch(go_version) is None:
        raise ValueError("fixture report go_version must be exact go1.27.x")
    for value, name in ((goos, "goos"), (goarch, "goarch")):
        if not value or any(ch.isspace() for ch in value):
            raise ValueError(f"fixture report {name} invalid")
    for value, name in (
        (go_toolchain_tree_sha256, "go_toolchain_tree_sha256"),
        (wrapper_source_tree_sha256, "wrapper_source_tree_sha256"),
        (upstream_source_tree_sha256, "upstream_source_tree_sha256"),
    ):
        _hex(value, HEX64_RE, name)
    tests, package_pass = parse_go_test_json(go_test_json)
    if not package_pass:
        raise ValueError("go test package did not finish with PASS")
    core: dict[str, Any] = {
        "schema_version": FIXTURE_REPORT_SCHEMA_VERSION,
        "object_type": FIXTURE_REPORT_OBJECT_TYPE,
        "network_used": False,
        "vendored_source_verified": True,
        "external_modules_used": False,
        "go_version": go_version,
        "goos": goos,
        "goarch": goarch,
        "go_toolchain_tree_sha256": go_toolchain_tree_sha256,
        "cgo_enabled": False,
        "command": FIXTURE_COMMAND,
        "wrapper_source_tree_sha256": wrapper_source_tree_sha256,
        "upstream_source_tree_sha256": upstream_source_tree_sha256,
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
    _exact_keys(report, FIXTURE_REPORT_KEYS, "fixture report")
    expected = {
        "schema_version": FIXTURE_REPORT_SCHEMA_VERSION,
        "object_type": FIXTURE_REPORT_OBJECT_TYPE,
        "network_used": False,
        "vendored_source_verified": True,
        "external_modules_used": False,
        "cgo_enabled": False,
        "command": FIXTURE_COMMAND,
        "overall": "PASS",
    }
    for key, wanted in expected.items():
        if report[key] != wanted:
            raise ValueError(f"fixture report {key} mismatch")
    if not isinstance(report["go_version"], str) or GO127_RE.fullmatch(report["go_version"]) is None:
        raise ValueError("fixture report go_version must be exact go1.27.x")
    for field in ("goos", "goarch"):
        value = report[field]
        if not isinstance(value, str) or not value or any(ch.isspace() for ch in value):
            raise ValueError(f"fixture report {field} invalid")
    for field in ("go_toolchain_tree_sha256", "wrapper_source_tree_sha256", "upstream_source_tree_sha256"):
        _hex(report[field], HEX64_RE, field)
    tests = report["tests"]
    if not isinstance(tests, list) or not tests:
        raise ValueError("fixture report tests must be nonempty")
    names: list[str] = []
    for index, item in enumerate(tests):
        if not isinstance(item, Mapping):
            raise ValueError(f"tests[{index}] must be an object")
        _exact_keys(item, TEST_RESULT_KEYS, f"tests[{index}]")
        if item["result"] != "PASS" or not isinstance(item["name"], str) or not item["name"].startswith("Test"):
            raise ValueError(f"tests[{index}] invalid")
        names.append(item["name"])
    if names != sorted(names) or len(set(names)) != len(names):
        raise ValueError("fixture report tests must be unique and sorted")
    if not REQUIRED_FIXTURE_TESTS.issubset(names):
        raise ValueError("fixture report missing required tests")
    supplied = _hex(report["report_sha256"], HEX64_RE, "report_sha256")
    computed = _self_hash(report, "report_sha256")
    if supplied != computed:
        raise ValueError("fixture report content hash mismatch")
    return computed

def make_verifier_build_profile(
    *, dependency_lock: Mapping[str, Any], fixture_report: Mapping[str, Any],
    wrapper_dir: Path, binary: Path, go_version: str, goos: str, goarch: str,
    go_toolchain_tree_sha256: str, go_toolchain_distribution_source: str,
    go_toolchain_distribution_sha256: str, go_toolchain_carrier_sha256: str,
) -> dict[str, Any]:
    dependency_hash = validate_dependency_lock(dependency_lock)
    fixture_hash = validate_fixture_report(fixture_report)
    wrapper_hash = compute_wrapper_source_tree_sha256(wrapper_dir)
    source_tree = dependency_lock["upstream_source_tree_sha256"]
    for value, name in (
        (go_toolchain_tree_sha256, "go_toolchain_tree_sha256"),
        (go_toolchain_distribution_sha256, "go_toolchain_distribution_sha256"),
        (go_toolchain_carrier_sha256, "go_toolchain_carrier_sha256"),
    ):
        _hex(value, HEX64_RE, name)
    if not isinstance(go_toolchain_distribution_source, str) or not go_toolchain_distribution_source.strip() or "\n" in go_toolchain_distribution_source:
        raise ValueError("go_toolchain_distribution_source invalid")
    if fixture_report["wrapper_source_tree_sha256"] != wrapper_hash:
        raise ValueError("fixture report wrapper source tree does not match current wrapper")
    if fixture_report["upstream_source_tree_sha256"] != source_tree:
        raise ValueError("fixture report upstream source tree does not match dependency lock")
    if fixture_report["go_toolchain_tree_sha256"] != go_toolchain_tree_sha256:
        raise ValueError("fixture report toolchain tree does not match build toolchain")
    if fixture_report["go_version"] != go_version or fixture_report["goos"] != goos or fixture_report["goarch"] != goarch:
        raise ValueError("fixture report toolchain environment does not match build profile")
    if not binary.is_file() or binary.is_symlink():
        raise ValueError("verifier binary must be a regular file")
    core: dict[str, Any] = {
        "schema_version": "1.2",
        "upstream_repository": VERIFIER_REPOSITORY,
        "upstream_tag": VERIFIER_TAG,
        "upstream_commit": VERIFIER_COMMIT,
        "upstream_tag_object_sha": VERIFIER_TAG_OBJECT_SHA,
        "upstream_tag_signature_verified": True,
        "go_version": go_version,
        "goos": goos,
        "goarch": goarch,
        "go_toolchain_tree_sha256": go_toolchain_tree_sha256,
        "go_toolchain_distribution_source": go_toolchain_distribution_source,
        "go_toolchain_distribution_sha256": go_toolchain_distribution_sha256,
        "go_toolchain_carrier_sha256": go_toolchain_carrier_sha256,
        "cgo_enabled": False,
        "dependency_lock_sha256": dependency_hash,
        "wrapper_source_tree_sha256": wrapper_hash,
        "upstream_source_tree_sha256": source_tree,
        "verifier_source_bundle_sha256": compute_source_bundle_sha256(source_tree, wrapper_hash),
        "build_command": BUILD_COMMAND,
        "binary_sha256": _sha256(binary.read_bytes()),
        "fixture_report_sha256": fixture_hash,
    }
    profile = dict(core)
    profile["profile_sha256"] = _sha256(canonical_json(core))
    validate_verifier_build_profile(profile)
    return profile

def offline_go_env() -> dict[str, str]:
    env = dict(os.environ)
    env.update({
        "GOTOOLCHAIN": "local", "CGO_ENABLED": "0", "GOENV": "off", "GOWORK": "off",
        "GO111MODULE": "on", "GOFLAGS": "-mod=readonly", "GOPROXY": "off", "GOSUMDB": "off",
        "GOPRIVATE": "", "GONOPROXY": "", "GONOSUMDB": "", "GOINSECURE": "",
    })
    return env

def run_checked(argv: list[str], *, cwd: Path, env: Mapping[str, str]) -> bytes:
    proc = subprocess.run(argv, cwd=cwd, env=dict(env), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode != 0:
        raise ValueError(f"command failed ({proc.returncode}): {' '.join(argv)}\n{proc.stderr.decode(errors='replace')}")
    return proc.stdout

def verify_main_module_only(wrapper_dir: Path, env: Mapping[str, str]) -> None:
    modules = run_checked(["go", "list", "-m", "all"], cwd=wrapper_dir, env=env).decode("utf-8").splitlines()
    modules = [line.strip() for line in modules if line.strip()]
    if modules != [MAIN_MODULE]:
        raise ValueError(f"external Go modules are prohibited: {modules}")
