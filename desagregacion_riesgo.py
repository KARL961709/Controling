"""
Desagregación de riesgo con puntaje_mod como proxy (continuo)
============================================================

Genera DOS Excel (uno por metodología):
  - arbol_solo.xlsx        -> Metodología A: árbol monótono, dirección por Spearman
  - optbinning_arbol.xlsx  -> Metodología B: dirección detectada con optbinning + Kendall-tau

Por cada Excel hay una hoja por ESCENARIO:
  1) FLG_CAST_AP = CAST_NOIBK_REP>=5anios
  2) FLG_CAST_AP = NO_CAST_NOIBK_U24M
  3) (1) y flg_far_mto_trx_presencial_12m_c216 = 1
  4) (2) y flg_far_mto_trx_presencial_12m_c216 = 1

Cada hoja muestra:
  - Imagen del árbol coloreada verde (bajo riesgo) -> rojo (alto riesgo)
  - Cuadro por CANTIDAD (doble entrada, top-2 variables del árbol)
  - Cuadro por RIESGO (promedio de puntaje_mod) coloreado verde->rojo, con banda G1-G5 (CORTES)

MISSING: se reemplazan por el valor especial -99999999 para que el árbol los aísle
en su propia rama y aparezcan como "Missing" en los cuadros.

Requisitos:
  pip install pandas numpy scikit-learn matplotlib openpyxl scipy
  pip install optbinning   # solo para metodología B
"""

import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr, kendalltau
from sklearn.tree import DecisionTreeRegressor, plot_tree

from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter

warnings.filterwarnings("ignore")

# =============================================================================
# CONFIG  --  EDITA ESTO
# =============================================================================
DATA_PATH = "base_riesgo.tsv"        # tu base (TSV/CSV). Ajusta sep en load_data().
SCORE_COL = "puntaje_mod"            # proxy de riesgo (continuo)
FLG_COL   = "FLG_CAST_AP"            # define escenarios
FAR_COL   = "flg_far_mto_trx_presencial_12m_c216"  # filtro escenarios 3 y 4

VALORES_FLG = ["CAST_NOIBK_REP>=5anios", "NO_CAST_NOIBK_U24M"]

# Variables numéricas predictoras (monto_castigado_ibk DESCARTADA por pedido)
NUM_VARS = [
    "edad_num", "rk_ing_num", "DEUDA_CAS", "monto_castigado_total",
    "monto_castigado_otros", "nro_entidades_castigo", "max_dias_mora_castigo",
    "meses_desde_ultimo_castigo", "meses_desde_primer_castigo",
    "saldo_pasivo_actual", "saldo_prom_pasivo", "saldo_activo_actual",
    "prom_saldo_pasivo_u4m", "max_saldo_pasivo_u6m", "nro_meses_con_pasivo_u6m",
]
ORD_VAR  = "segmentacion_gdp_v2"     # ordinal G1..G5 (entra como predictor, sin optbinning)
NOM_VAR  = "sit_laboral_mod"         # nominal (sin restricción monótona)

SENTINEL = -99999999                 # valor especial para missing
MAX_DEPTH = 4
MIN_SAMPLES_LEAF = 0.03              # 3% mínimo por hoja
RANDOM_STATE = 42

# puntaje alto = MENOR riesgo  -> color verde para alto, rojo para bajo
SCORE_ALTO_ES_MENOR_RIESGO = True

# Cortes de negocio puntaje_mod -> banda, por sit_laboral_mod (umbrales descendentes)
CORTES = {
    "DEPENDIENTE":   [("G1", 967), ("G2", 941), ("G3", 876)],
    "MIXTO":         [("G1", 971), ("G2", 949), ("G3", 915), ("G4", 872), ("G5", 852)],
    "DEPEN_EXPERIAN":[("G1", 971), ("G2", 949), ("G3", 915), ("G4", 872), ("G5", 852)],
    "INDEPENDIENTE": [("G1", 981), ("G2", 960), ("G3", 943), ("G4", 898), ("G5", 844)],
}

# Estética de colores
CMAP = plt.cm.RdYlGn            # 0=rojo (alto riesgo), 1=verde (bajo riesgo)
THIN = Side(style="thin", color="999999")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


# =============================================================================
# Carga
# =============================================================================
def load_data():
    # Autodetecta separador tab/coma
    try:
        df = pd.read_csv(DATA_PATH, sep="\t")
        if df.shape[1] == 1:
            df = pd.read_csv(DATA_PATH, sep=",")
    except Exception:
        df = pd.read_csv(DATA_PATH, sep=",")
    print(f"Base: {df.shape[0]} filas, {df.shape[1]} columnas")
    return df


