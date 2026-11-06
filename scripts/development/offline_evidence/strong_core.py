"""Internal OTS/header/Core-reply consistency, not node or protocol authority.

A fixed, independently admitted driver must supply the real read interface and
policy. Calling this with matching dictionaries, a version string or a test RPC
does not establish owner-controlled Core, chain provenance, Strong or readiness.
"""
import hashlib
import re
from typing import NamedTuple
from .strong_inputs import capture_request
from .ots_body import consume_ots_paths, check_header_pow

HEX64=re.compile('[0-9a-f]{64}',re.ASCII)
HEX160=re.compile('[0-9a-f]{160}',re.ASCII)


class CoreInputConflict(ValueError):pass
class CoreEvidenceMissing(ValueError):pass
class CoreUnsupported(ValueError):pass


class AnchorObservation(NamedTuple):
    height: int
    block_hash: str
    header_sha256: str
    confirmations: int


class CorePathObservation(NamedTuple):
    bundle_sha256: str
    proof_sha256: str
    reported_node_subversion: str
    tip_height: int
    tip_hash: str
    anchors: tuple[AnchorObservation,...]


def _integer(value,minimum=0,maximum=2**31-1):
    return type(value) is int and minimum<=value<=maximum


def _object(value):
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise CoreInputConflict('CORE_REPLY_OBJECT_REQUIRED')
    return value


def _digest(value):return type(value) is str and HEX64.fullmatch(value) is not None


def _rpc(read,method,*args):
    try:reply=read(method,*args)
    except Exception:raise CoreEvidenceMissing('CORE_RPC_UNAVAILABLE_'+method.upper()) from None
    if reply is None:raise CoreEvidenceMissing('CORE_REPLY_MISSING_'+method.upper())
    return reply


def _chain(value):
    value=_object(value)
    try:
        chain,ibd,blocks,headers,tip,work=[value[key] for key in (
            'chain','initialblockdownload','blocks','headers','bestblockhash','chainwork')]
    except KeyError:raise CoreEvidenceMissing('CORE_CHAIN_FIELDS_MISSING') from None
    if (type(chain) is not str or chain!='main' or ibd is not False or
            not _integer(blocks) or not _integer(headers) or blocks!=headers or
            not _digest(tip) or not _digest(work) or int(work,16)==0):
        raise CoreInputConflict('CORE_CHAIN_STATE_UNSUPPORTED_OR_CONFLICTING')
    # Copy primitive values now; an alias to a mutable read adapter must not
    # rewrite the historical begin-snapshot during a later query.
    return (blocks,headers,tip,work,chain,ibd)


def _header(height,block_hash,raw_hex,verbose,tip_height,minimum):
    if not _digest(block_hash):raise CoreInputConflict('CORE_ACTIVE_HASH_FORMAT')
    if type(raw_hex) is not str or HEX160.fullmatch(raw_hex) is None:
        raise CoreInputConflict('CORE_RAW_HEADER_FORMAT')
    raw=bytes.fromhex(raw_hex)
    computed=hashlib.sha256(hashlib.sha256(raw).digest()).digest()[::-1].hex()
    if computed!=block_hash:raise CoreInputConflict('CORE_HEADER_HASH_MISMATCH')
    verbose=_object(verbose)
    expected={'hash':block_hash,'height':height,
        'version':int.from_bytes(raw[:4],'little',signed=True),
        'versionHex':format(int.from_bytes(raw[:4],'little'),'08x'),
        'merkleroot':raw[36:68][::-1].hex(),'time':int.from_bytes(raw[68:72],'little'),
        'bits':format(int.from_bytes(raw[72:76],'little'),'08x'),'nonce':int.from_bytes(raw[76:80],'little')}
    if height>0:expected['previousblockhash']=raw[4:36][::-1].hex()
    for key,value in expected.items():
        if key not in verbose:raise CoreEvidenceMissing('CORE_HEADER_FIELD_MISSING_'+key.upper())
        if type(verbose[key]) is not type(value) or verbose[key]!=value:
            raise CoreInputConflict('CORE_HEADER_FIELD_MISMATCH_'+key.upper())
    confirmations=verbose.get('confirmations')
    if (not _integer(confirmations,1) or confirmations!=tip_height-height+1 or confirmations<minimum):
        raise CoreInputConflict('CORE_CONFIRMATION_DEPTH_OR_ARITHMETIC')
    pow_result=check_header_pow(raw_hex.encode('ascii'))
    if pow_result['status']!='OBSERVED':raise CoreInputConflict('CORE_HEADER_POW_MISMATCH')
    if 'target' in verbose and verbose['target']!=pow_result['target_hex']:
        raise CoreInputConflict('CORE_HEADER_TARGET_MISMATCH')
    return raw,AnchorObservation(height,block_hash,hashlib.sha256(raw).hexdigest(),confirmations)


