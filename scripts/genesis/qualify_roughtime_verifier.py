#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

from forecast_trust_core._roughtime_qualification import (
    base_go_env,
    compute_directory_tree_sha256,
    compute_wrapper_source_tree_sha256,
    make_dependency_lock,
    make_fixture_report,
    make_verifier_build_profile,
    module_graph_command,
    offline_go_env,
    parse_module_download_json,
    run_checked,
    strict_json_file,
    upstream_download_command,
    validate_dependency_lock_material,
)


def write_new_json(path: Path, value: dict) -> None:
    if path.exists():
        raise ValueError(f"refusing to overwrite existing output: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def copy_new_file(source: Path, destination: Path) -> None:
    if destination.exists():
        raise ValueError(f"refusing to overwrite existing output: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with source.open("rb") as src, destination.open("xb") as dst:
        while True:
            chunk = src.read(1024 * 1024)
            if not chunk:
                break
            dst.write(chunk)
        dst.flush()
        os.fsync(dst.fileno())


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def exact_go_env(wrapper_dir: Path, env: dict[str, str]) -> tuple[str, str, str, Path]:
    version = run_checked(["go", "version"], cwd=wrapper_dir, env=env).decode().strip().split()
    if len(version) < 4 or not version[2].startswith("go1.27."):
        raise ValueError("qualification requires an exact Go 1.27.x toolchain")
    go_version = version[2]
    goos = run_checked(["go", "env", "GOOS"], cwd=wrapper_dir, env=env).decode().strip()
    goarch = run_checked(["go", "env", "GOARCH"], cwd=wrapper_dir, env=env).decode().strip()
    goroot_text = run_checked(["go", "env", "GOROOT"], cwd=wrapper_dir, env=env).decode().strip()
    if not goos or not goarch or not goroot_text:
        raise ValueError("Go environment returned an empty GOOS, GOARCH, or GOROOT")
    goroot = Path(goroot_text)
    if not goroot.is_dir():
        raise ValueError(f"GOROOT is not a directory: {goroot}")
    return go_version, goos, goarch, goroot


def freeze_dependencies(args: argparse.Namespace) -> None:
    wrapper = args.wrapper_dir.resolve()
    if args.output.exists():
        raise ValueError(f"refusing to overwrite existing output: {args.output}")
    if args.upstream_source_archive.exists():
        raise ValueError(f"refusing to overwrite existing output: {args.upstream_source_archive}")
    env = base_go_env()
    exact_go_env(wrapper, env)
    run_checked(["go", "mod", "download", "all"], cwd=wrapper, env=env)
    go_sum = wrapper / "go.sum"
    if not go_sum.is_file() or go_sum.is_symlink():
        raise ValueError("go mod download did not produce a regular go.sum")
    graph = run_checked(module_graph_command(), cwd=wrapper, env=env).decode("utf-8")
    lock = make_dependency_lock((wrapper / "go.mod").read_bytes(), go_sum.read_bytes(), graph)
    download_json = run_checked(upstream_download_command(), cwd=wrapper, env=env)
    cached_zip = parse_module_download_json(download_json, lock)
    copy_new_file(cached_zip, args.upstream_source_archive)
    write_new_json(args.output, lock)


def qualify_offline(args: argparse.Namespace) -> None:
    wrapper = args.wrapper_dir.resolve()
    binary = wrapper / "fpp-roughtime-strict"
    for path in (args.fixture_report, args.build_profile, binary):
        if path.exists():
            raise ValueError(f"refusing to overwrite existing output: {path}")
    if not args.upstream_source_archive.is_file() or args.upstream_source_archive.is_symlink():
        raise ValueError("retained upstream source archive must be a regular file")

    env = offline_go_env()
    go_version, goos, goarch, goroot = exact_go_env(wrapper, env)
    lock = strict_json_file(args.dependency_lock)

    run_checked(["go", "mod", "verify"], cwd=wrapper, env=env)
    graph = run_checked(module_graph_command(), cwd=wrapper, env=env).decode("utf-8")
    validate_dependency_lock_material(lock, (wrapper / "go.mod").read_bytes(), (wrapper / "go.sum").read_bytes(), graph)

    cached_zip = parse_module_download_json(run_checked(upstream_download_command(), cwd=wrapper, env=env), lock)
    if file_sha256(cached_zip) != file_sha256(args.upstream_source_archive):
        raise ValueError("retained upstream source archive differs from the exact module Zip used by Go")

    toolchain_hash = compute_directory_tree_sha256(goroot)
    wrapper_hash = compute_wrapper_source_tree_sha256(wrapper)
    test_json = run_checked(["go", "test", "-count=1", "-json", "./..."], cwd=wrapper, env=env)
    fixture_report = make_fixture_report(
        test_json,
        go_version=go_version,
        goos=goos,
        goarch=goarch,
        go_toolchain_tree_sha256=toolchain_hash,
        wrapper_source_tree_sha256=wrapper_hash,
    )

    run_checked(
        ["go", "build", "-trimpath", "-buildvcs=false", "-ldflags=-buildid=", "-o", "fpp-roughtime-strict", "."],
        cwd=wrapper,
        env=env,
    )
    if not binary.is_file() or binary.is_symlink():
        raise ValueError("frozen build command did not create a regular fpp-roughtime-strict")

    run_checked(["go", "mod", "verify"], cwd=wrapper, env=env)
    cached_zip_after = parse_module_download_json(run_checked(upstream_download_command(), cwd=wrapper, env=env), lock)
    if file_sha256(cached_zip_after) != file_sha256(args.upstream_source_archive):
        raise ValueError("upstream module Zip changed during qualification")
    if compute_directory_tree_sha256(goroot) != toolchain_hash:
        raise ValueError("GOROOT tree changed during qualification")

    profile = make_verifier_build_profile(
        dependency_lock=lock,
        fixture_report=fixture_report,
        wrapper_dir=wrapper,
        upstream_source_archive=args.upstream_source_archive,
        binary=binary,
        go_version=go_version,
        goos=goos,
        goarch=goarch,
        go_toolchain_tree_sha256=toolchain_hash,
    )
    write_new_json(args.fixture_report, fixture_report)
    write_new_json(args.build_profile, profile)


def main() -> int:
    parser = argparse.ArgumentParser(description="Freeze and qualify the offline Roughtime strict verifier. No provider packets are sent.")
    sub = parser.add_subparsers(dest="command", required=True)

    freeze = sub.add_parser(
        "freeze-dependencies",
        help="Acquire Go module bytes, freeze the resolved module set, and retain the exact pinned upstream module Zip.",
    )
    freeze.add_argument("--wrapper-dir", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True, help="New dependency-lock JSON path.")
    freeze.add_argument("--upstream-source-archive", type=Path, required=True, help="New retained pinned module Zip path.")

    qualify = sub.add_parser(
        "qualify-offline",
        help="Verify cached modules, run fixtures, and build with Go module network access disabled.",
    )
    qualify.add_argument("--wrapper-dir", type=Path, required=True)
    qualify.add_argument("--dependency-lock", type=Path, required=True)
    qualify.add_argument("--upstream-source-archive", type=Path, required=True)
    qualify.add_argument("--fixture-report", type=Path, required=True)
    qualify.add_argument("--build-profile", type=Path, required=True)

    args = parser.parse_args()
    try:
        if args.command == "freeze-dependencies":
            freeze_dependencies(args)
        else:
            qualify_offline(args)
    except Exception as exc:
        print(f"Roughtime verifier qualification failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
