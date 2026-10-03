"""Build the printable presentation from the same content and evidence as React."""
import json
import math
import shutil
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'frontend/src/presentation'
OUT = ROOT / 'output/pdf/SteamScope-Database-Presentation.pdf'
deck = json.loads((DATA / 'deck.json').read_text())
evidence = json.loads((DATA / 'evidence.json').read_text())
source = json.loads((DATA / 'source-audit.json').read_text())
graphs = json.loads((DATA / 'diagrams.json').read_text())
tables = {t['name']: t for t in evidence['tables']}
FONT_DIR = Path(reportlab.__file__).resolve().parent / 'fonts'
pdfmetrics.registerFont(TTFont('Body', str(FONT_DIR / 'Vera.ttf')))
pdfmetrics.registerFont(TTFont('Strong', str(FONT_DIR / 'VeraBd.ttf')))
W, H = 1440, 1000
BG, PANEL, BORDER = '#17111f', '#291d35', '#614375'
TEXT, MUTED, LIME, LAVENDER = '#f5edfa', '#cbb8d8', '#d2fc75', '#c1a2df'
OUT.parent.mkdir(parents=True, exist_ok=True)
c = canvas.Canvas(str(OUT), pagesize=(W, H))
c.setTitle('Behind SteamScope - Database Project Presentation')
c.setAuthor('SteamScope')
c.setSubject('Verified source cleaning, relational schema, SQL, integrity, and transactions')
total = len(deck['slides']) + math.ceil(len(tables) / 4)
page_number = 0


def clean(s):
    return str(s).replace('—', '-').replace('–', '-').replace('→', '->').replace('×', 'x').replace('↗', '').replace('↓', '').replace('’', "'").replace('“', '"').replace('”', '"').replace('\u2011', '-')


def box(x, y, w, h, fill=PANEL, stroke=BORDER, radius=10):
    c.setFillColor(colors.HexColor(fill)); c.setStrokeColor(colors.HexColor(stroke))
    c.roundRect(x, H-y-h, w, h, radius, stroke=1, fill=1)


def para(s, x, y, w, size=18, color=TEXT, bold=False, max_h=None):
    style = ParagraphStyle('p', fontName='Strong' if bold else 'Body', fontSize=size,
                           leading=size*1.45, textColor=colors.HexColor(color), spaceAfter=0)
    p = Paragraph(escape(clean(s)).replace('\n', '<br/>'), style)
    _, h = p.wrap(w, H)
    if max_h is not None and h > max_h + .1:
        raise ValueError(f'Text overflow on page {page_number}: {s[:70]} height {h} > {max_h}')
    if y+h>H-35:
        raise ValueError(f'Text exceeds page {page_number}: {s[:70]}')
    p.drawOn(c, x, H-y-h)
    return h


def line(x1,y1,x2,y2,color=BORDER,width=1):
    c.setStrokeColor(colors.HexColor(color));c.setLineWidth(width)
    c.line(x1,H-y1,x2,H-y2)


def page(chapter,title,lead):
    global page_number
    page_number += 1
    c.setFillColor(colors.HexColor(BG));c.rect(0,0,W,H,fill=1,stroke=0)
    para('STEAMSCOPE / DATABASE PROJECT',52,29,800,11,LAVENDER,True)
    para(f'{page_number:02d} / {total:02d}',1280,29,100,11,LIME,True)
    line(52,58,1388,58)
    para(chapter.upper(),52,80,1300,11,LAVENDER,True)
    used=para(title,52,110,1320,39,TEXT,True,max_h=115)
    para(lead,52,120+used,1310,17,MUTED,max_h=80)


def footer(slide=None):
    line(52,948,1388,948)
    date = datetime.fromisoformat(evidence['captured_at']).strftime('%d %b %Y, %H:%M')
    para(f'Saved database evidence: {date} IST',52,960,650,9,MUTED)
    para('Real catalog / simulated profiles / no live connection required',800,960,590,9,MUTED)
    c.showPage()


def takeaway(text,y=858):
    box(52,y,1336,70,LIME,LIME,7)
    para('THE TAKEAWAY',70,y+10,1200,9,'#31421a',True)
    para(text,70,y+28,1287,14,'#24320f',max_h=40)


def points(slide,top=658):
    for i,(title,text) in enumerate(slide['points']):
        x=52+i*452
        line(x,top,x+422,top,LAVENDER)
        para(f'0{i+1}',x,top+12,100,10,LAVENDER,True)
        para(title,x,top+34,418,17,TEXT,True,max_h=50)
        para(text,x,top+88,415,13,MUTED,max_h=105)


