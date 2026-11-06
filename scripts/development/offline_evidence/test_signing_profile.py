"""Keyless technical-profile consumption never establishes rule effectivity."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from types import ModuleType
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CANDIDATE = ROOT/'docs/development/mainline-execution-2026-10-19-signing-profile-content-rev-001/PROFILE_CANDIDATE.json'
SCHEMA = ROOT/'schemas/acceptance_policy_v3.schema.json'
REF = {'object_id': 'signing-profile:genesis-initial-ma3:a1',
       'content_sha256': '339833cdba8a9143d6ae74c53dd833d21e9a6f23ddc144272760e6b65d705166'}


def canonical():
    path = ROOT/'src/forecast_trust_core/canonical.py'
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == 'f9ef49579a5c54757c6660d377275a0ed5f8afdf646f33130651a711005ac9ba'
    module = ModuleType('d189_test_canonical')
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def rule_bytes(change=None):
    schema = json.loads(SCHEMA.read_bytes())
    def value(node):
        if 'const' in node:
            return copy.deepcopy(node['const'])
        if '$ref' in node:
            kind = node['$ref'].rsplit('/', 1)[-1]
            if kind == 'exact_ref':
                return {'object_id': 'SYNTHETIC_TEST_ONLY:D189_SENTINEL', 'content_sha256': '1'*64}
            return '1'*64 if kind == 'sha256' else 'SYNTHETIC_TEST_ONLY:D189_TOKEN'
        if node.get('type') == 'object':
            return {key: value(child) for key, child in node['properties'].items()}
        if node.get('type') == 'array':
            return [value(child) for child in node.get('prefixItems', [])]
        raise AssertionError(node)
    obj = value(schema)
    obj['policy_id'] = 'SYNTHETIC_TEST_ONLY:D189_RULE'
    for field in ('profile_ref', 'carrier_profile_ref'):
        obj['rules']['signing_semantics'][field] = dict(REF)
    if change:
        change(obj)
    payload = {k: v for k, v in obj.items() if k not in ('object_type', 'object_id', 'payload_sha256', 'content_sha256')}
    sealed = canonical().seal_object(payload, object_type='PolicyDefinition', stable_context='SYNTHETIC_TEST_ONLY',
                                     semantic_id='SYNTHETIC_TEST_ONLY:D189_RULE')
    return json.dumps(sealed).encode()


class SigningProfileTests(unittest.TestCase):
    def consumer(self):
        path = HERE/'signing_profile.py'
        self.assertTrue(path.is_file(), 'typed profile consumer missing')
        module = ModuleType('d189_profile_test')
        module.__file__ = str(path)
        exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
        return module

    def test_actual_candidate_content_is_consumed_while_missing_rule_stays_missing(self):
        result = self.consumer().consume(CANDIDATE.read_bytes())
        self.assertEqual(result['profile_content_status'], 'OBSERVED')
        self.assertEqual(result['status'], 'MISSING')
        self.assertEqual(result['proposed_rule_binding_status'], 'MISSING')
        self.assertIn('rule_bytes', result['missing'])
        self.assertEqual(result['operational_bindings_established'], 0)

    def test_two_typed_uses_match_only_in_synthetic_rule_and_never_create_authority(self):
        result = self.consumer().consume(CANDIDATE.read_bytes(), rule_bytes())
        self.assertEqual(result['status'], 'OBSERVED', result)
        self.assertEqual(result['proposed_rule_binding_status'], 'OBSERVED')
        self.assertEqual(result['consumed_sections'], ['signing_rules', 'carrier_rules'])
        self.assertEqual(result['verdict'], 'UNRESOLVED')
        self.assertEqual(result['operational_bindings_established'], 0)
        self.assertEqual(result['independent_authority_and_applicability'], 'NOT_ESTABLISHED')
        self.assertEqual(result['separate_verifier_contract'], 'NOT_ESTABLISHED')
        self.assertEqual(result['complete_profile_inputs'], 'NOT_ESTABLISHED')
        self.assertEqual(result['real_admission'], 'NOT_READY')
        self.assertEqual(result['protocol_state_change'], 'NONE')

    def test_either_use_with_same_object_id_but_different_full_ref_is_rejected(self):
        for field in ('profile_ref', 'carrier_profile_ref'):
            raw = rule_bytes(lambda obj: obj['rules']['signing_semantics'][field].update(content_sha256='2'*64))
            result = self.consumer().consume(CANDIDATE.read_bytes(), raw)
            self.assertEqual(result['status'], 'REJECTED')
            self.assertIn('RULE_'+field.upper()+'_MISMATCH', result['errors'])

    def test_rule_shape_seal_semantic_id_and_old_version_are_checked(self):
        cases = [rule_bytes(lambda obj: obj.update(schema_version='1.0')),
                 rule_bytes(lambda obj: obj.update(policy_id='SYNTHETIC_TEST_ONLY:OTHER')),
                 rule_bytes(lambda obj: obj['rules']['signing_semantics'].update(algorithm='OTHER'))]
        seal = json.loads(rule_bytes()); seal['content_sha256'] = '3'*64
        cases.append(json.dumps(seal).encode())
        for raw in cases:
            self.assertEqual(self.consumer().consume(CANDIDATE.read_bytes(), raw)['status'], 'REJECTED')

    def test_profile_raw_type_full_identity_content_and_duplicate_json_are_checked(self):
        raw = CANDIDATE.read_bytes()
        changed = json.loads(raw); changed['carrier_rules']['schema_version'] = 'DRAFT_A1'
        full = json.loads(raw); full['content_sha256'] = '2'*64
        for bad in (raw+b'\n', bytearray(raw), b'{}', b'{"x":1,"x":2}', b'\xef\xbb\xbf'+raw,
                    json.dumps(changed).encode(), json.dumps(full).encode(), b'x'*1048577):
            self.assertEqual(self.consumer().consume(bad)['status'], 'REJECTED')

    def test_profile_errors_and_rule_errors_are_not_hidden_by_missing_other_input(self):
        for profile, rule, error, missing in [(None, b'{}', 'RULE_SHAPE_INVALID', 'profile_bytes'),
                                            (b'{}', None, 'PROFILE_RAW_MISMATCH', 'rule_bytes')]:
            result = self.consumer().consume(profile, rule)
            self.assertEqual(result['status'], 'REJECTED')
            self.assertIn(error, result['errors'])
            self.assertIn(missing, result['missing'])
        result = self.consumer().consume(None, None)
        self.assertEqual(result['status'], 'MISSING')
        self.assertEqual(len(result['missing']), 2)

    def test_dependency_schema_drift_is_rejected_before_use(self):
        path = HERE/'signing_profile.py'
        self.assertTrue(path.exists(), 'typed profile consumer missing')
        raw = path.read_bytes().replace(
            b'4bbea6a34351178e4adefe5c31b04e8a2eb4cc9e08bbfadbe8c164d066f68fe1', b'0'*64)
        module = ModuleType('d189_changed_dependency_control'); module.__file__ = str(path)
        with self.assertRaises(RuntimeError):
            exec(compile(raw, str(path), 'exec'), module.__dict__)

    def test_mainline_uses_candidate_content_without_promoting_initial_authority(self):
        process = subprocess.run([str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'),
                                  'mainline', '--json'], capture_output=True, text=True, timeout=45)
        result = json.loads(process.stdout)
        row = next(row for row in result['modules'] if row['id'] == 'initial-authority')
        technical = row['result'].get('technical_signing_profile_candidate', {})
        self.assertEqual(technical.get('profile_content_status'), 'OBSERVED')
        self.assertEqual(technical['proposed_rule_binding_status'], 'MISSING')
        self.assertEqual(row['status'], 'MISSING')
        self.assertIn('BLOCKED_BY_G02', row['result']['reason_codes'])
        self.assertEqual(len(result['modules']), 14)
        self.assertEqual(result['real_admission'], 'NOT_READY')
        self.assertEqual(process.returncode, 1)

    def test_explicit_profile_directory_has_no_fallback_and_rejection_reaches_parent(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for replaced in (False, True):
                if replaced:
                    (directory/'PROFILE_CANDIDATE.json').write_bytes(b'{}')
                process = subprocess.run([str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'),
                                          'mainline', '--profile-inputs', str(directory), '--json'],
                                         capture_output=True, text=True, timeout=45)
                result = json.loads(process.stdout)
                rows = {row['id']: row for row in result['modules']}
                self.assertEqual(rows['initial-authority']['status'], 'REJECTED' if replaced else 'MISSING')
                local = rows['initial-authority']['result']['technical_signing_profile_candidate']
                self.assertEqual(local['status'], 'REJECTED' if replaced else 'MISSING')
                self.assertEqual(rows['economic-data']['status'], 'OBSERVED')
                self.assertEqual(result['real_admission'], 'NOT_READY')
                self.assertEqual(process.returncode, 2 if replaced else 1)


if __name__ == '__main__':
    unittest.main()
