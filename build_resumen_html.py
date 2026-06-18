# -*- coding: utf-8 -*-
"""Vista resumida y explicativa del árbol, ordenada de MENOR a MAYOR riesgo."""
from build_arbol_html import leaves, TOTAL, color, DISP

# --- agrupar por quintil ---
TIERS = {}
for l in leaves:
    TIERS.setdefault(l["q"], []).append(l)

def agg(ls):
    n = sum(x["n"] for x in ls)
    return {"n": n, "pct": 100*n/TOTAL,
            "smin": min(x["sc"] for x in ls), "smax": max(x["sc"] for x in ls),
            "savg": sum(x["sc"]*x["n"] for x in ls)/n, "top": sorted(ls, key=lambda x:-x["n"])[:3]}

orden = sorted(TIERS, key=lambda q: -agg(TIERS[q])["savg"])   # mayor score (menor riesgo) primero

ETIQ = {0:("Riesgo MUY BAJO","Mejor perfil — priorizar / mejor oferta"),
        1:("Riesgo BAJO","Buen perfil — campañas con condiciones estándar"),
        2:("Riesgo MEDIO","Perfil intermedio — ofertas acotadas / cautela"),
        3:("Riesgo ALTO","Peor perfil — descartar o monitoreo estricto")}

PERFIL = {
 "G1":"Categoría de score buena (cat ≤ 5). Mejores clientes: mayor categoría, suelen tener más ingreso y edad.",
 "G2":"Categoría de score 6 PERO rescatados por edad alta (&gt;54) o pocos días de mora del castigo.",
 "G4":"Categoría 6, edad ≤ 50 y mora del castigo moderada (≤ 3,192 días). Zona de frontera.",
 "G5":"Categoría 6 + mora alta (&gt; 3,192 días) + clientes jóvenes. Núcleo del riesgo.",
}

def regla(l):
    return " · ".join(f"{DISP.get(v,v)} {s}" if v!="puntuacion_cal_cat" else f"cat_score {s}"
                      for v,s in l["conds"].items())

cards = ""
for i,q in enumerate(orden):
    a = agg(TIERS[q]); tit,acc = ETIQ[i]; col = color(a["savg"])
    tops = "".join(
      f'<tr><td class="rg">{regla(l)}</td><td>{l["n"]:,}</td><td>{100*l["n"]/TOTAL:.1f}%</td>'
      f'<td><b style="color:{color(l["sc"])}">{l["sc"]:.0f}</b></td></tr>' for l in a["top"])
    cards += f"""
    <div class="card" style="border-left:10px solid {col}">
      <div class="hd">
        <div><span class="q" style="background:{col}">{q}</span>
          <span class="tit">{tit}</span></div>
        <div class="kpi"><b>{a['n']:,}</b> clientes · <b>{a['pct']:.1f}%</b> · score {a['smin']:.0f}–{a['smax']:.0f}</div>
      </div>
      <div class="perfil">{PERFIL.get(q,'')}</div>
      <table><thead><tr><th>Segmentos más grandes</th><th>n</th><th>%</th><th>score</th></tr></thead>
        <tbody>{tops}</tbody></table>
    </div>"""

HTML = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Resumen de riesgo — Escenario Global</title>
<style>
 *{{box-sizing:border-box;margin:0;padding:0;font-family:"Segoe UI",Roboto,Arial,sans-serif}}
 body{{background:#f4f7f6;color:#10241f;padding:30px 8vw 60px}}
 h1{{color:#007a72;font-size:30px}} .sub{{color:#5b6f6a;margin:6px 0 24px;font-size:16px}}
 .flow{{display:flex;align-items:center;gap:10px;margin-bottom:24px;font-size:14px;color:#5b6f6a}}
 .flow .ar{{flex:1;height:10px;border-radius:6px;background:linear-gradient(90deg,#1a9850,#ffffbf,#d73027)}}
 .card{{background:#fff;border-radius:14px;padding:20px 24px;margin-bottom:18px;box-shadow:0 4px 14px #0000000f}}
 .hd{{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px}}
 .q{{color:#10241f;font-weight:800;border-radius:8px;padding:4px 12px;font-size:16px;margin-right:10px}}
 .tit{{font-size:20px;font-weight:700;color:#23433c}}
 .kpi{{font-size:15px;color:#33514a}}
 .perfil{{margin:12px 0 14px;font-size:15.5px;line-height:1.55;color:#2c463f;background:#f1f7f5;padding:10px 14px;border-radius:8px}}
 table{{width:100%;border-collapse:collapse;font-size:13.5px}}
 th{{text-align:left;color:#5b6f6a;font-weight:600;border-bottom:2px solid #e6efec;padding:6px 8px}}
 td{{padding:6px 8px;border-bottom:1px solid #f0f4f3}}
 .rg{{font-family:Consolas,monospace;font-size:12px;color:#33514a}}
</style></head><body>
 <h1>Mapa de riesgo — Escenario Global</h1>
 <div class="sub">2.28 M clientes · 74 segmentos · objetivo = score · ordenado de <b>menor</b> a <b>mayor</b> riesgo</div>
 <div class="flow"><span>menor riesgo</span><span class="ar"></span><span>mayor riesgo</span></div>
 {cards}
</body></html>"""

with open("resumen_riesgo_global.html","w",encoding="utf-8") as f:
    f.write(HTML)
print("OK ->", " > ".join(orden))
