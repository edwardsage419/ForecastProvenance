"""Pure development decoder for the existing seven-field Strong process ABI.

Only immutable raw-byte and SHA256 detached-file-header bindings are checked.
No bundle-schema, OTS-body, Core, chain, authority or verification result is
established. Caps are development support limits, not adopted project rules.
"""
import base64
import binascii
import hashlib
import json
import re
from typing import NamedTuple

MAX_BUNDLE_BYTES=2*1024*1024
MAX_PROOF_BYTES=1024*1024
MAX_REQUEST_BYTES=5*1024*1024
MAGIC=bytes.fromhex('004f70656e54696d657374616d7073000050726f6f6600bf89e2e884e89294')
FIXED={'schema_version':'1.0','action':'verify-bitcoin-durability',
       'verification_mode':'OWNER_CONTROLLED_BITCOIN_CORE'}
FIELDS=frozenset(FIXED)|{'bundle_sha256','bundle_base64','proof_sha256','proof_base64'}
DIGEST=re.compile('[0-9a-f]{64}',re.ASCII)


class RequestError(ValueError):
    """Unsupported or inconsistent process input; no protocol verdict."""


class StrongRequestSnapshot(NamedTuple):
    bundle_bytes: bytes
    proof_bytes: bytes
    bundle_sha256: str
    proof_sha256: str


def _flat_preflight(raw):
    # The ABI has exactly one object and seven string-valued fields. Refuse
    # nested containers/large pair lists before JSON can allocate a tree.
    quoted=False;escaped=False;depth=0;fields=0
    for char in raw:
        if quoted:
            if escaped:escaped=False
            elif char==92:escaped=True
            elif char==34:quoted=False
        elif char==34:quoted=True
        elif char==123:
            depth+=1
            if depth>1:raise RequestError('REQUEST_NOT_FLAT')
        elif char==125:depth-=1
        elif char in (91,93):raise RequestError('REQUEST_NOT_FLAT')
        elif char==58:
            fields+=1
            if fields>7:raise RequestError('REQUEST_FIELD_COUNT')


def _pairs(items):
    value={}
    for key,item in items:
        if key in value:raise RequestError('DUPLICATE_REQUEST_KEY')
        value[key]=item
    return value


def _no_number(_):raise RequestError('REQUEST_NUMERIC_VALUE')


def _encoded_bound(value,limit):
    if (not value or not value.isascii() or len(value)%4 or
            len(value)>4*((limit+2)//3)):
        raise RequestError('BASE64_TYPE_SIZE_OR_ENCODING')
    padding=2 if value.endswith('==') else 1 if value.endswith('=') else 0
    if 3*(len(value)//4)-padding>limit:raise RequestError('DECODED_INPUT_LIMIT')


def capture_request(raw: bytes) -> StrongRequestSnapshot:
    """Capture exact decoded bytes; a successful return is not Strong success."""
    if type(raw) is not bytes or not 0<len(raw)<=MAX_REQUEST_BYTES:
        raise RequestError('REQUEST_BYTES_OR_LIMIT')
    _flat_preflight(raw)
    try:
        value=json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs,
                         parse_int=_no_number,parse_float=_no_number,parse_constant=_no_number)
    except RequestError:raise
    except (ValueError,UnicodeError,RecursionError) as error:
        raise RequestError('REQUEST_JSON_INVALID') from error
    if type(value) is not dict or set(value)!=FIELDS or any(type(item) is not str for item in value.values()):
        raise RequestError('REQUEST_FIELDS_OR_TYPES')
    if any(value[key]!=expected for key,expected in FIXED.items()):raise RequestError('REQUEST_FIXED_TOKEN')
    for name in ('bundle_sha256','proof_sha256'):
        if DIGEST.fullmatch(value[name]) is None:raise RequestError('REQUEST_DIGEST_FORMAT')
    # Both decoded bounds are checked before either payload is decoded.
    _encoded_bound(value['bundle_base64'],MAX_BUNDLE_BYTES)
    _encoded_bound(value['proof_base64'],MAX_PROOF_BYTES)
    decoded=[]
    for name in ('bundle','proof'):
        encoded=value[name+'_base64']
        try:artifact=base64.b64decode(encoded,validate=True)
        except (ValueError,binascii.Error) as error:raise RequestError('BASE64_INVALID') from error
        if base64.b64encode(artifact).decode('ascii')!=encoded:raise RequestError('BASE64_NONCANONICAL')
        digest=hashlib.sha256(artifact).hexdigest()
        if digest!=value[name+'_sha256']:raise RequestError(name.upper()+'_DIGEST_MISMATCH')
        decoded.append(artifact)
    bundle,proof=decoded
    if len(proof)<65 or proof[:31]!=MAGIC or proof[31:33]!=b'\x01\x08':
        raise RequestError('UNSUPPORTED_OTS_SHA256_FILE_HEADER')
    if proof[33:65].hex()!=value['bundle_sha256']:raise RequestError('OTS_SUBJECT_DIGEST_MISMATCH')
    return StrongRequestSnapshot(bundle,proof,value['bundle_sha256'],value['proof_sha256'])
