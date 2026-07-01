# -*- coding: utf-8 -*-
"""PPTX nativo y editable: Rebank · Modelamiento (1 slide).
Ficha técnica (campos) + Resultados Gini (tabla nativa) + Variables SHAP (barras) y fuentes.
Formas nativas: rects + tabla + textos. Nada de imágenes."""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

GREEN_DEEP=RGBColor(0x1F,0x51,0x30); GREEN_DEEP2=RGBColor(0x26,0x60,0x3A)
GREEN=RGBColor(0x1A,0xA4,0x4C); GREEN_BRIGHT=RGBColor(0x22,0xB2,0x4C)
GREEN_TEAL=RGBColor(0x2F,0x7D,0x70); GREEN_SOFT=RGBColor(0xE8,0xF5,0xEE)
GRAY_TITLE=RGBColor(0x9A,0xA6,0xA0); GRAY_TXT=RGBColor(0x5B,0x6F,0x66)
INK=RGBColor(0x14,0x27,0x1D); WHITE=RGBColor(0xFF,0xFF,0xFF)
CARD_LINE=RGBColor(0xE7,0xEE,0xE9); NAVY=RGBColor(0x3D,0x4A,0x63)
BLUE=RGBColor(0x7F,0xB8,0xE0); GRAYPILL=RGBColor(0x9A,0xA6,0xA0)
SRC_BG=RGBColor(0xEE,0xF4,0xF1); SRC_INK=RGBColor(0x26,0x60,0x3A); SRC_LINE=RGBColor(0xDD,0xE8,0xE3)
DL_BG=RGBColor(0xEE,0xF5,0xFB); DL_LINE=RGBColor(0xD8,0xE6,0xF3); DL_INK=RGBColor(0x24,0x5B,0x96); DL_K=RGBColor(0x3A,0x6E,0xA5)
BAR1=RGBColor(0x3F,0xA6,0x4A); TRACK=RGBColor(0xEC,0xF3,0xEE)
HL_BG=RGBColor(0xFF,0xF4,0xE0); HL_LINE=RGBColor(0xF4,0xE2,0xBD); HL_INK=RGBColor(0x9A,0x6A,0x12); HL_INK2=RGBColor(0x7A,0x52,0x00)
FOOT_LINE=RGBColor(0xE3,0xEC,0xE7); FOOT_INK=RGBColor(0x8A,0x9B,0x93); BORDER="EAF1ED"
FONT="Segoe UI"

prs=Presentation(); prs.slide_width=Inches(13.333); prs.slide_height=Inches(7.5)
s=prs.slides.add_slide(prs.slide_layouts[6])

def rrect(x,y,w,h,fill,line=None,radius=0.12,lw=1.0):
    sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
    try: sh.adjustments[0]=max(0.0,min(0.5,radius/min(w,h)))
    except Exception: pass
    sh.fill.solid(); sh.fill.fore_color.rgb=fill
    if line is None: sh.line.fill.background()
    else: sh.line.color.rgb=line; sh.line.width=Pt(lw)
    sh.shadow.inherit=False; return sh
def rect(x,y,w,h,fill,line=None,lw=0.75):
    sh=s.shapes.add_shape(MSO_SHAPE.RECTANGLE,Inches(x),Inches(y),Inches(w),Inches(h))
    if fill is None: sh.fill.background()
    else: sh.fill.solid(); sh.fill.fore_color.rgb=fill
    if line is None: sh.line.fill.background()
    else: sh.line.color.rgb=line; sh.line.width=Pt(lw)
    sh.shadow.inherit=False; return sh
def oval(x,y,w,h,fill):
    sh=s.shapes.add_shape(MSO_SHAPE.OVAL,Inches(x),Inches(y),Inches(w),Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb=fill; sh.line.fill.background(); sh.shadow.inherit=False; return sh
def hline(x1,x2,y,color,w):
    ln=s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,Inches(x1),Inches(y),Inches(x2),Inches(y))
    ln.line.color.rgb=color; ln.line.width=Pt(w); ln.shadow.inherit=False; return ln
