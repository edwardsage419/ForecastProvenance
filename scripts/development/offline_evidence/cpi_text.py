"""One retained user text copy: source declarations, never publisher raw bytes."""
from decimal import Decimal
from hashlib import sha256
import re

COPY_SHA256 = '6801f88bba316af7e6aa1af85a719bd60261f2bfa2ed097ed1ff7950a5f0c4d2'
TABLE = 'Table A. Percent changes in CPI for All Urban Consumers (CPI-U): U.S. city average'


def parse_retained_text(text):
    """Extract selected measures under the fixed edition layout, not a general BLS parser."""
    heading = 'CONSUMER PRICE INDEX - JUNE 2026'
    release_id = 'USDL-26-1191'
    date_label = '8:30 a.m. (ET) Tuesday, July 14, 2026'
    if any(text.count(label) != 1 for label in (heading, release_id, date_label, TABLE)):
        raise ValueError('retained edition header missing or ambiguous')
    flat = ' '.join(text.split())
    headlines = re.findall(
        r'The Consumer Price Index for All Urban Consumers \(CPI-U\) '
        r'(increased|decreased) (\d+\.\d+) percent on a seasonally adjusted basis in June', flat)
    if len(headlines) != 1:
        raise ValueError('unique seasonally adjusted CPI-U monthly headline required')
    verb, amount = headlines[0]
    headline = Decimal(amount) * (-1 if verb == 'decreased' else 1)
    table = text.split(TABLE)[1].split('\nFood\n')[0]
    if table.count('\nAll items\n') != 1:
        raise ValueError('unique Table A all-items row required')
    header, row = table.split('\nAll items\n')
    expected_header = ('Seasonally adjusted changes from preceding month Un- adjusted 12-mos. ended '
                       'Jun. 2026 Dec. 2025 Jan. 2026 Feb. 2026 Mar. 2026 Apr. 2026 May 2026 Jun. 2026')
    if ' '.join(header.split()) != expected_header:
        raise ValueError('Table A adjustment/period columns differ')
    cells = row.split()
    if len(cells) != 8 or any(re.fullmatch(r'-?\d+\.\d+', value) is None for value in cells):
        raise ValueError('Table A value row differs')
    yearly = re.findall(r'Over the last 12 months, the all items index increased '
                        r'(\d+\.\d+) percent before seasonal adjustment\.', flat)
    if (Decimal(cells[6]) != headline or len(yearly) != 1
            or Decimal(cells[7]) != Decimal(yearly[0])):
        raise ValueError('headline and corresponding Table A measures disagree')
    return {'reference_month': '2026-06', 'publication_date_declaration': '2026-07-14',
            'release_id': release_id, 'target': 'CPI_U_ALL_ITEMS',
            'measure': 'PERCENT_CHANGE_FROM_PRECEDING_MONTH', 'adjustment': 'SEASONALLY_ADJUSTED',
            'display_value': cells[6], 'unadjusted_yearly_change': cells[7],
            'table_A_month_columns': ['2025-12', '2026-01', '2026-02', '2026-03',
                                      '2026-04', '2026-05', '2026-06'],
            'table_A_sa_monthly_values': cells[:7],
            'table_A_heading_line': text[:text.index(TABLE)].count('\n')+1,
            'evidence_class': 'USER_SUPPLIED_RENDERED_TEXT_SOURCE_DECLARATION_ONLY',
            'original_publisher_bytes': False, 'full_document_completeness': 'NOT_ESTABLISHED',
            'historical_first_release': 'NOT_ESTABLISHED',
            'authenticated_availability': 'NOT_ESTABLISHED'}


def observe_cpi_copy(raw):
    if type(raw) is not bytes or sha256(raw).hexdigest() != COPY_SHA256:
        raise ValueError('outside exact retained public-copy scope')
    return dict(parse_retained_text(raw.decode('utf-8')), raw_sha256=COPY_SHA256)
