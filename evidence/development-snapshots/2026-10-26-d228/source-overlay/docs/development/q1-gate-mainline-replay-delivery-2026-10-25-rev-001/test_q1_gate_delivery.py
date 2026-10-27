"""Current Q1 and gate consumption must survive exact finite transport."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tempfile
import unittest
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PRIOR=ROOT/'docs/development/current-mainline-replay-delivery-2026-10-25-rev-001'
D220=ROOT/'docs/development/mainline-verifier-gate-integration-2026-10-25-rev-001'
BASELINE=D220/'MAINLINE_A.json'
GATE_CATALOG=Path('docs/development/mainline-verifier-gate-integration-2026-10-25-rev-001/GATE_INPUTS.json')
SELECTION=Path('docs/development/q1-2027-read-only-assessment-2026-10-25-rev-001/READ_ONLY_SCOPE_SELECTION.json')


def recipe():
    path=HERE/'build_current_bundle.py'
    if not path.exists():path=PRIOR/'build_current_bundle.py'
    spec=importlib.util.spec_from_file_location('d221_recipe',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def unpack(archive,root):
    with ZipFile(archive) as z:
        for entry in z.infolist():
            p=PurePosixPath(entry.filename)
            assert not p.is_absolute() and '..' not in p.parts
            assert entry.external_attr>>16==stat.S_IFREG|0o644
            target=root/entry.filename;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(entry))


def comparable(report):
    result=deepcopy(report);rows={r['id']:r for r in result['modules']}
    for parent in (rows['finite-reports']['selected_code_loading'],rows['execution-trace']['selected_code_loading'],
                   rows['execution-trace']['source_package_binding']['selected_current_top_level_code']):
        hashes=parent.pop('executed_top_level_code_sha256');assert len(hashes)==21
    return result


class Q1GateDeliveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory();cls.archive=Path(cls.temp.name)/'current.zip';cls.inventory=None
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def build(self):
        if self.__class__.inventory is None:
            try:self.__class__.inventory=recipe().build_bundle(self.archive)
            except Exception as e:self.fail('current Q1/gate closure cannot be transported: '+str(e))
        return self.__class__.inventory
    def command(self,root,command='mainline'):
        p=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B',str(root/'scripts/development/offline_evidence/cli.py'),command,'--json'],
                         cwd=root,capture_output=True,text=True,timeout=50)
        self.assertTrue(p.stdout.strip(),p.stderr);return p,json.loads(p.stdout)

    def test_full_current_report_replays_in_two_new_roots(self):
        self.build();baseline=comparable(json.loads(BASELINE.read_text()))
        for _ in range(2):
            with tempfile.TemporaryDirectory() as name:
                root=Path(name);unpack(self.archive,root);p,r=self.command(root)
                self.assertEqual(p.returncode,1);self.assertEqual(comparable(r),baseline)
                rows={x['id']:x for x in r['modules']}
                gate=rows['initial-authority']['result']['technical_verifier_identity_gate']
                self.assertEqual(gate['status'],'OBSERVED');self.assertEqual(gate['consumed_distinct_gate_inputs'],63)
                self.assertEqual(rows['official-calendar']['read_only_assessment']['status'],'OBSERVED')
                self.assertEqual(rows['official-calendar']['predecessor_calendar_binding']['matched_predecessor_count'],3)

    def test_new_gate_omission_and_same_size_substitution_survive_transport(self):
        self.build();catalog=json.loads((ROOT/GATE_CATALOG).read_text())
        generated=next(r['path'] for r in catalog['inputs'] if '/generated/' in r['path'])
        source=next(r['path'] for r in catalog['inputs'] if '/public-verifier-source/' in r['path'])
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);unpack(self.archive,root);(root/generated).unlink()
            f=root/source;b=f.read_bytes();f.write_bytes(bytes([b[0]^1])+b[1:]);p,r=self.command(root)
        self.assertEqual(p.returncode,2);rows={x['id']:x for x in r['modules']};row=rows['initial-authority']
        self.assertEqual(row['status'],'REJECTED');self.assertEqual({f['status'] for f in row['findings']},{'MISSING','REJECTED'})
        self.assertEqual(rows['official-calendar']['read_only_assessment']['status'],'OBSERVED')
        self.assertEqual(row['result']['technical_verifier_contract_candidate']['artifact_binding_status'],'OBSERVED')

    def test_missing_q1_choice_and_gate_catalog_never_use_original_repository(self):
        self.build()
        with tempfile.TemporaryDirectory() as name:
            root=Path(name);unpack(self.archive,root);(root/SELECTION).unlink();(root/GATE_CATALOG).unlink();p,r=self.command(root)
        self.assertEqual(p.returncode,1);rows={x['id']:x for x in r['modules']}
        self.assertEqual(rows['official-calendar']['read_only_assessment']['status'],'MISSING')
        self.assertEqual(rows['initial-authority']['result']['technical_verifier_identity_gate']['status'],'MISSING')
        self.assertEqual(rows['economic-data']['status'],'OBSERVED')

    def test_all_current_inputs_safe_deterministic_bounded_and_wheel_sourced(self):
        inventory=self.build();catalog=json.loads((ROOT/GATE_CATALOG).read_text())
        with ZipFile(self.archive) as z:
            names=z.namelist();self.assertEqual(len(names),len(set(names)))
            self.assertEqual(set(names),{r['path'] for r in inventory['files']}|{'DEVELOPMENT_BUNDLE_MANIFEST.json'})
            for r in inventory['files']:
                raw=z.read(r['path']);self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(r['bytes'],r['sha256']))
                self.assertEqual(z.getinfo(r['path']).external_attr>>16,stat.S_IFREG|0o644)
            for r in catalog['inputs']:
                self.assertIn(r['path'],names);self.assertEqual(hashlib.sha256(z.read(r['path'])).hexdigest(),r['sha256'])
            self.assertIn(str(SELECTION),names);self.assertIn(str(GATE_CATALOG),names)
            self.assertNotIn('owner-initial-ed25519.pub','\n'.join(names));self.assertNotIn('AGENTS.md',names)
            self.assertLess(sum(x.file_size for x in z.infolist()),64*1024*1024)
        for name in ('architecture_compression_v1.py','claim_authority_contract_gate_v1.py','claim_authority_v1.py','claim_authority_v1_legacy.py'):
            row=next(r for r in inventory['files'] if r['path']=='src/forecast_trust_core/'+name)
            self.assertEqual(row['origin']['kind'],'FIXED_PUBLIC_WHEEL_MEMBER')
        with tempfile.TemporaryDirectory() as name:
            other=Path(name)/'same.zip';recipe().build_bundle(other);self.assertEqual(self.archive.read_bytes(),other.read_bytes())
            root=Path(name)/'root';root.mkdir();unpack(self.archive,root);p,r=self.command(root,'demo')
            self.assertEqual(p.returncode,0);self.assertEqual(len(r['cases']),5)

    def test_refused_new_helper_creates_no_archive_or_overwrite(self):
        self.build()
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)/'root';root.mkdir();unpack(self.archive,root)
            (root/'scripts/development/offline_evidence/verifier_gate.py').write_bytes(b'raise AssertionError("unadmitted source")\n')
            out=Path(name)/'refused.zip'
            with self.assertRaises(Exception):recipe().build_bundle(out,root=root)
            self.assertFalse(out.exists())
        before=self.archive.read_bytes()
        with self.assertRaises(FileExistsError):recipe().build_bundle(self.archive)
        self.assertEqual(self.archive.read_bytes(),before)


if __name__=='__main__':unittest.main()
