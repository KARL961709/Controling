# -*- coding: utf-8 -*-
"""
Generador de presentación HTML a partir de un Excel.

ENTRADA  : un .xlsx donde CADA HOJA es un escenario y contiene el bloque
           "CUADRO DEL ÁRBOL COMPLETO" (el que exporta tu pipeline):
               var1 | var2 | ... | n | % | score_medio (o RD_medio) | quintil
SALIDA   : un .html con:
             - Hoja "Resumen / Comparación"
             - Por escenario: tabla de Segmentos + Optimizador de apetito (± % manual)
             - Por escenario: Árbol (ramificación) reconstruido desde las reglas

Uso:
    python build_presentacion_excel.py
  (o ajusta EXCEL_IN / HTML_OUT / OBJETIVO / APETITO abajo)
"""
import sys
import math
import html as _html
import pandas as pd
import matplotlib.cm as cm

# ====================== CONFIG ======================
EXCEL_IN  = "segmentacion_score.xlsx"      # tu Excel (una hoja por escenario)
HTML_OUT  = "presentacion_segmentacion.html"
TITULO    = "Segmentación de riesgo — Escenarios"
OBJETIVO  = "SCORE"                        # "SCORE" (mayor=menor riesgo) | "RD" (mayor=mayor riesgo)
APETITO   = 730                            # umbral base (730 score | 0.02 RD)
# hojas que NO son escenarios (se ignoran)
SKIP = {"índice", "indice", "estrategia", "leads"}
# título del bloque a buscar en cada hoja
TITULO_CUADRO = "CUADRO DEL ÁRBOL COMPLETO"
# ====================================================

_SCORE = (OBJETIVO.upper() == "SCORE")
INF = math.inf


# ---------- helpers numéricos / formato ----------
def _num(s):
    s = str(s).strip().replace(",", "")
    if "inf" in s:
        return -INF if s.startswith("-") else INF
    return float(s)


def fmtnum(x):
    if x in (INF, -INF):
        return "∞" if x > 0 else "-∞"
    if abs(x - round(x)) < 1e-9:
        return f"{int(round(x)):,}"
    return f"{x:,.4f}".rstrip("0").rstrip(".")


def esc(t):
    return _html.escape(str(t), quote=True)


def hexcol(good):
    """good in [0,1]: 1 = mejor (verde), 0 = peor (rojo)."""
    good = max(0.0, min(1.0, good))
    r, g, b, _ = cm.RdYlGn(good)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def goodness(v, vmin, vmax):
    if vmax <= vmin:
        return 0.5
    return (v - vmin) / (vmax - vmin) if _SCORE else (vmax - v) / (vmax - vmin)


def parse_interval(lbl):
    """Devuelve (lo, hi, missing). 'missing' marca si incluye el bin Missing."""
    s = str(lbl).strip()
    if s in ("", "nan", "None", "(todos)"):
        return (-INF, INF, False)
    miss = "Missing" in s
    s = s.replace("Missing", "").replace("+", "").strip()
    if not s:
        return (-INF, INF, miss)
    try:
        if s.startswith("<="):
            return (-INF, _num(s[2:]), miss)
        if s.startswith(">"):
            return (_num(s[1:]), INF, miss)
        if s.startswith("(") and s.endswith("]") and "," in s:
            a, b = s[1:-1].split(",", 1)
            return (_num(a), _num(b), miss)
    except Exception:
        pass
    return (-INF, INF, miss)


def passes(score):
    return score >= APETITO if _SCORE else score <= APETITO


QCOLOR = {"G1": "#1a9850", "G2": "#a6d96a", "G3": "#fee08b", "G4": "#fdae61", "G5": "#d73027"}


