# -*- coding: utf-8 -*-
"""
Segmentación de riesgo (objetivo SCORE) con optbinning (WoE) + árbol monótono.

CAMBIO CLAVE vs versión previa:
  - Bloque (3b) PODA: tras el primer fit, el árbol se RE-ENTRENA usando SOLO las
    variables con importancia > 0. Así el modelo guardado (.pkl) NO exige columnas
    que no aparecen en ninguna regla (p.ej. saldo_pasivo_componentes_u3m al scorear).
Se conservan tus fixes previos:
  - _fmt_num / fmt_intervalo con TODOS los decimales (reglas en Excel y en el pkl).
  - hoja_estrategia con TOP_N_ESTRATEGIAS = 0 -> muestra TODAS las estrategias.
"""

import numpy as np
import pandas as pd
import joblib
from io import BytesIO
import matplotlib.pyplot as plt
from scipy.stats import spearmanr
from sklearn.tree import DecisionTreeRegressor, plot_tree
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image as XLImage

# ====================================================================================
# CONFIGURACIÓN
# ====================================================================================
OBJETIVO  = "SCORE"                         # "RD" ó "SCORE"  (no hay RD -> proxy = puntaje)
DATA_PATH = ""
RD_COL    = "rd"
SCORE_COL = "puntaje_mod"                   # a MAYOR score, MENOR riesgo
SIT_COL   = "sit_lab_ap"
SIT_CAL_COL = "sit_laboral_mod"             # situación laboral para puntuacion_cal_cat
CAL_COL   = "puntuacion_cal_cat"
FLG_COL   = "FLG_CAST_AP"
FAR_COL   = ""
VALORES_FLG = ['CAST_NOIBK_REP>=5anios']

APETITO_RD    = 0.02
APETITO_SCORE = 730
FACTORES = [0.90, 0.95, 1.00, 1.05, 1.10]

VARS_DIRECTAS = []

NUM_VARS = [
    "deuda_cas", "monto_castigado_total", "monto_castigado_ibk", "monto_castigado_otros",
    "nro_entidades_castigo",
    #"nro_entidades_castigo_vida",
    #"max_dias_mora_castigo",
    "meses_desde_ultimo_castigo", "meses_desde_primer_castigo",
    "edad_num", "rk_ing_num",
    #"saldo_fdp_tot_txs_um", "saldo_fdp_tot_txs_u3m", "saldo_fdp_tot_txs_u6m",
    #"saldo_prom_tot_txs_um", "saldo_prom_tot_txs_u3m", "saldo_prom_tot_txs_u6m",
    #"saldo_fdp_tot_planilla_um", "saldo_fdp_tot_planilla_u3m", "saldo_fdp_tot_planilla_u6m",
    #"saldo_prom_tot_planilla_um", "saldo_prom_tot_planilla_u3m", "saldo_prom_tot_planilla_u6m",
    #"saldo_fdp_tot_tc_um", "saldo_fdp_tot_tc_u3m", "saldo_fdp_tot_tc_u6m",
    #"saldo_prom_tot_tc_um", "saldo_prom_tot_tc_u3m", "saldo_prom_tot_tc_u6m",
    "saldo_prom_tot_pasivo_um", "saldo_prom_tot_pasivo_u3m", "saldo_prom_tot_pasivo_u6m",
    "saldo_prom_tot_pasivo_max_u6m", "saldo_pasivo_componentes_u3m",
    "saldo_pasivo_actual", "saldo_prom_pasivo", "saldo_activo_actual", "prom_saldo_pasivo_u4m",
    #"ratio_tc_pasivo_u3m", "ratio_planilla_pasivo_u3m", "ratio_txs_pasivo_u3m",
    "var_pasivo_um_vs_u6m",
    #"flg_colaborador_um", "flg_cliente_cts_um", "flg_cliente_inversion_um",
    #"flg_cliente_millonaria_um", "flg_cliente_alcancia_um", "flg_cliente_planilla_um",
    "puntuacion_cal_cat", 'sexo',
    'nivel_profesional',
    'tipinstitucion',
]
ORD_VAR = "segmentacion_gdp_v2"
VARS_EXCLUIR = ["edad_num"]

WOE_AL_ARBOL = True
SENTINEL  = -99999999
MAX_DEPTH = 6
MIN_SAMPLES_LEAF = 0.002
OPTB_SAMPLE = 3_000_000
RANDOM_STATE = 42
UMBRAL_MISSING_IMPUTA = 0                    # > este % de missing -> imputa con WoE del peor bin

# --- Binning por variable -----------------------------------------------------------
BINS_OBJETIVO = [7, 2]                       # genéricas: prueba 7, luego 2 bins
SALDO_MIN_BINS, SALDO_MAX_BINS = 2, 2        # variables de saldo: entre 2 y 3 bins
# puntuacion_cal_cat: se prueban estos dos esquemas de split (se usa el 1ro factible)
USER_SPLITS_CAL = [
    [1.5, 2.5, 3.5, 4.5, 5.5],
    [2.5, 3.5, 5.5],
]

# Cortes por situación laboral -> puntuacion_cal_cat (banda 1=mejor ... 6=peor)
CORTES = {
    "DEPENDIENTE":    [(1, 967), (2, 941), (3, 876)],
    "MIXTO":          [(1, 971), (2, 949), (3, 915), (4, 872), (5, 852)],
    "DEPEN_EXPERIAN": [(1, 971), (2, 949), (3, 915), (4, 872), (5, 852)],
    "INDEPENDIENTE":  [(1, 981), (2, 960), (3, 943), (4, 898), (5, 844)],
}

