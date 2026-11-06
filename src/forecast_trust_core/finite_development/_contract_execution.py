"""Finite contract/execution conjunction; preserves independent scope unknown."""
import hashlib
from . import _operation as _M
from .. import r4t_execution_content_v1 as _C

def consume_contract_execution(expected_base, base_records, mapping_bytes, mapping_sha256,
                               registry_bytes, component_records, pre_definition,
                               result_binding, schema_bytes, raw_artifacts):
    """Join declared finite scope; its independent completeness stays unknown."""
    records = (dict(base_records) if type(base_records) is dict and len(base_records) <= 32
               and all(type(k) is str for k in base_records) else {})
    contract = _M.consume(expected_base, records if records else base_records,
                          mapping_bytes, mapping_sha256, registry_bytes, component_records)
    report = records.get('r4t')
    if type(report) is not bytes:
        report = None
    content = _C.consume_predeclared_execution_content(
        pre_definition, result_binding, report, schema_bytes, raw_artifacts)
    errors = []

    def fail(code):
        if code not in errors:
            errors.append(code)

    bound = contract['operation_binding_verdict'] == 'LOCAL_OPERATION_MAPPING_VERIFIED'
    if bound and content['pre_definition_status'] == 'VALID_STRUCTURE':
        # Immutable raw snapshots already consumed above; no second resolution.
        try:
            objects = {name: _M._B.parse_json_strict(records[name]) for name in ('tc1', 'ib', 'vc', 'runtime')}
            tc = objects['tc1']; ib = objects['ib']; runtime = objects['runtime']
            bindings = pre_definition['bindings']
            if (bindings['test_definition_ref'] != _M._B._ref(tc)
                    or pre_definition['test_definition_raw_sha256'] != hashlib.sha256(records['tc1']).hexdigest()):
                fail('PRE_DEFINITION_TC_MISMATCH')
            if (bindings['runtime_profile_ref'] != _M._B._ref(runtime)
                    or bindings['runtime_profile_ref'] != tc['runtime_profile_ref']
                    or bindings['runtime_profile_ref'] != ib['runtime_profile_ref']):
                fail('PRE_RUNTIME_MISMATCH')
            if any(bindings[k] != ib[k] for k in
                   ('source_file_manifest_ref', 'package_artifact_ref', 'dependency_lock_ref')):
                fail('PRE_IMPLEMENTATION_BINDING_MISMATCH')
            def refkey(ref): return ref['object_id'], ref['content_sha256']
            if ({refkey(r) for r in bindings['component_contract_refs']}
                    != {refkey(r) for r in objects['vc']['component_contract_refs']}):
                fail('PRE_IMPLEMENTATION_BINDING_MISMATCH')
            commands = {row['command_id']: row['argv'] for row in tc['command_declarations']}
            invocations = pre_definition['invocations']
            if {row['command_id'] for row in invocations} != set(commands):
                fail('COMMAND_COVERAGE_MISMATCH')
            checks = {row['check_id']: row for row in contract['resolved_checks']}
            supplied_checks = set()
            fixtures = {refkey(r) for r in tc['fixture_refs']}
            for inv in invocations:
                if inv['argv'] != commands.get(inv['command_id']):
                    fail('COMMAND_ARGV_MISMATCH')
                if inv['executable_sha256'] != runtime['execution_engine']['executable_sha256']:
                    fail('EXECUTOR_MISMATCH')
                for instance in inv['instances']:
                    supplied_checks.add(instance['check_id'])
                    check = checks.get(instance['check_id'])
                    if (check is None or instance['operation_id'] != check['operation_id']
                            or inv['command_id'] not in check['command_ids']):
                        fail('CHECK_OPERATION_COMMAND_MISMATCH')
                    if not {refkey(r) for r in instance['fixture_refs']} <= fixtures:
                        fail('FIXTURE_NOT_DECLARED')
            if supplied_checks != set(checks):
                fail('CHECK_COVERAGE_MISMATCH')
        except (KeyError, ValueError, TypeError, RecursionError):
            fail('JOIN_INPUT_INVALID')
    rejected = contract['verdict'] == 'REJECT' or content['verdict'] == 'REJECT' or bool(errors)
    return {
        'verdict': 'REJECT' if rejected else 'UNRESOLVED',
        'finite_contract_execution_match': bound and content['finite_expectations_match'] and not errors,
        'join_errors': errors, 'contract_result': contract, 'execution_content_result': content,
        'comparison_scope': 'FINITE_SELECTED_CONTRACT_EXECUTION_ONLY',
        'independently_complete_product_universe': 'NOT_ESTABLISHED',
        'authority_and_applicability': 'NOT_ESTABLISHED', 'authenticated_chronology': 'NOT_ESTABLISHED',
        'actual_execution_truth': 'NOT_VERIFIED', 'pre_run_fixing': 'NOT_VERIFIED',
        'real_admission': 'NOT_READY', 'real_g02_g03': 'NOT_ESTABLISHED',
        'real_genesis_readiness': 'NOT_ESTABLISHED', 'prospective_eligible': False,
        'protocol_state_change': 'NONE',
    }
