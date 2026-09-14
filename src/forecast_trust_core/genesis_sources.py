from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from html.parser import HTMLParser
from typing import Any, Mapping, Sequence
import re
from urllib.parse import urlparse

_DECIMAL = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_MONTHS = {
    "01": "January", "02": "February", "03": "March", "04": "April",
    "05": "May", "06": "June", "07": "July", "08": "August",
    "09": "September", "10": "October", "11": "November", "12": "December",
}
_QUARTERS = {"Q1": "1st", "Q2": "2nd", "Q3": "3rd", "Q4": "4th"}


class GenesisSourceParseError(ValueError):
    pass


@dataclass(frozen=True)
class ReleasedDecimal:
    display_value: str
    canonical_decimal: str
    display_scale: int


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag.lower() in {"script", "style", "noscript"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth and data.strip():
            self.parts.append(data)


def html_visible_text(raw_html: bytes) -> str:
    if not isinstance(raw_html, (bytes, bytearray)) or not raw_html:
        raise GenesisSourceParseError("raw HTML must be non-empty bytes")
    try:
        text = bytes(raw_html).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise GenesisSourceParseError("official HTML is not valid UTF-8") from exc
    parser = _VisibleTextParser()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:
        raise GenesisSourceParseError("official HTML could not be parsed") from exc
    normalized = " ".join(" ".join(parser.parts).split())
    if not normalized:
        raise GenesisSourceParseError("official HTML contains no visible text")
    return normalized


def parse_released_decimal(value: Any) -> ReleasedDecimal:
    if not isinstance(value, str):
        raise GenesisSourceParseError("released value must be a string")
    raw = value.strip()
    if raw != value:
        raise GenesisSourceParseError("released value contains surrounding whitespace")
    if not _DECIMAL.fullmatch(raw):
        raise GenesisSourceParseError("released value is not a plain decimal")
    try:
        dec = Decimal(raw)
    except InvalidOperation as exc:
        raise GenesisSourceParseError("invalid released decimal") from exc
    scale = len(raw.split(".", 1)[1]) if "." in raw else 0
    if dec == 0:
        canonical = "0"
    else:
        canonical = format(dec, "f")
        if "." in canonical:
            canonical = canonical.rstrip("0").rstrip(".")
    return ReleasedDecimal(raw, canonical, scale)


def validate_official_artifact(
    artifact: Mapping[str, Any],
    *,
    allowed_hosts: Sequence[str],
    expected_sha256: str | None = None,
) -> None:
    url = artifact.get("resolved_url")
    sha = artifact.get("raw_sha256")
    if not isinstance(url, str):
        raise GenesisSourceParseError("resolved_url missing")
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise GenesisSourceParseError("artifact URL must use HTTPS")
    host = (parsed.hostname or "").lower()
    allowed = {h.lower() for h in allowed_hosts}
    if host not in allowed:
        raise GenesisSourceParseError("artifact host is not admitted")
    if not isinstance(sha, str) or not _HEX64.fullmatch(sha):
        raise GenesisSourceParseError("artifact SHA256 is malformed")
    if expected_sha256 is not None and sha != expected_sha256:
        raise GenesisSourceParseError("artifact SHA256 mismatch")
    if artifact.get("http_status") != 200:
        raise GenesisSourceParseError("artifact HTTP status is not 200")


def _unique_match(
    records: Sequence[Mapping[str, Any]],
    predicate,
    *,
    label: str,
) -> Mapping[str, Any]:
    matches = [row for row in records if predicate(row)]
    if len(matches) != 1:
        raise GenesisSourceParseError(
            f"{label} expected exactly one semantic match, found {len(matches)}"
        )
    return matches[0]


def _first_release_guard(row: Mapping[str, Any]) -> None:
    if row.get("release_stage") != "FIRST":
        raise GenesisSourceParseError("record is not a first-release value")


def _month_label(reference_month: str) -> tuple[str, str]:
    match = re.fullmatch(r"(\d{4})-(\d{2})", reference_month)
    if not match or match.group(2) not in _MONTHS:
        raise GenesisSourceParseError("reference month must use YYYY-MM")
    return match.group(1), _MONTHS[match.group(2)]


def _quarter_label(reference_quarter: str) -> tuple[str, str]:
    match = re.fullmatch(r"(\d{4})-(Q[1-4])", reference_quarter)
    if not match:
        raise GenesisSourceParseError("reference quarter must use YYYY-QN")
    return match.group(1), _QUARTERS[match.group(2)]


def _signed_change(direction: str, magnitude: str) -> str:
    value = parse_released_decimal(magnitude)
    if direction.lower() in {"decreased", "declined", "fell", "dropped"}:
        return "0" if value.canonical_decimal == "0" else f"-{value.display_value}"
    if direction.lower() in {"increased", "rose", "grew"}:
        return value.display_value
    raise GenesisSourceParseError("unrecognized change direction")


def adapt_bls_cpi_html(raw_html: bytes, *, reference_month: str) -> list[dict[str, Any]]:
    year, month = _month_label(reference_month)
    text = html_visible_text(raw_html)
    heading = f"CONSUMER PRICE INDEX - {month.upper()} {year}"
    if heading not in text.upper():
        raise GenesisSourceParseError("CPI release heading does not match reference month")
    pattern = re.compile(
        rf"Consumer Price Index for All Urban Consumers \(CPI-U\) "
        rf"(increased|rose|decreased|declined|fell|dropped) "
        rf"([0-9]+(?:\.[0-9]+)?) percent on a seasonally adjusted basis in {re.escape(month)}\b",
        re.IGNORECASE,
    )
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise GenesisSourceParseError(f"CPI raw adapter expected one headline value, found {len(matches)}")
    display_value = _signed_change(matches[0][0], matches[0][1])
    return [{
        "target_family": "CPI_U",
        "reference_period": reference_month,
        "item": "All items",
        "adjustment": "SEASONALLY_ADJUSTED",
        "measure": "PERCENT_CHANGE_FROM_PRECEDING_MONTH",
        "table_semantics": "CPI_TABLE_1",
        "release_stage": "FIRST",
        "display_value": display_value,
        "adapter_evidence": "CPI_U_HEADLINE_CORROBORATES_TABLE_1_TARGET",
    }]


def adapt_bls_u3_html(raw_html: bytes, *, reference_month: str) -> list[dict[str, Any]]:
    year, month = _month_label(reference_month)
    text = html_visible_text(raw_html)
    heading = f"THE EMPLOYMENT SITUATION - {month.upper()} {year}"
    if heading not in text.upper():
        raise GenesisSourceParseError("Employment Situation heading does not match reference month")
    pattern = re.compile(
        rf"The unemployment rate [^.]*? at ([0-9]+(?:\.[0-9]+)?) percent in {re.escape(month)}\b",
        re.IGNORECASE,
    )
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise GenesisSourceParseError(f"U-3 raw adapter expected one total unemployment-rate value, found {len(matches)}")
    return [{
        "target_family": "CPS_LABOR_FORCE",
        "reference_period": reference_month,
        "population_scope": "TOTAL",
        "measure": "U3_UNEMPLOYMENT_RATE",
        "adjustment": "SEASONALLY_ADJUSTED",
        "table_semantics": "EMPLOYMENT_TABLE_A1",
        "release_stage": "FIRST",
        "display_value": matches[0],
        "adapter_evidence": "HOUSEHOLD_SURVEY_TOTAL_RATE_CORROBORATES_TABLE_A1_TARGET",
    }]


def adapt_bea_real_gdp_advance_html(raw_html: bytes, *, reference_quarter: str) -> list[dict[str, Any]]:
    year, quarter_ordinal = _quarter_label(reference_quarter)
    text = html_visible_text(raw_html)
    heading_pattern = re.compile(
        rf"GDP \(Advance Estimate\), {re.escape(quarter_ordinal)} Quarter {re.escape(year)}",
        re.IGNORECASE,
    )
    if len(heading_pattern.findall(text)) != 1:
        raise GenesisSourceParseError("GDP page is not uniquely identified as the requested Advance Estimate")
    pattern = re.compile(
        rf"Real gross domestic product \(GDP\) (increased|decreased|declined|fell) "
        rf"at an annual rate of ([0-9]+(?:\.[0-9]+)?) percent in the "
        rf"{re.escape(quarter_ordinal)} quarter of {re.escape(year)} .*?"
        rf"according to the advance estimate released today",
        re.IGNORECASE,
    )
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise GenesisSourceParseError(f"GDP raw adapter expected one advance-estimate value, found {len(matches)}")
    display_value = _signed_change(matches[0][0], matches[0][1])
    return [{
        "target_family": "REAL_GDP",
        "reference_period": reference_quarter,
        "measure": "PERCENT_CHANGE_FROM_PRECEDING_PERIOD",
        "seasonal_basis": "SAAR",
        "estimate_type": "ADVANCE_ESTIMATE",
        "table_semantics": "NIPA_TABLE_1_1_1",
        "release_stage": "FIRST",
        "display_value": display_value,
        "adapter_evidence": "BEA_ADVANCE_HEADLINE_CORROBORATES_NIPA_1_1_1_TARGET",
    }]


def parse_cpi_first_release(
    records: Sequence[Mapping[str, Any]], *, reference_month: str
) -> ReleasedDecimal:
    row = _unique_match(
        records,
        lambda r: (
            r.get("target_family") == "CPI_U"
            and r.get("reference_period") == reference_month
            and r.get("item") == "All items"
            and r.get("adjustment") == "SEASONALLY_ADJUSTED"
            and r.get("measure") == "PERCENT_CHANGE_FROM_PRECEDING_MONTH"
            and r.get("table_semantics") == "CPI_TABLE_1"
        ),
        label="CPI first release",
    )
    _first_release_guard(row)
    return parse_released_decimal(row.get("display_value"))


def parse_u3_first_release(
    records: Sequence[Mapping[str, Any]], *, reference_month: str
) -> ReleasedDecimal:
    row = _unique_match(
        records,
        lambda r: (
            r.get("target_family") == "CPS_LABOR_FORCE"
            and r.get("reference_period") == reference_month
            and r.get("population_scope") == "TOTAL"
            and r.get("measure") == "U3_UNEMPLOYMENT_RATE"
            and r.get("adjustment") == "SEASONALLY_ADJUSTED"
            and r.get("table_semantics") == "EMPLOYMENT_TABLE_A1"
        ),
        label="U-3 first release",
    )
    _first_release_guard(row)
    return parse_released_decimal(row.get("display_value"))


def parse_real_gdp_advance(
    records: Sequence[Mapping[str, Any]], *, reference_quarter: str
) -> ReleasedDecimal:
    row = _unique_match(
        records,
        lambda r: (
            r.get("target_family") == "REAL_GDP"
            and r.get("reference_period") == reference_quarter
            and r.get("measure") == "PERCENT_CHANGE_FROM_PRECEDING_PERIOD"
            and r.get("seasonal_basis") == "SAAR"
            and r.get("estimate_type") == "ADVANCE_ESTIMATE"
            and r.get("table_semantics") == "NIPA_TABLE_1_1_1"
        ),
        label="real GDP advance estimate",
    )
    _first_release_guard(row)
    return parse_released_decimal(row.get("display_value"))


def select_baseline_first_release(
    records: Sequence[Mapping[str, Any]],
    *,
    target_family: str,
    previous_reference_period: str,
    information_cutoff: str,
) -> Mapping[str, Any]:
    matches = [
        row
        for row in records
        if row.get("target_family") == target_family
        and row.get("reference_period") == previous_reference_period
        and row.get("release_stage") == "FIRST"
    ]
    if len(matches) != 1:
        raise GenesisSourceParseError(
            f"baseline expected exactly one preceding first release, found {len(matches)}"
        )
    row = matches[0]
    available_at = row.get("available_at")
    if not isinstance(available_at, str):
        raise GenesisSourceParseError("baseline availability is unknown")
    if available_at > information_cutoff:
        raise GenesisSourceParseError("baseline first release was unavailable at cutoff")
    return row
