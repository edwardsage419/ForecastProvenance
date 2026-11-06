"""Actual finite external replay arithmetic/bindings; crypto/chain seams explicit."""
import importlib
import importlib.util
from dataclasses import replace
from pathlib import Path
import json
from hashlib import sha256
from copy import deepcopy
import pytest
from forecast_trust_core.authority_primitives_v1 import ExactRef
from forecast_trust_core.canonical import canonical_json
from test_confirmatory_replay_v1 import fixture as scientific_fixture

CORPUS=Path(__file__).parent/'fixtures/independent_replay_v1'

def api():
    assert importlib.util.find_spec('forecast_trust_core.g10_external_evidence_v1'),'T07 external evidence replay missing'
    return importlib.import_module('forecast_trust_core.g10_external_evidence_v1')

def fixture():
    mod=api(); _,basis,resolver,requirements,cycles,qualifications,scientific=scientific_fixture()
    for path in (CORPUS/'evidence').rglob('*.json'):
        obj=json.loads(path.read_bytes())
        if 'object_id' in obj and 'content_sha256' in obj: resolver.data[ExactRef(obj['object_id'],obj['content_sha256'])]=path.read_bytes()
    for path in (CORPUS/'evidence').rglob('*.raw'):
        raw=path.read_bytes();resolver.data[ExactRef('model:external:raw:'+path.stem,sha256(raw).hexdigest())]=raw
    result=mod.replay_external_evidence(basis,cycles,qualifications,scientific,resolver)
    return mod,basis,resolver,requirements,cycles,qualifications,scientific,result

def reasons(r):return {c.reason_code for c in r.checks}

def test_retry_numeric_transition_consumes_explicit_attempt_offsets():
    from forecast_trust_core.external_model_engine_v1 import retry_transition
    before={'failures':0,'retry_not_before_ns':0}
    attempts=[{'outcome':'FAILED','duration_ns':2_000_000_000,'started_offset_ns':0},
              {'outcome':'FAILED','duration_ns':2_000_000_000,'started_offset_ns':3_000_000_000}]
    assert retry_transition(before,attempts,100)=={'failures':2,'retry_not_before_ns':6_500_000_100}

def test_verified_nonqualifying_response_resets_persistent_backoff():
    from forecast_trust_core.external_model_engine_v1 import retry_transition
    assert retry_transition({'failures':99,'retry_not_before_ns':0},
        [{'outcome':'VERIFIED_NONQUALIFYING_RESPONSE','duration_ns':1,'started_offset_ns':0}],0)=={'failures':0,'retry_not_before_ns':0}

def test_complete_ten_events_and_three_retrospective_sources_actually_replay():
    *_,result=fixture()
    assert result.overall=='PASS',reasons(result)
    assert len(result.events)==10 and len(result.measurements)==3
    assert all(e.overall=='PASS' for e in result.events)
    assert all(e.provider_order==('p1','p2','p3') for e in result.events)
    assert result.records and all(x.raw_result for x in result.records)
    assert result.model_only and not result.prospective_eligible
    assert result.real_genesis_readiness=='NOT_ESTABLISHED' and result.protocol_state_change=='NONE'
    assert result.seams and all(e.fresh_execution for e in result.events)

@pytest.mark.parametrize('event',['plan-t1','cycle-t1','dvr-t1','final-acceptance'])
def test_entire_event_missing_preserves_independent_event_universe(event):
    mod,b,r,_,cy,q,s,old=fixture();row=next(e for e in old.events if e.name==event)
    for ref in row.input_refs.values():r.data.pop(ref,None)
    new=mod.replay_external_evidence(b,cy,q,s,r)
    assert len(new.events)==10 and new.overall=='UNKNOWN',reasons(new)

@pytest.mark.parametrize('kind',['bundle','execution','retry_before','retry_after','proof','chain','authentication'])
def test_missing_mandatory_evidence_is_unknown_not_persisted_pass(kind):
    mod,b,r,_,cy,q,s,old=fixture();r.data.pop(old.events[0].input_refs[kind])
    new=mod.replay_external_evidence(b,cy,q,s,r)
    assert new.overall=='UNKNOWN',reasons(new)

