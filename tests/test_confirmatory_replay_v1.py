"""M1 C01 executable model capability; real authority guard remains protected."""
import importlib
import importlib.util
import json
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest
from forecast_trust_core.authority_primitives_v1 import ExactRef
from forecast_trust_core.canonical import canonical_json
from test_qualification_scope_v1 import fixture as qualified_fixture

CORPUS = Path(__file__).parent / "fixtures/independent_replay_v1"


def api():
    assert importlib.util.find_spec("forecast_trust_core.confirmatory_replay_v1"), "T06 complete scientific replay missing"
    return importlib.import_module("forecast_trust_core.confirmatory_replay_v1")


def fixture():
    mod = api()
    _, b, r, requirements, cycles, qualifications = qualified_fixture()
    for path in (CORPUS / "scientific").rglob("*.json"):
        obj = json.loads(path.read_bytes())
        if "object_id" in obj and "content_sha256" in obj:
            r.data[ExactRef(obj["object_id"], obj["content_sha256"])] = path.read_bytes()
    for path in (CORPUS / "scientific").rglob("*.raw"):
        raw = path.read_bytes(); r.data[ExactRef("model:raw:" + path.stem, sha256(raw).hexdigest())] = raw
    result = mod.replay_confirmatory_checks(b, cycles, qualifications, r)
    return mod, b, r, requirements, cycles, qualifications, result


def codes(result): return {c.reason_code for c in result.checks}


def test_all_nt_conjuncts_execute_for_three_slots_with_actual_method_and_scores():
    _, _, _, _, _, _, result = fixture()
    assert result.overall == "PASS", codes(result)
    assert len(result.slot_results) == len(result.executions) == 3
    assert [x.prediction for x in result.executions] == ["100.25", "200.25", "300.25"]
    assert result.scored_squared_errors == ("0.5625", "0.5625", "0.5625")
    for slot in result.slot_results:
        assert {c.check_id.split("_")[0] for c in slot.checks if c.check_id.startswith("NT")} == {f"NT0{n}" for n in range(1, 9)}
        assert all(c.status == "PASS" for c in slot.checks)
    assert result.records and all(r.raw_result for r in result.records)
    assert result.model_only and not result.prospective_eligible
    assert result.real_genesis_readiness == "NOT_ESTABLISHED"
    assert result.protocol_state_change == "NONE"

@pytest.mark.parametrize("target", ["t1", "t2", "t3"])
def test_missing_entire_scientific_slot_never_shrinks_denominator(target):
    mod, b, r, _, cycles, qualifications, result = fixture()
    row = next(x for x in result.slot_results if x.target_name == target)
    for reference in row.input_refs.values(): r.data.pop(reference, None)
    changed = mod.replay_confirmatory_checks(b, cycles, qualifications, r)
    assert len(changed.slot_results) == 3
    assert changed.overall == "UNKNOWN"
    assert not any(x.prediction for x in changed.executions if x.target_name == target)

@pytest.mark.parametrize("kind", ["snapshot", "run", "attempt_ledger", "resolution_selection", "cohort"])
def test_mandatory_scientific_input_unavailable_is_unknown(kind):
    mod, b, r, _, cycles, qualifications, result = fixture()
    reference = result.slot_results[0].input_refs[kind]
    r.data.pop(reference)
    changed = mod.replay_confirmatory_checks(b, cycles, qualifications, r)
    assert changed.overall == "UNKNOWN", codes(changed)

@pytest.mark.parametrize("field,value", [("configuration", {"selection": "BEST_OUTCOME"}), ("runtime", {"python": "wrong"}),
    ("prediction", "999"), ("origin", "LIVE_OPERATIONAL"), ("information_cutoff", "2031-01-01T00:00:00Z")])