# Dirección monótona POR NEGOCIO frente al RIESGO. +1 = más var -> más riesgo | -1 = menos | 0 = ambigua
DIRECCION_NEGOCIO = {
    "deuda_cas": +1, "monto_castigado_total": +1, "monto_castigado_ibk": +1,
    "monto_castigado_otros": +1, "nro_entidades_castigo": +1, "nro_entidades_castigo_vida": +1,
    "max_dias_mora_castigo": +1,
    "meses_desde_ultimo_castigo": -1, "meses_desde_primer_castigo": -1,
    "edad_num": 0, "rk_ing_num": -1,
    "saldo_fdp_tot_txs_um": -1, "saldo_fdp_tot_txs_u3m": -1, "saldo_fdp_tot_txs_u6m": -1,
    "saldo_prom_tot_txs_um": -1, "saldo_prom_tot_txs_u3m": -1, "saldo_prom_tot_txs_u6m": -1,
    "saldo_fdp_tot_planilla_um": -1, "saldo_fdp_tot_planilla_u3m": -1, "saldo_fdp_tot_planilla_u6m": -1,
    "saldo_prom_tot_planilla_um": -1, "saldo_prom_tot_planilla_u3m": -1, "saldo_prom_tot_planilla_u6m": -1,
    "saldo_fdp_tot_tc_um": +1, "saldo_fdp_tot_tc_u3m": +1, "saldo_fdp_tot_tc_u6m": +1,
    "saldo_prom_tot_tc_um": +1, "saldo_prom_tot_tc_u3m": +1, "saldo_prom_tot_tc_u6m": +1,
    "saldo_prom_tot_pasivo_um": -1, "saldo_prom_tot_pasivo_u3m": -1, "saldo_prom_tot_pasivo_u6m": -1,
    "saldo_prom_tot_pasivo_max_u6m": -1, "saldo_pasivo_componentes_u3m": -1,
    "saldo_pasivo_actual": -1, "saldo_prom_pasivo": -1, "prom_saldo_pasivo_u4m": -1,
    "saldo_activo_actual": 0,
    "ratio_tc_pasivo_u3m": +1, "ratio_planilla_pasivo_u3m": -1, "ratio_txs_pasivo_u3m": 0,
    "var_pasivo_um_vs_u6m": -1,
    "flg_colaborador_um": -1, "flg_cliente_cts_um": -1, "flg_cliente_inversion_um": -1,
    "flg_cliente_millonaria_um": -1, "flg_cliente_alcancia_um": -1, "flg_cliente_planilla_um": -1,
    "flg_far_mto_trx_presencial_12m_c216": 0,
    "segmentacion_gdp_v2": +1, "puntuacion_cal_cat": +1, 'sexo': 0,
    'nivel_profesional': +1,
    'tipinstitucion': +1,
}

SUBJECT_COL = "subject_id"
TOP_N_ESTRATEGIAS = 0
LEADS_EN_EXCEL_MAX = 100_000

CMAP = plt.cm.RdYlGn
BORDER = Border(*[Side(style="thin", color="999999")] * 4)
BOLD = Font(bold=True)

# ---- Derivados del objetivo --------------------------------------------------------
_RD = (OBJETIVO.upper() == "RD")
TARGET_COL = RD_COL if _RD else SCORE_COL
SIGN = 1 if _RD else -1
APETITO = APETITO_RD if _RD else APETITO_SCORE
TGT = "RD" if _RD else "score"
OP = "<=" if _RD else ">="

_IMG_BUFS = []                               # mantiene vivos los buffers de imagen hasta wb.save


# ====================================================================================
# HELPERS
# ====================================================================================
def fmt_target(v):
    return f"{v:.4f}" if _RD else f"{v:,.0f}"


def norm_riesgo(v, vmin, vmax):
    lo, hi = SIGN * vmin, SIGN * vmax
    rmin, rmax = min(lo, hi), max(lo, hi)
    return 0.5 if rmax <= rmin else (rmax - SIGN * v) / (rmax - rmin)


def hex_color(t):
    r, g, b, _ = CMAP(float(np.clip(t, 0, 1)))
    return f"{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def fill_riesgo(v, vmin, vmax):
    return PatternFill("solid", fgColor=hex_color(norm_riesgo(v, vmin, vmax)))


def asignar_grupo(score, segmento):
    if pd.isna(score) or segmento not in CORTES:
        return None
    for banda, minimo in sorted(CORTES[segmento], key=lambda x: x[1], reverse=True):
        if score >= minimo:
            return banda
    return 6


def preparar_base(df):
    """Crea puntuacion_cal_cat a partir del score y la situación laboral."""
    df = df.copy()
    if SCORE_COL in df.columns and SIT_CAL_COL in df.columns:
        df[CAL_COL] = [asignar_grupo(s, seg) for s, seg in zip(df[SCORE_COL], df[SIT_CAL_COL])]
        df[CAL_COL] = pd.to_numeric(df[CAL_COL], errors="coerce")
        print(f"  [preparar] {CAL_COL} creada (no nulos: {df[CAL_COL].notna().sum():,})")
    else:
        print(f"  [preparar] AVISO: faltan '{SCORE_COL}' o '{SIT_CAL_COL}', no se creó {CAL_COL}")
    return df


def _fmt_num(x):
    """Formatea con separador de miles y TODOS los decimales (sin ceros de relleno)."""
    x = round(float(x), 6)                      # evita ruido de punto flotante
    s = f"{x:,.6f}".rstrip("0").rstrip(".")
    return s if s not in ("", "-0") else "0"


