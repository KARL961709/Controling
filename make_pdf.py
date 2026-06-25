#!/usr/bin/env python3
# Pure-python PDF generator (no deps). Helvetica = metric substitute for Arial.
import zlib, struct

PAGE_W, PAGE_H = 595.28, 841.89
MARGIN = 62.4                      # ~2.2 cm
SIZE = 11.0
LEAD = SIZE * 1.5                  # interlineado 1.5
CONTENT_W = PAGE_W - 2 * MARGIN

# ---- Helvetica / Helvetica-Bold AFM widths (units/1000) ----
HELV = {' ':278,'!':278,'"':355,'#':556,'$':556,'%':889,'&':667,"'":191,'(':333,')':333,'*':389,'+':584,',':278,'-':333,'.':278,'/':278,'0':556,'1':556,'2':556,'3':556,'4':556,'5':556,'6':556,'7':556,'8':556,'9':556,':':278,';':278,'<':584,'=':584,'>':584,'?':556,'@':1015,'A':667,'B':667,'C':722,'D':722,'E':667,'F':611,'G':778,'H':722,'I':278,'J':500,'K':667,'L':556,'M':833,'N':722,'O':778,'P':667,'Q':778,'R':722,'S':667,'T':611,'U':722,'V':667,'W':944,'X':667,'Y':667,'Z':611,'[':278,'\\':278,']':278,'^':469,'_':556,'`':333,'a':556,'b':556,'c':500,'d':556,'e':556,'f':278,'g':556,'h':556,'i':222,'j':222,'k':500,'l':222,'m':833,'n':556,'o':556,'p':556,'q':556,'r':333,'s':500,'t':278,'u':556,'v':500,'w':722,'x':500,'y':500,'z':500,'{':334,'|':260,'}':334,'~':584}
HELVB = {' ':278,'!':333,'"':474,'#':556,'$':556,'%':889,'&':722,"'":238,'(':333,')':333,'*':389,'+':584,',':278,'-':333,'.':278,'/':278,'0':556,'1':556,'2':556,'3':556,'4':556,'5':556,'6':556,'7':556,'8':556,'9':556,':':333,';':333,'<':584,'=':584,'>':584,'?':611,'@':975,'A':722,'B':722,'C':722,'D':722,'E':667,'F':611,'G':778,'H':722,'I':278,'J':556,'K':722,'L':611,'M':833,'N':722,'O':778,'P':667,'Q':778,'R':722,'S':667,'T':611,'U':722,'V':667,'W':944,'X':667,'Y':667,'Z':611,'[':333,'\\':278,']':333,'^':584,'_':556,'`':333,'a':556,'b':611,'c':556,'d':611,'e':556,'f':333,'g':611,'h':611,'i':278,'j':278,'k':556,'l':278,'m':889,'n':611,'o':611,'p':611,'q':611,'r':389,'s':556,'t':333,'u':611,'v':556,'w':778,'x':556,'y':556,'z':500,'{':389,'|':280,'}':389,'~':584}
# accented / punctuation -> map to a base glyph width
ACCENT = {'á':'a','é':'e','í':'i','ó':'o','ú':'u','ü':'u','ñ':'n','Á':'A','É':'E','Í':'I','Ó':'O','Ú':'U','Ñ':'N','¿':'?','¡':'!','“':'"','”':'"','‘':"'",'’':"'",'—':'M','–':'n','…':'.','·':'.'}

def cw(ch, bold):
    t = HELVB if bold else HELV
    if ch in t: return t[ch]
    if ch in ACCENT: return t.get(ACCENT[ch], 556)
    return 556

def wstr(s, bold, size=SIZE):
    return sum(cw(c, bold) for c in s) * size / 1000.0

def esc(s):
    out = []
    for c in s:
        try:
            b = c.encode('cp1252')
        except UnicodeEncodeError:
            b = b'?'
        for x in b:
            if x in (0x28, 0x29, 0x5C):  # ( ) \
                out.append('\\' + chr(x))
            elif x < 32 or x > 126:
                out.append('\\%03o' % x)
            else:
                out.append(chr(x))
    return ''.join(out)

FONT = {'':'F1','b':'F2','i':'F3','bi':'F4'}
def isbold(st): return 'b' in st

