"""C05 independent model history and consequential admission consumption."""
import importlib
import importlib.util
import json
from dataclasses import replace
from copy import deepcopy
from pathlib import Path

import pytest
from forecast_trust_core.authority_primitives_v1 import ExactRef
from forecast_trust_core.canonical import canonical_json
from forecast_trust_core.g10_requirements_v1 import reconstruct_requirements
from forecast_trust_core.cycle_universe_v1 import reconstruct_cycle_universe
from replay_model_support import model_basis
from test_cycle_universe_v1 import resolver as cycle_resolver

CORPUS = Path(__file__).parent / "fixtures/independent_replay_v1"

def api():
    assert importlib.util.find_spec("forecast_trust_core.qualification_scope_v1"), "T05 qualification history replay missing"
    return importlib.import_module("forecast_trust_core.qualification_scope_v1")

def fixture():
    mod = api()
    r = cycle_resolver()
    for path in (CORPUS / "qualification").rglob("*.json"):
        obj = json.loads(path.read_bytes())
        if "object_id" in obj and "content_sha256" in obj:
            r.data[ExactRef(obj["object_id"], obj["content_sha256"])] = path.read_bytes()
    b = model_basis()
    requirements = reconstruct_requirements(b, r)
    cycles = reconstruct_cycle_universe(b, r)
    assert cycles.overall == "PASS"
    result = mod.replay_qualification_scope(b, cycles, requirements, r)
    return mod, b, r, requirements, cycles, result

def codes(result):
    return {c.reason_code for c in result.checks}

def test_full_scope_three_providers_all_eleven_distinct_role_boundaries_are_executed():
    _, _, _, _, _, result = fixture()
    assert result.overall == "PASS", codes(result)
    assert len(result.providers) == 3
    assert len(result.boundaries) == 11
    assert len(result.admissions) == 33
    assert len({(a.provider, a.boundary_ref) for a in result.admissions}) == 33
    assert {b.role for b in result.boundaries} == {"formation", "final-acceptance",
        "plan-t1", "cycle-t1", "dvr-t1", "plan-t2", "cycle-t2", "dvr-t2", "plan-t3", "cycle-t3", "dvr-t3"}
    assert all(a.admitted is True and a.validation_result is not None for a in result.admissions)
    assert result.records and all(r.raw_result for r in result.records)
    assert result.model_only is True

@pytest.mark.parametrize("provider", ["p1", "p2", "p3"])
def test_missing_whole_provider_history_never_qualified_by_two_other_provider_votes(provider):
    mod, b, r, requirements, cycles, result = fixture()
    for ref in result.history_inputs[provider]:
        r.data.pop(ref, None)
    changed = mod.replay_qualification_scope(b, cycles, requirements, r)
    assert {a.provider for a in changed.admissions} == {"p1", "p2", "p3"}
    assert changed.overall == "UNKNOWN", codes(changed)
    assert not any(a.admitted for a in changed.admissions if a.provider == provider)
    boundary = next(x for x in changed.boundaries if x.role == "final-acceptance")
    checks = mod.consume_model_admissions(changed, ("p1", "p2", "p3"), boundary.ref)
    assert mod.reduce_checks(checks) != "PASS"

@pytest.mark.parametrize("change,reason", [
    ("old_head", "INDEPENDENT_HISTORY_HEAD_MISMATCH"),
    ("early_cutoff", "HISTORY_CUTOFF_DOES_NOT_COVER_BOUNDARIES"),
    ("omit_adverse", "COMPLETE_HISTORY_EVENT_SET_MISMATCH"),
    ("omit_provider", "COMPLETE_PROVIDER_SCOPE_MISMATCH"),
    ("sync_directory_snapshot", "COMPLETE_HISTORY_EVENT_SET_MISMATCH"),
])
def test_caller_package_selection_cannot_shrink_independent_history_scope(change, reason):
    mod, _, _, _, _, result = fixture()
    selected = deepcopy(result.selection_observations)
    if change == "old_head":
        selected["p1"]["head_ref"] = selected["p1"]["old_head_ref"]
    elif change == "early_cutoff":
        selected["p1"]["cutoff"] = "2030-01-01T00:00:00Z"
    elif change == "omit_provider":
        del selected["p3"]
    else:
        selected["p1"]["event_refs"] = selected["p1"]["event_refs"][1:]
        if change == "sync_directory_snapshot":
            selected["p1"]["directory_event_refs"] = selected["p1"]["event_refs"]
    checks = mod.verify_model_history_selection(selected, result.independent_scope)
    assert mod.reduce_checks(checks) == "FAIL"
    assert reason in {c.reason_code for c in checks}