# ---------- 1) leer un escenario del Excel ----------
def leer_hoja(df):
    """df = hoja cruda (header=None). Devuelve lista de leaves o None si no halla el cuadro."""
    nfil, ncol = df.shape
    trow = None
    for i in range(nfil):
        c0 = str(df.iat[i, 0]) if pd.notna(df.iat[i, 0]) else ""
        if c0.strip().upper().startswith(TITULO_CUADRO):
            trow = i
            break
    if trow is None:
        return None

    hrow = trow + 1
    headers = [str(df.iat[hrow, j]).strip() if pd.notna(df.iat[hrow, j]) else "" for j in range(ncol)]
    if "n" not in headers:
        return None
    idx_n = headers.index("n")
    variables = [headers[j] for j in range(idx_n) if headers[j]]
    idx_pct, idx_sc, idx_q = idx_n + 1, idx_n + 2, idx_n + 3
    col_med = headers[idx_sc] if idx_sc < ncol else "score_medio"

    leaves = []
    r = hrow + 1
    while r < nfil:
        vn = df.iat[r, idx_n] if idx_n < ncol else None
        if pd.isna(vn):
            break
        try:
            n = int(float(vn))
        except Exception:
            break
        try:
            score = float(df.iat[r, idx_sc])
        except Exception:
            r += 1
            continue
        pct = None
        if idx_pct < ncol and pd.notna(df.iat[r, idx_pct]):
            try:
                pct = float(df.iat[r, idx_pct])
            except Exception:
                pct = None
        quint = str(df.iat[r, idx_q]).strip() if (idx_q < ncol and pd.notna(df.iat[r, idx_q])) else ""

        conds, partes = {}, []
        for j, var in enumerate(variables):
            lbl = str(df.iat[r, j]).strip() if pd.notna(df.iat[r, j]) else ""
            lo, hi, _miss = parse_interval(lbl)
            conds[var] = (lo, hi)
            if lbl and lbl not in ("(todos)", "nan", "None"):
                partes.append(f"{var} {lbl}")
        regla = " · ".join(partes) if partes else "(raíz)"
        leaves.append(dict(conds=conds, regla=regla, n=n, score=score, pct=pct, quint=quint))
        r += 1
    return leaves if leaves else None


# ---------- 2) reconstruir árbol desde las reglas ----------
def mejor_split(leaves, variables):
    best = None
    for var in variables:
        bset = set()
        for lf in leaves:
            lo, hi = lf["conds"].get(var, (-INF, INF))
            if lo > -INF:
                bset.add(lo)
            if hi < INF:
                bset.add(hi)
        for t in bset:
            left, right, straddle = [], [], False
            for lf in leaves:
                lo, hi = lf["conds"].get(var, (-INF, INF))
                if hi <= t:
                    left.append(lf)
                elif lo >= t:
                    right.append(lf)
                else:
                    straddle = True
                    break
            if straddle or not left or not right:
                continue
            # explícitos = #leaves que tienen t como frontera real en esa var
            expl = sum(1 for lf in leaves
                       if t in lf["conds"].get(var, (-INF, INF)))
            balance = -abs(len(left) - len(right))
            key = (expl, balance)
            if best is None or key > best[0]:
                best = (key, var, t, left, right)
    return best  # None si no hay split consistente


def agg(leaves):
    n = sum(lf["n"] for lf in leaves)
    sc = sum(lf["score"] * lf["n"] for lf in leaves) / n if n else 0
    return n, sc


