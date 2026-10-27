"""One offline entry for finite economic-data observations and keyless bindings."""
import argparse
from copy import deepcopy
from datetime import date
from decimal import Decimal, localcontext
import json
from pathlib import Path
import re
import subprocess
import sys

CASES = json.loads((Path(__file__).resolve().parent/"catalog.json").read_text())

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
# Existing bundled runtime, already used by the retained PDF consumer; no install/search.
PDF_PYTHON = Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
STATUSES = {'OBSERVED', 'MISSING', 'REJECTED', 'UNAVAILABLE', 'UNSUPPORTED'}


def run_case(name, input_root=None, repository_root=None):
    if name not in CASES:
        return {'id': name, 'status': 'UNSUPPORTED', 'error': 'UNSUPPORTED_CASE'}
    case = CASES[name]
    base = {'id': name, 'title': case['title'], 'scope': case['scope']}
    runtime = PDF_PYTHON if case['kind'] in {'u3', 'u3_a1', 'gdp_news', 'cpi_archive_pdf', 'calendar_predecessors', 'q1_scope'} else Path(sys.executable)
    if not runtime.is_file():
        return dict(base, status='UNAVAILABLE', error='MISSING_RUNTIME')
    request = {'case': name, 'repository_root': str(Path(repository_root or ROOT).absolute()),
               'input_root': str(Path(input_root).absolute()) if input_root is not None else None}
    try:
        proc = subprocess.run([str(runtime), '-I', '-B', str(HERE/'worker.py')],
                              input=json.dumps(request), capture_output=True, text=True, timeout=30)
        if proc.returncode != 0:
            return dict(base, status='REJECTED', error='WORKER_FAILED')
        result = json.loads(proc.stdout)
        if (type(result) is not dict or result.get('id') != name or result.get('status') not in STATUSES
            or (result['status'] == 'OBSERVED' and type(result.get('observations')) is not dict)):
            return dict(base, status='REJECTED', error='INVALID_WORKER_RESULT')
        return result
    except (OSError, subprocess.TimeoutExpired):
        return dict(base, status='UNAVAILABLE', error='RUNTIME_FAILED')
    except (ValueError, TypeError):
        return dict(base, status='REJECTED', error='INVALID_WORKER_RESULT')


def build_report(results):
    cases = []
    for result in results:
        if type(result) is not dict or result.get('status') not in STATUSES:
            cases.append({'id': result.get('id', 'unknown') if type(result) is dict else 'unknown',
                          'status': 'REJECTED', 'error': 'INVALID_RESULT'})
        else:
            cases.append(deepcopy(result))
    return {'mode': 'FINITE_OFFLINE_DEVELOPMENT_OBSERVATIONS', 'cases': cases,
            'overall': 'UNRESOLVED', 'real_admission': 'NOT_READY',
            'real_g02_g03': 'NOT_ESTABLISHED', 'real_genesis_readiness': 'NOT_ESTABLISHED',
            'prospective_eligible': False, 'protocol_state_change': 'NONE',
            'coverage': 'EXPLICIT_SUPPORTED_SAMPLES_ONLY_NOT_COMPLETE_HISTORY',
            'authenticated_availability': 'NOT_ESTABLISHED'}


