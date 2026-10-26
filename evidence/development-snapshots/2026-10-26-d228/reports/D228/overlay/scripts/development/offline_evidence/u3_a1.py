"""Two retained A-1 TOTAL/SA declarations; no FIRST, time or admission claim."""
from hashlib import sha256
from importlib.metadata import version
from io import BytesIO
from decimal import Decimal
import re
from pypdf import PdfReader

TITLE='Table A-1. Employment status of the civilian population by sex and age'
SELECTOR='EMPLOYMENT_TABLE_A1_TOTAL_SEASONALLY_ADJUSTED_U3'
SCOPE={
 '2025-07':(11,'3cab42e98aae44f6e90678d75c7c028d1703729e95e1f1f91724519bacf42a84',
   'July 2024 June 2025 July 2025 July 2024 Mar. 2025 Apr. 2025 May 2025 June 2025 July 2025',
   ['2024-07','2025-06','2025-07','2024-07','2025-03','2025-04','2025-05','2025-06','2025-07']),
 '2025-11':(14,'6408e38172c272f3d8416f01873d3bc40d11c9ceb90933feb4939830cd63f6d2',
   'Nov. 2024 Oct. 2025 Nov. 2025 Nov. 2024 July 2025 Aug. 2025 Sept. 2025 Oct. 2025 Nov. 2025',
   ['2024-11','2025-10','2025-11','2024-11','2025-07','2025-08','2025-09','2025-10','2025-11'])}


def require(condition,message):
    if not condition:raise ValueError(message)


def parse_a1_text(text,*,reference_month):
    """Parse a checked page representation; this alone authenticates no PDF."""
    require(type(text) is str and reference_month in SCOPE,'unsupported A1 text or month')
    page,digest,columns,periods=SCOPE[reference_month]
    lines=[s.strip() for s in text.splitlines() if s.strip()]
    require(lines[:3]==['HOUSEHOLD DATA',TITLE,'[Numbers in thousands]'] and lines.count(TITLE)==1,'exact A1 heading required')
    require(lines.count('TOTAL')==1 and lines.count('Men, 16 years and over')==1,'unique TOTAL section required')
    start=lines.index('TOTAL');end=lines.index('Men, 16 years and over')
    require(start<end and ' '.join(lines[3:start])==
        'Employment status, sex, and age Not seasonally adjusted Seasonally adjusted 1 '+columns,
        'exact NSA/SA column identities required')
    rows=[line for line in lines[start+1:end] if line.startswith('Unemployment rate.')]
    require(len(rows)==1,'unique TOTAL unemployment rate required')
    cells=rows[0][len('Unemployment rate'):].strip(' .').split()
    require(len(cells)==9,'nine A1 columns required')
    for i,value in enumerate(cells):
        if reference_month=='2025-11' and i in (1,7):
            require(value in ('–','—'),'October missing value must remain missing')
        else:
            require(re.fullmatch(r'\d+\.\d+',value) is not None and 0<=Decimal(value)<=100,'invalid A1 rate')
    if reference_month=='2025-11':
        require('Data for October 2025 were not collected due to the federal government shutdown.' in ' '.join(lines),
                'missing October context required')
    return {'semantic_selector':SELECTOR,'table':'A-1','row':'TOTAL / Unemployment rate',
        'adjustment':'SEASONALLY_ADJUSTED','reference_month':reference_month,
        'table_pdf_page':page,'column_reference_periods':list(periods),'column_values':cells,
        'selected_column_1_based':9,'display_value':cells[8],'unadjusted_current_value':cells[2],
        'prior_reference_month':periods[7],
        'prior_value':None if cells[7] in ('–','—') else cells[7],
        'prior_status':'SOURCE_DECLARED_NOT_COLLECTED' if cells[7] in ('–','—') else 'SOURCE_DECLARED_VALUE'}


def observe_a1_pdf(raw,*,reference_month,summary_observer):
    """Use the fixed legacy summary observer on the same immutable input bytes.

    Offline worker supplies the separately admitted existing observer, not a
    caller-selected authority/eligibility result. Pure text parsing is distinct.
    """
    require(type(raw) is bytes and raw and type(reference_month) is str and reference_month in SCOPE,'finite immutable PDF required')
    page,digest,_,_=SCOPE[reference_month]
    require(sha256(raw).hexdigest()==digest,'retained A1 PDF identity mismatch')
    require(version('pypdf')=='6.10.0','checked pypdf required')
    # Existing code verifies edition/header/summary/absent-prior context.
    summary=summary_observer(raw,reference_month=reference_month)
    require(type(summary) is dict and summary.get('reference_month')==reference_month and summary.get('raw_sha256')==digest,
            'same checked summary edition required')
    reader=PdfReader(BytesIO(raw),strict=True)
    parsed=parse_a1_text(reader.pages[page-1].extract_text(),reference_month=reference_month)
    for key in ('display_value','prior_reference_month','prior_value','prior_status'):
        require(parsed[key]==summary.get(key),'summary/A1 mismatch')
    return dict(parsed,raw_sha256=digest,publication_date=summary['publication_date'],release_id=summary['release_id'],
        parser_version=version('pypdf'),summary_table_pdf_page=summary['table_pdf_page'],
        evidence_class='ARCHIVAL_A1_TABLE_DECLARATION_ONLY',historical_first_bytes='NOT_ESTABLISHED',
        authenticated_availability='NOT_ESTABLISHED',actual_source_admission='NOT_ESTABLISHED',
        actual_governing_scope='NOT_ESTABLISHED',protocol_state_change='NONE')
