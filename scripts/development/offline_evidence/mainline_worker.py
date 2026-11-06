"""Offline development module composition, with no real-authority input route.

The only run package accepted here is the retained D178 public development set.
Native authority/history/universe components receive *missing* inputs, and their
diagnostics cannot establish applicability or authenticate the finite package.
"""
from dataclasses import asdict
from importlib.metadata import PackageNotFoundError
import hashlib
import json
from pathlib import Path
import sys
from types import ModuleType

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
RUN_DIRECTORY = ROOT/'docs/development/mainline-execution-2026-10-18-observed-five-report-replay-rev-001'
RUN_MANIFEST = {'bytes': 6170,
                'sha256': '6d2e0038cc808127f6a7074cf588a749b804a60762ce9dcaa6955a6e04f0e441'}
TRACE_DIRECTORY = ROOT/'docs/development/mainline-execution-2026-10-18-observed-development-run-rev-001'
PROOF_DIRECTORY = ROOT/'docs/development/mainline-execution-2026-10-09-rev-001/gdp-public-proof-pair-2026-10-15-rev-001'
TRACE_FILES = {
    'expected': ('EVENT_EXPECTED_CORRECTED.json', 3133, '4be7110e625c2d4d93d3bd3122ef0117d195ce5b51626d63cf928cca7a32746c'),
    'run': ('EVENT_RUN_OBSERVATION.json', 195, '88ffbcc569c973e4facf251ca9ae0a0a77785e0b37045b5383fe74fe6cb5d48d'),
    'mapping': ('pre-attempt2/method-map.json', 8236, 'a74c040880072c08cb51f779b99e6b2a439ff43db5f449151be403ceedbaf56e'),
    'events': ('raw-attempt2/events.jsonl', 15165, '42b86058168873f23df1c68a047b9a4c689344a966d4ceb6d774d42eb278282b'),
}
HEADER_DIRECTORY = ROOT/'docs/development/mainline-execution-2026-10-19-public-bitcoin-header-rev-001'
HEADER_FILES = {
    'blockstream_hash': ('raw/blockstream-height-912095.txt', 64, 'a652367b8887cb555b2f97fb0c3181970c074691074753dfc21fb63d5c05d3a3'),
    'blockstream_header': ('raw/blockstream-header.hex', 160, 'e32a7c960950bc80adefad2bd7fdfadc133441e1fd7f98346da7f5cee8d76185'),
    'mempool_hash': ('raw/mempool-height-912095.txt', 64, 'a652367b8887cb555b2f97fb0c3181970c074691074753dfc21fb63d5c05d3a3'),
    'mempool_header': ('raw/mempool-header.hex', 160, 'e32a7c960950bc80adefad2bd7fdfadc133441e1fd7f98346da7f5cee8d76185'),
}
CHAIN_DIRECTORY = ROOT/'docs/development/mainline-execution-2026-10-19-public-chain-observation-rev-001'
CHAIN_FILES = {
    'requests': ('REQUESTS.json', 4014, '0ceafb2506c66c06f68ab8722ecbf31b2f7822dcc95636bb3bbec1b1bade78f1'),
    'blockstream_block': ('raw/blockstream-block.json', 439, '7d0609a5692513104f14910b92610ba83c7fa868872180b5f5fa25e3fa29e591'),
    'blockstream_status': ('raw/blockstream-status.json', 117, 'd48577094792a1e7874e8a484e2c879593867f82b6275258d2113e70a3761894'),
    'blockstream_tip-height': ('raw/blockstream-tip-height.txt', 6, 'dcaf9a83016366549a3d613c9604fc5f1fa8651ee43afa1bf033f0697a6bd302'),
    'blockstream_tip-hash': ('raw/blockstream-tip-hash.txt', 64, 'f9eceae65f082fcec05906c153ddf700babf82b4ebec677c97552c8562996d7a'),
}
CORE_DIRECTORY = ROOT/'docs/development/mainline-execution-2026-10-19-pruned-core-sample-execution-rev-001'
CORE_FILES = {
    'result': ('online-107-RESULT.json', 11663, 'ba18857cf56230b93f280a18089b74ef89ae4967f7540b7da1eafd9353116294'),
    'events': ('online-107-PUBLIC_EVENTS.jsonl', 98515, '16274a124a0758db82f012901ed9dcdbda361c34b2212f284962710a6e599542'),
    'verification': ('SEGMENT_107_512_VERIFICATION.json', 14194, 'f0c9256907919281a6566ec9a8ad95ab8bb3ecd352389d63eaef7b1794dea50e'),
    'controller': ('supervise_core.metadata-rescan.py', 22458, '0b37b628c290bf34ac263ffe38a3d321c93e8217a3714b453561563809a8619f'),
    'config': ('bitcoin.conf.cache512-continuation.txt', 486, '01439530bd38ba5a74794a2a86ca63f3f0a22d60cf48a04092e33aa32fa1dd4b'),
}
PROOF_FILES = {
    'pdf': ('raw/gdp2q25-2nd.pdf', 1370386, 'c70972a12908b73c2407d9cc6842ba2a02203a690f3090cd29f30c45f0cfd93d'),
    'proof': ('raw/gdp2q25-2nd.pdf.ots', 650, '0a63adf8a7b47b68d42aec05f365f78a631e64f734b8af5bc594188ee2d751e9'),
}
PROVENANCE_FILES = {
    'inputs': ('INPUTS_ATTEMPT2.json', 29573, 'e7d9f13a17a396d2c8d037d945f202aea873f375f30d145e41ef8972858e1dce'),
    'pre': ('PRE_RUN_ATTEMPT2.json', 68914, 'c35cdd5912f32d4385ead97749f0696d37d932814be11765c07815d5ca8bd5c2'),
    'run': ('RUN_OBSERVATION_ATTEMPT2.json', 1107, '35cbbb8ac425b64427110391db64e693f8adf203bdedcce1c19ba5c20ea74659'),
    'loaded': ('raw-attempt2/loaded-code.json', 42827, 'ad1591f949266ac358c65cb04dad6d63f4d0256fd88a2a430053e5296e440401'),
    'package': ('pre-attempt2/material-package.json', 511, '0a3504e639703d74b45a0d4b9da8d3233a21d3e512cc97de333f829037f129c4'),
    'lock': ('pre-attempt2/material-lock.json', 2082, '5f34be9092cbb6280a5f118f1f61abd59cd7994fda0e929a176871215d083570'),
    'runtime': ('pre-attempt2/runtime.json', 952, '036685ca79769f4ee4407fda23d73ee99a8570ec363cf998fb0452dc7d8ad31b'),
    'sources': ('pre-attempt2/material-sources.json', 20133, 'e4ff0517f9d7bac3a5f05f5ac05f236b193498f48b79c3f0b39095cef06b4f03'),
}

# Reuse the existing passive reader; execute source directly, not sibling pyc.
reader = ModuleType('fp_mainline_passive_reader')
reader.__file__ = str(HERE/'worker.py')
sys.modules[reader.__name__] = reader
exec(compile((HERE/'worker.py').read_bytes(), reader.__file__, 'exec'), reader.__dict__)


def finite_module(directory, snapshot=None):
    from forecast_trust_core.finite_development import consume_finite_report_set
    module = {'id': 'finite-reports', 'title': '运行合同与五报告组合',
              'scope': 'D178 exact finite development inputs; one local test report, four synthetic siblings'}
    findings, cache = [], {}
    def read(record):
        key = (record['path'], record['bytes'], record['sha256'])
        if key not in cache:
            try:
                cache[key] = reader.read_fixed(directory, record['path'], record)
            except reader.OfflineFailure as error:
                findings.append({'item': record['path'], 'status': error.status, 'error': error.code})
                cache[key] = None
        return cache[key]
    raw = read(dict(RUN_MANIFEST, path='INPUT_SET.json'))
    if raw is not None:
        # The exact manifest identity is checked before any of its paths are read.
        def load(value):
            if isinstance(value, dict):
                if set(value) == {'path', 'bytes', 'sha256'}:
                    return read(value)
                return {key: load(item) for key, item in value.items()}
            if isinstance(value, list):
                return [load(item) for item in value]
            return value
        inputs = load(json.loads(raw)['inputs'])
        if snapshot is not None:
            snapshot.update(inputs)
    if findings:
        status = 'REJECTED' if any(row['status'] == 'REJECTED' for row in findings) else 'MISSING'
        return dict(module, status=status, findings=findings)
    controls = {'expected_set', 'expected_base', 'mapping_sha256', 'pre_definition', 'result_binding'}
    arguments = [json.loads(inputs[name]) if name in controls else inputs[name]
                 for name in json.loads(raw)['parameter_order']]
    result = consume_finite_report_set(*arguments)
    status = ('REJECTED' if result['verdict'] == 'REJECT' else
              'OBSERVED' if result['finite_report_set_match'] else 'MISSING')
    return dict(module, status=status, result=result)


