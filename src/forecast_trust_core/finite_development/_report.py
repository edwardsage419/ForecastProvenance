"""Finite VR2 binding and declared check aggregation; no report truth."""
import copy
import hashlib
import json
from jsonschema import Draft202012Validator
from . import _check_join as _J
from ._schemas import RAW_BYTES

_C = _J._C
_H = _J._M._B._HELPER
schema = _H.parse_json_strict(RAW_BYTES["validation_report"])
Draft202012Validator.check_schema(schema)
_V = Draft202012Validator(schema)
EXPECTED={'format','scope','report_ref','report_raw_sha256','subject_ref','validator_contract_ref',
          'report_kind','content_profile_ref','dependency_refs'}

def _expected(value):
    _J._plain(value);_C._closed(value,EXPECTED,'REPORT_EXPECTED')
    if value['format']!='FP_DEV_R6_REPORT_EXPECTED_V1' or value['scope']!='FINITE_DEVELOPMENT_SCOPE_ONLY':raise ValueError('scope')
    for k in ('report_ref','subject_ref','validator_contract_ref','content_profile_ref'):_C._ref(value[k])
    if type(value['report_kind']) is not str or value['report_kind'] not in _C.KINDS:raise ValueError('kind')
    if type(value['report_raw_sha256']) is not str or _C.DIGEST.fullmatch(value['report_raw_sha256']) is None:raise ValueError('digest')
    _C._set_keys(value['dependency_refs'],_C._ref)
    return value

def _integer(text):
    value=int(text)
    if text=='-0' or abs(value)>_H.MAX_SAFE_INTEGER:raise ValueError('noncanonical integer')
    return value

def _body(raw):
    if type(raw) is not bytes or len(raw)>1048576:raise ValueError('bytes size/type')
    obj=json.loads(_H.decode_utf8_json(raw),object_pairs_hook=_C._pairs,
                   parse_int=_integer,parse_float=_C._number,parse_constant=_C._number)
    _J._plain(obj)
    if type(obj) is not dict:raise ValueError('body object')
    return obj

def _refs(report):
    _C._token(report['object_id'],'REPORT_ID')
    for k in ('trusted_manifest_ref','candidate_object_ref','validator_contract_ref'):_C._ref(report[k])
    if 'manifest_acceptance_ref' in report:_C._ref(report['manifest_acceptance_ref'])
    _C._set_keys(report['dependency_refs'],_C._ref)
    if type(report['derived_claims']) is not list:raise ValueError('claims')
    for claim in report['derived_claims']:
        _C._ref(claim['subject_ref'])
        for k in ('policy_refs','evidence_refs'):
            for ref in claim[k]:_C._ref(ref)
        for reason in claim['reason_codes']:_C._token(reason,'REASON')
        for k in ('verified_upper_bound','frozen_deadline'):
            if k in claim:_H.require_utc_timestamp(claim[k])