def observe_core_paths(request_raw,rpc,*,minimum_confirmations,expected_node_version,expected_subversion):
    """Compute all supplied Bitcoin-anchor checks against sampled read replies.

    No default confirmation policy or caller eligibility assertion exists.
    This internal callback seam is not a public authoritative entry point.
    """
    if (not _integer(minimum_confirmations,1) or not _integer(expected_node_version,1) or
            type(expected_subversion) is not str or not 0<len(expected_subversion)<=128 or not callable(rpc)):
        raise CoreInputConflict('EXPLICIT_TYPED_CORE_POLICY_REQUIRED')
    snapshot=capture_request(request_raw)
    try:body=consume_ots_paths(snapshot.bundle_bytes,snapshot.proof_bytes)
    except ValueError as error:
        # The existing reader intentionally supports a bounded operation set.
        # Failure here is not a universal OTS validity or Bitcoin verdict.
        raise CoreUnsupported('OTS_BODY_NOT_CONSUMABLE_'+str(error)) from None
    attestations=body['bitcoin_attestations']
    if not attestations:raise CoreEvidenceMissing('BITCOIN_ATTESTATION_MISSING')
    if any(not _integer(row['claimed_height']) for row in attestations):raise CoreUnsupported('BITCOIN_HEIGHT_RANGE')
    heights=sorted({row['claimed_height'] for row in attestations})
    if len(heights)>32:raise CoreUnsupported('BITCOIN_DISTINCT_HEIGHT_LIMIT')
    network=_object(_rpc(rpc,'getnetworkinfo'))
    if (type(network.get('version')) is not int or network['version']!=expected_node_version or
            type(network.get('subversion')) is not str or network['subversion']!=expected_subversion):
        raise CoreInputConflict('CORE_REPORTED_VERSION_MISMATCH')
    before=_chain(_rpc(rpc,'getblockchaininfo'))
    if heights[-1]>before[0]:raise CoreEvidenceMissing('BITCOIN_HEIGHT_ABOVE_VALIDATED_TIP')
    headers={};anchors=[]
    for height in heights:
        block_hash=_rpc(rpc,'getblockhash',height)
        if not _digest(block_hash):raise CoreInputConflict('CORE_ACTIVE_HASH_FORMAT')
        raw_hex=_rpc(rpc,'getblockheader',block_hash,False)
        verbose=_rpc(rpc,'getblockheader',block_hash,True)
        raw,anchor=_header(height,block_hash,raw_hex,verbose,before[0],minimum_confirmations)
        if height==before[0] and block_hash!=before[2]:raise CoreInputConflict('CORE_TIP_HEADER_HASH_MISMATCH')
        headers[height]=raw;anchors.append(anchor)
    # Examine every supplied path, including later paths at an already-cached
    # height. A first successful anchor cannot conceal a later mismatch.
    for row in attestations:
        if row['commitment_hex']!=headers[row['claimed_height']][36:68].hex():
            raise CoreInputConflict('OTS_HEADER_MERKLE_ROOT_MISMATCH')
    after=_chain(_rpc(rpc,'getblockchaininfo'))
    if before!=after:raise CoreEvidenceMissing('CORE_CHAIN_SNAPSHOT_CHANGED')
    return CorePathObservation(snapshot.bundle_sha256,snapshot.proof_sha256,
                               expected_subversion,before[0],before[2],tuple(anchors))
