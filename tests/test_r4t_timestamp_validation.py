"""Actual content-entry timestamp regressions using existing keyless fixtures."""
from copy import deepcopy
import hashlib
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('_timestamp_fixture', ROOT / 'tests/test_r4t_unavailable_observations.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)
base = fixtures.base


class TimestampValidationTests(unittest.TestCase):
    def consume(self, start, end=None, *, successor=False, missing_elapsed=False, failure=False):
        body, expected, artifacts = base.fixture()
        times = body['invocations'][0]['time_observations']
        times.update(local_start_utc=start, local_end_utc=start if end is None else end)
        if missing_elapsed: times['elapsed_monotonic_ns'] = fixtures.unavailable('NOT_OBSERVED')
        if failure:
            body['results'][0]['outcome'] = 'FAILURE'
            sibling = deepcopy(expected['invocations'][0]['instances'][0]); sibling['instance_id'] = 'CASE.2'
            expected['invocations'][0]['instances'].append(sibling)
        raw, expected = base.wire(body, expected)
        schema = fixtures.schema_bytes() if successor else base.SCHEMA
        if successor:
            expected.update(format='FP_DEV_R4T_EXECUTION_EXPECTED_V2', schema_raw_sha256=hashlib.sha256(schema).hexdigest())
        args=(expected, raw, schema, artifacts);before=deepcopy(args)
        try: result=base.consumer.consume_execution_content(*args)
        except Exception as exc: self.fail('Actual content entry raised '+type(exc).__name__)
        self.assertEqual(args,before)
        self.assertEqual(result['real_admission'],'NOT_READY')
        self.assertFalse(result['prospective_eligible'])
        self.assertEqual(result['protocol_state_change'],'NONE')
        return result

    # Permissive ISO parsing, unchecked fractions, arbitrary separators and partial forms cannot match.
    def test_malformed_lexical_timestamps_are_rejected_in_both_schemas(self):
        for successor in (False,True):
            for stamp in ('not-a-dateZ','2026-10-17X00:00:00Z','20261017T000000Z',
                          '2026-10-17 00:00:00Z','2026-10-17T00:00Z',
                          '2026-10-17T00:00:00.aZ','2026-10-17T00:00:00.Z',
                          '2026-10-17T00:00:00,5Z','2026-10-17T00:00:00.５Z'):
                with self.subTest(successor=successor,stamp=stamp):
                    r=self.consume(stamp,successor=successor)
                    self.assertEqual(r['verdict'],'REJECT')
                    self.assertIn('LOCAL_TIME_INVALID',r['report_errors'])
                    self.assertFalse(r['finite_expectations_match'])

    def test_calendar_and_clock_ranges_are_checked_for_each_endpoint(self):
        for stamp in ('2026-02-30T00:00:00Z','1900-02-29T00:00:00Z',
                      '2026-00-01T00:00:00Z','2026-13-01T00:00:00Z',
                      '2026-10-00T00:00:00Z','2026-10-17T24:00:00Z',
                      '2026-10-17T00:60:00Z','2026-10-17T00:00:61Z'):
            for endpoint in ('start','end'):
                with self.subTest(stamp=stamp,endpoint=endpoint):
                    r=self.consume(stamp if endpoint=='start' else '2026-01-01T00:00:00Z',
                                   stamp if endpoint=='end' else '2026-12-31T23:59:59Z',successor=True)
                    self.assertIn('LOCAL_TIME_INVALID',r['report_errors'])
                    self.assertEqual(r['verdict'],'REJECT')

    def test_valid_gregorian_boundaries_lowercase_t_and_long_fraction_remain_usable(self):
        for successor in (False,True):
            for stamp in ('0000-02-29T00:00:00Z','0001-01-01T00:00:00Z',
                          '2000-02-29t23:59:59Z','9999-12-31T23:59:59Z',
                          '2026-10-17T00:00:00.'+'0'*5000+'1Z'):
                with self.subTest(successor=successor,stamp=stamp[:35]):
                    r=self.consume(stamp,successor=successor)
                    self.assertTrue(r['finite_expectations_match'])
                    self.assertEqual(r['verdict'],'UNRESOLVED')

    def test_fractional_order_does_not_round_or_require_equal_digit_counts(self):
        r=self.consume('2026-10-17T00:00:00.100000000000000000002Z',
                       '2026-10-17T00:00:00.100000000000000000001Z')
        self.assertIn('LOCAL_TIME_ORDER',r['report_errors'])
        r=self.consume('2026-10-17t00:00:00.100Z','2026-10-17T00:00:00.1Z')
        self.assertNotIn('LOCAL_TIME_ORDER',r['report_errors'])
        self.assertTrue(r['finite_expectations_match'])

    def test_invalid_known_time_is_not_hidden_by_unavailable_other_fields(self):
        r=self.consume(fixtures.unavailable(), '2026-02-30T00:00:00Z', successor=True,missing_elapsed=True)
        self.assertIn('LOCAL_TIME_INVALID',r['report_errors'])
        self.assertIn('local_time:INV.1',r['missing_inputs'])
        self.assertEqual(len(r['unavailable_observations']),2)
        self.assertEqual(r['verdict'],'REJECT')

    def test_potential_leap_second_remains_unverified_without_context(self):
        for stamp in ('1990-12-31T23:59:60Z','2030-01-31T23:59:60.123Z'):
            with self.subTest(stamp=stamp):
                r=self.consume(stamp,successor=True)
                self.assertEqual(r['report_errors'],[])
                self.assertIn('local_time:LEAP_SECOND_CONTEXT:INV.1',r['missing_inputs'])
                self.assertFalse(r['finite_expectations_match'])
                self.assertEqual(r['verdict'],'UNRESOLVED')

    def test_impossible_leap_second_placement_is_invalid(self):
        for stamp in ('1990-12-30T23:59:60Z','1990-12-31T22:59:60Z','1990-12-31T23:58:60Z'):
            with self.subTest(stamp=stamp):
                r=self.consume(stamp)
                self.assertIn('LOCAL_TIME_INVALID',r['report_errors'])
                self.assertEqual(r['verdict'],'REJECT')

    def test_leap_context_missing_preserves_failed_child_and_missing_sibling(self):
        r=self.consume('1990-12-31T23:59:60Z',successor=True,failure=True)
        self.assertEqual(r['failed_instances'],['INV.1/CASE.1'])
        self.assertEqual(r['missing_instances'],['INV.1/CASE.2'])
        self.assertIn('local_time:LEAP_SECOND_CONTEXT:INV.1',r['missing_inputs'])
        self.assertEqual(r['verdict'],'REJECT')


if __name__=='__main__':
    unittest.main(verbosity=2)
