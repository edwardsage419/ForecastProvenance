#!/usr/bin/env python3
"""Offline, inert R4T_VC_DEV_001 transport. No protocol authority or execution."""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
from importlib.machinery import SourceFileLoader
import importlib.util
from importlib.metadata import version
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PROFILE = "R4T_VC_DEV_001"
FORMAT = "R4T_VC_DEV_BUNDLE_V1"
CORE_REL = "docs/development/r4t-vc-prototype-2026-10-09-rev-002/prototype.py"
CORE_PINS = {
    CORE_REL: "c7cb10aa3fd05920e07d98cb03725b992608117087884d2af1e4c8335eb1573e",
    "docs/development/r4t-vc-prototype-2026-10-09-rev-002/draft_schemas.json": "50b302d1d8dda7f764d8058dcb812bf2c6fde5fae7c88be215073333d736ea98",
    "src/forecast_trust_core/canonical.py": "f9ef49579a5c54757c6660d377275a0ed5f8afdf646f33130651a711005ac9ba",
    "schemas/validator_contract_v1.schema.json": "ad312dfa33f7d09b14d3abd5123799aafdb9f83caa6a87022eb5f5d11730c34e",
    "schemas/implementation_binding_v1.schema.json": "d04aace0bd1893e88417d77cc5c4458a2be22a62b3bd256f08abaa59fbddb65e",
    "schemas/test_contract_v1.schema.json": "934342de9d45ca584b8d4dedd61865edcef563a8ba33927dd24215af54f80545",
    "schemas/runtime_profile_v1.schema.json": "b2fc759be85d115415c8ca37aec487d4b57537c6e155ac36d3851bed3069ab6a",
    "schemas/component_contract_v1.schema.json": "200a1c73e40edf0b6935226985a524fe63628fc3a3f1d133f8252759bc442b11",
    "schemas/operation_registry_v1.schema.json": "60d9909eace436a5384b929023c1989f690de75762d984f8acd13830aaa22d63",
}
LIMITS = {
    "development_only": True, "REAL_ADMISSION": "NOT_READY",
    "REAL_G02_G03": "NOT_ESTABLISHED", "REAL_GENESIS_READINESS": "NOT_ESTABLISHED",
    "prospective_eligible": False, "PROTOCOL_STATE_CHANGE": "NONE",
}


class StartupError(RuntimeError):
    """A fixed dependency or environment is unavailable; never fall back."""


class TransportError(ValueError):
    """Untrusted transport rejected without disclosing its content."""


