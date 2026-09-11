import unittest

from forecast_trust_core.genesis_sources import (
    GenesisSourceParseError,
    parse_cpi_first_release,
    parse_real_gdp_advance,
    parse_released_decimal,
    parse_u3_first_release,
    select_baseline_first_release,
    validate_official_artifact,
)


class GenesisSourceParserTests(unittest.TestCase):
    def test_released_decimal_preserves_display_scale(self):
        value = parse_released_decimal("3.0")
        self.assertEqual(value.canonical_decimal, "3")
        self.assertEqual(value.display_scale, 1)

    def test_cpi_semantic_selection(self):
        rows = [{
            "target_family": "CPI_U",
            "reference_period": "2026-08",
            "item": "All items",
            "adjustment": "SEASONALLY_ADJUSTED",
            "measure": "PERCENT_CHANGE_FROM_PRECEDING_MONTH",
            "table_semantics": "CPI_TABLE_1",
            "release_stage": "FIRST",
            "display_value": "0.4",
        }]
        result = parse_cpi_first_release(rows, reference_month="2026-08")
        self.assertEqual(result.canonical_decimal, "0.4")

    def test_cpi_duplicate_semantic_match_fails(self):
        row = {
            "target_family": "CPI_U",
            "reference_period": "2026-08",
            "item": "All items",
            "adjustment": "SEASONALLY_ADJUSTED",
            "measure": "PERCENT_CHANGE_FROM_PRECEDING_MONTH",
            "table_semantics": "CPI_TABLE_1",
            "release_stage": "FIRST",
            "display_value": "0.4",
        }
        with self.assertRaises(GenesisSourceParseError):
            parse_cpi_first_release([row, dict(row)], reference_month="2026-08")

    def test_u3_rejects_u6_substitute(self):
        rows = [{
            "target_family": "CPS_LABOR_FORCE",
            "reference_period": "2026-08",
            "population_scope": "TOTAL",
            "measure": "U6_LABOR_UNDERUTILIZATION",
            "adjustment": "SEASONALLY_ADJUSTED",
            "table_semantics": "EMPLOYMENT_TABLE_A1",
            "release_stage": "FIRST",
            "display_value": "7.9",
        }]
        with self.assertRaises(GenesisSourceParseError):
            parse_u3_first_release(rows, reference_month="2026-08")

    def test_gdp_rejects_second_estimate(self):
        rows = [{
            "target_family": "REAL_GDP",
            "reference_period": "2026-Q2",
            "measure": "PERCENT_CHANGE_FROM_PRECEDING_PERIOD",
            "seasonal_basis": "SAAR",
            "estimate_type": "SECOND_ESTIMATE",
            "table_semantics": "NIPA_TABLE_1_1_1",
            "release_stage": "FIRST",
            "display_value": "3.0",
        }]
        with self.assertRaises(GenesisSourceParseError):
            parse_real_gdp_advance(rows, reference_quarter="2026-Q2")

    def test_baseline_rejects_future_first_release(self):
        rows = [{
            "target_family": "CPI_U",
            "reference_period": "2026-07",
            "release_stage": "FIRST",
            "available_at": "2026-08-12T12:30:00Z",
        }]
        with self.assertRaises(GenesisSourceParseError):
            select_baseline_first_release(
                rows,
                target_family="CPI_U",
                previous_reference_period="2026-07",
                information_cutoff="2026-08-10T00:00:00Z",
            )

    def test_official_artifact_host_and_hash(self):
        validate_official_artifact(
            {
                "resolved_url": "https://www.bls.gov/news.release/cpi.htm",
                "raw_sha256": "a" * 64,
                "http_status": 200,
            },
            allowed_hosts=["www.bls.gov"],
        )
        with self.assertRaises(GenesisSourceParseError):
            validate_official_artifact(
                {
                    "resolved_url": "https://example.com/cpi.htm",
                    "raw_sha256": "a" * 64,
                    "http_status": 200,
                },
                allowed_hosts=["www.bls.gov"],
            )


if __name__ == "__main__":
    unittest.main()
