# -*- coding: utf-8 -*-
"""
================================================================================
 modelo_riesgo_credito.py
 Pipeline de modelización de riesgo de crédito (PD) — Challenger vs Champion
--------------------------------------------------------------------------------
 Autor      : Principal Data Scientist — Model Risk
 Objetivo   : Construir, validar y gobernar un modelo de PD a nivel cliente,
              usando como BENCHMARK (champion) el modelo ya existente en la
              tabla: columna `prob_malo` (y `score`).
 Dataset    : nivel cliente. Columnas clave esperadas:
                - key_value / cod_cuc : identificadores
                - codmes_ejec         : periodo YYYYMM (para OOT / PSI / CSI)
                - split               : train/test/oot (si existe se respeta)
                - target_60_12m       : variable objetivo (1 = malo, 60+ dpd 12m)
                - prob_malo, score    : SALIDAS del modelo vigente => CHAMPION
                - resto               : features (bureau/SBS + transaccional POS)
--------------------------------------------------------------------------------
 PRINCIPIO METODOLOGICO (Model Risk):
   - La SELECCION de variables, el binning, la calibracion y los hiperparametros
     usan EXCLUSIVAMENTE informacion in-sample (train).
   - La ventana OOT (Out-of-Time) NO interviene en ninguna decision: se reserva
     para VALIDAR el modelo ya elegido (discriminacion + estabilidad + calibracion).
   - Se evalua SIEMPRE: discriminacion (Gini/KS/AUC), calibracion (Brier/ECE/EC)
     y estabilidad (PSI/CSI) ANTES de recomendar un modelo.
   - prob_malo / score se EXCLUYEN de las features (serian leakage del champion)
     y se usan solo como benchmark a batir.
--------------------------------------------------------------------------------
 DEPENDENCIAS (requirements sugeridos):
     pandas numpy scipy scikit-learn
     optbinning            # binning supervisado monotonico + scorecard regulatorio
     lightgbm              # challenger GBM
     optuna                # optimizacion bayesiana de hiperparametros
     shap                  # explicabilidad (TreeSHAP)
     matplotlib            # curvas de fiabilidad / PDP (opcional)
 El script degrada con elegancia: si una libreria opcional no esta instalada,
 omite esa etapa y deja constancia en el log (no rompe el pipeline).
================================================================================
"""

from __future__ import annotations

import json
import logging
import os
import warnings
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ------------------------------------------------------------------ logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("pd_model")

# --------------------------------------------------- imports opcionales -------
def _try(modname: str):
    try:
        return __import__(modname)
    except Exception:
        return None

optbinning = _try("optbinning")
lightgbm = _try("lightgbm")
xgboost = _try("xgboost")
catboost = _try("catboost")
optuna = _try("optuna")
shap = _try("shap")
mpl = _try("matplotlib")

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)


# =============================================================================
# 1. CONFIGURACION
# =============================================================================
@dataclass
class Config:
    # --- IO ---
    data_path: str = "data_cliente.parquet"   # cambia a tu fuente (.parquet/.csv)
    out_dir: str = "artefactos_modelo"

    # --- roles de columnas ---
    target: str = "target_60_12m"
    id_cols: Tuple[str, ...] = ("key_value", "cod_cuc")
    time_col: str = "codmes_ejec"             # YYYYMM
    split_col: Optional[str] = "split"        # si no existe -> split por tiempo
    # columnas del modelo vigente => benchmark (NUNCA como feature)
    champion_prob: str = "prob_malo"
    champion_score: str = "score"

    # --- particion temporal (si no hay split_col) ---
    oot_n_months: int = 4                       # ultimos K meses como OOT
    test_size: float = 0.25                     # holdout dentro de train

    # --- filtros de elegibilidad de variables (in-sample) ---
    max_missing_rate: float = 0.95              # descarta var con >95% nulos
    min_iv: float = 0.02                        # IV minimo (poder predictivo)
    max_iv: float = 1.50                        # IV excesivo => sospecha de leakage
    max_psi: float = 0.25                       # PSI train->oot maximo (estabilidad)
    max_corr: float = 0.80                      # |corr| WOE maxima admitida
    max_vif: float = 5.0                        # VIF maximo (multicolinealidad)
    max_card_categorical: int = 50              # cardinalidad maxima categorica

    # --- modelado ---
    monotonic: bool = True                      # binning monotono (regulatorio)
    use_woe_for_lr: bool = True                 # LR sobre WOE (scorecard)
    n_features_max: int = 25                    # tope de variables en el modelo final
    optuna_trials: int = 40                     # iteraciones de optimizacion bayesiana
    cv_folds: int = 5                           # validacion cruzada temporal

    # --- GBM challengers + control de over/under-fitting ---
    gbm_models: Tuple[str, ...] = ("lightgbm", "xgboost", "catboost")
    overfit_tol: float = 0.02                   # gap AUC(train)-AUC(val) tolerado
    overfit_penalty: float = 1.0                # peso del castigo al gap (anti-overfit)

    # --- calibracion ---
    # SOLO se calibra si el EC del modelo supera este umbral (ya calibrado -> no se toca)
    ec_calibration_threshold: float = 0.05
    calibration_method: str = "isotonic"        # 'isotonic' | 'sigmoid' (Platt)

    # --- explicabilidad SHAP ---
    shap_max_features: int = 20                 # nro de variables a graficar
    shap_sample: int = 5000                     # muestra para SHAP (coste)

    # --- diccionario de variables (categoricas ya intuidas del dataset) ---
    known_categoricals: Tuple[str, ...] = (
        "desc_grupo_carrera",
        "far_rubro_top2_frec_name_3m", "far_rubro_top1_monto_name_6m",
        "far_rubro_top3_monto_name_6m", "far_rubro_top2_monto_name_3m",
        "far_rubrofrec_9m", "spsa_rubro_top3_frec_name_9m",
        "far_rubro_top2_monto_name_6m", "spsa_rubro_top2_frec_name_12m",
        "far_rubro_top2_monto_name_9m", "far_rubro_top3_frec_name_1m",
        "far_rubro_top1_monto_name_6m",
    )
    # flags / ordinales de baja cardinalidad que conviene tratar como categoricas
    flag_cols: Tuple[str, ...] = (
        "flag_bancarizado", "flg_clasi_dif_nor_1m", "lvl_edu_poten_open",
    )

    # --- gobierno ---
    random_state: int = RANDOM_STATE

    leak_cols: Tuple[str, ...] = field(default_factory=tuple)

    def feature_blacklist(self) -> set:
        """Columnas que jamas pueden ser features."""
        bl = set(self.id_cols) | {
            self.target, self.time_col, self.champion_prob, self.champion_score,
        }
        if self.split_col:
            bl.add(self.split_col)
        bl |= set(self.leak_cols)
        return bl


