"""
Segmentación de clientes por nivel de riesgo
============================================

Cubre varios enfoques, de más interpretable a más avanzado:

  1. Segmentación por cuantiles del score (deciles / rating grades)
  2. Binning óptimo supervisado del score (WoE / IV)        [requiere etiqueta de default]
  3. Discretización óptima del score con árbol de decisión   [requiere etiqueta]
  4. Clustering K-Prototypes (numéricas + categóricas)
  5. Gaussian Mixture (segmentos "suaves" con probabilidad)
  6. Drivers de riesgo con Gradient Boosting + SHAP          [requiere etiqueta]

CÓMO USAR
---------
1) Ajusta la sección CONFIG (ruta del CSV y nombres de columnas).
2) Instala dependencias:
     pip install pandas numpy scikit-learn matplotlib
     pip install kmodes            # para K-Prototypes
     pip install optbinning        # para binning óptimo (WoE/IV)
     pip install shap xgboost      # para drivers de riesgo
3) Ejecuta:  python segmentacion_riesgo.py
   Algunos bloques se saltan solos si falta la librería o la etiqueta.
"""

import warnings
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# =============================================================================
# CONFIG  --  EDITA ESTO
# =============================================================================
CSV_PATH   = "clientes.csv"          # ruta a tu archivo
SCORE_COL  = "score"                 # columna del puntaje de riesgo
TARGET_COL = "default"               # etiqueta 0/1 (malo=1). Pon None si no la tienes.

NUM_COLS = ["edad", "ingreso", "antiguedad", "monto", "ratio_deuda"]   # numéricas
CAT_COLS = ["genero", "region", "producto", "estado_civil"]            # categóricas

N_SEGMENTS = 5      # nº de segmentos/clusters deseados
RANDOM_STATE = 42


# =============================================================================
# Carga de datos
# =============================================================================
def load_data():
    df = pd.read_csv(CSV_PATH)
    # Filtra a columnas existentes para evitar errores si la config no calza 100%
    global NUM_COLS, CAT_COLS, TARGET_COL
    NUM_COLS = [c for c in NUM_COLS if c in df.columns]
    CAT_COLS = [c for c in CAT_COLS if c in df.columns]
    if TARGET_COL and TARGET_COL not in df.columns:
        print(f"[aviso] No existe '{TARGET_COL}'; se omiten métodos supervisados.")
        TARGET_COL = None
    print(f"Datos: {df.shape[0]} filas, {df.shape[1]} columnas")
    return df


# =============================================================================
# 1) Cuantiles del score  ->  rating grades
# =============================================================================
def segmentar_por_cuantiles(df, n=N_SEGMENTS):
    print("\n=== 1) Segmentación por cuantiles del score ===")
    labels = [f"R{i+1}" for i in range(n)]          # R1 = mejor ... Rn = peor (ajusta a tu escala)
    df["seg_cuantil"] = pd.qcut(df[SCORE_COL], q=n, labels=labels, duplicates="drop")

    resumen = df.groupby("seg_cuantil", observed=True)[SCORE_COL].agg(["count", "min", "max", "mean"])
    if TARGET_COL:
        resumen["tasa_default"] = df.groupby("seg_cuantil", observed=True)[TARGET_COL].mean()
    print(resumen.round(3))
    return df


# =============================================================================
# 2) Binning óptimo del score (WoE / IV)  -- requiere etiqueta
# =============================================================================
def binning_optimo(df):
    if not TARGET_COL:
        return df
    try:
        from optbinning import OptimalBinning
    except ImportError:
        print("\n[2] omitido: instala 'optbinning' (pip install optbinning)")
        return df

    print("\n=== 2) Binning óptimo del score (WoE / IV) ===")
    optb = OptimalBinning(name=SCORE_COL, dtype="numerical", solver="cp")
    optb.fit(df[SCORE_COL].values, df[TARGET_COL].values)

    df["seg_woe"] = optb.transform(df[SCORE_COL].values, metric="bins")
    tabla = optb.binning_table.build()
    print(tabla)
    print(f"IV (poder predictivo del score): {optb.binning_table.iv:.4f}")
    # Guía IV:  <0.02 inútil | 0.1-0.3 medio | 0.3-0.5 fuerte | >0.5 sospechoso
    return df


# =============================================================================
# 3) Discretización óptima del score con árbol  -- requiere etiqueta
# =============================================================================
def cortes_con_arbol(df):
    if not TARGET_COL:
        return df
    from sklearn.tree import DecisionTreeClassifier

    print("\n=== 3) Cortes del score con árbol de decisión ===")
    tree = DecisionTreeClassifier(
        max_leaf_nodes=N_SEGMENTS, min_samples_leaf=0.05, random_state=RANDOM_STATE
    )
    tree.fit(df[[SCORE_COL]], df[TARGET_COL])

    thr = sorted(t for t in tree.tree_.threshold if t != -2)   # -2 = nodo hoja
    edges = [-np.inf] + thr + [np.inf]
    df["seg_arbol"] = pd.cut(df[SCORE_COL], bins=edges)
    print("Puntos de corte sugeridos:", [round(t, 3) for t in thr])

    resumen = df.groupby("seg_arbol", observed=True)[TARGET_COL].agg(["count", "mean"])
    resumen.columns = ["n", "tasa_default"]
    print(resumen.round(3))
    return df


