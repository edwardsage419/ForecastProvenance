"""Bounded public byte API checks; no protocol refs, signing or broad discovery."""
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('_local_content_base', ROOT / 'tests/test_r4t_execution_content_v1.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def fixture(*, failing=False):
    class PublicExample(base.case_events.ObservedCase):
        observation_source_path = 'public/local-example.py'
        def test_example(self):
            for key in ('A', 'B'):
                with self.subTest(case_key=key):
                    if failing and key == 'A': self.fail('intentional public failure')
                    self.assertTrue(True)
    sink = io.StringIO()
    unittest.TextTestRunner(stream=io.StringIO(), failfast=failing,
        resultclass=lambda *a, **k: base.case_events.EventResult(*a, sink=sink,
            invocation_id='LOCAL.1', attempt_index=1, **k)).run(
                unittest.TestSuite([PublicExample('test_example')]))
    raw = sink.getvalue().encode()
    expected = {'format': 'FP_DEV_UNITTEST_OBSERVATION_EXPECTED_V1',
        'scope': 'FINITE_LOCAL_UNITTEST_OBSERVATIONS_ONLY',
        'invocation_id': 'LOCAL.1', 'attempt_index': 1,
        'events_raw_sha256': hashlib.sha256(raw).hexdigest(),
        'expected_exit_codes': [0],
        'identities': [{'test_path': 'public/local-example.py', 'class_name': 'PublicExample',
            'method_name': 'test_example', 'case_keys': keys} for keys in ([], ['A'], ['B'])]}
    run = {'invocation_id': 'LOCAL.1', 'attempt_index': 1,
        'events_raw_sha256': expected['events_raw_sha256'],
        'termination': {'state': 'EXITED', 'exit_code': 1 if failing else 0}}
    return expected, raw, run


class LocalObservationContentTests(unittest.TestCase):
    def setUp(self):
        self.api = getattr(base.consumer, 'consume_local_unittest_content', None)
        self.assertTrue(callable(self.api), 'Missing local byte consumer entry')

    def consume(self, e, raw, run):
        before = deepcopy((e, raw, run)); result = self.api(e, raw, run)
        self.assertEqual((e, raw, run), before)
        self.assertEqual(result['real_admission'], 'NOT_READY')
        self.assertEqual(result['protocol_state_change'], 'NONE')
        self.assertFalse(result['prospective_eligible'])
        return result

    # Replacing actual callback comparison with a boolean, shape check or formal PASS fails.
    def test_actual_callbacks_match_only_the_supplied_local_scope(self):
        e, raw, run = fixture(); r = self.consume(e, raw, run)
        self.assertTrue(r['local_event_consistency_match'])
        self.assertEqual(r['verdict'], 'UNRESOLVED')
        self.assertEqual(r['actual_execution_truth'], 'NOT_VERIFIED')
        self.assertEqual(r['event_comparison']['missing'], [])

    def test_failure_and_missing_are_retained_with_unexpected_exit(self):
        e, raw, run = fixture(failing=True); r = self.consume(e, raw, run)
        self.assertFalse(r['local_event_consistency_match'])
        self.assertEqual(r['verdict'], 'REJECT')
        self.assertIn('EXIT_CODE_MISMATCH', r['comparison_errors'])
        self.assertEqual([x['case_keys'] for x in r['event_comparison']['failed']], [['A']])
        self.assertEqual([x['case_keys'] for x in r['event_comparison']['missing']], [[], ['B']])

    def test_missing_inputs_stay_unresolved(self):
        r = self.consume(None, None, None)
        self.assertEqual(set(r['missing_inputs']), {'expected', 'events', 'run_observation'})
        self.assertEqual(r['verdict'], 'UNRESOLVED')
        self.assertFalse(r['local_event_consistency_match'])

    def test_digest_and_run_context_do_not_cross_attempts(self):
        for change in ('digest', 'attempt', 'invocation', 'event_digest'):
            with self.subTest(change=change):
                e, raw, run = fixture()
                if change == 'digest': e['events_raw_sha256']='f'*64
                if change == 'attempt': run['attempt_index']=2
                if change == 'invocation': run['invocation_id']='FOREIGN'
                if change == 'event_digest': run['events_raw_sha256']='e'*64
                r = self.consume(e, raw, run)
                self.assertFalse(r['local_event_consistency_match'])
                self.assertEqual(r['verdict'], 'REJECT')

    def test_unavailable_termination_does_not_erase_event_failure(self):
        e, raw, run = fixture(failing=True)
        run['termination']={'state': 'UNKNOWN', 'reason_code': 'NOT_RETAINED'}
        r = self.consume(e, raw, run)
        self.assertIn('termination', r['missing_inputs'])
        self.assertEqual([x['case_keys'] for x in r['event_comparison']['failed']], [['A']])
        self.assertFalse(r['local_event_consistency_match'])

    def test_wire_is_strict_and_bounded(self):
        for data in (b'\xef\xbb\xbf{}\n', b'{"x":1,"x":2}\n', b'{"x":-0}\n',
                     b'{"x":NaN}\n', b'{"x":1.2}\n', b'{}\n\n{}\n', b'\xff'):
            with self.subTest(data=data):
                e, _, run = fixture(); e['events_raw_sha256']=hashlib.sha256(data).hexdigest()
                run['events_raw_sha256']=e['events_raw_sha256']
                r = self.consume(e, data, run)
                self.assertEqual(r['verdict'], 'REJECT')
                self.assertFalse(r['local_event_consistency_match'])
        e, _, run = fixture(); data=b' '*(base.consumer.BYTE_LIMIT+1)
        e['events_raw_sha256']=hashlib.sha256(data).hexdigest();run['events_raw_sha256']=e['events_raw_sha256']
        r = self.consume(e, data, run)
        self.assertIn('events:LOCAL_BYTE_LIMIT', r['missing_inputs'])
        self.assertEqual(r['verdict'], 'UNRESOLVED')

    def test_non_string_event_and_missing_outcome_produce_diagnostics(self):
        for change in ('event_type', 'outcome', 'case_shape'):
            with self.subTest(change=change):
                e, raw, run = fixture(); rows=[json.loads(x) for x in raw.splitlines()]
                row=next(r for r in rows if r['event']=='SUBTEST_RESULT')
                if change=='event_type': row['event']=[]
                if change=='outcome': del row['outcome']
                if change=='case_shape': row['identity']['case_keys']=None
                raw=b''.join(json.dumps(x).encode()+b'\n' for x in rows)
                e['events_raw_sha256']=hashlib.sha256(raw).hexdigest();run['events_raw_sha256']=e['events_raw_sha256']
                r=self.consume(e, raw, run)
                self.assertEqual(r['verdict'], 'REJECT')
                self.assertFalse(r['local_event_consistency_match'])

    def test_controls_are_closed_and_nonempty_without_fake_authority(self):
        for change in ('foreign', 'empty', 'duplicate', 'format', 'attempt', 'exit', 'orphan'):
            with self.subTest(change=change):
                e, raw, run=fixture()
                if change=='foreign': e['eligible']=True
                if change=='empty': e['identities']=[]
                if change=='duplicate': e['identities'].append(deepcopy(e['identities'][0]))
                if change=='format': e['format']='FP_DEV_R4T_EXECUTION_EXPECTED_V2'
                if change=='attempt': e['attempt_index']=True
                if change=='exit': e['expected_exit_codes']=[True]
                if change=='orphan': e['identities'].pop(0)
                r=self.consume(e, raw, run)
                self.assertIn('EXPECTED_INVALID', r['comparison_errors'])
                self.assertFalse(r['local_event_consistency_match'])

    def test_shared_comparator_still_retains_exact_multiplicity(self):
        e, raw, run=fixture();rows=[json.loads(x) for x in raw.splitlines()]
        child=next(i for i,r in enumerate(rows) if r['event']=='SUBTEST_RESULT')
        rows.insert(child,deepcopy(rows[child]))
        for index,row in enumerate(rows):row['sequence']=index
        raw=b''.join(json.dumps(x).encode()+b'\n' for x in rows)
        e['events_raw_sha256']=hashlib.sha256(raw).hexdigest();run['events_raw_sha256']=e['events_raw_sha256']
        r=self.consume(e,raw,run)
        self.assertEqual(r['event_comparison']['duplicate'],[e['identities'][1]])
        self.assertFalse(r['local_event_consistency_match'])

    def test_local_records_do_not_enter_the_formal_report_path(self):
        e, raw, _ = fixture()
        r = base.consumer.consume_execution_content(e, raw, base.SCHEMA, {})
        self.assertFalse(r['finite_expectations_match'])
        self.assertIn('EXPECTED_INVALID', r['comparison_errors'])
        self.assertEqual(r['real_admission'], 'NOT_READY')
        self.assertEqual(r['protocol_state_change'], 'NONE')


if __name__ == '__main__':
    unittest.main(verbosity=2)
