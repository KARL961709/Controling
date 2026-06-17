"""
Segmentación de riesgo con SCORE CONTINUO (sin binarizar)
=========================================================

El WoE clásico necesita target binario. Con score continuo se usa su análogo:
la MEDIA del score por tramo/celda (mean target encoding), con monotonía.

Incluye:
  A) Árbol de REGRESIÓN MONÓTONO  -> segmentos multivariados + score medio por hoja
                                     (captura interacciones; análogo a "WoE por hoja")
  B) Binning monótono 1D por variable  (optbinning.ContinuousOptimalBinning)
  C) Binning monótono 2D de un par     (optbinning.ContinuousOptimalBinning2D)
                                     <- tu idea de "WoE 2D" en versión continua

CÓMO USAR
---------
1) Ajusta CONFIG (CSV, columnas, dirección del riesgo).
2) pip install pandas numpy scikit-learn matplotlib
   pip install optbinning          # para B) y C)
3) python woe_continuo_arbol.py

REQUISITO: scikit-learn >= 1.4  (para monotonic_cst en el árbol)
"""

import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeRegressor, plot_tree
from sklearn.preprocessing import OrdinalEncoder

warnings.filterwarnings("ignore")

# =============================================================================
# CONFIG  --  EDITA ESTO
# =============================================================================
CSV_PATH  = "clientes.csv"
SCORE_COL = "score"

NUM_COLS = ["edad", "ingreso", "antiguedad", "monto", "ratio_deuda"]
CAT_COLS = ["genero", "region", "producto"]

# Dirección del riesgo:
#   True  -> score ALTO = MENOR riesgo (escala crediticia 300-850). G1 = mejor.
#   False -> score ALTO = MAYOR riesgo.
SCORE_ALTO_ES_MENOR_RIESGO = True

# Direcciones de monotonía del árbol, por variable (sobre el SCORE):
#   +1 : a mayor variable, mayor score   |  -1 : a mayor variable, menor score  |  0 : sin restricción
# Ej: ingreso +1, antiguedad +1, ratio_deuda -1
MONOTONIA = {
    "ingreso": +1,
    "antiguedad": +1,
    "ratio_deuda": -1,
}

PAR_2D   = ("ratio_deuda", "ingreso")   # par para el binning 2D
N_BANDAS = 5
MAX_DEPTH = 3
MIN_SAMPLES_LEAF = 0.05
RANDOM_STATE = 42


# =============================================================================
def preparar():
    df = pd.read_csv(CSV_PATH)
    num = [c for c in NUM_COLS if c in df.columns]
    cat = [c for c in CAT_COLS if c in df.columns]
    df = df.dropna(subset=[SCORE_COL] + num + cat).copy()

    X = df[num + cat].copy()
    if cat:
        enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        X[cat] = enc.fit_transform(X[cat].astype(str))
    feat_names = num + cat

    # Vector de restricciones monótonas alineado a las columnas de X
    mono = [MONOTONIA.get(c, 0) for c in feat_names]
    print(f"Datos: {len(df)} filas | features={feat_names}")
    print(f"monotonic_cst = {dict(zip(feat_names, mono))}")
    return df, X, feat_names, mono


# =============================================================================
# A) Árbol de regresión MONÓTONO  ->  score medio por hoja
# =============================================================================
def arbol_monotono(df, X, feat_names, mono):
    print("\n=== A) Árbol de regresión monótono (score medio por hoja) ===")
    y = df[SCORE_COL].values
    try:
        tree = DecisionTreeRegressor(
            max_depth=MAX_DEPTH, min_samples_leaf=MIN_SAMPLES_LEAF,
            monotonic_cst=mono, random_state=RANDOM_STATE,
        )
        tree.fit(X, y)
    except TypeError:
        print("[aviso] tu sklearn no soporta monotonic_cst (<1.4). Entreno sin restricción.")
        tree = DecisionTreeRegressor(
            max_depth=MAX_DEPTH, min_samples_leaf=MIN_SAMPLES_LEAF,
            random_state=RANDOM_STATE,
        ).fit(X, y)

    df["hoja"] = tree.apply(X)

    # score medio por hoja -> ordenar -> mapear a bandas G1..Gn
    medias = df.groupby("hoja")[SCORE_COL].mean().sort_values(
        ascending=not SCORE_ALTO_ES_MENOR_RIESGO  # peor riesgo primero
    )
    # G1 = menor riesgo. Si score alto = menor riesgo, G1 es la hoja de mayor media.
    orden_hojas = (medias.sort_values(ascending=False).index
                   if SCORE_ALTO_ES_MENOR_RIESGO
                   else medias.sort_values(ascending=True).index)
    banda_map = {h: f"G{i+1}" for i, h in enumerate(orden_hojas)}
    df["banda"] = df["hoja"].map(banda_map)

    resumen = (df.groupby("banda")[SCORE_COL]
               .agg(n="count", score_medio="mean", score_min="min", score_max="max")
               .reindex([f"G{i+1}" for i in range(len(banda_map))]))
    print(resumen.round(2))

    plt.figure(figsize=(22, 11))
    plot_tree(tree, feature_names=feat_names, filled=True, rounded=True,
              impurity=False, precision=2, fontsize=10)
    plt.title("Árbol de regresión monótono — score como proxy de riesgo")
    plt.tight_layout()
    plt.savefig("arbol_monotono.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Imagen guardada: arbol_monotono.png")
    return df


# =============================================================================
# B) Binning monótono 1D por variable  (target continuo)
# =============================================================================
def binning_1d(df):
    try:
        from optbinning import ContinuousOptimalBinning
    except ImportError:
        print("\n[B] omitido: pip install optbinning")
        return
    print("\n=== B) Binning monótono 1D por variable (media de score) ===")
    trend = "descending" if SCORE_ALTO_ES_MENOR_RIESGO else "ascending"
    for var in NUM_COLS:
        if var not in df.columns:
            continue
        optb = ContinuousOptimalBinning(name=var, monotonic_trend="auto")
        optb.fit(df[var].values, df[SCORE_COL].values)
        print(f"\n--- {var} ---")
        print(optb.binning_table.build().round(2))


# =============================================================================
# C) Binning monótono 2D de un par  (tu "WoE 2D" continuo)
# =============================================================================
def binning_2d(df):
    try:
        from optbinning import ContinuousOptimalBinning2D
    except ImportError:
        print("\n[C] omitido: pip install optbinning")
        return
    v1, v2 = PAR_2D
    if v1 not in df.columns or v2 not in df.columns:
        print(f"\n[C] omitido: {PAR_2D} no están en los datos.")
        return
    print(f"\n=== C) Binning monótono 2D: {v1} x {v2} (media de score) ===")
    optb = ContinuousOptimalBinning2D(name_x=v1, name_y=v2)
    optb.fit(df[v1].values, df[v2].values, df[SCORE_COL].values)
    print(optb.binning_table.build().round(2))


# =============================================================================
def main():
    df, X, feat_names, mono = preparar()
    df = arbol_monotono(df, X, feat_names, mono)
    binning_1d(df)
    binning_2d(df)
    df.to_csv("clientes_segmentados.csv", index=False)
    print("\nListo. Revisa 'arbol_monotono.png' y 'clientes_segmentados.csv'.")


if __name__ == "__main__":
    main()
