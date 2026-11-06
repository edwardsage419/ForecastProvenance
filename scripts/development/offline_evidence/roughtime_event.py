"""One retained nonforecast event. No network, native execution or authority."""
import base64
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CATALOG_PATH='scripts/development/offline_evidence/roughtime_event_inputs.json'
CATALOG_IDENTITY={'bytes':16734,'sha256':'f31555ba9edc34adae241f7736d1990d48de57fe50b06fa9b832dcea6c3df9b9'}
SUPPORT='docs/development/first-nonforecast-roughtime-execution-2026-10-27-rev-001/'


def consume(directory=ROOT, *, source_root=ROOT, reader=None):
    if reader is None:
        reader=ModuleType('fp_nonforecast_passive_reader');reader.__file__=str(HERE/'worker.py')
        exec(compile((HERE/'worker.py').read_bytes(),reader.__file__,'exec'),reader.__dict__)
    result={'status':'MISSING','scope':'D241_EXACT_NON_FORECAST_EVENT_AND_RETAINED_OFFLINE_AUDIT_ONLY',
            'findings':[],'raw_event_binding_match':False,'native_reverification_executed':False,
            'independent_complete_history':False,'provider_qualification':'NOT_ESTABLISHED',
            'project_forecast_time_evidence':'NOT_ESTABLISHED','independent_control_domains':'NOT_ESTABLISHED',
            'transport_is_local_observation_only':True,'prospective_eligible':False,
            'real_admission':'NOT_READY','protocol_state_change':'NONE'}
    def read(base,path,record):
        try:
            try:Path(base).lstat()
            except FileNotFoundError:raise reader.OfflineFailure('MISSING_INPUT','MISSING')
            except OSError:raise reader.OfflineFailure('UNREADABLE_INPUT','MISSING')
            return reader.read_fixed(base,path,record)
        except reader.OfflineFailure as error:
            result['findings'].append({'item':path,'status':error.status,'error':error.code})
            return None
    def finish():
        result['status']=('REJECTED' if any(f['status']=='REJECTED' for f in result['findings'])
                          else 'MISSING' if result['findings'] else 'OBSERVED')
        return result
    catalog_raw=read(source_root,CATALOG_PATH,CATALOG_IDENTITY)
    if catalog_raw is None:return finish()
    catalog=json.loads(catalog_raw)
    inputs={row['path']:read(directory,row['path'],row) for row in catalog['inputs']}
    sources={Path(row['path']).stem:(row['path'],read(source_root,row['path'],row)) for row in catalog['sources']}
    result['input_count']=len(inputs)
    if result['findings']:return finish()
    # Temporarily install only the captured dependency closure, with no package
    # initializer/fallback. Restore the original product namespace on every exit.
    sentinel=object();keys=['forecast_trust_core',*['forecast_trust_core.'+n for n in sources]]
    original={key:sys.modules.get(key,sentinel) for key in keys}
    package=ModuleType('forecast_trust_core');package.__path__=[]
    loaded={};sys.modules['forecast_trust_core']=package
    def require(condition,code):
        if not condition:raise ValueError(code)
    try:
        for name,(path,raw) in sources.items():
            module=ModuleType('forecast_trust_core.'+name);module.__package__='forecast_trust_core'
            module.__file__=str(Path(source_root)/path);sys.modules[module.__name__]=module
            exec(compile(raw,module.__file__,'exec'),module.__dict__);loaded[name]=module
        canonical=loaded['canonical'];control=loaded['_roughtime_control'];prefix=catalog['event_prefix']
        def parsed(path):return canonical.parse_json_strict(inputs[path])
        def event(name):return parsed(prefix+name)
        plan,auth,profile,before,after,report,trace=[event(name) for name in (
            'plan.json','authorization.json','verifier-build-profile.json','retry-state-before.json',
            'retry-state-after.json','report.json','execution-transcript.json')]
        loaded['_roughtime_plan'].validate_authorization_record(auth,plan)
        loaded['_roughtime_report'].validate_rehearsal_report(report,plan=plan,authorization=auth)
        control.validate_report_control_binding(report,plan,auth,profile,before,after)
        require(auth['authorization_sha256']==catalog['auth_sha256'],'AUTHORIZATION_BINDING_MISMATCH')
        trace_core={k:v for k,v in trace.items() if k!='execution_transcript_sha256'}
        require(hashlib.sha256(canonical.canonical_json(trace_core)).hexdigest()==trace['execution_transcript_sha256']
                ==report['execution_transcript_sha256'],'EXECUTION_TRANSCRIPT_MISMATCH')
        proof=parsed(SUPPORT+'OFFLINE_REPLAY.json')
        require(proof['authorization_sha256']==auth['authorization_sha256']
                and proof['report_content_sha256']==report['content_sha256']
                and proof['after_state_sha256']==after['state_sha256']
                and proof['execution_transcript_sha256']==trace['execution_transcript_sha256'],
                'RETAINED_AUDIT_SUBJECT_MISMATCH')
        observed=[];failures=[];sent=0;outbound=0;timeouts=0;state=before;positive=[]
        for provider,row in zip(plan['providers'],report['provider_results']):
            require(provider['provider_id']==row['provider_id'],'PROVIDER_ORDER_MISMATCH')
            root_hash=hashlib.sha256(base64.b64decode(provider['root_public_key_base64'],validate=True)).hexdigest()
            previous_request=None
            for attempt in row['attempts']:
                relative=prefix+'providers/'+provider['provider_id']+'/attempt-'+str(attempt['attempt_number'])+'/'
                request=inputs[relative+'request.bin'];transport=parsed(relative+'transport.json')
                require(len(request)==1036 and hashlib.sha256(request).hexdigest()==attempt['request_sha256']
                        ==inputs[relative+'request.sha256'].decode().strip()
                        and base64.b64decode(attempt['request_base64'],validate=True)==request,'RAW_REQUEST_MISMATCH')
                require(previous_request is None or request==previous_request,'RETRY_REQUEST_CHANGED')
                previous_request=request
                reserved=parsed(relative+'retry-state-reserved.json')
                root=next(s for s in reserved['root_states'] if s['root_public_key_sha256']==root_hash)
                state=control.record_failure(state,root_hash,root['last_failure_unix_ms'])
                require(state==reserved,'RESERVED_STATE_MISMATCH')
                require(transport['sent'] is True and transport['expected_host']==provider['host']
                        and transport['expected_port']==provider['port'],'TRANSPORT_RECORD_MISMATCH')
                sent+=1;outbound+=len(request)
                if attempt['outcome']=='QUALIFYING_VERIFIED_RESPONSE':
                    response=inputs[relative+'response.bin'];verification=parsed(relative+'verification.json')
                    receipt=row['receipt']
                    require(transport['transport_status']=='RESPONSE'
                            and base64.b64decode(attempt['response_base64'],validate=True)==response
                            and hashlib.sha256(response).hexdigest()==attempt['response_sha256']
                            ==inputs[relative+'response.sha256'].decode().strip(),'RAW_RESPONSE_MISMATCH')
                    require(hashlib.sha256(canonical.canonical_json(verification)).hexdigest()
                            ==receipt['verification_transcript_sha256'],'VERIFICATION_TRANSCRIPT_MISMATCH')
                    positive.append({'provider_id':provider['provider_id'],'response_sha256':attempt['response_sha256'],
                                     'midpoint_utc':verification['midpoint_utc'],
                                     'radius_nanoseconds':verification['radius_nanoseconds'],
                                     'native_replay_equal_retained_transcript':True})
                    observed.append(provider['provider_id']);state=control.reset_root_state(state,root_hash)
                else:
                    require(attempt['failure_code']=='TRANSPORT_TIMEOUT' and transport['transport_status']=='TIMEOUT'
                            and relative+'response.bin' not in inputs,'TIMEOUT_RECORD_MISMATCH')
                    timeouts+=1;failures.append({'provider_id':provider['provider_id'],
                                               'attempt':attempt['attempt_number'],'failure_code':'TRANSPORT_TIMEOUT'})
        require(state==after,'AFTER_STATE_MISMATCH')
        require(proof['native_positive_replays']==positive and proof['local_sent_datagrams']==sent
                and proof['outbound_application_payload_bytes']==outbound,'RETAINED_NATIVE_AUDIT_MISMATCH')
        require(sent==4 and len(observed)==2 and timeouts==2,'EXACT_EVENT_COUNTS_MISMATCH')
        base=prefix.split('/run-evidence/events/')[0]
        consumed=parsed(base+'/run-evidence/consumed/'+auth['authorization_sha256']+'.json')
        launch=parsed(base+'/LAUNCH_RESULT.json')
        require(consumed['authorization_sha256']==auth['authorization_sha256']
                and launch['authorization_sha256']==auth['authorization_sha256']
                and launch['exit_code']==0 and launch['automatic_retry'] is False,'UNIQUE_EXECUTION_BINDING_MISMATCH')
        result.update(raw_event_binding_match=True,local_send_records=sent,outbound_application_payload_bytes=outbound,
                      retained_verified_responses=len(observed),verified_response_provider_ids=observed,
                      timeout_attempts=timeouts,retained_failures=failures,
                      retry_state_after_sha256=after['state_sha256'],
                      verifier_build_profile_sha256=profile['profile_sha256'],
                      report_ref={'object_id':report['object_id'],'content_sha256':report['content_sha256']},
                      retained_native_validation='EXACT_RECORDED_AUDIT_MATCHED_NOT_REEXECUTED',
                      authorization='EXACT_ONE_EVENT_ALREADY_CONSUMED_NO_NEW_NETWORK_PERMISSION')
    except (ValueError,TypeError,KeyError,ImportError,OSError,StopIteration):
        result['findings'].append({'item':'event-content','status':'REJECTED','error':'EVENT_CONTENT_OR_BINDING_REJECTED'})
    finally:
        for key,value in original.items():
            if value is sentinel:sys.modules.pop(key,None)
            else:sys.modules[key]=value
    return finish()


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description='Read one exact retained NON_FORECAST event; no native/network or real readiness.')
    parser.add_argument('--inputs',type=Path,help='mirror root containing fixed repository-relative public inputs; no fallback')
    args=parser.parse_args()
    passive=ModuleType('fp_nonforecast_entry_reader');passive.__file__=str(HERE/'worker.py')
    exec(compile((HERE/'worker.py').read_bytes(),passive.__file__,'exec'),passive.__dict__)
    sys.addaudithook(passive.audit_policy)
    report=consume(args.inputs if args.inputs is not None else ROOT,reader=passive)
    print(json.dumps(report,ensure_ascii=False,sort_keys=True))
    raise SystemExit(0 if report['status']=='OBSERVED' else 2 if report['status']=='REJECTED' else 1)
