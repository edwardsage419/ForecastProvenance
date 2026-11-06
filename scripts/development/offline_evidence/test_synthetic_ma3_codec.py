"""Synthetic-only codec tests: no keys, signatures or actual project messages."""
import copy
import hashlib
import io
import json
from pathlib import Path
import struct
import subprocess
from types import ModuleType
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROFILE = ROOT/'docs/development/mainline-execution-2026-10-19-signing-profile-content-rev-001/PROFILE_CANDIDATE.json'
SCOPE = 'D191_SYNTHETIC_TEST_ONLY'


def ref(name):
    identity = 'SYNTHETIC_TEST_ONLY:D191:'+name
    return {'object_id': identity, 'content_sha256': hashlib.sha256(('D191_REF/'+identity).encode()).hexdigest()}


def case(decision='ACCEPT'):
    return {'scope': SCOPE,
            'context': {'action': 'MANIFEST_ACCEPTANCE_DECISION',
                        'actor_id': 'SYNTHETIC_TEST_ONLY:D191_ACTOR',
                        'effective_scope_ref': ref('ROOT'), 'project_id': 'SYNTHETIC_TEST_ONLY:D191_PROJECT',
                        'public_key_sha256': hashlib.sha256(b'D191_NOT_A_REAL_PUBLIC_KEY').hexdigest(),
                        'role': 'BOOTSTRAP_MANIFEST_ACCEPTANCE', 'scope': 'GENESIS_INITIAL_MANIFEST',
                        'validator_contract_ref': ref('VALIDATOR')},
            'unsigned': {'acceptance_rule_ref': ref('RULE'), 'authority_ref': ref('ROOT'),
                         'blocking_finding_refs': [], 'bootstrap_governance_root_ref': ref('ROOT'),
                         'candidate_manifest_ref': ref('MANIFEST'), 'decision': decision,
                         'object_type': 'ManifestAcceptance',
                         'reason_codes': ['SYNTHETIC_TEST_ONLY_D191_REASON'],
                         'required_validation_report_refs': [ref('REPORT_'+str(i)) for i in range(5)],
                         'schema_version': '3.0'}}


def raw(value):
    return json.dumps(value, ensure_ascii=False).encode('utf-8')


