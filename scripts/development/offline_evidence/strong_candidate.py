"""Candidate seven-field ABI, gated by a separately recorded local operation.

The local record is an operator execution control, not an authority proof.
Actual human approval provenance and independent runtime admission are external
requirements; this file's hashes and process observations cannot create them.
"""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import sys
import time
from .core_cli import CoreCLI,read_fixed
from .strong_inputs import capture_request,MAX_REQUEST_BYTES
from .strong_core import observe_core_paths


class CandidateUnresolved(ValueError):pass


def profile_bytes(profile):return json.dumps(profile,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')


def _pairs(items):
    value={}
    for key,item in items:
        if key in value:raise CandidateUnresolved('AUTHORIZATION_DUPLICATE_KEY')
        value[key]=item
    return value


def _utc(value):
    if type(value) is not str or re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z',value,re.ASCII) is None:
        raise CandidateUnresolved('AUTHORIZATION_UTC_FORMAT')
    return datetime.fromisoformat(value.replace('Z','+00:00'))


def read_authorization(raw_request,snapshot,profile):
    try:raw=read_fixed(profile['authorization_path'],maximum=65536)
    except OSError:raise CandidateUnresolved('AUTHORIZATION_INPUT_MISSING_OR_UNREADABLE') from None
    try:auth=json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs)
    except (ValueError,UnicodeError,RecursionError):raise CandidateUnresolved('AUTHORIZATION_JSON_INVALID') from None
    keys={'format','authorization_scope','runtime_profile_sha256','request_sha256','subject_sha256','proof_sha256',
          'owned_core_pid','authorized_at_utc','expires_at_utc','authorized_by','authorization_sha256'}
    if type(auth) is not dict or set(auth)!=keys or any(type(key) is not str for key in auth):raise CandidateUnresolved('AUTHORIZATION_FIELDS')
    core={key:value for key,value in auth.items() if key!='authorization_sha256'}
    expected={'format':'FP_DEV_STRONG_CORE_READ_AUTH_V1','authorization_scope':'ONE_PUBLIC_SUBJECT_CORE_READ_CHECK',
              'runtime_profile_sha256':hashlib.sha256(profile_bytes(profile)).hexdigest(),
              'request_sha256':hashlib.sha256(raw_request).hexdigest(),
              'subject_sha256':snapshot.bundle_sha256,'proof_sha256':snapshot.proof_sha256,
              'authorization_sha256':hashlib.sha256(profile_bytes(core)).hexdigest()}
    if any(type(auth[key]) is not str or auth[key]!=value for key,value in expected.items()):raise CandidateUnresolved('AUTHORIZATION_BINDING_MISMATCH')
    if type(auth['owned_core_pid']) is not int or not 1<auth['owned_core_pid']<2**31:raise CandidateUnresolved('OWNED_CORE_PID_REQUIRED')
    if type(auth['authorized_by']) is not str or not 0<len(auth['authorized_by'])<=128:raise CandidateUnresolved('AUTHORIZATION_ACTOR_REQUIRED')
    now=datetime.now(timezone.utc)
    if not _utc(auth['authorized_at_utc'])<=now<_utc(auth['expires_at_utc']):raise CandidateUnresolved('AUTHORIZATION_NOT_CURRENT')
    return auth


def wire_result(snapshot,observed):
    anchor=observed.anchors[0]
    return {'schema_version':'1.0','action':'verify-bitcoin-durability','verification_mode':'OWNER_CONTROLLED_BITCOIN_CORE',
            'bundle_sha256':snapshot.bundle_sha256,'proof_sha256':snapshot.proof_sha256,'verified':True,
            'bitcoin_block_height':anchor.height,'bitcoin_block_hash':anchor.block_hash,
            'bitcoin_header_sha256':anchor.header_sha256,'node_version':observed.reported_node_subversion}


def run_request(raw_request,profile):
    snapshot=capture_request(raw_request)
    auth=read_authorization(raw_request,snapshot,profile)
    reservation=Path(profile['reservation_path'])
    if reservation.exists() or reservation.is_symlink():raise CandidateUnresolved('CORE_READ_ALREADY_RESERVED')
    expires=_utc(auth['expires_at_utc'])
    remaining=(expires-datetime.now(timezone.utc)).total_seconds()
    if remaining<=0:raise CandidateUnresolved('AUTHORIZATION_NOT_CURRENT')
    deadline=time.monotonic()+min(profile['limits']['work_seconds'],remaining)
    client=CoreCLI(profile,owned_pid=auth['owned_core_pid'],deadline=deadline,expires_at=expires)
    client.verify_binding()
    if datetime.now(timezone.utc)>=expires or time.monotonic()>=deadline:
        raise CandidateUnresolved('AUTHORIZATION_EXPIRED_BEFORE_RESERVATION')
    # No record grants its own external approval. This reservation is created
    # only on the separately approved exact local operation's execution path.
    with reservation.open('x') as stream:
        json.dump({'authorization_sha256':auth['authorization_sha256'],'request_sha256':auth['request_sha256'],
                   'state':'RESERVED_MAY_HAVE_READ','protocol_state_change':'NONE'},stream,sort_keys=True)
        stream.flush();os.fsync(stream.fileno())
    observed=observe_core_paths(raw_request,client,**profile['policy'])
    client.verify_binding()
    if datetime.now(timezone.utc)>=expires or time.monotonic()>=deadline:
        raise CandidateUnresolved('AUTHORIZATION_EXPIRED_BEFORE_RESULT')
    return wire_result(snapshot,observed)


def main(profile):
    if sys.argv[1:]==['--describe']:
        print(json.dumps({'format':'FP_DEV_STRONG_EXECUTABLE_CANDIDATE_V1','scope':profile['scope'],
             'runtime_profile_sha256':hashlib.sha256(profile_bytes(profile)).hexdigest(),
             'source_count':len(profile.get('sources',{})),'default_requires_separate_actual_operation_approval':True,
             'source_identity_does_not_establish_full_runtime_trust':True,'real_admission':'NOT_READY','protocol_state_change':'NONE'},sort_keys=True))
        return 0
    if sys.argv[1:]:return 2
    previous={}
    def stopped(signum,frame):raise KeyboardInterrupt
    for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):previous[sig]=signal.signal(sig,stopped)
    try:
        raw=sys.stdin.buffer.read(MAX_REQUEST_BYTES+1)
        value=run_request(raw,profile)
        sys.stdout.write(json.dumps(value,sort_keys=True,separators=(',',':'))+'\n');return 0
    except (ValueError,OSError,KeyError,TypeError,KeyboardInterrupt):
        # Never print arbitrary path/RPC stderr/request/exception content.
        sys.stderr.write('STRONG_OPERATION_UNRESOLVED_OR_REJECTED\n');return 2
    finally:
        for sig,handler in previous.items():signal.signal(sig,handler)