def asignar_banda(score, sit):
    """puntaje_mod -> banda G1..Gx según CORTES y sit_laboral_mod."""
    if pd.isna(score):
        return "Missing"
    tabla = CORTES.get(str(sit))
    if tabla is None:
        return np.nan
    for banda, umbral in tabla:      # descendente
        if score >= umbral:
            return banda
    return tabla[-1][0]              # peor banda si está por debajo de todo


# =============================================================================
# Preparación de features (con sentinel para missing)
# =============================================================================
def construir_X(df):
    feats = NUM_VARS + [ORD_VAR, NOM_VAR]
    feats = [c for c in feats if c in df.columns]
    X = pd.DataFrame(index=df.index)

    num_presentes = [c for c in NUM_VARS if c in df.columns]
    for c in num_presentes:
        X[c] = pd.to_numeric(df[c], errors="coerce")

    if ORD_VAR in df.columns:        # G1..G5 -> 1..5 (G1 mejor = mayor puntaje)
        mapa = {f"G{i}": i for i in range(1, 9)}
        X[ORD_VAR] = df[ORD_VAR].map(mapa)

    if NOM_VAR in df.columns:        # nominal -> códigos
        X[NOM_VAR] = df[NOM_VAR].astype("category").cat.codes.replace(-1, np.nan)

    # Marca de missing original (para los cuadros) y relleno con sentinel
    miss_mask = X.isna()
    X_filled = X.fillna(SENTINEL)
    return X_filled, miss_mask, list(X.columns)


# =============================================================================
# Dirección monótona
# =============================================================================
def mono_por_spearman(X, miss, y, feats):
    """Metodología A: signo de Spearman sobre filas no-missing."""
    cst = []
    for c in feats:
        if c == NOM_VAR:
            cst.append(0)
            continue
        ok = ~miss[c]
        if ok.sum() < 30:
            cst.append(0); continue
        rho, p = spearmanr(X.loc[ok, c], y[ok])
        cst.append(0 if (np.isnan(rho) or p > 0.05) else int(np.sign(rho)))
    return cst


def mono_por_optbinning(df_sc, X, miss, y, feats):
    """Metodología B: optbinning detecta tendencia; Kendall-tau define el signo."""
    try:
        from optbinning import ContinuousOptimalBinning
    except ImportError:
        print("[B] optbinning no instalado -> uso Spearman.")
        return mono_por_spearman(X, miss, y, feats)
    cst = []
    for c in feats:
        if c == NOM_VAR:
            cst.append(0); continue
        ok = ~miss[c]
        if ok.sum() < 30:
            cst.append(0); continue
        x = X.loc[ok, c].values
        yy = y[ok]
        try:
            optb = ContinuousOptimalBinning(name=c, monotonic_trend="auto")
            optb.fit(x, yy)
            tau, p = kendalltau(x, yy)
            if np.isnan(tau) or p > 0.05:
                cst.append(0)
            else:
                cst.append(int(np.sign(tau)))
        except Exception:
            rho, p = spearmanr(x, yy)
            cst.append(0 if (np.isnan(rho) or p > 0.05) else int(np.sign(rho)))
    return cst


# =============================================================================
# Árbol + imagen coloreada
# =============================================================================
def entrenar_arbol(X, y, cst):
    try:
        tree = DecisionTreeRegressor(
            max_depth=MAX_DEPTH, min_samples_leaf=MIN_SAMPLES_LEAF,
            monotonic_cst=cst, random_state=RANDOM_STATE)
        tree.fit(X, y)
    except (TypeError, ValueError):
        tree = DecisionTreeRegressor(
            max_depth=MAX_DEPTH, min_samples_leaf=MIN_SAMPLES_LEAF,
            random_state=RANDOM_STATE).fit(X, y)
    return tree


def norm_score(v, vmin, vmax):
    if vmax <= vmin:
        return 0.5
    t = (v - vmin) / (vmax - vmin)
    return t if SCORE_ALTO_ES_MENOR_RIESGO else 1 - t


def hex_color(t):
    r, g, b, _ = CMAP(float(np.clip(t, 0, 1)))
    return f"{int(r*255):02X}{int(g*255):02X}{int(b*255):02X}"


