"""Fixed development identity checks on admitted snapshots; no native loader."""
import ast
import hashlib
import json
from pathlib import Path

CATALOG_SHA256='a57c4fa4426a1dec2fad298fea4a63f4a7b717331b826a15db25c6daa4795bff'


def consume(catalog_raw, read_input):
    """Run selected existing gate logic; read_input admits one declared record.

    The fixed catalog describes the D212 gate, not an independent runtime
    universe. Its public C headers under libsodium/private are software sources.
    """
    result={'status':'MISSING', 'findings':[], 'admitted_input_count':0,
            'required_declared_gate_inputs':63, 'consumed_distinct_gate_inputs':0,
            'gate_snapshot_read_calls':0, 'gate_read_paths':[],
            'all_declared_gate_inputs_consumed':False, 'gate_check_executed':False,
            'scope':'FIXED_D212_IDENTITY_LOGIC_ON_ADMITTED_SNAPSHOTS_ONLY',
            'native_loaded':False, 'backend_called':False, 'message_constructed':False,
            'full_build_runtime_closure':'NOT_ESTABLISHED',
            'independent_software_trust':'NOT_ESTABLISHED',
            'message_resource_policy':'NOT_ESTABLISHED',
            'public_authentication':'NOT_ESTABLISHED', 'operational_bindings_established':0,
            'real_admission':'NOT_READY', 'protocol_state_change':'NONE'}
    if (type(catalog_raw) is not bytes or len(catalog_raw)!=25968
            or hashlib.sha256(catalog_raw).hexdigest()!=CATALOG_SHA256):
        result.update(status='REJECTED',findings=[{'item':'gate-input-catalog','status':'REJECTED',
                                                  'error':'GATE_CATALOG_IDENTITY_MISMATCH'}])
        return result
    catalog=json.loads(catalog_raw)
    snapshots={}
    for row in catalog['inputs']:
        raw=read_input(row)
        if raw is None:
            result['findings'].append({'item':row['path'],'status':'MISSING','error':'GATE_INPUT_NOT_ADMITTED'})
        elif (type(raw) is not bytes or len(raw)!=row['bytes']
                or hashlib.sha256(raw).hexdigest()!=row['sha256']):
            result['findings'].append({'item':row['path'],'status':'REJECTED','error':'GATE_INPUT_IDENTITY_MISMATCH'})
        else:
            snapshots[row['path']]=raw
    result['admitted_input_count']=len(snapshots)
    if result['findings']:
        result['status']='REJECTED' if any(f['status']=='REJECTED' for f in result['findings']) else 'MISSING'
        return result

    virtual_root=Path('/__fp_declared_gate_snapshots__')
    reads=[]
    def snapshot_read(path):
        relative=str(path.relative_to(virtual_root))
        if relative not in snapshots:
            raise ValueError('UNDECLARED_GATE_SNAPSHOT_READ')
        reads.append(relative)
        return snapshots[relative]
    # Select unmodified hash/PRE_RUN check definitions from the pinned source.
    # Exclude imports, ctypes, _read_regular's OS access, native loader and verify.
    tree=ast.parse(snapshots[catalog['gate_module']])
    names={'EXPECTED_BINARY_SHA256','EXPECTED_BUILD_OBS_SHA256','EXPECTED_SOURCE_MANIFEST_SHA256',
           'EXPECTED_CONFIG_SHA256','REQUIRED_PRE_RUN_FILES'}
    body=[node for node in tree.body if
          (isinstance(node,ast.FunctionDef) and node.name in {'_hash','_pinned','_check_identity'}) or
          (isinstance(node,ast.ClassDef) and node.name=='Unresolved') or
          (isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
           and node.targets[0].id in names)]
    binding=ast.parse(snapshots[catalog['binding_module']])
    values=[ast.literal_eval(node.value) for node in binding.body if isinstance(node,ast.Assign)
            and len(node.targets)==1 and isinstance(node.targets[0],ast.Name)
            and node.targets[0].id=='EXPECTED_PRE_RUN_SHA256']
    if len(body)!=9 or len(values)!=1:
        result.update(status='REJECTED',findings=[{'item':'gate-definitions','status':'REJECTED',
                                                  'error':'GATE_DEFINITION_SET_MISMATCH'}])
        return result
    namespace={'__name__':'fp_admitted_identity_gate', 'hashlib':hashlib, 'json':json, 'Path':Path,
               'HERE':virtual_root/Path(catalog['gate_module']).parent,
               '_read_regular':snapshot_read,'EXPECTED_PRE_RUN_SHA256':values[0]}
    try:
        exec(compile(ast.Module(body=body,type_ignores=[]),catalog['gate_module'],'exec'),namespace)
        result['gate_check_executed']=True
        path=namespace['_check_identity']()
        if path!=namespace['HERE']/'native/fp_public_verify.dylib' or set(reads)!=set(catalog['gate_paths']):
            raise ValueError('GATE_INPUT_COVERAGE_MISMATCH')
        result.update(status='OBSERVED',all_declared_gate_inputs_consumed=True)
    except (ValueError,KeyError,TypeError,RuntimeError) as error:
        result.update(status='REJECTED',findings=[{'item':'declared-identity-gate','status':'REJECTED',
                                                  'error':str(error) or 'GATE_CHECK_FAILED'}])
    result.update(gate_snapshot_read_calls=len(reads),gate_read_paths=sorted(set(reads)),
                  consumed_distinct_gate_inputs=len(set(reads)))
    return result
