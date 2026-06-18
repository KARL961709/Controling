# -*- coding: utf-8 -*-
"""HTML 2 pestañas: (1) segmentos desagrupados por riesgo; (2) árbol cat_score -> demás variables."""
from build_arbol_html import leaves, TOTAL, color, DISP, CALNUM, INF

def regla(l, sin_cat=False):
    return " · ".join(f"{DISP.get(v,v)} {s}" if v != "puntuacion_cal_cat" else f"cat_score {s}"
                      for v, s in l["conds"].items() if not (sin_cat and v == "puntuacion_cal_cat")) or "(todos)"

def fmt(t): return f"{int(t):,}" if float(t).is_integer() else f"{t:g}"
def blab(var, t, side):
    name = DISP.get(var, var)
    return f"{name} ≤ {fmt(t)}" if side == "L" else f"{name} > {fmt(t)}"

def best_split(ls, exclude):
    vars_all = set().union(*[set(l["iv"]) for l in ls]) - exclude
    cands = []
    for var in vars_all:
        act = sum(1 for l in ls if var in l["iv"])
        bounds = set()
        for l in ls:
            lo, hi = l["iv"].get(var, (-INF, INF))
            if lo > -INF: bounds.add(lo)
            if hi < INF: bounds.add(hi)
        for t in bounds:
            left = [l for l in ls if l["iv"].get(var, (-INF, INF))[1] <= t]
            right = [l for l in ls if l["iv"].get(var, (-INF, INF))[0] >= t]
            if left and right and len(left) + len(right) == len(ls):
                nl = sum(l["n"] for l in left); nr = sum(l["n"] for l in right)
                cands.append((act, -abs(nl - nr), var, t, left, right))
    if not cands: return None
    cands.sort(reverse=True)
    _, _, var, t, left, right = cands[0]
    return var, t, left, right

def sub(ls):
    n = sum(l["n"] for l in ls); sc = sum(l["sc"] * l["n"] for l in ls) / n
    if len(ls) == 1:
        l = ls[0]; rg = regla(l, sin_cat=True)
        return (f'<div class="leaf" data-rule="{rg}"><span class="chip" style="background:{color(l["sc"])}">{l["sc"]:.0f}</span>'
                f'<span class="meta">n={l["n"]:,} · {100*l["n"]/TOTAL:.1f}% · {l["q"]}</span>'
                f'<div class="rule">{rg}</div></div>')
    sp = best_split(ls, {"puntuacion_cal_cat"})
    if sp is None: return "".join(sub([l]) for l in ls)
    var, t, lft, rgt = sp
    chip = f'<span class="chip" style="background:{color(sc)}">{sc:.0f}</span>'
    head = f'<summary><span class="tw">▸</span>{chip}<span class="meta">n={n:,} · score {sc:.0f}</span></summary>'
    kids = (f'<div class="branch"><div class="cond yes">{blab(var,t,"L")}</div>{sub(lft)}</div>'
            f'<div class="branch"><div class="cond no">{blab(var,t,"R")}</div>{sub(rgt)}</div>')
    return f'<details class="node">{head}<div class="kids">{kids}</div></details>'

# --- raíz: cat_score 1..6 (mejor a peor) ---
grp = {}
for l in leaves:
    grp.setdefault(CALNUM[l["conds"]["puntuacion_cal_cat"]], []).append(l)
orden = sorted(grp, key=lambda k: -sum(x["sc"]*x["n"] for x in grp[k]) / sum(x["n"] for x in grp[k]))
TREE = ""
for k in orden:
    g = grp[k]; n = sum(x["n"] for x in g); sc = sum(x["sc"]*x["n"] for x in g)/n
    chip = f'<span class="chip" style="background:{color(sc)}">{sc:.0f}</span>'
    op = "open" if k == orden[0] else ""
    TREE += (f'<details class="node root" {op}><summary><span class="tw">▸</span>'
             f'<b style="font-size:15px">cat_score = {k}</b> {chip}'
             f'<span class="meta">n={n:,} · {100*n/TOTAL:.1f}% · score medio {sc:.0f}</span></summary>'
             f'<div class="kids">{sub(g)}</div></details>')

# --- pestaña 1: 74 segmentos, menor a mayor riesgo ---
rows = ""
for i, l in enumerate(sorted(leaves, key=lambda x: -x["sc"]), 1):
    c = color(l["sc"])
    rows += (f'<tr style="border-left:8px solid {c}"><td class="r">{i}</td>'
             f'<td><span class="chip" style="background:{c}">{l["sc"]:.0f}</span></td>'
             f'<td><span class="q">{l["q"]}</span></td><td class="num">{l["n"]:,}</td>'
             f'<td class="num">{100*l["n"]/TOTAL:.1f}%</td><td class="rg">{regla(l)}</td></tr>')

