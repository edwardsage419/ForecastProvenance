#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import tomllib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

PINNED_PYTEST = "9.0.2"
PINNED_JSONSCHEMA = "4.26.0"
PINNED_TEST_DEPENDENCIES = ["pytest==9.0.2", "jsonschema==4.26.0"]

REQUIRED_SUCCESSOR_MODULES = (
    "forecast_trust_core.architecture_compression_v1",
    "forecast_trust_core.architecture_compression_v1_hardening",
    "forecast_trust_core.claim_authority_v1",
    "forecast_trust_core.claim_authority_trust_root_v1",
    "forecast_trust_core.production_receipt_admission_v1",
)

CANDIDATE_TESTS = (
    "tests/test_genesis_candidate_objects.py",
    "tests/test_genesis_candidate_patch.py",
    "tests/test_genesis_candidate_patch_v06.py",
    "tests/test_genesis_materializer.py",
    "tests/test_genesis_fixture_manifest.py",
    "tests/test_genesis_fixture_validation.py",
)

CLAIM_AUTHORITY_TESTS = (
    "tests/test_architecture_compression_p5.py",
    "tests/test_architecture_compression_p5_hardening.py",
    "tests/test_claim_authority_v1.py",
    "tests/test_claim_authority_trust_root_v1.py",
    "tests/test_claim_authority_qualification_root_v1.py",
)

PROVIDER_AUTHORITY_TESTS = (
    "tests/test_production_receipt_admission_v1.py",
    "tests/test_roughtime_execution.py",
    "tests/test_roughtime_production_qualification.py",
    "tests/test_roughtime_production_qualification_hardening.py",
    "tests/test_ed25519_qualification.py",
    "tests/test_ed25519_verifier.py",
)

ADVERSARIAL_TESTS = (
    "tests/test_adversarial_registry.py",
    "tests/test_adversarial_execution.py",
    "tests/test_full_adversarial_matrix.py",
)


class P6EnvironmentIneligible(RuntimeError):
    """Execution environment cannot start the frozen P6 test program."""


class P6Failure(RuntimeError):
    """Frozen P6 execution encountered a repository correctness/security failure."""


def run_quiet(command: list[str], cwd: Path, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if completed.returncode != 0:
        raise P6Failure(
            f"command failed before report initialization: {shlex.join(command)}\n"
            f"{completed.stdout}"
        )
    return completed.stdout.strip()


def strict_json_load(path: Path) -> object:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON object key: {key}")
            result[key] = value
        return result

    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=reject_duplicates)


