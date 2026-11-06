"""Bounded candidate-binding behavior tests, no keys or real signed objects."""
from copy import deepcopy
import json
import sys
import subprocess
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from test_support import SLOTS, SCOPES, case, external
from canonical_helper import canonical_json
try:
    from consumer import consume
except ModuleNotFoundError as exc:
    if exc.name != 'consumer':
        raise
    consume = None

_BASE = Path(__file__).resolve().parent
_ROOT = _BASE.parents[2]
_SCHEMA_NAMES = (
    'validator_contract_v1.schema.json', 'implementation_binding_v2.schema.json',
    'test_contract_v1.schema.json', 'test_contract_v2.schema.json',
    'runtime_profile_v1.schema.json',
)


def _copy_repository(destination):
    """Copy only explicit safe rollout dependencies; never scan a checkout."""
    destination = Path(destination)
    entry = destination / 'scripts/development/ib2_tc2_bindings'
    entry.mkdir(parents=True)
    (destination / 'schemas').mkdir()
    for name in ('consumer.py', 'canonical_helper.py', 'real_missing.json', 'replay.py'):
        source = _BASE / name
        if not source.is_file():
            raise AssertionError('Missing rollout file: ' + str(source))
        (entry / name).write_bytes(source.read_bytes())
    for name in _SCHEMA_NAMES:
        source = _ROOT / 'schemas' / name
        if not source.is_file():
            raise AssertionError('Missing rollout schema: ' + str(source))
        (destination / 'schemas' / name).write_bytes(source.read_bytes())
    return entry


def _write_case(directory):
    directory.mkdir()
    expected, records = case()
    (directory / 'expected.json').write_bytes(canonical_json(expected))
    for slot, raw in records.items():
        (directory / (slot + '.json')).write_bytes(raw)


