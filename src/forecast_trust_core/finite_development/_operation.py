"""Finite operation bindings; no complete actual operation universe."""
import hashlib
import re
from jsonschema import Draft202012Validator
from . import _base as _B
from ._schemas import RAW_BYTES

LIMIT = 1048576
SCHEMAS = {name+"_v1.json": _B.parse_json_strict(RAW_BYTES[name]) for name in ("operation_registry", "component_contract")}
for s in SCHEMAS.values(): Draft202012Validator.check_schema(s)
REGISTRY_V = Draft202012Validator(SCHEMAS['operation_registry_v1.json'])
COMPONENT_V = Draft202012Validator(SCHEMAS['component_contract_v1.json'])

T = {'type':'string','minLength':1,'pattern':'^[A-Za-z0-9._:/-]+$'}
R = {'$ref':'#/$defs/exact_ref'}
def _closed(properties):
    return {'type':'object','additionalProperties':False,'required':list(properties),'properties':properties}
def _array(items):
    return {'type':'array','minItems':1,'maxItems':1024,'items':items}
CMDS = _array(T)
CHECK = _closed({'check_id':T,'command_ids':CMDS})
OP = _closed({'operation_id':T,'component_role':T,'logical_entrypoint_id':T,
              'source_unit_ref':R,'symbol':T,'command_ids':CMDS,'checks':_array(CHECK)})
MAPPING_SCHEMA = {**_closed({'format':{'const':'FP_DEV_OPERATION_MAPPING_V1'},
    'scope':{'const':'FINITE_DEVELOPMENT_SCOPE_ONLY'},
    'registry':_closed({'ref':R,'version':T}),
    'components':_array(_closed({'role':T,'ref':R,'version':T})),
    'operations':_array(OP)}),'$defs':SCHEMAS['operation_registry_v1.json']['$defs']}
MAP_V = Draft202012Validator(MAPPING_SCHEMA)

def _tree(value):
    pending=[(value,0)]
    while pending:
        item,depth=pending.pop()
        if depth>64: raise ValueError('depth')
        if type(item) is dict:
            if any(type(k) is not str for k in item): raise ValueError('plain keys')
            pending.extend((v,depth+1) for v in item.values())
        elif type(item) is list:
            pending.extend((v,depth+1) for v in item)
        elif type(item) not in (str,int,bool,type(None)):
            raise ValueError('plain JSON only')

def _parse(raw):
    if type(raw) is not bytes or len(raw)>LIMIT: raise ValueError('bytes limit')
    obj=_B.parse_json_strict(raw); _tree(obj)
    if type(obj) is not dict: raise ValueError('object')
    return obj

def _ordered(values):
    return values==sorted(set(values))

def _mapping(raw,pin):
    if type(pin) is not str or re.fullmatch('[0-9a-f]{64}',pin) is None:
        raise ValueError('pin')
    if type(raw) is not bytes or len(raw)>LIMIT: raise ValueError('mapping bytes')
    if hashlib.sha256(raw).hexdigest()!=pin: return None,'MAPPING_PIN_MISMATCH'
    m=_parse(raw)
    if not MAP_V.is_valid(m): raise ValueError('mapping shape')
    # All mapping value strings are machine tokens, including nested full refs.
    # JSON Schema's $ may match before final LF; reuse pinned fullmatch checking.
    pending=[m]
    while pending:
        value=pending.pop()
        if type(value) is dict: pending.extend(value.values())
        elif type(value) is list: pending.extend(value)
        else: _B._HELPER.require_ascii_token(value,'mapping')
    if not _ordered([c['role'] for c in m['components']]): raise ValueError('component keys')
    refs=[(c['ref']['object_id'],c['ref']['content_sha256']) for c in m['components']]
    if len(refs)!=len(set(refs)): raise ValueError('component refs')
    if not _ordered([o['operation_id'] for o in m['operations']]): raise ValueError('operation keys')
    roles={c['role'] for c in m['components']}; seen=set()
    for o in m['operations']:
        if o['component_role'] not in roles or not _ordered(o['command_ids']): raise ValueError('role/commands')
        if not _ordered([c['check_id'] for c in o['checks']]): raise ValueError('checks')
        covered=set()
        for c in o['checks']:
            if c['check_id'] in seen or not _ordered(c['command_ids']): raise ValueError('check keys')
            seen.add(c['check_id'])
            if not set(c['command_ids'])<=set(o['command_ids']): raise ValueError('check commands')
            covered.update(c['command_ids'])
        if covered!=set(o['command_ids']): raise ValueError('check omission')
    if roles!={o['component_role'] for o in m['operations']}: raise ValueError('empty component')
    return m,None

