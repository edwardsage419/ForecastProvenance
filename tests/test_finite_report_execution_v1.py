"""Port parity and import/consume boundaries using existing keyless fixtures."""
from copy import deepcopy
import ast
import hashlib
import importlib.util
import inspect
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / 'docs/development/mainline-execution-2026-10-18-five-report-execution-join-rev-001/test_consumer.py'
spec = importlib.util.spec_from_file_location('_finite_port_existing_cases', OLD)
LEGACY = importlib.util.module_from_spec(spec); spec.loader.exec_module(LEGACY)
T = LEGACY.T
IMPORT_DOC_READS = []
_ACTIVE_IMPORT = False
_ACTIVE_CONSUME = False

def audit(event, args):
    if _ACTIVE_CONSUME and (event == 'open' or event.startswith('socket.') or event in {'subprocess.Popen','os.system','os.posix_spawn'}):
        raise AssertionError('I/O during finite consumption: ' + event)
    if _ACTIVE_IMPORT and event == 'open' and args and isinstance(args[0], str) and '/docs/' in args[0]:
        IMPORT_DOC_READS.append(args[0])
        raise AssertionError('docs access during normal finite library import')
sys.addaudithook(audit)
S = None
_ACTIVE_IMPORT = True
try:
    from forecast_trust_core import finite_development as S
except ImportError as exc:
    if 'finite_development' not in str(exc): raise
finally:
    _ACTIVE_IMPORT = False

def guarded_consume(args):
    global _ACTIVE_CONSUME
    _ACTIVE_CONSUME = True
    try: return S.consume_finite_report_set(*args)
    finally: _ACTIVE_CONSUME = False

def without_supplementary(value):
    if type(value) is dict:
        return {k: without_supplementary(v) for k, v in value.items() if k != 'rejected_observations'}
    if type(value) is list: return [without_supplementary(v) for v in value]
    return value

