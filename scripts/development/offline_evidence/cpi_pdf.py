"""One exact FRASER archive PDF; first-page declarations, not historical availability."""
from decimal import Decimal
from hashlib import sha256
from io import BytesIO
import re

PDF_SHA256 = 'dd9288175bd38ef9c05b1e5d5ce03ea6c6032a1c2900355208905f78f94aea81'
ARCHIVE_URL = 'https://fraser.stlouisfed.org/files/docs/publications/bls/newsreleases/cpi/cpi_20260714.pdf'


def parse_archive_first_page(text):
    """Fixed edition/headline layout only; raster Table A is outside this parser."""
    if type(text) is not str:
        raise ValueError('first-page text required')
    flat = ' '.join(text.split())
    for label in ('CONSUMER PRICE INDEX – JUNE 2026', 'USDL-26-1191',
                  '8:30 a.m. (ET) Tuesday, July 14, 2026'):
        if flat.count(label) != 1:
            raise ValueError('archive edition missing or ambiguous')
    # pypdf splits the word Consumer across a line in this PDF. Anchor on the
    # intact distinctive index name instead of inventing general word joining.
    monthly = re.findall(r'Price Index for All Urban Consumers \(CPI-U\) '
                         r'(increased|decreased) (\d+\.\d+) percent on a seasonally '
                         r'adjusted basis in June', flat)
    yearly = re.findall(r'Over the last 12 months, the all items index '
                        r'(increased|decreased) (\d+\.\d+) percent before seasonal adjustment\.', flat)
    if len(monthly) != 1 or len(yearly) != 1:
        raise ValueError('unique monthly and yearly headlines required')
    def signed(match):
        verb, amount = match
        return format(Decimal(amount) * (-1 if verb == 'decreased' else 1), 'f')
    return {'reference_month': '2026-06', 'publication_date_declaration': '2026-07-14',
            'release_id': 'USDL-26-1191', 'target': 'CPI_U_ALL_ITEMS',
            'measure': 'PERCENT_CHANGE_FROM_PRECEDING_MONTH', 'adjustment': 'SEASONALLY_ADJUSTED',
            'display_value': signed(monthly[0]), 'unadjusted_yearly_change': signed(yearly[0])}


def observe_archive_pdf(raw):
    if (type(raw) is not bytes or len(raw) != 502033 or not raw.startswith(b'%PDF-')
            or sha256(raw).hexdigest() != PDF_SHA256):
        raise ValueError('outside exact retained archive PDF scope')
    from pypdf import PdfReader
    reader = PdfReader(BytesIO(raw), strict=True)
    if reader.is_encrypted or len(reader.pages) != 38:
        raise ValueError('unsupported archive structure')
    text = reader.pages[0].extract_text()
    return dict(parse_archive_first_page(text), raw_sha256=PDF_SHA256,
                source_url=ARCHIVE_URL, pages=38, page_1_based=1,
                extracted_page_sha256=sha256(text.encode('utf-8')).hexdigest(),
                evidence_class='FRASER_ARCHIVE_HOSTED_BLS_PDF_HEADLINE_DECLARATIONS_ONLY',
                table_A_machine_verification='NOT_CHECKED_RASTER_TABLE',
                original_publisher_bytes=False, full_document_completeness='NOT_ESTABLISHED',
                historical_first_release='NOT_ESTABLISHED', authenticated_availability='NOT_ESTABLISHED')
