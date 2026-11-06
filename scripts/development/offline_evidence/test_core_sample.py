"""D199 local retained observations must not become real project readiness."""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import ModuleType
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKAGE = ROOT/'docs/development/mainline-execution-2026-10-19-pruned-core-sample-execution-rev-001'
FILES = {'result': 'online-107-RESULT.json', 'events': 'online-107-PUBLIC_EVENTS.jsonl',
         'verification': 'SEGMENT_107_512_VERIFICATION.json',
         'controller': 'supervise_core.metadata-rescan.py', 'config': 'bitcoin.conf.cache512-continuation.txt'}
PROOF = ROOT/'docs/development/mainline-execution-2026-10-09-rev-001/gdp-public-proof-pair-2026-10-15-rev-001/raw'
HEADER = ROOT/'docs/development/mainline-execution-2026-10-19-public-bitcoin-header-rev-001/raw/blockstream-header.hex'


def load(name):
    path = HERE/(name+'.py'); module = ModuleType('test_d200_'+name)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


class CoreSampleTests(unittest.TestCase):
    def setUp(self):
        self.raw = {key: (PACKAGE/name).read_bytes() for key, name in FILES.items()}
        self.raw.update(pdf=(PROOF/'gdp2q25-2nd.pdf').read_bytes(),
                        proof=(PROOF/'gdp2q25-2nd.pdf.ots').read_bytes(), header=HEADER.read_bytes())

    def consume(self):
        self.assertTrue((HERE/'core_sample.py').is_file(), 'D199 retained observations have no consumer')
        return load('core_sample').consume_core_sample(self.raw, load('ots_body'))

    def rewrite(self, result=None, events=None):
        # Public local Core observations, never FPP messages. Keep raw bindings
        # coherent so tests reach semantic checks rather than failing old pins.
        old = json.loads(self.raw['result'])
        lines = [json.loads(x) for x in self.raw['events'].splitlines()]
        if result is not None:
            lines[-1] = dict(result, stage='SEGMENT_RESULT', observed_at_utc=lines[-1]['observed_at_utc'])
            self.raw['result'] = json.dumps(result).encode()
        if events is not None:
            lines = events
        self.raw['events'] = b''.join(json.dumps(x).encode()+b'\n' for x in lines)
        verification = json.loads(self.raw['verification'])
        for key in ('result', 'events'):
            row = next(x for x in verification['identities'] if x['path'].endswith('/'+FILES[key]))
            row.update(bytes=len(self.raw[key]), sha256=hashlib.sha256(self.raw[key]).hexdigest())
        self.raw['verification'] = json.dumps(verification).encode()

    def test_retained_sample_recomputes_links_and_preserves_scope(self):
        value = self.consume()
        self.assertEqual(value['status'], 'OBSERVED', value)
        self.assertEqual(value['observed_blocks'], 972999)
        self.assertEqual(value['confirmations_observed'], 60905)
        self.assertEqual(value['retained_live_resource_records'], 19)
        self.assertEqual(value['complete_consumer_observations'], 18)
        self.assertEqual(value['subject_link']['body_computation']['operation_count'], 40)
        self.assertEqual(value['subject_link']['header_binding']['status'], 'OBSERVED')
        self.assertEqual(value['subject_link']['header_binding']['chain_verification'], 'NOT_CHECKED')
        self.assertEqual(value['project_Strong'], 'NOT_ESTABLISHED')
        self.assertFalse(value['compact_evidence_replays_full_chain'])

    def test_ibd_or_verbose_contradiction_is_rejected_after_binding(self):
        for kind in ('ibd', 'nonce', 'confirmations'):
            with self.subTest(kind=kind):
                self.setUp(); result = json.loads(self.raw['result'])
                if kind == 'ibd':
                    result['last_chain']['result']['initialblockdownload'] = True
                else:
                    result['sample_header_verbose']['result'][kind] += 1
                self.rewrite(result=result)
                value = self.consume()
                self.assertEqual(value['status'], 'REJECTED')
                self.assertIn('CORE_SAMPLE_FIELDS_INVALID', [x['error'] for x in value['findings']])

    def test_later_failure_and_missing_consumer_survive_first_success(self):
        events = [json.loads(x) for x in self.raw['events'].splitlines()]
        bad = copy.deepcopy(next(x for x in events if x['stage'] == 'SYNC_OBSERVATION'))
        bad['network'] = {'ok': False, 'error_kind': 'RETAINED_PUBLIC_TEST_FAILURE'}
        bad.pop('peer_diagnostics')
        events.insert(-1, bad); self.rewrite(events=events)
        value = self.consume()
        self.assertEqual(value['status'], 'REJECTED')
        errors = [x['error'] for x in value['findings']]
        self.assertIn('RETAINED_CONSUMER_FAILED', errors)
        self.assertIn('RETAINED_CONSUMER_MISSING', errors)

    def test_missing_proof_does_not_hide_resource_or_duplicate_terminal_failure(self):
        self.raw['pdf'] = None
        events = [json.loads(x) for x in self.raw['events'].splitlines()]
        sync = next(x for x in events if x['stage'] == 'SYNC_OBSERVATION')
        sync['resources']['own_node_rss_bytes'] = 8522825728
        events.insert(-1, copy.deepcopy(events[-1])); self.rewrite(events=events)
        value = self.consume()
        self.assertEqual(value['status'], 'REJECTED')
        self.assertIn('MISSING', [x['status'] for x in value['findings']])
        self.assertIn('RETAINED_RESOURCE_OUT_OF_BOUNDS', [x['error'] for x in value['findings']])
        self.assertIn('CORE_EVENT_FRAMING_INVALID', [x['error'] for x in value['findings']])

    def test_strict_json_and_unbound_result_are_rejected(self):
        for raw in (b'{"mode":"online","mode":"offline"}', b'{"x":NaN}', b'[]'):
            with self.subTest(raw=raw):
                self.setUp(); self.raw['result'] = raw
                self.assertEqual(self.consume()['status'], 'REJECTED')
        self.setUp(); self.raw['result'] += b' '
        self.assertEqual(self.consume()['status'], 'REJECTED')

    def test_negative_verification_and_incomplete_success_payload_do_not_pass(self):
        verification = json.loads(self.raw['verification'])
        verification['sample_chain_verified'] = False
        self.raw['verification'] = json.dumps(verification).encode()
        value = self.consume()
        self.assertEqual(value['status'], 'REJECTED')
        self.assertIn('CORE_VERIFICATION_NEGATIVE', [x['error'] for x in value['findings']])

    def test_successful_chain_payload_is_checked_in_every_observation(self):
        for missing in (False, True):
            with self.subTest(missing=missing):
                self.setUp(); events = [json.loads(x) for x in self.raw['events'].splitlines()]
                later = copy.deepcopy(next(x for x in events if x['stage'] == 'SYNC_OBSERVATION'))
                if missing: later['chain'] = {'ok': True}
                else: later['chain']['result']['blocks'] = 1
                events.insert(-1, later); self.rewrite(events=events)
                value = self.consume()
                self.assertEqual(value['status'], 'REJECTED')
                self.assertIn('RETAINED_CHAIN_INVALID', [x['error'] for x in value['findings']])

    def test_omitted_last_observation_cannot_leave_terminal_claim_unbound(self):
        events = [json.loads(x) for x in self.raw['events'].splitlines()]
        last = max(i for i, x in enumerate(events) if x['stage'] == 'SYNC_OBSERVATION')
        events.pop(last); self.rewrite(events=events)
        value = self.consume()
        self.assertEqual(value['status'], 'REJECTED')
        self.assertIn('CORE_LAST_OBSERVATION_MISMATCH', [x['error'] for x in value['findings']])

    def test_successful_network_and_peer_markers_require_payloads(self):
        for field in ('network', 'peer_diagnostics'):
            with self.subTest(field=field):
                self.setUp(); events = [json.loads(x) for x in self.raw['events'].splitlines()]
                next(x for x in events if x['stage'] == 'SYNC_OBSERVATION')[field] = {'ok': True}
                self.rewrite(events=events)
                value = self.consume()
                self.assertNotEqual(value['status'], 'OBSERVED')
                self.assertIn('RETAINED_CONSUMER_PAYLOAD_MISSING', [x['error'] for x in value['findings']])

    def test_final_disk_and_last_live_resource_are_consumed(self):
        for field in ('final_resources', 'last_resources_observation'):
            with self.subTest(field=field):
                self.setUp(); result = json.loads(self.raw['result'])
                if field == 'final_resources':
                    result[field].update(logical_bytes=10**12, allocated_bytes=10**12, free_bytes=0)
                    expected = 'CORE_FINAL_RESOURCE_INVALID'
                else:
                    result[field] = None; expected = 'CORE_LAST_RESOURCE_MISMATCH'
                self.rewrite(result=result); value = self.consume()
                self.assertEqual(value['status'], 'REJECTED')
                self.assertIn(expected, [x['error'] for x in value['findings']])

    def test_verification_exception_and_both_chain_summaries_are_reconciled(self):
        for field in ('exception_type', 'last_retained_successful_chain_read',
                      'last_successful_full_observation_chain_from_result'):
            with self.subTest(field=field):
                self.setUp(); verification = json.loads(self.raw['verification'])
                verification[field] = 'RuntimeError' if field == 'exception_type' else {'ok': False}
                self.raw['verification'] = json.dumps(verification).encode()
                value = self.consume()
                self.assertEqual(value['status'], 'REJECTED')
                self.assertIn('CORE_VERIFICATION_NEGATIVE' if field == 'exception_type'
                              else 'CORE_VERIFICATION_CHAIN_MISMATCH',
                              [x['error'] for x in value['findings']])

    def test_exponent_overflow_is_rejected_as_nonfinite_json(self):
        events = [json.loads(x) for x in self.raw['events'].splitlines()]
        next(x for x in events if x['stage'] == 'SYNC_OBSERVATION')['network']['result']['relayfee'] = 'overflow-marker'
        self.rewrite(events=events)
        self.raw['events'] = self.raw['events'].replace(b'"overflow-marker"', b'1e309', 1)
        verification = json.loads(self.raw['verification'])
        row = next(x for x in verification['identities'] if x['path'].endswith('/'+FILES['events']))
        row.update(bytes=len(self.raw['events']), sha256=hashlib.sha256(self.raw['events']).hexdigest())
        self.raw['verification'] = json.dumps(verification).encode()
        value = self.consume()
        self.assertEqual(value['status'], 'REJECTED')
        self.assertIn('CORE_EVENTS_JSON_INVALID', [x['error'] for x in value['findings']])

    def test_exact_launch_argv_is_bound_to_retained_profile(self):
        for kind in ('binary', 'config', 'datadir', 'network', 'override', 'missing', 'missing-proof'):
            with self.subTest(kind=kind):
                self.setUp(); result = json.loads(self.raw['result'])
                if kind == 'binary': result['argv'][0] = '/SYNTHETIC_TEST_ONLY/other-bitcoind'
                elif kind in ('config', 'missing-proof'):
                    result['argv'][1] = '-conf=/SYNTHETIC_TEST_ONLY/other-config.conf'
                elif kind == 'datadir': result['argv'][2] = '-datadir=/SYNTHETIC_TEST_ONLY/other-data'
                elif kind == 'network': result['argv'][3] = '-networkactive=0'
                elif kind == 'override': result['argv'].append('-conf=/SYNTHETIC_TEST_ONLY/override.conf')
                elif kind == 'missing': result.pop('argv')
                if kind == 'missing-proof': self.raw['pdf'] = None
                self.rewrite(result=result); value = self.consume()
                self.assertEqual(value['status'], 'REJECTED')
                self.assertIn('CORE_LAUNCH_PROFILE_MISMATCH', [x['error'] for x in value['findings']])
                if kind == 'missing-proof':
                    self.assertIn('MISSING', [x['status'] for x in value['findings']])

    def test_memory_policy_matches_fixed_types_and_thresholds(self):
        for field, value in [('rss_stop_bytes', 8522825729),
                             ('footprint_upper_stop_bytes', 2080374784.0),
                             ('sampling_is_not_atomic_quota', 1),
                             ('id', 'SYNTHETIC_OTHER_POLICY'), ('extra', True)]:
            with self.subTest(field=field):
                self.setUp(); result = json.loads(self.raw['result'])
                result['memory_policy'][field] = value; self.rewrite(result=result)
                value = self.consume()
                self.assertEqual(value['status'], 'REJECTED')
                self.assertIn('CORE_MEMORY_POLICY_MISMATCH', [x['error'] for x in value['findings']])

    def test_retry_policy_matches_fixed_types_and_limits(self):
        for field, value in [('maximum_attempts', 3), ('HTTP_timeout_only', 1),
                             ('first_CLI_timeout_seconds', 5.0),
                             ('guarded_cooldown_target_seconds', 0), ('extra', True)]:
            with self.subTest(field=field):
                self.setUp(); result = json.loads(self.raw['result'])
                result['read_retry_policy'][field] = value; self.rewrite(result=result)
                value = self.consume()
                self.assertEqual(value['status'], 'REJECTED')
                self.assertIn('CORE_RETRY_POLICY_MISMATCH', [x['error'] for x in value['findings']])

    def command(self, *args, human=False):
        args = [str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'), 'mainline', *args]
        if not human: args.append('--json')
        process = subprocess.run(args, capture_output=True, text=True, timeout=45)
        self.assertTrue(process.stdout.strip(), process.stderr)
        return process, process.stdout if human else json.loads(process.stdout)

    def sample(self, report):
        row = next(x for x in report['modules'] if x['id'] == 'time-and-durability')
        value = row['public_example'].get('retained_core_sample')
        self.assertIsInstance(value, dict, 'D199 Core observation disconnected from mainline')
        return row, value

    def test_new_processes_replay_same_core_observation_without_readiness(self):
        first, report = self.command(); second, again = self.command()
        self.assertEqual(first.returncode, 1); self.assertEqual(second.returncode, 1)
        self.assertEqual(report, again)
        row, value = self.sample(report)
        self.assertEqual(value['status'], 'OBSERVED')
        self.assertEqual(row['status'], 'MISSING')
        self.assertEqual(report['real_admission'], 'NOT_READY')
        self.assertFalse(report['prospective_eligible'])
        self.assertEqual(report['protocol_state_change'], 'NONE')
        process, text = self.command(human=True)
        self.assertEqual(process.returncode, 1)
        self.assertIn('本地Core留存样例', text)
        self.assertIn('非项目Strong', text)

    def test_explicit_missing_directory_never_falls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            process, report = self.command('--core-inputs', directory)
        row, value = self.sample(report)
        self.assertEqual(value['status'], 'MISSING')
        self.assertEqual(process.returncode, 1)
        self.assertEqual(next(x for x in report['modules'] if x['id'] == 'economic-data')['status'], 'OBSERVED')

    def test_missing_replaced_and_symlink_inputs_propagate_without_masking(self):
        for symlink in (False, True):
            with self.subTest(symlink=symlink), tempfile.TemporaryDirectory() as directory:
                destination = Path(directory)
                for name in FILES.values(): shutil.copyfile(PACKAGE/name, destination/name)
                (destination/FILES['verification']).unlink()
                target = destination/FILES['events']; target.unlink()
                if symlink: target.symlink_to(PACKAGE/FILES['events'])
                else: target.write_bytes(b'replaced\n')
                process, report = self.command('--core-inputs', directory)
                row, value = self.sample(report)
                self.assertEqual(process.returncode, 2)
                self.assertEqual(row['status'], 'REJECTED')
                self.assertEqual(value['status'], 'REJECTED')
                self.assertIn('MISSING', [x['status'] for x in value['findings']])
                self.assertIn('UNSAFE_PATH' if symlink else 'INPUT_IDENTITY_MISMATCH',
                              [x['error'] for x in value['findings']])


if __name__ == '__main__': unittest.main()