def tb(x,y,w,h,runs,size=12,color=INK,bold=False,align=PP_ALIGN.LEFT,anchor=MSO_ANCHOR.TOP,ls=1.05):
    bx=s.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h))
    tf=bx.text_frame; tf.word_wrap=True
    tf.margin_left=0;tf.margin_right=0;tf.margin_top=0;tf.margin_bottom=0;tf.vertical_anchor=anchor
    p=tf.paragraphs[0]; p.alignment=align
    if ls:p.line_spacing=ls
    if isinstance(runs,str):runs=[(runs,{})]
    for t,st in runs:
        r=p.add_run();r.text=t;r.font.size=Pt(st.get('sz',size));r.font.bold=st.get('b',bold)
        r.font.name=FONT;r.font.color.rgb=st.get('c',color)
    return bx
def srcchips(x,y,labels,size=7):
    cx=x
    for lb in labels:
        w=0.14+len(lb)*(size*0.0092)
        rrect(cx,y,w,0.19,SRC_BG,line=SRC_LINE,radius=0.09,lw=0.6)
        tb(cx,y,w,0.19,[(lb,{'sz':size,'b':True,'c':SRC_INK})],align=PP_ALIGN.CENTER,anchor=MSO_ANCHOR.MIDDLE)
        cx+=w+0.05

# ---------- Encabezado ----------
tb(0.42,0.26,11.0,0.46,[("Rebank ",{'sz':21,'b':True,'c':GREEN_DEEP}),("| Modelamiento",{'sz':21,'b':True,'c':GREEN_BRIGHT})],anchor=MSO_ANCHOR.MIDDLE)
tb(0.42,0.74,11.2,0.28,[("Ficha técnica del modelo, desempeño (Gini) y variables de mayor importancia — modelo de riesgo para la rebancarización de Altas TC",{'sz':10,'c':GRAY_TXT})])
bw=1.72; rrect(12.91-bw,0.30,bw,0.34,GREEN_SOFT,radius=0.17); oval(12.91-bw+0.14,0.41,0.11,0.11,GREEN)
tb(12.91-bw+0.30,0.30,bw-0.3,0.34,[("Altas TC · SSFF",{'sz':9,'b':True,'c':GREEN_DEEP})],anchor=MSO_ANCHOR.MIDDLE)

def cardhead(x,y,w,title):
    rrect(x,y,w,0.40,GREEN_DEEP,radius=0.11); rect(x,y+0.29,w,0.11,GREEN_DEEP)
    tb(x,y,w,0.40,[(title,{'sz':13,'b':True,'c':WHITE})],align=PP_ALIGN.CENTER,anchor=MSO_ANCHOR.MIDDLE)

# ============================== FICHA (izquierda)
FX,FY,FW,FH=0.42,1.12,7.22,3.06
rrect(FX,FY,FW,FH,WHITE,line=CARD_LINE,radius=0.12,lw=1.0)
cardhead(FX,FY,FW,"Ficha técnica")
LBLX=FX+0.14; LBLW=1.02; VX=FX+1.26; VW=FW-1.26-0.16
def field(y,lab,labcol,runs,h,chips=None,chy=None):
    rrect(LBLX,y+0.02,LBLW,0.24,labcol,radius=0.07)
    tb(LBLX,y+0.02,LBLW,0.24,[(lab,{'sz':8.7,'b':True,'c':WHITE})],align=PP_ALIGN.CENTER,anchor=MSO_ANCHOR.MIDDLE)
    tb(VX,y,VW,h,runs,size=9.6,ls=1.12)
    if chips: srcchips(VX,chy,chips,size=7)
    if y>FY+0.42+0.02:
        hline(FX+0.12,FX+FW-0.12,y-0.03,RGBColor(0xEA,0xF1,0xED),0.75)
y0=FY+0.46
GD={'b':True,'c':GREEN_DEEP}; MUT={'c':GRAY_TXT}
field(y0,"Objetivo",GREEN_DEEP,[("Estimar el ",{}),("riesgo de mal comportamiento",GD),(" de clientes con alta de tarjeta de crédito en el sistema financiero, para ",{}),("apoyar la rebancarización",GD),(".",{})],0.44); y0+=0.455
field(y0,"Uso",GREEN_BRIGHT,[("Ordenar y priorizar clientes",GD),(" en campañas: a quién ofrecer y con qué nivel de riesgo, y separar segmentos (TC Bank / TC No Bank).",{})],0.42); y0+=0.435
field(y0,"Población",GREEN_TEAL,[("Altas de TC en el SSFF",GD),("  ",{}),("(clientes que sacaron tarjeta en el sistema financiero).",MUT)],0.22,
      chips=["BCP","BBVA","Scotiabank","BanBif","Falabella","SIP"],chy=y0+0.235); y0+=0.475