@pytest.mark.parametrize("field", ["history_ref", "profile_ref", "decision_ref", "validation_contract_ref", "deadline"])
def test_admission_cannot_be_rebound_to_caller_expected_refs_or_deadline(field):
    mod, _, _, _, _, result = fixture()
    original = result.admissions[0]
    changed = mod.recheck_model_admission(original, **{field: "2030-01-02T00:00:00Z" if field == "deadline" else ExactRef("wrong:expected", "a" * 64)})
    assert changed.admitted is False
    assert changed.status == "FAIL"

def test_native_invalid_admission_cannot_be_overridden_by_model_package_qualified_label():
    mod, _, _, _, _, result = fixture()
    bad = replace(result.admissions[0], admitted=False, status="FAIL", reason_codes=("VALIDATION_STATUS_NOT_VALID",))
    changed = replace(result, admissions=(bad,) + result.admissions[1:])
    checks = mod.consume_model_admissions(changed, ("p1", "p2", "p3"), bad.boundary_ref)
    assert mod.reduce_checks(checks) == "FAIL"
    assert "QUALIFICATION_ADMISSION_NOT_CONSUMABLE" in {c.reason_code for c in checks}

def test_unknown_validation_or_unavailable_admission_is_not_native_valid():
    mod, _, _, _, _, result = fixture()
    old = result.admissions[0]
    unknown = replace(old, admitted=False, status="UNKNOWN", validation_result=None)
    changed = replace(result, admissions=(unknown,) + result.admissions[1:])
    checks = mod.consume_model_admissions(changed, ("p1", "p2", "p3"), unknown.boundary_ref)
    assert mod.reduce_checks(checks) == "UNKNOWN"

def test_public_mode_cannot_consume_model_qualification_pass():
    mod, b, r, requirements, cycles, _ = fixture()
    public = mod.replay_qualification_scope(replace(b, mode="PUBLIC_EVIDENCE"), cycles, requirements, r)
    assert public.overall == "UNKNOWN"
    assert not any(a.admitted for a in public.admissions)
    assert "MODEL_QUALIFICATION_PROFILE_NOT_APPLICABLE" in codes(public)

def test_declared_qualified_profile_does_not_skip_raw_formation_criteria():
    mod, b, r, requirements, cycles, result = fixture()
    ref = result.formation_refs["p1"]
    obj = json.loads(r.data[ref])
    obj["permission"] = "DENIED"
    r.data[ref] = canonical_json(obj)
    changed = mod.replay_qualification_scope(b, cycles, requirements, r)
    assert changed.overall == "FAIL"
    assert not any(a.admitted for a in changed.admissions if a.provider == "p1")

def test_formation_role_owner_does_not_transfer_initial_acceptance_authority():
    mod, b, r, requirements, cycles, result = fixture()
    ref = result.formation_refs["p1"]
    obj = json.loads(r.data[ref])
    obj["authority_role"] = "MODEL_INITIAL_ACCEPT_ONLY"
    r.data[ref] = canonical_json(obj)
    changed = mod.replay_qualification_scope(b, cycles, requirements, r)
    assert changed.overall == "FAIL"

# Causal kernel tests deliberately avoid the outer immutable pin rejection.
def raw_formation_inputs():
    from forecast_trust_core.qualification_model_engine_v1 import validate_model_formation
    _, _, r, _, _, scope = fixture()
    form = deepcopy(json.loads(r.data[scope.formation_refs["p1"]]))
    def resolve(mapping): return deepcopy(json.loads(r.data[ExactRef.from_mapping(mapping)]))
    profile, review, metadata = map(resolve, (form["profile_ref"], form["review_ref"], form["metadata_ref"]))
    observations = [resolve(x) for x in form["observation_refs"]]
    return validate_model_formation, form, profile, review, metadata, observations

