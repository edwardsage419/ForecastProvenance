"""Finite declarations in three retained BEA release PDFs, never first-byte proof."""
from decimal import Decimal
import hashlib
import io
import re

SPECS = {
    'q1_third': ('gdp1q26-3rd.pdf', '2026-06', '2026-06-25', 8,
                 'June 25, 2026', 'BEA 26-30', 'GDP (Third Estimate)', '1st Quarter 2026'),
    'q2_third': ('gdp2q26-3rd.pdf', '2026-09', '2026-09-30', 10,
                 'September 30, 2026', 'BEA 26-42', 'GDP (Third Estimate)', '2nd Quarter 2026'),
    'q2_second': ('gdp2q26-2nd.pdf', '2026-08', '2026-08-26', 5,
                  'August 26, 2026', 'BEA 26-38', 'GDP (Second Estimate)', '2nd Quarter 2026'),
}
NUMBER = r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?'


def normal(text):
    return ' '.join(text.replace('\u2013', '-').replace('\u2014', '-').split())


def _values(text, prefix, count):
    pattern = re.escape(prefix) + r' Real GDP ' + ' '.join('('+NUMBER+')' for _ in range(count))
    pattern += r' Current-dollar GDP '
    matches = re.findall(pattern, normal(text), flags=re.I)
    if len(matches) != 1:
        raise ValueError('unique Real GDP row with exact table/header/unit required')
    return list(matches[0])


def table_values(text, quarter, stages):
    periods = {'2026-Q1': '2025:Q4 to 2026:Q1', '2026-Q2': '2026:Q1 to 2026:Q2'}
    if quarter not in periods or tuple(stages) not in {('Advance', 'Second'), ('Advance', 'Second', 'Third')}:
        raise ValueError('unsupported finite table')
    prefix = ('Real GDP and Related Measures [Percent Change (SAAR) from '+periods[quarter]+'] '
              + ' '.join(stage+' Estimate' for stage in stages))
    return _values(text, prefix, len(stages))


def observe_news_pdfs(raw_by_role):
    from pypdf import PdfReader
    if set(raw_by_role) != set(SPECS):
        raise ValueError('three explicit carriers required')
    pages = {}
    carriers = {}
    for role, spec in SPECS.items():
        filename, month, when, count, date_label, release_id, title, quarter_label = spec
        raw = raw_by_role[role]
        if type(raw) is not bytes or not raw.startswith(b'%PDF-') or len(raw) > 10*1024*1024:
            raise ValueError('bounded public PDF required')
        reader = PdfReader(io.BytesIO(raw), strict=True)
        if reader.is_encrypted or len(reader.pages) != count:
            raise ValueError('wrong carrier page count or encryption')
        first = normal(reader.pages[0].extract_text() or '')
        if any(label.casefold() not in first.casefold() for label in
               (date_label, release_id, title, quarter_label, 'EMBARGOED UNTIL RELEASE')):
            raise ValueError('carrier publication/edition mismatch')
        needed = (2, 7) if role == 'q2_third' else ((2, 3) if role == 'q2_second' else (2,))
        pages[role] = {i: reader.pages[i].extract_text() or '' for i in needed}
        carriers[role] = {'file': filename, 'sha256': hashlib.sha256(raw).hexdigest(),
            'bytes': len(raw), 'pages': count, 'carrier_publication_date': when,
            'source_url': 'https://www.bea.gov/sites/default/files/'+month+'/'+filename}
    q1 = table_values(pages['q1_third'][2], '2026-Q1', ('Advance', 'Second', 'Third'))
    q2 = table_values(pages['q2_third'][2], '2026-Q2', ('Advance', 'Second', 'Third'))
    second = table_values(pages['q2_second'][2], '2026-Q2', ('Advance', 'Second'))
    revised = _values(pages['q2_third'][7],
        'First Quarter 2026 Previous Estimate Revised Estimate (Percent change (SAAR) from preceding quarter)', 2)
    if Decimal(revised[0]) != Decimal(q1[2]) or [Decimal(v) for v in second] != [Decimal(v) for v in q2[:2]]:
        raise ValueError('cross-carrier declarations disagree')
    note = normal(pages['q2_second'][3])
    if ('Sources of revision to real GDP in the second estimate' not in note
        or 'in the second quarter, a downward revision of less than 0.1 percentage point.' not in note):
        raise ValueError('specific rounding note required')
    declarations = []
    def declaration(quarter, stage, value, role, page, column):
        decimal = Decimal(value)
        canonical = format(decimal.normalize(), 'f') if decimal != 0 else '0'
        return {'reference_quarter': quarter, 'stage': stage, 'raw_lexical': value,
            'canonical_decimal': canonical, 'file': carriers[role]['file'],
            'raw_sha256': carriers[role]['sha256'], 'page_1_based': page,
            'column_label': column, 'metric': 'REAL_GDP', 'unit': 'PERCENT_CHANGE_SAAR',
            'carrier_publication_date': carriers[role]['carrier_publication_date'],
            'evidence_class': 'RETAINED_RELEASE_PDF_DECLARATION_ONLY',
            'historical_first_bytes': 'NOT_ESTABLISHED', 'authenticated_availability': 'NOT_ESTABLISHED'}
    for stage, value in zip(('Advance', 'Second', 'Third'), q1):
        declarations.append(declaration('2026-Q1', stage, value, 'q1_third', 3, stage+' Estimate'))
    declarations.append(declaration('2026-Q1', 'Revised', revised[1], 'q2_third', 8, 'Revised Estimate'))
    for stage, value in zip(('Advance', 'Second', 'Third'), q2):
        declarations.append(declaration('2026-Q2', stage, value, 'q2_third', 3, stage+' Estimate'))
    return {'declarations': declarations, 'carriers': list(carriers.values()),
        'rounding_note': {'file': carriers['q2_second']['file'],
            'raw_sha256': carriers['q2_second']['sha256'], 'page_1_based': 4,
            'direction': 'DOWNWARD', 'magnitude_pp': 'LESS_THAN_0.1',
            'exact_unrounded_revision_pp': None, 'displayed_values': second},
        'coverage': 'THREE_RETAINED_PDFS_SEVEN_DECLARATIONS_NOT_COMPLETE_HISTORY',
        'earlier_columns_are_original_release_carriers': False,
        'historical_first_bytes': 'NOT_ESTABLISHED', 'authenticated_availability': 'NOT_ESTABLISHED'}
