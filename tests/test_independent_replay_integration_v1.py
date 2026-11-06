"""Full fixed M1 replay; no signing, live backend or private material."""
import importlib,importlib.util
from pathlib import Path
from dataclasses import replace
from copy import deepcopy
import json
import pytest
from forecast_trust_core.authority_primitives_v1 import ExactRef
from forecast_trust_core.g10_requirements_v1 import _fixed_basis
from forecast_trust_core.replay_model_v1 import MODEL_SOURCE_REFS
from forecast_trust_core.external_model_pins_v1 import MODEL_EXTERNAL_REFS,MODEL_EXTERNAL_ALL_REFS
from forecast_trust_core.scientific_model_pins_v1 import MODEL_SCIENTIFIC_REFS,MODEL_SCIENTIFIC_RAW_REFS
CORPUS=Path(__file__).parent/'fixtures/independent_replay_v1'

def api():
    assert importlib.util.find_spec('forecast_trust_core.independent_replay_v1'),'T09 full replay missing'
    return importlib.import_module('forecast_trust_core.independent_replay_v1')

def fixture():
    mod=api();r=mod.CorpusResolver(CORPUS);b=_fixed_basis()
    return mod,b,r

def reasons(result):return {reason for row in result.raw_results for reason in row.reason_codes}

def failed_checks(result):
    found=[]
    for row in result.raw_results:
        if not row.raw_result:continue
        value=json.loads(row.raw_result)
        if isinstance(value,dict):found.extend(x.get('id') for x in value.get('checks',[]) if x.get('status')=='FAIL')
    return set(found)

@pytest.mark.parametrize('field', ['subject','root_ref','rule_ref','scope_ref','effective_ref',
    'source_selection_rule_ref','historical_rule_ref','workflow_rule_ref','profile'])
def test_review_missing_nullable_basis_full_and_persisted(field):
    mod,b,r=fixture()
    missing=replace(b,**{field:() if field=='profile' else None})
    result=mod.replay_initial_acceptance(missing,r)
    assert result.overall=='UNKNOWN',reasons(result)
    assert 'INDEPENDENT_BASIS_MISSING' in reasons(result)
    current=mod.validate_persisted_independent_replay(missing,r,mod.stable_report(result))
    assert current.overall=='UNKNOWN'
    assert all(isinstance(ref,ExactRef) for ref in current.input_refs)

def test_review_missing_subject_combination_preserves_known_fail():
    mod,b,r=fixture();missing=replace(b,subject=None,root_ref=None)
    assert mod.replay_initial_acceptance(missing,r).overall=='UNKNOWN'
    r.data[ExactRef.from_mapping(MODEL_SOURCE_REFS['target-t3'])]=b'{}'
    result=mod.replay_initial_acceptance(missing,r)
    assert result.overall=='FAIL',reasons(result)
    assert mod.validate_persisted_independent_replay(missing,r,mod.stable_report(result)).overall=='FAIL'

def test_review_all_presigning_reports_and_runtime_provenance_use_fixed_prefix():
    mod,b,full=fixture()
    from forecast_trust_core.integration_model_pins_v1 import MODEL_COPY_REFS
    from forecast_trust_core.integration_model_v1 import replay_integration_checks,observe_model_runtime
    pre={ExactRef(x['object_id'],x['content_sha256']) for x in MODEL_COPY_REFS['pre-signing']}
    class Prefix:
        def resolve_exact(self,ref):return full.resolve_exact(ref) if ref in pre else None
        def resolve_copy_exact(self,group,ref):return full.resolve_copy_exact(group,ref) if ref in pre else None
    r=Prefix();req=mod.reconstruct_requirements(b,r);cycles=mod.reconstruct_cycle_universe(b,r)
    qualifications=mod.replay_qualification_scope(b,cycles,req,r)
    native,errors,bitcoin,objects=replay_integration_checks(b,req,r,observe_model_runtime())
    reports,evidence=mod._reports(b,req,r,native,bitcoin,qualifications)
    assert all(c.status=='PASS' for checks in reports.values() for c in checks),reports
    assert set(native['runtime_pairing'].input_refs)<=pre
    assert native['runtime_pairing'].input_refs
    assert all(item['input_refs'] and set(item['input_refs'])<=pre for item in evidence.values())
    assert any(c.status=='UNKNOWN' for c in native['retention_corpus'].checks)

@pytest.mark.parametrize('later',['missing','timeout','mismatch'])
def test_review_calendar_page_uses_one_validated_raw_capture(later):
    mod,b,r=fixture()
    from forecast_trust_core.calendar_model_v1 import MODEL_CALENDAR_PAGE_REFS
    page=ExactRef.from_mapping(next(iter(MODEL_CALENDAR_PAGE_REFS.values())))
    calls=0
    class Supply:
        def resolve_exact(self,ref):
            nonlocal calls
            if ref==page:
                calls+=1
                if calls>1:
                    if later=='timeout':raise TimeoutError('later retained page unavailable')
                    return None if later=='missing' else b'{}'
            return r.resolve_exact(ref)
    # C06 must parse and hash one captured exact observation, not two reads.
    result=mod.reconstruct_cycle_universe(b,Supply())
    assert calls==1
    assert result.overall=='PASS'
    assert len(result.cycles)==3

@pytest.mark.parametrize('first',['missing','timeout','mismatch'])
def test_review_calendar_first_observation_keeps_unknown_or_known_fail(first):
    mod,b,r=fixture()
    from forecast_trust_core.calendar_model_v1 import MODEL_CALENDAR_PAGE_REFS
    page=ExactRef.from_mapping(next(iter(MODEL_CALENDAR_PAGE_REFS.values())))
    original=r.resolve_exact
    def supply(ref):
        if ref==page:
            if first=='timeout':raise TimeoutError('retained page unavailable')
            return None if first=='missing' else b'{}'
        return original(ref)
    r.resolve_exact=supply
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall==('FAIL' if first=='mismatch' else 'UNKNOWN'),reasons(result)

