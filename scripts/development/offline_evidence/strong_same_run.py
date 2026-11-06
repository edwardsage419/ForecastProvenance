"""One public CLI reply event, captured once; no native/Core/authority action."""
import json
from pathlib import Path
from types import ModuleType

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CATALOG_PATH='scripts/development/offline_evidence/strong_same_run_inputs.json'
CATALOG_IDENTITY={'bytes':8109,'sha256':'b3c18ed018b49391649a5c73ba08ecefc601f9fee626252fc9af35f1a6bea201'}

def passive_reader():
    module=ModuleType('fp_same_run_passive_reader');module.__file__=str(HERE/'worker.py')
    exec(compile((HERE/'worker.py').read_bytes(),module.__file__,'exec'),module.__dict__)
    return module

def consume(directory=ROOT,*,source_root=ROOT,reader=None):
    if reader is None:reader=passive_reader()
    result={'status':'MISSING','scope':'D257_RETAINED_LOCAL_PUBLIC_CLI_REPLY_MATH_NOT_EXECUTION_AUTHENTICATION',
        'findings':[],'observation':None,'native_execution':False,'project_Strong':'NOT_ESTABLISHED',
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
    raw=read(source_root,CATALOG_PATH,CATALOG_IDENTITY)
    if raw is None:return finish()
    catalog=json.loads(raw);roles=catalog['roles'];rows=catalog['inputs']
    if len(rows)>128 or sum(row['bytes'] for row in rows)>32*2**20:
        result['findings'].append({'item':'catalog','status':'REJECTED','error':'FINITE_INPUT_LIMIT'});return finish()
    captured={row['path']:read(directory,row['path'],row) for row in rows}
    result['input_count']=len(captured)
    if result['findings']:return finish()
    try:
        # Exact admitted audit code has a bytes-only function. Never call main(),
        # follow a record path, or reread input files after this capture boundary.
        module=ModuleType('fp_captured_same_run_audit');module.__file__=str(HERE/'__captured_public_audit__.py')
        exec(compile(captured[roles['audit_source']],module.__file__,'exec'),module.__dict__)
        snapshot={name:captured[roles[name]] for name in module.INPUT_LIMITS}
        observation=module.verify_captured(snapshot)
        if (type(observation) is not dict or observation['status']!='OBSERVED' or observation['real_admission']!='NOT_READY' or
            observation['protocol_state_change']!='NONE' or observation['all_recorded_results_consumed'] is not True or
            observation['local_success_references_separately_checked'] is not True or
            observation['independent_actual_execution_or_owner_authentication'] is not False or
            observation['HTTP_TCP_transport_packets_replayed'] is not False):raise ValueError('scope')
        # Prior independently run audit outputs must agree, but their labels
        # cannot substitute for this fresh computation from the same snapshots.
        a=captured[roles['replay_a']];b=captured[roles['replay_b']]
        if a!=b or json.loads(a)!=observation:raise ValueError('retained calculation mismatch')
        result['observation']=observation
    except (ValueError,KeyError,TypeError,AssertionError,UnicodeError,RecursionError):
        result['findings'].append({'item':'same-snapshot-replay','status':'REJECTED','error':'SAME_RUN_REPLAY_BINDING_MISMATCH'})
    return finish()
