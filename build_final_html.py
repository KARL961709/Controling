# -*- coding: utf-8 -*-
"""HTML con 2 pestañas: (1) Segmentos desagrupados ordenados por riesgo, (2) Árbol interactivo."""
from build_arbol_html import leaves, TOTAL, color, DISP, TREE

def regla(l):
    return " · ".join(f"{DISP.get(v,v)} {s}" if v != "puntuacion_cal_cat" else f"cat_score {s}"
                      for v, s in l["conds"].items())

# --- Pestaña 1: TODOS los segmentos, de menor a mayor riesgo (score desc) ---
ls = sorted(leaves, key=lambda x: -x["sc"])
rows = ""
for i, l in enumerate(ls, 1):
    c = color(l["sc"])
    rows += (f'<tr style="border-left:8px solid {c}">'
             f'<td class="r">{i}</td>'
             f'<td><span class="chip" style="background:{c}">{l["sc"]:.0f}</span></td>'
             f'<td><span class="q">{l["q"]}</span></td>'
             f'<td class="num">{l["n"]:,}</td><td class="num">{100*l["n"]/TOTAL:.1f}%</td>'
             f'<td class="rg">{regla(l)}</td></tr>')

HTML = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Segmentación de riesgo — Escenario Global</title>
<style>
 *{{box-sizing:border-box;margin:0;padding:0;font-family:"Segoe UI",Roboto,Arial,sans-serif}}
 body{{background:#f4f7f6;color:#10241f}}
 header{{background:linear-gradient(90deg,#007a72,#00a499);color:#fff;padding:16px 28px;position:sticky;top:0;z-index:20}}
 header h1{{font-size:21px}} header .s{{opacity:.9;font-size:13.5px;margin-top:3px}}
 .tabs{{display:flex;gap:8px;margin-top:12px}}
 .tabs button{{background:#ffffff22;color:#fff;border:1px solid #ffffff66;border-radius:18px;padding:8px 18px;cursor:pointer;font-size:14px}}
 .tabs button.on{{background:#fff;color:#007a72;font-weight:700}}
 .view{{display:none;padding:22px 4vw 70px}} .view.on{{display:block}}
 .legend{{display:flex;align-items:center;gap:8px;font-size:13px;color:#33514a;margin-bottom:14px}}
 .grad{{width:150px;height:12px;border-radius:6px;background:linear-gradient(90deg,#1a9850,#ffffbf,#d73027)}}
 input.f{{border:1px solid #cfdcd8;border-radius:18px;padding:8px 14px;font-size:13px;min-width:220px;margin-left:auto}}
 .bar{{display:flex;align-items:center;gap:12px;margin-bottom:12px;flex-wrap:wrap}}
 table{{width:100%;border-collapse:collapse;background:#fff;border-radius:10px;overflow:hidden;font-size:13.5px}}
 th{{background:#eaf3f1;color:#23433c;text-align:left;padding:9px 10px;position:sticky;top:96px}}
 td{{padding:7px 10px;border-bottom:1px solid #f0f4f3}}
 td.r{{color:#9fb0ab;font-weight:700;width:34px}} td.num{{text-align:right;white-space:nowrap}}
 .chip{{color:#10241f;font-weight:800;border-radius:7px;padding:3px 9px;font-size:13px}}
 .q{{background:#eef3f1;border-radius:10px;padding:2px 9px;font-size:12px;font-weight:700;color:#33514a}}
 .rg{{font-family:Consolas,monospace;font-size:12px;color:#33514a}}
 tr.hide{{display:none}}
 /* árbol */
 details.node{{margin:4px 0}} .kids{{margin-left:24px;border-left:2px dashed #b9ccc7;padding-left:16px}}
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
  <div class="bar">
    <span class="legend">menor riesgo <span class="grad"></span> mayor riesgo</span>
    <input class="f" placeholder="filtrar segmentos… (ej. edad, mora)" oninput="filt('#v0 tbody tr',this.value)">
  </div>
  <table><thead><tr><th>#</th><th>score</th><th>Q</th><th>n</th><th>%</th><th>Regla del segmento</th></tr></thead>
  <tbody>{rows}</tbody></table>
</section>

<section class="view" id="v1">
  <div class="bar">
    <span class="legend">menor score <span class="grad" style="background:linear-gradient(90deg,#d73027,#ffffbf,#1a9850)"></span> mayor score</span>
    <button onclick="setAll(true)" style="border:1px solid #cfdcd8;background:#fff;border-radius:18px;padding:8px 14px;cursor:pointer">Expandir todo</button>
    <button onclick="setAll(false)" style="border:1px solid #cfdcd8;background:#fff;border-radius:18px;padding:8px 14px;cursor:pointer">Colapsar todo</button>
    <input class="f" placeholder="resaltar variable… (ej. cat_score)" oninput="hlt(this.value)">
  </div>
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
print("OK ->", len(ls), "segmentos")
