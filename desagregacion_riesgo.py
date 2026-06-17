"""
====================================================================================
DESAGREGACIÓN DE RIESGO  (proxy = puntaje_mod, continuo)
====================================================================================
Genera DOS Excel:
  - arbol_solo.xlsx        Metodología A: árbol monótono, dirección por Spearman.
  - optbinning_arbol.xlsx  Metodología B: dirección por optbinning + GRÁFICO de
                           tendencia (creciente/decreciente) por variable.

Cada Excel tiene 1 hoja por ESCENARIO:
  1) FLG_CAST_AP = CAST_NOIBK_REP>=5anios
  2) FLG_CAST_AP = NO_CAST_NOIBK_U24M
  3) (1) con flg_far... = 1
  4) (2) con flg_far... = 1

Cada hoja contiene:
  - Imagen del árbol coloreada verde (bajo riesgo) -> rojo (alto riesgo).
  - CUADRO POR CANTIDAD          (doble entrada, top-2 variables del árbol).
  - CUADRO POR RIESGO            (prom puntaje_mod, doble entrada, coloreado).
  - CUADRO DEL ÁRBOL COMPLETO    (1 fila = 1 hoja, con la condición de cada variable).
  - (solo B) GRÁFICOS optbinning por variable (tendencia creciente/decreciente).

MISSING -> se reemplazan por el valor especial -99999999, así el árbol los aísla en
su propia rama y aparecen como "Missing" en los cuadros. optbinning los grafica como
bin "Missing" aparte.

Optimizado para ~3M filas: bandas vectorizadas y optbinning sobre muestra.
Requisitos: pip install pandas numpy scikit-learn matplotlib openpyxl scipy optbinning
====================================================================================
"""

import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")                       # backend sin ventana (servidor/batch)
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, kendalltau
from sklearn.tree import DecisionTreeRegressor, plot_tree, export_text
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter

warnings.filterwarnings("ignore")

# ====================================================================================
# CONFIGURACIÓN  (edita esto)
# ====================================================================================
DATA_PATH = "base_riesgo.tsv"               # tu base (TSV o CSV; autodetecta separador)
SCORE_COL = "puntaje_mod"                   # proxy de riesgo (alto = MENOR riesgo)
FLG_COL   = "FLG_CAST_AP"                   # define escenarios
FAR_COL   = "flg_far_mto_trx_presencial_12m_c216"   # filtro escenarios 3 y 4
VALORES_FLG = ["CAST_NOIBK_REP>=5anios", "NO_CAST_NOIBK_U24M"]

# Variables numéricas predictoras (monto_castigado_ibk DESCARTADA a pedido)
NUM_VARS = [
    "edad_num", "rk_ing_num", "DEUDA_CAS", "monto_castigado_total",
    "monto_castigado_otros", "nro_entidades_castigo", "max_dias_mora_castigo",
    "meses_desde_ultimo_castigo", "meses_desde_primer_castigo",
    "saldo_pasivo_actual", "saldo_prom_pasivo", "saldo_activo_actual",
    "prom_saldo_pasivo_u4m", "max_saldo_pasivo_u6m", "nro_meses_con_pasivo_u6m",
]
ORD_VAR = "segmentacion_gdp_v2"             # ordinal G1..G5 (entra como predictor; sin optbinning)
NOM_VAR = "sit_laboral_mod"                 # nominal (sin restricción monótona)

# Variables numéricas a EXCLUIR en el 2º juego de Excel (sufijo "_sinalgunasvariables").
# Edita esta lista con lo que quieras quitar. Si la dejas vacía, no se genera el 2º juego.
VARS_EXCLUIR = [
    "monto_castigado_otros",
    "saldo_activo_actual",
]

SENTINEL  = -99999999                       # valor especial para missing
MAX_DEPTH = 4                               # profundidad del árbol
MIN_SAMPLES_LEAF = 0.03                     # 3% mínimo por hoja
OPTB_SAMPLE = 200_000                       # muestra para optbinning (dirección + gráfico)
RANDOM_STATE = 42

# Cortes de negocio puntaje_mod -> banda, por sit_laboral_mod (umbrales DESCENDENTES)
CORTES = {
    "DEPENDIENTE":    [("G1", 967), ("G2", 941), ("G3", 876)],
    "MIXTO":          [("G1", 971), ("G2", 949), ("G3", 915), ("G4", 872), ("G5", 852)],
    "DEPEN_EXPERIAN": [("G1", 971), ("G2", 949), ("G3", 915), ("G4", 872), ("G5", 852)],
    "INDEPENDIENTE":  [("G1", 981), ("G2", 960), ("G3", 943), ("G4", 898), ("G5", 844)],
}