# ---------- content model ----------
# A paragraph is a list of runs (text, style). style in '', 'b', 'i', 'bi'
def runs_to_words(runs):
    words = []  # list of list-of-(text,style) ; each word may span styles (rare) -> keep simple per run split
    for text, st in runs:
        parts = text.split(' ')
        for i, p in enumerate(parts):
            if p == '' and i != 0 and i != len(parts)-1:
                # collapse multiple spaces -> treat as space separator only
                continue
            words.append((p, st))
    return [w for w in words if w[0] != '']

def wrap_runs(runs, max_w, size=SIZE):
    words = runs_to_words(runs)
    lines, cur, curw = [], [], 0.0
    space = None
    for (txt, st) in words:
        wlen = wstr(txt, isbold(st), size)
        add = wlen if not cur else wlen + wstr(' ', isbold(st), size)
        if cur and curw + add > max_w:
            lines.append(cur)
            cur, curw = [(txt, st)], wlen
        else:
            cur.append((txt, st)); curw += add
    if cur: lines.append(cur)
    return lines

# ---------- page builder ----------
class Doc:
    def __init__(self):
        self.pages = []   # each page: list of content-stream strings
        self.buf = []
        self.y = PAGE_H - MARGIN
    def newpage(self):
        if self.buf: self.pages.append(''.join(self.buf))
        self.buf = []; self.y = PAGE_H - MARGIN
    def space(self, h):
        self.y -= h
        if self.y < MARGIN: self.newpage()
    def ensure(self, h):
        if self.y - h < MARGIN: self.newpage()

    def line(self, line_runs, x, size, justify, max_w):
        # natural width and space count
        nat = 0.0; nsp = 0
        for i,(txt,st) in enumerate(line_runs):
            nat += wstr(txt, isbold(st), size)
            if i>0:
                nat += wstr(' ', isbold(st), size); nsp += 1
        tw = 0.0
        if justify and nsp>0:
            tw = (max_w - nat)/nsp
            if tw < 0: tw = 0
        y = self.y
        s = ['BT %.2f %.2f Td %.2f Tw' % (x, y, tw)]
        prev_font = None
        for i,(txt,st) in enumerate(line_runs):
            piece = (' ' if i>0 else '') + txt
            f = FONT[st]
            if f != prev_font:
                s.append('/%s %.1f Tf' % (f, size)); prev_font = f
            s.append('(%s) Tj' % esc(piece))
        s.append('0 Tw ET')
        self.buf.append(' '.join(s) + '\n')

    def paragraph(self, runs, size=SIZE, lead=LEAD, indent=0, justify=True, hang=0, gap=4):
        max_w = CONTENT_W - indent
        lines = wrap_runs(runs, max_w, size)
        for idx, ln in enumerate(lines):
            self.ensure(lead)
            last = (idx == len(lines)-1)
            x = MARGIN + indent
            self.line(ln, x, size, justify and not last, max_w)
            self.y -= lead
        self.y -= gap

    def bullet(self, runs, size=SIZE, lead=LEAD):
        # hanging bullet
        bx = MARGIN
        tx_indent = 14
        max_w = CONTENT_W - tx_indent
        lines = wrap_runs(runs, max_w, size)
        for idx, ln in enumerate(lines):
            self.ensure(lead)
            if idx == 0:
                self.buf.append('BT %.2f %.2f Td /F1 %.1f Tf (\\225) Tj ET\n' % (bx, self.y, size))
            last = (idx == len(lines)-1)
            self.line(ln, bx + tx_indent, size, not last, max_w)
            self.y -= lead
        self.y -= 2

    def heading(self, text, size, bold=True, center=False, gap_before=8, gap_after=3):
        self.space(gap_before)
        self.ensure(size*1.3)
        st = 'b' if bold else ''
        w = wstr(text, bold, size)
        x = MARGIN + (CONTENT_W - w)/2 if center else MARGIN
        self.line([(text, st)], x, size, False, CONTENT_W)
        self.y -= size*1.3
        self.y -= gap_after

    def table(self, headers, rows, colw, size=9.5, pad=4, lead=12):
        x0 = MARGIN
        def cell_lines(text, w):
            return wrap_runs([(text,'')], w-2*pad, size)
        def row_height(cells, ws, header=False):
            mx = 1
            for c,w in zip(cells, ws):
                mx = max(mx, len(cell_lines(c, w)))
            return mx*lead + 2*pad
        # header
        def draw_row(cells, ws, header=False):
            h = row_height(cells, ws, header)
            self.ensure(h)
            ytop = self.y
            # backgrounds + borders
            cx = x0
            if header:
                self.buf.append('0.91 0.91 0.91 rg %.2f %.2f %.2f %.2f re f 0 g\n' % (x0, ytop-h, sum(ws), h))
            cx = x0
            for w in ws:
                self.buf.append('%.2f %.2f %.2f %.2f re S\n' % (cx, ytop-h, w, h))
                cx += w
            # text
            cx = x0
            for c, w in zip(cells, ws):
                lines = cell_lines(c, w)
                ty = ytop - pad - size
                bold = 'b' if header else ''
                for ln in lines:
                    # left aligned
                    self.line([(seg[0], bold) for seg in ln] if False else [(t, ('b' if header else st)) for (t,st) in ln], cx+pad, size, False, w-2*pad)
                    # the line() above uses self.y; override:
                    self.buf[-1] = self.buf[-1]  # noop
                    ty -= lead
                cx += w
            self.y = ytop - h
        # The generic line() uses self.y for baseline, so render cells manually instead:
        def draw_row2(cells, ws, header=False):
            h = row_height(cells, ws, header)
            self.ensure(h)
            ytop = self.y
            cx = x0
            if header:
                self.buf.append('0.91 0.91 0.91 rg %.2f %.2f %.2f %.2f re f 0 g\n' % (x0, ytop-h, sum(ws), h))
            cx = x0
            for w in ws:
                self.buf.append('0.27 0.27 0.27 RG 0.5 w %.2f %.2f %.2f %.2f re S 0 G\n' % (cx, ytop-h, w, h))
                cx += w
            cx = x0
            for c, w in zip(cells, ws):
                lines = cell_lines(c, w)
                ty = ytop - pad - size*0.85
                for ln in lines:
                    runs = [(t, ('b' if header else '')) for (t,st) in ln]
                    s = ['BT %.2f %.2f Td' % (cx+pad, ty)]
                    pf=None
                    for i,(txt,stt) in enumerate(runs):
                        piece=(' ' if i>0 else '')+txt
                        f=FONT[stt]
                        if f!=pf: s.append('/%s %.1f Tf'%(f,size)); pf=f
                        s.append('(%s) Tj'%esc(piece))
                    s.append('ET')
                    self.buf.append(' '.join(s)+'\n')
                    ty -= lead
                cx += w
            self.y = ytop - h
        draw_row2(headers, colw, header=True)
        for r in rows:
            draw_row2(r, colw, header=False)

    def build(self):
        if self.buf: self.pages.append(''.join(self.buf)); self.buf=[]
        objs = []
        # 1 catalog, 2 pages, fonts 3-6, then page objs + content objs
        nfonts = 4
        font_objs = list(range(3, 3+nfonts))
        first_page_obj = 3+nfonts
        npages = len(self.pages)
        page_obj_ids = [first_page_obj + 2*i for i in range(npages)]
        content_ids  = [first_page_obj + 2*i + 1 for i in range(npages)]
        def obj(n, body): objs.append((n, body))
        obj(1, '<< /Type /Catalog /Pages 2 0 R >>')
        kids = ' '.join('%d 0 R' % p for p in page_obj_ids)
        obj(2, '<< /Type /Pages /Count %d /Kids [%s] >>' % (npages, kids))
        bf = [('F1','Helvetica'),('F2','Helvetica-Bold'),('F3','Helvetica-Oblique'),('F4','Helvetica-BoldOblique')]
        for i,(nm, base) in enumerate(bf):
            obj(font_objs[i], '<< /Type /Font /Subtype /Type1 /BaseFont /%s /Encoding /WinAnsiEncoding >>' % base)
        fontres = ' '.join('/%s %d 0 R' % (bf[i][0], font_objs[i]) for i in range(nfonts))
        for i in range(npages):
            obj(page_obj_ids[i], '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] /Resources << /Font << %s >> >> /Contents %d 0 R >>' % (PAGE_W, PAGE_H, fontres, content_ids[i]))
            data = self.pages[i].encode('latin-1', 'replace')
            comp = zlib.compress(data)
            stream = b'<< /Length %d /Filter /FlateDecode >>\nstream\n' % len(comp) + comp + b'\nendstream'
            objs.append((content_ids[i], stream))
        objs.sort(key=lambda x: x[0])
        out = b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n'
        offsets = {}
        for n, body in objs:
            offsets[n] = len(out)
            if isinstance(body, str): body = body.encode('latin-1')
            out += ('%d 0 obj\n' % n).encode() + body + b'\nendobj\n'
        xref_pos = len(out)
        maxn = max(offsets)
        out += ('xref\n0 %d\n' % (maxn+1)).encode()
        out += b'0000000000 65535 f \n'
        for n in range(1, maxn+1):
            out += ('%010d 00000 n \n' % offsets.get(n,0)).encode()
        out += ('trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF' % (maxn+1, xref_pos)).encode()
        return out

