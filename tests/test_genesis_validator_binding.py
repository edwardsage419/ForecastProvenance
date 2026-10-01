import importlib.util
import tempfile
import unittest
from pathlib import Path

from forecast_trust_core.canonical import verify_sealed_object


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "genesis" / "build_validator_binding.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_validator_binding", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GenesisValidatorBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_module()

    def test_binding_is_sealed_and_binds_test_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = Path(tmpdir) / "final_test_report.txt"
            report.write_text("GEN001 TEST REPORT\n", encoding="utf-8")
            contract = self.module.build_contract("a" * 40, report)

        self.assertTrue(verify_sealed_object(contract))
        self.assertEqual(contract["object_id"], "validator:forecast-trust-core-genesis:v1")
        self.assertEqual(contract["git_commit"], "a" * 40)
        self.assertEqual(contract["runtime_dependencies"], [])
        self.assertTrue(contract["source_files"])
        self.assertEqual(contract["test_report"]["filename"], "final_test_report.txt")
        paths = {row["path"] for row in contract["source_files"]}
        self.assertIn("pyproject.toml", paths)
        self.assertIn("src/forecast_trust_core/canonical.py", paths)

    def test_invalid_commit_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            report = Path(tmpdir) / "report.txt"
            report.write_text("x", encoding="utf-8")
            with self.assertRaises(ValueError):
                self.module.build_contract("not-a-commit", report)


if __name__ == "__main__":
    unittest.main()
