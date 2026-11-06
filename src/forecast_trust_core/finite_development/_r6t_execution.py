"""Finite R6T positive support; no protocol authority or eligibility lift."""
from copy import deepcopy
from . import _report as _R
from . import _contract_execution as _E

def consume_finite_r6t(expected_report, report_bytes, expected_base, base_records,
                       mapping_bytes, mapping_sha256, registry_bytes, component_records,
                       catalog_bytes, catalog_sha256, pre_definition, result_binding,
                       schema_bytes, raw_artifacts):
    """Support only a selected finite positive; independent completeness unknown."""
    records = (dict(base_records) if type(base_records) is dict and len(base_records) <= 32
               and all(type(k) is str for k in base_records) else base_records)
    base = (expected_base, records, mapping_bytes, mapping_sha256, registry_bytes, component_records)
    report = _R.consume(expected_report, report_bytes, *base, catalog_bytes, catalog_sha256)
    execution = _E.consume_contract_execution(*base, pre_definition, result_binding, schema_bytes, raw_artifacts)
    errors = []
    expected = catalog = None
    try:
        expected = _R._expected(expected_report)
    except (ValueError, TypeError, RecursionError):
        pass  # Actual report consumer retains the invalid-control diagnostic.
    try:
        catalog = _R._C._catalog(catalog_bytes, catalog_sha256)
    except (ValueError, TypeError, RecursionError):
        pass  # Actual report consumer retains the invalid-catalog diagnostic.
    if ((expected is not None and expected['report_kind'] != 'TRUST_CORE_TEST_REPORT')
            or (catalog is not None and catalog['report_kind'] != 'TRUST_CORE_TEST_REPORT')):
        errors.append('R6T_KIND_MISMATCH')
    operation = execution['contract_result']
    if catalog is not None and operation['operation_binding_verdict'] == 'LOCAL_OPERATION_MAPPING_VERIFIED':
        if ({x['check_id'] for x in catalog['checks']}
                != {x['check_id'] for x in operation['resolved_checks']}):
            errors.append('R6T_CHECK_COVERAGE_MISMATCH')
    rejected = report['verdict'] == 'REJECT' or execution['verdict'] == 'REJECT' or bool(errors)
    positive = (not rejected
                and report['local_report_binding_verdict'] == 'LOCAL_REPORT_CONTENT_BINDINGS_VERIFIED'
                and report['aggregate_check_result'] == 'VALID'
                and execution['finite_contract_execution_match'])
    return {
        'verdict': 'REJECT' if rejected else 'UNRESOLVED',
        'finite_r6t_positive_match': positive,
        'report_result': report, 'execution_result': execution, 'join_errors': errors,
        'comparison_scope': 'FINITE_SELECTED_R6T_POSITIVE_SUPPORT_ONLY',
        'real_missing': deepcopy(report['real_missing']),
        'unverified_obligations': deepcopy(report['unverified_obligations']),
        'independently_complete_product_universe': 'NOT_ESTABLISHED',
        'authority_and_applicability': 'NOT_ESTABLISHED',
        'authenticated_chronology': 'NOT_ESTABLISHED',
        'actual_execution_truth': 'NOT_VERIFIED', 'pre_run_fixing': 'NOT_VERIFIED',
        'invalid_reason_projection': 'NOT_VERIFIED',
        'real_admission': 'NOT_READY', 'real_g02_g03': 'NOT_ESTABLISHED',
        'real_genesis_readiness': 'NOT_ESTABLISHED', 'prospective_eligible': False,
        'protocol_state_change': 'NONE',
    }
