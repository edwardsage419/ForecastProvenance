"""Breaks: trusting submitted sets, incomplete source extraction or expansion."""
import importlib
import importlib.util
import json
from copy import deepcopy
from dataclasses import replace

import pytest

from forecast_trust_core.authority_primitives_v1 import ExactRef
from forecast_trust_core.g10_replay_v1 import mandatory_set_identity
from replay_model_support import ModelResolver, model_basis


def api():
    assert importlib.util.find_spec("forecast_trust_core.g10_requirements_v1"), "T02 reconstruction missing"
    return importlib.import_module("forecast_trust_core.g10_requirements_v1")


def test_complete_sources_are_independently_reconstructed_with_exact_instance_binding():
    u = api().reconstruct_requirements(model_basis(), ModelResolver())
    assert u.overall == "PASS"
    assert {k.predicate_id for k in u.mandatory_keys} >= {f"P{i:02}" for i in range(1, 26)}
    assert len(u.sources) >= 10
    assert len(u.requirements) > 60
    assert len(u.mandatory_keys) > len(u.requirements)
    assert all(p.status == "PASS" and p.evidence_refs for p in u.proofs)
    assert {p.mandatory_set_identity for p in u.proofs} == {mandatory_set_identity(u.mandatory_keys)}
    assert all(x.disposition in {"CONSEQUENTIAL", "NON_CONSEQUENTIAL"} and x.reason for x in u.inventory)
    retention = [r for r in u.requirements if r.check == "offline_backup_rule"]
    assert len(retention) == 1
    assert retention[0].keys and retention[0].source_location.endswith("/check")
    assert len(u.domains["targets"]) == len(u.domains["providers"]) == len(u.domains["slots"]) == 3
    assert len(u.domains["source_contracts"]) == 6
    assert len(u.domains["fixtures"]) == 3


def test_sources_and_mapping_cannot_shrink_with_caller_transport():
    m = api()
    resolver = ModelResolver()
    original = m.reconstruct_requirements(model_basis(), resolver)
    omitted = next(r for r in original.sources if "scientific" in r.object_id)
    del resolver.data[omitted]
    u = m.reconstruct_requirements(model_basis(), resolver)
    assert u.overall == "UNKNOWN"
    assert "SOURCE_BYTES_UNAVAILABLE" in {c.reason_code for c in u.diagnostics}
    assert omitted in u.required_sources
    assert u.proofs[0].status == "UNKNOWN"
    assert len(u.required_sources) == len(original.required_sources)


@pytest.mark.parametrize("mutation", ["field", "nested", "class", "instances", "wrong-version"])
def test_changed_source_bytes_cannot_authorize_reduced_obligations(mutation):
    m = api()
    resolver = ModelResolver()
    ref = next(r for r in resolver.data if "scientific" in r.object_id)
    obj = json.loads(resolver.data[ref])
    if mutation == "field":
        del obj["requirements"][0]["check"]
    elif mutation == "nested":
        obj["requirements"][0]["parameters"] = {"new_mandatory": True}
    elif mutation == "class":
        obj["requirements"] = [r for r in obj["requirements"] if r["predicate"] != "P21"]
    elif mutation == "instances":
        obj["requirements"][0]["domain"] = "governance"
    else:
        obj["model_version"] = "wrong-version"
    resolver.data[ref] = json.dumps(obj).encode()
    u = m.reconstruct_requirements(model_basis(), resolver)
    assert u.overall == "FAIL"
    assert "SOURCE_IDENTITY_MISMATCH" in {c.reason_code for c in u.diagnostics}


def test_transport_duplicates_and_unknown_objects_do_not_select_the_universe():
    m = api()
    resolver = ModelResolver()
    a = m.reconstruct_requirements(model_basis(), resolver)
    resolver.data[ExactRef("caller:unexpected", "f" * 64)] = b"{}"
    b = m.reconstruct_requirements(model_basis(), resolver)
    assert a.mandatory_keys == b.mandatory_keys
    assert a.required_sources == b.required_sources
    assert b.overall == "PASS"


def test_unknown_profile_and_missing_independent_basis_are_unknown_not_empty_pass():
    m = api()
    for b in [replace(model_basis(), profile=(ExactRef("unknown:profile", "e" * 64),)),
              replace(model_basis(), source_selection_rule_ref=None)]:
        u = m.reconstruct_requirements(b, ModelResolver())
        assert u.overall == "UNKNOWN"
        assert u.mandatory_keys
        assert u.proofs[0].status == "UNKNOWN"


