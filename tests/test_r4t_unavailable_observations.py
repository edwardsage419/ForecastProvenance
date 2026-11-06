"""New wire semantics against the actual consumer; reuses D150 software data.

No actual report/profile/run, private keys, signing messages, mocks or suite
discovery. The fixed schema patch is data, applied in memory only for tests.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('_r4t_software_fixtures', ROOT / 'tests/test_r4t_execution_content_v1.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
PACKAGE = ROOT / 'docs/development/mainline-execution-2026-10-09-rev-001/r4t-null-free-observations-2026-10-16-rev-001'


def schema_bytes():
    patch_path = PACKAGE / 'NULL_FREE_SCHEMA_PATCH.json'
    assert patch_path.is_file(), 'Missing null-free schema patch implementation'
    obj = json.loads(base.SCHEMA)
    for op in json.loads(patch_path.read_bytes()):
        keys = [x.replace('~1', '/').replace('~0', '~') for x in op['path'][1:].split('/')]
        parent = obj
        for key in keys[:-1]:
            parent = parent[int(key)] if type(parent) is list else parent[key]
        assert op['op'] in ('add', 'replace')
        key = int(keys[-1]) if type(parent) is list else keys[-1]
        parent[key] = op['value']
    return base.canonical.canonical_json(obj)


def unavailable(reason='NOT_RETAINED'):
    return {'state': 'UNAVAILABLE', 'reason_code': reason}


class UnavailableObservationTests(base.case_events.ObservedCase):
    observation_source_path = 'tests/test_r4t_unavailable_observations.py'
    def consume(self, body=None, expected=None, artifacts=None):
        body0, expected0, artifacts0 = base.fixture()
        raw, controls = base.wire(body0 if body is None else body,
                                  expected0 if expected is None else expected)
        schema = schema_bytes()
        controls['format'] = 'FP_DEV_R4T_EXECUTION_EXPECTED_V2'
        controls['schema_raw_sha256'] = hashlib.sha256(schema).hexdigest()
        args = (controls, raw, schema, artifacts0 if artifacts is None else artifacts)
        before = deepcopy(args)
        result = base.consumer.consume_execution_content(*args)
        self.assertEqual(args, before)
        self.assertEqual(result['real_admission'], 'NOT_READY')
        self.assertEqual(result['protocol_state_change'], 'NONE')
        return result

    def test_missing_output_is_sealed_but_not_completed(self):
        b, e, _ = base.fixture(); b['invocations'][0]['stdout'] = unavailable()
        r = self.consume(b, e)
        self.assertEqual(r['seal_status'], 'VERIFIED')
        self.assertEqual(r['verdict'], 'UNRESOLVED')
        self.assertIn('stdout:INV.1', r['missing_inputs'])
        self.assertEqual(r['unavailable_observations'], [{'invocation_id': 'INV.1',
            'field': 'stdout', 'state': 'UNAVAILABLE', 'reason_code': 'NOT_RETAINED'}])
        self.assertFalse(r['finite_expectations_match'])

    def test_unknown_executable_is_missing_without_false_digest_contradiction(self):
        b, e, _ = base.fixture(); b['invocations'][0]['executable_sha256'] = unavailable('NOT_OBSERVED')
        b['results'][0]['outcome'] = 'FAILURE'
        r = self.consume(b, e)
        self.assertEqual(r['seal_status'], 'VERIFIED')
        self.assertEqual(r['verdict'], 'UNRESOLVED')
        self.assertIn('executable:INV.1', r['missing_inputs'])
        self.assertEqual(r['comparison_errors'], [])
        self.assertEqual(r['failed_instances'], [])
        self.assertFalse(r['observations'][0]['expectation_bound'])

    def test_missing_elapsed_does_not_hide_known_time_reversal(self):
        b, e, _ = base.fixture(); t = b['invocations'][0]['time_observations']
        t['elapsed_monotonic_ns'] = unavailable('CLOCK_UNAVAILABLE')
        t['local_end_utc'] = '2026-10-15T00:00:00Z'
        r = self.consume(b, e)
        self.assertIn('local_time:INV.1', r['missing_inputs'])
        self.assertIn('LOCAL_TIME_ORDER', r['report_errors'])
        self.assertEqual(r['verdict'], 'REJECT')

    def test_not_started_preserves_every_unavailable_observation(self):
        b, e, _ = base.fixture(); inv = b['invocations'][0]
        for field in ('executable_sha256', 'stdout', 'stderr'):
            inv[field] = unavailable('NOT_STARTED')
        inv['time_observations'] = {k: unavailable('NOT_STARTED') for k in inv['time_observations']}
        inv['termination'] = {'state': 'NOT_STARTED', 'reason_code': 'NOT_STARTED'}
        b['run_completion'] = 'INCOMPLETE'; b['results'] = []
        r = self.consume(b, e, {})
        self.assertEqual(r['seal_status'], 'VERIFIED')
        self.assertEqual(r['verdict'], 'UNRESOLVED')
        self.assertEqual(len(r['unavailable_observations']), 6)
        self.assertEqual(r['missing_instances'], ['INV.1/CASE.1'])
        self.assertIn('termination:INV.1', r['missing_inputs'])
        self.assertFalse(r['finite_expectations_match'])

    def test_missing_output_keeps_failed_instance_and_missing_sibling(self):
        b, e, _ = base.fixture(); b['invocations'][0]['stdout'] = unavailable()
        b['results'][0]['outcome'] = 'FAILURE'
        extra = deepcopy(e['invocations'][0]['instances'][0]); extra['instance_id'] = 'CASE.2'
        e['invocations'][0]['instances'].append(extra)
        r = self.consume(b, e, {'software-output': b'wrong'})
        self.assertIn('stdout:INV.1', r['missing_inputs'])
        self.assertIn('RAW_ARTIFACT_MISMATCH', r['report_errors'])
        self.assertEqual(r['failed_instances'], ['INV.1/CASE.1'])
        self.assertEqual(r['missing_instances'], ['INV.1/CASE.2'])
        self.assertEqual(r['verdict'], 'REJECT')

    def test_unknown_marker_must_be_closed_and_carry_a_reason(self):
        for case_key, marker in (
                ('MISSING_REASON', {'state': 'UNAVAILABLE'}),
                ('UNKNOWN_STATE', {'state': 'UNKNOWN', 'reason_code': 'X'}),
                ('EMPTY_REASON', {'state': 'UNAVAILABLE', 'reason_code': ''}),
                ('FOREIGN_ELIGIBLE_FIELD', {'state': 'UNAVAILABLE', 'reason_code': 'X', 'eligible': True})):
            with self.subTest(case_key=case_key, marker=marker):
                b, e, _ = base.fixture(); b['invocations'][0]['stdout'] = marker
                r = self.consume(b, e)
                self.assertIn('REPORT_SHAPE_INVALID', r['report_errors'])
                self.assertFalse(r['finite_expectations_match'])

    def test_wire_and_expected_versions_cannot_be_silently_crossed(self):
        b, e, a = base.fixture(); raw, e = base.wire(b, e); new_schema = schema_bytes()
        r = base.consumer.consume_execution_content(e, raw, new_schema, a)
        self.assertIn('EXPECTED_INVALID', r['comparison_errors'])
        e['format'] = 'FP_DEV_R4T_EXECUTION_EXPECTED_V2'
        e['schema_raw_sha256'] = hashlib.sha256(new_schema).hexdigest()
        self.assertIn('EXPECTED_INVALID', base.consumer.consume_execution_content(e, raw, base.SCHEMA, a)['comparison_errors'])
        er = deepcopy(e); er['schema_raw_sha256'] = 'f' * 64
        self.assertIn('EXPECTED_INVALID', base.consumer.consume_execution_content(er, raw, new_schema, a)['comparison_errors'])
        self.assertIn('SCHEMA_IDENTITY_MISMATCH', base.consumer.consume_execution_content(e, raw, new_schema + b' ', a)['report_errors'])

    def test_complete_known_values_still_only_match_finite_scope(self):
        r = self.consume()
        self.assertTrue(r['finite_expectations_match'])
        self.assertEqual(r['seal_status'], 'VERIFIED')
        self.assertEqual(r['verdict'], 'UNRESOLVED')
        self.assertEqual(r['actual_execution_truth'], 'NOT_VERIFIED')

    def test_real_empty_output_is_distinct_from_unavailable(self):
        b, e, _ = base.fixture()
        b['invocations'][0]['stdout'] = {'artifact_id': 'empty-output',
            'raw_sha256': hashlib.sha256(b'').hexdigest(), 'byte_length': 0}
        r = self.consume(b, e, {'empty-output': b'', 'software-output': b'ok'})
        self.assertTrue(r['finite_expectations_match'])
        self.assertEqual(r['unavailable_observations'], [])

    def test_legacy_schema_does_not_accept_new_markers(self):
        b, e, a = base.fixture(); b['invocations'][0]['stdout'] = unavailable()
        raw, e = base.wire(b, e)
        r = base.consumer.consume_execution_content(e, raw, base.SCHEMA, a)
        self.assertIn('REPORT_SHAPE_INVALID', r['report_errors'])

    def test_marker_reason_cannot_change_under_existing_seal(self):
        b, e, a = base.fixture(); b['invocations'][0]['stdout'] = unavailable()
        raw, e = base.wire(b, e); obj = json.loads(raw)
        obj['invocations'][0]['stdout']['reason_code'] = 'DIFFERENT'
        raw = json.dumps(obj).encode(); e['report_raw_sha256'] = hashlib.sha256(raw).hexdigest()
        schema = schema_bytes(); e.update(format='FP_DEV_R4T_EXECUTION_EXPECTED_V2', schema_raw_sha256=hashlib.sha256(schema).hexdigest())
        r = base.consumer.consume_execution_content(e, raw, schema, a)
        self.assertIn('REPORT_SEAL_INVALID', r['report_errors'])


if __name__ == '__main__':
    base.case_events.main()