def fmt_intervalo(lo, hi):
    if hi < -1e7:
        return "Missing"
    if lo < -1e7:
        lo = -np.inf
    if lo == -np.inf and hi == np.inf:
        return "(todos)"
    if lo == -np.inf:
        return f"<= {_fmt_num(hi)}"
    if hi == np.inf:
        return f"> {_fmt_num(lo)}"
    return f"({_fmt_num(lo)}, {_fmt_num(hi)}]"


def _parse_bin(s):
    s = str(s).strip()
    if s in ("Special", "Missing", "", "nan"):
        return None
    s = s.strip("[]()")
    if "," not in s:
        return None
    a, b = s.split(",", 1)

    def f(z):
        z = z.strip()
        if "inf" in z:
            return -np.inf if z.startswith("-") else np.inf
        try:
            return float(z)
        except ValueError:
            return None
    lo, hi = f(a), f(b)
    return None if lo is None or hi is None else (lo, hi)


def labelmap_from_table(tb, valcol):
    vbins, miss_val = [], None
    for _, row in tb.iterrows():
        b = str(row["Bin"])
        val = pd.to_numeric(row.get(valcol), errors="coerce")
        if b == "Missing":
            if pd.notna(val) and row.get("Count", 0) > 0:
                miss_val = float(val)
            continue
        pr = _parse_bin(b)
        if pr is None or pd.isna(val):
            continue
        vbins.append((float(val), pr[0], pr[1]))
    vbins.sort(key=lambda z: z[0])
    return {"vbins": vbins, "miss_val": miss_val}


def cond_label(woemap, var, lo, hi):
    if var not in woemap:
        return fmt_intervalo(lo, hi)
    info = woemap[var]
    vb, mv = info["vbins"], info["miss_val"]
    sel = [(low, high) for (w, low, high) in vb if (w > lo and w <= hi)]
    inc_miss = (mv is not None and mv > lo and mv <= hi)
    total = len(vb) + (1 if mv is not None else 0)
    if len(sel) + (1 if inc_miss else 0) >= total:
        return "(todos)"
    partes = []
    if sel:
        partes.append(fmt_intervalo(min(l for l, _ in sel), max(h for _, h in sel)))
    if inc_miss:
        partes.append("Missing")
    return " + ".join(partes) if partes else "(ninguno)"


def reglas_por_hoja(tree, feats):
    t = tree.tree_
    out, stack = {}, [(0, {})]
    while stack:
        node, conds = stack.pop()
        if t.children_left[node] == -1:
            out[node] = conds
            continue
        f, thr = feats[t.feature[node]], t.threshold[node]
        lo, hi = conds.get(f, (-np.inf, np.inf))
        izq = dict(conds); izq[f] = (lo, min(hi, thr))
        der = dict(conds); der[f] = (max(lo, thr), hi)
        stack += [(t.children_left[node], izq), (t.children_right[node], der)]
    return out


def optbinning_fit(x, y, nombre, direccion):
    """Devuelve (feasible, etiqueta, tabla, dir_ef, optb)."""
    from optbinning import ContinuousOptimalBinning
    trend = {1: "ascending", -1: "descending", 0: "auto_asc_desc"}[direccion]
    etiqueta = {1: f"CRECIENTE {TGT} (+)", -1: f"DECRECIENTE {TGT} (-)", 0: "auto"}[direccion]
    if (~np.isnan(x)).sum() < 50:
        return False, "sin datos -> descartada", None, 0, None

    if nombre == CAL_COL:
        intentos = [dict(user_splits=np.array(sp, float), min_n_bins=2,
                         max_n_bins=len(sp) + 1) for sp in USER_SPLITS_CAL]
    elif "saldo" in nombre:
        intentos = [dict(min_n_bins=SALDO_MIN_BINS, max_n_bins=SALDO_MAX_BINS),
                    dict(min_n_bins=2, max_n_bins=2)]
    else:
        intentos = [dict(min_n_bins=mb, max_n_bins=max(mb, 8)) for mb in BINS_OBJETIVO]

    optb = None
    for kw in intentos:
        try:
            o = ContinuousOptimalBinning(name=nombre, monotonic_trend=trend, **kw)
            o.fit(x, y)
            if o.status in ("OPTIMAL", "FEASIBLE") and len(o.splits) >= (kw.get("min_n_bins", 2) - 1):
                optb = o
                break
        except Exception:
            continue
    if optb is None:
        return False, etiqueta + " -> SIN BINARIZACIÓN, descartada", None, 0, None

    n_bins = len(optb.splits) + 1
    tb = optb.binning_table.build()
    if direccion != 0:
        dir_ef = direccion
    else:
        mask = ~tb["Bin"].astype(str).isin(["Special", "Missing", ""])
        means = pd.to_numeric(tb.loc[mask, "Mean"], errors="coerce").dropna().values
        dir_ef = (1 if means[-1] >= means[0] else -1) if len(means) >= 2 else 0
        etiqueta = (f"CRECIENTE {TGT} (+)" if dir_ef > 0 else f"DECRECIENTE {TGT} (-)") + " (detectada)"
    return True, f"{etiqueta} [{n_bins} bins]", tb, dir_ef, optb