def test_wrong_independent_root_or_scope_is_a_known_contradiction():
    m = api()
    for field in ["root_ref", "scope_ref", "rule_ref"]:
        u = m.reconstruct_requirements(replace(model_basis(), **{field: ExactRef("wrong:basis", "d" * 64)}), ModelResolver())
        assert u.overall == "FAIL"
        assert "INDEPENDENT_BASIS_MISMATCH" in {c.reason_code for c in u.diagnostics}


def test_full_location_inventory_keeps_unknown_nested_field_and_refuses_false_exclusion():
    m = api()
    source = {"requirements": [{"id": "one", "check": "offline_backup_rule", "predicate": "P11", "domain": "governance", "parameters": {"unrecognized_mandatory": "required"}}]}
    rows = m.inventory_source(ExactRef("synthetic:inventory-probe", "c" * 64), source)
    row = next(x for x in rows if x.location.endswith("/parameters/unrecognized_mandatory"))
    assert row.disposition == "UNKNOWN"
    assert m.classify_exclusion({"reason": "caller-says-not-required"}) == "UNKNOWN"


def test_mapping_deletion_cannot_silently_remove_a_whole_category(monkeypatch):
    m = api()
    with monkeypatch.context() as p:
        reduced = {k: v for k, v in m.CHECK_SPECS.items() if v[0] != "P21"}
        p.setattr(m, "CHECK_SPECS", reduced)
        u = m.reconstruct_requirements(model_basis(), ModelResolver())
    assert u.overall == "FAIL"
    assert "REQUIREMENT_MAPPING_MISSING" in {c.reason_code for c in u.diagnostics}
    assert any(k.predicate_id == "P21" for k in u.mandatory_keys)


def test_governance_basis_subject_is_the_retained_exact_candidate_not_a_hash_only_label():
    api()
    resolver = ModelResolver()
    raw = resolver.resolve_exact(model_basis().subject)
    assert raw is not None, "governance subject bytes must be replayable"
    manifest = json.loads(raw)
    assert manifest["object_type"] == "SyntheticCandidateManifest"
    assert manifest["sequence"] == 0
    assert manifest["project"] == model_basis().project
    u = api().reconstruct_requirements(model_basis(), resolver)
    assert {ExactRef.from_mapping(x["subject"]) for x in u.domains["governance"]} == {model_basis().subject}


@pytest.mark.parametrize("check", ["NT08_denominator", "offline_backup_rule"])
def test_independent_raw_clause_domain_comparison_detects_expander_instance_omission(monkeypatch, check):
    m = api()
    original = m._expand
    def omit_one(name, *args):
        keys = original(name, *args)
        return keys[:-1] if name == check else keys
    monkeypatch.setattr(m, "_expand", omit_one)
    u = m.reconstruct_requirements(model_basis(), ModelResolver())
    assert u.overall == "FAIL"
    assert u.proofs[2].status == "FAIL"
    assert "PREDICATE_INSTANCE_OMISSION_OR_SUBSTITUTION" in {c.reason_code for c in u.diagnostics}


def test_wrong_known_semantics_cannot_replace_source_field_mapping(monkeypatch):
    m = api()
    changed = deepcopy(m._FIELDS)
    changed["target"]["unit"] = "NT05_control_class"
    monkeypatch.setattr(m, "_FIELDS", changed)
    u = m.reconstruct_requirements(model_basis(), ModelResolver())
    assert u.overall == "FAIL"
    assert "SOURCE_FIELD_MAPPING_CONTRADICTION" in {c.reason_code for c in u.diagnostics}


@pytest.mark.parametrize("fault", ["omit", "false-nonconsequential"])
def test_independent_raw_source_inventory_audit_detects_lost_consequential_field(monkeypatch, fault):
    m = api()
    original = m.inventory_source
    def lose_unit(ref, obj):
        rows = original(ref, obj)
        if obj.get("kind") != "target":
            return rows
        if fault == "omit":
            return tuple(r for r in rows if r.location != "/unit")
        return tuple(replace(r, disposition="NON_CONSEQUENTIAL", check=None) if r.location == "/unit" else r for r in rows)
    monkeypatch.setattr(m, "inventory_source", lose_unit)
    u = m.reconstruct_requirements(model_basis(), ModelResolver())
    assert u.overall == "FAIL"
    assert any(c.reason_code in {"SOURCE_LOCATION_INVENTORY_OMISSION", "SOURCE_FIELD_DISPOSITION_CONTRADICTION"} for c in u.diagnostics)