def pintar_arbol(tree, feats, png_path, vmin, vmax):
    plt.figure(figsize=(26, 12))
    anns = plot_tree(tree, feature_names=feats, filled=True, rounded=True,
                     impurity=False, precision=1, fontsize=9, proportion=True)
    vals = tree.tree_.value.reshape(-1)
    for ann, v in zip(anns, vals):
        patch = ann.get_bbox_patch()
        if patch is not None:
            patch.set_facecolor(CMAP(norm_score(v, vmin, vmax)))
            patch.set_edgecolor("black")
    plt.title("Árbol — verde = bajo riesgo (puntaje alto), rojo = alto riesgo")
    plt.tight_layout()
    plt.savefig(png_path, dpi=130, bbox_inches="tight")
    plt.close()


# =============================================================================
# Pasar el árbol a CUADRO (doble entrada por top-2 variables)
# =============================================================================
def bins_de_variable(tree, feats, var):
    """Bordes de corte que el árbol usó para 'var' (excluye cortes del sentinel)."""
    idx = feats.index(var)
    thr = sorted({round(t, 4) for f, t in zip(tree.tree_.feature, tree.tree_.threshold)
                  if f == idx and t > SENTINEL / 2})
    return thr


def binar_eje(serie, miss_col, thr):
    """Devuelve etiquetas de bin; 'Missing' para los que estaban vacíos."""
    edges = [-np.inf] + thr + [np.inf]
    labels = []
    for i in range(len(edges) - 1):
        lo, hi = edges[i], edges[i + 1]
        lo_s = "-inf" if lo == -np.inf else f"{lo:,.0f}"
        hi_s = "inf" if hi == np.inf else f"{hi:,.0f}"
        labels.append(f"({lo_s}, {hi_s}]")
    out = pd.cut(serie, bins=edges, labels=labels)
    out = out.astype("object")
    out[miss_col.values] = "Missing"
    return out, labels


def construir_cuadros(df_sc, X, miss, tree, feats):
    """Top-2 variables del árbol -> cuadro cantidad y cuadro riesgo (prom puntaje)."""
    imp = pd.Series(tree.feature_importances_, index=feats).sort_values(ascending=False)
    top = [v for v in imp.index if imp[v] > 0][:2]
    while len(top) < 2:                       # fallback
        for v in feats:
            if v not in top:
                top.append(v); break
    vfil, vcol = top[0], top[1]

    thr_f = bins_de_variable(tree, feats, vfil)
    thr_c = bins_de_variable(tree, feats, vcol)

    bf, lab_f = binar_eje(X[vfil], miss[vfil], thr_f)
    bc, lab_c = binar_eje(X[vcol], miss[vcol], thr_c)

    tmp = pd.DataFrame({"f": bf, "c": bc, "score": df_sc[SCORE_COL].values})
    orden_f = lab_f + (["Missing"] if (bf == "Missing").any() else [])
    orden_c = lab_c + (["Missing"] if (bc == "Missing").any() else [])

    cant = (tmp.pivot_table(index="f", columns="c", values="score", aggfunc="count")
            .reindex(index=orden_f, columns=orden_c))
    riesgo = (tmp.pivot_table(index="f", columns="c", values="score", aggfunc="mean")
              .reindex(index=orden_f, columns=orden_c))
    return vfil, vcol, cant, riesgo


# =============================================================================
# Escritura de cuadros en Excel
# =============================================================================
def escribir_cuadro(ws, r0, c0, titulo, df_tab, vfil, vcol,
                    colorear="riesgo", vmin=None, vmax=None, df_sit=None):
    bold = Font(bold=True)
    ws.cell(r0, c0, titulo).font = Font(bold=True, size=12)
    ws.cell(r0 + 1, c0 + 1, vcol).font = bold
    ws.cell(r0 + 2, c0, vfil).font = bold

    # encabezados de columna
    for j, col in enumerate(df_tab.columns):
        cc = ws.cell(r0 + 2, c0 + 1 + j, str(col))
        cc.font = bold; cc.alignment = Alignment(horizontal="center", wrap_text=True)
        cc.border = BORDER
    # filas
    for i, fila in enumerate(df_tab.index):
        rc = ws.cell(r0 + 3 + i, c0, str(fila))
        rc.font = bold; rc.border = BORDER
        for j, col in enumerate(df_tab.columns):
            val = df_tab.iloc[i, j]
            cell = ws.cell(r0 + 3 + i, c0 + 1 + j)
            cell.border = BORDER
            cell.alignment = Alignment(horizontal="center")
            if pd.isna(val):
                continue
            if colorear == "riesgo":
                cell.value = round(float(val), 0)
                t = norm_score(val, vmin, vmax)
                cell.fill = PatternFill("solid", fgColor=hex_color(t))
            else:  # cantidad: azul tenue por densidad
                cell.value = int(val)
                mx = np.nanmax(df_tab.values)
                t = (val / mx) if mx else 0
                g = int(255 - 120 * t)
                cell.fill = PatternFill("solid", fgColor=f"D6E4{g:02X}")
    # ancho
    ws.column_dimensions[get_column_letter(c0)].width = 22
    for j in range(len(df_tab.columns)):
        ws.column_dimensions[get_column_letter(c0 + 1 + j)].width = 16
    return r0 + 4 + len(df_tab.index)