def _hash(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_reviewed_core():
    """Check all nine fixed dependencies before executing either local module."""
    sys.dont_write_bytecode = True
    identities = []
    sources = {}
    for rel, expected in CORE_PINS.items():
        try:
            raw = (ROOT / rel).read_bytes()
        except OSError as exc:
            raise StartupError("FIXED_DEPENDENCY_UNAVAILABLE: " + rel) from exc
        actual = _hash(raw)
        if actual != expected:
            raise StartupError("FIXED_DEPENDENCY_DRIFT: " + rel)
        identities.append({"path": rel, "sha256": actual, "bytes": len(raw)})
        if rel.endswith(".py"):
            sources[str((ROOT / rel).resolve())] = raw
    # The reviewed prototype itself creates a file spec for canonical.py.
    # Scope this source-only hook to those two fixed, already verified paths.
    # Standard environment imports retain their ordinary loader; no data is code.
    original_get_code = SourceFileLoader.get_code
    def reviewed_get_code(loader, fullname):
        path = str(Path(loader.path).resolve())
        if path in sources:
            return compile(sources[path], path, "exec", dont_inherit=True)
        return original_get_code(loader, fullname)
    try:
        SourceFileLoader.get_code = reviewed_get_code
        spec = importlib.util.spec_from_file_location("r4t_vc_reviewed_core", ROOT / CORE_REL)
        core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(core)
    except Exception as exc:
        raise StartupError("REVIEWED_CORE_IMPORT_FAILED") from exc
    finally:
        SourceFileLoader.get_code = original_get_code
    # Schemas are read by the unmodified core; detect persistent import-time drift.
    for rel, expected in CORE_PINS.items():
        try:
            actual = _hash((ROOT / rel).read_bytes())
        except OSError as exc:
            raise StartupError("FIXED_DEPENDENCY_UNAVAILABLE: " + rel) from exc
        if actual != expected:
            raise StartupError("FIXED_DEPENDENCY_DRIFT: " + rel)
    core.development_core_identities = identities
    return core


def _require(ok: bool, path: str):
    if not ok:
        raise TransportError("INVALID_TRANSPORT: " + path)


def _bytes_slot(value, encode: bool, path: str):
    if encode:
        _require(type(value) is bytes, path)
        return {"base64": base64.b64encode(value).decode("ascii")}
    _require(isinstance(value, dict) and set(value) == {"base64"}, path)
    text = value["base64"]
    _require(isinstance(text, str), path)
    try:
        raw = base64.b64decode(text, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise TransportError("INVALID_BASE64: " + path) from exc
    _require(base64.b64encode(raw).decode("ascii") == text, path)
    return raw


def _transform_package(package: dict, encode: bool) -> dict:
    _require(isinstance(package, dict) and set(package) == {
        "development_only", "profile", "vc", "objects", "retained"}, "package")
    _require(package["development_only"] is True and package["profile"] == PROFILE, "package.profile")
    _require(isinstance(package["vc"], dict) and isinstance(package["objects"], list)
             and all(isinstance(o, dict) for o in package["objects"]), "package.catalog")
    retained = package["retained"]
    _require(isinstance(retained, dict) and set(retained) == {
        "r4t", "package_artifact", "source_files", "schema_files", "fixtures"}, "retained")
    out = {}
    for field in ("r4t", "package_artifact"):
        out[field] = _bytes_slot(retained[field], encode, "retained." + field)
    for field, key in (("source_files", "path"), ("schema_files", "path"), ("fixtures", "fixture_id")):
        rows = retained[field]
        _require(isinstance(rows, list), "retained." + field)
        out[field] = []
        for row in rows:
            _require(isinstance(row, dict) and set(row) == {key, "raw"}
                     and isinstance(row[key], str), "retained." + field + ".row")
            out[field].append({key: row[key], "raw": _bytes_slot(row["raw"], encode, "retained." + field + ".raw")})
    # No sorting, resealing, repair, recursive type markers, or embedded-path I/O.
    return {**package, "retained": out}


def _encode(package: dict, core) -> bytes:
    envelope = {"format": FORMAT, "development_only": True, "profile": PROFILE,
                "package": _transform_package(package, True)}
    try:
        return core.CAN.canonical_json(envelope) + b"\n"
    except (ValueError, TypeError, RecursionError) as exc:
        raise TransportError("INVALID_TRANSPORT_JSON") from exc


def encode_package(package: dict) -> bytes:
    """Lossless development transport, not a claim of consumer acceptance."""
    return _encode(package, load_reviewed_core())


def _decode(raw: bytes, core) -> dict:
    _require(type(raw) is bytes, "bundle.bytes")
    try:
        envelope = core.CAN.parse_json_strict(raw)
    except (ValueError, TypeError, RecursionError) as exc:
        raise TransportError("INVALID_BUNDLE_JSON") from exc
    _require(isinstance(envelope, dict) and set(envelope) == {
        "format", "development_only", "profile", "package"}, "envelope")
    _require(envelope["format"] == FORMAT and envelope["development_only"] is True
             and envelope["profile"] == PROFILE, "envelope.profile")
    return _transform_package(envelope["package"], False)


def decode_package(raw: bytes) -> dict:
    """Restore only the five known retained byte-slot families."""
    return _decode(raw, load_reviewed_core())


def _identities(core) -> dict:
    try:
        cli_raw = Path(__file__).read_bytes()
        environment = {"python": sys.version.split()[0], "jsonschema": version("jsonschema")}
    except Exception as exc:
        raise StartupError("ENVIRONMENT_IDENTITY_UNAVAILABLE") from exc
    return {"core_dependencies": core.development_core_identities,
            "cli_identity": {"path": "scripts/development/replay_r4t_vc.py",
                             "sha256": _hash(cli_raw), "bytes": len(cli_raw)},
            "environment": environment}


def _replay(bundle_raw: bytes, expected_raw: bytes, core) -> dict:
    _require(type(bundle_raw) is bytes and type(expected_raw) is bytes, "replay.bytes")
    report = {**LIMITS, **_identities(core), "format": FORMAT, "profile": PROFILE,
              "bundle_raw_sha256": _hash(bundle_raw), "expected_raw_sha256": _hash(expected_raw)}
    try:
        expected = core.CAN.parse_json_strict(expected_raw)
    except (ValueError, TypeError, RecursionError):
        return {**report, "verdict": "TRANSPORT_REJECT", "rejection_layer": "expected_json",
                "checked": [], "failures": [{"code": "EXPECTED_JSON", "path": "expected"}]}
    try:
        package = _decode(bundle_raw, core)
    except TransportError:
        return {**report, "verdict": "TRANSPORT_REJECT", "rejection_layer": "transport",
                "checked": [], "failures": [{"code": "BUNDLE_TRANSPORT", "path": "bundle"}]}
    # This is the ONLY replay consumer. No construction or expected inference.
    result = core.verify_prototype(package, expected)
    return {**report, **result,
            "rejection_layer": "NONE" if result["verdict"] == "MODEL_PASS" else "consumer"}


def replay_bundle(bundle_raw: bytes, expected_raw: bytes) -> dict:
    """Consume the actual retained package against separately supplied model pins."""
    return _replay(bundle_raw, expected_raw, load_reviewed_core())


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's raw message can contain caller data; retain only the class.
        raise TransportError("ARGUMENTS_INVALID")


class _OutputError(OSError):
    output_incomplete = True


def _check_conflicts(output: Path, inputs: list[Path]):
    resolved = output.resolve()
    for path in inputs:
        actual = path.resolve()
        if resolved == actual or resolved in actual.parents:
            raise TransportError("INPUT_OUTPUT_CONFLICT")


def _create_output(output: Path) -> int:
    """Walk existing parents without symlinks; atomically create a new directory."""
    path = Path(os.path.abspath(output))
    if path == Path(path.anchor):
        raise TransportError("OUTPUT_ROOT_INVALID")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    parent_fd = os.open(path.anchor, flags)
    try:
        for part in path.parts[1:-1]:
            child_fd = os.open(part, flags, dir_fd=parent_fd)
            os.close(parent_fd)
            parent_fd = child_fd
        os.mkdir(path.name, mode=0o700, dir_fd=parent_fd)
        try:
            return os.open(path.name, flags, dir_fd=parent_fd)
        except OSError as exc:
            raise _OutputError("NEW_OUTPUT_OPEN_FAILED") from exc
    finally:
        os.close(parent_fd)


def _write_file(directory_fd: int, name: str, raw: bytes):
    # Names are fixed by this script, never obtained from bundle data.
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                 mode=0o600, dir_fd=directory_fd)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)