def test_known_run_substitution_fails_without_claiming_replay_verified(field, value):
    mod, b, r, _, cycles, qualifications, result = fixture()
    reference = result.slot_results[0].input_refs["run"]
    raw = json.loads(r.data[reference]); raw[field] = value; raw["reported_replay_verified"] = True
    r.data[reference] = canonical_json(raw)
    changed = mod.replay_confirmatory_checks(b, cycles, qualifications, r)
    assert changed.overall == "FAIL", codes(changed)


def test_qualification_admission_is_consumed_in_scientific_context():
    mod, b, r, _, cycles, qualifications, _ = fixture()
    old = next(a for a in qualifications.admissions if a.provider == "p3" and a.boundary_ref == next(x.ref for x in qualifications.boundaries if x.role == "cycle-t1"))
    bad = replace(old, admitted=False, status="FAIL", reason_codes=("VALIDATION_STATUS_NOT_VALID",))
    qualifications = replace(qualifications, admissions=tuple(bad if a == old else a for a in qualifications.admissions))
    changed = mod.replay_confirmatory_checks(b, cycles, qualifications, r)
    assert changed.overall == "FAIL"
    assert "QUALIFICATION_ADMISSION_NOT_CONSUMABLE" in codes(changed)


def test_real_mode_never_borrows_complete_model_scientific_pass():
    mod, b, r, _, cycles, qualifications, _ = fixture()
    result = mod.replay_confirmatory_checks(replace(b, mode="PUBLIC_EVIDENCE"), cycles, qualifications, r)
    assert result.overall == "UNKNOWN" and not result.prospective_eligible
    assert not result.executions



def reseal(obj):
    from forecast_trust_core.canonical import seal_object
    return seal_object({k:v for k,v in obj.items() if k not in {"object_id","content_sha256","payload_sha256"}},
        object_type=obj["object_type"], stable_context="M1_DEVELOPMENT_ONLY", semantic_id=obj["object_id"])


def semantic_inputs():
    result = fixture()[-1]
    row=result.slot_results[0]
    return deepcopy(row.raw_inputs),deepcopy(row.independent_context),api().observed_runtime()


def raw_change(inputs, name, field, value):
    capture=inputs["objects"][name]; key=capture["raw_ref"]["object_id"]
    obj=json.loads(inputs["raw"][key]); obj[field]=value
    raw=canonical_json(obj); inputs["raw"][key]=raw
    capture["raw_ref"]["content_sha256"]=sha256(raw).hexdigest()
    if field in capture: capture[field]=value
    inputs["objects"][name]=reseal(capture)