def read_group(directory, records):
    values, findings = {}, []
    for key, (path, size, digest) in records.items():
        try:
            values[key] = reader.read_fixed(directory, path, {'bytes': size, 'sha256': digest})
        except reader.OfflineFailure as error:
            values[key] = None
            findings.append({'item': path, 'status': error.status, 'error': error.code})
    return values, findings


def bind_event_results(expected, mapping, observation, events_raw, r4t_raw, definition):
    """Finite cross-join only; full event/report validation stays in existing consumers."""
    result = {'finite_mapping_match': False, 'errors': [],
              'r4t_raw_sha256': hashlib.sha256(r4t_raw).hexdigest(),
              'mapped_methods': 0, 'event_rows': 0}
    try:
        report = json.loads(r4t_raw)
        events = [json.loads(line) for line in events_raw.splitlines()]
        result['event_rows'] = len(events)
        identity = lambda value: json.dumps(value, sort_keys=True)
        wanted = [identity(value) for value in expected['identities']]
        mapped = [identity(row['identity']) for row in mapping]
        actual = [row for row in events if row['event'] in {'METHOD_RESULT', 'SUBTEST_RESULT'}]
        observed = [identity(row['identity']) for row in actual]
        if (len(set(wanted)) != len(wanted) or sorted(wanted) != sorted(mapped)
                or sorted(wanted) != sorted(observed)):
            result['errors'].append('METHOD_IDENTITY_SET_MISMATCH')
        if (len(definition['invocations']) != 1 or len(report['invocations']) != 1):
            raise ValueError('finite single invocation required')
        declared, recorded = definition['invocations'][0], report['invocations'][0]
        for key in ('invocation_id', 'attempt_index'):
            if not (declared[key] == recorded[key] == expected[key] == observation[key]):
                result['errors'].append('INVOCATION_ATTEMPT_MISMATCH')
        if (recorded['termination'] != observation['termination']
                or declared['expected_exit_codes'] != expected['expected_exit_codes']):
            result['errors'].append('TERMINATION_BINDING_MISMATCH')
        encode = lambda rows: sorted(json.dumps(row, sort_keys=True) for row in rows)
        if encode(declared['instances']) != encode([row['instance'] for row in mapping]):
            result['errors'].append('PREDEFINITION_METHOD_MAP_MISMATCH')
        outcomes = {identity(row['identity']): row['outcome'] for row in actual}
        fields = ('instance_id', 'check_id', 'operation_id', 'fixture_refs')
        projected = []
        for row in mapping:
            if row['invocation_id'] != expected['invocation_id']:
                result['errors'].append('MAPPING_INVOCATION_MISMATCH')
            projected.append({key: row['instance'][key] for key in fields} |
                             {'invocation_id': row['invocation_id'],
                              'outcome': outcomes[identity(row['identity'])]})
        supplied = [{key: row[key] for key in (*fields, 'invocation_id', 'outcome')}
                    for row in report['results']]
        if encode(projected) != encode(supplied):
            result['errors'].append('EVENT_R4T_RESULT_MISMATCH')
        result['mapped_methods'] = len(mapping)
    except (ValueError, TypeError, KeyError, IndexError):
        result['errors'].append('EVENT_R4T_BINDING_INVALID')
    result['finite_mapping_match'] = not result['errors']
    return result


def execution_module(directory, snapshot):
    from forecast_trust_core.r4t_execution_content_v1 import consume_local_unittest_content
    values, findings = read_group(directory, TRACE_FILES)
    module = {'id': 'execution-trace', 'title': '留存测试事件与R4T对应',
              'scope': 'D177 retained finite local events joined to the same captured D178 R4T bytes'}
    result = consume_local_unittest_content(
        json.loads(values['expected']) if values['expected'] is not None else None,
        values['events'], json.loads(values['run']) if values['run'] is not None else None)
    raw = snapshot.get('base_records', {}).get('r4t')
    pre = snapshot.get('pre_definition')
    if raw is None or pre is None:
        findings.append({'item': 'shared-r4t-and-predefinition', 'status': 'MISSING',
                         'error': 'SHARED_FINITE_INPUT_MISSING'})
    binding = None
    if not findings:
        binding = bind_event_results(json.loads(values['expected']), json.loads(values['mapping']),
                                     json.loads(values['run']), values['events'], raw, json.loads(pre))
    provenance = source_package_binding(directory, snapshot)
    rejected = (result['verdict'] == 'REJECT' or
                any(row['status'] == 'REJECTED' for row in findings) or
                (binding is not None and not binding['finite_mapping_match']) or
                provenance['status'] == 'REJECTED')
    status = ('REJECTED' if rejected else 'OBSERVED' if not findings
              and result['local_event_consistency_match'] and binding['finite_mapping_match']
              and provenance['status'] == 'OBSERVED' else 'MISSING')
    return dict(module, status=status, result=result, findings=findings, r4t_binding=binding,
                source_package_binding=provenance)


def source_package_binding(directory, snapshot):
    values, findings = read_group(directory, PROVENANCE_FILES)
    if findings:
        return {'status': 'REJECTED' if any(row['status'] == 'REJECTED' for row in findings) else 'MISSING',
                'findings': findings, 'complete_runtime_closure': 'NOT_ESTABLISHED',
                'current_loaded_bytecode_identity': 'NOT_ESTABLISHED', 'actual_execution_truth': 'NOT_VERIFIED'}
    # Interpret paths only after all eight fixed control identities were checked.
    documents = {key: json.loads(raw) for key, raw in values.items()}
    documents['_raw'] = values
    current = {name: getattr(sys.modules.get(name), '__file__', None)
               for name in documents['loaded']['product_origins']}
    consumer = provenance_consumer()
    return consumer.bind_retained_sources(documents, ROOT, reader, current, snapshot)


def provenance_consumer():
    path = HERE/'replay_provenance.py'
    consumer = ModuleType('fp_retained_provenance')
    consumer.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), consumer.__dict__)
    return consumer


