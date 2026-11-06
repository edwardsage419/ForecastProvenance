"""Internal Core calculation tests; RPC replies are retained/public or synthetic.

No node is contacted or started and no caller reply is promoted to trusted Core.
"""
import base64
import copy
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
HEIGHT=912095
BTC_TAG=bytes.fromhex('0588960d73d71901')
MAGIC=bytes.fromhex('004f70656e54696d657374616d7073000050726f6f6600bf89e2e884e89294')


def varuint(value):
    out=bytearray()
    while value>=128:out.append((value&127)|128);value>>=7
    out.append(value);return bytes(out)


def attestation(height):
    payload=varuint(height)
    return b'\0'+BTC_TAG+varuint(len(payload))+payload


class RetainedRPC:
    """Explicit test adapter, never proof of a live/owned node."""
    def __init__(self):
        path=ROOT/'docs/development/mainline-execution-2026-10-19-pruned-core-sample-execution-rev-001/online-107-RESULT.json'
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!='ba18857cf56230b93f280a18089b74ef89ae4967f7540b7da1eafd9353116294':
            raise AssertionError('registered public Core record changed')
        value=json.loads(raw)
        self.chain=copy.deepcopy(value['last_chain']['result'])
        self.after=None
        self.network=copy.deepcopy(value['last_network']['result'])
        self.verbose=copy.deepcopy(value['sample_header_verbose']['result'])
        self.raw=value['sample_header_raw']['result']
        self.hash=self.verbose['hash'];self.calls=[];self.chains=0
        self.mutate_on_raw=False

    def __call__(self,method,*args):
        self.calls.append((method,args))
        if method=='getnetworkinfo':return copy.deepcopy(self.network)
        if method=='getblockchaininfo':
            self.chains+=1
            if self.chains>1 and self.after is not None:return copy.deepcopy(self.after)
            return self.chain  # Deliberately exposes mutable source alias.
        if method=='getblockhash':
            if args!=(HEIGHT,):raise LookupError('no retained header for this other height')
            return self.hash
        if method=='getblockheader':
            if args[1] is False:
                if self.mutate_on_raw:self.chain['bestblockhash']='0'*64
                return self.raw
            return copy.deepcopy(self.verbose)
        raise AssertionError('unapproved RPC method '+method)


