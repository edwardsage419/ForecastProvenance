"""Fixed synthetic calendar kernel; retained TZif, no host timezone lookup.

UTC duration offsets below belong only to M1_FIXED_MODEL_V1. They neither
select a real schedule version nor resolve real DST/day-offset semantics.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from .core import Check
from .authority_primitives_v1 import ExactRef
from .canonical import seal_object, canonical_json
from .genesis_contracts_v1 import (reconstruct_schedule_derivation_evidence,
    reconstruct_target_instance, reconstruct_forecast_slot, reconstruct_issuance_cycle_plan)

MODEL_CYCLE_RULES = {
    "horizon_start": "2030-02-01T00:00:00Z", "horizon_end": "2030-03-01T00:00:00Z",
    "acceptance": "2030-02-01T00:00:00Z", "genesis": "2030-02-02T00:00:00Z",
    "plan_days": 8, "cutoff_days": 7, "window_close_days": 6,
    "external_days": 1, "resolution_days_after": 1,
    "timezone": "America/New_York", "revision": "COMPLETE_RETAINED_REVISIONS",
    "origin": "SYNTHETIC_ONLY",
}
ENTRY_FIELDS = frozenset({"target", "release_id", "reference_period", "revision",
    "local_datetime", "timezone", "state", "published_at"})
PAGE_FIELDS = frozenset({"object_id", "object_type", "payload_sha256", "content_sha256",
    "model_only", "schema_version", "target", "source_contract_ref", "revision",
    "page", "page_count", "previous_revision_refs", "published_at", "retrieved_at", "entries"})

@dataclass(frozen=True)
class EntryDisposition:
    source_ref: ExactRef
    pointer: str
    disposition: str
    release_id: str | None
    barrier: str | None = None

@dataclass(frozen=True)
class CalendarRelease:
    target: str
    release_id: str
    reference_period: str
    barrier: str
    local_datetime: str
    source_ref: ExactRef
    retrieved_at: str

def utc(value):
    if not isinstance(value, str) or len(value) != 20 or not value.endswith("Z"):
        raise ValueError("canonical UTC required")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)

def stamp(value):
    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def convert_local_release(local, zone):
    try:
        if not isinstance(local, str) or len(local) != 19:
            raise ValueError("canonical local datetime required")
        dt = datetime.strptime(local, "%Y-%m-%dT%H:%M:%S")
        candidates = set()
        for fold in (0, 1):
            aware = dt.replace(tzinfo=zone, fold=fold)
            candidate = aware.astimezone(timezone.utc)
            if candidate.astimezone(zone).replace(tzinfo=None) == dt:
                candidates.add(candidate)
        if not candidates:
            return None, (Check("calendar-local-time", "FAIL", "NONEXISTENT_LOCAL_RELEASE_TIME"),)
        if len(candidates) != 1:
            return None, (Check("calendar-local-time", "UNKNOWN", "AMBIGUOUS_LOCAL_RELEASE_TIME"),)
        return stamp(next(iter(candidates))), (Check("calendar-local-time", "PASS", "RETAINED_TZIF_CONVERSION"),)
    except (ValueError, TypeError, OverflowError):
        return None, (Check("calendar-local-time", "FAIL", "INVALID_LOCAL_RELEASE_TIME"),)

def parse_calendar_pages(pages, target, source_contract_ref, zone):
    """Pure kernel; full adapter independently selects/verifies its inputs."""
    checks, dispositions, entries = [], [], []
    for page in pages:
        ref = ExactRef(page["object_id"], page["content_sha256"])
        if set(page) != PAGE_FIELDS or page.get("object_type") != "SyntheticOfficialCalendarPage" or page.get("model_only") is not True or page.get("schema_version") != "MODEL_CALENDAR_V1":
            checks.append(Check("calendar-page", "FAIL", "CALENDAR_PAGE_SCHEMA_INVALID"))
            continue
        if page.get("target") != target or page.get("source_contract_ref") != source_contract_ref.to_dict():
            checks.append(Check("calendar-source", "FAIL", "CALENDAR_TARGET_SOURCE_BINDING"))
        raw = page.get("entries")
        if not isinstance(raw, list):
            checks.append(Check("calendar-entries", "FAIL", "CALENDAR_ENTRIES_INVALID"))
            continue
        for index, entry in enumerate(raw):
            pointer = "/entries/" + str(index)
            release_id = entry.get("release_id") if isinstance(entry, dict) else None
            valid = isinstance(entry, dict) and set(entry) == ENTRY_FIELDS
            valid = valid and all(isinstance(entry[x], str) and bool(entry[x]) for x in ENTRY_FIELDS - {"revision"})
            valid = valid and type(entry.get("revision")) is int and entry["revision"] >= 0
            valid = valid and entry.get("target") == target and entry.get("timezone") == MODEL_CYCLE_RULES["timezone"]
            valid = valid and entry.get("state") in ("ACTIVE", "CANCELLED")
            try:
                if not valid or utc(entry["published_at"]) > utc(page["retrieved_at"]) or utc(page["published_at"]) > utc(page["retrieved_at"]):
                    raise ValueError("entry schema/provenance")
            except (ValueError, TypeError):
                checks.append(Check("calendar-entry", "FAIL", "CALENDAR_ENTRY_SCHEMA_OR_PROVENANCE_INVALID"))
                dispositions.append(EntryDisposition(ref, pointer, "INVALID", release_id))
                continue
            barrier, local_checks = convert_local_release(entry["local_datetime"], zone)
            checks.extend(local_checks)
            if barrier is None:
                dispositions.append(EntryDisposition(ref, pointer, "UNRESOLVED", release_id))
                continue
            entries.append((entry, ref, pointer, barrier, page["retrieved_at"]))
    groups = defaultdict(list)
    for item in entries:
        entry = item[0]
        groups[(entry["release_id"], entry["reference_period"])].append(item)
    releases = []
    for key, items in sorted(groups.items()):
        revisions = {item[0]["revision"] for item in items}
        if revisions != set(range(max(revisions) + 1)):
            checks.append(Check("calendar-revisions", "FAIL", "CALENDAR_REVISION_GAP"))
        by_revision = defaultdict(list)
        for item in items:
            by_revision[item[0]["revision"]].append(item)
        conflicting = any(len({canonical_json(x[0]) for x in values}) > 1 for values in by_revision.values())
        if conflicting:
            checks.append(Check("calendar-conflict", "FAIL", "CONFLICTING_CALENDAR_ENTRY_REVISION"))
            dispositions.extend(EntryDisposition(ref, pointer, "CONFLICT", key[0], barrier) for _, ref, pointer, barrier, _ in items)
            continue
        head = max(revisions)
        selected = by_revision[head][0]
        for rev, values in sorted(by_revision.items()):
            for i, (entry, ref, pointer, barrier, retrieved) in enumerate(values):
                disposition = "SUPERSEDED" if rev != head else "DUPLICATE" if i else "EXPECTED"
                if rev == head and i == 0:
                    if entry["state"] == "CANCELLED":
                        disposition = "CANCELLED"
                    elif not (MODEL_CYCLE_RULES["horizon_start"] <= barrier < MODEL_CYCLE_RULES["horizon_end"]):
                        disposition = "OUTSIDE_HORIZON"
                    elif utc(barrier) < utc(MODEL_CYCLE_RULES["genesis"]) or utc(barrier) < utc(MODEL_CYCLE_RULES["acceptance"]) + timedelta(days=8):
                        disposition = "OUTSIDE_MANDATORY_BOUNDARY"
                    else:
                        releases.append(CalendarRelease(target, key[0], key[1], barrier, entry["local_datetime"], ref, retrieved))
                dispositions.append(EntryDisposition(ref, pointer, disposition, key[0], barrier))
    if not checks:
        checks.append(Check("calendar-entries", "UNKNOWN", "CALENDAR_ENTRIES_NOT_ESTABLISHED"))
    elif all(c.status == "PASS" for c in checks):
        checks.append(Check("calendar-selection", "PASS", "ALL_RAW_ENTRIES_DISPOSED"))
    return tuple(releases), tuple(dispositions), tuple(checks)

def identity(obj):
    return ExactRef(obj["object_id"], obj["content_sha256"])

def logical_ref(kind, name, boundary):
    obj = seal_object({"kind": kind, "name": name, "boundary": boundary, "model_only": True},
        object_type="SyntheticLogicalSubject", stable_context="M1_DEVELOPMENT_ONLY",
        semantic_id=f"model:subject:{kind}:{name}:v1")
    return identity(obj)

def derive_model_cycle_artifacts(basis, release, source_refs, tz_ref, page_raw_sha256):
    """Actually execute frozen structural helpers, under model authority only."""
    b = utc(release.barrier)
    dates = {
        "plan_commitment_deadline": stamp(b - timedelta(days=8)),
        "information_cutoff": stamp(b - timedelta(days=7)),
        "execution_window_open": stamp(b - timedelta(days=7)),
        "execution_window_close": stamp(b - timedelta(days=6)),
        "external_proof_deadline": stamp(b - timedelta(days=1)),
        "durability_completion_deadline": release.barrier,
        "resolution_deadline": stamp(b + timedelta(days=1)),
    }
    name = release.target
    rd = lambda key: source_refs[key].to_dict()
    evidence = reconstruct_schedule_derivation_evidence({
        "schema_version": "1.0", "trusted_manifest_ref": basis.subject.to_dict(),
        "issuance_schedule_policy_ref": rd("schedule"), "target_ref": rd("target-" + name),
        "schedule_source_ref": rd("schedule-" + name), "schedule_artifact_ref": release.source_ref.to_dict(),
        "schedule_artifact_sha256": page_raw_sha256, "parser_id": "strict-json-model-v1",
        "parser_version": "MODEL_CALENDAR_V1", "iana_tzdb_version": "RETAINED_TZIF_MODEL_V1",
        "tzdb_artifact_ref": tz_ref.to_dict(), "retrieved_at": release.retrieved_at,
        "parsed_release_identifier": release.release_id, "reference_period": release.reference_period,
        "published_timezone": "America/New_York", "published_local_date": release.local_datetime[:10],
        "published_local_time": release.local_datetime[11:], "authoritative_release_time": release.barrier, **dates})
    ev_ref = identity(evidence).to_dict()
    target = reconstruct_target_instance({"schema_version": "1.0", "trusted_manifest_ref": basis.subject.to_dict(),
        "issuance_schedule_policy_ref": rd("schedule"), "target_ref": rd("target-" + name),
        "schedule_source_ref": rd("schedule-" + name), "measurement_source_ref": rd("measurement-" + name),
        "schedule_derivation_evidence_ref": ev_ref, "reference_period": release.reference_period,
        "release_identifier": release.release_id, "outcome_information_barrier": release.barrier,
        "information_cutoff": dates["information_cutoff"], "resolution_deadline": dates["resolution_deadline"]})
    target_ref = identity(target).to_dict()
    sources = sorted([rd("schedule-" + name), rd("measurement-" + name)], key=lambda x: (x["object_id"], x["content_sha256"]))
    slot = reconstruct_forecast_slot({"schema_version": "1.0", "trusted_manifest_ref": basis.subject.to_dict(),
        "issuance_schedule_policy_ref": rd("schedule"), "target_instance_ref": target_ref,
        "schedule_derivation_evidence_ref": ev_ref, "method_ref": rd("method"), "source_contract_refs": sources,
        "information_cutoff": dates["information_cutoff"], "output_schema": "continuous_scalar_forecast_v1",
        "selection_control_class": "DETERMINISTIC_REPLAY", "forecast_cardinality": 1})
    plan = reconstruct_issuance_cycle_plan({"schema_version": "1.0", "trusted_manifest_ref": basis.subject.to_dict(),
        "schedule_policy_ref": rd("schedule"), "schedule_derivation_evidence_ref": ev_ref,
        "target_instance_ref": target_ref, "method_refs": [rd("method")],
        "expected_slots": [identity(slot).to_dict()], "retry_policy_ref": rd("method"),
        "omission_policy_ref": rd("schedule"), **{k: v for k, v in dates.items() if k != "resolution_deadline"}})
    return {"evidence": evidence, "target": target, "slot": slot, "plan": plan}