def time_module(directory, header_directory=HEADER_DIRECTORY, chain_directory=CHAIN_DIRECTORY,
                core_directory=CORE_DIRECTORY, roughtime_build_directory=None, roughtime_event_directory=None,
                strong_candidate_directory=None):
    values, findings = read_group(directory, PROOF_FILES)
    header_values, header_findings = read_group(header_directory, HEADER_FILES)
    consumer = ModuleType('fp_passive_ots_body')
    consumer.__file__ = str(HERE/'ots_body.py')
    exec(compile((HERE/'ots_body.py').read_bytes(), consumer.__file__, 'exec'), consumer.__dict__)
    example = {'scope': 'PUBLIC_2025_GDP_MIRROR_BYTES_AND_OTS_HEADER_ONLY_NOT_PROJECT_TIME',
               'findings': findings, 'full_ots_verification': 'NOT_CHECKED',
               'bitcoin_verification': 'NOT_CHECKED', 'project_subject_binding': 'NOT_ESTABLISHED'}
    if findings:
        example['status'] = 'REJECTED' if any(row['status'] == 'REJECTED' for row in findings) else 'MISSING'
    else:
        proof = values['proof']
        # Static upstream format: 31-byte magic, version byte, SHA256 tag, digest.
        magic = bytes.fromhex('004f70656e54696d657374616d7073000050726f6f6600bf89e2e884e89294')
        match = (proof[:31] == magic and proof[31:33] == b'\x01\x08'
                 and proof[33:65] == hashlib.sha256(values['pdf']).digest())
        example.update(status='OBSERVED' if match else 'REJECTED', subject_digest_match=match,
                       pdf_raw_sha256=hashlib.sha256(values['pdf']).hexdigest(),
                       proof_raw_sha256=hashlib.sha256(proof).hexdigest(),
                       unverified_body_bytes=len(proof)-65)
        if match:
            try:
                records = [] if header_findings else [
                    {'source_id': source, 'claimed_height': 912095,
                     'block_hash_response': header_values[source+'_hash'],
                     'header_response': header_values[source+'_header']}
                    for source in ('blockstream', 'mempool')]
                example.update(consumer.consume_ots_header_links(values['pdf'], proof, records))
                if header_findings:
                    example['header_binding']['findings'] = header_findings
                    example['header_binding']['status'] = ('REJECTED' if any(
                        row['status'] == 'REJECTED' for row in header_findings) else 'MISSING')
                    example['standalone_pow'].update(
                        status=example['header_binding']['status'], findings=header_findings,
                        scope='RAW_HEADER_INPUTS_NOT_ADMITTED_POW_NOT_CHECKED')
                chain_values, chain_findings = read_group(chain_directory, CHAIN_FILES)
                if chain_findings or header_findings:
                    all_findings = chain_findings+header_findings
                    example['public_chain_observation'] = {
                        'status': 'REJECTED' if any(row['status'] == 'REJECTED' for row in all_findings) else 'MISSING',
                        'scope': 'RAW_CHAIN_OR_HEADER_INPUTS_NOT_ADMITTED',
                        'sources': [], 'findings': all_findings,
                        'chain_verification': 'NOT_CHECKED', 'authenticated_time': 'NOT_ESTABLISHED',
                        'source_independence': 'NOT_ESTABLISHED', 'tip_queries_atomic': False}
                else:
                    example['public_chain_observation'] = consumer.consume_public_chain_observations(
                        header_values['blockstream_header'], 912095, json.loads(chain_values['requests']),
                        {key: value for key, value in chain_values.items() if key != 'requests'})
                if (example['header_binding']['status'] == 'REJECTED'
                        or example['standalone_pow']['status'] == 'REJECTED'
                        or example['public_chain_observation']['status'] == 'REJECTED'):
                    example['status'] = 'REJECTED'
                example['scope'] = 'PUBLIC_GDP_OTS_PATH_AND_HEADER_BYTES_NOT_CHAIN_OR_PROJECT_TIME'
            except ValueError as error:
                example['status'] = 'REJECTED'
                example['findings'].append({'item': 'OTS_BODY', 'status': 'REJECTED', 'error': str(error)})
    core_values, core_findings = read_group(core_directory, CORE_FILES)
    core_values.update(pdf=values['pdf'], proof=values['proof'], header=header_values['blockstream_header'])
    core = ModuleType('fp_retained_core_sample')
    core.__file__ = str(HERE/'core_sample.py')
    exec(compile((HERE/'core_sample.py').read_bytes(), core.__file__, 'exec'), core.__dict__)
    retained = core.consume_core_sample(core_values, consumer)
    retained['findings'].extend(core_findings)
    if any(x['status'] == 'REJECTED' for x in retained['findings']):
        retained['status'] = 'REJECTED'
    example['retained_core_sample'] = retained
    if retained['status'] == 'REJECTED':
        example['status'] = 'REJECTED'
    elif retained['status'] == 'MISSING' and example['status'] != 'REJECTED':
        example['status'] = 'MISSING'
    build_consumer = ModuleType('fp_retained_roughtime_build_consumer')
    build_consumer.__file__ = str(HERE/'roughtime_build.py')
    exec(compile((HERE/'roughtime_build.py').read_bytes(), build_consumer.__file__, 'exec'), build_consumer.__dict__)
    build = build_consumer.consume(roughtime_build_directory if roughtime_build_directory is not None
                                   else build_consumer.BUILD_DIRECTORY, reader=reader)
    event_consumer=ModuleType('fp_retained_roughtime_event_consumer')
    event_consumer.__file__=str(HERE/'roughtime_event.py')
    exec(compile((HERE/'roughtime_event.py').read_bytes(),event_consumer.__file__,'exec'),event_consumer.__dict__)
    event=event_consumer.consume(roughtime_event_directory if roughtime_event_directory is not None
                                 else ROOT,reader=reader)
    strong_consumer=ModuleType('fp_retained_strong_event_consumer')
    strong_consumer.__file__=str(HERE/'strong_event.py')
    exec(compile((HERE/'strong_event.py').read_bytes(),strong_consumer.__file__,'exec'),strong_consumer.__dict__)
    strong=strong_consumer.consume(strong_candidate_directory if strong_candidate_directory is not None
                                   else ROOT,reader=reader)
    same_consumer=ModuleType('fp_retained_same_run_consumer')
    same_consumer.__file__=str(HERE/'strong_same_run.py')
    exec(compile((HERE/'strong_same_run.py').read_bytes(),same_consumer.__file__,'exec'),same_consumer.__dict__)
    same=same_consumer.consume(strong_candidate_directory if strong_candidate_directory is not None else ROOT,reader=reader)
    return {'id': 'time-and-durability', 'title': '真实时间与Bitcoin耐久证据',
            'status': 'REJECTED' if any(s=='REJECTED' for s in (example['status'],build['status'],event['status'],strong['status'],same['status'])) else 'MISSING',
            'scope': 'REAL_CHECK_NOT_EXECUTED', 'error': 'REAL_PROVIDER_OTS_CORE_EVIDENCE_NOT_SUPPLIED',
            'public_example': example, 'roughtime_verifier_build': build,'roughtime_nonforecast_event':event,
            'strong_candidate_public_event':strong,
            'same_run_public_core_replay':same,
            'findings': [*build['findings'],*event['findings'],*strong['findings'],*same['findings']]}


