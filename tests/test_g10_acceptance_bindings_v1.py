"""Actual acceptance/report composition, independent of wall/Bitcoin results."""
import importlib
import importlib.util
from copy import deepcopy
from dataclasses import replace

import pytest

from forecast_trust_core.canonical import seal_object, canonical_json
from forecast_trust_core.authority_primitives_v1 import ExactRef
from forecast_trust_core.core import Check
from forecast_trust_core.g10_requirements_v1 import reconstruct_requirements
from replay_model_support import ModelResolver, model_basis


def api():
    assert importlib.util.find_spec("forecast_trust_core.g10_acceptance_v1"), "T03 acceptance composition missing"
    return importlib.import_module("forecast_trust_core.g10_acceptance_v1")


def store(resolver, payload, kind, name):
    obj = seal_object(payload, object_type=kind, stable_context="M1_DEVELOPMENT_ONLY", semantic_id=name)
    ref = ExactRef(obj["object_id"], obj["content_sha256"])
    resolver.data[ref] = canonical_json(obj)
    return ref, obj


def reseal(resolver, obj, **changes):
    payload = {k: deepcopy(v) for k, v in obj.items() if k not in {"object_id", "object_type", "payload_sha256", "content_sha256"}}
    payload.update(changes)
    return store(resolver, payload, obj["object_type"], obj["object_id"])


def facts():
    b = model_basis()
    r = ModelResolver()
    u = reconstruct_requirements(b, r)
    reports = []
    expected_checks = {"runtime": ["python-profile", "test-dependencies"], "sources": ["source-universe", "clause-coverage", "predicate-expansion"], "qualification": ["complete-history", "consumed-admission"], "bitcoin-pre-signing": ["model-bitcoin-capability"], "candidate-review": ["manifest-role-closure", "finding-closure"]}
    for name in ("runtime", "sources", "qualification", "bitcoin-pre-signing", "candidate-review"):
        # Missing future-component evidence is explicitly UNKNOWN at this
        # stage; it never becomes PASS merely because a report says PASS.
        ref, obj = store(r, {"schema_version": "MODEL_REPORT_V1", "model_only": True,
                            "kind": name, "subject_ref": b.subject.to_dict(),
                            "validator_ref": b.profile[0].to_dict(), "dependency_refs": [b.rule_ref.to_dict()],
                            "stage": "PRE_SIGNING", "checks": [{"check_id": c, "status": "UNKNOWN", "reason_code": "UNEXECUTED"} for c in expected_checks[name]], "status": "UNKNOWN", "finding_refs": []},
                         "SyntheticReplayReport", "model:report:" + name)
        reports.append(ref)
    carrier, _ = store(r, {"model_only": True, "actor": "MODEL_OWNER", "action": "INITIAL_ACCEPT", "subject_ref": b.subject.to_dict(), "root_ref": b.root_ref.to_dict()}, "SyntheticAuthenticationFact", "model:authentication:initial")
    acceptance, _ = store(r, {"schema_version": "2.0", "candidate_manifest_ref": b.subject.to_dict(),
                             "bootstrap_governance_root_ref": b.root_ref.to_dict(), "acceptance_rule_ref": b.rule_ref.to_dict(),
                             "required_validation_report_refs": [x.to_dict() for x in reports],
                             "authority_ref": b.root_ref.to_dict(), "decision": "ACCEPT", "reason_codes": ["MODEL_ONLY"],
                             "blocking_finding_refs": [], "signature_ref": carrier.to_dict()}, "ManifestAcceptance", "model:acceptance:initial")
    return b, u, r, acceptance, tuple(reports)


def replay(b, u, r, acceptance, reports, component_reports=None):
    return api().replay_acceptance_bindings(b, u, r, acceptance_ref=acceptance, report_refs=reports, component_reports=component_reports)


def codes(rows):
    return {c for row in rows for c in row.reason_codes}