@pytest.mark.parametrize('later',['missing','timeout','mismatch'])
def test_review_calendar_transient_full_entry_retains_current_truth(later):
    mod,b,r=fixture()
    from forecast_trust_core.calendar_model_v1 import MODEL_CALENDAR_PAGE_REFS
    page=ExactRef.from_mapping(next(iter(MODEL_CALENDAR_PAGE_REFS.values())))
    original=r.resolve_exact;calls=0
    def supply(ref):
        nonlocal calls
        if ref==page:
            calls+=1
            if calls>1:
                if later=='timeout':raise TimeoutError('later retained page unavailable')
                return None if later=='missing' else b'{}'
        return original(ref)
    r.resolve_exact=supply
    result=mod.replay_initial_acceptance(b,r)
    assert result.cycles.overall=='PASS'
    # The final complete-copy audit still consumes its own current observation.
    assert result.overall==('FAIL' if later=='mismatch' else 'UNKNOWN'),reasons(result)

@pytest.mark.parametrize('retention',['missing','mismatch'])
def test_review_postsign_retention_remains_consequential_at_full_boundary(retention):
    mod,b,r=fixture()
    from forecast_trust_core.integration_model_pins_v1 import MODEL_INTEGRATION_REFS
    rr=ExactRef.from_mapping(MODEL_INTEGRATION_REFS['retention'])
    if retention=='missing':r.data.pop(rr)
    else:r.data[rr]=b'{}'
    result=mod.replay_initial_acceptance(b,r)
    assert all(c.status=='PASS' for c in result.component_reports['runtime'])
    assert result.overall==('UNKNOWN' if retention=='missing' else 'FAIL'),reasons(result)

@pytest.mark.parametrize('later',['missing','timeout','mismatch'])
def test_review_presign_member_uses_one_validated_raw_capture(monkeypatch,later):
    mod,b,r=fixture()
    from forecast_trust_core.integration_model_pins_v1 import MODEL_PRESIGN_QUALIFICATION
    member=ExactRef.from_mapping(MODEL_PRESIGN_QUALIFICATION['p1']['formation']['members']['m-0.json'])
    original=mod._reports;counts=[]
    def with_transient(basis,requirements,resolver,*args):
        calls=0
        class Supply:
            def resolve_exact(self,ref):
                nonlocal calls
                if ref==member:
                    calls+=1;counts.append(calls)
                    if calls>1:
                        if later=='timeout':raise TimeoutError('later member observation unavailable')
                        return None if later=='missing' else b'{}'
                return resolver.resolve_exact(ref)
        return original(basis,requirements,Supply(),*args)
    monkeypatch.setattr(mod,'_reports',with_transient)
    result=mod.replay_initial_acceptance(b,r)
    # The first package uses captured validated bytes. A later package may need
    # its own fresh observation, whose unavailable/invalid truth must survive.
    assert result.overall==('FAIL' if later=='mismatch' else 'UNKNOWN'),reasons(result)
    assert counts

def test_review_presign_complete_history_is_past_and_final_admissions_remain_complete():
    mod,b,r=fixture()
    from forecast_trust_core.integration_model_pins_v1 import MODEL_PRESIGN_QUALIFICATION,MODEL_COPY_REFS,MODEL_INTEGRATION_REFS
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='PASS'
    assert len(result.qualifications.admissions)==33
    final=[a for a in result.qualifications.admissions if a.deadline=='2030-02-01T00:00:00Z']
    assert len(final)==3 and all(a.admitted for a in final)
    pre={ExactRef(x['object_id'],x['content_sha256']) for x in MODEL_COPY_REFS['pre-signing']}
    retention=json.loads(r.resolve_exact(ExactRef.from_mapping(MODEL_INTEGRATION_REFS['retention'])))
    for provider in ('p1','p2','p3'):
        pins=MODEL_PRESIGN_QUALIFICATION[provider].get('pre-signing')
        assert pins is not None,'pre-signing scope must differ from later final-deadline scope'
        package=json.loads(r.resolve_exact(ExactRef.from_mapping(pins['package_ref'])))
        history=json.loads(r.resolve_exact(ExactRef.from_mapping(pins['history_ref'])))
        assert package['as_of_utc']==history['through_as_of_utc']=='2030-01-31T21:00:00Z'
        assert history['through_as_of_utc']<retention['pre_signing_retained_at']
        from forecast_trust_core.qualification_model_pins_v1 import MODEL_QUALIFICATION_PACKAGES
        assert ExactRef.from_mapping(MODEL_QUALIFICATION_PACKAGES[provider]['final-acceptance']['package_ref']) not in pre
    assert importlib.util.find_spec('forecast_trust_core.presigning_model_v1')
    from forecast_trust_core.presigning_model_v1 import MODEL_PRE_SIGNING_RULE
    assert MODEL_PRE_SIGNING_RULE['report_as_of_utc']<MODEL_PRE_SIGNING_RULE['reports_available_at']<MODEL_PRE_SIGNING_RULE['copies_available_at']<MODEL_PRE_SIGNING_RULE['signing_not_before']

@pytest.mark.parametrize('name',['presign-chronology','presign-report-availability','signing-formation'])
def test_review_presign_chronology_unavailable_is_full_unknown(name):
    assert importlib.util.find_spec('forecast_trust_core.presigning_model_v1'),'independent chronology check missing'
    from forecast_trust_core.integration_model_pins_v1 import MODEL_INTEGRATION_REFS
    mod,b,r=fixture();r.data.pop(ExactRef.from_mapping(MODEL_INTEGRATION_REFS[name]))
    assert mod.replay_initial_acceptance(b,r).overall=='UNKNOWN'

@pytest.mark.parametrize('family',['future-scope','late-report','early-sign','late-sign','wrong-subject'])
def test_review_presign_chronology_contradictions_consumed_by_full_entry(monkeypatch,family):
    assert importlib.util.find_spec('forecast_trust_core.presigning_model_v1'),'independent chronology check missing'
    from forecast_trust_core import presigning_model_v1 as stage
    mod,b,r=fixture()
    original=stage.read
    def changed(reference,resolver,checks):
        obj=original(reference,resolver,checks)
        if obj is None:return None
        obj=deepcopy(obj);kind=obj.get('object_type')
        if family=='future-scope' and kind=='SyntheticPreSigningChronologyContract':obj['report_as_of_utc']='2030-02-01T00:00:00Z'
        elif family=='late-report' and kind=='SyntheticReportAvailability':obj['available_at']='2030-01-31T23:00:00Z'
        elif kind=='SyntheticModelSigningFormation':
            if family=='early-sign':obj['formed_at']='2030-01-31T21:00:00Z'
            elif family=='late-sign':obj['formed_at']='2030-02-01T01:00:00Z'
            elif family=='wrong-subject':obj['subject_ref']=b.subject.to_dict()
        return obj
    monkeypatch.setattr(stage,'read',changed)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL',reasons(result)

