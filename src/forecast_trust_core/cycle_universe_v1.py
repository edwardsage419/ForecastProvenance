"""Independent finite synthetic C06 replay. No real schedule applicability."""
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
from hashlib import sha256
from io import BytesIO
from types import SimpleNamespace
from zoneinfo import ZoneInfo
import platform
import sys
import importlib.metadata

from .authority_primitives_v1 import ExactRef, resolve_exact, AuthorityPrimitiveError
from .core import Check, validate_cycle_plan, validate_cycle_manifest
from .genesis_contracts_v1 import _validate_accounting_row, ContractViolation
from .calendar_parser_v1 import (convert_local_release, parse_calendar_pages, derive_model_cycle_artifacts,
    identity, logical_ref, MODEL_CYCLE_RULES, utc)
from . import calendar_parser_v1
from .calendar_model_v1 import (MODEL_CALENDAR_PAGE_REFS, MODEL_CALENDAR_COVERAGE_REFS, MODEL_TZDB_REFS,
    MODEL_CYCLE_SUBMISSION_REFS, MODEL_SUBMISSION_INVENTORY_REF, MODEL_CALENDAR_RUNTIME, MODEL_CALENDAR_RULES)
from .replay_model_v1 import MODEL_SOURCE_REFS, MODEL_BASIS_DATA
from .g10_requirements_v1 import reconstruct_requirements
from .replay_records_v1 import NativeReplay, emit_records, reduce_checks

P12 = ("calendar_target_period_coverage", "calendar_page_revision_coverage", "calendar_entry_disposition",
    "calendar_parser_tzdb", "calendar_horizon_boundaries", "cycle_identity", "slot_method_matrix")
P13 = ("cycle_record_coverage", "slot_record_coverage", "lifecycle_partition", "issued_withdrawn_accounting",
    "resolution_partition", "omission_evidence")

@dataclass(frozen=True)
class ExpectedCycle:
    target_name: str
    logical_ref: ExactRef
    barrier: str
    artifacts: dict
    record_refs: dict
    submitted_refs: tuple[ExactRef, ...]
    deadlines: dict

@dataclass(frozen=True)
class ExpectedSlot:
    target_name: str
    logical_ref: ExactRef
    sealed_ref: ExactRef
    cycle_ref: ExactRef
    barrier: str

@dataclass(frozen=True)
class AccountingPartition:
    expected: frozenset
    issued: frozenset
    failed: frozenset
    omitted: frozenset
    pending: frozenset
    withdrawn: frozenset
    ineligible: frozenset
    resolved: frozenset
    unresolved: frozenset
    resolution_pending: frozenset

@dataclass(frozen=True)
class CycleUniverse:
    cycles: tuple
    slots: tuple
    entry_dispositions: tuple
    accounting: tuple
    partition: AccountingPartition
    submission_inventory: dict
    checks: tuple
    records: tuple
    overall: str
    input_refs: tuple
    model_only: bool = True

def _check(name, value, reason):
    return Check(name, "UNKNOWN" if value is None else "PASS" if value else "FAIL", reason)

def runtime_identity():
    return {"python": platform.python_version(),
        "executable_sha256": sha256(Path(sys.executable).read_bytes()).hexdigest(),
        "pytest": importlib.metadata.version("pytest"), "jsonschema": importlib.metadata.version("jsonschema"),
        "parser_sha256": sha256(Path(calendar_parser_v1.__file__).read_bytes()).hexdigest()}

def _read_raw(ref, resolver):
    try:
        raw = resolver.resolve_exact(ref)
        obj = resolve_exact(ref, SimpleNamespace(resolve_exact=lambda _: raw))
        return obj, raw, ()
    except AuthorityPrimitiveError as exc:
        return None, None, (Check("exact-input", "UNKNOWN" if str(exc) == "NO_AUTHORITATIVE_RESULT" else "FAIL", str(exc)),)
    except Exception as exc:
        return None, None, (Check('exact-input', 'UNKNOWN', 'CALENDAR_INPUT_UNAVAILABLE_' + type(exc).__name__),)

def _read(ref, resolver):
    obj, _, errors = _read_raw(ref, resolver)
    return obj, errors

