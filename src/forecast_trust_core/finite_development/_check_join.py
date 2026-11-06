"""Finite report/check/operation bindings; no domain truth."""
import copy
import hashlib
from . import _operation as _M
from .. import report_check_content_v1 as _C

def _plain(value):
    pending=[(value,0)]; count=0
    while pending:
        item,depth=pending.pop();count+=1
        if depth>64 or count>65536: raise ValueError('Plain input depth/size')
        if type(item) is dict:
            if any(type(k) is not str for k in item): raise ValueError('Plain keys')
            pending.extend((v,depth+1) for v in item.values())
        elif type(item) is list:pending.extend((v,depth+1) for v in item)
        elif type(item) not in (str,int,bool,type(None)):raise ValueError('Plain JSON values')

def consume(expected_base,base_records,mapping_bytes,mapping_sha256,registry_bytes,
            component_records,catalog_bytes,catalog_sha256,checks):
    """Pure after fixed import startup; subset report checks keep finite operation identity."""
    operation=_M.consume(expected_base,base_records,mapping_bytes,mapping_sha256,
                         registry_bytes,component_records)
    errors=[]
    def error(code):
        if code not in errors:errors.append(code)
    safe=[]
    if type(checks) is not list or len(checks)>1024:error('INVALID_CHECKS')
    else:
        for row in checks:
            try:_plain(row);safe.append(row)
            except ValueError:error('INVALID_CHECK_ROW');safe.append(None)
    catalog=None
    try:
        catalog=_C._catalog(catalog_bytes,catalog_sha256)
        content=_C.consume_checks(catalog_bytes,catalog_sha256,safe)
    except _C.ContentError:
        error('CATALOG_INVALID')
        content={'well_formed_and_bound':False,'hard_errors':['CATALOG_INVALID'],
                 'missing_checks':[],'missing_inputs':[],'missing_coverage':[],
                 'failed_checks':[],'unknown_checks':[]}
    joined=[]
    valid_operation=operation['operation_binding_verdict']=='LOCAL_OPERATION_MAPPING_VERIFIED'
    if catalog is not None and valid_operation:
        if catalog['validator_contract_ref']!=expected_base['refs']['vc']:
            error('REPORT_VALIDATOR_MISMATCH')
        resolved={c['check_id']:c for c in operation['resolved_checks']}
        for definition in catalog['checks']:
            check=resolved.get(definition['check_id'])
            if check is None:error('REPORT_CHECK_NOT_MAPPED');continue
            coverage=[x['member_ref'] for x in definition['required_coverage'] if x['dimension']=='OPERATION']
            if coverage!=[check['registry_ref']]:error('REPORT_OPERATION_COVERAGE_MISMATCH')
            joined.append(copy.deepcopy(check))
    local=valid_operation and content['well_formed_and_bound'] and not errors
    hard=bool(operation['failures'] or errors or content['hard_errors'] or content['failed_checks'])
    return {'profile':'FP_DEV_REPORT_OPERATION_JOIN_V1','verdict':'REJECT' if hard else 'UNRESOLVED',
            'local_join_verdict':'LOCAL_REPORT_OPERATION_BINDINGS_VERIFIED' if local else 'NOT_VERIFIED',
            'operation_result':operation,'content_result':content,'join_errors':errors,
            'joined_checks':joined if local else [],
            'real_missing':copy.deepcopy(operation['real_missing']),
            'unverified_obligations':copy.deepcopy(operation['unverified_obligations']),
            'independently_complete_product_universe':'NOT_ESTABLISHED',
            'actual_check_execution_and_report_truth':'NOT_VERIFIED',
            'source_package_build_lock_runtime_and_chronology':'NOT_ESTABLISHED',
            'real_admission':'NOT_READY','real_g02_g03':'NOT_ESTABLISHED',
            'real_genesis_readiness':'NOT_ESTABLISHED','prospective_eligible':False,'protocol_state_change':'NONE'}
