from __future__ import annotations

import hashlib

import pytest

from forecast_trust_core.canonical import seal_object
from forecast_trust_core.genesis_source_authority_v1 import (
    FIRST_RELEASE_PARSER_VERSION,
    SCHEDULE_PARSER_VERSION,
    GenesisSourceAuthorityError,
    derive_cycle_times_from_barrier,
    immediately_preceding_reference_period,
    recompute_schedule_fields,
    validate_baseline_evidence_snapshot_authoritatively,
    validate_schedule_snapshot_authoritatively,
    validate_target_instance_authoritatively,
)


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="genesis-source-authority-test",
        semantic_id=object_id,
    )


def source_contract(object_id, primary_url, hosts):
    return sealed(
        "SourceContract",
        object_id,
        access_mode="HTTPS_PUBLIC",
        allowed_hosts=hosts,
        primary_url=primary_url,
    )


def target(object_id, schedule_contract, first_release_contract):
    return sealed(
        "TargetDefinition",
        object_id,
        schedule_source_ref=ref(schedule_contract),
        measurement_source_ref=ref(first_release_contract),
    )


def artifact(contract, raw, url, retrieved_at="2026-08-01T00:00:00Z"):
    return sealed(
        "SourceArtifactEvidence",
        f"artifact:{hashlib.sha256(raw).hexdigest()[:12]}",
        source_contract_ref=ref(contract),
        resolved_url=url,
        retrieved_at=retrieved_at,
        http_status=200,
        raw_sha256=hashlib.sha256(raw).hexdigest(),
        raw_artifact_ref={"object_id": "raw:fixture:v1", "content_sha256": "a" * 64},
    )


def cpi_fixture():
    schedule = source_contract(
        "source:bls-cpi-release-schedule:v1",
        "https://www.bls.gov/schedule/news_release/cpi.htm",
        ["www.bls.gov"],
    )
    first = source_contract(
        "source:bls-cpi-first-release:v1",
        "https://www.bls.gov/bls/news-release/cpi.htm",
        ["www.bls.gov"],
    )
    return target("target:us-cpi-all-items-mom-sa:v1", schedule, first), schedule, first


def empsit_fixture():
    schedule = source_contract(
        "source:bls-employment-situation-schedule:v1",
        "https://www.bls.gov/schedule/news_release/empsit.htm",
        ["www.bls.gov"],
    )
    first = source_contract(
        "source:bls-u3-first-release:v1",
        "https://www.bls.gov/bls/news-release/empsit.htm",
        ["www.bls.gov"],
    )
    return target("target:us-unemployment-rate-u3-sa:v1", schedule, first), schedule, first


def gdp_fixture():
    schedule = source_contract(
        "source:bea-gdp-release-schedule:v1",
        "https://www.bea.gov/news/schedule",
        ["www.bea.gov"],
    )
    first = source_contract(
        "source:bea-real-gdp-advance:v1",
        "https://www.bea.gov/news/",
        ["www.bea.gov", "apps.bea.gov"],
    )
    return target("target:us-real-gdp-qoq-saar-advance:v1", schedule, first), schedule, first


def test_preceding_reference_period_month_and_quarter():
    cpi, _, _ = cpi_fixture()
    gdp, _, _ = gdp_fixture()
    assert immediately_preceding_reference_period(cpi, "2026-01") == "2025-12"
    assert immediately_preceding_reference_period(cpi, "2026-08") == "2026-07"
    assert immediately_preceding_reference_period(gdp, "2026-Q1") == "2025-Q4"
    assert immediately_preceding_reference_period(gdp, "2026-Q3") == "2026-Q2"


def test_bls_cpi_schedule_replay():
    target_def, contract, _ = cpi_fixture()
    raw = b"""
    <html><body><h1>Schedule of Releases for the Consumer Price Index</h1>
    <table><tr><th>Reference Month</th><th>Release Date</th><th>Release Time</th></tr>
    <tr><td>August 2026</td><td>Sep. 11, 2026</td><td>08:30 AM</td></tr></table>
    </body></html>
    """
    art = artifact(contract, raw, contract["primary_url"])
    fields = recompute_schedule_fields(
        target_def, contract, art, raw, reference_period="2026-08"
    )
    assert fields == {
        "parsed_release_identifier": "BLS_CPI:2026-08",
        "reference_period": "2026-08",
        "published_release_date": "2026-09-11",
        "published_release_time": "08:30:00",
        "published_timezone": "America/New_York",
        "parser_version": SCHEDULE_PARSER_VERSION,
    }


def test_bls_employment_schedule_replay():
    target_def, contract, _ = empsit_fixture()
    raw = b"""
    <html><body><h1>Schedule of Releases for the Employment Situation</h1>
    <table><tr><td>August 2026</td><td>Sep. 04, 2026</td><td>08:30 AM</td></tr></table>
    </body></html>
    """
    art = artifact(contract, raw, contract["primary_url"])
    fields = recompute_schedule_fields(
        target_def, contract, art, raw, reference_period="2026-08"
    )
    assert fields["parsed_release_identifier"] == "BLS_EMPSIT:2026-08"
    assert fields["published_release_date"] == "2026-09-04"


