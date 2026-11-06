"""Mainline command behavior: local support must never become real readiness."""
import json
import hashlib
import importlib.util
from copy import deepcopy
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
INPUTS = ROOT/'docs/development/mainline-execution-2026-10-18-observed-five-report-replay-rev-001'
TRACE = ROOT/'docs/development/mainline-execution-2026-10-18-observed-development-run-rev-001'
PROOF = ROOT/'docs/development/mainline-execution-2026-10-09-rev-001/gdp-public-proof-pair-2026-10-15-rev-001'


def copy_run(destination):
    manifest = json.loads((INPUTS/'INPUT_SET.json').read_bytes())
    destination = Path(destination)
    shutil.copyfile(INPUTS/'INPUT_SET.json', destination/'INPUT_SET.json')
    def visit(value):
        if isinstance(value, dict):
            if set(value) == {'path', 'bytes', 'sha256'}:
                target = destination/value['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(INPUTS/value['path'], target)
            else:
                for item in value.values():
                    visit(item)
        elif isinstance(value, list):
            for item in value:
                visit(item)
    visit(manifest['inputs'])


class MainlineFrameworkTests(unittest.TestCase):
    def command(self, *args, json_output=True):
        command = [str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'), 'mainline', *args]
        if json_output:
            command.append('--json')
        process = subprocess.run(command, capture_output=True, text=True, timeout=45)
        self.assertTrue(process.stdout.strip(), process.stderr)
        return process, json.loads(process.stdout) if json_output else process.stdout

    def test_human_summary_missing_run_cannot_claim_local_support(self):
        with tempfile.TemporaryDirectory() as directory:
            process, text = self.command('--run-inputs', directory, json_output=False)
        self.assertEqual(process.returncode, 1)
        self.assertIn('五报告本次内容核对：待补真实输入', text)
        self.assertIn('留存测试事件对应：本次未核对', text)
        self.assertNotIn('五报告组合仅一份有实际有限本机测试支持', text)

    def test_human_summary_rejected_run_keeps_rejection_and_missing_findings(self):
        with tempfile.TemporaryDirectory() as directory:
            copy_run(directory)
            (Path(directory)/'inputs/output-0.raw').unlink()
            file = Path(directory)/'inputs/report-3.raw'
            file.write_bytes(file.read_bytes()+b' ')
            process, text = self.command('--run-inputs', directory, json_output=False)
        self.assertEqual(process.returncode, 2)
        self.assertIn('五报告本次内容核对：拒绝', text)
        self.assertIn('MISSING_INPUT', text)
        self.assertIn('INPUT_IDENTITY_MISMATCH', text)
        self.assertNotIn('五报告组合仅一份有实际有限本机测试支持', text)

    def test_human_summary_missing_trace_does_not_erase_finite_content_or_claim_event_support(self):
        with tempfile.TemporaryDirectory() as directory:
            process, text = self.command('--execution-inputs', directory, json_output=False)
        self.assertEqual(process.returncode, 1)
        self.assertIn('五报告本次内容核对：已核对（局部）', text)
        self.assertIn('留存测试事件对应：本次未核对', text)
        self.assertNotIn('留存测试事件对应：已核对（局部）', text)

    def test_human_summary_default_keeps_content_events_and_real_truth_separate(self):
        process, text = self.command(json_output=False)
        self.assertEqual(process.returncode, 1)
        self.assertIn('五报告本次内容核对：已核对（局部）', text)
        self.assertIn('留存测试事件对应：已核对（局部）', text)
        self.assertIn('不证明真实执行或完整报告真值', text)
        self.assertIn('真实准入：NOT_READY', text)
        self.assertIn('其余四份仍为合成模板', text)

    def test_human_summary_absent_product_results_makes_no_observed_support_claim(self):
        spec = importlib.util.spec_from_file_location('summary_cli', HERE/'cli.py')
        cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
        report = {'mode':'FINITE_MAINLINE_FRAMEWORK', 'modules':[
            {'id':'module-consumption','status':'UNAVAILABLE','error':'MAINLINE_RUNTIME_UNAVAILABLE'}]}
        text = cli.human_report(report)
        self.assertIn('五报告本次内容核对：未执行', text)
        self.assertIn('留存测试事件对应：本次未核对', text)
        self.assertNotIn('五报告组合仅一份有实际有限本机测试支持', text)

    def test_human_summary_stale_status_or_nonboolean_result_never_claims_support(self):
        spec = importlib.util.spec_from_file_location('summary_flags_cli', HERE/'cli.py')
        cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cli)
        baseline = json.loads((ROOT/'docs/development/mainline-verifier-integration-2026-10-25-rev-001/MAINLINE_FINAL_A.json').read_text())
        for kind in ('finite-rejected','trace-rejected','finite-string','trace-string','binding-string'):
            with self.subTest(kind=kind):
                report=deepcopy(baseline); rows={r['id']:r for r in report['modules']}
                if kind=='finite-rejected': rows['finite-reports']['status']='REJECTED'
                if kind=='trace-rejected': rows['execution-trace']['status']='REJECTED'
                if kind=='finite-string': rows['finite-reports']['result']['finite_report_set_match']='true'
                if kind=='trace-string': rows['execution-trace']['result']['local_event_consistency_match']='true'
                if kind=='binding-string': rows['execution-trace']['r4t_binding']['finite_mapping_match']='true'
                text=cli.human_report(report)
                self.assertIn('留存测试事件对应：本次未核对', text)
                self.assertNotIn('留存测试事件对应：已核对（局部）', text)

    def test_one_command_connects_finite_inputs_data_and_protected_diagnostics(self):
        # Catches a disconnected/static dashboard or local success promoted to readiness.
        process, report = self.command()
        self.assertEqual(process.returncode, 1)
        modules = {row['id']: row for row in report['modules']}
        self.assertEqual(modules['finite-reports']['status'], 'OBSERVED')
        self.assertTrue(modules['finite-reports']['result']['finite_report_set_match'])
        self.assertEqual(modules['economic-data']['status'], 'OBSERVED')
        self.assertEqual(len(modules['economic-data']['result']['observations']['versions']), 7)
        self.assertEqual(modules['official-calendar']['status'], 'OBSERVED')
        self.assertEqual(modules['qualification-history']['status'], 'MISSING')
        self.assertEqual(modules['mandatory-cycles']['status'], 'MISSING')
        self.assertIn('FULL_TRUST_CORE_CHECK_AUTHORITY_NOT_IMPLEMENTED',
                      modules['prospective-eligibility']['result']['reason_codes'])
        self.assertEqual(modules['final-readiness']['status'], 'MISSING')
        self.assertEqual(report['real_admission'], 'NOT_READY')
        self.assertFalse(report['prospective_eligible'])
        self.assertEqual(report['protocol_state_change'], 'NONE')

    def test_explicit_missing_run_directory_never_falls_back_and_other_modules_continue(self):
        # Catches silently reusing the default package or stopping all work on missing input.
        with tempfile.TemporaryDirectory() as directory:
            process, report = self.command('--run-inputs', directory)
        modules = {row['id']: row for row in report['modules']}
        self.assertEqual(process.returncode, 1)
        self.assertEqual(modules['finite-reports']['status'], 'MISSING')
        self.assertEqual(modules['economic-data']['status'], 'OBSERVED')
        self.assertEqual(modules['final-readiness']['result']['status'], 'UNKNOWN')

    def test_raw_substitution_and_missing_output_are_both_retained(self):
        # Catches first-error-only loading or reporting a local finite positive after replacement.
        with tempfile.TemporaryDirectory() as directory:
            copy_run(directory)
            manifest = json.loads((Path(directory)/'INPUT_SET.json').read_bytes())['inputs']
            (Path(directory)/manifest['base_records']['r4t']['path']).write_bytes(b'replaced')
            output = next(iter(manifest['raw_artifacts'].values()))
            (Path(directory)/output['path']).unlink()
            process, report = self.command('--run-inputs', directory)
        finite = next(row for row in report['modules'] if row['id'] == 'finite-reports')
        self.assertEqual(process.returncode, 2)
        self.assertEqual(finite['status'], 'REJECTED')
        self.assertEqual({row['error'] for row in finite['findings']},
                         {'INPUT_IDENTITY_MISMATCH', 'MISSING_INPUT'})
        self.assertNotIn('result', finite)
        self.assertEqual(report['overall'], 'REJECTED')

    def test_changed_manifest_is_rejected_before_following_its_paths(self):
        # Catches arbitrary-file reads enabled by accepting a caller-controlled manifest.
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/'INPUT_SET.json').write_text('{"path":"/not-authorized"}')
            process, report = self.command('--run-inputs', directory)
        finite = next(row for row in report['modules'] if row['id'] == 'finite-reports')
        self.assertEqual(process.returncode, 2)
        self.assertEqual(finite['findings'][0]['error'], 'INPUT_IDENTITY_MISMATCH')

    def test_symlink_input_is_rejected_even_with_correct_target_bytes(self):
        # Catches following a caller alias outside the declared public-input layout.
        with tempfile.TemporaryDirectory() as directory:
            copy_run(directory)
            original = Path(directory)/'inputs/report-0.raw'
            original.unlink()
            original.symlink_to(INPUTS/'inputs/report-0.raw')
            process, report = self.command('--run-inputs', directory)
        finite = next(row for row in report['modules'] if row['id'] == 'finite-reports')
        self.assertEqual(process.returncode, 2)
        self.assertIn('UNSAFE_PATH', [row['error'] for row in finite['findings']])

    def test_human_output_distinguishes_framework_and_real_gaps(self):
        # Catches displaying a framework demonstration as full project completion.
        process, text = self.command(json_output=False)
        self.assertEqual(process.returncode, 1)
        self.assertIn('主线开发框架', text)
        self.assertIn('真实准入：NOT_READY', text)
        self.assertIn('合成', text)

    def test_actual_events_are_joined_to_the_same_r4t_without_authenticating_execution(self):
        process, report = self.command()
        modules = {row['id']: row for row in report['modules']}
        trace = modules.get('execution-trace', {})
        self.assertEqual(trace.get('status'), 'OBSERVED', trace)
        result = trace['result']
        self.assertTrue(result['local_event_consistency_match'])
        self.assertTrue(trace['r4t_binding']['finite_mapping_match'])
        self.assertEqual(trace['r4t_binding']['mapped_methods'], 16)
        self.assertEqual(trace['r4t_binding']['event_rows'], 50)
        self.assertEqual(trace['r4t_binding']['r4t_raw_sha256'],
                         'b42f189a3d2def677635c34627d007644a90a410b53af2f7d52a34985f3c4b4c')
        self.assertEqual(result['actual_execution_truth'], 'NOT_VERIFIED')
        time = modules['time-and-durability']
        self.assertEqual(time['status'], 'MISSING')
        self.assertEqual(time['public_example']['status'], 'OBSERVED')
        self.assertTrue(time['public_example']['subject_digest_match'])
        self.assertEqual(time['public_example']['unverified_body_bytes'], 585)
        self.assertEqual(time['public_example']['full_ots_verification'], 'NOT_CHECKED')
        self.assertEqual(report['real_admission'], 'NOT_READY')
        self.assertEqual(process.returncode, 1)

    def test_missing_trace_and_proof_do_not_fall_back_or_stop_other_branches(self):
        with tempfile.TemporaryDirectory() as directory:
            process, report = self.command('--execution-inputs', directory, '--proof-inputs', directory)
        modules = {row['id']: row for row in report['modules']}
        self.assertEqual(process.returncode, 1)
        self.assertEqual(modules.get('execution-trace', {}).get('status'), 'MISSING')
        self.assertEqual(modules['time-and-durability']['public_example']['status'], 'MISSING')
        self.assertEqual(modules['finite-reports']['status'], 'OBSERVED')
        self.assertEqual(modules['economic-data']['status'], 'OBSERVED')

    def test_replaced_events_and_missing_mapping_are_both_visible(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            for name in ['EVENT_EXPECTED_CORRECTED.json', 'EVENT_RUN_OBSERVATION.json',
                         'raw-attempt2/events.jsonl']:
                (target/name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(TRACE/name, target/name)
            (target/'raw-attempt2/events.jsonl').write_bytes(b'{}\n')
            process, report = self.command('--execution-inputs', directory)
        trace = next((row for row in report['modules'] if row['id'] == 'execution-trace'), {})
        self.assertEqual(trace.get('status'), 'REJECTED', trace)
        self.assertEqual({row['error'] for row in trace['findings']},
                         {'MISSING_INPUT', 'INPUT_IDENTITY_MISMATCH'})
        self.assertEqual(process.returncode, 2)

    def test_proof_failure_preserves_missing_pdf_and_never_becomes_time_support(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/'raw'
            target.mkdir()
            (target/'gdp2q25-2nd.pdf.ots').write_bytes(b'not a proof')
            process, report = self.command('--proof-inputs', directory)
        time = next(row for row in report['modules'] if row['id'] == 'time-and-durability')
        self.assertEqual(time['status'], 'REJECTED')
        self.assertEqual({row['error'] for row in time['public_example']['findings']},
                         {'MISSING_INPUT', 'INPUT_IDENTITY_MISMATCH'})
        self.assertEqual(process.returncode, 2)

    def test_event_join_rejects_outcome_identity_and_invocation_substitution(self):
        # Exercise the actual join independently of the fixed-file admission layer.
        from copy import deepcopy
        from types import ModuleType
        worker = ModuleType('mainline_join_test')
        worker.__file__ = str(HERE/'mainline_worker.py')
        exec(compile((HERE/'mainline_worker.py').read_bytes(), worker.__file__, 'exec'), worker.__dict__)
        self.assertTrue(hasattr(worker, 'bind_event_results'), 'event-to-R4T join not implemented')
        expected = json.loads((TRACE/'EVENT_EXPECTED_CORRECTED.json').read_bytes())
        mapping = json.loads((TRACE/'pre-attempt2/method-map.json').read_bytes())
        observation = json.loads((TRACE/'EVENT_RUN_OBSERVATION.json').read_bytes())
        events = (TRACE/'raw-attempt2/events.jsonl').read_bytes()
        raw = (TRACE/'OBSERVED_R4T.raw').read_bytes()
        definition = json.loads((TRACE/'pre-attempt2/definition.json').read_bytes())
        positive = worker.bind_event_results(expected, mapping, observation, events, raw, definition)
        self.assertTrue(positive['finite_mapping_match'])
        for field, value in [('outcome', 'FAILURE'), ('instance_id', 'FOREIGN'),
                             ('invocation_id', 'FOREIGN')]:
            report = json.loads(raw)
            report['results'][0][field] = value
            changed = json.dumps(report).encode()
            with self.subTest(field=field):
                result = worker.bind_event_results(expected, mapping, observation, events, changed, definition)
                self.assertFalse(result['finite_mapping_match'])
                self.assertEqual(result['r4t_raw_sha256'], hashlib.sha256(changed).hexdigest())
        duplicate = deepcopy(mapping)
        duplicate[-1] = deepcopy(duplicate[0])
        self.assertFalse(worker.bind_event_results(expected, duplicate, observation, events, raw,
                                                   definition)['finite_mapping_match'])


if __name__ == '__main__':
    unittest.main()
