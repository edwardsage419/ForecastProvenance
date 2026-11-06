"""Passive OTS byte consumption never establishes chain truth or civil time."""
import hashlib
import json
from pathlib import Path
import subprocess
from types import ModuleType
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROOF = ROOT/'docs/development/mainline-execution-2026-10-09-rev-001/gdp-public-proof-pair-2026-10-15-rev-001/raw'
MAGIC = bytes.fromhex('004f70656e54696d657374616d7073000050726f6f6600bf89e2e884e89294')
BTC_TAG = bytes.fromhex('0588960d73d71901')
PENDING_TAG = bytes.fromhex('83dfe30d2ef90c8e')


class OTSBodyTests(unittest.TestCase):
    def consumer(self):
        path = HERE/'ots_body.py'
        self.assertTrue(path.is_file(), 'passive proof-body consumer is missing')
        module = ModuleType('ots_body_test')
        module.__file__ = str(path)
        exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
        return module

    def proof(self, body, data=b'declared synthetic binary-parser input'):
        return MAGIC+b'\x01\x08'+hashlib.sha256(data).digest()+body

    def attestation(self, height):
        self.assertLess(height, 128)
        return b'\x00'+BTC_TAG+b'\x01'+bytes([height])

    def test_existing_public_proof_body_is_fully_consumed_without_claiming_strong(self):
        proof = (PROOF/'gdp2q25-2nd.pdf.ots').read_bytes()
        result = self.consumer().consume_ots_paths((PROOF/'gdp2q25-2nd.pdf').read_bytes(), proof)
        self.assertEqual(result['proof_bytes_consumed'], 650)
        self.assertEqual(result['body_bytes_consumed'], 585)
        self.assertGreater(result['operation_count'], 0)
        self.assertTrue(result['bitcoin_attestations'])
        self.assertTrue(result['subject_digest_match'])
        self.assertEqual(result['bitcoin_verification'], 'NOT_CHECKED')
        self.assertEqual(result['full_ots_verification'], 'NOT_CHECKED')
        self.assertEqual(result['authenticated_time'], 'NOT_ESTABLISHED')

    def test_append_prepend_and_both_fork_branches_use_the_parent_message(self):
        data = b'declared synthetic binary-parser input'
        digest = hashlib.sha256(data).digest()
        body = (b'\xff\xf0\x01a\x08'+self.attestation(1)
                +b'\xf1\x01b\x08'+self.attestation(2))
        result = self.consumer().consume_ots_paths(data, self.proof(body))
        rows = result['bitcoin_attestations']
        self.assertEqual([(r['claimed_height'], r['commitment_hex']) for r in rows],
                         [(1, hashlib.sha256(digest+b'a').hexdigest()),
                          (2, hashlib.sha256(b'b'+digest).hexdigest())])
        self.assertEqual(result['operation_count'], 4)
        changed = body.replace(b'\x01a', b'\x01z')
        other = self.consumer().consume_ots_paths(data, self.proof(changed))
        self.assertNotEqual(other['bitcoin_attestations'][0]['commitment_hex'], rows[0]['commitment_hex'])
        self.assertEqual(other['bitcoin_verification'], 'NOT_CHECKED')

    def test_truncation_trailing_data_wrong_subject_and_later_unsupported_branch_fail(self):
        consumer = self.consumer()
        raw = self.proof(b'\xf0\x01a\x08'+self.attestation(1))
        data = b'declared synthetic binary-parser input'
        for cut in range(len(raw)):
            with self.subTest(cut=cut), self.assertRaises(ValueError):
                consumer.consume_ots_paths(data, raw[:cut])
        for bad in [raw+b'\x00', raw[:31]+b'\x02'+raw[32:],
                    self.proof(b'\xff'+self.attestation(1)+b'\x99')]:
            with self.assertRaises(ValueError):
                consumer.consume_ots_paths(data, bad)
        with self.assertRaises(ValueError):
            consumer.consume_ots_paths(b'wrong input', raw)

    def test_known_attestation_payload_must_be_complete_unknown_one_is_preserved(self):
        consumer = self.consumer()
        data = b'declared synthetic binary-parser input'
        unknown = b'\x00'+b'unknown!'+b'\x03abc'
        result = consumer.consume_ots_paths(data, self.proof(unknown))
        self.assertEqual(result['unknown_attestations'][0]['payload_hex'], b'abc'.hex())
        self.assertFalse(result['bitcoin_attestations'])
        for body in [b'\x00'+BTC_TAG+b'\x02\x01\x00', b'\x00'+BTC_TAG+b'\x00',
                     b'\xf0\x00'+self.attestation(1),
                     b'\x00'+BTC_TAG+b'\x02\x81\x00']:
            with self.assertRaises(ValueError):
                consumer.consume_ots_paths(data, self.proof(body))

    def test_pending_calendar_is_only_a_retained_uri_and_is_never_fetched(self):
        uri = b'https://calendar.example.invalid'
        payload = bytes([len(uri)])+uri
        body = b'\x00'+PENDING_TAG+bytes([len(payload)])+payload
        result = self.consumer().consume_ots_paths(b'declared synthetic binary-parser input', self.proof(body))
        self.assertEqual(result['pending_attestations'][0]['uri'], uri.decode())
        self.assertEqual(result['calendar_requests'], 0)
        self.assertFalse(result['bitcoin_attestations'])

    def test_forked_path_expansion_cannot_create_an_unbounded_report(self):
        # A small encoded tree can repeat the same long operation path at leaves.
        leaves = [b'\x00'+index.to_bytes(8, 'big')+b'\x00' for index in range(192)]
        body = b'\xf0\xa0\x1f'+b'a'*4000+b'\x08'
        body += b''.join(b'\xff'+leaf for leaf in leaves[:-1])+leaves[-1]
        with self.assertRaisesRegex(ValueError, 'OTS_REPORT_SIZE_LIMIT'):
            self.consumer().consume_ots_paths(b'declared synthetic binary-parser input', self.proof(body))

    def test_reverse_hexlify_are_computed_and_overlong_operations_are_rejected(self):
        data = b'declared synthetic binary-parser input'
        body = b'\xf2\xf3\x08'+self.attestation(1)
        result = self.consumer().consume_ots_paths(data, self.proof(body))
        expected = hashlib.sha256(hashlib.sha256(data).digest()[::-1].hex().encode()).hexdigest()
        self.assertEqual(result['bitcoin_attestations'][0]['commitment_hex'], expected)
        with self.assertRaises(ValueError):
            self.consumer().consume_ots_paths(data, self.proof(b'\xf0\x80\x20'+b'a'*4096+self.attestation(1)))

    def test_mainline_uses_body_computation_but_keeps_real_time_missing(self):
        process = subprocess.run([str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'),
                                  'mainline', '--json'], capture_output=True, text=True, timeout=45)
        report = json.loads(process.stdout)
        time = next(row for row in report['modules'] if row['id'] == 'time-and-durability')
        paths = time['public_example'].get('body_computation', {})
        self.assertEqual(paths.get('body_bytes_consumed'), 585, paths)
        self.assertTrue(paths['bitcoin_attestations'])
        self.assertEqual(time['status'], 'MISSING')
        self.assertEqual(time['public_example']['bitcoin_verification'], 'NOT_CHECKED')
        self.assertEqual(report['real_admission'], 'NOT_READY')
        self.assertEqual(process.returncode, 1)


if __name__ == '__main__':
    unittest.main()