# ---------------- content ----------------
def R(*parts): return list(parts)
def t(s): return (s,'')
def b(s): return (s,'b')
def i(s): return (s,'i')

d = Doc()

d.heading('Diagnóstico, impacto y liderazgo ético en la práctica de la ciencia de datos', 13, bold=True, center=True, gap_before=0, gap_after=2)
d.paragraph([i('Ensayo de responsabilidad social y ética profesional')], size=10, justify=False, gap=8)
# center the subtitle manually
# (kept simple; left aligned italic is acceptable)

d.heading('a. Diagnóstico ético personal', 11.5)
d.paragraph([t('Como profesional de la ciencia de datos trabajo con información que describe a personas reales y con modelos que terminan decidiendo sobre ellas; por eso mis decisiones técnicas son, antes que nada, decisiones éticas. Reconozco cuatro valores que hoy guían mi toma de decisiones:')])
d.bullet([b('Veracidad epistémica: '), t('no maquillo resultados. '), i('Evidencia: '), t('en cada informe documento los supuestos, la incertidumbre y las limitaciones del modelo (intervalos de confianza, casos donde falla), aunque eso debilite la "buena noticia" que el cliente espera. Esto conecta con la dimensión de la verdad que Morris (1997) señala como base de la excelencia organizacional.')])
d.bullet([b('Justicia y equidad: '), t('reviso que el modelo no perjudique sistemáticamente a un grupo. '), i('Evidencia: '), t('antes de entregar un clasificador audito su desempeño desagregado por género y procedencia, y reporto las brechas. Sigo aquí la ética del reconocimiento de Cortina (2007): el otro no es un dato, es un interlocutor con dignidad.')])
d.bullet([b('Responsabilidad y cuidado del dato personal: '), t('trato la privacidad como un derecho, no como un trámite. '), i('Evidencia: '), t('aplico anonimización y minimización de datos, y rechazo usar variables sensibles sin consentimiento explícito.')])
d.bullet([b('Transparencia y rendición de cuentas: '), i('Evidencia: '), t('entrego "tarjetas de modelo" (model cards) que explican en lenguaje claro qué hace el algoritmo, con qué datos se entrenó y a quién puede afectar.')])
d.paragraph([b('Dilemas enfrentados. '), t('(1) Detecté que un modelo de scoring para preseleccionar postulantes laborales reproducía un sesgo histórico que penalizaba a candidatas mujeres, pese a tener buen rendimiento global. (2) En otro proyecto recibí presión para entregar un modelo cuyas métricas estaban infladas por una fuga de datos (data leakage): se "veía" excelente, pero engañaba al cliente y a los usuarios finales. Ambas decisiones impactaban directamente a terceros: personas que serían aceptadas o rechazadas por una máquina.')])