# Dirección monótona POR NEGOCIO (solo metodología B).  +1 creciente / -1 decreciente / 0 sin forzar.
# Si optbinning NO logra binarizar con esta dirección, la variable se DESCARTA del árbol.
DIRECCION_NEGOCIO = {
    "edad_num": 0,                       # ambigua
    "rk_ing_num": +1,                    # más ingreso -> mejor (mayor puntaje)
    "deuda_cas": -1,                     # más deuda castigada -> peor
    "monto_castigado_total": -1,
    "monto_castigado_otros": -1,
    "nro_entidades_castigo": -1,
    "max_dias_mora_castigo": -1,
    "meses_desde_ultimo_castigo": +1,    # castigo más antiguo -> mejor
    "meses_desde_primer_castigo": +1,
    "saldo_pasivo_actual": +1,           # pasivo = ahorro/depósito -> más ahorro = menor riesgo
    "saldo_prom_pasivo": +1,
    "saldo_activo_actual": 0,            # activo = crédito vigente (ambigua)
    "prom_saldo_pasivo_u4m": +1,
    "max_saldo_pasivo_u6m": +1,
    "nro_meses_con_pasivo_u6m": +1,
    "segmentacion_gdp_v2": -1,           # G1 mejor (cod 1) ... G5 peor (cod 5)
}

# Hoja de estrategia final (una por Excel)
SUBJECT_COL = "subject_id"               # id de cliente para deduplicar leads
TOP_N_ESTRATEGIAS = 15                   # nº de segmentos (hojas) de menor riesgo a tomar como estrategias
LEADS_EN_EXCEL_MAX = 100_000             # si hay más leads, solo se exportan a CSV (no a la hoja)
PCTS_LEADS = [0.10, 0.15, 0.20, 0.30]    # cortes de "bajo riesgo" a comparar en la hoja final
MAIN_PCT = 0.20                          # corte principal (CSV + detalle por estrategia)
BINS_OBJETIVO = [5, 2]                   # optbinning: intenta 5 bins; si no, 2; si no -> descarta variable

CMAP = plt.cm.RdYlGn                         # 0=rojo (alto riesgo), 1=verde (bajo riesgo)
BORDER = Border(*[Side(style="thin", color="999999")] * 4)
BOLD = Font(bold=True)


# ====================================================================================
# UTILIDADES
# ====================================================================================
def norm_score(v, vmin, vmax):
    """Normaliza el puntaje a [0,1]; 1 = verde (puntaje alto = menor riesgo)."""
    return 0.5 if vmax <= vmin else (v - vmin) / (vmax - vmin)


def hex_color(t):
    """Color hex del colormap RdYlGn para t en [0,1]."""
    r, g, b, _ = CMAP(float(np.clip(t, 0, 1)))
    return f"{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def banda_cortes_vec(score, sit):
    """Asigna banda G1..Gx (CORTES) VECTORIZADO. Si el puntaje cae bajo el umbral
    más bajo -> peor banda. NaN -> 'Missing'. sit desconocido -> 's/d'."""
    score = np.asarray(score, dtype=float)
    sit = np.asarray(sit, dtype=object)
    out = np.full(score.shape, "s/d", dtype=object)
    out[np.isnan(score)] = "Missing"
    for key, tabla in CORTES.items():
        m = (sit == key) & ~np.isnan(score)
        if not m.any():
            continue
        bandas = np.array([b for b, _ in tabla])
        umbrales = np.array([u for _, u in tabla], dtype=float)      # descendentes
        # nº de umbrales mayores que el puntaje = mejor banda alcanzada; tope = peor banda
        idx = (umbrales[None, :] > score[m][:, None]).sum(axis=1)
        out[m] = bandas[np.minimum(idx, len(tabla) - 1)]
    return out


def fmt_intervalo(lo, hi):
    """Texto del rango (lo, hi] de una variable en una hoja, manejando el sentinel."""
    if hi < -1e7:                       # todo bajo el sentinel -> solo Missing
        return "Missing"
    if lo < -1e7:                       # el límite inferior es el sentinel -> Missing excluido
        lo = -np.inf
    if lo == -np.inf and hi == np.inf:
        return "(todos)"
    if lo == -np.inf:
        return f"<= {hi:,.0f}"
    if hi == np.inf:
        return f"> {lo:,.0f}"
    return f"({lo:,.0f}, {hi:,.0f}]"


def reglas_por_hoja(tree, feats):
    """Por cada hoja, rango (lo, hi] de cada variable de su camino. Iterativo (sin recursión)."""
    t = tree.tree_
    out, stack = {}, [(0, {})]
    while stack:
        node, conds = stack.pop()
        if t.children_left[node] == -1:                 # es hoja
            out[node] = conds
            continue
        f, thr = feats[t.feature[node]], t.threshold[node]
        lo, hi = conds.get(f, (-np.inf, np.inf))
        izq = dict(conds); izq[f] = (lo, min(hi, thr))  # rama izquierda: <= thr
        der = dict(conds); der[f] = (max(lo, thr), hi)  # rama derecha:  > thr
        stack += [(t.children_left[node], izq), (t.children_right[node], der)]
    return out


