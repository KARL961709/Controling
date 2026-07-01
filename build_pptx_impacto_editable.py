# -*- coding: utf-8 -*-
"""2 PPT EDITABLES (formas + tabla nativa, NO imagen) del simulador de impacto,
como foto del corte (5 años → hasta B3 · 24 meses → hasta B4), cada uno con
botón-hipervínculo al HTML interactivo correspondiente. Umbral fijo: Prob ≤ 35%."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

GREEN_DEEP=RGBColor(0x1F,0x51,0x30); GREEN_DEEP2=RGBColor(0x26,0x60,0x3A)
GREEN=RGBColor(0x1A,0xA4,0x4C); GREEN_BRIGHT=RGBColor(0x22,0xB2,0x4C)
GREEN_TEAL=RGBColor(0x2F,0x7D,0x70); TEALD=RGBColor(0x0A,0x5A,0x44); GREEN_SOFT=RGBColor(0xE8,0xF5,0xEE)
GRAY_TITLE=RGBColor(0x9A,0xA6,0xA0); GRAY_TXT=RGBColor(0x5B,0x6F,0x66); INK=RGBColor(0x14,0x27,0x1D)
WHITE=RGBColor(0xFF,0xFF,0xFF); CARD_LINE=RGBColor(0xE0,0xEB,0xE4); LIGHT=RGBColor(0xEE,0xF4,0xF1)
INCBG=RGBColor(0xEA,0xFA,0xEF); TOTBG=RGBColor(0xDF,0xF0,0xEA); TOTINK=RGBColor(0x0A,0x4B,0x44)
RED=RGBColor(0xD2,0x4B,0x3E); EXC=RGBColor(0x9F,0xB0,0xA8)
FOOT_LINE=RGBColor(0xE3,0xEC,0xE7); FOOT_INK=RGBColor(0x8A,0x9B,0x93); BORDER="EAF1ED"
FONT="Segoe UI"

def hsl(i):
    import colorsys
    h=(130-i/11*130)/360.0
    r,g,b=colorsys.hls_to_rgb(h,0.80,0.60)
    return RGBColor(int(r*255),int(g*255),int(b*255))

# ---- datos por escenario ----
D24=[('B1',24.4,4442,1102,3233,4.55,756),('B2',26.9,7021,708,5668,5.55,730),
     ('B3',28.8,27721,5045,17052,6.69,711),('B4',34.6,26961,5587,18067,10.13,654),
     ('B5',35.1,51215,2983,42440,11.51,649),('B6',40.0,32686,6747,24750,13.40,599),
     ('B7',40.3,132679,5418,121324,12.67,597),('B8',44.4,20663,5167,17990,17.13,555),
     ('B9',45.1,108579,5243,103892,17.69,549),('B10',45.3,28296,145,28128,19.63,547),
     ('B11',51.8,38475,19931,37084,36.96,482),('B12',52.3,104189,1631,103856,40.82,477)]
D5=[('B1',28.2,20304,2358,17656,7.15,718),('B2',31.5,28500,642,27642,8.14,685),
    ('B3',33.5,140065,13937,117373,8.70,664),('B4',35.2,187958,5434,177463,9.42,647),
    ('B5',39.6,114041,4018,110285,13.36,603),('B6',39.8,289713,3483,285437,13.53,602),
    ('B7',40.1,278690,1306,276720,13.17,598),('B8',42.1,86512,1798,85882,17.07,579),
    ('B9',44.9,111032,1049,110728,18.13,550),('B10',45.0,147087,420,146876,19.10,549),
    ('B11',47.8,70579,3300,70510,36.89,522),('B12',52.2,223194,3642,223102,39.68,478)]

SCEN=[
 dict(rows=D24, base_tot=582927, name="24 meses", link="impacto_leads_24m.html", out="presentacion_impacto_24m_editable.pptx"),
 dict(rows=D5,  base_tot=1697675,name="5 años",  link="impacto_leads_slide.html",out="presentacion_impacto_5a_editable.pptx"),
]
THR=35.0
fmt=lambda n:f"{int(round(n)):,}"

def build(sc):
    prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
    s=prs.slides.add_slide(prs.slide_layouts[6])
    def rrect(x,y,w,h,fill,line=None,radius=0.12,lw=1.0):
        sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
        try: sh.adjustments[0]=max(0,min(0.5,radius/min(w,h)))
        except Exception: pass
        sh.fill.solid(); sh.fill.fore_color.rgb=fill
        if line is None: sh.line.fill.background()
        else: sh.line.color.rgb=line; sh.line.width=Pt(lw)
        sh.shadow.inherit=False; return sh
    def tb(x,y,w,h,runs,size=12,color=INK,align=PP_ALIGN.LEFT,anchor=MSO_ANCHOR.TOP,ls=1.05):
        bx=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
        tf=bx.text_frame; tf.word_wrap=True
        tf.margin_left=0;tf.margin_right=0;tf.margin_top=0;tf.margin_bottom=0;tf.vertical_anchor=anchor
        p=tf.paragraphs[0]; p.alignment=align; p.line_spacing=ls
        if isinstance(runs,str):runs=[(runs,{})]
        for t,st in runs:
            r=p.add_run();r.text=t;r.font.size=Pt(st.get('sz',size));r.font.bold=st.get('b',False)
            r.font.name=FONT;r.font.color.rgb=st.get('c',color)
        return bx
    def dline(x1,x2,y):
        cn=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1),Inches(y),Inches(x2),Inches(y))
        cn.line.color.rgb=RED; cn.line.width=Pt(1.6); cn.shadow.inherit=False
        ln=cn.line._get_or_add_ln(); d=ln.makeelement(qn('a:prstDash'),{'val':'dash'}); ln.append(d)
        return cn

    rows=sc['rows']; BT=sc['base_tot']
    inc=[i for i,r in enumerate(rows) if r[1]<=THR+1e-9]; last=inc[-1]
    leads=sum(rows[i][2] for i in inc); camp=sum(rows[i][3] for i in inc); fuera=sum(rows[i][4] for i in inc)
    wp=sum(rows[i][2]*rows[i][1] for i in inc); wt=sum(rows[i][2]*rows[i][5] for i in inc); ws=sum(rows[i][2]*rows[i][6] for i in inc)
    nuevos=leads-camp; mult=leads/camp if camp else 0; meses=6
    probA=wp/leads; tasaA=wt/leads; scoreA=ws/leads

    # encabezado
    tb(0.42,0.26,8.2,0.44,[("Impacto ",{'sz':21,'b':True,'c':GREEN_DEEP}),(f"| Nuevos leads · {sc['name']}",{'sz':21,'b':True,'c':GRAY_TITLE})],anchor=MSO_ANCHOR.MIDDLE)
    tb(0.42,0.74,8.0,0.44,[("Foto del apetito de riesgo: leads elegibles de la ",{'sz':10,'c':GRAY_TXT}),("base inicial",{'sz':10,'b':True,'c':GREEN_DEEP}),
       (", incremento vs. campaña actual y riesgo del pool",{'sz':10,'c':GRAY_TXT})])
    # chip de control estático
    rrect(8.85,0.30,1.95,0.62,LIGHT,line=CARD_LINE,radius=0.10)
    tb(8.99,0.34,1.7,0.24,[("PROB. MÁXIMA ≤",{'sz':8.5,'b':True,'c':GREEN_DEEP})])
    tb(8.99,0.55,1.7,0.30,[(f"{THR:.0f}%",{'sz':16,'b':True,'c':GREEN_DEEP})])
    rrect(10.92,0.30,1.99,0.62,LIGHT,line=CARD_LINE,radius=0.10)
    tb(11.05,0.34,1.8,0.24,[("APETITO RESULTANTE",{'sz':8,'b':True,'c':GREEN_DEEP})])
    tb(11.05,0.55,1.8,0.30,[("hasta ",{'sz':11,'c':GRAY_TXT}),(rows[last][0],{'sz':13,'b':True,'c':GREEN_BRIGHT}),(f" · {len(inc)} buckets",{'sz':9.5,'c':GRAY_TXT})])

    # KPIs (5 tarjetas)
    KX=0.42; KG=0.14; KW=(12.49-4*KG)/5; KY=1.16; KH=1.16
    def kpi(i,fill,tcol,title,val,sub,dark=True):
        x=KX+i*(KW+KG)
        rrect(x,KY,KW,KH,fill,line=(None if dark else CARD_LINE),radius=0.11)
        tc=WHITE if dark else GRAY_TXT; vc=WHITE if dark else GREEN_DEEP
        tb(x+0.14,KY+0.12,KW-0.24,0.34,[(title,{'sz':9.5,'b':True,'c':tc})],ls=1.05)
        tb(x+0.14,KY+0.50,KW-0.24,0.42,[(val,{'sz':23,'b':True,'c':vc})])
        tb(x+0.14,KY+0.92,KW-0.24,0.2,[(sub,{'sz':8.7,'c':(RGBColor(0xE6,0xF3,0xEC) if dark else GRAY_TXT)})])
    kpi(0,GREEN_DEEP,WHITE,"Leads elegibles (base inicial)",fmt(leads),f"{leads/BT*100:.1f}% de la base inicial")
    kpi(1,GREEN_BRIGHT,WHITE,"Nuevos leads (incremento vs. campaña)","+"+fmt(nuevos),f"× {mult:.1f} vs. campaña actual")
    kpi(2,LIGHT,None,"Hoy en campaña (en estos buckets)",fmt(camp),"base de campañas · 20260624",dark=False)
    # tarjeta riesgo (3 mini)
    x=KX+3*(KW+KG); rrect(x,KY,KW,KH,LIGHT,line=CARD_LINE,radius=0.11)
    tb(x+0.14,KY+0.12,KW-0.24,0.3,[("Riesgo del pool seleccionado",{'sz':9.5,'b':True,'c':GRAY_TXT})],ls=1.05)
    mini=[("Prob. prom",f"{probA:.1f}%"),("Tasa malos",f"{tasaA:.1f}%"),("Score",f"{scoreA:.0f}")]
    mw=(KW-0.24)/3
    for j,(k,v) in enumerate(mini):
        mx=x+0.14+j*mw
        tb(mx,KY+0.52,mw,0.18,[(k,{'sz':8.3,'c':GRAY_TXT})])
        tb(mx,KY+0.70,mw,0.30,[(v,{'sz':15,'b':True,'c':GREEN_DEEP})])
    kpi(4,TEALD,WHITE,"Nuevos leads por mes","+"+fmt(nuevos/meses),f"{fmt(leads/meses)} elegibles / mes")

    # tabla nativa
    TX=0.42; TY=2.52; TW=12.49
    gf=s.shapes.add_table(14,7,Inches(TX),Inches(TY),Inches(TW),Inches(0.3)); tbl=gf.table
    tbl.first_row=False; tbl.horz_banding=False
    tbl._tbl.tblPr.set('firstRow','0'); tbl._tbl.tblPr.set('bandRow','0')
    fr=[0.075,0.10,0.175,0.09,0.19,0.175,0.195]
    for i,f in enumerate(fr): tbl.columns[i].width=Inches(TW*f)
    tbl.rows[0].height=Inches(0.26)
    for r in range(1,13): tbl.rows[r].height=Inches(0.265)
    tbl.rows[13].height=Inches(0.28)
    def setb(c,color=BORDER,w=9525):
        tcPr=c._tc.get_or_add_tcPr()
        for tag in ('a:lnB','a:lnT','a:lnR','a:lnL'):
            for el in tcPr.findall(qn(tag)): tcPr.remove(el)
            ln=tcPr.makeelement(qn(tag),{'w':str(w),'cap':'flat'})
            sf=tcPr.makeelement(qn('a:solidFill'),{}); cl=tcPr.makeelement(qn('a:srgbClr'),{'val':color}); sf.append(cl); ln.append(sf); tcPr.insert(0,ln)
    def cell(c,txt,sz=8.6,b=False,col=INK,fill=None,align=PP_ALIGN.RIGHT):
        if fill is not None: c.fill.solid(); c.fill.fore_color.rgb=fill
        else: c.fill.background()
        c.vertical_anchor=MSO_ANCHOR.MIDDLE; c.margin_left=Inches(0.06); c.margin_right=Inches(0.06)
        c.margin_top=Inches(0.01); c.margin_bottom=Inches(0.01)
        tf=c.text_frame; tf.word_wrap=False; p=tf.paragraphs[0]; p.alignment=align
        r=p.add_run(); r.text=txt; r.font.size=Pt(sz); r.font.bold=b; r.font.name=FONT; r.font.color.rgb=col
        setb(c)
    heads=["Buck.","Prob.","Base inicial","% base","Nuevos (fuera camp.)","Hoy en campaña","Score"]
    for j,h in enumerate(heads):
        cell(tbl.cell(0,j),h,sz=8.6,b=True,col=WHITE,fill=GREEN_DEEP,align=(PP_ALIGN.LEFT if j==0 else PP_ALIGN.RIGHT))
    for i,(bk,prob,cant,cmp,fu,ta,sc_) in enumerate(rows):
        r=i+1; on=i in inc
        rowfill=INCBG if on else WHITE
        cell(tbl.cell(r,0),bk+("  ✓" if on else ""),sz=8.6,b=True,col=RGBColor(0x11,0x22,0x33),fill=hsl(i),align=PP_ALIGN.CENTER)
        vals=[f"{prob:.1f}%",fmt(cant),f"{cant/BT*100:.1f}%",fmt(fu),fmt(cmp),f"{sc_}"]
        strong=[True,True,False,False,False,False]
        for j,v in enumerate(vals):
            col=(GREEN_DEEP if (on and strong[j]) else (INK if on else EXC))
            cell(tbl.cell(r,j+1),v,sz=8.6,b=(on and strong[j]),col=col,fill=rowfill)
    # total
    cell(tbl.cell(13,0),f"Incluidos ({len(inc)})",sz=8.6,b=True,col=TOTINK,fill=TOTBG,align=PP_ALIGN.LEFT)
    tvals=[f"{probA:.1f}%",fmt(leads),f"{leads/BT*100:.1f}%",fmt(fuera),fmt(camp),f"{scoreA:.0f}"]
    for j,v in enumerate(tvals): cell(tbl.cell(13,j+1),v,sz=8.6,b=True,col=TOTINK,fill=TOTBG)
    # línea de corte punteada (bajo el último incluido)
    ycut=TY+0.26+(last+1)*0.265
    dline(TX,TX+TW,ycut)

    # botón hipervínculo
    bw,bh=3.55,0.48; bx=(13.333-bw)/2; by=6.48
    btn=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(bx),Inches(by),Inches(bw),Inches(bh))
    btn.adjustments[0]=0.5; btn.fill.solid(); btn.fill.fore_color.rgb=GREEN
    btn.line.color.rgb=GREEN_DEEP; btn.line.width=Pt(1.25); btn.shadow.inherit=False
    tf=btn.text_frame; tf.word_wrap=False; tf.vertical_anchor=MSO_ANCHOR.MIDDLE
    tf.margin_left=0;tf.margin_right=0;tf.margin_top=0;tf.margin_bottom=0
    p=tf.paragraphs[0]; p.alignment=PP_ALIGN.CENTER
    rr=p.add_run(); rr.text="▶  Abrir simulador interactivo (HTML)"; rr.font.size=Pt(13.5); rr.font.bold=True; rr.font.name=FONT; rr.font.color.rgb=WHITE
    btn.click_action.hyperlink.address=sc['link']

    # pie
    cn=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(0.42),Inches(7.06),Inches(12.91),Inches(7.06))
    cn.line.color.rgb=FOOT_LINE; cn.line.width=Pt(1.0); cn.shadow.inherit=False
    tb(0.42,7.13,8.6,0.3,[("Leads elegibles:",{'sz':7.6,'b':True,'c':GREEN_DEEP2}),(" Σ Cantidad de la base inicial con Prob. ≤ "+f"{THR:.0f}%",{'sz':7.6,'c':FOOT_INK}),
       ("  ·  Nuevos:",{'sz':7.6,'b':True,'c':GREEN_DEEP2}),(" elegibles − los que hoy están en campaña.",{'sz':7.6,'c':FOOT_INK})])
    tb(9.3,7.13,3.6,0.3,[("Enlace:",{'sz':7.6,'b':True,'c':GREEN_DEEP2}),(" mantén el HTML junto a este PPT.",{'sz':7.6,'c':FOOT_INK})])

    prs.save(sc['out']); print("OK",sc['out'],"→",sc['link'])

for sc in SCEN: build(sc)
