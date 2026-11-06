"""Finite artifact joins for D177; never proof of execution or complete runtime."""
import hashlib
from contextlib import contextmanager
import importlib.machinery
import importlib.util
from io import BytesIO
import json
import marshal
from pathlib import Path
import sys
from zipfile import BadZipFile, ZipFile


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


@contextmanager
def checked_product_imports(root, reader, observation):
    """Compile admitted source snapshots; ignore timestamp/hash pyc alternatives.

    The audit covers top-level exec of the selected Python module code only.
    It does not attest every function call, dependency, native or platform input.
    """
    if any(name == 'forecast_trust_core' or name.startswith('forecast_trust_core.') for name in sys.modules):
        raise reader.OfflineFailure('PRELOADED_PRODUCT_CODE_UNVERIFIED')
    root = Path(root).absolute()
    compiled, findings = {}, []
    for row in FINITE_PRODUCT_SOURCES:
        try:
            raw = reader.read_fixed(root, row['path'], row)
        except reader.OfflineFailure as error:
            findings.append({'item': row['path'], 'status': error.status, 'error': error.code})
            continue
        path = str(root/row['path'])
        code = compile(raw, path, 'exec', dont_inherit=True, optimize=sys.flags.optimize)
        compiled[path] = (code, digest(marshal.dumps(code)))
    if findings:
        primary = next((row for row in findings if row['status'] == 'REJECTED'), findings[0])
        raise reader.OfflineFailure(primary['error'], primary['status'], findings)
    observation.update(scope='SELECTED_PRODUCT_TOP_LEVEL_PYTHON_CODE_ONLY',
                       source_snapshot_count=len(compiled), executed_selected_modules=0,
                       executed_top_level_code_sha256={},
                       complete_runtime_closure='NOT_ESTABLISHED')
    state = {'active': False}
    product_directory = root/'src/forecast_trust_core'
    def audit(event, args):
        if not state['active'] or event != 'exec':
            return
        code = args[0]
        path = str(Path(code.co_filename).absolute())
        if path in compiled:
            actual = digest(marshal.dumps(code))
            if actual != compiled[path][1]:
                raise reader.OfflineFailure('SELECTED_PRODUCT_CODE_MISMATCH')
            observation['executed_top_level_code_sha256'][str(Path(path).relative_to(root))] = actual
            observation['executed_selected_modules'] = len(observation['executed_top_level_code_sha256'])
        elif Path(path).is_relative_to(product_directory):
            raise reader.OfflineFailure('UNREGISTERED_PRODUCT_CODE')
    # Select only this admitted namespace, rather than adding root/src to
    # sys.path (which would also expose unrelated, unchecked sibling modules).
    selected_names = {}
    for filename in compiled:
        parts = Path(filename).relative_to(root/'src').with_suffix('').parts
        name = '.'.join(parts[:-1] if parts[-1] == '__init__' else parts)
        selected_names[name] = filename

    class SelectedProductFinder:
        def find_spec(self, fullname, path=None, target=None):
            if fullname == 'forecast_trust_core' or fullname.startswith('forecast_trust_core.'):
                filename = selected_names.get(fullname)
                if filename is None:
                    raise reader.OfflineFailure('UNREGISTERED_PRODUCT_CODE')
                return importlib.util.spec_from_file_location(fullname, filename)
            return None

    finder = SelectedProductFinder()
    original = importlib.machinery.SourceFileLoader.get_code
    def get_code(loader, fullname):
        path = str(Path(loader.get_filename(fullname)).absolute())
        if path in compiled:
            return compiled[path][0]
        if fullname == 'forecast_trust_core' or fullname.startswith('forecast_trust_core.'):
            raise reader.OfflineFailure('UNREGISTERED_PRODUCT_CODE')
        return original(loader, fullname)
    sys.addaudithook(audit)
    importlib.machinery.SourceFileLoader.get_code = get_code
    sys.meta_path.insert(0, finder)
    state['active'] = True
    try:
        yield
    finally:
        state['active'] = False
        if finder in sys.meta_path:
            sys.meta_path.remove(finder)
        importlib.machinery.SourceFileLoader.get_code = original