def nodo_html(leaves, variables, vmin, vmax, total, depth=0):
    n, sc = agg(leaves)
    chip = f'<span class="chip" style="background:{hexcol(goodness(sc, vmin, vmax))}">{sc:.0f}</span>'
    if len(leaves) == 1:
        lf = leaves[0]
        pct = lf["pct"] if lf["pct"] is not None else 100 * lf["n"] / total
        rule = esc(lf["regla"])
        return (f'<div class="leaf" data-rule="{rule}">'
                f'<span class="chip" style="background:{hexcol(goodness(lf["score"], vmin, vmax))}">{lf["score"]:.0f}</span>'
                f'<span class="meta">n={lf["n"]:,} · {pct:.1f}% · {esc(lf["quint"])}</span>'
                f'<div class="rule">➜ {rule}</div></div>')

    sp = mejor_split(leaves, variables)
    if sp is None:                       # sin split: lista plana
        body = "".join(nodo_html([lf], variables, vmin, vmax, total, depth + 1) for lf in leaves)
        cls = "node root" if depth == 0 else "node"
        op = " open" if depth == 0 else ""
        return (f'<details class="{cls}"{op}><summary><span class="tw">▸</span>{chip}'
                f'<span class="meta">n={n:,} · {len(leaves)} segmentos</span></summary>'
                f'<div class="kids">{body}</div></details>')

    _, var, t, left, right = sp
    cond_y = f'{esc(var)} ≤ {fmtnum(t)}'
    cond_n = f'{esc(var)} &gt; {fmtnum(t)}'
    izq = (f'<div class="branch"><div class="cond yes">{cond_y}</div>'
           f'{nodo_html(left, variables, vmin, vmax, total, depth + 1)}</div>')
    der = (f'<div class="branch"><div class="cond no">{cond_n}</div>'
           f'{nodo_html(right, variables, vmin, vmax, total, depth + 1)}</div>')
    cls = "node root" if depth == 0 else "node"
    op = " open" if depth == 0 else ""
    return (f'<details class="{cls}"{op}><summary><span class="tw">▸</span>{chip}'
            f'<span class="meta">n={n:,} · score {sc:.0f}</span></summary>'
            f'<div class="kids">{izq}{der}</div></details>')


def arbol_html(leaves, variables, vmin, vmax, total):
    sp = mejor_split(leaves, variables)
    if sp is None:
        return "".join(nodo_html([lf], variables, vmin, vmax, total, 0) for lf in leaves)
    # primer split: cada rama es un <details root>
    _, var, t, left, right = sp
    out = []
    for sub, op, lbl in [(left, "≤", f"{esc(var)} ≤ {fmtnum(t)}"),
                         (right, ">", f"{esc(var)} &gt; {fmtnum(t)}")]:
        n, sc = agg(sub)
        chip = f'<span class="chip" style="background:{hexcol(goodness(sc, vmin, vmax))}">{sc:.0f}</span>'
        body = (nodo_html(sub, variables, vmin, vmax, total, 1) if len(sub) > 1
                else nodo_html(sub, variables, vmin, vmax, total, 1))
        out.append(f'<details class="node root"{" open" if not out else ""}>'
                   f'<summary><span class="tw">▸</span><b style="font-size:15px">{lbl}</b> {chip}'
                   f'<span class="meta">n={n:,} · {sc:.0f}</span></summary>'
                   f'<div class="kids">{body}</div></details>')
    return "".join(out)