class StrongCoreTests(unittest.TestCase):
    def consumer(self):
        self.assertTrue((HERE/'strong_core.py').is_file(),'Strong Core kernel is missing')
        package='fp_strong_core_test';names=[package,*[package+'.'+name for name in ('strong_inputs','ots_body','strong_core')]]
        absent=object();old={name:sys.modules.get(name,absent) for name in names}
        try:
            namespace=ModuleType(package);namespace.__path__=[];sys.modules[package]=namespace
            for name in ('strong_inputs','ots_body','strong_core'):
                path=HERE/(name+'.py');module=ModuleType(package+'.'+name);module.__file__=str(path);module.__package__=package
                sys.modules[module.__name__]=module;exec(compile(path.read_bytes(),str(path),'exec'),module.__dict__)
            return module
        finally:
            for name,value in old.items():
                if value is absent:sys.modules.pop(name,None)
                else:sys.modules[name]=value

    def request(self,proof=None,subject=None):
        directory=ROOT/'docs/development/mainline-execution-2026-10-09-rev-001/gdp-public-proof-pair-2026-10-15-rev-001/raw'
        subject=(directory/'gdp2q25-2nd.pdf').read_bytes() if subject is None else subject
        proof=(directory/'gdp2q25-2nd.pdf.ots').read_bytes() if proof is None else proof
        value={'schema_version':'1.0','action':'verify-bitcoin-durability','verification_mode':'OWNER_CONTROLLED_BITCOIN_CORE',
               'bundle_base64':base64.b64encode(subject).decode('ascii'),'bundle_sha256':hashlib.sha256(subject).hexdigest(),
               'proof_base64':base64.b64encode(proof).decode('ascii'),'proof_sha256':hashlib.sha256(proof).hexdigest()}
        return json.dumps(value,separators=(',',':')).encode()

    def observe(self,consumer,rpc,raw=None,**kwargs):
        policy={'minimum_confirmations':6,'expected_node_version':310100,'expected_subversion':'/Satoshi:31.1.0/'}
        policy.update(kwargs)
        return consumer.observe_core_paths(self.request() if raw is None else raw,rpc,**policy)

    def test_public_retained_values_compute_without_claiming_core_control(self):
        consumer=self.consumer();rpc=RetainedRPC();result=self.observe(consumer,rpc)
        self.assertEqual(result.anchors[0].height,HEIGHT)
        self.assertEqual(result.anchors[0].confirmations,60905)
        self.assertEqual(result.tip_height,972999)
        self.assertEqual(result.anchors[0].block_hash,rpc.hash)
        self.assertFalse(hasattr(result,'verified'));self.assertFalse(hasattr(result,'owner_controlled'))
        self.assertEqual({name for name,args in rpc.calls},{'getnetworkinfo','getblockchaininfo','getblockhash','getblockheader'})
        with self.assertRaises((AttributeError,TypeError)):result.tip_height=0

    def test_policy_parameters_are_explicit_and_strict_before_rpc(self):
        consumer=self.consumer()
        for kwargs in ({'minimum_confirmations':0},{'minimum_confirmations':True},{'minimum_confirmations':1.5},
                       {'expected_node_version':True},{'expected_subversion':''}):
            rpc=RetainedRPC()
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):self.observe(consumer,rpc,**kwargs)
            self.assertFalse(rpc.calls)

    def test_bad_request_or_truncated_body_stops_before_rpc(self):
        consumer=self.consumer();rpc=RetainedRPC()
        for raw in (b'{}',self.request(proof=MAGIC+b'\x01\x08'+hashlib.sha256(b'x').digest(),subject=b'x')):
            with self.assertRaises(ValueError):self.observe(consumer,rpc,raw)
        self.assertFalse(rpc.calls)

    def test_pending_only_proof_is_missing_not_verified_false(self):
        consumer=self.consumer();rpc=RetainedRPC();subject=b'declared public parser sample'
        uri=b'https://example.com';payload=varuint(len(uri))+uri
        proof=MAGIC+b'\x01\x08'+hashlib.sha256(subject).digest()+b'\0'+bytes.fromhex('83dfe30d2ef90c8e')+varuint(len(payload))+payload
        with self.assertRaises(consumer.CoreEvidenceMissing):self.observe(consumer,rpc,self.request(proof,subject))
        self.assertFalse(rpc.calls)

    def test_node_version_and_subversion_do_not_use_truthiness(self):
        consumer=self.consumer()
        for key,value in [('version',True),('version',310099),('subversion','unbound')]:
            rpc=RetainedRPC();rpc.network[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.observe(consumer,rpc)

    def test_wrong_network_ibd_or_incomplete_chain_rejected(self):
        consumer=self.consumer()
        for key,value in [('chain','signet'),('initialblockdownload',True),('initialblockdownload',0),
                          ('blocks',True),('headers',973000),('bestblockhash','x'*64),('chainwork','0')]:
            rpc=RetainedRPC();rpc.chain[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.observe(consumer,rpc)

    def test_active_chain_lookup_and_raw_hash_are_cross_checked(self):
        consumer=self.consumer()
        for which in ('lookup','raw'):
            rpc=RetainedRPC()
            if which=='lookup':rpc.hash='0'*64
            else:rpc.raw=rpc.raw[:-2]+'00'
            with self.subTest(which=which),self.assertRaises(ValueError):self.observe(consumer,rpc)

    def test_verbose_header_fields_are_bound_to_raw_bytes(self):
        consumer=self.consumer()
        for field,value in [('hash','0'*64),('height',HEIGHT+1),('version',True),('merkleroot','0'*64),
                            ('time',0),('nonce',0),('bits','1d00ffff'),('previousblockhash','0'*64)]:
            rpc=RetainedRPC();rpc.verbose[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):self.observe(consumer,rpc)

    def test_declared_pow_is_checked_even_for_self_consistent_rpc_labels(self):
        consumer=self.consumer();rpc=RetainedRPC();raw=bytearray.fromhex(rpc.raw);raw[76:80]=b'\0'*4
        rpc.raw=raw.hex();rpc.hash=hashlib.sha256(hashlib.sha256(raw).digest()).digest()[::-1].hex()
        rpc.verbose.update(hash=rpc.hash,nonce=0)
        with self.assertRaisesRegex(ValueError,'POW'):self.observe(consumer,rpc)

    def test_confirmation_depth_is_positive_integer_exact_tip_arithmetic(self):
        consumer=self.consumer()
        for confirmations in (True,-1,0,60904):
            rpc=RetainedRPC();rpc.verbose['confirmations']=confirmations
            with self.subTest(confirmations=confirmations),self.assertRaises(ValueError):self.observe(consumer,rpc)
        rpc=RetainedRPC();rpc.chain.update(blocks=HEIGHT+4,headers=HEIGHT+4);rpc.verbose['confirmations']=5
        with self.assertRaisesRegex(ValueError,'CONFIRMATION'):self.observe(consumer,rpc)

    def test_tip_and_chainwork_change_cannot_reuse_previous_header_check(self):
        consumer=self.consumer()
        for key,value in [('bestblockhash','0'*64),('chainwork','f'*64),('blocks',973000)]:
            rpc=RetainedRPC();rpc.after=copy.deepcopy(rpc.chain);rpc.after[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.observe(consumer,rpc)

    def test_mutable_rpc_response_alias_cannot_rewrite_begin_snapshot(self):
        consumer=self.consumer();rpc=RetainedRPC();rpc.mutate_on_raw=True
        with self.assertRaisesRegex(ValueError,'CHAIN_SNAPSHOT'):self.observe(consumer,rpc)

    def test_missing_rpc_response_is_unknown_evidence_not_false_success(self):
        consumer=self.consumer()
        def unavailable(method,*args):raise OSError('declared unavailable local test transport')
        with self.assertRaises(consumer.CoreEvidenceMissing):self.observe(consumer,unavailable)

    def test_later_missing_bitcoin_anchor_is_not_masked_by_first_success(self):
        consumer=self.consumer();rpc=RetainedRPC()
        directory=ROOT/'docs/development/mainline-execution-2026-10-09-rev-001/gdp-public-proof-pair-2026-10-15-rev-001/raw'
        proof=(directory/'gdp2q25-2nd.pdf.ots').read_bytes();original=attestation(HEIGHT)
        self.assertEqual(proof.count(original),1)
        proof=proof.replace(original,b'\xff'+original+attestation(HEIGHT+1))
        with self.assertRaises(consumer.CoreEvidenceMissing):self.observe(consumer,rpc,self.request(proof))
        self.assertIn(('getblockhash',(HEIGHT,)),rpc.calls)
        self.assertIn(('getblockhash',(HEIGHT+1,)),rpc.calls)


if __name__=='__main__':unittest.main()
