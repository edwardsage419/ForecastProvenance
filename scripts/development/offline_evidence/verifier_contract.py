"""Exact developer verifier-use content and eight anchors; no verification API."""
import hashlib
from pathlib import Path
from types import ModuleType

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT/'docs/development/verifier-contract-consumption-2026-10-25-rev-001'
CONTRACT_RAW = '05fa6b5a9be36a560046c7b2e24b06e4124dce60af7877b28493d076a2120e79'
CONTRACT_REF = {'object_id': 'verifier-contract:initial-ma3:strict-c-dev:v1',
                'content_sha256': '1a2c215289e95f4c2b955468314e05488b8d1dfe2ed20b7562165cccb6e3f160'}
SUCCESSOR_RAW = 'd304ada9f6f09887a95a419e8c03682627f1bfa0f768ad7e9085db5f87b51cf3'
SUCCESSOR_REF = {'object_id': 'verifier-contract:initial-ma3:strict-c-dev:v2',
                 'content_sha256': '2d2edd93cdb477942ec7466fadfd96df21e63bd3fe507f109f3af0b5eebfe5d8'}
EXECUTION_CATALOG = 'docs/development/verifier-execution-contract-successor-2026-10-28-rev-001/EXECUTION_INPUTS.json'
EXECUTION_CATALOG_SHA = '33c556c33ba92556e85b3c17eddc431b697589c6f07cacaed4a0628dca5f5480'


def _fixed(path, digest):
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != digest:
        raise RuntimeError('D211_FIXED_DEPENDENCY_CHANGED')
    return raw


path = ROOT/'scripts/development/offline_evidence/signing_profile.py'
_P = ModuleType('d211_fixed_profile'); _P.__file__ = str(path)
exec(compile(_fixed(path, 'ea28e595ce0b8d6996ca7dfbf40aa42a60bee19f07cb4755427032e4c74149ff'),
             str(path), 'exec'), _P.__dict__)
_C = _P.canonical
_SCHEMA = _C.parse_json_strict(_fixed(PACKAGE/'CONTRACT_SCHEMA_CANDIDATE.json',
    '08edcb7b2572f8d9d783b6f7079bb6a5f294e0823efa357747a3b419325ef9a5'))
_ARTIFACTS = _C.parse_json_strict(_fixed(PACKAGE/'ARTIFACT_INPUTS.json',
    '475ea94672662aaee9681b0b3e594574a05570b888aa949fc00de7f00232c81a'))
Draft202012Validator.check_schema(_SCHEMA)
_VALIDATOR = Draft202012Validator(_SCHEMA)


def _execution_support(inputs, error, missing):
    """Admit a fixed finite snapshot before compiling the existing passive consumer.

    This API reads no files, executes no D271 child or native function, and does
    not treat the fixed catalogue as the independent complete runtime universe.
    """
    result = {'status': 'NOT_CHECKED'}
    if inputs is None:
        missing.append('execution_inputs')
        return result, 'NOT_CHECKED'
    if type(inputs) is not dict:
        error('EXECUTION_INPUT_MAPPING_INVALID')
        return result, 'NOT_CHECKED'
    raw = inputs.get(EXECUTION_CATALOG)
    if raw is None:
        missing.append('execution:'+EXECUTION_CATALOG)
        return result, 'NOT_CHECKED'
    if (type(raw) is not bytes or len(raw) > 1048576
            or hashlib.sha256(raw).hexdigest() != EXECUTION_CATALOG_SHA):
        error('EXECUTION_CATALOG_IDENTITY_MISMATCH')
        return result, 'NOT_CHECKED'
    catalogue = _C.parse_json_strict(raw)
    expected = catalogue['inputs']
    allowed = {row['path'] for row in expected} | {EXECUTION_CATALOG}
    valid = True
    if any(type(key) is not str for key in inputs) or set(inputs)-allowed:
        error('EXECUTION_INPUT_ROLES_INVALID'); valid = False
    snapshots, total = {}, len(raw)
    for row in expected:
        name = row['path']; body = inputs.get(name)
        if body is None:
            missing.append('execution:'+name); valid = False
        elif (type(body) is not bytes or len(body) > 1048576
              or len(body) != row['bytes'] or hashlib.sha256(body).hexdigest() != row['sha256']):
            error('EXECUTION_IDENTITY_MISMATCH:'+name); valid = False
        else:
            snapshots[name] = body; total += len(body)
    if total > 67108864:
        error('EXECUTION_SNAPSHOT_BUDGET_EXCEEDED'); valid = False
    if not valid:
        return result, 'NOT_CHECKED'
    # All source and evidence identities are admitted before this compile. The
    # admitted public_math source only consumes retained observations.
    source_name = catalogue['public_math_consumer']
    module = ModuleType('d279_admitted_retained_math')
    exec(compile(snapshots[source_name], source_name, 'exec'), module.__dict__)
    result = module.consume(snapshots[catalogue['public_math_manifest']],
                            lambda row: snapshots.get(row['path']))
    if result['status'] != 'OBSERVED':
        error('EXECUTION_RETAINED_SUPPORT_NOT_OBSERVED')
    definition = snapshots[catalogue['build_definition']]
    build = _C.parse_json_strict(snapshots[catalogue['build_result']])
    binding = _C.parse_json_strict(snapshots[catalogue['build_binding']])
    native = _ARTIFACTS['native_binary']
    rebuild_ok = (build['definition_sha256'] == hashlib.sha256(definition).hexdigest()
                  and build['binary_sha256'] == native['sha256']
                  and build['old_binary_sha256'] == native['sha256']
                  and build['binary_equal_to_old'] is True
                  and binding['new_binary_sha256'] == native['sha256']
                  and binding['retained_math_input'] == native
                  and binding['math_execution_source_sha256'] == result.get('source_sha256')
                  and build['native_loaded'] is False and build['crypto_executed'] is False
                  and binding['native_reexecuted_for_this_link'] is False
                  and build['full_build_runtime_closure'] == 'NOT_ESTABLISHED'
                  and build['protocol_state_change'] == binding['protocol_state_change'] == 'NONE')
    if not rebuild_ok:
        error('EXECUTION_SAME_BINARY_BUILD_BINDING_INVALID')
    return result, 'OBSERVED' if rebuild_ok else 'REJECTED'


