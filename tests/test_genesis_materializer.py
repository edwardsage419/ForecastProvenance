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
    def test_materialized_inventory_is_deterministic_and_non_prospective(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "inventory.json"
            result = run_materializer("--output", str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            inventory = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(inventory["candidate_version"], "0.7")
        self.assertEqual(inventory["object_count"], 21)
        self.assertIs(inventory["prospective_eligible"], False)
        self.assertEqual(inventory["base_file"], "candidate_object_set_v0_2.json")
        self.assertEqual(inventory["patch_file"], "candidate_patch_v0_7.json")
        self.assertEqual(
            inventory["patch_chain"],
            [
                "candidate_patch_v0_3.json",
                "candidate_patch_v0_4.json",
                "candidate_patch_v0_5.json",
                "candidate_patch_v0_6.json",
                "candidate_patch_v0_7.json",
            ],
        )
        ids = [obj["object_id"] for obj in inventory["objects"]]
        self.assertEqual(ids, sorted(ids))
        self.assertIn("policy:deadline-receipt-quorum:v4", ids)
        self.assertNotIn("policy:deadline-receipt-quorum:v1", ids)
        self.assertNotIn("policy:deadline-receipt-quorum:v2", ids)
        self.assertNotIn("policy:deadline-receipt-quorum:v3", ids)
        self.assertIn("policy:genesis-evaluation:v2", ids)
        self.assertIn("policy:genesis-acceptance:v2", ids)
        core = {key: value for key, value in inventory.items() if key != "inventory_sha256"}
        self.assertEqual(inventory["inventory_sha256"], sha256_hex(canonical_json(core)))

    def test_stdout_output_is_reproducible(self):
        first = run_materializer()
        second = run_materializer()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_v7_retirement_hash_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            patch_v3 = tmp / PATCH_V3.name
            patch_v4 = tmp / PATCH_V4.name
            patch_v5 = tmp / PATCH_V5.name
            patch_v6 = tmp / PATCH_V6.name
            patch_v7 = tmp / PATCH_V7.name
            for source, target in (
                (PATCH_V3, patch_v3),
                (PATCH_V4, patch_v4),
                (PATCH_V5, patch_v5),
                (PATCH_V6, patch_v6),
            ):
                target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
            tampered = json.loads(PATCH_V7.read_text(encoding="utf-8"))
            tampered["retire_objects"][0]["retires_content_sha256"] = "0" * 64
            patch_v7.write_text(
                json.dumps(tampered, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            result = run_materializer(
                "--base",
                str(BASE),
                "--patch",
                str(patch_v7),
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("retirement predecessor hash mismatch", result.stderr)


if __name__ == "__main__":
    unittest.main()