def bind_retained_sources(documents, root, reader, current_origins, shared):
    """Caller admits the eight control files by their fixed raw identities first.

    Only declared repository files and wheel members are read, never the recorded
    absolute historical installation paths. Current source is compared as source;
    source equality does not authenticate cached or in-memory executed bytecode.
    """
    result = {'status': 'MISSING', 'findings': [], 'checked_repository_sources': 0,
              'checked_wheel_members': 0, 'checked_wheels': 0,
              'checked_current_product_sources': 0,
              'actual_execution_truth': 'NOT_VERIFIED',
              'current_loaded_bytecode_identity': 'NOT_ESTABLISHED',
              'complete_runtime_closure': 'NOT_ESTABLISHED',
              'independent_applicability': 'NOT_ESTABLISHED',
              'scope': 'RETAINED_DECLARED_PYTHON_SOURCES_AND_WHEELS_ONLY_NOT_COMPLETE_RUNTIME'}
    findings = result['findings']
    def fail(code, item='', status='REJECTED'):
        findings.append({'item': item, 'status': status, 'error': code})
    def read(record):
        try:
            return reader.read_fixed(root, record['path'], record)
        except reader.OfflineFailure as error:
            fail(error.code, record['path'], error.status)
            return None
    try:
        inputs, pre, run, loaded, package, lock, runtime = (
            documents[key] for key in ('inputs', 'pre', 'run', 'loaded', 'package', 'lock', 'runtime'))
        if pre['selected_source_sha256'] != digest(documents['_raw']['inputs']):
            fail('PRE_INPUT_IDENTITY_MISMATCH')
        declarations = {row['path']: row for row in inputs['sources']}
        if documents['sources']['files'] != inputs['sources']:
            fail('SOURCE_MANIFEST_PREDECLARATION_MISMATCH')
        rows = loaded['executed_sources']
        if len(rows) != 82 or len({row['path'] for row in rows}) != len(rows):
            fail('LOADED_SOURCE_SET_MISMATCH')
        wheels = {row['sha256']: row for row in lock['wheels']}
        if len(wheels) != 7 or len(lock['wheels']) != 7:
            fail('WHEEL_SET_MISMATCH')
        product = wheels.get(package['raw_sha256'])
        if product is None or product['path'] != package['path']:
            fail('PRODUCT_PACKAGE_LOCK_MISMATCH')
        archives = {}
        for key, record in wheels.items():
            raw = read(record)
            if raw is not None:
                archives[key] = raw
                result['checked_wheels'] += 1
        wheel_index = {row['installed_relative_path']: row for row in pre['wheel_member_sources']}
        member_bytes, products = {}, {}
        for row in rows:
            if row['kind'] == 'PREDECLARED_REPOSITORY_SOURCE':
                declared = declarations.get(row['path'])
                if declared is None or row['sha256'] != declared['sha256']:
                    fail('REPOSITORY_PREDECLARATION_MISMATCH', row['path'])
                    continue
                if read(declared) is not None:
                    result['checked_repository_sources'] += 1
            elif row['kind'] == 'FIXED_INSTALLED_WHEEL_MEMBER':
                # Historical absolute paths are compared as strings only.
                relative = 'lib/python3.12/site-packages/'+row['member']
                declared = wheel_index.get(relative)
                if (declared is None or any(row[key] != declared[key]
                        for key in ('sha256', 'wheel_sha256', 'member'))
                        or row['path'] != inputs['runtime_env']+'/'+relative):
                    fail('WHEEL_PREDECLARATION_MISMATCH', row['member'])
                    continue
                archive = archives.get(row['wheel_sha256'])
                if archive is None:
                    continue  # The missing/replaced wheel finding is retained.
                try:
                    with ZipFile(BytesIO(archive)) as wheel:
                        candidates = [info for info in wheel.infolist() if info.filename == row['member']]
                        if len(candidates) != 1 or candidates[0].file_size > 2_000_000:
                            raise ValueError('not one bounded member')
                        raw = wheel.read(candidates[0])
                    if digest(raw) != row['sha256']:
                        raise ValueError('wrong wheel member')
                except (BadZipFile, KeyError, ValueError, OSError):
                    fail('WHEEL_MEMBER_IDENTITY_MISMATCH', row['member'])
                    continue
                member_bytes[row['member']] = raw
                result['checked_wheel_members'] += 1
                if row['member'].startswith('forecast_trust_core/'):
                    if row['wheel_sha256'] != package['raw_sha256']:
                        fail('PRODUCT_WHEEL_MISMATCH', row['member'])
                    products[row['path']] = row
            else:
                fail('UNSUPPORTED_LOADED_SOURCE_KIND', row['path'])
        if (sum(row['kind'] == 'PREDECLARED_REPOSITORY_SOURCE' for row in rows) != 22
                or sum(row['kind'] == 'FIXED_INSTALLED_WHEEL_MEMBER' for row in rows) != 60
                or len(loaded['product_origins']) != 21
                or (set(loaded['product_origins'].values()) != set(products)
                    and len(archives) == 7)):
            fail('LOADED_SOURCE_SET_MISMATCH')
        # Match current imported product source paths only to the declared repo
        # layout. A different installation is unsupported, not silently trusted.
        if set(current_origins) != set(loaded['product_origins']):
            fail('CURRENT_PRODUCT_SET_MISMATCH')
        for name, historical in loaded['product_origins'].items():
            row = products.get(historical)
            if row is None:
                continue
            relative = 'src/'+row['member']
            if current_origins.get(name) != str(Path(root).absolute()/relative):
                fail('CURRENT_PRODUCT_ORIGIN_UNSUPPORTED', name)
                continue
            raw = member_bytes[row['member']]
            try:
                reader.read_fixed(root, relative, {'bytes': len(raw), 'sha256': digest(raw)})
                result['checked_current_product_sources'] += 1
            except reader.OfflineFailure as error:
                fail('CURRENT_PRODUCT_SOURCE_CHANGED' if error.status == 'REJECTED' else error.code,
                     relative, error.status)
        executable = inputs['runtime_executable']
        if (runtime['execution_engine']['executable_sha256'] != executable['sha256']
                or pre['argv'][0] != executable['path']
                or runtime['runtime_identity']['runtime_version'] != '3.12.3'
                or runtime['dependency_environment']['dependency_lock_ref'] !=
                {key: lock[key] for key in ('object_id', 'content_sha256')}):
            fail('RUNTIME_EXECUTABLE_BINDING_MISMATCH')
        r4t_raw, definition_raw = shared.get('base_records', {}).get('r4t'), shared.get('pre_definition')
        if r4t_raw is None or definition_raw is None:
            fail('SHARED_FINITE_INPUT_MISSING', 'shared-r4t-and-predefinition', 'MISSING')
        else:
            report, pre_definition = json.loads(r4t_raw), json.loads(definition_raw)
            invocation = report['invocations'][0]
            definition = pre_definition['invocations'][0]
            for field, record in [('package_artifact_ref', package), ('dependency_lock_ref', lock),
                                  ('runtime_profile_ref', runtime), ('source_file_manifest_ref', documents['sources'])]:
                reference = {key: record[key] for key in ('object_id', 'content_sha256')}
                if report[field] != reference or pre_definition['bindings'][field] != reference:
                    fail('R4T_MATERIAL_BINDING_MISMATCH', field)
            shared_runtime = shared.get('base_records', {}).get('runtime')
            if shared_runtime is None:
                fail('SHARED_RUNTIME_MISSING', 'shared-runtime', 'MISSING')
            elif shared_runtime != documents['_raw']['runtime']:
                fail('SHARED_RUNTIME_RAW_MISMATCH')
            good = (run['pre_run_raw_sha256'] == digest(documents['_raw']['pre'])
                    and run['pre_definition_raw_sha256'] == digest(definition_raw)
                    and run['invocation_id'] == pre['invocation_id'] == invocation['invocation_id']
                    and invocation['executable_sha256'] == definition['executable_sha256'] == executable['sha256']
                    and invocation['termination'] == run['termination']
                    and invocation['time_observations'] == run['time_observations'])
            for key in ('argv', 'cwd'):
                good = good and run[key] == pre[key] == definition[key] == invocation[key]
            good = good and run['environment'] == pre['environment'] == {
                row['name']: row['value'] for row in invocation['environment']}
            for channel in ('stdout', 'stderr'):
                output = invocation[channel]
                original = shared.get('raw_artifacts', {}).get(output['artifact_id'])
                if original is None:
                    fail('SHARED_OUTPUT_MISSING', channel, 'MISSING')
                else:
                    good = good and run[channel] == {'bytes': len(original), 'sha256': digest(original)}
                    good = good and output['byte_length'] == len(original) and output['raw_sha256'] == digest(original)
            if not good:
                fail('RUN_RECORD_BINDING_MISMATCH')
    except (KeyError, TypeError, ValueError, IndexError):
        fail('PROVENANCE_BINDING_INVALID')
    result['status'] = ('REJECTED' if any(row['status'] == 'REJECTED' for row in findings)
                        else 'MISSING' if findings else 'OBSERVED')
    return result


