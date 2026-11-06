"""Partial developer-only IB2/TC2 retained-byte binding consumption.

No authority, chronology, execution-success, complete-closure or admission claim.
Import loads fixed local dependencies; consume itself performs no IO.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
from jsonschema import Draft202012Validator
from types import ModuleType

_BASE = Path(__file__).resolve().parent
_ROOT = _BASE.parents[2]
# Explicit repository paths only: no private schema copies, cwd lookup, or fallback.
_INPUT_PATHS = {
    'real_missing.json': _BASE / 'real_missing.json',
    'canonical_helper.py': _BASE / 'canonical_helper.py',
    'schemas/vc.json': _ROOT / 'schemas/validator_contract_v1.schema.json',
    'schemas/ib.json': _ROOT / 'schemas/implementation_binding_v2.schema.json',
    'schemas/tc1.json': _ROOT / 'schemas/test_contract_v1.schema.json',
    'schemas/tc2.json': _ROOT / 'schemas/test_contract_v2.schema.json',
    'schemas/runtime.json': _ROOT / 'schemas/runtime_profile_v1.schema.json',
}
# Fixed reviewed source identities. Never walk inventories or import the product package.
_PINS = {
    'real_missing.json': 'd0d39c0456c9f5063f00eb9b890fe8f1bafb61e2c687383ed9ddf1fb4beaac5f',
    'canonical_helper.py': 'f9ef49579a5c54757c6660d377275a0ed5f8afdf646f33130651a711005ac9ba',
    'schemas/vc.json': 'ad312dfa33f7d09b14d3abd5123799aafdb9f83caa6a87022eb5f5d11730c34e',
    'schemas/ib.json': '6ecc1a6bed47e47cb3627d5fc0bb9dc58a55ea0aeebff153ce407f315c339d5f',
    'schemas/tc1.json': '934342de9d45ca584b8d4dedd61865edcef563a8ba33927dd24215af54f80545',
    'schemas/tc2.json': 'bf68dffb9893568652a96116d27729c3b08c37c77a3ed77b515314eef34a7124',
    'schemas/runtime.json': 'b2fc759be85d115415c8ca37aec487d4b57537c6e155ac36d3851bed3069ab6a',
}
SLOTS = ('vc', 'ib', 'tc1', 'tc2', 'r4t', 'runtime')
PROFILE = 'FP_IB2_TC2_BINDINGS_DEVELOPMENT_V1'
SCOPES = frozenset(('TRUST_CORE_ADVERSARIAL_MATRIX', 'GENESIS_CANDIDATE_OBJECTS',
                    'GENESIS_SOURCE_PARSER', 'GENESIS_READINESS_VALIDATORS'))
UNVERIFIED = (
    'INDEPENDENT_AUTHORITY_AND_APPLICABILITY', 'AUTHENTICATED_CHRONOLOGY',
    'OBJECT_ID_DERIVATION_PROFILE', 'COMPLETE_R4T_EXECUTION_PROFILE',
    'ACTUAL_EXECUTION_RESULTS', 'FULL_PRODUCT_SUITE_AND_OPERATION_UNIVERSE',
    'SOURCE_PACKAGE_BUILD_LOCK_RUNTIME_CLOSURE', 'COMPONENT_AND_OPERATION_REF_CLOSURE',
    'RPREB_AND_FIVE_REPORT_CONSUMPTION', 'PUBLIC_DOMAIN_EVIDENCE_AND_WORKFLOW',
    'COMPLETE_G10_AND_FINAL_INDEPENDENT_VALIDATION',
)

def _hash(raw):
    return hashlib.sha256(raw).hexdigest()

def _pinned_bytes(relative):
    raw = _INPUT_PATHS[relative].read_bytes()
    if _hash(raw) != _PINS[relative]:
        raise RuntimeError('Pinned local dependency changed: ' + relative)
    return raw

# Load only the hash-checked known helper bytes, without product-package imports
# or module search-path substitution. This does not pin the full Python runtime.
_HELPER = ModuleType('_ml_b01a_canonical')
_HELPER.__file__ = str(_BASE / 'canonical_helper.py')
exec(compile(_pinned_bytes('canonical_helper.py'), _HELPER.__file__, 'exec'), _HELPER.__dict__)
canonical_json = _HELPER.canonical_json
parse_json_strict = _HELPER.parse_json_strict
verify_sealed_object = _HELPER.verify_sealed_object

def _load(relative):
    return parse_json_strict(_pinned_bytes(relative))

_SCHEMAS = {slot: _load('schemas/' + slot + '.json') for slot in SLOTS if slot != 'r4t'}
for _schema in _SCHEMAS.values():
    Draft202012Validator.check_schema(_schema)
_VALIDATORS = {slot: Draft202012Validator(s) for slot, s in _SCHEMAS.items()}
_DEFS = _SCHEMAS['vc']['$defs']
_TOKEN = {'$ref': '#/$defs/token'}
_REF = {'$ref': '#/$defs/exact_ref'}
_SHA = {'$ref': '#/$defs/sha256'}

def _closed(properties):
    return {'type': 'object', 'additionalProperties': False,
            'required': list(properties), 'properties': properties}

_EXPECTED_SCHEMA = {
    **_closed({
        'profile': {'const': PROFILE},
        'refs': _closed({slot: _REF for slot in SLOTS}),
        'tc1_raw_sha256': _SHA,
        'legacy_validator_binding': _SCHEMAS['ib']['properties']['legacy_validator_binding'],
        'versions': _closed({slot: _TOKEN for slot in SLOTS if slot != 'r4t'}),
        'runtime_identity': _SCHEMAS['runtime']['$defs']['runtime_identity'],
    }), '$defs': _DEFS,
}
# IB2 definitions include additional legacy container definitions; runtime identity
# uses the same token definition. All schema references are local, never network.
_EXPECTED_SCHEMA['$defs'] = _SCHEMAS['ib']['$defs']
Draft202012Validator.check_schema(_EXPECTED_SCHEMA)
_EXPECTED_VALIDATOR = Draft202012Validator(_EXPECTED_SCHEMA)
_R4T_SUBSET = {
    'type': 'object', 'required': ['object_type', 'schema_version', 'object_id',
        'payload_sha256', 'content_sha256', 'test_definition_ref',
        'test_definition_raw_sha256', 'runtime_profile_ref'],
    'properties': {'object_type': {'const': 'DevelopmentTestRunReport'},
        'schema_version': {'const': '1.0'}, 'object_id': {'$ref': '#/$defs/object_id'},
        'payload_sha256': _SHA, 'content_sha256': _SHA,
        'test_definition_ref': _REF, 'test_definition_raw_sha256': _SHA,
        'runtime_profile_ref': _REF},
    '$defs': _DEFS,
    # This is explicitly a subset, not an official/full R4T schema.
}
_R4T_VALIDATOR = Draft202012Validator(_R4T_SUBSET)
_REAL_MISSING = tuple(_load('real_missing.json'))
if len(_REAL_MISSING) != 29 or len(set(_REAL_MISSING)) != 29:
    raise RuntimeError('Unexpected real_missing baseline')
_DEFINITION_FIELDS = tuple(k for k in _SCHEMAS['tc1']['properties'] if k not in {
    'object_type', 'schema_version', 'test_contract_version', 'object_id',
    'payload_sha256', 'content_sha256'})
_FUTURE_KEYS = frozenset(('validator_contract_ref', 'main_validator_contract_ref',
    'trusted_manifest_ref', 'manifest_ref', 'manifest_acceptance_ref',
    'signed_acceptance_ref', 'post_test_contract_ref'))

def _equal(left, right):
    # Canonical equality avoids Python's bool == int equivalence.
    return canonical_json(left) == canonical_json(right)

def _ref(obj):
    return {key: obj[key] for key in ('object_id', 'content_sha256')}

def _has_future(value, future_ids):
    # Iterative traversal accepts arbitrary JSON details without hashability or
    # extra recursion assumptions. Unknown execution semantics stay unverified.
    pending = [value]
    while pending:
        item = pending.pop()
        if isinstance(item, dict):
            object_id = item.get('object_id')
            if _FUTURE_KEYS.intersection(item) or (isinstance(object_id, str) and object_id in future_ids):
                return True
            pending.extend(item.values())
        elif isinstance(item, list):
            pending.extend(item)
    return False

def consume(expected: dict, records: dict[str, bytes]) -> dict:
    """Consume explicit bytes under developer controls; never return real PASS.

    Error outputs contain codes and fixed slot/field names, not supplied bytes.
    Invalid expected controls cannot select schemas, authority or eligibility.
    """
    failures = []
    def fail(code, slot, field=''):
        item = {'code': code, 'slot': slot, 'field': field}
        if item not in failures:
            failures.append(item)
    controls_ok = False
    try:
        canonical_json(expected)
        controls_ok = isinstance(expected, dict) and _EXPECTED_VALIDATOR.is_valid(expected)
    except (TypeError, ValueError, RecursionError):
        pass
    if not controls_ok:
        fail('INVALID_EXPECTED', 'expected')
    if not isinstance(records, dict):
        fail('INVALID_INPUT_RECORDS', 'records')
        records = {}
    missing = [slot for slot in SLOTS if slot not in records]
    if set(records) - set(SLOTS):
        fail('UNKNOWN_INPUT_SLOT', 'records')
    future_ids = set()
    if controls_ok:
        future_ids = {expected['refs'][s]['object_id'] for s in ('vc', 'ib', 'tc2')}
    objects = {}
    for slot in SLOTS:
        if slot not in records:
            continue
        try:
            if not isinstance(records[slot], bytes):
                raise ValueError('bytes required')
            obj = parse_json_strict(records[slot])
            if not isinstance(obj, dict):
                raise ValueError('object required')
        except (TypeError, ValueError, RecursionError):
            fail('INVALID_RECORD', slot)
            continue
        if slot in ('tc1', 'r4t') and _has_future(obj, future_ids):
            fail('FUTURE_REFERENCE', slot)
        try:
            validator = _R4T_VALIDATOR if slot == 'r4t' else _VALIDATORS[slot]
            shape_ok = validator.is_valid(obj)
            if not shape_ok:
                fail('R4T_BINDING_SHAPE' if slot == 'r4t' else 'SCHEMA_MISMATCH', slot)
            seal_ok = verify_sealed_object(obj)
        except RecursionError:
            # Parsing and resealing have different call-stack overhead. Keep
            # all missing/hard diagnostics when either validation hits its limit.
            fail('INPUT_VALIDATION_LIMIT', slot)
            continue
        if not seal_ok:
            fail('INVALID_SEAL', slot)
        if not shape_ok or not seal_ok:
            continue
        objects[slot] = obj
        if controls_ok and not _equal(_ref(obj), expected['refs'][slot]):
            fail('EXPECTED_REF_MISMATCH', slot)
        if controls_ok and slot != 'r4t':
            field = {'vc':'contract_version', 'ib':'binding_version', 'tc1':'test_contract_version',
                     'tc2':'test_contract_version', 'runtime':'runtime_profile_version'}[slot]
            if obj[field] != expected['versions'][slot]:
                fail('VERSION_MISMATCH', slot, field)

    def link(slot, value, target, field):
        if target in objects and not _equal(value, _ref(objects[target])):
            fail('CROSS_REF_MISMATCH', slot, field)
    for slot in ('vc', 'ib', 'tc1', 'tc2', 'r4t'):
        if slot in objects:
            link(slot, objects[slot]['runtime_profile_ref'], 'runtime', 'runtime_profile_ref')
    if 'vc' in objects:
        vc = objects['vc']
        link('vc', vc['implementation_binding_ref'], 'ib', 'implementation_binding_ref')
        link('vc', vc['test_contract_ref'], 'tc2', 'test_contract_ref')
    if 'ib' in objects:
        ib = objects['ib']; legacy = ib['legacy_validator_binding']
        if controls_ok and not _equal(legacy, expected['legacy_validator_binding']):
            fail('LEGACY_DECLARATION_MISMATCH', 'ib', 'legacy_validator_binding')
        if not SCOPES.issubset(legacy['required_test_scope']):
            fail('REQUIRED_SCOPE_OMISSION', 'ib', 'required_test_scope')
        if 'runtime' in objects and not _equal(ib['dependency_lock_ref'],
                objects['runtime']['dependency_environment']['dependency_lock_ref']):
            fail('CROSS_REF_MISMATCH', 'ib', 'dependency_lock_ref')
    if controls_ok and 'runtime' in objects and not _equal(
            objects['runtime']['runtime_identity'], expected['runtime_identity']):
        fail('RUNTIME_IDENTITY_MISMATCH', 'runtime', 'runtime_identity')
    if 'tc1' in objects and controls_ok and _hash(records['tc1']) != expected['tc1_raw_sha256']:
        fail('TC1_RAW_MISMATCH', 'tc1')
    if 'tc2' in objects:
        post = objects['tc2']; binding = post['execution_binding']
        link('tc2', binding['test_definition_ref'], 'tc1', 'test_definition_ref')
        link('tc2', binding['test_report_ref'], 'r4t', 'test_report_ref')
        if 'tc1' in objects:
            pre = objects['tc1']
            for field in _DEFINITION_FIELDS:
                if not _equal(pre[field], post[field]):
                    fail('TC_DEFINITION_DRIFT', 'tc2', field)
        if 'r4t' in objects and binding['test_report_raw_sha256'] != _hash(records['r4t']):
            fail('R4T_RAW_MISMATCH', 'tc2', 'test_report_raw_sha256')
        if 'ib' in objects:
            report = objects['ib']['legacy_validator_binding']['test_report']
            if report['filename'] != binding['test_report_filename']:
                fail('R4T_FILENAME_MISMATCH', 'ib', 'test_report.filename')
    if 'r4t' in objects:
        report = objects['r4t']
        link('r4t', report['test_definition_ref'], 'tc1', 'test_definition_ref')
        if 'tc1' in objects and report['test_definition_raw_sha256'] != _hash(records['tc1']):
            fail('TC1_RAW_MISMATCH', 'r4t', 'test_definition_raw_sha256')
        if 'ib' in objects and objects['ib']['legacy_validator_binding']['test_report']['sha256'] != _hash(records['r4t']):
            fail('R4T_RAW_MISMATCH', 'ib', 'test_report.sha256')
    for slot in ('tc1', 'tc2'):
        if slot not in objects:
            continue
        obj = objects[slot]
        commands = [c['command_id'] for c in obj['command_declarations']]
        coverage = obj['operation_coverage']
        ops = [c['operation_id'] for c in coverage]
        if len(commands) != len(set(commands)) or len(ops) != len(set(ops)):
            fail('DUPLICATE_COMMAND_OR_OPERATION', slot)
        covered = {cmd for c in coverage for cmd in c['command_ids']}
        if covered != set(commands):
            fail('COMMAND_COVERAGE_MISMATCH', slot)
    local_ok = controls_ok and not missing and not failures
    return {
        'profile': PROFILE, 'development_only': True,
        'verdict': 'REJECT' if failures else 'UNRESOLVED',
        'binding_verdict': 'LOCAL_CANDIDATE_BINDINGS_VERIFIED' if local_ok else 'NOT_VERIFIED',
        'missing_inputs': missing, 'failures': failures,
        'unverified_obligations': list(UNVERIFIED), 'real_missing': list(_REAL_MISSING),
        'REAL_ADMISSION': 'NOT_READY', 'REAL_G02_G03': 'NOT_ESTABLISHED',
        'REAL_GENESIS_READINESS': 'NOT_ESTABLISHED', 'prospective_eligible': False,
        'PROTOCOL_STATE_CHANGE': 'NONE',
    }