def _report_bytes(report: dict) -> bytes:
    return (json.dumps(report, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def main(argv=None) -> int:
    parser = _Parser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="Persist an explicitly supplied synthetic model; no verification")
    build.add_argument("--inputs", type=Path, required=True)
    build.add_argument("--output", type=Path, required=True)
    replay = commands.add_parser("replay", help="Directly consume retained bundle and explicit external expected")
    replay.add_argument("--bundle", type=Path, required=True)
    replay.add_argument("--expected", type=Path, required=True)
    replay.add_argument("--output", type=Path, required=True)
    directory_fd = None
    output = None
    try:
        args = parser.parse_args(argv)
        output = args.output
        paths = [args.inputs] if args.command == "build" else [args.bundle, args.expected]
        _check_conflicts(output, paths)
        core = load_reviewed_core()
        if args.command == "build":
            inputs_raw = args.inputs.read_bytes()
            try:
                inputs = core.CAN.parse_json_strict(inputs_raw)
                package = core.build_prototype(inputs)
            except (ValueError, TypeError, KeyError, RecursionError) as exc:
                raise TransportError("BUILD_INPUT_REJECTED") from exc
            bundle_raw = _encode(package, core)
            report = {**LIMITS, **_identities(core), "format": FORMAT, "profile": PROFILE,
                      "status": "BUILT_UNVERIFIED", "inputs_raw_sha256": _hash(inputs_raw),
                      "bundle_raw_sha256": _hash(bundle_raw)}
            directory_fd = _create_output(output)
            _write_file(directory_fd, "bundle.json", bundle_raw)
            _write_file(directory_fd, "build.json", _report_bytes(report))
            code = 0
            summary = {"status": "BUILT_UNVERIFIED", "bundle_raw_sha256": report["bundle_raw_sha256"]}
        else:
            bundle_raw = args.bundle.read_bytes()
            expected_raw = args.expected.read_bytes()
            report = _replay(bundle_raw, expected_raw, core)
            directory_fd = _create_output(output)
            _write_file(directory_fd, "result.json", _report_bytes(report))
            code = 0 if report["verdict"] == "MODEL_PASS" else 2
            summary = {k: report[k] for k in ("verdict", "rejection_layer", "failures", "bundle_raw_sha256", "expected_raw_sha256")}
        print(json.dumps({**LIMITS, **summary}, sort_keys=True))
        return code
    except (TransportError, StartupError, OSError) as exc:
        code = 2 if isinstance(exc, TransportError) else 3
        error = str(exc) if isinstance(exc, (TransportError, StartupError)) else "IO_FAILURE"
        incomplete = directory_fd is not None or getattr(exc, "output_incomplete", False)
        report = {**LIMITS, "error": error, "exit_code": code, "output_incomplete": incomplete}
        if incomplete and output is not None:
            report["partial_output_directory"] = str(output)
        print(json.dumps(report, sort_keys=True), file=sys.stderr)
        return code
    finally:
        if directory_fd is not None:
            os.close(directory_fd)


if __name__ == "__main__":
    raise SystemExit(main())
