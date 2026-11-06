"""Standalone declared-target PoW is not chain, height or time verification."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from types import ModuleType
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HEADERS = ROOT/'docs/development/mainline-execution-2026-10-19-public-bitcoin-header-rev-001/raw'
PROOF = ROOT/'docs/development/mainline-execution-2026-10-09-rev-001/gdp-public-proof-pair-2026-10-15-rev-001/raw'


class HeaderPowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.response = (HEADERS/'blockstream-header.hex').read_bytes()
        cls.pdf = (PROOF/'gdp2q25-2nd.pdf').read_bytes()
        cls.proof = (PROOF/'gdp2q25-2nd.pdf.ots').read_bytes()

    def consumer(self):
        path = HERE/'ots_body.py'; module = ModuleType('d192_test'); module.__file__ = str(path)
        exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
        self.assertTrue(callable(getattr(module, 'check_header_pow', None)), 'standalone PoW check missing')
        return module

    def records(self):
        return [{'source_id': source, 'claimed_height': 912095,
                 'block_hash_response': (HEADERS/f'{source}-height-912095.txt').read_bytes(),
                 'header_response': self.response} for source in ('blockstream', 'mempool')]

    def test_real_retained_header_and_independent_integer_oracle(self):
        result = self.consumer().check_header_pow(self.response)
        header = bytes.fromhex(self.response.decode()); digest = hashlib.sha256(hashlib.sha256(header).digest()).digest()
        # Independent literal decomposition of this retained header's 0x17022b91.
        target = int('022b91'+'00'*20, 16)
        self.assertEqual(result['status'], 'OBSERVED')
        self.assertEqual(result['target_hex'], format(target, '064x'))
        self.assertEqual(result['block_hash'], digest[::-1].hex())
        self.assertLessEqual(int(digest[::-1].hex(), 16), target)
        self.assertEqual(result['chain_verification'], 'NOT_CHECKED')
        self.assertEqual(result['required_target_at_height'], 'NOT_CHECKED')
        self.assertEqual(result['authenticated_time'], 'NOT_ESTABLISHED')

    def test_compact_small_exponents_and_valid_noncanonical_forms(self):
        module = self.consumer()
        for bits, target in [(0x01123456, 0x12), (0x02008000, 0x80), (0x02008001, 0x80),
                             (0x03008000, 0x8000), (0x04008000, 0x800000),
                             (0x1d00ffff, int('ffff'+'00'*26, 16))]:
            with self.subTest(bits=bits):
                self.assertEqual(module.decode_mainnet_pow_target(bits), target)

    def test_zero_negative_overflow_above_mainnet_and_wrong_types_reject(self):
        module = self.consumer()
        for bits in [0, 0x01003456, 0x01800000, 0x04923456, 0x23000001,
                     0x22000100, 0x21010000, 0x207fffff, 0x1d010000,
                     True, -1, 2**32, '17022b91']:
            with self.subTest(bits=bits), self.assertRaises(ValueError):
                module.decode_mainnet_pow_target(bits)

    def test_fixed_header_mutation_and_invalid_target_reject_without_nonce_search(self):
        module = self.consumer(); changed = bytearray.fromhex(self.response.decode()); changed[0] ^= 1
        target = int('022b91'+'00'*20, 16)
        digest = hashlib.sha256(hashlib.sha256(changed).digest()).digest()
        self.assertGreater(int.from_bytes(digest, 'little'), target)
        self.assertEqual(module.check_header_pow(changed.hex().encode())['status'], 'REJECTED')
        changed[72:76] = b'\x00'*4
        self.assertEqual(module.check_header_pow(changed.hex().encode())['status'], 'REJECTED')
        for raw in [b'', b'0'*158, b'F'*160, self.response+b'\n\n', bytearray(self.response)]:
            with self.assertRaises(ValueError):
                module.check_header_pow(raw)
        self.assertEqual(module.check_header_pow(self.response+b'\n')['status'], 'OBSERVED')

    def test_all_pow_inputs_and_missing_plus_rejection_are_preserved(self):
        module = self.consumer(); records = self.records()
        changed = bytearray.fromhex(self.response.decode()); changed[72:76] = b'\x00'*4
        records[1]['header_response'] = changed.hex().encode()
        result = module.consume_ots_header_links(self.pdf, self.proof, records)['standalone_pow']
        self.assertEqual(result['status'], 'REJECTED')
        self.assertEqual([row['status'] for row in result['headers']], ['OBSERVED', 'REJECTED'])
        del records[0]['header_response']
        result = module.consume_ots_header_links(self.pdf, self.proof, records)['standalone_pow']
        self.assertEqual(result['status'], 'REJECTED')
        self.assertIn('MISSING', [row['status'] for row in result['findings']])
        self.assertIn('REJECTED', [row['status'] for row in result['findings']])

    def test_byte_consistent_fabrication_does_not_pass_the_new_separate_pow_check(self):
        module = self.consumer()
        # Preserve the actual root and all bytes except invalid declared target;
        # recompute only the claimed hash to make the byte comparison consistent.
        changed = bytearray.fromhex(self.response.decode()); changed[72:76] = b'\x00'*4
        row = self.records()[0]; row['header_response'] = changed.hex().encode()
        row['block_hash_response'] = hashlib.sha256(hashlib.sha256(changed).digest()).digest()[::-1].hex().encode()
        result = module.consume_ots_header_links(self.pdf, self.proof, [row])
        self.assertEqual(result['header_binding']['status'], 'OBSERVED')
        self.assertEqual(result['header_binding']['proof_of_work'], 'NOT_CHECKED')
        self.assertEqual(result['standalone_pow']['status'], 'REJECTED')

    def test_mainline_displays_partial_pow_and_keeps_real_status_missing(self):
        process = subprocess.run([str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'),
                                  'mainline', '--json'], capture_output=True, text=True, timeout=45)
        result = json.loads(process.stdout)
        time = next(row for row in result['modules'] if row['id'] == 'time-and-durability')
        self.assertEqual(time['public_example'].get('standalone_pow', {}).get('status'), 'OBSERVED')
        self.assertEqual(time['status'], 'MISSING')
        self.assertEqual(time['public_example']['bitcoin_verification'], 'NOT_CHECKED')
        self.assertEqual(result['real_admission'], 'NOT_READY')
        self.assertEqual(process.returncode, 1)

    def test_later_controlled_pow_failure_reaches_time_parent_without_hiding_bytes(self):
        self.consumer()  # RED requires the real new API first.
        path = HERE/'mainline_worker.py'; worker = ModuleType('d192_worker'); worker.__file__ = str(path)
        original_read = Path.read_bytes
        exec(compile(original_read(path), str(path), 'exec'), worker.__dict__)
        # Failure propagation seam only; never evidence of an actual PoW failure.
        appended = b'''\n_original_pow = check_header_pow
_pow_calls = 0
def check_header_pow(raw):
    global _pow_calls
    _pow_calls += 1
    result = _original_pow(raw)
    if _pow_calls == 2:
        result.update(status='REJECTED', error='CONTROLLED_TEST_FAILURE')
    return result
'''
        def read(selected):
            value = original_read(selected)
            return value+appended if selected == HERE/'ots_body.py' else value
        with patch.object(Path, 'read_bytes', autospec=True, side_effect=read):
            result = worker.time_module(worker.PROOF_DIRECTORY)
        self.assertEqual(result['public_example']['header_binding']['status'], 'OBSERVED')
        self.assertEqual(result['public_example']['standalone_pow']['status'], 'REJECTED')
        self.assertEqual(result['status'], 'REJECTED')

    def test_explicit_missing_header_inputs_do_not_fall_back_to_default_pow(self):
        with tempfile.TemporaryDirectory() as directory:
            process = subprocess.run([str(ROOT/'.venv/bin/python'), '-I', '-B', str(HERE/'cli.py'),
                                      'mainline', '--header-inputs', directory, '--json'],
                                     capture_output=True, text=True, timeout=45)
            result = json.loads(process.stdout)
            rows = {row['id']: row for row in result['modules']}
            self.assertEqual(rows['time-and-durability']['public_example']['standalone_pow']['status'], 'MISSING')
            self.assertEqual(rows['economic-data']['status'], 'OBSERVED')
            self.assertEqual(process.returncode, 1)


if __name__ == '__main__':
    unittest.main()