def test_bea_advance_schedule_replay():
    target_def, contract, _ = gdp_fixture()
    raw = b"""
    <html><body><h1>Release Schedule</h1>
    <div>October 29 8:30 AM News GDP (Advance Estimate), 3rd Quarter 2026</div>
    <div>November 25 8:30 AM News GDP (Second Estimate), 3rd Quarter 2026</div>
    </body></html>
    """
    art = artifact(contract, raw, contract["primary_url"])
    fields = recompute_schedule_fields(
        target_def, contract, art, raw, reference_period="2026-Q3"
    )
    assert fields["parsed_release_identifier"] == "BEA_GDP_ADVANCE:2026-Q3"
    assert fields["published_release_date"] == "2026-10-29"
    assert fields["published_release_time"] == "08:30:00"


def test_schedule_raw_hash_mismatch_fails_closed():
    target_def, contract, _ = cpi_fixture()
    raw = b"<html><body>Schedule of Releases for the Consumer Price Index August 2026 Sep. 11, 2026 08:30 AM</body></html>"
    art = artifact(contract, raw, contract["primary_url"])
    with pytest.raises(GenesisSourceAuthorityError, match="SHA256 mismatch"):
        recompute_schedule_fields(
            target_def, contract, art, raw + b"tamper", reference_period="2026-08"
        )


def test_schedule_wrong_source_contract_fails_closed():
    target_def, _, _ = cpi_fixture()
    wrong = source_contract(
        "source:bls-employment-situation-schedule:v1",
        "https://www.bls.gov/schedule/news_release/empsit.htm",
        ["www.bls.gov"],
    )
    raw = b"<html><body>Schedule of Releases for the Consumer Price Index August 2026 Sep. 11, 2026 08:30 AM</body></html>"
    art = artifact(wrong, raw, wrong["primary_url"])
    with pytest.raises(GenesisSourceAuthorityError, match="schedule_source_ref mismatch"):
        recompute_schedule_fields(
            target_def, wrong, art, raw, reference_period="2026-08"
        )


def test_duplicate_schedule_row_fails_closed():
    target_def, contract, _ = cpi_fixture()
    row = "August 2026 Sep. 11, 2026 08:30 AM"
    raw = f"<html><body>Schedule of Releases for the Consumer Price Index {row} {row}</body></html>".encode()
    art = artifact(contract, raw, contract["primary_url"])
    with pytest.raises(GenesisSourceAuthorityError, match="expected one row"):
        recompute_schedule_fields(
            target_def, contract, art, raw, reference_period="2026-08"
        )


def test_schedule_snapshot_and_target_instance_recompute_barrier():
    target_def, contract, _ = cpi_fixture()
    raw = b"<html><body>Schedule of Releases for the Consumer Price Index August 2026 Sep. 11, 2026 08:30 AM</body></html>"
    art = artifact(contract, raw, contract["primary_url"])
    fields = recompute_schedule_fields(
        target_def, contract, art, raw, reference_period="2026-08"
    )
    snapshot = sealed(
        "ScheduleSnapshot",
        "schedule:cpi:2026-08:v1",
        schedule_source_contract_ref=ref(contract),
        source_artifact_evidence_ref=ref(art),
        **fields,
    )
    validate_schedule_snapshot_authoritatively(snapshot, target_def, contract, art, raw)
    instance = sealed(
        "TargetInstance",
        "target-instance:cpi:2026-08:v1",
        target_definition_ref=ref(target_def),
        resolution_rule_ref={"object_id": "resolution:cpi:v1", "content_sha256": "b" * 64},
        schedule_snapshot_ref=ref(snapshot),
        reference_period="2026-08",
        outcome_information_barrier="2026-09-11T12:30:00Z",
    )
    validate_target_instance_authoritatively(instance, target_def, snapshot)


def test_cycle_time_derivation_preserves_calendar_days_across_dst():
    # March 13, 2026 08:30 America/New_York is EDT (12:30Z), while March 6
    # is EST (13:30Z). Seven calendar days therefore differ by 167 UTC hours.
    times = derive_cycle_times_from_barrier("2026-03-13T12:30:00Z")
    assert times["information_cutoff"] == "2026-03-06T13:30:00Z"
    assert times["execution_window_open"] == "2026-03-06T13:30:00Z"
    assert times["external_proof_deadline"] == "2026-03-12T12:30:00Z"


def _baseline_instances(target_def, reference_period, previous_period, cutoff):
    current = sealed(
        "TargetInstance",
        f"instance:current:{reference_period}",
        target_definition_ref=ref(target_def),
        resolution_rule_ref={"object_id": "resolution:test:v1", "content_sha256": "c" * 64},
        schedule_snapshot_ref={"object_id": "schedule:current:v1", "content_sha256": "d" * 64},
        reference_period=reference_period,
        outcome_information_barrier="2026-09-11T12:30:00Z",
    )
    previous = sealed(
        "TargetInstance",
        f"instance:previous:{previous_period}",
        target_definition_ref=ref(target_def),
        resolution_rule_ref={"object_id": "resolution:test:v1", "content_sha256": "c" * 64},
        schedule_snapshot_ref={"object_id": "schedule:previous:v1", "content_sha256": "e" * 64},
        reference_period=previous_period,
        outcome_information_barrier="2026-08-12T12:30:00Z",
    )
    method = sealed("ForecastMethod", "method:last-observed-value:v1", value="baseline")
    return current, previous, method


