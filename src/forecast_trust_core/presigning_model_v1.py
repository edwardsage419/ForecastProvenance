"""Past-only model report formation. Times are explicit synthetic assumptions.

Pre-signing checks never consume final acceptance or later completeness facts.
The final chronology conjunction separately compares model formation intervals
with the freshly computed existence upper bound; that bound is not signed_at.
"""
from .authority_primitives_v1 import ExactRef
from .core import Check
from .integration_model_v1 import read,check
from .qualification_scope_v1 import _read_raw,ModelAdmission,recheck_model_admission
from .qualification_model_engine_v1 import execute_model_qualification_validation
from .qualification_model_pins_v1 import MODEL_QUALIFICATION_CONTRACT_REF
from .replay_model_v1 import MODEL_SOURCE_REFS
from .replay_records_v1 import NativeReplay,reduce_checks
from .canonical import require_utc_timestamp

MODEL_PRE_SIGNING_RULE = {
    'formation_as_of_utc':'2030-01-01T00:00:00Z',
    'report_as_of_utc':'2030-01-31T21:00:00Z',
    'reports_available_at':'2030-01-31T21:30:00Z',
    'copies_available_at':'2030-01-31T22:00:00Z',
    'signing_not_before':'2030-01-31T22:30:00Z',
    'signing_not_after':'2030-01-31T22:31:00Z',
    'signing_formed_at':'2030-01-31T22:30:30Z',
}

def _rule(basis,resolver,checks):
    from .integration_model_pins_v1 import MODEL_INTEGRATION_REFS
    rule=read(MODEL_INTEGRATION_REFS['presign-chronology'],resolver,checks)
    checks.append(check('presign-fixed-chronology',None if rule is None else
        all(rule.get(k)==v for k,v in MODEL_PRE_SIGNING_RULE.items()) and
        rule.get('manifest_ref')==basis.subject.to_dict() and rule.get('real_authority') is False,
        'INDEPENDENT_PRE_SIGNING_CHRONOLOGY'))
    return rule

def replay_presigning_qualification(basis,requirements,resolver):
    from .integration_model_pins_v1 import MODEL_PRESIGN_QUALIFICATION,MODEL_INTEGRATION_REFS
    history=[];admission=[];refs=[]
    rule=_rule(basis,resolver,history)
    scope=read(MODEL_INTEGRATION_REFS['presign-qualification-scope'],resolver,history)
    refs.extend(ExactRef.from_mapping(MODEL_INTEGRATION_REFS[n]) for n in ('presign-chronology','presign-qualification-scope'))
    refs.append(ExactRef.from_mapping(MODEL_QUALIFICATION_CONTRACT_REF))
    history.append(check('presign-scope',None if scope is None else
        scope.get('providers')==MODEL_PRESIGN_QUALIFICATION and scope.get('contains_future_observations') is False and
        scope.get('report_as_of_utc')==MODEL_PRE_SIGNING_RULE['report_as_of_utc'] and
        scope.get('chronology_contract_ref')==MODEL_INTEGRATION_REFS['presign-chronology'],
        'INDEPENDENT_COMPLETE_PAST_PRE_SIGNING_HISTORY_SCOPE'))
    source_scope=requirements.source_objects.get(MODEL_SOURCE_REFS['scope']['object_id'])
    history.append(check('formation-boundary',None if source_scope is None else
        any(x['name']=='formation' and x['boundary']==MODEL_PRE_SIGNING_RULE['formation_as_of_utc'] for x in source_scope['qualification_boundaries']),
        'INDEPENDENT_FORMATION_REPORT_BOUNDARY'))
    for provider in ('p1','p2','p3'):
        for role in ('formation','pre-signing'):
            pins=MODEL_PRESIGN_QUALIFICATION[provider][role];local=[]
            refs.extend(ExactRef.from_mapping(pins[n]) for n in ('package_ref','invocation_ref','history_ref','decision_ref'))
            refs.extend(ExactRef.from_mapping(rr) for rr in pins['members'].values())
            package=read(pins['package_ref'],resolver,local)
            invocation=read(pins['invocation_ref'],resolver,local)
            selected_history=read(pins['history_ref'],resolver,local)
            expected_as_of=MODEL_PRE_SIGNING_RULE['formation_as_of_utc' if role=='formation' else 'report_as_of_utc']
            local.append(check('past-prefix-as-of',None if package is None or selected_history is None else
                package.get('as_of_utc')==selected_history.get('through_as_of_utc')==pins['as_of_utc']==expected_as_of,
                'PRE_SIGNING_PAST_PREFIX_EXACT_AS_OF'))
            if invocation is not None:
                local.append(check('presign-invocation',invocation['package_ref']==pins['package_ref'] and
                    invocation['history_ref']==pins['history_ref'] and invocation['contract_ref']==MODEL_QUALIFICATION_CONTRACT_REF and
                    invocation['role']==role and invocation['as_of_utc']==expected_as_of and invocation['boundary_ref']==pins['boundary_ref'] and
                    invocation['contains_future_observations'] is False,'INDEPENDENT_PRE_SIGNING_INVOCATION_BINDINGS'))
            members={}
            for name,rr in pins['members'].items():
                obj,raw,errors=_read_raw(ExactRef.from_mapping(rr),resolver);local.extend(errors)
                if obj is None:continue
                members[name]=raw
                try:
                    fields=('formed_at','reviewed_at','retrieved_at','observed_at','detected_at','effective_at','through_as_of_utc','as_of_utc')
                    for field in fields:
                        if field in obj:
                            require_utc_timestamp(obj[field])
                            local.append(check('past-member-'+field,obj[field]<=expected_as_of,'PRE_SIGNING_HISTORY_FUTURE_INPUT'))
                except (ValueError,TypeError):local.append(Check('past-member','FAIL','PRE_SIGNING_HISTORY_TIME_INVALID'))
            history.extend(local)
            if package and invocation and scope and rule and reduce_checks(history)=='PASS':
                try:
                    current=execute_model_qualification_validation(package,members,ExactRef.from_mapping(MODEL_QUALIFICATION_CONTRACT_REF),ExactRef.from_mapping(pins['invocation_ref']))
                    history.extend(current.checks)
                    original=ModelAdmission(provider,ExactRef.from_mapping(pins['boundary_ref']),expected_as_of,
                        ExactRef.from_mapping(MODEL_SOURCE_REFS['provider-'+provider]),ExactRef.from_mapping(pins['decision_ref']),
                        ExactRef.from_mapping(pins['history_ref']),ExactRef.from_mapping(MODEL_QUALIFICATION_CONTRACT_REF),
                        current.native_result,False,reduce_checks(current.checks),())
                    consumed=recheck_model_admission(original)
                    admission.append(Check('presign-admission',consumed.status,'PRESIGN_ACTUAL_NATIVE_ADMISSION'))
                except (ValueError,TypeError,KeyError):history.append(Check('presign-package','FAIL','PRESIGN_PACKAGE_INVALID'))
                except Exception as exc:history.append(Check('presign-package','UNKNOWN','PRESIGN_UNAVAILABLE_'+type(exc).__name__))
            else:admission.append(Check('presign-admission','UNKNOWN','PRESIGN_ADMISSION_UNAVAILABLE'))
    return tuple(history),tuple(admission),{'checks':tuple(history+admission),
        'scope_ref':MODEL_INTEGRATION_REFS['presign-qualification-scope'],'invocations':MODEL_PRESIGN_QUALIFICATION,
        'input_refs':tuple(dict.fromkeys(refs))}