def consume(expected_report,report_bytes,expected_base,base_records,mapping_bytes,
            mapping_sha256,registry_bytes,component_records,catalog_bytes,catalog_sha256):
    """Consume supplied public/development bytes only; no I/O after fixed imports."""
    errors=[];missing=[];report=None;expected=None;catalog=None
    def error(code):
        if code not in errors:errors.append(code)
    try:expected=_expected(expected_report)
    except (ValueError,TypeError,RecursionError):error('INVALID_REPORT_EXPECTED')
    try:catalog=_C._catalog(catalog_bytes,catalog_sha256)
    except _C.ContentError:error('CATALOG_INVALID')
    if report_bytes is None:missing.append('report_bytes')
    else:
        try:report=_body(report_bytes)
        except (ValueError,TypeError,RecursionError):error('INVALID_REPORT_JSON')
    base_args=(expected_base,base_records,mapping_bytes,mapping_sha256,registry_bytes,component_records)
    join=None
    if report is not None:
        join=_J.consume(*base_args,catalog_bytes,catalog_sha256,report.get('checks'))
        operation=copy.deepcopy(join['operation_result'])
    else:operation=_J._M.consume(*base_args)
    aggregate='NOT_VERIFIED';claims=[]
    if report is not None:
        if 'manifest_acceptance_ref' in report:error('PRESIGN_ACCEPTANCE_PRESENT')
        if not _V.is_valid(report):error('REPORT_SHAPE_INVALID')
        try:_H.canonical_json(report)
        except ValueError:error('INVALID_REPORT_JSON')
        try:
            if not _H.verify_sealed_object(report):error('REPORT_SEAL_INVALID')
        except (ValueError,TypeError,RecursionError):error('REPORT_SEAL_INVALID')
        try:_refs(report)
        except (ValueError,TypeError,KeyError):error('REPORT_REFERENCE_INVALID')
        deps=None
        try:deps=set(_C._set_keys(report.get('dependency_refs'),_C._ref))
        except ValueError:error('REPORT_DEPENDENCIES_INVALID')
        if expected is not None:
            if hashlib.sha256(report_bytes).hexdigest()!=expected['report_raw_sha256']:error('REPORT_RAW_MISMATCH')
            if {k:report.get(k) for k in ('object_id','content_sha256')}!=expected['report_ref']:error('REPORT_REF_MISMATCH')
            if any(report.get(k)!=expected['subject_ref'] for k in ('trusted_manifest_ref','candidate_object_ref')):error('REPORT_SUBJECT_MISMATCH')
            if report.get('validator_contract_ref')!=expected['validator_contract_ref']:error('REPORT_VALIDATOR_MISMATCH')
            if report.get('dependency_refs')!=expected['dependency_refs']:error('REPORT_DEPENDENCIES_MISMATCH')
        if type(report.get('result')) is not str or report['result'] not in ('VALID','INVALID','INELIGIBLE_TRUST_UNKNOWN'):error('REPORT_RESULT_UNSUPPORTED')
        if join['content_result']['well_formed_and_bound']:
            content=join['content_result']
            aggregate='INVALID' if content['failed_checks'] else 'INELIGIBLE_TRUST_UNKNOWN' if content['unknown_checks'] else 'VALID'
            if report.get('result')!=aggregate:error('REPORT_RESULT_MISMATCH')
        if type(report.get('derived_claims')) is list:claims=copy.deepcopy(report['derived_claims'])
        if catalog is not None and deps is not None:
            required={_C._ref(catalog['content_profile_ref'])}
            for definition in catalog['checks']:
                required.update(_C._ref(x) for x in definition['required_support_refs'])
                required.update(_C._ref(x['member_ref']) for x in definition['required_coverage'])
            if join['content_result']['well_formed_and_bound']:
                for check in report['checks']:
                    required.update(_C._ref(x) for x in check['support_refs']+check['blocking_finding_refs'])
            if not required<=deps:error('REQUIRED_REPORT_DEPENDENCY_MISSING')
    if catalog is not None and expected is not None:
        if any(catalog[k]!=expected[k] for k in ('report_kind','subject_ref','validator_contract_ref','content_profile_ref')):error('REPORT_CATALOG_MISMATCH')
    local=not errors and not missing and join is not None and join['local_join_verdict']=='LOCAL_REPORT_OPERATION_BINDINGS_VERIFIED'
    hard=bool(errors or operation['failures'] or (join is not None and join['verdict']=='REJECT'))
    return {'profile':'FP_DEV_FULL_R6_REPORT_CONSUMPTION_V1','verdict':'REJECT' if hard else 'UNRESOLVED',
            'local_report_binding_verdict':'LOCAL_REPORT_CONTENT_BINDINGS_VERIFIED' if local else 'NOT_VERIFIED',
            'report_errors':errors,'missing_report_inputs':missing,'join_result':join,'operation_result':operation,
            'report_body_consumption':'BODY_AVAILABLE' if report is not None else 'BODY_UNAVAILABLE',
            'aggregate_check_result':aggregate,'unverified_derived_claims':claims,'derived_claims_verified':'NOT_VERIFIED',
            'real_missing':copy.deepcopy(operation['real_missing']),
            'unverified_obligations':copy.deepcopy(operation['unverified_obligations']),
            'support_bytes_and_domain_truth':'NOT_VERIFIED','independently_complete_product_universe':'NOT_ESTABLISHED',
            'source_package_build_lock_runtime_and_chronology':'NOT_ESTABLISHED',
            'real_admission':'NOT_READY','real_g02_g03':'NOT_ESTABLISHED','real_genesis_readiness':'NOT_ESTABLISHED',
            'prospective_eligible':False,'protocol_state_change':'NONE'}