def compare_gdp(input_root=None):
    """Derive differences only after the existing fixed-file GDP check succeeds."""
    result = deepcopy(run_case('gdp-2026-vintages', input_root))
    if result['status'] != 'OBSERVED':
        result.pop('observations', None)
        return result
    case = CASES['gdp-2026-vintages']
    releases = {
        ('2026-Q1', 'Advance', '2026-04-30'), ('2026-Q1', 'Second', '2026-05-28'),
        ('2026-Q1', 'Third', '2026-06-25'), ('2026-Q1', 'Revised', '2026-09-30'),
        ('2026-Q2', 'Advance', '2026-07-30'), ('2026-Q2', 'Second', '2026-08-26'),
        ('2026-Q2', 'Third', '2026-09-30'),
    }
    try:
        data = result['observations']
        versions = data['versions']
        if len(versions) != 7 or {
            (v['reference_quarter'], v['stage'], v['publication_date']) for v in versions
        } != releases:
            raise ValueError('incomplete supported declarations')
        for v in versions:
            if v['raw_sha256'] != case['inputs'][0]['sha256'] or v['sheet'] != 'Vintage History':
                raise ValueError('wrong vintage source')
            for field in ('quarter_cell', 'stage_cell', 'value_cell', 'date_cell'):
                if not isinstance(v[field], str) or not re.fullmatch(r'[A-Z]+[1-9][0-9]*', v[field]):
                    raise ValueError('missing source position')
            for field in ('canonical_decimal', 'raw_lexical'):
                value = v[field]
                if (not isinstance(value, str) or len(value) > 32
                    or not re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?', value)):
                    raise ValueError('not a bounded decimal declaration')
            if Decimal(v['canonical_decimal']) != Decimal(v['raw_lexical']):
                raise ValueError('inconsistent numeric declaration')
        bindings = data['advance_bindings']
        if len(bindings) != 2:
            raise ValueError('missing advance binding')
        by_quarter = {b['vintage']['reference_quarter']: b for b in bindings}
        if set(by_quarter) != {'2026-Q1', '2026-Q2'}:
            raise ValueError('wrong advance binding')
        for index, quarter in ((1, '2026-Q1'), (2, '2026-Q2')):
            b = by_quarter[quarter]
            v = next(v for v in versions if v['reference_quarter'] == quarter and v['stage'] == 'Advance')
            if b['vintage'] != v or b['archive']['raw_sha256'] != case['inputs'][index]['sha256']:
                raise ValueError('wrong bound source')
            if any(b['archive'][field] != v[field] for field in
                   ('reference_quarter', 'publication_date', 'canonical_decimal')):
                raise ValueError('inconsistent advance declarations')
        def decimal_text(number):
            if number == 0:
                return '0'
            text = format(number, 'f')
            return text.rstrip('0').rstrip('.') if '.' in text else text
        groups = []
        # More than enough precision for the bounded decimal declarations above.
        with localcontext() as context:
            context.prec = 80
            for quarter in ('2026-Q1', '2026-Q2'):
                rows = sorted((v for v in versions if v['reference_quarter'] == quarter),
                              key=lambda v: v['publication_date'])
                first = Decimal(rows[0]['canonical_decimal'])
                previous = None
                output = []
                for row in rows:
                    value = Decimal(row['canonical_decimal'])
                    output.append(dict(row,
                        change_from_previous_pp=None if previous is None else decimal_text(value-previous),
                        change_from_first_listed_pp=decimal_text(value-first)))
                    previous = value
                groups.append({'reference_quarter': quarter, 'rows': output})
        data['comparison'] = {
            'quarters': groups, 'value_unit': 'PERCENT_CHANGE_FROM_PRECEDING_PERIOD_AS_DECLARED',
            'difference_unit': 'PERCENTAGE_POINTS',
            'difference_basis': 'SUBTRACTION_OF_LISTED_DECIMAL_VALUES_NOT_UNROUNDED_REVISION',
            'unrounded_revisions': 'NOT_ESTABLISHED_BY_DISPLAY_VALUE_SUBTRACTION',
            'coverage': 'SEVEN_RETAINED_DECLARATIONS_ONLY_NOT_COMPLETE_REVISION_HISTORY',
            'evidence_class': 'CURRENT_RETROSPECTIVE_VINTAGE_DECLARATIONS_WITH_TWO_ADVANCE_JOINS',
            'sources': deepcopy(case['inputs']),
            'historical_first_bytes': 'NOT_ESTABLISHED',
            'authenticated_availability': 'NOT_ESTABLISHED',
        }
    except (KeyError, TypeError, ValueError, ArithmeticError, StopIteration):
        result.pop('observations', None)
        result.update(status='REJECTED', error='INVALID_GDP_COMPARISON_INPUT')
    return result


def compare_gdp_with_news(input_root=None):
    """Join two checked carriers' finite claims; all failures keep their findings."""
    base = compare_gdp(input_root)
    pdf = run_case('gdp-news-pdfs', input_root)
    failed = [r for r in (base, pdf) if r['status'] != 'OBSERVED']
    if failed:
        rank = {'REJECTED': 0, 'UNSUPPORTED': 0, 'MISSING': 1, 'UNAVAILABLE': 2}
        primary = min(failed, key=lambda r: rank[r['status']])
        result = {k: v for k, v in base.items() if k != 'observations'}
        result.update(status=primary['status'], error=primary.get('error', 'GDP_NEWS_NOT_VERIFIED'))
        result['findings'] = [dict(f, case=r['id']) for r in failed for f in r.get('findings',
            [{'item': r['id'], 'status': r['status'], 'error': r.get('error', 'CASE_FAILED')}])]
        return result
    try:
        versions = base['observations']['versions']
        rows = pdf['observations']['declarations']
        expected = {(v['reference_quarter'], v['stage']): v for v in versions}
        actual = {(v['reference_quarter'], v['stage']): v for v in rows}
        if len(rows) != 7 or set(actual) != set(expected):
            raise ValueError('incomplete PDF declaration mapping')
        matches = []
        for identity, v in expected.items():
            declaration = actual[identity]
            if declaration['canonical_decimal'] != v['canonical_decimal']:
                raise ValueError('PDF/vintage value mismatch')
            matches.append({'vintage': deepcopy(v), 'pdf': deepcopy(declaration)})
        base['observations']['news_pdf_support'] = dict(deepcopy(pdf['observations']), matches=matches)
    except (KeyError, TypeError, ValueError):
        base.pop('observations', None)
        base.update(status='REJECTED', error='GDP_NEWS_DECLARATION_MISMATCH')
    return base


def compare_cpi_carriers(copy, archive):
    """Compare finite declarations; retain all child failures without source upgrades."""
    result = {'source_independence': 'NOT_ESTABLISHED',
              'coverage': 'SHARED_FIRST_PAGE_DECLARATIONS_ONLY_NOT_FULL_TABLES',
              'authenticated_availability': 'NOT_ESTABLISHED', 'findings': []}
    failed = [row for row in (copy, archive) if row['status'] != 'OBSERVED']
    if failed:
        rank = {'REJECTED': 0, 'UNSUPPORTED': 0, 'MISSING': 1, 'UNAVAILABLE': 2}
        result['status'] = min(failed, key=lambda row: rank[row['status']])['status']
        result['findings'] = [dict(f, case=row['id']) for row in failed for f in row.get('findings',
            [{'item': row['id'], 'status': row['status'], 'error': row.get('error', 'CASE_FAILED')}])]
        return result
    fields = ('reference_month', 'publication_date_declaration', 'release_id', 'target',
              'measure', 'adjustment', 'display_value', 'unadjusted_yearly_change')
    try:
        left, right = copy['observations'], archive['observations']
        if any(type(left[field]) is not str or type(right[field]) is not str
               or left[field] != right[field] for field in fields):
            raise ValueError('shared declaration mismatch')
        result.update(status='OBSERVED', matched_declarations={field: left[field] for field in fields})
    except (KeyError, TypeError, ValueError):
        result.update(status='REJECTED', findings=[{'item': 'shared-cpi-declarations',
                      'status': 'REJECTED', 'error': 'CPI_CARRIER_DECLARATION_MISMATCH'}])
    return result


def bind_predecessor_calendars(assessment, research):
    """Join already-consumed D218/D208 planning records, without reads or admission.

    Fixed keys below describe this user-selected development comparison only.
    Neither those keys nor agreement of two outputs proves a mandatory universe.
    """
    result = {'id': 'q1-predecessor-calendar-binding', 'bindings': [], 'findings': [],
              'comparison_scope': 'D218_OUTSIDE_WINDOW_TO_D208_PLANNING_DECLARATIONS_ONLY',
              'required_predecessor_count': 3, 'matched_predecessor_count': 0,
              'value_and_authenticated_availability': 'NOT_SUPPLIED',
              'actual_required_cycle_or_slot_universe': 'NOT_ESTABLISHED',
              'actual_source_admission_established': False, 'utc_deadline_computed': False,
              'real_admission': 'NOT_READY', 'protocol_state_change': 'NONE'}
    frontier = {('GDP', '2026-Q3'), ('U3', '2026-11'), ('CPI', '2026-11')}
    expected = {('GDP', '2026-Q4'): '2026-Q3',
                **{(s, p): prev for s in ('CPI', 'U3') for p, prev in
                   (('2026-12', '2026-11'), ('2027-01', '2026-12'), ('2027-02', '2027-01'))}}

    def common(child, name):
        if child['id'] != name or child['scope'] != CASES[name]['scope']:
            raise ValueError('wrong child identity/scope')
        data = child['observations']
        for key, value in (('real_admission', 'NOT_READY'), ('protocol_state_change', 'NONE'),
                           ('operational_bindings_established', 0)):
            if type(data[key]) is not type(value) or data[key] != value:
                raise ValueError('upgraded child')
        for key in ('actual_source_admission_established', 'authenticated_availability_established',
                    'utc_deadline_computed'):
            if data[key] is not False:
                raise ValueError('upgraded child evidence')
        return data

    def checked_assessment():
        data = common(assessment, 'q1-2027-read-only-assessment')
        if data['read_only_scope_selected'] is not True or any(data[key] is not False for key in
                ('actual_rule_adopted', 'actual_governing_scope_established', 'forecast_issued',
                 'quarter_end_terminates_post_genesis_duties')):
            raise ValueError('not selected read-only scope')
        identities = [{'role': role, 'bytes': item['bytes'], 'sha256': item['sha256']}
                      for role, item in zip(('omb', 'bea', 'inventory', 'selection'),
                                            CASES[assessment['id']]['inputs'])]
        if data['input_identities'] != identities:
            raise ValueError('wrong assessment inputs')
        outside = data['outside_window_predecessors']
        if len(outside) != 3 or {(r['series'], r['reference_period']) for r in outside} != frontier:
            raise ValueError('incomplete fixed frontier')
        targets = [r for r in data['rows'] if r['planning_role']=='TARGET_RELEASE_CANDIDATE_PENDING_APPLICABILITY']
        by_key = {(r['series'], r['reference_period']): r for r in targets}
        edges = data['dependency_edges']
        if (len(targets) != 7 or set(by_key) != set(expected) or len(edges) != 7
                or {(e['series'], e['target_reference_period']) for e in edges} != set(expected)):
            raise ValueError('incomplete fixed dependencies')
        external = []
        for edge in edges:
            key = (edge['series'], edge['target_reference_period'])
            prior = (edge['series'], expected[key])
            target = by_key[key]
            if (edge['predecessor_reference_period'] != prior[1]
                    or edge['target_date'] != target['scheduled_date_declaration']
                    or target['release_stage'] != ('Advance' if key[0]=='GDP' else 'Scheduled release')
                    or edge['value_and_authenticated_availability'] != 'NOT_SUPPLIED'
                    or edge['predecessor_date_in_window'] !=
                       (None if prior in frontier else by_key[prior]['scheduled_date_declaration'])):
                raise ValueError('dependency does not match assessed target')
            date.fromisoformat(edge['target_date'])
            if prior in frontier:
                external.append(edge)
        return external

    def checked_research():
        data = common(research, 'calendar-predecessors-2026')
        if any(data[key] is not False for key in
               ('actual_scope_selected', 'value_obtained', 'publication_event_verified')):
            raise ValueError('upgraded predecessor evidence')
        sources = data['sources']
        identities = [{'role': role, 'file': item['alias'], 'bytes': item['bytes'], 'sha256': item['sha256']}
                      for role, item in zip(('nyfed_oct2026', 'nyfed_dec2026', 'omb_2026'),
                                            CASES[research['id']]['inputs'])]
        if [{k: row[k] for k in ('role', 'file', 'bytes', 'sha256')} for row in sources] != identities:
            raise ValueError('wrong predecessor inputs')
        markers = data['predecessor_markers']
        if len(markers) != 3 or {(m['series'], m['reference_period']) for m in markers} != frontier:
            raise ValueError('incomplete fixed predecessor declarations')
        for marker in markers:
            day = date.fromisoformat(marker['scheduled_date_declaration'])
            clock = marker['scheduled_time_declaration']
            cell_day = re.match(r'([0-9]{1,2})(?:\s|$)', marker['nyfed_cell_text'])
            gdp = marker['series']=='GDP'
            label = {'GDP': 'Gross Domestic Product 1st Release',
                     'U3': 'Employment Situation', 'CPI': 'Consumer Price Index'}[marker['series']]
            if (day.year != 2026 or day.month != (10 if gdp else 12)
                    or marker['nyfed_month_heading'] != ('October 2026' if gdp else 'December 2026')
                    or marker['release_stage'] != ('Advance' if gdp else 'Scheduled first release')
                    or marker['timezone_declaration'] != 'Eastern Time'
                    or type(clock) is not str or not re.fullmatch(r'(?:[01][0-9]|2[0-3]):[0-5][0-9]', clock)
                    or marker['omb_month_column_1_based'] != day.month
                    or marker['omb_day_declaration'] != str(day.day)
                    or cell_day is None or int(cell_day[1]) != day.day
                    or marker['omb_page_1_based'] != (3 if gdp else 4)
                    or marker['nyfed_indicator_label'] != label
                    or type(marker['nyfed_cell_index_1_based']) is not int or marker['nyfed_cell_index_1_based'] < 1
                    or marker['nyfed_indicator_label']+' ('+clock+')' not in marker['nyfed_cell_text']):
                raise ValueError('inconsistent own planning declaration')
        return {(m['series'], m['reference_period']): m for m in markers}, sources

    checked = {}
    # Validate each successful sibling even when another child failed; stale
    # observations attached to non-success results never participate in a join.
    for key, child, validate in (('assessment', assessment, checked_assessment),
                                 ('research', research, checked_research)):
        if child['status'] != 'OBSERVED':
            result['findings'].extend(dict(f, case=child['id']) for f in (child.get('findings') or
                [{'item': child['id'], 'status': child['status'], 'error': child.get('error', 'CASE_FAILED')}]))
            continue
        try:
            checked[key] = validate()
        except (KeyError, TypeError, ValueError):
            result['findings'].append({'case': result['id'], 'item': key, 'status': 'REJECTED',
                                       'error': 'INVALID_PREDECESSOR_BINDING_INPUT'})
    if not result['findings']:
        markers, sources = checked['research']
        for edge in checked['assessment']:
            marker = markers[(edge['series'], edge['predecessor_reference_period'])]
            if marker['scheduled_date_declaration'] >= edge['target_date']:
                result['findings'].append({'case': result['id'], 'item': edge['series'], 'status': 'REJECTED',
                                           'error': 'PREDECESSOR_NOT_BEFORE_TARGET'})
                break
            result['bindings'].append({'series': edge['series'], 'reference_period': edge['predecessor_reference_period'],
                'needed_by': deepcopy(edge), 'calendar_declaration': deepcopy(marker),
                'calendar_sources': deepcopy([s for s in sources if s['role'] in
                    ('omb_2026', 'nyfed_oct2026' if edge['series']=='GDP' else 'nyfed_dec2026')])})
    rank = {'REJECTED': 0, 'UNSUPPORTED': 0, 'MISSING': 1, 'UNAVAILABLE': 2}
    result['status'] = min(result['findings'], key=lambda f: rank[f['status']])['status'] if result['findings'] else 'OBSERVED'
    if result['status'] != 'OBSERVED':
        result['bindings'] = []
    result['matched_predecessor_count'] = len(result['bindings'])
    return result


def compare_u3_target_table(summary, exact):
    """Same retained edition/value comparison; no source authority promotion."""
    result={'id':'u3-summary-a1-comparison','findings':[],
        'comparison_scope':'TWO_RETAINED_EDITION_DECLARATIONS_ONLY',
        'authenticated_availability':'NOT_ESTABLISHED','actual_source_admission':'NOT_ESTABLISHED',
        'same_edition_and_rate_match':False,'protocol_state_change':'NONE'}
    for label,child in [('summary',summary),('a1',exact)]:
        if child.get('status')!='OBSERVED':
            result['findings'].extend(deepcopy(child.get('findings') or [
                {'item':label,'status':child.get('status','REJECTED'),'error':child.get('error','CHILD_NOT_OBSERVED')}]))
    if not result['findings']:
        try:
            a,b=summary['observations'],exact['observations']
            if any(a[k]!=b[k] for k in ('raw_sha256','reference_month','publication_date','release_id',
                                         'display_value','prior_reference_month','prior_value','prior_status')):
                raise ValueError('same edition/rate required')
            if (b['semantic_selector']!='EMPLOYMENT_TABLE_A1_TOTAL_SEASONALLY_ADJUSTED_U3'
                or b['selected_column_1_based']!=9 or b['adjustment']!='SEASONALLY_ADJUSTED'
                or b['evidence_class']!='ARCHIVAL_A1_TABLE_DECLARATION_ONLY'
                or b['table']!='A-1' or b['row']!='TOTAL / Unemployment rate'
                or b['summary_table_pdf_page']!=a['table_pdf_page']
                or type(b['column_values']) is not list or len(b['column_values'])!=9
                or b['column_values'][8]!=b['display_value']
                or b['column_reference_periods'][8]!=b['reference_month']):
                raise ValueError('exact finite A1 declaration required')
            result['same_edition_and_rate_match']=True
        except (KeyError,TypeError,ValueError):
            result['findings'].append({'item':'edition-or-selector','status':'REJECTED','error':'A1_SUMMARY_BINDING_MISMATCH'})
    rank={'REJECTED':0,'UNSUPPORTED':0,'MISSING':1,'UNAVAILABLE':2}
    result['status']=min(result['findings'],key=lambda f:rank[f['status']])['status'] if result['findings'] else 'OBSERVED'
    return result


def exit_code(report):
    statuses = [row['status'] for row in report['cases']]
    if any(s in {'REJECTED', 'UNSUPPORTED'} for s in statuses):
        return 2
    if not statuses or any(s != 'OBSERVED' for s in statuses):
        return 1
    return 0


def run_mainline(input_root=None, run_inputs=None, execution_inputs=None, proof_inputs=None, header_inputs=None, profile_inputs=None, chain_inputs=None, core_inputs=None, verifier_inputs=None, verifier_gate_inputs=None):
    """One development overview; current missing-evidence diagnostics stay missing."""
    request = {key: str(Path(value).absolute()) if value is not None else None
               for key, value in (('run_inputs', run_inputs), ('execution_inputs', execution_inputs),
                                  ('proof_inputs', proof_inputs), ('header_inputs', header_inputs),
                                  ('profile_inputs', profile_inputs), ('chain_inputs', chain_inputs),
                                  ('core_inputs', core_inputs), ('verifier_inputs', verifier_inputs),
                                  ('verifier_gate_inputs', verifier_gate_inputs))}
    try:
        process = subprocess.run([sys.executable, '-I', '-B', str(HERE/'mainline_worker.py')],
                                 input=json.dumps(request), capture_output=True, text=True, timeout=30)
        payload = json.loads(process.stdout) if process.returncode == 0 else None
        if (not isinstance(payload, dict) or payload.get('mode') != 'FINITE_MAINLINE_MODULES'
                or not isinstance(payload.get('modules'), list) or not payload['modules']
                or any(not isinstance(row, dict) or row.get('status') not in STATUSES
                       for row in payload['modules'])):
            raise ValueError('Invalid mainline worker result')
        modules = payload['modules']
    except (OSError, subprocess.TimeoutExpired):
        modules = [{'id': 'module-consumption', 'title': '主线模块检查', 'status': 'UNAVAILABLE',
                    'error': 'MAINLINE_RUNTIME_UNAVAILABLE'}]
    except (ValueError, TypeError):
        modules = [{'id': 'module-consumption', 'title': '主线模块检查', 'status': 'REJECTED',
                    'error': 'MAINLINE_WORKER_FAILED'}]
    # Existing public-data consumers still run after missing/rejected run inputs.
    for name, case in (('economic-data', 'gdp-2026-vintages'), ('official-calendar', 'bea-calendar'),
                       ('inflation-data', 'cpi-june-2026-copy'),
                       ('unemployment-july', 'u3-july-2025'),
                       ('unemployment-november', 'u3-november-2025')):
        result = run_case(case, input_root)
        row = {'id': name, 'title': result.get('title', case),
               'status': result['status'], 'result': result}
        if name == 'inflation-data':
            archive = run_case('cpi-june-2026-archive', input_root)
            comparison = compare_cpi_carriers(result, archive)
            row.update(title='2026年6月 CPI 两份载体声明', archive_carrier=archive,
                       carrier_comparison=comparison, status=comparison['status'],
                       findings=deepcopy(comparison['findings']))
        if name == 'official-calendar':
            research = run_case('calendar-predecessors-2026', input_root)
            assessment = run_case('q1-2027-read-only-assessment', input_root)
            binding = bind_predecessor_calendars(assessment, research)
            failed = [child for child in (result, research, assessment, binding) if child['status'] != 'OBSERVED']
            rank = {'REJECTED': 0, 'UNSUPPORTED': 0, 'MISSING': 1, 'UNAVAILABLE': 2}
            status = min(failed, key=lambda child: rank[child['status']])['status'] if failed else 'OBSERVED'
            findings = [dict(f, case=child['id']) for child in failed if child is not binding for f in child.get('findings',
                [{'item': child['id'], 'status': child['status'], 'error': child.get('error', 'CASE_FAILED')}])]
            findings.extend(deepcopy(f) for f in binding['findings'] if f['case']==binding['id'])
            row.update(title='官方日历与前置资料研究（有限）', status=status,
                       predecessor_research=research, read_only_assessment=assessment,
                       predecessor_calendar_binding=binding, findings=findings)
        if name in ('unemployment-july','unemployment-november'):
            exact=run_case(case+'-a1',input_root)
            comparison=compare_u3_target_table(result,exact)
            row.update(target_table_support={'table':exact,'comparison':comparison},status=comparison['status'])
            if comparison['findings']:
                row['findings']=deepcopy(comparison['findings'])
        modules.append(row)
    report = build_report([])
    report.pop('cases')
    report.update(mode='FINITE_MAINLINE_FRAMEWORK', modules=modules,
                  overall='REJECTED' if any(row['status'] in {'REJECTED', 'UNSUPPORTED'}
                                            for row in modules) else 'UNRESOLVED',
                  scope='Existing supported samples and actual missing-input diagnostics; not complete real replay',
                  independent_actual_scope='NOT_ESTABLISHED')
    return report


def human_report(report):
    if report['mode'] == 'FINITE_MAINLINE_FRAMEWORK':
        labels = {'OBSERVED': '已核对（局部）', 'MISSING': '待补真实输入', 'REJECTED': '拒绝',
                  'UNAVAILABLE': '环境不可用', 'UNSUPPORTED': '不支持'}
        lines = ['主线开发框架：已有模块统一检查']
        for row in report['modules']:
            lines.append(row.get('title', row['id'])+'：'+labels[row['status']])
            if row.get('error'):
                lines.append('  '+row['error'])
            if 'carrier_comparison' in row:
                lines.append('  原用户正文与FRASER归档PDF第一页声明分别消费；表A图片未自动核验。')
            if 'predecessor_research' in row:
                research = row['predecessor_research']
                lines.append('  前置资料日历：'+labels[research['status']]+'；官方汇编研究，未纳入实际来源合同。')
            if 'read_only_assessment' in row:
                assessment=row['read_only_assessment']
                lines.append('  2027Q1只读评估：'+labels[assessment['status']]+'；未建立完整必需全集或实际规则适用。')
                if assessment['status']=='OBSERVED':
                    data=assessment['observations']
                    lines.append('    '+str(data['target_release_candidates'])+'个目标发行候选，'+
                                 str(data['revision_reference_rows'])+'个GDP修订参考；'+
                                 str(len(data['missing_release_times']))+'条CPI/U3时刻仍缺。')
            if 'predecessor_calendar_binding' in row:
                binding = row['predecessor_calendar_binding']
                lines.append('  窗外前置日历对应：'+str(binding['matched_predecessor_count'])+'/3；'+
                             labels[binding['status']]+'；首次发行值及认证可得证据仍缺。')
                for item in binding['bindings']:
                    marker = item['calendar_declaration']
                    lines.append('    '+item['series']+' '+item['reference_period']+'：计划 '+
                                 marker['scheduled_date_declaration']+' '+marker['scheduled_time_declaration']+
                                 ' '+marker['timezone_declaration']+'（暂定声明）。')
            verifier = row.get('result', {}).get('technical_verifier_contract_candidate')
            gate = row.get('result', {}).get('technical_verifier_identity_gate')
            if gate is not None:
                lines.append('  声明输入身份检查：'+labels[gate['status']]+'；'+
                             str(gate['consumed_distinct_gate_inputs'])+'个声明gate输入 / '+
                             str(gate['admitted_input_count'])+'份准入快照。')
                lines.append('  未执行原生验签；完整运行环境、独立软件信任及真实权限仍未建立。')
            if verifier is not None:
                contract_status = ('REJECTED' if verifier.get('read_admission', {}).get('contract') == 'REJECTED'
                                   else verifier.get('contract_content_status'))
                lines.append('  验签合同内容：'+labels.get(contract_status, '未核对')+
                             '；八份材料：'+labels.get(verifier.get('artifact_binding_status'), '未核对')+
                             '；规则绑定：'+labels.get(verifier.get('proposed_verifier_use_status'), '未核对')+'。')
                lines.append('  仅开发技术诊断，不执行验签、不建立实际权限或完整运行环境。')
            for finding in row.get('findings', []):
                lines.append('  '+finding['item']+'：'+finding['error'])
            if 'selected_code_loading' in row and row['id'] == 'finite-reports':
                loading = row['selected_code_loading']
                lines.append('  当前有限产品代码：'+str(loading['executed_selected_modules'])+
                             '个模块由已核对源码快照编译载入；完整运行环境仍未建立。')
            if 'source_package_binding' in row:
                binding = row['source_package_binding']
                lines.append('  留存源码与发行物对应：'+labels[binding['status']]+'；源码相符不证明实际执行字节码或完整运行环境。')
                for finding in binding['findings']:
                    lines.append('  '+finding['item']+'：'+finding['error'])
            if 'target_table_support' in row:
                support=row['target_table_support']
                lines.append('  Table A-1 总体季调表项：'+labels[support['comparison']['status']]+'；仅归档版本声明，非历史首次/认证时间/来源准入。')
            if 'public_example' in row:
                example = row['public_example']
                paths = example.get('body_computation')
                if paths is not None:
                    lines.append('  公开2025 GDP样例：'+labels[example['status']]+'；已重算'+str(paths['operation_count'])+
                                 '步证明路径；此路径消费者不核验Bitcoin链或完整证明。')
                else:
                    lines.append('  公开2025 GDP样例：'+labels[example['status']]+'；仅文件摘要与OTS头，完整证明未验证。')
                if 'header_binding' in example:
                    binding = example['header_binding']
                    lines.append('  公开区块头字节绑定：'+labels[binding['status']]+
                                 '；高度仅公开服务声明，未验证链、确认或认证时间。')
                    for finding in binding['findings']:
                        lines.append('  '+finding['item']+'：'+finding['error'])
                if 'standalone_pow' in example:
                    pow_check = example['standalone_pow']
                    lines.append('  独立PoW子检查：'+labels[pow_check['status']]+
                                 '；仅声明目标与mainnet上限，未核该高度应有难度或链。')
                    for finding in pow_check['findings']:
                        lines.append('  '+finding['item']+'：'+finding['error'])
                if 'public_chain_observation' in example:
                    public = example['public_chain_observation']
                    lines.append('  公开服务观察：'+labels[public['status']]+
                                 '；非独立链验证，tip查询非原子，未建立来源独立性或认证时间。')
                    for source in public['sources']:
                        statement = source.get('service_reported_in_best_chain')
                        state = '是' if statement is True else '否' if statement is False else '未取得'
                        depth = source.get('reported_depth_arithmetic')
                        lines.append('    '+source['source_id']+'：服务报告在主链='+state+
                                     '；算术深度='+('未计算' if depth is None else str(depth))+
                                     '（非已认证确认数）。')
                    for finding in public['findings']:
                        lines.append('  '+finding['item']+'：'+finding['error'])
                if 'retained_core_sample' in example:
                    core = example['retained_core_sample']
                    lines.append('  本地Core留存样例：'+labels[core['status']]+
                                 '；历史公开GDP节点观察，非项目Strong、非全链离线重放。')
                    if 'observed_blocks' in core:
                        lines.append('    留存高度='+str(core['observed_blocks'])+
                                     '；样例确认数='+str(core['confirmations_observed'])+'（该时点本地观察）。')
                    for finding in core['findings']:
                        lines.append('  '+finding['item']+'：'+finding['error'])
                for finding in example['findings']:
                    lines.append('  '+finding['item']+'：'+finding['error'])
        finite = next((row for row in report['modules'] if row['id'] == 'finite-reports'), {})
        trace = next((row for row in report['modules'] if row['id'] == 'execution-trace'), {})
        content_checked = (finite.get('status') == 'OBSERVED'
                           and finite.get('result', {}).get('finite_report_set_match') is True)
        events_checked = (content_checked and trace.get('status') == 'OBSERVED'
                          and trace.get('result', {}).get('local_event_consistency_match') is True
                          and (trace.get('r4t_binding') or {}).get('finite_mapping_match') is True)
        content_status = ('已核对（局部）' if content_checked else
                          '未核对' if finite.get('status') == 'OBSERVED' else
                          labels.get(finite.get('status'), '未执行'))
        lines.append('五报告本次内容核对：'+content_status+'。')
        lines.append('留存测试事件对应：'+('已核对（局部）' if events_checked else '本次未核对')+
                     '；不证明真实执行或完整报告真值。')
        if events_checked:
            lines.append('留存五报告构成：一份具有有限本机测试观察，其余四份仍为合成模板。')
        elif content_checked:
            lines.append('有限五报告中四份仍为合成模板；本次未建立完整留存测试事件对应。')
        else:
            lines.append('本次不认定报告组合已获运行支持；合成模板不能代替真实领域证据。')
        lines.extend([
                      'CPI为用户正文及FRASER归档PDF有限声明；失业率为两份有限PDF，均不证明完整历史或认证可得时间。',
                      '规则、资格、周期与G10仅检查缺输入诊断；时间、workflow与留存未执行真实核验。',
                      '真实准入：NOT_READY；完整主线未完成；没有协议状态改变。'])
        return '\n'.join(lines)
    if report['mode'] == 'CATALOG_ONLY_NOT_VERIFIED':
        lines = ['有限离线核验：支持目录（尚未执行检查）']
        for row in report['cases']:
            lines.append(row['id']+' — '+row['title'])
            for item in row['inputs']:
                lines.append('  '+item['alias']+'  SHA256='+item['sha256'])
        lines.append('仅支持列明有限文件；CPI包含用户正文与FRASER归档PDF。其他发行版、CSV及任意PDF/XLSX目前不支持。')
        return '\n'.join(lines)
    labels = {'OBSERVED': '已核对（局部）', 'MISSING': '缺少文件', 'REJECTED': '拒绝',
              'UNAVAILABLE': '运行环境不可用', 'UNSUPPORTED': '不支持'}
    lines = ['有限离线证据核验']
    for row in report['cases']:
        lines.append(row.get('title', row['id'])+'：'+labels[row['status']])
        if row['status'] != 'OBSERVED':
            lines.append('  '+row.get('error', 'INVALID_RESULT'))
            for finding in row.get('findings', []):
                lines.append('  '+finding['item']+'：'+labels[finding['status']]+' / '+finding['error'])
            continue
        data = row['observations']
        news = data.get('news_pdf_support', data if 'declarations' in data else None)
        if news is not None:
            lines.append('  已用3份留存新闻稿PDF核对7个列示声明；比较列不是历史首次原件。')
            for item in news['declarations']:
                lines.append('  '+item['reference_quarter']+' '+item['stage']+'='+item['canonical_decimal']+
                             '  '+item['file']+' 第'+str(item['page_1_based'])+'页')
            for carrier in news['carriers']:
                lines.append('  PDF '+carrier['file']+' SHA256='+carrier['sha256'])
            lines.append('  Q2 Second技术说明：下调小于0.1个百分点；精确未舍入修订量未建立。')
            if 'comparison' not in data:
                continue
        if data.get('assessment') == 'PARTIAL_PUBLIC_CALENDAR_SUPPORT':
            lines.append('  2027Q1只读评估：'+str(data['target_release_candidates'])+'个目标发行候选，'+
                         str(data['revision_reference_rows'])+'个GDP修订参考；'+str(len(data['missing_release_times']))+'条时刻仍缺。')
            for item in data['rows']:
                lines.append('  '+item['scheduled_date_declaration']+' '+item['series']+' '+item['release_stage']+
                             ' 参考期='+item['reference_period']+'；'+(item['scheduled_time_declaration'] or '时刻未供'))
            for item in data['outside_window_predecessors']:
                lines.append('  窗外前置首次发行待供：'+item['series']+' '+item['reference_period'])
            lines.append('  未建立完整必需全集、实际来源准入或真实规则适用；未生成预测，不计算UTC/截止，不豁免季度外义务。')
        elif 'predecessor_markers' in data:
            for marker in data['predecessor_markers']:
                lines.append('  '+marker['series']+' 参考期='+marker['reference_period']+'；计划公布='+
                             marker['scheduled_date_declaration']+' '+marker['scheduled_time_declaration']+
                             ' '+marker['timezone_declaration'])
            lines.append('  官方汇编声明，日期/时刻可能变动；参考期由OMB资料关联，未纳入实际来源合同。')
            lines.append('  未取得2027Q1的CPI/U3时刻原件、实际数值或认证可得时间；完整周期仍未建立。')
        elif 'display_value' in data:
            if data.get('target') == 'CPI_U_ALL_ITEMS':
                lines.append('  '+data['reference_month']+' CPI-U季调月变化='+data['display_value']+'%')
                scope = ('FRASER归档PDF第一页声明，表A图片未自动核验。'
                         if data.get('evidence_class') == 'FRASER_ARCHIVE_HOSTED_BLS_PDF_HEADLINE_DECLARATIONS_ONLY'
                         else '仅用户正文副本，非发布者原字节。')
                lines.append('  未季调同比='+data['unadjusted_yearly_change']+'%；'+scope)
            else:
                lines.append('  '+data['reference_month']+' 失业率='+data['display_value'])
            if 'prior_value' in data and data['prior_value'] is None:
                lines.append('  前月缺测保留为缺测，不替换为0。')
        elif 'comparison' in data:
            comparison = data['comparison']
            lines.append('  实际GDP较前期变化率按来源表口径列示（%）；列示公布值之差的单位为百分点。')
            lines.append('  差值仅用列示的小数值相减；差值为0不表示底层估计完全没有修订。')
            for group in comparison['quarters']:
                lines.append('\n'+group['reference_quarter'])
                lines.append('| 日期 | 版本 | 公布值（%） | 较上次（百分点） | 较首次列示（百分点） | 表 / 数值单元格 |')
                lines.append('| --- | --- | --- | --- | --- | --- |')
                for item in group['rows']:
                    changes = []
                    for field in ('change_from_previous_pp', 'change_from_first_listed_pp'):
                        value = item[field]
                        changes.append('—' if value is None else ('+'+value if Decimal(value) > 0 else value))
                    lines.append('| '+' | '.join([item['publication_date'], item['stage'],
                        item['canonical_decimal'], *changes, item['sheet']+' / '+item['value_cell']])+' |')
            lines.append('\n来源：')
            for source in comparison['sources']:
                lines.append('  '+source['path']+'  SHA256='+source['sha256'])
            lines.append('当前回溯版本表中的七条声明；两次Advance与留存归档声明配对一致。')
            lines.append('不证明完整修订历史、历史首次原件或认证可得时间；首行仅指本工具首次列示版本。')
        elif 'versions' in data:
            for item in data['versions']:
                lines.append('  '+item['reference_quarter']+' '+item['stage']+' '+item['publication_date']+
                             ' GDP='+item['canonical_decimal'])
            lines.append('  两份Advance归档与版本表的来源声明配对一致。')
        elif 'events' in data:
            lines.append('  已核对8个既有日历例子；不证明全部应有周期。')
        else:
            lines.append('  仅合成开发绑定样本；局部绑定一致，整体仍UNRESOLVED。')
    lines.append('整体真实准入尚未建立（NOT_READY）；历史首次可得时间与完整性仍未建立。')
    lines.append('未建立正式时间认证、Bitcoin或Genesis；没有协议状态改变。')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description='有限本地证据核验，不联网、不建立真实准入。')
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('list', 'verify', 'demo', 'compare-gdp', 'mainline'):
        sub = commands.add_parser(name)
        sub.add_argument('--json', action='store_true', help='输出稳定JSON')
        if name != 'list':
            sub.add_argument('--inputs', type=Path, help='已授权公共文件目录；只读取list中列明别名')
        if name == 'verify':
            sub.add_argument('case', choices=tuple(CASES))
        if name == 'compare-gdp':
            sub.add_argument('--news-pdfs', action='store_true', help='另核对3份明确留存新闻稿PDF')
        if name == 'mainline':
            sub.add_argument('--run-inputs', type=Path, help='明确公共D178运行材料目录；缺失时不回退')
            sub.add_argument('--execution-inputs', type=Path, help='明确公共D177事件材料目录；缺失时不回退')
            sub.add_argument('--proof-inputs', type=Path, help='明确公共D132 PDF/OTS样例目录；缺失时不回退')
            sub.add_argument('--header-inputs', type=Path, help='明确公共D187区块头目录；缺失时不回退')
            sub.add_argument('--profile-inputs', type=Path, help='明确D185技术候选目录；不接受真实规则，缺失不回退')
            sub.add_argument('--verifier-inputs', type=Path, help='明确D211合同与八份公共材料目录；不执行验签，缺失不回退')
            sub.add_argument('--verifier-gate-inputs', type=Path, help='64条声明公共输入的镜像根目录；固定相对路径，无默认回退，不执行原生验签')
            sub.add_argument('--chain-inputs', type=Path, help='明确D195轻量公开观察目录；不联网、不回退或建立独立链验证')
            sub.add_argument('--core-inputs', type=Path, help='明确D199留存Core公开样例目录；不启动节点、不回退或建立项目Strong')
    args = parser.parse_args(argv)
    if args.command == 'list':
        report = {'mode': 'CATALOG_ONLY_NOT_VERIFIED', 'cases': [
            {'id': name, 'title': case['title'], 'scope': case['scope'], 'inputs': case['inputs']}
            for name, case in CASES.items()]}
        code = 0
    elif args.command == 'mainline':
        report = run_mainline(args.inputs, args.run_inputs, args.execution_inputs, args.proof_inputs,
                              args.header_inputs, args.profile_inputs, args.chain_inputs, args.core_inputs, args.verifier_inputs,
                              args.verifier_gate_inputs)
        code = exit_code({'cases': report['modules']})
    else:
        if args.command == 'compare-gdp':
            results = [(compare_gdp_with_news if args.news_pdfs else compare_gdp)(args.inputs)]
        else:
            names = [args.case] if args.command == 'verify' else [
                name for name, case in CASES.items() if case.get('default_demo', True)]
            results = [run_case(name, args.inputs) for name in names]
        report = build_report(results)
        code = exit_code(report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) if args.json else human_report(report))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
