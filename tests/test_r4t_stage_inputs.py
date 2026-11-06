"""Stage-separated local comparison using existing synthetic-only fixtures.

No actual TC/report/profile, signatures, event collection or test discovery.
"""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('_r4t_stage_fixtures', ROOT / 'tests/test_r4t_unavailable_observations.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
base = fixtures.base


def inputs(body=None, expected=None, successor=False):
    b, e, artifacts = base.fixture()
    raw, e = base.wire(b if body is None else body, e if expected is None else expected)
    schema = fixtures.schema_bytes() if successor else base.SCHEMA
    post = {k: e[k] for k in ('report_ref', 'report_raw_sha256')}
    pre = {k: deepcopy(e[k]) for k in ('bindings', 'test_definition_raw_sha256', 'run_id', 'invocations')}
    pre.update(format='FP_DEV_R4T_PRE_RUN_EXPECTATIONS_V1', scope='FINITE_DEVELOPMENT_SCOPE_ONLY',
               schema_raw_sha256=hashlib.sha256(schema).hexdigest())
    return pre, post, raw, schema, artifacts


class StageInputTests(unittest.TestCase):
    def consume(self, args):
        fn = getattr(base.consumer, 'consume_predeclared_execution_content', None)
        self.assertTrue(callable(fn), 'Missing stage-separated content entry')
        before = deepcopy(args)
        out = fn(*args)
        self.assertEqual(args, before)
        self.assertEqual(out['real_admission'], 'NOT_READY')
        self.assertEqual(out['real_genesis_readiness'], 'NOT_ESTABLISHED')
        self.assertFalse(out['prospective_eligible'])
        self.assertEqual(out['protocol_state_change'], 'NONE')
        self.assertEqual(out['authenticated_chronology'], 'NOT_ESTABLISHED')
        self.assertEqual(out['independently_complete_universe'], 'NOT_ESTABLISHED')
        self.assertEqual(out['pre_run_fixing'], 'NOT_VERIFIED')
        return out

    def test_legacy_complete_content_preserves_local_only_match(self):
        out = self.consume(inputs())
        self.assertTrue(out['finite_expectations_match'])
        self.assertEqual(out['verdict'], 'UNRESOLVED')
        self.assertEqual(out['pre_definition_status'], 'VALID_STRUCTURE')
        self.assertEqual(out['result_binding_status'], 'VALID_STRUCTURE')

    def test_successor_complete_content_keeps_schema_version_boundary(self):
        out = self.consume(inputs(successor=True))
        self.assertTrue(out['finite_expectations_match'])
        self.assertEqual(out['verdict'], 'UNRESOLVED')

    def test_pre_cannot_include_post_report_identity(self):
        for key in ('report_ref', 'report_raw_sha256'):
            with self.subTest(key=key):
                args = list(inputs()); args[0][key] = deepcopy(args[1][key])
                out = self.consume(args)
                self.assertEqual(out['verdict'], 'REJECT')
                self.assertIn('PRE_DEFINITION_INVALID', out['comparison_errors'])
                self.assertFalse(out['finite_expectations_match'])

    def test_post_cannot_shrink_pre_invocations(self):
        args = list(inputs()); args[1]['invocations'] = []
        out = self.consume(args)
        self.assertEqual(out['verdict'], 'REJECT')
        self.assertIn('RESULT_BINDING_INVALID', out['comparison_errors'])
        self.assertFalse(out['finite_expectations_match'])

    def test_post_raw_and_full_identity_mismatch_stay_distinct(self):
        for key, diagnostic in (('report_raw_sha256', 'REPORT_RAW_MISMATCH'), ('report_ref', 'REPORT_REF_MISMATCH')):
            with self.subTest(key=key):
                args = list(inputs())
                if key == 'report_ref': args[1][key]['content_sha256'] = '0' * 64
                else: args[1][key] = '0' * 64
                out = self.consume(args)
                self.assertIn(diagnostic, out['comparison_errors'])
                self.assertEqual(out['verdict'], 'REJECT')

    def test_pre_schema_identity_mismatch_has_no_automatic_downgrade(self):
        args = list(inputs(successor=True)); args[0]['schema_raw_sha256'] = hashlib.sha256(base.SCHEMA).hexdigest()
        out = self.consume(args)
        self.assertIn('PRE_SCHEMA_IDENTITY_MISMATCH', out['comparison_errors'])
        self.assertFalse(out['finite_expectations_match'])
        args = list(inputs()); args[0]['format'] = 'FP_DEV_R4T_EXECUTION_EXPECTED_V1'
        self.assertEqual(self.consume(args)['verdict'], 'REJECT')

    def test_missing_stage_inputs_remain_unresolved(self):
        for n, missing in ((0, 'pre_definition'), (1, 'result_binding')):
            with self.subTest(stage=n):
                args = list(inputs()); args[n] = None
                out = self.consume(args)
                self.assertIn(missing, out['missing_inputs'])
                self.assertEqual(out['verdict'], 'UNRESOLVED')
                self.assertFalse(out['finite_expectations_match'])

    def test_bound_failure_and_missing_instance_both_survive(self):
        b, e, _ = base.fixture()
        extra = deepcopy(e['invocations'][0]['instances'][0]); extra['instance_id'] = 'CASE.2'
        e['invocations'][0]['instances'].append(extra); b['results'][0]['outcome'] = 'FAILURE'
        out = self.consume(inputs(b, e))
        self.assertEqual(out['failed_instances'], ['INV.1/CASE.1'])
        self.assertEqual(out['missing_instances'], ['INV.1/CASE.2'])
        self.assertEqual(out['verdict'], 'REJECT')

    def test_report_argv_order_changes_are_not_normalized(self):
        args = list(inputs()); args[0]['invocations'][0]['argv'] = ['python', 'same', '', 'same']
        out = self.consume(args)
        self.assertIn('INVOCATION_BINDING_MISMATCH', out['comparison_errors'])
        self.assertFalse(out['finite_expectations_match'])

    def test_unknown_authority_controls_and_callback_values_are_rejected(self):
        def forbidden(): raise AssertionError('Caller callback executed')
        for n, key, value in ((0, 'verified', True), (1, 'universe_complete', True), (0, 'callback', forbidden)):
            with self.subTest(stage=n, key=key):
                args = list(inputs()); args[n][key] = value
                out = self.consume(args)
                self.assertEqual(out['verdict'], 'REJECT')
                self.assertFalse(out['finite_expectations_match'])

    def test_limits_remain_unresolved_or_rejected_without_partial_success(self):
        args = list(inputs()); deep = []
        for _ in range(66): deep = [deep]
        args[0]['invocations'] = deep
        out = self.consume(args)
        self.assertEqual(out['verdict'], 'REJECT')
        self.assertFalse(out['finite_expectations_match'])
        args = list(inputs()); args[2] = b' ' * (4 * 1024 * 1024 + 1)
        out = self.consume(args)
        self.assertIn('report:LOCAL_BYTE_LIMIT', out['missing_inputs'])
        self.assertFalse(out['finite_expectations_match'])

    def test_declared_negative_exit_and_outcome_keep_original_semantics(self):
        b, e, _ = base.fixture(); b['invocations'][0]['termination']['exit_code'] = 2
        b['results'][0]['outcome'] = 'FAILURE'; e['invocations'][0]['expected_exit_codes'] = [2]
        e['invocations'][0]['instances'][0]['allowed_outcomes'] = ['FAILURE']
        self.assertTrue(self.consume(inputs(b, e))['finite_expectations_match'])
        e['invocations'][0]['instances'][0]['allowed_outcomes'] = ['SUCCESS']
        out = self.consume(inputs(b, e))
        self.assertEqual(out['failed_instances'], ['INV.1/CASE.1'])
        self.assertEqual(out['verdict'], 'REJECT')


if __name__ == '__main__':
    unittest.main()