@pytest.mark.parametrize("change", ["permission", "role", "criteria", "executor", "review_time", "stale", "nonce", "decoded", "radius", "bool_integer", "provider", "unknown_field"])
def test_causal_formation_criteria_no_hash_shortcut(change):
    validate, form, profile, review, metadata, obs = raw_formation_inputs()
    if change == "permission": metadata["permission"] = "DENIED"
    elif change == "role": form["authority_role"] = "MODEL_INITIAL_ACCEPT_ONLY"
    elif change == "criteria": review["criteria"] = "wrong-model-criteria"
    elif change == "executor": review["reviewer"] = review["executor"]
    elif change == "review_time": review["reviewed_at"] = "2030-01-02T00:00:00Z"
    elif change == "stale": metadata["retrieved_at"] = "2029-01-01T00:00:00Z"
    elif change == "nonce": obs[1]["nonce"] = obs[0]["nonce"]
    elif change == "decoded": obs[0]["decoded"]["midpoint_us"] += 1
    elif change == "radius": obs[0]["radius_us"] = -1
    elif change == "bool_integer": obs[0]["radius_us"] = True
    elif change == "provider": review["provider"] = "p3"
    else: form["criteria_override"] = "PASS"
    assert api().reduce_checks(validate(form, profile, review, metadata, obs, as_of="2030-01-01T00:00:00Z")) == "FAIL"


def state_inputs():
    from forecast_trust_core.qualification_model_engine_v1 import derive_model_state
    _, _, r, _, _, scope = fixture()
    objects = [deepcopy(json.loads(r.data[x])) for x in scope.history_inputs["p1"]]
    def typed(kind): return [o for o in objects if o["object_type"] == "SyntheticQualification" + kind]
    profile = deepcopy(json.loads(r.data[ExactRef.from_mapping(api().MODEL_SOURCE_REFS["provider-p1"])]))
    return derive_model_state, profile, typed("Formation"), typed("Review"), typed("Metadata"), typed("Observation"), typed("Event")


def test_adverse_between_decisions_is_requalification_required_until_actual_new_formation():
    derive, profile, forms, reviews, metadata, obs, events = state_inputs()
    state, selected, checks = derive(profile, forms, reviews, metadata, obs, events, "2030-01-17T00:00:00Z")
    assert state == "REQUALIFICATION_REQUIRED"
    assert selected["formed_at"] == "2029-12-20T04:00:00Z"
    assert api().reduce_checks(checks) == "FAIL"
    state, selected, checks = derive(profile, forms, reviews, metadata, obs, events, "2030-02-01T00:00:00Z")
    assert state == "PRODUCTION_QUALIFIED" and api().reduce_checks(checks) == "PASS"


def test_post_decision_metadata_change_cannot_be_ignored():
    derive, profile, forms, reviews, metadata, obs, events = state_inputs()
    late = deepcopy(metadata[-1]); late["reviewed_at"] = "2030-01-25T00:00:00Z"; late["change_disposition"] = "CHANGED"
    metadata.append(late)
    state, _, checks = derive(profile, forms, reviews, metadata, obs, events, "2030-02-01T00:00:00Z")
    assert state != "PRODUCTION_QUALIFIED" and api().reduce_checks(checks) == "FAIL"


def test_same_time_conflicting_decisions_are_not_hash_tiebroken():
    derive, profile, forms, reviews, metadata, obs, events = state_inputs()
    conflict = deepcopy(forms[-1]); conflict["permission"] = "DENIED"; conflict["content_sha256"] = "0" * 64
    forms.append(conflict)
    state, _, checks = derive(profile, forms, reviews, metadata, obs, events, "2030-02-01T00:00:00Z")
    assert state != "PRODUCTION_QUALIFIED" and api().reduce_checks(checks) == "FAIL"


def test_raw_member_serialization_mismatch_is_not_silently_canonicalized():
    mod, b, r, requirements, cycles, scope = fixture()
    pins = mod.MODEL_QUALIFICATION_PACKAGES["p1"]["formation"]
    member = ExactRef.from_mapping(next(iter(pins["members"].values())))
    r.data[member] = b" " + r.data[member]
    changed = mod.replay_qualification_scope(b, cycles, requirements, r)
    assert changed.overall == "FAIL"
    assert not next(a for a in changed.admissions if a.provider == "p1" and a.boundary_ref == scope.admissions[0].boundary_ref).admitted


