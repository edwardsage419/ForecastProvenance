"""Same-run joins consume planning observations without supplying actual events."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PACKAGE = ROOT/'docs/development/q1-2027-read-only-assessment-2026-10-25-rev-001'


class PredecessorBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('binding_cli', HERE/'cli.py')
        cls.cli = importlib.util.module_from_spec(spec); spec.loader.exec_module(cls.cli)
        cls.baseline = json.loads((PACKAGE/'MAINLINE_A.json').read_text())

    def inputs(self):
        row = next(x for x in deepcopy(self.baseline)['modules'] if x['id']=='official-calendar')
        return row['read_only_assessment'], row['predecessor_research']

    def bind(self, a, r):
        self.assertTrue(hasattr(self.cli, 'bind_predecessor_calendars'), 'same-run binding is absent')
        return self.cli.bind_predecessor_calendars(a, r)

    def test_three_real_planning_joins_without_io_mutation_or_evidence_upgrade(self):
        a,r=self.inputs();before=deepcopy((a,r))
        with patch('builtins.open',side_effect=AssertionError('unexpected IO')), \
             patch.object(Path,'read_bytes',side_effect=AssertionError('unexpected IO')), \
             patch.object(Path,'read_text',side_effect=AssertionError('unexpected IO')):
            result=self.bind(a,r)
        self.assertEqual(result['status'],'OBSERVED');self.assertEqual(result['matched_predecessor_count'],3)
        self.assertEqual({(b['series'],b['reference_period'],b['calendar_declaration']['scheduled_date_declaration'])
                          for b in result['bindings']},
                         {('GDP','2026-Q3','2026-10-29'),('U3','2026-11','2026-12-04'),('CPI','2026-11','2026-12-10')})
        self.assertEqual((a,r),before)
        result['bindings'][0]['calendar_declaration']['series']='changed'
        self.assertEqual((a,r),before)
        self.assertEqual(result['value_and_authenticated_availability'],'NOT_SUPPLIED')
        self.assertEqual(result['actual_required_cycle_or_slot_universe'],'NOT_ESTABLISHED')
        self.assertFalse(result['actual_source_admission_established']);self.assertFalse(result['utc_deadline_computed'])
        self.assertEqual(result['real_admission'],'NOT_READY');self.assertEqual(result['protocol_state_change'],'NONE')
        self.assertEqual(len(a['observations']['missing_release_times']),6)

    def test_wrong_period_series_or_stage_rejected(self):
        for field,value in [('reference_period','2026-Q2'),('series','CPI'),('release_stage','Second')]:
            with self.subTest(field=field):
                a,r=self.inputs();r['observations']['predecessor_markers'][0][field]=value
                self.assertEqual(self.bind(a,r)['status'],'REJECTED')

    def test_own_month_day_time_zone_position_and_target_order_required(self):
        for field,value in [('nyfed_month_heading','December 2026'),('omb_day_declaration','28'),
                            ('omb_month_column_1_based',12),('scheduled_time_declaration',None),
                            ('scheduled_time_declaration','25:30'),('timezone_declaration',None),
                            ('nyfed_cell_index_1_based',0),('omb_page_1_based',4),
                            ('scheduled_date_declaration','2027-02-01')]:
            with self.subTest(field=field,value=value):
                a,r=self.inputs();r['observations']['predecessor_markers'][0][field]=value
                self.assertEqual(self.bind(a,r)['status'],'REJECTED')

    def test_duplicate_missing_and_jointly_shrunk_sets_do_not_pass(self):
        for kind in ('duplicate','missing','joint','edge','frontier','inside-edge'):
            with self.subTest(kind=kind):
                a,r=self.inputs();data=a['observations'];markers=r['observations']['predecessor_markers']
                if kind=='duplicate':markers.append(deepcopy(markers[0]))
                if kind=='missing':markers.pop(0)
                if kind=='joint':
                    markers.pop(0)
                    data['outside_window_predecessors']=[x for x in data['outside_window_predecessors'] if x['series']!='GDP']
                    data['dependency_edges']=[x for x in data['dependency_edges'] if x['series']!='GDP']
                if kind=='edge':data['dependency_edges'][0]['target_date']='2027-01-09'
                if kind=='frontier':data['outside_window_predecessors'][0]['reference_period']='2026-10'
                if kind=='inside-edge':data['dependency_edges'][3]['predecessor_date_in_window']='2027-01-09'
                self.assertEqual(self.bind(a,r)['status'],'REJECTED')

    def test_input_metadata_scope_and_real_claim_changes_rejected(self):
        for child,field in [('a','sha256'),('a','bytes'),('r','sha256'),('r','file'),('r','role'),
                            ('a','scope'),('r','scope'),('a','actual_rule_adopted'),('r','value_obtained')]:
            with self.subTest(child=child,field=field):
                a,r=self.inputs();row=a if child=='a' else r
                if field=='scope':row['scope']='other'
                elif field in ('actual_rule_adopted','value_obtained'):row['observations'][field]=True
                else:
                    item=row['observations']['input_identities' if child=='a' else 'sources'][0]
                    item[field]=0 if field=='bytes' else 'changed'
                self.assertEqual(self.bind(a,r)['status'],'REJECTED')

    def test_missing_unavailable_and_rejected_never_consume_stale_observations(self):
        for side in (0,1):
            for state in ('MISSING','UNAVAILABLE','REJECTED','UNSUPPORTED'):
                with self.subTest(side=side,state=state):
                    inputs=list(self.inputs());inputs[side]['status']=state
                    result=self.bind(*inputs)
                    self.assertEqual(result['status'],state);self.assertEqual(result['bindings'],[])

    def test_known_bad_successful_sibling_survives_missing_input(self):
        for side in (0,1):
            a,r=self.inputs()
            if side==0:
                a['status']='MISSING';r['observations']['predecessor_markers'][0]['release_stage']='Third'
            else:
                r['status']='MISSING';a['observations']['dependency_edges'].pop()
            result=self.bind(a,r)
            self.assertEqual(result['status'],'REJECTED')
            self.assertEqual({f['status'] for f in result['findings']},{'MISSING','REJECTED'})

    def test_consistent_declaration_times_not_hardcoded_to_eight_thirty(self):
        a,r=self.inputs();marker=r['observations']['predecessor_markers'][0]
        marker['scheduled_time_declaration']='09:15'
        marker['nyfed_cell_text']=marker['nyfed_cell_text'].replace('1st Release (08:30)','1st Release (09:15)')
        result=self.bind(a,r)
        self.assertEqual(result['status'],'OBSERVED')
        self.assertEqual(result['bindings'][2]['calendar_declaration']['scheduled_time_declaration'],'09:15')

    def test_neighbor_indicator_label_and_clock_cannot_replace_own_series(self):
        for index,label,clock in [(0,'Weekly Economic Index','11:30'),
                                  (1,'Michigan Consumer Survey (Preliminary)','10:00'),
                                  (2,'Initial Claims','08:30')]:
            with self.subTest(series=index):
                a,r=self.inputs();marker=r['observations']['predecessor_markers'][index]
                marker.update(nyfed_indicator_label=label,scheduled_time_declaration=clock)
                result=self.bind(a,r)
                self.assertEqual(result['status'],'REJECTED');self.assertEqual(result['bindings'],[])

    def command(self,*args):
        p=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B',str(HERE/'cli.py'),*args],
                         capture_output=True,text=True,timeout=50)
        self.assertTrue(p.stdout.strip(),p.stderr);return p

    def test_actual_mainline_only_new_binding_changes_and_counts_preserved(self):
        proc=self.command('mainline','--json');self.assertEqual(proc.returncode,1)
        report=json.loads(proc.stdout);row=next(x for x in report['modules'] if x['id']=='official-calendar')
        self.assertIn('predecessor_calendar_binding',row)
        self.assertEqual(row.pop('predecessor_calendar_binding')['status'],'OBSERVED')
        next(x for x in report['modules'] if x['id']=='initial-authority')['result'].pop('technical_verifier_identity_gate')
        # New A1 children are independently asserted in test_u3_a1; preserve this older projection.
        for module in report['modules']:
            if module['id'] in ('unemployment-july','unemployment-november'):
                self.assertEqual(module.pop('target_table_support')['comparison']['status'],'OBSERVED')
        self.assertEqual(report,self.baseline)
        self.assertEqual(len(report['modules']),14);self.assertEqual(len(self.cli.CASES),12)
        self.assertEqual(sum(len(c['inputs']) for c in self.cli.CASES.values()),29)
        self.assertEqual(sum(c.get('default_demo',True) for c in self.cli.CASES.values()),5)

    def test_failed_child_empty_findings_cannot_pass(self):
        a,r=self.inputs();a.update(status='MISSING',findings=[])
        self.assertEqual(self.bind(a,r)['status'],'MISSING')

    def test_joint_date_edit_must_match_original_cell_day(self):
        a,r=self.inputs();marker=r['observations']['predecessor_markers'][0]
        marker.update(scheduled_date_declaration='2026-10-28',omb_day_declaration='28')
        self.assertEqual(self.bind(a,r)['status'],'REJECTED')

    def test_actual_empty_input_and_symlink_keep_failures_and_no_joins(self):
        with tempfile.TemporaryDirectory() as name:
            p=self.command('mainline','--inputs',name,'--json');self.assertEqual(p.returncode,1)
            row=next(x for x in json.loads(p.stdout)['modules'] if x['id']=='official-calendar')
            self.assertEqual(row.get('predecessor_calendar_binding',{}).get('status'),'MISSING')
            source=self.cli.CASES['calendar-predecessors-2026']['inputs'][0]
            (Path(name)/source['alias']).symlink_to(ROOT/source['path'])
            p=self.command('mainline','--inputs',name,'--json');self.assertEqual(p.returncode,2)
            row=next(x for x in json.loads(p.stdout)['modules'] if x['id']=='official-calendar')
            self.assertEqual(row['predecessor_calendar_binding']['status'],'REJECTED')
            self.assertEqual(row['predecessor_calendar_binding']['bindings'],[])
            self.assertEqual({f['status'] for f in row['findings']},{'REJECTED','MISSING'})

    def test_human_shows_planning_binding_and_remaining_value_gap(self):
        p=self.command('mainline');self.assertEqual(p.returncode,1)
        for text in ('窗外前置日历对应：3/3','2026-10-29','2026-12-04','2026-12-10','Eastern Time',
                     '首次发行值及认证可得证据仍缺','6条CPI/U3时刻仍缺'):
            self.assertIn(text,p.stdout)


if __name__=='__main__':unittest.main()