def test_historical_report_pass_current_runtime_unavailable_is_unknown():
    import json
    b,u,r,acceptance,reports=facts()
    old=json.loads(r.data[reports[0]])
    rows=[dict(x,status='PASS') for x in old['checks']]
    new,_=reseal(r,old,checks=rows,status='PASS')
    refs=(new,*reports[1:])
    ar,_=reseal(r,json.loads(r.data[acceptance]),required_validation_report_refs=[x.to_dict() for x in refs])
    actual={'runtime':tuple(Check(x['check_id'],'UNKNOWN',x['reason_code']) for x in rows)}
    result=replay(b,u,r,ar,refs,actual)
    assert {x.normalized for x in result if x.key.predicate_id=='P16'}=={'UNKNOWN'}
    assert 'REPORT_CURRENT_REPLAY_UNAVAILABLE' in codes(result)


def test_structural_acceptance_and_report_unknowns_are_separate_raw_records():
    args = facts()
    rows = replay(*args)
    assert rows and all(row.raw_result for row in rows)
    assert any(row.normalized == "PASS" and row.key.predicate_id == "P07" for row in rows)
    assert any(row.normalized == "UNKNOWN" and row.key.predicate_id == "P16" for row in rows)
    assert "REPORT_REPLAY_NOT_EXECUTED" in codes(rows)


def test_reject_with_local_contract_valid_is_actual_p07_failure():
    b, u, r, acceptance, reports = facts()
    import json
    ref, _ = reseal(r, json.loads(r.data[acceptance]), decision="REJECT")
    rows = replay(b, u, r, ref, reports)
    assert any(row.normalized == "FAIL" and row.key.predicate_id == "P07" for row in rows)
    assert "MANIFEST_NOT_ACCEPTED" in codes(rows)


@pytest.mark.parametrize("field", ["bootstrap_governance_root_ref", "acceptance_rule_ref", "candidate_manifest_ref", "authority_ref"])
def test_wrong_exact_acceptance_binding_fails(field):
    import json
    b, u, r, acceptance, reports = facts()
    ref, _ = reseal(r, json.loads(r.data[acceptance]), **{field: ExactRef("wrong:subject", "d" * 64).to_dict()})
    rows = replay(b, u, r, ref, reports)
    assert any(row.normalized == "FAIL" for row in rows)


@pytest.mark.parametrize("mutation", ["kind", "subject", "validator", "stage", "dependency", "duplicate", "missing"])
def test_report_roles_subject_stage_cardinality_and_validator_checked(mutation):
    import json
    b, u, r, acceptance, reports = facts()
    refs = list(reports)
    obj = json.loads(r.data[refs[0]])
    updates = {"kind": "wrong-kind", "subject": ExactRef("wrong:subject", "e" * 64).to_dict(),
               "validator": ExactRef("wrong:validator", "f" * 64).to_dict(), "stage": "POST_SIGNING",
               "dependency": []}
    fields = {"kind": "kind", "subject": "subject_ref", "validator": "validator_ref", "stage": "stage", "dependency": "dependency_refs"}
    if mutation == "duplicate":
        refs.append(refs[0])
    elif mutation == "missing":
        refs.pop(3)  # bitcoin pre-signing role is mandatory, never silently dropped
    else:
        refs[0], _ = reseal(r, obj, **{fields[mutation]: updates[mutation]})
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, revised, tuple(refs))
    assert any(row.normalized == "FAIL" and row.key.predicate_id == "P16" for row in rows)


def test_report_blocker_cannot_be_hidden_by_empty_acceptance_blockers():
    import json
    b, u, r, acceptance, reports = facts()
    finding, _ = store(r, {"model_only": True, "subject_ref": b.subject.to_dict(), "blocking": True, "state": "OPEN"}, "SyntheticFinding", "model:finding:one")
    first, _ = reseal(r, json.loads(r.data[reports[0]]), finding_refs=[finding.to_dict()])
    refs = (first,) + reports[1:]
    ref, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, ref, refs)
    assert any(row.key.predicate_id == "P22" and row.normalized == "FAIL" and finding in row.finding_refs for row in rows)


def test_old_finding_closure_is_not_valid_for_new_exact_subject():
    import json
    b, u, r, acceptance, reports = facts()
    old = ExactRef(b.subject.object_id, "d" * 64)
    closure, _ = store(r, {"model_only": True, "subject_ref": old.to_dict(), "finding_ref": ExactRef("model:finding:one", "c" * 64).to_dict(), "evidence_refs": [b.rule_ref.to_dict()]}, "SyntheticFindingClosure", "model:closure:old")
    finding, _ = store(r, {"model_only": True, "subject_ref": b.subject.to_dict(), "blocking": True, "state": "CLOSED", "closure_ref": closure.to_dict()}, "SyntheticFinding", "model:finding:one")
    report, _ = reseal(r, json.loads(r.data[reports[0]]), finding_refs=[finding.to_dict()])
    refs = (report,) + reports[1:]
    ref, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, ref, refs)
    assert "FINDING_CLOSURE_WRONG_SUBJECT_OR_FINDING" in codes(rows)