def optbinning_var(x, y, nombre, direccion, png_path):
    """Ajusta optbinning FORZANDO la dirección de negocio y exigiendo bins (5, luego 2).
    Devuelve (feasible, etiqueta, png_path, dir_efectiva).
    - Si no logra binarizar respetando la dirección ni con 5 ni con 2 bins -> feasible=False
      y la variable se descarta del árbol (no queremos sentidos contraintuitivos).
    - Para dirección 0 (ambigua), toma la tendencia que detecte optbinning.
    x,y vienen muestreados."""
    from optbinning import ContinuousOptimalBinning
    trend = {1: "ascending", -1: "descending", 0: "auto_asc_desc"}[direccion]
    etiqueta = {1: "CRECIENTE (+)", -1: "DECRECIENTE (-)", 0: "auto"}[direccion]
    if (~np.isnan(x)).sum() < 50:
        return False, "sin datos -> descartada", None, 0

    optb = None
    for min_bins in BINS_OBJETIVO:                       # intenta 5 bins, luego 2
        try:
            o = ContinuousOptimalBinning(name=nombre, monotonic_trend=trend,
                                         min_n_bins=min_bins, max_n_bins=max(min_bins, 8))
            o.fit(x, y)
            if o.status in ("OPTIMAL", "FEASIBLE") and len(o.splits) >= (min_bins - 1):
                optb = o
                break
        except Exception:
            continue
    if optb is None:                                     # no binariza con la dirección pedida
        return False, etiqueta + " -> SIN BINARIZACIÓN (ni 5 ni 2 bins), descartada", None, 0

    n_bins = len(optb.splits) + 1
    # Dirección efectiva: la forzada, o la detectada si era ambigua (0)
    if direccion != 0:
        dir_ef = direccion
    else:
        tb = optb.binning_table.build()
        mask = ~tb["Bin"].astype(str).isin(["Special", "Missing", ""])
        means = pd.to_numeric(tb.loc[mask, "Mean"], errors="coerce").dropna().values
        dir_ef = (1 if means[-1] >= means[0] else -1) if len(means) >= 2 else 0
        etiqueta = ("CRECIENTE (+)" if dir_ef > 0 else "DECRECIENTE (-)") + " (detectada)"
    try:
        optb.binning_table.plot(metric="mean", savefig=png_path)
        plt.close("all")
    except Exception:
        png_path = None
    return True, f"{etiqueta} [{n_bins} bins]", png_path, dir_ef


def escribir_cuadro(ws, r0, c0, titulo, tab, vfil, vcol, modo, vmin=None, vmax=None):
    """Escribe un cuadro de doble entrada. modo='riesgo' colorea verde->rojo;
    modo='cantidad' colorea con un azul tenue por densidad."""
    ws.cell(r0, c0, titulo).font = Font(bold=True, size=12)
    ws.cell(r0 + 1, c0 + 1, vcol).font = BOLD
    ws.cell(r0 + 2, c0, vfil).font = BOLD
    for j, col in enumerate(tab.columns):                # encabezados de columna
        c = ws.cell(r0 + 2, c0 + 1 + j, str(col))
        c.font = BOLD; c.border = BORDER
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    mx = np.nanmax(tab.values) if tab.size else 1
    for i, fila in enumerate(tab.index):                 # filas + celdas
        rc = ws.cell(r0 + 3 + i, c0, str(fila)); rc.font = BOLD; rc.border = BORDER
        for j in range(len(tab.columns)):
            val = tab.iloc[i, j]
            cell = ws.cell(r0 + 3 + i, c0 + 1 + j)
            cell.border = BORDER; cell.alignment = Alignment(horizontal="center")
            if pd.isna(val):
                continue
            if modo == "riesgo":
                cell.value = round(float(val), 0)
                cell.fill = PatternFill("solid", fgColor=hex_color(norm_score(val, vmin, vmax)))
            else:
                cell.value = int(val)
                g = int(255 - 120 * (val / mx if mx else 0))
                cell.fill = PatternFill("solid", fgColor=f"D6E4{g:02X}")
    ws.column_dimensions[get_column_letter(c0)].width = 22
    for j in range(len(tab.columns)):
        ws.column_dimensions[get_column_letter(c0 + 1 + j)].width = 15
    return r0 + 4 + len(tab.index)


