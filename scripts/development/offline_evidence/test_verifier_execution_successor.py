"""Forward technical contract; retained public evidence only, no native calls."""
import copy
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from test_verifier_contract import load, artifacts, rule, PROFILE

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = ROOT/'docs/development/verifier-execution-contract-successor-2026-10-28-rev-001'


class ExecutionSuccessorTests(unittest.TestCase):
    def inputs(self):
        self.assertTrue((PACKAGE/'EXECUTION_INPUTS.json').exists(), 'execution input catalogue missing')
        rows = json.loads((PACKAGE/'EXECUTION_INPUTS.json').read_bytes())['inputs']
        result={row['path']:(ROOT/row['path']).read_bytes() for row in rows}
        result[str((PACKAGE/'EXECUTION_INPUTS.json').relative_to(ROOT))]=(PACKAGE/'EXECUTION_INPUTS.json').read_bytes()
        return result

    def consume(self, **changes):
        module = load('verifier_contract')
        self.assertTrue(hasattr(module, 'SUCCESSOR_REF'), 'explicit successor admission not implemented')
        values = dict(contract_bytes=(PACKAGE/'CONTRACT_CANDIDATE.json').read_bytes(),
                      profile_bytes=PROFILE.read_bytes(), rule_bytes=None,
                      artifact_bytes=artifacts(), execution_inputs=self.inputs())
        values.update(changes)
        # Import prerequisites above are admitted software. The API itself must
        # consume provided immutable bytes without reading files or loading C.
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('unexpected reread')):
            return module.consume(**values)

    def test_exact_successor_binds_execution_without_establishing_authority(self):
        r = self.consume()
        self.assertEqual(r['contract_content_status'], 'OBSERVED')
        self.assertEqual(r['technical_execution_support']['status'], 'OBSERVED')
        self.assertEqual(r['technical_execution_support']['bound_execution_input_count'], 67)
        self.assertEqual(r['technical_execution_support']['retained_executions_consumed'], 2)
        self.assertEqual(r['same_binary_rebuild_support'], 'OBSERVED')
        self.assertEqual(r['message_resource_policy'], 'DEVELOPMENT_FIXED_SAMPLE_POLICY_BOUND')
        self.assertEqual(r['status'], 'MISSING')
        self.assertIn('rule_bytes', r['missing'])
        for name in ['full_build_runtime_closure', 'execution_contract_complete', 'public_authentication']:
            self.assertEqual(r[name], 'NOT_ESTABLISHED')
        self.assertFalse(r['backend_called']);self.assertFalse(r['native_loaded'])
        self.assertEqual(r['operational_bindings_established'], 0)
        self.assertEqual(r['protocol_state_change'], 'NONE')

    def test_old_contract_output_is_unchanged(self):
        m=load('verifier_contract')
        original=ROOT/'docs/development/verifier-contract-consumption-2026-10-25-rev-001/CONTRACT_CANDIDATE.json'
        r=m.consume(original.read_bytes(), PROFILE.read_bytes(), None, artifacts())
        self.assertEqual(r, json.loads((PACKAGE/'BASELINE_V1_RESULT.json').read_bytes()))

    def test_old_rule_does_not_implicitly_select_successor(self):
        r=self.consume(rule_bytes=rule())
        self.assertEqual(r['status'], 'REJECTED')
        self.assertIn('RULE_VERIFIER_CONTRACT_REF_MISMATCH', r['errors'])
        m=load('verifier_contract')
        synthetic=rule(lambda o:o['rules']['signing_semantics'].update(verifier_contract_ref=m.SUCCESSOR_REF))
        r=self.consume(rule_bytes=synthetic)
        self.assertEqual(r['status'],'OBSERVED')
        self.assertEqual(r['real_admission'],'NOT_READY')

    def test_missing_and_substitution_are_both_retained(self):
        inputs=self.inputs();names=list(inputs)
        inputs[names[0]]=None
        raw=inputs[names[1]];inputs[names[1]]=bytes([raw[0]^1])+raw[1:]
        r=self.consume(execution_inputs=inputs)
        self.assertEqual(r['status'],'REJECTED')
        self.assertIn('execution:'+names[0],r['missing'])
        self.assertIn('EXECUTION_IDENTITY_MISMATCH:'+names[1],r['errors'])
        self.assertEqual(r['technical_execution_support']['status'],'NOT_CHECKED')

    def test_caller_shrinking_and_extra_mapping_cannot_create_completeness(self):
        original=self.inputs()
        reduced=dict(original);reduced.pop(next(iter(reduced)))
        r=self.consume(execution_inputs=reduced)
        self.assertEqual(r['status'],'MISSING')
        extra=dict(original, arbitrary=b'public bytes')
        self.assertIn('EXECUTION_INPUT_ROLES_INVALID',self.consume(execution_inputs=extra)['errors'])
        self.assertIn('EXECUTION_INPUT_MAPPING_INVALID',self.consume(execution_inputs=[])['errors'])

    def test_resealed_contract_cannot_choose_different_resources(self):
        obj=json.loads((PACKAGE/'CONTRACT_CANDIDATE.json').read_bytes())
        obj['resources']['direct_message_bytes']=1
        c=load('verifier_contract')._C
        payload={k:v for k,v in obj.items() if k not in ['object_type','object_id','payload_sha256','content_sha256']}
        changed=c.seal_object(payload,object_type=obj['object_type'],stable_context='D279_TEST',semantic_id=obj['object_id'])
        r=self.consume(contract_bytes=json.dumps(changed).encode())
        self.assertEqual(r['status'],'REJECTED')
        self.assertIn('CONTRACT_RAW_MISMATCH',r['errors'])

    def test_no_execution_evidence_keeps_content_and_missing_separate(self):
        r=self.consume(execution_inputs=None)
        self.assertEqual(r['contract_content_status'],'OBSERVED')
        self.assertEqual(r['technical_execution_support']['status'],'NOT_CHECKED')
        self.assertIn('execution_inputs',r['missing'])
        self.assertEqual(r['message_resource_policy'],'NOT_ESTABLISHED')

    def test_oversize_contract_is_rejected_before_identity_hashing(self):
        original=hashlib.sha256
        def bounded(raw=b''):
            self.assertLessEqual(len(raw),1048576,'oversize contract hashed before size rejection')
            return original(raw)
        with patch.object(hashlib,'sha256',side_effect=bounded):
            r=self.consume(contract_bytes=b' ' * 1048577)
        self.assertEqual(r['status'],'REJECTED')
        self.assertIn('CONTRACT_RAW_MISMATCH',r['errors'])

    def test_two_fresh_processes_consume_exact_support_without_native_or_rereads(self):
        entry=PACKAGE/'replay.py'
        self.assertTrue(entry.exists(),'bounded successor replay entry missing')
        outputs=[]
        with tempfile.TemporaryDirectory() as elsewhere:
            for cwd in (ROOT,Path(elsewhere)):
                p=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B',str(entry)],
                                 cwd=cwd,capture_output=True,timeout=20)
                self.assertEqual(p.returncode,0,p.stderr.decode());outputs.append(p.stdout)
        self.assertEqual(outputs[0],outputs[1])
        r=json.loads(outputs[0]);self.assertEqual(r['technical_execution_support']['status'],'OBSERVED')
        self.assertFalse(r['native_loaded']);self.assertEqual(r['status'],'MISSING')


if __name__=='__main__':unittest.main()
