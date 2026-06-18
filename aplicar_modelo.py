"""
Reaplica un modelo de estrategias (.pkl generado por el script V4) a una base nueva.

Uso rápido:
    import pandas as pd
    from aplicar_modelo import aplicar_modelo

    df_nuevo = pd.read_csv("base_nueva.csv")
    res = aplicar_modelo("optbinning_arbol_RD_V4_modelo.pkl", df_nuevo)
    # res tiene, por cada fila de df_nuevo, las columnas:
    #   <subject_id>, escenario, leaf, valor_predicho, regla, nro_estrategia, cumple_apetito
"""
import numpy as np
import pandas as pd
import joblib


def _reconstruir_X(df, modelo, cfg):
    """Reconstruye la matriz de features EXACTAMENTE como en el entrenamiento."""
    feats   = modelo["feats"]
    optbs   = modelo.get("optbs", {})
    usa_woe = modelo.get("usa_woe", False)
    imputa  = modelo.get("imputa_missing", {})
    ORD_VAR  = cfg.get("ORD_VAR")
    SENTINEL = cfg.get("SENTINEL", -99999999)

    cols = {}
    for var in feats:
        # 1) serie cruda igual que en entrenamiento
        if var == ORD_VAR:
            serie = df.get(var, pd.Series(index=df.index, dtype=object)) \
                      .map({f"G{i}": i for i in range(1, 9)})
            serie = pd.to_numeric(serie, errors="coerce")
        else:
            serie = pd.to_numeric(df.get(var, np.nan), errors="coerce")
        serie = serie.reindex(df.index)

        # 2) transformación
        if var in optbs and usa_woe:
            try:
                col = optbs[var].transform(serie.values, metric="woe")
            except Exception:
                col = optbs[var].transform(serie.values, metric="mean")
            col = np.asarray(col, dtype=float)
            if var in imputa:                       # imputación de missing del entrenamiento
                col[serie.isna().values] = imputa[var]
        else:                                       # método A, B sin WoE, directas/ordinales
            col = serie.fillna(SENTINEL).values.astype(float)
        cols[var] = col
    return pd.DataFrame(cols, columns=feats, index=df.index)


def aplicar_un_escenario(df, nombre, modelo, cfg, estrategia_rank):
    """Aplica el modelo de UN escenario a todo el df que se le pase."""
    X = _reconstruir_X(df, modelo, cfg)
    leaf = modelo["tree"].apply(X.values)

    leaf_val  = modelo["leaf_val"]
    regla_txt = modelo["regla_txt"]
    SIGN    = cfg["SIGN"]
    APETITO = cfg["APETITO"]

    valor = np.array([leaf_val.get(l, np.nan) for l in leaf], dtype=float)
    out = pd.DataFrame({
        cfg.get("SUBJECT_COL", "subject_id"):
            df[cfg["SUBJECT_COL"]].values if cfg.get("SUBJECT_COL") in df.columns else df.index.values,
        "escenario": nombre,
        "leaf": leaf,
        "valor_predicho": valor,                                   # RD o score del segmento
        "regla": [regla_txt.get(l, "") for l in leaf],
        "nro_estrategia": [estrategia_rank.get(f"{nombre}#{l}", np.nan) for l in leaf],
        # un cliente "cumple" si su segmento pasa el apetito (RD<=apetito ó score>=apetito)
        "cumple_apetito": (SIGN * valor) <= (SIGN * APETITO),
    }, index=df.index)
    return out


def aplicar_modelo(pkl_path, df, escenario=None):
    """
    Reaplica el .pkl a una base nueva.

    pkl_path  : ruta del *_modelo.pkl
    df        : DataFrame nuevo (debe traer las columnas predictoras y el subject_id)
    escenario : nombre del escenario a usar. Si None y hay 1 solo, se usa ese;
                si hay varios, se aplica CADA escenario y se concatena.
    """
    bundle = joblib.load(pkl_path)
    cfg    = bundle["config"]
    rank   = bundle.get("estrategia_rank", {})
    escen  = bundle["escenarios"]

    if escenario is not None:
        if escenario not in escen:
            raise KeyError(f"Escenario '{escenario}' no está. Disponibles: {list(escen)}")
        return aplicar_un_escenario(df, escenario, escen[escenario], cfg, rank)

    if len(escen) == 1:
        nom = next(iter(escen))
        return aplicar_un_escenario(df, nom, escen[nom], cfg, rank)

    # varios escenarios -> aplica todos (útil cuando el modelo se entrenó por segmentos)
    partes = [aplicar_un_escenario(df, nom, mod, cfg, rank) for nom, mod in escen.items()]
    return pd.concat(partes, ignore_index=True)


if __name__ == "__main__":
    import sys
    pkl, csv = sys.argv[1], sys.argv[2]
    df = pd.read_csv(csv)
    res = aplicar_modelo(pkl, df)
    salida = csv.replace(".csv", "_scored.csv")
    res.to_csv(salida, index=False)
    print(f"Generado: {salida}  ({len(res):,} filas)")
    print(res.head(10).to_string(index=False))