@pytest.mark.parametrize("change,check", [
    ("future_information","NT02_input_availability"),
    ("missing_raw_member","NT02_snapshot_recursive_bytes"),
    ("nested_snapshot_omission","NT02_snapshot_recursive_bytes"),
    ("first_release_vintage","NT02_source_vintage"),
    ("retry_cherry_pick","NT04_first_success_output"),
    ("unit","NT06_type_unit_decimal"),
    ("noncanonical_decimal","NT06_type_unit_decimal"),
    ("origin_upgrade","NT06_origin_preservation"),
    ("resolution_conflict","NT07_conflict_ambiguity"),
    ("cohort_denominator","NT08_denominator"),
    ("configuration","NT03_method_configuration"),
    ("runtime","NT03_environment_identity"),
    ("prediction","NT03_deterministic_reexecution"),
    ("historical_manifest","NT01_historical_bindings"),
    ("wrong_resolution_policy","NT01_policy_compatibility"),
    ("attempt_gap","NT04_attempt_succession"),
    ("failure_terminal","NT04_failure_retry_budget"),
    ("selection_after_plan","NT05_precommitted_selection"),
    ("control_class","NT05_control_class"),
    ("cutoff","NT06_cutoff_horizon_bindings"),
    ("resolution_vintage","NT07_first_release_resolution"),
    ("erase_original","NT07_correction_withdrawal"),
    ("wrong_score","NT08_cohort_scoring"),
])
def test_causal_raw_semantics_each_conjunct_without_source_hash_gate(change,check):
    from forecast_trust_core.scientific_model_engine_v1 import evaluate_scientific_slot
    inputs, context, runtime = semantic_inputs(); o=inputs["objects"]
    if change=="future_information": raw_change(inputs,"baseline","available_at","2031-01-01T00:00:00Z")
    elif change=="missing_raw_member": del inputs["raw"][o["older"]["raw_ref"]["object_id"]]
    elif change=="nested_snapshot_omission":
        o["nested"]["members"]=o["nested"]["members"][1:]; o["nested"]=reseal(o["nested"])
        o["snapshot"]["members"]=[{k:o["nested"][k] for k in ("object_id","content_sha256")}]; o["snapshot"]=reseal(o["snapshot"])
    elif change=="first_release_vintage": raw_change(inputs,"baseline","release_stage","REVISED")
    elif change=="retry_cherry_pick": o["attempt_ledger"]["selected_attempt_ref"]=context["issued_ref"]
    elif change=="unit": o["run"]["unit"]="other-unit"
    elif change=="noncanonical_decimal": o["run"]["prediction"]="100.250"
    elif change=="origin_upgrade": o["run"]["origin"]="LIVE_OPERATIONAL"
    elif change=="resolution_conflict": o["resolution_selection"]["ambiguous"]=True
    elif change=="cohort_denominator": o["cohort"]["included_forecast_refs"]=o["cohort"]["included_forecast_refs"][:2]
    elif change=="configuration": o["run"]["configuration"]["selection"]="BEST_OUTCOME"
    elif change=="runtime": o["run"]["runtime"]["python"]="wrong"
    elif change=="prediction": o["run"]["prediction"]="999"
    elif change=="historical_manifest": o["run"]["subject_ref"]=context["method_ref"]
    elif change=="wrong_resolution_policy": context["resolution_policy"]["vintage"]="LATEST"
    elif change=="attempt_gap": o["execution-0"]["sequence"]=1
    elif change=="failure_terminal": o["execution-0"]["status"]="FAILED"
    elif change=="selection_after_plan": o["selection"]["committed_at"]="2030-02-13T00:00:00Z"
    elif change=="control_class": o["run"]["control_class"]="UNCONTROLLED_NONDETERMINISM"
    elif change=="cutoff": o["run"]["information_cutoff"]="2031-01-01T00:00:00Z"
    elif change=="resolution_vintage": o["resolution_selection"]["selected_vintage"]="LATEST"
    elif change=="erase_original": o["cohort"]["included_forecast_refs"]=[]
    elif change=="wrong_score": o["cohort"]["scores"]["t1"]="0"
    checks, _=evaluate_scientific_slot(inputs,context,runtime)
    assert next(c for c in checks if c.check_id==check).status==("UNKNOWN" if change=="missing_raw_member" else "FAIL"), checks
    assert len(checks)==21


def test_run_boolean_never_substitutes_actual_execution():
    from forecast_trust_core.scientific_model_engine_v1 import evaluate_scientific_slot
    inputs,context,runtime=semantic_inputs()
    inputs["objects"]["run"]["reported_replay_verified"]=True
    inputs["objects"]["run"]["prediction"]="999"
    checks,execution=evaluate_scientific_slot(inputs,context,runtime)
    assert execution.prediction=="100.25"
    assert next(c for c in checks if c.check_id=="NT03_deterministic_reexecution").status=="FAIL"


@pytest.mark.parametrize("kind",["run","snapshot","attempt_ledger","resolution_selection","cohort","selection","older","baseline","outcome","execution-0"])
def test_missing_semantic_class_never_collapses_remaining_nt_vector(kind):
    from forecast_trust_core.scientific_model_engine_v1 import evaluate_scientific_slot
    inputs,context,runtime=semantic_inputs(); del inputs["objects"][kind]
    checks,_=evaluate_scientific_slot(inputs,context,runtime)
    assert len(checks)==21 and any(c.status=="UNKNOWN" for c in checks)
    assert api().reduce_checks(checks)=="UNKNOWN"


