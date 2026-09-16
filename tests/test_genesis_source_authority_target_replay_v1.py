from __future__ import annotations

import hashlib

from forecast_trust_core.canonical import seal_object
from forecast_trust_core.genesis_source_authority_v1 import (
    FIRST_RELEASE_PARSER_VERSION,
    validate_baseline_evidence_snapshot_authoritatively,
)


def ref(obj):
    return {"object_id": obj["object_id"], "content_sha256": obj["content_sha256"]}


def sealed(kind, object_id, **payload):
    return seal_object(
        {"schema_version": "1.0", **payload},
        object_type=kind,
        stable_context="genesis-source-authority-target-replay-test",
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


def target(object_id, schedule_source_ref, first_release_contract):
    return sealed(
        "TargetDefinition",
        object_id,
        schedule_source_ref=schedule_source_ref,
        measurement_source_ref=ref(first_release_contract),
    )


def artifact(contract, raw, resolved_url, retrieved_at):
    return sealed(
        "SourceArtifactEvidence",
        f"artifact:{hashlib.sha256(raw).hexdigest()[:12]}",
        source_contract_ref=ref(contract),
        resolved_url=resolved_url,
        retrieved_at=retrieved_at,
        http_status=200,
        raw_sha256=hashlib.sha256(raw).hexdigest(),
        raw_artifact_ref={"object_id": "raw:fixture:v1", "content_sha256": "a" * 64},
    )


def target_instance(target_def, object_id, reference_period, barrier, schedule_tag):
    return sealed(
        "TargetInstance",
        object_id,
        target_definition_ref=ref(target_def),
        resolution_rule_ref={"object_id": "resolution:test:v1", "content_sha256": "b" * 64},
        schedule_snapshot_ref={"object_id": f"schedule:{schedule_tag}:v1", "content_sha256": "c" * 64},
        reference_period=reference_period,
        outcome_information_barrier=barrier,
    )


def baseline_snapshot(
    *,
    method,
    current,
    previous,
    contract,
    evidence,
    cutoff,
    value,
    object_id,
):
    return sealed(
        "EvidenceSnapshot",
        object_id,
        method_ref=ref(method),
        current_target_instance_ref=ref(current),
        information_cutoff=cutoff,
        preceding_target_instance_ref=ref(previous),
        preceding_first_release_source_contract_ref=ref(contract),
        preceding_source_artifact_evidence_ref=ref(evidence),
        parsed_decimal_value=value,
        parser_version=FIRST_RELEASE_PARSER_VERSION,
    )


def test_u3_baseline_authority_replays_exact_preceding_first_release():
    first = source_contract(
        "source:bls-u3-first-release:v1",
        "https://www.bls.gov/bls/news-release/empsit.htm",
        ["www.bls.gov"],
    )
    target_def = target(
        "target:us-unemployment-rate-u3-sa:v1",
        {"object_id": "source:bls-employment-situation-schedule:v1", "content_sha256": "d" * 64},
        first,
    )
    method = sealed("ForecastMethod", "method:last-observed-value:v1", value="baseline")
    current = target_instance(
        target_def,
        "instance:u3:2026-09:v1",
        "2026-09",
        "2026-10-02T12:30:00Z",
        "u3-current",
    )
    previous = target_instance(
        target_def,
        "instance:u3:2026-08:v1",
        "2026-08",
        "2026-09-04T12:30:00Z",
        "u3-previous",
    )
    raw = b"""
    <html><body>
    <h1>THE EMPLOYMENT SITUATION - AUGUST 2026</h1>
    <p>The unemployment rate was unchanged at 4.1 percent in August, and the number of unemployed people changed little.</p>
    </body></html>
    """
    evidence = artifact(
        first,
        raw,
        "https://www.bls.gov/news.release/empsit.nr0.htm",
        "2026-09-04T13:00:00Z",
    )
    snapshot = baseline_snapshot(
        method=method,
        current=current,
        previous=previous,
        contract=first,
        evidence=evidence,
        cutoff="2026-09-25T12:30:00Z",
        value="4.1",
        object_id="evidence:u3:2026-09:v1",
    )

    value = validate_baseline_evidence_snapshot_authoritatively(
        snapshot,
        method=method,
        target_definition=target_def,
        current_target_instance=current,
        preceding_target_instance=previous,
        first_release_source_contract=first,
        first_release_artifact_evidence=evidence,
        first_release_raw_bytes=raw,
    )

    assert value == "4.1"


def test_gdp_baseline_authority_replays_exact_preceding_advance_estimate():
    first = source_contract(
        "source:bea-real-gdp-advance:v1",
        "https://www.bea.gov/news/",
        ["www.bea.gov", "apps.bea.gov"],
    )
    target_def = target(
        "target:us-real-gdp-qoq-saar-advance:v1",
        {"object_id": "source:bea-gdp-release-schedule:v1", "content_sha256": "e" * 64},
        first,
    )
    method = sealed("ForecastMethod", "method:last-observed-value:v1", value="baseline")
    current = target_instance(
        target_def,
        "instance:gdp:2026-Q3:v1",
        "2026-Q3",
        "2026-10-29T12:30:00Z",
        "gdp-current",
    )
    previous = target_instance(
        target_def,
        "instance:gdp:2026-Q2:v1",
        "2026-Q2",
        "2026-07-30T12:30:00Z",
        "gdp-previous",
    )
    raw = b"""
    <html><body>
    <h1>GDP (Advance Estimate), 2nd Quarter 2026</h1>
    <p>Real gross domestic product (GDP) increased at an annual rate of 1.5 percent in the 2nd quarter of 2026 (April, May, and June), according to the advance estimate released today by the U.S. Bureau of Economic Analysis (BEA).</p>
    </body></html>
    """
    evidence = artifact(
        first,
        raw,
        "https://www.bea.gov/news/2026/gdp-advance-estimate-2nd-quarter-2026",
        "2026-07-30T13:00:00Z",
    )
    snapshot = baseline_snapshot(
        method=method,
        current=current,
        previous=previous,
        contract=first,
        evidence=evidence,
        cutoff="2026-10-22T12:30:00Z",
        value="1.5",
        object_id="evidence:gdp:2026-Q3:v1",
    )

    value = validate_baseline_evidence_snapshot_authoritatively(
        snapshot,
        method=method,
        target_definition=target_def,
        current_target_instance=current,
        preceding_target_instance=previous,
        first_release_source_contract=first,
        first_release_artifact_evidence=evidence,
        first_release_raw_bytes=raw,
    )

    assert value == "1.5"
