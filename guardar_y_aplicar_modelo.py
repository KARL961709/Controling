# ====================================================================================
# GUARDAR EL MODELO (árboles + optbinning) Y APLICARLO A UNA BASE NUEVA
# ====================================================================================
# Idea general
# ------------
# 1) Durante el entrenamiento guardamos, por cada ESCENARIO, un "modelo_sc" con:
#       - tree            : el DecisionTreeRegressor entrenado
#       - feats           : orden EXACTO de columnas que vio el árbol
#       - optbs           : dict {variable: objeto optbinning}  -> crudo -> WoE
#       - usa_woe         : si las numéricas entran como WoE o crudas
#       - cst             : monotonic_cst (solo informativo)
#       - woemap          : para reconstruir las etiquetas/reglas
#       - leafmap         : nodo -> condiciones
#       - leaf_val        : leaf_id -> target medio (riesgo de la hoja)
#       - regla_txt       : leaf_id -> regla legible
#    Y a nivel GLOBAL guardamos el ranking de estrategias (leaf_key -> nº estrategia).
#
# 2) Para aplicar a una base nueva (variables CRUDAS):
#       - reconstruimos las mismas features (igual que en procesar_escenario),
#       - pasamos a WoE con el MISMO optb guardado,
#       - corremos tree.apply() -> hoja -> leaf_key -> estrategia.
#
# Requiere que las constantes/funciones del notebook estén importadas/definidas
# (TGT, SIGN, SENTINEL, NUM_VARS, ORD_VAR, etc. y banda_cortes_vec, cond_label, ...).
# Para que el archivo del modelo sea autónomo, también snapshot-eamos la config.
# ====================================================================================

import numpy as np
import pandas as pd
import joblib


# ------------------------------------------------------------------------------------
# (A) Reutilizable: arma las features crudas IGUAL que procesar_escenario
# ------------------------------------------------------------------------------------
def construir_raw(df_sc, excluir=()):
    """Devuelve (raw: dict col->Series, feats: list) replicando procesar_escenario."""
    num = [c for c in NUM_VARS if c in df_sc.columns and c not in excluir and c != TARGET_COL]
    raw = {c: pd.to_numeric(df_sc[c], errors="coerce") for c in num}
    feats = list(num)

    if ORD_VAR in df_sc.columns:
        raw[ORD_VAR] = df_sc[ORD_VAR].map({f"G{i}": i for i in range(1, 9)})
        feats.append(ORD_VAR)

    if USA_SCORE_FEATURE and SCORE_COL in df_sc.columns and SIT_COL in df_sc.columns:
        bandas = banda_cortes_vec(pd.to_numeric(df_sc[SCORE_COL], errors="coerce").values,
                                  df_sc[SIT_COL].values)
        raw[SCORE_BANDA] = pd.Series(bandas, index=df_sc.index).map({f"G{i}": i for i in range(1, 6)})
        feats.append(SCORE_BANDA)

    for c in VARS_DIRECTAS:
        if c in df_sc.columns and c not in excluir and c != TARGET_COL and c not in feats:
            raw[c] = pd.to_numeric(df_sc[c], errors="coerce")
            feats.append(c)

    return raw, feats


# ------------------------------------------------------------------------------------
# (B) Transforma una base nueva con UN modelo de escenario -> X listo para el árbol
# ------------------------------------------------------------------------------------
def transformar_base(df_sc, modelo_sc, excluir=()):
    """Crudo -> WoE/crudo en el mismo orden que vio el árbol."""
    feats = modelo_sc["feats"]
    optbs = modelo_sc["optbs"]
    usa_woe = modelo_sc["usa_woe"]
    imputa = modelo_sc.get("imputa_missing", {})   # {var: WoE de mayor riesgo}
    raw, _ = construir_raw(df_sc, excluir)

    Xcols, misscol = {}, {}
    for c in feats:
        serie = raw.get(c)
        if serie is None:               # la columna no existe en la base nueva
            serie = pd.Series(np.nan, index=df_sc.index)

        if usa_woe and c in optbs:
            optb = optbs[c]
            try:
                col = optb.transform(serie.values, metric="woe")
            except Exception:
                col = optb.transform(serie.values, metric="mean")
            col = np.asarray(col, dtype=float)
            # mismo criterio del entrenamiento: missing -> WoE del bin de mayor riesgo
            woe_peor = imputa.get(c)
            if woe_peor is not None:
                col[serie.isna().values] = woe_peor
            Xcols[c] = col
            misscol[c] = np.zeros(len(df_sc), dtype=bool)
        else:
            Xcols[c] = serie.fillna(SENTINEL).values
            misscol[c] = serie.isna().values

    X = pd.DataFrame({c: Xcols[c] for c in feats}, index=df_sc.index)
    return X


# ------------------------------------------------------------------------------------
# (C) APLICA TODO EL MODELO a una base nueva y devuelve la columna "estrategia"
# ------------------------------------------------------------------------------------
def aplicar_modelo(df_nuevo, modelo, excluir=()):
    """
    df_nuevo : base con variables CRUDAS (mismas columnas de origen que el entrenamiento)
    modelo   : dict cargado con joblib.load(...)
    Devuelve df_nuevo + columnas: leaf_key, leaf_val (riesgo de la hoja), regla, estrategia.
    Si un cliente cae en varios escenarios, se queda con el de MENOR riesgo (igual que _dedup).
    """
    sign = modelo["config"]["SIGN"]
    rank = modelo["estrategia_rank"]          # leaf_key -> nº de estrategia
    subject_col = modelo["config"]["SUBJECT_COL"]

    piezas = []
    # construir_escenarios usa los MISMOS globals del notebook -> mismos cortes/segmentos
    for nombre, sub in construir_escenarios(df_nuevo):
        modelo_sc = modelo["escenarios"].get(nombre)
        if modelo_sc is None or len(sub) == 0:
            continue
        X = transformar_base(sub, modelo_sc, excluir)
        leaf_id = modelo_sc["tree"].apply(X)
        leaf_val = np.array([modelo_sc["leaf_val"].get(l, np.nan) for l in leaf_id])
        sid = sub[subject_col].values if subject_col in sub.columns else sub.index.values
        piezas.append(pd.DataFrame({
            "subject_id": sid,
            "escenario": nombre,
            "leaf_key": [f"{nombre}#{l}" for l in leaf_id],
            "regla": [modelo_sc["regla_txt"].get(l, "") for l in leaf_id],
            "leaf_val": leaf_val,
            "_orig_index": sub.index.values,
        }))

    if not piezas:
        out = df_nuevo.copy()
        out["leaf_key"] = out["regla"] = ""
        out["leaf_val"] = np.nan
        out["estrategia"] = np.nan
        return out

    pool = pd.concat(piezas, ignore_index=True)
    pool["estrategia"] = pool["leaf_key"].map(rank)

    # Cada cliente -> su segmento de MENOR riesgo (idéntico a _dedup del entrenamiento)
    pool["_risk"] = sign * pool["leaf_val"]
    pool = (pool.sort_values("_risk", ascending=True)
                .drop_duplicates("subject_id", keep="first")
                .drop(columns="_risk"))

    out = df_nuevo.copy()
    asignado = pool.set_index("_orig_index")[["leaf_key", "regla", "leaf_val", "escenario", "estrategia"]]
    for col in ["leaf_key", "regla", "leaf_val", "escenario", "estrategia"]:
        out[col] = asignado[col].reindex(out.index)
    return out


# ------------------------------------------------------------------------------------
# (D) Cargar el modelo guardado
# ------------------------------------------------------------------------------------
def cargar_modelo(ruta):
    return joblib.load(ruta)