class FiniteProductTests(unittest.TestCase):
    def call(self, args):
        self.assertIsNotNone(S, 'Missing new five-report execution consumer')
        before = deepcopy(args); out = guarded_consume(args)
        oracle = LEGACY.S.consume_finite_report_set(*args)
        self.assertEqual(without_supplementary(out), oracle)
        self.assertEqual(args, before)
        self.assertEqual(out['real_admission'], 'NOT_READY')
        self.assertEqual(out['independently_complete_product_universe'], 'NOT_ESTABLISHED')
        self.assertEqual(out['strong_truth'], 'NOT_VERIFIED')
        self.assertFalse(out['prospective_eligible']); self.assertEqual(out['protocol_state_change'], 'NONE')
        self.assertEqual(len(out['real_missing']), 29); self.assertEqual(len(out['unverified_obligations']), 11)
        return out

    def test_exact_five_and_complete_finite_execution_match_without_authority(self):
        a, _ = T.case(); r = self.call(a)
        self.assertTrue(r['finite_report_set_match']); self.assertEqual(r['verdict'], 'UNRESOLVED')
        self.assertEqual(len(r['r6t_results']), 1)
        self.assertTrue(r['r6t_results'][0]['result']['finite_r6t_positive_match'])
        self.assertEqual(r['set_result']['local_set_binding_verdict'], 'LOCAL_REQUIRED_REPORT_SET_BINDINGS_VERIFIED')

    def test_valid_summaries_cannot_hide_unexpected_run_failure(self):
        a, b = T.case(); b['results'][0]['outcome'] = 'FAILURE'; T.refresh(a, b); r = self.call(a)
        self.assertEqual(r['set_result']['local_set_binding_verdict'], 'LOCAL_REQUIRED_REPORT_SET_BINDINGS_VERIFIED')
        self.assertEqual(r['r6t_results'][0]['result']['execution_result']['execution_content_result']['failed_instances'], ['INV.A/CASE.A'])
        self.assertEqual(r['verdict'], 'REJECT'); self.assertFalse(r['finite_report_set_match'])

    def test_missing_output_is_unresolved_not_finite_success(self):
        a, b = T.case(); del a[12][b['invocations'][0]['stdout']['artifact_id']]; r = self.call(a)
        self.assertFalse(r['finite_report_set_match']); self.assertEqual(r['verdict'], 'UNRESOLVED')
        self.assertTrue(r['r6t_results'][0]['result']['execution_result']['execution_content_result']['missing_inputs'])

    def test_explicit_missing_r4t_uses_shared_missing_snapshot(self):
        a, _ = T.case(); a[4]['r4t'] = None; r = self.call(a)
        self.assertEqual(r['verdict'], 'UNRESOLVED')
        self.assertFalse(r['finite_report_set_match'])
        self.assertIn('r4t_bytes', r['set_result']['missing_set_inputs'])
        self.assertIn('report', r['r6t_results'][0]['result']['execution_result']['execution_content_result']['missing_inputs'])

    def test_joint_trust_catalog_body_omission_is_detected_beyond_old_set_positive(self):
        a, _ = T.case(trust_ids=('CHECK-A',)); r = self.call(a)
        self.assertEqual(r['set_result']['local_set_binding_verdict'], 'LOCAL_REQUIRED_REPORT_SET_BINDINGS_VERIFIED')
        self.assertIn('R6T_CHECK_COVERAGE_MISMATCH', r['r6t_results'][0]['result']['join_errors'])
        self.assertFalse(r['finite_report_set_match']); self.assertEqual(r['verdict'], 'REJECT')

    def test_duplicate_later_fail_is_consumed_in_both_paths(self):
        a, _ = T.case(); old = deepcopy(T.row(a))
        T.OLD.rewrite(a, T.KIND, lambda r: (r['checks'][0].update(status='FAIL'), r.update(result='INVALID')))
        a[1].insert(0, old); r = self.call(a)
        self.assertEqual(len(r['r6t_results']), 2)
        self.assertEqual(r['r6t_results'][1]['result']['report_result']['join_result']['content_result']['failed_checks'], ['CHECK-A'])
        self.assertIn('DUPLICATE_REPORT_KIND', r['set_result']['set_errors'])
        self.assertEqual(r['verdict'], 'REJECT'); self.assertFalse(r['finite_report_set_match'])

    def test_missing_sibling_keeps_runtime_failure(self):
        a, b = T.case(); b['results'][0]['outcome'] = 'FAILURE'; T.refresh(a, b)
        a[1] = [x for x in a[1] if x['kind'] != 'PROVIDER_REHEARSAL_REPORT']; r = self.call(a)
        self.assertIn('PROVIDER_REHEARSAL_REPORT', r['set_result']['missing_report_kinds'])
        self.assertEqual(r['verdict'], 'REJECT'); self.assertFalse(r['finite_report_set_match'])

    def test_missing_r6t_still_checks_actual_runtime_content(self):
        a, b = T.case(); b['results'][0]['outcome'] = 'FAILURE'; T.refresh(a, b)
        a[1] = [x for x in a[1] if x['kind'] != T.KIND]; r = self.call(a)
        self.assertIn(T.KIND, r['set_result']['missing_report_kinds'])
        self.assertEqual(r['r6t_results'][0]['status'], 'MISSING_REPORT')
        self.assertEqual(r['r6t_results'][0]['result']['execution_result']['execution_content_result']['failed_instances'], ['INV.A/CASE.A'])
        self.assertEqual(r['verdict'], 'REJECT')

    def test_explicit_missing_r6t_is_unknown_with_valid_execution(self):
        a, _ = T.case(); T.row(a)['bytes'] = None; r = self.call(a)
        self.assertFalse(r['finite_report_set_match']); self.assertEqual(r['verdict'], 'UNRESOLVED')
        self.assertEqual(r['r6t_results'][0]['status'], 'MISSING_REPORT')

    def test_r4t_wire_substitution_reaches_both_real_layers(self):
        a, _ = T.case(); a[4]['r4t'] += b'\n'; r = self.call(a)
        self.assertIn('R4T_RAW_MISMATCH', r['set_result']['set_errors'])
        self.assertIn('REPORT_RAW_MISMATCH', r['r6t_results'][0]['result']['execution_result']['execution_content_result']['comparison_errors'])
        self.assertEqual(r['verdict'], 'REJECT')

    def test_subject_substitution_cannot_pass(self):
        a, _ = T.case(); a[0]['final_manifest_ref'] = T.H.external('FOREIGN-SUBJECT'); r = self.call(a)
        self.assertIn('SET_CONTEXT_MISMATCH', r['set_result']['set_errors'])
        self.assertFalse(r['finite_report_set_match']); self.assertEqual(r['verdict'], 'REJECT')

    def test_strong_failed_declaration_remains_failed_and_unreplayed(self):
        a, _ = T.case(verified=False); r = self.call(a)
        self.assertEqual(r['set_result']['strong_reported_result'], 'FAILED')
        self.assertFalse(r['finite_report_set_match']); self.assertEqual(r['verdict'], 'REJECT')

    def test_report_order_does_not_assign_roles(self):
        a, _ = T.case(); a[1].reverse(); r = self.call(a)
        self.assertTrue(r['finite_report_set_match'])

    def test_global_joint_shrink_keeps_independent_universe_unknown(self):
        base, body = T.T.case(); T.T.shrink_all_supplied_scope(base, body)
        a = T.assemble(base, trust_ids=('CHECK-A',))
        # Other report scopes may be subsets; use the same single selected check.
        for kind in T.OLD.KINDS:
            T.T.summarize(base, ids=('CHECK-A',), kind=kind)
            a[0]['r6_expected'][kind] = deepcopy(base[0]); a[2][kind] = {'bytes': base[8], 'sha256': base[9]}
            next(x for x in a[1] if x['kind'] == kind)['bytes'] = base[1]
        r = self.call(a); self.assertTrue(r['finite_report_set_match'])
        self.assertEqual(r['verdict'], 'UNRESOLVED')

    def test_unknown_record_and_caller_eligibility_never_execute_or_upgrade(self):
        class Trap:
            def __iter__(self): raise AssertionError('unknown iteration')
            def __eq__(self, other): raise AssertionError('unknown equality')
        a, _ = T.case(); a[1].insert(0, Trap())
        self.assertIsNotNone(S, 'Missing new five-report execution consumer')
        r = S.consume_finite_report_set(*a)
        self.assertEqual(r['verdict'], 'REJECT'); self.assertFalse(r['finite_report_set_match'])
        a, _ = T.case(); a[0]['prospective_eligible'] = True; r = self.call(a)
        self.assertEqual(r['verdict'], 'REJECT'); self.assertFalse(r['finite_report_set_match'])

    def test_oversized_report_list_is_not_truncated_into_success(self):
        a, _ = T.case(); a[1] = [deepcopy(T.row(a)) for _ in range(17)]; r = self.call(a)
        self.assertIn('INVALID_REPORT_LIST', r['set_result']['set_errors'])
        self.assertFalse(r['finite_report_set_match']); self.assertEqual(r['verdict'], 'REJECT')
    def test_exact_public_signature_and_single_export(self):
        self.assertIsNotNone(S, 'Missing import-safe finite development library')
        self.assertEqual(len(inspect.signature(S.consume_finite_report_set).parameters), 13)
        self.assertEqual(S.__all__, ['consume_finite_report_set'])

    def test_normal_import_does_not_read_development_documents(self):
        self.assertIsNotNone(S, 'Missing import-safe finite development library')
        self.assertEqual(IMPORT_DOC_READS, [])
        self.assertIn('/src/forecast_trust_core/finite_development/', S.__file__)

    def test_embedded_formats_match_retained_exact_development_bytes(self):
        self.assertIsNotNone(S, 'Missing import-safe finite development library')
        from forecast_trust_core.finite_development import _schemas
        inputs = json.loads((ROOT / 'docs/development/mainline-execution-2026-10-18-import-safe-finite-consumer-rev-001/INPUTS.json').read_bytes())
        self.assertEqual(set(_schemas.RAW_BYTES), set(inputs['embedded_schema_inputs']))
        for name, record in inputs['embedded_schema_inputs'].items():
            self.assertEqual(hashlib.sha256(_schemas.RAW_BYTES[name]).hexdigest(), record['sha256'])

    def test_no_dynamic_document_loader_in_product_source(self):
        self.assertIsNotNone(S, 'Missing import-safe finite development library')
        for path in Path(S.__file__).parent.glob('*.py'):
            tree = ast.parse(path.read_bytes())
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    self.assertNotIn(node.func.id, {'exec','compile','ModuleType','eval','open'})
            self.assertNotIn('Path(__file__)', path.read_text())

    def test_rejected_context_diagnostics_stay_supplementary(self):
        a, _ = T.case()
        def wrong_context(report):
            report['checks'][0]['status'] = 'FAIL'
            report['checks'][0]['report_context']['subject_ref'] = T.H.external('FOREIGN-CONTEXT')
        T.OLD.rewrite(a, T.KIND, wrong_context)
        r = self.call(a)
        content = r['r6t_results'][0]['result']['report_result']['join_result']['content_result']
        self.assertEqual(content['failed_checks'], [])
        self.assertFalse(content['rejected_observations'][0]['context_bound'])
        self.assertEqual(content['rejected_observations'][0]['reported_status'], 'FAIL')
        self.assertEqual(r['verdict'], 'REJECT')


if __name__ == '__main__': unittest.main()
