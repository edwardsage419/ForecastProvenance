"""Retained service observations must replay without becoming chain authority."""
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
PACKAGE = ROOT/'docs/development/mainline-execution-2026-10-19-public-chain-observation-rev-001'
HEADER = ROOT/'docs/development/mainline-execution-2026-10-19-public-bitcoin-header-rev-001/raw/blockstream-header.hex'


class PublicChainTests(unittest.TestCase):
    def setUp(self):
        self.header = HEADER.read_bytes()
        self.requests = json.loads((PACKAGE/'REQUESTS.json').read_bytes())
        self.raw = {row['provider']+'_'+row['kind']: (ROOT/row['path']).read_bytes()
                    for row in self.requests if row['status'] == 'RETAINED'}

    def consume(self, requests=None, raw=None):
        path = HERE/'ots_body.py'; module = ModuleType('d196_test')
        exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
        self.assertTrue(callable(getattr(module, 'consume_public_chain_observations', None)),
                        'retained public observations are not consumed')
        return module.consume_public_chain_observations(
            self.header, 912095, self.requests if requests is None else requests,
            self.raw if raw is None else raw)

    def replace_raw(self, kind, raw):
        # Alter the bounded input consistently so semantic validation, rather
        # than an unchanged hash pin, has to catch the counterexample.
        self.raw['blockstream_'+kind] = raw
        row = next(row for row in self.requests
                   if row['provider'] == 'blockstream' and row['kind'] == kind)
        row.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

    def command(self, *args, human=False):
        command = [str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'), 'mainline', *args]
        if not human:
            command.append('--json')
        process = subprocess.run(command, capture_output=True, text=True, timeout=45)
        self.assertTrue(process.stdout.strip(), process.stderr)
        return process, process.stdout if human else json.loads(process.stdout)

    def test_retained_bytes_and_failed_source_are_both_consumed_without_authority(self):
        result = self.consume()
        self.assertEqual(result['status'], 'MISSING')
        self.assertEqual(len(result['sources']), 2)
        observed, failed = result['sources']
        self.assertEqual(observed['status'], 'OBSERVED')
        self.assertTrue(observed['service_reported_in_best_chain'])
        self.assertEqual(observed['reported_depth_arithmetic'], 60040)
        self.assertEqual(observed['service_reported_tip_height'], 972134)
        self.assertEqual(failed['status'], 'MISSING')
        self.assertEqual(len(failed['findings']), 4)
        self.assertEqual(result['chain_verification'], 'NOT_CHECKED')
        self.assertEqual(result['authenticated_time'], 'NOT_ESTABLISHED')
        self.assertEqual(result['source_independence'], 'NOT_ESTABLISHED')
        self.assertFalse(result['tip_queries_atomic'])

    def test_each_header_field_and_strict_json_type_are_actually_checked(self):
        original = json.loads(self.raw['blockstream_block'])
        for field in ['id', 'version', 'timestamp', 'bits', 'nonce', 'merkle_root',
                      'previousblockhash', 'height']:
            with self.subTest(field=field):
                changed = dict(original)
                changed[field] = '0'*64 if type(changed[field]) is str else changed[field]+1
                self.replace_raw('block', json.dumps(changed).encode())
                self.assertEqual(self.consume()['sources'][0]['status'], 'REJECTED')
        for raw in [b'{"id":"x","id":"y"}', b'{"height":NaN}',
                    json.dumps(dict(original, version=True)).encode(), b'[]']:
            with self.subTest(raw=raw[:40]):
                self.replace_raw('block', raw)
                self.assertEqual(self.consume()['status'], 'REJECTED')

    def test_missing_response_does_not_hide_later_bad_metadata_or_failed_source(self):
        del self.raw['blockstream_tip-hash']
        changed = json.loads(self.raw['blockstream_block']); changed['nonce'] += 1
        self.replace_raw('block', json.dumps(changed).encode())
        result = self.consume()
        self.assertEqual(result['status'], 'REJECTED')
        statuses = [row['status'] for row in result['findings']]
        self.assertIn('MISSING', statuses)
        self.assertIn('REJECTED', statuses)
        self.assertEqual(result['sources'][1]['status'], 'MISSING')

    def test_duplicate_or_omitted_requests_and_unbound_response_do_not_pass(self):
        duplicate = copy.deepcopy(self.requests); duplicate.append(duplicate[0])
        self.assertEqual(self.consume(duplicate)['status'], 'REJECTED')
        omitted = self.requests[1:]
        self.assertEqual(self.consume(omitted)['status'], 'REJECTED')  # unbound raw remains
        del self.raw['blockstream_block']
        result = self.consume(omitted)
        self.assertEqual(result['status'], 'MISSING')
        self.assertTrue(result['findings'])
        self.assertEqual(self.consume([], {})['status'], 'MISSING')

    def test_valid_negative_service_observation_is_retained_without_fake_depth(self):
        self.replace_raw('status', b'{"in_best_chain":false,"height":912095}')
        result = self.consume(); observed = result['sources'][0]
        self.assertEqual(observed['status'], 'OBSERVED')
        self.assertFalse(observed['service_reported_in_best_chain'])
        self.assertIsNone(observed['reported_depth_arithmetic'])
        self.assertEqual(result['chain_verification'], 'NOT_CHECKED')
        self.replace_raw('status', b'{"in_best_chain":true,"height":912095}')
        self.replace_raw('tip-height', b'912094')
        self.assertEqual(self.consume()['sources'][0]['status'], 'REJECTED')

    def test_origin_hash_and_bounded_formats_prevent_unchecked_claims(self):
        requests = copy.deepcopy(self.requests); requests[0]['url'] = 'https://example.invalid/'
        self.assertEqual(self.consume(requests)['status'], 'REJECTED')
        raw = dict(self.raw); raw['blockstream_block'] += b' '
        self.assertEqual(self.consume(raw=raw)['status'], 'REJECTED')
        for kind, value in [('block', b' '*65537), ('tip-height', b'-1'),
                            ('tip-height', b'9'*25), ('tip-hash', b'F'*64),
                            ('status', b'{"in_best_chain":1}'),
                            ('status', b'{"in_best_chain":true,"height":true}')]:
            with self.subTest(kind=kind, value=value[:30]):
                self.replace_raw(kind, value)
                self.assertEqual(self.consume()['status'], 'REJECTED')

    def test_mainline_replays_in_new_processes_and_keeps_real_time_missing(self):
        first, report = self.command(); second, again = self.command()
        self.assertEqual(first.returncode, 1); self.assertEqual(second.returncode, 1)
        self.assertEqual(report, again)
        rows = {row['id']: row for row in report['modules']}
        time = rows['time-and-durability']
        observation = time['public_example'].get('public_chain_observation')
        self.assertIsInstance(observation, dict, 'lightweight observations disconnected from entry')
        self.assertEqual(observation['sources'][0]['reported_depth_arithmetic'], 60040)
        self.assertEqual(observation['sources'][1]['status'], 'MISSING')
        self.assertEqual(time['status'], 'MISSING')
        self.assertEqual(time['public_example']['bitcoin_verification'], 'NOT_CHECKED')
        self.assertEqual(report['real_admission'], 'NOT_READY')
        self.assertFalse(report['prospective_eligible'])
        self.assertEqual(report['protocol_state_change'], 'NONE')
        process, human = self.command(human=True)
        self.assertEqual(process.returncode, 1)
        self.assertIn('公开服务观察', human)
        self.assertIn('非独立链验证', human)

    def test_explicit_missing_chain_directory_does_not_fall_back(self):
        with tempfile.TemporaryDirectory() as directory:
            process, report = self.command('--chain-inputs', directory)
        self.assertEqual(process.returncode, 1)
        rows = {row['id']: row for row in report['modules']}
        result = rows['time-and-durability']['public_example']['public_chain_observation']
        self.assertEqual(result['status'], 'MISSING')
        self.assertFalse(result['sources'])
        self.assertEqual(rows['economic-data']['status'], 'OBSERVED')

    def test_replaced_raw_and_missing_log_are_retained_and_rejection_reaches_parent(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name); shutil.copytree(PACKAGE/'raw', directory/'raw')
            target = directory/'raw/blockstream-status.json'
            target.write_bytes(target.read_bytes()+b' ')
            process, report = self.command('--chain-inputs', name)
        self.assertEqual(process.returncode, 2)
        rows = {row['id']: row for row in report['modules']}
        time = rows['time-and-durability']
        result = time['public_example']['public_chain_observation']
        self.assertEqual(time['status'], 'REJECTED')
        self.assertIn('MISSING', [row['status'] for row in result['findings']])
        self.assertIn('REJECTED', [row['status'] for row in result['findings']])
        self.assertEqual(rows['economic-data']['status'], 'OBSERVED')


if __name__ == '__main__':
    unittest.main()
