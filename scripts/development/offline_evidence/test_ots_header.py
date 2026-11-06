"""Header-byte consistency is never chain, authority or civil-time verification."""
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
PACKAGE = ROOT/'docs/development/mainline-execution-2026-10-19-public-bitcoin-header-rev-001'
PROOF = ROOT/'docs/development/mainline-execution-2026-10-09-rev-001/gdp-public-proof-pair-2026-10-15-rev-001/raw'
MAGIC = bytes.fromhex('004f70656e54696d657374616d7073000050726f6f6600bf89e2e884e89294')
BTC = bytes.fromhex('0588960d73d71901')
DATA = b'declared synthetic header-parser input'


def attestation(height):
    return b'\x00'+BTC+b'\x01'+bytes([height])


def proof(body):
    return MAGIC+b'\x01\x08'+hashlib.sha256(DATA).digest()+body


def record(root, height=1, source='synthetic'):
    header = b'\x01\x00\x00\x00'+b'\x00'*32+root+b'\x01\x00\x00\x00'+b'\x00'*8
    digest = hashlib.sha256(hashlib.sha256(header).digest()).digest()[::-1].hex()
    return {'source_id': source, 'claimed_height': height,
            'block_hash_response': digest.encode(), 'header_response': header.hex().encode()}


class OTSHeaderTests(unittest.TestCase):
    def consume(self, data, raw, records):
        path = HERE/'ots_body.py'
        module = ModuleType('ots_header_test')
        exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
        function = getattr(module, 'consume_ots_header_links', None)
        self.assertTrue(callable(function), 'actual proof/header consumer missing')
        return function(data, raw, records)

    def public_records(self):
        return [{'source_id': source, 'claimed_height': 912095,
                 'block_hash_response': (PACKAGE/'raw'/f'{source}-height-912095.txt').read_bytes(),
                 'header_response': (PACKAGE/'raw'/f'{source}-header.hex').read_bytes()}
                for source in ('blockstream', 'mempool')]

    def test_retained_public_pair_links_every_header_to_the_actual_proof(self):
        result = self.consume((PROOF/'gdp2q25-2nd.pdf').read_bytes(),
                              (PROOF/'gdp2q25-2nd.pdf.ots').read_bytes(), self.public_records())
        binding = result['header_binding']
        self.assertEqual(result['body_computation']['operation_count'], 40)
        self.assertEqual(binding['status'], 'OBSERVED')
        self.assertEqual(len(binding['headers']), 2)
        self.assertTrue(all(row['merkle_root_match'] for row in binding['links']))
        self.assertEqual(binding['headers'][0]['block_hash'],
                         '000000000000000000007f0753c6209263c7072e51b725e89e75a0c708b90345')
        self.assertEqual(binding['chain_verification'], 'NOT_CHECKED')
        self.assertEqual(binding['height_verification'], 'PUBLIC_SERVICE_DECLARATION_ONLY')
        self.assertEqual(binding['authenticated_time'], 'NOT_ESTABLISHED')

    def test_consistent_fabricated_header_does_not_establish_pow_chain_or_time(self):
        root = hashlib.sha256(DATA).digest()
        row = record(root)
        result = self.consume(DATA, proof(attestation(1)), [row])['header_binding']
        self.assertEqual(result['status'], 'OBSERVED')
        self.assertEqual(result['headers'][0]['merkle_wire_hex'], root.hex())
        self.assertEqual(result['proof_of_work'], 'NOT_CHECKED')
        self.assertEqual(result['full_ots_verification'], 'NOT_CHECKED')
        self.assertEqual(result['project_subject_binding'], 'NOT_ESTABLISHED')
        self.assertEqual(result['authenticated_time'], 'NOT_ESTABLISHED')

    def test_hash_identity_root_byte_order_and_non_merkle_mutation_reject(self):
        root = hashlib.sha256(DATA).digest()
        good = record(root)
        wrong_hash = dict(good, block_hash_response=b'0'*64)
        changed = bytearray.fromhex(good['header_response'].decode()); changed[79] ^= 1
        changed_header = dict(good, header_response=changed.hex().encode())
        for row in (wrong_hash, changed_header, record(root[::-1])):
            with self.subTest(row=row):
                result = self.consume(DATA, proof(attestation(1)), [row])['header_binding']
                self.assertEqual(result['status'], 'REJECTED')

    def test_exact_response_format_lengths_types_and_duplicate_source_reject(self):
        good = record(hashlib.sha256(DATA).digest())
        cases = [[], [good, good]]
        for field, bad_values in [('header_response', [b'', b'0'*158, b'0'*162,
                                                      b'G'*160, b' '*160, b'\xff'*160,
                                                      good['header_response']+b'\n\n']),
                                  ('block_hash_response', [b'', b'F'*64, '0'*64]),
                                  ('claimed_height', [True, -1]), ('source_id', ['', None])]:
            cases.extend([[dict(good, **{field: value})] for value in bad_values])
        for rows in cases[1:]:
            with self.subTest(rows=rows):
                self.assertEqual(self.consume(DATA, proof(attestation(1)), rows)['header_binding']['status'],
                                 'REJECTED')
        newline = dict(good, header_response=good['header_response']+b'\n',
                       block_hash_response=good['block_hash_response']+b'\n')
        self.assertEqual(self.consume(DATA, proof(attestation(1)), [newline])['header_binding']['status'],
                         'OBSERVED')
        many = [dict(good, source_id=str(i)) for i in range(33)]
        self.assertEqual(self.consume(DATA, proof(attestation(1)), many)['header_binding']['status'],
                         'REJECTED')

    def test_missing_header_or_bitcoin_path_cannot_be_empty_success(self):
        for raw, rows in [(proof(attestation(1)), []),
                          (proof(b'\x00unknown!\x00'), []),
                          (proof(attestation(2)), [record(hashlib.sha256(DATA).digest())])]:
            result = self.consume(DATA, raw, rows)['header_binding']
            self.assertNotEqual(result['status'], 'OBSERVED')
        self.assertEqual(self.consume(DATA, proof(attestation(1)), [])['header_binding']['status'], 'MISSING')

    def test_all_forks_headers_and_failures_are_consumed_including_missing_plus_rejection(self):
        root = hashlib.sha256(DATA).digest()
        good = record(root)
        bad = record(root[::-1], source='later-source')
        self.assertEqual(self.consume(DATA, proof(attestation(1)), [good, bad])['header_binding']['status'],
                         'REJECTED')
        forks = b'\xff'+attestation(1)+b'\xf0\x01a\x08'+attestation(2)
        result = self.consume(DATA, proof(forks), [good])['header_binding']
        self.assertEqual(result['status'], 'MISSING')
        self.assertEqual(len(result['links']), 2)
        both = self.consume(DATA, proof(forks), [record(root[::-1])])['header_binding']
        self.assertEqual(both['status'], 'REJECTED')
        self.assertIn('MISSING', [row['status'] for row in both['findings']])
        self.assertIn('REJECTED', [row['status'] for row in both['findings']])
        with self.assertRaises(ValueError):
            self.consume(DATA, proof(b'\xff'+attestation(1)+b'\x99'), [good])

    def command(self, *args, human=False):
        command = [str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'), 'mainline', *args]
        if not human:
            command.append('--json')
        process = subprocess.run(command, capture_output=True, text=True, timeout=45)
        return process, process.stdout if human else json.loads(process.stdout)

    def test_mainline_consumes_the_retained_pair_and_keeps_real_state_unresolved(self):
        process, result = self.command()
        time = next(row for row in result['modules'] if row['id'] == 'time-and-durability')
        self.assertEqual(time['public_example'].get('header_binding', {}).get('status'), 'OBSERVED')
        self.assertEqual(time['status'], 'MISSING')
        self.assertEqual(time['public_example']['bitcoin_verification'], 'NOT_CHECKED')
        self.assertEqual(result['real_admission'], 'NOT_READY')
        self.assertEqual(result['protocol_state_change'], 'NONE')
        self.assertFalse(result['prospective_eligible'])
        self.assertEqual(process.returncode, 1)
        human, text = self.command(human=True)
        self.assertEqual(human.returncode, 1)
        self.assertIn('区块头字节绑定', text)
        self.assertIn('Bitcoin链与完整证明未验证', text)

    def test_explicit_missing_or_replaced_header_directory_never_falls_back(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            for replaced in (False, True):
                if replaced:
                    shutil.copytree(PACKAGE/'raw', directory/'raw')
                    target = directory/'raw/mempool-header.hex'
                    target.write_bytes(b'0'*160)
                process, result = self.command('--header-inputs', str(directory))
                rows = {row['id']: row for row in result['modules']}
                header = rows['time-and-durability']['public_example']['header_binding']
                self.assertEqual(header['status'], 'REJECTED' if replaced else 'MISSING')
                self.assertEqual(rows['time-and-durability']['public_example']['body_computation']['operation_count'], 40)
                self.assertEqual(rows['economic-data']['status'], 'OBSERVED')
                self.assertEqual(result['real_admission'], 'NOT_READY')
                self.assertEqual(process.returncode, 2 if replaced else 1)


if __name__ == '__main__':
    unittest.main()
