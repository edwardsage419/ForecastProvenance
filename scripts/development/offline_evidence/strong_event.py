"""Finite D255 local receipt + D254 calculation; no Core/authority execution."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CATALOG_PATH='scripts/development/offline_evidence/strong_event_inputs.json'
CATALOG_IDENTITY={'bytes':11082,'sha256':'3f292d5b4437dd46569cb491cdfcb2ec866ad65e0328b0da1cc977cfc64eae7c'}

def sha(raw):return hashlib.sha256(raw).hexdigest()
def compact(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')

def passive_reader():
    reader=ModuleType('fp_strong_event_passive_reader');reader.__file__=str(HERE/'worker.py')
    exec(compile((HERE/'worker.py').read_bytes(),reader.__file__,'exec'),reader.__dict__)
    return reader

def consume(directory=ROOT,*,source_root=ROOT,reader=None):
    if reader is None:reader=passive_reader()
    result={'status':'MISSING','scope':'D255_LOCAL_PUBLIC_RECEIPT_AND_SEPARATE_D254_RETAINED_CALCULATION',
        'findings':[],'raw_input_and_wire_binding_match':False,'actual_D255_RPC_transport_replayed':False,
        'actual_owner_or_full_runtime_authenticated':False,'native_execution':False,
        'project_Strong':'NOT_ESTABLISHED','actual_policy_adoption':'NOT_ESTABLISHED',
        'authenticated_time':'NOT_ESTABLISHED','independent_complete_history':False,
        'prospective_eligible':False,'real_admission':'NOT_READY','protocol_state_change':'NONE'}
    def finish():
        result['status']='REJECTED' if any(f['status']=='REJECTED' for f in result['findings']) else 'MISSING' if result['findings'] else 'OBSERVED'
        return result
    def read(base,path,row):
        try:
            try:Path(base).lstat()
            except FileNotFoundError:raise reader.OfflineFailure('MISSING_INPUT','MISSING')
            except OSError:raise reader.OfflineFailure('UNREADABLE_INPUT','MISSING')
            return reader.read_fixed(base,path,row)
        except reader.OfflineFailure as error:
            result['findings'].append({'item':path,'status':error.status,'error':error.code});return None
    catalog_raw=read(source_root,CATALOG_PATH,CATALOG_IDENTITY)
    if catalog_raw is None:return finish()
    catalog=json.loads(catalog_raw);roles=catalog['roles']
    if len(catalog['inputs'])>128 or sum(row['bytes'] for row in catalog['inputs'])>32*2**20:
        result['findings'].append({'item':'catalog','status':'REJECTED','error':'FINITE_INPUT_LIMIT'});return finish()
    inputs={row['path']:read(directory,row['path'],row) for row in catalog['inputs']}
    result['input_count']=len(inputs)
    if result['findings']:return finish() # No captured code before ALL input admission.
    def raw(role):return inputs[roles[role]]
    def require(condition,code):
        if not condition:raise ValueError(code)
    package='fp_strong_event_math';names=('strong_inputs','ots_body','strong_core','core_cli','strong_candidate','canonical')
    keys=[package,*[package+'.'+n for n in names]];sentinel=object();old={k:sys.modules.get(k,sentinel) for k in keys}
    try:
        # Only the exactly pinned, previously reviewed artifact is parsed.
        require(raw('loaded_executable')==raw('artifact'),'EXECUTABLE_COPY_MISMATCH')
        values={}
        for node in ast.parse(raw('artifact')).body:
            if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id in {'ORDER','SOURCE_PACK','PROFILE'}:
                key=node.targets[0].id;require(key not in values,'EMBEDDED_DUPLICATE_ASSIGNMENT');values[key]=ast.literal_eval(node.value)
        order=values['ORDER'];pack=values['SOURCE_PACK'];profile=values['PROFILE']
        require(order==names[:5] and set(pack)==set(order) and set(profile['sources'])==set(order),'EMBEDDED_SOURCE_CLOSURE')
        require(json.loads(raw('runtime'))==profile,'PROFILE_COPY_MISMATCH')
        captured={}
        for name in order:
            source=bytes.fromhex(pack[name]['hex']);identity=profile['sources'][name]
            require(len(source)==identity['bytes'] and sha(source)==identity['sha256']==pack[name]['sha256'],'EMBEDDED_SOURCE_IDENTITY')
            captured[name]=source
        captured['canonical']=raw('canonical')
        namespace=ModuleType(package);namespace.__path__=[];sys.modules[package]=namespace;loaded={}
        for name in names:
            module=ModuleType(package+'.'+name);module.__package__=package;module.__file__='captured-public-source:'+name
            sys.modules[module.__name__]=module;exec(compile(captured[name],module.__file__,'exec'),module.__dict__);loaded[name]=module
        parse=loaded['ots_body']._service_json
        canonical=loaded['canonical']
        r,auth,reservation,launch,scope,bindings,contract=[parse(raw(role)) for role in (
            'result','authorization','reservation','launch','scope','bindings','contract')]
        profile_sha=sha(compact(profile));request=raw('loaded_request')
        require(request==raw('request'),'REQUEST_COPY_MISMATCH')
        snapshot=loaded['strong_inputs'].capture_request(request)
        require(snapshot.bundle_bytes==raw('subject') and snapshot.proof_bytes==raw('proof'),'SUBJECT_PROOF_COPY_MISMATCH')
        require(profile_sha==bindings['runtime_profile_canonical_sha256'],'PROFILE_BINDING')
        require(canonical.verify_sealed_object(contract) and contract['executable_sha256']==sha(raw('artifact'))
                and bindings['candidate_ref']=={'object_id':contract['object_id'],'content_sha256':contract['content_sha256']},'CONTRACT_SEAL_OR_EXECUTABLE')
        require(bindings['actual_governing_bindings']==0 and profile['actual_governing_binding']=='NOT_ESTABLISHED','DEVELOPMENT_SCOPE_CHANGED')
        scope_sha=sha(compact(scope))
        require(r['scope_sha256']==launch['scope_sha256']==scope_sha,'SCOPE_BINDING')
        for row in scope['inputs']:
            require(row['path'] in inputs and len(inputs[row['path']])==row['bytes'] and sha(inputs[row['path']])==row['sha256'],'SCOPE_INPUT_BINDING')
        original_approval=parse(raw('original_authorization'))
        require(launch['approval_record_sha256']==sha(compact(original_approval))
                and auth['authorized_by']=='existing-D199-human-approval:'+sha(compact(original_approval)),'EXISTING_APPROVAL_REFERENCE')
        require(auth['format']=='FP_DEV_STRONG_CORE_READ_AUTH_V1' and auth['authorization_scope']=='ONE_PUBLIC_SUBJECT_CORE_READ_CHECK','OPERATION_CONTROL_KIND')
        core={k:v for k,v in auth.items() if k!='authorization_sha256'}
        require(sha(compact(core))==auth['authorization_sha256']==reservation['authorization_sha256'],'OPERATION_CONTROL_SEAL')
        require(auth['runtime_profile_sha256']==profile_sha and auth['request_sha256']==sha(request)==reservation['request_sha256']
                and auth['subject_sha256']==snapshot.bundle_sha256 and auth['proof_sha256']==snapshot.proof_sha256,'OPERATION_CONTROL_SUBJECT')
        require(type(r['owned_pid']) is int and r['owned_pid']==auth['owned_core_pid']==r['shutdown']['pid'],'OWNED_PID_REFERENCE')
        utc=loaded['strong_candidate']._utc
        require(utc(r['started_at_utc'])<=utc(auth['authorized_at_utc'])<=utc(r['finished_at_utc'])<utc(auth['expires_at_utc']),'LOCAL_EXPIRY_REFERENCE')
        require(r['status']=='DEVELOPMENT_WIRE_MATCHED_NOT_PROJECT_STRONG' and r['not_a_project_StrongReport'] is True
                and r['real_admission']=='NOT_READY' and r['protocol_state_change']=='NONE','RECEIPT_SCOPE')
        require(r['shutdown']['confirmed_exited'] is True and type(r['shutdown']['exit_code']) is int and r['shutdown']['exit_code']==0,'RETAINED_SHUTDOWN')
        require(r['network']['networkactive'] is False and type(r['network']['connections']) is int and r['network']['connections']==0,'RETAINED_OFFLINE_STATE')
        require(raw('stderr')==b'' and reservation['state']=='RESERVED_MAY_HAVE_READ','OUTPUT_OR_CONSUMPTION_STATE')
        require(profile['authorization_path'].endswith('/'+roles['authorization']) and profile['reservation_path'].endswith('/'+roles['reservation']),'CONTROL_LOCATION_REFERENCE')
        # No record path is opened. These strings only compare reviewed source bytes.
        current='docs/development/strong-candidate-public-sample-run-2026-10-27-rev-001/'
        prior='docs/development/strong-macos-listener-correction-2026-10-27-rev-001/'
        normalized=raw('operation').decode().replace('FP_D255','FP_D253').replace("D252='"+current+"'","D252='"+prior+"'")
        require(normalized.encode()==raw('prior_operation') and raw('test').decode().replace('FP_D255','FP_D253').encode()==raw('prior_test'),'REVIEWED_ALGORITHM_REUSE')
        retained=parse(raw('retained_core'));chain=retained['last_chain']['result']
        require(chain['bestblockhash']==r['pre_candidate_chain']['bestblockhash'] and chain['blocks']==chain['headers']==r['pre_candidate_chain']['blocks']
                and chain['initialblockdownload'] is False,'CROSS_RUN_TIP_CORRESPONDENCE')
        calls=[]
        def rpc(method,*args):
            calls.append([method,*args])
            if method=='getnetworkinfo' and not args:return copy.deepcopy(retained['last_network']['result'])
            if method=='getblockchaininfo' and not args:return copy.deepcopy(chain)
            if method=='getblockhash' and args==(912095,):return retained['sample_hash']['result']
            if method=='getblockheader' and len(args)==2 and args[0]==retained['sample_hash']['result'] and type(args[1]) is bool:
                return copy.deepcopy(retained['sample_header_verbose' if args[1] else 'sample_header_raw']['result'])
            raise ValueError('UNSUPPORTED_RETAINED_CALLBACK_REQUEST')
        observation=loaded['strong_core'].observe_core_paths(request,rpc,**profile['policy'])
        wire=loaded['strong_candidate'].wire_result(snapshot,observation)
        require(compact(wire)+b'\n'==raw('stdout') and wire==r['wire'],'RECOMPUTED_WIRE_MISMATCH')
        require(raw('replay_a')==raw('replay_b'),'RETAINED_REPLAY_INCONSISTENT')
        replay=parse(raw('replay_a'))
        require(replay['scope']=='POST_RUN_RETAINED_D254_CALCULATION_NOT_D255_RPC_TRANSPORT_REPLAY'
                and replay['artifact_sha256']==sha(raw('artifact')) and replay['request_sha256']==sha(request)
                and replay['D254_retained_result_sha256']==sha(raw('retained_core')) and replay['D255_actual_stdout_sha256']==sha(raw('stdout'))
                and replay['closed_callback_calls']==calls and replay['actual_D255_RPC_raw_transcript_retained'] is False,'POST_RUN_AUDIT_BINDING')
        result.update(raw_input_and_wire_binding_match=True,artifact_sha256=sha(raw('artifact')),
            reported_tip_from_retained_D254=observation.tip_height,confirmations_from_retained_D254=observation.anchors[0].confirmations,
            replay_scope='D254_RETAINED_CALCULATION_MATCHES_D255_WIRE_NOT_TRANSPORT_TRACE',
            authorization_basis='RETAINED_D199_RESEARCH_APPROVAL_NOT_FPP_AUTHORITY',retained_shutdown_exit_code=0)
    except (ValueError,KeyError,TypeError,AssertionError,UnicodeError,RecursionError):
        result['findings'].append({'item':'semantic-binding','status':'REJECTED','error':'STRONG_EVENT_SEMANTIC_BINDING_MISMATCH'})
    finally:
        for key,value in old.items():
            if value is sentinel:sys.modules.pop(key,None)
            else:sys.modules[key]=value
    return finish()
