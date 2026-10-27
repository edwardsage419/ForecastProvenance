"""Bounded, offline D228 replay; only writes this package and fresh temp roots."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import ModuleType
from zipfile import ZipFile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
CODE=Path('scripts/development/offline_evidence')
PYTHON=ROOT/'.venv/bin/python'
BASE=ROOT/'docs/development/q1-gate-mainline-replay-delivery-2026-10-25-rev-001'
ARCHIVE=BASE/'q1-gate-mainline-replay.zip'


def identity(raw):return {'bytes':len(raw),'sha256':sha256(raw).hexdigest()}
def save(name,data):
    (HERE/name).write_text(json.dumps(data,ensure_ascii=False,sort_keys=True,indent=2)+'\n')


def command(name,root,*args):
    p=subprocess.run([str(PYTHON),'-I','-B',str(root/CODE/'cli.py'),'mainline',*args,'--json'],
                     cwd=root,capture_output=True,timeout=60)
    (HERE/(name+'.json')).write_bytes(p.stdout)
    (HERE/(name+'.stderr.txt')).write_bytes(p.stderr)
    result=json.loads(p.stdout)
    assert result['real_admission']=='NOT_READY' and result['protocol_state_change']=='NONE'
    return p.returncode,result


def differences(a,b,path=''):
    if type(a) is not type(b):return [dict(path=path,before=a,after=b)]
    if isinstance(a,dict):
        assert a.keys()==b.keys(),path
        return [d for k in a for d in differences(a[k],b[k],path+'/'+k)]
    if isinstance(a,list):
        assert len(a)==len(b),path
        return [d for i,(x,y) in enumerate(zip(a,b)) for d in differences(x,y,path+'/'+str(i))]
    return [] if a==b else [dict(path=path,before=a,after=b)]


def main():
    # Never import an unbound cached bytecode version of the replay helper.
    helper=BASE/'test_q1_gate_delivery.py';raw=helper.read_bytes()
    assert sha256(raw).hexdigest()=='3c16d177f1d584a7d8a7042984497eee79802c29ed638c956f1f2b9bf455a5cb'
    m=ModuleType('d228_pinned_delivery');m.__file__=str(helper);sys.modules[m.__name__]=m
    exec(compile(raw,str(helper),'exec'),m.__dict__)
    assert identity(ARCHIVE.read_bytes())==dict(bytes=15024382,sha256='929c335232c9eae1ccde94bab6dca9b2395cf8c6600579a673e4f09ba69f648f')
    # The old unpack helper checks member paths/types; independently check every
    # retained manifest identity before using its output. No build recipe called.
    with ZipFile(ARCHIVE) as z:
        manifest=json.loads(z.read('DEVELOPMENT_BUNDLE_MANIFEST.json'))
        before={r['path']:r for r in manifest['files']}
        assert len(before)==291 and len(z.infolist())==292
        for path,r in before.items():assert identity(z.read(path))=={k:r[k] for k in ('bytes','sha256')}
    entries=[]
    for name in ('cli.py','worker.py','catalog.json','u3_a1.py','cpi_table1.py','mainline_worker.py'):
        path=str(CODE/name);raw=(ROOT/path).read_bytes();target=HERE/'overlay'/path
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        entries.append(dict(path=path,before=before.get(path),after=identity(raw)))
    assert next(r for r in entries if r['path'].endswith('/u3_a1.py'))['after']['sha256']=='29f48c62859ccf45f0b07e590fcceb9d2bd7af86a1b5e1a1d0a47a3b3ea897c5'
    assert next(r for r in entries if r['path'].endswith('/mainline_worker.py'))['after']['sha256']=='e91900adf10a405f7ff4b1672d6af8d570d80bc059b074211fc1aff640bdc32e'
    save('OVERLAY.json',dict(role='DEVELOPMENT_EXACT_FILE_OVERLAY_NOT_PROTOCOL_STATE',
        base_zip_sha256=sha256(ARCHIVE.read_bytes()).hexdigest(),
        apply_scope='NEW_VERIFIED_EXTRACTION_ONLY_NOT_EXISTING_UNKNOWN_WORK',files=entries,
        unchanged_D227_A1_and_D222_runtime_fixes=True,base_manifest_describes_original_zip_only=True))
    results={}
    for label in ('MAINLINE_A','MAINLINE_B'):
        exitcode,report=command(label,ROOT);assert exitcode==1
        results[label]=dict(exit=exitcode,**identity((HERE/(label+'.json')).read_bytes()))
    normal=json.loads((HERE/'MAINLINE_A.json').read_bytes())
    assert (HERE/'MAINLINE_A.json').read_bytes()==(HERE/'MAINLINE_B.json').read_bytes()
    projected=deepcopy(normal)
    next(r for r in projected['modules'] if r['id']=='inflation-data').pop('target_table_support')
    prior=ROOT/'docs/development/u3-exact-a1-table-consumption-2026-10-26-rev-001/MAINLINE_A.json'
    assert (json.dumps(projected,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()==prior.read_bytes()
    catalog=json.loads((ROOT/CODE/'catalog.json').read_bytes())
    with tempfile.TemporaryDirectory(prefix='d228-mixed-') as directory:
        root=Path(directory);seen={}
        for case in catalog.values():
            for r in case['inputs']:
                raw=(ROOT/r['path']).read_bytes();assert identity(raw)=={k:r[k] for k in ('bytes','sha256')}
                if r['alias'] in seen:assert seen[r['alias']]==raw
                else:
                    target=root/r['alias'];target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(raw);seen[r['alias']]=raw
        (root/'cpi-june2026-copy.txt').unlink()
        (root/'cpi-june2026-fraser.pdf').write_bytes(b'changed public archive')
        exitcode,mixed=command('MIXED_BAD_AND_MISSING',ROOT,'--inputs',str(root));assert exitcode==2
        rows={r['id']:r for r in mixed['modules']};cpi=rows['inflation-data']
        assert cpi['status']=='REJECTED' and cpi['result']['status']=='MISSING'
        assert cpi['archive_carrier']['status']=='REJECTED' and cpi['target_table_support']['table']['status']=='REJECTED'
        assert {f['status'] for f in cpi['target_table_support']['comparison']['findings']}=={'REJECTED','MISSING'}
        assert all(rows[k]['status']=='OBSERVED' for k in ('economic-data','unemployment-july','unemployment-november'))
        results['MIXED_BAD_AND_MISSING']=dict(exit=exitcode,**identity((HERE/'MIXED_BAD_AND_MISSING.json').read_bytes()))
    for label in ('RELOCATED_A','RELOCATED_B'):
        with tempfile.TemporaryDirectory(prefix='d228-replay-') as directory:
            root=Path(directory);m.unpack(ARCHIVE,root)
            for entry in entries:
                target=root/entry['path'];expected=entry['before']
                if expected is None:assert not target.exists() and not target.is_symlink()
                else:assert identity(target.read_bytes())=={k:expected[k] for k in ('bytes','sha256')}
                raw=(HERE/'overlay'/entry['path']).read_bytes();assert identity(raw)==entry['after']
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            exitcode,report=command(label,root);assert exitcode==1
            assert m.comparable(report)==m.comparable(normal)
            changes=differences(normal,report);assert len(changes)==63
            assert all('/executed_top_level_code_sha256/' in r['path'] for r in changes)
            save('DIFFERENCES_'+label+'.json',changes)
            results[label]=dict(exit=exitcode,**identity((HERE/(label+'.json')).read_bytes()),allowed_scalar_differences=63)
    results.update(projected_D227_byte_equal=True,catalog_cases=len(catalog),
                   catalog_input_references=sum(len(c['inputs']) for c in catalog.values()),
                   overlay_bytes=sum(r['after']['bytes'] for r in entries))
    save('ACTUAL_RESULTS.json',results)
    print(json.dumps(results,sort_keys=True))


if __name__=='__main__':main()
