"""Finite supplied-byte R4T content comparison; no I/O or protocol authority.

Fixed D149 or D151 successor schema bytes are supplied, never loaded from docs.
Expected controls describe a local comparison, not independent applicability.
Null observations remain readable but cannot acquire a new sealing convention.
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
from calendar import monthrange
from collections import Counter

from jsonschema import Draft202012Validator, FormatChecker

from . import canonical
from . import unittest_observations_v1 as local_observations

SCHEMA_SHA256 = '578305258cd7a2a23560f0bfe4c3620d4eee32576ddab113665a911677c0a978'
UNAVAILABLE_SCHEMA_SHA256 = 'd081c35091a25f031f7ccdd398e7bc7fcfe9f712a08c94bc30f6edff65fef5a9'
BYTE_LIMIT = 4 * 1024 * 1024
ROOT_REFS = ('test_definition_ref', 'runtime_profile_ref', 'content_profile_ref',
             'source_file_manifest_ref', 'package_artifact_ref', 'dependency_lock_ref')
INV_FIELDS = ('invocation_id', 'command_id', 'attempt_index', 'argv', 'cwd',
              'environment', 'executable_sha256', 'loaded_source_bindings')
INSTANCE_FIELDS = ('instance_id', 'check_id', 'operation_id', 'fixture_refs')
UNEXECUTED = frozenset({'SKIPPED', 'NOT_RUN', 'ABORTED', 'UNKNOWN'})


def _tree(value):
    pending = [(value, 0)]
    count = 0
    has_null = False
    while pending:
        item, depth = pending.pop()
        count += 1
        if depth > 64 or count > 131072:
            raise ValueError('LOCAL_TREE_LIMIT')
        if type(item) is dict:
            if any(type(k) is not str or not k.isascii() for k in item):
                raise ValueError('JSON_KEYS')
            pending.extend((v, depth + 1) for v in item.values())
        elif type(item) is list:
            pending.extend((v, depth + 1) for v in item)
        elif item is None:
            has_null = True
        elif type(item) is str:
            if any(0xD800 <= ord(c) <= 0xDFFF for c in item):
                raise ValueError('JSON_SURROGATE')
        elif type(item) is int:
            if abs(item) > canonical.MAX_SAFE_INTEGER:
                raise ValueError('JSON_INTEGER')
        elif type(item) is not bool:
            raise ValueError('JSON_VALUE')
    return has_null


def _parse(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            if key in result:
                raise ValueError('DUPLICATE_JSON_KEY')
            result[key] = value
        return result

    def integer(text):
        if text == '-0':
            raise ValueError('NEGATIVE_ZERO')
        value = int(text)
        if abs(value) > canonical.MAX_SAFE_INTEGER:
            raise ValueError('JSON_INTEGER')
        return value

    def forbidden(_):
        raise ValueError('JSON_NUMBER')

    obj = json.loads(canonical.decode_utf8_json(raw), object_pairs_hook=pairs,
                     parse_int=integer, parse_float=forbidden, parse_constant=forbidden)
    _tree(obj)
    return obj


def _closed(properties):
    return {'type': 'object', 'additionalProperties': False,
            'required': list(properties), 'properties': properties}


def _expected_validator(schema, schema_raw_sha256):
    defs = copy.deepcopy(schema['$defs'])
    ip = defs['invocation']['properties']
    rp = defs['instance_result']['properties']
    instance = _closed({**{k: rp[k] for k in INSTANCE_FIELDS}, 'allowed_outcomes': {
        'type': 'array', 'minItems': 1, 'uniqueItems': True, 'items': rp['outcome']}})
    invocation = _closed({**{k: ip[k] for k in INV_FIELDS},
        'expected_exit_codes': {'type': 'array', 'minItems': 1, 'uniqueItems': True,
                                'items': {'type': 'integer', 'minimum': -2147483648, 'maximum': 2147483647}},
        'instances': {'type': 'array', 'minItems': 1, 'maxItems': 16384, 'items': instance}})
    # A fixed expected executable digest must not be an unknown observation.
    invocation['properties']['executable_sha256'] = {'$ref': '#/$defs/sha256'}
    root = schema['properties']
    successor = schema_raw_sha256 == UNAVAILABLE_SCHEMA_SHA256
    properties = {'format': {'const': 'FP_DEV_R4T_EXECUTION_EXPECTED_V2' if successor else 'FP_DEV_R4T_EXECUTION_EXPECTED_V1'},
        'scope': {'const': 'FINITE_DEVELOPMENT_SCOPE_ONLY'},
        'report_ref': {'$ref': '#/$defs/exact_ref'}, 'report_raw_sha256': {'$ref': '#/$defs/sha256'},
        'bindings': _closed({k: root[k] for k in (*ROOT_REFS, 'component_contract_refs')}),
        'test_definition_raw_sha256': root['test_definition_raw_sha256'], 'run_id': root['run_id'],
        'invocations': {'type': 'array', 'minItems': 1, 'maxItems': 1024, 'items': invocation}}
    if successor:
        properties['schema_raw_sha256'] = {'const': UNAVAILABLE_SCHEMA_SHA256}
    return Draft202012Validator({**_closed(properties), '$defs': defs}, format_checker=FormatChecker())


def _unique(rows, key):
    values = [key(row) for row in rows]
    return len(values) == len(set(values))


def _pre_definition_validator(schema, schema_raw_sha256):
    """Reuse the finite expected shape without post-run report selectors."""
    shape = copy.deepcopy(_expected_validator(schema, schema_raw_sha256).schema)
    properties = shape['properties']
    for key in ('report_ref', 'report_raw_sha256'):
        del properties[key]
    properties['format'] = {'const': 'FP_DEV_R4T_PRE_RUN_EXPECTATIONS_V1'}
    properties['schema_raw_sha256'] = {'const': schema_raw_sha256}
    shape['required'] = list(properties)
    return Draft202012Validator(shape, format_checker=FormatChecker())


def _ref_key(value):
    return value['object_id'], value['content_sha256']


def _ordered_refs(rows):
    keys = [_ref_key(x) for x in rows]
    return keys == sorted(set(keys))


def _instance_label(key):
    # Reversible JSON-Pointer-style escaping keeps the pair injective.
    return '/'.join(part.replace('~', '~0').replace('/', '~1') for part in key)


def _local_time_key(stamp):
    # Only the two pinned schema timestamp fields use this UTC grammar.
    # FormatChecker's optional plugins and permissive ISO parsers are not used.
    match = re.fullmatch(
        r'([0-9]{4})-([0-9]{2})-([0-9]{2})[Tt]([0-9]{2}):([0-9]{2}):([0-9]{2})'
        r'(?:\.([0-9]+))?Z', stamp)
    if match is None:
        raise ValueError('LOCAL_TIME_INVALID')
    parts = tuple(int(part) for part in match.groups()[:6])
    year, month, day, hour, minute, second = parts
    if not 1 <= month <= 12:
        raise ValueError('LOCAL_TIME_INVALID')
    last_day = monthrange(year, month)[1]
    if not (1 <= day <= last_day and hour <= 23 and minute <= 59 and second <= 60):
        raise ValueError('LOCAL_TIME_INVALID')
    if second == 60 and not (day == last_day and hour == 23 and minute == 59):
        raise ValueError('LOCAL_TIME_INVALID')
    # Fraction stays a digit string, including beyond int/float precision limits.
    return parts, (match.group(7) or '').rstrip('0')


def _unavailable(value):
    # Called on schema-validated observations only. Legacy null remains unknown.
    return value is None or (type(value) is dict and value.get('state') == 'UNAVAILABLE')


def consume_execution_content(expected, report_bytes, schema_bytes, raw_artifacts):
    """Compare finite public/software inputs; never run argv or resolve a path.

    Expected controls and artifact bytes must already have been fixed outside
    this function. Their authority/completeness and actual execution remain
    unestablished, including when finite_expectations_match is true.
    """
    out = {'verdict': 'UNRESOLVED', 'finite_expectations_match': False,
        'comparison_scope': 'LOCAL_EXPECTED_SCOPE_ONLY', 'seal_status': 'NOT_CHECKED',
        'report_errors': [], 'comparison_errors': [], 'missing_inputs': [],
        'missing_invocations': [], 'missing_instances': [], 'failed_instances': [],
        'unknown_instances': [], 'observations': [], 'finding_refs': [],
        'unavailable_observations': [],
        'actual_execution_truth': 'NOT_VERIFIED', 'independently_complete_universe': 'NOT_ESTABLISHED',
        'authenticated_chronology': 'NOT_ESTABLISHED', 'authority_and_applicability': 'NOT_ESTABLISHED',
        'real_admission': 'NOT_READY', 'real_g02_g03': 'NOT_ESTABLISHED',
        'real_genesis_readiness': 'NOT_ESTABLISHED', 'prospective_eligible': False,
        'protocol_state_change': 'NONE'}

    def add(field, code):
        if code not in out[field]:
            out[field].append(code)

    schema = None
    schema_raw_sha256 = None
    if schema_bytes is None:
        add('missing_inputs', 'schema')
    elif type(schema_bytes) is not bytes or hashlib.sha256(schema_bytes).hexdigest() not in (SCHEMA_SHA256, UNAVAILABLE_SCHEMA_SHA256):
        add('report_errors', 'SCHEMA_IDENTITY_MISMATCH')
    else:
        schema_raw_sha256 = hashlib.sha256(schema_bytes).hexdigest()
        schema = _parse(schema_bytes)
    controls = None
    if expected is None:
        add('missing_inputs', 'expected')
    elif schema is not None:
        try:
            if type(expected) is not dict or _tree(expected) or not _expected_validator(schema, schema_raw_sha256).is_valid(expected):
                raise ValueError('expected shape')
            controls = copy.deepcopy(expected)
            invs = controls['invocations']
            if not _unique(invs, lambda x: x['invocation_id']):
                raise ValueError('expected duplicate')
            for inv in invs:
                if not _unique(inv['instances'], lambda x: x['instance_id']):
                    raise ValueError('expected duplicate instance')
        except (ValueError, TypeError, RecursionError):
            controls = None
            add('comparison_errors', 'EXPECTED_INVALID')
    report = None
    if report_bytes is None:
        add('missing_inputs', 'report')
    elif type(report_bytes) is not bytes:
        add('report_errors', 'REPORT_BYTES_TYPE')
    else:
        if controls is not None and hashlib.sha256(report_bytes).hexdigest() != controls['report_raw_sha256']:
            add('comparison_errors', 'REPORT_RAW_MISMATCH')
        if len(report_bytes) > BYTE_LIMIT:
            add('missing_inputs', 'report:LOCAL_BYTE_LIMIT')
        else:
            try:
                candidate = _parse(report_bytes)
                if schema is not None:
                    # These exact schema hashes contain only the two date-time
                    # formats, explicitly validated below independently of plugins.
                    if not Draft202012Validator(schema).is_valid(candidate):
                        add('report_errors', 'REPORT_SHAPE_INVALID')
                    else:
                        report = candidate
            except (ValueError, TypeError, RecursionError) as exc:
                if str(exc) == 'LOCAL_TREE_LIMIT':
                    add('missing_inputs', 'report:LOCAL_TREE_LIMIT')
                else:
                    add('report_errors', 'REPORT_JSON_INVALID')
    if report is not None:
        time_keys = []
        for inv in report['invocations']:
            pair = []
            for field in ('local_start_utc', 'local_end_utc'):
                value = inv['time_observations'][field]
                key = None
                if not _unavailable(value):
                    try:
                        key = _local_time_key(value)
                    except ValueError:
                        add('report_errors', 'LOCAL_TIME_INVALID')
                    if key is not None and key[0][-1] == 60:
                        # Syntax cannot establish an announced leap-second event.
                        add('missing_inputs', 'local_time:LEAP_SECOND_CONTEXT:' + inv['invocation_id'])
                        key = None
                pair.append(key)
            time_keys.append(pair)
        if _tree(report):
            out['seal_status'] = 'NOT_ESTABLISHED_NULL_UNSUPPORTED'
            add('missing_inputs', 'seal:NULL_CANONICALIZATION_UNSUPPORTED')
        elif canonical.verify_sealed_object(report):
            out['seal_status'] = 'VERIFIED'
        else:
            out['seal_status'] = 'INVALID'
            add('report_errors', 'REPORT_SEAL_INVALID')
        if controls is not None:
            if {k: report[k] for k in ('object_id', 'content_sha256')} != controls['report_ref']:
                add('comparison_errors', 'REPORT_REF_MISMATCH')
            if any(report[k] != controls['bindings'][k] for k in (*ROOT_REFS, 'component_contract_refs')):
                add('comparison_errors', 'ROOT_BINDING_MISMATCH')
            if any(report[k] != controls[k] for k in ('test_definition_raw_sha256', 'run_id')):
                add('comparison_errors', 'DEFINITION_RUN_MISMATCH')
        bound = controls is not None and not out['comparison_errors'] and not out['report_errors'] and out['seal_status'] == 'VERIFIED'
        if not _ordered_refs(report['component_contract_refs']):
            add('report_errors', 'COMPONENT_SET_INVALID')
        for role in report['unavailable_evidence']:
            add('missing_inputs', 'declared:' + role['role_id'])
        if report['run_completion'] != 'COMPLETE':
            add('missing_inputs', 'run:INCOMPLETE')
        findings = list(report['finding_refs'])
        actual_ids = []
        invocation_counts = Counter(x['invocation_id'] for x in report['invocations'])
        attributable_invocations = set()
        expected_invs = {x['invocation_id']: x for x in controls['invocations']} if controls is not None else {}
        if type(raw_artifacts) is not dict or len(raw_artifacts) > 2048 or any(type(k) is not str for k in raw_artifacts):
            raw_artifacts = {}
            add('report_errors', 'ARTIFACT_MAP_INVALID')
        for index, inv in enumerate(report['invocations']):
            iid = inv['invocation_id']
            observed_fields = [(k, inv[k]) for k in ('executable_sha256', 'stdout', 'stderr')]
            observed_fields.extend(('time_observations.' + k, v) for k, v in inv['time_observations'].items())
            for field, value in observed_fields:
                if type(value) is dict and _unavailable(value):
                    out['unavailable_observations'].append({'invocation_id': iid, 'field': field,
                        'state': 'UNAVAILABLE', 'reason_code': value['reason_code']})
            if iid in actual_ids or inv['ordinal'] != index:
                add('report_errors', 'INVOCATION_ORDER_OR_DUPLICATE')
            actual_ids.append(iid)
            if not _unique(inv['environment'], lambda x: x['name']) or not _unique(inv['loaded_source_bindings'], lambda x: _ref_key(x['source_unit_ref'])):
                add('report_errors', 'OBSERVED_BINDING_DUPLICATE')
            if bound:
                ex = expected_invs.get(iid)
                if ex is None or any(inv[k] != ex[k] for k in INV_FIELDS
                                     if not (k == 'executable_sha256' and _unavailable(inv[k]))):
                    add('comparison_errors', 'INVOCATION_BINDING_MISMATCH')
                elif inv['termination']['state'] == 'EXITED' and inv['termination']['exit_code'] not in ex['expected_exit_codes']:
                    add('comparison_errors', 'EXIT_CODE_MISMATCH')
                elif (invocation_counts[iid] == 1 and inv['ordinal'] == index
                      and inv['termination']['state'] == 'EXITED'
                      and not _unavailable(inv['executable_sha256'])
                      and _unique(inv['environment'], lambda x: x['name'])
                      and _unique(inv['loaded_source_bindings'], lambda x: _ref_key(x['source_unit_ref']))):
                    attributable_invocations.add(iid)
            if inv['termination']['state'] != 'EXITED':
                add('missing_inputs', 'termination:' + iid)
            if _unavailable(inv['executable_sha256']):
                add('missing_inputs', 'executable:' + iid)
            times = inv['time_observations']
            if any(_unavailable(v) for v in times.values()):
                add('missing_inputs', 'local_time:' + iid)
            start_key, end_key = time_keys[index]
            if start_key is not None and end_key is not None and end_key < start_key:
                add('report_errors', 'LOCAL_TIME_ORDER')
            for stream in ('stdout', 'stderr'):
                artifact = inv[stream]
                if _unavailable(artifact):
                    add('missing_inputs', stream + ':' + iid)
                    continue
                aid = artifact['artifact_id']
                raw = raw_artifacts.get(aid)
                if raw is None:
                    add('missing_inputs', 'artifact:' + aid)
                elif type(raw) is not bytes:
                    add('report_errors', 'RAW_ARTIFACT_TYPE')
                elif len(raw) > BYTE_LIMIT:
                    add('missing_inputs', 'artifact:LOCAL_BYTE_LIMIT')
                elif len(raw) != artifact['byte_length'] or hashlib.sha256(raw).hexdigest() != artifact['raw_sha256']:
                    add('report_errors', 'RAW_ARTIFACT_MISMATCH')
        if bound:
            expected_ids = list(expected_invs)
            out['missing_invocations'] = [x for x in expected_ids if x not in actual_ids]
            if [x for x in actual_ids if x in expected_invs] != [x for x in expected_ids if x in actual_ids]:
                add('comparison_errors', 'EXPECTED_INVOCATION_ORDER_MISMATCH')
                attributable_invocations.clear()
        expected_cases = {(inv['invocation_id'], row['instance_id']): row
            for inv in expected_invs.values() for row in inv['instances']}
        seen_cases = set()
        result_counts = Counter((x['invocation_id'], x['instance_id']) for x in report['results'])
        for row in report['results']:
            key = (row['invocation_id'], row['instance_id'])
            duplicate = key in seen_cases
            seen_cases.add(key)
            ex = expected_cases.get(key)
            row_bound = (bound and key[0] in attributable_invocations and result_counts[key] == 1
                         and ex is not None and all(row[k] == ex[k] for k in INSTANCE_FIELDS))
            out['observations'].append({k: row[k] for k in ('invocation_id', 'instance_id', 'outcome')} | {'expectation_bound': row_bound})
            if duplicate or key[0] not in actual_ids:
                add('report_errors', 'RESULT_LINK_OR_DUPLICATE')
            if bound and (ex is None or any(row[k] != ex[k] for k in INSTANCE_FIELDS)):
                add('comparison_errors', 'INSTANCE_BINDING_MISMATCH')
            if row_bound:
                label = _instance_label(key)
                if row['outcome'] in UNEXECUTED:
                    add('unknown_instances', label)
                elif row['outcome'] not in ex['allowed_outcomes']:
                    add('failed_instances', label)
            for name in ('fixture_refs', 'support_refs', 'finding_refs'):
                if not _ordered_refs(row[name]):
                    add('report_errors', 'RESULT_REF_SET_INVALID')
            if row['reason_codes'] != sorted(set(row['reason_codes'])):
                add('report_errors', 'REASON_CODE_SET_INVALID')
            findings.extend(row['finding_refs'])
        if bound:
            out['missing_instances'] = [_instance_label(k) for k in expected_cases if k not in seen_cases]
        if not _ordered_refs(report['finding_refs']):
            add('report_errors', 'FINDING_SET_INVALID')
        out['finding_refs'] = [dict(object_id=k[0], content_sha256=k[1]) for k in sorted(set(map(_ref_key, findings)))]
        if findings:
            add('missing_inputs', 'findings:TRUTH_NOT_VERIFIED')
        out['finite_expectations_match'] = bound and not any(out[k] for k in (
            'report_errors', 'comparison_errors', 'missing_inputs', 'missing_invocations',
            'missing_instances', 'failed_instances', 'unknown_instances'))
    if out['report_errors'] or out['comparison_errors'] or out['failed_instances']:
        out['verdict'] = 'REJECT'
    return out


def consume_predeclared_execution_content(pre_definition, result_binding,
                                         report_bytes, schema_bytes, raw_artifacts):
    """Separate finite pre-run semantics from post-run report identity.

    Structure and content comparisons cannot authenticate when either input
    was fixed, its authority, or completeness. No path/argv/callback executes.
    """
    errors = []
    missing = []
    schema_sha256 = hashlib.sha256(schema_bytes).hexdigest() if type(schema_bytes) is bytes else None
    schema = _parse(schema_bytes) if schema_sha256 in (SCHEMA_SHA256, UNAVAILABLE_SCHEMA_SHA256) else None
    pre_keys = {'format', 'scope', 'schema_raw_sha256', 'bindings',
                'test_definition_raw_sha256', 'run_id', 'invocations'}
    post_keys = {'report_ref', 'report_raw_sha256'}
    statuses = []
    for label, value, keys, diagnostic in (
        ('pre_definition', pre_definition, pre_keys, 'PRE_DEFINITION_INVALID'),
        ('result_binding', result_binding, post_keys, 'RESULT_BINDING_INVALID'),
    ):
        if value is None:
            missing.append(label)
            statuses.append('MISSING')
            continue
        try:
            if type(value) is not dict or _tree(value) or set(value) != keys:
                raise ValueError('stage shape')
            if schema is None:
                statuses.append('NOT_CHECKED_SCHEMA_UNAVAILABLE')
                continue
            if label == 'pre_definition':
                if value['schema_raw_sha256'] != schema_sha256:
                    errors.append('PRE_SCHEMA_IDENTITY_MISMATCH')
                validator = _pre_definition_validator(schema, schema_sha256)
            else:
                expected_shape = _expected_validator(schema, schema_sha256).schema
                validator = Draft202012Validator({
                    **_closed({k: expected_shape['properties'][k] for k in post_keys}),
                    '$defs': expected_shape['$defs'],
                })
            if not validator.is_valid(value):
                raise ValueError('stage fields')
            statuses.append('VALID_STRUCTURE')
        except (ValueError, TypeError, RecursionError):
            errors.append(diagnostic)
            statuses.append('INVALID')
    expected = None
    if statuses == ['VALID_STRUCTURE', 'VALID_STRUCTURE']:
        expected = copy.deepcopy(pre_definition)
        expected.update(copy.deepcopy(result_binding))
        expected['format'] = ('FP_DEV_R4T_EXECUTION_EXPECTED_V2'
                              if schema_sha256 == UNAVAILABLE_SCHEMA_SHA256
                              else 'FP_DEV_R4T_EXECUTION_EXPECTED_V1')
        if schema_sha256 == SCHEMA_SHA256:
            del expected['schema_raw_sha256']
    out = consume_execution_content(expected, report_bytes, schema_bytes, raw_artifacts)
    out.update(pre_definition_status=statuses[0], result_binding_status=statuses[1],
               pre_run_fixing='NOT_VERIFIED')
    for code in errors:
        if code not in out['comparison_errors']:
            out['comparison_errors'].append(code)
    for label in missing:
        if label not in out['missing_inputs']:
            out['missing_inputs'].append(label)
    if errors:
        out['verdict'] = 'REJECT'
        out['finite_expectations_match'] = False
    return out


def consume_local_unittest_content(expected, events_bytes, run_observation):
    """Check supplied local JSONL bytes, distinct from any formal R4T report.

    Labels, digest controls and termination are caller-supplied local evidence.
    Matching them establishes neither execution truth nor protocol authority.
    No file/path/URL resolution, event generation, execution or signing occurs.
    """
    out = {'verdict': 'UNRESOLVED', 'local_event_consistency_match': False,
        'comparison_scope': 'FINITE_LOCAL_UNITTEST_OBSERVATIONS_ONLY',
        'report_errors': [], 'comparison_errors': [], 'missing_inputs': [],
        'event_comparison': {}, 'actual_execution_truth': 'NOT_VERIFIED',
        'independently_complete_universe': 'NOT_ESTABLISHED',
        'authenticated_chronology': 'NOT_ESTABLISHED',
        'authority_and_applicability': 'NOT_ESTABLISHED',
        'real_admission': 'NOT_READY', 'real_g02_g03': 'NOT_ESTABLISHED',
        'real_genesis_readiness': 'NOT_ESTABLISHED', 'prospective_eligible': False,
        'protocol_state_change': 'NONE'}

    def digest(value):
        return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)

    controls = None
    if expected is None:
        out['missing_inputs'].append('expected')
    else:
        try:
            fields = {'format', 'scope', 'invocation_id', 'attempt_index',
                      'events_raw_sha256', 'expected_exit_codes', 'identities'}
            if (type(expected) is not dict or _tree(expected) or set(expected) != fields
                    or expected['format'] != 'FP_DEV_UNITTEST_OBSERVATION_EXPECTED_V1'
                    or expected['scope'] != out['comparison_scope']
                    or not digest(expected['events_raw_sha256'])):
                raise ValueError('expected shape')
            local_observations._context(expected['invocation_id'], expected['attempt_index'])
            exits = expected['expected_exit_codes']
            if (type(exits) is not list or not exits or len(exits) > 256
                    or any(type(x) is not int or not -2147483648 <= x <= 2147483647 for x in exits)
                    or len(exits) != len(set(exits)) or type(expected['identities']) is not list):
                raise ValueError('expected exits/identities')
            if len(expected['identities']) > 16384:
                out['missing_inputs'].append('expected:LOCAL_IDENTITY_LIMIT')
            else:
                # Shared identity/parent/duplicate validation with no supplied events.
                local_observations.compare_events(expected['identities'], [],
                    expected['invocation_id'], expected['attempt_index'])
                controls = copy.deepcopy(expected)
        except (ValueError, TypeError, RecursionError):
            out['comparison_errors'].append('EXPECTED_INVALID')

    events = None
    if events_bytes is None:
        out['missing_inputs'].append('events')
    elif type(events_bytes) is not bytes:
        out['report_errors'].append('EVENT_BYTES_TYPE')
    else:
        if controls is not None and hashlib.sha256(events_bytes).hexdigest() != controls['events_raw_sha256']:
            out['comparison_errors'].append('EVENT_RAW_MISMATCH')
        if len(events_bytes) > BYTE_LIMIT:
            out['missing_inputs'].append('events:LOCAL_BYTE_LIMIT')
        else:
            lines = events_bytes.split(b'\n')
            if lines[-1] == b'': lines.pop()
            if len(lines) > 32768:
                out['missing_inputs'].append('events:LOCAL_EVENT_LIMIT')
            else:
                try:
                    events = [_parse(line) for line in lines]
                except (ValueError, TypeError, RecursionError):
                    out['report_errors'].append('EVENT_JSON_INVALID')

    run_matches = False
    termination_complete = False
    if run_observation is None:
        out['missing_inputs'].append('run_observation')
    else:
        try:
            if (type(run_observation) is not dict or _tree(run_observation)
                    or set(run_observation) != {'invocation_id', 'attempt_index', 'events_raw_sha256', 'termination'}
                    or not digest(run_observation['events_raw_sha256'])):
                raise ValueError('run shape')
            local_observations._context(run_observation['invocation_id'], run_observation['attempt_index'])
            term = run_observation['termination']
            if type(term) is not dict: raise ValueError('termination shape')
            if term.get('state') == 'EXITED':
                if (set(term) != {'state', 'exit_code'} or type(term['exit_code']) is not int
                        or not -2147483648 <= term['exit_code'] <= 2147483647):
                    raise ValueError('exit shape')
                termination_complete = True
            elif (term.get('state') in ('UNKNOWN', 'ABORTED', 'NOT_STARTED')
                    and set(term) == {'state', 'reason_code'}
                    and type(term['reason_code']) is str and term['reason_code']):
                out['missing_inputs'].append('termination')
            else:
                raise ValueError('termination shape')
            if controls is not None:
                run_matches = all(run_observation[k] == controls[k] for k in
                    ('invocation_id', 'attempt_index', 'events_raw_sha256'))
                if not run_matches: out['comparison_errors'].append('RUN_BINDING_MISMATCH')
                if termination_complete and term['exit_code'] not in controls['expected_exit_codes']:
                    out['comparison_errors'].append('EXIT_CODE_MISMATCH')
        except (ValueError, TypeError, RecursionError):
            out['report_errors'].append('RUN_OBSERVATION_INVALID')

    if controls is not None and events is not None and 'EVENT_RAW_MISMATCH' not in out['comparison_errors']:
        comparison = local_observations.compare_events(controls['identities'], events,
            controls['invocation_id'], controls['attempt_index'])
        out['event_comparison'] = comparison
        if not comparison['finite_observations_match']:
            out['comparison_errors'].append('LOCAL_EVENT_COMPARISON_MISMATCH')
        out['local_event_consistency_match'] = (comparison['finite_observations_match']
            and run_matches and termination_complete and not any(out[k] for k in
                ('report_errors', 'comparison_errors', 'missing_inputs')))
    if out['report_errors'] or out['comparison_errors']:
        out['verdict'] = 'REJECT'
    return out
