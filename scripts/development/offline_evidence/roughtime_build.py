"""Consume one retained public build, never execute it or infer qualification."""
from pathlib import Path
import hashlib
import sys
from types import ModuleType

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BUILD_DIRECTORY = ROOT/'docs/development/owner-roughtime-build-results.K0fixS'
ARTIFACTS = {
    'verifier-build-profile.json': (1573, 'd3941c0f4ce698b50cb1ff308a5eabe783394367260d9217aba52cdfdf3651da'),
    'dependency-lock.json': (3008, '0ebfa7d4ceda120547530b9ac73cac6fe780266af4f798267aa9bba9c112490b'),
    'fixture-report.json': (2305, '1f005f50a94677f3faa45e7b7a20905f00a78e18c93186f2c26a81c08ae16c08'),
    'fpp-roughtime-strict': (4462818, '55af6512c6c9b53786c0605b2d444ba970ba32f70746797001000cb36e572fa5'),
}
SOURCES = {
    'canonical': (8126, 'f9ef49579a5c54757c6660d377275a0ed5f8afdf646f33130651a711005ac9ba'),
    '_roughtime_profile': (3598, '7bdd60de603875c1fc71f8b295dd286dc6d4a1366ab13d147284fd191762a727'),
    '_roughtime_control': (15966, '2470285ddc04c618d64c398523819c8a45ad3e3c6f733d23e8ba40b11f123e47'),
    '_roughtime_qualification_vendored': (21591, '21f79b21dce2552d4a7acd8718c3f0515b05ab7ecc96a539f69c00a6d1625e84'),
}


def consume(directory=BUILD_DIRECTORY, *, source_root=ROOT, reader=None):
    if reader is None:
        reader = ModuleType('fp_roughtime_passive_reader')
        reader.__file__ = str(HERE/'worker.py')
        exec(compile((HERE/'worker.py').read_bytes(), reader.__file__, 'exec'), reader.__dict__)
    result = {'status': 'MISSING', 'scope': 'D238_EXACT_RETAINED_BUILD_ARTIFACTS_ONLY',
              'findings': [], 'artifact_binding_match': False, 'binary_executed': False,
              'live_compatibility': 'NOT_ESTABLISHED', 'provider_qualification': 'NOT_ESTABLISHED',
              'authenticated_time': 'NOT_ESTABLISHED', 'independent_software_trust': 'NOT_ESTABLISHED',
              'prospective_eligible': False, 'real_admission': 'NOT_READY', 'protocol_state_change': 'NONE'}
    def read(base, path, record):
        size, digest = record
        try:
            # A directory never supplied is missing evidence. lstat preserves
            # dangling links as present so read_fixed still rejects aliases.
            try:
                Path(base).lstat()
            except FileNotFoundError:
                raise reader.OfflineFailure('MISSING_INPUT', 'MISSING')
            except OSError:
                raise reader.OfflineFailure('UNREADABLE_INPUT', 'MISSING')
            return reader.read_fixed(base, path, {'bytes': size, 'sha256': digest})
        except reader.OfflineFailure as error:
            result['findings'].append({'item': path, 'status': error.status, 'error': error.code})
            return None
    # All expected artifacts and code are admitted before executing any validator.
    artifacts = {name: read(directory, name, record) for name, record in ARTIFACTS.items()}
    sources = {name: read(source_root, 'src/forecast_trust_core/'+name+'.py', record)
               for name, record in SOURCES.items()}
    if not result['findings']:
        prefix = '_fp_retained_roughtime_build'
        package = ModuleType(prefix)
        package.__path__ = []  # no repository package initializer or filesystem fallback
        sys.modules[prefix] = package
        loaded = {}
        try:
            for name, raw in sources.items():
                module = ModuleType(prefix+'.'+name)
                module.__file__ = str(Path(source_root)/'src/forecast_trust_core'/(name+'.py'))
                module.__package__ = prefix
                sys.modules[module.__name__] = module
                exec(compile(raw, module.__file__, 'exec'), module.__dict__)
                loaded[name] = module
            canonical = loaded['canonical']
            control = loaded['_roughtime_control']
            validators = loaded['_roughtime_qualification_vendored']
            profile, lock, fixtures = [canonical.parse_json_strict(artifacts[name]) for name in
                ('verifier-build-profile.json', 'dependency-lock.json', 'fixture-report.json')]
            profile_hash = control.validate_verifier_build_profile(profile)
            lock_hash = validators.validate_dependency_lock(lock)
            fixture_hash = validators.validate_fixture_report(fixtures)
            checks = [profile['dependency_lock_sha256'] == lock_hash,
                      profile['fixture_report_sha256'] == fixture_hash,
                      profile['binary_sha256'] == hashlib.sha256(artifacts['fpp-roughtime-strict']).hexdigest(),
                      profile['upstream_source_tree_sha256'] == lock['upstream_source_tree_sha256']]
            checks.extend(profile[key] == fixtures[key] for key in (
                'go_version', 'goos', 'goarch', 'go_toolchain_tree_sha256',
                'wrapper_source_tree_sha256', 'upstream_source_tree_sha256'))
            if not all(checks):
                raise ValueError('build artifact cross binding mismatch')
            result.update(artifact_binding_match=True, profile_sha256=profile_hash,
                          binary_sha256=profile['binary_sha256'],
                          fixture_pass_rows=len(fixtures['tests']),
                          required_fixture_names=len(validators.REQUIRED_FIXTURE_TESTS),
                          declared_build_platform=profile['goos']+'/'+profile['goarch'],
                          runtime_platform_applicability='NOT_CHECKED_NO_EXECUTION',
                          tag_signature='RETAINED_BUILD_DECLARATION_NOT_FRESHLY_VERIFIED')
        except (ValueError, TypeError, KeyError, ImportError, OSError) as error:
            result['findings'].append({'item': 'build-content', 'status': 'REJECTED',
                                       'error': 'BUILD_CONTENT_OR_BINDING_REJECTED'})
        finally:
            for name in SOURCES:
                sys.modules.pop(prefix+'.'+name, None)
            sys.modules.pop(prefix, None)
    result['status'] = ('REJECTED' if any(f['status']=='REJECTED' for f in result['findings'])
                        else 'MISSING' if result['findings'] else 'OBSERVED')
    return result
