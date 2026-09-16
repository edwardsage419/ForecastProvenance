from __future__ import annotations

import hashlib
import re
from datetime import datetime, timedelta
from typing import Any, Mapping
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from .canonical import verify_sealed_object
from .genesis_lifecycle_contract_gate_v1 import (
    validate_evidence_snapshot_contract,
    validate_schedule_snapshot_contract,
    validate_source_artifact_evidence_contract,
    validate_target_instance_contract,
)
from .genesis_sources import (
    GenesisSourceParseError,
    adapt_bea_real_gdp_advance_html,
    adapt_bls_cpi_html,
    adapt_bls_u3_html,
    html_visible_text,
    parse_cpi_first_release,
    parse_real_gdp_advance,
    parse_u3_first_release,
)


GENESIS_TIMEZONE = "America/New_York"
SCHEDULE_PARSER_VERSION = "FPP_GENESIS_SCHEDULE_HTML_V1"
FIRST_RELEASE_PARSER_VERSION = "FPP_GENESIS_FIRST_RELEASE_HTML_V1"
BASELINE_METHOD_ID = "method:last-observed-value:v1"

TARGET_PROFILES = {
    "target:us-cpi-all-items-mom-sa:v1": {
        "schedule_source_id": "source:bls-cpi-release-schedule:v1",
        "first_release_source_id": "source:bls-cpi-first-release:v1",
        "reference_kind": "MONTH",
        "schedule_kind": "BLS_CPI",
    },
    "target:us-unemployment-rate-u3-sa:v1": {
        "schedule_source_id": "source:bls-employment-situation-schedule:v1",
        "first_release_source_id": "source:bls-u3-first-release:v1",
        "reference_kind": "MONTH",
        "schedule_kind": "BLS_EMPSIT",
    },
    "target:us-real-gdp-qoq-saar-advance:v1": {
        "schedule_source_id": "source:bea-gdp-release-schedule:v1",
        "first_release_source_id": "source:bea-real-gdp-advance:v1",
        "reference_kind": "QUARTER",
        "schedule_kind": "BEA_GDP_ADVANCE",
    },
}

_MONTH_NAMES = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}
_MONTH_NUMBERS = {name.lower(): number for number, name in _MONTH_NAMES.items()}
_MONTH_NUMBERS.update({name[:3].lower(): number for number, name in _MONTH_NAMES.items()})
_QUARTER_ORDINAL = {1: "1st", 2: "2nd", 3: "3rd", 4: "4th"}


class GenesisSourceAuthorityError(ValueError):
    pass


def _fail(message: str) -> None:
    raise GenesisSourceAuthorityError(message)


def _exact_ref(obj: Mapping[str, Any], *, object_type: str | None = None) -> dict[str, str]:
    if not isinstance(obj, Mapping) or not verify_sealed_object(obj):
        _fail("authority input must be a valid sealed object")
    if object_type is not None and obj.get("object_type") != object_type:
        _fail(f"expected object_type {object_type}")
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def _profile(target_definition: Mapping[str, Any]) -> Mapping[str, str]:
    _exact_ref(target_definition, object_type="TargetDefinition")
    profile = TARGET_PROFILES.get(target_definition.get("object_id"))
    if profile is None:
        _fail("target is outside the Genesis v1 source-authority profile")
    return profile


