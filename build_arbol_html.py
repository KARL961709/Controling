# -*- coding: utf-8 -*-
"""Reconstruye el árbol a partir del CUADRO DEL ÁRBOL COMPLETO y genera HTML interactivo."""
INF = float("inf")
TOTAL = 2280675

# cal (puntuacion_cal_cat): los labels vienen redondeados -> mapeo a límites reales (.5)
CALMAP = {"<= 2": (-INF, 1.5), "(2, 2]": (1.5, 2.5), "(2, 4]": (2.5, 3.5),
          "(4, 4]": (3.5, 4.5), "(4, 6]": (4.5, 5.5), "> 6": (5.5, INF)}
CALNUM = {"<= 2": 1, "(2, 2]": 2, "(2, 4]": 3, "(4, 4]": 4, "(4, 6]": 5, "> 6": 6}

DISP = {  # nombres cortos para mostrar
    "deuda_cas": "deuda_cas", "monto_castigado_total": "monto_cast",
    "nro_entidades_castigo": "nro_ent_cast", "max_dias_mora_castigo": "dias_mora",
    "meses_desde_primer_castigo": "meses_1er_cast", "edad_num": "edad",
    "rk_ing_num": "ingreso(rk)", "saldo_fdp_tot_txs_u3m": "txs_fdp_u3m",
    "saldo_prom_tot_txs_u3m": "txs_prom_u3m", "saldo_prom_tot_txs_u6m": "txs_prom_u6m",
    "saldo_fdp_tot_planilla_u6m": "planilla_u6m", "saldo_prom_tot_pasivo_u3m": "pasivo_u3m",
    "saldo_prom_tot_pasivo_u6m": "pasivo_u6m", "saldo_pasivo_componentes_u3m": "pasivo_comp",
    "prom_saldo_pasivo_u4m": "pasivo_u4m", "puntuacion_cal_cat": "cat_score",
    "segmentacion_gdp_v2": "seg_gdp", "flg_far_mto_trx_presencial_12m_c216": "flg_far",
}

def num(z): return float(str(z).replace(",", "").strip())

def parse(var, s):
    if var == "puntuacion_cal_cat":
        return CALMAP[s]
    s = s.strip()
    if s.startswith("<="):
        return (-INF, num(s[2:]))
    if s.startswith(">"):
        return (num(s[1:]), INF)
    a, b = s.strip("()[]").split(", ")
    return (num(a), num(b))

