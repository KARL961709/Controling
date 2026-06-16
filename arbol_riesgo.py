"""
Árbol de decisión para segmentar clientes por riesgo (score como proxy)
=======================================================================

No hay target real -> se usa el SCORE como variable objetivo (proxy de riesgo).
El árbol aprende reglas sobre tus variables numéricas y categóricas para
separar clientes con distinto nivel de score, y se exporta como IMAGEN.

Genera dos imágenes:
  - arbol_regresion.png      : árbol de REGRESIÓN (predice el score continuo).
                               Cada hoja = un segmento con su score medio.
  - arbol_clasificacion.png  : árbol de CLASIFICACIÓN sobre bandas de riesgo
                               (Bajo/Medio/Alto), coloreado por clase.

CÓMO USAR
---------
1) Ajusta la sección CONFIG (ruta del CSV y nombres de columnas).
2) pip install pandas numpy scikit-learn matplotlib
3) python arbol_riesgo.py
"""

import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")               # backend sin pantalla -> guarda a archivo
import matplotlib.pyplot as plt

from sklearn.tree import DecisionTreeRegressor, DecisionTreeClassifier, plot_tree
from sklearn.preprocessing import OrdinalEncoder

warnings.filterwarnings("ignore")

# =============================================================================
# CONFIG  --  EDITA ESTO
# =============================================================================
CSV_PATH  = "clientes.csv"          # ruta a tu archivo
SCORE_COL = "score"                 # columna del puntaje (proxy de riesgo)

NUM_COLS = ["edad", "ingreso", "antiguedad", "monto", "ratio_deuda"]   # numéricas
CAT_COLS = ["genero", "region", "producto", "estado_civil"]            # categóricas

MAX_DEPTH        = 3        # profundidad del árbol (3-4 = legible). Sube para más detalle.
MIN_SAMPLES_LEAF = 0.05     # mínimo 5% de clientes por hoja (evita hojas diminutas)
N_BANDAS         = 3        # bandas de riesgo para el árbol de clasificación
RANDOM_STATE     = 42


# =============================================================================
# Preparación de datos
# =============================================================================
def preparar():
    df = pd.read_csv(CSV_PATH)

    num = [c for c in NUM_COLS if c in df.columns]
    cat = [c for c in CAT_COLS if c in df.columns]
    print(f"Datos: {df.shape[0]} filas | numéricas={num} | categóricas={cat}")

    df = df.dropna(subset=[SCORE_COL] + num + cat).copy()

    # Codificación de categóricas (ordinal): el árbol parte por umbrales numéricos.
    X = df[num + cat].copy()
    if cat:
        enc = OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)
        X[cat] = enc.fit_transform(X[cat].astype(str))
        # Guarda el mapeo código -> categoría para leerlo en la imagen si hace falta
        for c, cats in zip(cat, enc.categories_):
            mapping = {i: v for i, v in enumerate(cats)}
            print(f"  [{c}] codificación: {mapping}")

    feat_names = num + cat
    return df, X, feat_names


# =============================================================================
# 1) Árbol de REGRESIÓN  (score continuo)
# =============================================================================
def arbol_regresion(df, X, feat_names):
    print("\n=== Árbol de regresión (score como proxy de riesgo) ===")
    y = df[SCORE_COL].values

    tree = DecisionTreeRegressor(
        max_depth=MAX_DEPTH,
        min_samples_leaf=MIN_SAMPLES_LEAF,
        random_state=RANDOM_STATE,
    )
    tree.fit(X, y)
    df["segmento_reg"] = tree.apply(X)        # id de hoja = segmento

    # Resumen de segmentos ordenados por score medio
    resumen = (
        df.groupby("segmento_reg")[SCORE_COL]
        .agg(n="count", score_medio="mean", score_min="min", score_max="max")
        .sort_values("score_medio")
    )
    print(resumen.round(2))

    plt.figure(figsize=(22, 11))
    plot_tree(
        tree, feature_names=feat_names, filled=True, rounded=True,
        impurity=False, precision=2, fontsize=10,
    )
    plt.title("Árbol de regresión — segmentación por score (proxy de riesgo)")
    plt.tight_layout()
    plt.savefig("arbol_regresion.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Imagen guardada: arbol_regresion.png")
    return df


# =============================================================================
# 2) Árbol de CLASIFICACIÓN  (bandas de riesgo a partir del score)
# =============================================================================
def arbol_clasificacion(df, X, feat_names):
    print("\n=== Árbol de clasificación (bandas de riesgo) ===")
    etiquetas = ["Bajo", "Medio", "Alto"][:N_BANDAS]
    # OJO: ajusta el orden si en tu escala score ALTO = MENOS riesgo
    df["banda_riesgo"] = pd.qcut(df[SCORE_COL], q=N_BANDAS, labels=etiquetas)

    y = df["banda_riesgo"].astype(str).values
    tree = DecisionTreeClassifier(
        max_depth=MAX_DEPTH,
        min_samples_leaf=MIN_SAMPLES_LEAF,
        random_state=RANDOM_STATE,
    )
    tree.fit(X, y)

    print("Distribución de bandas:\n", df["banda_riesgo"].value_counts())

    plt.figure(figsize=(22, 11))
    plot_tree(
        tree, feature_names=feat_names, class_names=tree.classes_,
        filled=True, rounded=True, impurity=False, precision=2, fontsize=10,
    )
    plt.title("Árbol de clasificación — bandas de riesgo (Bajo/Medio/Alto)")
    plt.tight_layout()
    plt.savefig("arbol_clasificacion.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("Imagen guardada: arbol_clasificacion.png")

    # Variables más importantes para separar el riesgo
    imp = pd.Series(tree.feature_importances_, index=feat_names).sort_values(ascending=False)
    print("\nImportancia de variables:\n", imp[imp > 0].round(3))
    return df


# =============================================================================
# MAIN
# =============================================================================
def main():
    df, X, feat_names = preparar()
    df = arbol_regresion(df, X, feat_names)
    df = arbol_clasificacion(df, X, feat_names)

    df.to_csv("clientes_segmentados.csv", index=False)
    print("\nListo. Revisa las imágenes .png y 'clientes_segmentados.csv'.")


if __name__ == "__main__":
    main()
