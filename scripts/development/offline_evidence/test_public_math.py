"""Retained public math evidence binds to the same admitted development bytes."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PACKAGE=ROOT/'docs/development/public-math-mainline-consumption-2026-10-28-rev-001'


def load(name):
    path=HERE/(name+'.py')
    if not path.is_file():raise AssertionError('D272 retained math consumer not implemented')
    m=ModuleType('d272_test_'+name);m.__file__=str(path);sys.modules[m.__name__]=m
    exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__)
    return m


class PublicMathTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest_raw=(PACKAGE/'EXPECTED_INPUTS.json').read_bytes()
        cls.manifest=json.loads(cls.manifest_raw)
        cls.raws={row['path']:(ROOT/row['path']).read_bytes() for row in cls.manifest['inputs']}

    def test_consumes_exact_seventy_snapshots_without_io_or_backend(self):
        m=load('public_math');seen=[]
        with patch.object(Path,'read_bytes',side_effect=AssertionError('unexpected read')), \
             patch.object(os,'open',side_effect=AssertionError('unexpected open')):
            r=m.consume(self.manifest_raw,lambda row:(seen.append(row['path']),self.raws[row['path']])[1])
        self.assertEqual(r['status'],'OBSERVED');self.assertEqual(len(seen),70)
        self.assertEqual(r['bound_execution_input_count'],67)
        self.assertEqual(r['retained_math_statuses'],{'305':'VERIFIED','0':'REJECTED'})
        self.assertFalse(r['native_loaded_here']);self.assertFalse(r['backend_called_here'])
        self.assertEqual(r['real_admission'],'NOT_READY')
        self.assertEqual(r['full_build_runtime_closure'],'NOT_ESTABLISHED')

    def test_missing_report_and_replaced_source_both_survive(self):
        m=load('public_math');raws=dict(self.raws)
        raws.pop(self.manifest['reports'][1]);raws[self.manifest['execution_source']]=b'public replacement'
        r=m.consume(self.manifest_raw,lambda row:raws.get(row['path']))
        self.assertEqual(r['status'],'REJECTED')
        self.assertEqual({x['status'] for x in r['findings']},{'MISSING','REJECTED'})

    def test_joint_shrink_is_refused_before_input_calls(self):
        m=load('public_math');manifest=deepcopy(self.manifest)
        manifest['inputs'].pop();manifest['execution_inputs'].pop();seen=[]
        r=m.consume(json.dumps(manifest).encode(),lambda row:seen.append(row))
        self.assertEqual(r['status'],'REJECTED');self.assertEqual(seen,[])

    def test_semantic_source_message_scope_and_safety_substitution_refused(self):
        m=load('public_math');original=json.loads(self.raws[self.manifest['reports'][0]])
        for change in ('source','message','flag','universe','gate'):
            report=deepcopy(original)
            if change=='source':report['child_source_sha256']='0'*64
            elif change=='message':report['samples'][0]['message_sha256']='0'*64
            elif change=='flag':report['samples'][0]['prospective_eligible']=0
            elif change=='universe':report['input_identities'].pop()
            else:report['gate']['actual_adapter_distinct_read_paths']=62
            with self.subTest(change=change):
                with self.assertRaises(ValueError):m._validate_report(report,self.manifest,self.raws)

    def test_integration_reuses_same_sixty_six_admitted_byte_objects(self):
        m=load('mainline_worker');shared={};gate={}
        m.signing_candidates(gate_output=gate,gate_snapshot_output=shared)
        self.assertEqual(len(shared),66);self.assertTrue(all(type(v) is bytes for v in shared.values()))
        original=m.reader.read_fixed;seen=[]
        def read(root,name,row):
            self.assertNotIn(str(name),shared,'borrowed snapshot was reread')
            seen.append(str(name));return original(root,name,row)
        with patch.object(m.reader,'read_fixed',side_effect=read):r=m.technical_public_math(shared)
        self.assertEqual(r['status'],'OBSERVED');self.assertEqual(r['reused_admitted_snapshots'],66)
        self.assertEqual(len(seen),6) # manifest, consumer, corpus, execution source, two reports
        for name,raw in shared.items():self.assertEqual(raw,self.raws[name])

    def test_nonadmitted_borrowed_input_has_no_repository_fallback(self):
        m=load('mainline_worker');shared={};gate={}
        m.signing_candidates(gate_output=gate,gate_snapshot_output=shared)
        name=next(n for n in shared if n.endswith('fp_public_verify.dylib'));shared[name]=None
        original=m.reader.read_fixed
        def read(root,relative,row):
            self.assertNotEqual(str(relative),name);return original(root,relative,row)
        with patch.object(m.reader,'read_fixed',side_effect=read):r=m.technical_public_math(shared)
        self.assertEqual(r['status'],'MISSING');self.assertEqual(r['reused_admitted_snapshots'],65)

    def test_actual_mainline_only_adds_child_and_two_cwd_outputs_equal(self):
        outputs=[]
        with tempfile.TemporaryDirectory() as directory:
            for cwd in (ROOT,Path(directory)):
                p=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B',str(HERE/'cli.py'),'mainline','--json'],
                                 cwd=cwd,capture_output=True,timeout=50)
                self.assertEqual(p.returncode,1,p.stderr.decode());outputs.append(p.stdout)
        self.assertEqual(outputs[0],outputs[1]);report=json.loads(outputs[0])
        row=next(r for r in report['modules'] if r['id']=='initial-authority')
        child=row['result'].pop('technical_public_math_execution')
        choices=row['result'].pop('independent_source_choices')
        preflight=row['result'].pop('technical_initial_auth_input_preflight')
        self.assertEqual(preflight['status'],'MISSING')
        self.assertEqual(preflight['admitted_data_inputs'],3);self.assertFalse(preflight['may_load_backend'])
        self.assertEqual(choices['status'],'OBSERVED')
        self.assertTrue(choices['owner_role_choice_supplied']);self.assertTrue(choices['software_basis_choice_supplied'])
        self.assertEqual(child['status'],'OBSERVED');self.assertEqual(child['reused_admitted_snapshots'],66)
        self.assertEqual(row['status'],'MISSING');self.assertEqual(row['result']['status'],'UNKNOWN')
        old=json.loads((ROOT/'docs/development/bls-clock-mainline-consumption-2026-10-28-rev-001/MAINLINE_A.json').read_text())
        self.assertEqual(report,old)
        # Historical D272 reports are evidence, never mutable test output.

if __name__=='__main__':unittest.main()
