"""Finite five-report bindings; Strong truth remains unverified."""
import copy
import hashlib
from jsonschema import Draft202012Validator
from . import _report as _R
from ._schemas import RAW_BYTES

_C = _R._C
_H = _R._H
schema = _H.parse_json_strict(RAW_BYTES["strong_report"])
Draft202012Validator.check_schema(schema)
_S = Draft202012Validator(schema)
R6=tuple(sorted(_C.KINDS));BTC='OTS_BITCOIN_STRONG_VERIFICATION_REPORT';KINDS=tuple(sorted((*R6,BTC)))
SET_KEYS={'format','scope','final_manifest_ref','validator_contract_ref','r4t_ref','r4t_raw_sha256','r6_expected','prebitcoin_expected'}
STRONG_REF_FIELDS=('subject_ref','validator_contract_ref','strong_verifier_contract_ref','external_time_evidence_bundle_ref','ots_proof_ref')
STRONG_KEYS=set(STRONG_REF_FIELDS)|{'report_ref','report_raw_sha256','bundle_sha256','proof_sha256','origin_class'}
def _digest(x):
    if type(x) is not str or _C.DIGEST.fullmatch(x) is None:raise ValueError('digest')
def _expected(e):
    _R._J._plain(e);_C._closed(e,SET_KEYS,'SET_EXPECTED')
    if e['format']!='FP_DEV_REQUIRED_REPORT_SET_V1' or e['scope']!='FINITE_DEVELOPMENT_SCOPE_ONLY':raise ValueError('scope')
    for k in ('final_manifest_ref','validator_contract_ref','r4t_ref'):_C._ref(e[k])
    _digest(e['r4t_raw_sha256']);_C._closed(e['r6_expected'],R6,'R6_EXPECTED')
    for v in e['r6_expected'].values():_R._expected(v)
    s=e['prebitcoin_expected'];_C._closed(s,STRONG_KEYS,'STRONG_EXPECTED')
    for k in (*STRONG_REF_FIELDS,'report_ref'):_C._ref(s[k])
    for k in ('report_raw_sha256','bundle_sha256','proof_sha256'):_digest(s[k])
    if type(s['origin_class']) is not str or s['origin_class'] not in ('SYNTHETIC','LIVE_OPERATIONAL'):raise ValueError('origin')
    return e

def _strong(raw,expected):
    errors=[];body=None
    def error(x):
        if x not in errors:errors.append(x)
    try:body=_R._body(raw)
    except (ValueError,TypeError,RecursionError):error('INVALID_STRONG_JSON')
    if body is not None:
        if not _S.is_valid(body):error('STRONG_SHAPE_INVALID')
        try:
            _H.canonical_json(body)
            if not _H.verify_sealed_object(body):error('STRONG_SEAL_INVALID')
        except (ValueError,TypeError,RecursionError):error('STRONG_SEAL_INVALID')
        try:
            _C._token(body['object_id'],'STRONG_ID')
            for k in STRONG_REF_FIELDS:_C._ref(body[k])
            for k in ('payload_sha256','content_sha256','bundle_sha256','proof_sha256'):_digest(body[k])
            if body.get('verified') is True:
                if type(body.get('bitcoin_block_height')) is not int:raise ValueError('height')
                for k in ('bitcoin_block_hash','bitcoin_header_sha256'):_digest(body[k])
        except (ValueError,TypeError,KeyError):error('STRONG_REFERENCE_INVALID')
        if expected is not None:
            if hashlib.sha256(raw).hexdigest()!=expected['report_raw_sha256']:error('STRONG_RAW_MISMATCH')
            if {k:body.get(k) for k in ('object_id','content_sha256')}!=expected['report_ref']:error('STRONG_REF_MISMATCH')
            if any(body.get(k)!=expected[k] for k in (*STRONG_REF_FIELDS,'bundle_sha256','proof_sha256','origin_class')):error('STRONG_EXPECTED_MISMATCH')
    return {'local_strong_binding_verdict':'LOCAL_STRONG_REPORT_BINDINGS_VERIFIED' if expected is not None and not errors else 'NOT_VERIFIED',
      'errors':errors,'reported_result':'FAILED' if body is not None and body.get('verified') is False else 'REPORTED_VERIFIED_UNREPLAYED' if body is not None and body.get('verified') is True else 'NOT_REPORTED',
      'strong_truth':'NOT_VERIFIED','header_time_as_civil_bound':'NOT_ESTABLISHED'}