# ---- 74 hojas: (n, score, quintil, {variable: condicion}) ----
RAW = [
 (3655,977.54,"G1",{"puntuacion_cal_cat":"<= 2"}),
 (2294,959.17,"G1",{"rk_ing_num":"> 3,328","saldo_prom_tot_pasivo_u6m":"> 67","puntuacion_cal_cat":"(2, 2]"}),
 (2980,957.92,"G1",{"rk_ing_num":"> 3,328","saldo_prom_tot_pasivo_u6m":"<= 67","puntuacion_cal_cat":"(2, 2]"}),
 (2490,956.64,"G1",{"rk_ing_num":"<= 3,328","saldo_prom_tot_pasivo_u3m":"> 267","puntuacion_cal_cat":"(2, 2]"}),
 (5026,956.57,"G1",{"rk_ing_num":"<= 3,328","saldo_prom_tot_pasivo_u3m":"<= 267","puntuacion_cal_cat":"(2, 2]"}),
 (5535,919.59,"G1",{"rk_ing_num":"> 3,328","saldo_fdp_tot_txs_u3m":"> 61","puntuacion_cal_cat":"(2, 4]"}),
 (2793,916.02,"G1",{"nro_entidades_castigo":"<= 2","max_dias_mora_castigo":"<= 3,192","edad_num":"> 50","rk_ing_num":"> 3,328","saldo_fdp_tot_txs_u3m":"<= 61","puntuacion_cal_cat":"(2, 4]"}),
 (5758,915.70,"G1",{"nro_entidades_castigo":"<= 2","max_dias_mora_castigo":"> 3,192","edad_num":"> 50","rk_ing_num":"> 3,328","saldo_fdp_tot_txs_u3m":"<= 61","puntuacion_cal_cat":"(2, 4]"}),
 (11278,914.47,"G1",{"nro_entidades_castigo":"<= 2","edad_num":"<= 50","rk_ing_num":"> 3,328","saldo_fdp_tot_txs_u3m":"<= 61","puntuacion_cal_cat":"(2, 4]"}),
 (3284,912.89,"G1",{"nro_entidades_castigo":"> 2","rk_ing_num":"> 3,328","saldo_fdp_tot_txs_u3m":"<= 61","puntuacion_cal_cat":"(2, 4]"}),
 (2872,912.21,"G1",{"edad_num":"> 54","rk_ing_num":"<= 3,328","saldo_prom_tot_txs_u6m":"> 5","puntuacion_cal_cat":"(2, 4]"}),
 (13592,912.20,"G1",{"edad_num":"> 54","rk_ing_num":"<= 3,328","saldo_prom_tot_txs_u6m":"<= 5","puntuacion_cal_cat":"(2, 4]"}),
 (3408,911.97,"G1",{"edad_num":"(50, 54]","rk_ing_num":"<= 3,328","puntuacion_cal_cat":"(2, 4]"}),
 (7025,910.93,"G1",{"edad_num":"<= 50","rk_ing_num":"<= 3,328","saldo_prom_tot_pasivo_u6m":"> 67","puntuacion_cal_cat":"(2, 4]"}),
 (5341,909.40,"G1",{"edad_num":"<= 50","rk_ing_num":"<= 3,328","saldo_prom_tot_pasivo_u6m":"<= 67","puntuacion_cal_cat":"(2, 4]","segmentacion_gdp_v2":"<= 4"}),
 (8305,909.27,"G1",{"edad_num":"<= 50","rk_ing_num":"<= 3,328","saldo_prom_tot_pasivo_u6m":"<= 67","puntuacion_cal_cat":"(2, 4]","segmentacion_gdp_v2":"> 4"}),
 (9054,908.95,"G1",{"max_dias_mora_castigo":"<= 2,256","rk_ing_num":"<= 3,328","puntuacion_cal_cat":"(4, 4]"}),
 (3280,908.54,"G1",{"max_dias_mora_castigo":"(2,256, 2,534]","rk_ing_num":"<= 3,328","puntuacion_cal_cat":"(4, 4]"}),
 (3773,907.64,"G1",{"max_dias_mora_castigo":"(2,534, 3,192]","edad_num":"> 50","rk_ing_num":"<= 3,328","puntuacion_cal_cat":"(4, 4]"}),
 (2888,907.62,"G1",{"max_dias_mora_castigo":"(2,534, 3,192]","edad_num":"<= 50","rk_ing_num":"<= 3,328","puntuacion_cal_cat":"(4, 4]"}),
 (3732,907.34,"G1",{"max_dias_mora_castigo":"> 3,192","rk_ing_num":"<= 3,328","saldo_prom_tot_pasivo_u3m":"> 267","puntuacion_cal_cat":"(4, 4]"}),
 (31235,906.24,"G1",{"max_dias_mora_castigo":"> 3,192","rk_ing_num":"<= 3,328","saldo_prom_tot_pasivo_u3m":"<= 267","puntuacion_cal_cat":"(4, 4]"}),
 (3548,871.29,"G1",{"monto_castigado_total":"<= 282","edad_num":"> 60","puntuacion_cal_cat":"(4, 6]","segmentacion_gdp_v2":"<= 4"}),
 (22035,869.59,"G1",{"monto_castigado_total":"> 282","edad_num":"> 66","puntuacion_cal_cat":"(4, 6]","segmentacion_gdp_v2":"<= 4"}),
 (20237,868.93,"G1",{"monto_castigado_total":"> 282","edad_num":"(60, 66]","puntuacion_cal_cat":"(4, 6]","segmentacion_gdp_v2":"<= 4"}),
 (4907,868.54,"G1",{"edad_num":"<= 60","saldo_prom_tot_pasivo_u6m":"> 67","saldo_pasivo_componentes_u3m":"> 171","puntuacion_cal_cat":"(4, 6]","segmentacion_gdp_v2":"<= 4"}),
 (3174,868.41,"G1",{"edad_num":"<= 60","saldo_prom_tot_pasivo_u6m":"> 67","saldo_pasivo_componentes_u3m":"<= 171","puntuacion_cal_cat":"(4, 6]","segmentacion_gdp_v2":"<= 4"}),
 (23135,867.97,"G1",{"edad_num":"(54, 60]","saldo_prom_tot_pasivo_u6m":"<= 67","puntuacion_cal_cat":"(4, 6]","segmentacion_gdp_v2":"<= 4"}),
 (40407,867.40,"G1",{"edad_num":"<= 54","saldo_prom_tot_pasivo_u6m":"<= 67","puntuacion_cal_cat":"(4, 6]","segmentacion_gdp_v2":"<= 4"}),
 (2393,866.99,"G1",{"max_dias_mora_castigo":"<= 2,534","saldo_prom_tot_pasivo_u6m":"> 67","puntuacion_cal_cat":"(4, 6]","segmentacion_gdp_v2":"> 4"}),
 (6124,866.44,"G1",{"max_dias_mora_castigo":"> 2,534","saldo_prom_tot_pasivo_u6m":"> 67","puntuacion_cal_cat":"(4, 6]","segmentacion_gdp_v2":"> 4"}),
 (2932,865.92,"G1",{"deuda_cas":"<= 156","nro_entidades_castigo":"<= 2","saldo_prom_tot_pasivo_u6m":"<= 67","puntuacion_cal_cat":"(4, 6]","segmentacion_gdp_v2":"> 4"}),
 (38025,865.57,"G1",{"deuda_cas":"> 156","nro_entidades_castigo":"<= 2","saldo_prom_tot_pasivo_u6m":"<= 67","puntuacion_cal_cat":"(4, 6]","segmentacion_gdp_v2":"> 4"}),
 (4637,864.04,"G1",{"nro_entidades_castigo":"> 2","saldo_prom_tot_pasivo_u6m":"<= 67","puntuacion_cal_cat":"(4, 6]","segmentacion_gdp_v2":"> 4"}),
 (5739,785.44,"G2",{"nro_entidades_castigo":"<= 2","max_dias_mora_castigo":"<= 2,534","edad_num":"> 60","puntuacion_cal_cat":"> 6","segmentacion_gdp_v2":"<= 2"}),
 (2581,776.62,"G2",{"nro_entidades_castigo":"> 2","max_dias_mora_castigo":"<= 2,534","edad_num":"> 60","puntuacion_cal_cat":"> 6","segmentacion_gdp_v2":"<= 2"}),
 (16487,770.85,"G2",{"nro_entidades_castigo":"<= 2","max_dias_mora_castigo":"<= 2,534","edad_num":"> 66","puntuacion_cal_cat":"> 6","segmentacion_gdp_v2":"> 2"}),
 (7107,761.64,"G2",{"nro_entidades_castigo":"> 2","max_dias_mora_castigo":"<= 2,534","edad_num":"> 66","puntuacion_cal_cat":"> 6","segmentacion_gdp_v2":"> 2"}),
 (11812,760.31,"G2",{"max_dias_mora_castigo":"<= 2,044","edad_num":"(60, 66]","puntuacion_cal_cat":"> 6","segmentacion_gdp_v2":"> 2"}),
 (13764,750.75,"G2",{"max_dias_mora_castigo":"(2,044, 2,534]","edad_num":"(60, 66]","puntuacion_cal_cat":"> 6","segmentacion_gdp_v2":"> 2"}),
 (80248,749.31,"G2",{"nro_entidades_castigo":"<= 2","max_dias_mora_castigo":"> 2,534","edad_num":"> 66","puntuacion_cal_cat":"> 6"}),
 (2683,737.64,"G2",{"nro_entidades_castigo":"> 2","max_dias_mora_castigo":"> 2,534","edad_num":"> 66","puntuacion_cal_cat":"> 6","flg_far_mto_trx_presencial_12m_c216":"> 0"}),
 (12218,736.32,"G2",{"nro_entidades_castigo":"> 2","max_dias_mora_castigo":"> 2,534","edad_num":"> 66","puntuacion_cal_cat":"> 6","flg_far_mto_trx_presencial_12m_c216":"<= 0"}),
 (4101,731.76,"G2",{"deuda_cas":"<= 156","max_dias_mora_castigo":"> 2,534","edad_num":"(60, 66]","puntuacion_cal_cat":"> 6"}),
 (2768,727.24,"G2",{"deuda_cas":"> 156","max_dias_mora_castigo":"> 2,534","edad_num":"(60, 66]","saldo_prom_tot_txs_u3m":"> 91","puntuacion_cal_cat":"> 6"}),
 (10419,725.91,"G2",{"deuda_cas":"> 156","max_dias_mora_castigo":"> 2,534","edad_num":"(60, 66]","rk_ing_num":"> 3,072","saldo_prom_tot_txs_u3m":"<= 91","puntuacion_cal_cat":"> 6"}),
 (90873,724.47,"G2",{"deuda_cas":"> 156","max_dias_mora_castigo":"> 2,534","edad_num":"(60, 66]","rk_ing_num":"<= 3,072","saldo_prom_tot_txs_u3m":"<= 91","puntuacion_cal_cat":"> 6"}),
 (72578,720.38,"G2",{"edad_num":"(54, 60]","puntuacion_cal_cat":"> 6","segmentacion_gdp_v2":"<= 4"}),
 (4171,714.19,"G2",{"deuda_cas":"<= 156","edad_num":"(54, 60]","puntuacion_cal_cat":"> 6","segmentacion_gdp_v2":"> 4"}),
 (116825,709.96,"G2",{"deuda_cas":"> 156","edad_num":"(54, 60]","puntuacion_cal_cat":"> 6","segmentacion_gdp_v2":"> 4"}),
 (5742,706.12,"G2",{"edad_num":"(50, 54]","saldo_prom_tot_txs_u6m":"> 106","saldo_prom_tot_pasivo_u6m":"> 67","puntuacion_cal_cat":"> 6"}),
 (5586,702.37,"G2",{"edad_num":"(50, 54]","saldo_prom_tot_txs_u6m":"<= 106","saldo_prom_tot_pasivo_u6m":"> 67","puntuacion_cal_cat":"> 6"}),
 (152030,698.50,"G2",{"edad_num":"(50, 54]","saldo_prom_tot_pasivo_u6m":"<= 67","puntuacion_cal_cat":"> 6"}),
 (380739,693.12,"G4",{"nro_entidades_castigo":"<= 2","max_dias_mora_castigo":"<= 3,192","edad_num":"<= 50","puntuacion_cal_cat":"> 6"}),
 (24269,682.71,"G4",{"nro_entidades_castigo":"> 2","max_dias_mora_castigo":"<= 3,192","edad_num":"<= 50","puntuacion_cal_cat":"> 6","flg_far_mto_trx_presencial_12m_c216":"> 0"}),
 (10412,677.73,"G2",{"nro_entidades_castigo":"> 2","max_dias_mora_castigo":"<= 3,192","edad_num":"<= 50","saldo_pasivo_componentes_u3m":"> 35","puntuacion_cal_cat":"> 6","flg_far_mto_trx_presencial_12m_c216":"<= 0"}),
 (83624,673.88,"G4",{"nro_entidades_castigo":"> 2","max_dias_mora_castigo":"<= 3,192","edad_num":"<= 50","saldo_pasivo_componentes_u3m":"<= 35","puntuacion_cal_cat":"> 6","flg_far_mto_trx_presencial_12m_c216":"<= 0"}),
 (51046,669.45,"G5",{"max_dias_mora_castigo":"> 3,192","meses_desde_primer_castigo":"> 20","edad_num":"(36, 50]","saldo_pasivo_componentes_u3m":"> 35","puntuacion_cal_cat":"> 6"}),
 (462011,663.50,"G5",{"max_dias_mora_castigo":"> 3,192","meses_desde_primer_castigo":"> 20","edad_num":"(36, 50]","saldo_pasivo_componentes_u3m":"<= 35","puntuacion_cal_cat":"> 6"}),
 (2620,654.84,"G5",{"max_dias_mora_castigo":"(3,192, 4,090]","meses_desde_primer_castigo":"> 20","edad_num":"(28, 36]","saldo_prom_tot_txs_u3m":"> 91","puntuacion_cal_cat":"> 6"}),
 (50537,652.57,"G5",{"max_dias_mora_castigo":"(3,192, 4,090]","meses_desde_primer_castigo":"> 20","edad_num":"(28, 36]","saldo_prom_tot_txs_u3m":"<= 91","puntuacion_cal_cat":"> 6"}),
 (96843,649.09,"G5",{"max_dias_mora_castigo":"> 4,090","meses_desde_primer_castigo":"> 20","edad_num":"(32, 36]","rk_ing_num":"> 1,382","puntuacion_cal_cat":"> 6"}),
 (48561,647.74,"G5",{"max_dias_mora_castigo":"> 4,090","meses_desde_primer_castigo":"> 20","edad_num":"(28, 32]","rk_ing_num":"> 1,382","puntuacion_cal_cat":"> 6"}),
 (5810,646.12,"G5",{"max_dias_mora_castigo":"> 4,090","meses_desde_primer_castigo":"> 20","edad_num":"(32, 36]","rk_ing_num":"<= 1,382","puntuacion_cal_cat":"> 6"}),
 (5801,645.24,"G5",{"max_dias_mora_castigo":"> 4,090","meses_desde_primer_castigo":"> 20","edad_num":"(28, 32]","rk_ing_num":"<= 1,382","puntuacion_cal_cat":"> 6"}),
 (10408,642.75,"G5",{"max_dias_mora_castigo":"> 3,192","meses_desde_primer_castigo":"> 20","edad_num":"<= 28","puntuacion_cal_cat":"> 6","flg_far_mto_trx_presencial_12m_c216":"> 0"}),
 (3695,637.72,"G5",{"max_dias_mora_castigo":"> 3,192","meses_desde_primer_castigo":"> 20","edad_num":"<= 28","prom_saldo_pasivo_u4m":"> 4","puntuacion_cal_cat":"> 6","flg_far_mto_trx_presencial_12m_c216":"<= 0"}),
 (36742,637.68,"G5",{"max_dias_mora_castigo":"> 3,192","meses_desde_primer_castigo":"> 20","edad_num":"<= 28","prom_saldo_pasivo_u4m":"<= 4","puntuacion_cal_cat":"> 6","flg_far_mto_trx_presencial_12m_c216":"<= 0"}),
 (31373,627.26,"G5",{"max_dias_mora_castigo":"> 3,192","meses_desde_primer_castigo":"<= 20","edad_num":"(36, 50]","puntuacion_cal_cat":"> 6"}),
 (4003,610.95,"G5",{"max_dias_mora_castigo":"> 3,192","meses_desde_primer_castigo":"<= 20","edad_num":"(28, 36]","saldo_fdp_tot_txs_u3m":"> 3","puntuacion_cal_cat":"> 6"}),
 (11770,605.76,"G5",{"max_dias_mora_castigo":"> 3,192","meses_desde_primer_castigo":"<= 20","edad_num":"(32, 36]","saldo_fdp_tot_txs_u3m":"<= 3","puntuacion_cal_cat":"> 6"}),
 (10084,603.39,"G5",{"max_dias_mora_castigo":"> 3,192","meses_desde_primer_castigo":"<= 20","edad_num":"(28, 32]","saldo_fdp_tot_txs_u3m":"<= 3","puntuacion_cal_cat":"> 6"}),
 (3316,592.71,"G5",{"max_dias_mora_castigo":"> 3,192","meses_desde_primer_castigo":"<= 20","edad_num":"<= 28","saldo_fdp_tot_txs_u3m":"> 3","puntuacion_cal_cat":"> 6"}),
 (18127,584.02,"G5",{"max_dias_mora_castigo":"> 3,192","meses_desde_primer_castigo":"<= 20","edad_num":"<= 28","saldo_fdp_tot_txs_u3m":"<= 3","puntuacion_cal_cat":"> 6"}),
]

