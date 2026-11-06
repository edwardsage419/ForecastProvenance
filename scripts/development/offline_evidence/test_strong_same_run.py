"""Same-run public reply snapshots; no Core, native action or new controls."""
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
CATALOG=json.loads((HERE/'strong_same_run_inputs.json').read_bytes())
ROLES=CATALOG['roles']

def mirror(directory):
    for row in CATALOG['inputs']:
        path=Path(directory)/row['path'];path.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/row['path'],path)

class SameRunTests(unittest.TestCase):
    def module(self):
        path=HERE/'strong_same_run.py';self.assertTrue(path.exists(),'same-run public bytes have no mainline consumer')
        spec=importlib.util.spec_from_file_location('test_same_run_consumer',path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

    def command(self,*args,text=False):
        command=[str(ROOT/'.venv/bin/python'),'-I','-B',str(HERE/'cli.py'),'mainline',*args]
        if not text:command.append('--json')
        r=subprocess.run(command,capture_output=True,text=True,timeout=45)
        return r,(r.stdout if text else json.loads(r.stdout))

    def test_same_run_snapshot_consumption_without_native_or_authority(self):
        m=self.module()
        with patch('subprocess.run',side_effect=AssertionError('native forbidden')),patch('subprocess.Popen',side_effect=AssertionError('child forbidden')):
            result=m.consume()
        self.assertEqual(result['status'],'OBSERVED');self.assertEqual(result['observation']['raw_reply_count'],6)
        self.assertTrue(result['observation']['all_recorded_results_consumed'])
        self.assertTrue(result['observation']['local_success_references_separately_checked'])
        self.assertFalse(result['observation']['HTTP_TCP_transport_packets_replayed'])
        self.assertFalse(result['observation']['independent_actual_execution_or_owner_authentication'])
        self.assertEqual(result['real_admission'],'NOT_READY');self.assertEqual(result['protocol_state_change'],'NONE')

    def test_missing_trace_and_changed_result_both_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            mirror(directory);(Path(directory)/ROLES['RPC_TRANSCRIPT.jsonl']).unlink()
            (Path(directory)/ROLES['RESULT.json']).write_bytes(b'public changed record')
            result=self.module().consume(directory)
        self.assertEqual(result['status'],'REJECTED')
        self.assertEqual({r['error'] for r in result['findings']},{'MISSING_INPUT','INPUT_IDENTITY_MISMATCH'})

    def test_all_critical_originals_required(self):
        for role in ('CORE_OPERATION_AUTHORIZATION.json','CORE_READ_RESERVED.json','CORE_READ_EXECUTABLE.py','CANDIDATE_STDOUT.raw','RPC_TRANSCRIPT.jsonl','review','replay_a'):
            with self.subTest(role=role),tempfile.TemporaryDirectory() as directory:
                mirror(directory);(Path(directory)/ROLES[role]).unlink();result=self.module().consume(directory)
                self.assertEqual(result['status'],'MISSING');self.assertIsNone(result['observation'])

    def test_capture_then_remove_files_does_not_reread_or_follow_record_paths(self):
        m=self.module();reader=m.passive_reader();original=reader.read_fixed;seen=[]
        with tempfile.TemporaryDirectory() as directory:
            mirror(directory)
            def capture(base,path,row):
                raw=original(base,path,row)
                if Path(base).absolute()==Path(directory).absolute():
                    seen.append(path)
                    if len(seen)==len(CATALOG['inputs']):
                        (Path(directory)/ROLES['CORE_READ_REQUEST.raw']).unlink()
                        (Path(directory)/ROLES['RPC_TRANSCRIPT.jsonl']).unlink()
                return raw
            reader.read_fixed=capture
            result=m.consume(directory,reader=reader)
        self.assertEqual(result['status'],'OBSERVED');self.assertEqual(len(seen),len(CATALOG['inputs']))

    def test_mirror_equal_and_namespace_restored(self):
        m=self.module();key='fp_same_run_public_math';sentinel=object();old=sys.modules.get(key,sentinel);poison=object();sys.modules[key]=poison
        try:
            with tempfile.TemporaryDirectory() as directory:mirror(directory);self.assertEqual(m.consume(directory),m.consume())
            self.assertIs(sys.modules[key],poison)
        finally:
            if old is sentinel:sys.modules.pop(key,None)
            else:sys.modules[key]=old

    def test_catalog_replacement_rejected_before_input_read(self):
        m=self.module()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'scripts/development/offline_evidence/strong_same_run_inputs.json';path.parent.mkdir(parents=True)
            path.write_text('{"inputs":[{"path":"/unapproved"}]}')
            result=m.consume(source_root=directory)
        self.assertEqual(result['status'],'REJECTED');self.assertEqual(len(result['findings']),1)

    def test_symlink_rejected_and_missing_root_no_fallback(self):
        m=self.module()
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(m.consume(Path(directory)/'absent')['status'],'MISSING')
            mirror(directory);path=Path(directory)/ROLES['RPC_TRANSCRIPT.jsonl'];path.unlink();path.symlink_to(ROOT/ROLES['RPC_TRANSCRIPT.jsonl'])
            self.assertEqual(m.consume(directory)['status'],'REJECTED')

    def test_mainline_keeps_older_observations_and_not_ready(self):
        process,report=self.command();self.assertEqual(process.returncode,1)
        t=next(r for r in report['modules'] if r['id']=='time-and-durability')
        self.assertEqual(t['same_run_public_core_replay']['status'],'OBSERVED')
        self.assertEqual(t['strong_candidate_public_event']['status'],'OBSERVED')
        self.assertEqual(t['roughtime_nonforecast_event']['status'],'OBSERVED')
        self.assertEqual(t['public_example']['retained_core_sample']['status'],'OBSERVED')
        self.assertEqual(t['status'],'MISSING');self.assertEqual(report['real_admission'],'NOT_READY')

    def test_explicit_missing_and_changed_new_event_propagate(self):
        with tempfile.TemporaryDirectory() as directory:
            process,report=self.command('--strong-candidate-inputs',str(Path(directory)/'missing'))
            t=next(r for r in report['modules'] if r['id']=='time-and-durability');self.assertEqual(process.returncode,1)
            self.assertEqual(t['same_run_public_core_replay']['status'],'MISSING')
            mirror(directory);(Path(directory)/ROLES['RPC_TRANSCRIPT.jsonl']).write_bytes(b'public changed trace')
            process,report=self.command('--strong-candidate-inputs',directory)
            t=next(r for r in report['modules'] if r['id']=='time-and-durability');self.assertEqual(process.returncode,2)
            self.assertEqual(t['same_run_public_core_replay']['status'],'REJECTED');self.assertEqual(t['status'],'REJECTED')

    def test_text_scope_is_clear(self):
        process,text=self.command(text=True);self.assertEqual(process.returncode,1)
        self.assertIn('同次公开CLI数学重放',text);self.assertIn('非项目Strong',text)

if __name__=='__main__':unittest.main()