def consume(contract_bytes, profile_bytes, rule_bytes=None, artifact_bytes=None, *, execution_inputs=None):
    """Pure finite comparisons, including the real D189 child; never authenticate.

    Files are admitted at import. This function accepts only supplied bytes and
    does not load the described adapter or dylib. The eight anchors are not the
    existing backend's complete gate/input/runtime closure. Result descriptions
    are content, not observations of a caller's signature or result callback.
    """
    child = _P.consume(profile_bytes, rule_bytes)
    errors, missing = list(child['errors']), list(child['missing'])

    def error(code):
        if code not in errors:
            errors.append(code)

    successor = (type(contract_bytes) is bytes and len(contract_bytes) <= 1048576
                 and hashlib.sha256(contract_bytes).hexdigest() == SUCCESSOR_RAW)
    expected_ref = SUCCESSOR_REF if successor else CONTRACT_REF
    expected_raw = SUCCESSOR_RAW if successor else CONTRACT_RAW
    contract = None
    if contract_bytes is None:
        missing.append('contract_bytes')
    else:
        if (type(contract_bytes) is not bytes or len(contract_bytes) > 1048576
                or hashlib.sha256(contract_bytes).hexdigest() != expected_raw):
            error('CONTRACT_RAW_MISMATCH')
        try:
            if type(contract_bytes) is not bytes or len(contract_bytes) > 1048576:
                raise ValueError('bytes/size')
            contract = _C.parse_json_strict(contract_bytes)
            if type(contract) is not dict:
                raise ValueError('object')
        except (ValueError, TypeError, RecursionError):
            error('CONTRACT_JSON_INVALID')
        else:
            # v2 is an exact raw-identity candidate, not a caller-selected schema
            # or arbitrary resealed successor. v1 retains its original validator.
            if not successor and not _VALIDATOR.is_valid(contract):
                error('CONTRACT_SHAPE_INVALID')
            try:
                if not _C.verify_sealed_object(contract):
                    error('CONTRACT_SEAL_INVALID')
            except (ValueError, TypeError, KeyError, RecursionError):
                error('CONTRACT_SEAL_INVALID')
            if contract.get('contract_id') != contract.get('object_id'):
                error('CONTRACT_SEMANTIC_ID_MISMATCH')
            if {key:contract.get(key) for key in expected_ref} != expected_ref:
                error('CONTRACT_FULL_REF_MISMATCH')
            if contract.get('profile_ref') != _P.PROFILE_REF:
                error('CONTRACT_PROFILE_REF_MISMATCH')

    if rule_bytes is not None:
        try:
            if type(rule_bytes) is not bytes or len(rule_bytes) > 1048576:
                raise ValueError('bytes/size')
            rule = _C.parse_json_strict(rule_bytes)
            reference = rule['rules']['signing_semantics']['verifier_contract_ref']
        except (ValueError, TypeError, KeyError, RecursionError):
            error('RULE_VERIFIER_USES_INVALID')
        else:
            if reference != expected_ref:
                error('RULE_VERIFIER_CONTRACT_REF_MISMATCH')

    supplied = {}
    if artifact_bytes is None:
        missing.append('artifact_bytes')
    elif type(artifact_bytes) is not dict:
        error('ARTIFACT_MAPPING_INVALID')
    else:
        supplied = {key:value for key,value in artifact_bytes.items() if type(key) is str}
        if len(supplied) != len(artifact_bytes) or set(supplied)-set(_ARTIFACTS):
            error('ARTIFACT_ROLES_INVALID')
    statuses = {}
    for role, expected in _ARTIFACTS.items():
        raw = supplied.get(role)
        if raw is None:
            missing.append('artifact:'+role)
            status = 'MISSING'
        elif (type(raw) is not bytes or len(raw) != expected['bytes']
                or hashlib.sha256(raw).hexdigest() != expected['sha256']):
            error('ARTIFACT_IDENTITY_MISMATCH:'+role)
            status = 'REJECTED'
        else:
            status = 'OBSERVED'
        statuses[role] = {'status':status, 'expected_bytes':expected['bytes'],
                          'expected_sha256':expected['sha256']}
    execution, rebuild_status = None, None
    if successor:
        execution, rebuild_status = _execution_support(execution_inputs, error, missing)
    elif execution_inputs is not None:
        error('EXECUTION_INPUTS_REQUIRE_EXACT_SUCCESSOR')
    contract_ok = contract is not None and not any(e.startswith('CONTRACT_') for e in errors)
    artifact_errors = any(e.startswith('ARTIFACT_') for e in errors)
    artifact_missing = any(s['status'] == 'MISSING' for s in statuses.values())
    artifact_status = 'REJECTED' if artifact_errors else 'MISSING' if artifact_missing else 'OBSERVED'
    matched = contract_ok and not errors and not missing
    result = {'scope':'EXACT_D211_CONTRACT_EIGHT_ANCHORS_AND_SUPPLIED_RULE_LOCAL_COMPARISON_ONLY',
            'status':'REJECTED' if errors else 'MISSING' if missing else 'OBSERVED',
            'verdict':'REJECT' if errors else 'UNRESOLVED', 'errors':errors, 'missing':missing,
            'contract_content_status':'OBSERVED' if contract_ok else 'MISSING' if contract_bytes is None else 'REJECTED',
            'contract_ref':dict(expected_ref) if contract_ok else None,
            'artifact_binding_status':artifact_status, 'artifact_statuses':statuses,
            'profile_result':child,
            'proposed_verifier_use_status':'REJECTED' if errors else 'OBSERVED' if matched else 'MISSING',
            'local_three_signing_uses':'LOCAL_DEVELOPMENT_THREE_USES_MATCHED' if matched else 'NOT_VERIFIED',
            'operational_bindings_established':0,
            'independent_authority_and_applicability':'NOT_ESTABLISHED',
            'effective_boundary':'NOT_ESTABLISHED', 'public_authentication':'NOT_ESTABLISHED',
            'full_build_runtime_closure':'NOT_ESTABLISHED', 'message_resource_policy':'NOT_ESTABLISHED',
            'execution_contract_complete':'NOT_ESTABLISHED',
            'all_source_and_gate_inputs_checked':'NOT_ESTABLISHED',
            'backend_called':False, 'native_loaded':False, 'message_constructed':False, 'carrier_constructed':False,
            'real_admission':'NOT_READY', 'prospective_eligible':False, 'protocol_state_change':'NONE'}
    if successor:
        result.update(scope='EXACT_D279_TECHNICAL_SUCCESSOR_RETAINED_SUPPORT_NOT_FUTURE_MA3_AUTHENTICATION',
                      predecessor_ref=dict(CONTRACT_REF), technical_execution_support=execution,
                      same_binary_rebuild_support=rebuild_status,
                      execution_evidence_scope='FIXED_PUBLIC_SAMPLES_NOT_COMPLETE_FPP_RUN',
                      default_rule_refs_migrated=False,
                      future_initial_ma3_execution_applicability='NOT_ESTABLISHED')
        if execution['status'] == 'OBSERVED':
            result['message_resource_policy'] = 'DEVELOPMENT_FIXED_SAMPLE_POLICY_BOUND'
    return result