def stats(items,y=265,h=140):
    width=(1336-(len(items)-1)*18)/len(items)
    for i,(value,label) in enumerate(items):
        x=52+i*(width+18)
        box(x,y,width,h)
        para(str(value),x+22,y+17,width-44,42,LIME,max_h=65)
        para(label,x+22,y+86,width-44,13,MUTED,max_h=45)


def table(rows,x,y,w,headings=None,size=13,row_h=40):
    columns=headings or list(rows[0])
    widths=[w/len(columns)]*len(columns)
    # Give names and SQL labels more room than numeric counts.
    if len(columns)==2: widths=[w*.68,w*.32]
    box(x,y,w,row_h*(len(rows)+1),PANEL,BORDER,6)
    at=x
    for name,width in zip(columns,widths):
        para(name.replace('_',' ').upper(),at+12,y+10,width-24,10,LAVENDER,True,max_h=row_h-12);at+=width
    for i,row in enumerate(rows):
        yy=y+(i+1)*row_h;line(x,yy,x+w,yy)
        at=x
        for key,width in zip(columns,widths):
            value=row[key]
            if isinstance(value,int):value=f'{value:,}'
            para(str(value),at+12,yy+8,width-24,size,TEXT,max_h=row_h-12);at+=width


def diagram(kind):
    graph=graphs[kind]
    x0,y0=52,245
    scale=min(970/graph['width'],590/graph['height'])
    nodes={n['name']:n for n in graph['nodes']}
    def pt(x,y):return x0+x*scale,H-y0-y*scale
    for edge in graph['edges']:
        p,ch=nodes[edge['parent']],nodes[edge['child']]
        horizontal=abs(p['x']-ch['x'])>abs(p['y']-ch['y'])
        if horizontal:
            a=[p['x']+(p['width'] if p['x']<ch['x'] else 0),p['y']+p['height']/2]
            b=[ch['x']+(0 if p['x']<ch['x'] else ch['width']),ch['y']+ch['height']/2]
            mid=(a[0]+b[0])/2; controls=[mid,a[1],mid,b[1]]
        else:
            a=[p['x']+p['width']/2,p['y']+p['height']];b=[ch['x']+ch['width']/2,ch['y']]
            mid=(a[1]+b[1])/2;controls=[a[0],mid,b[0],mid]
        path=c.beginPath();path.moveTo(*pt(*a));path.curveTo(*pt(*controls[:2]),*pt(*controls[2:]),*pt(*b))
        c.setStrokeColor(colors.HexColor('#b49ac5'));c.setLineWidth(1.2);c.drawPath(path)
        c.setFont('Body',9);c.setFillColor(colors.HexColor(LIME))
        ax,ay=pt(*a);bx,by=pt(*b)
        c.drawString(ax+(5 if not horizontal or p['x']<ch['x'] else -10),ay+5,'1')
        c.drawString(bx+(-27 if horizontal and p['x']<ch['x'] else 5),by+5,'0..N')
    for n in graph['nodes']:
        xx=x0+n['x']*scale;yy=y0+n['y']*scale
        box(xx,yy,n['width']*scale,n['height']*scale,'#30203d',LAVENDER,5)
        para(n['name'],xx+9,yy+7,n['width']*scale-18,11,TEXT,True,max_h=18)
        for i,field in enumerate(n['fields']):
            para(field,xx+9,yy+26+i*12,n['width']*scale-18,8.2,MUTED,max_h=14)
    x=1045
    para('READ THE MAP',x,247,335,11,LIME,True)
    para('PK = unique row identity\nFK = link to another table\n1 = one parent\n0..N = zero or many child rows',x,277,330,14,MUTED,max_h=120)
    slide=next(s for s in deck['slides'] if s['kind']==kind+'-schema')
    yy=420
    for title,text in slide['points']:
        para(title,x,yy,335,15,TEXT,True,max_h=45)
        h=para(text,x,yy+44,330,12,MUTED,max_h=88)
        yy+=50+h+20
    para('Columns, keys, and delete rules were read from the live database. All 24 tables and 27 foreign keys appear across these two maps.',52,837,930,10,MUTED,max_h=30)


