"""Selected read-only calendar assessment; no actual duty, value or event creation."""
from copy import deepcopy
from datetime import date
from hashlib import sha256
from io import BytesIO
import json
import re

INPUTS={
    'omb':(218990,'20482c7a2c35871c387c0d86d77d2f63a9e1dcc53ec301b32d331845414bde20'),
    'bea':(106652,'a54b35967680161b604b2d114079a7392e002043b94994274945f89603f74fcd'),
    'inventory':(9633,'3849eb9e0dbf69ab41fa172c86a66356a9702a7346dacb3ac1f1dbed13537dab'),
    'selection':(606,'5a1df97d428389e18f51b2f5ded021aa5fea5159acb7ed592187fa545fdcb4a8'),
}
GDP_TITLES={
    'Advance':'GDP (Advance Estimate), 4th Quarter and Year 2026',
    'Second':'GDP (Second Estimate), 4th Quarter and Year 2026',
    'Third':'GDP (Third Estimate), Industries, Corporate Profits, State GDP, and State Personal Income, 4th Quarter and Year 2026',
}
MONTHS=('January','February','March')
TARGET='TARGET_RELEASE_CANDIDATE_PENDING_APPLICABILITY'
REVISION='REVISION_REFERENCE_ONLY_NOT_ANOTHER_ADVANCE_TARGET_CYCLE'


def require(condition,reason):
    if not condition:raise ValueError(reason)


def check_selection(selection):
    expected={'artifact_role':'USER_SELECTED_READ_ONLY_ASSESSMENT_SCOPE_NOT_GOVERNING_RULE',
        'basis':'RELEASE_DATE_CALENDAR_WINDOW','start_inclusive':'2027-01-01','end_inclusive':'2027-03-31',
        'series':['GDP','CPI','U3'],'method':'last-observed-value','gdp_target_stage':'Advance',
        'gdp_second_third_role':'REVISION_REFERENCE_ONLY','user_answer':'采用2027Q1作为只读评估范围（推荐）',
        'quarter_end_terminates_post_genesis_duties':False,'actual_rule_adopted':False,
        'actual_governing_scope_established':False,'protocol_state_change':'NONE'}
    # JSON type-sensitive equality; 0/False or 1/True must not substitute for choices.
    require(type(selection) is dict and json.dumps(selection,sort_keys=True,ensure_ascii=False)==
            json.dumps(expected,sort_keys=True,ensure_ascii=False),'exact selected assessment scope required')


def bea_gdp_rows(rows):
    result={}
    for stage,title in GDP_TITLES.items():
        matched=[(i,row) for i,row in enumerate(rows,1) if any(c['text']==title for c in row)]
        require(len(matched)==1,'unique selected BEA GDP row required')
        index,row=matched[0]
        require(len(row)==4 and row[2]['text']==title and row[1]['text']=='News','BEA columns differ')
        require(all(c['kind']=='td' and c['attrs'].get('colspan','1')=='1' and
                    c['attrs'].get('rowspan','1')=='1' for c in row),'BEA cell shape differs')
        require(row[0]['attrs'].get('headers')=='view-field-scheduled-release-date-1-table-column' and
                row[2]['attrs'].get('headers')=='view-field-scheduled-release-subject-table-column',
                'BEA column identity differs')
        require(row[3]['text']=='' and row[3]['links']==[],'retained future row locator differs')
        match=re.fullmatch(r'(January|February|March) ([0-9]{1,2}) ([0-9]{1,2}):([0-9]{2}) (AM|PM)',row[0]['text'])
        require(match is not None,'own selected BEA date and time required')
        require(1<=int(match[3])<=12 and int(match[4])<=59,'invalid BEA clock')
        when=date(2027,MONTHS.index(match[1])+1,int(match[2]))
        result[stage]={'scheduled_date_declaration':when.isoformat(),
            'scheduled_time_declaration':match[3]+':'+match[4]+' '+match[5],
            'bea_data_row_index_1_based':index,'bea_subject':title,'bea_date_cell':row[0]['text']}
    return result