def escribir_cuadro(ws, r0, c0, titulo, tab, vfil, vcol, modo, vmin=None, vmax=None):
    ws.cell(r0, c0, titulo).font = Font(bold=True, size=12)
    ws.cell(r0 + 1, c0 + 1, vcol).font = BOLD
    ws.cell(r0 + 2, c0, vfil).font = BOLD
    for j, col in enumerate(tab.columns):
        c = ws.cell(r0 + 2, c0 + 1 + j, str(col))
        c.font = BOLD; c.border = BORDER
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    mx = np.nanmax(tab.values) if tab.size else 1
    for i, fila in enumerate(tab.index):
        rc = ws.cell(r0 + 3 + i, c0, str(fila)); rc.font = BOLD; rc.border = BORDER
        for j in range(len(tab.columns)):
            val = tab.iloc[i, j]
            cell = ws.cell(r0 + 3 + i, c0 + 1 + j)
            cell.border = BORDER; cell.alignment = Alignment(horizontal="center")
            if pd.isna(val):
                continue
            if modo == "riesgo":
                cell.value = round(float(val), 4)
                cell.fill = fill_riesgo(val, vmin, vmax)
            else:
                cell.value = int(val)
                g = int(255 - 120 * (val / mx if mx else 0))
                cell.fill = PatternFill("solid", fgColor=f"D6E4{g:02X}")
    ws.column_dimensions[get_column_letter(c0)].width = 26
    for j in range(len(tab.columns)):
        ws.column_dimensions[get_column_letter(c0 + 1 + j)].width = 16
    return r0 + 4 + len(tab.index)


def escribir_tabla_df(ws, r0, c0, titulo, df):
    if titulo:
        ws.cell(r0, c0, titulo).font = BOLD
        r0 += 1
    cols = list(df.columns)
    for j, h in enumerate(cols):
        cc = ws.cell(r0, c0 + j, str(h)); cc.font = BOLD; cc.border = BORDER
    for i in range(len(df)):
        for j, h in enumerate(cols):
            v = df.iloc[i][h]
            cell = ws.cell(r0 + 1 + i, c0 + j); cell.border = BORDER
            if isinstance(v, (int, float, np.integer, np.floating)) and not pd.isna(v):
                cell.value = round(float(v), 5)
            else:
                cell.value = str(v)
    return r0 + 2 + len(df)


def ejes_unicos(labels):
    vistos, out = {}, []
    for l in labels:
        if l in vistos:
            vistos[l] += 1
            out.append(l + " " * vistos[l])
        else:
            vistos[l] = 0
            out.append(l)
    return out