for slide in deck['slides']:
    kind=slide['kind']
    page(slide['chapter'],slide['title'],slide['lead'])
    if kind in ('catalog-schema','player-schema'):
        diagram(kind.split('-')[0]);takeaway(slide['takeaway'],885);footer(slide);continue
    if kind=='intro':
        stats([(f"{tables['game']['count']:,}",'catalog games'),(24,'connected tables'),(f"{tables['user']['count']:,}",'demo profiles')],y=295,h=190)
        para('THE QUESTION THAT STARTED IT',52,530,1300,12,LAVENDER,True)
        para('How do we connect a game someone loves to a game they have not found yet?',52,560,1260,27,TEXT,max_h=80)
    elif kind=='source':
        table([{'heading':'About the game','observed':'Number','expected':'Description'}, {'heading':'Metacritic score','observed':'Boolean','expected':'Score'}, {'heading':'Website','observed':'Image URL','expected':'Website URL'}],52,280,630,row_h=55)
        box(715,280,673,310)
        para('JSON EXCERPT / REAL SOURCE RECORD',738,300,600,11,LIME,True)
        sample=next(s for s in source['samples'] if s['app_id']==730)
        para(f"app_id: 730\nname: {sample['name']}\nrelease_date: {sample['release_date']}\ngenres: Action, Free To Play\ndeveloper: Valve",738,344,605,18,MUTED,max_h=210)
        para('CSV observations are from the early sample notes, not a newly measured corruption rate.',52,535,620,13,MUTED,max_h=70)
    elif kind=='pipeline':
        stats([(f"{source['counts']['records']:,}",'JSON records read'),(1,'unnamed record skipped'),(f"{source['counts']['retained']:,}",'retained games')])
        for i,label in enumerate(['Read JSON','Clean values','Extract names','Load games','Load links','Validate']):
            x=52+i*225;box(x,455,211,115);para(f'0{i+1}',x+16,469,180,22,LAVENDER,True);para(label,x+16,513,180,14,TEXT)
        para('949.6 MB source. Zero duplicate IDs and zero invalid IDs found in this JSON pass.',52,594,1300,13,MUTED)
    elif kind=='cleaning':
        table([{'example':'Trim text (illustrative)','before':'"  Counter-Strike 2  "','after':'"Counter-Strike 2"'}, {'example':'Missing / unreadable','before':'Blank text or invalid number','after':'NULL (unknown)'}, {'example':'Date (source app 730)','before':'Aug 21, 2012','after':'2012-08-21'}, {'example':'Genre list (source app 730)','before':'Action, Free To Play','after':'Two game_genre links'}],52,280,1336,row_h=62,size=14)
        para('Precision note: the loader also accepts month/year dates, which become the first day of that month.',52,612,1300,12,MUTED)
    elif kind=='normalization':
        for x,title in [(52,'GAME'),(505,'GAME_GENRE'),(1005,'GENRE')]:para(title,x,278,400,12,LIME,True)
        table([{'app_id':10,'name':'Counter-Strike'},{'app_id':730,'name':'Counter-Strike 2'}],52,310,420,row_h=60)
        table([{'app_id':10,'genre':'Action'},{'app_id':730,'genre':'Action'},{'app_id':730,'genre':'Free To Play'}],505,310,465,row_h=60)
        table([{'name':'Action'},{'name':'Free To Play'}],1005,310,383,row_h=60)
        para('Teaching view: the real linking table stores genre_id, not the name shown here. One game can have many genres; one genre can describe many games.',52,596,1300,13,MUTED,max_h=48)
    elif kind=='inventory':
        for i,t in enumerate(evidence['tables']):
            x=52+(i%6)*225;y=260+(i//6)*79
            box(x,y,211,69);para(t['name'],x+11,y+8,189,10,LAVENDER,True,max_h=18);para(f"{t['count']:,} rows",x+11,y+32,189,16,LIME,max_h=26)
        para('Important: review has 0 rows. The app uses review totals stored on game, not imported review text.',52,603,1300,13,LAVENDER)
    elif kind=='integrity':
        stats([(len(evidence['foreign_keys']),'declared links checked'),(sum(f['orphans'] for f in evidence['foreign_keys']),'orphan rows found'),(f"{evidence['quality']['unique_ids']:,}",'distinct game IDs')])
        table([{'check':'Missing / blank names','count':int(evidence['quality']['missing_names'])},{'check':'NULL prices','count':int(evidence['quality']['unknown_prices'])},{'check':'NULL release dates','count':int(evidence['quality']['unknown_dates'])}],52,433,700,row_h=43)
        para('These checks found no missing names, prices, or dates. That does not prove the values are up-to-date or free from source placeholders.',800,450,555,20,MUTED,max_h=150)
    elif kind=='queries':
        for i,q in enumerate(evidence['query_examples']):
            x=52+i*680
            para(q['title'],x,263,650,18,LIME,True,max_h=32)
            box(x,307,650,202,'#100b15');para(q['sql'],x+15,322,620,11,MUTED,max_h=177)
            table(q['rows'][:3],x,524,650,row_h=29,size=10)
    elif kind=='recommendations':
        stats([(3,'points per shared tag'),(1,'point per shared genre'),(2,'points per shared developer')])
        box(52,440,650,172);box(726,440,662,172,LAVENDER,LAVENDER)
        para('EXAMPLE / ONE SOURCE GAME',76,460,600,11,LAVENDER,True)
        para('2 shared tags + 1 shared genre\n(2 x 3) + (1 x 1) = 7 points',76,500,600,23,TEXT,max_h=90)
        para('IF THAT SOURCE IS A FAVORITE',750,460,610,11,'#341f45',True)
        para('7 x 3 = 21 points\nA stronger signal from a game you love.',750,500,610,23,'#291838',max_h=90)
    elif kind=='transactions':
        table([{'stage':'Starting state','library':'Absent','wishlist':'Present'}, {'stage':'Changes pending','library':'Added','wishlist':'Removed'}, {'stage':'Success: COMMIT','library':'Present','wishlist':'Absent'}, {'stage':'Failure: ROLLBACK','library':'Absent','wishlist':'Present'}],52,280,1336,row_h=61,size=16)
        para('Illustrative sequence. The interactive version lets you step through success and failure without editing any database rows.',52,611,1300,12,MUTED)
    elif kind=='stack':
        for i,(title,body) in enumerate([('REACT','Shows the interface'),('FASTAPI','Checks the request'),('RAW SQL','Asks the question'),('MYSQL','Stores the facts')]):
            x=52+i*339;box(x,300,320,225);para(f'0{i+1}',x+22,320,275,30,LAVENDER);para(title,x+22,384,275,25,TEXT,True);para(body,x+22,449,275,15,MUTED)
        para('Supporting tools: Python + ijson for recovery, pandas for earlier profiling, Uvicorn for the API server, unittest + HTTPX for checks.',52,572,1300,16,MUTED,max_h=65)
    elif kind=='conclusion':
        box(52,275,1336,337,LAVENDER,LAVENDER)
        para('THE DATABASE IS THE STORY.',85,304,1250,12,'#4f3166',True)
        para('Clean it.\nConnect it.\nBuild on it.',85,345,1200,45,'#2b173b',True,max_h=205)
    elif kind=='evidence':
        rows=[{'evidence':'Source recovery','where':'scripts/clean_games_json.py; scripts/extract_relationships_json.py'},
              {'evidence':'Loading','where':'scripts/load_games.py; scripts/load_relationships.py'},
              {'evidence':'Source audit','where':'scripts/presentation_source_audit.py'},
              {'evidence':'Schema / counts / FK checks','where':'scripts/presentation_snapshot.py'},
              {'evidence':'Queries / transactions','where':'backend/app/routers/ and backend/app/db.py'},
              {'evidence':'Saved evidence for both versions','where':'frontend/src/presentation/*.json'}]
        # Equal-width columns here allow longer paths to wrap.
        table(rows,52,270,1336,row_h=49,size=12)
        para('All evidence paths are relative to the repository root. Original dataset download attribution remains a follow-up. No profile records are exported.',52,595,1300,12,MUTED,max_h=48)
    points(slide);takeaway(slide['takeaway']);footer(slide)

# A readable reference for every column, separate from the plain-language slides.
all_tables=list(evidence['tables'])
for start in range(0,len(all_tables),4):
    page('Appendix / field reference',f'The schema, field by field. ({start//4+1}/6)',
         'Saved database definitions. PK = unique identity; FK = reference; UQ = unique value; ? = missing allowed. No profile rows are included.')
    for i,t in enumerate(all_tables[start:start+4]):
        x=52+(i%2)*680;y=235+(i//2)*348
        box(x,y,656,330)
        para(t['name'],x+16,y+11,620,18,LIME,True,max_h=29)
        para(f"{t['count']:,} rows",x+16,y+40,620,10,MUTED)
        columns=t['columns']; font=9 if len(columns)>20 else 10.5
        gap=min(22,253/max(1,len(columns)))
        for j,col in enumerate(columns):
            fk=any(f['child']==t['name'] and f['child_key']==col['name'] for f in evidence['foreign_keys'])
            flags=('PK ' if col['key']=='PRI' else 'UQ ' if col['key']=='UNI' else '')+('FK ' if fk else '')+('?' if col['nullable']=='YES' else '')
            yy=y+66+j*gap
            para(col['name'],x+16,yy,242,font,TEXT,max_h=gap+1)
            para(col['type'],x+269,yy,286,font,MUTED,max_h=gap+1)
            para(flags,x+567,yy,78,font,LAVENDER,max_h=gap+1)
    footer()
c.save()
public = ROOT / 'frontend/public/presentation' / OUT.name
public.parent.mkdir(parents=True, exist_ok=True)
shutil.copyfile(OUT, public)
print(f'Created {page_number} pages: {OUT}')
