"""One retained public nonforecast event; never rerun a network/native action."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CATALOG=json.loads((HERE/'roughtime_event_inputs.json').read_bytes())
PREFIX=CATALOG['event_prefix']


def copy_inputs(directory):
    for row in CATALOG['inputs']:
        destination=Path(directory)/row['path'];destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/row['path'],destination)


class RoughtimeEventTests(unittest.TestCase):
    def consume(self, directory=ROOT, **kwargs):
        source=HERE/'roughtime_event.py'
        self.assertTrue(source.exists(),'retained nonforecast event consumer is absent')
        spec=importlib.util.spec_from_file_location('test_event_consumer',source)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module.consume(directory,**kwargs)

    def command(self,*args,json_output=True):
        command=[str(ROOT/'.venv/bin/python'),'-I','-B',str(HERE/'cli.py'),'mainline',*args]
        if json_output:command.append('--json')
        process=subprocess.run(command,capture_output=True,text=True,timeout=45)
        self.assertTrue(process.stdout.strip(),process.stderr)
        return process,json.loads(process.stdout) if json_output else process.stdout

    def test_real_event_is_consumed_without_production_or_native_promotion(self):
        with patch('subprocess.run',side_effect=AssertionError('native execution forbidden')):
            result=self.consume()
        self.assertEqual(result['status'],'OBSERVED')
        self.assertTrue(result['raw_event_binding_match'])
        self.assertEqual(result['input_count'],47)
        self.assertEqual(result['local_send_records'],4)
        self.assertEqual(result['retained_verified_responses'],2)
        self.assertEqual(result['timeout_attempts'],2)
        self.assertFalse(result['native_reverification_executed'])
        self.assertFalse(result['independent_complete_history'])
        self.assertEqual(result['provider_qualification'],'NOT_ESTABLISHED')
        self.assertFalse(result['prospective_eligible'])
        self.assertEqual(result['real_admission'],'NOT_READY')
        self.assertEqual(result['protocol_state_change'],'NONE')

    def test_each_critical_original_omission_stays_missing(self):
        names=['report.json','retry-state-after.json','providers/time.txryan.com/attempt-1/response.bin',
               'providers/roughtime.se/attempt-2/transport.json',
               'providers/roughtime.se/attempt-1/retry-state-reserved.json']
        consumed=next(r['path'] for r in CATALOG['inputs'] if '/consumed/' in r['path'])
        paths=[PREFIX+n for n in names]+[consumed]
        for path in paths:
            with self.subTest(path=path),tempfile.TemporaryDirectory() as directory:
                copy_inputs(directory);(Path(directory)/path).unlink()
                result=self.consume(directory)
                self.assertEqual(result['status'],'MISSING')
                self.assertFalse(result['raw_event_binding_match'])
                self.assertIn(path,[f['item'] for f in result['findings']])

    def test_missing_and_swapped_provider_response_are_both_retained(self):
        with tempfile.TemporaryDirectory() as directory:
            copy_inputs(directory)
            a=Path(directory)/(PREFIX+'providers/time.txryan.com/attempt-1/response.bin')
            b=Path(directory)/(PREFIX+'providers/TimeNL-Roughtime/attempt-1/response.bin')
            a.write_bytes(b.read_bytes())
            (Path(directory)/(PREFIX+'retry-state-after.json')).unlink()
            result=self.consume(directory)
        self.assertEqual(result['status'],'REJECTED')
        self.assertEqual({f['error'] for f in result['findings']},{'INPUT_IDENTITY_MISMATCH','MISSING_INPUT'})

    def test_retained_replay_and_review_are_required_and_not_executed(self):
        paths=[r['path'] for r in CATALOG['inputs'] if r['path'].endswith(('/OFFLINE_REPLAY.json','/REVIEW.md','/replay_public_event.py'))]
        self.assertEqual(len(paths),3)
        with tempfile.TemporaryDirectory() as directory:
            copy_inputs(directory)
            for path in paths:(Path(directory)/path).unlink()
            result=self.consume(directory)
        self.assertEqual(result['status'],'MISSING')
        self.assertEqual(len(result['findings']),3)
        self.assertFalse(result['raw_event_binding_match'])

    def test_mirror_replays_identically_and_restores_existing_package_namespace(self):
        import sys
        sentinel=object();old=sys.modules.get('forecast_trust_core',sentinel)
        with tempfile.TemporaryDirectory() as directory:
            copy_inputs(directory)
            self.assertEqual(self.consume(directory),self.consume())
        self.assertIs(sys.modules.get('forecast_trust_core',sentinel),old)

    def test_nonexistent_directory_missing_but_symlink_response_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            result=self.consume(Path(directory)/'not-created')
            self.assertEqual(result['status'],'MISSING')
            self.assertEqual(len(result['findings']),47)
            copy_inputs(directory)
            path=PREFIX+'providers/TimeNL-Roughtime/attempt-1/response.bin'
            target=Path(directory)/path;target.unlink();target.symlink_to(ROOT/path)
            result=self.consume(directory)
        self.assertEqual(result['status'],'REJECTED')
        self.assertIn('UNSAFE_PATH',[f['error'] for f in result['findings']])

    def test_changed_catalog_is_rejected_before_any_declared_paths_are_followed(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'scripts/development/offline_evidence/roughtime_event_inputs.json'
            target.parent.mkdir(parents=True)
            target.write_text('{"path":"/not-authorized"}')
            result=self.consume(source_root=Path(directory))
        self.assertEqual(result['status'],'REJECTED')
        self.assertEqual(len(result['findings']),1)
        self.assertEqual(result['findings'][0]['error'],'INPUT_IDENTITY_MISMATCH')

    def test_changed_and_missing_validator_sources_are_both_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory)
            catalog=base/'scripts/development/offline_evidence/roughtime_event_inputs.json'
            catalog.parent.mkdir(parents=True);shutil.copyfile(HERE/'roughtime_event_inputs.json',catalog)
            changed=base/'src/forecast_trust_core/canonical.py'
            changed.parent.mkdir(parents=True);changed.write_bytes(b'raise AssertionError("not executed")')
            result=self.consume(source_root=base)
        self.assertEqual(result['status'],'REJECTED')
        self.assertEqual(len(result['findings']),7)

    def test_cli_default_event_is_observed_with_parent_still_missing(self):
        process,report=self.command()
        row=next(r for r in report['modules'] if r['id']=='time-and-durability')
        self.assertIn('roughtime_nonforecast_event',row)
        self.assertEqual(row['roughtime_nonforecast_event']['status'],'OBSERVED')
        self.assertEqual(row['status'],'MISSING')
        self.assertEqual(process.returncode,1)
        self.assertEqual(report['real_admission'],'NOT_READY')

    def test_direct_isolated_entry_reads_only_retained_data(self):
        process=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-S','-B',str(HERE/'roughtime_event.py')],
                               capture_output=True,text=True,timeout=15)
        self.assertTrue(process.stdout.strip(),process.stderr)
        result=json.loads(process.stdout)
        self.assertEqual(result['status'],'OBSERVED')
        self.assertEqual(process.returncode,0)
        self.assertFalse(result['native_reverification_executed'])
        self.assertEqual(result['real_admission'],'NOT_READY')

    def test_cli_explicit_missing_or_rejected_event_keeps_other_modules(self):
        with tempfile.TemporaryDirectory() as directory:
            for expected in ('MISSING','REJECTED'):
                if expected=='REJECTED':
                    copy_inputs(directory);(Path(directory)/(PREFIX+'report.json')).write_bytes(b'wrong')
                process,report=self.command('--roughtime-event-inputs',directory)
                rows={r['id']:r for r in report['modules']}
                child=rows['time-and-durability']['roughtime_nonforecast_event']
                self.assertEqual(child['status'],expected)
                self.assertEqual(process.returncode,2 if expected=='REJECTED' else 1)
                self.assertEqual(rows['economic-data']['status'],'OBSERVED')
                self.assertEqual(report['protocol_state_change'],'NONE')


if __name__=='__main__':unittest.main()