def _parse_refs(values, check_id):
    refs, checks = [], []
    if not isinstance(values, (list, tuple)):
        return [], [Check(check_id, "FAIL", "SUBMISSION_INVENTORY_SCHEMA_INVALID")]
    for data in values:
        try:
            refs.append(ExactRef.from_mapping(data))
        except (ValueError, TypeError):
            checks.append(Check(check_id, "FAIL", "SUBMISSION_REFERENCE_INVALID"))
    if len(refs) != len(set(refs)):
        checks.append(Check(check_id, "FAIL", "DUPLICATE_SUBMISSION_IDENTITY"))
    return refs, checks

def compare_submission_inventory(cycles, slots, observed):
    """Observed inventory is never the authority for the expected universe."""
    checks = []
    if not isinstance(observed, dict):
        return (Check("submission-inventory", "FAIL", "SUBMISSION_INVENTORY_SCHEMA_INVALID"),)
    for label, expected, missing, extra in (
        ("cycles", {c.logical_ref for c in cycles}, "MISSING_EXPECTED_CYCLE", "UNEXPECTED_SUBMITTED_CYCLE"),
        ("slots", {s.logical_ref for s in slots}, "MISSING_EXPECTED_SLOT", "UNEXPECTED_SUBMITTED_SLOT")):
        actual, errors = _parse_refs(observed.get(label), label)
        checks.extend(errors)
        checks.append(_check(label + "-missing", not (expected - set(actual)), missing))
        checks.append(_check(label + "-unexpected", not (set(actual) - expected), extra))
    return tuple(checks)

def project_accounting(slots, rows):
    """Math projection with actual native row validation, not eligibility authority."""
    sets = {name: set() for name in ("issued", "failed", "omitted", "pending", "withdrawn",
        "ineligible", "resolved", "unresolved", "resolution_pending")}
    expected = {s.sealed_ref for s in slots}
    seen, checks = set(), []
    if not isinstance(rows, (list, tuple)):
        rows = []
        checks.append(Check("accounting", "FAIL", "ACCOUNTING_COLLECTION_INVALID"))
    for row in rows:
        try:
            if not isinstance(row, dict):
                raise ValueError("not row")
            raw = {k: v for k, v in row.items() if k != "resolution_state"}
            _validate_accounting_row(raw)
            ref = ExactRef.from_mapping(row["slot_ref"])
        except (ValueError, TypeError, KeyError):
            checks.append(Check("accounting-schema", "FAIL", "ACCOUNTING_ROW_SCHEMA_INVALID"))
            continue
        if ref in seen:
            checks.append(Check("accounting-duplicate", "FAIL", "DUPLICATE_SLOT_ACCOUNTING"))
        seen.add(ref)
        outcome = row["issuance_outcome"]
        bucket = {"ISSUED": "issued", "FAILED": "failed", "OMITTED": "omitted", "EXPECTED": "pending"}[outcome]
        sets[bucket].add(ref)
        slot = next((s for s in slots if s.sealed_ref == ref), None)
        if slot is not None and outcome == "EXPECTED":
            checks.append(_check("issuance-terminal-boundary", MODEL_CYCLE_RULES["horizon_end"] < slot.barrier,
                "NONTERMINAL_SLOT_AFTER_FINAL_BOUNDARY"))
        if outcome == "ISSUED":
            if row["withdrawal_state"] == "WITHDRAWN":
                sets["withdrawn"].add(ref)
            if row["eligibility_state"] == "INELIGIBLE":
                sets["ineligible"].add(ref)
            status = row.get("resolution_state")
            if status in ("RESOLVED", "UNRESOLVED", "RESOLUTION_PENDING"):
                sets[{"RESOLVED": "resolved", "UNRESOLVED": "unresolved", "RESOLUTION_PENDING": "resolution_pending"}[status]].add(ref)
                if status == "RESOLUTION_PENDING" and slot is not None:
                    from datetime import timedelta
                    checks.append(_check("resolution-terminal-boundary", utc(MODEL_CYCLE_RULES["horizon_end"]) < utc(slot.barrier) + timedelta(days=MODEL_CYCLE_RULES["resolution_days_after"]),
                        "RESOLUTION_PENDING_AFTER_FINAL_BOUNDARY"))
            else:
                checks.append(Check("resolution", "UNKNOWN" if status is None else "FAIL", "RESOLUTION_ACCOUNTING_NOT_ESTABLISHED"))
        elif row.get("resolution_state") not in (None, "NOT_APPLICABLE"):
            checks.append(Check("resolution", "FAIL", "NONISSUED_RESOLUTION_AXIS_INVALID"))
    checks.extend((
        _check("accounting-missing", not (expected - seen), "MISSING_EXPECTED_SLOT_ACCOUNTING"),
        _check("accounting-unexpected", not (seen - expected), "UNEXPECTED_SLOT_ACCOUNTING"),
        _check("issuance-partition", set.union(*(sets[x] for x in ("issued", "failed", "omitted", "pending"))) == expected,
            "ISSUANCE_PARTITION_INCOMPLETE"),
        _check("withdrawal-subset", sets["withdrawn"] <= sets["issued"] and sets["ineligible"] <= sets["issued"],
            "WITHDRAWAL_INELIGIBILITY_MUST_RETAIN_ISSUED"),
        _check("resolution-partition", sets["resolved"] | sets["unresolved"] | sets["resolution_pending"] == sets["issued"],
            "RESOLUTION_PARTITION_INCOMPLETE")))
    partition = AccountingPartition(frozenset(expected), **{k: frozenset(v) for k, v in sets.items()})
    return partition, tuple(checks)