# ====================================================================================
# PROCESA UN ESCENARIO -> UNA HOJA
# ====================================================================================
def procesar_escenario(wb, nombre, df_sc, metodologia, excluir=()):
    ws = wb.create_sheet(title=nombre[:31])
    df_sc = df_sc.loc[pd.to_numeric(df_sc[TARGET_COL], errors="coerce").notna()].reset_index(drop=True)
    n = len(df_sc)
    if n < 50:
        ws.cell(1, 1, f"Escenario con muy pocos casos ({n}). Se omite.")
        return None, None

    y = pd.to_numeric(df_sc[TARGET_COL], errors="coerce").values
    vmin, vmax = np.nanmin(y), np.nanmax(y)

    # ----- 1) Predictores -----
    num = [c for c in NUM_VARS if c in df_sc.columns and c not in excluir and c != TARGET_COL]
    raw = {c: pd.to_numeric(df_sc[c], errors="coerce") for c in num}
    feats = list(num)
    if ORD_VAR in df_sc.columns:
        raw[ORD_VAR] = df_sc[ORD_VAR].map({f"G{i}": i for i in range(1, 9)})
        feats.append(ORD_VAR)
    for c in VARS_DIRECTAS:
        if c in df_sc.columns and c not in excluir and c != TARGET_COL and c not in feats:
            raw[c] = pd.to_numeric(df_sc[c], errors="coerce")
            feats.append(c)

    # ----- 2) Dirección + (B) WoE/binning con imputación de missing -----
    usa_woe = (metodologia == "B" and WOE_AL_ARBOL)
    Xcols, misscol, cst_map, woemap, tablas, drop = {}, {}, {}, {}, [], []
    optbs_guardados, imputados = {}, {}
    samp = (df_sc.sample(OPTB_SAMPLE, random_state=RANDOM_STATE).index
            if (metodologia == "B" and n > OPTB_SAMPLE) else df_sc.index)
    y_s = pd.Series(y, index=df_sc.index)
    for c in feats:
        serie = raw[c]
        risk_dir = DIRECCION_NEGOCIO.get(c, 0)
        tgt_dir = risk_dir * SIGN
        if metodologia == "B" and c in NUM_VARS:
            feasible, etiqueta, tb, dir_ef, optb = optbinning_fit(
                serie.loc[samp].values, y_s.loc[samp].values, c, tgt_dir)
            tablas.append((c, etiqueta, tb))
            if not feasible:
                drop.append(c)
                continue
            if usa_woe:
                try:
                    col = optb.transform(serie.values, metric="woe"); valcol = "WoE"
                except Exception:
                    col = optb.transform(serie.values, metric="mean"); valcol = "Mean"
                col = np.asarray(col, dtype=float)
                woemap[c] = labelmap_from_table(tb, valcol)
                # imputar missings con el WoE del bin de MAYOR riesgo
                miss_mask = serie.isna().values
                if miss_mask.mean() > UMBRAL_MISSING_IMPUTA and woemap[c]["vbins"]:
                    woes = [w for (w, _, _) in woemap[c]["vbins"]]
                    woe_peor = max(woes) if SIGN == 1 else min(woes)
                    col[miss_mask] = woe_peor
                    imputados[c] = woe_peor
                    woemap[c]["miss_val"] = None
                Xcols[c] = col
                cst_map[c] = +1
                misscol[c] = np.zeros(n, dtype=bool)
                optbs_guardados[c] = optb
            else:
                Xcols[c] = serie.fillna(SENTINEL).values
                cst_map[c] = dir_ef
                misscol[c] = serie.isna().values
                optbs_guardados[c] = optb
        else:
            if risk_dir != 0:
                cst_map[c] = tgt_dir
            else:
                ok = serie.notna()
                if ok.sum() < 30:
                    cst_map[c] = 0
                else:
                    rho, p = spearmanr(serie[ok], y[ok.values])
                    cst_map[c] = 0 if (np.isnan(rho) or p > 0.05) else int(np.sign(rho))
            Xcols[c] = serie.fillna(SENTINEL).values
            misscol[c] = serie.isna().values

    feats = [c for c in feats if c not in drop]
    X = pd.DataFrame({c: Xcols[c] for c in feats})
    miss = pd.DataFrame({c: misscol[c] for c in feats})
    cst = [cst_map[c] for c in feats]

    # ----- 3) Árbol monótono -----
    try:
        tree = DecisionTreeRegressor(max_depth=MAX_DEPTH, min_samples_leaf=MIN_SAMPLES_LEAF,
                                     monotonic_cst=cst, random_state=RANDOM_STATE).fit(X, y)
    except (TypeError, ValueError):
        tree = DecisionTreeRegressor(max_depth=MAX_DEPTH, min_samples_leaf=MIN_SAMPLES_LEAF,
                                     random_state=RANDOM_STATE).fit(X, y)

    # ----- 3b) PODA: re-entrenar SOLO con variables que el árbol usa (importancia > 0)
    #          -> el modelo guardado NO exigirá columnas que no salen en ninguna regla
    #             (p.ej. saldo_pasivo_componentes_u3m al hacer scoring).
    usadas_idx = [i for i in range(len(feats)) if tree.feature_importances_[i] > 0]
    if usadas_idx and len(usadas_idx) < len(feats):
        feats = [feats[i] for i in usadas_idx]
        cst   = [cst[i]   for i in usadas_idx]
        X      = X[feats]
        miss   = miss[feats]
        # filtra TODO lo que se guarda en el modelo a las variables realmente usadas
        woemap          = {c: woemap[c]          for c in feats if c in woemap}
        optbs_guardados = {c: optbs_guardados[c] for c in feats if c in optbs_guardados}
        imputados       = {c: imputados[c]       for c in feats if c in imputados}
        misscol         = {c: misscol[c]         for c in feats if c in misscol}
        # re-entrena con el set reducido (mismo random_state -> mismas reglas)
        try:
            tree = DecisionTreeRegressor(max_depth=MAX_DEPTH, min_samples_leaf=MIN_SAMPLES_LEAF,
                                         monotonic_cst=cst, random_state=RANDOM_STATE).fit(X, y)
        except (TypeError, ValueError):
            tree = DecisionTreeRegressor(max_depth=MAX_DEPTH, min_samples_leaf=MIN_SAMPLES_LEAF,
                                         random_state=RANDOM_STATE).fit(X, y)

    # ----- 4) Imagen en memoria (sin guardar PNG en disco) -----
    t_ = tree.tree_
    plt.figure(figsize=(26, 12))
    anns = plot_tree(tree, feature_names=feats, filled=True, rounded=True,
                     impurity=False, precision=4, fontsize=9, proportion=True)
    for i in range(t_.node_count):
        ann = anns[i]
        if ann.get_bbox_patch() is not None:
            ann.get_bbox_patch().set_facecolor(CMAP(norm_riesgo(t_.value[i][0][0], vmin, vmax)))
            ann.get_bbox_patch().set_edgecolor("black")
        if t_.children_left[i] != -1:
            var = feats[t_.feature[i]]
            cond = cond_label(woemap, var, -np.inf, t_.threshold[i])
            lineas = ann.get_text().split("\n")
            lineas[0] = f"{var}\n{cond}"
            ann.set_text("\n".join(lineas))
    verde = "RD bajo" if _RD else "score alto"
    rojo = "RD alto" if _RD else "score bajo"
    plt.title(f"Árbol — verde = {verde} (menor riesgo), rojo = {rojo}  (cortes = rangos de bins; izq = se cumple)")
    plt.tight_layout()
    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close()
    buf.seek(0)
    _IMG_BUFS.append(buf)

    # ----- 5) Encabezado + imagen -----
    metnom = "Solo árbol" if metodologia == "A" else ("Optbinning + árbol (WoE al árbol)" if usa_woe else "Optbinning + árbol")
    ws.cell(1, 1, f"ESCENARIO: {nombre}").font = Font(bold=True, size=14)
    ws.cell(2, 1, f"n = {n:,}   |   {TGT} medio = {fmt_target(np.nanmean(y))}   |   objetivo = {TGT}   |   metodología = {metnom}")
    ws.cell(3, 1, f"monotonic_cst: {dict(zip(feats, cst))}")
    try:
        img = XLImage(buf); img.width, img.height = 1100, 520
        ws.add_image(img, "A5")
    except Exception as e:
        ws.cell(5, 1, f"(no se pudo insertar imagen: {e})")

    # ----- 6) Cuadros de doble entrada (top-2 variables) -----
    imp = pd.Series(tree.feature_importances_, index=feats).sort_values(ascending=False)
    top = [v for v in imp.index if imp[v] > 0][:2]
    for v in feats:
        if len(top) >= 2:
            break
        if v not in top:
            top.append(v)
    vfil, vcol = top[0], top[1]

    cuadro = {}
    for var in (vfil, vcol):
        idx = feats.index(var)
        es_woe = var in woemap
        thr = sorted({round(t, 6) for f, t in zip(tree.tree_.feature, tree.tree_.threshold)
                      if f == idx and (es_woe or t > SENTINEL / 2)})
        edges = [-np.inf] + thr + [np.inf]
        labels = ejes_unicos([cond_label(woemap, var, e0, e1) for e0, e1 in zip(edges[:-1], edges[1:])])
        b = pd.cut(X[var], bins=edges, labels=labels).astype(object)
        if not es_woe:
            b[miss[var].values] = "Missing"
        cuadro[var] = (b, labels)
    bf, lab_f = cuadro[vfil]
    bc, lab_c = cuadro[vcol]
    ord_f = lab_f + (["Missing"] if (bf == "Missing").any() else [])
    ord_c = lab_c + (["Missing"] if (bc == "Missing").any() else [])
    base = pd.DataFrame({"f": bf, "c": bc, "s": y})
    cant = base.pivot_table(index="f", columns="c", values="s", aggfunc="count").reindex(ord_f, axis=0).reindex(ord_c, axis=1)
    riesgo = base.pivot_table(index="f", columns="c", values="s", aggfunc="mean").reindex(ord_f, axis=0).reindex(ord_c, axis=1)

    fila = 34
    fila = escribir_cuadro(ws, fila, 1, "CUADRO POR CANTIDAD", cant, vfil, vcol, "cantidad") + 2
    fila = escribir_cuadro(ws, fila, 1, f"CUADRO POR RIESGO ({TGT} promedio)", riesgo,
                           vfil, vcol, "riesgo", vmin, vmax) + 2

    # ----- 6b) Importancia de variables -----
    ws.cell(fila, 1, "IMPORTANCIA DE VARIABLES (peso en el árbol)").font = Font(bold=True, size=12)
    for j, h in enumerate(["Variable", "Peso", "Peso %"]):
        c = ws.cell(fila + 1, 1 + j, h); c.font = BOLD; c.border = BORDER
    for i, (var, w) in enumerate(imp.items()):
        ws.cell(fila + 2 + i, 1, var).border = BORDER
        ws.cell(fila + 2 + i, 2, round(float(w), 4)).border = BORDER
        ws.cell(fila + 2 + i, 3, round(float(w) * 100, 1)).border = BORDER
    fila = fila + 3 + len(imp)

    # ----- 7) Cuadro del árbol completo -----
    leafmap = reglas_por_hoja(tree, feats)
    usadas = [f for f in feats if any(f in cond for cond in leafmap.values())]
    leaf_id = tree.apply(X)
    rv = pd.Series(SIGN * y, index=df_sc.index)
    try:
        quint_v = pd.qcut(rv, 5, labels=["G1", "G2", "G3", "G4", "G5"])
    except ValueError:
        quint_v = pd.qcut(rv.rank(method="first"), 5, labels=["G1", "G2", "G3", "G4", "G5"])
    res = pd.DataFrame({"leaf": leaf_id, "s": y, "quint": quint_v.values})

    col_med = f"{TGT}_medio"
    filas = []
    for lid, sub in res.groupby("leaf"):
        cond = leafmap.get(lid, {})
        row = {f: cond_label(woemap, f, *cond.get(f, (-np.inf, np.inf))) for f in usadas}
        row["n"] = len(sub)
        row["%"] = round(100 * len(sub) / n, 1)
        row[col_med] = sub["s"].mean()
        row["quintil"] = sub["quint"].mode().iloc[0] if not sub["quint"].mode().empty else ""
        filas.append(row)
    tab = pd.DataFrame(filas).sort_values(col_med, ascending=_RD).reset_index(drop=True)

    ws.cell(fila, 1, "CUADRO DEL ÁRBOL COMPLETO (una fila = una hoja, ordenado por menor riesgo)").font = Font(bold=True, size=12)
    cols = usadas + ["n", "%", col_med, "quintil"]
    for j, h in enumerate(cols):
        c = ws.cell(fila + 1, 1 + j, h); c.font = BOLD; c.border = BORDER
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    for i in range(len(tab)):
        for j, h in enumerate(cols):
            cell = ws.cell(fila + 2 + i, 1 + j); cell.border = BORDER
            cell.alignment = Alignment(horizontal="center")
            val = tab.iloc[i][h]
            if h == col_med:
                cell.value = round(float(val), 4)
                cell.fill = fill_riesgo(val, vmin, vmax)
            elif h in ("n", "%"):
                cell.value = float(val) if h == "%" else int(val)
            else:
                cell.value = str(val)
    for j, h in enumerate(cols):
        ws.column_dimensions[get_column_letter(1 + j)].width = 20 if h in usadas else 11
    fila = fila + 3 + len(tab)

    # ----- 8) (B) TABLA optbinning por variable -----
    if tablas:
        fila += 2
        ws.cell(fila, 1, f"TABLA OPTBINNING POR VARIABLE (bin · WoE · {TGT} medio)").font = Font(bold=True, size=12)
        fila += 1
        for nom, etiqueta, tb in tablas:
            ws.cell(fila, 1, f"{nom}  —  {etiqueta}").font = BOLD
            if tb is not None:
                fila = escribir_tabla_df(ws, fila + 1, 1, "", tb) + 1
            else:
                fila += 2

    # ----- 9) Leads + regla por hoja -----
    leaf_val = res.groupby("leaf")["s"].mean().to_dict()
    regla_txt = {}
    for lid, cond in leafmap.items():
        partes = [f"{f} {cond_label(woemap, f, *rng)}" for f, rng in cond.items()
                  if cond_label(woemap, f, *rng) != "(todos)"]
        regla_txt[lid] = " & ".join(partes) if partes else "(raíz)"
    sid = df_sc[SUBJECT_COL].values if SUBJECT_COL in df_sc.columns else df_sc.index.values
    leads = pd.DataFrame({
        "subject_id": sid, "escenario": nombre,
        "leaf_key": [f"{nombre}#{l}" for l in leaf_id],
        "regla": [regla_txt.get(l, "") for l in leaf_id],
        "val_cliente": y, "leaf_val": [leaf_val.get(l, np.nan) for l in leaf_id],
    })
    risk_tope = max(SIGN * APETITO * f for f in FACTORES)
    leads = leads[SIGN * leads["leaf_val"] <= risk_tope].reset_index(drop=True)

    modelo_sc = {
        "tree": tree, "feats": feats, "cst": dict(zip(feats, cst)),
        "optbs": optbs_guardados, "usa_woe": usa_woe, "imputa_missing": imputados,
        "woemap": woemap, "leafmap": leafmap, "leaf_val": leaf_val, "regla_txt": regla_txt,
    }
    return leads, modelo_sc


