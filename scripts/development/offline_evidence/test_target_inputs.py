"""Selected target observations retain their source class and measurement units."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CPI = ROOT/'docs/development/mainline-execution-2026-10-09-rev-001/bls-cpi-pasted-observation/public-rendered-copy.txt'


class TargetInputTests(unittest.TestCase):
    def command(self, *args):
        process = subprocess.run([str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'),
                                  *args, '--json'], capture_output=True, text=True, timeout=45)
        self.assertTrue(process.stdout.strip(), process.stderr)
        return process, json.loads(process.stdout)

    def consumer(self):
        path = HERE/'cpi_text.py'
        self.assertTrue(path.is_file(), 'CPI fixed-text consumer not implemented')
        spec = importlib.util.spec_from_file_location('cpi_text_test', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_cpi_extracts_negative_sa_mom_and_keeps_yoy_separate(self):
        process, report = self.command('verify', 'cpi-june-2026-copy')
        self.assertEqual(process.returncode, 0)
        case = report['cases'][0]
        self.assertEqual(case['status'], 'OBSERVED')
        value = case['observations']
        self.assertEqual(value['display_value'], '-0.4')
        self.assertEqual(value['reference_month'], '2026-06')
        self.assertEqual(value['measure'], 'PERCENT_CHANGE_FROM_PRECEDING_MONTH')
        self.assertEqual(value['adjustment'], 'SEASONALLY_ADJUSTED')
        self.assertEqual(value['unadjusted_yearly_change'], '3.5')
        self.assertEqual(value['evidence_class'], 'USER_SUPPLIED_RENDERED_TEXT_SOURCE_DECLARATION_ONLY')
        self.assertEqual(value['authenticated_availability'], 'NOT_ESTABLISHED')
        self.assertFalse(value['original_publisher_bytes'])
        self.assertEqual(report['real_admission'], 'NOT_READY')
        human = subprocess.run([str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'),
                                'verify', 'cpi-june-2026-copy'], capture_output=True, text=True, timeout=45)
        self.assertEqual(human.returncode, 0)
        self.assertIn('CPI-U季调月变化=-0.4%', human.stdout)
        self.assertIn('仅用户正文副本', human.stdout)
        self.assertNotIn('失业率=', human.stdout)

    def test_cpi_parser_rejects_changed_sign_columns_and_duplicate_target_row(self):
        module = self.consumer()
        text = CPI.read_text()
        self.assertEqual(module.parse_retained_text(text)['display_value'], '-0.4')
        for changed in [text.replace('decreased 0.4 percent', 'increased 0.4 percent', 1),
                        text.replace('Seasonally adjusted changes from preceding month',
                                     'Unadjusted changes from preceding month', 1),
                        text.replace('0.3\t0.2\t0.3\t0.9\t0.6\t0.5\t-0.4\t3.5',
                                     '0.3\t0.2\t0.3\t0.9\t0.6\t0.5\t3.5\t-0.4', 1),
                        text.replace('All items\n\n0.3', 'All items\n\n0.3\nAll items\n\n0.3', 1)]:
            with self.subTest(change=changed != text):
                self.assertNotEqual(changed, text)
                with self.assertRaises(ValueError):
                    module.parse_retained_text(changed)

    def test_cpi_public_entry_rejects_edited_bytes_even_if_measurement_same(self):
        module = self.consumer()
        with self.assertRaises(ValueError):
            module.observe_cpi_copy(CPI.read_bytes()+b'\n')

    def test_mainline_includes_cpi_and_both_existing_u3_editions(self):
        process, report = self.command('mainline')
        modules = {row['id']: row for row in report['modules']}
        self.assertEqual(modules.get('inflation-data', {}).get('status'), 'OBSERVED')
        self.assertEqual(modules['inflation-data']['result']['observations']['display_value'], '-0.4')
        self.assertEqual(modules.get('unemployment-july', {}).get('status'), 'OBSERVED')
        november = modules.get('unemployment-november', {})
        self.assertEqual(november.get('status'), 'OBSERVED')
        self.assertIsNone(november['result']['observations']['prior_value'])
        self.assertEqual(modules['economic-data']['status'], 'OBSERVED')
        self.assertEqual(modules['final-readiness']['status'], 'MISSING')
        self.assertEqual(process.returncode, 1)

    def test_explicit_empty_input_directory_never_reuses_cpi_or_u3(self):
        with tempfile.TemporaryDirectory() as directory:
            process, report = self.command('mainline', '--inputs', directory)
        modules = {row['id']: row for row in report['modules']}
        for identity in ['inflation-data', 'unemployment-july', 'unemployment-november']:
            self.assertEqual(modules.get(identity, {}).get('status'), 'MISSING')
        self.assertEqual(modules['finite-reports']['status'], 'OBSERVED')
        self.assertEqual(process.returncode, 1)


if __name__ == '__main__':
    unittest.main()