# ---------- 3) HTML ----------
CSS = """
 *{box-sizing:border-box;margin:0;padding:0;font-family:"Segoe UI",Roboto,Arial,sans-serif}
 body{background:#f4f7f6;color:#10241f}
 header{background:linear-gradient(90deg,#007a72,#00a499);color:#fff;padding:16px 28px}
 header h1{font-size:21px} header .s{opacity:.9;font-size:13.5px;margin-top:3px}
 .selwrap{margin-top:12px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
 .selwrap select{padding:9px 14px;border-radius:10px;border:none;font-size:15px;font-weight:600;color:#007a72;min-width:340px}
 .tabs{display:flex;gap:8px;padding:14px 4vw 0}
 .tabs button{background:#dfeeeb;color:#23433c;border:1px solid #cfe1dc;border-radius:18px;padding:8px 18px;cursor:pointer;font-size:14px}
 .tabs button.on{background:#007a72;color:#fff;font-weight:700}
 .scn{display:none} .scn.on{display:block}
 .view{display:none;padding:16px 4vw 70px} .view.on{display:block}
 .bar{display:flex;align-items:center;gap:12px;margin-bottom:12px;flex-wrap:wrap}
 .legend{display:flex;align-items:center;gap:8px;font-size:13px;color:#33514a}
 .grad{width:150px;height:12px;border-radius:6px;background:linear-gradient(90deg,#1a9850,#ffffbf,#d73027)}
 input.f{border:1px solid #cfdcd8;border-radius:18px;padding:8px 14px;font-size:13px;min-width:200px;margin-left:auto}
 table{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;font-size:13.5px}
 th{background:#007a72;color:#fff;text-align:left;padding:10px}
 td{padding:7px 10px;border-bottom:1px solid #f0f4f3;vertical-align:top}
 td.r{color:#9fb0ab;font-weight:700;width:34px} td.num{text-align:right;white-space:nowrap}
 .chip{color:#10241f;font-weight:800;border-radius:7px;padding:3px 9px;font-size:13px;display:inline-block;min-width:42px;text-align:center}
 .q{background:#eef3f1;border-radius:10px;padding:2px 9px;font-size:12px;font-weight:700;color:#33514a}
 .rg{font-family:Consolas,monospace;font-size:12px;color:#33514a;line-height:1.5}
 tr.hide{display:none}
 .opt{background:#fff;border-radius:14px;padding:20px 24px;margin-bottom:22px;box-shadow:0 4px 14px #0000000f}
 .opt h2{color:#007a72;font-size:19px;margin-bottom:4px} .opt .h{color:#5b6f6a;font-size:13.5px;margin-bottom:16px}
 .slider{display:flex;align-items:center;gap:12px;margin-bottom:18px;flex-wrap:wrap}
 .slider input[type=range]{flex:1;min-width:200px}
 .kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:18px}
 .kc{border-radius:12px;padding:14px 16px;border:1px solid #e6efec}
 .kc.base{background:#eef7f5;border-color:#bfe0da}
 .kc .t{font-size:13px;color:#5b6f6a;margin-bottom:6px} .kc .v{font-size:26px;font-weight:800;color:#23433c}
 .kc .d{font-size:13px;margin-top:4px;font-weight:600} .up{color:#1a9850} .dn{color:#d73027}
 svg{width:100%;height:300px;background:#fbfdfc;border-radius:10px;border:1px solid #eef2f1}
 details.node{margin:4px 0} details.root{margin:8px 0}
 details.root>summary{background:#eef7f5;border-color:#bfe0da}
 .kids{margin-left:24px;border-left:2px dashed #b9ccc7;padding-left:16px}
 summary{list-style:none;cursor:pointer;display:inline-flex;align-items:center;gap:9px;background:#fff;border:1px solid #e0e9e6;border-radius:10px;padding:6px 11px;box-shadow:0 2px 6px #0000000d}
 summary::-webkit-details-marker{display:none}
 .tw{color:#00a499;font-weight:700;transition:.2s} details[open]>summary .tw{transform:rotate(90deg)}
 .branch{margin-top:7px}
 .cond{display:inline-block;font-family:Consolas,monospace;font-size:12px;font-weight:600;padding:3px 10px;border-radius:13px;margin-bottom:3px}
 .cond.yes{background:#e3f4ec;color:#1a7a4a} .cond.no{background:#fdecea;color:#b23b30}
 .meta{font-size:12.5px;color:#5b6f6a}
 .leaf{display:flex;align-items:center;gap:9px;background:#fff;border:1px solid #e6efec;border-radius:10px;padding:6px 11px;margin:5px 0;flex-wrap:wrap}
 .leaf .rule{flex-basis:100%;font-family:Consolas,monospace;font-size:11.5px;color:#1a7a4a;display:none}
 .leaf:hover .rule{display:block} .leaf:hover{box-shadow:0 4px 12px #00a49955;border-color:#00a499}
 .hl{outline:3px solid #f1c40f}
"""