@pytest.mark.parametrize('target',['t1','t2','t3'])
def test_measurement_fixture_missing_is_not_omitted_from_three_source_scope(target):
    mod,b,r,_,cy,q,s,old=fixture();row=next(x for x in old.measurements if x.target_name==target)
    for ref in row.input_refs:r.data.pop(ref,None)
    new=mod.replay_external_evidence(b,cy,q,s,r)
    assert len(new.measurements)==3 and new.overall=='UNKNOWN',reasons(new)


def test_actual_third_provider_admission_blocks_quorum_even_with_two_votes():
    mod,b,r,_,cy,q,s,_=fixture();boundary=next(x.ref for x in q.boundaries if x.role=='cycle-t1')
    original=next(x for x in q.admissions if x.provider=='p3' and x.boundary_ref==boundary)
    bad=replace(original,admitted=False,status='FAIL',reason_codes=('VALIDATION_STATUS_NOT_VALID',))
    q=replace(q,admissions=tuple(bad if x==original else x for x in q.admissions))
    new=mod.replay_external_evidence(b,cy,q,s,r)
    assert new.overall=='FAIL' and 'QUALIFICATION_ADMISSION_NOT_CONSUMABLE' in reasons(new)


def test_public_mode_never_consumes_model_crypto_or_chain_as_real_pass():
    mod,b,r,_,cy,q,s,_=fixture()
    new=mod.replay_external_evidence(replace(b,mode='PUBLIC_EVIDENCE'),cy,q,s,r)
    assert new.overall=='UNKNOWN' and not new.prospective_eligible
    assert not any(e.fresh_execution for e in new.events)

@pytest.mark.parametrize('change,check',[
    ('wrong_subject','wall_subject_nonce'),('wrong_nonce','wall_subject_nonce'),
    ('invalid_authentication','wall_signature_delegation'),('delegation_interval','wall_signature_delegation'),
    ('shared_control','wall_provider_independence'),('provider_omission','wall_quorum_transcript'),
    ('provider_reorder','wall_quorum_transcript'),('retry_omit','wall_quorum_transcript'),
    ('retry_request_change','wall_quorum_transcript'),('retry_after_verified','wall_quorum_transcript'),
    ('backoff_state_substitution','wall_quorum_transcript'),('timeout','wall_quorum_transcript'),
    ('protocol_fallback','wall_quorum_transcript'),('transcript_missing','wall_quorum_transcript'),
    ('radius_zero','wall_conservative_bound'),('averaged_bound','wall_conservative_bound'),
    ('late_bound','deadline_upper_bound'),('deadline_substitution','deadline_subject_frozen'),
    ('bundle_splice','bitcoin_subject_bundle'),('proof_missing','bitcoin_fresh_execution'),
    ('chain_missing','bitcoin_pin_chain'),('engine_pin','bitcoin_pin_chain'),
    ('persisted_only','bitcoin_fresh_execution'),('origin_upgrade','wall_subject_nonce'),
])
def test_causal_external_semantic_family_cannot_pass_with_coherent_observations(change,check):
    """Inputs are independently modified here; production supplies no counterexample factory."""
    from forecast_trust_core.external_model_engine_v1 import evaluate_external_event
    result=fixture()[-1];event=next(e for e in result.events if e.name=='cycle-t1')
    inputs=deepcopy(event.raw_inputs);context=deepcopy(event.independent_context);o=inputs['objects']
    if change=='wrong_subject': o['bundle']['subject_ref']=context['rule_ref']
    elif change=='wrong_nonce': o['execution']['providers'][0]['nonce_hex']='0'*64
    elif change=='invalid_authentication': o['authentication']['provider_facts'][0]['model_status']='INVALID'
    elif change=='delegation_interval': o['authentication']['provider_facts'][0]['delegation_until']='2000-01-01T00:00:00Z'
    elif change=='shared_control': context['provider_groups']['p2']=context['provider_groups']['p1']
    elif change=='provider_omission': o['execution']['providers']=o['execution']['providers'][:2]
    elif change=='provider_reorder': o['execution']['providers'].reverse()
    elif change=='retry_omit': o['execution']['providers'][2]['attempts']=[]
    elif change=='retry_request_change': o['execution']['providers'][2]['attempts'][1]['request_ref']=context['rule_ref']
    elif change=='retry_after_verified': o['execution']['providers'][0]['attempts'].append(deepcopy(o['execution']['providers'][0]['attempts'][0]))
    elif change=='backoff_state_substitution': o['retry_before']['providers']['p1']['failures']=99
    elif change=='timeout': o['execution']['providers'][2]['attempts'][0]['duration_ns']=3_000_000_000
    elif change=='protocol_fallback': o['execution']['providers'][0]['transport']='TCP'
    elif change=='transcript_missing': del o['execution']['transcript_sha256']
    elif change=='radius_zero': o['authentication']['provider_facts'][0]['radius_ns']=0
    elif change=='averaged_bound': o['bundle']['reported_upper_bound']='2030-02-14T13:28:59Z'
    elif change=='late_bound': o['bundle']['reported_upper_bound']='2030-02-19T13:30:01Z'
    elif change=='deadline_substitution': o['bundle']['frozen_cutoff']='2031-01-01T00:00:00Z'
    elif change=='bundle_splice': o['proof']['bundle_ref']=context['rule_ref']
    elif change=='proof_missing': o['proof']=None
    elif change=='chain_missing': o['chain']=None
    elif change=='engine_pin': context['runtime']['engine_sha256']='0'*64
    elif change=='persisted_only': o['proof']=None;o['report']['status']='PASS'
    elif change=='origin_upgrade': o['bundle']['origin']='LIVE_OPERATIONAL'
    checks,trace=evaluate_external_event(inputs,context)
    matching=next(c for c in checks if c.check_id==check)
    assert matching.status==('UNKNOWN' if change in {'proof_missing','chain_missing','persisted_only'} else 'FAIL'),checks