d.heading('b. Análisis de impacto — Modelo PASTO', 11.5)
d.paragraph([t('Aplico PASTO al primer dilema: '), b('el modelo de selección con sesgo de género.')])
d.bullet([b('Personas: '), t('postulantes (especialmente mujeres), el equipo de Recursos Humanos que confía en el sistema, mi equipo de datos, la empresa cliente y, de fondo, la sociedad que valora la igualdad de oportunidades.')])
d.bullet([b('Afectos: '), t('sentí incomodidad y responsabilidad al descubrir la brecha; los afectados sentirían frustración e injusticia al ser descartados sin saber por qué. Damasio (1994) explica por qué esa señal emocional importa: los marcadores somáticos no nublan la razón, la orientan hacia lo que debo proteger.')])
d.bullet([b('Situación: '), t('el modelo ya estaba aprobado y en fecha de entrega; corregirlo implicaba retrasos y admitir un error ante el cliente.')])
d.bullet([b('Trade-offs: '), t('precisión global vs. equidad; cumplir el plazo y la facturación vs. detener el despliegue; mi comodidad laboral vs. el derecho de las postulantes a un trato no discriminatorio.')])
d.bullet([b('Opciones: '), t('(i) entregar tal cual; (ii) ocultar la brecha; (iii) detener, comunicarla y rediseñar.')])
d.paragraph([b('Soluciones viables. '), t('Opté y propongo: (1) re-balancear y re-entrenar el modelo retirando o neutralizando las variables que actuaban como sustitutas del género, y aplicar métricas de equidad (paridad demográfica, igualdad de oportunidades) como criterio de aceptación, no solo la exactitud; (2) incorporar supervisión humana en la decisión final, de modo que el algoritmo recomiende pero no excluya automáticamente, y abrir un canal de apelación para el postulante. Ambas soluciones se fundamentan en el derecho a la no discriminación y la igualdad (derechos humanos) y en la ética cordial de Cortina: una decisión es legítima si podría justificarse ante todos los afectados.')])
d.paragraph([b('Reflexión. '), t('Aprendí que la métrica "objetiva" puede esconder una injusticia y que el silencio técnico también es una decisión moral. Cambiaría el momento de la auditoría: integraría las pruebas de equidad desde el diseño del proyecto y no al final, cuando corregir es más costoso y más tentador callar.')])

