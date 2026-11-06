"""Independent finite C05 model history selection and consumed admission.

Public evidence is fail-closed. Model native VALID results are transient internal
kernel inputs, always enclosed by ModelAdmission, never persisted as authority.
"""
from dataclasses import dataclass, replace
from types import SimpleNamespace
from .canonical import parse_json_strict
from .authority_primitives_v1 import ExactRef, AuthorityPrimitiveError, resolve_exact
from .canonical import canonical_json, sha256_hex
from .core import Check
from .replay_model_v1 import MODEL_SOURCE_REFS
from .qualification_model_pins_v1 import (MODEL_QUALIFICATION_SCOPE_REF, MODEL_QUALIFICATION_CONTRACT_REF,
    MODEL_QUALIFICATION_PACKAGES, MODEL_QUALIFICATION_HISTORY_INPUTS, MODEL_QUALIFICATION_FORMATION_REFS)
from .qualification_model_engine_v1 import execute_model_qualification_validation, derive_model_state, ref, check
from .g10_requirements_v1 import _fixed_basis
from .qualification_admission_v1 import require_qualification_admission, QualificationAdmissionError
from .replay_records_v1 import NativeReplay, emit_records, reduce_checks

OWNED = ("formation_authority", "formation_criteria", "formation_permission", "formation_repeatability_freshness", "formation_independence_review",
    "history_scope_head", "history_succession_coverage", "history_authentication", "history_effective_selection", "history_deadline_binding", "history_validation", "history_admission_consumed")

@dataclass(frozen=True)
class QualificationBoundary:
    role: str
    deadline: str
    ref: ExactRef

@dataclass(frozen=True)
class ModelAdmission:
    provider: str
    boundary_ref: ExactRef
    deadline: str
    profile_ref: ExactRef
    decision_ref: ExactRef
    history_ref: ExactRef
    validation_contract_ref: ExactRef
    validation_result: dict | None
    admitted: bool
    status: str
    reason_codes: tuple
    model_only: bool = True

@dataclass(frozen=True)
class QualificationScope:
    providers: tuple
    boundaries: tuple
    admissions: tuple
    independent_scope: dict
    selection_observations: dict
    history_inputs: dict
    formation_refs: dict
    checks: tuple
    records: tuple
    overall: str
    input_refs: tuple
    history_transition_trace: tuple = ()
    model_only: bool = True

def _read_raw(reference, resolver):
    if reference is None:
        return None, None, (Check('qualification-exact-input', 'UNKNOWN', 'INDEPENDENT_BASIS_MISSING'),)
    try:
        raw = resolver.resolve_exact(reference)
        resolved = resolve_exact(reference, SimpleNamespace(resolve_exact=lambda _: raw))
        return resolved, raw, ()
    except AuthorityPrimitiveError as exc:
        return None, None, (Check("qualification-exact-input", "UNKNOWN" if str(exc) == "NO_AUTHORITATIVE_RESULT" else "FAIL", str(exc)),)

    except Exception as exc:
        return None, None, (check("qualification-exact-input", None, "NO_AUTHORITATIVE_RESULT_" + type(exc).__name__),)

def _read(reference, resolver):
    obj, _, errors = _read_raw(reference, resolver)
    return obj, errors

def verify_model_history_selection(observed, independent_scope):
    """Scope is from the independently pinned model head, never the directory."""
    checks = []
    if not isinstance(observed, dict) or not isinstance(independent_scope, dict):
        return (check("history-selection", None, "INDEPENDENT_HISTORY_SCOPE_UNAVAILABLE"),)
    expected = independent_scope.get("provider_scope", {})
    checks.append(check("provider-scope", set(observed) == set(expected) and len(expected) == 3, "COMPLETE_PROVIDER_SCOPE_MISMATCH"))
    for provider, wanted in expected.items():
        actual = observed.get(provider)
        if not isinstance(actual, dict):
            continue
        checks += [check("history-head", actual.get("head_ref") == wanted["head_ref"], "INDEPENDENT_HISTORY_HEAD_MISMATCH"),
            check("history-cutoff", actual.get("cutoff") == wanted["cutoff"], "HISTORY_CUTOFF_DOES_NOT_COVER_BOUNDARIES")]
        for key, reason in (("event_refs", "COMPLETE_HISTORY_EVENT_SET_MISMATCH"), ("metadata_refs", "COMPLETE_HISTORY_METADATA_SET_MISMATCH"), ("formation_refs", "COMPLETE_FORMATION_SET_MISMATCH")):
            values = actual.get(key)
            try:
                actual_refs = [ExactRef.from_mapping(x) for x in values]
                expected_refs = {ExactRef.from_mapping(x) for x in wanted[key]}
                ok = len(actual_refs) == len(set(actual_refs)) and set(actual_refs) == expected_refs
            except (ValueError, KeyError, TypeError):
                ok = False
            checks.append(check("history-" + key, ok, reason))
    return tuple(checks)

