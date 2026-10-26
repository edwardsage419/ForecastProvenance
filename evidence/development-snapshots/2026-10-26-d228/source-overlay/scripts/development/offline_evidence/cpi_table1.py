"""Exact Table1/All items/SA month declaration in one retained archive PDF."""
from hashlib import sha256
from importlib.metadata import version
from io import BytesIO
import re
from pypdf import PdfReader

PDF_SHA='dd9288175bd38ef9c05b1e5d5ce03ea6c6032a1c2900355208905f78f94aea81'
SELECTOR='CPI_TABLE_1_ALL_ITEMS_SEASONALLY_ADJUSTED_PERCENT_CHANGE_PRECEDING_MONTH'
HEADER=('Table 1. Consumer Price Index for All Urban Consumers (CPI-U): U.S. city average, by expenditure category, '
 'June 2026 [1982-84=100, unless otherwise noted] Expenditure category Relative impor- tance May 2026 '
 'Unadjusted indexes Unadjusted percent change Seasonally adjusted percent change '
 'Jun. 2025 May 2026 Jun. 2026 Jun. 2025- Jun. 2026 May 2026- Jun. 2026 '
 'Mar. 2026- Apr. 2026 Apr. 2026- May 2026 May 2026- Jun. 2026')


def require(condition,message):
    if not condition:raise ValueError(message)


def parse_table1_text(text):
    """Consume this exact page representation; not a PDF authenticity check."""
    require(type(text) is str,'Table1 text required')
    lines=[s.strip() for s in text.splitlines() if s.strip()]
    matches=[i for i,s in enumerate(lines) if s.startswith('All items.')]
    require(len(matches)==1 and text.count('Table 1.')==1,'unique own All items/Table1 required')
    i=matches[0]
    require(' '.join(lines[:i])==HEADER,'exact Table1 period and columns required')
    cells=lines[i][len('All items'):].strip(' .').split()
    require(len(cells)==9,'nine distinct Table1 columns required')
    cells=[s.replace('−','-') for s in cells]
    require(all(re.fullmatch(r'\d+\.\d{3}',s) is not None for s in cells[:4]) and cells[0]=='100.000',
            'All items importance and index columns required')
    require(all(re.fullmatch(r'-?\d+\.\d',s) is not None for s in cells[4:]),'displayed percent columns required')
    return {'reference_month':'2026-06','target':'CPI_U_ALL_ITEMS',
        'measure':'PERCENT_CHANGE_FROM_PRECEDING_MONTH','adjustment':'SEASONALLY_ADJUSTED',
        'table':'1','row':'All items','semantic_selector':SELECTOR,'page_1_based':9,
        'selected_column_1_based':9,'column_values':cells,'display_value':cells[8],
        'unadjusted_yearly_change':cells[4],'unadjusted_monthly_change':cells[5],
        'seasonally_adjusted_monthly_values':cells[6:],
        'seasonally_adjusted_reference_months':['2026-04','2026-05','2026-06']}


def observe_table1_pdf(raw,*,archive_observer):
    """The worker supplies the fixed admitted existing archive observer."""
    require(type(raw) is bytes and len(raw)==502033 and sha256(raw).hexdigest()==PDF_SHA,'exact retained archive required')
    require(version('pypdf')=='6.10.0','checked pypdf required')
    archive=archive_observer(raw)
    require(type(archive) is dict and archive.get('raw_sha256')==PDF_SHA,'same retained archive observer required')
    reader=PdfReader(BytesIO(raw),strict=True)
    parsed=parse_table1_text(reader.pages[8].extract_text())
    for key in ('reference_month','target','measure','adjustment','display_value','unadjusted_yearly_change'):
        require(parsed[key]==archive.get(key),'Table1/headline mismatch')
    return dict(parsed,publication_date_declaration=archive['publication_date_declaration'],release_id=archive['release_id'],
        raw_sha256=PDF_SHA,source_url=archive['source_url'],parser_version=version('pypdf'),
        evidence_class='FRASER_ARCHIVE_TABLE1_DECLARATIONS_ONLY',original_publisher_bytes=False,
        full_document_completeness='NOT_ESTABLISHED',historical_first_release='NOT_ESTABLISHED',
        authenticated_availability='NOT_ESTABLISHED',actual_source_admission='NOT_ESTABLISHED',protocol_state_change='NONE')