def retry_inputs():
    """Independently construct a finite FAILED -> first SUCCESS ledger."""
    inputs,context,runtime=semantic_inputs(); o=inputs['objects']; a=deepcopy(o['execution-0'])
    a.update(status='FAILED',failure_code='TRANSIENT',output_ref='NONE',issuance_eligible=False)
    a=reseal(a); b=deepcopy(o['execution-0']); b.update(object_id='model:scientific:t1-execution-1',sequence=1,
        predecessor_ref={k:a[k] for k in ('object_id','content_sha256')},started_at='2030-02-13T14:00:02Z',finished_at='2030-02-13T14:00:03Z')
    b=reseal(b); o['execution-0']=a; o['execution-1']=b
    pairs=[{k:x[k] for k in ('object_id','content_sha256')} for x in (a,b)]
    context.update(attempt_refs=pairs,attempt_names=['execution-0','execution-1'])
    o['attempt_ledger'].update(attempt_refs=pairs,head_ref=pairs[1],selected_attempt_ref=pairs[1]);o['run']['attempt_ref']=pairs[1]
    return inputs,context,runtime


def test_native_retry_kernel_and_first_success_actually_execute():
    from forecast_trust_core.scientific_model_engine_v1 import evaluate_scientific_slot
    inputs,context,runtime=retry_inputs(); checks,_=evaluate_scientific_slot(inputs,context,runtime)
    assert all(c.status=='PASS' for c in checks if c.check_id.startswith('NT04')),checks

@pytest.mark.parametrize('change,check',[('non_immediate_predecessor','NT04_attempt_succession'),('terminal_missing','NT04_attempt_succession'),
    ('late_finish','NT04_attempt_succession'),('unapproved_failure','NT04_failure_retry_budget'),('budget_exceeded','NT04_failure_retry_budget'),
    ('select_failure','NT04_first_success_output'),('ledger_truncation','NT04_attempt_succession')])
def test_actual_retry_chain_adversaries(change,check):
    from forecast_trust_core.scientific_model_engine_v1 import evaluate_scientific_slot
    inputs,context,runtime=retry_inputs(); o=inputs['objects']
    if change=='non_immediate_predecessor': o['execution-1']['predecessor_ref']=context['issued_ref']
    elif change=='terminal_missing': o['execution-1']['status']='RUNNING'
    elif change=='late_finish': o['execution-1']['finished_at']='2030-02-15T00:00:00Z'
    elif change=='unapproved_failure': o['execution-0']['failure_code']='INVALID_INPUT'
    elif change=='budget_exceeded': context['method']['retry']['budget']=1
    elif change=='select_failure': o['attempt_ledger']['selected_attempt_ref']=context['attempt_refs'][0]
    elif change=='ledger_truncation': o['attempt_ledger']['attempt_refs']=context['attempt_refs'][1:]
    checks,_=evaluate_scientific_slot(inputs,context,runtime)
    assert next(c for c in checks if c.check_id==check).status=='FAIL',checks


def test_later_success_output_cannot_replace_first_success():
    from forecast_trust_core.scientific_model_engine_v1 import evaluate_scientific_slot
    inputs,context,runtime=retry_inputs(); o=inputs['objects']
    o['execution-0'].update(status='SUCCESS',failure_code='NONE',output_ref=context['issued_ref'],issuance_eligible=True)
    o['execution-0']=reseal(o['execution-0']); pair={k:o['execution-0'][k] for k in ('object_id','content_sha256')}
    o['execution-1']['predecessor_ref']=pair;o['execution-1']=reseal(o['execution-1']); second={k:o['execution-1'][k] for k in ('object_id','content_sha256')}
    context['attempt_refs']=[pair,second]; o['attempt_ledger'].update(attempt_refs=[pair,second],head_ref=second,selected_attempt_ref=second)
    o['run']['attempt_ref']=second
    checks,_=evaluate_scientific_slot(inputs,context,runtime)
    assert next(c for c in checks if c.check_id=='NT04_first_success_output').status=='FAIL'


