"""SYNTHETIC_TEST_ONLY finite typed-check tests; no keys/seals/domain replay.

Direct -B -I -S execution imports only the new stdlib-only library, bypassing
package __init__, conftest, historical consumers and model/native dependencies.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'src/forecast_trust_core/report_check_content_v1.py'
spec = importlib.util.spec_from_file_location('_finite_report_check_tests', SOURCE)
codec = importlib.util.module_from_spec(spec)
spec.loader.exec_module(codec)


def ref(name, digest='a' * 64):
    return {'object_id': 'synthetic-test-only:' + name, 'content_sha256': digest}


def coverage():
    return {'dimension': 'OPERATION', 'member_ref': ref('operation')}


def fixture(count=1):
    catalog = {'format': 'FP_DEV_R6_CHECK_CATALOG_V1', 'scope': 'FINITE_DEVELOPMENT_SCOPE_ONLY',
        'report_kind': 'TRUST_CORE_TEST_REPORT', 'subject_ref': ref('subject'),
        'validator_contract_ref': ref('validator'), 'content_profile_ref': ref('profile'),
        'checks': [{'check_id': f'CHECK.{n}', 'required_support_refs': [ref('support')],
                    'required_coverage': [coverage()]} for n in range(count)]}
    return catalog


def encode(catalog):
    raw = json.dumps(catalog, sort_keys=True, separators=(',', ':')).encode()
    return raw, hashlib.sha256(raw).hexdigest()


def observation(n=0, status='PASS', missing=False):
    return {'check_id': f'CHECK.{n}', 'status': status, 'reason_code': 'SYNTHETIC_TEST_ONLY',
        'support_refs': [] if missing else [ref('support')],
        'coverage': [] if missing else [coverage()], 'blocking_finding_refs': []}


class ReportCheckContentTests(unittest.TestCase):
    def build(self, observations=None, catalog=None):
        raw, pin = encode(fixture() if catalog is None else catalog)
        return raw, pin, codec.build_checks(raw, pin, [observation()] if observations is None else observations)

    def consume(self, raw, pin, rows):
        before = deepcopy(rows)
        result = codec.consume_checks(raw, pin, rows)
        self.assertEqual(rows, before)
        self.assertEqual(result['real_admission'], 'NOT_READY')
        self.assertEqual(result['independently_complete_universe'], 'NOT_ESTABLISHED')
        self.assertFalse(result['prospective_eligible'])
        self.assertEqual(result['protocol_state_change'], 'NONE')
        return result

    def test_positive_content_is_finite_binding_only(self):
        raw, pin, rows = self.build()
        result = self.consume(raw, pin, rows)
        self.assertTrue(result['well_formed_and_bound'])
        for key in ['hard_errors', 'missing_checks', 'missing_inputs', 'missing_coverage', 'failed_checks', 'unknown_checks', 'rejected_observations']:
            self.assertEqual(result[key], [], key)
        self.assertNotIn('overall', result)
        self.assertNotIn('valid', result)

    def test_bound_fail_and_unknown_keep_computed_missing_inputs(self):
        for status, field in [('FAIL', 'failed_checks'), ('UNKNOWN', 'unknown_checks')]:
            with self.subTest(status=status):
                raw, pin, rows = self.build([observation(status=status, missing=True)])
                result = self.consume(raw, pin, rows)
                self.assertTrue(result['well_formed_and_bound'])
                self.assertEqual(result[field], ['CHECK.0'])
                self.assertEqual(result['missing_inputs'], [{'check_id': 'CHECK.0', 'refs': [ref('support')]}])
                self.assertEqual(result['missing_coverage'], [{'check_id': 'CHECK.0', 'members': [coverage()]}])
                self.assertEqual(result['rejected_observations'], [])

    def test_wrong_context_retains_safe_status_and_missing_as_unbound(self):
        for status in ['FAIL', 'UNKNOWN', 'PASS']:
            with self.subTest(status=status):
                raw, pin, rows = self.build([observation(status=status, missing=status != 'PASS')])
                rows[0]['report_context']['subject_ref'] = ref('other-subject')
                result = self.consume(raw, pin, rows)
                self.assertFalse(result['well_formed_and_bound'])
                self.assertEqual(result['hard_errors'], ['0:CONTEXT_MISMATCH'])
                self.assertEqual(result['failed_checks'], [])
                self.assertEqual(result['unknown_checks'], [])
                self.assertEqual(result['missing_inputs'], [])
                self.assertEqual(result.get('rejected_observations', []), [{
                    'row_index': 0, 'check_id': 'CHECK.0', 'reported_status': status,
                    'reported_blocking_finding_refs': [],
                    'local_missing_support_refs': [ref('support')] if status != 'PASS' else [],
                    'local_missing_coverage': [coverage()] if status != 'PASS' else [],
                    'context_bound': False, 'wire_valid': False,
                    'comparison_scope': 'LOCAL_EXPECTED_CATALOG_ONLY', 'reason_code': 'CONTEXT_MISMATCH'}])

    def test_malformed_auxiliary_diagnostics_retain_computed_facts(self):
        for field in ['missing_support_refs', 'missing_coverage']:
            with self.subTest(field=field):
                raw, pin, rows = self.build([observation(status='UNKNOWN', missing=True)])
                rows[0][field] = 'INVALID_SERIALIZED_MISSING'
                result = self.consume(raw, pin, rows)
                self.assertFalse(result['well_formed_and_bound'])
                saved = result['rejected_observations'][0]
                self.assertEqual(saved['reported_status'], 'UNKNOWN')
                self.assertEqual(saved['local_missing_support_refs'], [ref('support')])
                self.assertEqual(saved['local_missing_coverage'], [coverage()])
                self.assertTrue(saved['context_bound'])
                self.assertFalse(saved['wire_valid'])
                self.assertEqual(saved['reason_code'], 'SET_SIZE_OR_TYPE')
                self.assertNotIn('INVALID_SERIALIZED_MISSING', repr(saved))

    def test_context_validation_failure_never_enters_bound_status_lists(self):
        for field, value in [('catalog_raw_sha256', 'b' * 64), ('report_kind', 'PROVIDER_REHEARSAL_REPORT'),
                ('stage', 'G7'), ('content_profile_ref', ref('wrong-profile')),
                ('validator_contract_ref', ref('wrong-validator'))]:
            with self.subTest(field=field):
                raw, pin, rows = self.build([observation(status='FAIL', missing=True)])
                rows[0]['report_context'][field] = value
                result = self.consume(raw, pin, rows)
                self.assertEqual(result['failed_checks'], [])
                self.assertFalse(result['rejected_observations'][0]['context_bound'])
                self.assertEqual(result['rejected_observations'][0]['reported_status'], 'FAIL')

    def test_malformed_observation_is_not_retained_as_validated_data(self):
        for field, value in [('check_id', 'UNDECLARED'), ('status', 'FORGED_STATUS'),
                             ('support_refs', [ref('undeclared')]), ('coverage', [{'dimension': 'OTHER', 'member_ref': ref('operation')}])]:
            with self.subTest(field=field):
                raw, pin, rows = self.build()
                rows[0][field] = value
                result = self.consume(raw, pin, rows)
                self.assertFalse(result['well_formed_and_bound'])
                self.assertEqual(result['rejected_observations'], [])
                self.assertEqual(result['failed_checks'], [])

    def test_false_missing_diagnostic_does_not_override_recomputation(self):
        raw, pin, rows = self.build([observation(status='FAIL', missing=True)])
        rows[0]['missing_support_refs'] = []
        rows[0]['missing_coverage'] = []
        result = self.consume(raw, pin, rows)
        self.assertFalse(result['well_formed_and_bound'])
        self.assertEqual(result['hard_errors'], ['0:MISSING_DIAGNOSTIC_MISMATCH'])
        self.assertEqual(result['failed_checks'], ['CHECK.0'])
        self.assertEqual(result['missing_inputs'], [{'check_id': 'CHECK.0', 'refs': [ref('support')]}])

    def test_rejected_row_does_not_suppress_later_bound_sibling(self):
        raw, pin, rows = self.build([observation(0, 'UNKNOWN', True), observation(1, 'FAIL', True)], fixture(2))
        rows[0]['report_context']['stage'] = 'WRONG_STAGE'
        result = self.consume(raw, pin, rows)
        self.assertEqual(result['failed_checks'], ['CHECK.1'])
        self.assertEqual(result['unknown_checks'], [])
        self.assertEqual([r['check_id'] for r in result['missing_inputs']], ['CHECK.1'])
        self.assertEqual([r['check_id'] for r in result['rejected_observations']], ['CHECK.0'])
        self.assertEqual(result['missing_checks'], [])
        self.assertFalse(result['well_formed_and_bound'])

    def test_retained_rejected_diagnostics_are_deep_copies(self):
        raw, pin, rows = self.build([observation(status='FAIL', missing=True)])
        rows[0]['blocking_finding_refs'] = [ref('reported-blocker')]
        rows[0]['report_context']['stage'] = 'WRONG_STAGE'
        result = self.consume(raw, pin, rows)
        rows[0]['blocking_finding_refs'][0]['object_id'] = 'synthetic-test-only:mutated'
        rows[0]['missing_support_refs'][0]['object_id'] = 'synthetic-test-only:mutated'
        saved = result['rejected_observations'][0]
        self.assertEqual(saved['reported_blocking_finding_refs'], [ref('reported-blocker')])
        self.assertEqual(saved['local_missing_support_refs'], [ref('support')])

    def test_unknown_wire_fields_do_not_leak_into_diagnostics(self):
        raw, pin, rows = self.build([observation(status='FAIL', missing=True)])
        rows[0]['UNTRUSTED_EXTRA'] = 'DO_NOT_RETAIN_THIS_VALUE'
        result = self.consume(raw, pin, rows)
        self.assertFalse(result['well_formed_and_bound'])
        self.assertEqual(result['rejected_observations'], [])
        self.assertNotIn('DO_NOT_RETAIN_THIS_VALUE', repr(result))

    def test_catalog_identity_closed_fields_and_scope_are_enforced(self):
        raw, pin, _ = self.build()
        with self.assertRaises(codec.ContentError):
            codec.consume_checks(raw + b' ', pin, [])
        for field, value in [('scope', 'ACTUAL_ADOPT'), ('report_kind', 'OTHER'), ('unexpected', 'bad')]:
            catalog = fixture(); catalog[field] = value
            bad, digest = encode(catalog)
            with self.subTest(field=field), self.assertRaises(codec.ContentError):
                codec.consume_checks(bad, digest, [])
        with self.assertRaises(codec.ContentError):
            raw = b'{"format":"a","format":"b"}'
            codec.consume_checks(raw, hashlib.sha256(raw).hexdigest(), [])

    def test_four_kinds_reuse_one_content_contract_without_authority(self):
        for kind in ['TRUST_CORE_TEST_REPORT', 'GENESIS_ADVERSARIAL_REPORT', 'PROVIDER_REHEARSAL_REPORT', 'TARGET_SOURCE_PARSER_REPORT']:
            catalog = fixture(); catalog['report_kind'] = kind
            raw, pin, rows = self.build(catalog=catalog)
            self.assertEqual(rows[0]['report_context']['report_kind'], kind)
            self.assertTrue(self.consume(raw, pin, rows)['well_formed_and_bound'])
        catalog = fixture(); catalog['report_kind'] = 'OTS_BITCOIN_STRONG_VERIFICATION_REPORT'
        raw, pin = encode(catalog)
        with self.assertRaises(codec.ContentError):
            codec.build_checks(raw, pin, [observation()])

    def test_omission_duplicate_order_and_pass_missing_remain_rejected(self):
        raw, pin, rows = self.build([observation(0), observation(1)], fixture(2))
        for bad in [rows[:1], [rows[0], rows[0]], list(reversed(rows)), 'bad']:
            with self.subTest(bad=bad):
                result = self.consume(raw, pin, bad)
                self.assertFalse(result['well_formed_and_bound'])
                self.assertIn('CHECK_SET_OR_ORDER_MISMATCH', result['hard_errors'])
        raw, pin = encode(fixture())
        with self.assertRaises(codec.ContentError):
            codec.build_checks(raw, pin, [observation(missing=True)])
        blocked = observation(); blocked['blocking_finding_refs'] = [ref('blocker')]
        with self.assertRaises(codec.ContentError):
            codec.build_checks(raw, pin, [blocked])


if __name__ == '__main__':
    unittest.main()