def verify_presigning_chronology(basis,resolver,external,reports):
    from .integration_model_pins_v1 import MODEL_INTEGRATION_REFS
    from .external_model_pins_v1 import MODEL_EXTERNAL_ALL_REFS
    checks=[];rule=_rule(basis,resolver,checks)
    availability=read(MODEL_INTEGRATION_REFS['presign-report-availability'],resolver,checks)
    retention=read(MODEL_INTEGRATION_REFS['retention'],resolver,checks)
    signing=read(MODEL_INTEGRATION_REFS['signing-formation'],resolver,checks)
    checks.append(check('report-availability',None if availability is None else
        availability.get('manifest_ref')==basis.subject.to_dict() and availability.get('chronology_contract_ref')==MODEL_INTEGRATION_REFS['presign-chronology'] and
        availability.get('report_refs')=={role:MODEL_EXTERNAL_ALL_REFS['report-'+role] for role in reports} and
        availability.get('available_at')==MODEL_PRE_SIGNING_RULE['reports_available_at'], 'MODEL_REPORT_AVAILABILITY_INTERVAL'))
    checks.append(check('signing-formation',None if signing is None else
        signing.get('subject_ref')==MODEL_EXTERNAL_ALL_REFS['complete-initial-acceptance'] and
        signing.get('whole_authentication_ref')==MODEL_EXTERNAL_ALL_REFS['full-sa-auth'] and
        signing.get('chronology_contract_ref')==MODEL_INTEGRATION_REFS['presign-chronology'] and
        signing.get('assumption')=='MODEL_REPORT_AND_SIGNING_TIMES' and
        signing.get('formed_at')==MODEL_PRE_SIGNING_RULE['signing_formed_at'], 'MODEL_SIGNING_FORMATION_INTERVAL'))
    final=next((e for e in external.events if e.name=='final-acceptance'),None)
    upper=final.trace.get('upper_bound') if final and final.fresh_execution else None
    interval=None
    if rule and availability and retention and signing and upper is not None:
        try:
            timestamps=[rule[n] for n in MODEL_PRE_SIGNING_RULE]+[availability['available_at'],retention['pre_signing_retained_at'],signing['formed_at'],upper]
            for value in timestamps:require_utc_timestamp(value)
            interval=(rule['report_as_of_utc']<availability['available_at']<=retention['pre_signing_retained_at']==rule['copies_available_at']<
                rule['signing_not_before']<=signing['formed_at']<=rule['signing_not_after']<=upper and
                final.input_refs['subject'].to_dict()==signing['subject_ref'])
        except (ValueError,TypeError,KeyError):interval=False
    checks.append(check('signing-existence',interval,'MODEL_SIGNING_EXISTENCE_INTERVAL'))
    refs=tuple(ExactRef.from_mapping(MODEL_INTEGRATION_REFS[n]) for n in ('presign-chronology','presign-report-availability','retention','signing-formation'))
    if final:refs+=tuple(final.input_refs.values())
    return NativeReplay(tuple(checks),tuple(dict.fromkeys(refs)),True)