def test_native_history_and_admission_kernels_are_causally_executed(monkeypatch):
    from forecast_trust_core import qualification_state_package_v2 as native
    calls = {}
    for name in ("_read_raw_members", "validate_history_cutoff", "validate_history_succession", "validate_history_completeness"):
        original = getattr(native, name)
        def wrapper(*args, _name=name, _original=original, **kwargs):
            calls[_name] = calls.get(_name, 0) + 1
            return _original(*args, **kwargs)
        monkeypatch.setattr(native, name, wrapper)
    _, _, _, _, _, scope = fixture()
    assert scope.overall == "PASS"
    assert calls == {name: 33 for name in calls} and len(calls) == 4

@pytest.mark.parametrize("criterion", ["CRYPTOGRAPHIC", "PROTOCOL_STABILITY", "PRODUCTION_USE_PERMISSION", "LIVE_REPEATABILITY", "PILOT_EXPERIMENTAL", "OPERATIONAL", "INDEPENDENCE", "COMMON_DEPENDENCY", "PROVENANCE", "EVIDENCE_MANIFEST", "FRESHNESS", "FAILURE_PATH", "MERKLE_COVERAGE", "STANDARDS_TRANSITION", "SCHEMA_VALIDATOR_REGRESSION"])
def test_all_frozen_criterion_families_have_actual_derived_results_and_raw_bindings(criterion):
    validate, form, profile, review, metadata, obs = raw_formation_inputs()
    evidence = review.get("criteria_evidence")
    assert isinstance(evidence, dict) and criterion in evidence, "full native review matrix missing"
    checks = validate(form, profile, review, metadata, obs, as_of="2030-01-01T00:00:00Z")
    assert any(c.check_id == "criterion-" + criterion and c.status == "PASS" for c in checks)
    review["criteria_evidence"].pop(criterion)
    assert api().reduce_checks(validate(form, profile, review, metadata, obs, as_of="2030-01-01T00:00:00Z")) == "FAIL"


def engine_inputs():
    from forecast_trust_core.qualification_model_engine_v1 import execute_model_qualification_validation
    mod, _, r, _, _, scope = fixture()
    pins = mod.MODEL_QUALIFICATION_PACKAGES["p1"]["formation"]
    package = json.loads(r.data[ExactRef.from_mapping(pins["package_ref"])])
    members = {name: r.data[ExactRef.from_mapping(value)] for name, value in pins["members"].items()}
    return execute_model_qualification_validation, package, members, scope.admissions[0], ExactRef.from_mapping(pins["invocation_ref"])


def reseal(obj):
    from forecast_trust_core.canonical import seal_object
    from forecast_trust_core.qualification_model_engine_v1 import DERIVED
    return seal_object({k: v for k, v in obj.items() if k not in DERIVED}, object_type=obj["object_type"],
        stable_context="M1_DEVELOPMENT_ONLY", semantic_id=obj["object_id"])


def test_actual_native_invalid_result_cannot_be_overridden_by_retained_qualified_report():
    from forecast_trust_core.canonical import sha256_hex
    execute, package, members, admission, invocation = engine_inputs()
    auth_name = next(n for n, raw in members.items() if json.loads(raw)["object_type"] == "SyntheticQualificationAuthentication")
    auth = json.loads(members[auth_name]); auth["authority_role"] = "MODEL_INITIAL_ACCEPT_ONLY"
    members[auth_name] = canonical_json(reseal(auth))
    for m in package["members"]:
        if m["relative_path"] == auth_name:
            m["byte_length"], m["sha256"] = len(members[auth_name]), sha256_hex(members[auth_name])
    package = reseal(package)
    validation = execute(package, members, admission.validation_contract_ref, invocation)
    assert validation.native_result["validation_status"] == "INVALID"
    assert any(json.loads(raw).get("state") == "PRODUCTION_QUALIFIED" for raw in members.values())
    checked = api().recheck_model_admission(replace(admission, validation_result=validation.native_result))
    assert not checked.admitted and checked.status == "FAIL"
    assert checked.reason_codes == ("VALIDATION_STATUS_NOT_VALID",)