# ====================================================================================
# ORQUESTACIÓN
# ====================================================================================
def construir_escenarios(df):
    flg = FLG_COL if (FLG_COL and FLG_COL in df.columns) else ""
    if (not flg) and VALORES_FLG:
        for c in df.columns:
            if (not pd.api.types.is_numeric_dtype(df[c])) and df[c].isin(VALORES_FLG).any():
                flg = c
                print(f"  [escenarios] columna de segmento autodetectada: '{flg}'")
                break
    grupos = ([(v.replace(">=", "ge").replace("=", "").replace("/", "_")[:24], df[df[flg] == v])
               for v in VALORES_FLG]
              if (flg and VALORES_FLG) else [("TODOS", df)])
    out = []
    for nombre, base in grupos:
        out.append((nombre, base))
        if FAR_COL and FAR_COL in df.columns:
            far = base[pd.to_numeric(base[FAR_COL], errors="coerce") == 1]
            if len(far):
                out.append((f"{nombre}_far1"[:28], far))
    return out


def _dedup(pool):
    return (pool.assign(_risk=SIGN * pool["leaf_val"])
            .sort_values("_risk", ascending=True).drop_duplicates("subject_id", keep="first")
            .drop(columns="_risk"))


def hoja_estrategia(wb, leads_total, ruta):
    ws = wb.create_sheet("Estrategia")
    if leads_total.empty:
        ws.cell(1, 1, f"No hay segmentos que cumplan {TGT} {OP} apetito en los escenarios.")
        return {}

    ded = _dedup(leads_total)
    seg = (ded.groupby("leaf_key")
           .agg(escenario=("escenario", "first"), regla=("regla", "first"),
                val=("leaf_val", "first"), n_leads=("subject_id", "size"))
           .reset_index())
    seg["risk"] = SIGN * seg["val"]
    seg = seg.sort_values("risk", ascending=True).reset_index(drop=True)
    if TOP_N_ESTRATEGIAS and TOP_N_ESTRATEGIAS > 0:        # si es 0/None -> TODAS
        seg = seg.head(TOP_N_ESTRATEGIAS)
    seg = seg.reset_index(drop=True)

    seg.insert(0, "estrategia", range(1, len(seg) + 1))
    vmn, vmx = seg["val"].min(), seg["val"].max()
    escen = sorted(((f, APETITO * f, SIGN * APETITO * f) for f in FACTORES), key=lambda z: z[2])

    ws.cell(1, 1, f"HOJA DE ESTRATEGIA — objetivo = {TGT} | apetito base = {fmt_target(APETITO)} "
                  f"(un segmento entra si {TGT} {OP} apetito)").font = Font(bold=True, size=13)
    ws.cell(3, 1, "Leads únicos por estrategia según APETITO:").font = BOLD
    ws.cell(4, 1, "Estrategia").font = BOLD; ws.cell(4, 1).border = BORDER
    ws.cell(4, 2, f"{TGT} segmento").font = BOLD; ws.cell(4, 2).border = BORDER
    for j, (f, av, ra) in enumerate(escen):
        h = ws.cell(4, 3 + j, f"{TGT}{OP}{fmt_target(av)}"); h.font = BOLD; h.border = BORDER
    for i, row in enumerate(seg.itertuples(index=False)):
        ws.cell(5 + i, 1, int(row.estrategia)).border = BORDER
        cr = ws.cell(5 + i, 2, round(float(row.val), 4)); cr.border = BORDER
        cr.fill = fill_riesgo(row.val, vmn, vmx)
        for j, (f, av, ra) in enumerate(escen):
            ws.cell(5 + i, 3 + j, int(row.n_leads) if row.risk <= ra else 0).border = BORDER
    tot_row = 5 + len(seg)
    ws.cell(tot_row, 1, "TOTAL").font = BOLD; ws.cell(tot_row, 1).border = BORDER
    for j, (f, av, ra) in enumerate(escen):
        c = ws.cell(tot_row, 3 + j, int(seg.loc[seg["risk"] <= ra, "n_leads"].sum())); c.font = BOLD; c.border = BORDER

    risk_base = SIGN * APETITO
    main_seg = seg[seg["risk"] <= risk_base]
    rank = dict(zip(seg["leaf_key"], seg["estrategia"]))
    main_leads = ded[ded["leaf_key"].isin(main_seg["leaf_key"])].copy()
    # --- DOS COLUMNAS PEDIDAS: nro_estrategia + estrategia (la regla) ---
    main_leads["nro_estrategia"] = main_leads["leaf_key"].map(rank)
    main_leads["estrategia"] = main_leads["regla"]
    main_leads = (main_leads.assign(_r=SIGN * main_leads["val_cliente"])
                  .sort_values(["nro_estrategia", "_r"]).drop(columns="_r"))
    out_cols = ["nro_estrategia", "estrategia", "escenario", "subject_id", "val_cliente", "leaf_val", "leaf_key"]
    csv_path = ruta.replace(".xlsx", "_leads.csv")
    main_leads[out_cols].to_csv(csv_path, index=False)

    r0 = tot_row + 3
    ws.cell(r0, 1, f"DETALLE corte principal ({TGT} {OP} apetito {fmt_target(APETITO)})  |  "
                   f"leads únicos: {len(main_leads):,}  |  CSV: {csv_path}").font = Font(bold=True, size=12)
    headers = ["nro_estrategia", "Escenario", "estrategia (regla)", f"{TGT}_segmento", "n_leads"]
    for j, h in enumerate(headers):
        c = ws.cell(r0 + 1, 1 + j, h); c.font = BOLD; c.border = BORDER
    for i, row in enumerate(main_seg.itertuples(index=False)):
        ws.cell(r0 + 2 + i, 1, int(row.estrategia)).border = BORDER
        ws.cell(r0 + 2 + i, 2, row.escenario).border = BORDER
        ws.cell(r0 + 2 + i, 3, row.regla).border = BORDER
        cs = ws.cell(r0 + 2 + i, 4, round(float(row.val), 4)); cs.border = BORDER
        cs.fill = fill_riesgo(row.val, vmn, vmx)
        ws.cell(r0 + 2 + i, 5, int(row.n_leads)).border = BORDER
    ws.column_dimensions["C"].width = 80
    for col in ("A", "B", "D", "E"):
        ws.column_dimensions[col].width = 16

    if len(main_leads) <= LEADS_EN_EXCEL_MAX:
        ws2 = wb.create_sheet("Leads")
        cols = ["nro_estrategia", "estrategia", "escenario", "subject_id", "val_cliente", "leaf_val"]
        for j, h in enumerate(cols):
            ws2.cell(1, 1 + j, h).font = BOLD
        for i, row in enumerate(main_leads[cols].itertuples(index=False), start=2):
            for j, val in enumerate(row):
                ws2.cell(i, 1 + j, val if not isinstance(val, float) else round(val, 4))
    print(f"  Leads (apetito {fmt_target(APETITO)}) -> {csv_path}  ({len(main_leads):,} clientes únicos)")
    return rank