def test_missing_runtime_identity_is_unknown_with_no_fake_replay():
    from forecast_trust_core.scientific_model_engine_v1 import evaluate_scientific_slot
    inputs,context,_=semantic_inputs(); checks,execution=evaluate_scientific_slot(inputs,context,None)
    assert next(c for c in checks if c.check_id=='NT03_environment_identity').status=='UNKNOWN'
    assert api().reduce_checks(checks)=='UNKNOWN' and execution.prediction is None


def test_unavailable_runtime_does_not_erase_known_unit_failure():
    from forecast_trust_core.scientific_model_engine_v1 import evaluate_scientific_slot
    inputs,context,_=semantic_inputs(); inputs['objects']['run']['unit']='wrong'
    checks,_=evaluate_scientific_slot(inputs,context,None)
    assert api().reduce_checks(checks)=='FAIL'


def test_model_wrapper_records_runtime_error_as_unknown(monkeypatch):
    mod,b,r,_,cycles,qualifications,_=fixture()
    def unavailable(): raise OSError('model test failure')
    monkeypatch.setattr(mod,'observed_runtime',unavailable)
    result=mod.replay_confirmatory_checks(b,cycles,qualifications,r)
    assert result.overall=='UNKNOWN',codes(result)
    assert 'SCIENTIFIC_RUNTIME_UNAVAILABLE_OSError' in codes(result)
    assert not any(x.prediction for x in result.executions)


def lifecycle_inputs(kind):
    from forecast_trust_core.canonical import seal_object
    inputs,context,runtime=semantic_inputs(); o=inputs['objects']
    def event(type_,name,**kwargs):
        return seal_object({'model_only':True,'origin':'SYNTHETIC_ONLY',**kwargs},object_type=type_,stable_context='M1_TEST',semantic_id='model:test:'+name)
    if kind=='withdrawal':
        obj=event('SyntheticForecastWithdrawal','withdrawal',forecast_ref=context['issued_ref'],action='WITHDRAW',withdrawn_at='2030-02-15T00:00:00Z')
        context['withdrawal_names']=['withdrawal'];context['withdrawal_refs']=[{k:obj[k] for k in ('object_id','content_sha256')}]
        o['resolution_selection']['withdrawal_refs']=context['withdrawal_refs'];o['withdrawal']=obj
    else:
        replacement=event('SyntheticIssuedForecast','replacement',slot_ref=context['slot_ref'],method_ref=context['method_ref'],value='999',unit='model-index',issued_at='2030-02-14T13:00:00Z')
        pair={k:replacement[k] for k in ('object_id','content_sha256')};o['replacement']=replacement
        obj=event('SyntheticForecastCorrection','correction',original_forecast_ref=context['issued_ref'],affected_fields=['value'],correction_type='SUBSTANTIVE_REPLACEMENT',replacement_forecast_ref_or_none=pair,action='PRESERVE_ORIGINAL')
        context['correction_names']=['correction'];context['correction_refs']=[{k:obj[k] for k in ('object_id','content_sha256')}]
        context['replacement_names']=['replacement'];o['resolution_selection']['correction_refs']=context['correction_refs'];o['correction']=obj
    return inputs,context,runtime


@pytest.mark.parametrize('kind',['withdrawal','correction'])
def test_lifecycle_event_keeps_original_denominator_and_original_score(kind):
    from forecast_trust_core.scientific_model_engine_v1 import evaluate_scientific_slot
    inputs,context,runtime=lifecycle_inputs(kind); checks,execution=evaluate_scientific_slot(inputs,context,runtime)
    assert all(c.status=='PASS' for c in checks if c.check_id.startswith(('NT07','NT08'))),checks
    assert execution.squared_error=='0.5625'


