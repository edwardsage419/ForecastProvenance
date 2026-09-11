from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence
import re
from urllib.parse import urlparse

_DECIMAL = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class GenesisSourceParseError(ValueError):
    pass


@dataclass(frozen=True)
class ReleasedDecimal:
    display_value: str
    canonical_decimal: str
    display_scale: int


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
    host = (urlparse(url).hostname or "").lower()
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