def consume(expected_set,reports,catalogs,expected_base,base_records,mapping_bytes,
            mapping_sha256,registry_bytes,component_records):
    """Use explicit fixed byte inputs; no path dispatch or external actions."""
    errors=[];missing=[];e=None;safe_expected={}
    def error(x):
        if x not in errors:errors.append(x)
    try:
        _R._J._plain(expected_set)
        if type(expected_set) is dict:safe_expected=expected_set
        e=_expected(expected_set)
    except (ValueError,TypeError,RecursionError):error('INVALID_SET_EXPECTED')
    if e is not None:
        for kind,v in e['r6_expected'].items():
            if v['report_kind']!=kind or v['subject_ref']!=e['final_manifest_ref'] or v['validator_contract_ref']!=e['validator_contract_ref']:error('SET_CONTEXT_MISMATCH')
        s=e['prebitcoin_expected']
        if s['subject_ref']!=e['r4t_ref'] or s['validator_contract_ref']!=e['validator_contract_ref']:error('SET_CONTEXT_MISMATCH')
        refs=[_C._ref(v['report_ref']) for v in e['r6_expected'].values()]+[_C._ref(s['report_ref'])]
        if len(set(refs))!=5:error('DUPLICATE_EXPECTED_REPORT_REF')
        try:
            _R._J._plain(expected_base)
            if expected_base['refs']['vc']!=e['validator_contract_ref'] or expected_base['refs']['r4t']!=e['r4t_ref']:error('SET_CONTEXT_MISMATCH')
        except (ValueError,TypeError,KeyError):error('SET_CONTEXT_MISMATCH')
    shared_records=base_records
    if type(base_records) is dict and len(base_records)<=32 and all(type(k) is str for k in base_records):
        if 'r4t' in base_records and base_records['r4t'] is None:
            shared_records=dict(base_records);del shared_records['r4t']
    base=(expected_base,shared_records,mapping_bytes,mapping_sha256,registry_bytes,component_records)
    operation=_R._J._M.consume(*base)
    r4t=None;r4t_bound=False
    if type(base_records) is dict and all(type(k) is str for k in base_records):r4t=base_records.get('r4t')
    if r4t is None:missing.append('r4t_bytes')
    else:
        try:
            obj=_R._J._M._parse(r4t)
            if not _R._J._M._B._R4T_VALIDATOR.is_valid(obj) or not _H.verify_sealed_object(obj):raise ValueError('r4t')
            if e is not None:
                if hashlib.sha256(r4t).hexdigest()!=e['r4t_raw_sha256']:error('R4T_RAW_MISMATCH')
                elif {k:obj[k] for k in ('object_id','content_sha256')}!=e['r4t_ref']:error('R4T_REF_MISMATCH')
                else:r4t_bound=True
        except (ValueError,TypeError,KeyError,RecursionError):error('INVALID_R4T_BYTES')
    safe_catalogs={}
    if type(catalogs) is not dict or any(type(k) is not str for k in catalogs) or set(catalogs)!=set(R6):error('INVALID_CATALOG_CONTROLS')
    if type(catalogs) is dict and all(type(k) is str for k in catalogs) and len(catalogs)<=4:
        for kind,record in catalogs.items():
            if kind not in R6:continue
            try:
                _C._closed(record,{'bytes','sha256'},'CATALOG_RECORD');_C._catalog(record['bytes'],record['sha256']);safe_catalogs[kind]=record
            except (ValueError,TypeError):error('INVALID_CATALOG_CONTROLS')
    entries=[];counts={k:0 for k in KINDS};supplied={k:0 for k in KINDS};hard=bool(operation['failures']);strong_states=[]
    if type(reports) is not list or len(reports)>16:error('INVALID_REPORT_LIST')
    else:
        for index,row in enumerate(reports):
            try:
                _C._closed(row,{'kind','bytes'},'REPORT_RECORD');_C._token(row['kind'],'KIND')
                if type(row['bytes']) is not bytes and row['bytes'] is not None:raise ValueError('bytes')
            except (ValueError,TypeError):error('INVALID_REPORT_RECORD');continue
            kind=row['kind']
            if kind not in KINDS:error('UNKNOWN_REPORT_KIND');continue
            counts[kind]+=1
            if counts[kind]>1:error('DUPLICATE_REPORT_KIND')
            if row['bytes'] is None:
                entries.append({'index':index,'kind':kind,'result':None,'status':'MISSING'});continue
            supplied[kind]+=1
            if kind in R6:
                controls=safe_expected.get('r6_expected',{})
                er=controls.get(kind,{}) if type(controls) is dict else {}
                c=safe_catalogs.get(kind,{'bytes':None,'sha256':None})
                result=_R.consume(er,row['bytes'],*base,c['bytes'],c['sha256'])
                hard=hard or result['verdict']=='REJECT'
            else:
                result=_strong(row['bytes'],e['prebitcoin_expected'] if e is not None else None)
                for x in result['errors']:error(x)
                strong_states.append(result['reported_result']);hard=hard or result['reported_result']=='FAILED'
            entries.append({'index':index,'kind':kind,'result':result,'status':'CONSUMED'})
    missing_kinds=[k for k in KINDS if supplied[k]==0]
    local=not errors and not missing and not missing_kinds and e is not None and r4t_bound and operation['operation_binding_verdict']=='LOCAL_OPERATION_MAPPING_VERIFIED' and all(counts[k]==1 for k in KINDS)
    if local:
        for entry in entries:
            result=entry['result']
            if entry['kind'] in R6:local=local and result['local_report_binding_verdict']=='LOCAL_REPORT_CONTENT_BINDINGS_VERIFIED'
            else:local=local and result['local_strong_binding_verdict']=='LOCAL_STRONG_REPORT_BINDINGS_VERIFIED'
    return {'profile':'FP_DEV_REQUIRED_REPORT_SET_BINDING_V1','verdict':'REJECT' if errors or hard else 'UNRESOLVED',
      'local_set_binding_verdict':'LOCAL_REQUIRED_REPORT_SET_BINDINGS_VERIFIED' if local else 'NOT_VERIFIED',
      'set_errors':errors,'missing_report_kinds':missing_kinds,'missing_set_inputs':missing,
      'entry_results':entries,'operation_result':operation,
      'strong_reported_result':'FAILED' if 'FAILED' in strong_states else 'REPORTED_VERIFIED_UNREPLAYED' if 'REPORTED_VERIFIED_UNREPLAYED' in strong_states else 'NOT_REPORTED',
      'strong_truth':'NOT_VERIFIED','report_stage_chronology':'NOT_ESTABLISHED',
      'real_missing':copy.deepcopy(operation['real_missing']),'unverified_obligations':copy.deepcopy(operation['unverified_obligations']),
      'independently_complete_product_universe':'NOT_ESTABLISHED','domain_support_and_actual_report_truth':'NOT_VERIFIED',
      'source_package_build_lock_runtime_and_chronology':'NOT_ESTABLISHED',
      'real_admission':'NOT_READY','real_g02_g03':'NOT_ESTABLISHED','real_genesis_readiness':'NOT_ESTABLISHED',
      'prospective_eligible':False,'protocol_state_change':'NONE'}