def signing_candidates(profile_directory=None, verifier_directory=None, *, gate_directory=None, gate_output=None,
                       gate_snapshot_output=None, input_snapshot_output=None):
    """One profile snapshot, two technical diagnostics; no actual rule input."""
    profile_findings, findings, admitted, fixed_snapshots = [], [], {}, {}
    read_snapshots = {}

    def read_key(base, relative, expected):
        return (str((Path(base)/relative).absolute()), expected['bytes'], expected['sha256'])

    def read(base, relative, expected, role, target):
        try:
            raw = reader.read_fixed(base, relative, expected)
        except reader.OfflineFailure as error:
            finding = {'role': role, 'item': str(relative), 'status': error.status, 'error': error.code}
            target.append(finding)
            read_snapshots[read_key(base, relative, expected)] = (None, finding)
            admitted[role] = error.status
            return None
        admitted[role] = 'OBSERVED'
        read_snapshots[read_key(base, relative, expected)] = (raw, None)
        return raw

    def load(name, size, digest, role, target, dependencies_ready=True):
        relative = 'scripts/development/offline_evidence/'+name+'.py'
        raw = (fixed_snapshots[relative] if relative in fixed_snapshots else
               read(ROOT, relative, {'bytes': size, 'sha256': digest}, role, target))
        fixed_snapshots[relative] = raw
        if raw is None or not dependencies_ready:
            return None
        # Existing consumers use Path.read_bytes in their fixed imports. Serve
        # only their already admitted immutable snapshots, including both macOS
        # /var spellings, rather than following a rejected or changed path again.
        captured = {str(base/path): value for base in (ROOT.absolute(), ROOT.resolve())
                    for path, value in fixed_snapshots.items()}
        original_reader = Path.read_bytes
        def snapshot_reader(path):
            key = str(path.absolute())
            if key in captured:
                if captured[key] is None:
                    raise RuntimeError('TECHNICAL_DEPENDENCY_NOT_ADMITTED')
                return captured[key]
            return original_reader(path)
        try:
            Path.read_bytes = snapshot_reader
            try:
                return reader.load_source(ROOT/relative, raw, 'fp_mainline_'+name)
            finally:
                Path.read_bytes = original_reader
        except FileNotFoundError:
            status, code = 'MISSING', 'TECHNICAL_DEPENDENCY_MISSING'
        except ModuleNotFoundError:
            status, code = 'UNAVAILABLE', 'TECHNICAL_RUNTIME_UNAVAILABLE'
        except (OSError, RuntimeError, ValueError, TypeError, KeyError, RecursionError):
            status, code = 'REJECTED', 'TECHNICAL_CONSUMER_LOAD_FAILED'
        target.append({'role': role, 'item': relative, 'status': status, 'error': code})
        admitted[role] = status
        return None

    def admission(result, rows):
        if rows:
            result = dict(result, input_findings=list(rows), error=rows[0]['error'])
            if any(row['status'] == 'REJECTED' for row in rows):
                result.update(status='REJECTED', verdict='REJECT')
                result['errors'] = list(result.get('errors', []))+['INPUT_ADMISSION_REJECTED']
            elif result['status'] == 'OBSERVED':
                result['status'] = 'MISSING' if any(row['status'] == 'MISSING' for row in rows) else 'UNAVAILABLE'
        return result

    profile_base = profile_directory if profile_directory is not None else (
        ROOT/'docs/development/mainline-execution-2026-10-19-signing-profile-content-rev-001')
    profile_raw = read(profile_base, 'PROFILE_CANDIDATE.json', {'bytes': 6460,
        'sha256': '870ea01830e8000949f01dc060405d2f8536ad651d642aaf51bde6c029063472'}, 'profile', profile_findings)
    package = 'docs/development/verifier-contract-consumption-2026-10-25-rev-001/'
    catalog = read(ROOT, package+'ARTIFACT_INPUTS.json', {'bytes': 1908,
        'sha256': '475ea94672662aaee9681b0b3e594574a05570b888aa949fc00de7f00232c81a'}, 'artifact_catalog', findings)
    base = verifier_directory if verifier_directory is not None else ROOT
    contract_raw = read(base, 'CONTRACT_CANDIDATE.json' if verifier_directory is not None else package+'CONTRACT_CANDIDATE.json',
        {'bytes': 4193, 'sha256': '05fa6b5a9be36a560046c7b2e24b06e4124dce60af7877b28493d076a2120e79'}, 'contract', findings)
    artifacts = None
    if catalog is not None:
        artifacts = {}
        build = Path('docs/development/mainline-execution-2026-10-09-rev-001/public-verifier-build')
        for role, row in json.loads(catalog).items():
            relative = Path(row['path']).relative_to(build) if verifier_directory is not None else row['path']
            artifacts[role] = read(base, relative, row, role, findings)
    shared_dependencies = (
        ('scripts/development/offline_evidence/signing_profile.py', 5214,
         'ea28e595ce0b8d6996ca7dfbf40aa42a60bee19f07cb4755427032e4c74149ff', 'profile_consumer'),
        ('src/forecast_trust_core/canonical.py', 8126,
         'f9ef49579a5c54757c6660d377275a0ed5f8afdf646f33130651a711005ac9ba', 'canonical_source'),
        ('schemas/acceptance_policy_v3.schema.json', 17344,
         'dc861a3da1799f7f7888f15d6b6da97fdb11bb9de6f83e2a081e375b9f4d5d72', 'rule_schema'),
        ('docs/development/mainline-execution-2026-10-19-signing-profile-content-rev-001/PROFILE_SCHEMA_CANDIDATE.json', 8525,
         '4bbea6a34351178e4adefe5c31b04e8a2eb4cc9e08bbfadbe8c164d066f68fe1', 'profile_schema'),
    )
    for relative, size, digest, role in shared_dependencies:
        fixed_snapshots[relative] = read(ROOT, relative, {'bytes': size, 'sha256': digest}, role, profile_findings)
    if input_snapshot_output is not None:
        input_snapshot_output['src/forecast_trust_core/canonical.py'] = fixed_snapshots['src/forecast_trust_core/canonical.py']
        input_snapshot_output['docs/development/mainline-execution-2026-10-19-signing-profile-content-rev-001/PROFILE_CANDIDATE.json'] = profile_raw
        for relative, _, _, _ in shared_dependencies[2:]:
            input_snapshot_output[relative] = fixed_snapshots[relative]
    shared_ready = all(fixed_snapshots[row[0]] is not None for row in shared_dependencies)
    fixed_snapshots[package+'ARTIFACT_INPUTS.json'] = catalog
    fixed_snapshots[package+'CONTRACT_SCHEMA_CANDIDATE.json'] = read(
        ROOT, package+'CONTRACT_SCHEMA_CANDIDATE.json', {'bytes': 5555,
        'sha256': '08edcb7b2572f8d9d783b6f7079bb6a5f294e0823efa357747a3b419325ef9a5'}, 'contract_schema', findings)
    verifier_ready = shared_ready and catalog is not None and fixed_snapshots[package+'CONTRACT_SCHEMA_CANDIDATE.json'] is not None
    module = load('verifier_contract', 12600,
                  '8eae0158794ddca8b1e053bd2585ef749df805611ac3760dcd25db4fe391e0db',
                  'verifier_consumer', findings, verifier_ready)
    result = None
    if module is not None:
        try:
            result = module.consume(contract_raw, profile_raw, None, artifacts)
        except (RuntimeError, ValueError, TypeError, KeyError, RecursionError):
            findings.append({'role': 'verifier_consumer', 'item': 'verifier_contract.consume',
                             'status': 'REJECTED', 'error': 'TECHNICAL_CONSUMER_FAILED'})
    if result is not None:
        profile = result['profile_result']
    else:
        # The independent old diagnostic still runs after a new-source failure.
        old = load('signing_profile', 5214,
                   'ea28e595ce0b8d6996ca7dfbf40aa42a60bee19f07cb4755427032e4c74149ff',
                   'profile_consumer', profile_findings, shared_ready)
        profile = old.consume(profile_raw, None) if old is not None else {
            'status': 'MISSING', 'profile_content_status': 'NOT_CHECKED',
            'proposed_rule_binding_status': 'MISSING', 'operational_bindings_established': 0,
            'real_admission': 'NOT_READY', 'protocol_state_change': 'NONE'}
        result = {'status': 'MISSING', 'verdict': 'UNRESOLVED',
                  'contract_content_status': 'NOT_CHECKED', 'artifact_binding_status': 'NOT_CHECKED',
                  'proposed_verifier_use_status': 'MISSING', 'operational_bindings_established': 0,
                  'full_build_runtime_closure': 'NOT_ESTABLISHED', 'execution_contract_complete': 'NOT_ESTABLISHED',
                  'message_resource_policy': 'NOT_ESTABLISHED', 'public_authentication': 'NOT_ESTABLISHED',
                  'backend_called': False, 'native_loaded': False, 'message_constructed': False,
                  'real_admission': 'NOT_READY', 'protocol_state_change': 'NONE'}
    profile = admission(profile, profile_findings)
    if any(row['role'] == 'profile' and row['status'] == 'REJECTED' for row in profile_findings):
        profile['profile_content_status'] = 'NOT_CHECKED'
    result['profile_result'] = profile
    result = admission(result, profile_findings+findings)
    if any(row['role'] == 'contract' and row['status'] == 'REJECTED' for row in findings):
        # Reader rejection is known; the pure parser was not given those bytes.
        result['contract_content_status'] = 'NOT_CHECKED'
    for finding in findings:
        if finding['role'] in (artifacts or {}):
            result['artifact_binding_status'] = ('REJECTED' if finding['status'] == 'REJECTED'
                else result['artifact_binding_status'])
            if finding['role'] in result.get('artifact_statuses', {}):
                result['artifact_statuses'][finding['role']]['status'] = finding['status']
    if result['status'] == 'REJECTED':
        result['proposed_verifier_use_status'] = 'REJECTED'
    result['read_admission'] = dict(admitted)
    if gate_output is not None:
        gate_findings, reused = [], 0
        gate_package = 'docs/development/mainline-verifier-gate-integration-2026-10-25-rev-001/'
        gate_catalog = read(ROOT, gate_package+'GATE_INPUTS.json', {'bytes': 25968,
            'sha256': 'a57c4fa4426a1dec2fad298fea4a63f4a7b717331b826a15db25c6daa4795bff'},
            'gate_input_catalog', gate_findings)
        gate_module = load('verifier_gate', 5195,
            'e820522cdda3a51624b9152fe4da07e66d8a2c1d5f820dd0f2a1d44b9b41796f',
            'gate_consumer', gate_findings, gate_catalog is not None)
        gate_base = gate_directory if gate_directory is not None else ROOT
        def gate_read(row):
            nonlocal reused
            key = read_key(gate_base, row['path'], row)
            if key in read_snapshots:
                reused += 1
                raw, failure = read_snapshots[key]
                if failure is not None:
                    gate_findings.append(dict(failure, role='gate_input', item=row['path']))
                return raw
            return read(gate_base, row['path'], row, 'gate_input', gate_findings)
        gate = None
        if gate_module is not None:
            try:
                gate = gate_module.consume(gate_catalog, gate_read)
            except (OSError, RuntimeError, ValueError, TypeError, KeyError, RecursionError):
                gate_findings.append({'role':'gate_consumer', 'item':'verifier_gate.consume',
                                      'status':'REJECTED', 'error':'DECLARED_GATE_CONSUMER_FAILED'})
        if gate is None:
            gate = {'status':'MISSING', 'scope':'DECLARED_GATE_NOT_CHECKED', 'findings':[],
                    'gate_check_executed':False, 'admitted_input_count':0,
                    'required_declared_gate_inputs':63, 'consumed_distinct_gate_inputs':0,
                    'native_loaded':False, 'backend_called':False, 'message_constructed':False,
                    'full_build_runtime_closure':'NOT_ESTABLISHED', 'public_authentication':'NOT_ESTABLISHED',
                    'real_admission':'NOT_READY', 'protocol_state_change':'NONE'}
        # A rejected raw input is NOT_ADMITTED, rather than a second, invented
        # missing-file claim. Preserve the actual reader diagnosis exactly once.
        diagnosed = {f['item'] for f in gate_findings}
        own_findings = [dict(f, role='gate_check') for f in gate.get('findings', []) if f['item'] not in diagnosed]
        gate = admission(gate, gate_findings)
        gate['findings'] = gate_findings+own_findings
        if gate['findings']:
            rank = {'REJECTED':0, 'MISSING':1, 'UNAVAILABLE':2}
            gate['status'] = min(gate['findings'], key=lambda f:rank[f['status']])['status']
        gate['reused_admitted_snapshots'] = reused
        gate_output.update(gate)
        if gate_snapshot_output is not None:
            rows = json.loads(gate_catalog)['inputs'] if gate_catalog is not None else []
            for record in rows:
                gate_snapshot_output[record['path']] = read_snapshots.get(
                    read_key(gate_base, record['path'], record), (None, None))[0]
            for name, expected in (
                (gate_package+'GATE_INPUTS.json', {'bytes':25968,
                 'sha256':'a57c4fa4426a1dec2fad298fea4a63f4a7b717331b826a15db25c6daa4795bff'}),
                ('scripts/development/offline_evidence/verifier_gate.py', {'bytes':5195,
                 'sha256':'e820522cdda3a51624b9152fe4da07e66d8a2c1d5f820dd0f2a1d44b9b41796f'})):
                gate_snapshot_output[name] = read_snapshots.get(read_key(ROOT,name,expected),(None,None))[0]
    if input_snapshot_output is not None:
        input_snapshot_output.update(fixed_snapshots)
    return profile, result