class ConsumerTests(unittest.TestCase):
    def run_case(self, expected, records):
        self.assertIsNotNone(consume, 'Missing candidate IB2/TC2 consumption API')
        return consume(expected, records)

    def ceilings(self, result):
        self.assertTrue(result['development_only'])
        self.assertEqual(result['REAL_ADMISSION'], 'NOT_READY')
        self.assertEqual(result['REAL_G02_G03'], 'NOT_ESTABLISHED')
        self.assertEqual(result['REAL_GENESIS_READINESS'], 'NOT_ESTABLISHED')
        self.assertIs(result['prospective_eligible'], False)
        self.assertEqual(result['PROTOCOL_STATE_CHANGE'], 'NONE')
        self.assertEqual(len(result['real_missing']), 29)
        self.assertEqual(result['real_missing'][0], 'A.root_bytes_and_accepted_provenance')
        self.assertEqual(result['real_missing'][-1], 'I.final_independent_validation_and_Genesis_authorization')

    def reject(self, expected, records, code=None):
        result = self.run_case(expected, records)
        self.ceilings(result)
        self.assertEqual(result['verdict'], 'REJECT')
        self.assertEqual(result['binding_verdict'], 'NOT_VERIFIED')
        if code:
            self.assertIn(code, [f['code'] for f in result['failures']])
        return result

    def test_positive_remains_unresolved(self):
        result = self.run_case(*case())
        self.ceilings(result)
        self.assertEqual(result['verdict'], 'UNRESOLVED')
        self.assertEqual(result['binding_verdict'], 'LOCAL_CANDIDATE_BINDINGS_VERIFIED')
        self.assertEqual(result['failures'], [])
        self.assertEqual(result['missing_inputs'], [])
        self.assertIn('AUTHENTICATED_CHRONOLOGY', result['unverified_obligations'])
        self.assertIn('COMPLETE_R4T_EXECUTION_PROFILE', result['unverified_obligations'])

    def test_missing_all_is_unresolved_not_empty_success(self):
        expected, _ = case()
        result = self.run_case(expected, {})
        self.ceilings(result)
        self.assertEqual(result['missing_inputs'], list(SLOTS))
        self.assertEqual(result['binding_verdict'], 'NOT_VERIFIED')
        self.assertEqual(result['verdict'], 'UNRESOLVED')

    def test_missing_and_hard_failure_both_retained(self):
        expected, records = case(); del records['ib']; records['vc'] = b'{bad json'
        result = self.reject(expected, records, 'INVALID_RECORD')
        self.assertEqual(result['missing_inputs'], ['ib'])

    def test_strict_json_failures(self):
        expected, original = case()
        bad = [b'\xef\xbb\xbf'+original['r4t'], b'{"x":1,"x":2}', b'null', b'[]',
               b'{"x":1.0}', b'{"x":-0}', b'{"x":NaN}', b'{"x":9007199254740992}',
               b'{"x":"\\ud800"}', b'\xff', b'{"x":null}']
        for raw in bad:
            with self.subTest(raw=raw[:20]):
                records = dict(original); records['r4t'] = raw
                self.reject(expected, records, 'INVALID_RECORD')

    def test_unsealed_and_wrong_expected_ref(self):
        expected, records = case(); obj = json.loads(records['vc']); obj['authority_scope'] = 'changed'
        records['vc'] = canonical_json(obj)
        self.reject(expected, records, 'INVALID_SEAL')
        expected, records = case(); expected['refs']['vc']['content_sha256'] = 'f'*64
        self.reject(expected, records, 'EXPECTED_REF_MISMATCH')

    def test_full_ref_not_replaced_by_raw_hash(self):
        expected, records = case(); from test_support import digest
        expected['refs']['r4t']['content_sha256'] = digest(records['r4t'])
        self.reject(expected, records, 'EXPECTED_REF_MISMATCH')

    def test_same_semantic_r4t_different_raw_rejected(self):
        expected, records = case(); records['r4t'] += b' \n'
        self.reject(expected, records, 'R4T_RAW_MISMATCH')

    def test_tc1_same_semantic_different_raw_rejected(self):
        expected, records = case(); records['tc1'] += b'\n'
        self.reject(expected, records, 'TC1_RAW_MISMATCH')

    def test_definition_drift_all_fields(self):
        changes = {
            'fixture_refs': [external('different-fixture')],
            'command_declarations': [{'command_id':'other', 'argv':['other']}],
            'runtime_profile_ref': external('other-runtime'),
            'operation_coverage': [{'operation_id':'other', 'command_ids':['binding-tests']}],
            'expected_result_vocabulary': ['OTHER'], 'projection_profile_ref': external('other-projection')}
        for field, value in changes.items():
            with self.subTest(field=field):
                self.reject(*case({'tc2': lambda p, k=field, v=value: p.update({k:v})}), 'TC_DEFINITION_DRIFT')

    def test_legacy_all_ten_omissions_and_replacements(self):
        expected, _ = case(); original = expected['legacy_validator_binding']
        for field in original:
            with self.subTest(field=field, action='omit'):
                self.reject(*case({'ib':lambda p,k=field:p['legacy_validator_binding'].pop(k)}), 'SCHEMA_MISMATCH')
            value = original[field]
            replacement = 'changed' if isinstance(value,str) else ([] if isinstance(value,list) else {})
            with self.subTest(field=field, action='replace'):
                self.reject(*case({'ib':lambda p,k=field,v=replacement:p['legacy_validator_binding'].update({k:v})}))

    def test_four_original_scope_families_cannot_be_reduced(self):
        expected, records = case({'ib':lambda p:p['legacy_validator_binding'].update({'required_test_scope':SCOPES[:-1]})})
        expected['legacy_validator_binding']['required_test_scope'] = SCOPES[:-1]
        self.reject(expected, records, 'REQUIRED_SCOPE_OMISSION')

    def test_versions_and_unknown_fields(self):
        for slot, field in [('vc','contract_version'),('ib','binding_version'),('tc1','test_contract_version'),
                            ('tc2','test_contract_version'),('runtime','runtime_profile_version')]:
            with self.subTest(slot=slot):
                self.reject(*case({slot:lambda p,k=field:p.update({k:'changed'})}), 'VERSION_MISMATCH')
        self.reject(*case({'ib':lambda p:p.update({'unexpected':'extra'})}), 'SCHEMA_MISMATCH')
        self.reject(*case({'tc2':lambda p:p.update({'schema_version':'1.0'})}), 'SCHEMA_MISMATCH')

    def test_empty_expected_and_caller_eligibility_rejected(self):
        expected, records = case()
        for invalid in ({}, {**expected, 'prospective_eligible':True}, {**expected, 'refs':{}},
                        {**expected, 'profile':'other'}):
            with self.subTest(keys=list(invalid)):
                self.reject(invalid, records, 'INVALID_EXPECTED')

    def test_record_slot_allowlist_and_bytes_type(self):
        expected, records = case(); records['root'] = b'{}'
        self.reject(expected, records, 'UNKNOWN_INPUT_SLOT')
        expected, records = case(); records['vc'] = records['vc'].decode()
        self.reject(expected, records, 'INVALID_RECORD')

    def test_runtime_and_lock_links(self):
        for slot, key in [('vc','runtime_profile_ref'),('ib','runtime_profile_ref'),('tc1','runtime_profile_ref'),
                           ('tc2','runtime_profile_ref'),('r4t','runtime_profile_ref'),('ib','dependency_lock_ref')]:
            with self.subTest(slot=slot,key=key):
                self.reject(*case({slot:lambda p,k=key:p.update({k:external('other')})}), 'CROSS_REF_MISMATCH')
        self.reject(*case({'runtime':lambda p:p['runtime_identity'].update({'runtime_version':'changed'})}), 'RUNTIME_IDENTITY_MISMATCH')

    def test_vc_and_pre_definition_links(self):
        for key in ('implementation_binding_ref','test_contract_ref'):
            self.reject(*case({'vc':lambda p,k=key:p.update({k:external('wrong')})}), 'CROSS_REF_MISMATCH')
        self.reject(*case({'tc2':lambda p:p['execution_binding'].update({'test_definition_ref':external('wrong')})}), 'CROSS_REF_MISMATCH')
        self.reject(*case({'r4t':lambda p:p.update({'test_definition_ref':external('wrong')})}), 'CROSS_REF_MISMATCH')
        self.reject(*case({'r4t':lambda p:p.update({'test_definition_raw_sha256':'0'*64})}), 'TC1_RAW_MISMATCH')

    def test_report_full_raw_filename_cross_bindings(self):
        for field,value,code in [('test_report_ref',external('wrong'),'CROSS_REF_MISMATCH'),
            ('test_report_raw_sha256','0'*64,'R4T_RAW_MISMATCH'), ('test_report_filename','wrong.json','R4T_FILENAME_MISMATCH')]:
            with self.subTest(field=field):
                self.reject(*case({'tc2':lambda p,k=field,v=value:p['execution_binding'].update({k:v})}), code)
        self.reject(*case({'ib':lambda p:p['legacy_validator_binding']['test_report'].update({'sha256':'0'*64})}), 'R4T_RAW_MISMATCH')

    def test_command_and_coverage_omissions_or_duplicates(self):
        hooks = [lambda p:p.update({'command_declarations':[]}),
                 lambda p:p.update({'operation_coverage':[]}),
                 lambda p:p['command_declarations'].append({'command_id':'uncovered','argv':['x']}),
                 lambda p:p['command_declarations'].append({'command_id':'binding-tests','argv':['other']}),
                 lambda p:p['operation_coverage'][0].update({'command_ids':['undefined']}),
                 lambda p:p['operation_coverage'].append({'operation_id':'synthetic-binding','command_ids':['binding-tests','undefined']})]
        for hook in hooks:
            self.reject(*case({'tc1':hook}))

    def test_forward_refs_and_wrong_report_type(self):
        for slot in ('tc1','r4t'):
            for key in ('validator_contract_ref','trusted_manifest_ref','manifest_acceptance_ref','post_test_contract_ref'):
                with self.subTest(slot=slot,key=key):
                    self.reject(*case({slot:lambda p,k=key:p.update({k:external('future')})}), 'FUTURE_REFERENCE')
        self.reject(*case({'r4t':lambda p:p.update({'nested':{'validator_contract_ref':external('future')}})}), 'FUTURE_REFERENCE')
        self.reject(*case({'r4t':lambda p:p.pop('test_definition_ref')}), 'R4T_BINDING_SHAPE')
        # A valid seal with a real-protocol object type is outside this API.
        expected, records = case(); from canonical_helper import seal_object
        obj = json.loads(records['r4t']); payload={k:v for k,v in obj.items() if k not in {'object_id','payload_sha256','content_sha256','object_type'}}
        obj = seal_object(payload,object_type='UnexpectedProtocolType',stable_context='synthetic')
        records['r4t']=canonical_json(obj); expected['refs']['r4t']={k:obj[k] for k in ('object_id','content_sha256')}
        self.reject(expected,records,'R4T_BINDING_SHAPE')

    def test_nested_non_string_identifier_does_not_crash(self):
        # The R4T subset does not validate unknown nested execution semantics.
        # Arbitrary JSON shapes must still keep the API's fixed unresolved ceiling.
        result = self.run_case(*case({'r4t':lambda p:p.update({'details':{'object_id':[]}})}))
        self.ceilings(result)
        self.assertEqual(result['verdict'], 'UNRESOLVED')

    def test_missing_baseline_cannot_be_substituted_with_same_count(self):
        with tempfile.TemporaryDirectory(prefix='fp-ib2-tc2-pin-') as temporary:
            entry = _copy_repository(Path(temporary) / 'repo')
            missing = json.loads((entry / 'real_missing.json').read_bytes())
            missing[0] = 'fabricated.same_count'
            (entry / 'real_missing.json').write_bytes(canonical_json(missing))
            process = subprocess.run([sys.executable, '-c', 'import consumer'],
                                     cwd=entry, capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0, 'Same-count real_missing substitution was accepted')
            self.assertIn('Pinned local dependency changed: real_missing.json', process.stderr)

    def test_deep_json_validation_limit_retains_missing_and_hard_failure(self):
        import sys
        # Call-stack depth differs between a direct probe and unittest. Sweep
        # the narrow parser/seal boundary around the current recursion limit.
        for depth in range(max(0, sys.getrecursionlimit() - 60), sys.getrecursionlimit() + 3):
            with self.subTest(depth=depth):
                expected, records = case()
                raw = records['r4t'].rstrip()[:-1] + b',"details":' + b'['*depth + b'0' + b']'*depth + b'}'
                records['r4t'] = raw
                del records['ib']
                result = self.reject(expected, records)
                self.assertEqual(result['missing_inputs'], ['ib'])
                self.assertTrue(result['failures'])

    def test_no_mutation_no_call_time_io_and_stable_result(self):
        expected, records = case(); original = deepcopy((expected,records))
        self.assertIsNotNone(consume)
        with patch('builtins.open',side_effect=AssertionError('unexpected IO')), \
             patch('pathlib.Path.read_bytes',side_effect=AssertionError('unexpected IO')):
            result = consume(expected,records)
        self.assertEqual((expected,records),original)
        self.assertEqual(canonical_json(result),canonical_json(consume(expected,records)))
        result['real_missing'].clear()
        self.assertEqual(len(consume(expected,records)['real_missing']),29)

