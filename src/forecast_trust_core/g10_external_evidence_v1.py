"""Finite keyless M1 external replay. No public protocol authority or network."""
from dataclasses import dataclass,replace
from copy import deepcopy
from pathlib import Path
import platform,sys
from .authority_primitives_v1 import ExactRef,resolve_exact,AuthorityPrimitiveError
from .canonical import canonical_json,sha256_hex
from .core import Check
from . import canonical,_roughtime_support,claim_authority_v1_legacy
from . import external_model_engine_v1 as engine
from .external_model_pins_v1 import MODEL_EXTERNAL_REFS,MODEL_EXTERNAL_CONTEXTS,MODEL_EXTERNAL_ALL_REFS,MODEL_EXTERNAL_RUNTIME,MODEL_EXTERNAL_ENGINE_SHA256
from .scientific_model_pins_v1 import MODEL_SCIENTIFIC_REFS,MODEL_SCIENTIFIC_RAW_REFS
from .scientific_model_engine_v1 import measurement_rows,Unavailable as ScientificUnavailable
from .calendar_model_v1 import MODEL_CYCLE_SUBMISSION_REFS
from .replay_model_v1 import MODEL_SOURCE_REFS
from .g10_requirements_v1 import _fixed_basis,reconstruct_requirements
from .qualification_scope_v1 import consume_model_admissions
from .replay_records_v1 import NativeReplay,emit_records,reduce_checks
from .architecture_compression_v1_hardening import derive_deadline_existence_claim_strict,derive_pre_outcome_durability_claim_strict

SEAMS=('CRYPTO_WIRE_AND_DELEGATION_AUTH','CSPRNG_CHALLENGE_ORIGIN','RETAINED_TIMEOUT_OBSERVATIONS','COMPLETE_HISTORY_PRECOMMITMENT','BITCOIN_HEAD_AND_POW_TRUST','SOURCE_AUTH_AND_AVAILABILITY','INITIAL_AUTH_NO_FORMULA')
EVENT_NAMES=('final-acceptance',)+tuple(k+'-'+n for k in ('plan','cycle','dvr') for n in ('t1','t2','t3'))
MEASUREMENT_CHECKS=('retrospective_raw_identity','retrospective_source_vintage','retrospective_parser_replay','retrospective_origin')
@dataclass(frozen=True)
class ExternalEvent:
    name:str
    input_refs:dict
    raw_inputs:dict
    independent_context:dict
    checks:tuple
    trace:dict
    overall:str
    provider_order:tuple=('p1','p2','p3')
    fresh_execution:bool=False
@dataclass(frozen=True)
class MeasurementReplay:
    target_name:str
    input_refs:tuple
    checks:tuple
    raw_inputs:dict
@dataclass(frozen=True)
class ExternalReplay:
    events:tuple
    measurements:tuple
    checks:tuple
    records:tuple
    overall:str
    input_refs:tuple
    seams:tuple=SEAMS
    model_only:bool=True
    prospective_eligible:bool=False
    real_genesis_readiness:str='NOT_ESTABLISHED'
    protocol_state_change:str='NONE'

def observed_runtime():
    return {'python':platform.python_version(),'executable_sha256':sha256_hex(Path(sys.executable).read_bytes()),**{m.__name__.split('.')[-1]+'_sha256':sha256_hex(Path(m.__file__).read_bytes()) for m in (canonical,_roughtime_support,claim_authority_v1_legacy)}}
def fresh_model_execution(inputs,context):return engine.evaluate_external_event(inputs,context)
def _check(name,value,reason):return Check(name,'UNKNOWN' if value is None else 'PASS' if value else 'FAIL',reason)
def _claim(kind,subject,status,upper=None):
    # Internal model-only arithmetic adapter, populated solely by current execution.
    o={'claim_type':kind,'subject_ref':subject,'state':'VERIFIED' if status=='PASS' else 'FAILED' if status=='FAIL' else 'UNRESOLVED'}
    if upper is not None:o['verified_upper_bound']=upper
    return o