def consume(expected_base,base_records,mapping_bytes,mapping_sha256,registry_bytes,component_records):
    """Pure after fixed import startup; never execute supplied argv/path or trust PASS."""
    added=[]; missing=[]
    def fail(code,slot):
        d={'code':code,'slot':slot,'field':''}
        if d not in added: added.append(d)
    try:
        _tree(expected_base)
        if type(expected_base) is not dict: raise ValueError('expected')
    except (TypeError,ValueError,RecursionError):
        expected_base={}; fail('INVALID_BASE_EXPECTED','base')
    if type(base_records) is not dict or any(type(k) is not str for k in base_records) or len(base_records)>32:
        base_records={}; fail('INVALID_BASE_RECORDS','base')
    safe_records=dict(base_records)
    for slot in _B.SLOTS:
        if slot in safe_records:
            try: _parse(safe_records[slot])
            except (TypeError,ValueError,RecursionError):
                safe_records[slot]=None; fail('INVALID_BASE_RECORD','base:'+slot)
    base=_B.consume(expected_base,safe_records)
    missing.extend(base['missing_inputs'])
    try:
        mapping,err=_mapping(mapping_bytes,mapping_sha256)
        if err: fail(err,'mapping')
    except (TypeError,ValueError,RecursionError):
        mapping=None; fail('INVALID_MAPPING','mapping')
    if type(component_records) is not dict or any(type(k) is not str for k in component_records) or len(component_records)>1024:
        component_records={}; fail('INVALID_COMPONENT_RECORDS','components')
    if mapping:
        expected_components={c['role']:c for c in mapping['components']}
        if set(component_records)-set(expected_components): fail('UNKNOWN_COMPONENT_SLOT','components')
        for role in expected_components:
            if role not in component_records: missing.append('component:'+role)
    else: expected_components={}
    def object_record(raw,validator,slot):
        try:
            obj=_parse(raw)
            if not validator.is_valid(obj) or not _B.verify_sealed_object(obj): raise ValueError('shape/seal')
            return obj
        except (TypeError,ValueError,RecursionError):
            fail('INVALID_OPERATION_RECORD',slot); return None
    registry=None
    if registry_bytes is None: missing.append('registry')
    else: registry=object_record(registry_bytes,REGISTRY_V,'registry')
    components={}
    for role in sorted(component_records):
        obj=object_record(component_records[role],COMPONENT_V,'component')
        if obj is not None:
            components[role]=obj
            if mapping and role in expected_components:
                ex=expected_components[role]
                if _B._ref(obj)!=ex['ref']: fail('COMPONENT_REF_MISMATCH','component')
                if obj['component_role']!=role or obj['contract_version']!=ex['version']:
                    fail('COMPONENT_ROLE_VERSION_MISMATCH','component')
    base_objs={}
    for slot in ('vc','ib','tc1'):
        if type(safe_records.get(slot)) is bytes:
            obj=object_record(safe_records[slot],_B._VALIDATORS[slot],'base:'+slot)
            if obj is not None: base_objs[slot]=obj
    def keyed(rows,key,code,slot):
        d={}
        for row in rows:
            k=row[key]
            if k in d: fail(code,slot)
            else: d[k]=row
        return d
    def roles(rows,slot): return keyed(rows,'role_id','DUPLICATE_ROLE_ID',slot)
    registry_ops={}
    if registry:
        registry_ops=keyed(registry['operations'],'operation_id','DUPLICATE_OPERATION_ID','registry')
        for o in registry['operations']:
            roles(o['input_role_bindings'],'registry'); roles(o['output_role_bindings'],'registry')
    for c in components.values():
        roles(c['input_role_bindings'],'component'); roles(c['output_role_bindings'],'component')
    ib_ops={}
    if 'ib' in base_objs:
        ib_ops=keyed(base_objs['ib']['entrypoint_bindings'],'operation_id','DUPLICATE_OPERATION_ID','ib')
    tc_ops={}
    if 'tc1' in base_objs:
        tc_ops=keyed(base_objs['tc1']['operation_coverage'],'operation_id','DUPLICATE_OPERATION_ID','tc1')
    resolved=[]
    if mapping:
        exops={o['operation_id']:o for o in mapping['operations']}; opids=set(exops)
        if registry:
            if _B._ref(registry)!=mapping['registry']['ref'] or registry['registry_version']!=mapping['registry']['version']:
                fail('REGISTRY_REF_VERSION_MISMATCH','registry')
            if set(registry_ops)!=opids: fail('OPERATION_UNIVERSE_MISMATCH','registry')
        for slot,ops in (('ib',ib_ops),('tc1',tc_ops)):
            if slot in base_objs and set(ops)!=opids: fail('OPERATION_UNIVERSE_MISMATCH',slot)
        if 'vc' in base_objs:
            vc=base_objs['vc']
            if vc['operation_registry_ref']!=mapping['registry']['ref']: fail('VC_REGISTRY_MISMATCH','vc')
            full=lambda r:(r['object_id'],r['content_sha256'])
            if sorted(map(full,vc['component_contract_refs']))!=sorted(full(c['ref']) for c in mapping['components']):
                fail('VC_COMPONENT_MISMATCH','vc')
        for role,c in components.items():
            if role not in expected_components: continue
            owned={o['operation_id'] for o in mapping['operations'] if o['component_role']==role}
            if set(c['operation_ids'])!=owned: fail('COMPONENT_OPERATION_MISMATCH','component')
        for opid,ex in exops.items():
            role=ex['component_role']; ro=registry_ops.get(opid); co=components.get(role); ib=ib_ops.get(opid); tc=tc_ops.get(opid)
            if ro:
                if ro['owning_component_role']!=role: fail('OPERATION_COMPONENT_MISMATCH','registry')
                if ro['implementation_entrypoint_id']!=ex['logical_entrypoint_id']: fail('ENTRYPOINT_MISMATCH','registry')
                if co:
                    for field in ('input_role_bindings','output_role_bindings'):
                        if roles(ro[field],'registry')!=roles(co[field],'component'): fail('OPERATION_COMPONENT_MISMATCH','registry')
                    for field in ('failure_vocabulary_ref','determinism_requirement'):
                        if ro[field]!=co[field]: fail('OPERATION_COMPONENT_MISMATCH','registry')
            if ib and any(ib[k]!=ex[k] for k in ('logical_entrypoint_id','source_unit_ref','symbol')):
                fail('ENTRYPOINT_MISMATCH','ib')
            if tc and set(tc['command_ids'])!=set(ex['command_ids']): fail('OPERATION_COMMAND_MISMATCH','tc1')
            for check in ex['checks']:
                resolved.append({'check_id':check['check_id'],'registry_ref':mapping['registry']['ref'],
                                 'operation_id':opid,'component_ref':expected_components[role]['ref'],
                                 'command_ids':check['command_ids'][:]})
    failures=base['failures']+added
    local=base['binding_verdict']=='LOCAL_CANDIDATE_BINDINGS_VERIFIED' and mapping is not None and not failures and not missing
    return {**base,'profile':'FP_DEV_OPERATION_MAPPING_CONSUMPTION_V1',
        'verdict':'REJECT' if failures else 'UNRESOLVED','failures':failures,'missing_inputs':missing,
        'operation_binding_verdict':'LOCAL_OPERATION_MAPPING_VERIFIED' if local else 'NOT_VERIFIED',
        'resolved_checks':sorted(resolved,key=lambda c:c['check_id']) if local else [],
        'independently_complete_product_universe':'NOT_ESTABLISHED',
        'source_bytes_and_package_inclusion':'NOT_VERIFIED',
        'mapping_authority_and_chronology':'NOT_ESTABLISHED'}