def technical_public_math(shared, *, snapshot_output=None):
    """Consume retained D271 observations; never run its executable/native path."""
    package='docs/development/public-math-mainline-consumption-2026-10-28-rev-001/'
    findings=[];reused=0
    def read(row):
        nonlocal reused
        name=row['path']
        if name in shared:
            raw=shared[name]
            if raw is not None:reused+=1
        else:
            try:raw=reader.read_fixed(ROOT,name,row)
            except reader.OfflineFailure as error:
                findings.append({'role':'public_math_input','item':name,'status':error.status,'error':error.code})
                raw=None
        if snapshot_output is not None:snapshot_output[name]=raw
        return raw
    raw=read({'path':package+'EXPECTED_INPUTS.json','bytes':36745,
              'sha256':'f617aa1ee8365cd73357a79d07f9ef6736df423b8780bb02337a5568346ca94e'})
    source=read({'path':'scripts/development/offline_evidence/public_math.py','bytes':7055,
                 'sha256':'95c2338ed9ca427a8e4c10f7777699c43910aafd6a19898d1bae393f0f8b05c1'})
    result={'status':'MISSING','findings':[],'scope':'RETAINED_PUBLIC_MATH_NOT_CHECKED',
            'native_loaded_here':False,'backend_called_here':False,'public_authentication':'NOT_ESTABLISHED',
            'full_build_runtime_closure':'NOT_ESTABLISHED','real_admission':'NOT_READY','protocol_state_change':'NONE'}
    if raw is not None and source is not None:
        try:
            module=reader.load_source(HERE/'public_math.py',source,'fp_retained_public_math_consumer')
            result=module.consume(raw,read)
        except (OSError,RuntimeError,ValueError,TypeError,KeyError,RecursionError):
            findings.append({'role':'public_math_consumer','item':'public_math.consume',
                             'status':'REJECTED','error':'RETAINED_PUBLIC_MATH_CONSUMER_FAILED'})
    diagnosed={f['item'] for f in findings}
    result['findings']=findings+[dict(f,role='public_math_check') for f in result['findings'] if f['item'] not in diagnosed]
    if result['findings']:
        result['status']='REJECTED' if any(f['status']=='REJECTED' for f in result['findings']) else 'MISSING'
    result['reused_admitted_snapshots']=reused
    return result


def technical_rule_inputs(directory=None):
    """Reuse D265 finite snapshots; its observed content is never authority."""
    result = {'status': 'MISSING', 'scope': 'FINITE_TECHNICAL_RULE_INPUTS_ONLY',
              'public_authentication': 'NOT_ESTABLISHED', 'real_admission': 'NOT_READY',
              'protocol_state_change': 'NONE'}
    relative = 'docs/development/thirteen-profile-snapshot-consumption-2026-10-27-rev-001/consume.py'
    try:
        raw = reader.read_fixed(ROOT, relative, {'bytes': 8815,
            'sha256': '5f4860b4342821f863bfbf4b9c0590a2a263242be0c9865422250eb040522e7a'})
        module = ModuleType('fp_thirteen_profile_snapshots')
        module.__file__ = str(ROOT/relative)
        exec(compile(raw, module.__file__, 'exec'), module.__dict__)
        observation = module.consume(module.capture(ROOT if directory is None else directory))
        if (type(observation) is not dict or observation.get('status') not in {'OBSERVED', 'MISSING', 'REJECTED'}
                or observation.get('public_authentication') != 'NOT_ESTABLISHED'
                or observation.get('actual_governing_binding') != 'NOT_ESTABLISHED'
                or observation.get('full_build_runtime_closure') != 'NOT_ESTABLISHED'
                or observation.get('independently_complete_universe') != 'NOT_ESTABLISHED'
                or observation.get('real_admission') != 'NOT_READY'
                or observation.get('protocol_state_change') != 'NONE'):
            raise ValueError('TECHNICAL_SCOPE_CHANGED')
        if observation['status'] == 'OBSERVED' and (
                observation['snapshot_count'] != 13 or len(observation['profile_content_results']) != 8
                or not all(row['profile_content_valid'] is True for row in observation['profile_content_results'])
                or observation['shared_signing_raw_snapshot'] is not True
                or observation['quorum_container']['inner_seal_and_ref_valid'] is not True
                or observation['snapshot_failures'] or observation['content_failures'] or observation['missing']):
            raise ValueError('TECHNICAL_OBSERVATION_INCOMPLETE')
        return observation
    except reader.OfflineFailure as error:
        return dict(result, status=error.status, error=error.code)
    except (OSError, ValueError, KeyError, TypeError, IndexError, RecursionError):
        return dict(result, status='REJECTED', error='TECHNICAL_INPUT_CONSUMPTION_FAILED')


