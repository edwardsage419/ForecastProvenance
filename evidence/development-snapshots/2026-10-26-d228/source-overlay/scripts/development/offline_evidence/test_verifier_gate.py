"""The fixed identity gate consumes admitted bytes, without loading native code."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PACKAGE=ROOT/'docs/development/mainline-verifier-gate-integration-2026-10-25-rev-001'
BUILD=Path('docs/development/mainline-execution-2026-10-09-rev-001/public-verifier-build')


def load(path):
    spec=importlib.util.spec_from_file_location('d220_'+path.stem,path)
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    return module


class VerifierGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog_raw=(PACKAGE/'GATE_INPUTS.json').read_bytes()
        cls.catalog=json.loads(cls.catalog_raw)
        cls.raws={r['path']:(ROOT/r['path']).read_bytes() for r in cls.catalog['inputs']}

    def consumer(self):
        self.assertTrue((HERE/'verifier_gate.py').is_file(),'same-run gate consumer absent')
        return load(HERE/'verifier_gate.py')

    def consume(self,raws=None,catalog=None):
        data=self.raws if raws is None else raws
        return self.consumer().consume(self.catalog_raw if catalog is None else catalog,
                                       lambda row:data.get(row['path']))

    def command(self,*args):
        p=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B',str(HERE/'cli.py'),*args],
                         capture_output=True,text=True,timeout=50)
        self.assertTrue(p.stdout.strip(),'command produced no report: '+p.stderr)
        return p

    def mirror(self,base):
        for name,raw in self.raws.items():
            target=base/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)

    def test_actual_selected_gate_reads_all_declared_snapshots_without_io_or_native(self):
        module=self.consumer();before=deepcopy(self.raws)
        with patch('builtins.open',side_effect=AssertionError('gate attempted IO')), \
             patch.object(os,'open',side_effect=AssertionError('gate attempted IO')), \
             patch.object(Path,'read_bytes',side_effect=AssertionError('gate attempted IO')):
            result=module.consume(self.catalog_raw,lambda row:self.raws[row['path']])
        self.assertEqual(result['status'],'OBSERVED');self.assertEqual(result['admitted_input_count'],64)
        self.assertEqual(result['consumed_distinct_gate_inputs'],63)
        self.assertEqual(result['gate_snapshot_read_calls'],66)
        self.assertTrue(result['all_declared_gate_inputs_consumed']);self.assertTrue(result['gate_check_executed'])
        self.assertEqual(self.raws,before)
        for flag in ('native_loaded','backend_called','message_constructed'):
            self.assertFalse(result[flag])
        self.assertEqual(result['full_build_runtime_closure'],'NOT_ESTABLISHED')
        self.assertEqual(result['public_authentication'],'NOT_ESTABLISHED')
        self.assertEqual(result['real_admission'],'NOT_READY');self.assertEqual(result['protocol_state_change'],'NONE')

    def test_catalog_joint_shrink_rejected_before_reading_any_paths(self):
        changed=deepcopy(self.catalog);removed=changed['inputs'].pop()
        changed['gate_paths']=[p for p in changed['gate_paths'] if p!=removed['path']]
        calls=[];result=self.consumer().consume(json.dumps(changed).encode(),lambda row:calls.append(row))
        self.assertEqual(result['status'],'REJECTED');self.assertEqual(calls,[])
        self.assertFalse(result['gate_check_executed'])

    def test_same_size_native_generated_source_pre_and_bootstrap_substitutions_rejected(self):
        names=[str(BUILD/'native/fp_public_verify.dylib'),str(BUILD/'PRE_RUN.json'),
               self.catalog['binding_module'],self.catalog['gate_module'],
               next(x for x in self.raws if '/generated/' in x),
               next(x for x in self.raws if '/public-verifier-source/' in x)]
        for name in names:
            with self.subTest(path=name):
                raws=dict(self.raws);b=raws[name];raws[name]=bytes([b[0]^1])+b[1:]
                result=self.consume(raws)
                self.assertEqual(result['status'],'REJECTED');self.assertFalse(result['gate_check_executed'])
                self.assertIn(name,[f['item'] for f in result['findings']])

    def test_omission_retains_fixed_required_scope_instead_of_empty_success(self):
        for name in (self.catalog['binding_module'],next(x for x in self.raws if '/generated/' in x)):
            with self.subTest(path=name):
                raws=dict(self.raws);raws.pop(name);r=self.consume(raws)
                self.assertEqual(r['status'],'MISSING');self.assertFalse(r['gate_check_executed'])
                self.assertEqual(r['required_declared_gate_inputs'],63)
                self.assertEqual(r['consumed_distinct_gate_inputs'],0)

    def test_known_failure_and_missing_both_survive(self):
        raws=dict(self.raws);raws.pop(self.catalog['binding_module'])
        name=str(BUILD/'native/fp_public_verify.dylib');raws[name]=b'wrong'
        result=self.consume(raws)
        self.assertEqual(result['status'],'REJECTED')
        self.assertEqual({f['status'] for f in result['findings']},{'REJECTED','MISSING'})

    def test_all_inputs_admitted_before_gate_no_unknown_runtime_file_reads(self):
        module=self.consumer();seen=[]
        def read(row):seen.append(row['path']);return self.raws[row['path']]
        result=module.consume(self.catalog_raw,read)
        self.assertEqual(result['status'],'OBSERVED')
        self.assertEqual(len(seen),64);self.assertEqual(len(set(seen)),64)
        self.assertEqual(set(result['gate_read_paths']),set(self.catalog['gate_paths']))

    def test_actual_default_mainline_adds_only_gate_child_and_reuses_eight_snapshots(self):
        p=self.command('mainline','--json');self.assertEqual(p.returncode,1,p.stderr)
        report=json.loads(p.stdout);row=next(x for x in report['modules'] if x['id']=='initial-authority')
        self.assertIn('technical_verifier_identity_gate',row['result'])
        result=row['result'].pop('technical_verifier_identity_gate')
        self.assertEqual(result['status'],'OBSERVED');self.assertEqual(result['reused_admitted_snapshots'],8)
        self.assertEqual(result['consumed_distinct_gate_inputs'],63)
        baseline=json.loads((ROOT/'docs/development/q1-predecessor-calendar-binding-2026-10-25-rev-001/MAINLINE_A.json').read_text())
        # New A1/Table1 children have their own exact tests; preserve this older projection.
        for module in report['modules']:
            if module['id'] in ('unemployment-july','unemployment-november','inflation-data'):
                self.assertEqual(module.pop('target_table_support')['comparison']['status'],'OBSERVED')
        self.assertEqual(report,baseline);self.assertEqual(len(report['modules']),14)
        self.assertEqual(row['result']['technical_verifier_contract_candidate']['all_source_and_gate_inputs_checked'],'NOT_ESTABLISHED')

    def test_explicit_complete_mirror_uses_its_own_snapshots(self):
        with tempfile.TemporaryDirectory() as name:
            self.mirror(Path(name));p=self.command('mainline','--verifier-gate-inputs',name,'--json')
        self.assertEqual(p.returncode,1,p.stderr)
        r=next(x for x in json.loads(p.stdout)['modules'] if x['id']=='initial-authority')['result']['technical_verifier_identity_gate']
        self.assertEqual(r['status'],'OBSERVED');self.assertEqual(r['reused_admitted_snapshots'],0)
        self.assertEqual(r['admitted_input_count'],64)

    def test_mirror_corruption_and_omission_reach_parent_without_hiding_other_modules(self):
        with tempfile.TemporaryDirectory() as name:
            base=Path(name);self.mirror(base)
            (base/BUILD/'native/fp_public_verify.dylib').write_bytes(b'wrong')
            (base/self.catalog['binding_module']).unlink()
            p=self.command('mainline','--verifier-gate-inputs',name,'--json')
        self.assertEqual(p.returncode,2,p.stderr)
        modules={x['id']:x for x in json.loads(p.stdout)['modules']};row=modules['initial-authority']
        self.assertEqual(row['status'],'REJECTED');self.assertEqual(modules['economic-data']['status'],'OBSERVED')
        self.assertEqual({f['status'] for f in row['findings']},{'REJECTED','MISSING'})
        self.assertFalse(row['result']['technical_verifier_identity_gate']['gate_check_executed'])

    def test_empty_and_symlink_explicit_inputs_do_not_fall_back(self):
        with tempfile.TemporaryDirectory() as name:
            p=self.command('mainline','--verifier-gate-inputs',name,'--json')
            self.assertEqual(p.returncode,1,p.stderr)
            row=next(x for x in json.loads(p.stdout)['modules'] if x['id']=='initial-authority')
            self.assertEqual(row['result']['technical_verifier_identity_gate']['status'],'MISSING')
            target=Path(name)/self.catalog['gate_module'];target.parent.mkdir(parents=True)
            target.symlink_to(ROOT/self.catalog['gate_module'])
            p=self.command('mainline','--verifier-gate-inputs',name,'--json')
            self.assertEqual(p.returncode,2,p.stderr)
            row=next(x for x in json.loads(p.stdout)['modules'] if x['id']=='initial-authority')
            self.assertEqual(row['result']['technical_verifier_identity_gate']['status'],'REJECTED')

    def test_rejected_shared_native_is_not_read_twice(self):
        self.consumer();worker=load(HERE/'mainline_worker.py')
        with tempfile.TemporaryDirectory() as name:
            base=Path(name);self.mirror(base)
            (base/BUILD/'CONTRACT_CANDIDATE.json').write_bytes((ROOT/'docs/development/verifier-contract-consumption-2026-10-25-rev-001/CONTRACT_CANDIDATE.json').read_bytes())
            native=base/BUILD/'native/fp_public_verify.dylib';native.write_bytes(b'wrong');calls=[]
            original=worker.reader.read_fixed
            def observed(directory,relative,expected):
                if Path(directory)/relative==native:
                    calls.append(str(native));self.assertEqual(len(calls),1,'reopened a rejected shared path')
                return original(directory,relative,expected)
            output={}
            with patch.object(worker.reader,'read_fixed',side_effect=observed):
                _,old=worker.signing_candidates(None,base/BUILD,gate_directory=base,gate_output=output)
        self.assertEqual(len(calls),1);self.assertEqual(old['status'],'REJECTED');self.assertEqual(output['status'],'REJECTED')

    def test_human_describes_finite_gate_scope_and_no_authentication(self):
        p=self.command('mainline');self.assertEqual(p.returncode,1,p.stderr)
        self.assertIn('声明输入身份检查',p.stdout);self.assertIn('63',p.stdout);self.assertIn('64',p.stdout)
        self.assertIn('未执行原生验签',p.stdout)

    def test_independent_audit_denies_io_native_network_and_processes(self):
        self.consumer()
        program='''import ast, hashlib, json, sys
from pathlib import Path
from types import ModuleType
root=Path(sys.argv[1]); here=root/'scripts/development/offline_evidence'
raw=(root/'docs/development/mainline-verifier-gate-integration-2026-10-25-rev-001/GATE_INPUTS.json').read_bytes()
blobs={r['path']:(root/r['path']).read_bytes() for r in json.loads(raw)['inputs']}
source=(here/'verifier_gate.py').read_bytes(); denied=[]
def audit(event,args):
 if event=='open' or event.startswith(('ctypes.','socket.')) or event in {'subprocess.Popen','os.system','os.exec','os.fork','os.posix_spawn'}:
  denied.append(event); raise RuntimeError('D220_FORBIDDEN_OPERATION')
sys.addaudithook(audit)
m=ModuleType('d220_audited_gate');exec(compile(source,str(here/'verifier_gate.py'),'exec'),m.__dict__)
result=m.consume(raw,lambda row:blobs.get(row['path']))
print(json.dumps({'status':result['status'],'consumed':result['consumed_distinct_gate_inputs'],'denied':denied}))
'''
        p=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B','-c',program,str(ROOT)],
                         capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout),{'status':'OBSERVED','consumed':63,'denied':[]})


if __name__=='__main__':unittest.main()
