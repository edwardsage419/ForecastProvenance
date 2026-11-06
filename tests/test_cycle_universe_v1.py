"""Finite MODEL C06 capability: derive calendars before submitted accounting."""
import importlib
import importlib.util
import json
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from forecast_trust_core.authority_primitives_v1 import ExactRef
from forecast_trust_core.canonical import canonical_json, seal_object
from replay_model_support import ModelResolver, model_basis

CORPUS = Path(__file__).parent / "fixtures/independent_replay_v1"


def api():
    assert importlib.util.find_spec("forecast_trust_core.cycle_universe_v1"), "T04 calendar reconstruction missing"
    return importlib.import_module("forecast_trust_core.cycle_universe_v1")


def resolver():
    r = ModelResolver()
    for directory in ("calendars", "cycles"):
        for path in (CORPUS / directory).glob("*.json"):
            obj = json.loads(path.read_bytes())
            r.data[ExactRef(obj["object_id"], obj["content_sha256"])] = canonical_json(obj)
    for path in (CORPUS / "tzdb").glob("*.tzif"):
        raw = path.read_bytes()
        r.data[ExactRef("model:tzif:" + path.stem, sha256(raw).hexdigest())] = raw
    return r


def reasons(result):
    return {c.reason_code for c in result.checks}


def positive():
    mod = api()
    r = resolver()
    result = mod.reconstruct_cycle_universe(model_basis(), r)
    return mod, r, result


def test_calendar_positive_reconstructs_all_three_targets_cycles_and_slots():
    _, _, result = positive()
    assert result.overall == "PASS", reasons(result)
    assert len(result.cycles) == len(result.slots) == 3
    assert {c.target_name for c in result.cycles} == {"t1", "t2", "t3"}
    assert all(c.barrier == "2030-02-20T13:30:00Z" for c in result.cycles)
    assert result.entry_dispositions and all(d.disposition for d in result.entry_dispositions)
    assert result.records and all(row.raw_result for row in result.records)
    assert result.partition.expected == result.partition.issued
    assert len(result.partition.resolved) == 3


@pytest.mark.parametrize("target", ["t1", "t2", "t3"])
def test_whole_target_submitted_records_deleted_does_not_shrink_calendar_universe(target):
    mod, r, original = positive()
    expected = next(c for c in original.cycles if c.target_name == target)
    for ref in expected.submitted_refs:
        r.data.pop(ref, None)
    changed = mod.reconstruct_cycle_universe(model_basis(), r)
    assert {c.logical_ref for c in changed.cycles} == {c.logical_ref for c in original.cycles}
    assert {s.logical_ref for s in changed.slots} == {s.logical_ref for s in original.slots}
    assert changed.overall == "FAIL"
    assert "MISSING_EXPECTED_CYCLE_OR_SLOT_RECORD" in reasons(changed)


@pytest.mark.parametrize("kind", ["plan", "manifest", "slot", "issued"])
def test_independently_expected_record_missing_is_not_default_omission(kind):
    mod, r, original = positive()
    ref = original.cycles[0].record_refs[kind]
    del r.data[ref]
    changed = mod.reconstruct_cycle_universe(model_basis(), r)
    assert changed.overall == "FAIL"
    assert "MISSING_EXPECTED_CYCLE_OR_SLOT_RECORD" in reasons(changed)
    assert "NO_AUTHORITATIVE_RESULT" in reasons(changed)


@pytest.mark.parametrize("category", ["coverage", "calendar", "tzdb"])
def test_missing_calendar_coverage_or_timezone_is_unknown_not_empty_pass(category):
    mod, r, _ = positive()
    pins = importlib.import_module("forecast_trust_core.calendar_model_v1")
    refs = {"coverage": pins.MODEL_CALENDAR_COVERAGE_REFS,
            "calendar": pins.MODEL_CALENDAR_PAGE_REFS,
            "tzdb": pins.MODEL_TZDB_REFS}[category]
    for data in refs.values():
        r.data.pop(ExactRef.from_mapping(data), None)
    changed = mod.reconstruct_cycle_universe(model_basis(), r)
    assert changed.overall == "UNKNOWN", reasons(changed)
    assert "PASS" not in {row.normalized for row in changed.records}


