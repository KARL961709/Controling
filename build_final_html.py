# -*- coding: utf-8 -*-
"""HTML 2 pestañas: (1) segmentos + curva de optimización interactiva; (2) árbol con reglas reales."""
from build_arbol_html import leaves, TOTAL, color, DISP, INF

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
        act = sum(1 for l in ls if var in l["iv"]); bounds = set()
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
    cands.sort(reverse=True); _, _, var, t, left, right = cands[0]
    return var, t, left, right

def sub(ls):
    n = sum(l["n"] for l in ls); sc = sum(l["sc"] * l["n"] for l in ls) / n
    if len(ls) == 1:
        l = ls[0]; rg = regla(l, sin_cat=True)
        return (f'<div class="leaf" data-rule="{rg}"><span class="chip" style="background:{color(l["sc"])}">{l["sc"]:.0f}</span>'
                f'<span class="meta">n={l["n"]:,} · {100*l["n"]/TOTAL:.1f}% · {l["q"]}</span>'
                f'<div class="rule">➜ {rg}</div></div>')
    sp = best_split(ls, {"puntuacion_cal_cat"})
    if sp is None: return "".join(sub([l]) for l in ls)
    var, t, lft, rgt = sp
    chip = f'<span class="chip" style="background:{color(sc)}">{sc:.0f}</span>'
    head = f'<summary><span class="tw">▸</span>{chip}<span class="meta">n={n:,} · score {sc:.0f}</span></summary>'
    kids = (f'<div class="branch"><div class="cond yes">{blab(var,t,"L")}</div>{sub(lft)}</div>'
            f'<div class="branch"><div class="cond no">{blab(var,t,"R")}</div>{sub(rgt)}</div>')
    return f'<details class="node">{head}<div class="kids">{kids}</div></details>'

# raíz: agrupada por la REGLA REAL de cat_score
grp = {}
for l in leaves:
    grp.setdefault(l["conds"]["puntuacion_cal_cat"], []).append(l)
def cl(lbl): return lbl.replace("<= ", "≤ ")
orden = sorted(grp, key=lambda k: -sum(x["sc"]*x["n"] for x in grp[k]) / sum(x["n"] for x in grp[k]))
TREE = ""
for k in orden:
    g = grp[k]; n = sum(x["n"] for x in g); sc = sum(x["sc"]*x["n"] for x in g)/n
    chip = f'<span class="chip" style="background:{color(sc)}">{sc:.0f}</span>'
    op = "open" if k == orden[0] else ""
    TREE += (f'<details class="node root" {op}><summary><span class="tw">▸</span>'
             f'<b style="font-size:15px">cat_score {cl(k)}</b> {chip}'
             f'<span class="meta">n={n:,} · {100*n/TOTAL:.1f}% · score medio {sc:.0f}</span></summary>'
             f'<div class="kids">{sub(g)}</div></details>')

# pestaña 1: 74 segmentos
rows = ""
for i, l in enumerate(sorted(leaves, key=lambda x: -x["sc"]), 1):
    c = color(l["sc"])
    rows += (f'<tr style="border-left:8px solid {c}"><td class="r">{i}</td>'
             f'<td><span class="chip" style="background:{c}">{l["sc"]:.0f}</span></td>'
             f'<td><span class="q">{l["q"]}</span></td><td class="num">{l["n"]:,}</td>'
             f'<td class="num">{100*l["n"]/TOTAL:.1f}%</td><td class="rg">{regla(l)}</td></tr>')