HTML = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Segmentación de riesgo — Escenario Global</title>
<style>
 *{{box-sizing:border-box;margin:0;padding:0;font-family:"Segoe UI",Roboto,Arial,sans-serif}}
 body{{background:#f4f7f6;color:#10241f}}
 header{{background:linear-gradient(90deg,#007a72,#00a499);color:#fff;padding:16px 28px}}
 header h1{{font-size:21px}} header .s{{opacity:.9;font-size:13.5px;margin-top:3px}}
 .tabs{{display:flex;gap:8px;margin-top:12px}}
 .tabs button{{background:#ffffff22;color:#fff;border:1px solid #ffffff66;border-radius:18px;padding:8px 18px;cursor:pointer;font-size:14px}}
 .tabs button.on{{background:#fff;color:#007a72;font-weight:700}}
 .view{{display:none;padding:20px 4vw 70px}} .view.on{{display:block}}
 .bar{{display:flex;align-items:center;gap:12px;margin-bottom:12px;flex-wrap:wrap}}
 .legend{{display:flex;align-items:center;gap:8px;font-size:13px;color:#33514a}}
 .grad{{width:150px;height:12px;border-radius:6px;background:linear-gradient(90deg,#1a9850,#ffffbf,#d73027)}}
 input.f{{border:1px solid #cfdcd8;border-radius:18px;padding:8px 14px;font-size:13px;min-width:220px;margin-left:auto}}
 table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;font-size:13.5px}}
 th{{background:#007a72;color:#fff;text-align:left;padding:10px}}
 td{{padding:7px 10px;border-bottom:1px solid #f0f4f3;vertical-align:top}}
 td.r{{color:#9fb0ab;font-weight:700;width:34px}} td.num{{text-align:right;white-space:nowrap}}
 .chip{{color:#10241f;font-weight:800;border-radius:7px;padding:3px 9px;font-size:13px;display:inline-block;min-width:42px;text-align:center}}
 .q{{background:#eef3f1;border-radius:10px;padding:2px 9px;font-size:12px;font-weight:700;color:#33514a}}
 .rg{{font-family:Consolas,monospace;font-size:12px;color:#33514a;line-height:1.5}}
 tr.hide{{display:none}}
 details.node{{margin:4px 0}} details.root{{margin:8px 0}}
 details.root>summary{{background:#eef7f5;border-color:#bfe0da}}
 .kids{{margin-left:24px;border-left:2px dashed #b9ccc7;padding-left:16px}}
 summary{{list-style:none;cursor:pointer;display:inline-flex;align-items:center;gap:9px;background:#fff;
   border:1px solid #e0e9e6;border-radius:10px;padding:6px 11px;box-shadow:0 2px 6px #0000000d}}
 summary::-webkit-details-marker{{display:none}}
 .tw{{color:#00a499;font-weight:700;transition:.2s}} details[open]>summary .tw{{transform:rotate(90deg)}}
 .branch{{margin-top:7px}}
 .cond{{display:inline-block;font-family:Consolas,monospace;font-size:12px;font-weight:600;padding:3px 10px;border-radius:13px;margin-bottom:3px}}
 .cond.yes{{background:#e3f4ec;color:#1a7a4a}} .cond.no{{background:#fdecea;color:#b23b30}}
 .meta{{font-size:12.5px;color:#5b6f6a}}
 .leaf{{display:flex;align-items:center;gap:9px;background:#fff;border:1px solid #e6efec;border-radius:10px;padding:6px 11px;margin:5px 0;flex-wrap:wrap}}
 .leaf .rule{{flex-basis:100%;font-family:Consolas,monospace;font-size:11.5px;color:#46615b;display:none}}
 .leaf:hover .rule{{display:block}} .leaf:hover{{box-shadow:0 4px 12px #00a49955;border-color:#00a499}}
 .hl{{outline:3px solid #f1c40f}}
</style></head><body>
<header>
  <h1>🌳 Segmentación de riesgo — Escenario Global</h1>
  <div class="s">2.28 M clientes · 74 segmentos · objetivo = score · de menor a mayor riesgo</div>
  <div class="tabs">
    <button class="on" onclick="tab(0,this)">📋 Segmentos (lista)</button>
    <button onclick="tab(1,this)">🌳 Árbol (ramificación)</button>
  </div>
</header>

<section class="view on" id="v0">
  <div class="bar"><span class="legend">menor riesgo <span class="grad"></span> mayor riesgo</span>
    <input class="f" placeholder="filtrar… (ej. edad, mora)" oninput="filt('#v0 tbody tr',this.value)"></div>
  <table><thead><tr><th>#</th><th>score</th><th>Q</th><th>n</th><th>%</th><th>Regla del segmento</th></tr></thead>
  <tbody>{rows}</tbody></table>
</section>

<section class="view" id="v1">
  <div class="bar">
    <span class="legend">la raíz es <b>cat_score</b>; dentro de cada categoría se ramifican las demás variables</span>
    <button onclick="setAll(true)" style="border:1px solid #cfdcd8;background:#fff;border-radius:18px;padding:8px 14px;cursor:pointer">Expandir todo</button>
    <button onclick="setAll(false)" style="border:1px solid #cfdcd8;background:#fff;border-radius:18px;padding:8px 14px;cursor:pointer">Colapsar todo</button>
    <input class="f" placeholder="resaltar variable…" oninput="hlt(this.value)"></div>
  <div id="tree">{TREE}</div>
</section>

<script>
 function tab(i,b){{document.querySelectorAll('.view').forEach((v,k)=>v.classList.toggle('on',k===i));
   document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on'));b.classList.add('on');}}
 function filt(sel,t){{t=t.trim().toLowerCase();
   document.querySelectorAll(sel).forEach(tr=>tr.classList.toggle('hide',t&&!tr.textContent.toLowerCase().includes(t)));}}
 function setAll(o){{document.querySelectorAll('#tree details').forEach(d=>d.open=o);}}
 function hlt(t){{t=t.trim().toLowerCase();
   document.querySelectorAll('#tree .leaf').forEach(l=>l.classList.toggle('hl',t&&(l.dataset.rule||'').toLowerCase().includes(t)));
   if(t)setAll(true);}}
</script>
</body></html>"""

with open("segmentacion_riesgo_global.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print("OK -> categorias:", orden)