def test_external_environment_timeout_cannot_be_converted_to_model_pass(monkeypatch):
    mod,b,r,_,cy,q,s,_=fixture()
    def unavailable(*args,**kwargs):raise TimeoutError('model engine unavailable')
    monkeypatch.setattr(mod,'fresh_model_execution',unavailable)
    result=mod.replay_external_evidence(b,cy,q,s,r)
    assert result.overall=='UNKNOWN',reasons(result)
    assert 'MODEL_EXTERNAL_EXECUTION_UNAVAILABLE_TimeoutError' in reasons(result)


def test_known_external_hash_failure_survives_unavailable_engine(monkeypatch):
    mod,b,r,_,cy,q,s,old=fixture();r.data[old.events[0].input_refs['bundle']]=b'{}'
    def unavailable(*args,**kwargs):raise OSError('model engine unavailable')
    monkeypatch.setattr(mod,'fresh_model_execution',unavailable)
    result=mod.replay_external_evidence(b,cy,q,s,r)
    assert result.overall=='FAIL',reasons(result)

@pytest.mark.parametrize('change',['no_backoff_wait','missing_receipt_trace','nonqualifying_not_reset','duplicate_challenge','wrong_retry_root','missing_before_predecessor','contract_splice','DVR_subject_splice'])
def test_causal_coherent_transcript_still_enforces_complete_v3_contract(change):
    from forecast_trust_core.external_model_engine_v1 import evaluate_external_event
    event=next(e for e in fixture()[-1].events if e.name==('cycle-t3' if change=='nonqualifying_not_reset' else 'cycle-t1'))
    inputs=deepcopy(event.raw_inputs);ctx=deepcopy(event.independent_context);o=inputs['objects'];e=o['execution']
    if change=='no_backoff_wait':e['providers'][2]['attempts'][1]['started_offset_ns']=2_000_000_000
    elif change=='missing_receipt_trace':del e['providers'][0]['attempts'][0]['verification_trace']
    elif change=='nonqualifying_not_reset':o['retry_after']['providers']['p3']={'failures':2,'retry_not_before_ns':'0'}
    elif change=='duplicate_challenge':e['providers'][1]['public_challenge_hex']=e['providers'][0]['public_challenge_hex']
    elif change=='wrong_retry_root':o['retry_before']['root_ref']=ctx['rule_ref']
    elif change=='missing_before_predecessor':del o['retry_before']['predecessor_ref']
    elif change=='contract_splice':e['contract_ref']=ctx['rule_ref']
    elif change=='DVR_subject_splice':o['bundle']['authentication_ref']=ctx['rule_ref']
    core={k:v for k,v in e.items() if k not in {'object_id','object_type','payload_sha256','content_sha256','transcript_sha256'}}
    e['transcript_sha256']=sha256(canonical_json(core)).hexdigest()
    checks,_=evaluate_external_event(inputs,ctx)
    assert any(c.status=='FAIL' for c in checks),checks


