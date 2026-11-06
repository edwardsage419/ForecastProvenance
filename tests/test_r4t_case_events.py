"""Behavioral checks for the test-only event boundary, using real unittest calls."""
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import unittest

HELPER = Path(__file__).with_name('_r4t_case_events.py')


def load_helper():
    if not HELPER.is_file():
        return None
    spec = importlib.util.spec_from_file_location('_case_events_under_test', HELPER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class EventCaptureTests(unittest.TestCase):
    def setUp(self):
        self.api = load_helper()
        self.assertIsNotNone(self.api, 'Missing stable-key real-event collector')

    def capture(self, behavior, *, failfast=False):
        class Example(self.api.ObservedCase):
            observation_source_path = 'tests/public-example.py'
            def test_case(self):
                behavior(self)
        sink = io.StringIO()
        runner = unittest.TextTestRunner(stream=io.StringIO(), failfast=failfast,
            resultclass=lambda *a, **k: self.api.EventResult(*a, sink=sink,
                invocation_id='PUBLIC.INV', attempt_index=1, **k))
        result = runner.run(unittest.TestSuite([Example('test_case')]))
        events = [json.loads(line) for line in sink.getvalue().splitlines()]
        return result, events

    def expected(self):
        return [{'test_path': 'tests/public-example.py', 'class_name': 'Example',
                 'method_name': 'test_case', 'case_keys': keys}
                for keys in ([], ['A'], ['B'])]

    def compare(self, events):
        return self.api.compare_events(self.expected(), events, 'PUBLIC.INV', 1)

    def success(self, test):
        for key in ('A', 'B'):
            with test.subTest(case_key=key, diagnostic='same-prefix'):
                test.assertTrue(True)

    # Dropping successful subcallbacks, inferring parent success or flattening keys breaks this.
    def test_real_success_events_keep_parent_and_children_separate(self):
        result, events = self.capture(self.success)
        self.assertTrue(result.wasSuccessful())
        rows = [e for e in events if e['event'].endswith('_RESULT')]
        self.assertEqual([(r['event'], r['identity']['case_keys'], r['outcome'])
                          for r in rows], [('SUBTEST_RESULT', ['A'], 'SUCCESS'),
                          ('SUBTEST_RESULT', ['B'], 'SUCCESS'), ('METHOD_RESULT', [], 'SUCCESS')])
        self.assertTrue(self.compare(events)['finite_observations_match'])
        self.assertEqual(self.compare(events)['real_admission'], 'NOT_READY')

    # A child failure does not grant a missing parent or omitted sibling a result.
    def test_failfast_retains_failed_child_missing_parent_and_sibling(self):
        def failure(t):
            with t.subTest(case_key='A'):
                t.fail('public intentional fixture failure')
            with t.subTest(case_key='B'):
                t.assertTrue(True)
        result, events = self.capture(failure, failfast=True)
        self.assertFalse(result.wasSuccessful())
        report = self.compare(events)
        self.assertEqual([r['case_keys'] for r in report['failed']], [['A']])
        self.assertEqual([r['case_keys'] for r in report['missing']], [[], ['B']])
        self.assertFalse(report['finite_observations_match'])

    def test_skip_error_and_missing_case_key_cannot_be_success(self):
        def skip(t):
            with t.subTest(case_key='A'):
                t.skipTest('public fixture skip')
            with t.subTest(case_key='B'):
                raise RuntimeError('public fixture error')
        _, events = self.capture(skip)
        self.assertEqual([e['outcome'] for e in events if e['event']=='SUBTEST_RESULT'], ['SKIP', 'ERROR'])
        self.assertFalse(self.compare(events)['finite_observations_match'])
        def unkeyed(t):
            with t.subTest(diagnostic='A'):
                t.assertTrue(True)
        _, events = self.capture(unkeyed)
        self.assertEqual([e['outcome'] for e in events if e['event']=='METHOD_RESULT'], ['ERROR'])
        self.assertEqual(len(self.compare(events)['missing']), 2)

    # Equal counts, wrong attempt, or a valid parent cannot fill a missing child.
    def test_omission_duplicate_substitution_and_attempt_contamination_fail(self):
        _, original = self.capture(self.success)
        child = next(i for i, e in enumerate(original) if e['event']=='SUBTEST_RESULT')
        for change in ('omit', 'duplicate', 'foreign', 'attempt', 'parent', 'outcome', 'truncated'):
            with self.subTest(change=change):
                events = deepcopy(original)
                if change == 'omit': events.pop(child)
                if change == 'duplicate': events.insert(child, deepcopy(events[child]))
                if change == 'foreign': events[child]['identity']['case_keys']=['FOREIGN']
                if change == 'attempt': events[child]['attempt_index']=2
                if change == 'parent': events[child]['identity']['method_name']='other_method'
                if change == 'outcome': events[child]['outcome']='UNKNOWN'
                if change == 'truncated': events.pop()
                self.assertFalse(self.compare(events)['finite_observations_match'])

    def test_duplicate_expected_identity_and_invalid_context_are_rejected(self):
        _, events = self.capture(self.success)
        expected = self.expected(); expected.append(deepcopy(expected[0]))
        with self.assertRaises(ValueError):
            self.api.compare_events(expected, events, 'PUBLIC.INV', 1)
        for attempt in (True, 0, -1):
            with self.assertRaises(ValueError):
                self.api.compare_events(self.expected(), events, 'PUBLIC.INV', attempt)

    def test_nested_case_keys_remain_structured(self):
        def nested(t):
            with t.subTest(case_key='A/B'):
                with t.subTest(case_key='C'):
                    t.assertTrue(True)
        _, events = self.capture(nested)
        self.assertEqual([e['identity']['case_keys'] for e in events if e['event']=='SUBTEST_RESULT'],
                         [['A/B', 'C'], ['A/B']])
        self.assertFalse(self.compare(events)['finite_observations_match'])

    def test_extra_or_repeated_empty_method_lifecycle_cannot_hide(self):
        _, original = self.capture(self.success)
        for foreign in (False, True):
            with self.subTest(foreign=foreign):
                events = deepcopy(original)
                start = deepcopy(next(e for e in events if e['event']=='METHOD_START'))
                stop = deepcopy(next(e for e in events if e['event']=='METHOD_STOP'))
                if foreign:
                    start['identity']['method_name'] = stop['identity']['method_name'] = 'FOREIGN'
                events[-1:-1] = [start, stop]
                events[-1]['tests_run'] = 2
                for seq, event in enumerate(events): event['sequence'] = seq
                self.assertFalse(self.compare(events)['finite_observations_match'])

    def test_malformed_result_is_reported_missing_without_crashing(self):
        _, events = self.capture(self.success)
        row = next(e for e in events if e['event']=='SUBTEST_RESULT')
        del row['outcome']
        report = self.compare(events)
        self.assertFalse(report['finite_observations_match'])
        self.assertIn('EVENT_SHAPE_OR_SEQUENCE', report['errors'])
        self.assertEqual([r['case_keys'] for r in report['missing']], [['A']])


if __name__ == '__main__':
    unittest.main(verbosity=2)
