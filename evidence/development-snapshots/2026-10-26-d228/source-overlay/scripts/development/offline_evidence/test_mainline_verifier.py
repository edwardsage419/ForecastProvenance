"""Actual D211 diagnostic integration, preserving missing authority and failures."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
P211 = ROOT/'docs/development/verifier-contract-consumption-2026-10-25-rev-001'
P185 = ROOT/'docs/development/mainline-execution-2026-10-19-signing-profile-content-rev-001'
ALIASES = {'adapter':'public_verifier.py', 'run_binding':'run_binding.py',
           'build_observations':'BUILD_OBSERVATIONS.json', 'source_manifest':'SOURCE_MANIFEST.json',
           'configuration':'config.h', 'pre_run':'PRE_RUN.json',
           'dependency_audit':'evidence/DEPENDENCY_AUDIT.json', 'native_binary':'native/fp_public_verify.dylib'}


def load(name):
    spec = importlib.util.spec_from_file_location('d214_test_'+name, HERE/(name+'.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def supply(directory):
    directory = Path(directory)
    shutil.copyfile(P211/'CONTRACT_CANDIDATE.json', directory/'CONTRACT_CANDIDATE.json')
    for role,row in json.loads((P211/'ARTIFACT_INPUTS.json').read_text()).items():
        target=directory/ALIASES[role]; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/row['path'],target)


def repository_copy(directory):
    directory = Path(directory)
    files = ['scripts/development/offline_evidence/signing_profile.py',
             'scripts/development/offline_evidence/verifier_contract.py',
             'src/forecast_trust_core/canonical.py', 'schemas/acceptance_policy_v3.schema.json']
    files += [str((P185/name).relative_to(ROOT)) for name in ('PROFILE_CANDIDATE.json','PROFILE_SCHEMA_CANDIDATE.json')]
    files += [str((P211/name).relative_to(ROOT)) for name in ('CONTRACT_CANDIDATE.json','CONTRACT_SCHEMA_CANDIDATE.json','ARTIFACT_INPUTS.json')]
    files += [row['path'] for row in json.loads((P211/'ARTIFACT_INPUTS.json').read_text()).values()]
    for name in files:
        target=directory/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/name,target)


class MainlineVerifierTests(unittest.TestCase):
    def integration(self):
        module=load('mainline_worker')
        self.assertTrue(hasattr(module,'signing_candidates'),'D214 combined diagnostic is absent')
        return module

    def command(self,*args,human=False):
        self.integration()
        run=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B',str(HERE/'cli.py'),'mainline',
                            *args,*([] if human else ['--json'])],cwd=ROOT,capture_output=True,text=True,timeout=50)
        self.assertTrue(run.stdout.strip(),run.stderr)
        return run,run.stdout if human else json.loads(run.stdout)

    def authority(self,report):
        return next(row for row in report['modules'] if row['id']=='initial-authority')

    def test_default_actually_consumes_contract_and_preserves_original_profile(self):
        run,report=self.command()
        row=self.authority(report);result=row['result'];new=result['technical_verifier_contract_candidate']
        self.assertEqual(new['contract_content_status'],'OBSERVED')
        self.assertEqual(new['artifact_binding_status'],'OBSERVED')
        self.assertEqual(new['proposed_verifier_use_status'],'MISSING')
        self.assertEqual(new['profile_result'],result['technical_signing_profile_candidate'])
        self.assertEqual(row['status'],'MISSING');self.assertEqual(result['status'],'UNKNOWN')
        self.assertIn('BLOCKED_BY_G02',result['reason_codes'])
        self.assertEqual(len(report['modules']),14);self.assertEqual(run.returncode,1)
        for name in ('full_build_runtime_closure','execution_contract_complete','message_resource_policy'):
            self.assertEqual(new[name],'NOT_ESTABLISHED')
        self.assertEqual(new['operational_bindings_established'],0)
        self.assertFalse(new['native_loaded']);self.assertFalse(new['backend_called'])
        self.assertFalse(new['message_constructed']);self.assertEqual(report['real_admission'],'NOT_READY')

    def test_default_only_initial_authority_changes_against_prior_actual_output(self):
        _,new=self.command()
        old=json.loads((P211/'MAINLINE.json').read_text())
        # D218 adds an independent calendar child; retain this test's D214 projection.
        next(row for row in new['modules'] if row['id']=='official-calendar').pop('read_only_assessment')
        next(row for row in new['modules'] if row['id']=='official-calendar').pop('predecessor_calendar_binding')
        self.authority(new)['result'].pop('technical_verifier_identity_gate')
        for module in new['modules']:
            if module['id'] in ('unemployment-july','unemployment-november','inflation-data'):
                self.assertEqual(module.pop('target_table_support')['comparison']['status'],'OBSERVED')
        changed=[a['id'] for a,b in zip(new['modules'],old['modules']) if a!=b]
        self.assertEqual(changed,['initial-authority'])
        self.authority(new)['result'].pop('technical_verifier_contract_candidate')
        self.assertEqual(new,old)

    def test_complete_explicit_directory_and_unrelated_file_do_not_change_observations(self):
        module=self.integration();_,expected=module.signing_candidates()
        with tempfile.TemporaryDirectory() as directory:
            supply(directory);(Path(directory)/'UNSELECTED_RULE.json').write_bytes(b'not an input')
            run,report=self.command('--verifier-inputs',directory)
        actual=self.authority(report)['result']['technical_verifier_contract_candidate']
        self.assertEqual(run.returncode,1);self.assertEqual(actual,expected)

    def test_explicit_empty_directory_has_all_nine_missing_and_no_default_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            run,report=self.command('--verifier-inputs',directory)
        row=self.authority(report);new=row['result']['technical_verifier_contract_candidate']
        self.assertEqual(run.returncode,1);self.assertEqual(new['status'],'MISSING')
        self.assertEqual({r['role'] for r in new['input_findings']},{'contract',*ALIASES})
        self.assertTrue(all(r['status']=='MISSING' for r in new['input_findings']))
        self.assertEqual(row['result']['technical_signing_profile_candidate']['profile_content_status'],'OBSERVED')

    def test_bad_contract_and_missing_native_are_both_visible_at_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            supply(directory);base=Path(directory)
            (base/'CONTRACT_CANDIDATE.json').write_bytes(b'{}')
            (base/ALIASES['native_binary']).unlink()
            run,report=self.command('--verifier-inputs',directory)
        row=self.authority(report)
        self.assertEqual(run.returncode,2);self.assertEqual(row['status'],'REJECTED')
        self.assertEqual({r['status'] for r in row['findings']},{'REJECTED','MISSING'})
        technical=row['result']['technical_verifier_contract_candidate']
        self.assertEqual(technical['contract_content_status'],'NOT_CHECKED')
        self.assertEqual(technical['read_admission']['contract'],'REJECTED')
        self.assertEqual(row['result']['status'],'UNKNOWN')
        self.assertEqual(next(r for r in report['modules'] if r['id']=='economic-data')['status'],'OBSERVED')

    def test_profile_missing_does_not_hide_corrupt_native_or_good_contract(self):
        with tempfile.TemporaryDirectory() as directory,tempfile.TemporaryDirectory() as missing:
            supply(directory);file=Path(directory)/ALIASES['native_binary'];raw=file.read_bytes()
            file.write_bytes(bytes([raw[0]^1])+raw[1:])
            run,report=self.command('--profile-inputs',missing,'--verifier-inputs',directory)
        row=self.authority(report);new=row['result']['technical_verifier_contract_candidate']
        self.assertEqual(run.returncode,2);self.assertEqual(row['status'],'REJECTED')
        self.assertEqual(new['contract_content_status'],'OBSERVED')
        self.assertEqual(new['artifact_binding_status'],'REJECTED')
        self.assertEqual(new['artifact_statuses']['native_binary']['status'],'REJECTED')
        self.assertEqual(row['result']['technical_signing_profile_candidate']['status'],'MISSING')
        self.assertEqual({r['status'] for r in row['findings']},{'MISSING','REJECTED'})

    def test_rejected_profile_reaches_both_technical_branches_without_promoting_auth(self):
        with tempfile.TemporaryDirectory() as directory:
            (Path(directory)/'PROFILE_CANDIDATE.json').write_bytes(b'{}')
            run,report=self.command('--profile-inputs',directory)
        result=self.authority(report)['result']
        self.assertEqual(run.returncode,2)
        self.assertEqual(result['technical_signing_profile_candidate']['status'],'REJECTED')
        self.assertEqual(result['technical_verifier_contract_candidate']['status'],'REJECTED')
        self.assertEqual(result['status'],'UNKNOWN')

    def test_each_bad_anchor_rejected_without_hiding_missing_sibling(self):
        module=self.integration()
        for role,alias in ALIASES.items():
            with self.subTest(role=role),tempfile.TemporaryDirectory() as directory:
                supply(directory);file=Path(directory)/alias;raw=file.read_bytes()
                file.write_bytes(bytes([raw[0]^1])+raw[1:])
                (Path(directory)/'CONTRACT_CANDIDATE.json').unlink()
                _,new=module.signing_candidates(None,Path(directory))
                self.assertEqual(new['status'],'REJECTED')
                self.assertIn(role,{r['role'] for r in new['input_findings'] if r['status']=='REJECTED'})
                self.assertIn('contract',{r['role'] for r in new['input_findings'] if r['status']=='MISSING'})

    def test_leaf_and_directory_symlinks_are_rejected(self):
        module=self.integration()
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);inputs=base/'inputs';inputs.mkdir();supply(inputs)
            native=inputs/ALIASES['native_binary'];native.unlink()
            native.symlink_to(ROOT/json.loads((P211/'ARTIFACT_INPUTS.json').read_text())['native_binary']['path'])
            _,new=module.signing_candidates(None,inputs)
            self.assertEqual(new['status'],'REJECTED')
            self.assertIn('UNSAFE_PATH',{f['error'] for f in new['input_findings']})
            alias=base/'directory-link';alias.symlink_to(inputs,target_is_directory=True)
            _,new=module.signing_candidates(None,alias)
            self.assertEqual(new['status'],'REJECTED')

    def test_profile_is_one_immutable_snapshot_even_if_file_disappears_after_read(self):
        module=self.integration();original=module.reader.read_fixed;reads=[]
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);file=base/'PROFILE_CANDIDATE.json'
            shutil.copyfile(P185/'PROFILE_CANDIDATE.json',file)
            def capture(root,relative,expected):
                raw=original(root,relative,expected)
                if Path(root)==base and str(relative)=='PROFILE_CANDIDATE.json':
                    reads.append(raw);file.unlink()
                return raw
            with patch.object(module.reader,'read_fixed',capture):
                profile,new=module.signing_candidates(base)
        self.assertEqual(len(reads),1)
        self.assertEqual(profile['profile_content_status'],'OBSERVED')
        self.assertEqual(new['profile_result'],profile)
        self.assertEqual(new['profile_result']['profile_content_status'],'OBSERVED')

    def test_verifier_source_catalog_and_schema_failures_preserve_independent_profile(self):
        self.integration()
        cases=[('scripts/development/offline_evidence/verifier_contract.py','replace','REJECTED'),
               (str((P211/'ARTIFACT_INPUTS.json').relative_to(ROOT)),'replace','REJECTED'),
               (str((P211/'CONTRACT_SCHEMA_CANDIDATE.json').relative_to(ROOT)),'remove','MISSING'),
               ('scripts/development/offline_evidence/verifier_contract.py','remove','MISSING')]
        for name,action,status in cases:
            with self.subTest(path=name,action=action),tempfile.TemporaryDirectory() as directory:
                repository_copy(directory);base=Path(directory);file=base/name
                if action=='remove':file.unlink()
                elif file.suffix=='.py':
                    size=file.stat().st_size;payload=b"raise AssertionError('UNADMITTED_SOURCE_EXECUTED')\n"
                    file.write_bytes(payload+b' '*(size-len(payload)))
                else:
                    raw=file.read_bytes();file.write_bytes(bytes([raw[0]^1])+raw[1:])
                module=self.integration();module.ROOT=base;module.HERE=base/'scripts/development/offline_evidence'
                profile,new=module.signing_candidates()
                self.assertEqual(profile['profile_content_status'],'OBSERVED')
                self.assertEqual(new['status'],status)
                self.assertTrue(new['input_findings'])

    def test_rejected_catalog_symlink_is_never_read_again_during_consumer_import(self):
        self.integration()
        with tempfile.TemporaryDirectory() as directory:
            repository_copy(directory);base=Path(directory)
            catalog=base/(P211/'ARTIFACT_INPUTS.json').relative_to(ROOT)
            public_copy=base/'SAFE_PUBLIC_CATALOG_COPY.json'
            public_copy.write_bytes(catalog.read_bytes());catalog.unlink();catalog.symlink_to(public_copy)
            module=self.integration();module.ROOT=base;module.HERE=base/'scripts/development/offline_evidence'
            original=Path.read_bytes;rejected_reads=[]
            catalog_name=catalog.parent.resolve()/catalog.name
            def observed(path):
                # Normalize macOS /var vs /private/var parents without following
                # the rejected leaf symlink itself.
                if path.parent.resolve()/path.name==catalog_name:rejected_reads.append(str(path))
                return original(path)
            with patch.object(Path,'read_bytes',observed):
                profile,new=module.signing_candidates()
            self.assertEqual(rejected_reads,[])
            self.assertEqual(new['status'],'REJECTED')
            self.assertEqual(new['read_admission']['artifact_catalog'],'REJECTED')
            self.assertEqual(profile['profile_content_status'],'OBSERVED')

    def test_fixed_import_dependencies_reject_symlinks_before_any_leaf_read(self):
        cases=[('scripts/development/offline_evidence/signing_profile.py','NOT_CHECKED'),
               ('src/forecast_trust_core/canonical.py','NOT_CHECKED'),
               ('schemas/acceptance_policy_v3.schema.json','NOT_CHECKED'),
               (str((P185/'PROFILE_SCHEMA_CANDIDATE.json').relative_to(ROOT)),'NOT_CHECKED'),
               (str((P211/'CONTRACT_SCHEMA_CANDIDATE.json').relative_to(ROOT)),'OBSERVED')]
        for relative,expected_profile in cases:
            with self.subTest(path=relative),tempfile.TemporaryDirectory() as directory:
                repository_copy(directory);base=Path(directory);file=base/relative
                public_copy=base/'SAFE_PUBLIC_DEPENDENCY_COPY';public_copy.write_bytes(file.read_bytes())
                file.unlink();file.symlink_to(public_copy)
                module=self.integration();module.ROOT=base;module.HERE=base/'scripts/development/offline_evidence'
                original=Path.read_bytes;reads=[];rejected_name=file.parent.resolve()/file.name
                def observed(path):
                    if path.parent.resolve()/path.name==rejected_name:reads.append(str(path))
                    return original(path)
                with patch.object(Path,'read_bytes',observed):
                    profile,new=module.signing_candidates()
                self.assertEqual(reads,[])
                self.assertEqual(new['status'],'REJECTED')
                self.assertEqual(profile['profile_content_status'],expected_profile)
                self.assertIn('UNSAFE_PATH',{r['error'] for r in new['input_findings']})

    def test_fixed_schema_import_uses_admitted_snapshot_and_restores_path_reader(self):
        with tempfile.TemporaryDirectory() as directory:
            repository_copy(directory);base=Path(directory)
            schema=base/(P211/'CONTRACT_SCHEMA_CANDIDATE.json').relative_to(ROOT)
            module=self.integration();module.ROOT=base;module.HERE=base/'scripts/development/offline_evidence'
            original_read=module.reader.read_fixed;path_reader=Path.read_bytes;captures=[]
            def capture(root,relative,expected):
                raw=original_read(root,relative,expected)
                if Path(root)/relative==schema:
                    captures.append(raw);schema.unlink()
                return raw
            with patch.object(module.reader,'read_fixed',capture):
                profile,new=module.signing_candidates()
            self.assertEqual(len(captures),1)
            self.assertEqual(profile['profile_content_status'],'OBSERVED')
            self.assertEqual(new['contract_content_status'],'OBSERVED')
            self.assertEqual(new['status'],'MISSING')
            self.assertIs(Path.read_bytes,path_reader)

    def test_human_output_explains_contract_artifacts_rule_and_no_execution(self):
        run,text=self.command(human=True)
        self.assertEqual(run.returncode,1)
        for word in ('验签合同','八份材料','规则','不执行验签','NOT_READY'):
            self.assertIn(word,text)

    def test_two_processes_match_and_combined_helper_does_not_load_native(self):
        first,a=self.command();second,b=self.command()
        self.assertEqual(first.stdout,second.stdout);self.assertEqual(a,b)
        code='''import importlib.util,pathlib,sys
root=pathlib.Path.cwd();here=root/'scripts/development/offline_evidence'
s=importlib.util.spec_from_file_location('d214_test',here/'test_mainline_verifier.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t)
t.load('verifier_contract');m=t.load('mainline_worker')
def audit(event,args):
 if event.startswith(('ctypes.','socket.')) or event in ('subprocess.Popen','os.exec','os.fork','os.system'):
  raise RuntimeError('D214_FORBIDDEN_EXECUTION')
sys.addaudithook(audit)
p,v=m.signing_candidates()
assert p['profile_content_status']=='OBSERVED' and v['artifact_binding_status']=='OBSERVED'
assert not v['backend_called'] and not v['message_constructed']
print('NO_NATIVE_OR_MESSAGE')
'''
        run=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B','-c',code],cwd=ROOT,capture_output=True,text=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stderr);self.assertIn('NO_NATIVE_OR_MESSAGE',run.stdout)


if __name__=='__main__':unittest.main()
