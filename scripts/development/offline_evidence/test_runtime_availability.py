"""Unavailable dependencies do not turn unexecuted checks into bad evidence."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tempfile
import unittest
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
BUNDLED=Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
BASELINE=ROOT/'docs/development/mainline-verifier-gate-integration-2026-10-25-rev-001/MAINLINE_A.json'
ARCHIVE=ROOT/'docs/development/q1-gate-mainline-replay-delivery-2026-10-25-rev-001/q1-gate-mainline-replay.zip'


class RuntimeAvailabilityTests(unittest.TestCase):
    def command(self,python,root=ROOT,*args):
        p=subprocess.run([str(python),'-I','-B',str(root/'scripts/development/offline_evidence/cli.py'),
                          'mainline',*args,'--json'],cwd=root,capture_output=True,text=True,timeout=50)
        self.assertTrue(p.stdout.strip(),p.stderr);return p,json.loads(p.stdout)

    def test_actual_missing_jsonschema_is_unavailable_not_rejected(self):
        p,r=self.command(BUNDLED)
        self.assertEqual(p.returncode,1)
        modules={x['id']:x for x in r['modules']};failed=modules['module-consumption']
        self.assertEqual(failed['status'],'UNAVAILABLE');self.assertEqual(failed['error'],'MISSING_DEPENDENCY')
        self.assertEqual(r['overall'],'UNRESOLVED');self.assertEqual(modules['economic-data']['status'],'OBSERVED')
        self.assertEqual(modules['official-calendar']['read_only_assessment']['status'],'OBSERVED')
        self.assertEqual(r['real_admission'],'NOT_READY');self.assertEqual(r['protocol_state_change'],'NONE')

    def test_bad_time_inputs_remain_rejected_beside_missing_dependency(self):
        with tempfile.TemporaryDirectory() as name:
            (Path(name)/'raw').mkdir();(Path(name)/'raw/gdp2q25-2nd.pdf').write_bytes(b'wrong public sample')
            p,r=self.command(BUNDLED,ROOT,'--proof-inputs',name)
        self.assertEqual(p.returncode,2);modules={x['id']:x for x in r['modules']}
        self.assertEqual(modules['module-consumption']['status'],'UNAVAILABLE')
        self.assertEqual(modules['time-and-durability']['status'],'REJECTED')
        self.assertEqual({f['status'] for f in modules['time-and-durability']['public_example']['findings']},{'REJECTED','MISSING'})
        self.assertEqual(modules['economic-data']['status'],'OBSERVED');self.assertEqual(r['overall'],'REJECTED')

    def test_compatible_runtime_has_exactly_unchanged_report(self):
        p,r=self.command(ROOT/'.venv/bin/python')
        self.assertEqual(p.returncode,1)
        # Only the two A1 and one CPI Table1 children are removed for historical parity.
        for module in r['modules']:
            if module['id'] in ('unemployment-july','unemployment-november','inflation-data'):
                self.assertEqual(module.pop('target_table_support')['comparison']['status'],'OBSERVED')
        projected=json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
        self.assertEqual(projected.encode(),BASELINE.read_bytes())

    def test_exact_base_delivery_with_worker_overlay_preserves_source_refusal(self):
        self.assertEqual(hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
                         '929c335232c9eae1ccde94bab6dca9b2395cf8c6600579a673e4f09ba69f648f')
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            with ZipFile(ARCHIVE) as z:
                inventory=json.loads(z.read('DEVELOPMENT_BUNDLE_MANIFEST.json'))
                by_name={r['path']:r for r in inventory['files']}
                for member in z.infolist():
                    path=PurePosixPath(member.filename);self.assertFalse(path.is_absolute());self.assertNotIn('..',path.parts)
                    self.assertEqual(member.external_attr>>16,stat.S_IFREG|0o644)
                    raw=z.read(member)
                    if member.filename in by_name:
                        expected=by_name[member.filename]
                        self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(expected['bytes'],expected['sha256']))
                    target=root/member.filename;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            worker=root/'scripts/development/offline_evidence/mainline_worker.py'
            self.assertEqual(hashlib.sha256(worker.read_bytes()).hexdigest(),
                             'c4419ed7f1208921a43292eaa3095c582878aed3c7b6546b6fb51de46e5e0893')
            worker.write_bytes((HERE/'mainline_worker.py').read_bytes())
            p,r=self.command(BUNDLED,root)
            self.assertEqual(p.returncode,1)
            self.assertEqual(next(x for x in r['modules'] if x['id']=='module-consumption')['status'],'UNAVAILABLE')
            source=root/'src/forecast_trust_core/finite_development/_report_set.py'
            raw=source.read_bytes();source.write_bytes(bytes([raw[0]^1])+raw[1:])
            p,r=self.command(BUNDLED,root)
            self.assertEqual(p.returncode,2)
            failed=next(x for x in r['modules'] if x['id']=='module-consumption')
            self.assertEqual(failed['status'],'REJECTED')
            self.assertEqual(failed['scope'],'SELECTED_PRODUCT_CODE_ADMISSION_FAILED')

    def test_later_dependency_failure_does_not_erase_earlier_rejection(self):
        # Inject only the later dependency failure, retaining the real earlier
        # source admission and finite consumer on deliberately bad public input.
        program='''import importlib.util, io, json, sys
from pathlib import Path
root=Path(sys.argv[1]);path=root/'scripts/development/offline_evidence/mainline_worker.py'
spec=importlib.util.spec_from_file_location('d222_late_worker',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def unavailable_later(*args,**kwargs):raise ModuleNotFoundError('dependency unavailable later')
m.missing_input_modules=unavailable_later
sys.stdin=io.StringIO(json.dumps({'run_inputs':sys.argv[2]}));m.main()
'''
        with tempfile.TemporaryDirectory() as name:
            (Path(name)/'INPUT_SET.json').write_bytes(b'wrong retained public input')
            p=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B','-c',program,str(ROOT),name],
                             capture_output=True,text=True,timeout=30)
        self.assertEqual(p.returncode,0,p.stderr)
        rows={r['id']:r for r in json.loads(p.stdout)['modules']}
        self.assertIn('finite-reports',rows)
        self.assertEqual(rows['finite-reports']['status'],'REJECTED')
        self.assertEqual(rows['module-consumption']['status'],'UNAVAILABLE')
        self.assertEqual(rows['time-and-durability']['status'],'MISSING')


if __name__=='__main__':unittest.main()
