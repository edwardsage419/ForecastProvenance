import unittest

from forecast_trust_core.genesis_sources import (
    GenesisSourceParseError,
    adapt_bea_real_gdp_advance_html,
    adapt_bls_cpi_html,
    adapt_bls_u3_html,
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

    def test_baseline_accepts_exact_cutoff_boundary(self):
        rows = [{
            "target_family": "CPI_U",
            "reference_period": "2026-07",
            "release_stage": "FIRST",
            "available_at": "2026-08-10T00:00:00Z",
        }]
        selected = select_baseline_first_release(
            rows,
            target_family="CPI_U",
            previous_reference_period="2026-07",
            information_cutoff="2026-08-10T00:00:00Z",
        )
        self.assertIs(selected, rows[0])

    def test_baseline_rejects_noncanonical_offset_timestamp(self):
        rows = [{
            "target_family": "CPI_U",
            "reference_period": "2026-07",
            "release_stage": "FIRST",
            "available_at": "2026-08-12T00:30:00-01:00",
        }]
        with self.assertRaises(GenesisSourceParseError):
            select_baseline_first_release(
                rows,
                target_family="CPI_U",
                previous_reference_period="2026-07",
                information_cutoff="2026-08-12T00:45:00Z",
            )

    def test_baseline_rejects_malformed_cutoff_timestamp(self):
        rows = [{
            "target_family": "CPI_U",
            "reference_period": "2026-07",
            "release_stage": "FIRST",
            "available_at": "2026-08-10T00:00:00Z",
        }]
        with self.assertRaises(GenesisSourceParseError):
            select_baseline_first_release(
                rows,
                target_family="CPI_U",
                previous_reference_period="2026-07",
                information_cutoff="2026-08-10 00:00:00",
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

    def test_official_artifact_rejects_non_https_url(self):
        with self.assertRaises(GenesisSourceParseError):
            validate_official_artifact(
                {
                    "resolved_url": "http://www.bls.gov/news.release/cpi.htm",
                    "raw_sha256": "a" * 64,
                    "http_status": 200,
                },
                allowed_hosts=["www.bls.gov"],
            )

    def test_raw_cpi_adapter_to_semantic_parser(self):
        raw = b"""
        <html><body>
        <h1>CONSUMER PRICE INDEX - JULY 2026</h1>
        <p>The Consumer Price Index for All Urban Consumers (CPI-U) increased 0.1 percent on a seasonally adjusted basis in July after falling 0.4 percent in June.</p>
        </body></html>
        """
        records = adapt_bls_cpi_html(raw, reference_month="2026-07")
        result = parse_cpi_first_release(records, reference_month="2026-07")
        self.assertEqual(result.display_value, "0.1")

    def test_raw_cpi_adapter_preserves_negative_direction(self):
        raw = b"""
        <html><body>
        <h1>CONSUMER PRICE INDEX - JUNE 2026</h1>
        <p>The Consumer Price Index for All Urban Consumers (CPI-U) fell 0.4 percent on a seasonally adjusted basis in June.</p>
        </body></html>
        """
        records = adapt_bls_cpi_html(raw, reference_month="2026-06")
        result = parse_cpi_first_release(records, reference_month="2026-06")
        self.assertEqual(result.display_value, "-0.4")

    def test_raw_u3_adapter_to_semantic_parser(self):
        raw = b"""
        <html><body>
        <h1>THE EMPLOYMENT SITUATION - AUGUST 2026</h1>
        <p>The unemployment rate was unchanged at 4.1 percent in August, and the number of unemployed people changed little.</p>
        </body></html>
        """
        records = adapt_bls_u3_html(raw, reference_month="2026-08")
        result = parse_u3_first_release(records, reference_month="2026-08")
        self.assertEqual(result.display_value, "4.1")

    def test_raw_gdp_advance_adapter_to_semantic_parser(self):
        raw = b"""
        <html><body>
        <h1>GDP (Advance Estimate), 2nd Quarter 2026</h1>
        <p>Real gross domestic product (GDP) increased at an annual rate of 1.5 percent in the 2nd quarter of 2026 (April, May, and June), according to the advance estimate released today by the U.S. Bureau of Economic Analysis (BEA).</p>
        </body></html>
        """
        records = adapt_bea_real_gdp_advance_html(raw, reference_quarter="2026-Q2")
        result = parse_real_gdp_advance(records, reference_quarter="2026-Q2")
        self.assertEqual(result.display_value, "1.5")

    def test_raw_gdp_adapter_rejects_second_estimate_page(self):
        raw = b"""
        <html><body>
        <h1>GDP (Second Estimate) and Corporate Profits, 2nd Quarter 2026</h1>
        <p>Real gross domestic product (GDP) increased at an annual rate of 1.5 percent in the 2nd quarter of 2026, according to the second estimate released today.</p>
        </body></html>
        """
        with self.assertRaises(GenesisSourceParseError):
            adapt_bea_real_gdp_advance_html(raw, reference_quarter="2026-Q2")

    def test_raw_adapters_fail_on_reference_period_mismatch(self):
        raw = b"""
        <html><body>
        <h1>THE EMPLOYMENT SITUATION - AUGUST 2026</h1>
        <p>The unemployment rate was unchanged at 4.1 percent in August.</p>
        </body></html>
        """
        with self.assertRaises(GenesisSourceParseError):
            adapt_bls_u3_html(raw, reference_month="2026-07")


if __name__ == "__main__":
    unittest.main()
