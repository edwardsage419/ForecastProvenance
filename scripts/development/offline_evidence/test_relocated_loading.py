"""Admitted relocated sources must win over the ambient product installation."""
import ast
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN = Path('docs/development/mainline-execution-2026-10-18-observed-five-report-replay-rev-001')


def selected_sources():
    tree = ast.parse((HERE/'replay_provenance.py').read_bytes())
    assignment = next(node for node in tree.body if isinstance(node, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'FINITE_PRODUCT_SOURCES'
                              for t in node.targets))
    return ast.literal_eval(assignment.value)


def copy_record_tree(value, root):
    if type(value) is dict:
        if set(value) == {'path', 'bytes', 'sha256'}:
            target = root/RUN/value['path']; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/RUN/value['path'], target)
        else:
            for item in value.values():
                copy_record_tree(item, root)
    elif type(value) is list:
        for item in value:
            copy_record_tree(item, root)


class RelocatedLoadingTests(unittest.TestCase):
    def stage(self, root):
        for row in selected_sources():
            target = root/row['path']; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/row['path'], target)
        target = root/'scripts/development/offline_evidence'; target.mkdir(parents=True)
        for name in ['mainline_worker.py', 'replay_provenance.py', 'worker.py', 'catalog.json']:
            shutil.copyfile(HERE/name, target/name)
        (root/RUN).mkdir(parents=True)
        shutil.copyfile(ROOT/RUN/'INPUT_SET.json', root/RUN/'INPUT_SET.json')
        copy_record_tree(json.loads((ROOT/RUN/'INPUT_SET.json').read_bytes())['inputs'], root)

    def probe(self, root, body):
        # The existing interpreter retains its normal ambient installation;
        # the relocated product is NOT added to PYTHONPATH or sys.path.
        program = '''import json, sys
from pathlib import Path
from types import ModuleType
root = Path(sys.argv[1])
here = root/'scripts/development/offline_evidence'
def load(name):
    path=here/(name+'.py'); m=ModuleType('probe_'+name); m.__file__=str(path)
    exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__); return m
p=load('replay_provenance'); reader=load('worker'); observation={}
'''+body
        return subprocess.run([str(ROOT/'.venv/bin/python'), '-I', '-B', '-c', program, str(root)],
                              capture_output=True, text=True, timeout=30)

    def test_relocated_admitted_package_resolves_without_ambient_source_fallback(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); self.stage(root)
            process = self.probe(root, '''before=list(sys.meta_path)
with p.checked_product_imports(root,reader,observation):
    import forecast_trust_core.canonical as c
    assert c.canonical_json({'a':1}) == b'{"a":1}'
    assert Path(c.__file__) == root/'src/forecast_trust_core/canonical.py'
assert sys.meta_path == before
print(json.dumps({'origin':str(Path(c.__file__).relative_to(root)), 'scope':observation['scope']}))
''')
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)['origin'], 'src/forecast_trust_core/canonical.py')

    def test_namespace_selection_does_not_admit_unknown_or_nonproduct_siblings(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); self.stage(root)
            (root/'src/fp_unregistered_sibling_probe.py').write_text('raise RuntimeError("SIBLING_EXECUTED")')
            (root/'src/forecast_trust_core/undeclared_probe.py').write_text('raise RuntimeError("UNDECLARED_EXECUTED")')
            process = self.probe(root, '''import importlib.util
before=list(sys.meta_path)
try:
    with p.checked_product_imports(root,reader,observation):
        import forecast_trust_core.canonical
        try:
            import forecast_trust_core.undeclared_probe
        except reader.OfflineFailure as e:
            assert e.code=='UNREGISTERED_PRODUCT_CODE'
        else: raise AssertionError('undeclared product admitted')
        assert importlib.util.find_spec('fp_unregistered_sibling_probe') is None
        raise RuntimeError('OWNED_PROBE_EXIT')
except RuntimeError as e:
    assert str(e)=='OWNED_PROBE_EXIT'
assert sys.meta_path == before
try:
    with p.checked_product_imports(root,reader,{}): pass
except reader.OfflineFailure as e: assert e.code=='PRELOADED_PRODUCT_CODE_UNVERIFIED'
else: raise AssertionError('preloaded product accepted')
print('bounded namespace and restoration observed')
''')
        self.assertEqual(process.returncode, 0, process.stderr)

    def test_finite_replay_moves_with_its_exact_inputs_and_retains_omission_and_substitution(self):
        body = '''main=load('mainline_worker'); snapshot={}
with p.checked_product_imports(root,reader,observation):
    result=main.finite_module(root/Path('''+repr(str(RUN))+'''),snapshot)
print(json.dumps(result))
'''
        with tempfile.TemporaryDirectory() as name:
            root = Path(name); self.stage(root)
            process = self.probe(root, body)
            self.assertEqual(process.returncode, 0, process.stderr)
            positive = json.loads(process.stdout)
            self.assertEqual(positive['status'], 'OBSERVED')
            self.assertTrue(positive['result']['finite_report_set_match'])
            (root/RUN/'inputs/output-0.raw').unlink()
            changed = root/RUN/'inputs/report-3.raw'
            changed.write_bytes(changed.read_bytes()+b' ')
            process = self.probe(root, body)
            self.assertEqual(process.returncode, 0, process.stderr)
            negative = json.loads(process.stdout)
            self.assertEqual(negative['status'], 'REJECTED')
            self.assertIn('MISSING', [x['status'] for x in negative['findings']])
            self.assertIn('REJECTED', [x['status'] for x in negative['findings']])


if __name__ == '__main__':
    unittest.main()
