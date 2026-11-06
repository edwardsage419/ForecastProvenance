"""Keyless synthetic bytes for API behavior tests; never protocol evidence."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from canonical_helper import canonical_json, seal_object

SLOTS = ('vc', 'ib', 'tc1', 'tc2', 'r4t', 'runtime')
SCOPES = ['TRUST_CORE_ADVERSARIAL_MATRIX', 'GENESIS_CANDIDATE_OBJECTS',
          'GENESIS_SOURCE_PARSER', 'GENESIS_READINESS_VALIDATORS']

def ref(obj):
    return {k: obj[k] for k in ('object_id', 'content_sha256')}

def external(name):
    return {'object_id': 'synthetic:' + name,
            'content_sha256': hashlib.sha256(name.encode()).hexdigest()}

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def case(hooks=None):
    """Reseal changed records and propagate references to isolate binding checks.

    Expected full refs are repinned ONLY in synthetic tests, never in real intake.
    Expected legacy declarations/versions are fixed separately from hooks.
    """
    hooks = hooks or {}
    objects, records = {}, {}
    def put(slot, kind, payload):
        if slot in hooks:
            hooks[slot](payload)
        obj = seal_object(payload, object_type=kind, stable_context='synthetic-' + slot)
        objects[slot] = obj
        records[slot] = canonical_json(obj) + b'\n'
        return obj
    runtime = put('runtime', 'RuntimeProfile', {
        'schema_version': '1.0', 'runtime_profile_version': 'synthetic-runtime-v1',
        'runtime_identity': {'runtime_name': 'PYTHON', 'runtime_version': 'synthetic-3.11'},
        'execution_engine': {'engine_id': 'synthetic-python', 'executable_sha256': '1' * 64},
        'dependency_environment': {'dependency_lock_ref': external('lock'), 'environment_variables': []},
        'platform_constraints': ['synthetic-only'],
        'deterministic_settings': [{'setting_id': 'synthetic-setting', 'value': True}]})
    definition = {'fixture_refs': [external('fixture')],
        'command_declarations': [{'command_id': 'binding-tests', 'argv': ['python', 'test_consumer.py']}],
        'runtime_profile_ref': ref(runtime),
        'operation_coverage': [{'operation_id': 'synthetic-binding', 'command_ids': ['binding-tests']}],
        'expected_result_vocabulary': ['PASS', 'FAIL'], 'projection_profile_ref': external('projection')}
    tc1 = put('tc1', 'TestContract', {'schema_version': '1.0',
        'test_contract_version': 'synthetic-pre-v1', **deepcopy(definition)})
    r4t = put('r4t', 'DevelopmentTestRunReport', {'schema_version': '1.0',
        'test_definition_ref': ref(tc1), 'test_definition_raw_sha256': digest(records['tc1']),
        'runtime_profile_ref': ref(runtime),
        'synthetic_note': 'binding fixture only; no execution chronology claim'})
    # Copy the actual pre-definition after any test hook; then allow independent post drift.
    definition_keys = tuple(definition)
    tc2 = put('tc2', 'TestContract', {'schema_version': '2.0',
        'test_contract_version': 'synthetic-post-v2',
        **{k: deepcopy(tc1[k]) for k in definition_keys},
        'execution_binding': {'test_definition_ref': ref(tc1), 'test_report_ref': ref(r4t),
            'test_report_raw_sha256': digest(records['r4t']), 'test_report_filename': 'synthetic-r4t.json'}})
    legacy = {'object_role': 'NORMATIVE', 'validator_version': 'synthetic-validator-v1',
        'git_commit': '2' * 40, 'implementation_language': 'PYTHON', 'python_requirement': '>=3.11',
        'runtime_dependencies': ['synthetic-dependency'],
        'source_files': [{'path': 'synthetic/source.py', 'sha256': '3' * 64}],
        'test_report': {'filename': 'synthetic-r4t.json', 'sha256': digest(records['r4t'])},
        'required_test_scope': SCOPES[:],
        'change_policy': 'ANY_CONSEQUENTIAL_FILE_OR_RUNTIME_CHANGE_REQUIRES_NEW_VALIDATOR_CONTRACT'}
    ib = put('ib', 'ImplementationBinding', {'schema_version': '2.0',
        'binding_version': 'synthetic-binding-v2', 'source_file_manifest_ref': external('sources'),
        'package_artifact_ref': external('package'), 'dependency_lock_ref': external('lock'),
        'runtime_profile_ref': ref(runtime),
        'entrypoint_bindings': [{'operation_id': 'synthetic-binding', 'logical_entrypoint_id': 'synthetic-entry',
            'source_unit_ref': external('unit'), 'symbol': 'consume'}],
        'legacy_validator_binding': deepcopy(legacy)})
    put('vc', 'ValidatorContract', {'schema_version': '1.0', 'contract_version': 'synthetic-validator-v1',
        'authority_scope': 'DEVELOPMENT_TEST_ONLY', 'component_contract_refs': [external('component')],
        'operation_registry_ref': external('operations'), 'implementation_binding_ref': ref(ib),
        'test_contract_ref': ref(tc2), 'runtime_profile_ref': ref(runtime)})
    expected = {'profile': 'FP_IB2_TC2_BINDINGS_DEVELOPMENT_V1',
        'refs': {slot: ref(objects[slot]) for slot in SLOTS},
        'tc1_raw_sha256': digest(records['tc1']), 'legacy_validator_binding': legacy,
        'versions': {'vc': 'synthetic-validator-v1', 'ib': 'synthetic-binding-v2',
            'tc1': 'synthetic-pre-v1', 'tc2': 'synthetic-post-v2', 'runtime': 'synthetic-runtime-v1'},
        'runtime_identity': {'runtime_name': 'PYTHON', 'runtime_version': 'synthetic-3.11'}}
    return expected, records

if __name__ == '__main__':
    import sys
    dest = Path(sys.argv[1]); dest.mkdir(exist_ok=False)
    expected, records = case()
    (dest/'expected.json').write_bytes(canonical_json(expected) + b'\n')
    for slot, raw in records.items():
        (dest/(slot+'.json')).write_bytes(raw)
