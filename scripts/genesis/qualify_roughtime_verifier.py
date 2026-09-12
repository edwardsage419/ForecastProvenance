#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from forecast_trust_core._roughtime_qualification_vendored import (
    compute_directory_tree_sha256,
    compute_wrapper_source_tree_sha256,
    make_dependency_lock,
    make_fixture_report,
    make_verifier_build_profile,
    offline_go_env,
    run_checked,
    verify_main_module_only,
)

def write_new_json(path: Path, value: dict) -> None:
    if path.exists():
        raise ValueError(f"refusing to overwrite existing output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def exact_go_env(wrapper_dir: Path, env: dict[str, str]) -> tuple[str, str, str, Path]:
    version = run_checked(["go", "version"], cwd=wrapper_dir, env=env).decode().strip().split()
    if len(version) < 4 or not version[2].startswith("go1.27."):
        raise ValueError("qualification requires an exact Go 1.27.x toolchain")
    go_version = version[2]
    goos = run_checked(["go", "env", "GOOS"], cwd=wrapper_dir, env=env).decode().strip()
    goarch = run_checked(["go", "env", "GOARCH"], cwd=wrapper_dir, env=env).decode().strip()
    goroot = Path(run_checked(["go", "env", "GOROOT"], cwd=wrapper_dir, env=env).decode().strip())
    if not goos or not goarch or not goroot.is_dir():
        raise ValueError("Go environment returned invalid GOOS, GOARCH, or GOROOT")
    return go_version, goos, goarch, goroot

def qualify_offline(args: argparse.Namespace) -> None:
    wrapper = args.wrapper_dir.resolve()
    binary = wrapper / "fpp-roughtime-strict"
    for path in (args.dependency_lock, args.fixture_report, args.build_profile, binary):
        if path.exists():
            raise ValueError(f"refusing to overwrite existing output: {path}")

    env = offline_go_env()
    go_version, goos, goarch, goroot = exact_go_env(wrapper, env)
    verify_main_module_only(wrapper, env)

    lock = make_dependency_lock(wrapper)
    wrapper_hash = compute_wrapper_source_tree_sha256(wrapper)
    toolchain_hash = compute_directory_tree_sha256(goroot)

    test_json = run_checked(["go", "test", "-count=1", "-json", "./..."], cwd=wrapper, env=env)
    fixture_report = make_fixture_report(
        test_json,
        go_version=go_version,
        goos=goos,
        goarch=goarch,
        go_toolchain_tree_sha256=toolchain_hash,
        wrapper_source_tree_sha256=wrapper_hash,
        upstream_source_tree_sha256=lock["upstream_source_tree_sha256"],
    )

    run_checked(
        ["go", "build", "-trimpath", "-buildvcs=false", "-ldflags=-buildid=", "-o", "fpp-roughtime-strict", "."],
        cwd=wrapper,
        env=env,
    )
    if not binary.is_file() or binary.is_symlink():
        raise ValueError("frozen build command did not create a regular fpp-roughtime-strict")

    verify_main_module_only(wrapper, env)
    if make_dependency_lock(wrapper) != lock:
        raise ValueError("vendored source changed during qualification")
    if compute_wrapper_source_tree_sha256(wrapper) != wrapper_hash:
        raise ValueError("wrapper source changed during qualification")
    if compute_directory_tree_sha256(goroot) != toolchain_hash:
        raise ValueError("GOROOT tree changed during qualification")

    profile = make_verifier_build_profile(
        dependency_lock=lock,
        fixture_report=fixture_report,
        wrapper_dir=wrapper,
        binary=binary,
        go_version=go_version,
        goos=goos,
        goarch=goarch,
        go_toolchain_tree_sha256=toolchain_hash,
        go_toolchain_distribution_source=args.toolchain_distribution_source,
        go_toolchain_distribution_sha256=args.toolchain_distribution_sha256,
        go_toolchain_carrier_sha256=args.toolchain_carrier_sha256,
    )

    write_new_json(args.dependency_lock, lock)
    write_new_json(args.fixture_report, fixture_report)
    write_new_json(args.build_profile, profile)

def main() -> int:
    parser = argparse.ArgumentParser(description="Qualify the vendored offline Roughtime strict verifier. No provider packets are sent.")
    parser.add_argument("--wrapper-dir", type=Path, required=True)
    parser.add_argument("--dependency-lock", type=Path, required=True)
    parser.add_argument("--fixture-report", type=Path, required=True)
    parser.add_argument("--build-profile", type=Path, required=True)
    parser.add_argument("--toolchain-distribution-source", required=True)
    parser.add_argument("--toolchain-distribution-sha256", required=True)
    parser.add_argument("--toolchain-carrier-sha256", required=True)
    args = parser.parse_args()
    try:
        qualify_offline(args)
    except Exception as exc:
        print(f"Roughtime verifier qualification failed: {exc}", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