def test_report_pass_label_cannot_override_actual_raw_fail():
    import json
    b, u, r, acceptance, reports = facts()
    first, _ = reseal(r, json.loads(r.data[reports[0]]), status="PASS", checks=[{"check_id": "python-profile", "status": "PASS", "reason_code": "runtime"}])
    refs = (first,) + reports[1:]
    ref, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, ref, refs, {"runtime": (Check("python-profile", "FAIL", "wrong-runtime"),)})
    assert "PERSISTED_REPORT_DIFFERS_FROM_RAW_REPLAY" in codes(rows)
    assert any(row.normalized == "FAIL" and row.key.predicate_id == "P16" for row in rows)


def test_pre_signing_report_cannot_refer_to_acceptance_or_final_g10():
    import json
    b, u, r, acceptance, reports = facts()
    first, _ = reseal(r, json.loads(r.data[reports[0]]), dependency_refs=[acceptance.to_dict(), b.rule_ref.to_dict()])
    refs = (first,) + reports[1:]
    ref, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, ref, refs)
    assert "PRE_SIGNING_ACCEPTANCE_OR_FINAL_REPORT_CYCLE" in codes(rows)


def test_missing_public_authentication_contract_never_constructs_a_signature_message():
    b, u, r, acceptance, reports = facts()
    b = replace(b, mode="PUBLIC_EVIDENCE")
    u = reconstruct_requirements(b, r)
    rows = replay(b, u, r, acceptance, reports)
    auth = [row for row in rows if row.key.predicate_id in {"P05", "P06"}]
    assert auth and all(row.normalized == "UNKNOWN" for row in auth)
    assert "BLOCKED_BY_G02" in codes(auth)


def test_unavailable_acceptance_preserves_unknown_raw_rows():
    b, u, r, acceptance, reports = facts()
    del r.data[acceptance]
    rows = replay(b, u, r, acceptance, reports)
    assert all(row.normalized == "UNKNOWN" for row in rows if row.key.predicate_id == "P07")


def test_missing_signature_ref_returns_known_contract_fail_instead_of_exception():
    import json
    b, u, r, acceptance, reports = facts()
    payload = json.loads(r.data[acceptance])
    del payload["signature_ref"]
    revised, _ = reseal(r, payload)
    rows = replay(b, u, r, revised, reports)
    assert "ACCEPTANCE_CONTRACT_INVALID" in codes(rows)


def test_immutable_open_finding_can_have_separate_exact_closure_with_reexecuted_evidence():
    import json
    b, u, r, acceptance, reports = facts()
    finding, _ = store(r, {"model_only": True, "subject_ref": b.subject.to_dict(), "blocking": True, "state": "OPEN", "check_id": "root-project"}, "SyntheticFinding", "model:finding:closed-later")
    evidence, _ = store(r, {"model_only": True, "subject_ref": b.subject.to_dict(), "root_ref": b.root_ref.to_dict(), "check_id": "root-project", "expected_status": "PASS"}, "SyntheticClosureEvidence", "model:closure:evidence")
    closure, _ = store(r, {"model_only": True, "subject_ref": b.subject.to_dict(), "finding_ref": finding.to_dict(), "evidence_refs": [evidence.to_dict()]}, "SyntheticFindingClosure", "model:closure:separate")
    first, _ = reseal(r, json.loads(r.data[reports[0]]), finding_refs=[finding.to_dict()], finding_closure_refs=[closure.to_dict()])
    refs = (first,) + reports[1:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, revised, refs)
    assert all(row.normalized == "PASS" for row in rows if row.key.predicate_id == "P22")
    assert "EXACT_FINDING_CLOSURE_REEXECUTED" in codes(rows)