def construir_workbook(df, metodologia, ruta, excluir=()):
    wb = Workbook(); wb.remove(wb.active)
    idx = wb.create_sheet("Índice")
    metnom = "Solo árbol" if metodologia == "A" else ("Optbinning + árbol (WoE al árbol)" if WOE_AL_ARBOL else "Optbinning + árbol")
    idx.cell(1, 1, f"Desagregación de riesgo — objetivo {TGT} — {metnom}").font = Font(bold=True, size=14)
    idx.cell(2, 1, f"target: {TARGET_COL} | apetito base = {fmt_target(APETITO)} ({TGT} {OP} apetito)")
    if excluir:
        idx.cell(3, 1, f"Variables excluidas: {', '.join(excluir)}").font = Font(italic=True)
    r = 5
    leads_list, modelos = [], {}
    for nombre, sub in construir_escenarios(df):
        leads, modelo_sc = procesar_escenario(wb, nombre, sub, metodologia, excluir)
        if modelo_sc is not None:
            modelos[nombre] = modelo_sc
        if leads is not None and len(leads):
            leads_list.append(leads)
        idx.cell(r, 1, f"• {nombre}  (n={len(sub):,})"); r += 1

    leads_total = pd.concat(leads_list, ignore_index=True) if leads_list else pd.DataFrame()
    estrategia_rank = hoja_estrategia(wb, leads_total, ruta)
    wb.save(ruta)
    print(f"Generado: {ruta}")

    bundle = {
        "escenarios": modelos, "estrategia_rank": estrategia_rank,
        "config": {
            "SIGN": SIGN, "SENTINEL": SENTINEL, "TGT": TGT, "TARGET_COL": TARGET_COL,
            "SUBJECT_COL": SUBJECT_COL, "APETITO": APETITO, "FACTORES": FACTORES,
            "NUM_VARS": NUM_VARS, "ORD_VAR": ORD_VAR, "VARS_DIRECTAS": VARS_DIRECTAS,
            "SCORE_COL": SCORE_COL, "SIT_COL": SIT_COL, "CORTES": CORTES,
            "UMBRAL_MISSING_IMPUTA": UMBRAL_MISSING_IMPUTA,
        },
    }
    pkl_path = ruta.replace(".xlsx", "_modelo.pkl")
    joblib.dump(bundle, pkl_path)
    print(f"Modelo guardado: {pkl_path}")


# ====================================================================================
# EJECUCIÓN (en notebook normalmente llamas construir_workbook(df, "B", ruta, VARS_EXCLUIR))
# ====================================================================================
if __name__ == "__main__":
    if DATA_PATH:
        df = (pd.read_parquet(DATA_PATH) if DATA_PATH.endswith(".parquet")
              else pd.read_csv(DATA_PATH))
        df = preparar_base(df)
        construir_workbook(df, "B", "segmentacion_score.xlsx", excluir=VARS_EXCLUIR)
    else:
        print("Define DATA_PATH (o llama construir_workbook(df, 'B', ruta, VARS_EXCLUIR) con tu df).")