def source_choices(shared, directory=None, *, snapshot_output=None):
    """Consume the two recorded human choices, without deriving operative trust.

    These identities bind retained trusted-conversation records, not independent
    cryptographic authentication of that conversation or current platform proof.
    """
    role_base='docs/development/initial-role-actual-choice-proposal-2026-10-28-rev-001/'
    soft_base='docs/development/initial-software-basis-actual-choice-2026-10-28-rev-001/'
    definitions=(
        ('owner',role_base+'USER_ROLE_CHOICE.json',1795,'02a33704167e3922a4adddf01b8919b73ae45d61d5cd2ee4653436f216d9df92'),
        ('owner_proposal',role_base+'DECISION.md',3134,'bed3f51fae1bb7c6c151d83ceb46facd7cf931e8917a5d6c2dc44febda7125b2'),
        ('software',soft_base+'USER_SOFTWARE_BASIS_CHOICE.json',3039,'34cccd5ac0f8ee21bcc2fc7a443eb21865738ab9271960b244903fc3f4fc5c24'),
        ('software_proposal',soft_base+'DECISION.md',3292,'0d2742664bb7b65501403e082b9cbf4b844e3cf27c717bcdc4944c88174406fa'),
        ('software_basis',soft_base+'PROPOSED_BASIS.json',3448,'4dde4c09de69f22b971f5ba59361042f592309f7dae26344f88bced2872e6ab5'))
    result={'status':'MISSING','scope':'RECORDED_INDEPENDENT_USER_CHOICES_NOT_OPERATIVE_AUTHORITY',
            'owner_role_choice_supplied':False,'software_basis_choice_supplied':False,
            'current_gate_artifact_expectations_bound':0,'admitted_choice_inputs':0,'findings':[],
            'current_python_and_platform_match':'NOT_ASSESSED',
            'independent_cryptographic_authentication':'NOT_ESTABLISHED',
            'actual_governing_permission_verified':'NOT_ESTABLISHED',
            'full_build_runtime_closure':'NOT_ESTABLISHED','governing_rule_or_contract_adopted':False,
            'operational_bindings_established':0,'public_authentication':'NOT_ESTABLISHED',
            'real_admission':'NOT_READY','protocol_state_change':'NONE'}
    raw={};base=ROOT if directory is None else directory
    def finding(name,status,error):
        result['findings'].append({'role':'independent_choice_input','item':name,'status':status,'error':error})
    for name,path,size,digest in definitions:
        try:raw[name]=reader.read_fixed(base,path,{'bytes':size,'sha256':digest})
        except reader.OfflineFailure as error:finding(path,error.status,error.code)
        if snapshot_output is not None:snapshot_output[path]=raw.get(name)
    result['admitted_choice_inputs']=len(raw)
    for name,proposal,locator in (('owner','owner_proposal','call_cc05ce15785a42e9b885aec6bd433ede'),
                                   ('software','software_proposal','call_cccb844160b54f5e94e3218091591122')):
        if name not in raw or proposal not in raw or (name=='software' and 'software_basis' not in raw):continue
        try:
            record=json.loads(raw[name]);source=record['source']
            if (record['actual_choice_supplied'] is not True or record['project_id']!='forecast-provenance-project'
                or record['forward_only'] is not True or record['historical_retroactive_effect'] is not False
                or record['protocol_state_change']!='NONE'
                or source['kind']!='EXPLICIT_USER_REPLY_TO_EXACT_REVIEWABLE_PROPOSAL'
                or source['question_item_id']!=['request_user_input_async',locator,0]
                or source['independent_of_candidate_and_acceptance_contents'] is not True
                or source['authenticated_timestamp_established'] is not False
                or source['proposal_bytes']!=len(raw[proposal])
                or source['proposal_sha256']!=hashlib.sha256(raw[proposal]).hexdigest()):
                raise ValueError('CHOICE_SOURCE_BINDING')
            if name=='owner':
                if (record['role']!='BOOTSTRAP_MANIFEST_ACCEPTANCE' or record['scope']!='GENESIS_INITIAL_MANIFEST'
                    or record['action']!='MANIFEST_ACCEPTANCE_DECISION' or record['subject_type']!='TrustedManifest'
                    or record['specific_manifest_selected'] is not False or record['rule_versions_adopted'] is not False
                    or record['actual_governing_permission_verified']!='NOT_ESTABLISHED'):
                    raise ValueError('ROLE_SCOPE')
                result['owner_role_choice_supplied']=True
            else:
                basis=json.loads(raw['software_basis'])
                if (source['proposed_basis_bytes']!=len(raw['software_basis'])
                    or source['proposed_basis_sha256']!=hashlib.sha256(raw['software_basis']).hexdigest()
                    or record['use']!='FUTURE_FIRST_INITIAL_TRUSTED_MANIFEST_ACCEPTANCE_MATHEMATICAL_VERIFICATION_BASE'
                    or record['selected_software_expectations']!=basis['expected_software']
                    or record['selected_platform_assumption']!=basis['existing_local_platform']
                    or record['software_updates_automatically_trusted'] is not False
                    or record['four_expectations_are_complete_runtime'] is not False
                    or record['actual_rule_or_contract_adopted'] is not False
                    or record['real_message_or_public_entry_migration_authorized'] is not False):
                    raise ValueError('SOFTWARE_SCOPE')
                result['software_basis_choice_supplied']=True
                if type(shared) is not dict:raise ValueError('SHARED_GATE_MAPPING')
                for kind,size in (('strict_verifier_adapter',5606),('strict_verifier_binary',68344)):
                    expected=record['selected_software_expectations'][kind];body=shared.get(expected['path'])
                    if body is None:finding(expected['path'],'MISSING','SELECTED_GATE_INPUT_NOT_ADMITTED')
                    elif (type(body) is not bytes or len(body)!=size
                          or hashlib.sha256(body).hexdigest()!=expected['sha256']):
                        finding(expected['path'],'REJECTED','SELECTED_GATE_IDENTITY_MISMATCH')
                    else:result['current_gate_artifact_expectations_bound']+=1
        except (ValueError,TypeError,KeyError,IndexError,RecursionError):
            finding(name,'REJECTED','CHOICE_SOURCE_OR_SCOPE_BINDING_INVALID')
    findings=result['findings']
    result['status']='REJECTED' if any(f['status']=='REJECTED' for f in findings) else 'MISSING' if findings else 'OBSERVED'
    return result