class RolloutTests(unittest.TestCase):
    def test_copied_repository_cli_works_from_unrelated_cwd(self):
        # Catches resolving shared schemas from cwd or the task-only directory.
        with tempfile.TemporaryDirectory(prefix='fp-ib2-tc2-layout-') as temporary:
            root = Path(temporary)
            entry = _copy_repository(root / 'repo')
            _write_case(root / 'inputs')
            cwd = root / 'unrelated'; cwd.mkdir()
            process = subprocess.run([sys.executable, str(entry / 'replay.py'), str(root / 'inputs')],
                                     cwd=cwd, capture_output=True, text=True)
            self.assertEqual(process.returncode, 0, process.stderr)
            result = json.loads(process.stdout)
            self.assertEqual(result['binding_verdict'], 'LOCAL_CANDIDATE_BINDINGS_VERIFIED')
            self.assertEqual(result['verdict'], 'UNRESOLVED')
            self.assertEqual(result['REAL_ADMISSION'], 'NOT_READY')
            self.assertEqual(result['PROTOCOL_STATE_CHANGE'], 'NONE')

    def test_modified_shared_schema_is_rejected(self):
        # Catches accepting substituted raw schema bytes despite the frozen pin.
        with tempfile.TemporaryDirectory(prefix='fp-ib2-tc2-schema-') as temporary:
            root = Path(temporary) / 'repo'; entry = _copy_repository(root)
            schema = root / 'schemas/implementation_binding_v2.schema.json'
            schema.write_bytes(schema.read_bytes() + b'\n')
            process = subprocess.run([sys.executable, '-c', 'import consumer'],
                                     cwd=entry, capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn('Pinned local dependency changed: schemas/ib.json', process.stderr)

    def test_missing_shared_schema_does_not_use_local_fallback(self):
        # Catches silently reverting to the old private schema copy.
        with tempfile.TemporaryDirectory(prefix='fp-ib2-tc2-no-fallback-') as temporary:
            root = Path(temporary) / 'repo'; entry = _copy_repository(root)
            schema = root / 'schemas/test_contract_v2.schema.json'
            raw = schema.read_bytes(); schema.unlink()
            (entry / 'schemas').mkdir(); (entry / 'schemas/tc2.json').write_bytes(raw)
            process = subprocess.run([sys.executable, '-c', 'import consumer'],
                                     cwd=entry, capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn('test_contract_v2.schema.json', process.stderr)

    def test_matching_local_schema_cannot_hide_modified_shared_schema(self):
        # Catches a loader that uses local copies instead of the authorized target.
        with tempfile.TemporaryDirectory(prefix='fp-ib2-tc2-shadow-') as temporary:
            root = Path(temporary) / 'repo'; entry = _copy_repository(root)
            schema = root / 'schemas/implementation_binding_v2.schema.json'
            raw = schema.read_bytes(); (entry / 'schemas').mkdir()
            (entry / 'schemas/ib.json').write_bytes(raw); schema.write_bytes(raw + b'\n')
            process = subprocess.run([sys.executable, '-c', 'import consumer'],
                                     cwd=entry, capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertIn('Pinned local dependency changed: schemas/ib.json', process.stderr)


if __name__ == '__main__':
    unittest.main()
