"""Actual fixed public build artifacts; no Go, native verifier or test keys."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BUILD = ROOT/'docs/development/owner-roughtime-build-results.K0fixS'
NAMES = ('verifier-build-profile.json', 'dependency-lock.json', 'fixture-report.json', 'fpp-roughtime-strict')


def load():
    spec = importlib.util.spec_from_file_location('build_test_consumer', HERE/'roughtime_build.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def copy_build(directory):
    for name in NAMES:
        shutil.copyfile(BUILD/name, Path(directory)/name)


class RoughtimeBuildTests(unittest.TestCase):
    def consume(self, directory=BUILD, **kwargs):
        self.assertTrue((HERE/'roughtime_build.py').exists(), 'actual build consumer is absent')
        return load().consume(directory, **kwargs)

    def test_actual_artifacts_bound_without_execution_or_authority_promotion(self):
        with patch('subprocess.run', side_effect=AssertionError('native execution forbidden')):
            result = self.consume()
        self.assertEqual(result['status'], 'OBSERVED')
        self.assertTrue(result['artifact_binding_match'])
        self.assertEqual(result['fixture_pass_rows'], 18)
        self.assertEqual(result['required_fixture_names'], 15)
        self.assertEqual(result['profile_sha256'], '7d6bd040361534a0ef04348c9cb095e6ea134243a4ad0b6bc701c9c2a08f427b')
        self.assertFalse(result['binary_executed'])
        for field in ('live_compatibility', 'provider_qualification', 'authenticated_time', 'independent_software_trust'):
            self.assertEqual(result[field], 'NOT_ESTABLISHED')
        self.assertFalse(result['prospective_eligible'])
        self.assertEqual(result['protocol_state_change'], 'NONE')

    def test_each_omission_is_missing_without_default_fallback(self):
        for name in NAMES:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                copy_build(directory)
                (Path(directory)/name).unlink()
                result = self.consume(directory)
                self.assertEqual(result['status'], 'MISSING')
                self.assertFalse(result['artifact_binding_match'])
                self.assertIn(name, [f['item'] for f in result['findings']])

    def test_each_same_size_substitution_rejects_before_json_validation(self):
        for name in NAMES:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                copy_build(directory)
                path = Path(directory)/name
                raw = path.read_bytes()
                path.write_bytes(bytes([raw[0] ^ 1])+raw[1:])
                result = self.consume(directory)
                self.assertEqual(result['status'], 'REJECTED')
                self.assertIn('INPUT_IDENTITY_MISMATCH', [f['error'] for f in result['findings']])
                self.assertFalse(result['artifact_binding_match'])

    def test_missing_and_hard_failure_are_both_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            copy_build(directory)
            (Path(directory)/NAMES[0]).unlink()
            (Path(directory)/NAMES[3]).write_bytes(b'wrong')
            result = self.consume(directory)
        self.assertEqual(result['status'], 'REJECTED')
        self.assertEqual({f['error'] for f in result['findings']}, {'MISSING_INPUT', 'INPUT_IDENTITY_MISMATCH'})

    def test_symlink_artifact_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            copy_build(directory)
            file = Path(directory)/NAMES[0]
            file.unlink(); file.symlink_to(BUILD/NAMES[0])
            result = self.consume(directory)
        self.assertEqual(result['status'], 'REJECTED')
        self.assertIn('UNSAFE_PATH', [f['error'] for f in result['findings']])

    def test_nonexistent_directory_is_missing_and_dangling_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory)/'not-created'
            result = self.consume(missing)
            self.assertEqual(result['status'], 'MISSING')
            self.assertEqual(len(result['findings']), 4)
            alias = Path(directory)/'dangling'
            alias.symlink_to(missing, target_is_directory=True)
            self.assertEqual(self.consume(alias)['status'], 'REJECTED')

    def test_missing_and_changed_validator_sources_are_both_retained_without_loading(self):
        with tempfile.TemporaryDirectory() as directory:
            result = self.consume(source_root=Path(directory))
            self.assertEqual(result['status'], 'MISSING')
            self.assertEqual(len(result['findings']), 4)
            file = Path(directory)/'src/forecast_trust_core/canonical.py'
            file.parent.mkdir(parents=True); file.write_bytes(b'raise AssertionError("do not execute")')
            result = self.consume(source_root=Path(directory))
        self.assertEqual(result['status'], 'REJECTED')
        self.assertEqual(len(result['findings']), 4)
        self.assertFalse(result['artifact_binding_match'])

    def test_same_artifacts_in_new_directory_replay_identically(self):
        with tempfile.TemporaryDirectory() as directory:
            copy_build(directory)
            self.assertEqual(self.consume(directory), self.consume())

    def test_cli_default_consumes_child_and_keeps_parent_missing(self):
        command = [str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'), 'mainline', '--json']
        process = subprocess.run(command, capture_output=True, text=True, timeout=45)
        report = json.loads(process.stdout)
        row = next(r for r in report['modules'] if r['id']=='time-and-durability')
        self.assertIn('roughtime_verifier_build', row)
        self.assertEqual(row['roughtime_verifier_build']['status'], 'OBSERVED')
        self.assertEqual(row['status'], 'MISSING')
        self.assertEqual(process.returncode, 1)
        self.assertEqual(report['real_admission'], 'NOT_READY')
        self.assertEqual(report['protocol_state_change'], 'NONE')

    def test_cli_explicit_missing_and_bad_builds_do_not_silently_reuse_default(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'), 'mainline',
                       '--roughtime-build-inputs', directory, '--json']
            for expected in ('MISSING', 'REJECTED'):
                if expected=='REJECTED':
                    (Path(directory)/NAMES[0]).write_bytes(b'wrong')
                process = subprocess.run(command, capture_output=True, text=True, timeout=45)
                self.assertTrue(process.stdout.strip(), process.stderr)
                report = json.loads(process.stdout)
                rows = {r['id']:r for r in report['modules']}
                self.assertEqual(rows['time-and-durability']['roughtime_verifier_build']['status'], expected)
                self.assertEqual(rows['economic-data']['status'], 'OBSERVED')
                self.assertEqual(rows['time-and-durability']['status'], 'REJECTED' if expected=='REJECTED' else 'MISSING')
                self.assertEqual(process.returncode, 2 if expected=='REJECTED' else 1)


if __name__ == '__main__':
    unittest.main()
