"""Only new offline-entry behavior, using exact safe public inputs and keyless samples."""
import json
from copy import deepcopy
import importlib.util
import marshal
import struct
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import cli
import worker
CASES = json.loads((Path(__file__).resolve().parent/"catalog.json").read_text())

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PYTHON = ROOT / '.venv/bin/python'


def copy_inputs(destination):
    destination = Path(destination)
    for case in CASES.values():
        for row in case['inputs']:
            target = destination / row['alias']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / row['path'], target)


def copy_sources(destination):
    destination = Path(destination)
    for case in CASES.values():
        for row in case['sources']:
            target = destination / row['path']
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / row['path'], target)
    target = destination / 'scripts/development/offline_evidence'
    target.mkdir(parents=True, exist_ok=True)
    for name in ('cli.py', 'worker.py', 'catalog.json'):
        shutil.copyfile(HERE / name, target / name)


def write_cache(source, payload):
    cache = Path(importlib.util.cache_from_source(str(source)))
    cache.parent.mkdir(parents=True, exist_ok=True)
    info = source.stat()
    header = importlib.util.MAGIC_NUMBER+struct.pack('<III', 0, int(info.st_mtime), info.st_size)
    cache.write_bytes(header+marshal.dumps(compile(payload, str(source), 'exec')))


