"""D236 finite input-integrity tests; no signing inputs or package bootstrap."""
import dataclasses
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'src/forecast_trust_core/_initial_acceptance_auth_inputs_v1.py'
RAW = ('{"content_sha256":"3893202108e035232d48d332e1fae1f040623bc2a0d9d5340114e11a35203d82",'
       '"object_id":"dev:data:one","object_type":"DevelopmentInput",'
       '"payload_sha256":"bdfe92367068a21462afd23be84e993370db4fc78763b6890f6f282619d0264c",'
       '"schema_version":"1.0","value":"é"}').encode('utf-8')
REF = ('dev:data:one', '3893202108e035232d48d332e1fae1f040623bc2a0d9d5340114e11a35203d82')
_LOADED = None


def load_subject(case):
    global _LOADED
    case.assertTrue(SOURCE.is_file(), 'D236 immutable authentication input layer is not implemented')
    if _LOADED is None:
        package = ModuleType('fp_d236_inputs')
        package.__path__ = [str(SOURCE.parent)]
        sys.modules[package.__name__] = package
        canonical_path = SOURCE.parent / 'canonical.py'
        case.assertEqual(hashlib.sha256(canonical_path.read_bytes()).hexdigest(),
                         'f9ef49579a5c54757c6660d377275a0ed5f8afdf646f33130651a711005ac9ba')
        for name, path in [('canonical', canonical_path), ('_initial_acceptance_auth_inputs_v1', SOURCE)]:
            spec = importlib.util.spec_from_file_location(package.__name__ + '.' + name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
        _LOADED = module
    return _LOADED


def public_data_at_depth(depth):
    # Ordinary test data only; independent stdlib fixture encoding, no FPP message.
    value = 0
    for _ in range(depth - 1):
        value = [value]
    payload = {'object_type': 'DevelopmentInput', 'schema_version': '1.0', 'value': value}
    encode = lambda obj: json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    obj = dict(payload, object_id='dev:data:depth', payload_sha256=hashlib.sha256(encode(payload)).hexdigest())
    digest = hashlib.sha256(encode(obj)).hexdigest()
    obj['content_sha256'] = digest
    return encode(obj), ('dev:data:depth', digest)


class InputSnapshotsTests(unittest.TestCase):
    def setUp(self):
        self.m = load_subject(self)

    def spec(self, role='profile', raw=RAW, **changes):
        values = dict(role=role, data_format='SEALED_JSON', expected_bytes=len(raw),
                      raw_sha256=hashlib.sha256(raw).hexdigest(), object_ref=REF,
                      object_type='DevelopmentInput', schema_version='1.0')
        values.update(changes)
        return self.m.InputSpec(**values)

    def binary(self, role, raw):
        return self.m.InputSpec(role=role, data_format='BYTES', expected_bytes=len(raw),
                                raw_sha256=hashlib.sha256(raw).hexdigest())

    def test_preserves_exact_raw_bytes_and_has_no_authority_result(self):
        result = self.m.freeze_inputs((self.spec(),), {'profile': RAW})
        self.assertEqual(result.status, 'OBSERVED')
        self.assertEqual(result.items[0].raw, RAW)
        self.assertEqual(result.items[0].object_ref, REF)
        self.assertEqual(result.public_authentication, 'NOT_ESTABLISHED')
        self.assertEqual(result.retained_bytes, 265)
        with self.assertRaises(dataclasses.FrozenInstanceError):
            result.items[0].raw = b'changed'

    def test_same_full_ref_reuses_one_snapshot_for_two_roles(self):
        separate_copy = bytes(bytearray(RAW))
        result = self.m.freeze_inputs((self.spec(), self.spec('carrier_profile')),
                                      {'profile': RAW, 'carrier_profile': separate_copy})
        self.assertEqual(result.status, 'OBSERVED')
        self.assertIs(result.items[0].raw, result.items[1].raw)
        self.assertEqual(result.retained_bytes, 265)

    def test_later_alias_failure_is_not_masked_by_first_success(self):
        result = self.m.freeze_inputs((self.spec(), self.spec('carrier_profile')),
                                      {'profile': RAW, 'carrier_profile': RAW + b' '})
        self.assertEqual(result.status, 'REJECTED')
        self.assertIn(('carrier_profile', 'RAW_SIZE_MISMATCH'), result.failures)

    def test_same_full_ref_with_different_declared_raw_is_rejected(self):
        alternate = RAW + b' '
        result = self.m.freeze_inputs((self.spec(), self.spec('carrier_profile', alternate)),
                                      {'profile': RAW, 'carrier_profile': alternate})
        self.assertEqual(result.status, 'REJECTED')
        self.assertIn(('carrier_profile', 'FULL_REF_RAW_CONFLICT'), result.failures)

    def test_missing_and_known_failure_are_both_retained(self):
        result = self.m.freeze_inputs((self.spec(), self.binary('artifact', b'known')),
                                      {'profile': RAW.replace(b'"1.0"', b'"9.0"')})
        self.assertEqual(result.status, 'REJECTED')
        self.assertIn(('profile', 'RAW_SHA256_MISMATCH'), result.failures)
        self.assertEqual(result.missing, ('artifact',))

    def test_raw_and_full_identity_are_separate(self):
        result = self.m.freeze_inputs((self.spec(object_ref=(REF[0], '0' * 64)),), {'profile': RAW})
        self.assertIn(('profile', 'FULL_REF_MISMATCH'), result.failures)
        self.assertNotIn(('profile', 'RAW_SHA256_MISMATCH'), result.failures)

    def test_valid_full_hash_does_not_hide_bad_payload_seal(self):
        obj = json.loads(RAW)
        obj['payload_sha256'] = '0' * 64
        del obj['content_sha256']
        digest = hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False,
                                           separators=(',', ':')).encode()).hexdigest()
        obj['content_sha256'] = digest
        raw = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
        result = self.m.freeze_inputs((self.spec(raw=raw, object_ref=(REF[0], digest)),), {'profile': raw})
        self.assertIn(('profile', 'SEALED_IDENTITY_INVALID'), result.failures)

    def test_type_and_version_must_match_independent_comparison_inputs(self):
        result = self.m.freeze_inputs((self.spec(object_type='OtherType', schema_version='2.0'),), {'profile': RAW})
        self.assertIn(('profile', 'OBJECT_TYPE_MISMATCH'), result.failures)
        self.assertIn(('profile', 'SCHEMA_VERSION_MISMATCH'), result.failures)

    def test_json_one_mib_boundary_keeps_original_whitespace(self):
        raw = RAW + b' ' * (1048576 - len(RAW))
        result = self.m.freeze_inputs((self.spec(raw=raw),), {'profile': raw})
        self.assertEqual(result.status, 'OBSERVED')
        self.assertEqual(len(result.items[0].raw), 1048576)
        oversized = raw + b' '
        result = self.m.freeze_inputs((self.spec(raw=oversized),), {'profile': oversized})
        self.assertIn(('profile', 'JSON_BYTE_LIMIT'), result.failures)
        self.assertEqual(result.items, ())

    def test_total_budget_is_checked_before_hashing_extra_input(self):
        block = b'x' * 67108864
        result = self.m.freeze_inputs((self.binary('artifact', block), self.binary('extra', b'x')),
                                      {'artifact': block, 'extra': b'x'})
        self.assertIn(('extra', 'TOTAL_BYTE_LIMIT'), result.failures)
        self.assertEqual(result.retained_bytes, 67108864)
        self.assertEqual([item.role for item in result.items], ['artifact'])

    def test_all_supplied_occurrences_are_charged_to_work_budget(self):
        block = b'x' * 33554433
        result = self.m.freeze_inputs((self.binary('a', block), self.binary('b', block)), {'a': block, 'b': block})
        self.assertIn(('b', 'TOTAL_BYTE_LIMIT'), result.failures)

    def test_depth_boundary_is_checked_before_recursive_json_parse(self):
        raw, ref = public_data_at_depth(64)
        result = self.m.freeze_inputs((self.spec(raw=raw, object_ref=ref),), {'profile': raw})
        self.assertEqual(result.status, 'OBSERVED')
        for raw in (public_data_at_depth(65)[0], b'[' * 10000):
            result = self.m.freeze_inputs((self.spec(raw=raw),), {'profile': raw})
            self.assertIn(('profile', 'JSON_DEPTH_LIMIT'), result.failures)

    def test_json_braces_inside_escaped_strings_do_not_count_as_depth(self):
        value = '[{' * 100 + '\\"' + ']}' * 100
        obj = {'object_type': 'DevelopmentInput', 'schema_version': '1.0', 'value': value}
        encode = lambda data: json.dumps(data, sort_keys=True, separators=(',', ':')).encode()
        obj.update(object_id='dev:data:string', payload_sha256=hashlib.sha256(encode(obj)).hexdigest())
        digest = hashlib.sha256(encode(obj)).hexdigest()
        obj['content_sha256'] = digest
        raw = encode(obj)
        result = self.m.freeze_inputs((self.spec(raw=raw, object_ref=('dev:data:string', digest)),), {'profile': raw})
        self.assertEqual(result.status, 'OBSERVED')

    def test_strict_json_rejections_do_not_repair_input(self):
        cases = [b'{"a":1,"a":2}', b'{"a":null}', b'{"a":1.0}', b'{"a":-0}',
                 b'{"a":9007199254740992}', b'{"a":NaN}', b'{"a":"\\ud800"}',
                 b'\xef\xbb\xbf{}', b'{"a":"\xff"}', b'{"\xc3\xa9":1}']
        for raw in cases:
            with self.subTest(raw=raw):
                result = self.m.freeze_inputs((self.spec(raw=raw),), {'profile': raw})
                self.assertIn(('profile', 'JSON_INVALID'), result.failures)
                self.assertEqual(result.items, ())

    def test_duplicate_role_is_a_failure(self):
        result = self.m.freeze_inputs((self.spec(), self.spec()), {'profile': RAW})
        self.assertIn(('profile', 'DUPLICATE_ROLE'), result.failures)

    def test_unexpected_role_is_rejected_without_consuming_its_value(self):
        class NeverConvert:
            def __bytes__(self):
                raise AssertionError('Unexpected value must not be read or converted')
        result = self.m.freeze_inputs((self.spec(),), {'profile': RAW, 'unlisted': NeverConvert()})
        self.assertIn(('unlisted', 'UNEXPECTED_ROLE'), result.failures)

    def test_mutable_bytes_and_active_mapping_are_rejected(self):
        result = self.m.freeze_inputs((self.spec(),), {'profile': bytearray(RAW)})
        self.assertIn(('profile', 'INPUT_BYTES_REQUIRED'), result.failures)
        class ActiveDict(dict):
            def items(self):
                raise AssertionError('Active mapping must not be inspected')
        result = self.m.freeze_inputs((self.spec(),), ActiveDict(profile=RAW))
        self.assertIn(('#inputs', 'INVALID_SUPPLIED_INPUTS'), result.failures)

    def test_empty_or_invalid_expected_set_does_not_establish_scope(self):
        self.assertEqual(self.m.freeze_inputs((), {}).status, 'MISSING')
        result = self.m.freeze_inputs((self.spec(expected_bytes=True),), {'profile': RAW})
        self.assertIn(('profile', 'INVALID_SPEC'), result.failures)
        subset = self.m.freeze_inputs((self.binary('one', b'one'),), {'one': b'one'})
        self.assertEqual(subset.status, 'OBSERVED')
        self.assertEqual(subset.public_authentication, 'NOT_ESTABLISHED')

    def test_excessive_control_count_is_rejected_before_inputs_are_processed(self):
        result = self.m.freeze_inputs((self.spec(),) * 2049, {'profile': RAW})
        self.assertIn(('#specs', 'INPUT_COUNT_LIMIT'), result.failures)
        self.assertEqual(result.items, ())

    def test_non_string_mapping_key_cannot_execute_equality_during_lookup(self):
        class ActiveKey:
            def __hash__(self):
                return hash('profile')
            def __eq__(self, other):
                raise AssertionError('Unsafe key equality was invoked')
        result = None
        try:
            result = self.m.freeze_inputs((self.spec(),), {ActiveKey(): RAW})
        except AssertionError:
            pass
        self.assertIsNotNone(result, 'Invalid keys must be refused before expected-role lookup')
        self.assertIn(('#inputs', 'INVALID_SUPPLIED_ROLE'), result.failures)
        self.assertEqual(result.items, ())

    def test_supplied_role_count_boundary_precedes_per_role_diagnostics(self):
        supplied = {'role:' + str(index): b'x' for index in range(2048)}
        specs = tuple(self.binary(role, raw) for role, raw in supplied.items())
        result = self.m.freeze_inputs(specs, supplied)
        self.assertEqual(result.status, 'OBSERVED')
        self.assertEqual(len(result.items), 2048)
        self.assertEqual(result.retained_bytes, 1)
        supplied['one-too-many'] = b'x'
        result = self.m.freeze_inputs(specs, supplied)
        self.assertEqual(result.failures, (('#inputs', 'INPUT_COUNT_LIMIT'),))
        self.assertEqual(result.items, ())
        self.assertEqual(result.total_bytes_supplied, 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