def test_wrong_retained_timezone_bytes_fail_exact_pin():
    mod, r, _ = positive()
    pins = importlib.import_module("forecast_trust_core.calendar_model_v1")
    ref = ExactRef.from_mapping(next(iter(pins.MODEL_TZDB_REFS.values())))
    r.data[ref] += b"changed"
    changed = mod.reconstruct_cycle_universe(model_basis(), r)
    assert changed.overall == "FAIL"
    assert "TZDB_EXACT_BYTES_MISMATCH" in reasons(changed)


def test_wrong_calendar_bytes_fail_instead_of_selecting_new_revision():
    mod, r, _ = positive()
    pins = importlib.import_module("forecast_trust_core.calendar_model_v1")
    ref = ExactRef.from_mapping(next(iter(pins.MODEL_CALENDAR_PAGE_REFS.values())))
    obj = json.loads(r.data[ref])
    obj["entries"] = []
    r.data[ref] = canonical_json(obj)
    changed = mod.reconstruct_cycle_universe(model_basis(), r)
    assert changed.overall == "FAIL"
    assert "HASH_FAILURE" in reasons(changed)


def test_public_or_unknown_profile_never_runs_synthetic_cycle_authority():
    mod = api()
    for b in (replace(model_basis(), mode="PUBLIC_EVIDENCE"),
              replace(model_basis(), profile=(ExactRef("unknown:profile", "a" * 64),))):
        result = mod.reconstruct_cycle_universe(b, resolver())
        assert result.overall == "UNKNOWN"
        assert "MODEL_CYCLE_PROFILE_NOT_APPLICABLE" in reasons(result)


@pytest.mark.parametrize("local,expected,status", [
    ("2030-02-20T08:30:00", "2030-02-20T13:30:00Z", "PASS"),
    ("2030-07-20T08:30:00", "2030-07-20T12:30:00Z", "PASS"),
    ("2030-03-10T02:30:00", None, "FAIL"),
    ("2030-11-03T01:30:00", None, "UNKNOWN"),
])
def test_retained_tzif_dst_conversion_checks_nonexistent_and_ambiguous_times(local, expected, status):
    mod = api()
    tz = ZoneInfo.from_file(BytesIO((CORPUS / "tzdb/America-New_York.tzif").read_bytes()), key="America/New_York")
    timestamp, checks = mod.convert_local_release(local, tz)
    assert timestamp == expected
    assert mod.reduce_checks(checks) == status


@pytest.mark.parametrize("mutation,reason", [
    ("whole_cycle", "MISSING_EXPECTED_CYCLE"),
    ("whole_slot", "MISSING_EXPECTED_SLOT"),
    ("sync_shrink", "MISSING_EXPECTED_CYCLE"),
    ("unexpected", "UNEXPECTED_SUBMITTED_CYCLE"),
])
def test_untrusted_submission_inventory_cannot_define_expected_set(mutation, reason):
    mod, r, result = positive()
    observed = deepcopy(result.submission_inventory)
    if mutation in {"whole_cycle", "sync_shrink"}:
        observed["cycles"] = observed["cycles"][1:]
        if mutation == "sync_shrink":
            observed["claimed_expected_cycles"] = observed["cycles"]
    elif mutation == "whole_slot":
        observed["slots"] = observed["slots"][1:]
    else:
        observed["cycles"].append(ExactRef("model:unexpected", "a" * 64).to_dict())
    checks = mod.compare_submission_inventory(result.cycles, result.slots, observed)
    assert mod.reduce_checks(checks) == "FAIL"
    assert reason in {c.reason_code for c in checks}