class OfflineEntryTests(unittest.TestCase):
    def observed(self, name, **kwargs):
        result = cli.run_case(name, **kwargs)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['status'], 'OBSERVED', result)
        return result['observations']

    def command(self, *args, script=HERE/'cli.py', cwd=ROOT):
        result = subprocess.run([str(PYTHON), '-I', '-B', str(script), *args], cwd=cwd,
                                capture_output=True, text=True, timeout=45)
        return result

    def json_command(self, *args, **kwargs):
        result = self.command(*args, '--json', **kwargs)
        self.assertTrue(result.stdout.strip(), result.stderr)
        return result, json.loads(result.stdout)

    def test_two_actual_pdf_editions_keep_values_and_missing_october(self):
        july = self.observed('u3-july-2025')
        november = self.observed('u3-november-2025')
        self.assertEqual((july['reference_month'], july['display_value']), ('2025-07', '4.2'))
        self.assertEqual(november['display_value'], '4.6')
        self.assertIsNone(november['prior_value'])
        self.assertEqual(november['authenticated_availability'], 'NOT_ESTABLISHED')

    def test_review_gdp_cache_cannot_override_checked_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)/'repo'
            inputs = Path(tmp)/'inputs'
            copy_sources(repo)
            copy_inputs(inputs)
            source = repo/CASES['gdp-2026-vintages']['sources'][1]['path']
            marker = Path(tmp)/'cache-marker'
            payload = source.read_text() + "\nfrom pathlib import Path\nPath("+repr(str(marker))+").write_text('unregistered cache executed')\n"
            write_cache(source, payload)
            result = cli.run_case('gdp-2026-vintages', input_root=inputs, repository_root=repo)
            self.assertFalse(marker.exists(), result)
            self.assertEqual(result['status'], 'OBSERVED', result)

    def test_review_missing_and_corrupt_inputs_both_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_inputs(tmp)
            root = Path(tmp)
            (root/'binding/vc.json').unlink()
            path = root/'binding/ib.json'
            raw = path.read_bytes()
            path.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
            result = cli.run_case('bindings-demo', input_root=root)
            self.assertEqual(result['status'], 'REJECTED', result)
            self.assertIn('MISSING_INPUT', [x['error'] for x in result['findings']])
            self.assertIn('INPUT_IDENTITY_MISMATCH', [x['error'] for x in result['findings']])

    def test_review_unregistered_catalog_cache_is_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            copy_sources(repo)
            source = repo/'scripts/development/offline_evidence/catalog.py'
            if not source.exists():
                source.write_text('CASES = {}\n')
            marker = repo/'catalog-cache-marker'
            payload = source.read_text()+"\nfrom pathlib import Path\nPath("+repr(str(marker))+").write_text('unregistered cache executed')\n"
            write_cache(source, payload)
            proc, data = self.json_command('list', script=repo/'scripts/development/offline_evidence/cli.py')
            self.assertEqual(proc.returncode, 0)
            self.assertFalse(marker.exists())
            self.assertEqual(len(data['cases']), 12)

    def test_actual_gdp_seven_versions_and_two_bindings(self):
        data = self.observed('gdp-2026-vintages')
        self.assertEqual(len(data['versions']), 7)
        self.assertEqual(len(data['advance_bindings']), 2)
        self.assertEqual([v['canonical_decimal'] for v in data['versions']],
                         ['2', '1.6', '2.1', '2.5', '1.5', '1.5', '2.2'])
        self.assertEqual(data['versions'][0]['raw_lexical'], '2.0')

    def test_actual_calendar_keeps_eight_finite_declarations(self):
        data = self.observed('bea-calendar')
        self.assertEqual(len(data['events']), 8)
        self.assertEqual(data['mandatory_universe'], 'NOT_ESTABLISHED')

    def test_binding_sample_keeps_synthetic_label_and_unresolved(self):
        data = self.observed('bindings-demo')
        self.assertEqual(data['sample_class'], 'KEYLESS_SYNTHETIC_DEVELOPMENT_ONLY')
        self.assertEqual(data['result']['verdict'], 'UNRESOLVED')
        self.assertEqual(data['result']['binding_verdict'], 'LOCAL_CANDIDATE_BINDINGS_VERIFIED')

    def test_report_never_promotes_observations_or_caller_claims(self):
        data = cli.build_report([{'id': 'x', 'status': 'PASS', 'prospective_eligible': True}])
        self.assertIsInstance(data, dict)
        self.assertEqual(data['overall'], 'UNRESOLVED')
        self.assertFalse(data['prospective_eligible'])
        self.assertEqual(data['real_admission'], 'NOT_READY')
        self.assertEqual(data['protocol_state_change'], 'NONE')
        self.assertEqual(data['cases'][0]['status'], 'REJECTED')

    def test_unknown_case_is_rejected_without_spawn(self):
        with patch.object(subprocess, 'run', side_effect=AssertionError('must not spawn')):
            result = cli.run_case('not-supported')
        self.assertIsInstance(result, dict)
        self.assertEqual(result['status'], 'UNSUPPORTED')

    def test_missing_explicit_input_does_not_use_original(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = cli.run_case('u3-july-2025', input_root=Path(tmp))
        self.assertIsInstance(result, dict)
        self.assertEqual(result['status'], 'MISSING')

    def test_same_size_different_pdf_rejected_before_parse(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'u3-july2025.pdf'
            row = CASES['u3-july-2025']['inputs'][0]
            raw = (ROOT/row['path']).read_bytes()
            path.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
            result = cli.run_case('u3-july-2025', input_root=Path(tmp))
        self.assertIsInstance(result, dict)
        self.assertEqual(result['status'], 'REJECTED')
        self.assertEqual(result['error'], 'INPUT_IDENTITY_MISMATCH')

    def test_leaf_symlink_is_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base/'target').write_bytes(b'ordinary dummy data')
            (base/'u3-july2025.pdf').symlink_to(base/'target')
            with patch.object(os, 'open', side_effect=AssertionError('must not open')):
                with self.assertRaises(worker.OfflineFailure):
                    worker.read_fixed(base, 'u3-july2025.pdf', CASES['u3-july-2025']['inputs'][0])

    def test_directory_symlink_is_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base/'other').mkdir()
            (base/'binding').symlink_to(base/'other', target_is_directory=True)
            with patch.object(os, 'open', side_effect=AssertionError('must not open')):
                with self.assertRaises(worker.OfflineFailure):
                    worker.read_fixed(base, 'binding/vc.json', CASES['bindings-demo']['inputs'][1])

    def test_non_regular_input_is_rejected_without_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            os.mkfifo(base/'u3-july2025.pdf')
            with self.assertRaises(worker.OfflineFailure):
                worker.read_fixed(base, 'u3-july2025.pdf', CASES['u3-july-2025']['inputs'][0])

    def test_traversal_is_rejected_before_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(os, 'open', side_effect=AssertionError('must not open')):
                with self.assertRaises(worker.OfflineFailure):
                    worker.read_fixed(Path(tmp), '../other', CASES['u3-july-2025']['inputs'][0])

    def test_missing_runtime_reports_unavailable_without_install(self):
        with patch.object(cli, 'PDF_PYTHON', Path('/nonexistent/fp-runtime')):
            result = cli.run_case('u3-july-2025')
        self.assertIsInstance(result, dict)
        self.assertEqual(result['status'], 'UNAVAILABLE')

    def test_worker_policy_rejects_network_and_child_process_events(self):
        for event in ('socket.connect', 'socket.sendto', 'socket.getaddrinfo', 'subprocess.Popen', 'os.system'):
            with self.subTest(event=event):
                with self.assertRaises(worker.OfflineFailure):
                    worker.audit_policy(event, ())

    def test_list_catalog_is_finite_and_not_a_verification(self):
        proc, data = self.json_command('list')
        self.assertEqual(proc.returncode, 0)
        self.assertEqual(data['mode'], 'CATALOG_ONLY_NOT_VERIFIED')
        self.assertEqual({x['id'] for x in data['cases']}, set(CASES))
        self.assertEqual(sum(len(x['inputs']) for x in data['cases']), 29)

    def test_demo_success_is_local_only(self):
        proc, data = self.json_command('demo')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual([x['status'] for x in data['cases']], ['OBSERVED']*5)
        self.assertEqual(data['overall'], 'UNRESOLVED')
        self.assertEqual(data['real_genesis_readiness'], 'NOT_ESTABLISHED')

    def test_failed_case_keeps_later_observations(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_inputs(tmp)
            path = Path(tmp)/'u3-july2025.pdf'
            path.write_bytes(b'not a supported public edition')
            proc, data = self.json_command('demo', '--inputs', tmp)
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(data['cases'][0]['status'], 'REJECTED')
        self.assertEqual([x['status'] for x in data['cases'][1:]], ['OBSERVED']*4)

    def test_missing_input_exit_and_no_false_observation(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc, data = self.json_command('verify', 'u3-july-2025', '--inputs', tmp)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(data['cases'][0]['status'], 'MISSING')

    def test_human_output_explains_finite_results(self):
        proc = self.command('verify', 'u3-july-2025')
        self.assertEqual(proc.returncode, 0)
        self.assertIn('4.2', proc.stdout)
        self.assertIn('2025-07', proc.stdout)
        self.assertIn('未建立', proc.stdout)

    def test_unknown_cli_case_has_no_success(self):
        proc = self.command('verify', 'unsupported')
        self.assertEqual(proc.returncode, 2)
        self.assertNotIn('OBSERVED', proc.stdout)

    def test_copied_sources_and_inputs_work_from_unrelated_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)/'repo'
            inputs = Path(tmp)/'inputs'
            copy_sources(repo)
            copy_inputs(inputs)
            script = repo/'scripts/development/offline_evidence/cli.py'
            proc, moved = self.json_command('demo', '--inputs', str(inputs), script=script, cwd=Path(tmp))
            self.assertEqual(proc.returncode, 0, proc.stderr)
            original, normal = self.json_command('demo')
            self.assertEqual(original.returncode, 0)
            self.assertEqual(moved, normal)

    def test_modified_gdp_source_is_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            copy_sources(repo)
            row = CASES['gdp-2026-vintages']['sources'][0]
            (repo/row['path']).write_text('raise AssertionError("must never execute")\n')
            result = cli.run_case('gdp-2026-vintages', repository_root=repo)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['status'], 'REJECTED')
        self.assertEqual(result['error'], 'SOURCE_CHANGED')

    def test_modified_binding_shared_schema_is_not_hidden(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            copy_sources(repo)
            (repo/'schemas/test_contract_v2.schema.json').write_text('{}')
            result = cli.run_case('bindings-demo', repository_root=repo)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['status'], 'REJECTED')
        self.assertEqual(result['error'], 'SOURCE_CHANGED')


