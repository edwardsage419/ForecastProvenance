"""Keyless finite software data; no actual run/profile or signing message.

Direct -B -I execution loads canonical + actual new consumer, and the existing
installed JSON Schema library. No package init, conftest, old suite or mocks.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[1]
event_spec = importlib.util.spec_from_file_location('_r4t_event_hooks', ROOT / 'tests/_r4t_case_events.py')
case_events = importlib.util.module_from_spec(event_spec)
event_spec.loader.exec_module(case_events)
SOURCE = ROOT / 'src/forecast_trust_core'
PACKAGE = '_finite_r4t_content_tests'
package = types.ModuleType(PACKAGE)
package.__path__ = [str(SOURCE)]
sys.modules[PACKAGE] = package


def load(name):
    spec = importlib.util.spec_from_file_location(PACKAGE + '.' + name, SOURCE / (name + '.py'))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


canonical = load('canonical')
consumer = load('r4t_execution_content_v1')
SCHEMA = (ROOT / 'docs/development/mainline-execution-2026-10-09-rev-001/'
    'r4t-record-format-and-inventory-2026-10-16-rev-001/'
    'development_test_run_report_v1.candidate.schema.json').read_bytes()


def ref(name):
    return {'object_id': 'synthetic-test-only:' + name, 'content_sha256': 'a' * 64}


def fixture():
    binding = {k: ref(k) for k in ('test_definition_ref', 'runtime_profile_ref',
        'content_profile_ref', 'source_file_manifest_ref', 'package_artifact_ref', 'dependency_lock_ref')}
    binding['component_contract_refs'] = [ref('component')]
    artifact = {'artifact_id': 'software-output', 'raw_sha256': hashlib.sha256(b'ok').hexdigest(), 'byte_length': 2}
    invocation = {'invocation_id': 'INV.1', 'ordinal': 0, 'command_id': 'CMD.1', 'attempt_index': 1,
        'argv': ['python', '', 'same', 'same'], 'cwd': 'synthetic-test-only', 'environment': [],
        'executable_sha256': 'b' * 64, 'loaded_source_bindings': [],
        'termination': {'state': 'EXITED', 'exit_code': 0},
        'time_observations': {'local_start_utc': '2026-10-16T00:00:00Z',
            'local_end_utc': '2026-10-16T00:00:01Z', 'elapsed_monotonic_ns': 1000000000},
        'stdout': deepcopy(artifact), 'stderr': deepcopy(artifact)}
    row = {'instance_id': 'CASE.1', 'invocation_id': 'INV.1', 'check_id': 'CHECK.1',
        'operation_id': 'OP.1', 'fixture_refs': [ref('fixture')], 'outcome': 'SUCCESS',
        'reason_codes': [], 'support_refs': [], 'finding_refs': []}
    body = {**binding, 'schema_version': '1.0', 'test_definition_raw_sha256': 'c' * 64,
        'run_id': 'SYNTHETIC_TEST_ONLY', 'run_completion': 'COMPLETE', 'invocations': [invocation],
        'results': [row], 'unavailable_evidence': [], 'finding_refs': []}
    expected_inv = {k: deepcopy(invocation[k]) for k in ('invocation_id', 'command_id', 'attempt_index',
        'argv', 'cwd', 'environment', 'executable_sha256', 'loaded_source_bindings')}
    expected_inv.update(expected_exit_codes=[0], instances=[{k: deepcopy(row[k])
        for k in ('instance_id', 'check_id', 'operation_id', 'fixture_refs')}])
    expected_inv['instances'][0]['allowed_outcomes'] = ['SUCCESS']
    expected = {'format': 'FP_DEV_R4T_EXECUTION_EXPECTED_V1', 'scope': 'FINITE_DEVELOPMENT_SCOPE_ONLY',
        'report_ref': ref('temporary'), 'report_raw_sha256': 'd' * 64, 'bindings': binding,
        'test_definition_raw_sha256': 'c' * 64, 'run_id': 'SYNTHETIC_TEST_ONLY', 'invocations': [expected_inv]}
    return body, expected, {'software-output': b'ok'}


def wire(body, expected):
    report = canonical.seal_object(body, object_type='DevelopmentTestRunReport', stable_context='SYNTHETIC_TEST_ONLY')
    raw = canonical.canonical_json(report)
    expected = deepcopy(expected)
    expected['report_ref'] = {k: report[k] for k in ('object_id', 'content_sha256')}
    expected['report_raw_sha256'] = hashlib.sha256(raw).hexdigest()
    return raw, expected


class R4TExecutionContentTests(case_events.ObservedCase):
    observation_source_path = 'tests/test_r4t_execution_content_v1.py'
    def consume(self, body=None, expected=None, artifacts=None):
        b, e, a = fixture()
        raw, e = wire(b if body is None else body, e if expected is None else expected)
        args = (e, raw, SCHEMA, a if artifacts is None else artifacts)
        before = deepcopy(args)
        result = consumer.consume_execution_content(*args)
        self.assertEqual(args, before)
        self.assertEqual(result['real_admission'], 'NOT_READY')
        self.assertEqual(result['protocol_state_change'], 'NONE')
        self.assertEqual(result['independently_complete_universe'], 'NOT_ESTABLISHED')
        return result

    def test_exact_content_matches_only_finite_expectations(self):
        r = self.consume()
        self.assertTrue(r['finite_expectations_match'])
        self.assertEqual(r['seal_status'], 'VERIFIED')
        self.assertEqual(r['verdict'], 'UNRESOLVED')
        self.assertEqual(r['observations'][0]['outcome'], 'SUCCESS')

    def test_negative_exit_is_checked_against_fixed_expectation(self):
        b, e, _ = fixture()
        b['invocations'][0]['termination']['exit_code'] = 2
        b['results'][0]['outcome'] = 'FAILURE'
        e['invocations'][0]['expected_exit_codes'] = [2]
        e['invocations'][0]['instances'][0]['allowed_outcomes'] = ['FAILURE']
        self.assertTrue(self.consume(b, e)['finite_expectations_match'])
        r = self.consume(b)
        self.assertIn('EXIT_CODE_MISMATCH', r['comparison_errors'])
        self.assertEqual(r['failed_instances'], [])
        self.assertFalse(r['observations'][0]['expectation_bound'])
        e['invocations'][0]['instances'][0]['allowed_outcomes'] = ['SUCCESS']
        self.assertEqual(self.consume(b, e)['failed_instances'], ['INV.1/CASE.1'])

    def test_failure_and_missing_sibling_are_both_retained(self):
        b, e, _ = fixture()
        extra = deepcopy(e['invocations'][0]['instances'][0]); extra['instance_id'] = 'CASE.2'
        e['invocations'][0]['instances'].append(extra)
        b['results'][0]['outcome'] = 'FAILURE'
        r = self.consume(b, e)
        self.assertEqual(r['failed_instances'], ['INV.1/CASE.1'])
        self.assertEqual(r['missing_instances'], ['INV.1/CASE.2'])
        self.assertEqual(r['verdict'], 'REJECT')

    def test_wrong_invocation_or_ambiguous_result_cannot_attribute_failure(self):
        for change in ('argv', 'attempt', 'exit', 'absent', 'duplicate_inv', 'duplicate_result'):
            with self.subTest(case_key=change, change=change):
                b, e, _ = fixture()
                b['results'][0]['outcome'] = 'FAILURE'
                if change == 'argv':
                    b['invocations'][0]['argv'].append('wrong-subject')
                elif change == 'attempt':
                    b['invocations'][0]['attempt_index'] = 2
                elif change == 'exit':
                    b['invocations'][0]['termination']['exit_code'] = 99
                elif change == 'absent':
                    b['invocations'] = []
                elif change == 'duplicate_inv':
                    b['invocations'].append(deepcopy(b['invocations'][0]))
                else:
                    b['results'].append(deepcopy(b['results'][0]))
                r = self.consume(b, e)
                self.assertEqual(r['verdict'], 'REJECT')
                self.assertFalse(any(x['expectation_bound'] for x in r['observations']))
                self.assertEqual(r['failed_instances'], [])

    def test_skip_never_becomes_executed_success(self):
        b, e, _ = fixture(); b['results'][0]['outcome'] = 'SKIPPED'
        e['invocations'][0]['instances'][0]['allowed_outcomes'] = ['SKIPPED']
        r = self.consume(b, e)
        self.assertEqual(r['unknown_instances'], ['INV.1/CASE.1'])
        self.assertFalse(r['finite_expectations_match'])

    def test_instance_diagnostic_labels_preserve_distinct_pairs(self):
        b, e, _ = fixture()
        first = b['invocations'][0]; first['invocation_id'] = 'A/B'
        efirst = e['invocations'][0]; efirst['invocation_id'] = 'A/B'
        b['results'][0].update(invocation_id='A/B', instance_id='C', outcome='FAILURE')
        efirst['instances'][0]['instance_id'] = 'C'
        second = deepcopy(first); second.update(invocation_id='A', ordinal=1)
        esecond = deepcopy(efirst); esecond['invocation_id'] = 'A'
        esecond['instances'][0]['instance_id'] = 'B/C'
        b['invocations'].append(second); e['invocations'].append(esecond)
        other = deepcopy(b['results'][0]); other.update(invocation_id='A', instance_id='B/C')
        b['results'].append(other)
        r = self.consume(b, e)
        self.assertEqual(r['failed_instances'], ['A~1B/C', 'A/B~1C'])

    def test_submicrosecond_local_time_reversal_is_retained(self):
        b, e, _ = fixture()
        b['invocations'][0]['time_observations'].update(
            local_start_utc='2026-10-16T00:00:00.000000002Z',
            local_end_utc='2026-10-16T00:00:00.000000001Z')
        r = self.consume(b, e)
        self.assertIn('LOCAL_TIME_ORDER', r['report_errors'])
        self.assertFalse(r['finite_expectations_match'])

    def test_missing_output_and_wrong_output_are_distinct(self):
        b, e, _ = fixture(); b['invocations'][0]['stderr']['artifact_id'] = 'absent'
        r = self.consume(b, e, {'software-output': b'wrong'})
        self.assertIn('RAW_ARTIFACT_MISMATCH', r['report_errors'])
        self.assertIn('artifact:absent', r['missing_inputs'])

    def test_null_content_keeps_diagnostics_without_new_canonicalization(self):
        b, e, _ = fixture(); raw, e = wire(b, e); report = json.loads(raw)
        report['invocations'][0]['stdout'] = None
        raw = json.dumps(report).encode(); e['report_raw_sha256'] = hashlib.sha256(raw).hexdigest()
        r = consumer.consume_execution_content(e, raw, SCHEMA, {'software-output': b'ok'})
        self.assertEqual(r['seal_status'], 'NOT_ESTABLISHED_NULL_UNSUPPORTED')
        self.assertIn('stdout:INV.1', r['missing_inputs'])
        self.assertFalse(r['observations'][0]['expectation_bound'])
        self.assertFalse(r['finite_expectations_match'])

    def test_wrong_root_context_does_not_attribute_claimed_failure(self):
        b, e, _ = fixture(); b['results'][0]['outcome'] = 'FAILURE'
        e['bindings']['runtime_profile_ref'] = ref('other-runtime')
        r = self.consume(b, e)
        self.assertIn('ROOT_BINDING_MISMATCH', r['comparison_errors'])
        self.assertEqual(r['failed_instances'], [])
        self.assertFalse(r['observations'][0]['expectation_bound'])

    def test_invocation_order_repetition_and_exact_argv_are_checked(self):
        for change in ('ordinal', 'duplicate', 'argv', 'attempt', 'environment', 'loaded'):
            with self.subTest(case_key=change, change=change):
                b, e, _ = fixture()
                if change == 'ordinal': b['invocations'][0]['ordinal'] = 1
                if change == 'duplicate': b['invocations'].append(deepcopy(b['invocations'][0]))
                if change == 'argv': b['invocations'][0]['argv'].pop()
                if change == 'attempt': b['invocations'][0]['attempt_index'] = 2
                if change == 'environment': b['invocations'][0]['environment'] = [{'name': 'PUBLIC', 'value': 'different'}]
                if change == 'loaded': b['invocations'][0]['loaded_source_bindings'] = [{'source_unit_ref': ref('other-source'), 'raw_sha256': 'e' * 64}]
                r = self.consume(b, e)
                self.assertEqual(r['verdict'], 'REJECT')
                self.assertFalse(r['finite_expectations_match'])

    def test_instance_omission_duplicate_and_substitution_are_checked(self):
        for change in ('empty', 'duplicate', 'foreign', 'check', 'operation', 'fixture'):
            with self.subTest(case_key=change, change=change):
                b, e, _ = fixture()
                if change == 'empty': b['results'] = []
                if change == 'duplicate': b['results'].append(deepcopy(b['results'][0]))
                if change == 'foreign': b['results'][0]['invocation_id'] = 'FOREIGN'
                if change == 'check': b['results'][0]['check_id'] = 'OTHER'
                if change == 'operation': b['results'][0]['operation_id'] = 'OTHER'
                if change == 'fixture': b['results'][0]['fixture_refs'] = [ref('other-fixture')]
                r = self.consume(b, e)
                self.assertFalse(r['finite_expectations_match'])
                if change != 'empty': self.assertEqual(r['verdict'], 'REJECT')

    def test_raw_and_full_identity_and_seal_are_not_interchangeable(self):
        b, e, a = fixture(); raw, e = wire(b, e)
        for change in ('raw', 'ref', 'seal'):
            with self.subTest(case_key=change, change=change):
                er = deepcopy(e); data = raw
                if change == 'raw': data += b' '
                if change == 'ref': er['report_ref'] = ref('wrong-report')
                if change == 'seal':
                    obj = json.loads(raw); obj['payload_sha256'] = 'f' * 64
                    data = json.dumps(obj).encode(); er['report_raw_sha256'] = hashlib.sha256(data).hexdigest()
                self.assertEqual(consumer.consume_execution_content(er, data, SCHEMA, a)['verdict'], 'REJECT')

    def test_strict_wire_and_unknown_fields_cannot_leak(self):
        b, e, a = fixture(); raw, e = wire(b, e)
        samples = [('UTF8_BOM', b'\xef\xbb\xbf' + raw),
                   ('DUPLICATE_JSON_KEY', b'{"x":1,"x":2}'),
                   ('LEXICAL_NEGATIVE_ZERO', b'{"x":-0}'),
                   ('NONSTANDARD_NAN', b'{"x":NaN}'), ('JSON_FLOAT', b'{"x":1.2}')]
        obj = json.loads(raw); obj['foreign-secret-looking-field'] = 'DO_NOT_ECHO'
        samples.append(('FOREIGN_FIELD', json.dumps(obj).encode()))
        for case_key, data in samples:
            with self.subTest(case_key=case_key, prefix=data[:12]):
                r = consumer.consume_execution_content(e, data, SCHEMA, a)
                self.assertEqual(r['verdict'], 'REJECT')
                self.assertNotIn('DO_NOT_ECHO', repr(r))

    def test_expected_and_schema_controls_are_closed_and_independent(self):
        b, e, a = fixture(); raw, e = wire(b, e)
        er = deepcopy(e); er['eligible'] = True
        self.assertIn('EXPECTED_INVALID', consumer.consume_execution_content(er, raw, SCHEMA, a)['comparison_errors'])
        self.assertIn('SCHEMA_IDENTITY_MISMATCH', consumer.consume_execution_content(e, raw, SCHEMA + b' ', a)['report_errors'])
        er = deepcopy(e); er['invocations'] = []
        self.assertIn('EXPECTED_INVALID', consumer.consume_execution_content(er, raw, SCHEMA, a)['comparison_errors'])

    def test_local_resource_limit_stays_unresolved_without_empty_success(self):
        b, e, a = fixture(); raw, e = wire(b, e)
        data = b' ' * (4 * 1024 * 1024 + 1); e['report_raw_sha256'] = hashlib.sha256(data).hexdigest()
        r = consumer.consume_execution_content(e, data, SCHEMA, a)
        self.assertIn('report:LOCAL_BYTE_LIMIT', r['missing_inputs'])
        self.assertEqual(r['verdict'], 'UNRESOLVED')
        self.assertFalse(r['finite_expectations_match'])

    def test_local_time_and_finding_and_unavailable_evidence_are_not_authority(self):
        b, e, _ = fixture(); b['invocations'][0]['time_observations']['local_end_utc'] = '2026-10-15T00:00:00Z'
        self.assertIn('LOCAL_TIME_ORDER', self.consume(b, e)['report_errors'])
        b, e, _ = fixture(); b['finding_refs'] = [ref('finding')]
        b['unavailable_evidence'] = [{'role_id': 'PUBLIC_SUPPORT', 'reason_code': 'NOT_AVAILABLE'}]
        r = self.consume(b, e)
        self.assertEqual(r['finding_refs'], [ref('finding')])
        self.assertIn('declared:PUBLIC_SUPPORT', r['missing_inputs'])
        self.assertFalse(r['finite_expectations_match'])

    def test_missing_report_expected_and_schema_never_pass(self):
        r = consumer.consume_execution_content(None, None, None, {})
        self.assertEqual(r['verdict'], 'UNRESOLVED')
        self.assertFalse(r['finite_expectations_match'])
        self.assertEqual(set(r['missing_inputs']), {'expected', 'report', 'schema'})


if __name__ == '__main__':
    case_events.main()
