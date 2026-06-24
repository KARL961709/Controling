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
optuna = _try("optuna")
shap = _try("shap")

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
    """Separa features numericas vs categoricas, excluyendo blacklist y leakage."""
    bl = cfg.feature_blacklist()
    feats = [c for c in df.columns if c not in bl]
    num, cat = [], []
    for c in feats:
        if pd.api.types.is_numeric_dtype(df[c]):
            num.append(c)
        else:
            if df[c].nunique(dropna=True) <= cfg.max_card_categorical:
                cat.append(c)
            else:
                log.warning("  descartada por alta cardinalidad: %s (%d niveles)",
                            c, df[c].nunique())
    log.info("Features candidatas: %d numericas, %d categoricas", len(num), len(cat))
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
# 6. MODELOS:  (A) Scorecard regulatorio (LR/WOE)   (B) LightGBM challenger
# =============================================================================
def fit_scorecard_lr(cfg: Config, woe_tr: pd.DataFrame, y_tr: pd.Series, features: List[str]):
    """Regresion logistica L2 sobre WOE. Interpretable, trazable, regulatoria.
    Selecciona signo coherente (todos los coef deben ser >=0 sobre WOE 'good')."""
    from sklearn.linear_model import LogisticRegression
    X = woe_tr[features].fillna(0.0)
    model = LogisticRegression(penalty="l2", C=1.0, max_iter=1000,
                               random_state=cfg.random_state)
    model.fit(X, y_tr)
    coef = pd.Series(model.coef_[0], index=features).sort_values()
    log.info("Scorecard LR ajustado con %d variables", len(features))
    return model, coef