@pytest.mark.parametrize('kind',['SyntheticQualificationHistory','SyntheticQualificationObservation','SyntheticQualificationFormation'])
def test_review_presign_future_member_is_consequential(monkeypatch,kind):
    from forecast_trust_core import presigning_model_v1 as stage
    mod,b,r=fixture();original=stage._read_raw
    def changed(reference,resolver):
        obj,raw,errors=original(reference,resolver)
        if obj is not None and obj.get('object_type')==kind:
            obj=deepcopy(obj)
            field={'SyntheticQualificationHistory':'through_as_of_utc','SyntheticQualificationObservation':'observed_at','SyntheticQualificationFormation':'formed_at'}[kind]
            obj[field]='2030-02-01T00:00:00Z'
        return obj,raw,errors
    monkeypatch.setattr(stage,'_read_raw',changed)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL'
    assert any(c.reason_code=='PRE_SIGNING_HISTORY_FUTURE_INPUT' and c.status=='FAIL' for c in result.component_evidence['pre-signing-qualification']['checks'])

def test_review_past_report_cannot_replace_missing_final_deadline_admission():
    from forecast_trust_core.qualification_model_pins_v1 import MODEL_QUALIFICATION_PACKAGES
    mod,b,r=fixture();r.data.pop(ExactRef.from_mapping(MODEL_QUALIFICATION_PACKAGES['p3']['final-acceptance']['package_ref']))
    result=mod.replay_initial_acceptance(b,r)
    assert all(c.status=='PASS' for c in result.component_reports['qualification'])
    final=next(a for a in result.qualifications.admissions if a.provider=='p3' and a.deadline=='2030-02-01T00:00:00Z')
    assert final.status=='UNKNOWN' and not final.admitted
    assert result.overall=='UNKNOWN'

def test_review_chronology_consumes_computed_upper_bound_not_as_signing_time(monkeypatch):
    assert importlib.util.find_spec('forecast_trust_core.presigning_model_v1'),'independent chronology check missing'
    mod,b,r=fixture();original=mod.replay_external_evidence
    def earlier(*args,**kwargs):
        result=original(*args,**kwargs);events=list(result.events)
        event=events[0];trace=deepcopy(event.trace);trace['upper_bound']='2030-01-31T22:00:00Z'
        events[0]=replace(event,trace=trace)
        return replace(result,events=tuple(events))
    monkeypatch.setattr(mod,'replay_external_evidence',earlier)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL' and 'MODEL_SIGNING_EXISTENCE_INTERVAL' in reasons(result)

def test_full_model_actual_complete_chain_and_four_completeness():
    mod,b,r=fixture();result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='PASS',reasons(result)
    assert len(result.raw_results)==len(result.requirements.mandatory_keys)==2817
    assert {x.key for x in result.raw_results}==set(result.requirements.mandatory_keys)
    assert len(result.coverage_diagnostics)==5 and all(c.status=='PASS' for c in result.coverage_diagnostics)
    assert result.scientific.scored_squared_errors==('0.5625','0.5625','0.5625')
    assert len(result.cycles.cycles)==3 and len(result.qualifications.admissions)==33 and len(result.external.events)==10
    assert result.real_genesis_readiness=='NOT_ESTABLISHED' and not result.prospective_eligible and result.protocol_state_change=='NONE'
    assert result.model_only and result.seams

@pytest.mark.parametrize('kind',['root','selection','scope','target-t3','external','workflow','profile'])
def test_entire_source_missing_through_full_entry_never_empty_pass(kind):
    mod,b,r=fixture();r.data.pop(ExactRef.from_mapping(MODEL_SOURCE_REFS[kind]))
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall!='PASS',reasons(result)
    assert result.raw_results and result.requirements.mandatory_keys

@pytest.mark.parametrize('family',['source','report','scientific','raw','bitcoin','dvr','acceptance'])
def test_known_hash_contradiction_through_full_entry_fail(family):
    mod,b,r=fixture()
    ref={'source':MODEL_SOURCE_REFS['external'],'report':MODEL_EXTERNAL_ALL_REFS['report-runtime'],
         'scientific':MODEL_SCIENTIFIC_REFS['t1']['run'],'raw':MODEL_SCIENTIFIC_RAW_REFS['t1-baseline'],
         'bitcoin':MODEL_EXTERNAL_REFS['cycle-t1']['proof'],'dvr':MODEL_EXTERNAL_REFS['dvr-t1']['subject'],
         'acceptance':MODEL_EXTERNAL_ALL_REFS['complete-initial-acceptance']}[family]
    r.data[ExactRef.from_mapping(ref)]=b'{}'
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL',reasons(result)


def test_public_mode_never_borrows_model_pass_or_executes_model_crypto():
    mod,b,r=fixture();result=mod.replay_initial_acceptance(replace(b,mode='PUBLIC_EVIDENCE'),r)
    assert result.overall=='UNKNOWN',reasons(result)
    assert not result.prospective_eligible and result.real_genesis_readiness=='NOT_ESTABLISHED'
    assert result.raw_results and not any(e.fresh_execution for e in result.external.events)


def test_full_api_has_no_caller_vector_expected_universe_eligibility_or_callback():
    mod,b,r=fixture()
    for key in ('expected_universe','results','qualified','eligible','strong_state','callback','component_reports'):
        with pytest.raises(TypeError):mod.replay_initial_acceptance(b,r,**{key:True})


