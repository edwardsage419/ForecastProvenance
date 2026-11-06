"""Retained public sample receipts only. No Core or actual authorization use."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CATALOG=json.loads((HERE/'strong_event_inputs.json').read_bytes())
ROLES=CATALOG['roles']

def mirror(directory):
    for row in CATALOG['inputs']:
        path=Path(directory)/row['path'];path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/row['path'],path)

class StrongEventTests(unittest.TestCase):
    def module(self):
        source=HERE/'strong_event.py';self.assertTrue(source.exists(),'new actual Strong receipt has no consumer')
        spec=importlib.util.spec_from_file_location('test_strong_event_consumer',source)
        m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

    def command(self,*args,text=False):
        command=[str(ROOT/'.venv/bin/python'),'-I','-B',str(HERE/'cli.py'),'mainline',*args]
        if not text:command.append('--json')
        result=subprocess.run(command,capture_output=True,text=True,timeout=45)
        return result,(result.stdout if text else json.loads(result.stdout))

    def test_actual_receipt_and_math_replay_without_native_or_owner_promotion(self):
        module=self.module()
        with patch('subprocess.run',side_effect=AssertionError('native forbidden')),patch('subprocess.Popen',side_effect=AssertionError('child forbidden')):
            result=module.consume()
        self.assertEqual(result['status'],'OBSERVED');self.assertTrue(result['raw_input_and_wire_binding_match'])
        self.assertEqual(result['confirmations_from_retained_D254'],61249)
        self.assertFalse(result['actual_D255_RPC_transport_replayed'])
        self.assertFalse(result['actual_owner_or_full_runtime_authenticated'])
        self.assertEqual(result['project_Strong'],'NOT_ESTABLISHED');self.assertEqual(result['real_admission'],'NOT_READY')
        self.assertEqual(result['protocol_state_change'],'NONE')

    def test_critical_original_omissions_remain_missing(self):
        for role in ('loaded_executable','loaded_request','authorization','reservation','retained_core','replay_a','review'):
            with self.subTest(role=role),tempfile.TemporaryDirectory() as directory:
                mirror(directory);(Path(directory)/ROLES[role]).unlink()
                result=self.module().consume(directory)
                self.assertEqual(result['status'],'MISSING');self.assertFalse(result['raw_input_and_wire_binding_match'])
                self.assertIn(ROLES[role],[r['item'] for r in result['findings']])

    def test_replaced_subject_and_missing_authorization_both_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            mirror(directory);(Path(directory)/ROLES['subject']).write_bytes(b'changed public subject')
            (Path(directory)/ROLES['authorization']).unlink()
            result=self.module().consume(directory)
        self.assertEqual(result['status'],'REJECTED')
        self.assertEqual({r['error'] for r in result['findings']},{'INPUT_IDENTITY_MISMATCH','MISSING_INPUT'})

    def test_mirror_equal_and_math_namespace_restored(self):
        module=self.module();sentinel=object();key='fp_strong_event_math'
        old=sys.modules.get(key,sentinel);poison=object();sys.modules[key]=poison
        try:
            with tempfile.TemporaryDirectory() as directory:
                mirror(directory);self.assertEqual(module.consume(directory),module.consume())
            self.assertIs(sys.modules[key],poison)
        finally:
            if old is sentinel:sys.modules.pop(key,None)
            else:sys.modules[key]=old

    def test_all_inputs_admitted_before_embedded_code_load(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as directory:
            mirror(directory);(Path(directory)/ROLES['loaded_executable']).write_bytes(b'public bad artifact')
            # Reader is admitted separately so this assertion targets math code.
            reader=module.passive_reader()
            with patch('builtins.compile',side_effect=AssertionError('code before all input admission')):
                result=module.consume(directory,reader=reader)
        self.assertEqual(result['status'],'REJECTED')

    def test_catalog_replacement_does_not_read_caller_added_paths(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'scripts/development/offline_evidence/strong_event_inputs.json'
            target.parent.mkdir(parents=True);target.write_text('{"inputs":[{"path":"/not-approved"}]}')
            result=module.consume(source_root=directory)
        self.assertEqual(result['status'],'REJECTED');self.assertEqual(len(result['findings']),1)

    def test_symlink_input_rejected_and_missing_root_does_not_fallback(self):
        module=self.module()
        with tempfile.TemporaryDirectory() as directory:
            missing=module.consume(Path(directory)/'absent')
            self.assertEqual(missing['status'],'MISSING')
            mirror(directory);path=Path(directory)/ROLES['stdout'];path.unlink();path.symlink_to(ROOT/ROLES['stdout'])
            bad=module.consume(directory);self.assertEqual(bad['status'],'REJECTED')

    def test_mainline_composes_new_child_without_readiness_or_hiding_history(self):
        process,report=self.command();self.assertEqual(process.returncode,1)
        time=next(row for row in report['modules'] if row['id']=='time-and-durability')
        self.assertEqual(time['strong_candidate_public_event']['status'],'OBSERVED')
        self.assertEqual(time['public_example']['retained_core_sample']['status'],'OBSERVED')
        self.assertEqual(time['roughtime_nonforecast_event']['status'],'OBSERVED')
        self.assertEqual(time['status'],'MISSING');self.assertEqual(report['real_admission'],'NOT_READY')
        self.assertEqual(report['protocol_state_change'],'NONE')

    def test_mainline_explicit_missing_root_and_changed_record_propagate(self):
        with tempfile.TemporaryDirectory() as directory:
            process,report=self.command('--strong-candidate-inputs',str(Path(directory)/'missing'))
            time=next(row for row in report['modules'] if row['id']=='time-and-durability')
            self.assertEqual(process.returncode,1);self.assertEqual(time['strong_candidate_public_event']['status'],'MISSING')
            mirror(directory);(Path(directory)/ROLES['result']).write_bytes(b'changed public receipt')
            process,report=self.command('--strong-candidate-inputs',directory)
            time=next(row for row in report['modules'] if row['id']=='time-and-durability')
            self.assertEqual(process.returncode,2);self.assertEqual(time['status'],'REJECTED')

    def test_text_explains_public_sample_boundary(self):
        process,text=self.command(text=True);self.assertEqual(process.returncode,1)
        self.assertIn('公开样例Strong候选留存',text);self.assertIn('非项目Strong',text)

if __name__=='__main__':unittest.main()