def _fmt_intervalo(lo, hi):
    """Formatea el rango de una variable en una hoja, manejando el sentinel (Missing)."""
    UMB = -1e7
    if hi < UMB:                       # todo por debajo del sentinel -> solo Missing
        return "Missing"
    if lo < UMB:                       # el límite inferior es el sentinel -> Missing excluido
        lo = -np.inf
    if lo == -np.inf and hi == np.inf:
        return "(todos)"
    if lo == -np.inf:
        return f"≤ {hi:,.0f}"
    if hi == np.inf:
        return f"> {lo:,.0f}"
    return f"({lo:,.0f}, {hi:,.0f}]"


def reglas_por_hoja(tree, feats):
    """Reconstruye, por cada hoja, el rango (lo, hi] de cada variable usada en su camino."""
    t = tree.tree_
    out = {}

    def rec(node, conds):
        if t.children_left[node] == -1:               # hoja
            out[node] = {k: v for k, v in conds.items()}
            return
        f = feats[t.feature[node]]
        thr = t.threshold[node]
        lo, hi = conds.get(f, (-np.inf, np.inf))
        izq = conds.copy(); izq[f] = (lo, min(hi, thr))
        rec(t.children_left[node], izq)
        der = conds.copy(); der[f] = (max(lo, thr), hi)
        rec(t.children_right[node], der)

    rec(0, {})
    return out


def escribir_tabla_arbol(ws, r0, c0, df_sc, X, tree, feats, vmin, vmax):
    """CUADRO DEL ÁRBOL COMPLETO: una fila por hoja, columnas = condiciones por variable."""
    leafmap = reglas_por_hoja(tree, feats)
    usadas = [f for f in feats if any(f in cond for cond in leafmap.values())]

    df = df_sc.copy()
    df["_leaf"] = tree.apply(X)
    sit = df[NOM_VAR] if NOM_VAR in df.columns else pd.Series(index=df.index, dtype=object)
    df["_cortes"] = [asignar_banda(s, t) for s, t in zip(df[SCORE_COL], sit)]
    try:
        df["_quint"] = pd.qcut(df[SCORE_COL], 5, labels=["G5", "G4", "G3", "G2", "G1"])
    except ValueError:
        df["_quint"] = pd.qcut(df[SCORE_COL].rank(method="first"), 5,
                               labels=["G5", "G4", "G3", "G2", "G1"])

    total = len(df)
    filas = []
    for lid, sub in df.groupby("_leaf"):
        cond = leafmap.get(lid, {})
        fila = {f: _fmt_intervalo(*cond.get(f, (-np.inf, np.inf))) for f in usadas}
        fila["n"] = len(sub)
        fila["%"] = round(100 * len(sub) / total, 1)
        fila["score_medio"] = sub[SCORE_COL].mean()
        fila["CORTES"] = sub["_cortes"].mode().iloc[0] if not sub["_cortes"].mode().empty else ""
        fila["quintil"] = sub["_quint"].mode().iloc[0] if not sub["_quint"].mode().empty else ""
        filas.append(fila)

    tab = pd.DataFrame(filas).sort_values(
        "score_medio", ascending=not SCORE_ALTO_ES_MENOR_RIESGO).reset_index(drop=True)

    bold = Font(bold=True)
    ws.cell(r0, c0, "CUADRO DEL ÁRBOL COMPLETO (una fila = una hoja)").font = Font(bold=True, size=12)
    cols = usadas + ["n", "%", "score_medio", "CORTES", "quintil"]
    for j, h in enumerate(cols):
        c = ws.cell(r0 + 1, c0 + j, h)
        c.font = bold; c.border = BORDER
        c.alignment = Alignment(horizontal="center", wrap_text=True)
    for i in range(len(tab)):
        for j, h in enumerate(cols):
            cell = ws.cell(r0 + 2 + i, c0 + j)
            cell.border = BORDER
            val = tab.iloc[i][h]
            if h == "score_medio":
                cell.value = round(float(val), 0)
                cell.fill = PatternFill("solid", fgColor=hex_color(norm_score(val, vmin, vmax)))
                cell.alignment = Alignment(horizontal="center")
            elif h in ("n", "%"):
                cell.value = float(val) if h == "%" else int(val)
                cell.alignment = Alignment(horizontal="center")
            else:
                cell.value = str(val)
                cell.alignment = Alignment(horizontal="center")
    for j, h in enumerate(cols):
        ws.column_dimensions[get_column_letter(c0 + j)].width = 18 if h in usadas else 12
    return r0 + 3 + len(tab)