def test_fresh_resolver_replay_stable_identity_and_result():
    mod,b,r=fixture();a=mod.replay_initial_acceptance(b,r);other=mod.replay_initial_acceptance(b,mod.CorpusResolver(CORPUS))
    assert a.overall==other.overall=='PASS'
    assert a.stable_identity==other.stable_identity and a.mandatory_set_identity==other.mandatory_set_identity


def test_persisted_output_is_comparison_only_not_authority():
    mod,b,r=fixture();a=mod.replay_initial_acceptance(b,r)
    persisted=deepcopy(mod.stable_report(a));persisted['overall']='PASS';persisted['model_only']=False
    current=mod.validate_persisted_independent_replay(replace(b,mode='PUBLIC_EVIDENCE'),r,persisted)
    assert current.overall!='PASS'


def test_independent_full_entry_missing_runtime_cannot_use_historical_report_pass(monkeypatch):
    mod,b,r=fixture()
    def absent(*args,**kwargs):raise OSError('retained runtime unavailable')
    monkeypatch.setattr(mod,'observe_model_runtime',absent)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='UNKNOWN',reasons(result)


def test_partial_raw_records_do_not_gain_coverage_by_unknown_padding(monkeypatch):
    mod,b,r=fixture();original=mod.replay_external_evidence
    def partial(*args,**kwargs):
        result=original(*args,**kwargs)
        return replace(result,records=result.records[:-1])
    monkeypatch.setattr(mod,'replay_external_evidence',partial)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL'
    assert any(c.check_id=='RESULT_COVERAGE_COMPLETE' and c.status=='FAIL' for c in result.coverage_diagnostics)


def test_native_full_guard_preserves_unknown_and_known_fail():
    assert importlib.util.find_spec('forecast_trust_core.initial_replay_guard_v1'),'legacy full-entry G10 guard missing'
    guard=importlib.import_module('forecast_trust_core.initial_replay_guard_v1')
    from forecast_trust_core.core import Validation,Result,Check
    a=guard.require_complete_initial_replay(Validation(Result.VALID,()))
    assert a.result==Result.INELIGIBLE_TRUST_UNKNOWN and not a.valid
    assert any(c.reason_code=='INDEPENDENT_INITIAL_BASIS_NOT_ESTABLISHED' for c in a.checks)
    fail=guard.require_complete_initial_replay(Validation(Result.INVALID,(Check('known','FAIL','KNOWN'),)))
    assert fail.result==Result.INVALID and any(c.reason_code=='KNOWN' for c in fail.checks)

@pytest.mark.parametrize('family',['empty','duplicate','unknown','false-na'])
def test_full_raw_vector_control_and_precedence(monkeypatch,family):
    mod,b,r=fixture();original=mod.replay_external_evidence
    def mutated(*args,**kwargs):
        result=original(*args,**kwargs);rows=result.records
        if family=='empty':rows=()
        elif family=='duplicate':rows=rows+(rows[0],)
        elif family=='unknown':rows=(replace(rows[0],normalized='UNKNOWN',reason_codes=('MANDATORY_UNKNOWN_PROBE',)),*rows[1:])
        else:rows=(replace(rows[0],normalized='NOT_APPLICABLE',applicability='APPLICABLE'),*rows[1:])
        return replace(result,records=rows)
    monkeypatch.setattr(mod,'replay_external_evidence',mutated)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall==('UNKNOWN' if family=='unknown' else 'FAIL'),reasons(result)
    if family in ('empty','duplicate'):assert result.coverage_diagnostics[-1].status=='FAIL'

@pytest.mark.parametrize('family',['class','clause','retention'])
def test_full_mapping_omission_cannot_shrink_source_M_and_O_together(monkeypatch,family):
    from forecast_trust_core import g10_requirements_v1 as source
    mod,b,r=fixture();mapping=dict(source.CHECK_SPECS)
    if family=='class':mapping={k:v for k,v in mapping.items() if v[0]!='P23'}
    else:mapping.pop('offline_backup_rule' if family=='retention' else 'root_project')
    monkeypatch.setattr(source,'CHECK_SPECS',mapping)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL' and result.requirements.proofs[1].status=='FAIL'

def test_simultaneously_shrunken_M_and_O_is_caught_by_independent_source_expansion(monkeypatch):
    from forecast_trust_core import g10_requirements_v1 as source
    mod,b,r=fixture();original=source._expand
    def shrink(name,spec,*args):return () if spec and spec[0]=='P23' else original(name,spec,*args)
    monkeypatch.setattr(source,'_expand',shrink)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL' and len(result.requirements.mandatory_keys)<2817
    assert result.requirements.proofs[2].status=='FAIL'
    assert 'PREDICATE_INSTANCE_OMISSION_OR_SUBSTITUTION' in {c.reason_code for c in result.requirements.diagnostics}

@pytest.mark.parametrize('family',['root','rule'])
def test_full_wrong_independent_basis_fail(family):
    mod,b,r=fixture();b=replace(b,**{family+'_ref':ExactRef('model:wrong:'+family,'0'*64)})
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL' and result.requirements.proofs[0].status=='FAIL'

@pytest.mark.parametrize('family',['calendar','history','bitcoin','copy','pre-signing-witness'])
def test_full_missing_evidence_has_exact_unknown_classification(family):
    from forecast_trust_core.calendar_model_v1 import MODEL_CALENDAR_COVERAGE_REFS
    from forecast_trust_core.qualification_model_pins_v1 import MODEL_QUALIFICATION_HISTORY_INPUTS
    from forecast_trust_core.integration_model_pins_v1 import MODEL_COPY_REFS,MODEL_INTEGRATION_REFS
    mod,b,r=fixture()
    if family=='calendar':refs=[next(iter(MODEL_CALENDAR_COVERAGE_REFS.values()))]
    elif family=='history':refs=MODEL_QUALIFICATION_HISTORY_INPUTS['p3']
    elif family=='bitcoin':refs=[MODEL_EXTERNAL_REFS['cycle-t1']['proof']]
    elif family=='pre-signing-witness':refs=[MODEL_INTEGRATION_REFS['presign-proof']]
    else:
        entry=MODEL_COPY_REFS['pre-signing'][0];r.copies.pop(('pre-signing',ExactRef(entry['object_id'],entry['content_sha256'])));refs=[]
    for ref in refs:r.data.pop(ExactRef.from_mapping(ref),None)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='UNKNOWN',reasons(result)
    assert any(row.normalized=='UNKNOWN' for row in result.raw_results)