def test_withdrawn_and_ineligible_issued_forecast_remains_in_denominator():
    mod, _, result = positive()
    rows = deepcopy(result.accounting)
    rows[0]["withdrawal_state"] = "WITHDRAWN"
    rows[0]["withdrawal_refs"] = [ExactRef("model:withdrawal", "a" * 64).to_dict()]
    rows[0]["eligibility_state"] = "INELIGIBLE"
    rows[0]["ineligibility_evidence_refs"] = [ExactRef("model:ineligibility", "b" * 64).to_dict()]
    partition, checks = mod.project_accounting(result.slots, rows)
    assert mod.reduce_checks(checks) == "PASS"
    assert partition.expected == partition.issued == result.partition.issued
    assert len(partition.withdrawn) == len(partition.ineligible) == 1
    assert partition.resolved == result.partition.resolved


def test_missing_accounting_row_cannot_be_interpreted_as_omitted():
    mod, _, result = positive()
    partition, checks = mod.project_accounting(result.slots, result.accounting[1:])
    assert mod.reduce_checks(checks) == "FAIL"
    assert partition.omitted == frozenset()
    assert "MISSING_EXPECTED_SLOT_ACCOUNTING" in {c.reason_code for c in checks}


def test_parser_revision_dispositions_are_complete_and_deterministic():
    _, _, result = positive()
    states = {d.disposition for d in result.entry_dispositions}
    assert {"SUPERSEDED", "CANCELLED", "EXPECTED", "OUTSIDE_HORIZON"}.issubset(states)
    assert len({(d.source_ref, d.pointer) for d in result.entry_dispositions}) == len(result.entry_dispositions)


def test_runtime_and_parser_pins_are_checked_before_calendar_capability(monkeypatch):
    mod = api()
    monkeypatch.setattr(mod, "runtime_identity", lambda: {"python": "0.0.0", "parser_sha256": "f" * 64})
    result = mod.reconstruct_cycle_universe(model_basis(), resolver())
    assert result.overall == "FAIL"
    assert "CALENDAR_RUNTIME_OR_PARSER_MISMATCH" in reasons(result)


def raw_calendar_kernel_inputs():
    mod = api()
    pins = importlib.import_module("forecast_trust_core.calendar_model_v1")
    r = resolver()
    pages = [json.loads(r.data[ExactRef.from_mapping(v)]) for k, v in pins.MODEL_CALENDAR_PAGE_REFS.items() if k.startswith("t1-")]
    sources = importlib.import_module("forecast_trust_core.replay_model_v1").MODEL_SOURCE_REFS
    zone = ZoneInfo.from_file(BytesIO((CORPUS / "tzdb/America-New_York.tzif").read_bytes()), key="America/New_York")
    return mod, pages, ExactRef.from_mapping(sources["schedule-t1"]), zone


@pytest.mark.parametrize("date,expected", [
    ("2030-02-18T08:30:00", "2030-02-18T13:30:00Z"),
    ("2030-02-22T08:30:00", "2030-02-22T13:30:00Z"),
])
def test_raw_calendar_revision_advance_or_delay_changes_derived_release(date, expected):
    mod, pages, source, zone = raw_calendar_kernel_inputs()
    pages[1]["entries"][0]["local_datetime"] = date
    releases, dispositions, checks = mod.parse_calendar_pages(pages, "t1", source, zone)
    assert mod.reduce_checks(checks) == "PASS"
    assert len(releases) == 1 and releases[0].barrier == expected
    assert sum(d.disposition == "SUPERSEDED" for d in dispositions) == 2


def test_known_cancellation_removes_release_but_keeps_every_raw_entry_disposition():
    mod, pages, source, zone = raw_calendar_kernel_inputs()
    pages[1]["entries"][0]["state"] = "CANCELLED"
    releases, dispositions, checks = mod.parse_calendar_pages(pages, "t1", source, zone)
    assert mod.reduce_checks(checks) == "PASS"
    assert not releases
    assert len(dispositions) == sum(len(p["entries"]) for p in pages)
    assert sum(d.disposition == "CANCELLED" for d in dispositions) == 2