def technical_initial_preflight(shared, directory=None, *, snapshot_output=None):
    """Compose existing metadata and retained-code checks on one byte snapshot.

    The finite developer pins grant no independent load basis or permission.
    No real root/message/backend is introduced and no native math is executed.
    """
    definitions = (('canonical', 'src/forecast_trust_core/canonical.py', 8126, 'f9ef49579a5c54757c6660d377275a0ed5f8afdf646f33130651a711005ac9ba'), ('claim_authority_contract_gate_v1', 'src/forecast_trust_core/claim_authority_contract_gate_v1.py', 20234, '1ea56f1222afce7e7d96eae7f7217b5e4265c1c667a7f8489d130b92f74124e5'), ('_initial_acceptance_auth_inputs_v1', 'src/forecast_trust_core/_initial_acceptance_auth_inputs_v1.py', 7854, '79a26eebbc3e3ad43d4c81511df8787846fe2f64745a5cead326c23bb292030e'), ('_initial_acceptance_auth_preflight_v1', 'src/forecast_trust_core/_initial_acceptance_auth_preflight_v1.py', 13917, 'dea5c416dcbec810573c32c64bdef2d5d141fba18d281d9015e69732ce6b959c'), ('profile', 'docs/development/mainline-execution-2026-10-19-signing-profile-content-rev-001/PROFILE_CANDIDATE.json', 6460, '870ea01830e8000949f01dc060405d2f8536ad651d642aaf51bde6c029063472'), ('rule', 'docs/development/three-argument-verifier-contract-2026-10-28-rev-001/POLICY_PROPOSAL.json', 8191, '6106f13c08c244ab962a36ade9101891fd05cfaeebbc083b34f9ca89f150c8af'), ('verifier', 'docs/development/three-argument-verifier-contract-2026-10-28-rev-001/CONTRACT_CANDIDATE.json', 9780, 'd5584c6b9f37f0023c3ff8fd685a85fe785122691c2e58636a589576b1cb1ce1'), ('schema:root', 'schemas/bootstrap_governance_root_v1.schema.json', 3859, '5eb1ed5cc7944b7af285b53338cf2491978451b2e070e7b17d1d03b85a1c3438'), ('schema:rule', 'schemas/acceptance_policy_v3.schema.json', 17344, 'dc861a3da1799f7f7888f15d6b6da97fdb11bb9de6f83e2a081e375b9f4d5d72'), ('schema:acceptance', 'schemas/manifest_acceptance_v3.schema.json', 4295, '768b4a1078b01f3e17c512ebb608e4e451d3227c488c0b83342e6d88b9c79d9e'), ('schema:carrier', 'docs/development/mainline-execution-2026-10-09-rev-001/carrier-shape-candidate-2026-10-15-rev-001/candidate-schemas/manifest_acceptance_signature_carrier_shape.schema.json', 2846, 'da2213ed8ce41bc5d32badfb3b042772de87565ff26c215c1766712ead2b72de'), ('schema:profile', 'docs/development/mainline-execution-2026-10-19-signing-profile-content-rev-001/PROFILE_SCHEMA_CANDIDATE.json', 8525, '4bbea6a34351178e4adefe5c31b04e8a2eb4cc9e08bbfadbe8c164d066f68fe1'), ('schema:verifier', 'docs/development/three-argument-verifier-contract-2026-10-28-rev-001/CONTRACT_SCHEMA_CANDIDATE.json', 11648, '4f207b14cd96a84884e9b3d3a77e955fe65b24bff4efe4a9c7e62c0ce9b3e34d'))
    controls = [{'path': 'docs/development/three-argument-verifier-contract-2026-10-28-rev-001/consume.py', 'bytes': 10516, 'sha256': '0e0fbf42b1a2ba9075f1daba138d33f73d4ec04303f74b0417c6d4ab838ab3ba'}, {'path': 'docs/development/three-argument-verifier-contract-2026-10-28-rev-001/SUPPORT_INPUTS.json', 'bytes': 39789, 'sha256': '8a9130ef2ebd31c218c88322abfcf95e9e74beae6c876a3f5bb865a3dc0f7684'}, {'path': 'scripts/development/offline_evidence/verifier_contract.py', 'bytes': 12600, 'sha256': '8eae0158794ddca8b1e053bd2585ef749df805611ac3760dcd25db4fe391e0db'}, {'path': 'scripts/development/offline_evidence/signing_profile.py', 'bytes': 5214, 'sha256': 'ea28e595ce0b8d6996ca7dfbf40aa42a60bee19f07cb4755427032e4c74149ff'}, {'path': 'docs/development/verifier-contract-consumption-2026-10-25-rev-001/CONTRACT_SCHEMA_CANDIDATE.json', 'bytes': 5555, 'sha256': '08edcb7b2572f8d9d783b6f7079bb6a5f294e0823efa357747a3b419325ef9a5'}, {'path': 'docs/development/verifier-contract-consumption-2026-10-25-rev-001/ARTIFACT_INPUTS.json', 'bytes': 1908, 'sha256': '475ea94672662aaee9681b0b3e594574a05570b888aa949fc00de7f00232c81a'}]
    result = {'scope': 'DEVELOPMENT_PREFLIGHT_NOT_AUTHORITATIVE_ADMISSION',
              'status': 'MISSING', 'findings': [], 'failures': [],
              'missing': ['root', 'acceptance', 'manifest', 'carrier_for_signature_ref'],
              'checked_references': [], 'compiled_source_count': 0, 'admitted_data_inputs': 0,
              'reused_admitted_snapshots': 0, 'execution_reused_admitted_snapshots': 0,
              'schema_inputs_admitted': 0, 'validated_object_roles': [],
              'passive_contract_consumer_loaded': False,
              'retained_implementation_support': {'status': 'NOT_CHECKED'},
              'execution_source_admission': 'NOT_ESTABLISHED',
              'independent_authority_and_applicability': 'NOT_ESTABLISHED',
              'full_report_semantics': 'NOT_CHECKED', 'full_runtime': 'NOT_ESTABLISHED',
              'may_construct_message': False, 'may_load_backend': False,
              'public_authentication': 'NOT_ESTABLISHED', 'real_admission': 'NOT_READY',
              'prospective_eligible': False, 'protocol_state_change': 'NONE'}
    if (type(shared) is not dict or len(shared) > 2048 or any(type(k) is not str for k in shared)
            or (snapshot_output is not None and type(snapshot_output) is not dict)):
        return dict(result, status='REJECTED', error='INVALID_SHARED_SNAPSHOT_MAPPING')
    cache, identities, values = {}, {}, {}
    findings = result['findings']
    selected_bytes = 0
    def finding(path, status, code, phase):
        row = {'role': 'initial_preflight_'+phase, 'item': path, 'status': status, 'error': code}
        if row not in findings:
            findings.append(row)
    def read(path, size, digest, phase):
        nonlocal selected_bytes
        identity = (size, digest)
        if path in cache:
            if identities[path] != identity:
                finding(path, 'REJECTED', 'CONFLICTING_DECLARED_SNAPSHOT_IDENTITY', phase)
                return None
            if phase == 'execution' and cache[path] is not None:
                result['execution_reused_admitted_snapshots'] += 1
            return cache[path]
        identities[path] = identity
        selected_bytes += size
        try:
            if size > 1048576 or selected_bytes > 67108864 or len(identities) > 2048:
                raise reader.OfflineFailure('PREFLIGHT_SELECTED_SNAPSHOT_BUDGET')
            if path in shared:
                raw = shared[path]
                if raw is None:
                    raise reader.OfflineFailure('MISSING_ADMITTED_SNAPSHOT', 'MISSING')
                if phase == 'base':
                    result['reused_admitted_snapshots'] += 1
                else:
                    result['execution_reused_admitted_snapshots'] += 1
            else:
                raw = reader.read_fixed(ROOT if directory is None else directory, path,
                                        {'bytes': size, 'sha256': digest})
            if type(raw) is not bytes or len(raw) != size or hashlib.sha256(raw).hexdigest() != digest:
                raise reader.OfflineFailure('BORROWED_SNAPSHOT_IDENTITY_MISMATCH')
            cache[path] = raw
        except reader.OfflineFailure as error:
            cache[path] = None
            finding(path, error.status, error.code, phase)
        return cache[path]
    for role, path, size, digest in definitions:
        values[role] = read(path, size, digest, 'base')
    for row in controls:
        read(row['path'], row['bytes'], row['sha256'], 'execution')
    support_manifest = cache[controls[1]['path']]
    support_rows = []
    if support_manifest is not None:
        # Exact raw identity was checked before interpreting any paths.
        support_rows = json.loads(support_manifest)['inputs']
        for row in support_rows:
            read(row['path'], row['bytes'], row['sha256'], 'execution')
    if snapshot_output is not None:
        snapshot_output.update(cache)
    result['selected_snapshot_input_count'] = len(cache)
    result['selected_snapshot_total_bytes'] = sum(len(b) for b in cache.values() if b is not None)
    result['selected_snapshot_declared_bytes'] = selected_bytes
    if any(values[name] is None for name, *_ in definitions[:4]):
        return dict(result, status='REJECTED' if any(f['status']=='REJECTED' for f in findings) else 'MISSING')

    prefix = '_fp_d284_preflight'
    names = [prefix]+[prefix+'.'+row[0] for row in definitions[:4]]
    prior = {name: sys.modules.get(name) for name in names}
    package = ModuleType(prefix); package.__path__ = []
    sys.modules[prefix] = package
    try:
        for name, path, _, _ in definitions[:4]:
            module = ModuleType(prefix+'.'+name); module.__file__ = str(ROOT/path)
            module.__package__ = prefix
            sys.modules[module.__name__] = module
            exec(compile(values[name], module.__file__, 'exec'), module.__dict__)
            result['compiled_source_count'] += 1
        specs, data, schema_bytes = [], {}, {}
        for role, path, size, digest in definitions[4:]:
            raw = values[role]
            if role.startswith('schema:'):
                schema_bytes[role[7:]] = raw
                continue
            if raw is None:
                continue
            obj = module.parse_json_strict(raw)
            specs.append(module.InputSpec(role, 'SEALED_JSON', size, digest,
                         (obj['object_id'], obj['content_sha256']), obj['object_type'], obj['schema_version']))
            data[role] = raw
        checked = module.preflight_initial_contracts(tuple(specs), data, schema_bytes)
        snapshots = checked.pop('snapshots')
        result.update(checked)
        result['execution_source_admission'] = 'NOT_ESTABLISHED'
        result['admitted_data_inputs'] = sum(not item.role.startswith('schema:') for item in snapshots.items)
        result['snapshot_total_bytes'] = snapshots.total_bytes_supplied
        result['retained_bytes'] = snapshots.retained_bytes
        if not findings and support_manifest is not None:
            # Every selected source/data body has been admitted before loading
            # the unchanged passive consumer. Import reads only this snapshot.
            captured = {str(base/path): raw for base in (ROOT.absolute(), ROOT.resolve())
                        for path, raw in cache.items()}
            original_reader = Path.read_bytes
            def snapshot_reader(path):
                name = str(path.absolute())
                if name not in captured or type(captured[name]) is not bytes:
                    raise RuntimeError('UNADMITTED_PASSIVE_CONSUMER_READ')
                return captured[name]
            try:
                Path.read_bytes = snapshot_reader
                contract = reader.load_source(ROOT/controls[0]['path'], cache[controls[0]['path']],
                                              'fp_initial_retained_v3')
                result['passive_contract_consumer_loaded'] = True
                support = {row['path']: cache[row['path']] for row in support_rows}
                artifacts = {role: cache[row['path']] for role, row in contract.EXPECTED['artifacts'].items()}
                retained = contract.consume(values['verifier'], values['profile'], values['rule'],
                                            artifacts, support_manifest, support)
            finally:
                Path.read_bytes = original_reader
            if (type(retained) is not dict or retained.get('status') not in {'OBSERVED','MISSING','REJECTED'}
                    or retained.get('backend_called') is not False or retained.get('native_loaded') is not False
                    or retained.get('message_constructed') is not False
                    or retained.get('operational_bindings_established') != 0
                    or retained.get('actual_MA3_admission') != 'NOT_ESTABLISHED'
                    or retained.get('independent_authority_and_applicability') != 'NOT_ESTABLISHED'
                    or retained.get('public_authentication') != 'NOT_ESTABLISHED'
                    or retained.get('real_admission') != 'NOT_READY' or retained.get('protocol_state_change') != 'NONE'):
                raise ValueError('RETAINED_IMPLEMENTATION_SCOPE_CHANGED')
            result['retained_implementation_support'] = retained
            for code in retained['errors']:
                result['failures'].append(['retained_execution', code])
            for name in retained['missing']:
                marker = 'retained_execution:'+name
                if marker not in result['missing']:
                    result['missing'].append(marker)
            if retained['status'] == 'OBSERVED':
                result['execution_source_admission'] = 'FINITE_DEVELOPMENT_SUPPORT_MATCH_NOT_INDEPENDENT_LOAD_BASIS'
            elif retained['status'] == 'REJECTED':
                result['failures'].append(['retained_execution', 'RETAINED_IMPLEMENTATION_REJECTED'])
        if result['failures'] or any(f['status']=='REJECTED' for f in findings):
            result['status'] = 'REJECTED'
        elif result['missing'] or findings:
            result['status'] = 'MISSING'
        return result
    except (OSError, RuntimeError, ValueError, TypeError, KeyError, RecursionError, ImportError):
        return dict(result, status='REJECTED', error='INITIAL_INPUT_PREFLIGHT_FAILED')
    finally:
        for name in names:
            if prior[name] is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = prior[name]


