"""Finite development R6 typed-check content, not authority or domain replay.

Import-safe extraction of report-check-content/content_codec.py. Frozen legacy
consumers and their pins remain unchanged. Catalog scope stays finite; a local
binding never establishes an independently complete report universe.
"""
from __future__ import annotations
import copy
import hashlib
import json
import re

TOKEN = re.compile(r'[A-Za-z0-9._:/-]+', re.ASCII)
DIGEST = re.compile(r'[0-9a-f]{64}', re.ASCII)
KINDS = frozenset({'TRUST_CORE_TEST_REPORT', 'GENESIS_ADVERSARIAL_REPORT',
                   'PROVIDER_REHEARSAL_REPORT', 'TARGET_SOURCE_PARSER_REPORT'})
OBS_KEYS = frozenset({'check_id', 'status', 'reason_code', 'support_refs',
                      'coverage', 'blocking_finding_refs'})
WIRE_KEYS = OBS_KEYS | {'report_context', 'missing_support_refs', 'missing_coverage'}


class ContentError(ValueError):
    """Rejected closed content or independently pinned local catalog."""


def _closed(value, keys, label):
    if type(value) is not dict or any(type(key) is not str for key in value) or set(value) != set(keys):
        raise ContentError(label + '_FIELD_SET')


def _token(value, label):
    if type(value) is not str or TOKEN.fullmatch(value) is None:
        raise ContentError(label + '_TOKEN')
    return value


def _ref(value):
    _closed(value, {'object_id', 'content_sha256'}, 'REF')
    _token(value['object_id'], 'OBJECT_ID')
    if type(value['content_sha256']) is not str or DIGEST.fullmatch(value['content_sha256']) is None:
        raise ContentError('REF_DIGEST')
    return value['object_id'], value['content_sha256']


def _member(value):
    _closed(value, {'dimension', 'member_ref'}, 'COVERAGE')
    if type(value['dimension']) is not str or value['dimension'] not in {'PROVIDER', 'TARGET', 'OPERATION'}:
        raise ContentError('COVERAGE_DIMENSION')
    return (value['dimension'],) + _ref(value['member_ref'])


def _set_keys(items, key):
    if type(items) is not list or len(items) > 2048:
        raise ContentError('SET_SIZE_OR_TYPE')
    keys = [key(item) for item in items]
    if keys != sorted(keys) or len(keys) != len(set(keys)):
        raise ContentError('NONCANONICAL_SET')
    return keys


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ContentError('DUPLICATE_JSON_KEY')
        result[key] = value
    return result


def _number(_):
    raise ContentError('CATALOG_NUMERIC_SCALAR')


def _catalog(raw, pin):
    if type(raw) is not bytes or len(raw) > 1048576:
        raise ContentError('CATALOG_SIZE_OR_TYPE')
    if type(pin) is not str or DIGEST.fullmatch(pin) is None or hashlib.sha256(raw).hexdigest() != pin:
        raise ContentError('CATALOG_IDENTITY_MISMATCH')
    try:
        catalog = json.loads(raw.decode('utf-8'), object_pairs_hook=_pairs,
                             parse_int=_number, parse_float=_number, parse_constant=_number)
    except (UnicodeError, RecursionError, ValueError) as exc:
        if isinstance(exc, ContentError):
            raise
        raise ContentError('CATALOG_PARSE_ERROR') from exc
    _closed(catalog, {'format', 'scope', 'report_kind', 'subject_ref',
                      'validator_contract_ref', 'content_profile_ref', 'checks'}, 'CATALOG')
    if catalog['format'] != 'FP_DEV_R6_CHECK_CATALOG_V1' or catalog['scope'] != 'FINITE_DEVELOPMENT_SCOPE_ONLY':
        raise ContentError('CATALOG_DEVELOPMENT_SCOPE')
    if type(catalog['report_kind']) is not str or catalog['report_kind'] not in KINDS:
        raise ContentError('CATALOG_REPORT_KIND')
    for field in ('subject_ref', 'validator_contract_ref', 'content_profile_ref'):
        _ref(catalog[field])
    checks = catalog['checks']
    if type(checks) is not list or not 1 <= len(checks) <= 1024:
        raise ContentError('CATALOG_CHECK_COUNT')
    ids = []
    for check in checks:
        _closed(check, {'check_id', 'required_support_refs', 'required_coverage'}, 'CHECK_DEFINITION')
        ids.append(_token(check['check_id'], 'CHECK_ID'))
        _set_keys(check['required_support_refs'], _ref)
        _set_keys(check['required_coverage'], _member)
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise ContentError('CATALOG_CHECK_ORDER_OR_DUPLICATE')
    return catalog


def _context(catalog, pin):
    return {'catalog_raw_sha256': pin, 'report_kind': catalog['report_kind'], 'stage': 'G6',
            **{field: catalog[field] for field in ('subject_ref', 'validator_contract_ref', 'content_profile_ref')}}


def _validate_context(value, expected):
    _closed(value, expected, 'CONTEXT')
    for field in ('catalog_raw_sha256', 'report_kind', 'stage'):
        _token(value[field], 'CONTEXT_' + field.upper())
    for field in ('subject_ref', 'validator_contract_ref', 'content_profile_ref'):
        _ref(value[field])
    if value != expected:
        raise ContentError('CONTEXT_MISMATCH')