@pytest.mark.parametrize("conflict", [False, True])
def test_duplicate_calendar_entries_are_disposed_and_conflicting_revision_fails(conflict):
    mod, pages, source, zone = raw_calendar_kernel_inputs()
    duplicate = deepcopy(pages[1]["entries"][0])
    if conflict:
        duplicate["local_datetime"] = "2030-02-21T08:30:00"
    pages[1]["entries"].append(duplicate)
    releases, dispositions, checks = mod.parse_calendar_pages(pages, "t1", source, zone)
    assert len(dispositions) == sum(len(p["entries"]) for p in pages)
    if conflict:
        assert mod.reduce_checks(checks) == "FAIL"
        assert "CONFLICTING_CALENDAR_ENTRY_REVISION" in {c.reason_code for c in checks}
    else:
        assert mod.reduce_checks(checks) == "PASS"
        assert len(releases) == 1
        assert any(d.disposition == "DUPLICATE" for d in dispositions)


@pytest.mark.parametrize("field", ["timezone", "published_at", "reference_period", "revision", "state"])
def test_raw_consequential_calendar_field_omission_is_known_schema_failure(field):
    mod, pages, source, zone = raw_calendar_kernel_inputs()
    del pages[1]["entries"][0][field]
    _, dispositions, checks = mod.parse_calendar_pages(pages, "t1", source, zone)
    assert mod.reduce_checks(checks) == "FAIL"
    assert any(d.disposition == "INVALID" for d in dispositions)


def test_raw_revision_history_truncation_is_detected_independently_of_stored_cycle_lists():
    mod, pages, source, zone = raw_calendar_kernel_inputs()
    releases, _, checks = mod.parse_calendar_pages(pages[1:], "t1", source, zone)
    assert releases  # a plausible current release remains, but history is incomplete
    assert mod.reduce_checks(checks) == "FAIL"
    assert "CALENDAR_REVISION_GAP" in {c.reason_code for c in checks}


@pytest.mark.parametrize("mutation,reason", [
    ("page_missing", "CALENDAR_REVISION_COVERAGE_INCOMPLETE"),
    ("page_count", "CALENDAR_PAGE_COVERAGE_INCOMPLETE"),
    ("predecessor", "CALENDAR_REVISION_CHAIN_INVALID"),
])
def test_native_page_revision_coverage_checks_detect_causal_omission(mutation, reason):
    mod, pages, source, _ = raw_calendar_kernel_inputs()
    pins = importlib.import_module("forecast_trust_core.calendar_model_v1")
    r = resolver()
    coverage = json.loads(r.data[ExactRef.from_mapping(pins.MODEL_CALENDAR_COVERAGE_REFS["t1"])])
    if mutation == "page_missing":
        pages = pages[1:]
    elif mutation == "page_count":
        coverage["page_counts"]["1"] = 2
    else:
        pages[1]["previous_revision_refs"] = []
    checks = mod._coverage_checks("t1", coverage, pages, source)
    assert mod.reduce_checks(checks) == "FAIL"
    assert reason in {c.reason_code for c in checks}


@pytest.mark.parametrize("axis", ["issuance", "resolution"])
def test_pending_after_fixed_final_observation_boundary_cannot_pass_accounting(axis):
    mod, _, result = positive()
    rows = deepcopy(result.accounting)
    if axis == "issuance":
        row = rows[0]
        row["issuance_outcome"] = "EXPECTED"
        row["eligibility_state"] = "NOT_YET_DETERMINED"
        row["resolution_state"] = "NOT_APPLICABLE"
        for key in ("attempt_refs", "issued_forecast_refs", "failure_record_refs", "omission_evidence_refs",
                    "ineligibility_evidence_refs", "unresolved_evidence_refs", "withdrawal_refs", "correction_refs"):
            row[key] = []
    else:
        rows[0]["resolution_state"] = "RESOLUTION_PENDING"
    _, checks = mod.project_accounting(result.slots, rows)
    assert mod.reduce_checks(checks) == "FAIL"
    assert ("NONTERMINAL_SLOT_AFTER_FINAL_BOUNDARY" if axis == "issuance" else "RESOLUTION_PENDING_AFTER_FINAL_BOUNDARY") in {c.reason_code for c in checks}