SEG = "[" + ",".join(f"[{l['sc']:.2f},{l['n']}]" for l in leaves) + "]"

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
 input.f{{border:1px solid #cfdcd8;border-radius:18px;padding:8px 14px;font-size:13px;min-width:200px;margin-left:auto}}
 table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;font-size:13.5px}}
 th{{background:#007a72;color:#fff;text-align:left;padding:10px}}
 td{{padding:7px 10px;border-bottom:1px solid #f0f4f3;vertical-align:top}}
 td.r{{color:#9fb0ab;font-weight:700;width:34px}} td.num{{text-align:right;white-space:nowrap}}
 .chip{{color:#10241f;font-weight:800;border-radius:7px;padding:3px 9px;font-size:13px;display:inline-block;min-width:42px;text-align:center}}
 .q{{background:#eef3f1;border-radius:10px;padding:2px 9px;font-size:12px;font-weight:700;color:#33514a}}
 .rg{{font-family:Consolas,monospace;font-size:12px;color:#33514a;line-height:1.5}}
 tr.hide{{display:none}}
 /* optimizador */
 .opt{{background:#fff;border-radius:14px;padding:20px 24px;margin-bottom:22px;box-shadow:0 4px 14px #0000000f}}
 .opt h2{{color:#007a72;font-size:19px;margin-bottom:4px}} .opt .h{{color:#5b6f6a;font-size:13.5px;margin-bottom:16px}}
 .slider{{display:flex;align-items:center;gap:14px;margin-bottom:18px}}
 .slider input{{flex:1}} .slider b{{font-size:24px;color:#007a72;min-width:120px}}
 .kpis{{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:18px}}
 .kc{{border-radius:12px;padding:14px 16px;border:1px solid #e6efec}}
 .kc.base{{background:#eef7f5;border-color:#bfe0da}}
 .kc .t{{font-size:13px;color:#5b6f6a;margin-bottom:6px}} .kc .v{{font-size:26px;font-weight:800;color:#23433c}}
 .kc .d{{font-size:13px;margin-top:4px;font-weight:600}} .up{{color:#1a9850}} .dn{{color:#d73027}}
 svg{{width:100%;height:300px;background:#fbfdfc;border-radius:10px;border:1px solid #eef2f1}}
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
 .leaf .rule{{flex-basis:100%;font-family:Consolas,monospace;font-size:11.5px;color:#1a7a4a;display:none}}
 .leaf:hover .rule{{display:block}} .leaf:hover{{box-shadow:0 4px 12px #00a49955;border-color:#00a499}}
 .hl{{outline:3px solid #f1c40f}}
</style></head><body>
<header>
  <h1>🌳 Segmentación de riesgo — Escenario Global</h1>
  <div class="s">2.28 M clientes · 74 segmentos · objetivo = score · de menor a mayor riesgo</div>
  <div class="tabs">
    <button class="on" onclick="tab(0,this)">📋 Segmentos + Optimizador</button>
    <button onclick="tab(1,this)">🌳 Árbol (ramificación)</button>
  </div>
</header>

<section class="view on" id="v0">
  <div class="opt">
    <h2>🎯 Optimizador de apetito</h2>
    <div class="h">Mueve el apetito (score mínimo). Un segmento entra si su score promedio ≥ apetito. Score promedio = proxy de riesgo (mayor = menos riesgo).</div>
    <div class="slider">
      <span>apetito ≥</span>
      <input type="range" id="thr" min="584" max="978" step="1" value="730"
             oninput="document.getElementById('thrn').value=this.value;upd()">
      <input type="number" id="thrn" value="730" style="width:90px;font-size:20px;font-weight:800;color:#007a72;border:2px solid #bfe0da;border-radius:8px;padding:4px 8px;text-align:center"
             oninput="document.getElementById('thr').value=this.value;upd()">
      <span style="margin-left:18px">± </span>
      <input type="number" id="pct" value="5" min="0" step="0.5" style="width:64px;font-size:18px;font-weight:700;border:2px solid #cfdcd8;border-radius:8px;padding:4px 6px;text-align:center" oninput="upd()">
      <span>%</span>
    </div>
    <div class="kpis">
      <div class="kc base"><div class="t">Apetito actual</div><div class="v" id="k0n">–</div><div class="d" id="k0s"></div></div>
      <div class="kc"><div class="t" id="kmt">Si bajo el apetito −5%</div><div class="v" id="kmn">–</div><div class="d" id="kms"></div></div>
      <div class="kc"><div class="t" id="kpt">Si subo el apetito +5%</div><div class="v" id="kpn">–</div><div class="d" id="kps"></div></div>
    </div>
    <svg id="chart" viewBox="0 0 1000 300" preserveAspectRatio="none"></svg>
  </div>
  <div class="bar"><span class="legend">menor riesgo <span class="grad"></span> mayor riesgo</span>
    <input class="f" placeholder="filtrar… (ej. edad, mora)" oninput="filt('#v0 tbody tr',this.value)"></div>
  <table><thead><tr><th>#</th><th>score</th><th>Q</th><th>n</th><th>%</th><th>Regla del segmento</th></tr></thead>
  <tbody>{rows}</tbody></table>
</section>

<section class="view" id="v1">
  <div class="bar">
    <span class="legend">raíz = <b>cat_score</b> (reglas reales); dentro de cada categoría se ramifican las demás variables</span>
    <button onclick="setAll(true)" style="border:1px solid #cfdcd8;background:#fff;border-radius:18px;padding:8px 14px;cursor:pointer">Expandir todo</button>
    <button onclick="setAll(false)" style="border:1px solid #cfdcd8;background:#fff;border-radius:18px;padding:8px 14px;cursor:pointer">Colapsar todo</button>
    <input class="f" placeholder="resaltar variable…" oninput="hlt(this.value)"></div>
  <div id="tree">{TREE}</div>
</section>

<script>
 const SEG={SEG}, TOTAL={TOTAL};
 const SMIN=Math.min(...SEG.map(s=>s[0])), SMAX=Math.max(...SEG.map(s=>s[0]));
 function pool(thr){{let n=0,sw=0; for(const[s,c]of SEG) if(s>=thr){{n+=c;sw+=s*c;}}
   return {{n:n, pct:100*n/TOTAL, avg:n?sw/n:0}};}}
 function fmtN(x){{return x.toLocaleString('es-PE');}}
 function tab(i,b){{document.querySelectorAll('.view').forEach((v,k)=>v.classList.toggle('on',k===i));
   document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on'));b.classList.add('on');}}
 function filt(sel,t){{t=t.trim().toLowerCase();
   document.querySelectorAll(sel).forEach(tr=>tr.classList.toggle('hide',t&&!tr.textContent.toLowerCase().includes(t)));}}
 function setAll(o){{document.querySelectorAll('#tree details').forEach(d=>d.open=o);}}
 function hlt(t){{t=t.trim().toLowerCase();
   document.querySelectorAll('#tree .leaf').forEach(l=>l.classList.toggle('hl',t&&(l.dataset.rule||'').toLowerCase().includes(t)));
   if(t)setAll(true);}}
 function chart(thr){{
   const W=1000,H=300,L=60,R=950,T=20,B=260;
   const xs=s=>L+(s-SMIN)/(SMAX-SMIN)*(R-L);
   const maxN=TOTAL;
   const ys=n=>B-(n/maxN)*(B-T);
   let pts=[],step=(SMAX-SMIN)/120;
   for(let s=SMIN;s<=SMAX+1e-6;s+=step){{pts.push([xs(s),ys(pool(s).n)]);}}
   const poly=pts.map(p=>p[0].toFixed(1)+','+p[1].toFixed(1)).join(' ');
   const area='60,260 '+poly+' '+xs(SMAX).toFixed(1)+',260';
   const mx=xs(thr);
   let ticks='';
   for(let k=0;k<=4;k++){{const v=maxN*k/4, y=ys(v);
     ticks+=`<line x1="60" y1="${{y}}" x2="950" y2="${{y}}" stroke="#eef2f1"/>`+
            `<text x="54" y="${{y+4}}" text-anchor="end" font-size="11" fill="#9fb0ab">${{(v/1e6).toFixed(1)}}M</text>`;}}
   for(const v of [SMIN,650,730,820,SMAX]){{const x=xs(v);
     ticks+=`<text x="${{x}}" y="278" text-anchor="middle" font-size="11" fill="#9fb0ab">${{Math.round(v)}}</text>`;}}
   document.getElementById('chart').innerHTML=
     ticks+
     `<polygon points="${{area}}" fill="#00a49922"/>`+
     `<polyline points="${{poly}}" fill="none" stroke="#007a72" stroke-width="2.5"/>`+
     `<line x1="${{mx}}" y1="20" x2="${{mx}}" y2="260" stroke="#d73027" stroke-width="2" stroke-dasharray="5,4"/>`+
     `<circle cx="${{mx}}" cy="${{ys(pool(thr).n)}}" r="5" fill="#d73027"/>`+
     `<text x="500" y="296" text-anchor="middle" font-size="12" fill="#5b6f6a">apetito (score mínimo) →</text>`;
 }}
 function upd(){{
   const thr=+document.getElementById('thrn').value||0;
   const p=(+document.getElementById('pct').value||0)/100;
   const tlo=thr*(1-p), thi=thr*(1+p);
   const b=pool(thr), lo=pool(tlo), hi=pool(thi);
   document.getElementById('k0n').textContent=fmtN(b.n)+' leads';
   document.getElementById('k0s').textContent=b.pct.toFixed(1)+'% base · score prom '+b.avg.toFixed(0);
   const dlo=lo.n-b.n, dhi=hi.n-b.n, pp=(p*100);
   document.getElementById('kmt').textContent=`Si bajo el apetito −${{pp}}% (≥ ${{tlo.toFixed(0)}})`;
   document.getElementById('kpt').textContent=`Si subo el apetito +${{pp}}% (≥ ${{thi.toFixed(0)}})`;
   document.getElementById('kmn').textContent=fmtN(lo.n)+' leads';
   document.getElementById('kms').innerHTML=`<span class="${{dlo>=0?'up':'dn'}}">${{dlo>=0?'+':''}}${{fmtN(dlo)}} leads</span> · score prom ${{lo.avg.toFixed(0)}}`;
   document.getElementById('kpn').textContent=fmtN(hi.n)+' leads';
   document.getElementById('kps').innerHTML=`<span class="${{dhi>=0?'up':'dn'}}">${{dhi>=0?'+':''}}${{fmtN(dhi)}} leads</span> · score prom ${{hi.avg.toFixed(0)}}`;
   chart(thr);
 }}
 upd();
</script>
</body></html>"""

with open("segmentacion_riesgo_global.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print("OK -> categorias:", orden)
