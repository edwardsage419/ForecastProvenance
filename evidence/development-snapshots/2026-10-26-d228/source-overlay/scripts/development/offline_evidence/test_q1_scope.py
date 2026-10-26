"""User-selected assessment objects never become an actual mandatory universe."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PACKAGE=ROOT/'docs/development/q1-2027-read-only-assessment-2026-10-25-rev-001'
PRIOR=ROOT/'docs/development/forward-quarter-calendar-evidence-2026-10-25-rev-001'
BINDING=ROOT/'docs/development/mainline-execution-2026-10-09-rev-001/calendar-declaration-binding/binding.py'
ALIASES={'omb':'omb-2027-pfei.pdf','bea':'bea-2027-next-year.html',
         'inventory':'q1-2027-planning-inventory.json','selection':'q1-2027-read-only-scope.json'}
CASE='q1-2027-read-only-assessment'


def load(path):
    spec=importlib.util.spec_from_file_location('q1_test_'+path.stem,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class Q1ScopeTests(unittest.TestCase):
    def consumer(self):
        self.assertTrue((HERE/'q1_scope.py').is_file(),'selected-scope consumer is absent')
        return load(HERE/'q1_scope.py')

    def raws(self):
        return {'omb':(PRIOR/'raw/omb-2027-pfei.pdf').read_bytes(),
                'bea':(PRIOR/'raw/bea-2027-next-year.html').read_bytes(),
                'inventory':(PRIOR/'PLANNING_INVENTORY.json').read_bytes(),
                'selection':(PACKAGE/'READ_ONLY_SCOPE_SELECTION.json').read_bytes()}

    def parsed(self):
        self.consumer()
        annual=load(HERE/'predecessor_calendar.py').parse_omb_pages(
            (PRIOR/'inspection/page-3.txt').read_text(),(PRIOR/'inspection/page-4.txt').read_text(),
            year=2027,annual=True)
        raw=self.raws()
        return annual,load(BINDING).annual(raw['bea'],2027),json.loads(raw['inventory']),json.loads(raw['selection'])

    def observe(self):
        return self.consumer().observe_q1_assessment(self.raws(),
            parse_omb_pages=load(HERE/'predecessor_calendar.py').parse_omb_pages,
            annual_parser=load(BINDING).annual)

    def command(self,*args,human=False):
        process=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B',str(HERE/'cli.py'),
            *args,*([] if human else ['--json'])],capture_output=True,text=True,timeout=50)
        self.assertTrue(process.stdout.strip(),process.stderr)
        return process,process.stdout if human else json.loads(process.stdout)

    def test_exact_nine_dates_separate_seven_targets_and_two_revisions(self):
        data=self.observe()
        self.assertEqual([(x['series'],x['scheduled_date_declaration'],x['reference_period']) for x in data['rows']],
            [('U3','2027-01-08','2026-12'),('CPI','2027-01-13','2026-12'),('GDP','2027-01-28','2026-Q4'),
             ('U3','2027-02-05','2027-01'),('CPI','2027-02-11','2027-01'),('GDP','2027-02-25','2026-Q4'),
             ('U3','2027-03-05','2027-02'),('CPI','2027-03-10','2027-02'),('GDP','2027-03-31','2026-Q4')])
        self.assertEqual(data['target_release_candidates'],7)
        self.assertEqual(data['revision_reference_rows'],2)
        self.assertEqual([x['release_stage'] for x in data['rows'] if x['series']=='GDP'],['Advance','Second','Third'])
        self.assertFalse(data['forecast_issued']);self.assertEqual(data['protocol_state_change'],'NONE')

    def test_six_monthly_times_not_borrowed_and_no_timezone_or_deadlines_invented(self):
        data=self.observe()
        self.assertEqual(len(data['missing_release_times']),6)
        for row in data['rows']:
            if row['series']=='GDP':self.assertEqual(row['scheduled_time_declaration'],'8:30 AM')
            else:self.assertIsNone(row['scheduled_time_declaration'])
            self.assertIsNone(row['timezone_declaration'])
            self.assertIsNone(row['utc_barrier'])
        self.assertFalse(data['utc_deadline_computed'])
        self.assertEqual(data['actual_required_cycle_or_slot_universe'],'NOT_ESTABLISHED')

    def test_previous_first_release_dependencies_cross_year_and_exclude_revisions(self):
        data=self.observe();edges=data['dependency_edges']
        self.assertEqual(len(edges),7)
        expected={('U3','2026-12'):('2026-11',None),('CPI','2026-12'):('2026-11',None),
                  ('GDP','2026-Q4'):('2026-Q3',None),('U3','2027-01'):('2026-12','2027-01-08'),
                  ('CPI','2027-01'):('2026-12','2027-01-13'),('U3','2027-02'):('2027-01','2027-02-05'),
                  ('CPI','2027-02'):('2027-01','2027-02-11')}
        self.assertEqual({(e['series'],e['target_reference_period']):(e['predecessor_reference_period'],e['predecessor_date_in_window']) for e in edges},expected)
        self.assertEqual(len(data['outside_window_predecessors']),3)
        self.assertTrue(all(e['value_and_authenticated_availability']=='NOT_SUPPLIED' for e in edges))

    def test_selected_assessment_does_not_adopt_scope_or_truncate_duties(self):
        data=self.observe()
        self.assertTrue(data['read_only_scope_selected'])
        for key in ('actual_governing_scope_established','actual_rule_adopted','actual_source_admission_established',
                    'quarter_end_terminates_post_genesis_duties','authenticated_availability_established'):
            self.assertFalse(data[key])
        self.assertEqual(data['real_admission'],'NOT_READY')
        self.assertEqual(data['operational_bindings_established'],0)

    def test_annual_edition_columns_previous_month_and_quarter_rows_required(self):
        self.consumer();parser=load(HERE/'predecessor_calendar.py').parse_omb_pages
        p3=(PRIOR/'inspection/page-3.txt').read_text();p4=(PRIOR/'inspection/page-4.txt').read_text()
        for a,b in [(p3.replace('FOR 2027','FOR 2026'),p4),(p3,p4.replace('previous month','current month')),
                    (p3.replace("4Q'26","3Q'26"),p4),(p3+p3,p4),
                    (p3,p4.replace('JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC','FEB JAN MAR APR MAY JUN JUL AUG SEP OCT NOV DEC'))]:
            with self.subTest():
                with self.assertRaises(ValueError):parser(a,b,year=2027,annual=True)

    def test_bea_own_time_duplicate_and_date_conflict_rejected(self):
        consumer=self.consumer();a,b,inventory,scope=self.parsed()
        for kind in ('time','duplicate','date','columns','clock-conflict'):
            with self.subTest(kind=kind):
                rows=deepcopy(b);index=next(i for i,r in enumerate(rows) if r[2]['text']=='GDP (Advance Estimate), 4th Quarter and Year 2026')
                if kind=='time':rows[index][0]['text']='January 28'
                if kind=='duplicate':rows.append(deepcopy(rows[index]))
                if kind=='date':rows[index][0]['text']='January 29 8:30 AM'
                if kind=='columns':rows[index][0]['attrs']['headers']='wrong-column'
                if kind=='clock-conflict':rows[index][0]['text']='January 28 9:15 AM'
                with self.assertRaises(ValueError):consumer.assess(a,rows,inventory,scope)
        rows=deepcopy(b);index=next(i for i,r in enumerate(rows) if r[2]['text']=='GDP (Advance Estimate), 4th Quarter and Year 2026')
        rows[index][0]['text']='January 28 9:15 AM'
        inventory=deepcopy(inventory)
        next(r for r in inventory['items'] if r['release_stage']=='Advance')['release_time_declaration']='9:15 AM'
        result=consumer.assess(a,rows,inventory,scope)
        self.assertEqual(next(x for x in result['rows'] if x['series']=='GDP')['scheduled_time_declaration'],'9:15 AM')

    def test_jointly_reduced_calendar_and_inventory_rejected_not_empty_universe(self):
        consumer=self.consumer();a,b,inventory,scope=self.parsed()
        reduced=deepcopy(a);reduced['CPI'].pop(0)
        inventory=deepcopy(inventory);inventory['items']=[r for r in inventory['items'] if r['release_date_declaration']!='2027-01-13']
        with self.assertRaises(ValueError):consumer.assess(reduced,b,inventory,scope)
        self.assertEqual(self.observe()['actual_required_cycle_or_slot_universe'],'NOT_ESTABLISHED')

    def test_revision_or_reference_period_substitution_rejected_without_mutation(self):
        consumer=self.consumer();args=self.parsed();before=deepcopy(args)
        consumer.assess(*args);self.assertEqual(args,before)
        for field,value in [('planning_role','TARGET_RELEASE_CANDIDATE_PENDING_APPLICABILITY'),
                            ('reference_period_declaration','2027-Q1')]:
            a,b,inventory,scope=deepcopy(args)
            row=next(r for r in inventory['items'] if r['release_stage']=='Second');row[field]=value
            with self.assertRaises(ValueError):consumer.assess(a,b,inventory,scope)

    def test_scope_window_series_or_duty_exemption_cannot_be_silently_changed(self):
        consumer=self.consumer();args=self.parsed()
        for field,value in [('end_inclusive','2027-02-28'),('series',['GDP','U3']),
                            ('quarter_end_terminates_post_genesis_duties',True),('actual_rule_adopted',True)]:
            a,b,inventory,scope=deepcopy(args);scope[field]=value
            with self.assertRaises(ValueError):consumer.assess(a,b,inventory,scope)

    def test_exact_four_raw_inputs_and_source_identities_required(self):
        consumer=self.consumer();raw=self.raws();kwargs={'parse_omb_pages':load(HERE/'predecessor_calendar.py').parse_omb_pages,'annual_parser':load(BINDING).annual}
        for role in raw:
            with self.subTest(role=role):
                changed=dict(raw);changed[role]+=b' '
                with self.assertRaises(ValueError):consumer.observe_q1_assessment(changed,**kwargs)
        changed=dict(raw);changed['extra']=b'not selected'
        with self.assertRaises(ValueError):consumer.observe_q1_assessment(changed,**kwargs)

    def test_standalone_and_mainline_reuse_legacy_results_with_new_child_only(self):
        proc,data=self.command('verify',CASE)
        self.assertEqual(proc.returncode,0);self.assertEqual(data['cases'][0]['status'],'OBSERVED')
        proc,report=self.command('mainline');self.assertEqual(proc.returncode,1)
        self.assertEqual(len(report['modules']),14)
        row=next(x for x in report['modules'] if x['id']=='official-calendar')
        child=row.pop('read_only_assessment');self.assertEqual(child['status'],'OBSERVED')
        self.assertEqual(row.pop('predecessor_calendar_binding')['status'],'OBSERVED')
        next(x for x in report['modules'] if x['id']=='initial-authority')['result'].pop('technical_verifier_identity_gate')
        baseline=json.loads((ROOT/'docs/development/mainline-summary-truthfulness-2026-10-25-rev-001/MAINLINE_JSON.json').read_text())
        # New A1/Table1 children have their own exact tests; preserve this older projection.
        for module in report['modules']:
            if module['id'] in ('unemployment-july','unemployment-november','inflation-data'):
                self.assertEqual(module.pop('target_table_support')['comparison']['status'],'OBSERVED')
        self.assertEqual(report,baseline)

    def test_explicit_missing_and_corrupt_new_inputs_keep_legacy_children_observed(self):
        cases=json.loads((HERE/'catalog.json').read_text());self.assertIn(CASE,cases)
        with tempfile.TemporaryDirectory() as name:
            base=Path(name)
            for case in cases.values():
                for row in case['inputs']:
                    target=base/row['alias'];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/row['path'],target)
            (base/ALIASES['omb']).unlink();target=base/ALIASES['bea'];target.write_bytes(target.read_bytes()+b' ')
            proc,report=self.command('mainline','--inputs',name)
        row=next(x for x in report['modules'] if x['id']=='official-calendar')
        self.assertEqual(proc.returncode,2);self.assertEqual(row['status'],'REJECTED')
        self.assertEqual(row['result']['status'],'OBSERVED');self.assertEqual(row['predecessor_research']['status'],'OBSERVED')
        self.assertEqual({f['status'] for f in row['read_only_assessment']['findings']},{'REJECTED','MISSING'})

    def test_symlink_empty_directory_and_missing_runtime_never_use_ambient_inputs(self):
        self.consumer()
        with tempfile.TemporaryDirectory() as name:
            proc,data=self.command('verify',CASE,'--inputs',name)
            self.assertEqual(proc.returncode,1);self.assertEqual(data['cases'][0]['status'],'MISSING')
            for role,raw in self.raws().items():(Path(name)/ALIASES[role]).write_bytes(raw)
            target=Path(name)/ALIASES['omb'];target.unlink();target.symlink_to(PRIOR/'raw/omb-2027-pfei.pdf')
            proc,data=self.command('verify',CASE,'--inputs',name)
            self.assertEqual(proc.returncode,2);self.assertEqual(data['cases'][0]['status'],'REJECTED')
        cli=load(HERE/'cli.py')
        with patch.object(cli,'PDF_PYTHON',Path('/nonexistent/q1-pdf-runtime')):
            self.assertEqual(cli.run_case(CASE)['status'],'UNAVAILABLE')

    def test_human_scope_and_missing_time_explanation_and_demo_count(self):
        proc,text=self.command('verify',CASE,human=True)
        self.assertEqual(proc.returncode,0)
        for value in ('只读','7','2','6','2027-01-08','2027-01-28','2026-11','未建立完整必需全集'):
            self.assertIn(value,text)
        proc,data=self.command('demo');self.assertEqual(proc.returncode,0);self.assertEqual(len(data['cases']),5)


if __name__=='__main__':unittest.main()