def tabla_segmentos(leaves, total, vmin, vmax):
    # ordena de menor a mayor riesgo
    orden = sorted(leaves, key=lambda lf: lf["score"], reverse=_SCORE)
    filas = []
    for i, lf in enumerate(orden, 1):
        pct = lf["pct"] if lf["pct"] is not None else 100 * lf["n"] / total
        col = hexcol(goodness(lf["score"], vmin, vmax))
        filas.append(
            f'<tr style="border-left:8px solid {col}"><td class="r">{i}</td>'
            f'<td><span class="chip" style="background:{col}">{lf["score"]:.0f}</span></td>'
            f'<td><span class="q">{esc(lf["quint"])}</span></td>'
            f'<td class="num">{lf["n"]:,}</td><td class="num">{pct:.1f}%</td>'
            f'<td class="rg">{esc(lf["regla"])}</td></tr>')
    val = "score" if _SCORE else "RD"
    return (f'<table><thead><tr><th>#</th><th>{val}</th><th>Q</th><th>n</th><th>%</th>'
            f'<th>Regla del segmento</th></tr></thead><tbody>{"".join(filas)}</tbody></table>')


def kpis_quintil(leaves, total):
    by = {}
    for lf in leaves:
        by[lf["quint"]] = by.get(lf["quint"], 0) + lf["n"]
    barras = []
    for q in ["G1", "G2", "G3", "G4", "G5"]:
        if by.get(q):
            w = 100 * by[q] / total
            lbl = f"{q} {w:.0f}%" if w >= 4 else ""
            barras.append(f'<div title="{q}: {by[q]:,} ({w:.1f}%)" style="width:{w}%;'
                          f'background:{QCOLOR[q]};color:#1a3a16;font-size:11px;font-weight:700;'
                          f'display:flex;align-items:center;justify-content:center;overflow:hidden">{lbl}</div>')
    return "".join(barras)