def recheck_model_admission(original, **overrides):
    if original.validation_result is None:
        return replace(original, admitted=False, status="UNKNOWN", reason_codes=("RESULT_UNAVAILABLE_OR_UNAUTHENTICATED",))
    result = original.validation_result
    def expected(field):
        value = overrides.get(field, getattr(original, field))
        return value.to_dict()
    try:
        require_qualification_admission(ref(result).to_dict(), resolve_result=lambda _: canonical_json(result),
            expected_qualification_validation_contract_ref=expected("validation_contract_ref"),
            expected_provider_profile_ref=expected("profile_ref"), expected_qualification_decision_ref=expected("decision_ref"),
            expected_qualification_state_history_snapshot_ref=expected("history_ref"), frozen_deadline_utc=overrides.get("deadline", original.deadline))
        return replace(original, admitted=True, status="PASS", reason_codes=("MODEL_NATIVE_ADMISSION_EXECUTED",))
    except (QualificationAdmissionError, ValueError, AttributeError, KeyError, TypeError) as exc:
        reason = getattr(exc, "reason", "RESULT_UNAVAILABLE_OR_UNAUTHENTICATED")
        return replace(original, admitted=False, status="UNKNOWN" if reason == "RESULT_UNAVAILABLE_OR_UNAUTHENTICATED" else "FAIL", reason_codes=(reason,))
    except Exception as exc:
        return replace(original, admitted=False, status="UNKNOWN", reason_codes=("MODEL_ADMISSION_UNAVAILABLE_" + type(exc).__name__,))

def consume_model_admissions(scope, providers, boundary_ref):
    """Actual consequential full-profile consumer; no votes erase third provider."""
    checks = [check("consumer-provider-scope", len(providers) == len(set(providers)) and set(providers) == set(scope.providers), "COMPLETE_PROVIDER_SCOPE_MISMATCH"),
        check("consumer-boundary", boundary_ref in {b.ref for b in scope.boundaries}, "QUALIFICATION_BOUNDARY_UNKNOWN")]
    for provider in providers:
        matches = [a for a in scope.admissions if a.provider == provider and a.boundary_ref == boundary_ref]
        if len(matches) != 1:
            checks.append(check("consumer-admission", None, "QUALIFICATION_ADMISSION_UNAVAILABLE")); continue
        original = matches[0]
        current = recheck_model_admission(original)
        ok = original.admitted and original.status == "PASS" and current.admitted and original.model_only and scope.model_only
        status = "FAIL" if original.status == "FAIL" or current.status == "FAIL" else "UNKNOWN" if original.status == "UNKNOWN" or current.status == "UNKNOWN" else "PASS" if ok else "FAIL"
        checks.append(Check("consumer-admission-" + provider, status, "QUALIFICATION_ADMISSION_CONSUMED" if ok else "QUALIFICATION_ADMISSION_NOT_CONSUMABLE"))
    return tuple(checks)

