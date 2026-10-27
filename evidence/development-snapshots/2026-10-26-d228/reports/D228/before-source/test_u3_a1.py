"""Exact A-1 TOTAL/SA observations, with existing summary checks preserved."""
from copy import deepcopy
from dataclasses import asdict
import hashlib
import importlib.util
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
PACK=ROOT/'docs/development/u3-exact-a1-table-consumption-2026-10-26-rev-001'
LEGACY=ROOT/'docs/development/mainline-execution-2026-10-09-rev-001/unemployment-pdf-consumption/consumer.py'
CASES=json.loads((HERE/'catalog.json').read_text())
NAMES={'2025-07':'u3-july-2025','2025-11':'u3-november-2025'}
PAGES={'2025-07':11,'2025-11':14}


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


class A1Tests(unittest.TestCase):
    def module(self):
        self.assertTrue((HERE/'u3_a1.py').is_file(),'exact A1 consumer is absent')
        return load(HERE/'u3_a1.py','u3_a1_test')

    def raw(self,month):return (ROOT/CASES[NAMES[month]]['inputs'][0]['path']).read_bytes()
    def page(self,month):return PdfReader(BytesIO(self.raw(month)),strict=True).pages[PAGES[month]-1].extract_text()
    def legacy(self):return load(LEGACY,'u3_a1_legacy')

    def command(self,*args):
        p=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B',str(HERE/'cli.py'),*args,'--json'],capture_output=True,text=True,timeout=50)
        self.assertTrue(p.stdout.strip(),p.stderr);return p,json.loads(p.stdout)

    def test_actual_two_editions_use_total_SA_not_unadjusted_or_men(self):
        m=self.module();legacy=self.legacy()
        for month,want,nsa in [('2025-07','4.2','4.6'),('2025-11','4.6','4.3')]:
            with self.subTest(month=month):
                raw=self.raw(month);calls=[]
                def summarize(b,**kw):calls.append(b);return asdict(legacy.observe_u3_pdf(b,**kw))
                r=m.observe_a1_pdf(raw,reference_month=month,summary_observer=summarize)
                self.assertEqual(r['display_value'],want);self.assertEqual(r['unadjusted_current_value'],nsa)
                self.assertEqual(r['table_pdf_page'],PAGES[month]);self.assertEqual(len(r['column_values']),9)
                self.assertEqual(r['selected_column_1_based'],9);self.assertEqual(len(calls),1);self.assertIs(calls[0],raw)
                self.assertEqual(r['raw_sha256'],hashlib.sha256(raw).hexdigest())
                self.assertEqual(r['evidence_class'],'ARCHIVAL_A1_TABLE_DECLARATION_ONLY')
                self.assertEqual(r['authenticated_availability'],'NOT_ESTABLISHED')

    def test_november_absent_october_is_not_zero_or_a_revised_fallback(self):
        m=self.module();r=m.parse_a1_text(self.page('2025-11'),reference_month='2025-11')
        self.assertIsNone(r['prior_value']);self.assertEqual(r['prior_status'],'SOURCE_DECLARED_NOT_COLLECTED')
        for text in [self.page('2025-11').replace('4.0 – 4.3 4.2 4.2 4.3 4.4 – 4.6','4.0 – 4.3 4.2 4.2 4.3 4.4 0.0 4.6'),
                     self.page('2025-11').replace('Data for October 2025 were not collected','Data issue unknown')]:
            with self.assertRaises(ValueError):m.parse_a1_text(text,reference_month='2025-11')

    def test_own_header_order_month_and_section_required(self):
        m=self.module();text=self.page('2025-07')
        edits=[('Table A-1.','Summary table A.'),('Not seasonally adjusted Seasonally adjusted 1','Seasonally adjusted 1 Not seasonally adjusted'),
               ('July\n2024\nMar.\n2025','July\n2024\nApr.\n2025'),('\nTOTAL\n','\nMEN\n')]
        for old,new in edits:
            with self.subTest(old=old):
                self.assertIn(old,text)
                with self.assertRaises(ValueError):m.parse_a1_text(text.replace(old,new,1),reference_month='2025-07')

    def test_missing_duplicate_or_malformed_total_rate_is_rejected(self):
        m=self.module();text=self.page('2025-07');line=next(l for l in text.splitlines() if l.startswith('Unemployment rate.'))
        for changed in [text.replace(line,''),text.replace(line,line+'\n'+line),text.replace(line,line.replace('4.5 4.4 4.6','4.5 4.4')),
                        text.replace(line,line[:-3]+'–'),text.replace(line,line[:-3]+'101.0')]:
            with self.assertRaises(ValueError):m.parse_a1_text(changed,reference_month='2025-07')

    def test_parser_derives_current_value_instead_of_filling_expected_constant(self):
        m=self.module();text=self.page('2025-07');line=next(l for l in text.splitlines() if l.startswith('Unemployment rate.'))
        changed=text.replace(line,line[:-3]+'5.1')
        self.assertEqual(m.parse_a1_text(changed,reference_month='2025-07')['display_value'],'5.1')

    def test_summary_disagreement_and_wrong_raw_edition_do_not_pass(self):
        m=self.module();legacy=self.legacy();raw=self.raw('2025-07')
        summary=asdict(legacy.observe_u3_pdf(raw,reference_month='2025-07'));summary['display_value']='5.1'
        with self.assertRaises(ValueError):m.observe_a1_pdf(raw,reference_month='2025-07',summary_observer=lambda *a,**k:summary)
        with self.assertRaises(ValueError):m.observe_a1_pdf(self.raw('2025-11'),reference_month='2025-07',summary_observer=lambda *a,**k:summary)

    def test_new_cases_and_old_summary_have_same_raw_and_value(self):
        self.module()
        for month,name in NAMES.items():
            p,r=self.command('verify',name+'-a1');self.assertEqual(p.returncode,0)
            new=r['cases'][0];p,old=self.command('verify',name);self.assertEqual(p.returncode,0)
            self.assertEqual(new['observations']['raw_sha256'],old['cases'][0]['observations']['raw_sha256'])
            self.assertEqual(new['observations']['display_value'],old['cases'][0]['observations']['display_value'])
            self.assertEqual(old['cases'][0]['observations']['table_pdf_page'],4 if month=='2025-07' else 7)

    def test_exact_case_empty_corrupt_symlink_inputs_never_fall_back(self):
        self.module();name=NAMES['2025-07'];row=CASES[name]['inputs'][0]
        with tempfile.TemporaryDirectory() as n:
            p,r=self.command('verify',name+'-a1','--inputs',n);self.assertEqual(p.returncode,1)
            self.assertEqual(r['cases'][0]['status'],'MISSING')
            path=Path(n)/row['alias'];path.write_bytes(b'wrong')
            p,r=self.command('verify',name+'-a1','--inputs',n);self.assertEqual(p.returncode,2)
            path.unlink();path.symlink_to(ROOT/row['path'])
            p,r=self.command('verify',name+'-a1','--inputs',n);self.assertEqual(p.returncode,2)

    def test_new_source_refusal_does_not_replace_old_summary(self):
        self.module();cli=load(HERE/'cli.py','a1_source_cli');case=cli.CASES['u3-july-2025-a1']
        with tempfile.TemporaryDirectory() as n:
            root=Path(n)
            for row in case['sources']+case['inputs']:
                dest=root/row['path'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/row['path']).read_bytes())
            helper=root/'scripts/development/offline_evidence/u3_a1.py';helper.write_bytes(helper.read_bytes()+b' ')
            self.assertEqual(cli.run_case('u3-july-2025-a1',repository_root=root)['status'],'REJECTED')
            self.assertEqual(cli.run_case('u3-july-2025',repository_root=root)['status'],'OBSERVED')
            helper.unlink();(root/case['inputs'][0]['path']).write_bytes(b'wrong')
            result=cli.run_case('u3-july-2025-a1',repository_root=root)
            self.assertEqual({x['status'] for x in result['findings']},{'REJECTED','MISSING'})

    def test_crosscomparison_rejects_subject_or_value_substitution_and_retains_missing(self):
        self.module();cli=load(HERE/'cli.py','a1_binding_cli')
        self.assertTrue(hasattr(cli,'compare_u3_target_table'),'same-edition comparison absent')
        old=cli.run_case('u3-july-2025');new=cli.run_case('u3-july-2025-a1');before=deepcopy((old,new))
        self.assertEqual(cli.compare_u3_target_table(old,new)['status'],'OBSERVED')
        self.assertEqual((old,new),before)
        for key,value in [('raw_sha256','f'*64),('reference_month','2025-11'),('display_value','5.0')]:
            changed=deepcopy(new);changed['observations'][key]=value
            self.assertEqual(cli.compare_u3_target_table(old,changed)['status'],'REJECTED')
        old.update(status='MISSING',findings=[]);new.update(status='REJECTED',findings=[])
        r=cli.compare_u3_target_table(old,new);self.assertEqual(r['status'],'REJECTED')
        self.assertEqual({f['status'] for f in r['findings']},{'MISSING','REJECTED'})

    def test_equal_value_cannot_hide_wrong_A1_row_or_inconsistent_columns(self):
        self.module();cli=load(HERE/'cli.py','a1_strict_binding_cli')
        self.assertTrue(hasattr(cli,'compare_u3_target_table'))
        old=cli.run_case('u3-november-2025');new=cli.run_case('u3-november-2025-a1')
        # Men16+ happens to equal TOTAL4.6 in this actual edition; matching the
        # displayed rate alone must not establish the target selector.
        changes=[('row','Men, 16 years and over / Unemployment rate'),('table','A-2'),
                 ('summary_table_pdf_page',99),('evidence_class','OFFICIAL_FIRST_VERIFIED')]
        for key,value in changes:
            changed=deepcopy(new);changed['observations'][key]=value
            self.assertEqual(cli.compare_u3_target_table(old,changed)['status'],'REJECTED',key)
        changed=deepcopy(new);changed['observations']['column_values'][8]='5.0'
        self.assertEqual(cli.compare_u3_target_table(old,changed)['status'],'REJECTED')

    def test_mainline_only_two_new_children_change_retained_normal_report(self):
        self.module();p,r=self.command('mainline');self.assertEqual(p.returncode,1)
        for row in r['modules']:
            if row['id'] in ('unemployment-july','unemployment-november'):
                child=row.pop('target_table_support');self.assertEqual(child['comparison']['status'],'OBSERVED')
                self.assertEqual(child['table']['status'],'OBSERVED')
        prior=json.loads((ROOT/'docs/development/mainline-runtime-availability-2026-10-26-rev-001/COMPATIBLE_AFTER.json').read_text())
        self.assertEqual(r,prior);self.assertEqual(len(r['modules']),14)
        cli=load(HERE/'cli.py','a1_count_cli');self.assertEqual(len(cli.CASES),12)
        self.assertEqual(sum(len(c['inputs']) for c in cli.CASES.values()),29)
        p,r=self.command('demo');self.assertEqual(p.returncode,0);self.assertEqual(len(r['cases']),5)


if __name__=='__main__':unittest.main()