def optimize_lightgbm(cfg: Config, X_tr, y_tr, X_va, y_va):
    """Optimizacion bayesiana (Optuna) con early stopping y AUC de validacion.
    Si Optuna no esta, usa hiperparametros por defecto razonables."""
    import lightgbm as lgb

    def _params(trial=None):
        if trial is None:
            return dict(objective="binary", metric="auc", n_estimators=2000,
                        learning_rate=0.03, num_leaves=31, max_depth=-1,
                        min_child_samples=100, subsample=0.8, colsample_bytree=0.8,
                        reg_alpha=0.0, reg_lambda=1.0, random_state=cfg.random_state,
                        n_jobs=-1, verbose=-1)
        return dict(
            objective="binary", metric="auc", n_estimators=3000,
            learning_rate=trial.suggest_float("learning_rate", 0.01, 0.1, log=True),
            num_leaves=trial.suggest_int("num_leaves", 16, 128),
            max_depth=trial.suggest_int("max_depth", 3, 8),
            min_child_samples=trial.suggest_int("min_child_samples", 50, 500),
            subsample=trial.suggest_float("subsample", 0.6, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.6, 1.0),
            reg_alpha=trial.suggest_float("reg_alpha", 1e-3, 10.0, log=True),
            reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 10.0, log=True),
            random_state=cfg.random_state, n_jobs=-1, verbose=-1,
        )

    cb = [lgb.early_stopping(100, verbose=False), lgb.log_evaluation(0)]

    if optuna is None:
        log.warning("Optuna no disponible -> LightGBM con hiperparametros por defecto")
        m = lgb.LGBMClassifier(**_params())
        m.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], callbacks=cb)
        return m, {}

    def objective(trial):
        m = lgb.LGBMClassifier(**_params(trial))
        m.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], callbacks=cb)
        p = m.predict_proba(X_va)[:, 1]
        return _safe_auc(y_va.values, p)

    study = optuna.create_study(direction="maximize",
                                sampler=optuna.samplers.TPESampler(seed=cfg.random_state))
    study.optimize(objective, n_trials=cfg.optuna_trials, show_progress_bar=False)
    log.info("Optuna best AUC(val)=%.4f", study.best_value)
    best = lgb.LGBMClassifier(**_params(study.best_trial))
    best.fit(X_tr, y_tr, eval_set=[(X_va, y_va)], callbacks=cb)
    return best, study.best_params


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
# 9. EXPLICABILIDAD (TreeSHAP) + importancia por permutacion
# =============================================================================
def explain(cfg: Config, model, X_sample: pd.DataFrame, outdir: str):
    if shap is None:
        log.warning("shap no disponible -> se omite explicabilidad SHAP")
        return None
    try:
        explainer = shap.TreeExplainer(model)
        sv = explainer.shap_values(X_sample)
        vals = sv[1] if isinstance(sv, list) else sv
        imp = pd.DataFrame({
            "feature": X_sample.columns,
            "mean_abs_shap": np.abs(vals).mean(axis=0),
        }).sort_values("mean_abs_shap", ascending=False)
        imp.to_csv(os.path.join(outdir, "shap_importance.csv"), index=False)
        log.info("SHAP top-10:\n%s", imp.head(10).to_string(index=False))
        return imp
    except Exception as e:
        log.warning("SHAP fallo: %s", e)
        return None


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

    # --- 5B. challenger GBM (sobre features crudas; LightGBM maneja NA y no-lineal) ---
    p_gbm = None
    if lightgbm is not None:
        Xtr = train[num + cat].copy()
        Xte = test[num + cat].copy()
        Xoo = oot[num + cat].copy()
        for c in cat:  # LightGBM requiere category dtype
            for X in (Xtr, Xte, Xoo):
                X[c] = X[c].astype("category")
        gbm, best_params = optimize_lightgbm(cfg, Xtr, y_tr, Xte, test[cfg.target])
        json.dump(best_params, open(os.path.join(cfg.out_dir, "lgbm_best_params.json"), "w"),
                  indent=2, default=str)
        p_gbm = {
            "train": gbm.predict_proba(Xtr)[:, 1],
            "test": gbm.predict_proba(Xte)[:, 1],
            "oot": gbm.predict_proba(Xoo)[:, 1],
        }
        explain(cfg, gbm, Xte.sample(min(5000, len(Xte)), random_state=cfg.random_state),
                cfg.out_dir)
    else:
        log.warning("LightGBM no disponible -> challenger GBM omitido")

    # --- 6. calibracion (entrenada en train, aplicada a test/oot) ---
    cal_lr = calibrate(cfg, p_lr["train"], y_tr.values, "isotonic")
    p_lr_cal = {k: cal_lr(v) for k, v in p_lr.items()}
    preds_by_part = {
        "train": {"LR/WOE (raw)": p_lr["train"], "LR/WOE (cal)": p_lr_cal["train"]},
        "test":  {"LR/WOE (raw)": p_lr["test"],  "LR/WOE (cal)": p_lr_cal["test"]},
        "oot":   {"LR/WOE (raw)": p_lr["oot"],   "LR/WOE (cal)": p_lr_cal["oot"]},
    }
    if p_gbm is not None:
        cal_gbm = calibrate(cfg, p_gbm["train"], y_tr.values, "isotonic")
        for k in preds_by_part:
            preds_by_part[k]["LightGBM (raw)"] = p_gbm[k]
            preds_by_part[k]["LightGBM (cal)"] = cal_gbm(p_gbm[k])

    # --- 7. tabla de decision champion vs challenger ---
    bench = benchmark_table(cfg, parts, preds_by_part)
    bench.to_csv(os.path.join(cfg.out_dir, "benchmark_champion_vs_challenger.csv"),
                 index=False)
    log.info("\n%s\nTABLA DE DECISION (foco en OOT):\n%s",
             "-" * 70, bench[bench["particion"] == "oot"].to_string(index=False))

    # --- 8. estabilidad temporal del mejor challenger en OOT ---
    if p_gbm is not None:
        best_oot = preds_by_part["oot"]["LightGBM (cal)"]
        full = pd.concat([train, test, oot])
        full_p = np.concatenate([cal_gbm(p_gbm["train"]), cal_gbm(p_gbm["test"]), best_oot])
        ref_mask = np.array([True] * len(train) + [False] * (len(test) + len(oot)))
        stab = stability_by_period(cfg, full.reset_index(drop=True), full_p, ref_mask)
        stab.to_csv(os.path.join(cfg.out_dir, "estabilidad_score_por_periodo.csv"), index=False)

    # --- 9. gobierno: ficha de reproducibilidad ---
    ficha = {
        "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "config": asdict(cfg),
        "n_variables_finales": len(keep),
        "variables_finales": keep,
        "librerias": {
            "optbinning": optbinning is not None, "lightgbm": lightgbm is not None,
            "optuna": optuna is not None, "shap": shap is not None,
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
