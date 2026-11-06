"""Strong process-input boundary only; no Core, keys, claims or network."""
import base64
import hashlib
import json
from pathlib import Path
from types import ModuleType
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
MAGIC=bytes.fromhex('004f70656e54696d657374616d7073000050726f6f6600bf89e2e884e89294')


class StrongInputTests(unittest.TestCase):
    def consumer(self):
        path=HERE/'strong_inputs.py'
        self.assertTrue(path.is_file(),'Strong process-input parser is missing')
        module=ModuleType('fp_strong_request_test');module.__file__=str(path)
        exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__)
        return module

    def request(self,bundle=b'{ "public": "parser sample" }',proof=None):
        # This short header is deliberately not a complete OTS proof.
        if proof is None:proof=MAGIC+b'\x01\x08'+hashlib.sha256(bundle).digest()
        return {'schema_version':'1.0','action':'verify-bitcoin-durability',
                'verification_mode':'OWNER_CONTROLLED_BITCOIN_CORE',
                'bundle_sha256':hashlib.sha256(bundle).hexdigest(),
                'bundle_base64':base64.b64encode(bundle).decode('ascii'),
                'proof_sha256':hashlib.sha256(proof).hexdigest(),
                'proof_base64':base64.b64encode(proof).decode('ascii')}

    def encode(self,value):return json.dumps(value,separators=(',',':')).encode()

    def test_real_public_opaque_bytes_preserved_without_claiming_bundle_or_strong(self):
        consumer=self.consumer()
        directory=ROOT/'docs/development/mainline-execution-2026-10-09-rev-001/gdp-public-proof-pair-2026-10-15-rev-001/raw'
        bundle=(directory/'gdp2q25-2nd.pdf').read_bytes();proof=(directory/'gdp2q25-2nd.pdf.ots').read_bytes()
        self.assertEqual(hashlib.sha256(bundle).hexdigest(),'c70972a12908b73c2407d9cc6842ba2a02203a690f3090cd29f30c45f0cfd93d')
        self.assertEqual(hashlib.sha256(proof).hexdigest(),'0a63adf8a7b47b68d42aec05f365f78a631e64f734b8af5bc594188ee2d751e9')
        result=consumer.capture_request(self.encode(self.request(bundle,proof)))
        self.assertEqual(result.bundle_bytes,bundle);self.assertEqual(result.proof_bytes,proof)
        self.assertEqual(result.bundle_sha256,hashlib.sha256(bundle).hexdigest())
        self.assertFalse(hasattr(result,'verified'));self.assertFalse(hasattr(result,'real_admission'))

    def test_semantically_equal_reserialization_cannot_reuse_old_raw_proof(self):
        consumer=self.consumer();original=b'{ "same" : "value" }'
        request=self.request(original)
        replacement=json.dumps(json.loads(original),separators=(',',':')).encode()
        self.assertNotEqual(original,replacement)
        request['bundle_base64']=base64.b64encode(replacement).decode()
        request['bundle_sha256']=hashlib.sha256(replacement).hexdigest()
        with self.assertRaisesRegex(ValueError,'OTS_SUBJECT_DIGEST'):consumer.capture_request(self.encode(request))

    def test_snapshot_is_immutable_and_header_only_input_has_no_proof_verdict(self):
        consumer=self.consumer();snapshot=consumer.capture_request(self.encode(self.request()))
        with self.assertRaises((AttributeError,TypeError)):snapshot.bundle_bytes=b'changed'
        self.assertFalse(hasattr(snapshot,'bitcoin_verified'))
        self.assertEqual(len(snapshot.proof_bytes),65)

    def test_missing_and_extra_fields_refused(self):
        consumer=self.consumer();request=self.request()
        for key in request:
            with self.subTest(key=key):
                changed=dict(request);changed.pop(key)
                with self.assertRaises(ValueError):consumer.capture_request(self.encode(changed))
        with self.assertRaises(ValueError):consumer.capture_request(self.encode(dict(request,verified=True)))

    def test_duplicate_key_even_if_value_matches_refused(self):
        consumer=self.consumer();request=self.request();raw=self.encode(request)
        raw=raw[:-1]+b',"schema_version":"1.0"}'
        with self.assertRaises(ValueError):consumer.capture_request(raw)

    def test_fixed_tokens_and_scalar_types_are_not_negotiated(self):
        consumer=self.consumer()
        for key,value in [('schema_version','1'),('action','verify'),('verification_mode','REMOTE_EXPLORER'),
                          ('bundle_sha256','A'*64),('proof_sha256','g'*64)]:
            with self.subTest(key=key):
                changed=self.request();changed[key]=value
                with self.assertRaises(ValueError):consumer.capture_request(self.encode(changed))
        for value in (None,True,1,1.0,[],{}):
            with self.subTest(value=value):
                changed=self.request();changed['bundle_base64']=value
                with self.assertRaises(ValueError):consumer.capture_request(self.encode(changed))

    def test_digest_substitution_refused_for_both_artifacts(self):
        consumer=self.consumer()
        for key in ('bundle_sha256','proof_sha256'):
            with self.subTest(key=key):
                request=self.request();request[key]='0'*64
                with self.assertRaisesRegex(ValueError,'DIGEST_MISMATCH'):consumer.capture_request(self.encode(request))

    def test_base64_padding_bits_whitespace_and_nonascii_refused(self):
        consumer=self.consumer()
        for value in ('Zh==','Zg','Zg===','Z g==','Zg==\n','Zg==é'):
            with self.subTest(value=value):
                request=self.request(b'f');request['bundle_base64']=value
                with self.assertRaises(ValueError):consumer.capture_request(self.encode(request))

    def test_empty_and_oversized_decoded_artifacts_refused_before_decode(self):
        consumer=self.consumer()
        for key,limit in [('bundle_base64',consumer.MAX_BUNDLE_BYTES),('proof_base64',consumer.MAX_PROOF_BYTES)]:
            for value in ('','A'*(4*((limit+2)//3)+4)):
                with self.subTest(key=key,length=len(value)):
                    request=self.request();request[key]=value
                    with mock.patch.object(consumer.base64,'b64decode',side_effect=AssertionError('decode ran before length rejection')):
                        with self.assertRaises(ValueError):consumer.capture_request(self.encode(request))

    def test_raw_limit_and_type_refuse_before_json_parser(self):
        consumer=self.consumer()
        for raw in (bytearray(b'{}'),'{}',b' '*(consumer.MAX_REQUEST_BYTES+1)):
            with self.subTest(type=type(raw)):
                with mock.patch.object(consumer.json,'loads',side_effect=AssertionError('parser ran before size/type rejection')):
                    with self.assertRaises(ValueError):consumer.capture_request(raw)

    def test_nested_or_many_fields_refuse_before_tree_expansion(self):
        consumer=self.consumer()
        for raw in (b'{"bundle_base64":[{}]}',b'{"bundle_base64":{"many":"nodes"}}',
                    b'{'+b','.join(b'"x":"y"' for _ in range(8))+b'}'):
            with self.subTest(raw=raw):
                with mock.patch.object(consumer.json,'loads',side_effect=AssertionError('tree parser reached')):
                    with self.assertRaises(ValueError):consumer.capture_request(raw)

    def test_bad_utf8_bom_trailing_json_and_nonfinite_refuse(self):
        consumer=self.consumer();raw=self.encode(self.request())
        for value in (b'\xff',b'\xef\xbb\xbf'+raw,raw+b'{}',raw[:-1]+b',"extra":NaN}',b'[]'):
            with self.subTest(value=value[:20]):
                with self.assertRaises(ValueError):consumer.capture_request(value)

    def test_ots_header_identity_version_algorithm_and_digest_refuse(self):
        consumer=self.consumer();valid=base64.b64decode(self.request()['proof_base64'])
        for bad in (valid[:64],b'x'+valid[1:],valid[:31]+b'\x02'+valid[32:],
                    valid[:32]+b'\x02'+valid[33:],valid[:33]+b'\0'*32):
            with self.subTest(proof=bad[:34]):
                request=self.request(proof=bad)
                with self.assertRaises(ValueError):consumer.capture_request(self.encode(request))


if __name__=='__main__':unittest.main()