@pytest.mark.parametrize('kind,change',[('withdrawal','erase_action'),('withdrawal','missing_event'),('withdrawal','wrong_subject'),
    ('correction','missing_event'),('correction','wrong_replacement_origin'),('correction','replacement_unavailable')])
def test_lifecycle_mandatory_event_cannot_be_erased_or_upgrade_origin(kind,change):
    from forecast_trust_core.scientific_model_engine_v1 import evaluate_scientific_slot
    inputs,context,runtime=lifecycle_inputs(kind); o=inputs['objects']
    if change=='erase_action': o[kind]['action']='DELETE_ORIGINAL'
    elif change=='missing_event': del o[kind]
    elif change=='wrong_subject': o[kind]['forecast_ref']=context['method_ref']
    elif change=='wrong_replacement_origin': o['replacement']['origin']='LIVE_OPERATIONAL'
    elif change=='replacement_unavailable': del o['replacement']
    checks,_=evaluate_scientific_slot(inputs,context,runtime)
    assert next(c for c in checks if c.check_id=='NT07_correction_withdrawal').status==('UNKNOWN' if change in ('missing_event','replacement_unavailable') else 'FAIL'),checks

@pytest.mark.parametrize('failure',['exception','none','empty'])
def test_raw_formatter_unavailable_is_not_model_pass(monkeypatch,failure):
    mod,b,r,_,cycles,qualifications,_=fixture()
    def unavailable(*args,**kwargs):
        if failure=='exception': raise OSError('model raw output unavailable')
        return None if failure=='none' else ()
    monkeypatch.setattr(mod,'emit_records',unavailable)
    result=mod.replay_confirmatory_checks(b,cycles,qualifications,r)
    assert result.overall=='UNKNOWN'
    assert not result.records


def test_scientific_engine_unavailable_retains_known_byte_failure(monkeypatch):
    mod,b,r,_,cycles,qualifications,result=fixture()
    pair=result.slot_results[0].input_refs['run']; r.data[pair]=b'{}'
    def unavailable(*args): raise RuntimeError('model engine unavailable')
    monkeypatch.setattr(mod.engine,'evaluate_scientific_slot',unavailable)
    changed=mod.replay_confirmatory_checks(b,cycles,qualifications,r)
    assert changed.overall=='FAIL' and not changed.executions
    assert 'SCIENTIFIC_EXECUTION_UNAVAILABLE_RuntimeError' in codes(changed)


# Independent review causal counterexamples; temporal guard test is regression only.
from forecast_trust_core.scientific_model_engine_v1 import evaluate_scientific_slot, ref

def coherent_timing_inputs(*,finished=None,issued=None):
    inputs,context,runtime=semantic_inputs(); o=inputs['objects']
    if issued is not None:
        old=context['issued_ref'];o['issued']['issued_at']=issued;o['issued']=reseal(o['issued']);context['issued_ref']=ref(o['issued'])
        o['execution-0']['output_ref']=context['issued_ref']
        o['resolution']['issued_forecast_ref']=context['issued_ref'];o['resolution']=reseal(o['resolution'])
        for key in ('included_forecast_refs','scored_forecast_refs'):
            o['cohort'][key]=[context['issued_ref'] if x==old else x for x in o['cohort'][key]]
        context['all_issued_refs']=[context['issued_ref'] if x==old else x for x in context['all_issued_refs']]
        o['cohort']=reseal(o['cohort'])
    if finished is not None: o['execution-0']['finished_at']=finished
    o['execution-0']=reseal(o['execution-0']);pair=ref(o['execution-0'])
    context['attempt_refs']=[pair];o['attempt_ledger'].update(attempt_refs=[pair],head_ref=pair,selected_attempt_ref=pair);o['attempt_ledger']=reseal(o['attempt_ledger'])
    o['run'].update(attempt_ref=pair,attempt_ledger_ref=ref(o['attempt_ledger']));o['run']=reseal(o['run'])
    return inputs,context,runtime