@pytest.mark.parametrize('family,check',[
    ('future','NT02_input_availability'),('output','NT03_deterministic_reexecution'),
    ('method','NT03_method_configuration'),('attempt','NT04_attempt_succession'),
    ('retry','NT04_first_success_output'),('denominator','NT08_denominator'),
    ('origin','NT06_origin_preservation'),('vintage','NT07_first_release_resolution')])
def test_full_entry_consumes_causal_scientific_kernel_failures(monkeypatch,family,check):
    from forecast_trust_core import scientific_model_engine_v1 as engine
    from forecast_trust_core.canonical import canonical_json,seal_object
    mod,b,r=fixture();original=engine.evaluate_scientific_slot
    def mutate(inputs,context,runtime):
        inputs=deepcopy(inputs);o=inputs['objects']
        if family=='future':
            capture=o['baseline'];rr=capture['raw_ref'];data=json.loads(inputs['raw'][rr['object_id']]);data['available_at']='2031-01-01T00:00:00Z';raw=canonical_json(data)
            from hashlib import sha256
            inputs['raw'][rr['object_id']]=raw;capture['raw_ref']['content_sha256']=sha256(raw).hexdigest();capture['available_at']=data['available_at']
            o['baseline']=seal_object({k:v for k,v in capture.items() if k not in ('object_id','payload_sha256','content_sha256')},object_type=capture['object_type'],stable_context='M1_DEVELOPMENT_ONLY',semantic_id=capture['object_id'])
        elif family=='output':o['run']['prediction']='999'
        elif family=='method':o['run']['configuration']['selection']='BEST_OUTCOME'
        elif family=='attempt':o['execution-0']['sequence']=1
        elif family=='retry':o['attempt_ledger']['selected_attempt_ref']=context['issued_ref']
        elif family=='denominator':o['cohort']['included_forecast_refs']=[]
        elif family=='origin':o['run']['origin']='LIVE_OPERATIONAL'
        else:o['resolution_selection']['selected_vintage']='LATEST'
        return original(inputs,context,runtime)
    monkeypatch.setattr(engine,'evaluate_scientific_slot',mutate)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL' and check in failed_checks(result),reasons(result)

@pytest.mark.parametrize('family,check',[
    ('late','deadline_upper_bound'),('subject','wall_subject_nonce'),('two-bundles','bitcoin_subject_bundle'),
    ('auth','wall_signature_delegation'),('wrong-pin','bitcoin_pin_chain'),('retry','wall_quorum_transcript')])
def test_full_entry_consumes_causal_external_kernel_failures(monkeypatch,family,check):
    from forecast_trust_core import g10_external_evidence_v1 as adapter
    mod,b,r=fixture();original=adapter.fresh_model_execution
    def mutate(inputs,context):
        inputs=deepcopy(inputs);context=deepcopy(context);o=inputs['objects']
        if family=='late':o['bundle']['reported_upper_bound']='2031-01-01T00:00:00Z'
        elif family=='subject':o['bundle']['subject_ref']=context['rule_ref']
        elif family=='two-bundles':o['proof']['bundle_ref']=context['rule_ref']
        elif family=='auth':o['authentication']['provider_facts'][0]['model_status']='INVALID'
        elif family=='wrong-pin':context['runtime']['engine_sha256']='0'*64
        else:o['execution']['providers'][0]['attempts'].append(deepcopy(o['execution']['providers'][0]['attempts'][0]))
        return original(inputs,context)
    monkeypatch.setattr(adapter,'fresh_model_execution',mutate)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL' and check in failed_checks(result),reasons(result)

@pytest.mark.parametrize('exception',[TimeoutError,OSError])
def test_full_current_execution_exception_never_borrows_retained_pass(monkeypatch,exception):
    from forecast_trust_core import g10_external_evidence_v1 as adapter
    mod,b,r=fixture()
    def unavailable(*a,**k):raise exception('public model execution unavailable')
    monkeypatch.setattr(adapter,'fresh_model_execution',unavailable)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='UNKNOWN',reasons(result)
    assert any('MODEL_EXTERNAL_EXECUTION_UNAVAILABLE_'+exception.__name__ in reason for reason in reasons(result))

def test_fixed_resolver_does_not_read_caller_manifest_or_unknown_files(tmp_path):
    mod,b,r=fixture()
    root=tmp_path/'empty';root.mkdir();(root/'manifest.json').write_text('{"overall":"PASS","model_only":false}')
    other=mod.CorpusResolver(root)
    assert not other.data
    result=mod.replay_initial_acceptance(b,other)
    assert result.overall!='PASS'

def test_fixed_resolver_rejects_symlink_in_known_input_path(tmp_path):
    mod=api();(tmp_path/'sources').symlink_to(CORPUS/'sources',target_is_directory=True)
    with pytest.raises(ValueError,match='symlink'):mod.CorpusResolver(tmp_path)

@pytest.mark.parametrize('family,expected_reason',[
    ('reject','MANIFEST_NOT_ACCEPTED'),('blocking','APPLICABLE_BLOCKING_FINDING'),
    ('wrong-subject','WRONG_REPORT_SUBJECT'),('wrong-validator','WRONG_REPORT_VALIDATOR'),
    ('wrong-kind','WRONG_REPORT_KIND'),('report-blocker','REPORT_DECLARED_BLOCKER'),
    ('report-cardinality','REPORT_RAW_CHECK_COVERAGE'),('self-reference','PRE_SIGNING_ACCEPTANCE_OR_FINAL_REPORT_CYCLE')])
