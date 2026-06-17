# -*- coding: utf-8 -*-
"""Genera comparacion_modelos.html: deck comparando Solo árbol (A) vs Optbinning+árbol (B),
ambos SIN edad_num ni rk_ing_num. Dibuja los árboles estilo flujo (como la imagen 1N)."""

# ----------------------------------------------------------------------------- árboles (export_text reales)
TREES = {}
TREES[("A","CAST")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- saldo_activo_actual <= -50000000.00
|   |   |--- segmentacion_gdp_v2 <= 2.50
|   |   |   |--- value: [803.44]
|   |   |--- segmentacion_gdp_v2 >  2.50
|   |   |   |--- max_dias_mora_castigo <= 2649.50
|   |   |   |   |--- max_dias_mora_castigo <= 2311.50
|   |   |   |   |   |--- value: [779.55]
|   |   |   |   |--- max_dias_mora_castigo >  2311.50
|   |   |   |   |   |--- value: [764.87]
|   |   |   |--- max_dias_mora_castigo >  2649.50
|   |   |   |   |--- nro_entidades_castigo <= 1.50
|   |   |   |   |   |--- max_dias_mora_castigo <= 3038.50
|   |   |   |   |   |   |--- value: [757.12]
|   |   |   |   |   |--- max_dias_mora_castigo >  3038.50
|   |   |   |   |   |   |--- value: [750.47]
|   |   |   |   |--- nro_entidades_castigo >  1.50
|   |   |   |   |   |--- value: [727.04]
|   |--- saldo_activo_actual >  -50000000.00
|   |   |--- value: [713.75]
|--- segmentacion_gdp_v2 >  4.50
|   |--- saldo_activo_actual <= -50000000.00
|   |   |--- max_dias_mora_castigo <= 4428.50
|   |   |   |--- monto_castigado_otros <= 931.90
|   |   |   |   |--- value: [713.75]
|   |   |   |--- monto_castigado_otros >  931.90
|   |   |   |   |--- value: [713.75]
|   |   |--- max_dias_mora_castigo >  4428.50
|   |   |   |--- value: [695.49]
|   |--- saldo_activo_actual >  -50000000.00
|   |   |--- prom_saldo_pasivo_u4m <= 88.37
|   |   |   |--- max_dias_mora_castigo <= 2473.50
|   |   |   |   |--- value: [670.44]
|   |   |   |--- max_dias_mora_castigo >  2473.50
|   |   |   |   |--- max_dias_mora_castigo <= 2991.50
|   |   |   |   |   |--- value: [637.74]
|   |   |   |   |--- max_dias_mora_castigo >  2991.50
|   |   |   |   |   |--- saldo_pasivo_actual <= 2.24
|   |   |   |   |   |   |--- value: [608.01]
|   |   |   |   |   |--- saldo_pasivo_actual >  2.24
|   |   |   |   |   |   |--- value: [625.47]
|   |   |--- prom_saldo_pasivo_u4m >  88.37
|   |   |   |--- value: [713.75]
"""
TREES[("B","CAST")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- max_dias_mora_castigo <= 2533.50
|   |   |--- segmentacion_gdp_v2 <= 3.50
|   |   |   |--- value: [794.59]
|   |   |--- segmentacion_gdp_v2 >  3.50
|   |   |   |--- max_dias_mora_castigo <= 2079.50
|   |   |   |   |--- value: [770.10]
|   |   |   |--- max_dias_mora_castigo >  2079.50
|   |   |   |   |--- value: [753.48]
|   |--- max_dias_mora_castigo >  2533.50
|   |   |--- max_dias_mora_castigo <= 2965.50
|   |   |   |--- max_dias_mora_castigo <= 2747.50
|   |   |   |   |--- value: [749.11]
|   |   |   |--- max_dias_mora_castigo >  2747.50
|   |   |   |   |--- value: [748.87]
|   |   |--- max_dias_mora_castigo >  2965.50
|   |   |   |--- prom_saldo_pasivo_u4m <= 17.06
|   |   |   |   |--- DEUDA_CAS <= 436.68
|   |   |   |   |   |--- value: [733.95]
|   |   |   |   |--- DEUDA_CAS >  436.68
|   |   |   |   |   |--- max_dias_mora_castigo <= 3661.50
|   |   |   |   |   |   |--- value: [730.91]
|   |   |   |   |   |--- max_dias_mora_castigo >  3661.50
|   |   |   |   |   |   |--- value: [727.45]
|   |   |   |--- prom_saldo_pasivo_u4m >  17.06
|   |   |   |   |--- value: [739.53]
|--- segmentacion_gdp_v2 >  4.50
|   |--- max_dias_mora_castigo <= 2470.50
|   |   |--- prom_saldo_pasivo_u4m <= 3.75
|   |   |   |--- value: [709.71]
|   |   |--- prom_saldo_pasivo_u4m >  3.75
|   |   |   |--- value: [711.06]
|   |--- max_dias_mora_castigo >  2470.50
|   |   |--- nro_entidades_castigo <= 1.50
|   |   |   |--- max_dias_mora_castigo <= 2995.50
|   |   |   |   |--- value: [690.71]
|   |   |   |--- max_dias_mora_castigo >  2995.50
|   |   |   |   |--- max_dias_mora_castigo <= 4675.50
|   |   |   |   |   |--- max_dias_mora_castigo <= 3673.50
|   |   |   |   |   |   |--- value: [681.48]
|   |   |   |   |   |--- max_dias_mora_castigo >  3673.50
|   |   |   |   |   |   |--- value: [676.50]
|   |   |   |   |--- max_dias_mora_castigo >  4675.50
|   |   |   |   |   |--- value: [669.61]
|   |   |--- nro_entidades_castigo >  1.50
|   |   |   |--- value: [635.44]
"""
TREES[("A","NOCAST")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- segmentacion_gdp_v2 <= 3.50
|   |   |--- segmentacion_gdp_v2 <= 2.50
|   |   |   |--- value: [826.65]
|   |   |--- segmentacion_gdp_v2 >  2.50
|   |   |   |--- meses_desde_ultimo_castigo <= 6.50
|   |   |   |   |--- value: [754.92]
|   |   |   |--- meses_desde_ultimo_castigo >  6.50
|   |   |   |   |--- meses_desde_ultimo_castigo <= 13.50
|   |   |   |   |   |--- value: [770.03]
|   |   |   |   |--- meses_desde_ultimo_castigo >  13.50
|   |   |   |   |   |--- value: [771.72]
|   |--- segmentacion_gdp_v2 >  3.50
|   |   |--- prom_saldo_pasivo_u4m <= 41.67
|   |   |   |--- meses_desde_primer_castigo <= 20.50
|   |   |   |   |--- value: [703.22]
|   |   |   |--- meses_desde_primer_castigo >  20.50
|   |   |   |   |--- DEUDA_CAS <= 505.87
|   |   |   |   |   |--- value: [737.94]
|   |   |   |   |--- DEUDA_CAS >  505.87
|   |   |   |   |   |--- value: [722.13]
|   |   |--- prom_saldo_pasivo_u4m >  41.67
|   |   |   |--- value: [754.69]
|--- segmentacion_gdp_v2 >  4.50
|   |--- meses_desde_primer_castigo <= 9.50
|   |   |--- value: [518.57]
|   |--- meses_desde_primer_castigo >  9.50
|   |   |--- prom_saldo_pasivo_u4m <= 54.50
|   |   |   |--- meses_desde_ultimo_castigo <= 17.50
|   |   |   |   |--- DEUDA_CAS <= 422.90
|   |   |   |   |   |--- value: [670.95]
|   |   |   |   |--- DEUDA_CAS >  422.90
|   |   |   |   |   |--- value: [658.08]
|   |   |   |--- meses_desde_ultimo_castigo >  17.50
|   |   |   |   |--- value: [681.42]
|   |   |--- prom_saldo_pasivo_u4m >  54.50
|   |   |   |--- value: [702.68]
"""
TREES[("B","NOCAST")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- segmentacion_gdp_v2 <= 3.50
|   |   |--- segmentacion_gdp_v2 <= 2.50
|   |   |   |--- value: [826.65]
|   |   |--- segmentacion_gdp_v2 >  2.50
|   |   |   |--- meses_desde_ultimo_castigo <= 6.50
|   |   |   |   |--- value: [754.92]
|   |   |   |--- meses_desde_ultimo_castigo >  6.50
|   |   |   |   |--- meses_desde_ultimo_castigo <= 13.50
|   |   |   |   |   |--- value: [770.03]
|   |   |   |   |--- meses_desde_ultimo_castigo >  13.50
|   |   |   |   |   |--- value: [771.72]
|   |--- segmentacion_gdp_v2 >  3.50
|   |   |--- prom_saldo_pasivo_u4m <= 41.67
|   |   |   |--- meses_desde_primer_castigo <= 20.50
|   |   |   |   |--- value: [703.22]
|   |   |   |--- meses_desde_primer_castigo >  20.50
|   |   |   |   |--- DEUDA_CAS <= 505.87
|   |   |   |   |   |--- value: [737.94]
|   |   |   |   |--- DEUDA_CAS >  505.87
|   |   |   |   |   |--- value: [722.13]
|   |   |--- prom_saldo_pasivo_u4m >  41.67
|   |   |   |--- value: [754.69]
|--- segmentacion_gdp_v2 >  4.50
|   |--- meses_desde_primer_castigo <= 9.50
|   |   |--- value: [518.57]
|   |--- meses_desde_primer_castigo >  9.50
|   |   |--- prom_saldo_pasivo_u4m <= 54.50
|   |   |   |--- meses_desde_ultimo_castigo <= 17.50
|   |   |   |   |--- DEUDA_CAS <= 422.90
|   |   |   |   |   |--- value: [670.95]
|   |   |   |   |--- DEUDA_CAS >  422.90
|   |   |   |   |   |--- value: [658.08]
|   |   |   |--- meses_desde_ultimo_castigo >  17.50
|   |   |   |   |--- value: [681.42]
|   |   |--- prom_saldo_pasivo_u4m >  54.50
|   |   |   |--- value: [702.68]
"""

PRETTY = {
    "segmentacion_gdp_v2": "segmentación", "max_dias_mora_castigo": "máx días mora",
    "nro_entidades_castigo": "nro entidades", "prom_saldo_pasivo_u4m": "ahorro prom 4m",
    "DEUDA_CAS": "deuda cast.", "meses_desde_ultimo_castigo": "meses últ. castigo",
    "meses_desde_primer_castigo": "meses 1er castigo", "saldo_pasivo_actual": "saldo pasivo",
    "monto_castigado_otros": "monto cast. otros", "monto_castigado_total": "monto cast. total",
}

def color(s, lo=540.0, hi=890.0):
    t = max(0.0, min(1.0, (s - lo) / (hi - lo)))
    if t < 0.5:
        r, g, b = 224, int(120 + 100 * (t * 2)), 70
    else:
        r, g, b = int(224 - 150 * ((t - 0.5) * 2)), 176, 70
    return f"rgb({r},{g},{b})"

def fmt_cond(c):
    for op, sym in ((" <= ", "≤"), (" >  ", ">")):
        if op in c:
            var, thr = c.split(op)
            thr = float(thr)
            if var == "saldo_activo_actual":      # corte en el sentinel = flag de missing
                return ("⚑ saldo_activo = MISSING" if sym == "≤" else "saldo_activo = con dato"), (var == "saldo_activo_actual")
            v = PRETTY.get(var, var)
            if var == "segmentacion_gdp_v2":
                return f"{v} {sym} {int(round(thr))}", False
            return f"{v} {sym} {thr:,.0f}", False
    return c, False

def parse(text):
    root = {"label": None, "children": []}
    stack = [(-1, root)]
    for line in text.strip("\n").split("\n"):
        if "|---" not in line:
            continue
        idx = line.find("|---")
        depth = idx // 4
        content = line[idx + 4:].strip()
        node = {"label": content, "children": []}
        while stack and stack[-1][0] >= depth:
            stack.pop()
        stack[-1][1]["children"].append(node)
        stack.append((depth, node))
    return root

def render(node):
    kids = node["children"]
    if not kids:                                  # hoja
        s = float(node["label"].split("[")[1].split("]")[0])
        return f'<li><span class="leaf" style="background:{color(s)}">{s:.0f}</span></li>'
    cond, miss = fmt_cond(node["label"])
    cls = "cond miss" if miss else "cond"
    inner = "".join(render(k) for k in kids)
    return f'<li><span class="{cls}">{cond}</span><ul>{inner}</ul></li>'

def tree_html(key, title):
    root = parse(TREES[key])
    inner = "".join(render(k) for k in root["children"])
    return f'<ul class="tree"><li><span class="root">{title}</span><ul>{inner}</ul></li></ul>'

# ----------------------------------------------------------------------------- HTML
CSS = """
:root{--navy:#16366e;--navy2:#1f4e96;--green:#43b02a;--green-d:#2e7d1c;--ink:#2b2b2b;
--muted:#6b7280;--line:#cdd8e6;--soft:#eef3f9;--red:#c0392b;--amber:#e08e0b;}
*{box-sizing:border-box;margin:0;padding:0;}html,body{height:100%;}
body{font-family:"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:#0c1830;}
.deck{position:relative;width:100vw;height:100vh;overflow:hidden;}
.slide{position:absolute;inset:0;background:#fff;padding:42px 60px 64px;display:none;flex-direction:column;overflow:hidden;}
.slide.active{display:flex;animation:fade .35s ease;}
@keyframes fade{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:none;}}
.logo{position:absolute;top:30px;right:50px;font-weight:800;font-size:32px;color:var(--navy);}
.logo .n{color:var(--green);}
h1{color:var(--navy);font-size:40px;font-weight:800;line-height:1.05;}
h2{color:var(--navy);font-size:28px;font-weight:800;margin-bottom:4px;}
.sub{color:var(--green);font-size:20px;font-weight:600;margin-top:6px;}
.kicker{color:var(--green);font-weight:700;letter-spacing:2px;font-size:13px;text-transform:uppercase;margin-bottom:10px;}
p{font-size:17px;line-height:1.5;color:#37414f;}.lead{font-size:19px;}
ul.b{margin:8px 0 0 22px;}ul.b li{font-size:16px;line-height:1.5;margin-bottom:6px;color:#37414f;}
b,strong{color:var(--navy);}.green{color:var(--green-d);}.red{color:var(--red);}.amber{color:var(--amber);}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:16px;flex:1;min-height:0;}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px;margin-top:16px;}
.card{border:1px solid var(--line);border-radius:14px;padding:20px 22px;background:#fff;box-shadow:0 6px 18px rgba(20,40,80,.06);}
.card.win{border:2px solid var(--green);}.card.warn{border:2px solid #e7c27a;background:#fffdf6;}
.card h3{font-size:20px;margin-bottom:4px;color:var(--navy);}
.tag{display:inline-block;font-size:12px;font-weight:700;padding:3px 10px;border-radius:20px;color:#fff;margin-bottom:8px;}
.tag.b{background:var(--green);}.tag.a{background:var(--navy2);}
table{width:100%;border-collapse:collapse;margin-top:12px;font-size:15px;}
th,td{border:1px solid var(--line);padding:7px 9px;text-align:center;}
th{background:var(--navy);color:#fff;}td.l{text-align:left;}tr:nth-child(even) td{background:var(--soft);}
.best{background:#e7f6e2!important;color:var(--green-d);font-weight:700;}
.bar-row{display:flex;align-items:center;gap:10px;margin:6px 0;font-size:13px;}
.bar-lab{width:170px;text-align:right;color:#37414f;}
.bar-wrap{flex:1;background:#eef2f7;border-radius:6px;overflow:hidden;height:19px;}
.bar{height:100%;border-radius:6px;}.bar.b{background:linear-gradient(90deg,#43b02a,#6fce53);}
.bar.a{background:linear-gradient(90deg,#1f4e96,#3f78c9);}.bar-val{width:50px;color:var(--navy);font-weight:700;}
.callout{margin-top:12px;border-left:5px solid var(--green);background:#f2faef;padding:12px 16px;border-radius:0 10px 10px 0;}
.callout.bad{border-color:var(--red);background:#fdf1f0;}.callout p{font-size:15px;}
.verdict{display:flex;align-items:center;gap:14px;background:var(--navy);color:#fff;border-radius:14px;padding:18px 24px;margin-top:auto;}
.verdict .big{font-size:21px;font-weight:800;}.verdict .big em{color:#7fe06a;font-style:normal;}
.foot{position:absolute;left:60px;bottom:20px;font-size:12px;color:var(--muted);}
.note{font-size:13px;color:var(--muted);margin-top:6px;}
.pill{display:inline-block;background:var(--soft);border:1px solid var(--line);border-radius:20px;padding:5px 12px;font-size:13px;color:var(--navy);font-weight:600;margin:3px 4px 0 0;}
.nav{position:fixed;bottom:16px;right:24px;display:flex;gap:12px;z-index:20;}
.nav button{border:none;background:var(--navy);color:#fff;width:38px;height:38px;border-radius:50%;font-size:18px;cursor:pointer;}
.nav button:hover{background:var(--green);}
.counter{position:fixed;bottom:22px;left:50%;transform:translateX(-50%);color:#fff;background:rgba(0,0,0,.35);padding:4px 14px;border-radius:20px;font-size:13px;z-index:20;}
/* árbol estilo flujo */
.treecol{overflow:auto;max-height:64vh;border:1px solid var(--line);border-radius:12px;padding:10px 8px;background:#fcfdff;}
.treehd{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}
.tree,.tree ul{list-style:none;margin:0;padding:0;}
.tree{font-size:11.5px;}
.tree ul{margin-left:14px;padding-left:14px;position:relative;}
.tree ul::before{content:"";position:absolute;left:0;top:-6px;bottom:14px;border-left:2px solid var(--line);}
.tree li{position:relative;padding:3px 0 3px 14px;}
.tree li::before{content:"";position:absolute;left:0;top:13px;width:12px;border-top:2px solid var(--line);}
.tree>li{padding-left:0;}.tree>li::before{display:none;}.tree>li>ul::before{display:none;}.tree>li>ul{margin-left:0;padding-left:0;}
.root{display:inline-block;background:var(--navy);color:#fff;font-weight:700;padding:5px 12px;border-radius:8px;font-size:13px;}
.cond{display:inline-block;background:#eaf1fb;border:1px solid #cfe0f5;color:var(--navy);padding:3px 9px;border-radius:7px;white-space:nowrap;}
.cond.miss{background:#fdeceb;border-color:#f3c2bd;color:var(--red);font-weight:700;}
.leaf{display:inline-block;color:#1d1d1d;font-weight:800;padding:3px 10px;border-radius:14px;min-width:42px;text-align:center;box-shadow:inset 0 0 0 1px rgba(0,0,0,.08);}
.lgnd{font-size:12px;color:var(--muted);}
.lgnd .sw{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-1px;margin:0 3px 0 8px;}
"""

def slide(content):
    return f'<section class="slide">{content}</section>'

LOGO = '<div class="logo">1<span class="n">N</span></div>'

slides = []

# 1 portada
slides.append(f"""<section class="slide active">{LOGO}
<div style="margin-top:6vh">
<div class="kicker">Rebancarización Castigados · Modelo de segmentación</div>
<h1>Optbinning + Árbol &nbsp;vs.&nbsp; Solo Árbol</h1>
<div class="sub">Comparación justa: ambos modelos SIN ingreso (rk_ing) ni edad</div>
<p class="lead" style="margin-top:20px;max-width:900px">Mismo dataset (~2.7&nbsp;MM, 4 escenarios) y mismas variables.
Proxy de riesgo: <b>puntaje_mod</b> (alto = menor riesgo). Objetivo: priorizar <b>grupos de bajo riesgo</b>,
deduplicados por <b>subject_id</b>.</p>
<div style="margin-top:18px"><span class="pill">2.7 MM registros</span><span class="pill">4 escenarios</span>
<span class="pill">Restricciones monótonas de negocio</span><span class="pill">Leads sin duplicados</span></div>
</div><div class="foot">Comparativo de modelos · uso interno</div></section>""")

# 2 metodologias
slides.append(slide("""<h2>Las dos metodologías</h2>
<div class="sub" style="font-size:17px">Misma estructura; cambia cómo se decide la dirección y qué variables entran.</div>
<div class="grid2">
<div class="card win"><span class="tag b">MODELO B · recomendado</span><h3>Optbinning + Árbol</h3>
<ul class="b"><li>Dirección <b>fijada por negocio</b> (castigo/mora/deuda ↓ ; ahorro ↑).</li>
<li>Optbinning exige <b>5 bins (o 2 mínimo)</b>; <b>si no binariza con esa dirección, descarta la variable.</b></li>
<li>El árbol solo usa variables <b>coherentes y estables</b>.</li></ul></div>
<div class="card"><span class="tag a">MODELO A</span><h3>Solo Árbol</h3>
<ul class="b"><li>Dirección inferida de datos (Spearman); <b>entran todas</b>.</li>
<li>Sin filtro de binarización → admite variables ruidosas o artefactos.</li>
<li>Más flexible, menos disciplinado para producción.</li></ul></div></div>
<div class="callout"><p>Para que la comparación sea limpia, en esta corrida <b>ambos excluyen <code>edad_num</code> y <code>rk_ing_num</code></b>.</p></div>
<div class="foot">2 · Definición</div>"""))

# 3 hallazgo
slides.append(slide("""<h2>El hallazgo decisivo: ¿de qué se alimenta cada árbol?</h2>
<div class="grid2">
<div class="card win"><span class="tag b">MODELO B</span><h3 class="green">Señales reales de riesgo</h3>
<ul class="b"><li>Drivers: <b>segmentación</b>, <b>severidad de mora</b>, <b>multi-entidad</b>, <b>ahorro</b>.</li>
<li>En NO_CAST descarta castigo/mora (no aplican). Descarta <code>saldo_activo</code> (no binariza).</li>
<li>Reglas <b>explicables y auditables</b>.</li></ul></div>
<div class="card warn"><span class="tag a">MODELO A</span><h3 class="red">Usa el “dato faltante” como predictor</h3>
<ul class="b"><li>Su 2º driver es <code>saldo_activo ≤ -50,000,000</code> = clientes <b>SIN dato</b> (⚑ MISSING) — <b>33.2% del peso</b> en CAST.</li>
<li>Varias estrategias top se definen por <b>“no tener saldo activo”</b> (artefacto, no comportamiento).</li>
<li>Dirección de <code>saldo_activo</code> inconsistente entre escenarios (0 vs +1).</li></ul></div></div>
<div class="foot">3 · Coherencia</div>"""))

# 4 importancia
slides.append(slide("""<h2>Importancia de variables (escenario CAST · 1.7&nbsp;MM)</h2>
<div class="grid2">
<div class="card"><span class="tag b">MODELO B</span><div style="margin-top:10px">
<div class="bar-row"><div class="bar-lab">segmentación</div><div class="bar-wrap"><div class="bar b" style="width:84%"></div></div><div class="bar-val">67.8%</div></div>
<div class="bar-row"><div class="bar-lab">máx días mora</div><div class="bar-wrap"><div class="bar b" style="width:31%"></div></div><div class="bar-val">25.3%</div></div>
<div class="bar-row"><div class="bar-lab">nro entidades</div><div class="bar-wrap"><div class="bar b" style="width:8%"></div></div><div class="bar-val">6.6%</div></div>
<div class="bar-row"><div class="bar-lab">ahorro prom 4m</div><div class="bar-wrap"><div class="bar b" style="width:2%"></div></div><div class="bar-val">0.3%</div></div></div>
<div class="callout"><p>100% variables de <b>comportamiento</b>.</p></div></div>
<div class="card"><span class="tag a">MODELO A</span><div style="margin-top:10px">
<div class="bar-row"><div class="bar-lab">segmentación</div><div class="bar-wrap"><div class="bar a" style="width:60%"></div></div><div class="bar-val">47.8%</div></div>
<div class="bar-row"><div class="bar-lab">saldo_activo (=MISSING)</div><div class="bar-wrap"><div class="bar" style="width:42%;background:linear-gradient(90deg,#c0392b,#e57368)"></div></div><div class="bar-val red">33.2%</div></div>
<div class="bar-row"><div class="bar-lab">ahorro prom 4m</div><div class="bar-wrap"><div class="bar a" style="width:12%"></div></div><div class="bar-val">9.3%</div></div>
<div class="bar-row"><div class="bar-lab">máx días mora</div><div class="bar-wrap"><div class="bar a" style="width:10%"></div></div><div class="bar-val">8.3%</div></div></div>
<div class="callout bad"><p>El <b>2º driver es un artefacto</b> (flag de dato faltante).</p></div></div></div>
<div class="foot">4 · Importancia</div>"""))

# 5 volumen
slides.append(slide("""<h2>Volumen de leads de bajo riesgo (deduplicados)</h2>
<table>
<tr><th>Corte (top % puntaje)</th><th>top 10%</th><th>top 15%</th><th>top 20%</th><th>top 30%</th></tr>
<tr><td class="l"><b>Modelo A · Solo árbol</b></td><td>91,972</td><td>128,623</td><td>160,489</td><td>216,848</td></tr>
<tr><td class="l"><b>Modelo B · Optbinning</b></td><td>91,672</td><td>127,997</td><td>158,165</td><td>213,261</td></tr>
<tr><td class="l">Diferencia (A − B)</td><td>+300</td><td>+626</td><td>+2,324</td><td>+3,587</td></tr>
</table>
<div class="grid2" style="margin-top:16px">
<div class="card warn"><h3 class="amber">Empate técnico en volumen</h3>
<ul class="b"><li>A solo aporta <b>+0.5%</b> de leads en top 15% (≈ 626 clientes).</li>
<li>Ese “extra” proviene de segmentos definidos por el <b>flag de missing</b> → volumen <b>poco defendible</b>.</li></ul></div>
<div class="card win"><h3 class="green">Mismo volumen, mejor calidad</h3>
<ul class="b"><li>B entrega prácticamente los mismos leads <b>sin artefactos</b> y con segmentos explicables.</li>
<li>A igualdad de volumen, <b>gana la robustez</b>.</li></ul></div></div>
<div class="foot">5 · Volumen de leads</div>"""))

# 6 calidad segmentos
slides.append(slide("""<h2>Calidad de los segmentos top</h2>
<div class="grid2">
<div class="card win"><span class="tag b">MODELO B · reglas limpias</span>
<table><tr><th class="l">Regla del segmento</th><th>score</th></tr>
<tr><td class="l">segmentación ≤2 &amp; deuda ≤551</td><td class="best">875</td></tr>
<tr><td class="l">segmentación ≤4 &amp; ahorro_prom &gt;602</td><td class="best">840</td></tr>
<tr><td class="l">segmentación ≤4 &amp; mora ≤2,534</td><td>795</td></tr>
<tr><td class="l">segmentación(2,4] &amp; meses_últ_cast &gt;6 &amp; deuda ≤805</td><td>802</td></tr></table>
<p class="note">Comportamiento de pago + ahorro.</p></div>
<div class="card"><span class="tag a">MODELO A · varios con artefacto</span>
<table><tr><th class="l">Regla del segmento</th><th>n_leads</th></tr>
<tr><td class="l">segmentación ≤2 &amp; <span class="red">saldo_activo MISSING</span></td><td>21,765</td></tr>
<tr><td class="l">segmentación(2,4] &amp; <span class="red">saldo_activo MISSING</span> &amp; mora ≤2,312</td><td>30,790</td></tr>
<tr><td class="l">… &amp; <span class="red">saldo_activo MISSING</span> &amp; mora(2,312–2,650]</td><td>12,330</td></tr>
<tr><td class="l">… &amp; <span class="red">saldo_activo MISSING</span> &amp; mora(2,650–3,038]</td><td>9,010</td></tr></table>
<p class="note red">≈ 7 de las 20 estrategias dependen de “no tener saldo activo”.</p></div></div>
<div class="foot">6 · Calidad de segmentación</div>"""))

# 7-8 árboles
LEG = ('<div class="lgnd">Hojas coloreadas por puntaje_mod: '
       '<span class="sw" style="background:rgb(74,176,70)"></span>menor riesgo · '
       '<span class="sw" style="background:rgb(224,176,70)"></span>medio · '
       '<span class="sw" style="background:rgb(224,60,70)"></span>mayor riesgo</div>')

slides.append(slide(f"""<h2>Árboles · Escenario CAST (castigados, 1.7&nbsp;MM)</h2>{LEG}
<div class="grid2">
<div><div class="treehd"><span class="tag a">MODELO A · Solo árbol</span></div>
<div class="treecol">{tree_html(("A","CAST"),"CAST · Solo árbol")}</div></div>
<div><div class="treehd"><span class="tag b">MODELO B · Optbinning</span></div>
<div class="treecol">{tree_html(("B","CAST"),"CAST · Optbinning")}</div></div></div>
<div class="callout bad"><p>En A, el <b>primer/segundo corte</b> ya es <code>saldo_activo = MISSING</code>. En B la raíz es <b>segmentación</b> y luego <b>mora/entidades</b>.</p></div>
<div class="foot">7 · Árboles CAST</div>"""))

slides.append(slide(f"""<h2>Árboles · Escenario NO_CAST (no castigados, 0.6&nbsp;MM)</h2>{LEG}
<div class="grid2">
<div><div class="treehd"><span class="tag a">MODELO A · Solo árbol</span></div>
<div class="treecol">{tree_html(("A","NOCAST"),"NO_CAST · Solo árbol")}</div></div>
<div><div class="treehd"><span class="tag b">MODELO B · Optbinning</span></div>
<div class="treecol">{tree_html(("B","NOCAST"),"NO_CAST · Optbinning")}</div></div></div>
<div class="callout"><p>Aquí <b>ambos coinciden</b>: <b>segmentación + meses desde castigo + ahorro</b>. Sin variables de castigo (no aplican) y sin artefactos. Buena señal de estabilidad.</p></div>
<div class="foot">8 · Árboles NO_CAST</div>"""))

# 9 veredicto
slides.append(slide("""<h2>Veredicto comparativo</h2>
<table>
<tr><th>Criterio</th><th>Modelo B · Optbinning</th><th>Modelo A · Solo árbol</th></tr>
<tr><td class="l">Coherencia de negocio</td><td class="best">Alta — 100% coherente</td><td>Media — inconsistencias</td></tr>
<tr><td class="l">Artefacto (missing como predictor)</td><td class="best">Nulo</td><td class="red">Alto (33% del peso en CAST)</td></tr>
<tr><td class="l">Explicabilidad / auditoría</td><td class="best">Alta</td><td>Media</td></tr>
<tr><td class="l">Selección automática de variables</td><td class="best">Sí</td><td>No</td></tr>
<tr><td class="l">Volumen de leads (top 15%)</td><td>127,997</td><td>128,623 <span class="note">(+0.5%)</span></td></tr>
<tr><td class="l">Robustez para producción 3&nbsp;MM</td><td class="best">Alta</td><td>Media</td></tr></table>
<div class="verdict"><div class="big">A <em>igual volumen</em>, se recomienda implementar el <em>Modelo B (Optbinning + Árbol)</em>; usar A solo como benchmark.</div></div>
<div class="foot">9 · Veredicto</div>"""))

# 10 proximos pasos
slides.append(f"""<section class="slide">{LOGO}<h2>Recomendación e implementación</h2>
<div class="grid3">
<div class="card win"><h3 class="green">1 · Modelo base</h3><p>Adoptar <b>Optbinning + Árbol</b> con direcciones de negocio y descarte automático de variables.</p></div>
<div class="card"><h3>2 · Recuperar poder</h3><p>Evaluar <b>reincorporar rk_ing (ingreso, ↑)</b> a B para subir volumen sin perder coherencia, ahora que descartamos el artefacto.</p></div>
<div class="card"><h3>3 · Activación</h3><p>Usar la <b>hoja de Estrategia</b> (top segmentos, sin duplicados) y el CSV de leads. Calibrar el corte 10–30% según campaña.</p></div></div>
<div class="callout" style="margin-top:20px"><p><b>Quick win:</b> el corte <b>top 15%</b> de B entrega <b>~128 mil leads de riesgo controlado</b>, 100% explicables, listos para desplegar.</p></div>
<div class="verdict" style="background:var(--green-d)"><div class="big">Misma cosecha de leads, base más limpia → menos pérdida y mejor tasa de aprobación.</div></div>
<div class="foot">10 · Próximos pasos</div></section>""")

HTML = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Comparación de Modelos — Rebancarización Castigados</title><style>{CSS}</style></head>
<body><div class="deck" id="deck">{''.join(slides)}</div>
<div class="counter" id="counter">1 / {len(slides)}</div>
<div class="nav"><button onclick="go(-1)">‹</button><button onclick="go(1)">›</button></div>
<script>
const slides=[...document.querySelectorAll('.slide')];let i=0;
function show(n){{slides[i].classList.remove('active');i=(n+slides.length)%slides.length;
slides[i].classList.add('active');document.getElementById('counter').textContent=(i+1)+' / '+slides.length;}}
function go(d){{show(i+d);}}
document.addEventListener('keydown',e=>{{if(e.key==='ArrowRight'||e.key===' ')go(1);if(e.key==='ArrowLeft')go(-1);}});
</script></body></html>"""

with open("comparacion_modelos.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"OK -> comparacion_modelos.html ({len(slides)} slides, {len(HTML)} chars)")
