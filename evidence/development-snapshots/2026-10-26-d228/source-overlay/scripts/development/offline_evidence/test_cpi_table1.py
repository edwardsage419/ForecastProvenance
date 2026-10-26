"""One exact archived CPI Table1, with old carrier observations preserved."""
from copy import deepcopy
import importlib.util
from io import BytesIO
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from pypdf import PdfReader

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CASE='cpi-june-2026-table1'
CAT=json.loads((HERE/'catalog.json').read_text())
PDF=ROOT/CAT['cpi-june-2026-archive']['inputs'][0]['path']


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


class Table1Tests(unittest.TestCase):
    def module(self):
        self.assertTrue((HERE/'cpi_table1.py').is_file(),'exact CPI Table1 consumer absent')
        return load(HERE/'cpi_table1.py','cpi_table1_test')
    def text(self):return PdfReader(BytesIO(PDF.read_bytes()),strict=True).pages[8].extract_text()
    def command(self,*args,human=False):
        p=subprocess.run([str(ROOT/'.venv/bin/python'),'-I','-B',str(HERE/'cli.py'),*args,*([] if human else ['--json'])],capture_output=True,text=True,timeout=60)
        self.assertTrue(p.stdout.strip(),p.stderr);return p,p.stdout if human else json.loads(p.stdout)
    def inputs(self):
        cli=load(HERE/'cli.py','cpi_table1_cli');copy=cli.run_case('cpi-june-2026-copy');archive=cli.run_case('cpi-june-2026-archive');table=cli.run_case(CASE)
        return cli,cli.compare_cpi_carriers(copy,archive),archive,table

    def test_actual_pdf_uses_monthly_SA_allitems_not_index_NSA_or_yearly(self):
        m=self.module();archive=load(HERE/'cpi_pdf.py','cpi_table1_archive');raw=PDF.read_bytes();calls=[]
        def observe(b):calls.append(b);return archive.observe_archive_pdf(b)
        r=m.observe_table1_pdf(raw,archive_observer=observe)
        self.assertEqual(len(calls),1);self.assertIs(calls[0],raw)
        self.assertEqual(r['display_value'],'-0.4');self.assertEqual(r['unadjusted_monthly_change'],'-0.3');self.assertEqual(r['unadjusted_yearly_change'],'3.5')
        self.assertEqual(r['seasonally_adjusted_monthly_values'],['0.6','0.5','-0.4'])
        self.assertEqual(r['selected_column_1_based'],9);self.assertEqual(r['page_1_based'],9)
        self.assertEqual(r['evidence_class'],'FRASER_ARCHIVE_TABLE1_DECLARATIONS_ONLY')
        self.assertFalse(r['original_publisher_bytes']);self.assertEqual(r['historical_first_release'],'NOT_ESTABLISHED')
        self.assertEqual(r['authenticated_availability'],'NOT_ESTABLISHED')

    def test_own_title_period_and_adjustment_column_context_required(self):
        m=self.module();t=self.text()
        for old,new in [('Table 1.','Table 2.'),('June\n2026','June\n2025'),('Seasonally adjusted percent\nchange','Unadjusted percent\nchange'),('Mar.\n2026-\nApr.\n2026','Apr.\n2026-\nMay\n2026')]:
            self.assertIn(old,t)
            with self.assertRaises(ValueError):m.parse_table1_text(t.replace(old,new,1))

    def test_missing_duplicate_or_core_allitems_cannot_supply_target(self):
        m=self.module();t=self.text();line=next(l for l in t.splitlines() if l.startswith('All items.'))
        for changed in [t.replace(line,''),t.replace(line,line+'\n'+line),t.replace(line,line.replace('All items.','All items less food and energy.',1))]:
            with self.assertRaises(ValueError):m.parse_table1_text(changed)

    def test_malformed_missing_or_wrong_column_count_rejected(self):
        m=self.module();t=self.text();line=next(l for l in t.splitlines() if l.startswith('All items.'))
        for tail in ['100.000 322.561 335.123 333.952 3.5 -0.3 0.6 -0.4','100.000 322.561 335.123 333.952 3.5 -0.3 0.6 0.5 –',
                     '100.000 322.561 335.123 333.952 3.5 -0.3 0.6 0.5 NaN','100.000 322.561 335.123 333.952 3.5 -0.3 0.6 0.5 -0.40']:
            changed=t.replace(line,'All items. . . '+tail)
            with self.assertRaises(ValueError):m.parse_table1_text(changed)

    def test_table_value_and_sign_are_derived_not_filled_from_headline(self):
        m=self.module();t=self.text();line=next(l for l in t.splitlines() if l.startswith('All items.'))
        self.assertEqual(m.parse_table1_text(t.replace(line,line[:-4]+'0.7'))['display_value'],'0.7')

    def test_actual_raw_identity_and_headline_disagreement_are_rejected(self):
        m=self.module();old=load(HERE/'cpi_pdf.py','cpi_table1_mismatch_archive');raw=PDF.read_bytes()
        with self.assertRaises(ValueError):m.observe_table1_pdf(raw+b' ',archive_observer=old.observe_archive_pdf)
        data=old.observe_archive_pdf(raw);data['display_value']='0.4'
        with self.assertRaises(ValueError):m.observe_table1_pdf(raw,archive_observer=lambda b:data)

    def test_new_fixed_case_and_original_observations_are_separate(self):
        self.module();p,r=self.command('verify',CASE);self.assertEqual(p.returncode,0)
        p,old=self.command('verify','cpi-june-2026-archive');self.assertEqual(p.returncode,0)
        self.assertEqual(r['cases'][0]['observations']['raw_sha256'],old['cases'][0]['observations']['raw_sha256'])
        self.assertEqual(old['cases'][0]['observations']['page_1_based'],1)
        self.assertEqual(old['cases'][0]['observations']['table_A_machine_verification'],'NOT_CHECKED_RASTER_TABLE')

    def test_empty_corrupt_and_symlink_explicit_inputs_have_no_fallback(self):
        self.module();alias=CAT['cpi-june-2026-archive']['inputs'][0]['alias']
        with tempfile.TemporaryDirectory() as n:
            p,r=self.command('verify',CASE,'--inputs',n);self.assertEqual(p.returncode,1)
            target=Path(n)/alias;target.write_bytes(b'wrong archive')
            p,r=self.command('verify',CASE,'--inputs',n);self.assertEqual(p.returncode,2)
            target.unlink();target.symlink_to(PDF)
            p,r=self.command('verify',CASE,'--inputs',n);self.assertEqual(p.returncode,2)

    def test_new_source_refusal_keeps_old_archive_independent_and_mixed_findings(self):
        self.module();cli,comparison,archive,table=self.inputs();case=cli.CASES[CASE]
        with tempfile.TemporaryDirectory() as n:
            root=Path(n)
            for r in case['sources']+case['inputs']:
                target=root/r['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/r['path']).read_bytes())
            helper=root/'scripts/development/offline_evidence/cpi_table1.py';helper.write_bytes(helper.read_bytes()+b' ')
            self.assertEqual(cli.run_case(CASE,repository_root=root)['status'],'REJECTED')
            self.assertEqual(cli.run_case('cpi-june-2026-archive',repository_root=root)['status'],'OBSERVED')
            helper.unlink();(root/case['inputs'][0]['path']).write_bytes(b'wrong')
            bad=cli.run_case(CASE,repository_root=root);self.assertEqual({f['status'] for f in bad['findings']},{'REJECTED','MISSING'})

    def test_same_carrier_selector_and_values_are_bound_without_mutation(self):
        self.module();cli,comparison,archive,table=self.inputs();self.assertTrue(hasattr(cli,'compare_cpi_table1'))
        before=deepcopy((comparison,archive,table));r=cli.compare_cpi_table1(comparison,archive,table)
        self.assertEqual(r['status'],'OBSERVED');self.assertEqual((comparison,archive,table),before)
        for key,value in [('raw_sha256','f'*64),('display_value','0.4'),('row','All items less food and energy'),('selected_column_1_based',6),('original_publisher_bytes',True)]:
            changed=deepcopy(table);changed['observations'][key]=value
            self.assertEqual(cli.compare_cpi_table1(comparison,archive,changed)['status'],'REJECTED',key)
        changed=deepcopy(table);changed['observations']['column_values'][8]='0.7'
        self.assertEqual(cli.compare_cpi_table1(comparison,archive,changed)['status'],'REJECTED')
        comparison.update(status='MISSING',findings=[]);table.update(status='REJECTED',findings=[])
        mixed=cli.compare_cpi_table1(comparison,archive,table);self.assertEqual(mixed['status'],'REJECTED')
        self.assertEqual({f['status'] for f in mixed['findings']},{'MISSING','REJECTED'})

    def test_mainline_only_one_new_child_changes_actual_D227_report(self):
        self.module();p,r=self.command('mainline');self.assertEqual(p.returncode,1)
        row=next(x for x in r['modules'] if x['id']=='inflation-data');child=row.pop('target_table_support')
        self.assertEqual(child['table']['status'],'OBSERVED');self.assertEqual(child['comparison']['status'],'OBSERVED')
        prior=ROOT/'docs/development/u3-exact-a1-table-consumption-2026-10-26-rev-001/MAINLINE_A.json'
        self.assertEqual((json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode(),prior.read_bytes())
        cli=load(HERE/'cli.py','cpi_table1_count_cli');self.assertEqual(len(cli.CASES),13)
        self.assertEqual(sum(len(c['inputs']) for c in cli.CASES.values()),30)
        p,r=self.command('demo');self.assertEqual(p.returncode,0);self.assertEqual(len(r['cases']),5)

    def test_human_case_and_mainline_explain_table1_archive_scope(self):
        self.module();p,text=self.command('verify',CASE,human=True);self.assertEqual(p.returncode,0)
        self.assertIn('Table 1',text);self.assertIn('归档',text);self.assertIn('-0.4',text)
        p,text=self.command('mainline',human=True);self.assertEqual(p.returncode,1);self.assertIn('CPI Table 1',text)


if __name__=='__main__':unittest.main()
