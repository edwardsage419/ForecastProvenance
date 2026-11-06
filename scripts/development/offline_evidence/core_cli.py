"""Bounded internal read-only Core CLI adapter; no node startup or key access.

The admitted driver supplies a fixed public runtime profile and the PID from
its owned launch. File/UID/comm/listener checks are local observations, not a
portable proof of full runtime trust or project authority. Python never reads,
exports or logs RPC cookies; bitcoin-cli necessarily uses its normal local
cookie authentication. Wallets/keyrings/signing private keys are not accessed.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import re
import selectors
import signal
import stat
import subprocess
import time
from datetime import datetime,timezone


class CoreRuntimeError(ValueError):pass


def read_fixed(path,*,size=None,digest=None,maximum=32*1024*1024):
    path=Path(path)
    if not path.is_absolute():raise CoreRuntimeError('PUBLIC_RUNTIME_PATH_NOT_ABSOLUTE')
    current=Path(path.anchor)
    for part in path.parts[1:]:
        current=current/part
        if stat.S_ISLNK(current.lstat().st_mode):raise CoreRuntimeError('PUBLIC_RUNTIME_SYMLINK')
    if size is not None and (type(size) is not int or not 0<size<=maximum):raise CoreRuntimeError('PUBLIC_RUNTIME_SIZE_BOUND')
    limit=maximum if size is None else size
    with os.fdopen(os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK),'rb') as stream:
        info=os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size>limit:raise CoreRuntimeError('PUBLIC_RUNTIME_TYPE_OR_SIZE')
        data=stream.read(limit+1)
    if len(data)>limit or (size is not None and len(data)!=size):raise CoreRuntimeError('PUBLIC_RUNTIME_SIZE_MISMATCH')
    if digest is not None and hashlib.sha256(data).hexdigest()!=digest:raise CoreRuntimeError('PUBLIC_RUNTIME_HASH_MISMATCH')
    return data


def run_bounded(command,*,deadline,timeout_seconds,output_limit):
    if (type(timeout_seconds) not in (int,float) or not math.isfinite(timeout_seconds) or timeout_seconds<=0 or
            type(output_limit) is not int or not 0<output_limit<=65536):raise CoreRuntimeError('COMMAND_LIMITS_INVALID')
    end=min(deadline,time.monotonic()+timeout_seconds)
    if end<=time.monotonic():raise CoreRuntimeError('WORK_DEADLINE')
    process=None;poller=None;output=bytearray();stopped=[False]
    previous={sig:signal.getsignal(sig) for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP)}
    def request_stop(signum,frame):stopped[0]=True
    # No raising signal handler may interrupt Popen between actual creation
    # and assignment of the child handle to this owned finally scope.
    try:
        for sig in previous:signal.signal(sig,request_stop)
        if stopped[0]:raise CoreRuntimeError('COMMAND_INTERRUPTED')
        process=subprocess.Popen(command,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL,start_new_session=True)
        poller=selectors.DefaultSelector()
        os.set_blocking(process.stdout.fileno(),False);poller.register(process.stdout,selectors.EVENT_READ)
        while True:
            if stopped[0]:raise CoreRuntimeError('COMMAND_INTERRUPTED')
            remaining=end-time.monotonic()
            if remaining<=0:raise CoreRuntimeError('COMMAND_TIMEOUT')
            if not poller.select(min(.1,remaining)):continue
            chunk=os.read(process.stdout.fileno(),min(65536,output_limit-len(output)+1))
            if not chunk:break
            output.extend(chunk)
            if len(output)>output_limit:raise CoreRuntimeError('COMMAND_STDOUT_LIMIT')
        remaining=end-time.monotonic()
        if remaining<=0:raise CoreRuntimeError('COMMAND_TIMEOUT')
        try:code=process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:raise CoreRuntimeError('COMMAND_TIMEOUT') from None
        if code!=0:raise CoreRuntimeError('COMMAND_FAILED')
        if stopped[0]:raise CoreRuntimeError('COMMAND_INTERRUPTED')
        return bytes(output)
    finally:
        for sig in previous:signal.signal(sig,signal.SIG_IGN)
        try:
            try:
                if poller is not None:poller.close()
            finally:
                if process is not None:
                    try:
                        if process.stdout is not None:process.stdout.close()
                    finally:
                        # Only this helper's new session, never the Core PID.
                        try:os.killpg(process.pid,signal.SIGTERM)
                        except ProcessLookupError:pass
                        try:process.wait(timeout=.1)
                        except subprocess.TimeoutExpired:pass
                        try:os.killpg(process.pid,signal.SIGKILL)
                        except ProcessLookupError:pass
                        process.wait(timeout=1)
        finally:
            for sig,handler in previous.items():signal.signal(sig,handler)


def _pairs(items):
    value={}
    for key,item in items:
        if key in value:raise CoreRuntimeError('CORE_JSON_DUPLICATE_KEY')
        value[key]=item
    return value


def _constant(_):raise CoreRuntimeError('CORE_JSON_NONFINITE')


def _float(value):
    number=float(value)
    if not math.isfinite(number):raise CoreRuntimeError('CORE_JSON_NONFINITE')
    return number


class CoreCLI:
    def __init__(self,profile,*,owned_pid,deadline,expires_at=None):
        self.core=profile['core'];self.limits=profile['limits'];self.pid=owned_pid;self.deadline=deadline;self.calls=0
        self.expires_at=expires_at
        if type(owned_pid) is not int or not 1<owned_pid<2**31:raise CoreRuntimeError('OWNED_CORE_PID_REQUIRED')
        self._endpoint()

    def _endpoint(self):
        if self.core['rpcconnect']!='127.0.0.1' or type(self.core['rpcport']) is not int or self.core['rpcport']!=28332:
            raise CoreRuntimeError('FIXED_LOOPBACK_ENDPOINT_REQUIRED')

    def _run(self,command):
        self.check_deadline()
        result=run_bounded(command,deadline=self.deadline,timeout_seconds=self.limits['command_seconds'],
                           output_limit=self.limits['stdout_bytes'])
        self.check_deadline()
        return result

    def check_deadline(self):
        now=time.monotonic()
        if self.expires_at is not None:
            remaining=(self.expires_at-datetime.now(timezone.utc)).total_seconds()
            self.deadline=min(self.deadline,now+remaining)
        if now>=self.deadline:raise CoreRuntimeError('WORK_OR_AUTHORIZATION_DEADLINE')

    def command(self,method,*args):
        self._endpoint()
        integer=lambda value:type(value) is int and 0<=value<2**31
        digest=lambda value:type(value) is str and re.fullmatch('[0-9a-f]{64}',value,re.ASCII) is not None
        valid=(type(method) is str and ((method in {'getnetworkinfo','getblockchaininfo'} and not args) or
               (method=='getblockhash' and len(args)==1 and integer(args[0])) or
               (method=='getblockheader' and len(args)==2 and digest(args[0]) and type(args[1]) is bool)))
        if not valid:raise CoreRuntimeError('RPC_METHOD_OR_PARAMETERS_NOT_ALLOWED')
        encoded=[('true' if value else 'false') if type(value) is bool else str(value) for value in args]
        return [self.core['cli']['path'],'-conf='+self.core['config']['path'],'-datadir='+self.core['datadir'],
                '-rpcconnect=127.0.0.1','-rpcport=28332','-rpcclienttimeout=5',method,*encoded]

    def verify_binding(self):
        self.check_deadline()
        for name in ('cli','daemon','config'):
            record=self.core[name];read_fixed(record['path'],size=record['bytes'],digest=record['sha256'])
        result=self._run([self.core['ps'],'-ww','-p',str(self.pid),'-o','uid=','-o','comm='])
        try:
            lines=result.decode('utf-8').strip().splitlines()
            uid,command=lines[0].split(None,1)
            if len(lines)!=1 or re.fullmatch('[0-9]+',uid,re.ASCII) is None or int(uid)!=os.geteuid() or command!=self.core['daemon']['path']:
                raise CoreRuntimeError('OWNED_CORE_PROCESS_MISMATCH')
        except (UnicodeError,IndexError,ValueError):raise CoreRuntimeError('OWNED_CORE_PROCESS_MISMATCH') from None
        result=self._run([self.core['lsof'],'-nP','-a','-p',str(self.pid),'-iTCP:28332','-sTCP:LISTEN','-Fn'])
        try:lines=result.decode('ascii').splitlines()
        except UnicodeError:raise CoreRuntimeError('OWNED_CORE_LISTENER_MISMATCH') from None
        if (len(lines)!=3 or lines[0]!='p'+str(self.pid) or re.fullmatch(r'f[0-9]{1,10}',lines[1],re.ASCII) is None or
                lines[2]!='n127.0.0.1:28332'):
            raise CoreRuntimeError('OWNED_CORE_LISTENER_MISMATCH')

    def __call__(self,method,*args):
        command=self.command(method,*args)
        if self.calls>=self.limits['maximum_RPC_calls']:raise CoreRuntimeError('RPC_COUNT_LIMIT')
        self.calls+=1;raw=self._run(command)
        if method=='getblockhash' or (method=='getblockheader' and args[1] is False):
            try:value=raw.decode('ascii').removesuffix('\n')
            except UnicodeError:raise CoreRuntimeError('CORE_HEX_REPLY_ENCODING') from None
            length=64 if method=='getblockhash' else 160
            if re.fullmatch('[0-9a-f]{'+str(length)+'}',value,re.ASCII) is None:raise CoreRuntimeError('CORE_HEX_REPLY_FORMAT')
            return value
        try:return json.loads(raw.decode('utf-8'),object_pairs_hook=_pairs,parse_constant=_constant,parse_float=_float)
        except (ValueError,UnicodeError,RecursionError):raise CoreRuntimeError('CORE_JSON_REPLY_INVALID') from None