def test_actual_model_validation_environment_exception_is_unknown(monkeypatch):
    import forecast_trust_core.qualification_model_engine_v1 as engine
    execute, package, members, admission, invocation = engine_inputs()
    def unavailable(*_args, **_kwargs): raise OSError("model temporary filesystem unavailable")
    monkeypatch.setattr(engine.native_closure, "_open_root", unavailable)
    validation = execute(package, members, admission.validation_contract_ref, invocation)
    assert validation.native_result is None and api().reduce_checks(validation.checks) == "UNKNOWN"
    assert not api().recheck_model_admission(replace(admission, validation_result=None)).admitted


def test_native_real_validation_entry_rejects_synthetic_contract_without_crypto_backend(tmp_path):
    from forecast_trust_core.qualification_validation_v1 import execute_qualification_validation
    mod, _, r, _, _, scope = fixture()
    pins = mod.MODEL_QUALIFICATION_PACKAGES["p1"]["formation"]
    def resolver(mapping): return r.resolve_exact(ExactRef.from_mapping(mapping))
    result = execute_qualification_validation(scope.admissions[0].validation_contract_ref.to_dict(), pins["invocation_ref"],
        tmp_path / "package", tmp_path / "evidence", resolve_static_object=resolver, resolve_invocation=resolver,
        resolve_package=resolver, resolve_evidence_manifest=resolver, qualification_authority_public_key=None,
        qualification_ed25519_build_profile=None, qualification_ed25519_binary=None)
    assert result is None


def test_complete_formation_and_effective_detected_reviewed_transition_trace_is_executed():
    _, _, _, _, _, scope = fixture()
    assert len(scope.history_transition_trace) == 24
    assert {x["provider"] for x in scope.history_transition_trace} == {"p1", "p2", "p3"}
    for provider in scope.providers:
        rows = [x for x in scope.history_transition_trace if x["provider"] == provider]
        assert len({x["boundary"] for x in rows}) == 8
        assert any(x["state"] == "REQUALIFICATION_REQUIRED" for x in rows)
        assert any(x["state"] == "PRODUCTION_QUALIFIED" for x in rows)

@pytest.mark.parametrize("exception_type", [RuntimeError, TimeoutError, OSError])
def test_unexpected_package_adapter_exception_is_explicit_unknown_with_class(monkeypatch, exception_type):
    import forecast_trust_core.qualification_model_engine_v1 as engine
    execute, package, members, admission, invocation = engine_inputs()
    def unavailable(*_args, **_kwargs): raise exception_type("model adapter unavailable")
    monkeypatch.setattr(engine.native_closure, "_open_root", unavailable)
    validation = execute(package, members, admission.validation_contract_ref, invocation)
    assert validation.native_result is None and api().reduce_checks(validation.checks) == "UNKNOWN"
    assert any(exception_type.__name__ in c.reason_code for c in validation.checks)

@pytest.mark.parametrize("exception_type", [OSError, RuntimeError])
def test_runtime_bytes_exception_in_formation_and_transition_is_unknown(monkeypatch, exception_type):
    import sys
    validate, form, profile, review, metadata, obs = raw_formation_inputs()
    mod, b, r, requirements, cycles, _ = fixture()
    original = Path.read_bytes
    def unavailable(path):
        if str(path) == str(Path(sys.executable)):
            raise exception_type("model runtime bytes unavailable")
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", unavailable)
    checks = validate(form, profile, review, metadata, obs, as_of="2030-01-01T00:00:00Z")
    assert mod.reduce_checks(checks) == "UNKNOWN"
    assert any(exception_type.__name__ in c.reason_code for c in checks)
    scope = mod.replay_qualification_scope(b, cycles, requirements, r)
    assert scope.overall == "UNKNOWN" and not any(a.admitted for a in scope.admissions)
    assert any(c.status == "UNKNOWN" and exception_type.__name__ in c.reason_code for c in scope.checks)


def test_known_formation_fail_dominates_later_runtime_unavailability(monkeypatch):
    import sys
    validate, form, profile, review, metadata, obs = raw_formation_inputs()
    metadata["permission"] = "DENIED"
    original = Path.read_bytes
    def unavailable(path):
        if str(path) == str(Path(sys.executable)): raise OSError("model runtime unavailable")
        return original(path)
    monkeypatch.setattr(Path, "read_bytes", unavailable)
    checks = validate(form, profile, review, metadata, obs, as_of="2030-01-01T00:00:00Z")
    assert api().reduce_checks(checks) == "FAIL"
    assert any(c.status == "FAIL" and c.reason_code == "MODEL_PERMISSION_OR_SERVICE_INVALID" for c in checks)
    assert any(c.status == "UNKNOWN" for c in checks)