field(y0,"Target",GREEN_TEAL,[("Cliente malo",GD),(" en horizonte de ",{}),("12 meses",GD),(": atraso ",{}),("> 60 días",GD),(" o refinanciado.",{})],0.22); y0+=0.315
field(y0,"Periodos",GREEN_TEAL,[("Desarrollo:",GD),(" Nov'23 – Ene'25 ",{}),("(15 meses)",MUT),(" · ",{}),("OOT:",GD),(" Feb'25 – Abr'25 ",{}),("(3 meses)",MUT),(".",{})],0.22); y0+=0.315
field(y0,"Metodología",GREEN_TEAL,[("LightGBM",GD),("  ",{}),("(gradient boosting sobre árboles de decisión).",MUT)],0.22); y0+=0.315
field(y0,"Variables",GREEN_TEAL,[("52 candidatas",GD),(" de múltiples fuentes externas e internas.",{})],0.22,
      chips=["RCC","Sunedu","Sentinel","IBK","Sunat","Reniec","Sunarp"],chy=y0+0.235)

# ============================== RESULTADOS (derecha)
RX,RY,RW,RH=7.81,1.12,5.10,3.06
rrect(RX,RY,RW,RH,WHITE,line=CARD_LINE,radius=0.12,lw=1.0)
cardhead(RX,RY,RW,"Resultados · poder del modelo (Gini)")

def set_border(c,color=BORDER,w=9525):
    tcPr=c._tc.get_or_add_tcPr()
    for tag in ('a:lnB','a:lnT','a:lnR','a:lnL'):
        for el in tcPr.findall(qn(tag)): tcPr.remove(el)
        ln=tcPr.makeelement(qn(tag),{'w':str(w),'cap':'flat'})
        sf=tcPr.makeelement(qn('a:solidFill'),{}); cl=tcPr.makeelement(qn('a:srgbClr'),{'val':color})
        sf.append(cl);ln.append(sf);tcPr.insert(0,ln)
def setcell(c,runs,fill=None,align=PP_ALIGN.LEFT,anchor=MSO_ANCHOR.MIDDLE):
    if fill is not None: c.fill.solid(); c.fill.fore_color.rgb=fill
    else: c.fill.background()
    c.vertical_anchor=anchor; c.margin_left=Inches(0.06); c.margin_right=Inches(0.05)
    c.margin_top=Inches(0.02); c.margin_bottom=Inches(0.02)
    tf=c.text_frame; tf.word_wrap=True; p=tf.paragraphs[0]; p.alignment=align; p.line_spacing=1.0
    for t,st in runs:
        r=p.add_run(); r.text=t; r.font.size=Pt(st.get('sz',9)); r.font.bold=st.get('b',False)
        r.font.name=FONT; r.font.color.rgb=st.get('c',INK)
    set_border(c)

