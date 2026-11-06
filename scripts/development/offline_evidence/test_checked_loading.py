"""A valid timestamp cache must not choose finite replay implementation code."""
import importlib.machinery
import importlib.util
import json
import marshal
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
from types import ModuleType
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def api():
    module = ModuleType('checked_loading_test_api')
    module.__file__ = str(HERE/'replay_provenance.py')
    exec(compile((HERE/'replay_provenance.py').read_bytes(), module.__file__, 'exec'), module.__dict__)
    reader = ModuleType('checked_loading_reader')
    reader.__file__ = str(HERE/'worker.py')
    exec(compile((HERE/'worker.py').read_bytes(), reader.__file__, 'exec'), reader.__dict__)
    return module, reader


class CheckedLoadingTests(unittest.TestCase):
    def setup_api(self, directory):
        module, reader = api()
        self.assertTrue(callable(getattr(module, 'checked_product_imports', None)),
                        'verified source snapshot loader not implemented')
        root = Path(directory)
        for row in module.FINITE_PRODUCT_SOURCES:
            target = root/row['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/row['path'], target)
        return module, reader, root

    def test_timestamp_valid_poisoned_pyc_is_real_and_checked_loading_ignores_it(self):
        with tempfile.TemporaryDirectory() as directory:
            module, reader, root = self.setup_api(directory)
            source = root/'src/forecast_trust_core/canonical.py'
            cache = Path(importlib.util.cache_from_source(str(source)))
            cache.parent.mkdir()
            poison = compile('raise RuntimeError("UNREGISTERED_CACHE_EXECUTED")', str(source), 'exec')
            info = source.stat()
            cache.write_bytes(importlib.util.MAGIC_NUMBER+struct.pack('<III', 0, int(info.st_mtime), info.st_size)
                              +marshal.dumps(poison))
            loader = importlib.machinery.SourceFileLoader('canonical_cache_probe', str(source))
            with self.assertRaisesRegex(RuntimeError, 'UNREGISTERED_CACHE_EXECUTED'):
                exec(loader.get_code('canonical_cache_probe'), {})
            observation = {}
            original = importlib.machinery.SourceFileLoader.get_code
            with module.checked_product_imports(root, reader, observation):
                namespace = {}
                exec(loader.get_code('canonical_cache_probe'), namespace)
                self.assertTrue(callable(namespace['canonical_json']))
            self.assertIs(importlib.machinery.SourceFileLoader.get_code, original)
            self.assertEqual(observation['executed_selected_modules'], 1)
            self.assertEqual(observation['source_snapshot_count'], 21)
            self.assertEqual(observation['complete_runtime_closure'], 'NOT_ESTABLISHED')

    def test_replaced_source_is_rejected_before_import_or_cache_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            module, reader, root = self.setup_api(directory)
            source = root/module.FINITE_PRODUCT_SOURCES[0]['path']
            source.write_bytes(source.read_bytes()+b'\n# replacement\n')
            with self.assertRaises(reader.OfflineFailure) as caught:
                with module.checked_product_imports(root, reader, {}):
                    self.fail('changed source must not reach execution')
            self.assertEqual(caught.exception.code, 'INPUT_IDENTITY_MISMATCH')

    def test_missing_and_changed_sources_both_survive_code_admission(self):
        with tempfile.TemporaryDirectory() as directory:
            module, reader, root = self.setup_api(directory)
            (root/module.FINITE_PRODUCT_SOURCES[0]['path']).unlink()
            source = root/module.FINITE_PRODUCT_SOURCES[1]['path']
            source.write_bytes(source.read_bytes()+b'\n# replacement\n')
            with self.assertRaises(reader.OfflineFailure) as caught:
                with module.checked_product_imports(root, reader, {}):
                    self.fail('no partial unchecked load')
            self.assertEqual(caught.exception.status, 'REJECTED')
            self.assertEqual({row['error'] for row in caught.exception.findings},
                             {'MISSING_INPUT', 'INPUT_IDENTITY_MISMATCH'})

    def test_preloaded_product_and_unregistered_code_are_rejected_and_hook_restored(self):
        with tempfile.TemporaryDirectory() as directory:
            module, reader, root = self.setup_api(directory)
            original = importlib.machinery.SourceFileLoader.get_code
            name = 'forecast_trust_core.UNDECLARED_TEST_CACHE'
            sys.modules[name] = ModuleType(name)
            try:
                with self.assertRaises(reader.OfflineFailure) as caught:
                    with module.checked_product_imports(root, reader, {}):
                        self.fail('preloaded product must not be trusted')
                self.assertEqual(caught.exception.code, 'PRELOADED_PRODUCT_CODE_UNVERIFIED')
            finally:
                del sys.modules[name]
            with self.assertRaises(reader.OfflineFailure) as caught:
                with module.checked_product_imports(root, reader, {}):
                    foreign = root/'src/forecast_trust_core/not_declared.py'
                    exec(compile('pass', str(foreign), 'exec'), {})
            self.assertEqual(caught.exception.code, 'UNREGISTERED_PRODUCT_CODE')
            self.assertIs(importlib.machinery.SourceFileLoader.get_code, original)
            # A valid filename does not authorize different code under that name.
            with self.assertRaises(reader.OfflineFailure) as caught:
                with module.checked_product_imports(root, reader, {}):
                    source = root/'src/forecast_trust_core/canonical.py'
                    exec(compile('pass', str(source), 'exec'), {})
            self.assertEqual(caught.exception.code, 'SELECTED_PRODUCT_CODE_MISMATCH')

    def test_mainline_records_selected_current_code_and_keeps_real_gaps(self):
        command = [str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'), 'mainline', '--json']
        process = subprocess.run(command, capture_output=True, text=True, timeout=45)
        report = json.loads(process.stdout)
        modules = {row['id']: row for row in report['modules']}
        loading = modules['finite-reports'].get('selected_code_loading', {})
        self.assertEqual(loading.get('executed_selected_modules'), 21, loading)
        self.assertEqual(loading['source_snapshot_count'], 21)
        self.assertEqual(modules['execution-trace']['selected_code_loading'], loading)
        self.assertEqual(loading['scope'], 'SELECTED_PRODUCT_TOP_LEVEL_PYTHON_CODE_ONLY')
        self.assertEqual(loading['complete_runtime_closure'], 'NOT_ESTABLISHED')
        self.assertEqual(modules['initial-authority']['status'], 'MISSING')
        self.assertEqual(report['real_admission'], 'NOT_READY')
        self.assertFalse(report['prospective_eligible'])
        self.assertEqual(process.returncode, 1)

    def test_code_rejection_still_allows_independent_public_data_branch(self):
        with tempfile.TemporaryDirectory() as directory:
            module, reader, root = self.setup_api(directory)
            target = root/'scripts/development/offline_evidence'
            target.mkdir(parents=True)
            for name in ('cli.py', 'worker.py', 'mainline_worker.py', 'replay_provenance.py',
                         'catalog.json', 'cpi_text.py', 'cpi_pdf.py', 'cpi_table1.py', 'ots_body.py', 'core_sample.py',
                         'roughtime_build.py', 'roughtime_event.py', 'roughtime_event_inputs.json',
                         'strong_event.py', 'strong_event_inputs.json',
                         'strong_same_run.py', 'strong_same_run_inputs.json'):
                shutil.copyfile(HERE/name, target/name)
            cases = json.loads((HERE/'catalog.json').read_bytes())
            inputs = root/'public-inputs'
            inputs.mkdir()
            for name in ('cpi-june-2026-copy','cpi-june-2026-archive','cpi-june-2026-table1'):
                for row in cases[name]['inputs']:
                    shutil.copyfile(ROOT/row['path'], inputs/row['alias'])
            source = root/module.FINITE_PRODUCT_SOURCES[0]['path']
            source.write_bytes(source.read_bytes()+b'\n# replaced\n')
            process = subprocess.run([str(ROOT/'.venv/bin/python'), '-I', '-B', str(target/'cli.py'),
                                      'mainline', '--inputs', str(inputs), '--json'],
                                     capture_output=True, text=True, timeout=45)
        report = json.loads(process.stdout)
        modules = {row['id']: row for row in report['modules']}
        self.assertEqual(process.returncode, 2)
        self.assertEqual(modules['module-consumption']['status'], 'REJECTED')
        self.assertEqual(modules['module-consumption']['native_authority_diagnostics'],
                         'NOT_EXECUTED_AFTER_CODE_REJECTION')
        self.assertEqual(modules['inflation-data']['status'], 'OBSERVED')
        self.assertEqual(report['real_admission'], 'NOT_READY')


if __name__ == '__main__':
    unittest.main()