d.heading('c. Plan de liderazgo ético personal', 11.5)
d.paragraph([b('Valores que me comprometo a promover: '), t('(1) veracidad y transparencia; (2) justicia algorítmica y no discriminación; (3) respeto a la privacidad y la dignidad de las personas; (4) responsabilidad social del dato (orientación al bien común).')])
d.paragraph([b('Estrategias para decidir éticamente (filosofía + neurociencia):')], gap=2)
d.bullet([b('Prueba del interlocutor (Cortina): '), t('antes de desplegar un modelo me pregunto si podría justificar su funcionamiento ante las personas afectadas en un diálogo de iguales. Si no, lo rediseño.')])
d.bullet([b('Escuchar el marcador somático (Damasio): '), t('tomo la incomodidad o la duda no como ruido, sino como una alerta legítima que obliga a detenerme y analizar; la emoción y la razón deciden juntas, no separadas.')])
d.bullet([b('Buscar la excelencia, no solo el resultado (Morris): '), t('evalúo cada proyecto según las cuatro dimensiones —verdad, bien, belleza (claridad/calidad) y unidad (cohesión del equipo)— para que el éxito técnico sea también un éxito humano y sostenible.')])
d.bullet([b('Pausa deliberativa y consulta plural: '), t('en decisiones de alto impacto activo una revisión con pares de distintas perspectivas (técnica, legal, social) antes de cerrar, para contrastar puntos ciegos.')])
d.paragraph([b('Acciones desde mi rol orientadas al bien común: '), t('impulsar auditorías de sesgo y model cards como estándar del equipo; capacitar a colegas y áreas de negocio en lectura crítica de modelos; y promover el uso responsable y la apertura de datos para proyectos de interés público (salud, educación), siempre con resguardo de la privacidad.')], gap=6)

d.table(
    ['Compromiso','Indicador (¿cómo lo mediré?)','Momento (¿cuándo?)','Evidencia (¿qué lo prueba?)'],
    [
      ['Auditar sesgos de equidad en todo modelo que afecte a personas','% de proyectos con auditoría de equidad documentada (meta 100%)','En cada entrega/despliegue de modelo','Reporte de métricas desagregadas y model card archivada'],
      ['Comunicar con transparencia limitaciones e incertidumbre','Presencia de sección de supuestos y riesgos en cada informe','Al cierre de cada análisis o entregable','Informes firmados con apartado de limitaciones'],
      ['Proteger la privacidad y el consentimiento de los datos','N.º de incidentes de uso indebido (meta 0) y % de datos minimizados','Desde la recolección y durante todo el proyecto','Registro de tratamiento de datos y consentimientos'],
    ],
    colw=[150,128,92,100.5]
)

d.heading('Referencias', 11)
d.paragraph([t('Cortina, A. (2007). '), i('Ética de la razón cordial: Educar en la ciudadanía en el siglo XXI. '), t('Nobel.')], size=10, justify=False, indent=14, gap=2)
d.paragraph([t('Damasio, A. (1994). '), i('El error de Descartes: La emoción, la razón y el cerebro humano. '), t('Crítica.')], size=10, justify=False, indent=14, gap=2)
d.paragraph([t('Morris, T. (1997). '), i('Si Aristóteles dirigiera la General Motors. '), t('Planeta.')], size=10, justify=False, indent=14, gap=2)

pdf = d.build()
open('/home/user/Controling/Ensayo_etica_data_science.pdf','wb').write(pdf)
print('pages:', len(d.pages), 'bytes:', len(pdf))
