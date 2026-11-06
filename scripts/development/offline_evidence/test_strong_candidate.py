"""Candidate runtime refusals and bounded public Python children; no Core."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from types import ModuleType,SimpleNamespace
import unittest
from unittest import mock
from datetime import datetime,timezone,timedelta

HERE=Path(__file__).resolve().parent


class CandidateTests(unittest.TestCase):
    def modules(self):
        for name in ('core_cli','strong_candidate'):
            self.assertTrue((HERE/(name+'.py')).is_file(),'bounded Strong runtime module is missing')
        package='fp_strong_candidate_test';short=('strong_inputs','ots_body','strong_core','core_cli','strong_candidate')
        names=[package,*[package+'.'+name for name in short]];absent=object();old={n:sys.modules.get(n,absent) for n in names}
        loaded={}
        try:
            namespace=ModuleType(package);namespace.__path__=[];sys.modules[package]=namespace
            for name in short:
                path=HERE/(name+'.py');m=ModuleType(package+'.'+name);m.__package__=package;m.__file__=str(path)
                sys.modules[m.__name__]=m;exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);loaded[name]=m
            return loaded
        finally:
            for name,value in old.items():
                if value is absent:sys.modules.pop(name,None)
                else:sys.modules[name]=value

    @contextlib.contextmanager
    def profile(self):
        with tempfile.TemporaryDirectory(prefix='fp-strong-public-test-') as directory:
            root=Path(directory).resolve();core={}
            for name in ('cli','daemon','config'):
                path=root/name;raw=('public synthetic '+name).encode();path.write_bytes(raw)
                core[name]={'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
            core.update(datadir=str(root/'data'),rpcconnect='127.0.0.1',rpcport=28332,
                        ps='/bin/ps',lsof='/usr/sbin/lsof')
            profile={'format':'FP_DEV_STRONG_RUNTIME_V1','scope':'DEVELOPMENT_RESEARCH_ONLY_NOT_ADOPTED',
                     'core':core,'limits':{'work_seconds':90,'command_seconds':5,'stdout_bytes':65536,'maximum_RPC_calls':99},
                     'policy':{'minimum_confirmations':6,'expected_node_version':310100,'expected_subversion':'/Satoshi:31.1.0/'},
                     'authorization_path':str(root/'CORE_OPERATION_AUTHORIZATION.json'),
                     'reservation_path':str(root/'CORE_READ_RESERVED.json')}
            yield profile

    def raw_request(self,modules):
        import base64
        subject=b'public unit parser bytes'
        proof=modules['strong_inputs'].MAGIC+b'\x01\x08'+hashlib.sha256(subject).digest()
        value={'schema_version':'1.0','action':'verify-bitcoin-durability','verification_mode':'OWNER_CONTROLLED_BITCOIN_CORE',
            'bundle_base64':base64.b64encode(subject).decode(),'bundle_sha256':hashlib.sha256(subject).hexdigest(),
            'proof_base64':base64.b64encode(proof).decode(),'proof_sha256':hashlib.sha256(proof).hexdigest()}
        return json.dumps(value,separators=(',',':')).encode()

    def test_only_four_methods_and_closed_parameters_reach_command_builder(self):
        m=self.modules()
        with self.profile() as profile:
            client=m['core_cli'].CoreCLI(profile,owned_pid=123,deadline=time.monotonic()+10)
            for method,args in [('stop',()),('getblock',('0'*64,)),('getblockhash',(True,)),
                                ('getblockhash',(-1,)),('getblockhash',(1,2)),
                                ('getblockheader',('-rpcwallet=bad',False)),('getnetworkinfo',(1,))]:
                with self.subTest(method=method,args=args),self.assertRaises(ValueError):client.command(method,*args)
            command=client.command('getblockheader','a'*64,False)
            self.assertEqual(command[-3:],['getblockheader','a'*64,'false'])
            self.assertIn('-rpcconnect=127.0.0.1',command)
            self.assertIn('-rpcport=28332',command)

    def test_remote_endpoint_or_changed_port_is_not_a_fallback(self):
        m=self.modules()
        for field,value in [('rpcconnect','example.com'),('rpcport',8332)]:
            with self.profile() as profile:
                profile['core'][field]=value
                with self.assertRaises(ValueError):m['core_cli'].CoreCLI(profile,owned_pid=123,deadline=time.monotonic()+10)

    def test_three_public_identities_and_exact_owned_pid_metadata_are_checked(self):
        m=self.modules()
        with self.profile() as profile:
            client=m['core_cli'].CoreCLI(profile,owned_pid=123,deadline=time.monotonic()+10)
            replies=[f"{os.geteuid()} {profile['core']['daemon']['path']}\n".encode(),b'p123\nf17\nn127.0.0.1:28332\n']
            with mock.patch.object(client,'_run',side_effect=replies):client.verify_binding()

    def test_actual_macos_listener_fd_field_is_checked(self):
        m=self.modules()
        with self.profile() as profile:
            good=f"{os.geteuid()} {profile['core']['daemon']['path']}\n".encode()
            client=m['core_cli'].CoreCLI(profile,owned_pid=123,deadline=time.monotonic()+10)
            with mock.patch.object(client,'_run',side_effect=[good,b'p123\nf17\nn127.0.0.1:28332\n']):client.verify_binding()
            for bad in (b'p123\nn127.0.0.1:28332\n',b'p123\nfnot-an-fd\nn127.0.0.1:28332\n',b'p124\nf17\nn127.0.0.1:28332\n',b'p123\nf17\nn*:28332\n',b'p123\nf17\nn127.0.0.1:28332\nf18\nn127.0.0.1:28332\n'):
                with self.subTest(raw=bad),mock.patch.object(client,'_run',side_effect=[good,bad]):
                    with self.assertRaises(ValueError):client.verify_binding()

    def test_replaced_or_symlinked_runtime_file_refuses_before_process(self):
        m=self.modules()
        for change in ('replace','link'):
            with self.profile() as profile:
                target=Path(profile['core']['cli']['path'])
                if change=='replace':target.write_bytes(b'changed public test bytes')
                else:
                    target.unlink();target.symlink_to(Path(profile['core']['daemon']['path']))
                client=m['core_cli'].CoreCLI(profile,owned_pid=123,deadline=time.monotonic()+10)
                with mock.patch.object(client,'_run',side_effect=AssertionError('process before file gate')):
                    with self.assertRaises(ValueError):client.verify_binding()

    def test_wrong_uid_comm_pid_or_listener_refuses(self):
        m=self.modules()
        with self.profile() as profile:
            good=f"{os.geteuid()} {profile['core']['daemon']['path']}\n".encode()
            for replies in ([b'999999 /wrong\n',b'p123\nn127.0.0.1:28332\n'],
                            [f'{os.geteuid()} /wrong\n'.encode(),b'p123\nn127.0.0.1:28332\n'],
                            [good,b'p124\nn127.0.0.1:28332\n'],[good,b'p123\nn*:28332\n']):
                client=m['core_cli'].CoreCLI(profile,owned_pid=123,deadline=time.monotonic()+10)
                with mock.patch.object(client,'_run',side_effect=replies):
                    with self.assertRaises(ValueError):client.verify_binding()

    def test_rpc_limit_and_expired_work_budget_refuse_before_process(self):
        m=self.modules()
        with self.profile() as profile:
            client=m['core_cli'].CoreCLI(profile,owned_pid=123,deadline=time.monotonic()+10)
            client.calls=99
            with mock.patch.object(client,'_run',side_effect=AssertionError('process beyond count')):
                with self.assertRaises(ValueError):client('getnetworkinfo')
            with self.assertRaises(ValueError):m['core_cli'].run_bounded([sys.executable,'-c','pass'],deadline=time.monotonic()-1,timeout_seconds=1,output_limit=100)

    def test_rpc_json_duplicate_and_nonfinite_reject(self):
        m=self.modules()
        with self.profile() as profile:
            for raw in (b'{"x":1,"x":2}',b'{"x":NaN}',b'not json'):
                client=m['core_cli'].CoreCLI(profile,owned_pid=123,deadline=time.monotonic()+10)
                with mock.patch.object(client,'_run',return_value=raw):
                    with self.assertRaises(ValueError):client('getnetworkinfo')

    def test_stdout_limit_and_command_timeout_are_real_bounded_children(self):
        m=self.modules()
        for code,limit,seconds in [('import sys;sys.stdout.write("x"*100000)',100,2),('import time;time.sleep(2)',100,.05)]:
            with self.subTest(code=code),self.assertRaises(ValueError):
                m['core_cli'].run_bounded([sys.executable,'-I','-S','-B','-c',code],deadline=time.monotonic()+3,timeout_seconds=seconds,output_limit=limit)

    def test_descendant_holding_pipe_is_cleaned_when_leader_exits(self):
        m=self.modules()
        with tempfile.TemporaryDirectory() as directory:
            sentinel=Path(directory)/'survived'
            child='import signal,time,pathlib;signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(.5);pathlib.Path('+repr(str(sentinel))+').write_text("bad")'
            parent='import subprocess,sys;subprocess.Popen([sys.executable,"-I","-S","-B","-c",'+repr(child)+'])'
            with self.assertRaises(ValueError):m['core_cli'].run_bounded([sys.executable,'-I','-S','-B','-c',parent],deadline=time.monotonic()+2,timeout_seconds=.05,output_limit=100)
            time.sleep(.6);self.assertFalse(sentinel.exists())

    def signal_probe(self,*,during_spawn):
        self.modules()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);pidfile=root/'pid';ready=root/'ready';sentinel=root/'survived'
            child=('import os,signal,time,pathlib;signal.signal(signal.SIGTERM,signal.SIG_IGN);'
                   'pathlib.Path('+repr(str(ready))+').write_text("ready");time.sleep(.6);'
                   'pathlib.Path('+repr(str(sentinel))+').write_text("bad")')
            setup=('import os,signal,time,pathlib,types,sys;'
                   'm=types.ModuleType("bounded_signal_probe");m.__file__='+repr(str(HERE/'core_cli.py'))+';'
                   'exec(compile(pathlib.Path(m.__file__).read_bytes(),m.__file__,"exec"),m.__dict__);'
                   'original=m.subprocess.Popen\n'
                   'def stop(signum,frame):raise KeyboardInterrupt\n'
                   'signal.signal(signal.SIGTERM,stop)\n'
                   'def spawn(*args,**kwargs):\n'
                   ' p=original(*args,**kwargs)\n'
                   ' pathlib.Path('+repr(str(pidfile))+').write_text(str(p.pid))\n'+
                   (' os.kill(os.getpid(),signal.SIGTERM)\n' if during_spawn else '')+
                   ' return p\n'
                   'm.subprocess.Popen=spawn\n'
                   'try:m.run_bounded([sys.executable,"-I","-S","-B","-c",'+repr(child)+'],deadline=time.monotonic()+3,timeout_seconds=2,output_limit=100)\n'
                   'except BaseException:pass\n')
            owner=subprocess.Popen([sys.executable,'-I','-S','-B','-c',setup],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            child_pid=None
            try:
                if not during_spawn:
                    end=time.monotonic()+3
                    while not ready.exists() and time.monotonic()<end:time.sleep(.005)
                    self.assertTrue(ready.exists())
                    owner.send_signal(signal.SIGTERM);time.sleep(.02);owner.send_signal(signal.SIGTERM)
                owner.wait(timeout=4);time.sleep(.7)
                self.assertFalse(sentinel.exists(),'ordinary signal left an owned helper alive')
            finally:
                if pidfile.exists():child_pid=int(pidfile.read_text())
                if child_pid is not None:
                    try:os.killpg(child_pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                if owner.poll() is None:owner.kill()
                owner.wait(timeout=2)

    def test_signal_after_child_creation_before_ownership_assignment_is_safe(self):
        self.signal_probe(during_spawn=True)

    def test_repeated_signal_cannot_interrupt_owned_command_cleanup(self):
        self.signal_probe(during_spawn=False)

    def temporary_negative_authorization(self,m,profile,raw,now):
        snapshot=m['strong_inputs'].capture_request(raw)
        core={'format':'FP_DEV_STRONG_CORE_READ_AUTH_V1','authorization_scope':'ONE_PUBLIC_SUBJECT_CORE_READ_CHECK',
              'runtime_profile_sha256':hashlib.sha256(m['strong_candidate'].profile_bytes(profile)).hexdigest(),
              'request_sha256':hashlib.sha256(raw).hexdigest(),'subject_sha256':snapshot.bundle_sha256,
              'proof_sha256':snapshot.proof_sha256,'owned_core_pid':123,
              'authorized_at_utc':(now-timedelta(seconds=10)).isoformat().replace('+00:00','Z'),
              'expires_at_utc':(now+timedelta(seconds=1)).isoformat().replace('+00:00','Z'),
              'authorized_by':'SYNTHETIC_UNIT_NEGATIVE_ONLY_NOT_A_HUMAN_APPROVAL'}
        value={**core,'authorization_sha256':hashlib.sha256(m['strong_candidate'].profile_bytes(core)).hexdigest()}
        Path(profile['authorization_path']).write_text(json.dumps(value))

    def test_authorization_expiring_during_binding_prevents_reservation(self):
        m=self.modules();now=datetime(2026,10,27,3,tzinfo=timezone.utc)
        class Clock:
            @classmethod
            def now(cls,tz=None):return cls.value
            @staticmethod
            def fromisoformat(value):return datetime.fromisoformat(value)
        Clock.value=now
        with self.profile() as profile:
            raw=self.raw_request(m);self.temporary_negative_authorization(m,profile,raw,now)
            def expire():Clock.value=now+timedelta(seconds=2)
            client=mock.Mock();client.verify_binding.side_effect=expire
            with mock.patch.object(m['strong_candidate'],'datetime',Clock),mock.patch.object(m['strong_candidate'],'CoreCLI',return_value=client):
                with self.assertRaises(ValueError):m['strong_candidate'].run_request(raw,profile)
            self.assertFalse(Path(profile['reservation_path']).exists(),'authorization expired before reservation')

    def test_authorization_remaining_lifetime_clamps_work_deadline(self):
        m=self.modules();now=datetime(2026,10,27,3,tzinfo=timezone.utc)
        class Clock:
            @staticmethod
            def now(tz=None):return now
            @staticmethod
            def fromisoformat(value):return datetime.fromisoformat(value)
        with self.profile() as profile:
            raw=self.raw_request(m);self.temporary_negative_authorization(m,profile,raw,now)
            client=mock.Mock();client.verify_binding.side_effect=ValueError('stop synthetic probe before any action')
            before=time.monotonic()
            with mock.patch.object(m['strong_candidate'],'datetime',Clock),mock.patch.object(m['strong_candidate'],'CoreCLI',return_value=client) as factory:
                with self.assertRaises(ValueError):m['strong_candidate'].run_request(raw,profile)
                self.assertLessEqual(factory.call_args.kwargs['deadline']-before,1.1)

    def test_missing_authorization_stops_before_core_construction_or_reservation(self):
        m=self.modules()
        with self.profile() as profile:
            raw=self.raw_request(m)
            with mock.patch.object(m['strong_candidate'],'CoreCLI',side_effect=AssertionError('Core without approval')):
                with self.assertRaises(ValueError):m['strong_candidate'].run_request(raw,profile)
            self.assertFalse(Path(profile['reservation_path']).exists())

    def test_nonmatching_or_expired_synthetic_control_record_cannot_authorize_run(self):
        m=self.modules()
        with self.profile() as profile:
            # Only negative test data, explicitly not a real human authorization.
            path=Path(profile['authorization_path'])
            for value in ({'format':'SYNTHETIC_NEGATIVE_ONLY'},{'format':'FP_DEV_STRONG_CORE_READ_AUTH_V1','expires_at_utc':'2000-01-01T00:00:00Z'}):
                path.write_text(json.dumps(value))
                with mock.patch.object(m['strong_candidate'],'CoreCLI',side_effect=AssertionError('Core before authorization validation')):
                    with self.assertRaises(ValueError):m['strong_candidate'].run_request(self.raw_request(m),profile)
                self.assertFalse(Path(profile['reservation_path']).exists())

    def test_wire_output_is_closed_and_does_not_relabel_unknown_as_false(self):
        m=self.modules();request=m['strong_inputs'].capture_request(self.raw_request(m))
        anchor=SimpleNamespace(height=1,block_hash='a'*64,header_sha256='b'*64)
        observed=SimpleNamespace(anchors=(anchor,),reported_node_subversion='/synthetic-offline-test/')
        value=m['strong_candidate'].wire_result(request,observed)
        self.assertEqual(set(value),{'schema_version','action','verification_mode','bundle_sha256','proof_sha256','verified','bitcoin_block_height','bitcoin_block_hash','bitcoin_header_sha256','node_version'})
        self.assertIs(value['verified'],True)
        self.assertNotIn('reason_code',value)


if __name__=='__main__':unittest.main()