class GDPComparisonTests(unittest.TestCase):
    """Catch cross-quarter baselines, lost provenance, and false success tables."""

    @classmethod
    def setUpClass(cls):
        cls.observed = cli.run_case('gdp-2026-vintages')
        if cls.observed['status'] != 'OBSERVED':
            raise AssertionError(cls.observed)

    def compare(self, observed=None):
        self.assertTrue(callable(getattr(cli, 'compare_gdp', None)), 'comparison behavior missing')
        # Exercise derivation/error handling on full, real worker results; only
        # replace the already exercised passive worker for malformed-result probes.
        with patch.object(cli, 'run_case', return_value=deepcopy(self.observed if observed is None else observed)):
            return cli.compare_gdp()

    def command(self, *args):
        return subprocess.run([str(PYTHON), '-I', '-B', str(HERE/'cli.py'), 'compare-gdp', *args],
                              cwd=ROOT, capture_output=True, text=True, timeout=45)

    def test_equal_display_values_do_not_establish_no_underlying_revision(self):
        self.assertTrue(callable(getattr(cli, 'compare_gdp', None)))
        result = cli.compare_gdp()
        self.assertEqual(result['status'], 'OBSERVED', result)
        comparison = result['observations']['comparison']
        self.assertEqual(comparison['quarters'][1]['rows'][1]['change_from_previous_pp'], '0')
        self.assertEqual(comparison.get('difference_basis'),
                         'SUBTRACTION_OF_LISTED_DECIMAL_VALUES_NOT_UNROUNDED_REVISION')
        self.assertEqual(comparison.get('unrounded_revisions'),
                         'NOT_ESTABLISHED_BY_DISPLAY_VALUE_SUBTRACTION')

    def test_human_output_distinguishes_display_difference_from_unrounded_revision(self):
        result = cli.compare_gdp()
        text = cli.human_report(cli.build_report([result]))
        self.assertIn('列示公布值之差', text)
        self.assertIn('差值为0不表示底层估计完全没有修订', text)
        self.assertEqual(result['observations']['comparison']['quarters'][1]['rows'][1]['canonical_decimal'], '1.5')

    def test_quarter_baselines_and_decimal_point_differences(self):
        result = self.compare()
        self.assertEqual(result['status'], 'OBSERVED', result)
        groups = result['observations']['comparison']['quarters']
        self.assertEqual([g['reference_quarter'] for g in groups], ['2026-Q1', '2026-Q2'])
        self.assertEqual([[r['change_from_previous_pp'] for r in g['rows']] for g in groups],
                         [[None, '-0.4', '0.5', '0.4'], [None, '0', '0.7']])
        self.assertEqual([[r['change_from_first_listed_pp'] for r in g['rows']] for g in groups],
                         [['0', '-0.4', '0.1', '0.5'], ['0', '0', '0.7']])
        self.assertEqual(result['observations']['comparison']['difference_unit'], 'PERCENTAGE_POINTS')

    def test_same_value_different_edition_and_exact_source_preserved(self):
        data = self.compare()['observations']
        rows = [r for g in data['comparison']['quarters'] for r in g['rows']]
        self.assertEqual(len(rows), 7)
        self.assertEqual([r['canonical_decimal'] for r in rows[4:]], ['1.5', '1.5', '2.2'])
        for row, original in zip(rows, self.observed['observations']['versions']):
            for key, value in original.items():
                self.assertEqual(row[key], value, key)
        self.assertEqual(data['advance_bindings'], self.observed['observations']['advance_bindings'])

    def test_shuffled_rows_use_publication_order_without_cross_quarter_delta(self):
        observed = deepcopy(self.observed)
        observed['observations']['versions'].reverse()
        result = self.compare(observed)
        self.assertEqual(result['status'], 'OBSERVED', result)
        q1, q2 = result['observations']['comparison']['quarters']
        self.assertEqual(q1['rows'][0]['publication_date'], '2026-04-30')
        self.assertEqual(q2['rows'][0]['publication_date'], '2026-07-30')
        self.assertIsNone(q2['rows'][0]['change_from_previous_pp'])

    def test_missing_duplicate_or_unknown_release_does_not_make_partial_table(self):
        for mutation in ('missing', 'duplicate', 'unknown'):
            observed = deepcopy(self.observed)
            rows = observed['observations']['versions']
            if mutation == 'missing':
                rows.pop()
            elif mutation == 'duplicate':
                rows[-1] = deepcopy(rows[0])
            else:
                rows[-1]['publication_date'] = '2026-10-15'
            with self.subTest(mutation=mutation):
                result = self.compare(observed)
                self.assertEqual(result['status'], 'REJECTED', result)
                self.assertNotIn('observations', result)

    def test_nonfinite_or_mismatched_numeric_declaration_rejected(self):
        for value in ('NaN', 'Infinity', '1e999999', '2.1', True, None):
            observed = deepcopy(self.observed)
            observed['observations']['versions'][0]['canonical_decimal'] = value
            with self.subTest(value=value):
                result = self.compare(observed)
                self.assertEqual(result['status'], 'REJECTED', result)
                self.assertNotIn('observations', result)

    def test_missing_or_wrong_source_reference_rejected(self):
        for key, value in (('raw_sha256', '0'*64), ('value_cell', ''), ('sheet', 'other')):
            observed = deepcopy(self.observed)
            observed['observations']['versions'][0][key] = value
            with self.subTest(key=key):
                result = self.compare(observed)
                self.assertEqual(result['status'], 'REJECTED', result)
                self.assertNotIn('observations', result)

    def test_missing_advance_pair_is_not_silently_presented_as_verified(self):
        observed = deepcopy(self.observed)
        observed['observations']['advance_bindings'].pop()
        result = self.compare(observed)
        self.assertEqual(result['status'], 'REJECTED', result)
        self.assertNotIn('observations', result)

    def test_failed_worker_never_leaks_stale_comparison(self):
        for status in ('MISSING', 'REJECTED', 'UNAVAILABLE'):
            observed = deepcopy(self.observed)
            observed.update(status=status, error='example')
            result = self.compare(observed)
            self.assertEqual(result['status'], status)
            self.assertNotIn('observations', result)
            self.assertNotEqual(cli.exit_code(cli.build_report([result])), 0)

    def test_json_command_is_finite_and_retains_real_uncertainty(self):
        proc = self.command('--json')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual(len(data['cases']), 1)
        comparison = data['cases'][0]['observations']['comparison']
        self.assertEqual(comparison['coverage'], 'SEVEN_RETAINED_DECLARATIONS_ONLY_NOT_COMPLETE_REVISION_HISTORY')
        self.assertEqual(data['overall'], 'UNRESOLVED')
        self.assertEqual(data['real_admission'], 'NOT_READY')
        self.assertFalse(data['prospective_eligible'])
        self.assertEqual(data['protocol_state_change'], 'NONE')

    def test_human_command_shows_values_point_units_sources_and_scope(self):
        proc = self.command()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        for text in ('2026-Q1', '2026-Q2', '-0.4', '+0.5', '+0.7', '百分点', 'E21',
                     '49ef37def79cf5990992f57f1cc819e50fa5b0f8d0e2f5df824f0f19d5d38bf8',
                     '回溯', '不证明完整修订历史', '未建立'):
            self.assertIn(text, proc.stdout)
        self.assertEqual(proc.stdout.count('| Second |'), 2)

    def test_actual_missing_file_has_no_success_table_or_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            proc = self.command('--inputs', tmp, '--json')
        self.assertEqual(proc.returncode, 1, proc.stderr)
        row = json.loads(proc.stdout)['cases'][0]
        self.assertEqual(row['status'], 'MISSING')
        self.assertNotIn('observations', row)

    def test_actual_corrupt_and_missing_files_keep_both_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            registered = CASES['gdp-2026-vintages']['inputs'][0]
            raw = (ROOT/registered['path']).read_bytes()
            (root/registered['alias']).write_bytes(raw[:-1]+bytes([raw[-1]^1]))
            proc = self.command('--inputs', tmp, '--json')
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertTrue(proc.stdout.strip(), proc.stderr)
        row = json.loads(proc.stdout)['cases'][0]
        self.assertEqual(row['status'], 'REJECTED')
        self.assertEqual({x['error'] for x in row['findings']}, {'MISSING_INPUT', 'INPUT_IDENTITY_MISMATCH'})
        self.assertNotIn('observations', row)


