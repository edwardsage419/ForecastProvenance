"""New official compilations remain finite planning observations, not admission."""
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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RAW = ROOT/'docs/development/predecessor-calendar-times-2026-10-25-rev-001/raw'
INSPECTION = RAW.parent/'inspection'
FILES = {'nyfed_oct2026':'nyfed-oct2026.html', 'nyfed_dec2026':'nyfed-dec2026.html',
         'omb_2026':'omb-2026-pfei.pdf'}


def load(name):
    spec = importlib.util.spec_from_file_location('predecessor_test_'+name,HERE/(name+'.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PredecessorCalendarTests(unittest.TestCase):
    def observe(self):
        return load('predecessor_calendar').observe_predecessor_calendars(
            {role:(RAW/name).read_bytes() for role,name in FILES.items()})

    def parsed(self):
        m = load('predecessor_calendar')
        a = m.parse_nyfed_month((RAW/FILES['nyfed_oct2026']).read_text(),'2026-10')
        a.update(m.parse_nyfed_month((RAW/FILES['nyfed_dec2026']).read_text(),'2026-12'))
        b = m.parse_omb_pages((INSPECTION/'omb-page-3.txt').read_text(),
                              (INSPECTION/'omb-page-4.txt').read_text())
        return m,a,b

    def command(self,*args,human=False):
        process = subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B',str(HERE/'cli.py'),
                                  *args,*([] if human else ['--json'])],
                                 capture_output=True,text=True,timeout=45)
        self.assertTrue(process.stdout.strip(),process.stderr)
        return process,process.stdout if human else json.loads(process.stdout)

    def test_real_three_markers_and_explicit_unestablished_facts(self):
        data = self.observe()
        rows = {r['series']:r for r in data['predecessor_markers']}
        self.assertEqual({k:(r['scheduled_date_declaration'],r['reference_period']) for k,r in rows.items()},
                         {'GDP':('2026-10-29','2026-Q3'),'U3':('2026-12-04','2026-11'),
                          'CPI':('2026-12-10','2026-11')})
        for r in rows.values():
            self.assertEqual(r['scheduled_time_declaration'],'08:30')
            self.assertEqual(r['timezone_declaration'],'Eastern Time')
            self.assertTrue(r['schedule_tentative'])
            self.assertFalse(r['reference_period_directly_declared_by_nyfed'])
            self.assertGreater(r['nyfed_cell_index_1_based'],0)
            self.assertIn(r['omb_page_1_based'],[3,4])
        self.assertEqual(data['evidence_class'],'OFFICIAL_COMPILATION_PLANNING_DECLARATIONS_NOT_ADMITTED_SOURCE')
        self.assertEqual(data['mandatory_universe'],'NOT_ESTABLISHED')
        self.assertEqual(data['source_independence'],'NOT_ESTABLISHED')
        self.assertEqual(data['q1_2027_cpi_u3_time_rows_supplied'],0)
        self.assertEqual(data['operational_bindings_established'],0)
        for field in ['actual_source_admission_established','actual_scope_selected','external_links_followed',
                      'value_obtained','publication_event_verified','authenticated_availability_established',
                      'utc_deadline_computed']:
            self.assertFalse(data[field])

    def test_month_header_timezone_tentative_and_stage_required(self):
        m=load('predecessor_calendar');text=(RAW/FILES['nyfed_oct2026']).read_text()
        for changed in [text.replace('October 2026','October 2027'),
                        text.replace('all Eastern Time','all Central Time'),
                        text.replace('Dates and times are tentative and subject to immediate change.',''),
                        text.replace('Gross Domestic Product 1st Release','Gross Domestic Product 2nd Release')]:
            with self.subTest(change=changed[:80]):
                self.assertNotEqual(changed,text)
                with self.assertRaises(ValueError):m.parse_nyfed_month(changed,'2026-10')

    def test_target_time_cannot_be_borrowed_from_neighbor_or_defaulted(self):
        m=load('predecessor_calendar');text=(RAW/FILES['nyfed_dec2026']).read_text()
        pattern=r'(Employment Situation</a>\s*<br\s*/?>\s*)\(08:30\)'
        changed,n=re.subn(pattern,r'\1',text,count=1)
        self.assertEqual(n,1)
        with self.assertRaises(ValueError):m.parse_nyfed_month(changed,'2026-12')
        changed,n=re.subn(pattern,r'\1(09:15)',text,count=1);self.assertEqual(n,1)
        self.assertEqual(m.parse_nyfed_month(changed,'2026-12')['U3']['scheduled_time_declaration'],'09:15')
        self.assertEqual(m.parse_nyfed_month(changed,'2026-12')['CPI']['scheduled_time_declaration'],'08:30')

    def test_duplicate_target_and_invalid_calendar_day_rejected(self):
        m=load('predecessor_calendar');text=(RAW/FILES['nyfed_dec2026']).read_text()
        clone='<td class="somatdR dirColR"><div>04 <a href="https://www.bls.gov/news.release/empsit.toc.htm">Employment Situation</a>(08:30)</div></td>'
        with self.assertRaises(ValueError):m.parse_nyfed_month(text+clone,'2026-12')
        changed,n=re.subn(r'(<div>)04(\s*<br\s*/?>\s*<br\s*/?>\s*<span[^>]*><a[^>]*>Employment Situation)',r'\g<1>99\2',text,count=1)
        self.assertEqual(n,1)
        with self.assertRaises(ValueError):m.parse_nyfed_month(changed,'2026-12')

    def test_omb_edition_previous_month_and_quarter_mapping_required(self):
        m=load('predecessor_calendar');p3=(INSPECTION/'omb-page-3.txt').read_text();p4=(INSPECTION/'omb-page-4.txt').read_text()
        for a,b in [(p3.replace('FOR 2026','FOR 2027'),p4),
                    (p3,p4.replace('previous month','current month')),
                    (p3.replace("3Q'26","2Q'26"),p4), (p3+p3,p4)]:
            with self.subTest():
                with self.assertRaises(ValueError):m.parse_omb_pages(a,b)

    def test_join_rejects_conflict_and_jointly_shrunken_sets_never_prove_universe(self):
        m,a,b=self.parsed();original=deepcopy((a,b))
        result=m.join_declarations(a,b)
        self.assertEqual(len(result),3);self.assertEqual((a,b),original)
        changed=deepcopy(b);changed['U3']['scheduled_date_declaration']='2026-12-05'
        with self.assertRaises(ValueError):m.join_declarations(a,changed)
        for value in ['U3','GDP']:
            x,y=deepcopy(a),deepcopy(b);x.pop(value);y.pop(value)
            with self.assertRaises(ValueError):m.join_declarations(x,y)
        self.assertEqual(self.observe()['mandatory_universe'],'NOT_ESTABLISHED')

    def test_exact_input_roles_and_raw_identity(self):
        m=load('predecessor_calendar');raw={role:(RAW/name).read_bytes() for role,name in FILES.items()}
        for role in FILES:
            changed=dict(raw);changed[role]+=b'\n'
            with self.assertRaises(ValueError):m.observe_predecessor_calendars(changed)
        changed=dict(raw);changed['extra']=b'public-extra'
        with self.assertRaises(ValueError):m.observe_predecessor_calendars(changed)

    def test_standalone_replay_mainline_and_legacy_results(self):
        first,a=self.command('verify','calendar-predecessors-2026');second,b=self.command('verify','calendar-predecessors-2026')
        self.assertEqual((first.returncode,second.returncode),(0,0));self.assertEqual(a,b)
        self.assertEqual(a['cases'][0]['status'],'OBSERVED')
        proc,report=self.command('mainline');rows={r['id']:r for r in report['modules']}
        self.assertEqual(len(rows),14);self.assertEqual(proc.returncode,1)
        calendar=rows['official-calendar'];self.assertEqual(calendar['status'],'OBSERVED')
        self.assertEqual(len(calendar['result']['observations']['events']),8)
        self.assertEqual(calendar['predecessor_research']['status'],'OBSERVED')
        self.assertEqual(rows['mandatory-cycles']['status'],'MISSING')
        self.assertEqual(rows['initial-authority']['result']['status'],'UNKNOWN')
        self.assertEqual(report['real_admission'],'NOT_READY')

    def test_missing_and_corrupt_inputs_both_retained_without_fallback(self):
        with tempfile.TemporaryDirectory() as name:
            root=Path(name)
            shutil.copyfile(RAW/FILES['nyfed_oct2026'],root/FILES['nyfed_oct2026'])
            (root/FILES['nyfed_dec2026']).write_bytes((RAW/FILES['nyfed_dec2026']).read_bytes()+b' ')
            proc,report=self.command('mainline','--inputs',name)
        calendar=next(r for r in report['modules'] if r['id']=='official-calendar')
        self.assertEqual(proc.returncode,2);self.assertEqual(calendar['status'],'REJECTED')
        self.assertEqual(calendar['result']['status'],'MISSING')
        child=calendar['predecessor_research'];self.assertEqual(child['status'],'REJECTED')
        self.assertEqual({f['status'] for f in child['findings']},{'MISSING','REJECTED'})
        self.assertEqual({f['status'] for f in calendar['findings']},{'MISSING','REJECTED'})

    def test_empty_explicit_root_and_symlink_input_reject_or_remain_missing(self):
        with tempfile.TemporaryDirectory() as name:
            proc,report=self.command('verify','calendar-predecessors-2026','--inputs',name)
            self.assertEqual(proc.returncode,1);self.assertEqual(report['cases'][0]['status'],'MISSING')
            for filename in FILES.values():shutil.copyfile(RAW/filename,Path(name)/filename)
            target=Path(name)/FILES['nyfed_dec2026'];target.unlink();target.symlink_to(RAW/FILES['nyfed_dec2026'])
            proc,report=self.command('verify','calendar-predecessors-2026','--inputs',name)
            self.assertEqual(proc.returncode,2);self.assertEqual(report['cases'][0]['status'],'REJECTED')

    def test_missing_runtime_has_no_success(self):
        m=load('cli')
        with patch.object(m,'PDF_PYTHON',Path('/nonexistent/fp-pdf-runtime')):
            self.assertEqual(m.run_case('calendar-predecessors-2026')['status'],'UNAVAILABLE')

    def test_human_output_explains_association_and_no_source_admission(self):
        proc,text=self.command('verify','calendar-predecessors-2026',human=True)
        self.assertEqual(proc.returncode,0)
        self.assertIn('2026-10-29',text);self.assertIn('08:30',text)
        self.assertIn('汇编',text);self.assertIn('未纳入实际来源合同',text)
        self.assertIn('参考期',text);self.assertNotIn('失业率=',text)


if __name__=='__main__':unittest.main()