@pytest.mark.parametrize("field,value", [("checks", "PASS"), ("dependency_refs", "wrong"), ("finding_refs", "none")])
def test_malformed_report_collections_are_known_fail_without_exception(field, value):
    import json
    b, u, r, acceptance, reports = facts()
    first, _ = reseal(r, json.loads(r.data[reports[0]]), **{field: value})
    refs = (first,) + reports[1:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, revised, refs)
    assert "REPORT_COLLECTION_SCHEMA_INVALID" in codes(rows)


def test_unrelated_passing_check_cannot_close_a_material_finding():
    import json
    b, u, r, acceptance, reports = facts()
    finding, _ = store(r, {"model_only": True, "subject_ref": b.subject.to_dict(), "blocking": True, "state": "OPEN", "check_id": "future-information"}, "SyntheticFinding", "model:finding:unrelated")
    evidence, _ = store(r, {"model_only": True, "subject_ref": b.subject.to_dict(), "root_ref": b.root_ref.to_dict(), "check_id": "root-project", "expected_status": "PASS"}, "SyntheticClosureEvidence", "model:closure:unrelated-evidence")
    closure, _ = store(r, {"model_only": True, "subject_ref": b.subject.to_dict(), "finding_ref": finding.to_dict(), "evidence_refs": [evidence.to_dict()]}, "SyntheticFindingClosure", "model:closure:unrelated")
    first, _ = reseal(r, json.loads(r.data[reports[0]]), finding_refs=[finding.to_dict()], finding_closure_refs=[closure.to_dict()])
    refs = (first,) + reports[1:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, revised, refs)
    assert "FINDING_CLOSURE_CHECK_MISMATCH" in codes(rows)
    assert all(row.normalized == "FAIL" for row in rows if row.key.predicate_id == "P22")


@pytest.mark.parametrize("edge,reason,status", [
    ({"irrelevant": "field"}, "REPORT_DEPENDENCY_REFERENCE_INVALID", "FAIL"),
    ({"object_id": 1, "content_sha256": "a" * 64}, "REPORT_DEPENDENCY_REFERENCE_INVALID", "FAIL"),
    (ExactRef("model:unavailable", "a" * 64).to_dict(), "NO_AUTHORITATIVE_RESULT", "UNKNOWN"),
])
def test_every_report_dependency_edge_is_typed_and_resolved(edge, reason, status):
    import json
    b, u, r, acceptance, reports = facts()
    first, _ = reseal(r, json.loads(r.data[reports[0]]), dependency_refs=[b.rule_ref.to_dict(), edge])
    refs = (first,) + reports[1:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, revised, refs)
    assert reason in codes(rows)
    assert all(row.normalized == status for row in rows if row.key.predicate_id == "P16")


def test_absent_finding_collection_does_not_prove_empty_union():
    import json
    b, u, r, acceptance, reports = facts()
    report = json.loads(r.data[reports[0]])
    del report["finding_refs"]
    first, _ = reseal(r, report)
    refs = (first,) + reports[1:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, revised, refs)
    assert "COMPLETE_FINDING_INPUTS_NOT_ESTABLISHED" in codes(rows)
    assert all(row.normalized == "UNKNOWN" for row in rows if row.key.predicate_id == "P22")


@pytest.mark.parametrize("field", ["closure_ref", "evidence_refs"])
def test_malformed_finding_closure_edges_fail_without_exception(field):
    import json
    b, u, r, acceptance, reports = facts()
    closure, _ = store(r, {"model_only": True, "subject_ref": b.subject.to_dict(), "finding_ref": ExactRef("model:finding:malformed", "a" * 64).to_dict(), "evidence_refs": [{"bad": "ref"}]}, "SyntheticFindingClosure", "model:closure:malformed")
    finding, _ = store(r, {"model_only": True, "subject_ref": b.subject.to_dict(), "blocking": True, "state": "CLOSED", "closure_ref": {"bad": "ref"} if field == "closure_ref" else closure.to_dict()}, "SyntheticFinding", "model:finding:malformed")
    first, _ = reseal(r, json.loads(r.data[reports[0]]), finding_refs=[finding.to_dict()])
    refs = (first,) + reports[1:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, revised, refs)
    assert "MALFORMED_CLOSURE_REFERENCE" in codes(rows) or "MALFORMED_CLOSURE_EVIDENCE_REFERENCE" in codes(rows)
    assert all(row.normalized == "FAIL" for row in rows if row.key.predicate_id == "P22")


