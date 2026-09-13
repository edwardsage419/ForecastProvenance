#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

from forecast_trust_core._ed25519_qualification import (
    compute_directory_tree_sha256,
    exact_go_env,
    hardened_go_env,
    make_build_profile,
    resolve_pinned_go_binary,
    run_checked,
    run_reproducible_build,
    validate_source_tree,
    verify_main_module_only,
)


def write_new_json_exclusive(path: Path, value: dict) -> None:
    import json

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


def qualify_offline(args: argparse.Namespace) -> None:
    source_dir = args.source_dir.resolve(strict=True)
    output = args.build_profile.resolve()
    if os.path.lexists(output):
        raise ValueError(f"refusing to overwrite existing output: {output}")

    validate_source_tree(source_dir)

    with tempfile.TemporaryDirectory(prefix="fpp-ed25519-qualification-") as scratch_text:
        scratch = Path(scratch_text)
        env = hardened_go_env(os.environ, scratch_dir=scratch)
        go_binary, goroot = resolve_pinned_go_binary(source_dir, env)
        go_version, goos, goarch = exact_go_env(go_binary, source_dir, goroot, env)
        verify_main_module_only(go_binary, source_dir, env)
        toolchain_hash = compute_directory_tree_sha256(goroot)

        test_json = run_checked(
            [str(go_binary), "test", "-count=1", "-json", "./..."],
            cwd=source_dir,
            env=env,
        )
        validate_source_tree(source_dir)

        binary = run_reproducible_build(
            go_binary,
            source_dir,
            env,
            scratch_dir=scratch / "reproducibility",
        )
        validate_source_tree(source_dir, allow_binary=True)
        verify_main_module_only(go_binary, source_dir, env)

        profile = make_build_profile(
            source_dir=source_dir,
            binary=binary,
            go_test_json=test_json,
            go_version=go_version,
            goos=goos,
            goarch=goarch,
            go_toolchain_tree_sha256=toolchain_hash,
            go_toolchain_distribution_source=args.toolchain_distribution_source,
            go_toolchain_distribution_sha256=args.toolchain_distribution_sha256,
            go_toolchain_carrier_sha256=args.toolchain_carrier_sha256,
        )

    write_new_json_exclusive(output, profile)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Qualify the offline Ed25519 verification-only backend. "
            "No signing, private-key operation, or provider network request is performed."
        )
    )
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--build-profile", type=Path, required=True)
    parser.add_argument("--toolchain-distribution-source", required=True)
    parser.add_argument("--toolchain-distribution-sha256", required=True)
    parser.add_argument("--toolchain-carrier-sha256", required=True)
    args = parser.parse_args()
    try:
        qualify_offline(args)
    except Exception as exc:
        print(f"Ed25519 verifier qualification failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
