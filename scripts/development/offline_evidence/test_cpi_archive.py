"""Finite archive headlines: identity, measurement, and two-carrier failure propagation."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKAGE = ROOT/'docs/development/mainline-execution-2026-10-25-cpi-archive-carrier-rev-001'
PDF = PACKAGE/'raw/cpi_20260714.fraser.pdf'
COPY = ROOT/'docs/development/mainline-execution-2026-10-09-rev-001/bls-cpi-pasted-observation/public-rendered-copy.txt'


def load(name):
    spec = importlib.util.spec_from_file_location('archive_test_'+name, HERE/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CPIArchiveTests(unittest.TestCase):
    def command(self, *args, human=False):
        proc = subprocess.run([str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'),
                               *args, *([] if human else ['--json'])],
                              capture_output=True, text=True, timeout=50)
        self.assertTrue(proc.stdout.strip(), proc.stderr)
        return proc, proc.stdout if human else json.loads(proc.stdout)

    def pair(self):
        return ({'id': 'cpi-june-2026-copy', 'status': 'OBSERVED',
                 'observations': load('cpi_text').observe_cpi_copy(COPY.read_bytes())},
                {'id': 'cpi-june-2026-archive', 'status': 'OBSERVED',
                 'observations': load('cpi_pdf').observe_archive_pdf(PDF.read_bytes())})

    def test_pdf_first_page_scope_is_explicit_and_measures_are_separate(self):
        data = load('cpi_pdf').observe_archive_pdf(PDF.read_bytes())
        self.assertEqual((data['display_value'], data['unadjusted_yearly_change']), ('-0.4', '3.5'))
        self.assertEqual(data['reference_month'], '2026-06')
        self.assertEqual(data['release_id'], 'USDL-26-1191')
        self.assertEqual(data['publication_date_declaration'], '2026-07-14')
        self.assertEqual(data['pages'], 38)
        self.assertEqual(data['page_1_based'], 1)
        self.assertEqual(data['evidence_class'], 'FRASER_ARCHIVE_HOSTED_BLS_PDF_HEADLINE_DECLARATIONS_ONLY')
        self.assertFalse(data['original_publisher_bytes'])
        self.assertEqual(data['table_A_machine_verification'], 'NOT_CHECKED_RASTER_TABLE')
        for key in ('historical_first_release', 'authenticated_availability', 'full_document_completeness'):
            self.assertEqual(data[key], 'NOT_ESTABLISHED')

    def test_parser_rejects_wrong_edition_ambiguity_and_adjustment(self):
        text = (PACKAGE/'inspection/page-1.txt').read_text()
        parser = load('cpi_pdf').parse_archive_first_page
        self.assertEqual(parser(text)['display_value'], '-0.4')
        for changed in (text.replace('JUNE 2026', 'MAY 2026'),
                        text.replace('July 14, 2026', 'July 15, 2026'),
                        text.replace('USDL-26-1191', 'USDL-26-0000'),
                        text+text,
                        text.replace('seasonally \nadjusted basis', 'unadjusted basis'),
                        text.replace('before seasonal adjustment', 'after seasonal adjustment')):
            with self.subTest(changed=changed[:90]):
                self.assertNotEqual(changed, text)
                with self.assertRaises(ValueError):
                    parser(changed)

    def test_pdf_entry_rejects_changed_identity(self):
        consumer = load('cpi_pdf').observe_archive_pdf
        for changed in (PDF.read_bytes()+b'\n', COPY.read_bytes(), b'%PDF-fake'):
            with self.assertRaises(ValueError):
                consumer(changed)

    def test_shared_declarations_compare_without_upgrading_either_source(self):
        copy, archive = self.pair()
        originals = deepcopy((copy, archive))
        result = load('cli').compare_cpi_carriers(copy, archive)
        self.assertEqual(result['status'], 'OBSERVED')
        self.assertEqual(result['source_independence'], 'NOT_ESTABLISHED')
        self.assertEqual(result['coverage'], 'SHARED_FIRST_PAGE_DECLARATIONS_ONLY_NOT_FULL_TABLES')
        self.assertEqual((copy, archive), originals)
        for field, value in (('display_value', '0.4'), ('reference_month', '2026-05'),
                             ('unadjusted_yearly_change', '-0.4'), ('display_value', -0.4)):
            changed = deepcopy(archive)
            changed['observations'][field] = value
            self.assertEqual(load('cli').compare_cpi_carriers(copy, changed)['status'], 'REJECTED')

    def test_missing_and_rejection_coexist(self):
        result = load('cli').compare_cpi_carriers(
            {'id': 'cpi-june-2026-copy', 'status': 'MISSING', 'error': 'MISSING_INPUT'},
            {'id': 'cpi-june-2026-archive', 'status': 'REJECTED', 'error': 'INPUT_IDENTITY_MISMATCH'})
        self.assertEqual(result['status'], 'REJECTED')
        self.assertEqual({f['status'] for f in result['findings']}, {'MISSING', 'REJECTED'})

    def test_new_process_replay_and_mainline_keep_real_gaps(self):
        first, report = self.command('verify', 'cpi-june-2026-archive')
        second, replay = self.command('verify', 'cpi-june-2026-archive')
        self.assertEqual((first.returncode, second.returncode), (0, 0))
        self.assertEqual(report, replay)
        self.assertEqual(report['cases'][0]['status'], 'OBSERVED')
        process, mainline = self.command('mainline')
        rows = {row['id']: row for row in mainline['modules']}
        self.assertEqual(len(rows), 14)
        cpi = rows['inflation-data']
        self.assertEqual(cpi['status'], 'OBSERVED')
        self.assertEqual(cpi['archive_carrier']['status'], 'OBSERVED')
        self.assertEqual(cpi['result']['observations']['evidence_class'],
                         'USER_SUPPLIED_RENDERED_TEXT_SOURCE_DECLARATION_ONLY')
        self.assertEqual(rows['time-and-durability']['status'], 'MISSING')
        self.assertEqual(rows['final-readiness']['status'], 'MISSING')
        self.assertEqual(mainline['real_admission'], 'NOT_READY')
        self.assertEqual(process.returncode, 1)

    def test_explicit_roots_do_not_fall_back_and_both_children_run(self):
        for supplied in ('copy', 'archive', 'bad-archive', 'symlink'):
            with self.subTest(supplied=supplied), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                if supplied == 'copy':
                    shutil.copyfile(COPY, root/'cpi-june2026-copy.txt')
                elif supplied == 'archive':
                    shutil.copyfile(PDF, root/'cpi-june2026-fraser.pdf')
                elif supplied == 'bad-archive':
                    (root/'cpi-june2026-fraser.pdf').write_bytes(PDF.read_bytes()+b'\n')
                else:
                    (root/'cpi-june2026-fraser.pdf').symlink_to(PDF)
                process, report = self.command('mainline', '--inputs', directory)
                row = next(r for r in report['modules'] if r['id'] == 'inflation-data')
                self.assertEqual(row['result']['status'], 'OBSERVED' if supplied == 'copy' else 'MISSING')
                expected = 'MISSING' if supplied == 'copy' else 'OBSERVED' if supplied == 'archive' else 'REJECTED'
                self.assertEqual(row['archive_carrier']['status'], expected)
                self.assertEqual(row['status'], 'REJECTED' if expected == 'REJECTED' else 'MISSING')
                self.assertEqual(process.returncode, 2 if expected == 'REJECTED' else 1)
                if expected == 'REJECTED':
                    self.assertEqual({f['status'] for f in row['carrier_comparison']['findings']},
                                     {'MISSING', 'REJECTED'})

    def test_human_output_names_archive_and_narrow_scope(self):
        proc, output = self.command('verify', 'cpi-june-2026-archive', human=True)
        self.assertEqual(proc.returncode, 0)
        self.assertIn('CPI-U季调月变化=-0.4%', output)
        self.assertIn('FRASER', output)
        self.assertIn('第一页', output)
        self.assertNotIn('失业率=', output)


if __name__ == '__main__':
    unittest.main()