def main():
    try:
        hojas = pd.read_excel(EXCEL_IN, sheet_name=None, header=None)
    except Exception as e:
        print(f"ERROR leyendo {EXCEL_IN}: {e}")
        sys.exit(1)

    escenarios = []
    for nombre, df in hojas.items():
        if nombre.strip().lower() in SKIP:
            continue
        leaves = leer_hoja(df)
        if not leaves:
            print(f"  [skip] '{nombre}': no se encontró el cuadro del árbol")
            continue
        total = sum(lf["n"] for lf in leaves)
        scores = [lf["score"] for lf in leaves]
        vmin, vmax = min(scores), max(scores)
        variables = []
        for lf in leaves:
            for v in lf["conds"]:
                if v not in variables:
                    variables.append(v)
        escenarios.append(dict(nombre=nombre, leaves=leaves, total=total,
                               vmin=vmin, vmax=vmax, variables=variables))
        print(f"  [ok] '{nombre}': {len(leaves)} segmentos · {total:,} clientes")

    if not escenarios:
        print("No se encontró ningún escenario válido. Revisa el Excel.")
        sys.exit(1)

    # ----- comparación -----
    val_lbl = "Score" if _SCORE else "RD"
    op_lbl = "≥" if _SCORE else "≤"
    filas_cmp, bloques_q, SCN_js = [], [], []
    for e in escenarios:
        lv, tot = e["leaves"], e["total"]
        scmed = sum(lf["score"] * lf["n"] for lf in lv) / tot
        lead_n = sum(lf["n"] for lf in lv if passes(lf["score"]))
        lead_sw = sum(lf["score"] * lf["n"] for lf in lv if passes(lf["score"]))
        lead_avg = lead_sw / lead_n if lead_n else 0
        g5 = sum(lf["n"] for lf in lv if lf["quint"] == "G5")
        filas_cmp.append(
            f"<tr><td><b>{esc(e['nombre'])}</b></td><td class='num'>{tot:,}</td>"
            f"<td class='num'>{len(lv)}</td><td class='num'>{scmed:.0f}</td>"
            f"<td class='num'>{lead_n:,}</td><td class='num'>{100*lead_n/tot:.1f}%</td>"
            f"<td class='num'>{lead_avg:.0f}</td><td class='num'>{100*g5/tot:.1f}%</td></tr>")
        bloques_q.append(
            f'<div style="margin:10px 0"><div style="font-size:13.5px;margin-bottom:4px">'
            f'<b>{esc(e["nombre"])}</b> <span style="color:#5b6f6a">· {val_lbl.lower()} medio '
            f'{scmed:.0f} · {tot:,} clientes</span></div>'
            f'<div style="display:flex;height:26px;border-radius:6px;overflow:hidden;border:1px solid #e6efec">'
            f'{kpis_quintil(lv, tot)}</div></div>')
        seg = ",".join(f"[{lf['score']:.2f},{lf['n']}]" for lf in lv)
        SCN_js.append(f"{{seg:[{seg}],total:{tot}}}")

    cmp_html = (
        '<div class="scn on" id="scncmp"><div style="padding:20px 4vw 60px">'
        '<h2 style="color:#007a72;font-size:22px;margin-bottom:14px">Resumen y comparación de escenarios</h2>'
        '<table style="margin-bottom:26px"><thead><tr><th>Escenario</th><th>Clientes</th><th>Segmentos</th>'
        f'<th>{val_lbl} medio</th><th>Leads ({op_lbl}{fmtnum(APETITO)})</th><th>% leads</th>'
        f'<th>{val_lbl} prom. leads</th><th>% en G5 (alto riesgo)</th></tr></thead><tbody>'
        + "".join(filas_cmp) +
        '</tbody></table>'
        '<h3 style="color:#23433c;font-size:17px;margin-bottom:6px">Distribución por quintil de riesgo</h3>'
        '<div style="font-size:12.5px;color:#5b6f6a;margin-bottom:6px"><span style="color:#1a9850">■</span> '
        'G1 menor riesgo … <span style="color:#d73027">■</span> G5 mayor riesgo</div>'
        + "".join(bloques_q) + '</div></div>')

    # ----- opciones del selector -----
    opts = ['<option value="scncmp">Resumen / Comparación</option>']
    for k, e in enumerate(escenarios):
        opts.append(f'<option value="scn{k}">{esc(e["nombre"])}  ·  {e["total"]:,} clientes · '
                    f'{len(e["leaves"])} segmentos</option>')

    # ----- bloque por escenario -----
    bloques = []
    for k, e in enumerate(escenarios):
        lv, tot, vmin, vmax = e["leaves"], e["total"], e["vmin"], e["vmax"]
        thr_def = APETITO
        seg_tab = tabla_segmentos(lv, tot, vmin, vmax)
        tree = arbol_html(lv, e["variables"], vmin, vmax, tot)
        bloques.append(f'''<div class="scn" id="scn{k}">
  <div class="tabs">
    <button class="on" onclick="tab({k},0,this)">Segmentos + Optimizador</button>
    <button onclick="tab({k},1,this)">Árbol (ramificación)</button>
  </div>
  <section class="view on" id="v0{k}">
    <div class="opt">
      <h2>Optimizador de apetito — {esc(e["nombre"])}</h2>
      <div class="h">Un segmento entra si su {val_lbl.lower()} {op_lbl} apetito.</div>
      <div class="slider"><span>apetito {op_lbl}</span>
        <input type="range" id="thr{k}" min="{vmin:.0f}" max="{vmax:.0f}" step="1" value="{thr_def:g}"
               oninput="document.getElementById('thrn{k}').value=this.value;upd({k})">
        <input type="number" id="thrn{k}" value="{thr_def:g}" style="width:90px;font-size:20px;font-weight:800;color:#007a72;border:2px solid #bfe0da;border-radius:8px;padding:4px 8px;text-align:center"
               oninput="document.getElementById('thr{k}').value=this.value;upd({k})">
        <span style="margin-left:18px">± </span>
        <input type="number" id="pct{k}" value="5" min="0" step="0.5" style="width:64px;font-size:18px;font-weight:700;border:2px solid #cfdcd8;border-radius:8px;padding:4px 6px;text-align:center" oninput="upd({k})"><span>%</span>
      </div>
      <div class="kpis">
        <div class="kc base"><div class="t">Apetito actual</div><div class="v" id="k0n{k}">–</div><div class="d" id="k0s{k}"></div></div>
        <div class="kc"><div class="t" id="kmt{k}">±</div><div class="v" id="kmn{k}">–</div><div class="d" id="kms{k}"></div></div>
        <div class="kc"><div class="t" id="kpt{k}">±</div><div class="v" id="kpn{k}">–</div><div class="d" id="kps{k}"></div></div>
      </div>
      <svg id="chart{k}" viewBox="0 0 1000 300" preserveAspectRatio="none"></svg>
    </div>
    <div class="bar"><span class="legend">menor riesgo <span class="grad"></span> mayor riesgo</span>
      <input class="f" placeholder="filtrar…" oninput="filt({k},this.value)"></div>
    {seg_tab}
  </section>
  <section class="view" id="v1{k}">
    <div class="bar"><span class="legend">árbol reconstruido desde las reglas</span>
      <button onclick="setAll({k},true)" style="border:1px solid #cfdcd8;background:#fff;border-radius:18px;padding:8px 14px;cursor:pointer">Expandir todo</button>
      <button onclick="setAll({k},false)" style="border:1px solid #cfdcd8;background:#fff;border-radius:18px;padding:8px 14px;cursor:pointer">Colapsar todo</button>
      <input class="f" placeholder="resaltar variable…" oninput="hlt({k},this.value)"></div>
    <div id="tree{k}">{tree}</div>
  </section>
</div>''')

    js = '''
 const OBJ="%OBJ%";
 const SCN=[%SCN%];
 const smin=k=>Math.min(...SCN[k].seg.map(s=>s[0])), smax=k=>Math.max(...SCN[k].seg.map(s=>s[0]));
 function pass(s,thr){return OBJ==="SCORE"? s>=thr : s<=thr;}
 function pool(k,thr){let n=0,sw=0;for(const[s,c]of SCN[k].seg)if(pass(s,thr)){n+=c;sw+=s*c;}return{n:n,pct:100*n/SCN[k].total,avg:n?sw/n:0};}
 function fmtN(x){return Math.round(x).toLocaleString('es-PE');}
 function showScn(id){document.querySelectorAll('.scn').forEach(d=>d.classList.toggle('on',d.id===id));}
 function tab(k,i,b){const blk=document.getElementById('scn'+k);
   blk.querySelectorAll('.view').forEach((v,j)=>v.classList.toggle('on',j===i));
   blk.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on'));b.classList.add('on');}
 function filt(k,t){t=t.trim().toLowerCase();
   document.querySelectorAll('#v0'+k+' tbody tr').forEach(tr=>tr.classList.toggle('hide',t&&!tr.textContent.toLowerCase().includes(t)));}
 function setAll(k,o){document.querySelectorAll('#tree'+k+' details').forEach(d=>d.open=o);}
 function hlt(k,t){t=t.trim().toLowerCase();
   document.querySelectorAll('#tree'+k+' .leaf').forEach(l=>l.classList.toggle('hl',t&&(l.dataset.rule||'').toLowerCase().includes(t)));
   if(t)setAll(k,true);}
 function chart(k,thr){
   const A=smin(k),Z=smax(k),T=SCN[k].total,L=60,R=950,Tp=20,B=260;
   const xs=s=>L+(s-A)/(Z-A)*(R-L), ys=n=>B-(n/T)*(B-Tp);
   let pts=[],step=(Z-A)/120;
   for(let s=A;s<=Z+1e-6;s+=step) pts.push([xs(s),ys(pool(k,s).n)]);
   const poly=pts.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ');
   const area=xs(A).toFixed(1)+',260 '+poly+' '+xs(Z).toFixed(1)+',260';
   const mx=xs(thr); let g='';
   for(let i=0;i<=4;i++){const v=T*i/4,y=ys(v);
     g+=`<line x1="60" y1="${y}" x2="950" y2="${y}" stroke="#eef2f1"/><text x="54" y="${y+4}" text-anchor="end" font-size="11" fill="#9fb0ab">${(v/1e6).toFixed(2)}M</text>`;}
   for(let i=0;i<=4;i++){const v=A+(Z-A)*i/4,x=xs(v);
     g+=`<text x="${x}" y="278" text-anchor="middle" font-size="11" fill="#9fb0ab">${Math.round(v)}</text>`;}
   document.getElementById('chart'+k).innerHTML=g+
     `<polygon points="${area}" fill="#00a49922"/><polyline points="${poly}" fill="none" stroke="#007a72" stroke-width="2.5"/>`+
     `<line x1="${mx}" y1="20" x2="${mx}" y2="260" stroke="#d73027" stroke-width="2" stroke-dasharray="5,4"/>`+
     `<circle cx="${mx}" cy="${ys(pool(k,thr).n)}" r="5" fill="#d73027"/>`+
     `<text x="500" y="296" text-anchor="middle" font-size="12" fill="#5b6f6a">apetito →</text>`;
 }
 function upd(k){
   const thr=+document.getElementById('thrn'+k).value||0, p=(+document.getElementById('pct'+k).value||0)/100;
   const tlo=thr*(1-p), thi=thr*(1+p), b=pool(k,thr), lo=pool(k,tlo), hi=pool(k,thi);
   document.getElementById('k0n'+k).textContent=fmtN(b.n)+' leads';
   document.getElementById('k0s'+k).textContent=b.pct.toFixed(1)+'% base · prom '+b.avg.toFixed(0);
   const dlo=lo.n-b.n, dhi=hi.n-b.n, pp=(p*100).toFixed(1);
   document.getElementById('kmt'+k).textContent=`Si bajo −${pp}% (${tlo.toFixed(0)})`;
   document.getElementById('kpt'+k).textContent=`Si subo +${pp}% (${thi.toFixed(0)})`;
   document.getElementById('kmn'+k).textContent=fmtN(lo.n)+' leads';
   document.getElementById('kms'+k).innerHTML=`<span class="${dlo>=0?'up':'dn'}">${dlo>=0?'+':''}${fmtN(dlo)} leads</span> · prom ${lo.avg.toFixed(0)}`;
   document.getElementById('kpn'+k).textContent=fmtN(hi.n)+' leads';
   document.getElementById('kps'+k).innerHTML=`<span class="${dhi>=0?'up':'dn'}">${dhi>=0?'+':''}${fmtN(dhi)} leads</span> · prom ${hi.avg.toFixed(0)}`;
   chart(k,thr);
 }
 SCN.forEach((_,k)=>upd(k)); showScn('scncmp');
'''
    js = js.replace("%OBJ%", "SCORE" if _SCORE else "RD").replace("%SCN%", ",".join(SCN_js))

    doc = (f'<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">'
           f'<meta name="viewport" content="width=device-width, initial-scale=1.0">'
           f'<title>{esc(TITULO)}</title><style>{CSS}</style></head><body>'
           f'<header><h1>{esc(TITULO)}</h1>'
           f'<div class="s">Selecciona el escenario y explora segmentos, optimizador de apetito y el árbol.</div>'
           f'<div class="selwrap"><span>Vista:</span><select onchange="showScn(this.value)">'
           f'{"".join(opts)}</select></div></header>'
           f'{cmp_html}{"".join(bloques)}'
           f'<script>{js}</script></body></html>')

    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"\nOK -> {HTML_OUT}  ({len(escenarios)} escenarios)")


if __name__ == "__main__":
    main()