class SyntheticCodecTests(unittest.TestCase):
    def module(self):
        path = HERE/'synthetic_ma3_codec.py'
        self.assertTrue(path.is_file(), 'synthetic-only MA3 codec missing')
        module = ModuleType('d191_codec_test'); module.__file__ = str(path)
        exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
        return module

    def call(self, value=None):
        return self.module().encode_synthetic_case(raw(case() if value is None else value), PROFILE.read_bytes())

    def reject(self, value):
        with self.assertRaises(ValueError):
            self.call(value)

    def test_exact_envelope_and_direct_framing_match_an_independent_oracle(self):
        value = case(); result = self.call(value)
        envelope = {'acceptance_payload': value['unsigned'], 'algorithm': 'ED25519_PURE_STRICT_SUBGROUP_V1',
                    'context': value['context'], 'signing_profile': 'FPP_INITIAL_MA3_A1'}
        expected = json.dumps(envelope, ensure_ascii=False, separators=(',', ':'), sort_keys=True).encode('utf-8')
        self.assertEqual(result['envelope_bytes'], expected)
        domain = b'FPP_INITIAL_MANIFEST_ACCEPTANCE_MA3_A1'
        self.assertEqual(result['frame_bytes'], domain+b'\x00'+struct.pack('>Q', len(expected))+expected)
        self.assertNotEqual(result['frame_bytes'][-32:], hashlib.sha256(expected).digest())
        self.assertEqual(result['scope'], 'SYNTHETIC_CODEC_OBSERVATION')
        self.assertEqual(result['public_authentication'], 'NOT_IMPLEMENTED')
        self.assertEqual(result['independent_authority_and_applicability'], 'NOT_ESTABLISHED')
        self.assertEqual(result['real_admission'], 'NOT_READY')
        self.assertFalse(result['prospective_eligible'])
        self.assertFalse(result['signed_or_carrier_created'])
        self.assertEqual(result['protocol_state_change'], 'NONE')

    def test_json_member_order_is_canonicalized_without_modifying_input(self):
        value = case(); before = copy.deepcopy(value)
        altered = dict(reversed(list(value.items())))
        altered['context'] = dict(reversed(list(value['context'].items())))
        self.assertEqual(self.call(altered)['frame_bytes'], self.call(value)['frame_bytes'])
        self.assertEqual(value, before)

    def test_wrong_scope_project_actor_and_key_digest_cannot_be_labeled_synthetic(self):
        for section, field, replacement in [(None, 'scope', 'REAL'),
                                             ('context', 'project_id', 'OTHER_PROJECT'),
                                             ('context', 'actor_id', 'OTHER_ACTOR'),
                                             ('context', 'public_key_sha256', '0'*64)]:
            value = case(); target = value if section is None else value[section]
            target[field] = replacement
            self.reject(value)

    def test_every_full_ref_requires_exact_sentinel_name_and_hash(self):
        paths = [('context', 'effective_scope_ref'), ('context', 'validator_contract_ref'),
                 ('unsigned', 'authority_ref'), ('unsigned', 'bootstrap_governance_root_ref'),
                 ('unsigned', 'acceptance_rule_ref'), ('unsigned', 'candidate_manifest_ref')]
        for section, key in paths:
            for member in ('object_id', 'content_sha256'):
                value = case(); value[section][key][member] = 'OTHER' if member == 'object_id' else '0'*64
                self.reject(value)
        value = case(); value['unsigned']['required_validation_report_refs'][4]['content_sha256'] = '0'*64
        self.reject(value)

    def test_closed_context_unsigned_and_excluded_fields_are_enforced(self):
        value = case()
        for section in ('context', 'unsigned'):
            for field in value[section]:
                changed = copy.deepcopy(value); del changed[section][field]; self.reject(changed)
        for field in ('object_id', 'payload_sha256', 'content_sha256', 'signature_ref', 'unknown'):
            changed = case(); changed['unsigned'][field] = 'SYNTHETIC_TEST_ONLY'; self.reject(changed)
        changed = case(); changed['unknown'] = True; self.reject(changed)

    def test_ref_and_reason_sets_reject_duplicates_wrong_counts_and_wrong_order(self):
        for field in ('required_validation_report_refs', 'reason_codes'):
            value = case(); values = value['unsigned'][field]
            if field == 'reason_codes':
                values[:] = ['SYNTHETIC_TEST_ONLY_D191_A', 'SYNTHETIC_TEST_ONLY_D191_Z']
            value['unsigned'][field] = list(reversed(values)); self.reject(value)
            value = case(); value['unsigned'][field].append(copy.deepcopy(value['unsigned'][field][0])); self.reject(value)
        value = case(); value['unsigned']['required_validation_report_refs'].pop(); self.reject(value)
        value = case(); value['unsigned']['reason_codes'] = ['OTHER_REASON']; self.reject(value)

    def test_accept_blockers_reject_and_reject_decision_keeps_the_ceiling(self):
        value = case(); value['unsigned']['blocking_finding_refs'] = [ref('BLOCKER_0')]; self.reject(value)
        value['unsigned']['decision'] = 'REJECT'
        result = self.call(value)
        self.assertEqual(result['real_admission'], 'NOT_READY')
        for refs in ([ref('BLOCKER_1'), ref('BLOCKER_0')], [ref('BLOCKER_0')]*2):
            changed = copy.deepcopy(value); changed['unsigned']['blocking_finding_refs'] = refs; self.reject(changed)
        changed = copy.deepcopy(value); changed['unsigned']['blocking_finding_refs'][0]['content_sha256'] = '0'*64
        self.reject(changed)

    def test_type_version_context_and_decision_literals_have_no_fallback(self):
        for section, field, replacement in [('unsigned', 'schema_version', '2.0'),
                                             ('unsigned', 'object_type', 'Other'),
                                             ('unsigned', 'decision', 'OTHER'),
                                             ('context', 'action', 'QUALIFY'),
                                             ('context', 'role', 'OTHER'), ('context', 'scope', 'OTHER')]:
            value = case(); value[section][field] = replacement; self.reject(value)

    def test_parser_and_transport_reject_ambiguous_or_unbounded_inputs(self):
        module = self.module(); profile = PROFILE.read_bytes()
        for value in (b'{"scope":1,"scope":2}', b'\xef\xbb\xbf'+raw(case()), b'{}',
                      b'null', b'NaN', raw(case()).replace(b'"3.0"', b'3.0'), b'x'*1048577,
                      bytearray(raw(case()))):
            with self.assertRaises(ValueError):
                module.encode_synthetic_case(value, profile)
        with self.assertRaises(ValueError):
            module.encode_synthetic_case(raw(case()), profile+b'\n')

    def test_profile_selection_cannot_be_changed_by_the_case_or_profile_bytes(self):
        value = case(); value['signing_profile'] = 'DRAFT_A1'; self.reject(value)
        changed = json.loads(PROFILE.read_bytes()); changed['signing_rules']['framing']['domain_ascii'] = 'OTHER'
        with self.assertRaises(ValueError):
            self.module().encode_synthetic_case(raw(case()), raw(changed))

    def test_consumption_has_no_file_or_network_io_after_fixed_import(self):
        module = self.module(); value, profile = raw(case()), PROFILE.read_bytes()
        with patch('builtins.open', side_effect=AssertionError('I/O')), patch.object(io, 'open', side_effect=AssertionError('I/O')), \
                patch('socket.socket', side_effect=AssertionError('network')):
            result = module.encode_synthetic_case(value, profile)
        self.assertTrue(result['frame_bytes'])

    def test_fresh_process_replay_matches_without_saving_message_instances(self):
        path = HERE/'synthetic_ma3_codec.py'
        self.assertTrue(path.exists(), 'synthetic-only MA3 codec missing')
        code = ("import sys,json,hashlib;from pathlib import Path;from types import ModuleType;"
                "p=Path(sys.argv[1]);m=ModuleType('replay');m.__file__=str(p);"
                "exec(compile(p.read_bytes(),str(p),'exec'),m.__dict__);"
                "r=m.encode_synthetic_case(sys.stdin.buffer.read(),Path(sys.argv[2]).read_bytes());"
                "print(json.dumps({'sha256':hashlib.sha256(r['frame_bytes']).hexdigest(),'bytes':len(r['frame_bytes'])}))")
        command = [str(ROOT/'.venv/bin/python'), '-I', '-B', '-c', code, str(path), str(PROFILE)]
        value = raw(case()); expected = self.call()['frame_bytes']
        outputs = []
        for _ in range(2):
            process = subprocess.run(command, input=value, capture_output=True, timeout=30)
            self.assertEqual(process.returncode, 0, process.stderr)
            outputs.append(json.loads(process.stdout))
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(outputs[0], {'sha256': hashlib.sha256(expected).hexdigest(), 'bytes': len(expected)})


if __name__ == '__main__':
    unittest.main()