@pytest.mark.parametrize("exception_type", [RuntimeError, TimeoutError, OSError])
def test_unavailable_state_selection_does_not_become_known_wrong_decision(monkeypatch, exception_type):
    import forecast_trust_core.qualification_model_engine_v1 as engine
    execute, package, members, admission, invocation = engine_inputs()
    def unavailable(*_args, **_kwargs): raise exception_type("model state unavailable")
    monkeypatch.setattr(engine, "utc", unavailable)
    result = execute(package, members, admission.validation_contract_ref, invocation)
    assert result.native_result is None and api().reduce_checks(result.checks) == "UNKNOWN"
    assert any(c.check_id == "selected-decision" and c.status == "UNKNOWN" for c in result.checks)
    assert any(exception_type.__name__ in c.reason_code for c in result.checks)


def test_established_wrong_selected_decision_remains_fail():
    execute, package, members, admission, invocation = engine_inputs()
    package["decision_ref"] = ExactRef("wrong:decision", "f" * 64).to_dict()
    result = execute(reseal(package), members, admission.validation_contract_ref, invocation)
    assert result.native_result["validation_status"] == "INVALID" and api().reduce_checks(result.checks) == "FAIL"
    assert any(c.check_id == "selected-decision" and c.status == "FAIL" for c in result.checks)


def test_prior_authentication_fail_is_retained_during_state_unavailability(monkeypatch):
    import forecast_trust_core.qualification_model_engine_v1 as engine
    from forecast_trust_core.canonical import sha256_hex
    execute, package, members, admission, invocation = engine_inputs()
    auth_name = next(n for n, raw in members.items() if json.loads(raw)["object_type"] == "SyntheticQualificationAuthentication")
    auth = json.loads(members[auth_name]); auth["authority_role"] = "MODEL_INITIAL_ACCEPT_ONLY"
    members[auth_name] = canonical_json(reseal(auth))
    for m in package["members"]:
        if m["relative_path"] == auth_name:
            m["byte_length"], m["sha256"] = len(members[auth_name]), sha256_hex(members[auth_name])
    def unavailable(*_args, **_kwargs): raise RuntimeError("model state unavailable")
    monkeypatch.setattr(engine, "utc", unavailable)
    result = execute(reseal(package), members, admission.validation_contract_ref, invocation)
    assert result.native_result["validation_status"] == "INVALID" and api().reduce_checks(result.checks) == "FAIL"
    assert any(c.check_id == "model-auth-set" and c.status == "FAIL" for c in result.checks)
    assert any(c.check_id == "selected-decision" and c.status == "UNKNOWN" for c in result.checks)

@pytest.mark.parametrize("failure", ["raises", "none"])
def test_native_result_adapter_unavailable_keeps_known_invalid_and_no_false_pass(monkeypatch, failure):
    import forecast_trust_core.qualification_model_engine_v1 as engine
    execute, package, members, admission, invocation = engine_inputs()
    def unavailable(*_args, **_kwargs):
        if failure == "raises": raise RuntimeError("model result adapter unavailable")
        return None
    monkeypatch.setattr(engine, "build_qualification_validation_result", unavailable)
    result = execute(package, members, admission.validation_contract_ref, invocation)
    assert result.native_result is None and api().reduce_checks(result.checks) == "UNKNOWN"
    # Deterministically invalid member bytes plus unavailable result adapter:
    # preserve the invalid-byte fact, never report unavailable validation PASS.
    first = next(iter(members)); members[first] = b" " + members[first]
    result = execute(package, members, admission.validation_contract_ref, invocation)
    assert result.native_result is None and api().reduce_checks(result.checks) == "FAIL"
    assert any(c.status == "FAIL" for c in result.checks) and any(c.status == "UNKNOWN" for c in result.checks)


def test_known_malformed_package_identity_does_not_escape_invalid_result_binding():
    execute, package, members, admission, invocation = engine_inputs()
    package.pop("object_id")
    result = execute(package, members, admission.validation_contract_ref, invocation)
    assert result.native_result is None and api().reduce_checks(result.checks) == "FAIL"
    assert any(c.status == "UNKNOWN" for c in result.checks)