# =============================================================================
# 2. METRICAS (discriminacion, calibracion, estabilidad)
# =============================================================================
def _safe_auc(y: np.ndarray, p: np.ndarray) -> float:
    from sklearn.metrics import roc_auc_score
    mask = ~np.isnan(p)
    if mask.sum() == 0 or len(np.unique(y[mask])) < 2:
        return np.nan
    return roc_auc_score(y[mask], p[mask])


def gini(y: np.ndarray, p: np.ndarray) -> float:
    auc = _safe_auc(y, p)
    return np.nan if np.isnan(auc) else 2 * auc - 1


def ks_stat(y: np.ndarray, p: np.ndarray) -> float:
    """Kolmogorov-Smirnov entre distribuciones de score de buenos y malos."""
    df = pd.DataFrame({"y": y, "p": p}).dropna()
    if df["y"].nunique() < 2:
        return np.nan
    df = df.sort_values("p")
    cum_bad = (df["y"] == 1).cumsum() / max((df["y"] == 1).sum(), 1)
    cum_good = (df["y"] == 0).cumsum() / max((df["y"] == 0).sum(), 1)
    return float(np.max(np.abs(cum_bad - cum_good)))


def brier(y: np.ndarray, p: np.ndarray) -> float:
    mask = ~np.isnan(p)
    return float(np.mean((p[mask] - y[mask]) ** 2)) if mask.sum() else np.nan


def ec_calibration(y: np.ndarray, p: np.ndarray) -> float:
    """Error de calibracion agregado EC = |mean(PD)/mean(RD) - 1|.
    Es la metrica usada en el entregable vigente (hoja Metricas)."""
    mask = ~np.isnan(p)
    rd = np.mean(y[mask])
    if rd == 0:
        return np.nan
    return float(abs(np.mean(p[mask]) / rd - 1))