# =============================================================================
# Procesa un escenario -> una hoja
# =============================================================================
def procesar_escenario(wb, nombre_hoja, df_sc, metodologia):
    ws = wb.create_sheet(title=nombre_hoja[:31])
    if len(df_sc) < 50:
        ws.cell(1, 1, f"Escenario con muy pocos casos ({len(df_sc)}). Se omite.")
        return

    y = pd.to_numeric(df_sc[SCORE_COL], errors="coerce").values
    X, miss, feats = construir_X(df_sc)

    cst = (mono_por_spearman(X, miss, y, feats) if metodologia == "A"
           else mono_por_optbinning(df_sc, X, miss, y, feats))
    tree = entrenar_arbol(X, y, cst)

    vmin, vmax = np.nanmin(y), np.nanmax(y)

    # Imagen del árbol
    png = f"_tree_{nombre_hoja}.png"
    pintar_arbol(tree, feats, png, vmin, vmax)

    ws.cell(1, 1, f"ESCENARIO: {nombre_hoja}").font = Font(bold=True, size=14)
    ws.cell(2, 1, f"n = {len(df_sc)}   |   puntaje_mod medio = {np.nanmean(y):,.0f}"
                  f"   |   metodología = {'Solo árbol' if metodologia=='A' else 'Optbinning+árbol'}")
    ws.cell(3, 1, f"monotonic_cst: {dict(zip(feats, cst))}")
    try:
        img = XLImage(png); img.width = 1100; img.height = 520
        ws.add_image(img, "A5")
    except Exception as e:
        ws.cell(5, 1, f"(no se pudo insertar imagen: {e})")

    # Cuadros debajo de la imagen
    vfil, vcol, cant, riesgo = construir_cuadros(df_sc, X, miss, tree, feats)
    fila = 34
    fila = escribir_cuadro(ws, fila, 1, "CUADRO POR CANTIDAD", cant, vfil, vcol,
                           colorear="cantidad") + 2
    fila = escribir_cuadro(ws, fila, 1, "CUADRO POR RIESGO (prom puntaje_mod)", riesgo,
                           vfil, vcol, colorear="riesgo", vmin=vmin, vmax=vmax) + 2
    escribir_tabla_arbol(ws, fila, 1, df_sc, X, tree, feats, vmin, vmax)


# =============================================================================
# MAIN
# =============================================================================
def escenarios(df):
    out = []
    for v in VALORES_FLG:
        base = df[df[FLG_COL] == v]
        out.append((f"{v}"[:24], base))
        if FAR_COL in df.columns:
            far = base[pd.to_numeric(base[FAR_COL], errors="coerce") == 1]
            out.append((f"{v}_far1"[:28], far))
    return out


def construir_workbook(df, metodologia, ruta):
    wb = Workbook()
    wb.remove(wb.active)
    idx = wb.create_sheet("Índice")
    idx.cell(1, 1, f"Desagregación de riesgo — {'Solo árbol' if metodologia=='A' else 'Optbinning + árbol'}").font = Font(bold=True, size=14)
    idx.cell(2, 1, "proxy de riesgo: puntaje_mod (alto = menor riesgo)")
    r = 4
    for nombre, sub in escenarios(df):
        nombre = nombre.replace(">", "ge").replace("=", "").replace("/", "_")
        procesar_escenario(wb, nombre, sub, metodologia)
        idx.cell(r, 1, f"• {nombre}  (n={len(sub)})"); r += 1
    wb.save(ruta)
    print(f"Generado: {ruta}")


def main():
    df = load_data()
    construir_workbook(df, "A", "arbol_solo.xlsx")
    construir_workbook(df, "B", "optbinning_arbol.xlsx")
    print("\nListo: arbol_solo.xlsx y optbinning_arbol.xlsx")


if __name__ == "__main__":
    main()
