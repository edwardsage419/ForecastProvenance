"""Retained run provenance must consume actual artifacts and retain its limits."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import ModuleType
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
TRACE = ROOT/'docs/development/mainline-execution-2026-10-18-observed-development-run-rev-001'
NAMES = {'inputs': 'INPUTS_ATTEMPT2.json', 'pre': 'PRE_RUN_ATTEMPT2.json',
         'run': 'RUN_OBSERVATION_ATTEMPT2.json', 'loaded': 'raw-attempt2/loaded-code.json',
         'package': 'pre-attempt2/material-package.json', 'lock': 'pre-attempt2/material-lock.json',
         'runtime': 'pre-attempt2/runtime.json', 'sources': 'pre-attempt2/material-sources.json'}


def documents():
    raw = {key: (TRACE/name).read_bytes() for key, name in NAMES.items()}
    data = {key: json.loads(value) for key, value in raw.items()}
    data['_raw'] = raw
    data['_shared'] = {
        'base_records': {'r4t': (TRACE/'OBSERVED_R4T.raw').read_bytes(), 'runtime': raw['runtime']},
        'pre_definition': (TRACE/'pre-attempt2/definition.json').read_bytes(),
        'raw_artifacts': {'DEV.D177.STDOUT': (TRACE/'raw-attempt2/stdout.raw').read_bytes(),
                          'DEV.D177.STDERR': (TRACE/'raw-attempt2/stderr.raw').read_bytes()}}
    return data


def origins(data, root):
    by_path = {row['path']: row for row in data['loaded']['executed_sources']}
    return {name: str(root/'src'/by_path[path]['member'])
            for name, path in data['loaded']['product_origins'].items()}


class ProvenanceTests(unittest.TestCase):
    def api(self):
        path = HERE/'replay_provenance.py'
        self.assertTrue(path.is_file(), 'retained source/package consumer not implemented')
        module = ModuleType('provenance_under_test')
        module.__file__ = str(path)
        exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
        reader = ModuleType('passive_provenance_test_reader')
        reader.__file__ = str(HERE/'worker.py')
        exec(compile((HERE/'worker.py').read_bytes(), reader.__file__, 'exec'), reader.__dict__)
        return module, reader

    def consume(self, data, root=ROOT, current=None):
        api, reader = self.api()
        return api.bind_retained_sources(data, root, reader,
                                        origins(data, root) if current is None else current, data['_shared'])

    def copy_artifacts(self, root, data):
        repo = [row['path'] for row in data['loaded']['executed_sources']
                if row['kind'] == 'PREDECLARED_REPOSITORY_SOURCE']
        paths = set(repo + [row['path'] for row in data['lock']['wheels']])
        paths.update(str(Path(path).relative_to(root)) for path in origins(data, root).values())
        for path in paths:
            target = root/path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/path, target)

    def test_retained_files_join_to_wheels_and_current_source_without_claiming_loaded_bytecode(self):
        result = self.consume(documents())
        self.assertEqual(result['status'], 'OBSERVED', result)
        self.assertEqual(result['checked_repository_sources'], 22)
        self.assertEqual(result['checked_wheel_members'], 60)
        self.assertEqual(result['checked_wheels'], 7)
        self.assertEqual(result['checked_current_product_sources'], 21)
        self.assertEqual(result['actual_execution_truth'], 'NOT_VERIFIED')
        self.assertEqual(result['current_loaded_bytecode_identity'], 'NOT_ESTABLISHED')
        self.assertEqual(result['complete_runtime_closure'], 'NOT_ESTABLISHED')

    def test_loaded_omission_wrong_runtime_and_precommit_cannot_hide_behind_equal_hash_lists(self):
        for mutate, code in [
            (lambda d: d['loaded']['executed_sources'].pop(), 'LOADED_SOURCE_SET_MISMATCH'),
            (lambda d: d['pre'].update(selected_source_sha256='0'*64), 'PRE_INPUT_IDENTITY_MISMATCH'),
            (lambda d: d['runtime']['execution_engine'].update(executable_sha256='0'*64),
             'RUNTIME_EXECUTABLE_BINDING_MISMATCH'),
            (lambda d: d['loaded']['executed_sources'][0].update(sha256='0'*64),
             'REPOSITORY_PREDECLARATION_MISMATCH')]:
            data = documents()
            mutate(data)
            with self.subTest(code=code):
                result = self.consume(data)
                self.assertEqual(result['status'], 'REJECTED', result)
                self.assertIn(code, [row['error'] for row in result['findings']])

    def test_missing_repository_file_and_changed_wheel_are_both_reported(self):
        data = documents()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_artifacts(root, data)
            missing = next(row for row in data['loaded']['executed_sources']
                           if row['kind'] == 'PREDECLARED_REPOSITORY_SOURCE')['path']
            (root/missing).unlink()
            wheel = root/data['lock']['wheels'][0]['path']
            wheel.write_bytes(wheel.read_bytes()+b'changed')
            result = self.consume(data, root)
        self.assertEqual(result['status'], 'REJECTED', result)
        codes = {row['error'] for row in result['findings']}
        self.assertIn('MISSING_INPUT', codes)
        self.assertIn('INPUT_IDENTITY_MISMATCH', codes)

    def test_current_source_substitution_and_foreign_origin_are_rejected(self):
        data = documents()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.copy_artifacts(root, data)
            current = origins(data, root)
            source = Path(next(iter(current.values())))
            source.write_bytes(source.read_bytes()+b'\n# replaced\n')
            result = self.consume(data, root, current)
            self.assertEqual(result['status'], 'REJECTED', result)
            self.assertIn('CURRENT_PRODUCT_SOURCE_CHANGED', [r['error'] for r in result['findings']])
        current = origins(data, ROOT)
        current[next(iter(current))] = '/not-authorized/do-not-read'
        result = self.consume(data, current=current)
        self.assertIn('CURRENT_PRODUCT_ORIGIN_UNSUPPORTED', [r['error'] for r in result['findings']])

    def test_runtime_observation_must_bind_argv_definition_and_output_bytes(self):
        for field in ('argv', 'pre_definition_raw_sha256', 'stdout'):
            data = documents()
            data['run'][field] = [] if field == 'argv' else 'replaced'
            with self.subTest(field=field):
                result = self.consume(data)
                self.assertEqual(result['status'], 'REJECTED', result)
                self.assertIn('RUN_RECORD_BINDING_MISMATCH', [r['error'] for r in result['findings']])

    def test_material_references_and_shared_runtime_cannot_be_substituted(self):
        for field in ('package_artifact_ref', 'dependency_lock_ref', 'runtime_profile_ref', 'source_file_manifest_ref'):
            data = documents()
            report = json.loads(data['_shared']['base_records']['r4t'])
            report[field]['content_sha256'] = '0'*64
            data['_shared']['base_records']['r4t'] = json.dumps(report).encode()
            with self.subTest(field=field):
                result = self.consume(data)
                self.assertEqual(result['status'], 'REJECTED', result)
                self.assertIn('R4T_MATERIAL_BINDING_MISMATCH', [r['error'] for r in result['findings']])
        data = documents()
        data['_shared']['base_records']['runtime'] = data['_raw']['runtime']+b'\n'
        result = self.consume(data)
        self.assertIn('SHARED_RUNTIME_RAW_MISMATCH', [r['error'] for r in result['findings']])

    def test_mainline_consumes_provenance_and_explicit_directory_never_falls_back(self):
        command = [str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'), 'mainline', '--json']
        process = subprocess.run(command, capture_output=True, text=True, timeout=45)
        report = json.loads(process.stdout)
        trace = next(row for row in report['modules'] if row['id'] == 'execution-trace')
        binding = trace.get('source_package_binding', {})
        self.assertEqual(binding.get('status'), 'OBSERVED', binding)
        self.assertEqual(report['real_admission'], 'NOT_READY')
        self.assertEqual(process.returncode, 1)
        with tempfile.TemporaryDirectory() as directory:
            for name in ['EVENT_EXPECTED_CORRECTED.json', 'EVENT_RUN_OBSERVATION.json',
                         'pre-attempt2/method-map.json', 'raw-attempt2/events.jsonl']:
                target = Path(directory)/name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(TRACE/name, target)
            process = subprocess.run(command+['--execution-inputs', directory], capture_output=True,
                                     text=True, timeout=45)
        report = json.loads(process.stdout)
        modules = {row['id']: row for row in report['modules']}
        self.assertEqual(modules['execution-trace']['status'], 'MISSING')
        self.assertEqual(modules['execution-trace']['source_package_binding']['status'], 'MISSING')
        self.assertEqual(modules['finite-reports']['status'], 'OBSERVED')
        self.assertEqual(modules['economic-data']['status'], 'OBSERVED')


if __name__ == '__main__':
    unittest.main()