def test_missing_formatter_output_preserves_unknown_instead_of_empty_pass(monkeypatch):
    mod,b,r,_,cy,q,s,_=fixture();monkeypatch.setattr(mod,'emit_records',lambda *a,**k:())
    result=mod.replay_external_evidence(b,cy,q,s,r)
    assert result.overall=='UNKNOWN' and not result.records


def test_final_governance_deadlines_have_exact_verified_exclusion():
    result=fixture()[-1]
    rows=[r for r in result.records if r.key.predicate_id=='P19' and r.key.role.endswith('#final-acceptance')]
    assert len(rows)==2 and all(r.normalized=='NOT_APPLICABLE' and r.exclusion_result=='PASS' and r.exclusion_fact_refs for r in rows)
    assert all(r.normalized=='PASS' for r in result.records if r.key.predicate_id=='P19' and not r.key.role.endswith('#final-acceptance'))

@pytest.mark.parametrize('change',['missing_hash','wrong_hash','extra_provider_fact'])
def test_each_receipt_verification_trace_has_actual_hash_and_exact_provider_scope(change):
    from forecast_trust_core.external_model_engine_v1 import evaluate_external_event
    event=next(e for e in fixture()[-1].events if e.name=='cycle-t1')
    inputs=deepcopy(event.raw_inputs);ctx=deepcopy(event.independent_context);e=inputs['objects']['execution']
    if change=='missing_hash':e['providers'][0]['attempts'][0].pop('verification_trace_sha256',None)
    elif change=='wrong_hash':e['providers'][0]['attempts'][0]['verification_trace_sha256']='0'*64
    else:
        f=deepcopy(inputs['objects']['authentication']['provider_facts'][0]);f['provider']='p4';inputs['objects']['authentication']['provider_facts'].append(f)
    core={k:v for k,v in e.items() if k not in {'object_id','object_type','payload_sha256','content_sha256','transcript_sha256'}}
    e['transcript_sha256']=sha256(canonical_json(core)).hexdigest()
    checks,_=evaluate_external_event(inputs,ctx)
    selected=next(c for c in checks if c.check_id==('wall_signature_delegation' if change=='extra_provider_fact' else 'wall_quorum_transcript'))
    assert selected.status=='FAIL',checks

