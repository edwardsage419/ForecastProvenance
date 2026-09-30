import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from forecast_trust_core.canonical import canonical_json, sha256_hex


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "genesis" / "materialize_candidate.py"
BASE = ROOT / "genesis" / "candidate" / "objects" / "candidate_object_set_v0_2.json"
PATCH_V3 = ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_3.json"
PATCH_V4 = ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_4.json"
PATCH_V5 = ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_5.json"
PATCH_V6 = ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_6.json"
PATCH_V7 = ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_7.json"
PATCH_V8 = ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_8.json"
PATCH_V9 = ROOT / "genesis" / "candidate" / "objects" / "candidate_patch_v0_9.json"
AUTHORITY = ROOT / "genesis" / "candidate" / "candidate_lineage_authority.json"

SPEC = importlib.util.spec_from_file_location("materialize_candidate", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MATERIALIZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MATERIALIZER)


def run_materializer(*extra):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ROOT / "src")
    return subprocess.run(
        [sys.executable, str(SCRIPT), *extra],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


class GenesisMaterializerTests(unittest.TestCase):
    def test_effective_selection_materializes_v06(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "inventory.json"
            result = run_materializer("--effective", "--output", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            inventory = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(inventory["candidate_version"], "0.6")
        self.assertEqual(inventory["object_count"], 21)
        self.assertIs(inventory["prospective_eligible"], False)
        self.assertIs(inventory["effective"], True)
        self.assertEqual(inventory["base_file"], "candidate_object_set_v0_2.json")
        self.assertEqual(inventory["patch_file"], "candidate_patch_v0_6.json")
        self.assertEqual(
            inventory["patch_chain"],
            [
                "candidate_patch_v0_3.json",
                "candidate_patch_v0_4.json",
                "candidate_patch_v0_5.json",
                "candidate_patch_v0_6.json",
            ],
        )
        ids = [obj["object_id"] for obj in inventory["objects"]]
        self.assertEqual(ids, sorted(ids))
        self.assertIn("policy:deadline-receipt-quorum:v3", ids)
        self.assertNotIn("policy:deadline-receipt-quorum:v1", ids)
        self.assertNotIn("policy:deadline-receipt-quorum:v2", ids)
        self.assertIn("policy:genesis-issuance-schedule:v1", ids)
        core = {key: value for key, value in inventory.items() if key != "inventory_sha256"}
        self.assertEqual(inventory["inventory_sha256"], sha256_hex(canonical_json(core)))

    def test_stdout_output_is_reproducible(self):
        first = run_materializer("--effective")
        second = run_materializer("--effective")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_historical_v06_still_materializes_unchanged_when_explicitly_selected(self):
        result = run_materializer("--patch", str(PATCH_V6))
        self.assertEqual(result.returncode, 0, result.stderr)
        inventory = json.loads(result.stdout)
        self.assertEqual(inventory["candidate_version"], "0.6")
        self.assertEqual(inventory["object_count"], 21)
        self.assertIs(inventory["effective"], False)
        ids = [obj["object_id"] for obj in inventory["objects"]]
        self.assertIn("policy:deadline-receipt-quorum:v3", ids)
        self.assertNotIn("policy:deadline-receipt-quorum:v4", ids)

    def test_historical_v07_still_materializes_unchanged_when_explicitly_selected(self):
        result = run_materializer("--patch", str(PATCH_V7))
        self.assertEqual(result.returncode, 0, result.stderr)
        inventory = json.loads(result.stdout)
        self.assertEqual(inventory["candidate_version"], "0.7")
        self.assertEqual(inventory["object_count"], 21)
        self.assertIs(inventory["effective"], False)
        self.assertIs(inventory["prospective_eligible"], False)
        ids = [obj["object_id"] for obj in inventory["objects"]]
        self.assertIn("policy:genesis-issuance-schedule:v1", ids)
        self.assertNotIn("policy:genesis-issuance-schedule:v2", ids)

    def test_historical_v08_still_materializes_unchanged_when_explicitly_selected(self):
        result = run_materializer("--patch", str(PATCH_V8))
        self.assertEqual(result.returncode, 0, result.stderr)
        inventory = json.loads(result.stdout)
        self.assertEqual(inventory["candidate_version"], "0.8")
        self.assertEqual(inventory["object_count"], 21)
        self.assertIs(inventory["effective"], False)
        self.assertIs(inventory["prospective_eligible"], False)
        ids = [obj["object_id"] for obj in inventory["objects"]]
        self.assertIn("policy:genesis-issuance-schedule:v2", ids)
        self.assertNotIn("policy:genesis-issuance-schedule:v3", ids)

    def test_v09_materialization_does_not_change_effective_selection(self):
        successor = run_materializer("--patch", str(PATCH_V9))
        effective = run_materializer("--effective")
        self.assertEqual(successor.returncode, 0, successor.stderr)
        self.assertEqual(effective.returncode, 0, effective.stderr)
        successor_inventory = json.loads(successor.stdout)
        effective_inventory = json.loads(effective.stdout)
        self.assertEqual(successor_inventory["candidate_version"], "0.9")
        self.assertIs(successor_inventory["effective"], False)
        self.assertIs(successor_inventory["prospective_eligible"], False)
        self.assertEqual(effective_inventory["candidate_version"], "0.6")
        self.assertIs(effective_inventory["effective"], True)

    def test_selection_mode_is_required(self):
        result = run_materializer()
        self.assertEqual(result.returncode, 2)

    def test_selection_modes_are_mutually_exclusive(self):
        result = run_materializer("--effective", "--patch", str(PATCH_V6))
        self.assertEqual(result.returncode, 2)

    def test_missing_authority_declaration_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            missing = Path(tmpdir) / "candidate_lineage_authority.json"
            with self.assertRaisesRegex(ValueError, "authority declaration missing"):
                MATERIALIZER.resolve_candidate_authority(missing)

    def test_malformed_authority_declaration_fails_closed(self):
        malformed_declarations = (
            "not-json",
            json.dumps({"schema_version": "1.0"}),
        )
        for declaration in malformed_declarations:
            with self.subTest(declaration=declaration):
                with tempfile.TemporaryDirectory() as tmpdir:
                    authority = Path(tmpdir) / "candidate_lineage_authority.json"
                    authority.write_text(declaration, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        MATERIALIZER.resolve_candidate_authority(authority)

    def test_authority_candidate_version_must_match_patch(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            candidate_dir = Path(tmpdir)
            objects_dir = candidate_dir / "objects"
            objects_dir.mkdir()
            (objects_dir / BASE.name).write_text(BASE.read_text(encoding="utf-8"), encoding="utf-8")
            (objects_dir / PATCH_V6.name).write_text(PATCH_V6.read_text(encoding="utf-8"), encoding="utf-8")
            authority = candidate_dir / "candidate_lineage_authority.json"
            authority.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "authority_scope": "PRE_GENESIS_CANDIDATE_SELECTION_ONLY",
                        "effective_candidate_version": "0.9",
                        "base_file": f"objects/{BASE.name}",
                        "patch_file": f"objects/{PATCH_V6.name}",
                        "prospective_eligible": False,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "candidate version mismatch"):
                MATERIALIZER.resolve_candidate_authority(authority)

    def test_authority_rejects_unsafe_paths(self):
        unsafe_paths = ("../base.json", "/tmp/base.json")
        for unsafe_path in unsafe_paths:
            with self.subTest(unsafe_path=unsafe_path):
                with tempfile.TemporaryDirectory() as tmpdir:
                    authority = Path(tmpdir) / "candidate_lineage_authority.json"
                    authority.write_text(
                        json.dumps(
                            {
                                "schema_version": "1.0",
                                "authority_scope": "PRE_GENESIS_CANDIDATE_SELECTION_ONLY",
                                "effective_candidate_version": "0.6",
                                "base_file": unsafe_path,
                                "patch_file": f"objects/{PATCH_V6.name}",
                                "prospective_eligible": False,
                            }
                        ),
                        encoding="utf-8",
                    )
                    with self.assertRaisesRegex(ValueError, "unsafe authority path"):
                        MATERIALIZER.resolve_candidate_authority(authority)

    def test_v7_retirement_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            source_patches = (PATCH_V3, PATCH_V4, PATCH_V5, PATCH_V6, PATCH_V7)
            for source in source_patches:
                (tmp / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            tampered = json.loads((tmp / PATCH_V7.name).read_text(encoding="utf-8"))
            tampered["retire_objects"][0]["retires_content_sha256"] = "0" * 64
            (tmp / PATCH_V7.name).write_text(
                json.dumps(tampered, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            result = run_materializer(
                "--base",
                str(BASE),
                "--patch",
                str(tmp / PATCH_V7.name),
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("retirement predecessor hash mismatch", result.stderr)


if __name__ == "__main__":
    unittest.main()
