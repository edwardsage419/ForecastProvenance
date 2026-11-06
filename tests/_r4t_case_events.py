"""Test-only local callback observations; no R4T/profile/protocol authority.

JSONL is flushed per real callback. Tracebacks and diagnostic subTest parameters
are deliberately excluded; identities are explicit structured fields. Source
pins, process exit and runtime closure are separate evidence, not inferred here.
"""
import argparse
from contextlib import contextmanager
import json
import importlib.util
from pathlib import Path
import unittest

_core_spec = importlib.util.spec_from_file_location('_r4t_shared_observations',
    Path(__file__).resolve().parents[1] / 'src/forecast_trust_core/unittest_observations_v1.py')
_core = importlib.util.module_from_spec(_core_spec)
_core_spec.loader.exec_module(_core)
_context = _core._context
compare_events = _core.compare_events






class ObservedCase(unittest.TestCase):
    """Keep explicit method/case identity without reading unittest private data."""
    observation_source_path = ''

    def __init__(self, methodName='runTest'):
        super().__init__(methodName)
        self.observation_method_name = methodName
        self.observation_case_keys = []

    @contextmanager
    def subTest(self, msg=None, *, case_key='', **params):
        if type(case_key) is not str or not case_key:
            raise ValueError('Explicit stable case_key required')
        self.observation_case_keys.append(case_key)
        try:
            with super().subTest(msg=msg, case_key=case_key, **params):
                yield
        finally:
            self.observation_case_keys.pop()

    def observation_identity(self, *, child=False):
        return {'test_path': self.observation_source_path,
                'class_name': type(self).__name__, 'method_name': self.observation_method_name,
                'case_keys': list(self.observation_case_keys) if child else []}


class EventResult(unittest.TextTestResult):
    def __init__(self, *args, sink, invocation_id, attempt_index, **kwargs):
        super().__init__(*args, **kwargs)
        _context(invocation_id, attempt_index)
        self.sink = sink
        self.invocation_id = invocation_id
        self.attempt_index = attempt_index
        self.sequence = 0
        self.active_case = None

    def emit(self, event, **fields):
        row = {'sequence': self.sequence, 'event': event,
               'invocation_id': self.invocation_id, 'attempt_index': self.attempt_index, **fields}
        self.sink.write(json.dumps(row, ensure_ascii=True, allow_nan=False, sort_keys=True) + '\n')
        self.sink.flush()
        self.sequence += 1

    def startTestRun(self):
        super().startTestRun()
        self.emit('RUN_START')

    def stopTestRun(self):
        self.emit('RUN_STOP', tests_run=self.testsRun, was_successful=self.wasSuccessful())
        super().stopTestRun()

    def startTest(self, test):
        super().startTest(test)
        self.active_case = test
        self.emit('METHOD_START', identity=test.observation_identity())

    def stopTest(self, test):
        self.emit('METHOD_STOP', identity=test.observation_identity())
        self.active_case = None
        super().stopTest(test)

    def record(self, test, outcome, *, child=False):
        if self.active_case is None:
            self.emit('UNBOUND_RESULT', outcome=outcome)
            return
        if test is not self.active_case:
            child = True  # public addSkip may receive a subtest, not its parent
        self.emit('SUBTEST_RESULT' if child else 'METHOD_RESULT',
                  identity=self.active_case.observation_identity(child=child), outcome=outcome)

    def addSuccess(self, test):
        self.record(test, 'SUCCESS')
        super().addSuccess(test)

    def addFailure(self, test, err):
        self.record(test, 'FAILURE')
        super().addFailure(test, err)

    def addError(self, test, err):
        self.record(test, 'ERROR')
        super().addError(test, err)

    def addSkip(self, test, reason):
        self.record(test, 'SKIP')
        super().addSkip(test, reason)

    def addExpectedFailure(self, test, err):
        self.record(test, 'EXPECTED_FAILURE')
        super().addExpectedFailure(test, err)

    def addUnexpectedSuccess(self, test):
        self.record(test, 'UNEXPECTED_SUCCESS')
        super().addUnexpectedSuccess(test)

    def addSubTest(self, test, subtest, err):
        outcome = 'SUCCESS' if err is None else ('FAILURE' if issubclass(err[0], test.failureException) else 'ERROR')
        self.record(test, outcome, child=True)
        super().addSubTest(test, subtest, err)




def main():
    """Opt-in event output in the existing direct test entry points."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--fp-events')
    parser.add_argument('--fp-invocation')
    parser.add_argument('--fp-attempt', type=int)
    options, remaining = parser.parse_known_args()
    if all(v is None for v in vars(options).values()):
        unittest.main(verbosity=2)
    _context(options.fp_invocation, options.fp_attempt)
    if not options.fp_events:
        raise ValueError('Explicit new event output path required')
    with open(options.fp_events, 'x', encoding='utf-8') as sink:
        unittest.main(argv=['r4t-local-observations', *remaining], verbosity=2,
            testRunner=unittest.TextTestRunner(verbosity=2, resultclass=lambda *a, **k:
                EventResult(*a, sink=sink, invocation_id=options.fp_invocation,
                            attempt_index=options.fp_attempt, **k)))