def test_full_entry_consumes_acceptance_report_and_finding_semantics(monkeypatch,family,expected_reason):
    """Negative decode-boundary probes; actual checks execute, no fake PASS."""
    from forecast_trust_core import g10_acceptance_v1 as adapter
    from forecast_trust_core.canonical import seal_object,canonical_json
    mod,b,r=fixture();original=adapter._read
    finding=seal_object({'model_only':True,'blocking':True,'state':'OPEN','subject_ref':b.subject.to_dict()},object_type='SyntheticFinding',stable_context='M1_DEVELOPMENT_ONLY',semantic_id='model:full-test:blocking')
    fr=ExactRef(finding['object_id'],finding['content_sha256']);r.data[fr]=canonical_json(finding)
    def modified(ref,resolver):
        obj,errors=original(ref,resolver)
        if obj is None:return obj,errors
        obj=deepcopy(obj)
        if obj.get('object_type')=='ManifestAcceptance' and family=='reject':
            obj['decision']='REJECT'
            obj=seal_object({k:v for k,v in obj.items() if k not in ('object_id','content_sha256','payload_sha256')},object_type=obj['object_type'],stable_context='M1_DEVELOPMENT_ONLY',semantic_id=obj['object_id'])
        if obj.get('object_type')=='SyntheticReplayReport' and obj.get('kind')=='runtime':
            if family=='blocking':obj['finding_refs']=[fr.to_dict()]
            elif family=='wrong-subject':obj['subject_ref']=b.rule_ref.to_dict()
            elif family=='wrong-validator':obj['validator_ref']=b.rule_ref.to_dict()
            elif family=='wrong-kind':obj['kind']='not-mandatory'
            elif family=='report-blocker':obj['status']='FAIL'
            elif family=='report-cardinality':obj['checks'].append(deepcopy(obj['checks'][0]))
            elif family=='self-reference':obj['dependency_refs'].append(MODEL_EXTERNAL_ALL_REFS['complete-initial-acceptance'])
        return obj,errors
    monkeypatch.setattr(adapter,'_read',modified)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL',reasons(result)
    assert expected_reason in reasons(result),reasons(result)

def test_post_outcome_DVR_through_full_entry(monkeypatch):
    from forecast_trust_core import external_model_engine_v1 as engine
    mod,b,r=fixture();original=engine.evaluate_preoutcome_binding
    def late(*args,**kwargs):
        kwargs['dvr_upper_bound']='2031-01-01T00:00:00Z'
        return original(*args,**kwargs)
    monkeypatch.setattr(engine,'evaluate_preoutcome_binding',late)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL' and 'dvr_preoutcome_barrier' in failed_checks(result)

@pytest.mark.parametrize('family',['old-head','early-cutoff','adverse-omission'])
def test_full_history_selection_contradictions_cannot_be_erased(monkeypatch,family):
    from forecast_trust_core import qualification_scope_v1 as stage
    mod,b,r=fixture();original=stage.verify_model_history_selection
    def mutate(observed,scope):
        observed=deepcopy(observed)
        if family=='old-head':observed['p3']['head_ref']=observed['p3']['old_head_ref']
        elif family=='early-cutoff':observed['p3']['cutoff']='2030-01-01T00:00:00Z'
        else:observed['p3']['event_refs']=observed['p3']['event_refs'][1:]
        return original(observed,scope)
    monkeypatch.setattr(stage,'verify_model_history_selection',mutate)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL',reasons(result)
    assert {'old-head':'INDEPENDENT_HISTORY_HEAD_MISMATCH','early-cutoff':'HISTORY_CUTOFF_DOES_NOT_COVER_BOUNDARIES','adverse-omission':'COMPLETE_HISTORY_EVENT_SET_MISMATCH'}[family] in reasons(result)

def test_full_actual_invalid_admission_is_consumed_by_scientific_and_quorum(monkeypatch):
    from forecast_trust_core import qualification_scope_v1 as stage
    mod,b,r=fixture();original=stage.recheck_model_admission
    def invalid(admission,**overrides):
        current=original(admission,**overrides)
        return replace(current,admitted=False,status='FAIL',reason_codes=('VALIDATION_STATUS_NOT_VALID',)) if current.provider=='p3' else current
    monkeypatch.setattr(stage,'recheck_model_admission',invalid)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL' and 'QUALIFICATION_ADMISSION_NOT_CONSUMABLE' in reasons(result)

@pytest.mark.parametrize('family',['cycle','target','slot','synchronous-shrink'])
def test_full_submission_inventory_cannot_define_cycle_universe(monkeypatch,family):
    from forecast_trust_core import cycle_universe_v1 as stage
    mod,b,r=fixture();original=stage.compare_submission_inventory
    def shrink(cycles,slots,observed):
        observed=deepcopy(observed)
        field='slots' if family=='slot' else 'cycles';observed[field]=observed[field][1:]
        if family=='synchronous-shrink':observed['claimed_expected_cycles']=observed['cycles']
        return original(cycles,slots,observed)
    monkeypatch.setattr(stage,'compare_submission_inventory',shrink)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL',reasons(result)
    assert any('MISSING_EXPECTED' in reason for reason in reasons(result))

def test_withdrawn_ineligible_issued_forecast_cannot_be_removed_from_full_denominator(monkeypatch):
    from forecast_trust_core import cycle_universe_v1 as stage
    mod,b,r=fixture();original=stage.project_accounting
    def omitted(slots,rows):
        if not rows:return original(slots,rows)
        rows=deepcopy(rows);rows[0]['withdrawal_state']='WITHDRAWN';rows[0]['eligibility_state']='INELIGIBLE'
        rows[0]['withdrawal_refs']=[b.rule_ref.to_dict()];rows[0]['ineligibility_evidence_refs']=[b.rule_ref.to_dict()]
        return original(slots,rows[1:])
    monkeypatch.setattr(stage,'project_accounting',omitted)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL' and 'MISSING_EXPECTED_SLOT_ACCOUNTING' in reasons(result)

