import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "genesis" / "fixtures" / "retrospective" / "source_fixture_manifest_v0_1.json"
SCRIPT = ROOT / "scripts" / "genesis" / "fetch_retrospective_source_fixture.py"


def load_fetch_module():
    spec = importlib.util.spec_from_file_location("fetch_retrospective_source_fixture", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GenesisRetrospectiveFixtureManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.fetcher = load_fetch_module()

    def test_manifest_is_permanently_non_prospective(self):
        self.assertEqual(self.manifest["classification"], "RETROSPECTIVE_FIXTURE_MANIFEST")
        self.assertIs(self.manifest["prospective_eligible"], False)

    def test_fixture_ids_and_expected_values_are_frozen(self):
        expected = {
            "bls_cpi_2026_07_first_release": ("2026-07", "0.1"),
            "bls_u3_2026_08_first_release": ("2026-08", "4.1"),
            "bea_gdp_2026_q2_advance": ("2026-Q2", "1.5"),
        }
        actual = {
            row["fixture_id"]: (row["reference_period"], row["expected_display_value"])
            for row in self.manifest["fixtures"]
        }
        self.assertEqual(actual, expected)

    def test_all_fixture_urls_are_https_official_hosts(self):
        for row in self.manifest["fixtures"]:
            with self.subTest(fixture_id=row["fixture_id"]):
                self.assertTrue(row["url"].startswith("https://"))
                self.assertIn(row["allowed_host"], {"www.bls.gov", "www.bea.gov"})
                self.assertIn(row["allowed_host"], row["url"])
                self.assertEqual(row["scientific_role"], "RETROSPECTIVE_SOURCE_ADAPTER_REHEARSAL_ONLY")

    def test_fetcher_rejects_non_official_redirect_target_before_network(self):
        bad = {
            "fixture_id": "bad",
            "url": "https://example.com/not-admitted",
            "allowed_host": "www.bls.gov",
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaises(ValueError):
                self.fetcher.fetch_fixture(bad, Path(tmpdir))

    def test_fetcher_blocks_cross_host_redirect_before_following(self):
        handler = self.fetcher._SameHostRedirectHandler("www.bls.gov")
        request = self.fetcher.urllib.request.Request("https://www.bls.gov/start")
        with self.assertRaises(ValueError):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "https://example.com/redirected",
            )

    def test_fetcher_blocks_https_downgrade_redirect_before_following(self):
        handler = self.fetcher._SameHostRedirectHandler("www.bls.gov")
        request = self.fetcher.urllib.request.Request("https://www.bls.gov/start")
        with self.assertRaises(ValueError):
            handler.redirect_request(
                request,
                None,
                302,
                "Found",
                {},
                "http://www.bls.gov/redirected",
            )

    def test_fetcher_manifest_loader_enforces_non_prospective_classification(self):
        loaded = self.fetcher.load_manifest(MANIFEST)
        self.assertIs(loaded["prospective_eligible"], False)
        for fixture_id in (
            "bls_cpi_2026_07_first_release",
            "bls_u3_2026_08_first_release",
            "bea_gdp_2026_q2_advance",
        ):
            selected = self.fetcher.select_fixture(loaded, fixture_id)
            self.assertEqual(selected["fixture_id"], fixture_id)


if __name__ == "__main__":
    unittest.main()