def _validate_source_contract(
    source_contract: Mapping[str, Any],
    *,
    expected_id: str,
    artifact_evidence: Mapping[str, Any],
    raw_bytes: bytes,
    require_primary_url: bool,
) -> None:
    _exact_ref(source_contract, object_type="SourceContract")
    validate_source_artifact_evidence_contract(artifact_evidence)
    if source_contract.get("object_id") != expected_id:
        _fail("SourceContract semantic identity mismatch")
    if artifact_evidence.get("source_contract_ref") != _exact_ref(source_contract):
        _fail("SourceArtifactEvidence does not bind the exact SourceContract")
    if source_contract.get("access_mode") != "HTTPS_PUBLIC":
        _fail("Genesis v1 SourceContract must use HTTPS_PUBLIC")
    allowed_hosts = source_contract.get("allowed_hosts")
    if not isinstance(allowed_hosts, list) or not allowed_hosts or any(
        not isinstance(item, str) or not item for item in allowed_hosts
    ):
        _fail("SourceContract allowed_hosts invalid")
    resolved = artifact_evidence.get("resolved_url")
    host = (urlparse(resolved).hostname or "").lower()
    if host not in {item.lower() for item in allowed_hosts}:
        _fail("resolved artifact host is not admitted by SourceContract")
    if require_primary_url and resolved != source_contract.get("primary_url"):
        _fail("schedule artifact resolved_url must equal frozen SourceContract primary_url")
    if not isinstance(raw_bytes, (bytes, bytearray)) or not raw_bytes:
        _fail("retained raw artifact bytes are required")
    digest = hashlib.sha256(bytes(raw_bytes)).hexdigest()
    if digest != artifact_evidence.get("raw_sha256"):
        _fail("retained raw artifact SHA256 mismatch")