@pytest.mark.parametrize('change,expected',[
    ('positive','PASS'),('missing_primary','UNKNOWN'),('missing_bundle','UNKNOWN'),('missing_proof','UNKNOWN'),('missing_report','UNKNOWN'),
    ('wrong_primary','FAIL'),('wrong_bundle','FAIL'),('wrong_proof','FAIL'),('wrong_report','FAIL'),('old_persisted_report','FAIL'),
    ('missing_current_proof','UNKNOWN'),('wrong_current_proof','FAIL'),('barrier_substitution','FAIL'),
    ('equal_barrier','PASS'),('post_barrier','FAIL'),('offset_barrier','FAIL'),('missing_bound','UNKNOWN'),
])
def test_x04_actual_dvr_exact_current_bitcoin_bindings_and_barrier(change,expected):
    from forecast_trust_core import external_model_engine_v1 as engine
    result=fixture()[-1];cycle=next(e for e in result.events if e.name=='cycle-t1');event=next(e for e in result.events if e.name=='dvr-t1')
    dvr=deepcopy(event.raw_inputs['objects']['subject']);inputs=deepcopy(cycle.raw_inputs);ctx=deepcopy(cycle.independent_context)
    upper=event.trace['upper_bound'];barrier='2030-02-20T13:30:00Z'
    fields={'primary':'primary_subject_ref','bundle':'primary_bundle_ref','proof':'bitcoin_proof_ref','report':'bitcoin_computation_ref'}
    if change.startswith('missing_') and change[len('missing_'):] in fields:dvr.pop(fields[change[len('missing_'):]],None)
    elif change.startswith('wrong_') and change[len('wrong_'):] in fields:dvr[fields[change[len('wrong_'):]]]=ctx['rule_ref']
    elif change=='old_persisted_report':dvr['bitcoin_computation_ref']={'object_id':cycle.input_refs['report'].object_id,'content_sha256':'0'*64}
    elif change=='missing_current_proof':inputs['objects']['proof']=None
    elif change=='wrong_current_proof':inputs['objects']['proof']['bundle_ref']=ctx['rule_ref']
    elif change=='barrier_substitution':dvr['outcome_barrier']='2031-02-20T13:30:00Z'
    elif change=='equal_barrier':upper=barrier
    elif change=='post_barrier':upper='2030-02-20T13:30:01Z'
    elif change=='offset_barrier':upper='2030-02-20T13:30:00-10:00'
    elif change=='missing_bound':upper=None
    assert hasattr(engine,'evaluate_preoutcome_binding'),'X04 exact model DVR binding kernel missing'
    checks=engine.evaluate_preoutcome_binding(dvr,inputs,ctx,frozen_barrier=barrier,dvr_upper_bound=upper)
    from forecast_trust_core.replay_records_v1 import reduce_checks
    assert reduce_checks(checks)==expected,checks


def test_x04_known_wrong_primary_survives_simultaneously_missing_current_proof():
    from forecast_trust_core import external_model_engine_v1 as engine
    from forecast_trust_core.replay_records_v1 import reduce_checks
    result=fixture()[-1];cycle=next(e for e in result.events if e.name=='cycle-t1');event=next(e for e in result.events if e.name=='dvr-t1')
    dvr=deepcopy(event.raw_inputs['objects']['subject']);inputs=deepcopy(cycle.raw_inputs);ctx=deepcopy(cycle.independent_context)
    dvr['primary_subject_ref']=ctx['rule_ref'];inputs['objects']['proof']=None
    checks=engine.evaluate_preoutcome_binding(dvr,inputs,ctx,frozen_barrier='2030-02-20T13:30:00Z',dvr_upper_bound=event.trace['upper_bound'])
    assert reduce_checks(checks)=='FAIL',checks


def test_x04_positive_committed_report_is_identity_of_current_fresh_computation():
    from forecast_trust_core import external_model_engine_v1 as engine
    result=fixture()[-1]
    for n in ('t1','t2','t3'):
        cycle=next(e for e in result.events if e.name=='cycle-'+n);event=next(e for e in result.events if e.name=='dvr-'+n)
        expected=engine.ref(engine.reconstruct_model_bitcoin_report(cycle.raw_inputs,cycle.independent_context))
        assert event.raw_inputs['objects']['subject']['bitcoin_computation_ref']==expected==cycle.trace['computed_report_ref']
        assert event.raw_inputs['objects']['subject']['primary_bundle_ref']==cycle.input_refs['bundle'].to_dict()
        assert event.raw_inputs['objects']['subject']['bitcoin_proof_ref']==cycle.input_refs['proof'].to_dict()
        assert result.overall=='PASS'