def expected_calibration_error(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> Tuple[float, float]:
    """ECE y MCE por binning de probabilidad (reliability)."""
    df = pd.DataFrame({"y": y, "p": p}).dropna()
    df["bin"] = pd.qcut(df["p"], q=min(n_bins, df["p"].nunique()), duplicates="drop")
    g = df.groupby("bin", observed=True).agg(conf=("p", "mean"), acc=("y", "mean"), n=("y", "size"))
    gap = (g["conf"] - g["acc"]).abs()
    ece = float((gap * g["n"]).sum() / g["n"].sum())
    mce = float(gap.max())
    return ece, mce


def psi(expected: np.ndarray, actual: np.ndarray, n_bins: int = 10) -> float:
    """Population Stability Index entre dos distribuciones (mismo binning)."""
    e = pd.Series(expected).dropna()
    a = pd.Series(actual).dropna()
    if e.empty or a.empty:
        return np.nan
    try:
        edges = np.unique(np.quantile(e, np.linspace(0, 1, n_bins + 1)))
    except Exception:
        return np.nan
    if len(edges) < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    e_pct = np.histogram(e, bins=edges)[0] / len(e)
    a_pct = np.histogram(a, bins=edges)[0] / len(a)
    e_pct = np.clip(e_pct, 1e-6, None)
    a_pct = np.clip(a_pct, 1e-6, None)
    return float(np.sum((a_pct - e_pct) * np.log(a_pct / e_pct)))


def lift_gain_table(y: np.ndarray, p: np.ndarray, n: int = 10) -> pd.DataFrame:
    """Tabla de ganancias / lift por decil de riesgo."""
    df = pd.DataFrame({"y": y, "p": p}).dropna().sort_values("p", ascending=False)
    df["decil"] = pd.qcut(df["p"].rank(method="first"), q=n, labels=False) + 1
    base = df["y"].mean()
    g = df.groupby("decil").agg(n=("y", "size"), bad=("y", "sum"), bad_rate=("y", "mean"))
    g["lift"] = g["bad_rate"] / base
    g["captura_acum"] = g["bad"].cumsum() / df["y"].sum()
    return g.reset_index()


def metric_panel(y: np.ndarray, p: np.ndarray) -> Dict[str, float]:
    ece, mce = expected_calibration_error(y, p)
    return {
        "AUC": _safe_auc(y, p),
        "Gini": gini(y, p),
        "KS": ks_stat(y, p),
        "Brier": brier(y, p),
        "EC": ec_calibration(y, p),
        "ECE": ece,
        "MCE": mce,
        "mean_pred": float(np.nanmean(p)),
        "mean_obs": float(np.mean(y)),
    }


# =============================================================================
# 3. CARGA Y PARTICION (train / test / OOT)
# =============================================================================
def load_data(cfg: Config) -> pd.DataFrame:
    log.info("Cargando datos: %s", cfg.data_path)
    if cfg.data_path.endswith(".parquet"):
        df = pd.read_parquet(cfg.data_path)
    elif cfg.data_path.endswith((".csv", ".txt")):
        df = pd.read_csv(cfg.data_path)
    else:
        raise ValueError("Formato no soportado: usa .parquet o .csv")
    log.info("Shape: %s | target mean=%.4f", df.shape, df[cfg.target].mean())
    return df


def split_train_oot(cfg: Config, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Devuelve {'train','test','oot'} respetando split_col si existe,
    o particionando por tiempo (los ultimos K meses son OOT)."""
    from sklearn.model_selection import train_test_split

    if cfg.split_col and cfg.split_col in df.columns:
        vals = df[cfg.split_col].astype(str).str.lower()
        oot = df[vals.isin(["oot", "validation", "valid", "oos"])].copy()
        rest = df[~vals.isin(["oot", "validation", "valid", "oos"])].copy()
        if {"train", "test"}.issubset(set(vals.unique())):
            train = rest[vals.loc[rest.index] == "train"].copy()
            test = rest[vals.loc[rest.index] == "test"].copy()
        else:
            train, test = train_test_split(
                rest, test_size=cfg.test_size, random_state=cfg.random_state,
                stratify=rest[cfg.target],
            )
        log.info("Particion por columna '%s'", cfg.split_col)
    else:
        months = sorted(df[cfg.time_col].dropna().unique())
        oot_months = set(months[-cfg.oot_n_months:])
        oot = df[df[cfg.time_col].isin(oot_months)].copy()
        rest = df[~df[cfg.time_col].isin(oot_months)].copy()
        train, test = train_test_split(
            rest, test_size=cfg.test_size, random_state=cfg.random_state,
            stratify=rest[cfg.target],
        )
        log.info("Particion temporal | OOT meses: %s", sorted(oot_months))

    for nm, part in [("train", train), ("test", test), ("oot", oot)]:
        log.info("  %-5s: N=%-8d  bad_rate=%.4f", nm, len(part), part[cfg.target].mean())
    return {"train": train, "test": test, "oot": oot}


def classify_features(cfg: Config, df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Separa features numericas vs categoricas, excluyendo blacklist y leakage.
    Usa el DICCIONARIO de categoricas conocidas (cfg.known_categoricals + flag_cols):
    fuerza a categorica aunque vengan codificadas como numero (p.ej. flags/ordinales)."""
    bl = cfg.feature_blacklist()
    feats = [c for c in df.columns if c not in bl]
    forced_cat = set(cfg.known_categoricals) | set(cfg.flag_cols)
    num, cat = [], []
    for c in feats:
        is_forced = c in forced_cat
        is_obj = not pd.api.types.is_numeric_dtype(df[c])
        if is_forced or is_obj:
            card = df[c].nunique(dropna=True)
            if card <= cfg.max_card_categorical:
                cat.append(c)
            else:
                log.warning("  descartada por alta cardinalidad: %s (%d niveles)", c, card)
        else:
            num.append(c)
    log.info("Features candidatas: %d numericas, %d categoricas (forzadas por diccionario: %d)",
             len(num), len(cat), len(forced_cat & set(cat)))
    return num, cat


# =============================================================================
# 4. BINNING SUPERVISADO + IV/WOE  (OptBinning; fallback decil)
# =============================================================================
class WoeEngine:
    """Encapsula binning monotonico (OptBinning) con fallback robusto.
    Calcula IV por variable y transforma a WOE. El AJUSTE es solo in-sample."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.binning_process = None
        self.iv_table: Optional[pd.DataFrame] = None
        self._fallback_maps: Dict[str, pd.DataFrame] = {}
        self._fallback_iv: Dict[str, float] = {}
        self.selected: List[str] = []

    # ---- OptBinning path -----------------------------------------------------
    def fit_optbinning(self, X: pd.DataFrame, y: pd.Series, num, cat):
        from optbinning import BinningProcess
        variables = num + cat
        monotonic = "auto_asc_desc" if self.cfg.monotonic else None
        self.binning_process = BinningProcess(
            variable_names=variables,
            categorical_variables=cat,
            min_n_bins=2, max_n_bins=6, min_bin_size=0.05,
            monotonic_trend=monotonic,
            selection_criteria={"iv": {"min": self.cfg.min_iv, "max": self.cfg.max_iv,
                                       "strategy": "highest"}},
        )
        self.binning_process.fit(X[variables].values, y.values)
        summ = self.binning_process.summary()
        self.iv_table = (summ[["name", "iv", "selected"]]
                         .rename(columns={"name": "variable"})
                         .sort_values("iv", ascending=False))
        self.selected = self.iv_table.loc[self.iv_table["selected"], "variable"].tolist()
        log.info("OptBinning: %d/%d variables superan filtros IV/monotonia",
                 len(self.selected), len(variables))

    def transform_optbinning(self, X: pd.DataFrame) -> pd.DataFrame:
        variables = self.binning_process.get_support(names=True)
        woe = self.binning_process.transform(X[list(variables)].values, metric="woe")
        return pd.DataFrame(woe, columns=[f"woe_{v}" for v in variables], index=X.index)

    # ---- Fallback path (sin OptBinning) -------------------------------------
    @staticmethod
    def _iv_woe_single(x: pd.Series, y: pd.Series, n_bins=10) -> Tuple[pd.DataFrame, float]:
        d = pd.DataFrame({"x": x, "y": y})
        if pd.api.types.is_numeric_dtype(d["x"]):
            d["bin"] = pd.qcut(d["x"], q=n_bins, duplicates="drop")
        else:
            d["bin"] = d["x"].astype("object").fillna("__NA__")
        grp = d.groupby("bin", observed=True)["y"].agg(["count", "sum"])
        grp.columns = ["n", "bad"]
        grp["good"] = grp["n"] - grp["bad"]
        tot_bad, tot_good = grp["bad"].sum(), grp["good"].sum()
        grp["dist_bad"] = np.clip(grp["bad"] / max(tot_bad, 1), 1e-6, None)
        grp["dist_good"] = np.clip(grp["good"] / max(tot_good, 1), 1e-6, None)
        grp["woe"] = np.log(grp["dist_good"] / grp["dist_bad"])
        grp["iv"] = (grp["dist_good"] - grp["dist_bad"]) * grp["woe"]
        return grp, float(grp["iv"].sum())

    def fit_fallback(self, X: pd.DataFrame, y: pd.Series, num, cat):
        rows = []
        for c in num + cat:
            try:
                grp, iv = self._iv_woe_single(X[c], y)
                self._fallback_maps[c] = grp
                self._fallback_iv[c] = iv
                rows.append((c, iv))
            except Exception as e:
                log.debug("IV fallo en %s: %s", c, e)
        self.iv_table = (pd.DataFrame(rows, columns=["variable", "iv"])
                         .sort_values("iv", ascending=False))
        self.iv_table["selected"] = self.iv_table["iv"].between(self.cfg.min_iv, self.cfg.max_iv)
        self.selected = self.iv_table.loc[self.iv_table["selected"], "variable"].tolist()
        log.info("Fallback IV/WOE: %d variables seleccionadas por IV", len(self.selected))

    def transform_fallback(self, X: pd.DataFrame) -> pd.DataFrame:
        out = {}
        for c in self.selected:
            grp = self._fallback_maps[c]
            if pd.api.types.is_numeric_dtype(X[c]):
                # mapear cada valor a su bin via los intervalos del grupo
                bins = pd.IntervalIndex(grp.index.get_level_values(0))
                idx = bins.get_indexer(X[c].values)
                woe_vals = grp["woe"].values
                out[f"woe_{c}"] = np.where(idx >= 0, woe_vals[idx], 0.0)
            else:
                m = grp["woe"].to_dict()
                out[f"woe_{c}"] = X[c].astype("object").fillna("__NA__").map(m).fillna(0.0).values
        return pd.DataFrame(out, index=X.index)

    # ---- API unificada -------------------------------------------------------
    def fit(self, X, y, num, cat):
        if optbinning is not None:
            self.fit_optbinning(X, y, num, cat)
        else:
            log.warning("OptBinning no disponible -> fallback de binning por deciles")
            self.fit_fallback(X, y, num, cat)

    def transform(self, X) -> pd.DataFrame:
        if optbinning is not None:
            return self.transform_optbinning(X)
        return self.transform_fallback(X)


# =============================================================================
# 5. FILTROS DE ESTABILIDAD Y REDUNDANCIA (PSI, correlacion, VIF)
# =============================================================================
def filter_by_psi(cfg: Config, woe_train: pd.DataFrame, woe_oot: pd.DataFrame) -> List[str]:
    """Descarta variables inestables train->OOT (PSI alto). Solo informativo:
    la decision se toma con train+oot de la *misma* var (no usa el target OOT)."""
    keep, dropped = [], []
    for c in woe_train.columns:
        val = psi(woe_train[c].values, woe_oot[c].values)
        if np.isnan(val) or val <= cfg.max_psi:
            keep.append(c)
        else:
            dropped.append((c, val))
    if dropped:
        log.info("PSI>%.2f -> descartadas %d variables inestables", cfg.max_psi, len(dropped))
    return keep


def filter_correlation(cfg: Config, woe: pd.DataFrame, iv_map: Dict[str, float]) -> List[str]:
    """Ante pares muy correlacionados, conserva la de mayor IV."""
    corr = woe.corr().abs()
    cols = list(woe.columns)
    drop = set()
    for i, a in enumerate(cols):
        if a in drop:
            continue
        for b in cols[i + 1:]:
            if b in drop:
                continue
            if corr.loc[a, b] > cfg.max_corr:
                worse = a if iv_map.get(a, 0) < iv_map.get(b, 0) else b
                drop.add(worse)
    keep = [c for c in cols if c not in drop]
    if drop:
        log.info("Correlacion>|%.2f| -> descartadas %d variables redundantes",
                 cfg.max_corr, len(drop))
    return keep


def filter_vif(cfg: Config, woe: pd.DataFrame) -> List[str]:
    """Elimina iterativamente la variable de mayor VIF hasta < umbral."""
    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        from statsmodels.tools.tools import add_constant
    except Exception:
        log.warning("statsmodels no disponible -> se omite VIF")
        return list(woe.columns)
    cols = list(woe.columns)
    X = woe[cols].fillna(0.0)
    while len(cols) > 1:
        Xc = add_constant(X[cols])
        vifs = [variance_inflation_factor(Xc.values, i + 1) for i in range(len(cols))]
        vmax = max(vifs)
        if vmax <= cfg.max_vif:
            break
        worst = cols[int(np.argmax(vifs))]
        cols.remove(worst)
        log.debug("VIF %.1f -> elimino %s", vmax, worst)
    return cols


# =============================================================================
# 6. MODELOS
#    (A) Scorecard regulatorio (LR/WOE)
#    (B) Challengers GBM: LightGBM + XGBoost + CatBoost
#        - hiperparametros con REGULARIZACION (L1/L2, min_child, depth, subsample...)
#        - objetivo Optuna ANTI-OVERFIT: AUC(val) penalizando el gap AUC(train)-AUC(val)
#          => evita sobreajuste sin caer en underfitting (gap pequeno + AUC alta)
# =============================================================================
def fit_scorecard_lr(cfg: Config, woe_tr: pd.DataFrame, y_tr: pd.Series, features: List[str]):
    """Regresion logistica L2 sobre WOE. Interpretable, trazable, regulatoria."""
    from sklearn.linear_model import LogisticRegression
    X = woe_tr[features].fillna(0.0)
    model = LogisticRegression(penalty="l2", C=1.0, max_iter=1000,
                               random_state=cfg.random_state)
    model.fit(X, y_tr)
    coef = pd.Series(model.coef_[0], index=features).sort_values()
    log.info("Scorecard LR ajustado con %d variables", len(features))
    return model, coef


# ---------------------------------------------------------------------------
# Preparacion de la matriz segun la libreria (manejo nativo de categoricas)
# ---------------------------------------------------------------------------
def prepare_gbm_frame(model_type: str, X: pd.DataFrame, cat: List[str]) -> pd.DataFrame:
    X = X.copy()
    if model_type in ("lightgbm", "xgboost"):
        # ambos aceptan dtype 'category' (xgboost con enable_categorical=True)
        for c in cat:
            X[c] = X[c].astype("category")
    elif model_type == "catboost":
        # CatBoost no admite NaN en categoricas: relleno y fuerzo str
        for c in cat:
            X[c] = X[c].astype("object").where(X[c].notna(), "__NA__").astype(str)
    return X


def gbm_predict(model_type: str, model, X: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(X)[:, 1]


def _overfit_score(cfg: Config, y_tr, p_tr, y_va, p_va) -> float:
    """AUC(val) penalizando el exceso de gap respecto a train.
    score = AUC_val - penalty * max(0, (AUC_tr - AUC_val) - tol).
    Premia generalizacion (gap chico) sin sacrificar discriminacion."""
    a_tr = _safe_auc(np.asarray(y_tr), np.asarray(p_tr))
    a_va = _safe_auc(np.asarray(y_va), np.asarray(p_va))
    if np.isnan(a_tr) or np.isnan(a_va):
        return -1.0
    gap = max(0.0, (a_tr - a_va) - cfg.overfit_tol)
    return a_va - cfg.overfit_penalty * gap


def _space(model_type: str, trial, cfg: Config) -> dict:
    """Espacios de busqueda REGULARIZADOS por libreria."""
    rs = cfg.random_state
    if model_type == "lightgbm":
        return dict(
            objective="binary", metric="auc", n_estimators=4000,
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
            num_leaves=trial.suggest_int("num_leaves", 15, 63),          # acotado -> menos overfit
            max_depth=trial.suggest_int("max_depth", 3, 8),
            min_child_samples=trial.suggest_int("min_child_samples", 50, 500),
            min_split_gain=trial.suggest_float("min_split_gain", 0.0, 0.5),
            subsample=trial.suggest_float("subsample", 0.6, 1.0),
            subsample_freq=1,
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.6, 1.0),
            reg_alpha=trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),   # L1
            reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True), # L2
            random_state=rs, n_jobs=-1, verbose=-1,
        )
    if model_type == "xgboost":
        return dict(
            objective="binary:logistic", eval_metric="auc", n_estimators=4000,
            tree_method="hist", enable_categorical=True,
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
            max_depth=trial.suggest_int("max_depth", 3, 8),
            min_child_weight=trial.suggest_float("min_child_weight", 1.0, 300.0, log=True),
            gamma=trial.suggest_float("gamma", 0.0, 5.0),                 # min loss reduction
            subsample=trial.suggest_float("subsample", 0.6, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.6, 1.0),
            reg_alpha=trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
            reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            random_state=rs, n_jobs=-1, verbosity=0,
        )
    if model_type == "catboost":
        return dict(
            loss_function="Logloss", eval_metric="AUC", iterations=4000,
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
            depth=trial.suggest_int("depth", 3, 8),
            l2_leaf_reg=trial.suggest_float("l2_leaf_reg", 1.0, 30.0, log=True),  # L2
            random_strength=trial.suggest_float("random_strength", 0.0, 2.0),
            bagging_temperature=trial.suggest_float("bagging_temperature", 0.0, 1.0),
            border_count=trial.suggest_int("border_count", 64, 254),
            random_seed=rs, verbose=0, allow_writing_files=False,
        )
    raise ValueError(model_type)


def _default_space(model_type: str, cfg: Config) -> dict:
    """Hiperparametros por defecto razonables (si Optuna no esta disponible)."""
    class _T:  # trial dummy que devuelve el centro del rango
        def suggest_float(self, n, a, b, log=False):
            return (a * b) ** 0.5 if log else (a + b) / 2
        def suggest_int(self, n, a, b):
            return (a + b) // 2
    return _space(model_type, _T(), cfg)


def _fit_gbm(model_type: str, params: dict, Xtr, ytr, Xva, yva, cat: List[str]):
    """Ajuste con EARLY STOPPING (controla nro de arboles -> anti-overfit)."""
    if model_type == "lightgbm":
        import lightgbm as lgb
        m = lgb.LGBMClassifier(**params)
        m.fit(Xtr, ytr, eval_set=[(Xva, yva)],
              callbacks=[lgb.early_stopping(150, verbose=False), lgb.log_evaluation(0)])
        return m
    if model_type == "xgboost":
        import xgboost as xgb
        p = dict(params); p["early_stopping_rounds"] = 150
        m = xgb.XGBClassifier(**p)
        m.fit(Xtr, ytr, eval_set=[(Xva, yva)], verbose=False)
        return m
    if model_type == "catboost":
        from catboost import CatBoostClassifier, Pool
        cat_idx = [Xtr.columns.get_loc(c) for c in cat]
        m = CatBoostClassifier(**params, od_type="Iter", od_wait=150, cat_features=cat_idx)
        m.fit(Pool(Xtr, ytr, cat_features=cat_idx),
              eval_set=Pool(Xva, yva, cat_features=cat_idx), use_best_model=True, verbose=0)
        return m
    raise ValueError(model_type)


def optimize_gbm(cfg: Config, model_type: str, Xtr, ytr, Xva, yva, cat: List[str]):
    """Optimizacion bayesiana anti-overfit para un GBM concreto.
    Devuelve (modelo_ajustado, best_params)."""
    Xtr = prepare_gbm_frame(model_type, Xtr, cat)
    Xva = prepare_gbm_frame(model_type, Xva, cat)

    if optuna is None:
        log.warning("Optuna no disponible -> %s con hiperparametros por defecto", model_type)
        params = _default_space(model_type, cfg)
        return _fit_gbm(model_type, params, Xtr, ytr, Xva, yva, cat), {}

    def objective(trial):
        params = _space(model_type, trial, cfg)
        m = _fit_gbm(model_type, params, Xtr, ytr, Xva, yva, cat)
        p_tr = gbm_predict(model_type, m, Xtr)
        p_va = gbm_predict(model_type, m, Xva)
        return _overfit_score(cfg, ytr, p_tr, yva, p_va)

    study = optuna.create_study(direction="maximize",
                                sampler=optuna.samplers.TPESampler(seed=cfg.random_state))
    study.optimize(objective, n_trials=cfg.optuna_trials, show_progress_bar=False)
    best_params = _space(model_type, study.best_trial, cfg)
    best = _fit_gbm(model_type, best_params, Xtr, ytr, Xva, yva, cat)
    p_tr = gbm_predict(model_type, best, Xtr)
    p_va = gbm_predict(model_type, best, Xva)
    log.info("%-9s | score=%.4f | AUC_tr=%.4f AUC_val=%.4f (gap=%.4f)",
             model_type, study.best_value, _safe_auc(ytr.values, p_tr),
             _safe_auc(yva.values, p_va),
             _safe_auc(ytr.values, p_tr) - _safe_auc(yva.values, p_va))
    return best, study.best_trial.params


# =============================================================================
# 7. CALIBRACION DE PROBABILIDADES (Platt / Isotonic) + reliability
# =============================================================================
def calibrate(cfg: Config, p_tr: np.ndarray, y_tr: np.ndarray,
              method: str = "isotonic"):
    """Devuelve un calibrador entrenado en train (no toca OOT).
    - isotonic: flexible, requiere N grande (recomendado aqui).
    - sigmoid (Platt): parametrico, robusto con poca data."""
    if method == "isotonic":
        from sklearn.isotonic import IsotonicRegression
        cal = IsotonicRegression(out_of_bounds="clip")
        cal.fit(p_tr, y_tr)
        return lambda p: cal.predict(np.clip(p, 0, 1))
    else:
        from sklearn.linear_model import LogisticRegression
        lr = LogisticRegression()
        lr.fit(np.log(np.clip(p_tr, 1e-6, 1 - 1e-6) /
                      (1 - np.clip(p_tr, 1e-6, 1 - 1e-6))).reshape(-1, 1), y_tr)
        def _f(p):
            z = np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))
            return lr.predict_proba(z.reshape(-1, 1))[:, 1]
        return _f


def maybe_calibrate(cfg: Config, p_tr: np.ndarray, y_tr: np.ndarray,
                    p_dict: Dict[str, np.ndarray]) -> Tuple[Dict[str, np.ndarray], float, bool]:
    """Aplica calibracion SOLO si el EC del modelo (in-sample) supera el umbral.
    Si EC <= umbral => el modelo ya esta bien calibrado y NO se toca (evita
    introducir varianza/ruido innecesario). Devuelve (preds, ec, aplicada)."""
    ec = ec_calibration(y_tr, p_tr)
    if ec is None or np.isnan(ec) or ec <= cfg.ec_calibration_threshold:
        log.info("Calibracion OMITIDA (EC=%.4f <= %.2f): el modelo ya esta calibrado",
                 ec if ec is not None else float("nan"), cfg.ec_calibration_threshold)
        return p_dict, ec, False
    log.info("Calibracion APLICADA (EC=%.4f > %.2f) | metodo=%s",
             ec, cfg.ec_calibration_threshold, cfg.calibration_method)
    cal = calibrate(cfg, p_tr, y_tr, cfg.calibration_method)
    return {k: cal(v) for k, v in p_dict.items()}, ec, True


# =============================================================================
# 8. ESTABILIDAD TEMPORAL DEL SCORE (PSI/CSI por periodo) y por segmento
# =============================================================================
def stability_by_period(cfg: Config, df: pd.DataFrame, p: np.ndarray,
                         ref_mask: np.ndarray) -> pd.DataFrame:
    """PSI del score por periodo vs distribucion de referencia (train)."""
    ref = p[ref_mask]
    rows = []
    for m, idx in df.groupby(cfg.time_col).groups.items():
        sub = p[df.index.get_indexer(idx)]
        rows.append({"codmes": m, "N": len(sub),
                     "PSI_score": psi(ref, sub),
                     "mean_score": float(np.nanmean(sub))})
    return pd.DataFrame(rows).sort_values("codmes")


# =============================================================================
# 9. EXPLICABILIDAD — SHAP dependence plots
#    Por feature (en TRAIN):  eje X = valor de la variable (original o WOE),
#    eje Y = valor SHAP, y una LINEA que une el PROMEDIO de SHAP por
#    categoria/valor (por valor exacto cuando es WOE/categorica; por bin si es
#    continua original). Para variables ORIGINALES se usa el GBM (TreeSHAP);
#    para variables en WOE se usa el scorecard LR (LinearSHAP).
# =============================================================================
def _shap_values(model, X: pd.DataFrame, kind: str):
    """Devuelve la matriz de SHAP (clase positiva) para tree o linear."""
    if kind == "tree":
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X)
        return sv[1] if isinstance(sv, list) else sv
    # linear (LR sobre WOE): background = la propia muestra
    explainer = shap.LinearExplainer(model, X)
    sv = explainer.shap_values(X)
    return sv[1] if isinstance(sv, list) else sv


def shap_dependence_plots(cfg: Config, model, X: pd.DataFrame, outdir: str,
                          tag: str, kind: str = "tree", is_woe: bool = False):
    """Genera un PNG por variable con scatter(valor, SHAP) + linea de SHAP medio.
    - is_woe / categorica / baja cardinalidad -> linea por VALOR EXACTO.
    - continua original                       -> linea por BIN (decil)."""
    if shap is None:
        log.warning("shap no disponible -> se omiten dependence plots (%s)", tag)
        return None
    if mpl is None:
        log.warning("matplotlib no disponible -> se omiten dependence plots (%s)", tag)
        return None
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        vals = _shap_values(model, X, kind)
    except Exception as e:
        log.warning("SHAP fallo (%s): %s", tag, e)
        return None

    imp = pd.DataFrame({"feature": X.columns,
                        "mean_abs_shap": np.abs(vals).mean(axis=0)}
                       ).sort_values("mean_abs_shap", ascending=False)
    imp.to_csv(os.path.join(outdir, f"shap_importance_{tag}.csv"), index=False)

    plot_dir = os.path.join(outdir, f"shap_dependence_{tag}")
    os.makedirs(plot_dir, exist_ok=True)
    top = imp.head(cfg.shap_max_features)["feature"].tolist()

    for col in top:
        j = X.columns.get_loc(col)
        x_raw = X[col]
        s = vals[:, j]
        d = pd.DataFrame({"x": x_raw.values, "shap": s})

        numeric = pd.api.types.is_numeric_dtype(x_raw)
        discrete = is_woe or (not numeric) or (d["x"].nunique(dropna=True) <= 25)

        fig, ax = plt.subplots(figsize=(7.2, 4.2))
        if discrete:
            # posiciones ordenadas por valor (o por categoria)
            order = (sorted(d["x"].dropna().unique())
                     if numeric else list(pd.Series(d["x"].dropna().unique()).astype(str)))
            pos = {v: i for i, v in enumerate(order)}
            xk = (d["x"] if numeric else d["x"].astype(str))
            xpos = xk.map(pos).astype(float).values
            jitter = (np.random.rand(len(xpos)) - 0.5) * 0.15
            ax.scatter(xpos + jitter, d["shap"], s=7, alpha=0.25, color="#4C72B0")
            # LINEA: SHAP promedio por valor/categoria exacto
            means = d.assign(_k=xk).groupby("_k", observed=True)["shap"].mean().reindex(order)
            ax.plot([pos[v] for v in order], means.values, color="#C44E52",
                    marker="o", lw=2, label="SHAP promedio por valor/categoria")
            ax.set_xticks(range(len(order)))
            ax.set_xticklabels([str(v) for v in order], rotation=45, ha="right", fontsize=7)
        else:
            ax.scatter(d["x"], d["shap"], s=7, alpha=0.25, color="#4C72B0")
            # LINEA: SHAP promedio por bin (decil) para variable continua original
            d["bin"] = pd.qcut(d["x"], 10, duplicates="drop")
            g = d.groupby("bin", observed=True)["shap"].mean()
            centers = [iv.mid for iv in g.index]
            ax.plot(centers, g.values, color="#C44E52", marker="o", lw=2,
                    label="SHAP promedio por bin")

        ax.axhline(0.0, color="gray", lw=0.8, ls="--")
        xlabel = f"{col}  ({'WOE' if is_woe else 'valor original'})"
        ax.set_xlabel(xlabel)
        ax.set_ylabel("valor SHAP")
        ax.set_title(f"Dependence SHAP — {col} [{tag}]", fontsize=10)
        ax.legend(fontsize=8, loc="best")
        fig.tight_layout()
        fname = os.path.join(plot_dir, f"{col}.png")
        fig.savefig(fname, dpi=110)
        plt.close(fig)

    log.info("SHAP dependence (%s): %d graficos en %s", tag, len(top), plot_dir)
    return imp


# =============================================================================
# 10. BENCHMARK CHAMPION vs CHALLENGER  (la tabla de decision)
# =============================================================================
def benchmark_table(cfg: Config, parts: Dict[str, pd.DataFrame],
                    preds: Dict[str, Dict[str, np.ndarray]]) -> pd.DataFrame:
    """Compara, por particion, el champion (prob_malo) contra los challengers.
    preds = {particion: {nombre_modelo: prob}}.
    Decision basada en OOT: discriminacion + calibracion + estabilidad."""
    rows = []
    for part_name, df in parts.items():
        y = df[cfg.target].values
        # champion existente
        if cfg.champion_prob in df.columns:
            m = metric_panel(y, df[cfg.champion_prob].values)
            m.update({"particion": part_name, "modelo": "CHAMPION (prob_malo)"})
            rows.append(m)
        # challengers
        for mname, p in preds.get(part_name, {}).items():
            m = metric_panel(y, p)
            m.update({"particion": part_name, "modelo": mname})
            rows.append(m)
    cols = ["particion", "modelo", "Gini", "KS", "AUC", "Brier", "EC", "ECE", "MCE",
            "mean_pred", "mean_obs"]
    return pd.DataFrame(rows)[cols].sort_values(["particion", "Gini"], ascending=[True, False])


# =============================================================================
# 11. ORQUESTACION
# =============================================================================
def run(cfg: Config):
    os.makedirs(cfg.out_dir, exist_ok=True)
    log.info("=" * 70)
    log.info("PIPELINE PD — CHALLENGER vs CHAMPION(prob_malo)  | seed=%d", cfg.random_state)
    log.info("=" * 70)

    # --- 1. data + particion ---
    df = load_data(cfg)
    parts = split_train_oot(cfg, df)
    train, test, oot = parts["train"], parts["test"], parts["oot"]
    y_tr = train[cfg.target]
    num, cat = classify_features(cfg, df)

    # --- 2. filtro de elegibilidad por missing (in-sample) ---
    miss = train[num + cat].isna().mean()
    elig = miss[miss <= cfg.max_missing_rate].index.tolist()
    num = [c for c in num if c in elig]
    cat = [c for c in cat if c in elig]
    log.info("Tras filtro missing<=%.0f%%: %d num, %d cat",
             cfg.max_missing_rate * 100, len(num), len(cat))

    # --- 3. WOE/IV (ajuste solo en train) ---
    woe = WoeEngine(cfg)
    woe.fit(train, y_tr, num, cat)
    iv_map = dict(zip(woe.iv_table["variable"], woe.iv_table["iv"]))
    woe.iv_table.to_csv(os.path.join(cfg.out_dir, "iv_table.csv"), index=False)

    woe_tr = woe.transform(train)
    woe_te = woe.transform(test)
    woe_oo = woe.transform(oot)

    # --- 4. estabilidad + redundancia (sin usar target OOT) ---
    keep = filter_by_psi(cfg, woe_tr, woe_oo)
    woe_tr, woe_te, woe_oo = woe_tr[keep], woe_te[keep], woe_oo[keep]
    iv_woe = {f"woe_{k}": v for k, v in iv_map.items()}
    keep = filter_correlation(cfg, woe_tr, iv_woe)
    woe_tr, woe_te, woe_oo = woe_tr[keep], woe_te[keep], woe_oo[keep]
    keep = filter_vif(cfg, woe_tr)
    # tope final de variables por IV
    keep = sorted(keep, key=lambda c: iv_woe.get(c, 0), reverse=True)[:cfg.n_features_max]
    woe_tr, woe_te, woe_oo = woe_tr[keep], woe_te[keep], woe_oo[keep]
    log.info("Set final de variables WOE: %d", len(keep))

    # --- 5A. modelo regulatorio: Scorecard LR/WOE ---
    lr_model, lr_coef = fit_scorecard_lr(cfg, woe_tr, y_tr, keep)
    lr_coef.to_csv(os.path.join(cfg.out_dir, "scorecard_coeficientes.csv"))
    p_lr = {
        "train": lr_model.predict_proba(woe_tr.fillna(0))[:, 1],
        "test": lr_model.predict_proba(woe_te.fillna(0))[:, 1],
        "oot": lr_model.predict_proba(woe_oo.fillna(0))[:, 1],
    }

    # --- 5B. challengers GBM: LightGBM + XGBoost + CatBoost (features crudas) ---
    avail = {"lightgbm": lightgbm, "xgboost": xgboost, "catboost": catboost}
    Xtr, Xte, Xoo = train[num + cat], test[num + cat], oot[num + cat]
    y_te = test[cfg.target]
    gbm_models: Dict[str, object] = {}
    gbm_preds: Dict[str, Dict[str, np.ndarray]] = {}
    for mt in cfg.gbm_models:
        if avail.get(mt) is None:
            log.warning("%s no disponible -> challenger omitido", mt)
            continue
        log.info("--- Optimizando %s (anti-overfit, %d trials) ---", mt, cfg.optuna_trials)
        model, best_params = optimize_gbm(cfg, mt, Xtr, y_tr, Xte, y_te, cat)
        json.dump(best_params, open(os.path.join(cfg.out_dir, f"{mt}_best_params.json"), "w"),
                  indent=2, default=str)
        gbm_models[mt] = model
        gbm_preds[mt] = {
            part: gbm_predict(mt, model, prepare_gbm_frame(mt, X, cat))
            for part, X in [("train", Xtr), ("test", Xte), ("oot", Xoo)]
        }

    # --- 6. calibracion CONDICIONAL (solo si EC del modelo > umbral=0.05) ---
    preds_by_part = {"train": {}, "test": {}, "oot": {}}
    cal_report = []

    # 6.1 scorecard LR
    p_lr_cal, ec_lr, applied_lr = maybe_calibrate(cfg, p_lr["train"], y_tr.values, p_lr)
    cal_report.append({"modelo": "LR/WOE", "EC_train": ec_lr, "calibrado": applied_lr})
    for part in preds_by_part:
        preds_by_part[part]["LR/WOE"] = p_lr_cal[part]

    # 6.2 cada GBM
    for mt, preds in gbm_preds.items():
        preds_cal, ec, applied = maybe_calibrate(cfg, preds["train"], y_tr.values, preds)
        cal_report.append({"modelo": mt, "EC_train": ec, "calibrado": applied})
        for part in preds_by_part:
            preds_by_part[part][mt] = preds_cal[part]
    pd.DataFrame(cal_report).to_csv(
        os.path.join(cfg.out_dir, "reporte_calibracion.csv"), index=False)

    # --- 7. tabla de decision champion vs challenger ---
    bench = benchmark_table(cfg, parts, preds_by_part)
    bench.to_csv(os.path.join(cfg.out_dir, "benchmark_champion_vs_challenger.csv"),
                 index=False)
    log.info("\n%s\nTABLA DE DECISION (foco en OOT):\n%s",
             "-" * 70, bench[bench["particion"] == "oot"].to_string(index=False))

    # --- 8. explicabilidad SHAP (en TRAIN, muestra) ---
    #   (a) variables ORIGINALES: mejor GBM por Gini OOT (TreeSHAP)
    #   (b) variables en WOE:      scorecard LR (LinearSHAP)
    n_smp = min(cfg.shap_sample, len(Xtr))
    smp_idx = Xtr.sample(n_smp, random_state=cfg.random_state).index
    if gbm_models:
        oot_gini = {mt: gini(oot[cfg.target].values, gbm_preds[mt]["oot"])
                    for mt in gbm_models}
        best_mt = max(oot_gini, key=oot_gini.get)
        log.info("Mejor GBM por Gini OOT: %s (%.4f)", best_mt, oot_gini[best_mt])
        shap_dependence_plots(
            cfg, gbm_models[best_mt],
            prepare_gbm_frame(best_mt, Xtr.loc[smp_idx], cat),
            cfg.out_dir, tag=f"original_{best_mt}", kind="tree", is_woe=False)
    shap_dependence_plots(
        cfg, lr_model, woe_tr.loc[smp_idx].fillna(0.0),
        cfg.out_dir, tag="woe_scorecard", kind="linear", is_woe=True)

    # --- 9. estabilidad temporal del mejor challenger en OOT ---
    if gbm_models:
        full = pd.concat([train, test, oot]).reset_index(drop=True)
        full_p = np.concatenate([preds_by_part["train"][best_mt],
                                 preds_by_part["test"][best_mt],
                                 preds_by_part["oot"][best_mt]])
        ref_mask = np.array([True] * len(train) + [False] * (len(test) + len(oot)))
        stab = stability_by_period(cfg, full, full_p, ref_mask)
        stab.to_csv(os.path.join(cfg.out_dir, "estabilidad_score_por_periodo.csv"), index=False)

    # --- 10. gobierno: ficha de reproducibilidad ---
    ficha = {
        "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "config": asdict(cfg),
        "n_variables_finales": len(keep),
        "variables_finales": keep,
        "calibracion": cal_report,
        "librerias": {
            "optbinning": optbinning is not None, "lightgbm": lightgbm is not None,
            "xgboost": xgboost is not None, "catboost": catboost is not None,
            "optuna": optuna is not None, "shap": shap is not None,
            "matplotlib": mpl is not None,
        },
        "benchmark_oot": bench[bench["particion"] == "oot"].to_dict(orient="records"),
    }
    json.dump(ficha, open(os.path.join(cfg.out_dir, "ficha_modelo.json"), "w"),
              indent=2, default=str)
    log.info("Artefactos guardados en: %s", os.path.abspath(cfg.out_dir))
    log.info("FIN.")
    return bench


# =============================================================================
# 12. MAIN
# =============================================================================
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Modelo PD challenger vs champion(prob_malo)")
    ap.add_argument("--data", default="data_cliente.parquet", help="ruta a .parquet/.csv")
    ap.add_argument("--out", default="artefactos_modelo")
    ap.add_argument("--target", default="target_60_12m")
    ap.add_argument("--trials", type=int, default=40, help="iteraciones Optuna")
    ap.add_argument("--oot-months", type=int, default=4)
    args = ap.parse_args()

    cfg = Config(
        data_path=args.data, out_dir=args.out, target=args.target,
        optuna_trials=args.trials, oot_n_months=args.oot_months,
    )
    run(cfg)
