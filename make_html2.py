# -*- coding: utf-8 -*-
import json
data=open("arbol_rd_data.json").read()
HTML=r"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Árbol de RD por segmento</title>
<style>
:root{--bg:#0f1419;--card:#1a2230;--card2:#222c3d;--ink:#e7edf5;--mut:#9fb0c3;--line:#2c3a4f;--accent:#4ea1ff;}
*{box-sizing:border-box}body{margin:0;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;background:var(--bg);color:var(--ink);line-height:1.45}
.wrap{max-width:1180px;margin:0 auto;padding:22px 18px 60px}h1{font-size:22px;margin:0 0 4px}
.sub{color:var(--mut);font-size:13px;margin-bottom:18px}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px 18px;margin-bottom:18px}
.panel h2{font-size:15px;margin:0 0 10px;color:var(--accent)}.panel li{font-size:13.5px;margin:3px 0;color:#d6deea}
.kpis{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:18px}.kpi{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:10px 14px;min-width:120px}
.kpi .v{font-size:20px;font-weight:700}.kpi .l{font-size:11px;color:var(--mut);text-transform:uppercase;letter-spacing:.04em}
.qbar{display:flex;height:26px;border-radius:7px;overflow:hidden;border:1px solid var(--line)}
.qseg{display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#0b0f14}
.legend{display:inline-flex;align-items:center;gap:6px;margin-right:14px;font-size:12px;color:var(--mut)}
.chip{display:inline-flex;align-items:center;gap:5px;background:var(--card2);border:1px solid var(--line);border-radius:999px;padding:2px 9px;font-size:11.5px;color:#cdd8e6}
.dot{width:11px;height:11px;border-radius:3px;display:inline-block}
.tabs{display:flex;gap:8px;margin-bottom:14px}.tab{background:var(--card);border:1px solid var(--line);color:var(--mut);padding:7px 14px;border-radius:8px;cursor:pointer;font-size:13px}
.tab.on{background:var(--accent);color:#06121f;border-color:var(--accent);font-weight:600}
.toolbar{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap}.btn{background:var(--card2);border:1px solid var(--line);color:#cdd8e6;padding:5px 11px;border-radius:7px;cursor:pointer;font-size:12px}.btn:hover{border-color:var(--accent)}
.node{margin:3px 0}.row{display:flex;align-items:center;gap:9px;padding:7px 10px;border:1px solid var(--line);border-radius:9px;background:var(--card);cursor:pointer;transition:.12s}
.row:hover{border-color:var(--accent)}.row.leaf{cursor:default}.tw{width:14px;text-align:center;color:var(--mut);font-size:11px;flex:0 0 auto}
.cond{font-weight:600;font-size:13px}.var{color:var(--mut);font-size:12px}.spacer{flex:1}.meta{display:flex;align-items:center;gap:10px;flex:0 0 auto}
.rdpill{font-variant-numeric:tabular-nums;font-weight:700;font-size:12.5px;padding:2px 8px;border-radius:6px;color:#06121f;min-width:62px;text-align:center}
.npill{font-size:11.5px;color:var(--mut);font-variant-numeric:tabular-nums;min-width:120px;text-align:right}
.qbadge{font-size:10.5px;font-weight:800;color:#06121f;border-radius:5px;padding:2px 7px}
.kids{margin-left:20px;border-left:1px dashed var(--line);padding-left:12px;display:none}.kids.open{display:block}
.rules{margin:5px 0 2px 44px;display:flex;flex-wrap:wrap;gap:5px}
table{width:100%;border-collapse:collapse;font-size:12.5px}th,td{padding:7px 9px;border-bottom:1px solid var(--line);text-align:left}
th{color:var(--mut);font-weight:600}td.num{text-align:right;font-variant-numeric:tabular-nums}tr:hover td{background:#19222f}.hidden{display:none}
</style></head><body><div class="wrap">
<h1>🌳 Árbol de Riesgo (RD) por segmento</h1>
<div class="sub">Cada hoja es un segmento con sus reglas. Color = <b>RD medio</b> (tasa de incumplimiento): <b>verde = RD bajo (bueno)</b>, <b>rojo = RD alto (malo)</b>. La jerarquía es una reconstrucción didáctica; la definición exacta de cada segmento son sus reglas (chips).</div>
<div class="kpis" id="kpis"></div>
<div class="panel"><h2>Distribución de población por quintil</h2><div class="qbar" id="qbar"></div><div style="margin-top:10px" id="qlegend"></div></div>
<div class="panel"><h2>Cómo leer el árbol</h2><ul>
<li><b>Raíz → hojas:</b> bajas siguiendo condiciones. Si una variable <i>no aparece</i> en una rama es porque no se usó ahí (<code>(todos)</code>).</li>
<li><b>Primer corte = Score (rango):</b> es el ordenador principal del riesgo. A mayor score, menor RD: <b>&gt;650 → G1</b> (RD ~0.06–0.10); <b>(452, 650] → G3/G4</b> (RD ~0.16–0.19); <b>≤452 → G5</b> (RD 0.30–0.70).</li>
<li><b>Dentro de (452, 650] manda la segmentación:</b> <b>≤4 → G3</b> (se subdivide por pasivo U6M y deuda castigada); <b>&gt;4 → G4</b> (subdivide por pasivo U3M).</li>
<li><b>El tramo de peor riesgo (≤242) llega a RD 0.70</b>; el <code>Missing</code> de segmentación en (374, 452] tiene mejor RD (0.30) que el resto del tramo (0.35).</li>
<li><b>Nota:</b> en este corte <b>no aparece G2</b>; el orden por riesgo es G1 (mejor) → G3 → G4 → G5 (peor).</li>
</ul></div>
<div class="tabs"><div class="tab on" data-v="tree">Árbol</div><div class="tab" data-v="table">Tabla de hojas</div></div>
<div id="view-tree"><div class="toolbar"><button class="btn" onclick="setAll(true)">Expandir todo</button><button class="btn" onclick="setAll(false)">Colapsar todo</button><button class="btn" onclick="expandTo1()">Solo nivel 1</button></div><div id="tree"></div></div>
<div id="view-table" class="hidden"><table id="ftable"><thead><tr><th>#</th><th>Reglas del segmento</th><th class="num">n</th><th class="num">%</th><th class="num">RD medio</th><th>Quintil</th></tr></thead><tbody></tbody></table></div>
</div><script>
const DATA=__DATA__;
const QCOL={G1:"#1a9850",G2:"#91cf60",G3:"#f4d03f",G4:"#fc8d59",G5:"#d73027"};
const RDMIN=Math.min(...DATA.flat.map(r=>r.rd)),RDMAX=Math.max(...DATA.flat.map(r=>r.rd));
function rdColor(v){let t=(v-RDMIN)/(RDMAX-RDMIN);t=Math.max(0,Math.min(1,t));let h=(1-t)*130;return `hsl(${h},62%,52%)`;}
function fmt(n){return n.toLocaleString("es-PE");}
const total=DATA.total,leaves=DATA.flat.length;
const qsum={};DATA.flat.forEach(r=>qsum[r.q]=(qsum[r.q]||0)+r.n);
const wrd=DATA.flat.reduce((a,r)=>a+r.n*r.rd,0)/total;
document.getElementById("kpis").innerHTML=`
 <div class="kpi"><div class="v">${fmt(total)}</div><div class="l">Población (n)</div></div>
 <div class="kpi"><div class="v">${leaves}</div><div class="l">Segmentos (hojas)</div></div>
 <div class="kpi"><div class="v">${wrd.toFixed(4)}</div><div class="l">RD medio ponderado</div></div>
 <div class="kpi"><div class="v">${Object.keys(qsum).length}</div><div class="l">Quintiles presentes</div></div>`;
const order=["G1","G2","G3","G4","G5"];let qb="",ql="";
order.filter(q=>qsum[q]).forEach(q=>{const p=qsum[q]/total*100;qb+=`<div class="qseg" style="width:${p}%;background:${QCOL[q]}" title="${q}: ${fmt(qsum[q])} (${p.toFixed(1)}%)">${p>5?q:""}</div>`;});
order.filter(q=>qsum[q]).forEach(q=>{ql+=`<span class="legend"><span class="dot" style="background:${QCOL[q]}"></span>${q} — ${fmt(qsum[q])} (${(qsum[q]/total*100).toFixed(1)}%)</span>`;});
document.getElementById("qbar").innerHTML=qb;document.getElementById("qlegend").innerHTML=ql;
function nodeHTML(n){
 const hasK=n.kids&&n.kids.length;const tw=hasK?'<span class="tw">▶</span>':'<span class="tw">•</span>';
 const cond=n.val?`<span class="cond">${n.val}</span> <span class="var">· ${n.var}</span>`:`<span class="cond">${n.var}</span>`;
 const rd=`<span class="rdpill" style="background:${rdColor(n.rd)}">${n.rd.toFixed(4)}</span>`;
 const np=`<span class="npill">${fmt(n.n)} &nbsp;·&nbsp; ${n.pct}%</span>`;
 const qbg=n.leaf?`<span class="qbadge" style="background:${QCOL[n.leafQ]}">${n.leafQ}</span>`:`<span class="qbadge" style="background:${QCOL[n.q]};opacity:.55">${n.q}</span>`;
 let rules=n.leaf?`<div class="rules">`+n.rules.map(r=>`<span class="chip">${r[0]}: <b>&nbsp;${r[1]}</b></span>`).join("")+`</div>`:"";
 let kids=hasK?`<div class="kids">`+n.kids.map(nodeHTML).join("")+`</div>`:"";
 return `<div class="node"><div class="row ${n.leaf?'leaf':''}" ${hasK?'onclick="tog(this,event)"':''}>${tw}${cond}<span class="spacer"></span><span class="meta">${np}${rd}${qbg}</span></div>${rules}${kids}</div>`;
}
document.getElementById("tree").innerHTML=DATA.tree.kids.map(nodeHTML).join("");
function tog(row,e){e.stopPropagation();const k=row.parentNode.querySelector(":scope > .kids");if(!k)return;k.classList.toggle("open");row.querySelector(".tw").textContent=k.classList.contains("open")?"▼":"▶";}
function setAll(o){document.querySelectorAll(".kids").forEach(k=>k.classList.toggle("open",o));document.querySelectorAll(".row .tw").forEach(t=>{if(t.textContent!=="•")t.textContent=o?"▼":"▶";});}
function expandTo1(){setAll(false);document.querySelectorAll("#tree > .node > .row .tw").forEach(t=>{const k=t.closest(".node").querySelector(":scope > .kids");if(k){k.classList.add("open");if(t.textContent!=="•")t.textContent="▼";}});}
expandTo1();
let tb="";DATA.flat.forEach((r,i)=>{const chips=r.rules.map(x=>`<span class="chip">${x[0]}: <b>&nbsp;${x[1]}</b></span>`).join(" ");
 tb+=`<tr><td>${i+1}</td><td>${chips}</td><td class="num">${fmt(r.n)}</td><td class="num">${r.pct}</td><td class="num"><span class="rdpill" style="background:${rdColor(r.rd)}">${r.rd.toFixed(4)}</span></td><td><span class="qbadge" style="background:${QCOL[r.q]}">${r.q}</span></td></tr>`;});
document.querySelector("#ftable tbody").innerHTML=tb;
document.querySelectorAll(".tab").forEach(t=>t.onclick=()=>{document.querySelectorAll(".tab").forEach(x=>x.classList.remove("on"));t.classList.add("on");const v=t.dataset.v;document.getElementById("view-tree").classList.toggle("hidden",v!=="tree");document.getElementById("view-table").classList.toggle("hidden",v!=="table");});
</script></body></html>"""
open("arbol_rd.html","w").write(HTML.replace("__DATA__",data))
print("ok arbol_rd.html")