def test_missing_fixed_root_remains_unknown_at_component_boundary():
    b, u, r, acceptance, reports = facts()
    del r.data[b.root_ref]
    u = reconstruct_requirements(b, r)
    rows = replay(b, u, r, acceptance, reports)
    assert all(row.normalized == "UNKNOWN" for row in rows if row.key.predicate_id == "P02")


def test_report_dependency_transitive_acceptance_cycle_is_rejected():
    import json
    b, u, r, acceptance, reports = facts()
    intermediate, _ = store(r, {"schema_version": "MODEL_REPORT_V1", "model_only": True, "dependency_refs": [acceptance.to_dict()]}, "SyntheticReplayReport", "model:report:intermediate")
    first, _ = reseal(r, json.loads(r.data[reports[0]]), dependency_refs=[b.rule_ref.to_dict(), intermediate.to_dict()])
    refs = (first,) + reports[1:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, revised, refs)
    assert "PRE_SIGNING_ACCEPTANCE_OR_FINAL_REPORT_CYCLE" in codes(rows)
    assert all(row.normalized == "FAIL" for row in rows if row.key.predicate_id == "P16")


def test_absent_acceptance_does_not_prove_empty_finding_union():
    b, u, r, acceptance, reports = facts()
    del r.data[acceptance]
    rows = replay(b, u, r, acceptance, reports)
    assert all(row.normalized == "UNKNOWN" for row in rows if row.key.predicate_id == "P22")
    assert "COMPLETE_FINDING_INPUTS_NOT_ESTABLISHED" in codes(rows)


def test_missing_collection_cannot_discard_known_raw_failure():
    import json
    b, u, r, acceptance, reports = facts()
    report = json.loads(r.data[reports[0]])
    del report["finding_refs"]
    report["checks"][0]["status"] = "FAIL"
    report["status"] = "FAIL"
    first, _ = reseal(r, report)
    refs = (first,) + reports[1:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, revised, refs)
    assert "REPORT_RAW_BLOCKING_CHECK" in codes(rows)
    assert all(row.normalized == "FAIL" for row in rows if row.key.predicate_id == "P16")
    assert all(row.normalized == "UNKNOWN" for row in rows if row.key.predicate_id == "P22")


@pytest.mark.parametrize("stage,blocker", [("POST_SIGNING", False), ("PRE_SIGNING", True)])
def test_extra_report_dependency_cannot_bypass_fixed_roles_or_hide_blocker(stage, blocker):
    import json
    b, u, r, acceptance, reports = facts()
    finding, _ = store(r, {"model_only": True, "subject_ref": b.subject.to_dict(), "blocking": True, "state": "OPEN"}, "SyntheticFinding", "model:finding:nested")
    nested, _ = store(r, {"schema_version": "MODEL_REPORT_V1", "model_only": True,
                         "kind": "runtime", "stage": stage, "subject_ref": b.subject.to_dict(),
                         "validator_ref": b.profile[0].to_dict(), "dependency_refs": [],
                         "checks": [{"check_id": "nested-check", "status": "FAIL" if blocker else "PASS", "reason_code": "NESTED"}],
                         "status": "FAIL" if blocker else "PASS", "finding_refs": [finding.to_dict()] if blocker else []},
                        "SyntheticReplayReport", "model:dependency:opaque")
    first, _ = reseal(r, json.loads(r.data[reports[0]]), dependency_refs=[b.rule_ref.to_dict(), nested.to_dict()])
    refs = (first,) + reports[1:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, revised, refs)
    assert "REPORT_DEPENDENCY_ROLE_NOT_PERMITTED" in codes(rows)
    assert all(row.normalized == "FAIL" for row in rows if row.key.predicate_id == "P16")
    if blocker:
        assert "REPORT_RAW_BLOCKING_CHECK" in codes(rows)
        assert all(row.normalized == "FAIL" and finding in row.finding_refs for row in rows if row.key.predicate_id == "P22")