def missing_input_modules(profile_directory=None, verifier_directory=None, gate_directory=None):
    from forecast_trust_core.g10_replay_v1 import ReplayBasis, _aggregate_g10
    from forecast_trust_core.g10_requirements_v1 import reconstruct_requirements
    from forecast_trust_core.cycle_universe_v1 import reconstruct_cycle_universe
    from forecast_trust_core.qualification_scope_v1 import replay_qualification_scope
    from forecast_trust_core.initial_acceptance_public_auth_v1 import verify_initial_acceptance_public
    from forecast_trust_core.claim_authority_v1 import derive_confirmatory_eligibility_from_evidence
    from forecast_trust_core.canonical import seal_object
    class MissingResolver:
        def resolve_exact(self, reference):
            return None
    resolver = MissingResolver()
    # This missing public basis selects no actual project/root/rule or history.
    basis = ReplayBasis('PUBLIC_EVIDENCE', '', '', '', None, None, None, None, None, None, None, None, ())
    requirements = reconstruct_requirements(basis, resolver)
    cycles = reconstruct_cycle_universe(basis, resolver)
    qualification = replay_qualification_scope(basis, cycles, requirements, resolver)
    g10 = _aggregate_g10(requirements.reducer_input(()))
    auth = verify_initial_acceptance_public(basis=basis, acceptance=None, resolver=resolver)
    gate = {};gate_snapshots = {};initial_snapshots = {}
    technical_profile, technical_verifier = signing_candidates(profile_directory, verifier_directory,
                                                               gate_directory=gate_directory, gate_output=gate,
                                                               gate_snapshot_output=gate_snapshots,
                                                               input_snapshot_output=initial_snapshots)
    public_math = technical_public_math(gate_snapshots, snapshot_output=initial_snapshots)
    choices = source_choices(gate_snapshots, snapshot_output=initial_snapshots)
    initial_snapshots.update(gate_snapshots)
    preflight = technical_initial_preflight(initial_snapshots)
    technical_inputs = technical_rule_inputs()
    # Same keyless diagnostic subject as D174; no forecast is issued or saved.
    forecast = seal_object({'schema_version': '1.0', 'value': '1', 'synthetic_only': True},
                           object_type='IssuedForecast', stable_context='TASK_DEVELOPMENT_ONLY',
                           semantic_id='SYNTHETIC_NO_PROTOCOL_FORECAST')
    eligibility, _ = derive_confirmatory_eligibility_from_evidence(
        forecast, component_specs=[], required_claim_requirements=[])
    def row(identity, title, status, result):
        return {'id': identity, 'title': title,
                'status': 'REJECTED' if status in {'FAIL', 'REJECTED'} else 'MISSING',
                'scope': 'MISSING_INPUT_DIAGNOSTIC_ONLY_NOT_REAL_EVIDENCE_VERIFICATION', 'result': result}
    initial = row('initial-authority', '初始规则与权限',
            'REJECTED' if any(child['status'] == 'REJECTED' for child in (technical_profile, technical_verifier, gate, technical_inputs, public_math, choices, preflight)) else auth.status,
            {'status': auth.status, 'reason_codes': list(auth.reason_codes), 'message_constructed': False,
             'technical_signing_profile_candidate': technical_profile,
             'technical_verifier_contract_candidate': technical_verifier,
             'technical_verifier_identity_gate': gate,
             'technical_public_math_execution': public_math,
             'independent_source_choices': choices,
             'technical_initial_auth_input_preflight': preflight,
             'technical_rule_input_snapshots': technical_inputs})
    findings = technical_profile.get('input_findings', [])+technical_verifier.get('input_findings', [])+gate.get('findings', [])+public_math.get('findings', [])+choices.get('findings', [])+preflight.get('findings', [])
    if findings:
        initial['findings'] = list({(f['role'], f['item'], f['status'], f['error']): f for f in findings}.values())
    return [initial,
        row('qualification-history', '来源资格与完整历史', qualification.overall,
            {'status': qualification.overall, 'admissions': len(qualification.admissions),
             'checks': [asdict(check) for check in qualification.checks]}),
        row('mandatory-cycles', '完整周期与槽位范围', cycles.overall,
            {'status': cycles.overall, 'observed_cycles': len(cycles.cycles),
             'observed_slots': len(cycles.slots), 'checks': [asdict(check) for check in cycles.checks],
             'independent_complete_universe': 'NOT_ESTABLISHED'}),
        row('prospective-eligibility', '完整预测资格检查', eligibility['state'], eligibility),
        {'id': 'workflow-and-retention', 'title': '适用工作流与独立留存', 'status': 'MISSING',
         'scope': 'REAL_CHECK_NOT_EXECUTED', 'error': 'APPLICABILITY_AND_REAL_RECORDS_NOT_ESTABLISHED'},
        row('final-readiness', '完整G10与最终评估', g10.overall,
            {'status': g10.overall, 'requirements_status': requirements.overall,
             'coverage': [asdict(check) for check in g10.coverage_diagnostics],
             'complete_authoritative_replay': 'NOT_ESTABLISHED'}),
    ]


def main():
    request = json.loads(sys.stdin.read())
    sys.addaudithook(reader.audit_policy)
    directory = Path(request['run_inputs']) if request.get('run_inputs') is not None else RUN_DIRECTORY
    trace = Path(request['execution_inputs']) if request.get('execution_inputs') is not None else TRACE_DIRECTORY
    proof = Path(request['proof_inputs']) if request.get('proof_inputs') is not None else PROOF_DIRECTORY
    headers = Path(request['header_inputs']) if request.get('header_inputs') is not None else HEADER_DIRECTORY
    chain = Path(request['chain_inputs']) if request.get('chain_inputs') is not None else CHAIN_DIRECTORY
    core = Path(request['core_inputs']) if request.get('core_inputs') is not None else CORE_DIRECTORY
    profile = Path(request['profile_inputs']) if request.get('profile_inputs') is not None else None
    verifier = Path(request['verifier_inputs']) if request.get('verifier_inputs') is not None else None
    gate = Path(request['verifier_gate_inputs']) if request.get('verifier_gate_inputs') is not None else None
    roughtime = Path(request['roughtime_build_inputs']) if request.get('roughtime_build_inputs') is not None else None
    roughtime_event = Path(request['roughtime_event_inputs']) if request.get('roughtime_event_inputs') is not None else None
    strong_candidate = Path(request['strong_candidate_inputs']) if request.get('strong_candidate_inputs') is not None else None
    snapshot = {}
    loading = {}
    completed = []
    try:
        with provenance_consumer().checked_product_imports(ROOT, reader, loading):
            finite = finite_module(directory, snapshot)
            completed.append(finite)
            execution = execution_module(trace, snapshot)
            completed.append(execution)
        for module in (finite, execution):
            module['selected_code_loading'] = loading
        # Source-file equality remains separate from this selected local code
        # observation; neither establishes complete runtime or historical truth.
        execution['source_package_binding']['selected_current_top_level_code'] = loading
        completed.append(time_module(proof, headers, chain, core, roughtime, roughtime_event,strong_candidate))
        modules = [*completed, *missing_input_modules(profile, verifier, gate)]
    except reader.OfflineFailure as error:
        # No unchecked product branch is imported after source admission fails.
        # CLI public-data branches still execute in their separate workers.
        modules = [{'id': 'module-consumption', 'title': '有限产品代码载入', 'status': error.status,
                    'error': error.code, 'scope': 'SELECTED_PRODUCT_CODE_ADMISSION_FAILED',
                    'findings': error.findings,
                    'native_authority_diagnostics': 'NOT_EXECUTED_AFTER_CODE_REJECTION'}, time_module(proof, headers, chain, core, roughtime, roughtime_event,strong_candidate)]
    except (ModuleNotFoundError, PackageNotFoundError):
        # Dependency absence says nothing about the truth of unexecuted checks.
        # Keep independently readable time inputs and the CLI's public branches.
        modules = [*completed, {'id': 'module-consumption', 'title': '有限产品运行环境', 'status': 'UNAVAILABLE',
                    'error': 'MISSING_DEPENDENCY', 'scope': 'NOT_EXECUTED_MISSING_RUNTIME_DEPENDENCY',
                    'native_authority_diagnostics': 'NOT_EXECUTED_MISSING_RUNTIME_DEPENDENCY'}]
        if not any(row['id'] == 'time-and-durability' for row in completed):
            modules.append(time_module(proof, headers, chain, core, roughtime, roughtime_event,strong_candidate))
    print(json.dumps({'mode': 'FINITE_MAINLINE_MODULES', 'modules': modules}, sort_keys=True))


if __name__ == '__main__':
    main()