@pytest.mark.parametrize('finish',['2030-02-14T13:00:01Z','2030-02-14T13:10:00Z'])
def test_review_first_success_must_finish_before_issuance(finish):
    inputs,context,runtime=coherent_timing_inputs(finished=finish)
    checks,_=evaluate_scientific_slot(inputs,context,runtime)
    assert next(c for c in checks if c.check_id=='NT04_first_success_output').status=='FAIL',checks


def test_review_first_success_finish_exactly_at_issuance_is_allowed():
    inputs,context,runtime=coherent_timing_inputs(finished='2030-02-14T13:00:00Z')
    checks,_=evaluate_scientific_slot(inputs,context,runtime)
    assert all(c.status=='PASS' for c in checks),checks


@pytest.mark.parametrize('issued',['2030-02-14T13:00:00+00:00','2030-02-14T13:00:00.000Z'])
def test_review_noncanonical_issued_at_cannot_pass_nt06(issued):
    inputs,context,runtime=coherent_timing_inputs(issued=issued)
    checks,_=evaluate_scientific_slot(inputs,context,runtime)
    assert next(c for c in checks if c.check_id=='NT06_cutoff_horizon_bindings').status=='FAIL',checks


def test_four_verified_temporal_conjunction_still_cannot_remove_real_c01_guard(monkeypatch):
    """Temporal conjunction boundary injection only; no positive raw evidence.

    The native strict claim aggregator actually runs. This regression does not
    simulate crypto/build/provenance inputs or claim full temporal recomputation.
    """
    import forecast_trust_core.claim_authority_v1 as authority
    from forecast_trust_core.canonical import seal_object
    forecast=seal_object({'model_only':True,'value':'100.25','origin':'SYNTHETIC_ONLY'},object_type='SyntheticIssuedForecast',stable_context='M1_GUARD_REGRESSION',semantic_id='model:guard-regression:forecast')
    pair=ref(forecast)
    types=('DEADLINE_EXISTENCE_VERIFIED','BITCOIN_DURABILITY_VERIFIED','PRE_OUTCOME_DURABILITY_VERIFIED','EXTERNAL_EXISTENCE_BOUND_VERIFIED')
    requirements=[{'claim_type':t,'subject_ref':pair} for t in types]
    temporal=[authority._legacy._claim(t,pair,'VERIFIED',reason_codes=('TEST_TEMPORAL_CONJUNCTION_BOUNDARY_SEAM',)) for t in types]
    actual_strict=authority._legacy.derive_confirmatory_eligibility_strict; observed=[]
    def temporal_boundary(subject_ref,**kwargs):
        assert kwargs['required_claim_requirements']==requirements
        result=actual_strict(subject_ref,required_claims=temporal,required_claim_requirements=requirements,hard_invalidation_reason_codes=(),applicable=True)
        observed.append(result['state']); return result
    monkeypatch.setattr(authority._legacy,'derive_confirmatory_eligibility_strict',temporal_boundary)
    result,claims=authority.derive_confirmatory_eligibility_from_evidence(forecast,component_specs=[],required_claim_requirements=requirements)
    assert observed==['VERIFIED'] and len(temporal)==4 and claims==()
    assert result['state']=='UNRESOLVED'
    assert result['reason_codes']==['FULL_TRUST_CORE_CHECK_AUTHORITY_NOT_IMPLEMENTED']


def test_review_offset_issuance_actually_after_execution_window_is_invalid():
    inputs,context,runtime=coherent_timing_inputs(issued='2030-02-14T13:00:00-10:00')
    checks,_=evaluate_scientific_slot(inputs,context,runtime)
    assert next(c for c in checks if c.check_id=='NT06_cutoff_horizon_bindings').status=='FAIL',checks