TX,TY,TW=7.95,1.62,4.82
gf=s.shapes.add_table(6,3,Inches(TX),Inches(TY),Inches(TW),Inches(0.3))
tbl=gf.table; tbl.first_row=False; tbl.horz_banding=False
tbl._tbl.tblPr.set('firstRow','0'); tbl._tbl.tblPr.set('bandRow','0')
for i,frac in enumerate([0.31,0.40,0.29]): tbl.columns[i].width=Inches(TW*frac)
tbl.rows[0].height=Inches(0.26)
for r in range(1,6): tbl.rows[r].height=Inches(0.32)
# header
setcell(tbl.cell(0,0),[("Etapa",{'sz':8.5,'b':True,'c':GRAY_TXT})],fill=WHITE)
setcell(tbl.cell(0,1),[("Muestra",{'sz':8.5,'b':True,'c':GRAY_TXT})],fill=WHITE)
setcell(tbl.cell(0,2),[("Gini",{'sz':9,'b':True,'c':WHITE})],fill=NAVY,align=PP_ALIGN.CENTER)
# filas
setcell(tbl.cell(1,0),[("Desarrollo",{'sz':9.5,'b':True,'c':GREEN_DEEP})],fill=WHITE)
setcell(tbl.cell(2,0),[("",{})],fill=WHITE)
tbl.cell(1,0).merge(tbl.cell(2,0))
setcell(tbl.cell(1,1),[("Train (80%)",{'sz':8.5,'b':True,'c':WHITE})],fill=GREEN_BRIGHT,align=PP_ALIGN.CENTER)
setcell(tbl.cell(1,2),[("51%",{'sz':12,'b':True,'c':GREEN_DEEP2})],fill=WHITE,align=PP_ALIGN.CENTER)
setcell(tbl.cell(2,1),[("Test (20%)",{'sz':8.5,'b':True,'c':WHITE})],fill=BLUE,align=PP_ALIGN.CENTER)
setcell(tbl.cell(2,2),[("47%",{'sz':12,'b':True,'c':GREEN_DEEP2})],fill=WHITE,align=PP_ALIGN.CENTER)
setcell(tbl.cell(3,0),[("Validación",{'sz':9.5,'b':True,'c':GREEN_DEEP})],fill=RGBColor(0xF7,0xFB,0xF9))
setcell(tbl.cell(3,1),[("OOT",{'sz':8.5,'b':True,'c':WHITE})],fill=GRAYPILL,align=PP_ALIGN.CENTER)
setcell(tbl.cell(3,2),[("46%",{'sz':12,'b':True,'c':GREEN_DEEP2})],fill=RGBColor(0xF7,0xFB,0xF9),align=PP_ALIGN.CENTER)
setcell(tbl.cell(4,0),[("OOT · segmento ",{'sz':8.7,'c':GRAY_TXT}),("TC Bank",{'sz':8.7,'b':True,'c':INK})],fill=WHITE)
tbl.cell(4,0).merge(tbl.cell(4,1))
setcell(tbl.cell(4,2),[("29%",{'sz':12,'b':True,'c':GREEN_DEEP2})],fill=WHITE,align=PP_ALIGN.CENTER)
setcell(tbl.cell(5,0),[("OOT · segmento ",{'sz':8.7,'c':GRAY_TXT}),("TC No Bank",{'sz':8.7,'b':True,'c':INK})],fill=RGBColor(0xF7,0xFB,0xF9))
tbl.cell(5,0).merge(tbl.cell(5,1))
setcell(tbl.cell(5,2),[("23%",{'sz':12,'b':True,'c':GREEN_DEEP2})],fill=RGBColor(0xF7,0xFB,0xF9),align=PP_ALIGN.CENTER)

# deltas
DY=3.52; DH=0.56; DW=(RW-0.28-0.12)/2
def delta(x,k,v,d):
    rrect(x,DY,DW,DH,DL_BG,line=DL_LINE,radius=0.09,lw=0.75)
    tb(x+0.11,DY+0.06,DW-0.2,0.16,[(k,{'sz':8.3,'b':True,'c':DL_K})])
    tb(x+0.11,DY+0.20,DW-0.2,0.24,[(v,{'sz':15,'b':True,'c':DL_INK})])
    tb(x+0.11,DY+0.42,DW-0.2,0.14,[(d,{'sz':7.6,'c':GRAY_TXT})])
delta(RX+0.14,"Brecha OOT → TC Bank","+17 pp","Gini 46% → 29%")
delta(RX+0.14+DW+0.12,"Brecha OOT → TC No Bank","+20 pp","respecto al Gini global")

# ============================== SHAP + FUENTES (abajo)
BX,BY,BW2,BH=0.42,4.34,12.49,2.33
rrect(BX,BY,BW2,BH,WHITE,line=CARD_LINE,radius=0.12,lw=1.0)
rrect(BX,BY,BW2,0.38,GREEN_DEEP2,radius=0.12); rect(BX,BY+0.27,BW2,0.11,GREEN_DEEP2)
tb(BX+0.16,BY,BW2-0.3,0.38,[("Variables de mayor importancia (SHAP · Top 10) y fuentes de datos",{'sz':12.5,'b':True,'c':WHITE})],anchor=MSO_ANCHOR.MIDDLE)
SPLIT=BX+7.49
rect(SPLIT,BY+0.38,0.008,BH-0.38,RGBColor(0xEE,0xF3,0xF0))