class NewsPDFTests(unittest.TestCase):
    """Catch wrong metric/edition joins, hidden failures and retrospective promotion."""

    def command(self, *args, script=HERE/'cli.py', cwd=ROOT):
        return subprocess.run([str(PYTHON), '-I', '-B', str(script), *args], cwd=cwd,
                              capture_output=True, text=True, timeout=45)

    def comparison(self):
        self.assertTrue(callable(getattr(cli, 'compare_gdp_with_news', None)), 'PDF join missing')
        return cli.compare_gdp_with_news()

    def parser(self):
        source = HERE/'gdp_pdf.py'
        self.assertTrue(source.is_file(), 'PDF consumer missing')
        import types
        module = types.ModuleType('pdf_test_module')
        exec(compile(source.read_bytes(), str(source), 'exec'), module.__dict__)
        return module

    def test_three_actual_news_pdfs_expose_seven_declarations_and_rounding_bound(self):
        result = cli.run_case('gdp-news-pdfs')
        self.assertEqual(result['status'], 'OBSERVED', result)
        data = result['observations']
        self.assertEqual([(d['reference_quarter'], d['stage'], d['canonical_decimal']) for d in data['declarations']],
            [('2026-Q1','Advance','2'),('2026-Q1','Second','1.6'),('2026-Q1','Third','2.1'),
             ('2026-Q1','Revised','2.5'),('2026-Q2','Advance','1.5'),('2026-Q2','Second','1.5'),('2026-Q2','Third','2.2')])
        self.assertEqual(data['rounding_note']['direction'], 'DOWNWARD')
        self.assertEqual(data['rounding_note']['magnitude_pp'], 'LESS_THAN_0.1')
        self.assertIsNone(data['rounding_note']['exact_unrounded_revision_pp'])
        self.assertEqual(data['rounding_note']['page_1_based'], 4)

    def test_optional_comparison_joins_exact_values_and_keeps_pdf_vs_vintage_dates_distinct(self):
        result = self.comparison()
        self.assertEqual(result['status'], 'OBSERVED', result)
        support = result['observations']['news_pdf_support']
        self.assertEqual(len(support['matches']), 7)
        first = support['matches'][0]
        self.assertEqual(first['vintage']['publication_date'], '2026-04-30')
        self.assertEqual(first['pdf']['carrier_publication_date'], '2026-06-25')
        self.assertEqual(first['pdf']['page_1_based'], 3)
        self.assertEqual(first['pdf']['historical_first_bytes'], 'NOT_ESTABLISHED')
        self.assertEqual(support['matches'][3]['pdf']['page_1_based'], 8)

    def test_header_metric_unit_and_unique_row_required(self):
        module = self.parser()
        valid = ('Real GDP and Related Measures [Percent Change (SAAR) from 2026:Q1 to 2026:Q2] '
                 'Advance Estimate Second Estimate Real GDP 1.5 1.5 Current-dollar GDP 7.9 8.0')
        self.assertEqual(module.table_values(valid, '2026-Q2', ('Advance','Second')), ['1.5','1.5'])
        for text in (valid.replace('Real GDP 1.5 1.5','Nominal GDP 1.5 1.5'), valid.replace('SAAR','annual'),
                     valid.replace('2026:Q2','2026:Q3'), valid.replace('Second Estimate','Third Estimate'),
                     valid+' '+valid):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):module.table_values(text, '2026-Q2', ('Advance','Second'))

    def test_cli_json_and_human_keep_boundaries_and_page_sources(self):
        proc = self.command('compare-gdp','--news-pdfs','--json')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data=json.loads(proc.stdout)
        self.assertEqual(data['overall'],'UNRESOLVED')
        self.assertEqual(data['real_admission'],'NOT_READY')
        self.assertFalse(data['prospective_eligible'])
        self.assertEqual(data['protocol_state_change'],'NONE')
        self.assertEqual(len(data['cases'][0]['observations']['news_pdf_support']['matches']),7)
        human=self.command('compare-gdp','--news-pdfs')
        self.assertEqual(human.returncode,0,human.stderr)
        for text in ('PDF','7','gdp1q26-3rd.pdf','第3页','第8页','小于0.1','不是历史首次'):
            self.assertIn(text,human.stdout)

    def test_missing_optin_pdf_does_not_fallback_or_show_success_table(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_inputs(tmp)
            (Path(tmp)/'gdp1q26-3rd.pdf').unlink(missing_ok=True)
            proc=self.command('compare-gdp','--news-pdfs','--inputs',tmp,'--json')
        self.assertEqual(proc.returncode,1,proc.stderr)
        row=json.loads(proc.stdout)['cases'][0]
        self.assertEqual(row['status'],'MISSING')
        self.assertNotIn('observations',row)

    def test_missing_vintage_cannot_hide_corrupt_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_inputs(tmp);root=Path(tmp)
            (root/'gdp-history.xlsx').unlink()
            target=root/'gdp1q26-3rd.pdf'
            self.assertTrue(target.exists(),'new PDF input registration missing')
            raw=target.read_bytes();target.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
            proc=self.command('compare-gdp','--news-pdfs','--inputs',tmp,'--json')
        self.assertEqual(proc.returncode,2,proc.stderr)
        self.assertTrue(proc.stdout.strip(),proc.stderr)
        row=json.loads(proc.stdout)['cases'][0]
        self.assertEqual(row['status'],'REJECTED')
        self.assertEqual({f['error'] for f in row['findings']},{'MISSING_INPUT','INPUT_IDENTITY_MISMATCH'})
        self.assertNotIn('observations',row)

    def test_corrupt_vintage_cannot_hide_missing_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy_inputs(tmp);root=Path(tmp)
            target=root/'gdp-history.xlsx';raw=target.read_bytes();target.write_bytes(raw[:-1]+bytes([raw[-1]^1]))
            (root/'gdp1q26-3rd.pdf').unlink(missing_ok=True)
            proc=self.command('compare-gdp','--news-pdfs','--inputs',tmp,'--json')
        self.assertEqual(proc.returncode,2,proc.stderr)
        self.assertTrue(proc.stdout.strip(),proc.stderr)
        row=json.loads(proc.stdout)['cases'][0]
        self.assertEqual(row['status'],'REJECTED')
        self.assertEqual({f['error'] for f in row['findings']},{'MISSING_INPUT','INPUT_IDENTITY_MISMATCH'})

    def test_claim_substitution_and_omission_rejected_not_just_matching_counts(self):
        self.assertTrue(callable(getattr(cli,'compare_gdp_with_news',None)))
        original_run=cli.run_case
        pdf=original_run('gdp-news-pdfs');self.assertEqual(pdf['status'],'OBSERVED',pdf)
        for mutation in ('wrongvalue','duplicate','omitted'):
            changed=deepcopy(pdf);rows=changed['observations']['declarations']
            if mutation=='wrongvalue':rows[0]['canonical_decimal']='2.1'
            elif mutation=='duplicate':rows[-1]=deepcopy(rows[0])
            else:rows.pop()
            with self.subTest(mutation=mutation):
                with patch.object(cli,'run_case',side_effect=lambda name,*args: deepcopy(changed) if name=='gdp-news-pdfs' else original_run(name,*args)):
                    result=cli.compare_gdp_with_news()
                self.assertEqual(result['status'],'REJECTED',result)
                self.assertNotIn('observations',result)

    def test_missing_pdf_runtime_rejects_optin_without_breaking_default(self):
        self.assertTrue(callable(getattr(cli,'compare_gdp_with_news',None)))
        with patch.object(cli,'PDF_PYTHON',Path('/missing/fp-pdf-runtime')):
            result=cli.compare_gdp_with_news()
            default=cli.compare_gdp()
        self.assertEqual(result['status'],'UNAVAILABLE')
        self.assertNotIn('observations',result)
        self.assertEqual(default['status'],'OBSERVED')

    def test_relocated_optin_sources_and_inputs_work_from_unrelated_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo=Path(tmp)/'repo';inputs=Path(tmp)/'inputs';copy_sources(repo);copy_inputs(inputs)
            proc=self.command('compare-gdp','--news-pdfs','--inputs',str(inputs),'--json',
                              script=repo/'scripts/development/offline_evidence/cli.py',cwd=Path(tmp))
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertEqual(len(json.loads(proc.stdout)['cases'][0]['observations']['news_pdf_support']['matches']),7)


if __name__ == '__main__':
    unittest.main()
