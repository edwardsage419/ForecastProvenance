"""Isolated passive consumers for fixed public files; no protocol operations."""
from dataclasses import asdict
import hashlib
import importlib.metadata
import importlib.machinery
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType

CASES = json.loads((Path(__file__).resolve().parent/"catalog.json").read_text())


class OfflineFailure(Exception):
    def __init__(self, code, status='REJECTED', findings=None):
        super().__init__(code)
        self.code = code
        self.status = status
        self.findings = findings or []


def audit_policy(event, args):
    if event.startswith('socket.') or event in {
        'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn', 'os.fork',
    }:
        raise OfflineFailure('OFFLINE_POLICY_VIOLATION')


def read_fixed(base, relative, expected):
    """Read only one explicit non-symlink regular file with the exact size/hash."""
    base = Path(base).absolute()
    relative = Path(relative)
    if relative.is_absolute() or not relative.parts or '..' in relative.parts:
        raise OfflineFailure('UNSAFE_PATH')
    try:
        if base.is_symlink() or not base.is_dir():
            raise OfflineFailure('UNSAFE_PATH')
        target = base
        for part in relative.parts:
            target = target / part
            info = target.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise OfflineFailure('UNSAFE_PATH')
            if target != base / relative and not stat.S_ISDIR(info.st_mode):
                raise OfflineFailure('UNSAFE_PATH')
        if not stat.S_ISREG(info.st_mode):
            raise OfflineFailure('UNSAFE_PATH')
        if info.st_size != expected['bytes']:
            raise OfflineFailure('INPUT_IDENTITY_MISMATCH')
        descriptor = os.open(target, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        with os.fdopen(descriptor, 'rb') as stream:
            current = os.fstat(stream.fileno())
            if not stat.S_ISREG(current.st_mode) or current.st_size != expected['bytes']:
                raise OfflineFailure('INPUT_IDENTITY_MISMATCH')
            raw = stream.read(expected['bytes'] + 1)
    except FileNotFoundError as exc:
        raise OfflineFailure('MISSING_INPUT', 'MISSING') from exc
    except OSError as exc:
        raise OfflineFailure('UNREADABLE_INPUT', 'MISSING') from exc
    if len(raw) != expected['bytes'] or hashlib.sha256(raw).hexdigest() != expected['sha256']:
        raise OfflineFailure('INPUT_IDENTITY_MISMATCH')
    return raw


def load_source(path, raw, name):
    module = ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def observe(name, repository_root, input_root=None):
    case = CASES[name]
    root = Path(repository_root)
    checked = {}
    findings = []
    for source in case['sources']:
        try:
            checked[source['path']] = read_fixed(root, source['path'], source)
        except OfflineFailure as exc:
            findings.append({'item': source['path'], 'status': exc.status,
                             'error': 'SOURCE_MISSING' if exc.status == 'MISSING' else 'SOURCE_CHANGED'})
    inputs = []
    for row in case['inputs']:
        try:
            inputs.append(read_fixed(Path(input_root) if input_root is not None else root,
                          row['alias'] if input_root is not None else row['path'], row))
        except OfflineFailure as exc:
            inputs.append(None)
            findings.append({'item': row['alias'], 'status': exc.status, 'error': exc.code})
    if findings:
        primary = next((f for f in findings if f['status'] == 'REJECTED'), findings[0])
        raise OfflineFailure(primary['error'], primary['status'], findings)
    kind = case['kind']
    suffix = '/cpi_table1.py' if kind == 'cpi_table1' else '/u3_a1.py' if kind == 'u3_a1' else '/q1_scope.py' if kind == 'q1_scope' else '/predecessor_calendar.py' if kind == 'calendar_predecessors' else '/cpi_pdf.py' if kind == 'cpi_archive_pdf' else '/cpi_text.py' if kind == 'cpi_text' else '/gdp_pdf.py' if kind == 'gdp_news' else (
        '/consumer.py' if kind in {'u3', 'bindings'} else '/binding.py')
    source = next(row for row in case['sources'] if row['path'].endswith(suffix))
    # Sealed GDP code imports its archive helper through SourceFileLoader. -B only
    # suppresses cache writes. Compile registered checked bytes on nested imports,
    # so an unregistered timestamp-valid .pyc cannot replace the reviewed source.
    checked_paths = {str((root/path).resolve()): raw for path, raw in checked.items()}
    original_get_code = importlib.machinery.SourceFileLoader.get_code
    def checked_get_code(loader, fullname):
        path = str(Path(loader.get_filename(fullname)).resolve())
        if path in checked_paths:
            return compile(checked_paths[path], path, 'exec')
        return original_get_code(loader, fullname)
    importlib.machinery.SourceFileLoader.get_code = checked_get_code
    try:
        module = load_source(root/source['path'], checked[source['path']], '_fp_offline_'+kind)
    finally:
        importlib.machinery.SourceFileLoader.get_code = original_get_code
    if kind == 'u3':
        return asdict(module.observe_u3_pdf(inputs[0], reference_month=case['month']))
    if kind == 'u3_a1':
        legacy=next(row for row in case['sources'] if row['path'].endswith('/consumer.py'))
        old=load_source(root/legacy['path'],checked[legacy['path']],'_fp_u3_a1_summary')
        return module.observe_a1_pdf(inputs[0],reference_month=case['month'],
            summary_observer=lambda raw,**kw:asdict(old.observe_u3_pdf(raw,**kw)))
    if kind == 'cpi_text':
        return module.observe_cpi_copy(inputs[0])
    if kind == 'calendar_predecessors':
        if importlib.metadata.version('pypdf') != '6.10.0':
            raise OfflineFailure('UNSUPPORTED_RUNTIME', 'UNAVAILABLE')
        return module.observe_predecessor_calendars(dict(zip(
            ('nyfed_oct2026', 'nyfed_dec2026', 'omb_2026'), inputs)))
    if kind == 'q1_scope':
        if importlib.metadata.version('pypdf') != '6.10.0':
            raise OfflineFailure('UNSUPPORTED_RUNTIME', 'UNAVAILABLE')
        def source_module(suffix):
            row=next(row for row in case['sources'] if row['path'].endswith(suffix))
            return load_source(root/row['path'],checked[row['path']],'_fp_q1_'+suffix.split('/')[-1])
        predecessor=source_module('/predecessor_calendar.py')
        calendar=source_module('/calendar-declaration-binding/binding.py')
        return module.observe_q1_assessment(dict(zip(('omb','bea','inventory','selection'),inputs)),
            parse_omb_pages=predecessor.parse_omb_pages,annual_parser=calendar.annual)
    if kind == 'cpi_table1':
        if importlib.metadata.version('pypdf') != '6.10.0':
            raise OfflineFailure('UNSUPPORTED_RUNTIME', 'UNAVAILABLE')
        legacy=next(row for row in case['sources'] if row['path'].endswith('/cpi_pdf.py'))
        old=load_source(root/legacy['path'],checked[legacy['path']],'_fp_cpi_table1_headline')
        return module.observe_table1_pdf(inputs[0],archive_observer=old.observe_archive_pdf)
    if kind == 'cpi_archive_pdf':
        if importlib.metadata.version('pypdf') != '6.10.0':
            raise OfflineFailure('UNSUPPORTED_RUNTIME', 'UNAVAILABLE')
        return module.observe_archive_pdf(inputs[0])
    if kind == 'gdp_news':
        if importlib.metadata.version('pypdf') != '6.10.0':
            raise OfflineFailure('UNSUPPORTED_RUNTIME', 'UNAVAILABLE')
        return module.observe_news_pdfs(dict(zip(('q1_third', 'q2_third', 'q2_second'), inputs)))
    if kind == 'calendar':
        return module.consume(*inputs, sha256=[row['sha256'] for row in case['inputs']])
    if kind == 'bindings':
        if importlib.metadata.version('jsonschema') != '4.26.0':
            raise OfflineFailure('UNSUPPORTED_RUNTIME', 'UNAVAILABLE')
        expected = module.parse_json_strict(inputs[0])
        records = dict(zip(module.SLOTS, inputs[1:]))
        result = module.consume(expected, records)
        if result['verdict'] == 'REJECT' or result['binding_verdict'] != 'LOCAL_CANDIDATE_BINDINGS_VERIFIED':
            raise OfflineFailure('BINDING_NOT_VERIFIED')
        return {'sample_class': 'KEYLESS_SYNTHETIC_DEVELOPMENT_ONLY', 'result': result}
    versions = []
    for quarter, stage, when in (
        ('2026-Q1', 'Advance', '2026-04-30'), ('2026-Q1', 'Second', '2026-05-28'),
        ('2026-Q1', 'Third', '2026-06-25'), ('2026-Q1', 'Revised', '2026-09-30'),
        ('2026-Q2', 'Advance', '2026-07-30'), ('2026-Q2', 'Second', '2026-08-26'),
        ('2026-Q2', 'Third', '2026-09-30'),
    ):
        versions.append(asdict(module.observe_vintage(inputs[0], expected_sha256=case['inputs'][0]['sha256'],
                          reference_quarter=quarter, stage=stage, publication_date=when)))
    bindings = []
    for index, quarter, when in ((1, '2026-Q1', '2026-04-30'), (2, '2026-Q2', '2026-07-30')):
        bindings.append(asdict(module.bind_advance(inputs[0], inputs[index],
            vintage_sha256=case['inputs'][0]['sha256'], archive_sha256=case['inputs'][index]['sha256'],
            reference_quarter=quarter, publication_date=when)))
    return {'versions': versions, 'advance_bindings': bindings}


def main():
    request = json.loads(sys.stdin.read(16385))
    name = request['case']
    if name not in CASES:
        raise SystemExit(2)
    case = CASES[name]
    result = {'id': name, 'title': case['title'], 'scope': case['scope']}
    sys.addaudithook(audit_policy)
    try:
        data = observe(name, request['repository_root'], request.get('input_root'))
        result.update(status='OBSERVED', observations=data)
    except OfflineFailure as exc:
        result.update(status=exc.status, error=exc.code)
        if exc.findings:
            result['findings'] = exc.findings
    except (ModuleNotFoundError, importlib.metadata.PackageNotFoundError) as exc:
        result.update(status='UNAVAILABLE', error='MISSING_DEPENDENCY')
    except Exception:
        # Never print source data, arbitrary exception strings or traceback to the report.
        result.update(status='REJECTED', error='CONSUMER_REJECTED')
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == '__main__':
    main()
