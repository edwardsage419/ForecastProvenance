"""Recorded human choices are source facts, never operative public authority."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from test_verifier_contract import load

ROOT=Path(__file__).resolve().parents[3]
PACKAGE=ROOT/'docs/development/independent-choice-mainline-consumption-2026-10-28-rev-001'


class IndependentChoiceTests(unittest.TestCase):
    def module(self):
        m=load('mainline_worker')
        self.assertTrue(hasattr(m,'source_choices'),'recorded choice consumption missing')
        return m

    def shared(self):
        m=load('mainline_worker');snapshots={}
        m.signing_candidates(gate_output={},gate_snapshot_output=snapshots)
        return snapshots

    def test_real_choice_sources_and_two_current_gate_bindings_stay_separate(self):
        m=self.module();r=m.source_choices(self.shared())
        self.assertEqual(r['status'],'OBSERVED')
        self.assertTrue(r['owner_role_choice_supplied']);self.assertTrue(r['software_basis_choice_supplied'])
        self.assertEqual(r['current_gate_artifact_expectations_bound'],2)
        self.assertEqual(r['current_python_and_platform_match'],'NOT_ASSESSED')
        self.assertEqual(r['actual_governing_permission_verified'],'NOT_ESTABLISHED')
        self.assertEqual(r['independent_cryptographic_authentication'],'NOT_ESTABLISHED')
        self.assertEqual(r['real_admission'],'NOT_READY');self.assertEqual(r['protocol_state_change'],'NONE')

    def test_choices_are_read_once_and_shared_gate_bytes_are_never_reread(self):
        m=self.module();shared=self.shared();seen=[];original=m.reader.read_fixed
        def read(base,name,expected):
            self.assertNotIn(name,shared,'shared gate raw bytes reread')
            self.assertNotIn(name,seen,'choice input read twice');seen.append(name)
            return original(base,name,expected)
        with patch.object(m.reader,'read_fixed',side_effect=read):r=m.source_choices(shared)
        self.assertEqual(r['status'],'OBSERVED');self.assertEqual(len(seen),5)

    def test_missing_and_changed_records_remain_visible_together(self):
        m=self.module();rows=json.loads((PACKAGE/'INPUT_IDENTITIES.json').read_bytes())['inputs']
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            for row in rows:
                target=base/row['path'];target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes((ROOT/row['path']).read_bytes())
            (base/rows[0]['path']).unlink()
            raw=(base/rows[2]['path']).read_bytes();(base/rows[2]['path']).write_bytes(bytes([raw[0]^1])+raw[1:])
            r=m.source_choices(self.shared(),directory=base)
        self.assertEqual(r['status'],'REJECTED')
        self.assertEqual({f['status'] for f in r['findings']},{'MISSING','REJECTED'})
        self.assertFalse(r['owner_role_choice_supplied']);self.assertFalse(r['software_basis_choice_supplied'])

    def test_gate_missing_does_not_erase_supplied_choices_or_fallback(self):
        m=self.module();r=m.source_choices({})
        self.assertEqual(r['status'],'MISSING')
        self.assertTrue(r['owner_role_choice_supplied']);self.assertTrue(r['software_basis_choice_supplied'])
        self.assertEqual(r['current_gate_artifact_expectations_bound'],0)
        self.assertEqual(len(r['findings']),2)

    def test_gate_substitution_is_hard_without_promoting_current_environment(self):
        m=self.module();shared=self.shared()
        name='docs/development/mainline-execution-2026-10-09-rev-001/public-verifier-build/native/fp_public_verify.dylib'
        shared[name]=b'x'*len(shared[name]);r=m.source_choices(shared)
        self.assertEqual(r['status'],'REJECTED')
        self.assertTrue(r['software_basis_choice_supplied'])
        self.assertEqual(r['current_python_and_platform_match'],'NOT_ASSESSED')

    def test_new_source_choice_child_is_consumed_without_changing_auth_guard(self):
        m=self.module();rows=m.missing_input_modules();initial=next(r for r in rows if r['id']=='initial-authority')
        child=initial['result'].get('independent_source_choices')
        self.assertIsNotNone(child,'mainline does not consume actual choice sources')
        self.assertEqual(child['status'],'OBSERVED');self.assertEqual(initial['status'],'MISSING')
        self.assertEqual(initial['result']['status'],'UNKNOWN')
        self.assertIn('BLOCKED_BY_G02',initial['result']['reason_codes'])

    def test_existing_math_replay_never_writes_retained_historical_reports(self):
        history=ROOT/'docs/development/public-math-mainline-consumption-2026-10-28-rev-001'
        forbidden={history/'MAINLINE_A.json',history/'MAINLINE_B.json'}
        original=Path.write_bytes
        def guard(path,body):
            self.assertNotIn(path,forbidden,'regression test attempted to overwrite historical evidence')
            return original(path,body)
        case=load('test_public_math').PublicMathTests('test_actual_mainline_only_adds_child_and_two_cwd_outputs_equal')
        with patch.object(Path,'write_bytes',guard):case.test_actual_mainline_only_adds_child_and_two_cwd_outputs_equal()


if __name__=='__main__':unittest.main()
