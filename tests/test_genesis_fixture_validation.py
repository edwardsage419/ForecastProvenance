import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from forecast_trust_core.canonical import verify_sealed_object


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "genesis" / "validate_retrospective_source_fixture.py"


def load_module():
    spec = importlib.util.spec_from_file_location("validate_retrospective_source_fixture", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GenesisRetrospectiveFixtureValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.validator = load_module()

    def _write_cpi_fixture(self, root: Path, *, tamper_hash: bool = False) -> Path:
        fixture_dir = root / "bls_cpi_2026_07_first_release"
        fixture_dir.mkdir()
        raw = b"""
        <html><body>
        <h1>CONSUMER PRICE INDEX - JULY 2026</h1>
        <p>The Consumer Price Index for All Urban Consumers (CPI-U) increased 0.1 percent on a seasonally adjusted basis in July after falling 0.4 percent in June.</p>
        </body></html>
        """
        (fixture_dir / "artifact.html").write_bytes(raw)
        raw_sha = hashlib.sha256(raw).hexdigest()
        metadata = {
            "schema_version": "1.0",
            "classification": "RETROSPECTIVE_SOURCE_ADAPTER_REHEARSAL",
            "prospective_eligible": False,
            "fixture_id": "bls_cpi_2026_07_first_release",
            "source_url": "https://www.bls.gov/news.release/archives/cpi_08122026.htm",
            "resolved_url": "https://www.bls.gov/news.release/archives/cpi_08122026.htm",
            "allowed_host": "www.bls.gov",
            "http_status": 200,
            "raw_sha256": "0" * 64 if tamper_hash else raw_sha,
            "expected_target_id": "target:us-cpi-all-items-mom-sa:v1",
            "reference_period": "2026-07",
            "release_stage": "FIRST",
            "expected_semantics": {
                "target_family": "CPI_U",
                "item": "All items",
                "adjustment": "SEASONALLY_ADJUSTED",
                "measure": "PERCENT_CHANGE_FROM_PRECEDING_MONTH",
                "table_semantics": "CPI_TABLE_1",
            },
            "expected_display_value": "0.1",
            "expected_canonical_decimal": "0.1",
            "expected_display_scale": 1,
        }
        (fixture_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return fixture_dir

    def test_valid_fixture_produces_sealed_non_prospective_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = self._write_cpi_fixture(Path(tmpdir))
            report = self.validator.validate_fixture(fixture_dir)
        self.assertTrue(verify_sealed_object(report))
        self.assertEqual(report["validation_result"], "VALID_RETROSPECTIVE_FIXTURE")
        self.assertIs(report["prospective_eligible"], False)
        self.assertEqual(report["released_display_value"], "0.1")
        self.assertEqual(report["semantic_record_count"], 1)

    def test_raw_hash_tamper_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_dir = self._write_cpi_fixture(Path(tmpdir), tamper_hash=True)
            with self.assertRaises(ValueError):
                self.validator.validate_fixture(fixture_dir)


if __name__ == "__main__":
    unittest.main()