# =============================================================================
# 4) K-Prototypes  (numéricas + categóricas juntas)
# =============================================================================
def clustering_kprototypes(df, n=N_SEGMENTS):
    if not (NUM_COLS and CAT_COLS):
        print("\n[4] omitido: se necesitan columnas numéricas y categóricas.")
        return df
    try:
        from kmodes.kprototypes import KPrototypes
    except ImportError:
        print("\n[4] omitido: instala 'kmodes' (pip install kmodes)")
        return df
    from sklearn.preprocessing import StandardScaler

    print("\n=== 4) Clustering K-Prototypes ===")
    work = df[NUM_COLS + CAT_COLS].dropna().copy()
    work[NUM_COLS] = StandardScaler().fit_transform(work[NUM_COLS])
    work[CAT_COLS] = work[CAT_COLS].astype(str)

    matrix = work.values
    cat_idx = [work.columns.get_loc(c) for c in CAT_COLS]

    kp = KPrototypes(n_clusters=n, init="Huang", random_state=RANDOM_STATE, n_init=5)
    work["cluster"] = kp.fit_predict(matrix, categorical=cat_idx)
    df.loc[work.index, "seg_kproto"] = work["cluster"].values

    # Perfilado de cada cluster
    perfil = df.dropna(subset=["seg_kproto"]).groupby("seg_kproto")
    print("Tamaño por cluster:\n", perfil.size())
    print("\nMedia de score por cluster:\n", perfil[SCORE_COL].mean().round(2))
    if TARGET_COL:
        print("\nTasa de default por cluster:\n", perfil[TARGET_COL].mean().round(3))
    return df


# =============================================================================
# 5) Gaussian Mixture  (segmentos suaves)
# =============================================================================
def clustering_gmm(df, n=N_SEGMENTS):
    if not NUM_COLS:
        print("\n[5] omitido: se necesitan columnas numéricas.")
        return df
    from sklearn.preprocessing import StandardScaler
    from sklearn.mixture import GaussianMixture

    print("\n=== 5) Gaussian Mixture (probabilístico) ===")
    feats = NUM_COLS + ([SCORE_COL] if SCORE_COL not in NUM_COLS else [])
    work = df[feats].dropna()
    X = StandardScaler().fit_transform(work)

    gmm = GaussianMixture(n_components=n, covariance_type="full", random_state=RANDOM_STATE)
    df.loc[work.index, "seg_gmm"] = gmm.fit_predict(X)
    df.loc[work.index, "prob_seg_gmm"] = gmm.predict_proba(X).max(axis=1)

    grp = df.dropna(subset=["seg_gmm"]).groupby("seg_gmm")
    print("Media de score por componente:\n", grp[SCORE_COL].mean().round(2))
    if TARGET_COL:
        print("\nTasa de default por componente:\n", grp[TARGET_COL].mean().round(3))
    return df


# =============================================================================
# 6) Drivers de riesgo: Gradient Boosting + SHAP  -- requiere etiqueta
# =============================================================================
def drivers_riesgo(df):
    if not TARGET_COL:
        return
    try:
        import shap
        from xgboost import XGBClassifier
    except ImportError:
        print("\n[6] omitido: instala 'shap' y 'xgboost'")
        return
    from sklearn.model_selection import train_test_split

    print("\n=== 6) Drivers de riesgo (XGBoost + SHAP) ===")
    X = pd.get_dummies(df[NUM_COLS + CAT_COLS], drop_first=True)
    y = df[TARGET_COL]
    mask = X.notna().all(axis=1) & y.notna()
    X, y = X[mask], y[mask]

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.25, stratify=y, random_state=RANDOM_STATE
    )
    model = XGBClassifier(
        n_estimators=300, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8,
        eval_metric="auc", random_state=RANDOM_STATE,
    )
    model.fit(X_tr, y_tr)

    from sklearn.metrics import roc_auc_score
    auc = roc_auc_score(y_te, model.predict_proba(X_te)[:, 1])
    print(f"AUC test: {auc:.3f}")

    explainer = shap.TreeExplainer(model)
    sv = explainer.shap_values(X_te)
    imp = pd.Series(np.abs(sv).mean(axis=0), index=X_te.columns).sort_values(ascending=False)
    print("\nTop variables que explican el riesgo:")
    print(imp.head(15).round(4))


# =============================================================================
# MAIN
# =============================================================================
def main():
    df = load_data()
    df = segmentar_por_cuantiles(df)
    df = binning_optimo(df)
    df = cortes_con_arbol(df)
    df = clustering_kprototypes(df)
    df = clustering_gmm(df)
    drivers_riesgo(df)

    out = "clientes_segmentados.csv"
    df.to_csv(out, index=False)
    print(f"\nListo. Resultado guardado en '{out}'.")


if __name__ == "__main__":
    main()