# Software version pins from the D176 product wheel used by D177.
# This selected development code set establishes no independent actual universe.
FINITE_PRODUCT_SOURCES = [
    {
        "path": "src/forecast_trust_core/__init__.py",
        "bytes": 212,
        "sha256": "b635d26c3205b216864b5b87c2dcd319993de267073b9f8a1c8587dd78bbb007"
    },
    {
        "path": "src/forecast_trust_core/_checks.py",
        "bytes": 493,
        "sha256": "e465ef95f937df6d36406bd18548e5491230d1342465d9111c62ac57ac1458fe"
    },
    {
        "path": "src/forecast_trust_core/canonical.py",
        "bytes": 8126,
        "sha256": "f9ef49579a5c54757c6660d377275a0ed5f8afdf646f33130651a711005ac9ba"
    },
    {
        "path": "src/forecast_trust_core/core.py",
        "bytes": 9547,
        "sha256": "9f26d726802b8baead54f36e2caa9b6f3860e109cb777079e4432e4a29c6d206"
    },
    {
        "path": "src/forecast_trust_core/evidence.py",
        "bytes": 5395,
        "sha256": "ecd1c40a208d32eb1aa550314cca412d5674997370ed296cb25d3f5d678b93ed"
    },
    {
        "path": "src/forecast_trust_core/finite_development/__init__.py",
        "bytes": 426,
        "sha256": "c29b9392f09d07368246ddd8e401972df571ef17a8c05d266fe680424b52018c"
    },
    {
        "path": "src/forecast_trust_core/finite_development/_base.py",
        "bytes": 11786,
        "sha256": "8e92c61b6ee25b74a37943839deb70b1bdf173e9976bac6a8ed4adca55aaf887"
    },
    {
        "path": "src/forecast_trust_core/finite_development/_check_join.py",
        "bytes": 3737,
        "sha256": "e6d6c59b6cd7080286d8f74772ecd6090365d3d146dfefba3b26e756b0aabdb6"
    },
    {
        "path": "src/forecast_trust_core/finite_development/_contract_execution.py",
        "bytes": 5088,
        "sha256": "81bd7c302160a957a9c6c412a1f813cd5895d17e3e92c85b04664d9d7a87f18a"
    },
    {
        "path": "src/forecast_trust_core/finite_development/_operation.py",
        "bytes": 11735,
        "sha256": "611736bc2f43d3890a00cacc72b7874a6a6fc373bd09f41838cbef137e07587a"
    },
    {
        "path": "src/forecast_trust_core/finite_development/_r6t_execution.py",
        "bytes": 3353,
        "sha256": "abf359da2a40c75c8d519d0b7f03187de88f9c3c3e45184511d4d20073392abd"
    },
    {
        "path": "src/forecast_trust_core/finite_development/_report.py",
        "bytes": 7813,
        "sha256": "66475d897f867ab0f0f6acc24a9aba1b63f1ed08434743a703a8f99ccfc45844"
    },
    {
        "path": "src/forecast_trust_core/finite_development/_report_execution.py",
        "bytes": 4522,
        "sha256": "cdea6bd862442e984ee853a84445e18d16deb6e07839fbb1b450824772cfdf12"
    },
    {
        "path": "src/forecast_trust_core/finite_development/_report_set.py",
        "bytes": 10189,
        "sha256": "fe3c50695c1c77fe9b84395a4b22d49040d870582cff8f6c5e1032e6afce4af9"
    },
    {
        "path": "src/forecast_trust_core/finite_development/_schemas.py",
        "bytes": 30708,
        "sha256": "2e469bfb91f1fb4b5c0fa281434e3dae8850e0c310ae30f0152208dceca91433"
    },
    {
        "path": "src/forecast_trust_core/governance.py",
        "bytes": 6279,
        "sha256": "740a040a13f1fe9389c246f11f684b6711b3454faff5deeeeef7d0e74a714ead"
    },
    {
        "path": "src/forecast_trust_core/lifecycle.py",
        "bytes": 4030,
        "sha256": "9a21c0c89f84fa84c1f90727d33af00b73522ee208399262ee3b2e61c9733362"
    },
    {
        "path": "src/forecast_trust_core/policies.py",
        "bytes": 3843,
        "sha256": "e6cbf71f27d85b4e4a117cde43f3c8656947613eb9e83fc61ca11bbf72cb456f"
    },
    {
        "path": "src/forecast_trust_core/r4t_execution_content_v1.py",
        "bytes": 30011,
        "sha256": "6c5194392f43faf0dd1328a134a265fe6f711fa5c4884699f5cfbba41fae7396"
    },
    {
        "path": "src/forecast_trust_core/report_check_content_v1.py",
        "bytes": 10939,
        "sha256": "82342bfd8e6b4450d4a097388718dab6b789a12b0c4f78469e6baaf23f8fb52c"
    },
    {
        "path": "src/forecast_trust_core/unittest_observations_v1.py",
        "bytes": 5166,
        "sha256": "24c6fc42e7e7990039644bfb585cc35f9c5a6dfcb3fe1c6c169025523b3be403"
    }
]