def test_cpi_baseline_replay_and_value_binding():
    target_def, _, first = cpi_fixture()
    raw = b"""
    <html><body>
    <h1>CONSUMER PRICE INDEX - JULY 2026</h1>
    <p>The Consumer Price Index for All Urban Consumers (CPI-U) increased 0.1 percent on a seasonally adjusted basis in July.</p>
    </body></html>
    """
    art = artifact(first, raw, "https://www.bls.gov/news.release/cpi.nr0.htm", "2026-08-01T00:00:00Z")
    current, previous, method = _baseline_instances(target_def, "2026-08", "2026-07", "2026-09-04T12:30:00Z")
    snapshot = sealed(
        "EvidenceSnapshot",
        "evidence:cpi:2026-08:v1",
        method_ref=ref(method),
        current_target_instance_ref=ref(current),
        information_cutoff="2026-09-04T12:30:00Z",
        preceding_target_instance_ref=ref(previous),
        preceding_first_release_source_contract_ref=ref(first),
        preceding_source_artifact_evidence_ref=ref(art),
        parsed_decimal_value="0.1",
        parser_version=FIRST_RELEASE_PARSER_VERSION,
    )
    value = validate_baseline_evidence_snapshot_authoritatively(
        snapshot,
        method=method,
        target_definition=target_def,
        current_target_instance=current,
        preceding_target_instance=previous,
        first_release_source_contract=first,
        first_release_artifact_evidence=art,
        first_release_raw_bytes=raw,
    )
    assert value == "0.1"


def test_baseline_value_substitution_fails_closed():
    target_def, _, first = cpi_fixture()
    raw = b"""
    <html><body><h1>CONSUMER PRICE INDEX - JULY 2026</h1>
    <p>The Consumer Price Index for All Urban Consumers (CPI-U) increased 0.1 percent on a seasonally adjusted basis in July.</p>
    </body></html>
    """
    art = artifact(first, raw, "https://www.bls.gov/news.release/cpi.nr0.htm")
    current, previous, method = _baseline_instances(target_def, "2026-08", "2026-07", "2026-09-04T12:30:00Z")
    snapshot = sealed(
        "EvidenceSnapshot",
        "evidence:cpi:substitute:v1",
        method_ref=ref(method),
        current_target_instance_ref=ref(current),
        information_cutoff="2026-09-04T12:30:00Z",
        preceding_target_instance_ref=ref(previous),
        preceding_first_release_source_contract_ref=ref(first),
        preceding_source_artifact_evidence_ref=ref(art),
        parsed_decimal_value="9.9",
        parser_version=FIRST_RELEASE_PARSER_VERSION,
    )
    with pytest.raises(GenesisSourceAuthorityError, match="parsed decimal"):
        validate_baseline_evidence_snapshot_authoritatively(
            snapshot,
            method=method,
            target_definition=target_def,
            current_target_instance=current,
            preceding_target_instance=previous,
            first_release_source_contract=first,
            first_release_artifact_evidence=art,
            first_release_raw_bytes=raw,
        )


def test_future_retrieval_fails_closed():
    target_def, _, first = cpi_fixture()
    raw = b"""
    <html><body><h1>CONSUMER PRICE INDEX - JULY 2026</h1>
    <p>The Consumer Price Index for All Urban Consumers (CPI-U) increased 0.1 percent on a seasonally adjusted basis in July.</p>
    </body></html>
    """
    art = artifact(first, raw, "https://www.bls.gov/news.release/cpi.nr0.htm", "2026-09-05T00:00:00Z")
    current, previous, method = _baseline_instances(target_def, "2026-08", "2026-07", "2026-09-04T12:30:00Z")
    snapshot = sealed(
        "EvidenceSnapshot",
        "evidence:cpi:future:v1",
        method_ref=ref(method),
        current_target_instance_ref=ref(current),
        information_cutoff="2026-09-04T12:30:00Z",
        preceding_target_instance_ref=ref(previous),
        preceding_first_release_source_contract_ref=ref(first),
        preceding_source_artifact_evidence_ref=ref(art),
        parsed_decimal_value="0.1",
        parser_version=FIRST_RELEASE_PARSER_VERSION,
    )
    with pytest.raises(GenesisSourceAuthorityError, match="retrieved after information cutoff"):
        validate_baseline_evidence_snapshot_authoritatively(
            snapshot,
            method=method,
            target_definition=target_def,
            current_target_instance=current,
            preceding_target_instance=previous,
            first_release_source_contract=first,
            first_release_artifact_evidence=art,
            first_release_raw_bytes=raw,
        )