def test_declared_report_failure_is_retained_when_raw_checks_are_unavailable():
    import json
    b, u, r, acceptance, reports = facts()
    report = json.loads(r.data[reports[0]])
    del report["checks"]
    report["status"] = "FAIL"
    first, _ = reseal(r, report)
    refs = (first,) + reports[1:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, revised, refs)
    assert "REPORT_DECLARED_BLOCKER" in codes(rows)
    assert all(row.normalized == "FAIL" for row in rows if row.key.predicate_id == "P16")


def test_malformed_finding_state_is_schema_failure_without_exception():
    import json
    b, u, r, acceptance, reports = facts()
    finding, _ = store(r, {"model_only": True, "subject_ref": b.subject.to_dict(), "blocking": True, "state": []}, "SyntheticFinding", "model:finding:invalid-state")
    first, _ = reseal(r, json.loads(r.data[reports[0]]), finding_refs=[finding.to_dict()])
    refs = (first,) + reports[1:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, revised, refs)
    assert "FINDING_SCHEMA_INVALID" in codes(rows)
    assert all(row.normalized == "FAIL" for row in rows if row.key.predicate_id == "P22")


@pytest.mark.parametrize("role_index", range(5))
def test_absent_whole_required_report_does_not_prove_complete_empty_findings(role_index):
    import json
    b, u, r, acceptance, reports = facts()
    remaining = reports[:role_index] + reports[role_index + 1:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in remaining])
    rows = replay(b, u, r, revised, remaining)
    assert all(row.normalized == "FAIL" for row in rows if row.key.predicate_id == "P16")
    assert all(row.normalized == "UNKNOWN" for row in rows if row.key.predicate_id == "P22")
    assert "COMPLETE_FINDING_INPUTS_NOT_ESTABLISHED" in codes(rows)


@pytest.mark.parametrize("mutation", ["subject", "validator", "stage", "kind"])
def test_unbound_report_cannot_supply_complete_applicable_findings(mutation):
    import json
    b, u, r, acceptance, reports = facts()
    values = {"subject": ExactRef("model:wrong-subject", "a" * 64).to_dict(),
              "validator": ExactRef("model:wrong-validator", "a" * 64).to_dict(),
              "stage": "POST_SIGNING", "kind": "wrong-role"}
    fields = {"subject": "subject_ref", "validator": "validator_ref", "stage": "stage", "kind": "kind"}
    first, _ = reseal(r, json.loads(r.data[reports[0]]), **{fields[mutation]: values[mutation]})
    refs = (first,) + reports[1:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in refs])
    rows = replay(b, u, r, revised, refs)
    assert all(row.normalized == "FAIL" for row in rows if row.key.predicate_id == "P16")
    assert all(row.normalized == "UNKNOWN" for row in rows if row.key.predicate_id == "P22")


@pytest.mark.parametrize("source", ["rule", "scope"])
def test_unavailable_fixed_trust_source_is_unknown_not_a_violation(source):
    b, u, r, acceptance, reports = facts()
    ref = b.rule_ref if source == "rule" else b.scope_ref
    del r.data[ref]
    missing = reconstruct_requirements(b, r)
    assert missing.overall == "UNKNOWN"
    # A missing scope cannot establish M at all; test raw component behavior
    # separately with the previously independently established universe.
    rows = replay(b, u, r, acceptance, reports)
    assert all(row.normalized == "UNKNOWN" for row in rows if row.key.predicate_id == "P02")
    assert "NO_AUTHORITATIVE_RESULT" in codes(rows)


def test_missing_whole_report_preserves_discovered_finding_failure():
    import json
    b, u, r, acceptance, reports = facts()
    finding, _ = store(r, {"model_only": True, "subject_ref": b.subject.to_dict(), "blocking": True, "state": "OPEN"}, "SyntheticFinding", "model:finding:remaining")
    changed, _ = reseal(r, json.loads(r.data[reports[1]]), finding_refs=[finding.to_dict()])
    remaining = (changed,) + reports[2:]
    revised, _ = reseal(r, json.loads(r.data[acceptance]), required_validation_report_refs=[x.to_dict() for x in remaining])
    rows = replay(b, u, r, revised, remaining)
    assert all(row.normalized == "FAIL" and finding in row.finding_refs for row in rows if row.key.predicate_id == "P22")
    assert "COMPLETE_FINDING_INPUTS_NOT_ESTABLISHED" in codes(rows)
