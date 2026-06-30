# -*- coding: utf-8 -*-
"""Genera una presentación PPTX nativa y editable (tablas/formas/textos reales)
que replica presentacion_metodologia_arboles.html (2 slides)."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn

# ---------- paleta ----------
GREEN_DEEP   = RGBColor(0x1F, 0x51, 0x30)
GREEN_DEEP2  = RGBColor(0x26, 0x60, 0x3A)
GREEN        = RGBColor(0x1A, 0xA4, 0x4C)
GREEN_BRIGHT = RGBColor(0x1A, 0x98, 0x50)
GREEN_TEAL   = RGBColor(0x3A, 0x7D, 0x5C)
GREEN_SOFT   = RGBColor(0xE8, 0xF5, 0xEE)
GREEN_HEADBG = RGBColor(0xF3, 0xF8, 0xF5)
ROWON        = RGBColor(0xEE, 0xF9, 0xF1)
GRAY_TITLE   = RGBColor(0x9A, 0xA6, 0xA0)
GRAY_TXT     = RGBColor(0x5B, 0x6F, 0x66)
INK          = RGBColor(0x14, 0x27, 0x1D)
MONO_INK     = RGBColor(0x23, 0x43, 0x3C)
WHITE        = RGBColor(0xFF, 0xFF, 0xFF)
CARD_LINE    = RGBColor(0xE7, 0xEE, 0xE9)
BORDER       = "DDE7E4"
STATBG       = RGBColor(0xF5, 0xFA, 0xF7)
STATLINE     = RGBColor(0xE3, 0xEF, 0xE8)

# chips
CHIP = {
    'pos': (RGBColor(0xFD,0xEC,0xEB), RGBColor(0xC0,0x39,0x2B)),
    'neg': (RGBColor(0xE8,0xF5,0xEE), RGBColor(0x1A,0x7A,0x45)),
    'amb': (RGBColor(0xFF,0xF4,0xE0), RGBColor(0xB9,0x82,0x1F)),
    'ord': (RGBColor(0xE9,0xEE,0xFB), RGBColor(0x34,0x52,0x9C)),
    'inc': (GREEN_SOFT, GREEN_DEEP),
}
FONT = "Segoe UI"
MONO = "Consolas"

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]


def add_slide():
    return prs.slides.add_slide(BLANK)


def rrect(s, x, y, w, h, fill, line=None, radius=0.10, line_w=1.0, shadow=False):
    shp = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    try:
        shp.adjustments[0] = max(0.0, min(0.5, radius / min(w, h)))
    except Exception:
        pass
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line; shp.line.width = Pt(line_w)
    shp.shadow.inherit = False
    return shp


def rect(s, x, y, w, h, fill, line=None):
    shp = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = fill
    if line is None:
        shp.line.fill.background()
    else:
        shp.line.color.rgb = line; shp.line.width = Pt(1.0)
    shp.shadow.inherit = False
    return shp


def tb(s, x, y, w, h, runs, size=12, color=INK, bold=False, align=PP_ALIGN.LEFT,
       anchor=MSO_ANCHOR.TOP, font=FONT, line_spacing=1.0):
    """runs: str  ó  lista de (text, dict) con keys b(old)/c(olor)/f(ont)/sz."""
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.word_wrap = True
    tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    p = tf.paragraphs[0]; p.alignment = align
    if line_spacing: p.line_spacing = line_spacing
    if isinstance(runs, str):
        runs = [(runs, {})]
    for text, st in runs:
        r = p.add_run(); r.text = text
        r.font.size = Pt(st.get('sz', size))
        r.font.bold = st.get('b', bold)
        r.font.name = st.get('f', font)
        r.font.color.rgb = st.get('c', color)
    return box


def set_border(cell, color=BORDER, w=9525):
    tcPr = cell._tc.get_or_add_tcPr()
    for tag in ('a:lnB', 'a:lnT', 'a:lnR', 'a:lnL'):
        for el in tcPr.findall(qn(tag)):
            tcPr.remove(el)
        ln = tcPr.makeelement(qn(tag), {'w': str(w), 'cap': 'flat'})
        sf = tcPr.makeelement(qn('a:solidFill'), {})
        cl = tcPr.makeelement(qn('a:srgbClr'), {'val': color})
        sf.append(cl); ln.append(sf)
        tcPr.insert(0, ln)


def cell_fmt(cell, runs, size=11, color=INK, bold=False, align=PP_ALIGN.LEFT,
             fill=None, font=FONT, anchor=MSO_ANCHOR.MIDDLE, border=True, mgn=0.05):
    if fill is not None:
        cell.fill.solid(); cell.fill.fore_color.rgb = fill
    else:
        cell.fill.background()
    cell.vertical_anchor = anchor
    cell.margin_left = Inches(0.07); cell.margin_right = Inches(0.05)
    cell.margin_top = Inches(mgn); cell.margin_bottom = Inches(mgn)
    tf = cell.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    if isinstance(runs, str):
        runs = [(runs, {})]
    first = True
    for text, st in runs:
        r = p.add_run() if not first else (p.runs[0] if p.runs else p.add_run())
        first = False
        r.text = text
        r.font.size = Pt(st.get('sz', size)); r.font.bold = st.get('b', bold)
        r.font.name = st.get('f', font); r.font.color.rgb = st.get('c', color)
    if border:
        set_border(cell)


def card(s, x, y, w, h, label, title, hcolor=GREEN_DEEP, hh=0.36):
    rrect(s, x, y, w, h, WHITE, line=CARD_LINE, radius=0.12, line_w=1.0)
    rrect(s, x, y, w, hh, hcolor, radius=0.12)
    rect(s, x, y + hh - 0.13, w, 0.13, hcolor)          # cuadra el borde inferior del header
    # badge nº
    bd = rrect(s, x + 0.13, y + (hh - 0.22) / 2, 0.22, 0.22, GREEN if hcolor != GREEN else GREEN_BRIGHT, radius=0.06)
    tb(s, x + 0.13, y + (hh - 0.22) / 2 - 0.005, 0.22, 0.22, label, size=11, color=WHITE, bold=True,
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    tb(s, x + 0.45, y, w - 0.5, hh, title, size=13.5, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    return x + 0.14, y + hh + 0.08, w - 0.28          # inner x, y, w


def header(s, title_runs, subtitle, badge_text):
    tb(s, 0.46, 0.26, 9.6, 0.5, title_runs, size=26, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    tb(s, 0.46, 0.80, 9.8, 0.3, subtitle, size=11, color=GRAY_TXT, anchor=MSO_ANCHOR.MIDDLE)
    bw = 2.55
    rrect(s, 13.333 - 0.46 - bw, 0.30, bw, 0.42, GREEN_SOFT, radius=0.21)
    tb(s, 13.333 - 0.46 - bw, 0.30, bw, 0.42,
       [("●  ", {'c': GREEN, 'b': True, 'sz': 10}), (badge_text, {'c': GREEN_DEEP, 'b': True, 'sz': 10.5})],
       align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)


def footer(s, items):
    rect(s, 0.46, 7.02, 13.333 - 0.92, 0.012, STATLINE)
    runs = []
    for i, (lead, rest) in enumerate(items):
        if i: runs.append(("        ", {}))
        runs.append((lead, {'b': True, 'c': GREEN_DEEP2, 'sz': 8}))
        runs.append((rest, {'c': GRAY_TITLE, 'sz': 8}))
    tb(s, 0.46, 7.08, 13.333 - 0.92, 0.34, runs, size=8, color=GRAY_TITLE)


def chips_row(s, x, y, chips, h=0.26, gap=0.09, size=9.5):
    cx = x
    for text, kind in chips:
        fill, col = CHIP[kind]
        w = 0.16 + 0.072 * len(text)
        rrect(s, cx, y, w, h, fill, radius=h/2)
        tb(s, cx, y - 0.005, w, h, text, size=size, color=col, bold=True,
           align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        cx += w + gap
    return cx


def steps(s, x, y, w, items, step_h=0.40, badge=GREEN):
    cy = y
    for num, runs in items:
        rrect(s, x, cy, 0.26, 0.26, badge, radius=0.07)
        tb(s, x, cy - 0.01, 0.26, 0.26, num, size=11.5, color=WHITE, bold=True,
           align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
        tb(s, x + 0.36, cy - 0.02, w - 0.36, 0.42, runs, size=11.5, anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.0)
        cy += step_h
    return cy


def bullets(s, x, y, w, items, size=11, gap=0.04, dot=GREEN, color=INK):
    cy = y
    for runs in items:
        box = s.shapes.add_textbox(Inches(x), Inches(cy), Inches(w), Inches(0.6))
        tf = box.text_frame; tf.word_wrap = True
        tf.margin_left = 0; tf.margin_right = 0; tf.margin_top = 0; tf.margin_bottom = 0
        p = tf.paragraphs[0]; p.line_spacing = 1.05
        r = p.add_run(); r.text = "●  "; r.font.size = Pt(size - 2); r.font.color.rgb = dot; r.font.bold = True; r.font.name = FONT
        for text, st in runs:
            rr = p.add_run(); rr.text = text
            rr.font.size = Pt(st.get('sz', size)); rr.font.bold = st.get('b', False)
            rr.font.name = st.get('f', FONT); rr.font.color.rgb = st.get('c', color)
        cy += 0.205 * (1 + max(0, (sum(len(t) for t, _ in runs)) // 52)) + gap
    return cy


def stat(s, x, y, w, h, label, big=None, bul=None):
    rrect(s, x, y, w, h, STATBG, line=STATLINE, radius=0.09, line_w=1.0)
    cy = y + 0.08
    tb(s, x + 0.12, cy, w - 0.24, 0.2, label, size=10, color=GRAY_TXT, bold=True); cy += 0.20
    if big:
        tb(s, x + 0.12, cy, w - 0.24, 0.3, big, size=18, color=GREEN_DEEP, bold=True); cy += 0.30
    if bul:
        for t in bul:
            tb(s, x + 0.12, cy, w - 0.24, 0.2,
               [("● ", {'c': GREEN, 'sz': 7}), (t, {'c': INK, 'sz': 10})], size=10); cy += 0.175


# ====================================================================== SLIDE 1
s1 = add_slide()
header(s1,
       [("Segmentación de Riesgo ", {'c': GREEN_DEEP, 'b': True}), ("| Base, Score Rebank y Árbol 1", {'c': GRAY_TITLE, 'b': True})],
       [("Universo de castigados · objetivo = ", {'c': GRAY_TXT}), ("score", {'c': GRAY_TXT, 'b': True}),
        (" (mayor score → menor riesgo) · profundidades evaluadas 4–7", {'c': GRAY_TXT})],
       "REBANK 2 · Ventana 2506")

LX, LW = 0.46, 5.78
RX, RW = 6.42, 6.45
CY = 1.42

# --- Card 1: categorías ---
c1h = 2.32
ix, iy, iw = card(s1, LX, CY, LW, c1h, "1", "Categorías del universo de castigados")
t = s1.shapes.add_table(6, 2, Inches(ix), Inches(iy), Inches(iw), Inches(1.49)).table
t.first_row = False; t.horz_banding = False
t.columns[0].width = Inches(1.95); t.columns[1].width = Inches(iw - 1.95)
cats = [
    ("CAST_NOIBK_REP<5anios", "Castigo vigente en otra entidad (no-IBK), mora <5a.", False),
    ("CAST_NOIBK_REP>=5anios", "Igual, pero la mora del castigo no-IBK es ≥5 años.", True),
    ("NO_CAST_NOIBK_U24M", "Sin castigo vigente; castigo no-IBK en últ. 24m.", True),
    ("NO_CAST_IBK_U24M", "Sin castigo IBK hoy; lo tuvo en los últ. 24m.", False),
    ("CAST_IBK_REP", "Castigo vigente en Interbank (202601). Prioridad.", False),
]
cell_fmt(t.cell(0, 0), "Categoría", size=9, color=GREEN_DEEP, bold=True, fill=GREEN_HEADBG)
cell_fmt(t.cell(0, 1), "Descripción", size=9, color=GREEN_DEEP, bold=True, fill=GREEN_HEADBG)
for i, (cat, desc, mod) in enumerate(cats, start=1):
    fill = ROWON if mod else WHITE
    cell_fmt(t.cell(i, 0), [(cat, {'f': MONO, 'sz': 8.5, 'c': MONO_INK})], fill=fill, mgn=0.03)
    cell_fmt(t.cell(i, 1), [(desc, {'sz': 8.7, 'c': INK})], fill=fill, mgn=0.03)
t.rows[0].height = Inches(0.24)
for i in range(1, 6):
    t.rows[i].height = Inches(0.25)
tb(s1, ix, iy + 1.49 + 0.05, iw, 0.2,
   [("●  ", {'c': GREEN, 'b': True, 'sz': 8}),
    ("Filas en verde: categorías modeladas (>5 años y ≤24 meses).", {'c': GRAY_TXT, 'sz': 8.5})], size=8.5, color=GRAY_TXT)

# --- Card 2: Score Rebank ---
C2Y = CY + c1h + 0.16
c2h = 2.96
ix, iy, iw = card(s1, LX, C2Y, LW, c2h, "2", "Score Rebank · OptBinning")
t2 = s1.shapes.add_table(7, 4, Inches(ix), Inches(iy), Inches(iw), Inches(1.78)).table
t2.first_row = False; t2.horz_banding = False
t2.columns[0].width = Inches(0.55); t2.columns[1].width = Inches(1.95)
t2.columns[2].width = Inches(1.62); t2.columns[3].width = Inches(iw - 0.55 - 1.95 - 1.62)
hdr = ["Cat", "Bin (score)", "Tasa evento", "% distrib."]
for j, htxt in enumerate(hdr):
    al = PP_ALIGN.CENTER if j == 0 else (PP_ALIGN.RIGHT if j >= 2 else PP_ALIGN.LEFT)
    cell_fmt(t2.cell(0, j), htxt, size=9.5, color=GREEN_DEEP, bold=True, fill=GREEN_HEADBG, align=al)
rows = [
    ("1", "≥ 682.5", "6.2%", "14.3%", RGBColor(0xE8,0xF6,0xEC)),
    ("2", "627.5 – 682.5", "10.4%", "14.7%", RGBColor(0xEE,0xF7,0xE2)),
    ("3", "570.5 – 627.5", "13.4%", "18.5%", RGBColor(0xFB,0xF6,0xDA)),
    ("4", "523.5 – 570.5", "17.5%", "15.4%", RGBColor(0xFD,0xEE,0xD6)),
    ("5", "426.5 – 523.5", "24.2%", "21.4%", RGBColor(0xFB,0xE1,0xD1)),
    ("6", "< 426.5", "55.9%", "15.8%", RGBColor(0xF6,0xD0,0xCA)),
]
for i, (cat, binr, tasa, dist, col) in enumerate(rows, start=1):
    cell_fmt(t2.cell(i, 0), cat, size=11, color=GREEN_DEEP, bold=True, align=PP_ALIGN.CENTER)
    cell_fmt(t2.cell(i, 1), [(binr, {'f': MONO, 'sz': 10, 'c': MONO_INK})])
    cell_fmt(t2.cell(i, 2), [(tasa, {'sz': 11})], align=PP_ALIGN.RIGHT, fill=col)
    cell_fmt(t2.cell(i, 3), [(dist, {'sz': 11})], align=PP_ALIGN.RIGHT)
t2.rows[0].height = Inches(0.26)
for i in range(1, 7):
    t2.rows[i].height = Inches(0.24)
tb(s1, ix, iy + 1.98 + 0.06, iw, 0.45,
   [("Ajuste: ", {'b': True, 'c': GREEN_DEEP, 'sz': 9.5}),
    ("OptBinning del score vs target sobre la ", {'sz': 9.5, 'c': GRAY_TXT}),
    ("base de entrenamiento Rebank ", {'b': True, 'c': GREEN_DEEP, 'sz': 9.5}),
    ("(6 bins, descendente). Los cortes definen la categoría ", {'sz': 9.5, 'c': GRAY_TXT}),
    ("1 (mejor) … 6 (peor)", {'b': True, 'c': GREEN_DEEP, 'sz': 9.5}), (".", {'sz': 9.5, 'c': GRAY_TXT})],
   size=9.5, color=GRAY_TXT, line_spacing=1.05)

# --- Card A: variables (derecha) ---
cAh = C2Y + c2h - CY
ix, iy, iw = card(s1, RX, CY, RW, cAh, "A", "Variables que pueden entrar al Árbol 1", hcolor=GREEN_BRIGHT)
ta = s1.shapes.add_table(13, 3, Inches(ix), Inches(iy), Inches(iw), Inches(4.12)).table
ta.first_row = False; ta.horz_banding = False
ta.columns[0].width = Inches(1.25); ta.columns[1].width = Inches(2.95); ta.columns[2].width = Inches(iw - 1.25 - 2.95)
for j, htxt in enumerate(["Familia", "Variable", "Dirección de riesgo"]):
    cell_fmt(ta.cell(0, j), htxt, size=10, color=GREEN_DEEP, bold=True, fill=GREEN_HEADBG)
vrows = [
    ("deuda_cas", "+ más riesgo", 'pos'),
    ("monto_castigado_total / ibk / otros", "+ más riesgo", 'pos'),
    ("nro_entidades_castigo", "+ más riesgo", 'pos'),
    ("meses_desde_ultimo_castigo", "− menos riesgo", 'neg'),
    ("meses_desde_primer_castigo", "− menos riesgo", 'neg'),
    ("max_dias_mora_castigo", "+ más riesgo", 'pos'),
    ("rk_ing_num", "− menos riesgo", 'neg'),
    ("edad_num", "− mayor edad → menor score", 'neg'),
    ("sexo", "0 ambigua", 'amb'),
    ("nivel_profesional", "+ más riesgo", 'pos'),
    ("tipinstitucion", "+ más riesgo", 'pos'),
    ("segmentacion_gdp_v2 (G1…G8)", "ordinal · ORD_VAR", 'ord'),
]
for i, (var, dirtxt, kind) in enumerate(vrows, start=1):
    cell_fmt(ta.cell(i, 1), [(var, {'f': MONO, 'sz': 9.5, 'c': MONO_INK})], mgn=0.03)
    fill, col = CHIP[kind]
    cell_fmt(ta.cell(i, 2), [(dirtxt, {'sz': 9.5, 'c': col, 'b': True})], fill=fill, mgn=0.03)
# familia merges
def mergecol(a, b, txt):
    ca, cb = ta.cell(a, 0), ta.cell(b, 0)
    ca.merge(cb)
    cell_fmt(ca, [(txt, {'b': True, 'c': GREEN_DEEP2, 'sz': 10.5})], anchor=MSO_ANCHOR.MIDDLE)
mergecol(1, 6, "Castigo")
mergecol(7, 8, "Ingreso / edad")
mergecol(9, 11, "Demográfico")
cell_fmt(ta.cell(12, 0), [("Ordinal", {'b': True, 'c': GREEN_DEEP2, 'sz': 10.5})])
ta.rows[0].height = Inches(0.28)
for i in range(1, 13):
    ta.rows[i].height = Inches(0.32)
tb(s1, ix, iy + 4.12 + 0.06, iw, 0.3,
   [("+", {'b': True, 'c': CHIP['pos'][1], 'sz': 9}), ("  mayor→más riesgo   ", {'c': GRAY_TXT, 'sz': 9.5}),
    ("−", {'b': True, 'c': CHIP['neg'][1], 'sz': 9}), ("  mayor→menos riesgo   ", {'c': GRAY_TXT, 'sz': 9.5}),
    ("0", {'b': True, 'c': CHIP['amb'][1], 'sz': 9}), ("  por correlación", {'c': GRAY_TXT, 'sz': 9.5})],
   size=9.5, color=GRAY_TXT)

footer(s1, [
    ("Score Rebank:", " categoría 1–6 derivada del bin del score (puntuacion_cal_cat)."),
    ("Tasa evento:", " proporción de malos (target_60_12m=1) en el bin · % distrib.: peso del bin."),
    ("IBK:", " Interbank · no-IBK: otras entidades · RCC: reporte crediticio."),
])

# ====================================================================== SLIDE 2
s2 = add_slide()
header(s2,
       [("Construcción y Refinamiento ", {'c': GREEN_DEEP, 'b': True}), ("| Árbol 1 (B) y Árbol 2", {'c': GRAY_TITLE, 'b': True})],
       [("Cómo se arma el Árbol 1, qué cambia en el Árbol 2 y cómo se validan las reglas finales", {'c': GRAY_TXT})],
       "Árbol 1 · Árbol 2 · Validación")

TY = 1.42
LX2, LW2 = 0.46, 6.06
RX2, RW2 = 6.70, 6.17
TH = 3.80

# --- B: construcción Árbol 1 ---
ix, iy, iw = card(s2, LX2, TY, LW2, TH, "B", "Cómo se construye el Árbol 1")
ny = steps(s2, ix, iy + 0.04, iw, [
    ("1", [("OptBinning por variable ", {'b': True, 'c': GREEN_DEEP}), ("(WoE) con tendencia monótona según ", {'c': INK}), ("DIRECCION_NEGOCIO", {'f': MONO, 'c': MONO_INK, 'sz': 10.5}), (".", {'c': INK})]),
    ("2", [("Imputación de missing ", {'b': True, 'c': GREEN_DEEP}), ("con el WoE del ", {'c': INK}), ("peor bin", {'b': True, 'c': GREEN_DEEP}), (" (cliente sin dato → mayor riesgo).", {'c': INK})]),
    ("3", [("Árbol monótono ", {'b': True, 'c': GREEN_DEEP}), ("DecisionTreeRegressor", {'f': MONO, 'c': MONO_INK, 'sz': 10.5}), (" con ", {'c': INK}), ("monotonic_cst", {'f': MONO, 'c': MONO_INK, 'sz': 10.5}), (".", {'c': INK})]),
    ("4", [("Poda automática: ", {'b': True, 'c': GREEN_DEEP}), ("re-entrena solo con variables de importancia > 0.", {'c': INK})]),
    ("5", [("Salida: ", {'b': True, 'c': GREEN_DEEP}), ("cada hoja = estrategia rankeada por riesgo (Excel + .pkl).", {'c': INK})]),
], step_h=0.46)
sy = iy + 0.04 + 5 * 0.46 + 0.06
sw = (iw - 0.16) / 2
stat(s2, ix, sy, sw, 0.80, "Dos universos de variables", bul=["Con todas las variables", "Sin edad_num (*_sinalgunasvariables)"])
stat(s2, ix + sw + 0.16, sy, sw, 0.80, "Estrategias (prof. 6)", big="15 – 21", bul=["según escenario y profundidad"])

# --- C: Árbol 2 ---
ix, iy, iw = card(s2, RX2, TY, RW2, TH, "C", "Árbol 2 · qué cambia y resultado", hcolor=GREEN_BRIGHT)
tc = s2.shapes.add_table(4, 2, Inches(ix), Inches(iy), Inches(iw), Inches(1.0)).table
tc.first_row = False; tc.horz_banding = False
tc.columns[0].width = Inches(2.35); tc.columns[1].width = Inches(iw - 2.35)
cell_fmt(tc.cell(0, 0), "Variable de entrada", size=10, color=GREEN_DEEP, bold=True, fill=GREEN_HEADBG)
cell_fmt(tc.cell(0, 1), "Rol en el Árbol 2", size=10, color=GREEN_DEEP, bold=True, fill=GREEN_HEADBG)
c2rows = [
    ("bucket (B1…B8)", [("Resultado del Árbol 1, entra como ", {'sz': 10, 'c': INK}), ("ordinal", {'sz': 10, 'b': True, 'c': GREEN_DEEP})]),
    ("saldo_prom_tot_pasivo_u3m", [("Saldo pasivo promedio · binning 2–7 bins", {'sz': 10, 'c': INK})]),
    ("Score Rebank", [("Categoría de riesgo del score (1–6)", {'sz': 10, 'c': INK})]),
]
for i, (var, rol) in enumerate(c2rows, start=1):
    cell_fmt(tc.cell(i, 0), [(var, {'f': MONO, 'sz': 9.5, 'c': MONO_INK})])
    cell_fmt(tc.cell(i, 1), rol)
tc.rows[0].height = Inches(0.26)
for i in range(1, 4):
    tc.rows[i].height = Inches(0.25)
cy = iy + 1.16
cy = steps(s2, ix, cy, iw, [
    ("✓", [("FAMILIAS_UNICAS: ", {'b': True, 'c': GREEN_DEEP}), ("conserva una sola variable de \"saldo\" (la de mayor importancia).", {'c': INK})]),
    ("✓", [("Nuevas hojas = estrategias finas ", {'b': True, 'c': GREEN_DEEP}), ("→ agrupadas en ~12 buckets finales monótonos.", {'c': INK})]),
], step_h=0.46)
chips_row(s2, ix, cy + 0.02, [("Cascada", 'inc'), ("ChiMerge", 'inc'), ("OptBin", 'inc'), ("Shrinkage", 'inc'), ("MDLP", 'inc')])
sy2 = cy + 0.42
sw2 = (iw - 0.16) / 2
stat(s2, ix, sy2, sw2, 0.74, "≤24 meses", big="30 → 12", bul=["estrategias → buckets"])
stat(s2, ix + sw2 + 0.16, sy2, sw2, 0.74, "≥5 años", big="16 → 12", bul=["estrategias → buckets"])

# --- V1/V2/V3 ---
VY = TY + TH + 0.20
VH = 1.40
vw = (13.333 - 0.92 - 0.36) / 3
vx = 0.46
vdata = [
    ("V1", "Base de campañas", GREEN_DEEP, [
        [("Últimas ", {'c': INK}), ("3 campañas de junio", {'b': True, 'c': GREEN_DEEP}), (" con los ", {'c': INK}), ("5 pilotos", {'b': True, 'c': GREEN_DEEP}), (" vigentes.", {'c': INK})],
        [("Mide la ", {'c': INK}), ("distribución de nuestras reglas", {'b': True, 'c': GREEN_DEEP}), (" en lo que se envía.", {'c': INK})]]),
    ("V2", "Base de generación", GREEN_BRIGHT, [
        [("Base usada para ", {'c': INK}), ("construir los árboles", {'b': True, 'c': GREEN_DEEP}), (".", {'c': INK})],
        [("Evalúa las ", {'c': INK}), ("reglas finales del Árbol 2", {'b': True, 'c': GREEN_DEEP}), (" y la ", {'c': INK}), ("granularidad", {'b': True, 'c': GREEN_DEEP}), (".", {'c': INK})]]),
    ("V3", "Base fuera de campaña", GREEN_TEAL, [
        [("Clientes que ", {'c': INK}), ("hoy no están en campaña", {'b': True, 'c': GREEN_DEEP}), (" (5 pilotos actuales).", {'c': INK})],
        [("Muestra la ", {'c': INK}), ("distribución de los no incluidos", {'b': True, 'c': GREEN_DEEP}), (".", {'c': INK})]]),
]
for tag, ttl, col, buls in vdata:
    rrect(s2, vx, VY, vw, VH, WHITE, line=CARD_LINE, radius=0.11, line_w=1.0)
    rrect(s2, vx, VY, vw, 0.34, col, radius=0.11)
    rect(s2, vx, VY + 0.21, vw, 0.13, col)
    rrect(s2, vx + 0.12, VY + 0.06, 0.42, 0.22, RGBColor(0x4D,0x7A,0x66), radius=0.05)
    tb(s2, vx + 0.12, VY + 0.055, 0.42, 0.22, tag, size=11, color=WHITE, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    tb(s2, vx + 0.62, VY, vw - 0.66, 0.34, ttl, size=11.5, color=WHITE, bold=True, anchor=MSO_ANCHOR.MIDDLE)
    bullets(s2, vx + 0.14, VY + 0.44, vw - 0.26, buls, size=10.3)
    vx += vw + 0.18

footer(s2, [
    ("DIRECCION_NEGOCIO / monotonic_cst:", " dirección esperada de cada variable y su restricción monótona."),
    ("FAMILIAS_UNICAS:", " deja una sola variable por familia (p.ej. \"saldo\")."),
    ("Rechazo:", " clientes no capturados por ninguna regla."),
])

prs.save("/home/user/Controling/presentacion_metodologia_arboles.pptx")
print("OK pptx guardado")