# izquierda: barras
tb(BX+0.16,BY+0.46,4.0,0.2,[("VARIABLES RELEVANTES · % DE IMPORTANCIA",{'sz':8.3,'b':True,'c':GREEN_DEEP})])
BARS=[("Nº de deudas castigadas u24m","(RCC)",19.7),
      ("Máximo saldo peor clasificación u12m","(RCC)",7.1),
      ("Nivel educativo con títulos profesionales","(Sunedu)",6.2),
      ("Antigüedad desde alta del último producto en SSFF","(RCC)",4.7),
      ("Desviación saldo préstamos comerciales y personales u3m","(RCC)",4.1),
      ("Mínimo saldo total pasivos retail Interbank u12m","(IBK)",4.1),
      ("Ratio saldo riesgo total u1m / máximo u12m","(RCC)",3.9),
      ("Cantidad de empresas reportadas u12m","(Sentinel)",3.8),
      ("Máximo saldo pasivo u12m","(IBK)",3.6),
      ("Descripción de grupo carrera profesional","(Sunedu)",2.7)]
NMX=BX+0.16; NMW=3.62; BARX=NMX+NMW+0.10; BARMAX=1.95; PCTX=BARX+BARMAX+0.06
yy=BY+0.70; rh=0.152
for nm,src,v in BARS:
    tb(NMX,yy,NMW,0.16,[(nm+" ",{'sz':7.4,'c':INK}),(src,{'sz':7.4,'b':True,'c':GRAY_TXT})],anchor=MSO_ANCHOR.MIDDLE)
    rect(BARX,yy+0.028,BARMAX,0.095,TRACK)
    rect(BARX,yy+0.028,max(0.06,v/19.7*BARMAX),0.095,BAR1)
    tb(PCTX,yy,0.55,0.16,[(f"{v}%",{'sz':7.8,'b':True,'c':GREEN_DEEP2})],anchor=MSO_ANCHOR.MIDDLE)
    yy+=rh

# derecha: fuentes
RXX=SPLIT+0.16
tb(RXX,BY+0.46,4.5,0.2,[("FUENTES DE LA IMPORTANCIA",{'sz':8.3,'b':True,'c':GREEN_DEEP})])
tb(RXX,BY+0.68,4.7,0.2,[("RCC · 61% de la importancia total",{'sz':10,'b':True,'c':GREEN_DEEP})])
FU=[("Intercorp",13),("Sunedu",9),("Sentinel",7),("IBK",5),("Sunat",3),("Reniec",1),("Sunarp",1)]
fy=BY+0.92; frh=0.128; FBX=RXX+1.02; FBMAX=1.55
for nm,pc in FU:
    tb(RXX,fy,1.0,0.14,[(nm,{'sz':8,'b':True,'c':GREEN_DEEP2})],anchor=MSO_ANCHOR.MIDDLE)
    rect(FBX,fy+0.028,max(0.05,pc/13*FBMAX),0.075,BAR1)
    tb(FBX+max(0.05,pc/13*FBMAX)+0.06,fy,0.5,0.14,[(f"{pc}%",{'sz':7.8,'b':True,'c':GRAY_TXT})],anchor=MSO_ANCHOR.MIDDLE)
    fy+=frh
# highlight
hy=fy+0.04
rrect(RXX,hy,BW2-(RXX-BX)-0.16,0.42,HL_BG,line=HL_LINE,radius=0.08,lw=0.75)
tb(RXX+0.10,hy,BW2-(RXX-BX)-0.36,0.42,[("Ingresó al modelo la variable construida de ",{'sz':8.2,'c':HL_INK}),
   ("Perfil Castigado",{'sz':8.2,'b':True,'c':HL_INK2}),(": ",{'sz':8.2,'c':HL_INK}),
   ("Nº de Deudas Castigadas (19.7%)",{'sz':8.2,'b':True,'c':HL_INK2}),(" — la de mayor peso.",{'sz':8.2,'c':HL_INK})],anchor=MSO_ANCHOR.MIDDLE,ls=1.15)

# ---------- Pie ----------
hline(0.42,12.91,7.02,FOOT_LINE,1.0)
foot=[("Gini:","mide qué tan bien el modelo separa buenos de malos (0 = azar, 100% = perfecto).",5.2),
      ("OOT:","validación fuera de tiempo, en meses posteriores al desarrollo.",4.1),
      ("SHAP:","aporte de cada variable a la predicción.",2.7)]
fx=0.42
for lead,rest,w in foot:
    tb(fx,7.10,w,0.32,[(lead+" ",{'sz':7.6,'b':True,'c':GREEN_DEEP2}),(rest,{'sz':7.6,'c':FOOT_INK})])
    fx+=w+0.25

prs.save("presentacion_modelamiento.pptx")
print("OK presentacion_modelamiento.pptx")