# ---- estructura interna de cada hoja ----
leaves = []
for n, sc, q, conds in RAW:
    iv = {v: parse(v, s) for v, s in conds.items()}
    leaves.append({"n": n, "sc": sc, "q": q, "iv": iv, "conds": conds})

SMIN = min(l["sc"] for l in leaves)
SMAX = max(l["sc"] for l in leaves)

def color(sc):
    t = (sc - SMIN) / (SMAX - SMIN) if SMAX > SMIN else 0.5
    t = max(0.0, min(1.0, t))
    if t < 0.5:
        f = t / 0.5; r = 215 + (255 - 215) * f; g = 48 + (255 - 48) * f; b = 39 + (191 - 39) * f
    else:
        f = (t - 0.5) / 0.5; r = 255 + (26 - 255) * f; g = 255 + (152 - 255) * f; b = 191 + (80 - 191) * f
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def fmt(t):
    return f"{int(t):,}" if float(t).is_integer() else f"{t:g}"

def blab(var, t, side):
    if var == "puntuacion_cal_cat":
        return f"cat_score ≤ {int(t-0.5)}" if side == "L" else f"cat_score ≥ {int(t+0.5)}"
    name = DISP.get(var, var)
    return f"{name} ≤ {fmt(t)}" if side == "L" else f"{name} > {fmt(t)}"