@pytest.mark.parametrize('family,reason',[('control','MODEL_OWNER_CONTROL_ASSUMPTION'),('offline','MODEL_OFFLINE_COPY_ASSUMPTION'),('time','MODEL_COPY_TIMES_AND_PRE_SIGNING_SCOPE'),('freeze','MODEL_CANDIDATE_FREEZE_EXACT_ORDER'),('review','INDEPENDENT_MODEL_REQUIRED_REVIEW')])
def test_full_concrete_retention_and_workflow_checks_execute(monkeypatch,family,reason):
    from forecast_trust_core import integration_model_v1 as stage
    mod,b,r=fixture();original=stage.read
    def changed(ref,resolver,checks):
        obj=original(ref,resolver,checks)
        if obj is None:return obj
        obj=deepcopy(obj)
        if obj.get('object_type')=='SyntheticRetentionCopyEvidence':
            if family=='control':obj['controller']='UNKNOWN_CONTROLLER'
            elif family=='offline':obj['offline']=False
            elif family=='time':obj['pre_signing_retained_at']='2030-02-02T00:00:00Z'
        elif obj.get('object_type')=='SyntheticWorkflowFreeze' and family=='freeze':obj['actor']='MODEL_REVIEWER'
        elif obj.get('object_type')=='SyntheticWorkflowReview' and family=='review':obj['actor']='MODEL_OWNER'
        return obj
    monkeypatch.setattr(stage,'read',changed)
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL' and reason in reasons(result)

@pytest.mark.parametrize('family',['runtime','parser','tzdb','schedule','validator'])
def test_full_known_profile_or_version_substitution_fail(family,monkeypatch):
    from forecast_trust_core import cycle_universe_v1 as stage
    from forecast_trust_core.calendar_model_v1 import MODEL_TZDB_REFS
    mod,b,r=fixture()
    if family=='runtime':monkeypatch.setattr(mod,'observe_model_runtime',lambda:{'python':'wrong'})
    elif family=='parser':monkeypatch.setattr(stage,'runtime_identity',lambda:{'python':'3.12.3','parser_sha256':'0'*64})
    else:
        ref=next(iter(MODEL_TZDB_REFS.values())) if family=='tzdb' else MODEL_SOURCE_REFS['schedule' if family=='schedule' else 'profile']
        r.data[ExactRef.from_mapping(ref)]=b'wrong pinned bytes'
    result=mod.replay_initial_acceptance(b,r)
    assert result.overall=='FAIL',reasons(result)

def test_persisted_report_comparison_does_not_replace_current_truth():
    mod,b,r=fixture();result=mod.replay_initial_acceptance(b,r);report=mod.stable_report(result)
    report['raw_count']=1
    comparison=mod.validate_persisted_independent_replay(b,r,report)
    assert comparison.overall=='FAIL' and comparison.reduced.overall=='PASS'
    assert comparison.comparison_checks[0].reason_code=='PERSISTED_OUTPUT_DIFFERS_FROM_FRESH_REPLAY'

def test_persisted_historical_pass_current_missing_inputs_stays_unknown():
    mod,b,r=fixture();old=mod.stable_report(mod.replay_initial_acceptance(b,r))
    r.data.pop(ExactRef.from_mapping(MODEL_EXTERNAL_REFS['cycle-t1']['proof']))
    result=mod.validate_persisted_independent_replay(b,r,old)
    assert result.overall=='UNKNOWN' and result.reduced.overall=='UNKNOWN'

@pytest.mark.parametrize('wrapper',['full','persisted'])
def test_trusted_wrapper_routes_into_guarded_public_entry(monkeypatch,wrapper):
    """Negative routing only; no TrustedManifest/crypto fake positive result."""
    from types import SimpleNamespace
    from forecast_trust_core import claim_authority_trust_root_v1 as trusted
    from forecast_trust_core import claim_authority_v1 as public
    from forecast_trust_core.core import Validation,Result,Check
    reference=MODEL_SOURCE_REFS['profile'];calls=[]
    monkeypatch.setattr(trusted,'derive_trusted_manifest_authority_context',lambda *a:SimpleNamespace(trusted_manifest_ref=reference))
    monkeypatch.setattr(trusted,'bind_wall_clock_inputs_to_manifest',lambda *a,**k:{})
    monkeypatch.setattr(trusted,'bind_bitcoin_inputs_to_manifest',lambda *a,**k:{})
    def current(*a,**k):calls.append(True);return Validation(Result.INELIGIBLE_TRUST_UNKNOWN,(Check('full','UNKNOWN','INDEPENDENT_INITIAL_BASIS_NOT_ESTABLISHED'),)),(),{}
    name='validate_final_genesis_acceptance_authoritatively' if wrapper=='full' else 'validate_persisted_final_acceptance_report_authoritatively'
    # Verify the imported symbol is the real public boundary before replacing
    # it solely to observe delegation of this trusted wrapper.
    assert getattr(trusted,name) is getattr(public,name)
    monkeypatch.setattr(trusted,name,current)
    function=getattr(trusted,'validate_final_genesis_acceptance_from_trusted_manifest' if wrapper=='full' else 'validate_persisted_final_acceptance_report_from_trusted_manifest')
    args=({}, {'candidate_manifest_ref':reference}) if wrapper=='full' else ({},{},{'candidate_manifest_ref':reference})
    result=function(*args,final_evidence_subject_ref=reference,wall_clock_inputs={},bitcoin_inputs={})
    assert calls and result[0].result==Result.INELIGIBLE_TRUST_UNKNOWN

@pytest.mark.parametrize('mode,exit_code',[('synthetic-model',0),('public-evidence',2)])
def test_demo_fresh_process_exit_result_trace_and_guards(tmp_path,mode,exit_code):
    import subprocess,sys
    root=Path(__file__).resolve().parents[1];output=tmp_path/mode
    process=subprocess.run([sys.executable,str(root/'scripts/development/replay_independent_genesis.py'),'--corpus',str(CORPUS),'--mode',mode,'--output',str(output)],cwd=root,env={'PYTHONPATH':str(root/'src'),'PYTHONDONTWRITEBYTECODE':'1','PATH':'/usr/bin:/bin'},capture_output=True,text=True,timeout=60)
    assert process.returncode==exit_code,process.stderr+process.stdout
    report=json.loads((output/'result.json').read_bytes());trace=json.loads((output/'raw-trace.json').read_bytes());audit=json.loads((output/'audit.json').read_bytes())
    assert report['overall']==('PASS' if mode=='synthetic-model' else 'UNKNOWN')
    assert len(trace['M'])==len(trace['raw_O'])==2817
    assert report['real_genesis_readiness']=='NOT_ESTABLISHED' and report['prospective_eligible'] is False and report['protocol_state_change']=='NONE'
    assert audit['timestamp_is_stable'] is False and audit['stable_identity']==report['stable_identity']
    assert all(row['raw_result_ref'] in trace['raw_payloads'] and row['input_refs_ref'] in trace['input_ref_sets'] for row in trace['raw_O'])
    if mode=='synthetic-model':
        mod,b,r=fixture();assert report['stable_identity']==mod.replay_initial_acceptance(b,r).stable_identity