def assess(annual_rows,bea_rows,inventory,selection):
    """Finite source/inventory comparison only; controls cannot prove duty completeness."""
    check_selection(selection)
    require(type(annual_rows) is dict and set(annual_rows)=={'GDP','CPI','U3'},'three annual series required')
    for series,rows in annual_rows.items():
        require(type(rows) is list and len(rows)==12,'all twelve declared month columns required')
        for month,row in enumerate(rows,1):
            when=date.fromisoformat(row['scheduled_date_declaration'])
            require(when.year==2027 and when.month==month and row['omb_month_column_1_based']==month,
                    'annual month position differs')
            if series=='GDP':
                period='2026-Q4' if month<=3 else '2027-Q'+str((month-1)//3)
                require(row['reference_period']==period and row['release_stage']==('Advance','Second','Third')[(month-1)%3],
                        'GDP quarter or estimate order differs')
            else:
                period='2026-12' if month==1 else '2027-'+str(month-1).zfill(2)
                require(row['reference_period']==period and row['release_stage']=='Scheduled release','monthly reference differs')
    bea=bea_gdp_rows(bea_rows)
    records=[]
    for series in ('GDP','CPI','U3'):
        for source in annual_rows[series][:3]:
            row=deepcopy(source);row['series']=series
            row.update(scheduled_time_declaration=None,timezone_declaration=None,utc_barrier=None)
            row['planning_role']=REVISION if series=='GDP' and row['release_stage']!='Advance' else TARGET
            if series=='GDP':
                other=bea[row['release_stage']]
                require(other['scheduled_date_declaration']==row['scheduled_date_declaration'],'OMB/BEA date conflict')
                row.update(other)
            records.append(row)
    records.sort(key=lambda row:(row['scheduled_date_declaration'],row['series']))
    require(type(inventory) is dict and type(inventory.get('items')) is list and len(inventory['items'])==9,
            'exact retained nine-row planning inventory required')
    supplied={}
    for row in inventory['items']:
        key=(row['series'],row['release_date_declaration'])
        require(key not in supplied,'duplicate inventory row');supplied[key]=row
    require(set(supplied)=={(r['series'],r['scheduled_date_declaration']) for r in records},'inventory row set differs')
    for row in records:
        control=supplied[(row['series'],row['scheduled_date_declaration'])]
        require(control['reference_period_declaration']==row['reference_period'] and
                control['release_stage']==row['release_stage'] and control['planning_role']==row['planning_role'],
                'inventory period/stage/role differs')
        declared=control['release_time_declaration']
        normalized=declared.lstrip('0') if type(declared) is str else declared
        require(normalized==row['scheduled_time_declaration'],'inventory clock declaration differs')
        # The inventory is historical comparison, not a source of observed time.
        if row['planning_role']==TARGET:
            row['candidate_target_ref']=deepcopy(control['candidate_target_ref'])
            row['candidate_method_ref']=deepcopy(control['candidate_method_ref'])
    targets=[row for row in records if row['planning_role']==TARGET]
    edges=[];frontier=[]
    for row in targets:
        period=row['reference_period']
        if row['series']=='GDP':
            year,quarter=map(int,period.split('-Q'))
            previous=str(year-1)+'-Q4' if quarter==1 else str(year)+'-Q'+str(quarter-1)
        else:
            year,month=map(int,period.split('-'))
            previous=str(year-1)+'-12' if month==1 else str(year)+'-'+str(month-1).zfill(2)
        control=supplied[(row['series'],row['scheduled_date_declaration'])]
        require(control['preceding_first_release_reference_period_needed']==previous,'method predecessor differs')
        inside=[r for r in targets if r['series']==row['series'] and r['reference_period']==previous]
        require(len(inside)<=1,'ambiguous predecessor')
        predecessor=inside[0]['scheduled_date_declaration'] if inside else None
        if predecessor is not None:require(predecessor<row['scheduled_date_declaration'],'predecessor ordering differs')
        edge={'series':row['series'],'target_reference_period':period,
            'target_date':row['scheduled_date_declaration'],'predecessor_reference_period':previous,
            'predecessor_date_in_window':predecessor,'value_and_authenticated_availability':'NOT_SUPPLIED'}
        edges.append(edge)
        if not inside:frontier.append({'series':row['series'],'reference_period':previous})
    return {'assessment':'PARTIAL_PUBLIC_CALENDAR_SUPPORT','rows':records,'target_release_candidates':len(targets),
        'revision_reference_rows':len(records)-len(targets),'dependency_edges':edges,
        'outside_window_predecessors':frontier,
        'missing_release_times':[{'series':r['series'],'date':r['scheduled_date_declaration']} for r in targets
                                 if r['scheduled_time_declaration'] is None],
        'read_only_scope_selected':True,'actual_governing_scope_established':False,
        'actual_rule_adopted':False,'actual_source_admission_established':False,
        'quarter_end_terminates_post_genesis_duties':False,'candidate_refs_are_historical_labels_only':True,
        'actual_required_cycle_or_slot_universe':'NOT_ESTABLISHED','source_independence':'NOT_ESTABLISHED',
        'authenticated_availability_established':False,'utc_deadline_computed':False,'forecast_issued':False,
        'operational_bindings_established':0,'real_admission':'NOT_READY','protocol_state_change':'NONE'}


def observe_q1_assessment(raw_by_role,*,parse_omb_pages,annual_parser):
    require(type(raw_by_role) is dict and set(raw_by_role)==set(INPUTS),'exact four input roles required')
    for role,(size,digest) in INPUTS.items():
        raw=raw_by_role[role]
        require(type(raw) is bytes and len(raw)==size and sha256(raw).hexdigest()==digest,'fixed assessment input identity differs')
    from pypdf import PdfReader
    pdf=PdfReader(BytesIO(raw_by_role['omb']),strict=True)
    require(not pdf.is_encrypted and len(pdf.pages)==5,'retained five-page OMB required')
    annual=parse_omb_pages(pdf.pages[2].extract_text(),pdf.pages[3].extract_text(),year=2027,annual=True)
    result=assess(annual,annual_parser(raw_by_role['bea'],2027),
        json.loads(raw_by_role['inventory']),json.loads(raw_by_role['selection']))
    result['input_identities']=[{'role':role,'bytes':size,'sha256':digest} for role,(size,digest) in INPUTS.items()]
    return result