def best_split(ls):
    """Devuelve (var, t, left, right) reconstruyendo un split binario consistente."""
    vars_all = set().union(*[set(l["iv"]) for l in ls])
    cands = []
    for var in vars_all:
        act = sum(1 for l in ls if var in l["iv"])      # hojas que usan la variable
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
    if not cands:
        return None
    cands.sort(reverse=True)                              # más usada, luego más balanceada
    _, _, var, t, left, right = cands[0]
    return var, t, left, right

_id = [0]
def build(ls):
    n = sum(l["n"] for l in ls)
    sc = sum(l["sc"] * l["n"] for l in ls) / n
    if len(ls) == 1:
        l = ls[0]
        regla = " · ".join(f"{DISP.get(v,v)} {s}".replace("puntuacion_cal_cat", "cat_score")
                           for v, s in l["conds"].items())
        chip = f'<span class="chip" style="background:{color(l["sc"])}">{l["sc"]:.0f}</span>'
        return (f'<div class="leaf" data-rule="{regla}">{chip}'
                f'<span class="meta">n={l["n"]:,} · {100*l["n"]/TOTAL:.1f}% · {l["q"]}</span>'
                f'<div class="rule">{regla}</div></div>')
    sp = best_split(ls)
    if sp is None:
        return "".join(build([l]) for l in ls)
    var, t, left, right = sp
    _id[0] += 1; nid = _id[0]
    chip = f'<span class="chip" style="background:{color(sc)}">{sc:.0f}</span>'
    head = (f'<summary><span class="tw">▸</span>{chip}'
            f'<span class="meta">n={n:,} · {100*n/TOTAL:.1f}% · score medio {sc:.0f}</span></summary>')
    kids = (f'<div class="branch"><div class="cond yes">{blab(var,t,"L")}</div>{build(left)}</div>'
            f'<div class="branch"><div class="cond no">{blab(var,t,"R")}</div>{build(right)}</div>')
    return f'<details open class="node">{head}<div class="kids">{kids}</div></details>'

