"""Passive D271 observation consumption on exact shared snapshots. No native IO."""
import hashlib
import json

MANIFEST_SHA='f617aa1ee8365cd73357a79d07f9ef6736df423b8780bb02337a5568346ca94e'
CORPUS='docs/development/mainline-execution-2026-10-09-rev-001/public-verifier-evidence/CCTV/50a8ecf2a220f4c8bdc4f085789b8e85c26829e7/ed25519/ed25519vectors.json'
SAFE={'real_authentication':'NOT_ESTABLISHED','public_authentication':'NOT_ESTABLISHED',
      'real_admission':'NOT_READY','prospective_eligible':False,'protocol_state_change':'NONE'}


def _sha(raw):return hashlib.sha256(raw).hexdigest()

def _same(left,right):
    return json.dumps(left,sort_keys=True,separators=(',',':'))==json.dumps(right,sort_keys=True,separators=(',',':'))


def _validate_report(report,manifest,snapshots):
    if type(report) is not dict:raise ValueError('REPORT_OBJECT_REQUIRED')
    if (report.get('status')!='OBSERVED' or report.get('findings')!=[] or report.get('child_started') is not True
        or report.get('scope')!='FIXED_PUBLIC_CCTV_305_AND_0_DEVELOPMENT_MATH_ONLY'
        or type(report.get('sample_attempts')) is not int or report['sample_attempts']!=2):
        raise ValueError('RETAINED_EXECUTION_NOT_OBSERVED')
    for key,value in SAFE.items():
        if type(report.get(key)) is not type(value) or report[key]!=value:raise ValueError('UNSAFE_REPORT_TAG')
    for key in ('full_build_runtime_closure','independent_software_trust'):
        if report.get(key)!='NOT_ESTABLISHED':raise ValueError('RUNTIME_OR_TRUST_PROMOTED')
    if report.get('child_source_sha256')!=_sha(snapshots[manifest['execution_source']]):raise ValueError('ACTUAL_CHILD_SOURCE_BINDING')
    if not _same(report.get('input_identities'),manifest['execution_inputs']):raise ValueError('EXECUTION_INPUT_IDENTITY_SET')
    if (type(report.get('snapshot_bytes')) is not int or
        report['snapshot_bytes']!=sum(row['bytes'] for row in manifest['execution_inputs'])):
        raise ValueError('EXECUTION_SNAPSHOT_SIZE')
    expected_gate={'status':'OBSERVED','admitted_input_count':64,'consumed_distinct_gate_inputs':63,
                   'actual_adapter_distinct_read_paths':63,'actual_adapter_snapshot_read_calls':132}
    if not _same(report.get('gate'),expected_gate):raise ValueError('ACTUAL_GATE_CONSUMPTION_BINDING')
    if not _same(report.get('limits'),manifest['execution_limits']):raise ValueError('EXECUTION_LIMIT_IDENTITY')
    observation=report.get('runtime_observations')
    if (type(observation) is not dict or set(observation)!={'peak_rss_bytes','rlimit_core_bytes','rlimit_cpu_seconds','rlimit_fsize_bytes'}
        or type(observation['peak_rss_bytes']) is not int or not 0<observation['peak_rss_bytes']<=268435456
        or not _same(observation['rlimit_core_bytes'],[0,0])
        or not _same(observation['rlimit_cpu_seconds'],[5,5])
        or not _same(observation['rlimit_fsize_bytes'],[1048576,1048576])):
        raise ValueError('RESOURCE_OBSERVATION_BINDING')
    records=json.loads(snapshots[CORPUS]);samples=report.get('samples')
    if type(samples) is not list or len(samples)!=2:raise ValueError('PUBLIC_SAMPLE_SET')
    for sample,number,status in zip(samples,(305,0),('VERIFIED','REJECTED')):
        if (type(sample) is not dict or type(sample.get('number')) is not int
            or sample['number']!=number or sample.get('math_status')!=status):raise ValueError('PUBLIC_SAMPLE_OUTCOME')
        message=records[number]['msg'].encode('ascii')
        if (type(sample.get('message_bytes')) is not int or sample['message_bytes']!=len(message)
            or sample.get('message_sha256')!=_sha(message)):raise ValueError('ORIGINAL_PUBLIC_MESSAGE_IDENTITY')
        if (type(sample.get('reasons')) is not list or not 0<len(sample['reasons'])<=16
            or any(type(reason) is not str or not 0<len(reason)<=128 or not reason.isascii() for reason in sample['reasons'])):
            raise ValueError('PUBLIC_RESULT_REASONS')
        for key,value in SAFE.items():
            if type(sample.get(key)) is not type(value) or sample[key]!=value:raise ValueError('UNSAFE_SAMPLE_TAG')
    projection=dict(report);projection.pop('runtime_observations')
    return projection