def junit_counts(path: Path) -> dict[str, int]:
    root = ET.parse(path).getroot()
    testcases = root.findall(".//testcase")
    failures = root.findall(".//failure")
    errors = root.findall(".//error")
    skipped = root.findall(".//skipped")
    return {
        "tests": len(testcases),
        "failures": len(failures),
        "errors": len(errors),
        "skipped": len(skipped),
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the complete offline GEN_001 Architecture Compression P6 regression."
    )
    parser.add_argument("expected_head", help="Exact frozen 40 lowercase hex P6 input commit")
    parser.add_argument("outdir", type=Path, help="Evidence output directory outside the repository")
    args = parser.parse_args()

    if not re.fullmatch(r"[0-9a-f]{40}", args.expected_head):
        raise SystemExit("expected_head must be exactly 40 lowercase hexadecimal characters")
    if os.name != "posix":
        raise SystemExit("P6 requires a POSIX execution environment so mandatory security tests are not skipped")

    git = shutil.which("git")
    go = shutil.which("go")
    if git is None:
        raise SystemExit("git is required")
    if go is None:
        raise SystemExit("Go is required")

    provisional_root = Path(
        run_quiet([git, "rev-parse", "--show-toplevel"], Path.cwd())
    ).resolve()
    head = run_quiet([git, "rev-parse", "HEAD"], provisional_root)
    if head != args.expected_head:
        raise SystemExit(
            f"local HEAD {head} differs from frozen P6 input {args.expected_head}"
        )

    status = run_quiet(
        [git, "status", "--porcelain=v1", "--untracked-files=all"], provisional_root
    )
    if status:
        raise SystemExit("P6 requires a completely clean working tree, including no untracked files")

    repo_root = provisional_root
    outdir = args.outdir.expanduser().resolve()
    if outdir == repo_root or outdir.is_relative_to(repo_root):
        raise SystemExit("P6 evidence outdir must be outside the repository working tree")

    outdir.mkdir(parents=True, exist_ok=False)
    report = outdir / "p6_regression_report.txt"
    sidecar = outdir / "p6_regression_report.txt.sha256"

    log_handle = report.open("w", encoding="utf-8", newline="\n")
    failed = False
    environment_ineligible = False
    failure_reason = ""

    def log(line: str = "") -> None:
        print(line, file=log_handle, flush=True)

    def record_command(
        label: str,
        command: list[str],
        *,
        cwd: Path = repo_root,
        env: dict[str, str] | None = None,
    ) -> None:
        log()
        log(f"== {label} ==")
        log(f"cwd={cwd}")
        log(f"command={shlex.join(command)}")
        log_handle.flush()

        process = subprocess.Popen(
            command,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        assert process.stdout is not None
        for line in process.stdout:
            log_handle.write(line)
            log_handle.flush()
            sys.stdout.write(line)
            sys.stdout.flush()
        returncode = process.wait()
        log(f"exit_status={returncode}")
        if returncode != 0:
            raise P6Failure(f"{label} failed with exit status {returncode}")

    def require_zero_skip_junit(label: str, junit_path: Path) -> None:
        counts = junit_counts(junit_path)
        log(
            f"{label}_junit="
            f"tests:{counts['tests']},failures:{counts['failures']},"
            f"errors:{counts['errors']},skipped:{counts['skipped']}"
        )
        if counts["tests"] <= 0:
            raise P6Failure(f"{label} collected no tests")
        if counts["failures"] or counts["errors"]:
            raise P6Failure(f"{label} JUnit report contains failure or error")
        if counts["skipped"]:
            raise P6Failure(
                f"{label} contains an unexpected skip after environment preflight"
            )

    def pytest_suite(
        label: str,
        paths: Iterable[str],
        *,
        extra: Iterable[str] = (),
    ) -> None:
        junit_path = outdir / f"{label}.xml"
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-ra",
            *extra,
            *paths,
            f"--junitxml={junit_path}",
        ]
        record_command(label, command, env=test_env)
        require_zero_skip_junit(label, junit_path)

    try:
        log("classification=NON_FORECAST_VALIDATION_REPORT")
        log("prospective_eligible=false")
        log("purpose=GEN_001_ARCHITECTURE_COMPRESSION_P6_OFFLINE_REGRESSION")
        log(f"captured_utc={datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
        log(f"repository_root={repo_root}")
        log(f"frozen_git_commit={args.expected_head}")
        log(f"local_git_commit={head}")
        log("working_tree_clean=true")
        log("platform=" + platform.platform())
        log("os_name=" + os.name)
        log("python_executable=" + sys.executable)
        log("python_version=" + platform.python_version())

        if sys.version_info < (3, 11):
            raise P6EnvironmentIneligible("Python 3.11 or newer is required")

        pytest_version = importlib.metadata.version("pytest")
        jsonschema_version = importlib.metadata.version("jsonschema")
        log(f"pytest_version={pytest_version}")
        log(f"jsonschema_version={jsonschema_version}")
        if pytest_version != PINNED_PYTEST:
            raise P6EnvironmentIneligible(
                f"pytest version {pytest_version} differs from pin {PINNED_PYTEST}"
            )
        if jsonschema_version != PINNED_JSONSCHEMA:
            raise P6EnvironmentIneligible(
                f"jsonschema version {jsonschema_version} differs from pin {PINNED_JSONSCHEMA}"
            )

        pyproject = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
        declared_runtime = pyproject["project"].get("dependencies", [])
        declared_test = pyproject["project"]["optional-dependencies"]["test"]
        log(
            "declared_runtime_dependencies="
            + json.dumps(declared_runtime, separators=(",", ":"))
        )
        log(
            "declared_test_dependencies="
            + json.dumps(declared_test, separators=(",", ":"))
        )
        if declared_runtime != []:
            raise P6Failure(
                "declared runtime dependency set differs from the frozen P6 expectation"
            )
        if declared_test != PINNED_TEST_DEPENDENCIES:
            raise P6Failure(
                "declared test dependency set differs from the frozen P6 expectation"
            )

        go_version = run_quiet([go, "version"], repo_root)
        log(f"go_version={go_version}")
        go_match = re.search(r"\bgo1\.27(?:\.\d+)?\b", go_version)
        if go_match is None:
            raise P6EnvironmentIneligible(
                "P6 requires a local Go 1.27.x toolchain for the strict Roughtime verifier"
            )

        bash = shutil.which("bash")
        openssl = shutil.which("openssl")
        if bash is None:
            raise P6EnvironmentIneligible("bash is required for retained POSIX script regression")
        if openssl is None:
            raise P6EnvironmentIneligible(
                "OpenSSL is required so PKI integration coverage is executed rather than skipped"
            )
        log("bash_executable=" + bash)
        log("bash_version=" + run_quiet([bash, "--version"], repo_root).splitlines()[0])
        log("openssl_executable=" + openssl)
        log("openssl_version=" + run_quiet([openssl, "version"], repo_root))

        try:
            with tempfile.TemporaryDirectory(prefix="fpp-p6-symlink-") as tmpdir:
                tmp_root = Path(tmpdir)
                target = tmp_root / "target.txt"
                link = tmp_root / "link.txt"
                target.write_text("p6-symlink-preflight\n", encoding="utf-8")
                link.symlink_to(target)
                if not link.is_symlink() or link.resolve() != target.resolve():
                    raise OSError("created symlink did not resolve to its target")
        except (OSError, NotImplementedError) as exc:
            raise P6EnvironmentIneligible(
                f"symlink capability is required for fail-closed state-store regression: {exc}"
            ) from exc
        log("symlink_capability=PASS")
        log("environment_preflight=PASS")
        log("P6_EXECUTION_STARTED=YES")

        src_path = str(repo_root / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        test_env = os.environ.copy()
        test_env["PYTHONPATH"] = src_path
        test_env["FPP_NETWORK_AUTHORIZED"] = "false"
        test_env["OPENSSL_EXECUTABLE"] = openssl

        go_env = test_env.copy()
        go_env.update(
            {
                "GOTOOLCHAIN": "local",
                "CGO_ENABLED": "0",
                "GOENV": "off",
                "GOWORK": "off",
                "GOPROXY": "off",
                "GOSUMDB": "off",
            }
        )

        record_command(
            "python_compileall",
            [sys.executable, "-m", "compileall", "-q", "src", "scripts", "tests"],
            env=test_env,
        )

        log()
        log("== python_import_surface ==")
        package_dir = repo_root / "src" / "forecast_trust_core"
        module_names = {"forecast_trust_core"}
        for path in sorted(package_dir.glob("*.py")):
            if path.name != "__init__.py":
                module_names.add(f"forecast_trust_core.{path.stem}")
        module_names.update(REQUIRED_SUCCESSOR_MODULES)
        for module_name in sorted(module_names):
            importlib.import_module(module_name)
            log(f"import_pass={module_name}")
        log(f"import_count={len(module_names)}")

        log()
        log("== json_schema_draft_2020_12_meta_validation ==")
        from jsonschema import Draft202012Validator

        schema_paths = sorted((repo_root / "schemas").glob("*.schema.json"))
        if not schema_paths:
            raise P6Failure("no JSON schemas were found")
        for schema_path in schema_paths:
            schema = strict_json_load(schema_path)
            if not isinstance(schema, dict):
                raise P6Failure(f"schema root is not an object: {schema_path.name}")
            Draft202012Validator.check_schema(schema)
            log(
                f"schema_pass={schema_path.relative_to(repo_root)}"
                f",sha256={sha256_file(schema_path)}"
            )
        log(f"schema_meta_validation_count={len(schema_paths)}")

        record_command(
            "go_test_roughtime_strict_verifier",
            [go, "test", "-count=1", "./..."],
            cwd=repo_root / "scripts" / "genesis" / "roughtime_strict_verifier",
            env=go_env,
        )
        record_command(
            "go_test_ed25519_verifier",
            [go, "test", "-count=1", "./..."],
            cwd=repo_root / "scripts" / "genesis" / "ed25519_verify",
            env=go_env,
        )

        pytest_suite("focused_candidate_regression", CANDIDATE_TESTS)
        pytest_suite("focused_claim_authority_regression", CLAIM_AUTHORITY_TESTS)
        pytest_suite("focused_provider_authority_regression", PROVIDER_AUTHORITY_TESTS)
        pytest_suite(
            "focused_strong_bitcoin_authority_regression",
            ("tests/test_claim_authority_v1.py",),
            extra=("-k", "bitcoin"),
        )
        pytest_suite("synthetic_adversarial_regression", ADVERSARIAL_TESTS)
        pytest_suite("full_repository_pytest", ("tests",))

        log()
        log("execution_result=ALL_MANDATORY_EXECUTION_PASSED_PENDING_INDEPENDENT_REPORT_REVIEW")
        log("P6_PASS=NO")
        log("P6_FAIL=NO")
        log("P6_REPORT_REVIEW=PENDING")
        log("P7=PROHIBITED_UNTIL_P6_PASS")
    except P6EnvironmentIneligible as exc:
        environment_ineligible = True
        failure_reason = f"{type(exc).__name__}: {exc}"
        log()
        log("execution_result=NOT_STARTED_ENVIRONMENT_INELIGIBLE")
        log("P6_EXECUTION_STARTED=NO")
        log("P6_PASS=NO")
        log("P6_FAIL=NO")
        log("P6_REPORT_REVIEW=NOT_ELIGIBLE")
        log("P7=PROHIBITED_UNTIL_P6_PASS")
        log(f"environment_ineligibility_reason={failure_reason}")
    except Exception as exc:
        failed = True
        failure_reason = f"{type(exc).__name__}: {exc}"
        log()
        log("execution_result=FAILED")
        log("P6_PASS=NO")
        log("P6_FAIL=YES")
        log("P6_REPORT_REVIEW=NOT_ELIGIBLE")
        log("P7=PROHIBITED_UNTIL_P6_PASS")
        log(f"failure_reason={failure_reason}")
    finally:
        log()
        log("Genesis=NOT_STARTED")
        log("Forecast_Ledger_Genesis=NOT_CREATED")
        log("Forecast_Ledger=NOT_CREATED")
        log("prospective_forecast_count=0")
        log("production_qualified_provider_count=0")
        log("PRODUCTION_QUALIFIED=NO")
        log("production_forecasting=PROHIBITED")
        log("network_authorized=false")
        log("Roughtime_provider_requests_authorized=0")
        log("RFC3161_requests_authorized=0")
        log("production_qualification_requests_authorized=0")
        log("Genesis_private_key_handling=PROHIBITED")
        log_handle.close()

    digest = sha256_file(report)
    sidecar.write_text(f"{digest}  {report.name}\n", encoding="utf-8")
    print(f"Report: {report}")
    print(f"SHA256: {sidecar}")
    if environment_ineligible:
        print(f"P6 execution did not start: {failure_reason}", file=sys.stderr)
        return 2
    if failed:
        print(f"P6 execution failed: {failure_reason}", file=sys.stderr)
        return 1
    print("All mandatory P6 execution commands passed; independent report review is still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