TREE = build(leaves)

HTML = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Árbol de segmentación — Escenario Global</title>
<style>
 *{{box-sizing:border-box;margin:0;padding:0}}
 body{{font-family:"Segoe UI",Roboto,Arial,sans-serif;background:#0e1a17;color:#10241f;padding:0}}
 header{{background:linear-gradient(90deg,#007a72,#00a499);color:#fff;padding:18px 28px;
   display:flex;align-items:center;gap:20px;flex-wrap:wrap;position:sticky;top:0;z-index:10}}
 header h1{{font-size:22px}} header .s{{opacity:.9;font-size:14px}}
 .tools{{margin-left:auto;display:flex;gap:10px;align-items:center;flex-wrap:wrap}}
 .tools button,.tools input{{border:none;border-radius:18px;padding:8px 14px;font-size:13px;cursor:pointer}}
 .tools button{{background:#ffffff22;color:#fff;border:1px solid #ffffff55}}
 .tools button:hover{{background:#ffffff33}}
 .tools input{{cursor:text;min-width:180px}}
 .legend{{display:flex;align-items:center;gap:8px;font-size:13px;color:#fff}}
 .grad{{width:140px;height:12px;border-radius:6px;background:linear-gradient(90deg,#d73027,#ffffbf,#1a9850)}}
 .wrap{{padding:24px 30px 60px;background:#f4f7f6;min-height:100vh}}
 details.node{{margin:4px 0 4px 0}}
 .kids{{margin-left:26px;border-left:2px dashed #b9ccc7;padding-left:18px}}
 summary{{list-style:none;cursor:pointer;display:inline-flex;align-items:center;gap:10px;
   background:#fff;border:1px solid #e0e9e6;border-radius:10px;padding:7px 12px;box-shadow:0 2px 6px #0000000d}}
 summary::-webkit-details-marker{{display:none}}
 .tw{{transition:.2s;color:#00a499;font-weight:700}}
 details[open]>summary .tw{{transform:rotate(90deg)}}
 .branch{{margin-top:8px}}
 .cond{{display:inline-block;font-family:Consolas,monospace;font-size:12.5px;font-weight:600;
   padding:3px 10px;border-radius:14px;margin-bottom:4px}}
 .cond.yes{{background:#e3f4ec;color:#1a7a4a}} .cond.no{{background:#fdecea;color:#b23b30}}
 .chip{{color:#10241f;font-weight:800;border-radius:8px;padding:3px 10px;font-size:13px;min-width:44px;text-align:center;display:inline-block}}
 .meta{{font-size:13px;color:#5b6f6a}}
 .leaf{{display:flex;align-items:center;gap:10px;background:#fff;border:1px solid #e6efec;
   border-radius:10px;padding:7px 12px;margin:6px 0;flex-wrap:wrap}}
 .leaf .rule{{flex-basis:100%;font-family:Consolas,monospace;font-size:11.5px;color:#46615b;display:none}}
 .leaf:hover .rule{{display:block}}
 .leaf:hover{{box-shadow:0 4px 12px #00a49955;border-color:#00a499}}
 .hidden{{display:none !important}}
 .hl{{outline:3px solid #f1c40f}}
</style></head><body>
<header>
  <div><h1>🌳 Árbol de segmentación — Escenario Global</h1>
  <div class="s">2.28 M clientes · 74 segmentos · objetivo = score · pasa el cursor sobre una hoja para ver su regla completa</div></div>
  <div class="tools">
    <span class="legend">menor score <span class="grad"></span> mayor score</span>
    <button onclick="setAll(true)">Expandir todo</button>
    <button onclick="setAll(false)">Colapsar todo</button>
    <input id="q" placeholder="resaltar variable… (ej. edad)" oninput="filtra(this.value)">
  </div>
</header>
<div class="wrap">{TREE}</div>
<script>
 function setAll(o){{document.querySelectorAll('details').forEach(d=>d.open=o);}}
 function filtra(txt){{
   txt=txt.trim().toLowerCase();
   document.querySelectorAll('.leaf').forEach(l=>{{
     const r=(l.dataset.rule||'').toLowerCase();
     l.classList.toggle('hl', txt && r.includes(txt));
   }});
   if(txt) setAll(true);
 }}
</script>
</body></html>"""

with open("arbol_interactivo_global.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print("OK ->", len(leaves), "hojas | score", round(SMIN), "-", round(SMAX))
