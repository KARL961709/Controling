# -*- coding: utf-8 -*-
"""PPTX nativo y editable del deck de buckets (4 slides) — replica
presentacion_buckets_v1v2v3.html con tablas/formas/textos reales."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

GREEN_DEEP=RGBColor(0x1F,0x51,0x30); GREEN_DEEP2=RGBColor(0x26,0x60,0x3A)
GREEN=RGBColor(0x1A,0xA4,0x4C); GREEN_BRIGHT=RGBColor(0x1A,0x98,0x50)
GREEN_TEAL=RGBColor(0x3A,0x7D,0x5C); GREEN_SOFT=RGBColor(0xE8,0xF5,0xEE)
TH_BG=RGBColor(0x0A,0x5A,0x44); GRAY_TITLE=RGBColor(0x9A,0xA6,0xA0)
GRAY_TXT=RGBColor(0x5B,0x6F,0x66); INK=RGBColor(0x14,0x27,0x1D)
MONO_INK=RGBColor(0x23,0x43,0x3C); WHITE=RGBColor(0xFF,0xFF,0xFF)
CARD_LINE=RGBColor(0xE7,0xEE,0xE9); BORDER="DDE7E4"
TOT_BG=RGBColor(0xCF,0xE9,0xE4); TOT_INK=RGBColor(0x08,0x4B,0x44)
RJ_BG=RGBColor(0xEC,0xEF,0xF0); RJ_INK=RGBColor(0x4A,0x5A,0x56)
TOTC_BG=RGBColor(0xDF,0xF0,0xED); TOTC_INK=RGBColor(0x0A,0x5A,0x52)
FONT="Segoe UI"; MONO="Consolas"

def hsl(h, s=0.60, l=0.78):
    c=(1-abs(2*l-1))*s; x=c*(1-abs((h/60.0)%2-1)); m=l-c/2
    if   h<60:  r,g,b=c,x,0
    elif h<120: r,g,b=x,c,0
    elif h<180: r,g,b=0,c,x
    elif h<240: r,g,b=0,x,c
    elif h<300: r,g,b=x,0,c
    else:       r,g,b=c,0,x
    return RGBColor(int((r+m)*255), int((g+m)*255), int((b+m)*255))

BUCK = [hsl(130-(k)/6.0*130) for k in range(7)]   # B1..B7 verde->rojo

prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
BLANK=prs.slide_layouts[6]

def rrect(s,x,y,w,h,fill,line=None,radius=0.12,lw=1.0):
    sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
    try: sh.adjustments[0]=max(0.0,min(0.5,radius/min(w,h)))
    except Exception: pass
    sh.fill.solid(); sh.fill.fore_color.rgb=fill
    if line is None: sh.line.fill.background()
    else: sh.line.color.rgb=line; sh.line.width=Pt(lw)
    sh.shadow.inherit=False; return sh

def rect(s,x,y,w,h,fill):
    sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb=fill; sh.line.fill.background(); sh.shadow.inherit=False; return sh

def tb(s,x,y,w,h,runs,size=12,color=INK,bold=False,align=PP_ALIGN.LEFT,anchor=MSO_ANCHOR.TOP,font=FONT,ls=1.0):
    bx=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h)); tf=bx.text_frame; tf.word_wrap=True
    tf.margin_left=0; tf.margin_right=0; tf.margin_top=0; tf.margin_bottom=0; tf.vertical_anchor=anchor
    p=tf.paragraphs[0]; p.alignment=align
    if ls: p.line_spacing=ls
    if isinstance(runs,str): runs=[(runs,{})]
    for t,st in runs:
        r=p.add_run(); r.text=t; r.font.size=Pt(st.get('sz',size)); r.font.bold=st.get('b',bold)
        r.font.name=st.get('f',font); r.font.color.rgb=st.get('c',color)
    return bx

def set_border(cell,color=BORDER,w=9525):
    tcPr=cell._tc.get_or_add_tcPr()
    for tag in ('a:lnB','a:lnT','a:lnR','a:lnL'):
        for el in tcPr.findall(qn(tag)): tcPr.remove(el)
        ln=tcPr.makeelement(qn(tag),{'w':str(w),'cap':'flat'})
        sf=tcPr.makeelement(qn('a:solidFill'),{}); cl=tcPr.makeelement(qn('a:srgbClr'),{'val':color})
        sf.append(cl); ln.append(sf); tcPr.insert(0,ln)

def cell(c,runs,size=11,color=INK,bold=False,align=PP_ALIGN.CENTER,fill=None,font=FONT,anchor=MSO_ANCHOR.MIDDLE,mgn=0.03,nowrap=False):
    if fill is not None: c.fill.solid(); c.fill.fore_color.rgb=fill
    else: c.fill.background()
    c.vertical_anchor=anchor; c.margin_left=Inches(0.06); c.margin_right=Inches(0.05)
    c.margin_top=Inches(mgn); c.margin_bottom=Inches(mgn)
    tf=c.text_frame; tf.word_wrap=(not nowrap)
    p=tf.paragraphs[0]; p.alignment=align
    if isinstance(runs,str): runs=[(runs,{})]
    first=True
    for t,st in runs:
        r=p.runs[0] if (first and p.runs) else p.add_run(); first=False
        r.text=t; r.font.size=Pt(st.get('sz',size)); r.font.bold=st.get('b',bold)
        r.font.name=st.get('f',font); r.font.color.rgb=st.get('c',color)
    set_border(c)

def card(s,x,y,w,h,title,hcolor=GREEN_DEEP,sub=None,hh=0.34):
    rrect(s,x,y,w,h,WHITE,line=CARD_LINE,radius=0.12)
    rrect(s,x,y,w,hh,hcolor,radius=0.12); rect(s,x,y+hh-0.13,w,0.13,hcolor)
    runs=[(title,{'b':True,'sz':13,'c':WHITE})]
    if sub: runs.append(("   "+sub,{'sz':10.5,'c':WHITE}))
    tb(s,x+0.15,y,w-0.3,hh,runs,anchor=MSO_ANCHOR.MIDDLE)
    return x+0.14,y+hh+0.07,w-0.28

def header(s,title_runs,subtitle,badge):
    tb(s,0.46,0.26,9.8,0.5,title_runs,size=25,bold=True,anchor=MSO_ANCHOR.MIDDLE)
    tb(s,0.46,0.78,10.0,0.3,subtitle,size=11,color=GRAY_TXT,anchor=MSO_ANCHOR.MIDDLE)
    bw=2.5; rrect(s,13.333-0.46-bw,0.28,bw,0.42,GREEN_SOFT,radius=0.21)
    tb(s,13.333-0.46-bw,0.28,bw,0.42,[("●  ",{'c':GREEN,'b':True,'sz':10}),(badge,{'c':GREEN_DEEP,'b':True,'sz':11})],align=PP_ALIGN.CENTER,anchor=MSO_ANCHOR.MIDDLE)

def footer(s,items):
    rect(s,0.46,7.02,13.333-0.92,0.012,RGBColor(0xE3,0xEC,0xE7))
    runs=[]
    for i,(lead,rest) in enumerate(items):
        if i: runs.append(("      ",{}))
        runs.append((lead,{'b':True,'c':GREEN_DEEP2,'sz':8})); runs.append((rest,{'c':GRAY_TITLE,'sz':8}))
    tb(s,0.46,7.08,13.333-0.92,0.34,runs,size=8,color=GRAY_TITLE)

def add_slide(): return prs.slides.add_slide(BLANK)

# ---- tablas reutilizables ----
def th_row(t,row,headers,widths):
    for j,(htxt,al,sp) in enumerate(headers):
        fill=TH_BG; col=WHITE
        if sp=='rj': fill=RJ_BG; col=RJ_INK
        if sp=='tot': fill=TOTC_BG; col=TOTC_INK
        cell(t.cell(row,j),htxt,size=10.5,color=col,bold=True,fill=fill,align=al)

def buckcell(c,label,hue_idx,size=10.5,mgn=0.03):
    cell(c,label,size=size,color=INK,bold=True,fill=BUCK[hue_idx],align=PP_ALIGN.CENTER,mgn=mgn)

# ====== datos ======
TASA_24=[("B1","1, 2, 3","16.89%","1,403","3.1%"),("B2","4, 5","20.56%","214","0.5%"),
 ("B3","6, 7, 8, 9, 10","20.75%","32,719","72.0%"),("B4","11, 12, 13","21.41%","4,611","10.1%"),
 ("B5","14, 15, 16, 17","27.28%","942","2.1%"),("B6","18, 19","26.86%","4,318","9.5%"),
 ("B7","20, 21","26.92%","1,252","2.8%")]
TASA_24_TOT=("21 estrat.","21.58%","45,459","100%")
V2_24=[("19,103","3.3%","0.330","669.9"),("19,102","3.3%","0.354","646.0"),("76,066","13.0%","0.395","604.9"),
 ("150,105","25.8%","0.422","577.2"),("245,492","42.1%","0.446","553.4"),("53,558","9.2%","0.463","536.9"),
 ("19,501","3.3%","0.482","517.5")]; V2_24_TOT=("582,927","100%","0.429","570.4"); V2_24_RJ=None
V3_24=[("13,317","2.5%","0.337","663.0"),("13,673","2.6%","0.363","636.3"),("57,746","11.0%","0.404","595.7"),
 ("125,534","24.0%","0.430","569.3"),("240,860","46.0%","0.447","552.1"),("52,916","10.1%","0.463","536.2"),
 ("19,438","3.7%","0.482","517.3")]; V3_24_TOT=("523,484","100%","0.436","563.2"); V3_24_RJ=None
V1_24=[("20260617","11,889","8,486","20,120","26,544","5,363","615","57","0","73,074"),
 ("20260623","10,310","6,806","17,009","21,140","3,942","472","42","0","59,721"),
 ("20260624","10,316","6,807","17,007","21,133","3,930","472","42","0","59,707")]
V1_24_TOT=("Total","32,515","22,099","54,136","68,817","13,235","1,559","141","0","192,502")

TASA_5=[("B1","1","16.82%","1,290","2.8%"),("B2","2, 3","19.75%","319","0.7%"),
 ("B3","5, 6, 7","20.75%","32,661","71.8%"),("B4","9, 10","18.26%","115","0.3%"),
 ("B5","12","21.46%","4,562","10.0%"),("B6","13, 14","26.96%","6,496","14.3%"),
 ("B7","15","18.75%","16","0.0%")]
TASA_5_TOT=("15 estrat.","21.58%","45,459","100%")
V2_5=[("12,897","0.8%","0.321","678.5"),("38,249","2.3%","0.355","645.0"),("230,088","13.6%","0.388","611.5"),
 ("86,196","5.1%","0.400","599.2"),("533,913","31.4%","0.409","590.9"),("612,572","36.1%","0.429","570.6"),
 ("158,251","9.3%","0.446","553.3")]; V2_5_RJ=("25,509","1.5%","0.380","619.2"); V2_5_TOT=("1,697,675","100%","0.414","585.6")
V3_5=[("9,525","0.6%","0.335","665.0"),("33,778","2.0%","0.362","637.5"),("212,618","12.9%","0.393","606.9"),
 ("82,531","5.0%","0.403","596.3"),("522,188","31.7%","0.410","589.6"),("607,375","36.8%","0.429","570.1"),
 ("157,434","9.5%","0.447","552.8")]; V3_5_RJ=("24,225","1.5%","0.384","615.4"); V3_5_TOT=("1,649,674","100%","0.416","583.3")
V1_5=[("20260617","4,096","4,844","16,199","3,246","10,580","4,779","754","1,398","45,896"),
 ("20260623","3,728","4,276","14,059","2,813","10,099","4,492","740","1,213","41,420"),
 ("20260624","3,723","4,269","14,052","2,809","10,097","4,486","740","1,211","41,387")]
V1_5_TOT=("Total","11,547","13,389","44,310","8,868","30,776","13,757","2,234","3,822","128,703")

REGLAS_24=[("B1",0,[("1","segmentacion_gdp_v2 ≤ 2.5 & rk_ing_num > 3,383.5","16.8%","2.8%","1,294"),
  ("2","segmentacion_gdp_v2 (2.5, 3.5] & rk_ing_num > 3,383.5 & meses_desde_primer_castigo > 22.5","16.5%","0.2%","79"),
  ("3","segmentacion_gdp_v2 (2.5, 3.5] & rk_ing_num > 3,383.5 & meses_desde_primer_castigo ≤ 22.5","20.0%","0.1%","30")]),
 ("B2",1,[("4","segmentacion_gdp_v2 (3.5, 4.5] & rk_ing_num > 3,383.5 & meses_desde_primer_castigo > 22.5","19.0%","0.3%","158"),
  ("5","segmentacion_gdp_v2 (3.5, 4.5] & rk_ing_num > 3,383.5 & meses_desde_primer_castigo ≤ 22.5","25.0%","0.1%","56")]),
 ("B3",2,[("6","segmentacion_gdp_v2 ≤ 3.5 & rk_ing_num (3,088.5, 3,383.5]","17.3%","0.7%","301"),
  ("7","segmentacion_gdp_v2 ≤ 3.5 & rk_ing_num (2,746.5, 3,088.5]","20.5%","1.2%","533"),
  ("8","segmentacion_gdp_v2 ≤ 3.5 & rk_ing_num (1,411.5, 2,746.5] & meses_desde_primer_castigo > 22.5","19.1%","4.6%","2,071"),
  ("9","segmentacion_gdp_v2 ≤ 3.5 & rk_ing_num (1,411.5, 2,746.5] & meses_desde_primer_castigo ≤ 22.5","20.1%","1.6%","730"),
  ("10","segmentacion_gdp_v2 ≤ 3.5 & rk_ing_num ≤ 1,411.5","20.9%","64.0%","29,084")]),
 ("B4",3,[("11","segmentacion_gdp_v2 (3.5, 4.5] & rk_ing_num (2,910.5, 3,383.5]","23.7%","0.2%","97"),
  ("12","segmentacion_gdp_v2 (3.5, 4.5] & rk_ing_num (2,746.5, 2,910.5]","15.7%","0.1%","51"),
  ("13","segmentacion_gdp_v2 (3.5, 4.5] & rk_ing_num ≤ 2,746.5","21.4%","9.8%","4,463")]),
 ("B5",4,[("14","segmentacion_gdp_v2 > 4.5 & rk_ing_num > 2,746.5 & meses_desde_primer_castigo > 22.5","26.4%","0.6%","269"),
  ("15","segmentacion_gdp_v2 > 4.5 & rk_ing_num > 2,746.5 & meses_desde_primer_castigo (9.5, 22.5]","17.6%","0.2%","74"),
  ("16","segmentacion_gdp_v2 > 4.5 & rk_ing_num > 2,746.5 & meses_desde_primer_castigo ≤ 9.5","20.0%","0.0%","5"),
  ("17","segmentacion_gdp_v2 > 4.5 & rk_ing_num (1,348.5, 2,746.5] & meses_desde_primer_castigo > 22.5","29.0%","1.3%","594")]),
 ("B6",5,[("18","segmentacion_gdp_v2 > 4.5 & rk_ing_num ≤ 1,348.5 & meses_desde_primer_castigo > 22.5","26.8%","9.1%","4,155"),
  ("19","segmentacion_gdp_v2 > 4.5 & rk_ing_num (1,348.5, 2,746.5] & meses_desde_primer_castigo (9.5, 22.5]","28.2%","0.4%","163")]),
 ("B7",6,[("20","segmentacion_gdp_v2 > 4.5 & rk_ing_num ≤ 1,348.5 & meses_desde_primer_castigo (9.5, 22.5]","27.5%","2.5%","1,152"),
  ("21","segmentacion_gdp_v2 > 4.5 & rk_ing_num ≤ 2,746.5 & meses_desde_primer_castigo ≤ 9.5","20.0%","0.2%","100")])]

REGLAS_5=[("B1",0,[("1","segmentacion_gdp_v2 ≤ 2.5 & rk_ing_num > 3,391.5","16.8%","2.8%","1,290")]),
 ("B2",1,[("2","segmentacion_gdp_v2 (2.5, 3.5] & rk_ing_num > 3,391.5 & nro_entidades_castigo ≤ 1.5","17.4%","0.2%","109"),
  ("3","segmentacion_gdp_v2 (3.5, 4.5] & rk_ing_num > 3,391.5 & nro_entidades_castigo ≤ 1.5","21.0%","0.5%","210")]),
 ("B3",2,[("5","segmentacion_gdp_v2 ≤ 3.5 & rk_ing_num ≤ 3,391.5 & nro_entidades_castigo ≤ 1.5 & deuda_cas ≤ 218.33","20.3%","23.8%","10,802"),
  ("6","segmentacion_gdp_v2 ≤ 3.5 & rk_ing_num (3,100.5, 3,391.5] & nro_entidades_castigo ≤ 1.5 & deuda_cas > 218.33","21.6%","0.4%","185"),
  ("7","segmentacion_gdp_v2 ≤ 3.5 & rk_ing_num ≤ 3,100.5 & nro_entidades_castigo ≤ 1.5 & deuda_cas > 218.33","21.0%","47.7%","21,674")]),
 ("B4",3,[("9","segmentacion_gdp_v2 ≤ 3.5 & rk_ing_num ≤ 3,100.5 & nro_entidades_castigo > 1.5","21.0%","0.1%","62"),
  ("10","segmentacion_gdp_v2 (3.5, 4.5] & rk_ing_num (3,100.5, 3,391.5] & nro_entidades_castigo ≤ 1.5","15.1%","0.1%","53")]),
 ("B5",4,[("12","segmentacion_gdp_v2 (3.5, 4.5] & rk_ing_num ≤ 3,100.5","21.5%","10.0%","4,562")]),
 ("B6",5,[("13","segmentacion_gdp_v2 > 4.5 & nro_entidades_castigo ≤ 1.5 & deuda_cas ≤ 218.33","26.7%","4.0%","1,818"),
  ("14","segmentacion_gdp_v2 > 4.5 & nro_entidades_castigo ≤ 1.5 & deuda_cas > 218.33","27.1%","10.3%","4,678")]),
 ("B7",6,[("15","segmentacion_gdp_v2 > 4.5 & nro_entidades_castigo > 1.5","18.8%","0.0%","16")])]


def slide_resumen(meses, scn, n_estr, tasa, tasa_tot, v2, v2rj, v2tot, v3, v3rj, v3tot, v1, v1tot):
    s=add_slide()
    header(s,[(f"Buckets · {meses} ",{'c':GREEN_DEEP,'b':True}),("| Tasa de riesgo y distribución V1 / V2 / V3",{'c':GRAY_TITLE,'b':True})],
           [(f"Escenario {scn} · 7 buckets sobre {n_estr} estrategias del Árbol 2 · verde = menor riesgo, rojo = mayor",{'c':GRAY_TXT})], scn)
    TY=1.40; TH=3.28
    # Tasa
    ix,iy,iw=card(s,0.46,TY,4.85,TH,"Tasa de riesgo por bucket")
    t=s.shapes.add_table(9,5,Inches(ix),Inches(iy),Inches(iw),Inches(2.3)).table; t.first_row=False; t.horz_banding=False
    ws=[0.5,1.5,0.85,1.0,iw-0.5-1.5-0.85-1.0]
    for j,wd in enumerate(ws): t.columns[j].width=Inches(wd)
    th_row(t,0,[("Buck.",PP_ALIGN.CENTER,''),("Estrategias",PP_ALIGN.LEFT,''),("Tasa",PP_ALIGN.CENTER,''),("N",PP_ALIGN.CENTER,''),("% tot",PP_ALIGN.CENTER,'')],ws)
    for i,(b,est,ta,n,p) in enumerate(tasa,1):
        buckcell(t.cell(i,0),b,i-1); cell(t.cell(i,1),[(est,{'sz':10})],align=PP_ALIGN.LEFT,mgn=0.025)
        cell(t.cell(i,2),[(ta,{'sz':10})],mgn=0.025); cell(t.cell(i,3),[(n,{'sz':10})],align=PP_ALIGN.RIGHT,mgn=0.025); cell(t.cell(i,4),[(p,{'sz':10})],align=PP_ALIGN.RIGHT,mgn=0.025)
    cell(t.cell(8,0),"Tot",size=10,bold=True,fill=TOT_BG,color=TOT_INK,mgn=0.025); cell(t.cell(8,1),[(tasa_tot[0],{'b':True})],align=PP_ALIGN.LEFT,fill=TOT_BG,color=TOT_INK,mgn=0.025)
    cell(t.cell(8,2),[(tasa_tot[1],{'b':True})],fill=TOT_BG,color=TOT_INK,mgn=0.025); cell(t.cell(8,3),[(tasa_tot[2],{'b':True})],align=PP_ALIGN.RIGHT,fill=TOT_BG,color=TOT_INK,mgn=0.025); cell(t.cell(8,4),[(tasa_tot[3],{'b':True})],align=PP_ALIGN.RIGHT,fill=TOT_BG,color=TOT_INK,mgn=0.025)
    t.rows[0].height=Inches(0.24)
    for i in range(1,9): t.rows[i].height=Inches(0.235)
    # V2 / V3
    for (cx,cw,ttl,data,rj,tot) in [(5.49,3.66,"V2 · Base inicial",v2,v2rj,v2tot),(9.33,3.54,"V3 · Fuera de campaña",v3,v3rj,v3tot)]:
        nrows=1+7+(1 if rj else 0)+1
        ix,iy,iw=card(s,cx,TY,cw,TH,ttl,hcolor=GREEN_BRIGHT)
        tt=s.shapes.add_table(nrows,5,Inches(ix),Inches(iy),Inches(iw),Inches(0.235*nrows)).table; tt.first_row=False; tt.horz_banding=False
        ws2=[0.46,0.96,0.55,0.70,iw-0.46-0.96-0.55-0.70]
        for j,wd in enumerate(ws2): tt.columns[j].width=Inches(wd)
        th_row(tt,0,[("Buck.",PP_ALIGN.CENTER,''),("Cantidad",PP_ALIGN.CENTER,''),("%",PP_ALIGN.CENTER,''),("prob_jd",PP_ALIGN.CENTER,''),("score",PP_ALIGN.CENTER,'')],ws2)
        for i,(cn,pc,pj,sc) in enumerate(data,1):
            buckcell(tt.cell(i,0),f"B{i}",i-1)
            cell(tt.cell(i,1),[(cn,{'sz':10})],align=PP_ALIGN.RIGHT,mgn=0.025); cell(tt.cell(i,2),[(pc,{'sz':10})],align=PP_ALIGN.RIGHT,mgn=0.025)
            cell(tt.cell(i,3),[(pj,{'sz':10})],align=PP_ALIGN.RIGHT,mgn=0.025); cell(tt.cell(i,4),[(sc,{'sz':10})],align=PP_ALIGN.RIGHT,mgn=0.025)
        r=8
        if rj:
            cell(tt.cell(r,0),"Rech.",size=9.5,bold=True,fill=RJ_BG,color=RJ_INK,mgn=0.025)
            for j,v in enumerate(rj,1): cell(tt.cell(r,j),[(v,{'sz':10})],align=PP_ALIGN.RIGHT,fill=RJ_BG,color=RJ_INK,mgn=0.025)
            r=9
        cell(tt.cell(r,0),"Tot",size=10,bold=True,fill=TOT_BG,color=TOT_INK,mgn=0.025)
        for j,v in enumerate(tot,1): cell(tt.cell(r,j),[(v,{'b':True})],align=PP_ALIGN.RIGHT,fill=TOT_BG,color=TOT_INK,mgn=0.025)
        tt.rows[0].height=Inches(0.24)
        for i in range(1,nrows): tt.rows[i].height=Inches(0.235)
    # V1
    VY=TY+TH+0.16
    ix,iy,iw=card(s,0.46,VY,12.41,1.88,"V1 · Base de campañas",hcolor=GREEN_TEAL,sub="· 3 fechas de junio (5 pilotos) × bucket")
    nv=5
    tv=s.shapes.add_table(nv,10,Inches(ix),Inches(iy),Inches(iw),Inches(1.35)).table; tv.first_row=False; tv.horz_banding=False
    bcol=(iw-1.6-1.05-1.05)/7
    wsv=[1.6]+[bcol]*7+[1.05,1.05]
    for j,wd in enumerate(wsv): tv.columns[j].width=Inches(wd)
    hv=[("p_fecinformacion",PP_ALIGN.LEFT,'')]+[(f"B{k}",PP_ALIGN.CENTER,'') for k in range(1,8)]+[("Rechazo",PP_ALIGN.CENTER,'rj'),("Total",PP_ALIGN.CENTER,'tot')]
    th_row(tv,0,hv,wsv)
    for i,row in enumerate(v1,1):
        cell(tv.cell(i,0),[(row[0],{'b':True,'sz':11})],align=PP_ALIGN.LEFT,color=MONO_INK)
        for j in range(1,8): cell(tv.cell(i,j),[(row[j],{'sz':11})],align=PP_ALIGN.RIGHT)
        cell(tv.cell(i,8),[(row[8],{'sz':11})],align=PP_ALIGN.RIGHT,fill=RJ_BG,color=RJ_INK)
        cell(tv.cell(i,9),[(row[9],{'sz':11,'b':True})],align=PP_ALIGN.RIGHT,fill=TOTC_BG,color=TOTC_INK)
    cell(tv.cell(4,0),[("Total",{'b':True})],align=PP_ALIGN.CENTER,fill=TOT_BG,color=TOT_INK)
    for j in range(1,10): cell(tv.cell(4,j),[(v1tot[j],{'b':True})],align=PP_ALIGN.RIGHT,fill=TOT_BG,color=TOT_INK)
    tv.rows[0].height=Inches(0.26)
    for i in range(1,nv): tv.rows[i].height=Inches(0.26)
    footer(s,[("Tasa malos:"," % de target_60_12m=1 en la base de modelamiento (RD, n=45,459)."),
              ("V1:"," base de campañas (5 pilotos) · V2: base de generación · V3: fuera de campaña."),
              ("prob_jd / score:"," promedios por bucket · Rechazo: sin bucket asignado.")])


def slide_reglas(meses, scn, n_estr, reglas, rowh, varsline):
    s=add_slide()
    header(s,[(f"Buckets · {meses} ",{'c':GREEN_DEEP,'b':True}),("| Reglas por bucket",{'c':GRAY_TITLE,'b':True})],
           [(f"Escenario {scn} · {n_estr} estrategias del Árbol 2 agrupadas en 7 buckets · cada regla = una hoja del árbol",{'c':GRAY_TXT})], scn)
    nrows=1+sum(len(g[2]) for g in reglas)
    TY=1.28; hh0=0.26
    ch=0.41+hh0+rowh*(nrows-1)+0.14
    ix,iy,iw=card(s,0.46,TY,12.41,ch,"Reglas por bucket",sub="· estrategia → condición de la hoja → tasa de malos")
    t=s.shapes.add_table(nrows,6,Inches(ix),Inches(iy),Inches(iw),Inches(hh0+rowh*(nrows-1))).table; t.first_row=False; t.horz_banding=False
    ws=[0.5,0.4,iw-0.5-0.4-0.8-0.65-0.85,0.8,0.65,0.85]
    for j,wd in enumerate(ws): t.columns[j].width=Inches(wd)
    th_row(t,0,[("Buck.",PP_ALIGN.CENTER,''),("#",PP_ALIGN.CENTER,''),("Regla (condición de la hoja)",PP_ALIGN.LEFT,''),("Tasa",PP_ALIGN.CENTER,''),("% tot",PP_ALIGN.CENTER,''),("N",PP_ALIGN.CENTER,'')],ws)
    r=1
    for (b,hue,rules) in reglas:
        r0=r
        for (idx,rule,ta,pc,n) in rules:
            cell(t.cell(r,1),[(idx,{'b':True,'sz':9,'c':RGBColor(0x0A,0x5A,0x44)})],mgn=0.02)
            cell(t.cell(r,2),[(rule,{'f':MONO,'sz':8.8,'c':MONO_INK})],align=PP_ALIGN.LEFT,nowrap=True,mgn=0.02)
            cell(t.cell(r,3),[(ta,{'sz':9})],mgn=0.02); cell(t.cell(r,4),[(pc,{'sz':9})],align=PP_ALIGN.RIGHT,mgn=0.02); cell(t.cell(r,5),[(n,{'sz':9})],align=PP_ALIGN.RIGHT,mgn=0.02)
            r+=1
        # merge bucket col
        a=t.cell(r0,0)
        if r-1>r0: a.merge(t.cell(r-1,0))
        buckcell(a,b,hue,size=10,mgn=0.02)
    t.rows[0].height=Inches(hh0)
    for i in range(1,nrows): t.rows[i].height=Inches(rowh)
    footer(s,[("Regla:"," condición de la hoja del Árbol 2 (variables binarizadas con OptBinning)."),
              ("Tasa:"," % de malos de la estrategia · % tot / N: peso y tamaño en la base."),
              ("Variables:"," "+varsline)])


slide_resumen("24 meses","24m_sinedad_6","21",TASA_24,TASA_24_TOT,V2_24,V2_24_RJ,V2_24_TOT,V3_24,V3_24_RJ,V3_24_TOT,V1_24,V1_24_TOT)
slide_reglas("24 meses","24m_sinedad_6","21",REGLAS_24,0.228,"segmentacion_gdp_v2, rk_ing_num, meses_desde_primer_castigo.")
slide_resumen("5 años","5años_sinedad_6","15",TASA_5,TASA_5_TOT,V2_5,V2_5_RJ,V2_5_TOT,V3_5,V3_5_RJ,V3_5_TOT,V1_5,V1_5_TOT)
slide_reglas("5 años","5años_sinedad_6","15",REGLAS_5,0.30,"segmentacion_gdp_v2, rk_ing_num, nro_entidades_castigo, deuda_cas.")

prs.save("/home/user/Controling/presentacion_buckets_v1v2v3.pptx")
print("OK pptx buckets guardado")
