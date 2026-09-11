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


class GenesisMaterializerTests(unittest.TestCase):
    def test_materialized_inventory_is_deterministic_and_non_prospective(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            output = Path(tmpdir) / "inventory.json"
            env = dict(os.environ)
            env["PYTHONPATH"] = str(ROOT / "src")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--output", str(output)],
                cwd=ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            inventory = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(inventory["candidate_version"], "0.3")
        self.assertEqual(inventory["object_count"], 22)
        self.assertIs(inventory["prospective_eligible"], False)
        self.assertEqual(inventory["base_file"], "candidate_object_set_v0_2.json")
        self.assertEqual(inventory["patch_file"], "candidate_patch_v0_3.json")
        self.assertEqual(
            [obj["object_id"] for obj in inventory["objects"]],
            sorted(obj["object_id"] for obj in inventory["objects"]),
        )
        core = {key: value for key, value in inventory.items() if key != "inventory_sha256"}
        self.assertEqual(inventory["inventory_sha256"], sha256_hex(canonical_json(core)))

    def test_stdout_output_is_reproducible(self):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(ROOT / "src")
        command = [sys.executable, str(SCRIPT)]
        first = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, check=False)
        second = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, text=True, check=False)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()