def replay_qualification_scope(basis, cycles, requirements, resolver):
    checks, refs, admissions, observations, transitions = [], [], [], {}, []
    history_inputs = {p: tuple(ExactRef.from_mapping(x) for x in values) for p, values in MODEL_QUALIFICATION_HISTORY_INPUTS.items()}
    formation_refs = {p: ExactRef.from_mapping(v) for p, v in MODEL_QUALIFICATION_FORMATION_REFS.items()}
    providers = ("p1", "p2", "p3")
    scope, errors = _read(ExactRef.from_mapping(MODEL_QUALIFICATION_SCOPE_REF), resolver); checks.extend(errors)
    raw_scope, errors = _read(ExactRef.from_mapping(MODEL_SOURCE_REFS["scope"]), resolver); checks.extend(errors)
    contract_ref = ExactRef.from_mapping(MODEL_QUALIFICATION_CONTRACT_REF)
    contract, errors = _read(contract_ref, resolver); checks.extend(errors)
    for mapping in (MODEL_QUALIFICATION_SCOPE_REF, MODEL_SOURCE_REFS["scope"], MODEL_QUALIFICATION_CONTRACT_REF):
        refs.append(ExactRef.from_mapping(mapping))
    boundaries = tuple(QualificationBoundary(x["name"], x["boundary"], ExactRef.from_mapping(x["subject"])) for x in raw_scope["qualification_boundaries"]) if raw_scope else ()
    model = basis == _fixed_basis() and requirements.basis == basis
    checks.append(check("qualification-profile", True if model else None, "MODEL_QUALIFICATION_PROFILE_EXECUTED" if model else "MODEL_QUALIFICATION_PROFILE_NOT_APPLICABLE"))
    checks.append(Check("requirements", requirements.overall, "QUALIFICATION_REQUIREMENTS_UNIVERSE"))
    checks.append(Check("cycles", cycles.overall, "QUALIFICATION_CYCLE_UNIVERSE"))
    manifest, errors = _read(basis.subject, resolver); checks.extend(errors)
    if basis.subject is not None: refs.append(basis.subject)
    if manifest:
        pairs = {x["role"].removeprefix("provider-"): x["ref"] for x in manifest["dependency_roles"] if x["role"].startswith("provider-")}
        checks.append(check("manifest-provider-pairs", pairs == {p: MODEL_SOURCE_REFS["provider-" + p] for p in providers}, "MANIFEST_PROVIDER_PROFILE_PAIR_MISMATCH"))
        profiles = [requirements.source_objects.get(MODEL_SOURCE_REFS["provider-" + p]["object_id"]) for p in providers]
        checks.append(check("provider-independence", None if any(p is None for p in profiles) else len({p["independence"] for p in profiles}) == 3, "PROVIDER_CONTROL_GROUPS_NOT_INDEPENDENT"))
    if raw_scope:
        checks.append(check("provider-domain", {x["name"] for x in raw_scope["domains"]["providers"]} == set(providers), "COMPLETE_PROVIDER_SCOPE_MISMATCH"))
        events = {x["name"]: x["boundary"] for x in raw_scope["domains"]["events"]}
        derived = {"final-acceptance": raw_scope["horizon"]["start"]}
        for cycle in cycles.cycles:
            derived["plan-" + cycle.target_name] = cycle.deadlines["plan_commitment_deadline"]
            derived["cycle-" + cycle.target_name] = cycle.deadlines["external_proof_deadline"]
            # Fixed model DVR proof is due with external evidence, before the
            # native latest durability completion limit. Preserve both axes.
            derived["dvr-" + cycle.target_name] = cycle.deadlines["external_proof_deadline"]
            checks.append(check("dvr-maximum-deadline", derived["dvr-" + cycle.target_name] <= cycle.deadlines["durability_completion_deadline"], "DVR_MODEL_DEADLINE_EXCEEDS_COMPLETION_LIMIT"))
        checks.append(check("qualification-boundaries", None if cycles.overall != "PASS" else len(boundaries) == 11 and len({b.ref for b in boundaries}) == 11 and
            all(events.get(role) == deadline for role, deadline in derived.items()) and
            {b.role: b.deadline for b in boundaries if b.role != "formation"} == derived, "QUALIFICATION_DERIVED_BOUNDARY_SET_MISMATCH"))
    if scope and raw_scope:
        checks.append(check("scope-source", scope["scope_source_ref"] == ref(raw_scope).to_dict() and scope["contract_ref"] == contract_ref.to_dict(), "QUALIFICATION_SCOPE_BINDING_INVALID"))
        checks.append(check("contract-model", contract is not None and contract["criteria"] == "M1_QUALIFICATION_CRITERIA_V1" and contract["real_authority"] is False, "QUALIFICATION_MODEL_CONTRACT_INVALID"))
    base_checks = tuple(checks)
    for provider in providers:
        provider_checks, objects = [], {}
        for reference in history_inputs[provider]:
            obj, errors = _read(reference, resolver); provider_checks.extend(errors); refs.append(reference)
            if obj: objects[reference] = obj
        selected = scope["provider_scope"][provider] if scope else None
        if selected and len(objects) == len(history_inputs[provider]):
            head = objects[ExactRef.from_mapping(selected["head_ref"])]
            observations[provider] = {"head_ref": ref(head).to_dict(), "old_head_ref": head.get("predecessor_snapshot_ref"), "cutoff": head["through_as_of_utc"],
                "event_refs": head["requalification_event_refs"], "metadata_refs": head["metadata_review_refs"],
                "formation_refs": [ref(o).to_dict() for o in objects.values() if o["object_type"] == "SyntheticQualificationFormation"]}
        if selected and model and len(objects) == len(history_inputs[provider]) and not any(c.status != "PASS" for c in provider_checks):
            def typed(kind): return [o for o in objects.values() if o["object_type"] == "SyntheticQualification" + kind]
            profile, profile_errors = _read(ExactRef.from_mapping(MODEL_SOURCE_REFS["provider-" + provider]), resolver)
            provider_checks.extend(profile_errors)
            if profile:
                transition_points = {f["formed_at"] for f in typed("Formation")} | {e[x] for e in typed("Event") for x in ("effective_at", "detected_at")} | {m["reviewed_at"] for m in typed("Metadata")}
                for when in sorted(transition_points):
                    try:
                        state, decision, trace_checks = derive_model_state(profile, typed("Formation"), typed("Review"), typed("Metadata"), typed("Observation"), typed("Event"), when)
                    except Exception as exc:
                        state, decision = None, None
                        trace_checks = (check("transition-environment", None, "MODEL_TRANSITION_UNAVAILABLE_" + type(exc).__name__),)
                    provider_checks.extend(c for c in trace_checks if c.status == "UNKNOWN")
                    # These are actual historical states; adverse points need not
                    # be qualified. They never become eligible evidence events.
                    transitions.append({"provider": provider, "boundary": when, "state": state,
                        "decision_ref": ref(decision).to_dict() if decision else {},
                        "checks": tuple(trace_checks)})
        for boundary in boundaries:
            pins = MODEL_QUALIFICATION_PACKAGES[provider][boundary.role]
            local_checks = list(provider_checks)
            local_checks.extend(base_checks)
            package_ref, invocation_ref = map(ExactRef.from_mapping, (pins["package_ref"], pins["invocation_ref"]))
            package, package_raw, errors = _read_raw(package_ref, resolver); local_checks.extend(errors); refs.append(package_ref)
            invocation, errors = _read(invocation_ref, resolver); local_checks.extend(errors); refs.append(invocation_ref)
            members = {}
            for name, value in pins["members"].items():
                reference = ExactRef.from_mapping(value)
                obj, raw, errors = _read_raw(reference, resolver); local_checks.extend(errors); refs.append(reference)
                if obj is not None: members[name] = raw
            result = None
            if model and package and invocation and scope and reduce_checks(local_checks) == "PASS":
                local_checks.append(check("invocation-binding", invocation["contract_ref"] == contract_ref.to_dict() and
                    invocation["package_ref"] == package_ref.to_dict() and invocation["package_serialized_sha256"] == sha256_hex(package_raw) and
                    invocation["full_head_ref"] == selected["head_ref"] and invocation["boundary_ref"] == boundary.ref.to_dict(), "MODEL_INVOCATION_BINDING_INVALID"))
                projected = objects.values()
                expected_events = {ref(o) for o in projected if o["object_type"] == "SyntheticQualificationEvent" and o["detected_at"] <= boundary.deadline}
                expected_metadata = {ref(o) for o in projected if o["object_type"] == "SyntheticQualificationMetadata" and o["reviewed_at"] <= boundary.deadline}
                actual_objects = [o for raw in members.values() if (o := parse_json_strict(raw))]
                local_checks.append(check("complete-boundary-projection", expected_events == {ref(o) for o in actual_objects if o["object_type"] == "SyntheticQualificationEvent"} and
                    expected_metadata == {ref(o) for o in actual_objects if o["object_type"] == "SyntheticQualificationMetadata"}, "COMPLETE_HISTORY_BOUNDARY_PROJECTION_MISMATCH"))
                if reduce_checks(local_checks) == "PASS":
                    validation = execute_model_qualification_validation(package, members, contract_ref, invocation_ref)
                    result = validation.native_result; local_checks.extend(validation.checks)
            admission = ModelAdmission(provider, boundary.ref, boundary.deadline, ExactRef.from_mapping(MODEL_SOURCE_REFS["provider-" + provider]),
                ExactRef.from_mapping(pins["decision_ref"]), ExactRef.from_mapping(pins["history_ref"]), contract_ref, result,
                False, reduce_checks(local_checks), tuple(c.reason_code for c in local_checks if c.status != "PASS"))
            if result is not None:
                admission = recheck_model_admission(admission)
                local_checks.append(Check("native-admission", admission.status, ";".join(admission.reason_codes)))
            if admission.status == "PASS" and not admission.admitted:
                admission = replace(admission, status="UNKNOWN", reason_codes=("MODEL_VALIDATION_NOT_EXECUTED",))
            admissions.append(admission)
            checks.extend(c for c in local_checks if c not in checks)
    # Unavailable provider history remains UNKNOWN, not a proven deletion.
    if scope and len(observations) == 3:
        checks.extend(verify_model_history_selection(observations, scope))
    result_scope = QualificationScope(providers, boundaries, tuple(admissions), scope or {}, observations, history_inputs, formation_refs,
        tuple(checks), (), reduce_checks(checks), tuple(sorted(set(refs), key=lambda x: (x.object_id, x.content_sha256))), tuple(transitions))
    if model:
        for boundary in boundaries:
            checks.extend(consume_model_admissions(result_scope, providers, boundary.ref))
    facts = {name: NativeReplay(tuple(checks), result_scope.input_refs, model_seam=True) for name in OWNED}
    return replace(result_scope, checks=tuple(checks), overall=reduce_checks(checks), records=emit_records(requirements, facts, __file__))
