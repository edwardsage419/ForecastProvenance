"""Bounded codec/loader/CLI checks using explicit inert synthetic inputs only."""
import base64
import copy
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import py_compile
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/development/replay_r4t_vc.py"
FIXTURE = ROOT / "docs/development/r4t-vc-prototype-2026-10-09-rev-002/synthetic_inputs.json"
_UNSET = object()


def load_cli():
    if not SCRIPT.is_file():
        raise AssertionError("development codec/loader/CLI has not been implemented")
    spec = importlib.util.spec_from_file_location("tested_r4t_cli", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sample_package():
    # Deliberately not an accepted model: codec must preserve, never repair it.
    return {
        "development_only": True, "profile": "R4T_VC_DEV_001",
        "vc": {"inert": {"base64": "not-a-byte-slot"}, "text": "中文"},
        "objects": [{"index": 2}, {"index": 1}],
        "retained": {
            "r4t": b'{ "a": 1 }\n', "package_artifact": b"\x00\xff",
            "source_files": [{"path": "inert/never-read.py", "raw": "中文\n".encode()}],
            "schema_files": [{"path": "inert/schema.json", "raw": b"{}\n"}],
            "fixtures": [{"fixture_id": "empty-control", "raw": b""}],
        },
    }


class CodecLoaderTests(unittest.TestCase):
    def setUp(self):
        self.cli = load_cli()
        self.package = sample_package()

    def raw(self):
        return self.cli.encode_package(self.package)

    def test_all_byte_slots_values_and_list_order_round_trip(self):
        before = copy.deepcopy(self.package)
        raw = self.raw()
        envelope = json.loads(raw)
        self.assertEqual(envelope["package"]["retained"]["package_artifact"], {"base64": "AP8="})
        self.assertEqual(self.cli.decode_package(raw), before)
        self.assertEqual(self.package, before)
        self.assertEqual(envelope["package"]["vc"]["inert"], {"base64": "not-a-byte-slot"})

    def test_outer_json_whitespace_does_not_change_retained_bytes(self):
        raw = self.raw()
        other = json.dumps(json.loads(raw), ensure_ascii=False, separators=(",", ":")).encode()
        self.assertNotEqual(hashlib.sha256(raw).hexdigest(), hashlib.sha256(other).hexdigest())
        self.assertEqual(self.cli.decode_package(raw), self.cli.decode_package(other))

    def test_pretty_compact_and_unicode_bytes_are_not_reserialized(self):
        for raw in [b'{ "x": 1 }\n', b'{"x":1}\n', '{"text":"中文"}\n'.encode(), b""]:
            with self.subTest(raw=raw):
                self.package["retained"]["r4t"] = raw
                self.assertEqual(self.cli.decode_package(self.raw())["retained"]["r4t"], raw)

    def test_strict_json_encoding_duplicates_numbers_and_null(self):
        raw = self.raw()
        cases = [b"", b"\xff", b"\xef\xbb\xbf" + raw,
                 b'{"format":"a","format":"b"}',
                 b'{"x":NaN}', b'{"x":Infinity}', b'{"x":1.2}', b'{"x":-0}',
                 b'{"x":9007199254740992}', b'{"x":null}', b'{"x":"\\ud800"}',
                 b'{"vc":{"a":1,"a":2}}', "{}".encode("utf-16")]
        for bad in cases:
            with self.subTest(raw=bad):
                with self.assertRaises(ValueError):
                    self.cli.decode_package(bad)

    def test_unknown_missing_envelope_and_wrong_types(self):
        original = json.loads(self.raw())
        mutations = [("format", "R4T_VC_DEV_BUNDLE_V2"), ("profile", "other"),
                     ("development_only", 1), ("extra", True), ("package", []),
                     ("package", {}), ("package", None)]
        for field, value in mutations:
            with self.subTest(field=field, value=value):
                obj = copy.deepcopy(original); obj[field] = value
                with self.assertRaises(ValueError):
                    self.cli.decode_package(json.dumps(obj).encode())
        for field in original:
            obj = copy.deepcopy(original); del obj[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                self.cli.decode_package(json.dumps(obj).encode())
        for obj in [None, [], {}, 1, ""]:
            with self.subTest(root=obj), self.assertRaises(ValueError):
                self.cli.decode_package(json.dumps(obj).encode())

    def test_noncanonical_and_malformed_base64(self):
        for value in ["AP8", "AP8=\n", "AP9=", "AP8===", "_w==", "!!!!", 1, None]:
            obj = json.loads(self.raw()); obj["package"]["retained"]["r4t"] = {"base64": value}
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.cli.decode_package(json.dumps(obj).encode())
        for value in ["eA==", {}, {"base64": "eA==", "type": "bytes"}]:
            obj = json.loads(self.raw()); obj["package"]["retained"]["r4t"] = value
            with self.subTest(wrapper=value), self.assertRaises(ValueError):
                self.cli.decode_package(json.dumps(obj).encode())

    def test_missing_byte_slots_and_wrong_retained_rows(self):
        for field in self.package["retained"]:
            obj = json.loads(self.raw()); del obj["package"]["retained"][field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                self.cli.decode_package(json.dumps(obj).encode())
        for value in [[], {}, "", 1, None]:
            obj = json.loads(self.raw()); obj["package"]["retained"]["source_files"] = value
            if value == []:  # Empty collections are transported; consumer decides coverage.
                self.assertEqual(self.cli.decode_package(json.dumps(obj).encode())["retained"]["source_files"], [])
            else:
                with self.subTest(rows=value), self.assertRaises(ValueError):
                    self.cli.decode_package(json.dumps(obj).encode())
        for row in [{"path": "x"}, {"path": 1, "raw": {"base64": ""}},
                    {"path": "x", "raw": {"base64": ""}, "extra": True}]:
            obj = json.loads(self.raw()); obj["package"]["retained"]["source_files"] = [row]
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.cli.decode_package(json.dumps(obj).encode())

    def test_encoder_rejects_non_bytes_without_mutation(self):
        for value in [bytearray(b"x"), "x", 1, None, {"base64": "eA=="}]:
            self.package["retained"]["r4t"] = value
            before = copy.deepcopy(self.package)
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.cli.encode_package(self.package)
            self.assertEqual(self.package, before)

    def test_fixed_loader_and_core_positive_round_trip(self):
        core = self.cli.load_reviewed_core()
        expected = core.CAN.parse_json_strict(FIXTURE.read_bytes())
        package = core.build_prototype(expected)
        decoded = self.cli.decode_package(self.cli.encode_package(package))
        self.assertEqual(decoded, package)
        self.assertEqual(core.verify_prototype(decoded, expected)["verdict"], "MODEL_PASS")

    def test_dependency_drift_and_missing_are_rejected_before_import(self):
        with tempfile.TemporaryDirectory(prefix="r4t-pin-test-", dir="/private/tmp") as td:
            root = Path(td)
            for rel in self.cli.CORE_PINS:
                dest = root / rel; dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / rel, dest)
            for rel in self.cli.CORE_PINS:
                target = root / rel; original = target.read_bytes()
                target.write_bytes(original + b"\nDRIFT_NOT_EXECUTABLE\n")
                with self.subTest(drift=rel), patch.object(self.cli, "ROOT", root), \
                        patch.object(self.cli.importlib.util, "spec_from_file_location",
                                     side_effect=AssertionError("drift imported")):
                    with self.assertRaises(self.cli.StartupError):
                        self.cli.load_reviewed_core()
                target.write_bytes(original)
            target.unlink()
            with patch.object(self.cli, "ROOT", root), self.assertRaises(self.cli.StartupError):
                self.cli.load_reviewed_core()

    def test_matching_timestamp_bytecode_cannot_replace_reviewed_source(self):
        with tempfile.TemporaryDirectory(prefix="r4t-cache-test-", dir="/private/tmp") as td:
            root = Path(td)
            for rel in self.cli.CORE_PINS:
                dest = root / rel; dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / rel, dest)
            # Only our isolated, explicitly safe copied canonical source is changed.
            target = root / "src/forecast_trust_core/canonical.py"
            original = target.read_bytes()
            sentinel = b"raise AssertionError('UNREVIEWED_BYTECODE_SENTINEL')\n"
            target.write_bytes(sentinel + b" " * (len(original) - len(sentinel)))
            stat = target.stat()
            py_compile.compile(str(target), doraise=True)
            target.write_bytes(original)
            os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            with patch.object(self.cli, "ROOT", root):
                core = self.cli.load_reviewed_core()
            self.assertEqual(core.CAN.parse_json_strict(b'{"safe":true}'), {"safe": True})


class ReplayCliTests(unittest.TestCase):
    def setUp(self):
        self.cli = load_cli()
        self.core = self.cli.load_reviewed_core()
        self.expected_raw = FIXTURE.read_bytes()
        self.expected = json.loads(self.expected_raw)
        self.package = self.core.build_prototype(self.expected)
        self.bundle_raw = self.cli.encode_package(self.package)
        self.tmp = tempfile.TemporaryDirectory(prefix="r4t-cli-test-", dir="/private/tmp")
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.bundle = self.dir / "bundle.json"; self.bundle.write_bytes(self.bundle_raw)
        self.expected_path = self.dir / "expected.json"; self.expected_path.write_bytes(self.expected_raw)

    def replay(self, package=_UNSET, expected=_UNSET):
        p = self.package if package is _UNSET else package
        x = self.expected if expected is _UNSET else expected
        return self.cli.replay_bundle(self.cli.encode_package(p), json.dumps(x).encode())

    def run_cli(self, *args, want):
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        p = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], cwd=ROOT,
                           env=env, capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, want, p.stdout + p.stderr)
        return p

    def assert_limits(self, report):
        self.assertIs(report["development_only"], True)
        self.assertEqual(report["REAL_ADMISSION"], "NOT_READY")
        self.assertEqual(report["REAL_G02_G03"], "NOT_ESTABLISHED")
        self.assertEqual(report["REAL_GENESIS_READINESS"], "NOT_ESTABLISHED")
        self.assertIs(report["prospective_eligible"], False)
        self.assertEqual(report["PROTOCOL_STATE_CHANGE"], "NONE")

    def test_replay_requires_implemented_api(self):
        self.assertTrue(callable(getattr(self.cli, "replay_bundle", None)), "direct replay API is missing")
        self.assertEqual(self.cli.replay_bundle(self.bundle_raw, self.expected_raw)["verdict"], "MODEL_PASS")

    def test_distinct_build_and_replay_processes_repeat_same_result(self):
        build = self.dir / "build"; first = self.dir / "first"; second = self.dir / "second"
        self.run_cli("build", "--inputs", self.expected_path, "--output", build, want=0)
        self.assertTrue((build / "bundle.json").is_file(), "build must persist the actual package")
        meta = json.loads((build / "build.json").read_bytes())
        self.assertEqual(meta["status"], "BUILT_UNVERIFIED"); self.assertNotIn("verdict", meta)
        self.assert_limits(meta)
        envelope = json.loads((build / "bundle.json").read_bytes())
        self.assertEqual(set(envelope), {"format", "development_only", "profile", "package"})
        for out in [first, second]:
            self.run_cli("replay", "--bundle", build / "bundle.json", "--expected", self.expected_path,
                         "--output", out, want=0)
        a = json.loads((first / "result.json").read_bytes())
        b = json.loads((second / "result.json").read_bytes())
        self.assertEqual(a, b); self.assertEqual(a["verdict"], "MODEL_PASS"); self.assert_limits(a)
        self.assertEqual(a["bundle_raw_sha256"], hashlib.sha256((build / "bundle.json").read_bytes()).hexdigest())
        self.assertEqual(a["expected_raw_sha256"], hashlib.sha256(self.expected_raw).hexdigest())
        self.assertEqual(a["cli_identity"]["sha256"], hashlib.sha256(SCRIPT.read_bytes()).hexdigest())
        self.assertEqual(len(a["core_dependencies"]), 9)
        self.assertIn("python", a["environment"]); self.assertIn("jsonschema", a["environment"])
        self.assertEqual(a["checked"][-1], "declared_results")

    def test_replay_never_builds_or_reads_default_fixture_or_embedded_paths(self):
        original = Path.read_bytes
        def safe_read(path):
            if path not in (SCRIPT, self.bundle, self.expected_path):
                raise AssertionError("replay accessed a default fixture or embedded path")
            return original(path)
        with patch.object(self.cli, "load_reviewed_core", return_value=self.core), \
                patch.object(self.core, "build_prototype", side_effect=AssertionError("builder called")), \
                patch.object(Path, "read_bytes", safe_read), contextlib.redirect_stdout(io.StringIO()):
            result = self.cli.replay_bundle(self.bundle_raw, self.expected_raw)
            out = self.dir / "guarded-replay"
            code = self.cli.main(["replay", "--bundle", str(self.bundle), "--expected", str(self.expected_path),
                                  "--output", str(out)])
        self.assertEqual(result["verdict"], "MODEL_PASS")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads((out / "result.json").read_bytes())["verdict"], "MODEL_PASS")
        self.assertEqual(result["expected_raw_sha256"], hashlib.sha256(self.expected_raw).hexdigest())

    def test_retained_r4t_whitespace_reaches_original_consumer(self):
        package = copy.deepcopy(self.package); package["retained"]["r4t"] += b" "
        result = self.replay(package=package)
        self.assertEqual(result["verdict"], "MODEL_REJECT")
        self.assertEqual(result["rejection_layer"], "consumer")
        self.assertEqual(result["failures"], [{"code": "RAW_HASH", "path": "r4t.raw_sha256"}])
        self.assertIn("closed_vc_dependencies", result["checked"])

    def test_catalog_and_object_ref_tampering_rejected(self):
        cases = []
        p = copy.deepcopy(self.package); p["objects"].pop(); cases.append((p, "REF"))
        p = copy.deepcopy(self.package); p["objects"].append(copy.deepcopy(p["objects"][0])); cases.append((p, "DUPLICATE"))
        p = copy.deepcopy(self.package); p["objects"][0]["content_sha256"] = "0" * 64; cases.append((p, "SEAL"))
        p = copy.deepcopy(self.package); p["vc"]["test_contract_ref"]["content_sha256"] = "0" * 64; cases.append((p, "SEAL"))
        # Add a valid sealed, unreachable node: closure, not merely bad encoding.
        p = copy.deepcopy(self.package)
        p["objects"].append(self.core._draft("SourceUnit", {"path": "inert/orphan", "raw_sha256": "1" * 64}))
        cases.append((p, "CLOSURE"))
        for package, code in cases:
            with self.subTest(code=code):
                r = self.replay(package=package)
                self.assertEqual(r["verdict"], "MODEL_REJECT"); self.assertEqual(r["rejection_layer"], "consumer")
                self.assertEqual(r["failures"][0]["code"], code)

    def test_changed_base64_bytes_rejected_by_consumer(self):
        obj = json.loads(self.bundle_raw)
        obj["package"]["retained"]["package_artifact"] = {"base64": base64.b64encode(b"other inert bytes").decode()}
        r = self.cli.replay_bundle(json.dumps(obj).encode(), self.expected_raw)
        self.assertEqual(r["rejection_layer"], "consumer")
        self.assertEqual(r["failures"], [{"code": "EXPECTED", "path": "package.raw"}])

    def test_external_expected_drift_and_explicit_empty_values(self):
        x = copy.deepcopy(self.expected); x["runtime"]["runtime_version"] = "EXTERNAL_DRIFT"
        r = self.replay(expected=x)
        self.assertEqual(r["failures"], [{"code": "EXPECTED", "path": "runtime"}])
        for value in [{}, [], None, "", 0]:
            with self.subTest(expected=value):
                r = self.replay(expected=value)
                self.assertNotEqual(r["verdict"], "MODEL_PASS")
        with self.assertRaises(ValueError):
            self.replay(package={})

    def test_pretty_compact_expected_controls(self):
        x = copy.deepcopy(self.expected); x["report_serialization"] = "compact"
        # Fixed before construction and never derived from the package.
        compact = self.core.build_prototype(x)
        raw = self.cli.encode_package(compact)
        self.assertEqual(self.cli.decode_package(raw)["retained"]["r4t"], compact["retained"]["r4t"])
        mismatch = self.cli.replay_bundle(raw, self.expected_raw)
        self.assertEqual(mismatch["failures"], [{"code": "RAW_POLICY", "path": "r4t.serialization"}])
        control = self.cli.replay_bundle(raw, json.dumps(x).encode())
        self.assertEqual(control["verdict"], "MODEL_PASS")

    def test_transport_and_expected_json_failures_have_distinct_layer(self):
        for raw in [b"", b"null", b'{"format":"x","format":"y"}']:
            r = self.cli.replay_bundle(raw, self.expected_raw)
            self.assertEqual(r["verdict"], "TRANSPORT_REJECT"); self.assertEqual(r["rejection_layer"], "transport")
            self.assertEqual(r["checked"], []); self.assert_limits(r)
        r = self.cli.replay_bundle(self.bundle_raw, b'{"x":1,"x":2}')
        self.assertEqual(r["rejection_layer"], "expected_json"); self.assertEqual(r["checked"], [])

    def test_cli_missing_expected_and_io_exit_codes(self):
        self.run_cli("replay", "--bundle", self.bundle, "--output", self.dir / "out", want=2)
        self.run_cli("replay", "--bundle", self.bundle, "--expected", self.dir / "missing.json",
                     "--output", self.dir / "out", want=3)
        self.assertFalse((self.dir / "out").exists())

    def test_cli_reject_result_is_persisted_without_input_dump(self):
        package = copy.deepcopy(self.package); package["retained"]["r4t"] += b" "
        self.bundle.write_bytes(self.cli.encode_package(package))
        out = self.dir / "reject"
        self.run_cli("replay", "--bundle", self.bundle, "--expected", self.expected_path, "--output", out, want=2)
        r = json.loads((out / "result.json").read_bytes())
        self.assertEqual(r["failures"][0]["code"], "RAW_HASH"); self.assert_limits(r)
        self.assertNotIn("package", r); self.assertNotIn("expected", r)
        # The public error must not leak a schema exception containing input data.
        private_marker = "INERT_INPUT_NOT_FOR_LOGS"
        bad = self.dir / "bad.json"; bad.write_text(json.dumps({"extra": private_marker}))
        p = self.run_cli("build", "--inputs", bad, "--output", self.dir / "bad-out", want=2)
        self.assertNotIn(private_marker, p.stdout + p.stderr)

    def test_build_never_calls_consumer(self):
        out = self.dir / "build-only"
        with patch.object(self.cli, "load_reviewed_core", return_value=self.core), \
                patch.object(self.core, "verify_prototype", side_effect=AssertionError("build verified")), \
                contextlib.redirect_stdout(io.StringIO()):
            code = self.cli.main(["build", "--inputs", str(self.expected_path), "--output", str(out)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads((out / "build.json").read_bytes())["status"], "BUILT_UNVERIFIED")
        self.assertFalse((out / "result.json").exists())

    def test_cli_transport_reject_persisted_and_startup_failure_exit_three(self):
        obj = json.loads(self.bundle_raw); obj["profile"] = "WRONG_PROFILE"
        self.bundle.write_text(json.dumps(obj))
        out = self.dir / "transport"
        self.run_cli("replay", "--bundle", self.bundle, "--expected", self.expected_path, "--output", out, want=2)
        self.assertEqual(json.loads((out / "result.json").read_bytes())["rejection_layer"], "transport")
        err = io.StringIO()
        with patch.object(self.cli, "load_reviewed_core", side_effect=self.cli.StartupError("FIXED_DEPENDENCY_DRIFT")), \
                contextlib.redirect_stderr(err):
            code = self.cli.main(["build", "--inputs", str(self.expected_path), "--output", str(self.dir / "startup")])
        self.assertEqual(code, 3); self.assert_limits(json.loads(err.getvalue()))
        self.assertFalse((self.dir / "startup").exists())

    def test_output_existing_conflict_and_symlink_are_rejected_without_overwrite(self):
        out = self.dir / "exists"; out.mkdir(); marker = out / "marker"; marker.write_bytes(b"preserve")
        self.run_cli("replay", "--bundle", self.bundle, "--expected", self.expected_path, "--output", out, want=3)
        self.assertEqual(marker.read_bytes(), b"preserve")
        self.run_cli("build", "--inputs", self.expected_path, "--output", self.expected_path, want=2)
        self.assertEqual(self.expected_path.read_bytes(), self.expected_raw)
        self.run_cli("replay", "--bundle", self.bundle, "--expected", self.expected_path, "--output", self.dir, want=2)
        link = self.dir / "link"; link.symlink_to(out, target_is_directory=True)
        self.run_cli("build", "--inputs", self.expected_path, "--output", link / "escape", want=3)
        self.assertFalse((out / "escape").exists())
        final_link = self.dir / "final-link"; final_link.symlink_to(self.dir / "not-created")
        self.run_cli("build", "--inputs", self.expected_path, "--output", final_link, want=3)
        self.assertFalse((self.dir / "not-created").exists())

    def test_partial_new_output_is_retained_and_reported(self):
        self.assertTrue(callable(getattr(self.cli, "main", None)), "CLI main is missing")
        out = self.dir / "partial"
        original = self.cli._write_file
        calls = []
        def failing_second(fd, name, raw):
            calls.append(name)
            if len(calls) == 2:
                raise OSError("simulated second write failure")
            return original(fd, name, raw)
        err = io.StringIO()
        with patch.object(self.cli, "_write_file", failing_second), contextlib.redirect_stderr(err):
            code = self.cli.main(["build", "--inputs", str(self.expected_path), "--output", str(out)])
        self.assertEqual(code, 3); self.assertTrue((out / "bundle.json").is_file())
        self.assertIs(json.loads(err.getvalue())["output_incomplete"], True)


if __name__ == "__main__":
    unittest.main()