# ====================================================================================
# PROCESA UN ESCENARIO -> UNA HOJA
# ====================================================================================
def procesar_escenario(wb, nombre, df_sc, metodologia, excluir=()):
    ws = wb.create_sheet(title=nombre[:31])

    # El target (puntaje_mod) no puede tener NaN: descartamos esas filas y reindexamos.
    df_sc = df_sc.loc[pd.to_numeric(df_sc[SCORE_COL], errors="coerce").notna()].reset_index(drop=True)
    n = len(df_sc)
    if n < 50:
        ws.cell(1, 1, f"Escenario con muy pocos casos ({n}). Se omite.")
        return None, f"{'='*70}\nESCENARIO: {nombre}\n(omitido: solo {n} casos)\n\n"

    y = pd.to_numeric(df_sc[SCORE_COL], errors="coerce").values
    vmin, vmax = np.nanmin(y), np.nanmax(y)

    # ----- 1) Matriz de predictores X con sentinel para missing -----
    feats = [c for c in NUM_VARS if c in df_sc.columns and c not in excluir]
    X = pd.DataFrame({c: pd.to_numeric(df_sc[c], errors="coerce") for c in feats})
    if ORD_VAR in df_sc.columns:                         # G1..G5 -> 1..5
        X[ORD_VAR] = df_sc[ORD_VAR].map({f"G{i}": i for i in range(1, 9)})
        feats.append(ORD_VAR)
    if NOM_VAR in df_sc.columns:                         # nominal -> códigos
        X[NOM_VAR] = df_sc[NOM_VAR].astype("category").cat.codes.replace(-1, np.nan)
        feats.append(NOM_VAR)
    miss = X.isna()                                      # marca de missing (para los cuadros)
    X = X.fillna(SENTINEL)                               # sentinel -> el árbol lo aísla

    # ----- 2) Dirección monótona por variable -----
    #   Ambas metodologías RESPETAN la dirección de negocio (DIRECCION_NEGOCIO), para no
    #   tener sentidos contraintuitivos en el árbol.
    #   A: árbol con dirección de negocio (numéricas con dir 0 -> Spearman). Mantiene todas.
    #   B: además valida con optbinning (5 -> 2 bins). Si una variable no binariza con su
    #      dirección, se DESCARTA del árbol; las dir 0 toman la tendencia que detecta optbinning.
    cst_map, plots, drop = {}, [], []
    samp = (df_sc.sample(OPTB_SAMPLE, random_state=RANDOM_STATE).index
            if (metodologia == "B" and n > OPTB_SAMPLE) else df_sc.index)
    y_s = pd.Series(y, index=df_sc.index)
    for c in feats:
        if c == NOM_VAR:                                 # nominal: sin restricción
            cst_map[c] = 0
        elif metodologia == "B" and c in NUM_VARS:      # B numéricas: optbinning + bins exigidos
            d = DIRECCION_NEGOCIO.get(c, 0)
            xs = X.loc[samp, c].where(~miss.loc[samp, c]).values
            feasible, etiqueta, png, dir_ef = optbinning_var(
                xs, y_s.loc[samp].values, c, d, f"_ob_{nombre}_{c}.png")
            plots.append((c, etiqueta, png))
            if feasible:
                cst_map[c] = dir_ef
            else:
                drop.append(c)                          # no binariza -> fuera del árbol
        else:                                            # A (todas) y B ordinal: dirección de negocio
            d = DIRECCION_NEGOCIO.get(c, 0)
            if d != 0:
                cst_map[c] = d
            else:                                        # dir ambigua -> Spearman (data-driven)
                ok = ~miss[c]
                if ok.sum() < 30:
                    cst_map[c] = 0
                else:
                    rho, p = spearmanr(X.loc[ok, c], y[ok])
                    cst_map[c] = 0 if (np.isnan(rho) or p > 0.05) else int(np.sign(rho))

    # Aplica los descartes (solo ocurre en B) y arma X/feats/cst finales
    feats = [c for c in feats if c not in drop]
    X = X[feats]
    miss = miss[feats]
    cst = [cst_map[c] for c in feats]

    # ----- 3) Árbol de regresión monótono (entrenado con TODOS los datos) -----
    try:
        tree = DecisionTreeRegressor(max_depth=MAX_DEPTH, min_samples_leaf=MIN_SAMPLES_LEAF,
                                     monotonic_cst=cst, random_state=RANDOM_STATE).fit(X, y)
    except (TypeError, ValueError):                      # sklearn antiguo sin monotonic_cst
        tree = DecisionTreeRegressor(max_depth=MAX_DEPTH, min_samples_leaf=MIN_SAMPLES_LEAF,
                                     random_state=RANDOM_STATE).fit(X, y)

    # ----- 4) Imagen del árbol coloreada verde->rojo -----
    plt.figure(figsize=(26, 12))
    anns = plot_tree(tree, feature_names=feats, filled=True, rounded=True,
                     impurity=False, precision=1, fontsize=9, proportion=True)
    for ann, v in zip(anns, tree.tree_.value.reshape(-1)):
        if ann.get_bbox_patch() is not None:
            ann.get_bbox_patch().set_facecolor(CMAP(norm_score(v, vmin, vmax)))
            ann.get_bbox_patch().set_edgecolor("black")
    plt.title("Árbol — verde = bajo riesgo (puntaje alto), rojo = alto riesgo")
    plt.tight_layout(); plt.savefig(f"_tree_{nombre}.png", dpi=120, bbox_inches="tight"); plt.close()

    # ----- 5) Encabezado + imagen -----
    ws.cell(1, 1, f"ESCENARIO: {nombre}").font = Font(bold=True, size=14)
    ws.cell(2, 1, f"n = {n:,}   |   puntaje_mod medio = {np.nanmean(y):,.0f}   |   "
                  f"metodología = {'Solo árbol' if metodologia == 'A' else 'Optbinning + árbol'}")
    ws.cell(3, 1, f"monotonic_cst (+ creciente / - decreciente / 0 sin restricción): "
                  f"{dict(zip(feats, cst))}")
    try:
        img = XLImage(f"_tree_{nombre}.png"); img.width, img.height = 1100, 520
        ws.add_image(img, "A5")
    except Exception as e:
        ws.cell(5, 1, f"(no se pudo insertar imagen: {e})")

    # ----- 6) Cuadros de doble entrada (top-2 variables del árbol) -----
    imp = pd.Series(tree.feature_importances_, index=feats).sort_values(ascending=False)
    top = [v for v in imp.index if imp[v] > 0][:2]
    for v in feats:                                       # asegura 2 ejes
        if len(top) >= 2:
            break
        if v not in top:
            top.append(v)
    vfil, vcol = top[0], top[1]

    cuadro = {}                                           # construye los dos ejes binados
    for var in (vfil, vcol):
        idx = feats.index(var)
        thr = sorted({round(t, 4) for f, t in zip(tree.tree_.feature, tree.tree_.threshold)
                      if f == idx and t > SENTINEL / 2})  # cortes reales (excluye sentinel)
        edges = [-np.inf] + thr + [np.inf]
        labels = [f"({'-inf' if e0 == -np.inf else f'{e0:,.0f}'}, "
                  f"{'inf' if e1 == np.inf else f'{e1:,.0f}'}]"
                  for e0, e1 in zip(edges[:-1], edges[1:])]
        b = pd.cut(X[var], bins=edges, labels=labels).astype(object)
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
    fila = escribir_cuadro(ws, fila, 1, "CUADRO POR RIESGO (prom puntaje_mod)", riesgo,
                           vfil, vcol, "riesgo", vmin, vmax) + 2

    # ----- 6b) Importancia de variables (pesos del árbol) -----
    imp = (pd.Series(tree.feature_importances_, index=feats)
           .sort_values(ascending=False))
    ws.cell(fila, 1, "IMPORTANCIA DE VARIABLES (peso en el árbol)").font = Font(bold=True, size=12)
    for j, h in enumerate(["Variable", "Peso", "Peso %"]):
        c = ws.cell(fila + 1, 1 + j, h); c.font = BOLD; c.border = BORDER
    for i, (var, w) in enumerate(imp.items()):
        ws.cell(fila + 2 + i, 1, var).border = BORDER
        ws.cell(fila + 2 + i, 2, round(float(w), 4)).border = BORDER
        ws.cell(fila + 2 + i, 3, round(float(w) * 100, 1)).border = BORDER
    fila = fila + 3 + len(imp)

    # ----- 7) Cuadro del árbol completo (1 fila = 1 hoja) -----
    leafmap = reglas_por_hoja(tree, feats)
    usadas = [f for f in feats if any(f in cond for cond in leafmap.values())]
    leaf_id = tree.apply(X)
    sit = df_sc[NOM_VAR].values if NOM_VAR in df_sc.columns else np.array([None] * n)
    cortes_v = banda_cortes_vec(y, sit)                  # banda CORTES (vectorizada)
    try:
        quint_v = pd.qcut(y_s, 5, labels=["G5", "G4", "G3", "G2", "G1"])
    except ValueError:
        quint_v = pd.qcut(y_s.rank(method="first"), 5, labels=["G5", "G4", "G3", "G2", "G1"])
    res = pd.DataFrame({"leaf": leaf_id, "s": y, "cortes": cortes_v, "quint": quint_v.values})

    filas = []
    for lid, sub in res.groupby("leaf"):
        cond = leafmap.get(lid, {})
        row = {f: fmt_intervalo(*cond.get(f, (-np.inf, np.inf))) for f in usadas}
        row["n"] = len(sub)
        row["%"] = round(100 * len(sub) / n, 1)
        row["score_medio"] = sub["s"].mean()
        row["CORTES"] = sub["cortes"].mode().iloc[0] if not sub["cortes"].mode().empty else ""
        row["quintil"] = sub["quint"].mode().iloc[0] if not sub["quint"].mode().empty else ""
        filas.append(row)
    tab = pd.DataFrame(filas).sort_values("score_medio", ascending=False).reset_index(drop=True)

    ws.cell(fila, 1, "CUADRO DEL ÁRBOL COMPLETO (una fila = una hoja)").font = Font(bold=True, size=12)
    cols = usadas + ["n", "%", "score_medio", "CORTES", "quintil"]
    for j, h in enumerate(cols):
        c = ws.cell(fila + 1, 1 + j, h); c.font = BOLD; c.border = BORDER
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    for i in range(len(tab)):
        for j, h in enumerate(cols):
            cell = ws.cell(fila + 2 + i, 1 + j); cell.border = BORDER
            cell.alignment = Alignment(horizontal="center")
            val = tab.iloc[i][h]
            if h == "score_medio":
                cell.value = round(float(val), 0)
                cell.fill = PatternFill("solid", fgColor=hex_color(norm_score(val, vmin, vmax)))
            elif h in ("n", "%"):
                cell.value = float(val) if h == "%" else int(val)
            else:
                cell.value = str(val)
    for j, h in enumerate(cols):
        ws.column_dimensions[get_column_letter(1 + j)].width = 17 if h in usadas else 11
    fila = fila + 3 + len(tab)

    # ----- 8) (Solo B) Gráficos optbinning por variable (tendencia) -----
    if plots:
        fila += 2
        ws.cell(fila, 1, "TENDENCIA POR VARIABLE (optbinning): creciente / decreciente").font = Font(bold=True, size=12)
        fila += 1
        for k, (nom, etiqueta, png) in enumerate(plots):
            r = fila + (k // 3) * 15            # 3 gráficos por fila
            c = 1 + (k % 3) * 8
            ws.cell(r, c, f"{nom}: {etiqueta}").font = BOLD
            if png:
                try:
                    img = XLImage(png); img.width, img.height = 380, 250
                    ws.add_image(img, f"{get_column_letter(c)}{r + 1}")
                except Exception:
                    pass

    # ----- 9) Leads de BAJO RIESGO para la hoja de estrategia -----
    #   Devuelve, por cliente, su segmento (hoja), el riesgo del segmento (score medio de la
    #   hoja) y su PERCENTIL dentro del escenario (1 = mejor puntaje). Solo retorna el mejor
    #   30% (el corte más amplio), suficiente para evaluar 10/15/20/30% en la hoja final.
    leaf_mean = res.groupby("leaf")["s"].mean().to_dict()
    regla_txt = {lid: " & ".join(f"{f}{fmt_intervalo(*rng)}" for f, rng in cond.items()) or "(raíz)"
                 for lid, cond in leafmap.items()}
    sid = df_sc[SUBJECT_COL].values if SUBJECT_COL in df_sc.columns else df_sc.index.values
    pct = y_s.rank(pct=True).values                      # percentil del puntaje en el escenario
    leads = pd.DataFrame({
        "subject_id": sid,
        "escenario": nombre,
        "leaf_key": [f"{nombre}#{l}" for l in leaf_id],
        "regla": [regla_txt.get(l, "") for l in leaf_id],
        "score": y,
        "leaf_mean": [leaf_mean.get(l, np.nan) for l in leaf_id],
        "banda_cortes": cortes_v,
        "pct": pct,                                      # 1 = mejor; lead si pct >= 1 - corte
    })

    # ----- 10) Espejo en TEXTO de la hoja (mismo contenido que el Excel) -----
    L = ["=" * 70, f"ESCENARIO: {nombre}",
         f"n = {n:,} | puntaje_mod medio = {np.nanmean(y):,.0f} | "
         f"metodología = {'Solo árbol' if metodologia == 'A' else 'Optbinning + árbol'}",
         f"monotonic_cst: {dict(zip(feats, cst))}",
         "-" * 70, "ÁRBOL (texto):",
         export_text(tree, feature_names=list(feats)),
         "-" * 70, "IMPORTANCIA DE VARIABLES (peso / peso %):",
         pd.DataFrame({"peso": imp.round(4), "peso_%": (imp * 100).round(1)}).to_string(),
         "-" * 70, f"CUADRO POR CANTIDAD (filas={vfil} / columnas={vcol}):",
         cant.to_string(na_rep=""),
         "-" * 70, f"CUADRO POR RIESGO - prom puntaje_mod (filas={vfil} / columnas={vcol}):",
         riesgo.round(0).to_string(na_rep=""),
         "-" * 70, "CUADRO DEL ÁRBOL COMPLETO (una fila = una hoja):",
         tab.to_string(index=False)]
    if plots:
        L += ["-" * 70, "TENDENCIA POR VARIABLE (optbinning):"]
        L += [f"  {nom}: {etiqueta}" for nom, etiqueta, _ in plots]
    texto = "\n".join(L) + "\n\n"

    return leads[leads["pct"] >= 1 - max(PCTS_LEADS)].reset_index(drop=True), texto


# ====================================================================================
# ORQUESTACIÓN
# ====================================================================================
def construir_escenarios(df):
    """Lista de (nombre_hoja, subdataframe) para los 4 escenarios."""
    out = []
    for v in VALORES_FLG:
        base = df[df[FLG_COL] == v]
        nombre = v.replace(">=", "ge").replace("=", "").replace("/", "_")
        out.append((nombre[:24], base))
        if FAR_COL in df.columns:
            far = base[pd.to_numeric(base[FAR_COL], errors="coerce") == 1]
            out.append((f"{nombre}_far1"[:28], far))
    return out


def _dedup(pool):
    """Deja a cada cliente en su estrategia de menor riesgo (mayor score medio del segmento)."""
    return pool.sort_values("leaf_mean", ascending=False).drop_duplicates("subject_id", keep="first")


def hoja_estrategia(wb, leads_total, ruta):
    """Construye la hoja ESTRATEGIA final del Excel:
       - Toma los TOP_N segmentos (hojas) de menor riesgo como estrategias.
       - Compara cuántos leads únicos salen con cada corte de % (PCTS_LEADS).
       - Para el corte principal (MAIN_PCT): detalle por estrategia + CSV de leads."""
    ws = wb.create_sheet("Estrategia")
    if leads_total.empty:
        ws.cell(1, 1, "No hay leads de bajo riesgo para construir estrategias.")
        return "=" * 70 + "\nHOJA DE ESTRATEGIA\n(sin leads de bajo riesgo)\n"

    # Estrategias = top-N segmentos por menor riesgo (score medio de la hoja, descendente)
    seg = (leads_total.groupby("leaf_key")
           .agg(escenario=("escenario", "first"), regla=("regla", "first"),
                score_medio=("leaf_mean", "first"))
           .sort_values("score_medio", ascending=False))
    top_keys = seg.head(TOP_N_ESTRATEGIAS).index.tolist()
    rank = {k: i + 1 for i, k in enumerate(top_keys)}
    base = leads_total[leads_total["leaf_key"].isin(top_keys)].copy()
    base["estrategia"] = base["leaf_key"].map(rank)

    ws.cell(1, 1, "HOJA DE ESTRATEGIA — grupos de BAJO RIESGO (sin clientes duplicados)").font = Font(bold=True, size=13)

    # ---- A) Comparación de leads únicos por corte de % (10/15/20/30%) ----
    ws.cell(3, 1, "Leads únicos por corte de bajo riesgo (% top dentro de cada escenario):").font = BOLD
    cortes = sorted(PCTS_LEADS)
    ws.cell(4, 1, "Estrategia").font = BOLD; ws.cell(4, 1).border = BORDER
    for j, pc in enumerate(cortes):
        h = ws.cell(4, 2 + j, f"top {int(pc * 100)}%"); h.font = BOLD; h.border = BORDER
    pools = {pc: _dedup(base[base["pct"] >= 1 - pc]) for pc in cortes}
    estr_ids = sorted(base["estrategia"].unique())
    for i, e in enumerate(estr_ids):
        ws.cell(5 + i, 1, int(e)).border = BORDER
        for j, pc in enumerate(cortes):
            ws.cell(5 + i, 2 + j, int((pools[pc]["estrategia"] == e).sum())).border = BORDER
    tot_row = 5 + len(estr_ids)
    ws.cell(tot_row, 1, "TOTAL").font = BOLD; ws.cell(tot_row, 1).border = BORDER
    for j, pc in enumerate(cortes):
        c = ws.cell(tot_row, 2 + j, int(len(pools[pc]))); c.font = BOLD; c.border = BORDER

    # ---- B) Detalle por estrategia para el corte principal (MAIN_PCT) ----
    pool = pools[MAIN_PCT].sort_values(["estrategia", "score"], ascending=[True, False])
    csv_path = ruta.replace(".xlsx", "_leads.csv")
    pool[["estrategia", "leaf_key", "escenario", "regla", "subject_id", "score", "banda_cortes"]].to_csv(csv_path, index=False)

    resumen = (pool.groupby(["estrategia", "leaf_key"])
               .agg(escenario=("escenario", "first"), regla=("regla", "first"),
                    score_medio=("leaf_mean", "first"), n_leads=("subject_id", "size"))
               .reset_index().sort_values("estrategia"))
    vmin, vmax = resumen["score_medio"].min(), resumen["score_medio"].max()

    r0 = tot_row + 3
    ws.cell(r0, 1, f"DETALLE corte principal = top {int(MAIN_PCT * 100)}%  |  "
                   f"leads únicos: {len(pool):,}  |  CSV: {csv_path}").font = Font(bold=True, size=12)
    headers = ["Estrategia", "Escenario", "Regla del segmento", "score_medio", "n_leads"]
    for j, h in enumerate(headers):
        c = ws.cell(r0 + 1, 1 + j, h); c.font = BOLD; c.border = BORDER
    for i, row in enumerate(resumen.itertuples(index=False)):
        ws.cell(r0 + 2 + i, 1, int(row.estrategia)).border = BORDER
        ws.cell(r0 + 2 + i, 2, row.escenario).border = BORDER
        ws.cell(r0 + 2 + i, 3, row.regla).border = BORDER
        cs = ws.cell(r0 + 2 + i, 4, round(float(row.score_medio), 0)); cs.border = BORDER
        cs.fill = PatternFill("solid", fgColor=hex_color(norm_score(row.score_medio, vmin, vmax)))
        ws.cell(r0 + 2 + i, 5, int(row.n_leads)).border = BORDER
    ws.column_dimensions["C"].width = 70
    for col in ("A", "B", "D", "E"):
        ws.column_dimensions[col].width = 16

    # Lista de leads dentro del Excel si son pocos (siempre están en el CSV)
    if len(pool) <= LEADS_EN_EXCEL_MAX:
        ws2 = wb.create_sheet("Leads")
        cols = ["estrategia", "escenario", "subject_id", "score", "banda_cortes", "regla"]
        for j, h in enumerate(cols):
            ws2.cell(1, 1 + j, h).font = BOLD
        for i, row in enumerate(pool[cols].itertuples(index=False), start=2):
            for j, val in enumerate(row):
                ws2.cell(i, 1 + j, val if not isinstance(val, float) else round(val, 0))
    print(f"  Leads (top {int(MAIN_PCT*100)}%) -> {csv_path}  ({len(pool):,} clientes únicos)")

    # Espejo en TEXTO de la hoja de estrategia
    comp = pd.DataFrame({f"top {int(pc*100)}%": [int((pools[pc]['estrategia'] == e).sum()) for e in estr_ids]
                         for pc in cortes}, index=[f"Estrategia {e}" for e in estr_ids])
    comp.loc["TOTAL"] = [int(len(pools[pc])) for pc in cortes]
    T = ["=" * 70, "HOJA DE ESTRATEGIA — grupos de BAJO RIESGO (sin clientes duplicados)",
         "-" * 70, "Leads únicos por corte de bajo riesgo:", comp.to_string(),
         "-" * 70, f"DETALLE corte principal = top {int(MAIN_PCT*100)}% (leads únicos: {len(pool):,}) | CSV: {csv_path}",
         resumen.to_string(index=False)]
    return "\n".join(T) + "\n"


def construir_workbook(df, metodologia, ruta, excluir=()):
    """Genera un Excel completo para la metodología indicada ('A' o 'B'),
    excluyendo las variables numéricas de 'excluir'."""
    wb = Workbook(); wb.remove(wb.active)
    idx = wb.create_sheet("Índice")
    idx.cell(1, 1, f"Desagregación de riesgo — "
                   f"{'Solo árbol' if metodologia == 'A' else 'Optbinning + árbol'}").font = Font(bold=True, size=14)
    idx.cell(2, 1, "proxy de riesgo: puntaje_mod (alto = menor riesgo)")
    if excluir:
        idx.cell(3, 1, f"Variables excluidas: {', '.join(excluir)}").font = Font(italic=True)
    r = 5
    leads_list, txt_blocks = [], []
    cab = (f"DESAGREGACIÓN DE RIESGO — {'Solo árbol' if metodologia == 'A' else 'Optbinning + árbol'}\n"
           f"proxy de riesgo: puntaje_mod (alto = menor riesgo)\n"
           + (f"Variables excluidas: {', '.join(excluir)}\n" if excluir else ""))
    for nombre, sub in construir_escenarios(df):
        leads, texto = procesar_escenario(wb, nombre, sub, metodologia, excluir)
        txt_blocks.append(texto)
        if leads is not None and len(leads):
            leads_list.append(leads)
        idx.cell(r, 1, f"• {nombre}  (n={len(sub):,})"); r += 1

    # Hoja de estrategia final (una por Excel)
    leads_total = pd.concat(leads_list, ignore_index=True) if leads_list else pd.DataFrame()
    txt_estr = hoja_estrategia(wb, leads_total, ruta)

    wb.save(ruta)
    print(f"Generado: {ruta}")

    # Espejo en TXT del Excel completo (árbol como texto en vez de imagen)
    txt_path = ruta.replace(".xlsx", ".txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(cab + "\n" + "".join(txt_blocks) + "\n" + (txt_estr or ""))
    print(f"Generado: {txt_path}")


def main():
    # Carga (autodetecta TSV/CSV)
    df = pd.read_csv(DATA_PATH, sep="\t")
    if df.shape[1] == 1:
        df = pd.read_csv(DATA_PATH, sep=",")
    print(f"Base: {len(df):,} filas, {df.shape[1]} columnas")

    # 1er juego: con todas las variables
    construir_workbook(df, "A", "arbol_solo.xlsx")
    construir_workbook(df, "B", "optbinning_arbol.xlsx")
    print("Listo: arbol_solo.xlsx y optbinning_arbol.xlsx")

    # 2do juego: excluyendo VARS_EXCLUIR (solo si hay variables que quitar)
    excluir = [c for c in VARS_EXCLUIR if c in df.columns]
    if excluir:
        construir_workbook(df, "A", "arbol_solo_sinalgunasvariables.xlsx", excluir)
        construir_workbook(df, "B", "optbinning_arbol_sinalgunasvariables.xlsx", excluir)
        print(f"Listo (sin {', '.join(excluir)}): "
              "arbol_solo_sinalgunasvariables.xlsx y optbinning_arbol_sinalgunasvariables.xlsx")


if __name__ == "__main__":
    main()