def _coverage_checks(name, coverage, pages, source_ref):
    refs = [ExactRef.from_mapping(r) for key, r in MODEL_CALENDAR_PAGE_REFS.items() if key.startswith(name + "-")]
    checks = [
        _check("coverage-source", coverage.get("object_type") == "SyntheticCalendarCoverage" and
            coverage.get("model_only") is True and coverage.get("target") == name and
            coverage.get("source_contract_ref") == source_ref.to_dict() and
            coverage.get("official_source") == "model-official-" + name, "CALENDAR_COVERAGE_SOURCE_BINDING"),
        _check("coverage-horizon", coverage.get("horizon_start") == MODEL_CYCLE_RULES["horizon_start"] and
            coverage.get("horizon_end") == coverage.get("cutoff") == MODEL_CYCLE_RULES["horizon_end"],
            "CALENDAR_HORIZON_OR_CUTOFF_MISMATCH"),
        _check("coverage-refs", coverage.get("page_refs") == [r.to_dict() for r in refs], "CALENDAR_PAGE_REVISION_COVERAGE"),
        _check("coverage-authentication", coverage.get("authentication") == "EXPLICIT_MODEL_AUTH_SEAM",
            "CALENDAR_ORIGIN_AUTHENTICATION_MODEL_SEAM")]
    groups = defaultdict(list)
    for page in pages:
        groups[page.get("revision")].append(page)
    head = coverage.get("head_revision")
    counts = coverage.get("page_counts")
    if type(head) is not int or head < 0 or not isinstance(counts, dict):
        return tuple(checks + [Check("coverage-schema", "FAIL", "CALENDAR_COVERAGE_SCHEMA_INVALID")])
    checks.append(_check("revision-coverage", set(groups) == set(range(head + 1)), "CALENDAR_REVISION_COVERAGE_INCOMPLETE"))
    for rev in range(head + 1):
        group = groups.get(rev, [])
        count = counts.get(str(rev))
        if type(count) is not int or count < 1:
            checks.append(Check("page-count", "FAIL", "CALENDAR_PAGE_COUNT_INVALID"))
            continue
        checks.append(_check("page-coverage", sorted(p.get("page") for p in group) == list(range(1, count + 1)) and
            all(p.get("page_count") == count for p in group), "CALENDAR_PAGE_COVERAGE_INCOMPLETE"))
        prior = sorted((identity(p).to_dict() for p in groups.get(rev - 1, [])), key=lambda x: (x["object_id"], x["content_sha256"]))
        for page in group:
            checks.append(_check("previous-revision", page.get("previous_revision_refs") == prior, "CALENDAR_REVISION_CHAIN_INVALID"))
            checks.append(_check("entry-revision", all(isinstance(e, dict) and type(e.get("revision")) is int and e["revision"] <= rev for e in page.get("entries", [])), "CALENDAR_ENTRY_REVISION_INVALID"))
    return tuple(checks)