def replay_external_evidence(basis,cycles,qualifications,scientific,resolver):
    refs=set();checks=[];events=[];measurements=[]
    def read(reference,local):
        rr=ExactRef.from_mapping(reference) if isinstance(reference,dict) else reference;refs.add(rr)
        try:return resolve_exact(rr,resolver)
        except AuthorityPrimitiveError as exc:local.append(Check('external-exact-input','UNKNOWN' if str(exc)=='NO_AUTHORITATIVE_RESULT' else 'FAIL',str(exc)))
        except Exception as exc:local.append(Check('external-exact-input','UNKNOWN','MODEL_EXTERNAL_RESOLVER_UNAVAILABLE_'+type(exc).__name__))
        return None
    def rawread(reference,local):
        rr=ExactRef.from_mapping(reference);refs.add(rr)
        try:
            b=resolver.resolve_exact(rr)
            if b is None:local.append(Check('external-raw','UNKNOWN','MODEL_EXTERNAL_RAW_UNAVAILABLE'));return None
            if not isinstance(b,bytes) or sha256_hex(b)!=rr.content_sha256:local.append(Check('external-raw','FAIL','MODEL_EXTERNAL_RAW_HASH_INVALID'));return None
            return b
        except Exception as exc:local.append(Check('external-raw','UNKNOWN','MODEL_EXTERNAL_RAW_UNAVAILABLE_'+type(exc).__name__));return None
    if basis!=_fixed_basis():
        return ExternalReplay((),(),(Check('external-model-profile','UNKNOWN','PUBLIC_EXTERNAL_EVIDENCE_NOT_ESTABLISHED'),),(),'UNKNOWN',())
    requirements=reconstruct_requirements(basis,resolver)
    checks.extend((Check('external-requirements',requirements.overall,'EXTERNAL_REQUIREMENTS_UNIVERSE'),Check('external-cycles',cycles.overall,'EXTERNAL_CYCLE_UNIVERSE'),Check('external-scientific',scientific.overall,'EXTERNAL_SCIENTIFIC_CAPABILITY')))
    contract=read(MODEL_EXTERNAL_ALL_REFS['contract'],checks)
    policy=read(MODEL_EXTERNAL_ALL_REFS['retained-quorum-v3'],checks)
    checks.append(_check('external-quorum-contract',None if contract is None or policy is None else contract['quorum_policy_ref']==engine.ref(policy) and contract['providers']==['p1','p2','p3'] and contract['threshold']==2 and contract['assumptions']==list(SEAMS) and contract['cost']=='ZERO_RECURRING_CASH_COST' and contract['network']=='OFFLINE_ONLY','FIXED_V3_MODEL_CLAUSE_ACCOUNTING'))
    try:checks.append(_check('external-runtime',observed_runtime()==MODEL_EXTERNAL_RUNTIME and sha256_hex(Path(engine.__file__).read_bytes())==MODEL_EXTERNAL_ENGINE_SHA256,'MODEL_EXTERNAL_RUNTIME_IDENTITY'))
    except Exception as exc:checks.append(Check('external-runtime','UNKNOWN','MODEL_EXTERNAL_RUNTIME_UNAVAILABLE_'+type(exc).__name__))
    submissions={};native={}
    for n in ('t1','t2','t3'):
        submissions[n]=read(MODEL_CYCLE_SUBMISSION_REFS[n],checks);native[n]={}
        if submissions[n]:
            for k in ('plan','manifest','slot','target','issued'):native[n][k]=read(submissions[n]['records'][k],checks)
    previous=None
    for name in EVENT_NAMES:
        local=[];mapping={k:ExactRef.from_mapping(v) for k,v in MODEL_EXTERNAL_REFS[name].items()}
        objects={k:read(v,local) for k,v in mapping.items()}
        context=deepcopy(MODEL_EXTERNAL_CONTEXTS[name]);raws={}
        for k,v in context['raw_refs'].items():raws[v['object_id']]=rawread(v,local)
        inputs={'objects':objects,'raw':raws}
        # Exact independent pre/post history roots are retained even if a packet fails.
        before=objects.get('retry_before');after=objects.get('retry_after')
        continuity=None if before is None or after is None or name!=EVENT_NAMES[0] and previous is None else before['root_ref']==basis.root_ref.to_dict() and after['root_ref']==basis.root_ref.to_dict() and before['predecessor_ref']==context['previous_retry_ref'] and after['predecessor_ref']==mapping['retry_before'].to_dict() and (before['providers']==previous['providers'] if previous is not None else before['providers']=={p:{'failures':0,'retry_not_before_ns':'0'} for p in ('p1','p2','p3')})
        local.append(_check('external-retry-history',continuity,'INDEPENDENT_COMPLETE_RETRY_HISTORY'))
        previous=after
        subject=objects.get('subject')
        if name=='final-acceptance':
            detached=objects.get('full_authentication')
            binding=None if subject is None or detached is None else subject['object_type']=='ManifestAcceptance' and detached['subject_ref']==mapping['subject'].to_dict() and detached['whole_canonical_sha256']==sha256_hex(canonical_json(subject)) and detached['contract_ref']==MODEL_EXTERNAL_ALL_REFS['contract'] and detached['root_ref']==basis.root_ref.to_dict() and detached['actor']=='MODEL_OWNER' and detached['action']=='INITIAL_ACCEPT' and detached['assumption']=='INITIAL_AUTH_NO_FORMULA' and subject['candidate_manifest_ref']==basis.subject.to_dict()
            local.append(_check('final_full_signed_subject',binding,'MODEL_WHOLE_SA_AUTH_NO_FORMULA'))
        else:
            kind,n=name.split('-',1);plan=native[n].get('plan');manifest=native[n].get('manifest');target=native[n].get('target');slot=native[n].get('slot')
            binding=None if subject is None or plan is None or manifest is None or target is None or slot is None else context['frozen_cutoff']==plan['plan_commitment_deadline' if kind=='plan' else 'external_proof_deadline'] and (engine.ref(subject)==engine.ref(plan if kind=='plan' else manifest) if kind!='dvr' else subject['stage']=='PRE_OUTCOME_COMMITMENT' and subject['slot_ref']==engine.ref(slot) and subject['cycle_manifest_ref']==engine.ref(manifest) and subject['issued_ref']==submissions[n]['records']['issued'] and subject['scientific_run_ref']==MODEL_SCIENTIFIC_REFS[n]['run'] and subject['outcome_barrier']==target['outcome_information_barrier'] and subject['origin']=='SYNTHETIC_ONLY' and subject['contains_outcome'] is False)
            local.append(_check('external-subject-boundary',binding,'INDEPENDENT_PRIMARY_SUBJECT_DEADLINE'))
        boundary=next((b.ref for b in qualifications.boundaries if b.role==name and b.deadline==context['frozen_cutoff']),None)
        if boundary is None:local.append(Check('wall_historical_admission','UNKNOWN','QUALIFICATION_BOUNDARY_UNAVAILABLE'))
        else:local.extend(consume_model_admissions(qualifications,('p1','p2','p3'),boundary))
        try:
            current,trace=fresh_model_execution(inputs,context)
            if not isinstance(current,tuple) or len(current)!=len(engine.WALL_CHECKS) or {c.check_id for c in current}!=set(engine.WALL_CHECKS) or not isinstance(trace,dict) or trace.get('model_only') is not True:raise ValueError('incomplete external execution')
            local.extend(current)
        except Exception as exc:
            local.extend(Check(k,'UNKNOWN','MODEL_EXTERNAL_EXECUTION_UNAVAILABLE_'+type(exc).__name__) for k in engine.WALL_CHECKS);trace={'fresh_execution':False,'upper_bound':None,'model_only':True}
        # Native exact-subject deadline arithmetic operates only inside the model lane.
        status=reduce_checks(local);base=_claim('EXTERNAL_EXISTENCE_BOUND_VERIFIED',context['subject_ref'],status,trace.get('upper_bound'))
        if name!='final-acceptance':
            try:
                deadline=derive_deadline_existence_claim_strict(context['subject_ref'],external_existence_claim=base,frozen_deadline=context['frozen_cutoff'])
                local.append(Check('external-native-deadline', 'PASS' if deadline['state']=='VERIFIED' else 'FAIL' if status=='FAIL' else 'UNKNOWN','MODEL_NATIVE_DEADLINE_ARITHMETIC'))
                trace['deadline_claim']=deadline
            except Exception as exc:local.append(Check('external-native-deadline','UNKNOWN','MODEL_NATIVE_DEADLINE_UNAVAILABLE_'+type(exc).__name__))
        else:
            trace['governance_only']=bool(binding is True and contract and contract['applicability']['final-acceptance']=={'forecast_deadline':'NOT_APPLICABLE','pre_outcome':'NOT_APPLICABLE','scientific_checks':'NOT_APPLICABLE'})
        events.append(ExternalEvent(name,mapping,inputs,context,tuple(local),trace,reduce_checks(local),fresh_execution=trace.get('fresh_execution') is True))
    # Independently fixed three retained historical raw captures; never directory counts.
    for n in ('t1','t2','t3'):
        local=[];cr=MODEL_SCIENTIFIC_REFS[n]['baseline'];rr=MODEL_SCIENTIFIC_RAW_REFS[n+'-baseline'];capture=read(cr,local);b=rawread(rr,local)
        data={'objects':{'baseline':capture},'raw':{rr['object_id']:b}}
        status=reduce_checks(local) if local else 'PASS'
        try:
            rows=measurement_rows(data,['baseline']);row=rows[0]
            semantic={'retrospective_raw_identity':capture['raw_ref']==rr,'retrospective_source_vintage':capture['source_contract_ref']==MODEL_SOURCE_REFS['measurement-'+n] and row['target_family']==n and row['reference_period']=='2029-12' and row['release_stage']=='FIRST','retrospective_parser_replay':True,'retrospective_origin':row['origin']=='RETROSPECTIVE_FIXTURE' and capture['authentication']=='EXPLICIT_MODEL_SOURCE_AUTH_SEAM'}
            local.extend(_check(k,v,'MODEL_'+k.upper()) for k,v in semantic.items())
        except ScientificUnavailable:local.extend(Check(k,'UNKNOWN','MODEL_RETROSPECTIVE_RAW_UNAVAILABLE') for k in MEASUREMENT_CHECKS)
        except Exception:local.extend(Check(k,'FAIL' if status!='UNKNOWN' else 'UNKNOWN','MODEL_RETROSPECTIVE_PARSER_INVALID') for k in MEASUREMENT_CHECKS)
        measurements.append(MeasurementReplay(n,(ExactRef.from_mapping(cr),ExactRef.from_mapping(rr)),tuple(local),data))
    prechecks=[]
    for n in ('t1','t2','t3'):
        cycle=next(e for e in events if e.name=='cycle-'+n);dvr=next(e for e in events if e.name=='dvr-'+n)
        dvrsub=dvr.raw_inputs['objects']['subject'];target=native[n].get('target')
        if target is None:
            bindingchecks=(Check('dvr_exact_replay_bindings','UNKNOWN','MODEL_X04_BARRIER_UNAVAILABLE'),)
        else:
            bindingchecks=engine.evaluate_preoutcome_binding(dvrsub,cycle.raw_inputs,cycle.independent_context,
                frozen_barrier=target['outcome_information_barrier'],dvr_upper_bound=dvr.trace.get('upper_bound'))
        prechecks.extend(bindingchecks)
        status=reduce_checks(cycle.checks+dvr.checks+bindingchecks)
        try:
            claim=derive_pre_outcome_durability_claim_strict(cycle.independent_context['subject_ref'],bitcoin_durability_claim=_claim('BITCOIN_DURABILITY_VERIFIED',cycle.independent_context['subject_ref'],status),durability_record_deadline_claim=dvr.trace.get('deadline_claim'),durability_record_subject_ref=dvr.independent_context['subject_ref'],durability_record_bound_subject_ref=None if dvrsub is None else dvrsub['cycle_manifest_ref'])
            prechecks.append(Check('scientific_preoutcome','PASS' if claim['state']=='VERIFIED' else 'FAIL' if status=='FAIL' else 'UNKNOWN','MODEL_NATIVE_DVR_EXACT_CONJUNCTION'))
        except Exception as exc:prechecks.append(Check('scientific_preoutcome','UNKNOWN','MODEL_DVR_UNAVAILABLE_'+type(exc).__name__))
    allchecks=tuple(checks)+tuple(c for e in events for c in e.checks)+tuple(c for m in measurements for c in m.checks)+tuple(prechecks)
    refs=tuple(sorted(refs,key=lambda r:(r.object_id,r.content_sha256)))
    # All outer profile/universe checks remain consequential for every owned row.
    native={k:NativeReplay(tuple(checks)+tuple(c for e in events for c in e.checks if c.check_id==k or c.check_id not in engine.WALL_CHECKS),refs,True) for k in engine.WALL_CHECKS}
    native['wall_historical_admission']=NativeReplay(tuple(checks)+tuple(c for e in events for c in e.checks if c.check_id.startswith('consumer-') or c.check_id=='wall_historical_admission'),refs,True)
    native.update({k:NativeReplay(tuple(checks)+tuple(c for m in measurements for c in m.checks),refs,True) for k in MEASUREMENT_CHECKS})
    native['scientific_preoutcome']=NativeReplay(tuple(checks)+tuple(prechecks),refs,True)
    native['final_full_signed_subject']=NativeReplay(tuple(checks)+events[0].checks,refs,True)
    native['final_wall_bitcoin_same_bundle']=NativeReplay(tuple(checks)+events[0].checks,refs,True)
    try:
        records=emit_records(requirements,native,__file__)
        wanted={k for r in requirements.requirements if r.check in native for k in r.keys}
        if not isinstance(records,tuple) or {r.key for r in records}!=wanted or len(records)!=len(wanted) or any(not r.raw_result or r.basis!=basis for r in records):raise ValueError('raw record coverage')
        final=events[0]
        if final.overall=='PASS' and final.trace.get('governance_only') is True:
            records=tuple(replace(r,normalized='NOT_APPLICABLE',applicability='NOT_APPLICABLE',exclusion_clause_ref=ExactRef.from_mapping(MODEL_EXTERNAL_ALL_REFS['contract']),exclusion_clause_location='/applicability/final-acceptance/forecast_deadline',exclusion_fact_refs=(final.input_refs['subject'],final.input_refs['full_authentication']),exclusion_result='PASS') if r.key.predicate_id=='P19' and r.key.role.endswith('#final-acceptance') else r for r in records)
    except Exception as exc:records=();allchecks+=(Check('external-raw-records','UNKNOWN','MODEL_EXTERNAL_RAW_RECORDS_UNAVAILABLE_'+type(exc).__name__),)
    return ExternalReplay(tuple(events),tuple(measurements),allchecks,records,reduce_checks(allchecks),refs)
