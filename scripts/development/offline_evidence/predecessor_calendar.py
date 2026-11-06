"""Three fixed official compilation inputs, never actual calendar admission."""
from datetime import date
from hashlib import sha256
from html.parser import HTMLParser
from io import BytesIO
import re

SOURCES = {
    'nyfed_oct2026': ('nyfed-oct2026.html',117497,
        '86ed87d3d824da61cf3f97042f7609a9e75660f61c7a696b21eb2e636a46dfa0',
        'https://www.newyorkfed.org/research/calendars/i-oct26.html'),
    'nyfed_dec2026': ('nyfed-dec2026.html',112312,
        '62b208375a57b8740afe9ae5effe9af762ebdb4b5a06c88eab87410e50df5f78',
        'https://www.newyorkfed.org/research/calendars/i-dec26.html'),
    'omb_2026': ('omb-2026-pfei.pdf',266111,
        '5d2c16011a816bc527f628c1e20ff781ed309ed5de55c262ba7ba5bb7718c734',
        'https://www.whitehouse.gov/wp-content/uploads/2025/09/pfei_schedule_release_dates_cy2026.pdf'),
}
MONTHS = {'2026-10':('October 2026',('GDP',)), '2026-12':('December 2026',('U3','CPI'))}
LABELS = {'GDP':('Gross Domestic Product 1st Release','https://www.bea.gov/data/gdp/gross-domestic-product'),
          'U3':('Employment Situation','https://www.bls.gov/news.release/empsit.toc.htm'),
          'CPI':('Consumer Price Index','https://www.bls.gov/news.release/cpi.toc.htm')}


def normal(text):
    return ' '.join(text.split())


