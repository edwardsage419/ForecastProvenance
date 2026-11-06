"""Finite contract content/anchors, never messages, native calls or authority."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKAGE = ROOT/'docs/development/verifier-contract-consumption-2026-10-25-rev-001'
PROFILE = ROOT/'docs/development/mainline-execution-2026-10-19-signing-profile-content-rev-001/PROFILE_CANDIDATE.json'
REF = {'object_id': 'verifier-contract:initial-ma3:strict-c-dev:v1',
       'content_sha256': '1a2c215289e95f4c2b955468314e05488b8d1dfe2ed20b7562165cccb6e3f160'}
ROLES = {'adapter', 'run_binding', 'build_observations', 'source_manifest',
         'configuration', 'pre_run', 'dependency_audit', 'native_binary'}


def load(name):
    spec = importlib.util.spec_from_file_location('d211_test_'+name, HERE/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def artifacts():
    rows = json.loads((PACKAGE/'ARTIFACT_INPUTS.json').read_bytes())
    return {role:(ROOT/row['path']).read_bytes() for role,row in rows.items()}


def rule(change=None):
    def update(obj):
        obj['rules']['signing_semantics']['verifier_contract_ref'] = dict(REF)
        if change:
            change(obj)
    return load('test_signing_profile').rule_bytes(update)


class VerifierContractTests(unittest.TestCase):
    def consumer(self):
        self.assertTrue((HERE/'verifier_contract.py').exists(), 'D211 consume API is absent')
        return load('verifier_contract')

    def consume(self, **changes):
        values = dict(contract_bytes=(PACKAGE/'CONTRACT_CANDIDATE.json').read_bytes(),
                      profile_bytes=PROFILE.read_bytes(), rule_bytes=rule(), artifact_bytes=artifacts())
        values.update(changes)
        return self.consumer().consume(**values)

    def test_exact_content_and_anchors_with_no_rule_stay_missing(self):
        result = self.consume(rule_bytes=None)
        self.assertEqual(result['status'], 'MISSING')
        self.assertEqual(result['contract_content_status'], 'OBSERVED')
        self.assertEqual(result['artifact_binding_status'], 'OBSERVED')
        self.assertEqual(set(result['artifact_statuses']), ROLES)
        self.assertEqual(result['proposed_verifier_use_status'], 'MISSING')
        self.assertIn('rule_bytes', result['missing'])

    def test_three_matching_synthetic_uses_are_not_operational_authentication(self):
        result = self.consume()
        self.assertEqual(result['status'], 'OBSERVED')
        self.assertEqual(result['proposed_verifier_use_status'], 'OBSERVED')
        self.assertEqual(result['local_three_signing_uses'], 'LOCAL_DEVELOPMENT_THREE_USES_MATCHED')
        self.assertEqual(result['verdict'], 'UNRESOLVED')
        self.assertEqual(result['operational_bindings_established'], 0)
        for field in ('public_authentication', 'full_build_runtime_closure', 'message_resource_policy',
                      'execution_contract_complete', 'all_source_and_gate_inputs_checked'):
            self.assertEqual(result[field], 'NOT_ESTABLISHED')
        self.assertFalse(result['backend_called']); self.assertFalse(result['message_constructed'])
        self.assertFalse(result['carrier_constructed']); self.assertFalse(result['prospective_eligible'])
        self.assertEqual(result['real_admission'], 'NOT_READY')
        self.assertEqual(result['protocol_state_change'], 'NONE')

    def test_wrong_third_use_is_not_hidden_by_two_matching_uses(self):
        bad = rule(lambda obj: obj['rules']['signing_semantics']['verifier_contract_ref'].update(content_sha256='3'*64))
        result = self.consume(rule_bytes=bad)
        self.assertEqual(result['profile_result']['proposed_rule_binding_status'], 'OBSERVED')
        self.assertEqual(result['status'], 'REJECTED')
        self.assertIn('RULE_VERIFIER_CONTRACT_REF_MISMATCH', result['errors'])

    def test_old_two_use_failures_still_reject_when_third_matches(self):
        for field in ('profile_ref', 'carrier_profile_ref'):
            with self.subTest(field=field):
                bad = rule(lambda obj: obj['rules']['signing_semantics'][field].update(content_sha256='2'*64))
                result = self.consume(rule_bytes=bad)
                self.assertEqual(result['status'], 'REJECTED')
                self.assertIn('RULE_'+field.upper()+'_MISMATCH', result['errors'])

    def test_wrong_contract_raw_shape_seal_version_identity_and_declarations_reject(self):
        raw = (PACKAGE/'CONTRACT_CANDIDATE.json').read_bytes()
        values = [raw+b'\n', bytearray(raw), b'{}', b'{"x":1,"x":2}', b'\xef\xbb\xbf'+raw, b'x'*1048577]
        for edit in (
            lambda o:o.update(schema_version='2.0'), lambda o:o.update(object_type='Other'),
            lambda o:o.update(contract_id='OTHER'), lambda o:o.update(content_sha256='0'*64),
            lambda o:o['interface'].update(interpretation='BOOL_TRUTHINESS'),
            lambda o:o['interface']['statuses'].update(UNRESOLVED='AUTHENTICATED'),
            lambda o:o['resources'].update(message_resource_policy='COMPLETE'),
            lambda o:o['evidence_limits'].update(full_build_runtime_closure='COMPLETE')):
            obj = json.loads(raw); edit(obj); values.append(json.dumps(obj).encode())
        for bad in values:
            with self.subTest(size=len(bad)):
                result = self.consume(contract_bytes=bad)
                self.assertEqual(result['status'], 'REJECTED')
                self.assertIn('CONTRACT_RAW_MISMATCH', result['errors'])
                self.assertNotEqual(result['contract_content_status'], 'OBSERVED')

    def test_each_artifact_missing_remains_missing_without_fallback(self):
        original = artifacts()
        for role in ROLES:
            for omitted in (True, False):
                with self.subTest(role=role, omitted=omitted):
                    supplied = dict(original)
                    if omitted: del supplied[role]
                    else: supplied[role] = None
                    result = self.consume(artifact_bytes=supplied)
                    self.assertEqual(result['status'], 'MISSING')
                    self.assertIn('artifact:'+role, result['missing'])
                    self.assertEqual(result['artifact_statuses'][role]['status'], 'MISSING')

    def test_each_artifact_same_size_substitution_is_rejected(self):
        original = artifacts()
        for role in ROLES:
            with self.subTest(role=role):
                supplied = dict(original); raw = supplied[role]
                supplied[role] = bytes([raw[0]^1])+raw[1:]
                result = self.consume(artifact_bytes=supplied)
                self.assertEqual(result['status'], 'REJECTED')
                self.assertIn('ARTIFACT_IDENTITY_MISMATCH:'+role, result['errors'])

    def test_artifact_types_extra_keys_and_nonmapping_are_rejected(self):
        for bad in (False, [], {'unknown':b''}):
            self.assertEqual(self.consume(artifact_bytes=bad)['status'], 'REJECTED')
        supplied = artifacts(); supplied['native_binary'] = bytearray(supplied['native_binary'])
        self.assertEqual(self.consume(artifact_bytes=supplied)['status'], 'REJECTED')

    def test_hard_failure_and_missing_contract_profile_rule_and_sibling_are_all_retained(self):
        supplied = artifacts(); supplied['adapter'] = b'bad'; del supplied['native_binary']
        result = self.consume(contract_bytes=None, profile_bytes=None, rule_bytes=b'{}', artifact_bytes=supplied)
        self.assertEqual(result['status'], 'REJECTED')
        self.assertIn('ARTIFACT_IDENTITY_MISMATCH:adapter', result['errors'])
        self.assertIn('RULE_SHAPE_INVALID', result['errors'])
        for missing in ('contract_bytes', 'profile_bytes', 'artifact:native_binary'):
            self.assertIn(missing, result['missing'])

    def test_missing_artifacts_do_not_hide_wrong_profile_or_rule(self):
        for fields in ({'profile_bytes':b'{}'}, {'rule_bytes':b'{"rules":null}'}):
            result = self.consume(artifact_bytes=None, **fields)
            self.assertEqual(result['status'], 'REJECTED')
            self.assertIn('artifact_bytes', result['missing'])
            self.assertEqual(result['artifact_binding_status'], 'MISSING')

    def test_profile_child_is_actually_reused_and_inputs_are_not_mutated(self):
        source = artifacts(); before = copy.deepcopy(source); raw = rule()
        result = self.consume(artifact_bytes=source, rule_bytes=raw)
        expected = load('signing_profile').consume(PROFILE.read_bytes(), raw)
        self.assertEqual(result['profile_result'], expected)
        self.assertEqual(source, before)

    def test_caller_result_and_backend_callback_have_no_input_route(self):
        module = self.consumer()
        for extra in ({'backend':object()}, {'result':True}, {'message':b'not-a-message'}):
            with self.assertRaises(TypeError):
                module.consume(None, None, **extra)

    def test_fixed_schema_and_catalog_substitution_fail_before_consumption(self):
        self.consumer()
        read = Path.read_bytes
        for filename in ('CONTRACT_SCHEMA_CANDIDATE.json', 'ARTIFACT_INPUTS.json'):
            def replaced(path):
                raw = read(path)
                return raw+b' ' if path == PACKAGE/filename else raw
            with patch.object(Path, 'read_bytes', replaced):
                with self.assertRaises(RuntimeError): load('verifier_contract')

    def test_fresh_process_replay_is_identical_and_consume_performs_no_io_or_native(self):
        self.consumer()
        code = '''import importlib.util,json,pathlib,sys
root=pathlib.Path.cwd();here=root/'scripts/development/offline_evidence'
spec=importlib.util.spec_from_file_location('d211fresh',here/'test_verifier_contract.py')
t=importlib.util.module_from_spec(spec);spec.loader.exec_module(t)
m=t.load('verifier_contract');contract=(t.PACKAGE/'CONTRACT_CANDIDATE.json').read_bytes()
profile=t.PROFILE.read_bytes();rule=t.rule();assets=t.artifacts()
def audit(event,args):
 if event=='open' or event.startswith(('ctypes.','socket.')) or event in ('subprocess.Popen','os.system','os.exec','os.fork'):
  raise RuntimeError('D211_FORBIDDEN_SIDE_EFFECT')
sys.addaudithook(audit)
print(json.dumps(m.consume(contract,profile,rule,assets),sort_keys=True))
'''
        results = [subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B','-c',code],
                                 cwd=ROOT,capture_output=True,timeout=30) for _ in range(2)]
        for run in results: self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(results[0].stdout, results[1].stdout)
        self.assertEqual(json.loads(results[0].stdout)['status'], 'OBSERVED')


if __name__ == '__main__': unittest.main()