def reconstruct_cycle_universe(basis, resolver):
    requirements = reconstruct_requirements(basis, resolver)
    p12, p13, refs, cycles, slots, dispositions, accounting = [], [], [], [], [], [], []
    observed = {}
    empty = project_accounting((), ())[0]
    def finish(partition=empty):
        native = {name: NativeReplay(tuple(p12), tuple(dict.fromkeys(refs)), True) for name in P12}
        native.update({name: NativeReplay(tuple(p13), tuple(dict.fromkeys(refs)), True) for name in P13})
        return CycleUniverse(tuple(cycles), tuple(slots), tuple(dispositions), tuple(accounting), partition,
            observed, tuple(p12 + p13), emit_records(requirements, native, __file__),
            reduce_checks(p12 + p13), tuple(dict.fromkeys(refs)))
    if basis.mode != "SYNTHETIC_MODEL" or [r.to_dict() for r in basis.profile] != MODEL_BASIS_DATA["profile"]:
        p12.append(Check("profile", "UNKNOWN", "MODEL_CYCLE_PROFILE_NOT_APPLICABLE"))
        p13.extend(p12)
        return finish()
    if requirements.overall != "PASS":
        p12.append(Check("requirements", requirements.overall, "INDEPENDENT_SOURCE_UNIVERSE_NOT_ESTABLISHED"))
        p13.append(Check("universe", "UNKNOWN", "EXPECTED_CALENDAR_UNIVERSE_NOT_ESTABLISHED"))
        return finish()
    try:
        actual_runtime = runtime_identity()
        p12.append(_check("runtime", actual_runtime == MODEL_CALENDAR_RUNTIME and MODEL_CYCLE_RULES == MODEL_CALENDAR_RULES,
            "CALENDAR_RUNTIME_OR_PARSER_MISMATCH"))
    except (OSError, importlib.metadata.PackageNotFoundError):
        p12.append(Check("runtime", "UNKNOWN", "CALENDAR_RUNTIME_UNAVAILABLE"))
    source_refs = {k: ExactRef.from_mapping(v) for k, v in MODEL_SOURCE_REFS.items()}
    refs.extend(source_refs.values())
    zones = {}
    for label, data in MODEL_TZDB_REFS.items():
        ref = ExactRef.from_mapping(data)
        refs.append(ref)
        try:
            raw = resolver.resolve_exact(ref)
            if raw is None:
                p12.append(Check("tzdb", "UNKNOWN", "NO_AUTHORITATIVE_RESULT"))
                continue
            if not isinstance(raw, bytes) or sha256(raw).hexdigest() != ref.content_sha256:
                p12.append(Check("tzdb", "FAIL", "TZDB_EXACT_BYTES_MISMATCH"))
                continue
            zones[label] = ZoneInfo.from_file(BytesIO(raw), key=label.replace("-", "/"))
            p12.append(Check("tzdb", "PASS", "RETAINED_TZIF_EXACT_BYTES_PARSED"))
        except (OSError, ValueError, TypeError):
            p12.append(Check("tzdb", "UNKNOWN", "TZDB_RUNTIME_UNAVAILABLE"))
    if reduce_checks(p12) != "PASS":
        p13.append(Check("universe", "UNKNOWN", "EXPECTED_CALENDAR_UNIVERSE_NOT_ESTABLISHED"))
        return finish()
    all_releases = []
    page_raw_hashes = {}
    for name in ("t1", "t2", "t3"):
        coverage_ref = ExactRef.from_mapping(MODEL_CALENDAR_COVERAGE_REFS[name])
        refs.append(coverage_ref)
        coverage, errors = _read(coverage_ref, resolver)
        p12.extend(errors)
        pages = []
        for key, data in MODEL_CALENDAR_PAGE_REFS.items():
            if not key.startswith(name + "-"):
                continue
            ref = ExactRef.from_mapping(data)
            refs.append(ref)
            page, raw, errors = _read_raw(ref, resolver)
            p12.extend(errors)
            if page is not None:
                pages.append(page)
                page_raw_hashes[ref] = sha256(raw).hexdigest()
        if coverage is None or len(pages) != 2:
            p12.append(Check("calendar-coverage", "UNKNOWN", "CALENDAR_RETAINED_COVERAGE_NOT_ESTABLISHED"))
            continue
        p12.extend(_coverage_checks(name, coverage, pages, source_refs["schedule-" + name]))
        target = requirements.source_objects[source_refs["target-" + name].object_id]
        method = requirements.source_objects[source_refs["method"].object_id]
        p12.append(_check("method-matrix", target.get("method") == method.get("name") and method.get("control") == "DETERMINISTIC_REPLAY", "TARGET_METHOD_MATRIX_BINDING"))
        releases, entry_states, checks = parse_calendar_pages(pages, name, source_refs["schedule-" + name], zones["America-New_York"])
        p12.extend(checks)
        dispositions.extend(entry_states)
        all_releases.extend(releases)
    if reduce_checks(p12) != "PASS":
        p13.append(Check("universe", "UNKNOWN", "EXPECTED_CALENDAR_UNIVERSE_NOT_ESTABLISHED"))
        return finish()
    for release in all_releases:
        artifacts = derive_model_cycle_artifacts(basis, release, source_refs,
            ExactRef.from_mapping(MODEL_TZDB_REFS["America-New_York"]), page_raw_hashes[release.source_ref])
        record_refs = {k: identity(v) for k, v in artifacts.items()}
        cycle_ref = logical_ref("cycle", release.target, release.barrier)
        slot_ref = logical_ref("slot", release.target, release.barrier)
        slots.append(ExpectedSlot(release.target, slot_ref, record_refs["slot"], cycle_ref, release.barrier))
        plan = artifacts["plan"]
        cycles.append(ExpectedCycle(release.target, cycle_ref, release.barrier, artifacts, record_refs, (),
            {k: plan[k] for k in ("plan_commitment_deadline", "information_cutoff", "execution_window_close", "external_proof_deadline", "durability_completion_deadline")}))
    scope = requirements.source_objects[basis.scope_ref.object_id]
    p12.append(_check("declared-cycle-domain", {c.logical_ref for c in cycles} ==
        {ExactRef.from_mapping(x["subject"]) for x in scope["domains"]["cycles"]}, "INDEPENDENT_CALENDAR_CYCLE_SCOPE_MISMATCH"))
    p12.append(_check("declared-slot-domain", {s.logical_ref for s in slots} ==
        {ExactRef.from_mapping(x["subject"]) for x in scope["domains"]["slots"]}, "INDEPENDENT_METHOD_SLOT_SCOPE_MISMATCH"))
    p12.append(_check("nonempty-capability", len(cycles) == 3 and len(slots) == 3, "MODEL_C06_CAPABILITY_MUST_BE_NONEMPTY"))
    inventory_ref = ExactRef.from_mapping(MODEL_SUBMISSION_INVENTORY_REF)
    refs.append(inventory_ref)
    inventory, errors = _read(inventory_ref, resolver)
    p13.extend(errors)
    if inventory is not None:
        observed.update(inventory)
        p13.extend(compare_submission_inventory(cycles, slots, observed))
    else:
        p13.append(Check("submission-inventory", "UNKNOWN", "SUBMISSION_INVENTORY_NOT_ESTABLISHED"))
    for i, cycle in enumerate(cycles):
        # Look up independently derived expected artifacts even if submitted
        # inventories or records vanished. Missing is never a default omission.
        retained = {}
        for kind, ref in cycle.record_refs.items():
            refs.append(ref)
            obj, errors = _read(ref, resolver)
            p13.extend(errors)
            if obj is None:
                p13.append(Check("required-" + kind, "FAIL", "MISSING_EXPECTED_CYCLE_OR_SLOT_RECORD"))
            else:
                retained[kind] = obj
        subref = ExactRef.from_mapping(MODEL_CYCLE_SUBMISSION_REFS[cycle.target_name])
        refs.append(subref)
        submission, errors = _read(subref, resolver)
        p13.extend(errors)
        all_records = dict(cycle.record_refs)
        if submission is None:
            p13.append(Check("submission", "FAIL", "MISSING_EXPECTED_CYCLE_OR_SLOT_RECORD"))
        else:
            p13.append(_check("submission-binding", submission.get("object_type") == "SyntheticCycleSubmission" and
                submission.get("model_only") is True and submission.get("cycle_ref") == cycle.logical_ref.to_dict() and
                submission.get("slot_ref") == slots[i].logical_ref.to_dict(), "SUBMISSION_CYCLE_SLOT_BINDING"))
            try:
                all_records.update({k: ExactRef.from_mapping(v) for k, v in submission["records"].items()})
            except (ValueError, TypeError, KeyError, AttributeError):
                p13.append(Check("submission-records", "FAIL", "SUBMISSION_REFERENCE_INVALID"))
            for kind, ref in cycle.record_refs.items():
                p13.append(_check("submitted-" + kind, all_records.get(kind) == ref, "SUBMITTED_ARTIFACT_DIFFERS_FROM_CALENDAR_DERIVATION"))
            for kind, ref in all_records.items():
                if kind in cycle.record_refs:
                    continue
                refs.append(ref)
                obj, errors = _read(ref, resolver)
                p13.extend(errors)
                if obj is None:
                    p13.append(Check("required-" + kind, "FAIL", "MISSING_EXPECTED_CYCLE_OR_SLOT_RECORD"))
                else:
                    retained[kind] = obj
        cycles[i] = ExpectedCycle(cycle.target_name, cycle.logical_ref, cycle.barrier, cycle.artifacts,
            all_records, tuple([subref, *all_records.values()]), cycle.deadlines)
        if "plan" in retained:
            time = retained.get("plan_time")
            bound = None if time is None else time.get("upper_bound")
            if time is not None:
                p13.append(_check("plan-time-model", time.get("object_type") == "SyntheticPlanTimeFact" and time.get("model_only") is True and
                    time.get("subject_ref") == identity(retained["plan"]).to_dict() and time.get("authentication") == "EXPLICIT_MODEL_AUTH_SEAM",
                    "PLAN_TIME_AUTHENTICATION_MODEL_SEAM"))
            p13.extend(validate_cycle_plan(retained["plan"], verified_plan_existence_bound=bound,
                verified_plan_ref=None if time is None else time.get("subject_ref"),
                required_slots=[slots[i].sealed_ref.to_dict()], required_schedule_policy_ref=source_refs["schedule"].to_dict()).checks)
        if "manifest" not in retained:
            continue
        manifest = retained["manifest"]
        if "plan" in retained:
            p13.extend(validate_cycle_manifest(retained["plan"], manifest).checks)
        for rawrow in manifest.get("slot_accounting", []):
            row = dict(rawrow)
            for label in ("attempt_refs", "issued_forecast_refs", "failure_record_refs", "omission_evidence_refs",
                          "ineligibility_evidence_refs", "unresolved_evidence_refs", "withdrawal_refs", "correction_refs"):
                values, errors = _parse_refs(row.get(label), label)
                p13.extend(errors)
                for ref in values:
                    refs.append(ref)
                    obj, errors = _read(ref, resolver)
                    p13.extend(errors)
                    if obj is None:
                        p13.append(Check("lifecycle-evidence", "FAIL", "MISSING_EXPECTED_CYCLE_OR_SLOT_RECORD"))
                        continue
                    p13.append(_check("lifecycle-binding", obj.get("model_only") is True and obj.get("slot_ref") == row.get("slot_ref"),
                        "LIFECYCLE_SLOT_ORIGIN_BINDING"))
                    if label == "issued_forecast_refs":
                        p13.append(_check("issued-origin", obj.get("object_type") == "SyntheticIssuedForecast" and
                            obj.get("origin") == "SYNTHETIC_ONLY" and obj.get("method_ref") == source_refs["method"].to_dict(),
                            "ISSUED_FORECAST_TYPE_METHOD_ORIGIN"))
            resolution = retained.get("resolution")
            if row.get("issuance_outcome") == "ISSUED":
                row["resolution_state"] = None if resolution is None else resolution.get("status")
                if resolution is not None:
                    p13.append(_check("resolution-binding", resolution.get("object_type") == "SyntheticResolutionRecord" and
                        resolution.get("model_only") is True and resolution.get("slot_ref") == row.get("slot_ref") and
                        resolution.get("issued_forecast_ref") in row.get("issued_forecast_refs", []),
                        "RESOLUTION_ISSUED_SUBJECT_BINDING"))
            else:
                row["resolution_state"] = "NOT_APPLICABLE"
            accounting.append(row)
    partition, projection = project_accounting(slots, accounting)
    p13.extend(projection)
    return finish(partition)