def _month_reference(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([0-9]{4})-([0-9]{2})", value or "")
    if match is None:
        _fail("monthly reference period must use YYYY-MM")
    year, month = int(match.group(1)), int(match.group(2))
    if month not in _MONTH_NAMES:
        _fail("monthly reference period month invalid")
    return year, month


def _quarter_reference(value: str) -> tuple[int, int]:
    match = re.fullmatch(r"([0-9]{4})-Q([1-4])", value or "")
    if match is None:
        _fail("quarterly reference period must use YYYY-QN")
    return int(match.group(1)), int(match.group(2))


def immediately_preceding_reference_period(target_definition: Mapping[str, Any], current: str) -> str:
    profile = _profile(target_definition)
    if profile["reference_kind"] == "MONTH":
        year, month = _month_reference(current)
        if month == 1:
            return f"{year - 1:04d}-12"
        return f"{year:04d}-{month - 1:02d}"
    year, quarter = _quarter_reference(current)
    if quarter == 1:
        return f"{year - 1:04d}-Q4"
    return f"{year:04d}-Q{quarter - 1}"


def _parse_date(month_name: str, day: str, year: str) -> str:
    key = month_name.rstrip(".").lower()
    month = _MONTH_NUMBERS.get(key)
    if month is None:
        _fail("schedule release month invalid")
    try:
        parsed = datetime(int(year), month, int(day))
    except ValueError as exc:
        raise GenesisSourceAuthorityError("schedule release date invalid") from exc
    return parsed.strftime("%Y-%m-%d")


def _parse_clock(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value.strip().upper())
    try:
        parsed = datetime.strptime(normalized, "%I:%M %p")
    except ValueError as exc:
        raise GenesisSourceAuthorityError("schedule release time invalid") from exc
    return parsed.strftime("%H:%M:%S")


def _parse_bls_schedule(raw_html: bytes, *, reference_period: str, title: str, release_id: str) -> dict[str, str]:
    year, month = _month_reference(reference_period)
    text = html_visible_text(raw_html)
    heading = f"Schedule of Releases for the {title}"
    if heading.lower() not in text.lower():
        _fail("BLS schedule page identity mismatch")
    reference_label = f"{_MONTH_NAMES[month]} {year}"
    pattern = re.compile(
        rf"\b{re.escape(reference_label)}\s+"
        rf"(?P<month>[A-Za-z]+\.?)\s+(?P<day>[0-9]{{1,2}}),\s+(?P<year>[0-9]{{4}})\s+"
        rf"(?P<time>[0-9]{{1,2}}:[0-9]{{2}}\s+[AP]M)\b",
        re.IGNORECASE,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        _fail(f"BLS schedule expected one row for {reference_period}, found {len(matches)}")
    match = matches[0]
    return {
        "parsed_release_identifier": f"{release_id}:{reference_period}",
        "reference_period": reference_period,
        "published_release_date": _parse_date(match.group("month"), match.group("day"), match.group("year")),
        "published_release_time": _parse_clock(match.group("time")),
        "published_timezone": GENESIS_TIMEZONE,
        "parser_version": SCHEDULE_PARSER_VERSION,
    }


def _parse_bea_gdp_schedule(raw_html: bytes, *, reference_period: str) -> dict[str, str]:
    year, quarter = _quarter_reference(reference_period)
    text = html_visible_text(raw_html)
    if "Release Schedule" not in text:
        _fail("BEA schedule page identity mismatch")
    ordinal = _QUARTER_ORDINAL[quarter]
    pattern = re.compile(
        rf"(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)\s+"
        rf"(?P<day>[0-9]{{1,2}})\s+"
        rf"(?P<time>[0-9]{{1,2}}:[0-9]{{2}}\s+[AP]M)\s+"
        rf"(?:N\s*ews\s+)?GDP\s*\(Advance Estimate\),\s*{ordinal}\s+Quarter\s+{year}\b",
        re.IGNORECASE,
    )
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        _fail(f"BEA schedule expected one Advance Estimate row for {reference_period}, found {len(matches)}")
    match = matches[0]
    return {
        "parsed_release_identifier": f"BEA_GDP_ADVANCE:{reference_period}",
        "reference_period": reference_period,
        "published_release_date": _parse_date(match.group("month"), match.group("day"), str(year)),
        "published_release_time": _parse_clock(match.group("time")),
        "published_timezone": GENESIS_TIMEZONE,
        "parser_version": SCHEDULE_PARSER_VERSION,
    }


def recompute_schedule_fields(
    target_definition: Mapping[str, Any],
    source_contract: Mapping[str, Any],
    artifact_evidence: Mapping[str, Any],
    raw_bytes: bytes,
    *,
    reference_period: str,
) -> dict[str, str]:
    profile = _profile(target_definition)
    expected_schedule_ref = target_definition.get("schedule_source_ref")
    if expected_schedule_ref != _exact_ref(source_contract, object_type="SourceContract"):
        _fail("TargetDefinition schedule_source_ref mismatch")
    _validate_source_contract(
        source_contract,
        expected_id=profile["schedule_source_id"],
        artifact_evidence=artifact_evidence,
        raw_bytes=raw_bytes,
        require_primary_url=True,
    )
    kind = profile["schedule_kind"]
    if kind == "BLS_CPI":
        return _parse_bls_schedule(
            bytes(raw_bytes), reference_period=reference_period,
            title="Consumer Price Index", release_id="BLS_CPI",
        )
    if kind == "BLS_EMPSIT":
        return _parse_bls_schedule(
            bytes(raw_bytes), reference_period=reference_period,
            title="Employment Situation", release_id="BLS_EMPSIT",
        )
    return _parse_bea_gdp_schedule(bytes(raw_bytes), reference_period=reference_period)


def validate_schedule_snapshot_authoritatively(
    schedule_snapshot: Mapping[str, Any],
    target_definition: Mapping[str, Any],
    source_contract: Mapping[str, Any],
    artifact_evidence: Mapping[str, Any],
    raw_bytes: bytes,
) -> None:
    validate_schedule_snapshot_contract(schedule_snapshot)
    expected = recompute_schedule_fields(
        target_definition,
        source_contract,
        artifact_evidence,
        raw_bytes,
        reference_period=schedule_snapshot["reference_period"],
    )
    if schedule_snapshot.get("schedule_source_contract_ref") != _exact_ref(source_contract):
        _fail("ScheduleSnapshot SourceContract mismatch")
    if schedule_snapshot.get("source_artifact_evidence_ref") != _exact_ref(
        artifact_evidence, object_type="SourceArtifactEvidence"
    ):
        _fail("ScheduleSnapshot source artifact evidence mismatch")
    for field, value in expected.items():
        if schedule_snapshot.get(field) != value:
            _fail(f"ScheduleSnapshot {field} differs from deterministic parser output")


def _local_release_to_utc(date_value: str, time_value: str) -> str:
    try:
        naive = datetime.strptime(f"{date_value}T{time_value}", "%Y-%m-%dT%H:%M:%S")
    except ValueError as exc:
        raise GenesisSourceAuthorityError("release date/time invalid") from exc
    zone = ZoneInfo(GENESIS_TIMEZONE)
    local = naive.replace(tzinfo=zone, fold=0)
    roundtrip = local.astimezone(ZoneInfo("UTC")).astimezone(zone).replace(tzinfo=None)
    if roundtrip != naive:
        _fail("published local release time is nonexistent under America/New_York")
    alternate = naive.replace(tzinfo=zone, fold=1)
    if local.utcoffset() != alternate.utcoffset():
        _fail("published local release time is ambiguous under America/New_York")
    return local.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")


def validate_target_instance_authoritatively(
    target_instance: Mapping[str, Any],
    target_definition: Mapping[str, Any],
    schedule_snapshot: Mapping[str, Any],
) -> None:
    validate_target_instance_contract(target_instance)
    validate_schedule_snapshot_contract(schedule_snapshot)
    if target_instance.get("target_definition_ref") != _exact_ref(target_definition, object_type="TargetDefinition"):
        _fail("TargetInstance target definition mismatch")
    if target_instance.get("schedule_snapshot_ref") != _exact_ref(schedule_snapshot, object_type="ScheduleSnapshot"):
        _fail("TargetInstance schedule snapshot mismatch")
    if target_instance.get("reference_period") != schedule_snapshot.get("reference_period"):
        _fail("TargetInstance reference period differs from schedule snapshot")
    expected_barrier = _local_release_to_utc(
        schedule_snapshot["published_release_date"], schedule_snapshot["published_release_time"]
    )
    if target_instance.get("outcome_information_barrier") != expected_barrier:
        _fail("TargetInstance outcome information barrier differs from schedule-derived UTC")


def _parse_first_release_value(target_definition: Mapping[str, Any], raw_bytes: bytes, reference_period: str) -> str:
    target_id = target_definition.get("object_id")
    try:
        if target_id == "target:us-cpi-all-items-mom-sa:v1":
            rows = adapt_bls_cpi_html(raw_bytes, reference_month=reference_period)
            return parse_cpi_first_release(rows, reference_month=reference_period).canonical_decimal
        if target_id == "target:us-unemployment-rate-u3-sa:v1":
            rows = adapt_bls_u3_html(raw_bytes, reference_month=reference_period)
            return parse_u3_first_release(rows, reference_month=reference_period).canonical_decimal
        if target_id == "target:us-real-gdp-qoq-saar-advance:v1":
            rows = adapt_bea_real_gdp_advance_html(raw_bytes, reference_quarter=reference_period)
            return parse_real_gdp_advance(rows, reference_quarter=reference_period).canonical_decimal
    except GenesisSourceParseError as exc:
        raise GenesisSourceAuthorityError(str(exc)) from exc
    _fail("target is outside the Genesis v1 first-release parser profile")


def validate_baseline_evidence_snapshot_authoritatively(
    evidence_snapshot: Mapping[str, Any],
    *,
    method: Mapping[str, Any],
    target_definition: Mapping[str, Any],
    current_target_instance: Mapping[str, Any],
    preceding_target_instance: Mapping[str, Any],
    first_release_source_contract: Mapping[str, Any],
    first_release_artifact_evidence: Mapping[str, Any],
    first_release_raw_bytes: bytes,
) -> str:
    validate_evidence_snapshot_contract(evidence_snapshot)
    validate_target_instance_contract(current_target_instance)
    validate_target_instance_contract(preceding_target_instance)
    profile = _profile(target_definition)
    if method.get("object_id") != BASELINE_METHOD_ID or _exact_ref(method, object_type="ForecastMethod") != evidence_snapshot.get("method_ref"):
        _fail("EvidenceSnapshot must bind exact Genesis baseline method")
    if evidence_snapshot.get("current_target_instance_ref") != _exact_ref(current_target_instance, object_type="TargetInstance"):
        _fail("EvidenceSnapshot current target instance mismatch")
    if evidence_snapshot.get("preceding_target_instance_ref") != _exact_ref(preceding_target_instance, object_type="TargetInstance"):
        _fail("EvidenceSnapshot preceding target instance mismatch")
    if current_target_instance.get("target_definition_ref") != _exact_ref(target_definition):
        _fail("current TargetInstance target definition mismatch")
    if preceding_target_instance.get("target_definition_ref") != _exact_ref(target_definition):
        _fail("preceding TargetInstance target definition mismatch")
    expected_previous = immediately_preceding_reference_period(
        target_definition, current_target_instance["reference_period"]
    )
    if preceding_target_instance.get("reference_period") != expected_previous:
        _fail("preceding TargetInstance is not the immediately preceding reference period")
    if evidence_snapshot.get("information_cutoff") != current_target_instance.get("outcome_information_barrier"):
        # The exact cutoff is bound by the cycle plan in R6-C. Here we only
        # prohibit a snapshot cutoff after the current target barrier.
        if evidence_snapshot["information_cutoff"] > current_target_instance["outcome_information_barrier"]:
            _fail("EvidenceSnapshot information cutoff is after outcome barrier")
    expected_source_ref = target_definition.get("measurement_source_ref")
    if expected_source_ref != _exact_ref(first_release_source_contract, object_type="SourceContract"):
        _fail("TargetDefinition measurement_source_ref mismatch")
    if first_release_source_contract.get("object_id") != profile["first_release_source_id"]:
        _fail("wrong first-release SourceContract for target")
    _validate_source_contract(
        first_release_source_contract,
        expected_id=profile["first_release_source_id"],
        artifact_evidence=first_release_artifact_evidence,
        raw_bytes=first_release_raw_bytes,
        require_primary_url=False,
    )
    if evidence_snapshot.get("preceding_first_release_source_contract_ref") != _exact_ref(first_release_source_contract):
        _fail("EvidenceSnapshot first-release SourceContract mismatch")
    if evidence_snapshot.get("preceding_source_artifact_evidence_ref") != _exact_ref(
        first_release_artifact_evidence, object_type="SourceArtifactEvidence"
    ):
        _fail("EvidenceSnapshot source artifact evidence mismatch")
    if first_release_artifact_evidence.get("retrieved_at") > evidence_snapshot.get("information_cutoff"):
        _fail("preceding first-release artifact was retrieved after information cutoff")
    if evidence_snapshot.get("parser_version") != FIRST_RELEASE_PARSER_VERSION:
        _fail("EvidenceSnapshot parser_version mismatch")
    value = _parse_first_release_value(
        target_definition, bytes(first_release_raw_bytes), expected_previous
    )
    if evidence_snapshot.get("parsed_decimal_value") != value:
        _fail("EvidenceSnapshot parsed decimal differs from deterministic replay")
    return value


def derive_cycle_times_from_barrier(outcome_information_barrier: str) -> dict[str, str]:
    try:
        barrier_utc = datetime.strptime(outcome_information_barrier, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=ZoneInfo("UTC")
        )
    except (TypeError, ValueError) as exc:
        raise GenesisSourceAuthorityError("outcome information barrier must use canonical UTC") from exc
    local = barrier_utc.astimezone(ZoneInfo(GENESIS_TIMEZONE))

    def calendar_days_before(days: int) -> str:
        return (local - timedelta(days=days)).astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "plan_commitment_deadline": calendar_days_before(8),
        "information_cutoff": calendar_days_before(7),
        "execution_window_open": calendar_days_before(7),
        "execution_window_close": calendar_days_before(6),
        "external_proof_deadline": (barrier_utc - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "durability_completion_deadline": barrier_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