class _CalendarHTML(HTMLParser):
    """Retain data-table headings and day cells, including all anchor boundaries."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[];self.active=None;self.cells=[];self.headers=[];self.text=[]

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='td':
            if self.active is not None:
                raise ValueError('nested calendar cell unsupported')
            classes=attrs.get('class','').split()
            mode='day' if any(c.startswith('somatd') for c in classes) else (
                 'header' if 'ts-data-table-head' in classes else None)
            cell={'mode':mode,'parts':[],'anchors':[],'anchor':None} if mode else None
            self.stack.append(cell)
            self.active=cell
        elif tag=='a' and self.active is not None and self.active['mode']=='day':
            if self.active['anchor'] is not None:
                raise ValueError('nested anchor unsupported')
            self.active['anchor']={'href':attrs.get('href'),'text':[],
                                   'start':len(self.active['parts'])}

    def handle_data(self,data):
        self.text.append(data)
        if self.active is not None:
            self.active['parts'].append(data)
            if self.active['anchor'] is not None:
                self.active['anchor']['text'].append(data)

    def handle_endtag(self,tag):
        if tag=='a' and self.active is not None and self.active['anchor'] is not None:
            anchor=self.active['anchor'];anchor['end']=len(self.active['parts'])
            self.active['anchors'].append(anchor);self.active['anchor']=None
        elif tag=='td' and self.stack:
            cell=self.stack.pop()
            if cell is not None:
                if cell['anchor'] is not None:
                    raise ValueError('unclosed calendar anchor')
                (self.cells if cell['mode']=='day' else self.headers).append(cell)
            self.active=None


def parse_nyfed_month(text,month):
    if type(text) is not str or len(text)>2*1024*1024 or month not in MONTHS:
        raise ValueError('fixed retained month required')
    parser=_CalendarHTML();parser.feed(text);parser.close()
    heading,series=MONTHS[month]
    headers=[normal(' '.join(cell['parts'])) for cell in parser.headers]
    if headers!=[heading] or parser.active is not None:
        raise ValueError('unique retained month heading required')
    flat=normal(' '.join(parser.text))
    if ('all Eastern Time' not in flat
            or 'Dates and times are tentative and subject to immediate change.' not in flat):
        raise ValueError('timezone and tentative declarations required')
    result={}
    for key in series:
        label,href=LABELS[key];matches=[]
        for index,cell in enumerate(parser.cells,1):
            anchors=cell['anchors'];parts=cell['parts']
            for n,anchor in enumerate(anchors):
                if normal(' '.join(anchor['text']))!=label:
                    continue
                day_text=normal(' '.join(parts[:anchors[0]['start']]))
                if re.fullmatch(r'[0-9]{1,2}',day_text) is None or anchor['href']!=href:
                    raise ValueError('day or indicator link differs')
                end=anchors[n+1]['start'] if n+1<len(anchors) else len(parts)
                following=normal(' '.join(parts[anchor['end']:end]))
                match=re.fullmatch(r'\(([0-9]{2}):([0-9]{2})\)',following)
                if not match or int(match[1])>23 or int(match[2])>59:
                    raise ValueError('own adjacent indicator time required')
                when=date(int(month[:4]),int(month[-2:]),int(day_text))
                matches.append({'scheduled_date_declaration':when.isoformat(),
                    'scheduled_time_declaration':match[1]+':'+match[2],
                    'timezone_declaration':'Eastern Time','schedule_tentative':True,
                    'nyfed_month_heading':heading,'nyfed_indicator_label':label,
                    'nyfed_declared_external_href':href,'nyfed_cell_index_1_based':index,
                    'nyfed_cell_index_basis':'DAY_CELLS_WITH_SOMATD_CLASS_IN_DOCUMENT_ORDER',
                    'nyfed_cell_text':normal(' '.join(parts))})
        if len(matches)!=1:
            raise ValueError('unique expected indicator required')
        result[key]=matches[0]
    return result


def parse_omb_pages(page3,page4,*,year=2026,annual=False):
    if type(year) is not int or year not in (2026,2027) or type(annual) is not bool:
        raise ValueError('supported finite edition required')
    pages=[]
    heading='SCHEDULE OF RELEASE DATES FOR PRINCIPAL FEDERAL ECONOMIC INDICATORS FOR '+str(year)
    for text in (page3,page4):
        if type(text) is not str or len(text)>2*1024*1024:
            raise ValueError('bounded page text required')
        text=normal(text)
        if text.count(heading)!=1 or 'JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC' not in text:
            raise ValueError('fixed OMB edition and columns required')
        pages.append(text)
    sections=re.findall(r'Gross Domestic Product \(Advance, second, and third estimates '
                        r'are issued for each quarter\) (.*?) Corporate Profits',pages[0])
    if len(sections)!=1:
        raise ValueError('unique GDP annual row required')
    pairs=re.findall(r'([0-9]+) ([1-4])Q\x27([0-9]{2})',sections[0])
    wanted=[('4',str(year-1)[-2:])]*3+[(str(q),str(year)[-2:]) for q in (1,2,3) for _ in range(3)]
    if len(pairs)!=12 or [(q,y) for _,q,y in pairs]!=wanted:
        raise ValueError('GDP quarter columns differ')
    annual_rows={'GDP':[]}
    for i,(day,quarter,y) in enumerate(pairs,1):
        when=date(year,i,int(day))
        annual_rows['GDP'].append({'scheduled_date_declaration':when.isoformat(),
            'reference_period':'20'+y+'-Q'+quarter,'omb_page_1_based':3,'omb_row':'Gross Domestic Product',
            'omb_month_column_1_based':i,'omb_day_declaration':day,
            'release_stage':('Advance','Second','Third')[(i-1)%3],
            'reference_period_basis':'OMB_EXPLICIT_QUARTER_COLUMN_AND_ESTIMATE_POSITION'})
    day,q,y=pairs[9]
    result={'GDP':{'scheduled_date_declaration':date(year,10,int(day)).isoformat(),
                   'reference_period':'20'+y+'-Q'+q,'omb_page_1_based':3,
                   'omb_row':'Gross Domestic Product','omb_month_column_1_based':10,
                   'omb_day_declaration':day,'release_stage':'Advance',
                   'reference_period_basis':'OMB_EXPLICIT_QUARTER_COLUMN_AND_FIRST_ESTIMATE_POSITION'}}
    for key,label,following in [('U3','The Employment Situation','Producer Price Indexes'),
                                ('CPI','Consumer Price Index','Real Earnings')]:
        pattern=(re.escape(label)+r' \(Data are for previous month\) '
                 r'([0-9]+(?: [0-9]+){11}) '+re.escape(following))
        matches=re.findall(pattern,pages[1])
        if len(matches)!=1:
            raise ValueError('unique previous-month annual row required')
        days=matches[0].split()
        annual_rows[key]=[]
        for i,day in enumerate(days,1):
            when=date(year,i,int(day));reference=date(year-1,12,1) if i==1 else date(year,i-1,1)
            annual_rows[key].append({'scheduled_date_declaration':when.isoformat(),
                'reference_period':reference.strftime('%Y-%m'),'omb_page_1_based':4,'omb_row':label,
                'omb_month_column_1_based':i,'omb_day_declaration':day,'release_stage':'Scheduled release',
                'reference_period_basis':'OMB_PREVIOUS_MONTH_NOTE_APPLIED_TO_MONTH_COLUMN'})
        result[key]={'scheduled_date_declaration':date(year,12,int(days[11])).isoformat(),
                     'reference_period':str(year)+'-11','omb_page_1_based':4,'omb_row':label,
                     'omb_month_column_1_based':12,'omb_day_declaration':days[11],
                     'release_stage':'Scheduled first release',
                     'reference_period_basis':'OMB_PREVIOUS_MONTH_NOTE_APPLIED_TO_DECEMBER_COLUMN'}
    return annual_rows if annual else result


def join_declarations(nyfed_by_series,omb_by_series):
    if (type(nyfed_by_series) is not dict or type(omb_by_series) is not dict
            or set(nyfed_by_series)!=set(LABELS) or set(omb_by_series)!=set(LABELS)):
        raise ValueError('all three finite declared series required')
    rows=[]
    for key in ('GDP','U3','CPI'):
        left,right=nyfed_by_series[key],omb_by_series[key]
        if (type(left['scheduled_date_declaration']) is not str
                or left['scheduled_date_declaration']!=right['scheduled_date_declaration']):
            raise ValueError('calendar date declarations disagree')
        rows.append(dict(right,**{k:v for k,v in left.items() if k!='scheduled_date_declaration'},
                         series=key,reference_period_directly_declared_by_nyfed=False))
    return rows


def observe_predecessor_calendars(raw_by_role):
    if type(raw_by_role) is not dict or set(raw_by_role)!=set(SOURCES):
        raise ValueError('three fixed originals required')
    for key,(_,size,digest,_) in SOURCES.items():
        raw=raw_by_role[key]
        if type(raw) is not bytes or len(raw)!=size or sha256(raw).hexdigest()!=digest:
            raise ValueError('outside exact retained source identity')
    from pypdf import PdfReader
    reader=PdfReader(BytesIO(raw_by_role['omb_2026']),strict=True)
    if reader.is_encrypted or len(reader.pages)!=5:
        raise ValueError('fixed five-page unencrypted OMB PDF required')
    omb=parse_omb_pages(reader.pages[2].extract_text(),reader.pages[3].extract_text())
    nyfed=parse_nyfed_month(raw_by_role['nyfed_oct2026'].decode('utf-8'),'2026-10')
    nyfed.update(parse_nyfed_month(raw_by_role['nyfed_dec2026'].decode('utf-8'),'2026-12'))
    return {'predecessor_markers':join_declarations(nyfed,omb),
            'sources':[{'role':key,'file':name,'bytes':size,'sha256':digest,'source_url':url}
                       for key,(name,size,digest,url) in SOURCES.items()],
            'evidence_class':'OFFICIAL_COMPILATION_PLANNING_DECLARATIONS_NOT_ADMITTED_SOURCE',
            'coverage':'THREE_FIXED_PREDECESSOR_DECLARATIONS_ONLY_NOT_COMPLETE_CALENDAR',
            'source_independence':'NOT_ESTABLISHED','mandatory_universe':'NOT_ESTABLISHED',
            'q1_2027_cpi_u3_time_rows_supplied':0,'operational_bindings_established':0,
            'actual_source_admission_established':False,'actual_scope_selected':False,
            'external_links_followed':False,'value_obtained':False,'publication_event_verified':False,
            'authenticated_availability_established':False,'utc_deadline_computed':False,
            'real_admission':'NOT_READY','prospective_eligible':False,'protocol_state_change':'NONE'}