def consume(manifest_raw,read_input):
    result={**SAFE,'status':'MISSING','findings':[],'scope':'RETAINED_D271_PUBLIC_MATH_EXECUTION_ONLY',
            'bound_execution_input_count':0,'admitted_input_count':0,'retained_math_statuses':{},
            'retained_executions_consumed':0,'deterministic_projection_equal':False,
            'native_loaded_here':False,'backend_called_here':False,'message_constructed':False,
            'full_build_runtime_closure':'NOT_ESTABLISHED','independent_software_trust':'NOT_ESTABLISHED',
            'execution_contract_complete':'NOT_ESTABLISHED','operational_bindings_established':0}
    if type(manifest_raw) is not bytes or len(manifest_raw)>1048576 or _sha(manifest_raw)!=MANIFEST_SHA:
        result.update(status='REJECTED',findings=[{'item':'public_math_manifest','status':'REJECTED','error':'MANIFEST_IDENTITY_MISMATCH'}]);return result
    manifest=json.loads(manifest_raw);snapshots={}
    for row in manifest['inputs']:
        raw=read_input(row)
        if raw is None:status,error='MISSING','INPUT_NOT_ADMITTED'
        elif type(raw) is not bytes or len(raw)!=row['bytes'] or _sha(raw)!=row['sha256']:
            status,error='REJECTED','INPUT_IDENTITY_MISMATCH'
        else:snapshots[row['path']]=raw;continue
        result['findings'].append({'item':row['path'],'status':status,'error':error})
    result['admitted_input_count']=len(snapshots)
    if result['findings']:
        result['status']='REJECTED' if any(f['status']=='REJECTED' for f in result['findings']) else 'MISSING'
        return result
    projections=[]
    for path in manifest['reports']:
        try:projection=_validate_report(json.loads(snapshots[path]),manifest,snapshots)
        except (ValueError,TypeError,KeyError,IndexError,RecursionError):
            result['findings'].append({'item':path,'status':'REJECTED','error':'RETAINED_REPORT_CONTENT_BINDING_INVALID'})
        else:projections.append(projection)
    if result['findings']:result['status']='REJECTED';return result
    if not _same(projections[0],projections[1]):
        result.update(status='REJECTED',findings=[{'item':'paired-retained-executions','status':'REJECTED','error':'DETERMINISTIC_PROJECTION_MISMATCH'}]);return result
    result.update(status='OBSERVED',bound_execution_input_count=len(manifest['execution_inputs']),
                  retained_math_statuses={'305':'VERIFIED','0':'REJECTED'},retained_executions_consumed=2,
                  deterministic_projection_equal=True,
                  source_sha256=_sha(snapshots[manifest['execution_source']]),
                  deterministic_projection_sha256=_sha(json.dumps(projections[0],sort_keys=True,separators=(',',':')).encode()),
                  peak_rss_observations=[json.loads(snapshots[path])['runtime_observations']['peak_rss_bytes'] for path in manifest['reports']])
    return result