def _observe(row, definition):
    _closed(row, OBS_KEYS, 'OBSERVATION')
    if _token(row['check_id'], 'CHECK_ID') != definition['check_id']:
        raise ContentError('CHECK_ID_MISMATCH')
    if type(row['status']) is not str or row['status'] not in {'PASS', 'FAIL', 'UNKNOWN'}:
        raise ContentError('CHECK_STATUS')
    _token(row['reason_code'], 'REASON_CODE')
    support = set(_set_keys(row['support_refs'], _ref))
    coverage = set(_set_keys(row['coverage'], _member))
    _set_keys(row['blocking_finding_refs'], _ref)
    required_support = {_ref(item) for item in definition['required_support_refs']}
    required_coverage = {_member(item) for item in definition['required_coverage']}
    if not support <= required_support or not coverage <= required_coverage:
        raise ContentError('UNDECLARED_SUPPORT_OR_COVERAGE')
    missing_support = [item for item in definition['required_support_refs'] if _ref(item) not in support]
    missing_coverage = [item for item in definition['required_coverage'] if _member(item) not in coverage]
    if row['status'] == 'PASS' and (missing_support or missing_coverage):
        raise ContentError('PASS_WITH_MISSING_INPUT')
    if row['status'] == 'PASS' and row['blocking_finding_refs']:
        raise ContentError('PASS_WITH_BLOCKING_FINDING')
    return missing_support, missing_coverage


def build_checks(catalog_bytes: bytes, catalog_sha256: str, observations: list[dict]) -> list[dict]:
    """Preserve supplied observations, adding context and computed missing sets."""
    catalog = _catalog(catalog_bytes, catalog_sha256)
    if type(observations) is not list or len(observations) != len(catalog['checks']):
        raise ContentError('CHECK_SET_MISMATCH')
    output = []
    for definition, row in zip(catalog['checks'], observations):
        missing_support, missing_coverage = _observe(row, definition)
        output.append(copy.deepcopy({**row, 'report_context': _context(catalog, catalog_sha256),
                                     'missing_support_refs': missing_support, 'missing_coverage': missing_coverage}))
    return output


def consume_checks(catalog_bytes: bytes, catalog_sha256: str, checks: list[dict]) -> dict:
    """Audit finite content; never grant protocol authority or domain truth.

    rejected_observations retains only rows whose observation passed _observe
    before a later ContentError. It is supplementary, not an exhaustive reject
    log or a source of bound failed/unknown checks. Missing sets there describe
    the local expected catalog comparison, not a verified report obligation.
    """
    catalog = _catalog(catalog_bytes, catalog_sha256)
    definitions = {item['check_id']: item for item in catalog['checks']}
    context = _context(catalog, catalog_sha256)
    out = {'well_formed_and_bound': False, 'hard_errors': [], 'missing_checks': [],
           'missing_inputs': [], 'missing_coverage': [], 'failed_checks': [], 'unknown_checks': [],
           'rejected_observations': [],
           'independently_complete_universe': 'NOT_ESTABLISHED', 'real_admission': 'NOT_READY',
           'prospective_eligible': False, 'protocol_state_change': 'NONE'}
    if type(checks) is not list or len(checks) > 1024:
        out['hard_errors'].append('WIRE_SIZE_OR_TYPE')
        checks = []
    ids = []
    for index, row in enumerate(checks):
        observed = None
        cid = row.get('check_id') if type(row) is dict and all(type(key) is str for key in row) else None
        if type(cid) is str:
            ids.append(cid)
        try:
            _closed(row, WIRE_KEYS, 'WIRE')
            cid = _token(row['check_id'], 'CHECK_ID')
            if cid not in definitions:
                raise ContentError('UNDECLARED_CHECK')
            observation = {key: row[key] for key in OBS_KEYS}
            missing_support, missing_coverage = _observe(observation, definitions[cid])
            # Safe observations survive a later rejection, without assigning a
            # wrong-context report's claimed status to this catalog's subject.
            observed = {'row_index': index, 'check_id': cid, 'reported_status': row['status'],
                        'reported_blocking_finding_refs': copy.deepcopy(row['blocking_finding_refs']),
                        'local_missing_support_refs': copy.deepcopy(missing_support),
                        'local_missing_coverage': copy.deepcopy(missing_coverage),
                        'context_bound': False, 'wire_valid': False,
                        'comparison_scope': 'LOCAL_EXPECTED_CATALOG_ONLY'}
            # Compare context and missing independently of the producer's serialization.
            _validate_context(row['report_context'], context)
            observed['context_bound'] = True
            _set_keys(row['missing_support_refs'], _ref)
            _set_keys(row['missing_coverage'], _member)
            if row['missing_support_refs'] != missing_support or row['missing_coverage'] != missing_coverage:
                out['hard_errors'].append(f'{index}:MISSING_DIAGNOSTIC_MISMATCH')
            if missing_support:
                out['missing_inputs'].append({'check_id': cid, 'refs': copy.deepcopy(missing_support)})
            if missing_coverage:
                out['missing_coverage'].append({'check_id': cid, 'members': copy.deepcopy(missing_coverage)})
            if row['status'] == 'FAIL':
                out['failed_checks'].append(cid)
            if row['status'] == 'UNKNOWN':
                out['unknown_checks'].append(cid)
        except ContentError as exc:
            out['hard_errors'].append(f'{index}:{exc}')
            if observed is not None:
                out['rejected_observations'].append({**observed, 'reason_code': str(exc)})
    out['missing_checks'] = [cid for cid in definitions if cid not in ids]
    if ids != list(definitions):
        out['hard_errors'].append('CHECK_SET_OR_ORDER_MISMATCH')
    out['well_formed_and_bound'] = not out['hard_errors']
    return out
