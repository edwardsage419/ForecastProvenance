"""Finite keyless M1 scientific kernels. Observations cannot set expectations.

The method is implemented here, independently of a Run claim or candidate code.
External availability/authentication are retained model facts, not real authority.
"""
from dataclasses import dataclass
from decimal import Decimal, localcontext
from .canonical import canonical_json, sha256_hex, require_decimal_string, require_utc_timestamp, verify_sealed_object
from .authority_primitives_v1 import ExactRef
from .core import Check, validate_point_in_time, validate_selection_control
from .lifecycle import validate_attempt_chain, validate_evaluation_cohort, validate_forecast_correction
from .evidence import validate_resolution_evidence, validate_resolution_state
from .genesis_sources import parse_released_decimal, select_baseline_first_release
from .replay_records_v1 import reduce_checks

NT_CHECKS = (
 'NT01_historical_bindings', 'NT01_policy_compatibility',
 'NT02_snapshot_recursive_bytes', 'NT02_source_vintage', 'NT02_input_availability',
 'NT03_method_configuration', 'NT03_environment_identity', 'NT03_deterministic_reexecution',
 'NT04_attempt_succession', 'NT04_failure_retry_budget', 'NT04_first_success_output',
 'NT05_precommitted_selection', 'NT05_control_class',
 'NT06_type_unit_decimal', 'NT06_cutoff_horizon_bindings', 'NT06_origin_preservation',
 'NT07_first_release_resolution', 'NT07_conflict_ambiguity', 'NT07_correction_withdrawal',
 'NT08_denominator', 'NT08_cohort_scoring')

class Unavailable(ValueError): pass

def ref(obj): return {k: obj[k] for k in ('object_id', 'content_sha256')}

def get(inputs, name):
    obj = inputs['objects'].get(name)
    if obj is None: raise Unavailable(name)
    return obj

def same_refs(a, b):
    aa = [ExactRef.from_mapping(x) for x in a]; bb = [ExactRef.from_mapping(x) for x in b]
    return len(aa) == len(set(aa)) and set(aa) == set(bb)

def measurement_rows(inputs, names):
    rows = []
    for name in names:
        capture = get(inputs, name)
        raw = inputs['raw'].get(capture['raw_ref']['object_id'])
        if raw is None: raise Unavailable('raw ' + name)
        from .canonical import parse_json_strict
        if sha256_hex(raw) != capture['raw_ref']['content_sha256']: raise ValueError('raw hash')
        obj = parse_json_strict(raw)
        if set(obj) != {'target_family','reference_period','release_stage','available_at','value','unit','origin'}: raise ValueError('raw schema')
        parse_released_decimal(obj['value']); require_utc_timestamp(obj['available_at'])
        if any(capture[k] != obj[k] for k in ('available_at','target_family','reference_period','release_stage','unit','origin')): raise ValueError('capture/raw binding')
        rows.append(obj)
    return rows

def run_last_observed(inputs, context):
    """Actual preceding first-release selection and Decimal output, no Run flags."""
    rows = measurement_rows(inputs, context['input_captures'])
    selected = select_baseline_first_release(rows, target_family=context['target_name'],
        previous_reference_period=context['previous_period'], information_cutoff=context['cutoff'])
    available = [r for r in rows if r['available_at'] <= context['cutoff']]
    if not available or selected['available_at'] != max(r['available_at'] for r in available): raise ValueError('LAST_AVAILABLE disagreement')
    return parse_released_decimal(selected['value']).canonical_decimal

@dataclass(frozen=True)
class ScientificExecution:
    target_name: str
    prediction: str | None
    selected_raw_ref: dict | None
    squared_error: str | None


