"""Finite five-report/execution composition; no protocol authority."""
from copy import deepcopy
from . import _report_set as _SET
from . import _r6t_execution as _R6T

_KIND = "TRUST_CORE_TEST_REPORT"

def consume_finite_report_set(expected_set, reports, catalogs, expected_base, base_records,
                              mapping_bytes, mapping_sha256, registry_bytes, component_records,
                              pre_definition, result_binding, schema_bytes, raw_artifacts):
    """Consume every supplied R6T against the same immutable R4T byte snapshot."""
    records = (dict(base_records) if type(base_records) is dict and len(base_records) <= 32
               and all(type(k) is str for k in base_records) else base_records)
    if records is not base_records and records.get('r4t', False) is None:
        del records['r4t']  # One shared absent-input representation for both consumers.
    rows = reports
    if type(reports) is list and len(reports) <= 16:
        rows = [dict(row) if type(row) is dict and all(type(k) is str for k in row)
                else row for row in reports]
    base = (expected_base, records, mapping_bytes, mapping_sha256, registry_bytes, component_records)
    content = (pre_definition, result_binding, schema_bytes, raw_artifacts)
    report_set = _SET.consume(expected_set, rows, catalogs, *base)
    expected = {}
    try:
        _SET._R._J._plain(expected_set)
        if type(expected_set) is dict and type(expected_set.get('r6_expected')) is dict:
            expected = expected_set['r6_expected'].get(_KIND, {})
    except (ValueError, TypeError, RecursionError):
        pass  # The set consumer retains invalid comparison-control diagnostics.
    catalog_bytes = catalog_sha256 = None
    if (type(catalogs) is dict and len(catalogs) <= 4
            and all(type(k) is str for k in catalogs) and _KIND in catalogs):
        try:
            c = catalogs[_KIND]
            _SET._C._closed(c, {'bytes', 'sha256'}, 'CATALOG_RECORD')
            catalog_bytes, catalog_sha256 = c['bytes'], c['sha256']
        except (ValueError, TypeError):
            pass
    results = []
    if type(rows) is list and len(rows) <= 16:
        for index, row in enumerate(rows):
            try:
                _SET._C._closed(row, {'kind', 'bytes'}, 'REPORT_RECORD')
                _SET._C._token(row['kind'], 'KIND')
                if type(row['bytes']) is not bytes and row['bytes'] is not None:
                    raise ValueError('bytes')
            except (ValueError, TypeError):
                continue
            if row['kind'] == _KIND:
                result = _R6T.consume_finite_r6t(expected, row['bytes'], *base,
                                               catalog_bytes, catalog_sha256, *content)
                results.append({'index': index, 'status': 'MISSING_REPORT' if row['bytes'] is None else 'CONSUMED',
                                'result': result})
    if not results:
        # Missing/invalid report input cannot hide an independently visible run failure.
        result = _R6T.consume_finite_r6t(expected, None, *base,
                                       catalog_bytes, catalog_sha256, *content)
        results.append({'index': None, 'status': 'MISSING_REPORT', 'result': result})
    rejected = report_set['verdict'] == 'REJECT' or any(r['result']['verdict'] == 'REJECT' for r in results)
    positive = (not rejected
                and report_set['local_set_binding_verdict'] == 'LOCAL_REQUIRED_REPORT_SET_BINDINGS_VERIFIED'
                and len(results) == 1 and results[0]['status'] == 'CONSUMED'
                and results[0]['result']['finite_r6t_positive_match'])
    return {
        'verdict': 'REJECT' if rejected else 'UNRESOLVED', 'finite_report_set_match': positive,
        'set_result': report_set, 'r6t_results': results,
        'comparison_scope': 'FINITE_SELECTED_FIVE_REPORT_EXECUTION_SUPPORT_ONLY',
        'real_missing': deepcopy(report_set['real_missing']),
        'unverified_obligations': deepcopy(report_set['unverified_obligations']),
        'independently_complete_product_universe': 'NOT_ESTABLISHED',
        'authority_and_applicability': 'NOT_ESTABLISHED', 'authenticated_chronology': 'NOT_ESTABLISHED',
        'actual_execution_truth': 'NOT_VERIFIED', 'strong_truth': 'NOT_VERIFIED',
        'real_admission': 'NOT_READY', 'real_g02_g03': 'NOT_ESTABLISHED',
        'real_genesis_readiness': 'NOT_ESTABLISHED', 'prospective_eligible': False,
        'protocol_state_change': 'NONE',
    }