@pytest.mark.parametrize('error',['bad-argument','missing-corpus','existing-output','known-FAIL'])
def test_demo_command_errors_and_known_fail_have_exact_exit_codes(tmp_path,error):
    import subprocess,sys,shutil
    root=Path(__file__).resolve().parents[1];output=tmp_path/'out';corpus=CORPUS;extra=[]
    if error=='bad-argument':extra=['--arbitrary-callback','PASS']
    elif error=='missing-corpus':corpus=tmp_path/'missing'
    elif error=='existing-output':output.mkdir()
    else:
        corpus=tmp_path/'model';shutil.copytree(CORPUS,corpus)
        (corpus/'sources/profile.json').write_bytes(b'{}')
    process=subprocess.run([sys.executable,str(root/'scripts/development/replay_independent_genesis.py'),'--corpus',str(corpus),'--mode','synthetic-model','--output',str(output),*extra],cwd=root,env={'PYTHONPATH':str(root/'src'),'PYTHONDONTWRITEBYTECODE':'1','PATH':'/usr/bin:/bin'},capture_output=True,text=True,timeout=60)
    assert process.returncode==(1 if error=='known-FAIL' else 3),process.stderr+process.stdout
    if error=='known-FAIL':assert json.loads((output/'result.json').read_bytes())['overall']=='FAIL'

@pytest.mark.parametrize('layer',['public','legacy'])
def test_existing_full_final_entry_cannot_promote_local_valid_without_independent_basis(monkeypatch,layer):
    """Negative boundary only: local statuses are stubs, never model positive evidence."""
    from types import SimpleNamespace
    from forecast_trust_core import claim_authority_v1 as public
    from forecast_trust_core import claim_authority_v1_legacy as legacy
    from forecast_trust_core.core import Validation,Result
    acceptance=json.loads((CORPUS/'evidence/complete-initial-acceptance.json').read_bytes())
    subject={k:acceptance[k] for k in ('object_id','content_sha256')}
    monkeypatch.setattr(legacy,'_require_live_wall_inputs',lambda *a:None)
    monkeypatch.setattr(legacy,'_require_live_bitcoin_inputs',lambda *a:None)
    if layer=='public':
        monkeypatch.setattr(public._gate,'validate_wall_inputs',lambda *a:None)
        monkeypatch.setattr(public,'_validate_bitcoin_inputs_for_recomputation',lambda *a:None)
        monkeypatch.setattr(public._gate,'validate_strong_report',lambda *a:None)
        monkeypatch.setattr(legacy,'validate_final_genesis_acceptance_authoritatively',lambda *a,**k:(Validation(Result.VALID,()),(),{}))
        result=public.validate_final_genesis_acceptance_authoritatively(acceptance,final_evidence_subject_ref=subject,wall_clock_inputs={},bitcoin_inputs={})
    else:
        original=legacy._exact_ref
        def exact(obj,*,object_type=None):
            return dict(subject) if object_type=='ExternalTimeEvidenceBundle' else original(obj,object_type=object_type)
        monkeypatch.setattr(legacy,'_exact_ref',exact)
        monkeypatch.setattr(legacy,'recompute_external_existence_claim_authoritatively',lambda *a,**k:SimpleNamespace(external_existence_claim={'state':'VERIFIED'},deadline_existence_claim={'state':'NOT_APPLICABLE'}))
        monkeypatch.setattr(legacy,'recompute_bitcoin_durability_claim_authoritatively',lambda *a,**k:SimpleNamespace(bitcoin_durability_claim={'state':'VERIFIED'},strong_verification_report={}))
        result=legacy.validate_final_genesis_acceptance_authoritatively(acceptance,final_evidence_subject_ref=subject,wall_clock_inputs={'bundle':{}},bitcoin_inputs={'bundle':{}})
    assert result[0].result==Result.INELIGIBLE_TRUST_UNKNOWN and not result[0].valid
    assert any(c.reason_code=='INDEPENDENT_INITIAL_BASIS_NOT_ESTABLISHED' for c in result[0].checks)

@pytest.mark.parametrize('layer',['public','legacy'])
@pytest.mark.parametrize('status',['UNKNOWN','FAIL'])
def test_persisted_full_final_comparison_does_not_discard_inner_gate(monkeypatch,layer,status):
    """Negative equality boundary: matching/cache labels cannot replace actual validation."""
    from forecast_trust_core import claim_authority_v1 as public
    from forecast_trust_core import claim_authority_v1_legacy as legacy
    from forecast_trust_core.core import Validation,Result,Check
    module=public if layer=='public' else legacy
    inner=Validation(Result.INVALID if status=='FAIL' else Result.INELIGIBLE_TRUST_UNKNOWN,(Check('inner',status,'INNER_'+status),))
    monkeypatch.setattr(module,'validate_final_genesis_acceptance_authoritatively',lambda *a,**k:(inner,(),{}))
    monkeypatch.setattr(legacy,'build_validation_report_v2',lambda *a,**k:{'model_boundary':'comparison_only'})
    monkeypatch.setattr(legacy,'compare_persisted_validation_report_to_recomputed',lambda *a,**k:Validation(Result.VALID,()))
    validator=MODEL_SOURCE_REFS['profile']
    result=module.validate_persisted_final_acceptance_report_authoritatively({}, {},final_evidence_subject_ref=validator,wall_clock_inputs={'validator_contract_ref':validator},bitcoin_inputs={'validator_contract_ref':validator},trusted_manifest_ref=validator)
    assert result[0].result==inner.result and not result[0].valid
    assert any(c.reason_code=='INNER_'+status for c in result[0].checks)