def evaluate_scientific_slot(inputs, context, observed_runtime):
    """Pure raw semantic evaluation; context is independently verifier-derived."""
    checks = []
    prediction, score = None, None
    def record(name, fn):
        try:
            value = fn()
            if isinstance(value, tuple):
                status = reduce_checks(value); checks.append(Check(name, status, 'OK' if status == 'PASS' else next(c.reason_code for c in value if c.status != 'PASS')))
            else: checks.append(Check(name, 'PASS' if value is True else 'FAIL', 'OK' if value is True else name.upper() + '_MISMATCH'))
        except Unavailable:
            checks.append(Check(name, 'UNKNOWN', 'SCIENTIFIC_EVIDENCE_UNAVAILABLE'))
        except (ValueError, KeyError, TypeError, AttributeError, IndexError, ArithmeticError):
            checks.append(Check(name, 'FAIL', name.upper() + '_INVALID'))
        except Exception as exc:
            checks.append(Check(name, 'UNKNOWN', 'SCIENTIFIC_KERNEL_UNAVAILABLE_' + type(exc).__name__))
    def objects(): return [get(inputs,n) for n in ('run','snapshot','attempt_ledger','resolution_selection','cohort','selection')]
    def historical():
        r,s,a,o,c,p = objects()
        return r['subject_ref'] == context['subject'] and all(x['slot_ref'] == context['slot_ref'] for x in (r,s,a,o,p)) and r['plan_ref'] == context['plan_ref'] and r['target_ref'] == context['target_ref'] and r['method_ref'] == context['method_ref'] and r['snapshot_ref'] == ref(s) and r['attempt_ledger_ref'] == ref(a) and r['selection_ref'] == ref(p)
    record('NT01_historical_bindings', historical)
    record('NT01_policy_compatibility', lambda: get(inputs,'run')['policy_refs'] == context['policy_refs'] and context['method']['configuration'] == {'arithmetic':'DECIMAL','selection':'LAST_AVAILABLE'} and context['resolution_policy']['vintage'] == 'FIRST_OFFICIAL_RELEASE' and context['target']['method'] == context['method']['name'] and context['target']['resolution'] == context['resolution_policy']['name'])
    def closure():
        visited, active, leaves = set(), set(), []
        by_ref = {ExactRef.from_mapping(ref(o)): (name,o) for name,o in inputs['objects'].items() if o is not None}
        def walk(reference):
            pair = ExactRef.from_mapping(reference)
            if pair in active: raise ValueError('snapshot cycle')
            if pair in visited: raise ValueError('duplicate snapshot edge')
            if pair not in by_ref: raise Unavailable('snapshot node')
            name, obj = by_ref[pair]
            if not verify_sealed_object(obj): raise ValueError('snapshot seal')
            visited.add(pair); active.add(pair)
            if obj['object_type'] == 'SyntheticEvidenceSnapshot':
                if not obj['members']: raise ValueError('empty snapshot')
                for child in obj['members']: walk(child)
            elif obj['object_type'] == 'SyntheticMeasurementCapture':
                measurement_rows(inputs,[name]); leaves.append(reference)
            else: raise ValueError('snapshot member type')
            active.remove(pair)
        walk(ref(get(inputs,'snapshot')))
        return same_refs(leaves,context['input_capture_refs']) and {p.to_dict()['object_id'] for p in visited} == set(context['snapshot_node_ids'])
    record('NT02_snapshot_recursive_bytes', closure)
    def vintage():
        return all(r['target_family'] == context['target_name'] and r['release_stage'] == 'FIRST' and r['reference_period'] in context['input_periods'] and r['unit'] == context['target']['unit'] and r['origin'] == 'RETROSPECTIVE_FIXTURE' for r in measurement_rows(inputs,context['input_captures'])) and all(get(inputs,n)['source_contract_ref'] == context['measurement_ref'] for n in context['input_captures'])
    record('NT02_source_vintage', vintage)
    record('NT02_input_availability', lambda: validate_point_in_time(measurement_rows(inputs,context['input_captures']),context['cutoff']).checks)
    record('NT03_method_configuration', lambda: get(inputs,'run')['configuration'] == context['method']['configuration'] and get(inputs,'selection')['configuration'] == context['method']['configuration'])
    def environment():
        if observed_runtime is None: raise Unavailable('runtime')
        return get(inputs,'run')['runtime'] == context['runtime'] == observed_runtime
    record('NT03_environment_identity', environment)
    def reexecution():
        nonlocal prediction
        # Prerequisites are actual raw execution checks; no outcome bytes are inputs.
        if any(c.status != 'PASS' for c in checks if c.check_id.startswith(('NT02','NT03_method','NT03_environment'))): raise Unavailable('execution prerequisite')
        prediction = run_last_observed(inputs,context)
        return prediction == get(inputs,'run')['prediction'] == get(inputs,'issued')['value']
    record('NT03_deterministic_reexecution', reexecution)
    def attempts():
        ledger = get(inputs,'attempt_ledger')
        if not same_refs(ledger['attempt_refs'],context['attempt_refs']): raise ValueError('independent attempt scope')
        return [get(inputs,n) for n in context['attempt_names']]
    def succession():
        aa=attempts(); ledger=get(inputs,'attempt_ledger')
        if ledger['head_ref'] != ref(aa[-1]): return False
        for i,a in enumerate(aa):
            require_utc_timestamp(a['started_at']); require_utc_timestamp(a['finished_at'])
            if a['sequence'] != i or a['predecessor_ref'] != ('NONE' if i==0 else ref(aa[i-1])) or a['slot_ref'] != context['slot_ref'] or a['method_ref'] != context['method_ref'] or not(context['window_open'] <= a['started_at'] <= a['finished_at'] <= context['window_close']): return False
            if i and aa[i-1]['finished_at'] > a['started_at']: return False
            if a['status'] not in ('SUCCESS','FAILED'): return False
        return bool(aa)
    record('NT04_attempt_succession', succession)
    def retry():
        aa=attempts()
        native=[{'attempt_id':a['object_id'],'retry_of_or_none': None if a['predecessor_ref'] == 'NONE' else a['predecessor_ref']['object_id'], 'failure_code_or_none':a['failure_code'], 'terminal_status':'SUCCEEDED' if a['status']=='SUCCESS' else 'FAILED','issuance_eligible':a['issuance_eligible']} for a in aa]
        rules=context['method']['retry']
        result=validate_attempt_chain(native,{'max_attempts':rules['budget'], 'retry_eligible_failure_codes':rules['eligible_failures']}).checks
        extra=all((a['failure_code'] == 'NONE' and isinstance(a['output_ref'],dict)) if a['status']=='SUCCESS' else (a['failure_code'] != 'NONE' and a['output_ref'] == 'NONE' and not a['issuance_eligible']) for a in aa)
        return result+(Check('terminal-failure','PASS' if extra else 'FAIL','TERMINAL_FAILURE_ACCOUNTING_INVALID'),)
    record('NT04_failure_retry_budget',retry)
    def first_success():
        aa=attempts(); success=[a for a in aa if a['status']=='SUCCESS']
        issued=get(inputs,'issued'); require_utc_timestamp(issued['issued_at'])
        if success: require_utc_timestamp(success[0]['finished_at'])
        return ref(issued)==context['issued_ref'] and bool(success) and success[0]['finished_at'] <= issued['issued_at'] and get(inputs,'attempt_ledger')['selected_attempt_ref'] == ref(success[0]) and success[0]['output_ref'] == context['issued_ref'] and success[0]['issuance_eligible'] is True and all(a['issuance_eligible'] is False for a in success[1:]) and get(inputs,'run')['attempt_ref'] == ref(success[0])
    record('NT04_first_success_output', first_success)
    def selection():
        p=get(inputs,'selection'); require_utc_timestamp(p['committed_at'])
        return p['committed_at'] <= context['plan_deadline'] and p['rule']=='FIRST_SUCCESS_LAST_AVAILABLE' and p['method_ref']==context['method_ref'] and p['policy_refs']==context['policy_refs'] and p['origin']=='SYNTHETIC_ONLY'
    record('NT05_precommitted_selection', selection)
    def control():
        if get(inputs,'run')['control_class'] != context['method']['control'] or context['method']['control'] != 'DETERMINISTIC_REPLAY': return False
        if prediction is None: raise Unavailable('actual deterministic replay')
        return validate_selection_control({'selection_control_class':context['method']['control']},{'replay_verified':prediction is not None and prediction == get(inputs,'run')['prediction'] == get(inputs,'issued')['value']}).checks
    record('NT05_control_class', control)
    def typed():
        r=get(inputs,'run'); f=get(inputs,'issued'); require_decimal_string(r['prediction']); require_decimal_string(f['value'])
        return r['type'] == context['target']['prediction_type'] == 'DECIMAL' and r['unit'] == f['unit'] == context['target']['unit'] and context['output_schema']=='continuous_scalar_forecast_v1'
    record('NT06_type_unit_decimal', typed)
    def horizon():
        issued=get(inputs,'issued')
        for timestamp in (issued['issued_at'],context['cutoff'],context['window_open'],context['window_close'],context['barrier']): require_utc_timestamp(timestamp)
        return get(inputs,'run')['information_cutoff']==context['cutoff'] and get(inputs,'snapshot')['information_cutoff']==context['cutoff'] and get(inputs,'run')['reference_period']==context['period'] and get(inputs,'run')['outcome_barrier']==context['barrier'] and issued['slot_ref']==context['slot_ref'] and context['cutoff'] < issued['issued_at'] and context['window_open'] <= issued['issued_at'] <= context['window_close'] < context['barrier']
    record('NT06_cutoff_horizon_bindings',horizon)
    record('NT06_origin_preservation',lambda: get(inputs,'run')['origin']==get(inputs,'issued')['origin']==get(inputs,'selection')['origin']=='SYNTHETIC_ONLY' and all(r['origin']=='RETROSPECTIVE_FIXTURE' for r in measurement_rows(inputs,context['input_captures'])))
    def resolution():
        o=get(inputs,'resolution_selection'); rawrows=measurement_rows(inputs,context['outcome_captures']); matches=[r for r in rawrows if r['target_family']==context['target_name'] and r['reference_period']==context['period'] and r['release_stage']=='FIRST']
        if len(matches)!=1: return False
        first=matches[0]; rr=get(inputs,'resolution'); require_utc_timestamp(first['available_at'])
        valid=validate_resolution_evidence({'vintage_selection':context['resolution_policy']['vintage'],'resolution_deadline':context['resolution_deadline']},{'selected_vintage':o['selected_vintage'],'resolved_at':rr['resolved_at']}).checks
        ok=o['selected_raw_ref']==get(inputs,context['outcome_captures'][0])['raw_ref'] and first['available_at']==context['barrier'] and rr['resolved_at']==first['available_at'] and parse_released_decimal(rr['value']).canonical_decimal==parse_released_decimal(first['value']).canonical_decimal and first['unit']==context['target']['unit'] and rr['slot_ref']==context['slot_ref'] and rr['issued_forecast_ref']==context['issued_ref'] and rr['origin']==first['origin']=='RETROSPECTIVE_FIXTURE'
        return valid+(Check('first-release-binding','PASS' if ok else 'FAIL','FIRST_RELEASE_RESOLUTION_BINDING_INVALID'),)
    record('NT07_first_release_resolution', resolution)
    def conflicts():
        o=get(inputs,'resolution_selection'); rr=get(inputs,'resolution')
        expected=validate_resolution_state(ambiguous=o['ambiguous'],ambiguity_policy=context['resolution_policy']['ambiguity'],resolution_state=rr['status']).checks
        rows=measurement_rows(inputs,context['outcome_captures']); values={r['value'] for r in rows if r['release_stage']=='FIRST' and r['reference_period']==context['period']}
        consistent=(len(values)==1 and not o['conflict_refs'] and o['ambiguous'] is False and rr['status']=='RESOLVED') or (rr['status']=='UNRESOLVED' and (o['ambiguous'] or len(values)>1))
        return expected+(Check('resolution-conflict','PASS' if consistent else 'FAIL','UNRESOLVED_CONFLICT_SUPPRESSED'),)
    record('NT07_conflict_ambiguity',conflicts)
    def corrections():
        o=get(inputs,'resolution_selection'); cohort=get(inputs,'cohort')
        if not same_refs(o['correction_refs'],context['correction_refs']) or not same_refs(o['withdrawal_refs'],context['withdrawal_refs']): return False
        corrections=[get(inputs,name) for name in context['correction_names']]
        withdrawals=[get(inputs,name) for name in context.get('withdrawal_names',())]
        if not same_refs([ref(c) for c in corrections],context['correction_refs']) or not same_refs([ref(w) for w in withdrawals],context['withdrawal_refs']): return False
        for correction in corrections:
            vv=validate_forecast_correction(correction,original_forecast_ref=context['issued_ref'],correction_policy={'substantive_field_set':['value','unit','origin']})
            if not vv.valid or correction.get('origin')!='SYNTHETIC_ONLY': return False
            if correction['correction_type']=='SUBSTANTIVE_REPLACEMENT':
                replacements=[get(inputs,name) for name in context.get('replacement_names',())]
                matches=[r for r in replacements if ref(r)==correction['replacement_forecast_ref_or_none']]
                if len(matches)!=1: raise Unavailable('replacement forecast')
                replacement=matches[0]
                require_decimal_string(replacement['value'])
                if replacement['object_type']!='SyntheticIssuedForecast' or replacement['origin']!='SYNTHETIC_ONLY' or replacement['slot_ref']!=context['slot_ref'] or replacement['method_ref']!=context['method_ref'] or replacement['unit']!=context['target']['unit']: return False
        for withdrawal in withdrawals:
            require_utc_timestamp(withdrawal['withdrawn_at'])
            if withdrawal['action']!='WITHDRAW' or withdrawal['forecast_ref']!=context['issued_ref'] or withdrawal['origin']!='SYNTHETIC_ONLY' or withdrawal['withdrawn_at'] < get(inputs,'issued')['issued_at']: return False
        return context['resolution_policy']['corrections']=='PRESERVE_ORIGINAL' and context['issued_ref'] in cohort['included_forecast_refs'] and get(inputs,'resolution')['issued_forecast_ref']==context['issued_ref']
    record('NT07_correction_withdrawal',corrections)
    def denominator():
        cohort=get(inputs,'cohort')
        return validate_evaluation_cohort(context['all_issued_refs'],cohort['included_forecast_refs']).checks + (Check('slot-denominator','PASS' if same_refs(cohort['expected_slot_refs'],context['all_slot_refs']) and cohort['denominator']==len(context['all_slot_refs']) else 'FAIL','COHORT_DENOMINATOR_MISMATCH'),)
    record('NT08_denominator',denominator)
    def scoring():
        nonlocal score
        if prediction is None or any(c.status != 'PASS' for c in checks if c.check_id.startswith(('NT07','NT08_denominator'))): raise Unavailable('score prerequisite')
        cohort=get(inputs,'cohort'); observed=parse_released_decimal(get(inputs,'resolution')['value']).canonical_decimal
        with localcontext() as decimal_context:
            decimal_context.prec=50
            value=(Decimal(prediction)-Decimal(observed))**2
            score=parse_released_decimal(format(value,'f')).canonical_decimal
        return context['resolution_policy']['scoring']=='SQUARED_ERROR' and cohort['scoring']=='SQUARED_ERROR' and cohort['scores'][context['target_name']]==score and cohort['scored_forecast_refs']==cohort['included_forecast_refs']
    record('NT08_cohort_scoring',scoring)
    execution=ScientificExecution(context['target_name'],prediction, get(inputs,context['input_captures'][-1])['raw_ref'] if prediction else None, score)
    return tuple(checks),execution
