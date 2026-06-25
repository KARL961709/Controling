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
    valid_size: float = 0.20                    # VALIDACION interna (de train) para tuning/early-stop
                                                # TEST y OOT NUNCA se usan para optimizar

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
    woe_for_all: bool = True                    # TODOS los modelos usan WOE (LR y GBMs)
    min_n_bins: int = 5                         # bins minimos del WOE (si infeasible -> auto)
    max_n_bins: int = 7                         # bins maximos del WOE
    # Seleccion final en 2 etapas: Gini univariado (top n_gini_preselect) -> SHAP (top n_features_max)
    n_gini_preselect: int = 15                  # preseleccion por Gini univariado
    n_features_max: int = 8                      # set FINAL por SHAP (parsimonioso: 8-9)
    optuna_trials: int = 40                     # iteraciones de optimizacion bayesiana
    cv_folds: int = 5                           # validacion cruzada temporal

    # --- GBM challengers + control de over/under-fitting + CALIBRACION nativa ---
    gbm_models: Tuple[str, ...] = ("lightgbm", "xgboost")   # CatBoost removido
    # rango del learning rate (bajo pero practico; 0.001 suele ser demasiado lento)
    lr_min: float = 0.005
    lr_max: float = 0.03
    n_estimators_max: int = 8000               # tope de arboles (early stopping recorta)
    early_stopping_rounds: int = 200           # paciencia del early stopping
    # La OPTIMIZACION usa LOG-LOSS (regla propia) => el modelo sale calibrado por
    # construccion (sin parche post-hoc). El objetivo penaliza ademas:
    #   - el GAP de log-loss train-val (over/under-fitting)
    #   - el error de calibracion EC en validacion (que mean(PD)~mean(RD))
    overfit_tol: float = 0.0                     # gap log-loss(val)-log-loss(train) tolerado
    overfit_penalty: float = 1.0                 # peso del castigo al gap (anti-overfit)
    w_calib: float = 0.5                         # peso del castigo al EC de validacion
    # Importante: NO se usa rebalanceo de clases (scale_pos_weight/is_unbalance):
    # distorsiona el nivel de probabilidad y descalibra. Se mantiene la tasa real.

    # --- calibracion post-hoc (DESACTIVADA por defecto: el modelo ya sale calibrado) ---
    post_hoc_calibration: bool = False
    calibration_method: str = "isotonic"         # solo si post_hoc_calibration=True

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
        "lvl_edu_poten_open",            # nivel educativo (ordinal) -> categorica, NO flag
    )
    # flags binarios; por defecto se EXCLUYEN del modelo (use_flags=False)
    flag_cols: Tuple[str, ...] = (
        "flag_bancarizado", "flg_clasi_dif_nor_1m",
    )
    use_flags: bool = False                     # False: los flags NO entran (pedido del negocio)
                                                # True: entran como categoricas

    # --- regla de seleccion del ganador ---
    select_metric: str = "Gini"                 # metrica de seleccion
    select_partition: str = "train"             # GANA el mejor en TRAIN; luego se prueba en test/OOT

    # --- gobierno ---
    random_state: int = RANDOM_STATE

    leak_cols: Tuple[str, ...] = field(default_factory=tuple)

    def feature_blacklist(self) -> set:
        """Columnas que jamas pueden ser features (ids, target, tiempo, benchmark...)."""
        bl = set(self.id_cols) | {
            self.target, self.time_col, self.champion_prob, self.champion_score,
        }
        if self.split_col:
            bl.add(self.split_col)
        bl |= set(self.leak_cols)
        if not self.use_flags:               # si NO se consideran flags, se excluyen
            bl |= set(self.flag_cols)
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


def logloss(y: np.ndarray, p: np.ndarray) -> float:
    """Log-loss (regla de scoring ESTRICTAMENTE PROPIA): su minimo se alcanza
    con probabilidades a la vez discriminantes y CALIBRADAS. Es la pieza clave
    para que el modelo salga calibrado desde la optimizacion (sin parche)."""
    from sklearn.metrics import log_loss
    mask = ~np.isnan(p)
    if mask.sum() == 0 or len(np.unique(y[mask])) < 2:
        return np.nan
    return float(log_loss(y[mask], np.clip(p[mask], 1e-6, 1 - 1e-6)))


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
        "LogLoss": logloss(y, p),
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
    forced_cat = set(cfg.known_categoricals)
    if cfg.use_flags:
        forced_cat |= set(cfg.flag_cols)
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


def resolve_schema(cfg: Config, df: pd.DataFrame, outdir: str) -> Tuple[List[str], List[str]]:
    """AUTO-IDENTIFICACION de roles por nombre de columna (no requiere editar nada).
    Decide: target, ids, tiempo, particion, benchmark (excluidos como feature),
    flags (segun cfg.use_flags), categoricas y numericas. Guarda roles_columnas.csv."""
    present = set(df.columns)
    roles: Dict[str, Tuple[str, str]] = {}

    def put(c, r, why):
        if c in present:
            roles[c] = (r, why)

    put(cfg.target, "TARGET", "variable objetivo (1=malo)")
    put(cfg.time_col, "TIEMPO", "periodo YYYYMM (OOT / PSI / CSI)")
    if cfg.split_col:
        put(cfg.split_col, "PARTICION", "train/test/oot")
    for c in cfg.id_cols:
        put(c, "ID", "identificador (excluida)")
    put(cfg.champion_prob, "BENCHMARK", "PD del modelo vigente -> champion (excluida como feature)")
    put(cfg.champion_score, "BENCHMARK", "score del modelo vigente (excluida como feature)")

    num, cat = classify_features(cfg, df)
    for c in num:
        roles[c] = ("FEATURE_NUM", "predictora numerica")
    for c in cat:
        es_flag = c in set(cfg.flag_cols)
        roles[c] = ("FEATURE_CAT", "flag/ordinal" if es_flag else "categorica (diccionario)")

    # columnas presentes en la data pero sin rol asignado (p.ej. excluidas por flags/cardinalidad)
    for c in df.columns:
        if c not in roles:
            if (not cfg.use_flags) and c in set(cfg.flag_cols):
                roles[c] = ("EXCLUIDA", "flag no considerado (use_flags=False)")
            else:
                roles[c] = ("EXCLUIDA", "alta cardinalidad / no elegible")

    rep = (pd.DataFrame([(c, r, w) for c, (r, w) in roles.items()],
                        columns=["columna", "rol", "motivo"])
           .sort_values(["rol", "columna"]))
    rep.to_csv(os.path.join(outdir, "roles_columnas.csv"), index=False)
    resumen = rep["rol"].value_counts().to_dict()
    log.info("AUTO-ESQUEMA -> %s | flags considerados: %s", resumen, cfg.use_flags)
    log.info("  target=%s | tiempo=%s | split=%s | benchmark=%s/%s",
             cfg.target, cfg.time_col, cfg.split_col, cfg.champion_prob, cfg.champion_score)
    return num, cat


# =============================================================================
# 4. BINNING SUPERVISADO + IV/WOE  (OptBinning; fallback decil)
# =============================================================================
class WoeEngine:
    """Encapsula binning monotonico (OptBinning) con fallback robusto.
    Calcula IV por variable y transforma a WOE. El AJUSTE es solo in-sample."""

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.binnings: Dict[str, object] = {}     # variable -> OptimalBinning ajustado
        self.iv_table: Optional[pd.DataFrame] = None
        self._fallback_maps: Dict[str, pd.DataFrame] = {}
        self._fallback_iv: Dict[str, float] = {}
        self.selected: List[str] = []

    # ---- OptBinning path (VARIABLE POR VARIABLE, con fallback a auto) ---------
    def _fit_one(self, name, x, y, dtype):
        """Ajusta una variable pidiendo [min_n_bins, max_n_bins]. Si el problema
        es INFEASIBLE (p.ej. binaria/pocos valores), REINTENTA en modo AUTO
        (min_n_bins=2) para no colapsar la variable a 1 solo bin."""
        from optbinning import OptimalBinning
        mono = "auto_asc_desc" if (self.cfg.monotonic and dtype == "numerical") else "auto"
        def _mk(minb):
            return OptimalBinning(name=name, dtype=dtype, min_n_bins=minb,
                                  max_n_bins=self.cfg.max_n_bins, min_bin_size=0.05,
                                  monotonic_trend=mono)
        ob = _mk(self.cfg.min_n_bins)
        ob.fit(x, y)
        n_bins = len(ob.splits) + 1 if dtype == "numerical" else len(getattr(ob, "splits", []) or []) + 1
        if ob.status != "OPTIMAL" or n_bins < self.cfg.min_n_bins:
            ob = _mk(2)                      # AUTO: deja que OptBinning decida
            ob.fit(x, y)
        return ob

    def fit_optbinning(self, X: pd.DataFrame, y: pd.Series, num, cat):
        rows = []
        yv = y.values
        for v in num:
            ob = self._fit_one(v, X[v].values, yv, "numerical")
            bt = ob.binning_table; bt.build()
            self.binnings[v] = ob
            rows.append((v, float(bt.iv)))
        for v in cat:
            ob = self._fit_one(v, X[v].astype("object").values, yv, "categorical")
            bt = ob.binning_table; bt.build()
            self.binnings[v] = ob
            rows.append((v, float(bt.iv)))
        self.iv_table = (pd.DataFrame(rows, columns=["variable", "iv"])
                         .sort_values("iv", ascending=False))
        self.iv_table["selected"] = self.iv_table["iv"].between(self.cfg.min_iv, self.cfg.max_iv)
        self.selected = self.iv_table.loc[self.iv_table["selected"], "variable"].tolist()
        log.info("OptBinning (5-7 bins, auto si infeasible): %d/%d variables superan IV[%.2f,%.2f]",
                 len(self.selected), len(num) + len(cat), self.cfg.min_iv, self.cfg.max_iv)

    def transform_optbinning(self, X: pd.DataFrame) -> pd.DataFrame:
        out = {}
        for v in self.selected:
            ob = self.binnings[v]
            xv = X[v].astype("object").values if ob.dtype == "categorical" else X[v].values
            out[f"woe_{v}"] = ob.transform(xv, metric="woe")
        return pd.DataFrame(out, index=X.index)

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
def psi_discrete(ref: pd.Series, cur: pd.Series) -> float:
    """PSI tratando cada valor WOE (= cada BIN) como una categoria.
    Mide cuanto se mueve la PROPORCION de poblacion por bin entre dos muestras.
    PSI = sum_bin (a_i - e_i) * ln(a_i / e_i).  (e=referencia, a=actual)"""
    e = ref.value_counts(normalize=True)
    a = cur.value_counts(normalize=True)
    idx = e.index.union(a.index)
    e = e.reindex(idx).fillna(1e-6).clip(lower=1e-6)
    a = a.reindex(idx).fillna(1e-6).clip(lower=1e-6)
    return float(np.sum((a - e) * np.log(a / e)))


def filter_psi_woe_over_time(cfg: Config, woe_tr: pd.DataFrame, codmes: pd.Series,
                             outdir: str) -> List[str]:
    """Estabilidad CSI sobre los BINS WOE. Referencia = el periodo MAS MINIMO
    (mes mas antiguo del train). Para cada variable se compara la distribucion de
    sus bins WOE en cada mes posterior contra el mes minimo, y se toma el PSI
    MAXIMO (el peor mes). Si ese maximo > max_psi (0.25) -> variable inestable.
    NO usa test ni OOT. Guarda psi_variables.csv."""
    months = sorted(pd.Series(codmes).dropna().unique())
    keep, rows = [], []
    if len(months) < 2:
        log.info("PSI: train tiene 1 solo periodo -> no se evalua estabilidad temporal")
        return list(woe_tr.columns)
    ref_m = months[0]                                   # periodo MAS MINIMO = referencia
    ref_mask = (codmes.values == ref_m)
    for c in woe_tr.columns:
        ref = woe_tr.loc[ref_mask, c]
        max_psi, worst = 0.0, ref_m
        for m in months[1:]:
            val = psi_discrete(ref, woe_tr.loc[codmes.values == m, c])
            if val > max_psi:
                max_psi, worst = val, m
        estable = max_psi <= cfg.max_psi
        rows.append({"variable": c, "PSI_max": round(max_psi, 4),
                     "mes_ref": ref_m, "mes_peor": worst,
                     "decision": "SELECCIONADA" if estable else "ELIMINADA"})
        if estable:
            keep.append(c)
    pd.DataFrame(rows).sort_values("PSI_max", ascending=False).to_csv(
        os.path.join(outdir, "psi_variables.csv"), index=False)
    n_drop = len(woe_tr.columns) - len(keep)
    log.info("PSI(bins WOE, ref=mes minimo %s): %d estables, %d descartadas (>%.2f)",
             ref_m, len(keep), n_drop, cfg.max_psi)
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


def _shap_rank(cfg: Config, X: pd.DataFrame, y: pd.Series) -> pd.DataFrame:
    """Importancia por SHAP (mean|SHAP|) con un GBM rapido sobre las WOE.
    Si no hay shap/lightgbm, usa |coef estandarizado| de una LR como respaldo."""
    if shap is not None and lightgbm is not None:
        import lightgbm as lgb
        m = lgb.LGBMClassifier(n_estimators=400, learning_rate=0.05, num_leaves=31,
                               min_child_samples=100, subsample=0.8, colsample_bytree=0.8,
                               reg_lambda=1.0, random_state=cfg.random_state,
                               n_jobs=-1, verbose=-1)
        m.fit(X, y)
        sv = shap.TreeExplainer(m).shap_values(X)
        vals = sv[1] if isinstance(sv, list) else sv
        imp = np.abs(vals).mean(axis=0)
    else:
        from sklearn.linear_model import LogisticRegression
        lr = LogisticRegression(max_iter=1000, random_state=cfg.random_state).fit(X, y)
        imp = np.abs(lr.coef_[0]) * X.std().values     # respaldo: |coef| * sd
    return (pd.DataFrame({"variable": X.columns, "shap_imp": imp})
            .sort_values("shap_imp", ascending=False).reset_index(drop=True))


def final_selection(cfg: Config, woe_df: pd.DataFrame, y: pd.Series,
                    n_gini: int, n_final: int, outdir: str) -> List[str]:
    """SELECCION FINAL PARSIMONIOSA en dos etapas (in-sample, solo train):
      1) GINI UNIVARIADO de cada WOE -> se queda con las top `n_gini` (si las hay).
      2) SHAP sobre esas preseleccionadas -> top `n_final` (si las hay).
    Guarda seleccion_final_variables.csv con ambos rankings y la decision."""
    cands = list(woe_df.columns)
    # 1) Gini univariado (|2*AUC-1| de cada variable WOE contra el target)
    grows = [(c, abs(gini(y.values, woe_df[c].values))) for c in cands]
    gtab = (pd.DataFrame(grows, columns=["variable", "gini_univariado"])
            .sort_values("gini_univariado", ascending=False).reset_index(drop=True))
    pre = gtab.head(n_gini)["variable"].tolist()
    log.info("Filtro 1 (Gini univariado): %d -> top %d", len(cands), len(pre))

    # 2) SHAP sobre las preseleccionadas -> top n_final
    stab = _shap_rank(cfg, woe_df[pre].fillna(0.0), y)
    final = stab.head(n_final)["variable"].tolist()
    log.info("Filtro 2 (SHAP): %d -> top %d (FINAL)", len(pre), len(final))

    rep = gtab.merge(stab, on="variable", how="left")
    rep["preselec_gini"] = rep["variable"].isin(pre)
    rep["seleccion_final"] = rep["variable"].isin(final)
    (rep.sort_values(["seleccion_final", "shap_imp", "gini_univariado"], ascending=False)
        .to_csv(os.path.join(outdir, "seleccion_final_variables.csv"), index=False))
    return final


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


def _selection_score(cfg: Config, y_tr, p_tr, y_va, p_va) -> float:
    """Objetivo de seleccion ORIENTADO A CALIBRACION (no a AUC):
        score = -logloss_val
                - w_calib   * EC_val                       (nivel: mean(PD)~mean(RD))
                - penalty   * max(0, logloss_val-logloss_tr - tol)   (anti-overfit)
    - log-loss es regla propia: su optimo da probabilidades calibradas Y
      discriminantes => el modelo sale calibrado por construccion.
    - el termino EC asegura la calibracion 'en nivel' (la metrica del entregable).
    - el gap log-loss train-val evita over/under-fitting.
    Maximizar."""
    ll_tr = logloss(np.asarray(y_tr), np.asarray(p_tr))
    ll_va = logloss(np.asarray(y_va), np.asarray(p_va))
    if np.isnan(ll_tr) or np.isnan(ll_va):
        return -1e9
    ec_va = ec_calibration(np.asarray(y_va), np.asarray(p_va))
    ec_va = 0.0 if (ec_va is None or np.isnan(ec_va)) else ec_va
    gap = max(0.0, (ll_va - ll_tr) - cfg.overfit_tol)
    return -ll_va - cfg.w_calib * ec_va - cfg.overfit_penalty * gap


def _space(model_type: str, trial, cfg: Config) -> dict:
    """Espacios de busqueda REGULARIZADOS por libreria."""
    rs = cfg.random_state
    lo, hi = cfg.lr_min, cfg.lr_max
    if model_type == "lightgbm":
        return dict(
            objective="binary", metric="binary_logloss", n_estimators=cfg.n_estimators_max,
            learning_rate=trial.suggest_float("learning_rate", lo, hi, log=True),
            num_leaves=trial.suggest_int("num_leaves", 15, 127),         # estructura
            max_depth=trial.suggest_int("max_depth", 3, 10),
            min_child_samples=trial.suggest_int("min_child_samples", 30, 600),  # hojas con minimo soporte
            min_child_weight=trial.suggest_float("min_child_weight", 1e-3, 10.0, log=True),  # min hessiana
            min_split_gain=trial.suggest_float("min_split_gain", 0.0, 1.0),     # ganancia minima para abrir
            subsample=trial.suggest_float("subsample", 0.5, 1.0),              # bagging por fila
            subsample_freq=trial.suggest_int("subsample_freq", 0, 7),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.5, 1.0),  # features por arbol
            colsample_bynode=trial.suggest_float("colsample_bynode", 0.5, 1.0),  # features por nodo
            reg_alpha=trial.suggest_float("reg_alpha", 1e-3, 30.0, log=True),    # L1
            reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 30.0, log=True),  # L2
            min_data_in_bin=trial.suggest_int("min_data_in_bin", 3, 50),
            max_bin=trial.suggest_int("max_bin", 128, 512),                      # resolucion del histograma
            path_smooth=trial.suggest_float("path_smooth", 0.0, 1.0),           # suavizado anti-overfit
            extra_trees=trial.suggest_categorical("extra_trees", [False, True]),
            random_state=rs, n_jobs=-1, verbose=-1,
        )
    if model_type == "xgboost":
        return dict(
            objective="binary:logistic", eval_metric="logloss", n_estimators=cfg.n_estimators_max,
            tree_method="hist", enable_categorical=True,
            learning_rate=trial.suggest_float("learning_rate", lo, hi, log=True),
            max_depth=trial.suggest_int("max_depth", 3, 10),
            min_child_weight=trial.suggest_float("min_child_weight", 1.0, 400.0, log=True),
            gamma=trial.suggest_float("gamma", 1e-3, 5.0, log=True),            # min loss reduction (split)
            max_delta_step=trial.suggest_float("max_delta_step", 0.0, 10.0),    # estabiliza/calibra
            subsample=trial.suggest_float("subsample", 0.5, 1.0),
            colsample_bytree=trial.suggest_float("colsample_bytree", 0.5, 1.0),
            colsample_bylevel=trial.suggest_float("colsample_bylevel", 0.5, 1.0),
            colsample_bynode=trial.suggest_float("colsample_bynode", 0.5, 1.0),
            reg_alpha=trial.suggest_float("reg_alpha", 1e-3, 30.0, log=True),
            reg_lambda=trial.suggest_float("reg_lambda", 1e-3, 30.0, log=True),
            grow_policy=trial.suggest_categorical("grow_policy", ["depthwise", "lossguide"]),
            max_bin=trial.suggest_int("max_bin", 128, 512),
            random_state=rs, n_jobs=-1, verbosity=0,
        )
    if model_type == "catboost":
        # CatBoost usa arboles SIMETRICOS (2^depth hojas) => depth y border_count
        # son los que mas pesan en tiempo. Se acotan para optimizar rapido sin
        # sacrificar calidad relevante; el early stopping recorta las iteraciones.
        return dict(
            loss_function="Logloss", eval_metric="Logloss", iterations=1500,
            learning_rate=trial.suggest_float("learning_rate", 0.02, 0.12, log=True),
            depth=trial.suggest_int("depth", 3, 6),                     # 8 era muy lento
            l2_leaf_reg=trial.suggest_float("l2_leaf_reg", 1.0, 30.0, log=True),  # L2
            random_strength=trial.suggest_float("random_strength", 0.0, 2.0),
            bagging_temperature=trial.suggest_float("bagging_temperature", 0.0, 1.0),
            border_count=trial.suggest_int("border_count", 32, 128),    # 254 era muy lento
            random_seed=rs, verbose=0, allow_writing_files=False, thread_count=-1,
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


def _fit_gbm(model_type: str, params: dict, Xtr, ytr, Xva, yva, cat: List[str],
             rounds: int = 200):
    """Ajuste con EARLY STOPPING (controla nro de arboles -> anti-overfit).
    `rounds` = paciencia (mas alta cuando el learning rate es bajo)."""
    if model_type == "lightgbm":
        import lightgbm as lgb
        m = lgb.LGBMClassifier(**params)
        m.fit(Xtr, ytr, eval_set=[(Xva, yva)],
              callbacks=[lgb.early_stopping(rounds, verbose=False), lgb.log_evaluation(0)])
        return m
    if model_type == "xgboost":
        import xgboost as xgb
        p = dict(params); p["early_stopping_rounds"] = rounds
        m = xgb.XGBClassifier(**p)
        m.fit(Xtr, ytr, eval_set=[(Xva, yva)], verbose=False)
        return m
    if model_type == "catboost":
        from catboost import CatBoostClassifier, Pool
        cat_idx = [Xtr.columns.get_loc(c) for c in cat]
        m = CatBoostClassifier(**params, od_type="Iter", od_wait=rounds, cat_features=cat_idx)
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
        return _fit_gbm(model_type, params, Xtr, ytr, Xva, yva, cat, cfg.early_stopping_rounds), {}

    def objective(trial):
        params = _space(model_type, trial, cfg)
        m = _fit_gbm(model_type, params, Xtr, ytr, Xva, yva, cat, cfg.early_stopping_rounds)
        p_tr = gbm_predict(model_type, m, Xtr)
        p_va = gbm_predict(model_type, m, Xva)
        return _selection_score(cfg, ytr, p_tr, yva, p_va)

    study = optuna.create_study(direction="maximize",
                                sampler=optuna.samplers.TPESampler(seed=cfg.random_state))
    study.optimize(objective, n_trials=cfg.optuna_trials, show_progress_bar=False)
    best_params = _space(model_type, study.best_trial, cfg)
    best = _fit_gbm(model_type, best_params, Xtr, ytr, Xva, yva, cat, cfg.early_stopping_rounds)
    p_tr = gbm_predict(model_type, best, Xtr)
    p_va = gbm_predict(model_type, best, Xva)
    log.info("%-9s | score=%.4f | AUC_val=%.4f | LogLoss tr/val=%.4f/%.4f | EC_val=%.4f",
             model_type, study.best_value, _safe_auc(yva.values, p_va),
             logloss(ytr.values, p_tr), logloss(yva.values, p_va),
             ec_calibration(yva.values, p_va))
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
    cols = ["particion", "modelo", "Gini", "KS", "AUC", "LogLoss", "Brier", "EC", "ECE",
            "MCE", "mean_pred", "mean_obs"]
    return pd.DataFrame(rows)[cols].sort_values(["particion", "Gini"], ascending=[True, False])


def select_winner(cfg: Config, parts: Dict[str, pd.DataFrame],
                  preds_by_part: Dict[str, Dict[str, np.ndarray]],
                  candidates: List[str]) -> Tuple[str, pd.DataFrame]:
    """GANA el modelo con mejor Gini en la particion de seleccion (TRAIN por defecto).
    Luego se PRUEBA en test y OOT (solo reporte, no re-seleccion).
    El champion (prob_malo) se muestra como referencia pero NO compite por el puesto."""
    rows = []
    for name in candidates:
        r = {"modelo": name}
        for part in ("train", "test", "oot"):
            y = parts[part][cfg.target].values
            p = preds_by_part[part][name]
            r[f"Gini_{part}"] = gini(y, p)
            r[f"EC_{part}"] = ec_calibration(y, p)
        rows.append(r)
    tab = pd.DataFrame(rows).sort_values(f"{cfg.select_metric}_{cfg.select_partition}",
                                         ascending=False).reset_index(drop=True)
    winner = tab.iloc[0]["modelo"]
    return winner, tab


# =============================================================================
# 11. ORQUESTACION
# =============================================================================
def run(cfg: Config):
    os.makedirs(cfg.out_dir, exist_ok=True)
    log.info("=" * 70)
    log.info("PIPELINE PD — CHALLENGER vs CHAMPION(prob_malo)  | seed=%d", cfg.random_state)
    log.info("=" * 70)
    falt = [m for m in cfg.gbm_models if {"lightgbm": lightgbm, "xgboost": xgboost,
                                          "catboost": catboost}.get(m) is None]
    if falt:
        log.warning("GBMs NO instalados (%s). Para activarlos: pip install %s",
                    ", ".join(falt), " ".join(falt))

    # --- 1. data + particion ---
    df = load_data(cfg)
    num, cat = resolve_schema(cfg, df, cfg.out_dir)   # auto-identifica roles + guarda csv
    parts = split_train_oot(cfg, df)
    train, test, oot = parts["train"], parts["test"], parts["oot"]
    y_tr = train[cfg.target]

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

    # --- 4. estabilidad + redundancia (medidas DENTRO de train; sin tocar test/OOT) ---
    # PSI sobre los BINS WOE, referencia = mes MINIMO del train (peor mes vs ref)
    keep = filter_psi_woe_over_time(cfg, woe_tr, train[cfg.time_col], cfg.out_dir)
    woe_tr, woe_te, woe_oo = woe_tr[keep], woe_te[keep], woe_oo[keep]
    iv_woe = {f"woe_{k}": v for k, v in iv_map.items()}
    keep = filter_correlation(cfg, woe_tr, iv_woe)
    woe_tr, woe_te, woe_oo = woe_tr[keep], woe_te[keep], woe_oo[keep]
    keep = filter_vif(cfg, woe_tr)
    woe_tr, woe_te, woe_oo = woe_tr[keep], woe_te[keep], woe_oo[keep]
    # SELECCION FINAL PARSIMONIOSA: Gini univariado (top n_gini) -> SHAP (top n_final)
    keep = final_selection(cfg, woe_tr, y_tr, cfg.n_gini_preselect, cfg.n_features_max, cfg.out_dir)
    woe_tr, woe_te, woe_oo = woe_tr[keep], woe_te[keep], woe_oo[keep]
    log.info("Set final de variables WOE (parsimonioso): %d", len(keep))

    # --- 5A. modelo regulatorio: Scorecard LR/WOE ---
    lr_model, lr_coef = fit_scorecard_lr(cfg, woe_tr, y_tr, keep)
    lr_coef.to_csv(os.path.join(cfg.out_dir, "scorecard_coeficientes.csv"))
    p_lr = {
        "train": lr_model.predict_proba(woe_tr.fillna(0))[:, 1],
        "test": lr_model.predict_proba(woe_te.fillna(0))[:, 1],
        "oot": lr_model.predict_proba(woe_oo.fillna(0))[:, 1],
    }

    # --- 5B. GBM sobre la MISMA matriz WOE que el scorecard (todos usan WOE) ---
    # No hay seleccion raw separada: el set WOE 'keep' (IV + PSI + correlacion + VIF)
    # alimenta por igual a LR y a los GBMs. Las columnas WOE son todas numericas
    # (sin categoricas nativas), por eso gbm_cat = [].
    gbm_feats = keep
    gbm_cat: List[str] = []
    Xtr, Xte, Xoo = woe_tr.fillna(0.0), woe_te.fillna(0.0), woe_oo.fillna(0.0)

    # VALIDACION para tuning: se separa DENTRO de train (fit interno + valid interno).
    # El TEST y el OOT NO intervienen en la optimizacion ni en el early stopping.
    from sklearn.model_selection import train_test_split as _tts
    fit_idx, val_idx = _tts(Xtr.index, test_size=cfg.valid_size,
                            random_state=cfg.random_state, stratify=y_tr)
    X_fit, y_fit = Xtr.loc[fit_idx], y_tr.loc[fit_idx]
    X_val, y_val = Xtr.loc[val_idx], y_tr.loc[val_idx]
    log.info("Tuning con validacion INTERNA de train (fit=%d, valid=%d). "
             "TEST y OOT NO se usan en la optimizacion.", len(fit_idx), len(val_idx))

    avail = {"lightgbm": lightgbm, "xgboost": xgboost, "catboost": catboost}
    gbm_models: Dict[str, object] = {}
    gbm_preds: Dict[str, Dict[str, np.ndarray]] = {}
    for mt in cfg.gbm_models:
        if avail.get(mt) is None:
            log.warning("%s no disponible -> challenger omitido", mt)
            continue
        log.info("--- Optimizando %s sobre WOE (anti-overfit, %d trials) ---", mt, cfg.optuna_trials)
        model, best_params = optimize_gbm(cfg, mt, X_fit, y_fit, X_val, y_val, gbm_cat)
        json.dump(best_params, open(os.path.join(cfg.out_dir, f"{mt}_best_params.json"), "w"),
                  indent=2, default=str)
        gbm_models[mt] = model
        gbm_preds[mt] = {
            part: gbm_predict(mt, model, X)
            for part, X in [("train", Xtr), ("test", Xte), ("oot", Xoo)]
        }

    # --- 6. CALIBRACION NATIVA (el modelo ya sale calibrado por la optimizacion
    #        log-loss; NO se aplica parche post-hoc salvo cfg.post_hoc_calibration).
    #        Aqui solo se DIAGNOSTICA EC/ECE en train/test/OOT para evidenciar que
    #        la calibracion se sostiene fuera de muestra. ---
    preds_by_part = {"train": {}, "test": {}, "oot": {}}
    all_preds = {"LR/WOE": p_lr, **gbm_preds}

    for name, preds in all_preds.items():
        if cfg.post_hoc_calibration:
            # opcional (desactivado por defecto): ajuste entrenado SOLO en train
            cal = calibrate(cfg, preds["train"], y_tr.values, cfg.calibration_method)
            preds = {k: cal(v) for k, v in preds.items()}
            log.info("%s: calibracion post-hoc aplicada (%s)", name, cfg.calibration_method)
        for part in preds_by_part:
            preds_by_part[part][name] = preds[part]

    # diagnostico de calibracion (sin transformar nada): EC/ECE por particion
    diag = []
    for name in all_preds:
        for part, dfp in parts.items():
            y = dfp[cfg.target].values
            p = preds_by_part[part][name]
            ece, _ = expected_calibration_error(y, p)
            diag.append({"modelo": name, "particion": part,
                         "EC": ec_calibration(y, p), "ECE": ece,
                         "LogLoss": logloss(y, p), "Brier": brier(y, p),
                         "mean_PD": float(np.nanmean(p)), "mean_RD": float(np.mean(y))})
    pd.DataFrame(diag).to_csv(
        os.path.join(cfg.out_dir, "diagnostico_calibracion.csv"), index=False)
    log.info("\nDIAGNOSTICO DE CALIBRACION (EC debe ser bajo en train/test/OOT):\n%s",
             pd.DataFrame(diag).to_string(index=False))

    # --- 7. tabla de metricas champion vs challengers (todas las particiones) ---
    bench = benchmark_table(cfg, parts, preds_by_part)
    bench.to_csv(os.path.join(cfg.out_dir, "benchmark_champion_vs_challenger.csv"),
                 index=False)

    # --- 7b. SELECCION DEL GANADOR: mejor Gini(train); luego se prueba en test/OOT ---
    candidates = list(all_preds.keys())                 # LR/WOE + GBMs (sin champion)
    winner, win_tab = select_winner(cfg, parts, preds_by_part, candidates)
    win_tab.to_csv(os.path.join(cfg.out_dir, "seleccion_ganador.csv"), index=False)
    log.info("\n%s\nSELECCION POR Gini(%s) — el ganador se PRUEBA en test/OOT:\n%s",
             "=" * 70, cfg.select_partition, win_tab.to_string(index=False))
    log.info(">>> GANADOR: %s  | Gini train=%.4f  test=%.4f  oot=%.4f",
             winner,
             win_tab.set_index("modelo").loc[winner, "Gini_train"],
             win_tab.set_index("modelo").loc[winner, "Gini_test"],
             win_tab.set_index("modelo").loc[winner, "Gini_oot"])

    # comparacion del ganador contra el champion (prob_malo) en las 3 particiones
    if cfg.champion_prob in df.columns:
        comp = bench[bench["modelo"].isin([winner, "CHAMPION (prob_malo)"])]
        comp.to_csv(os.path.join(cfg.out_dir, "ganador_vs_champion.csv"), index=False)
        log.info("\nGANADOR vs CHAMPION:\n%s", comp.to_string(index=False))

    # --- 8. explicabilidad SHAP del GANADOR sobre el TEST (data independiente) ---
    #   Todo el mundo usa WOE, asi que el eje X de los SHAP son los valores WOE
    #   (linea de SHAP promedio por valor WOE). Se explica sobre TEST (no train).
    n_smp = min(cfg.shap_sample, len(Xte))
    smp_idx = Xte.sample(n_smp, random_state=cfg.random_state).index
    if winner in gbm_models:
        shap_dependence_plots(
            cfg, gbm_models[winner], Xte.loc[smp_idx],
            cfg.out_dir, tag=f"woe_{winner}_test", kind="tree", is_woe=True)
    shap_dependence_plots(
        cfg, lr_model, woe_te.loc[smp_idx].fillna(0.0),
        cfg.out_dir, tag="woe_scorecard_test", kind="linear", is_woe=True)

    # --- 9. estabilidad temporal del score del GANADOR ---
    full = pd.concat([train, test, oot]).reset_index(drop=True)
    full_p = np.concatenate([preds_by_part["train"][winner],
                             preds_by_part["test"][winner],
                             preds_by_part["oot"][winner]])
    ref_mask = np.array([True] * len(train) + [False] * (len(test) + len(oot)))
    stab = stability_by_period(cfg, full, full_p, ref_mask)
    stab.to_csv(os.path.join(cfg.out_dir, "estabilidad_score_por_periodo.csv"), index=False)

    # --- 10. gobierno: ficha de reproducibilidad ---
    ficha = {
        "fecha_ejecucion": datetime.now().isoformat(timespec="seconds"),
        "config": asdict(cfg),
        "ganador": winner,
        "regla_seleccion": f"mejor {cfg.select_metric}({cfg.select_partition})",
        "seleccion": win_tab.to_dict(orient="records"),
        "n_variables_scorecard": len(keep),
        "variables_scorecard": keep,
        "n_variables_gbm": len(gbm_feats),
        "variables_gbm": gbm_feats,
        "calibracion": {"post_hoc": cfg.post_hoc_calibration, "diagnostico": diag},
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
    return winner, bench


# =============================================================================
# 12. FUNCION UNICA — tu solo pasas el CSV y hace TODO
# =============================================================================
def modelar(csv: str,
            out_dir: str = "artefactos_modelo",
            target: str = "target_60_12m",
            trials: int = 40,
            oot_months: int = 4,
            usar_flags: bool = False,
            modelos: Tuple[str, ...] = ("lightgbm", "xgboost"),
            preselect_gini: int = 15,
            max_variables: int = 8,
            lr_min: float = 0.005,
            lr_max: float = 0.03,
            n_estimators_max: int = 8000):
    """Ejecuta TODO el pipeline a partir de un CSV. Solo necesitas la ruta.

    Hace, de punta a punta y sin que configures nada:
      1. Carga el CSV y AUTO-IDENTIFICA roles (target, ids, tiempo, particion,
         benchmark prob_malo/score, flags, categoricas, numericas).
      2. Particiona train/test/OOT (usa la columna 'split' si existe; si no, los
         ultimos `oot_months` meses de 'codmes_ejec' son OOT).
      3. WOE/IV (OptBinning) + filtros de estabilidad (PSI), correlacion y VIF.
      4. Entrena scorecard LR/WOE + GBMs (LightGBM/XGBoost/CatBoost) con Optuna
         anti-overfit y CALIBRACION NATIVA (objetivo log-loss, sin parche).
      5. Elige al GANADOR por mejor Gini(train) y lo prueba en test/OOT.
      6. Compara contra el champion (prob_malo), SHAP del ganador, estabilidad y
         ficha de gobierno.

    Devuelve (winner, benchmark_df). Todos los CSV/PNG quedan en `out_dir`.

    Uso:
        from modelo_riesgo_credito import modelar
        winner, bench = modelar("mi_data.csv")
    """
    cfg = Config(
        data_path=csv, out_dir=out_dir, target=target,
        optuna_trials=trials, oot_n_months=oot_months,
        use_flags=usar_flags, gbm_models=tuple(modelos),
        n_gini_preselect=preselect_gini, n_features_max=max_variables,
        lr_min=lr_min, lr_max=lr_max, n_estimators_max=n_estimators_max,
    )
    return run(cfg)


# =============================================================================
# 13. DATA DEMO (mismas columnas del dataset real) — para PROBAR que corre
# =============================================================================
# Columnas exactas del dataset de la tabla (nivel cliente)
SCHEMA_COLUMNS = [
    "key_value", "split", "flag_bancarizado", "target_60_12m", "cnt_monto_cast",
    "max_sld_peor_clsf_1m_12m", "ant_ult_prod_allsf", "min_sldtotfinpr12m",
    "lvl_edu_poten_open", "max_sldpas12m", "nro_otr_emprep_12m", "ctd_entreport_12m",
    "max_dif_ent_12m", "ratio_saldo_rt_t1_t12", "avg_emp_telc_1m_6m", "desc_grupo_carrera",
    "dsv_sld_pc_pp_3m", "beta_sld_pc_pp_1a", "mdn_sld_totsbs_3i_6m", "flg_clasi_dif_nor_1m",
    "meses_ult_inc_10_rat_dda_pp", "cod_cuc", "avg_prc_sald_otr_ent",
    "dsv_entidadesdistrdlineatc_u1a", "prm_datraso_rd_1a", "min_sldpas_03m",
    "rat_var_sld_tot_1m_3m", "prm_decrsld12m", "prm_rat_disp_ef_pn_6m", "prm_sld_cta_sld_12m",
    "cnt_prop_insc", "cnt_prod_dist_sf_1m", "rat_nro_ent_1m_1m_24m", "ratio_comparacion_u1m_u12m",
    "nro_edad", "mto_venta_fin_de_semana_pos_ult_6m", "mto_prom_inf_debito_efectivo_u1m",
    "mto_venta_con_tarjeta_credito_pos_ult_1m", "mto_min_venta_rubro_grifos_pos_ult_6m",
    "prm_rubro_restaurantes_pos_ult_6m", "far_rubro_top2_frec_name_3m", "monto_total_u6m",
    "far_rubro_top1_monto_name_6m", "porc_prom_trx_inf_debito_efectivo_u3m",
    "mto_prom_deb_farmacia_presencial_no_ibk_u12m", "far_rubro_top3_monto_name_6m",
    "far_rubro_top2_monto_name_3m", "mto_ticket_semanal_vestido_calzado_u12m", "far_rubrofrec_9m",
    "spsa_rubro_top3_frec_name_9m", "far_rubro_top2_monto_name_6m", "spsa_rubro_top2_frec_name_12m",
    "far_rubro_top2_monto_name_9m", "far_mtomax_medicamento_1m", "mto_bienestar_persona_u1m",
    "far_rubro_top3_frec_name_1m", "prob_malo", "score", "codmes_ejec",
]
_CAT_COLS_DEMO = [
    "desc_grupo_carrera", "far_rubro_top2_frec_name_3m", "far_rubro_top1_monto_name_6m",
    "far_rubro_top3_monto_name_6m", "far_rubro_top2_monto_name_3m", "far_rubrofrec_9m",
    "spsa_rubro_top3_frec_name_9m", "far_rubro_top2_monto_name_6m",
    "spsa_rubro_top2_frec_name_12m", "far_rubro_top2_monto_name_9m", "far_rubro_top3_frec_name_1m",
]
_FLAG_COLS_DEMO = ["flag_bancarizado", "flg_clasi_dif_nor_1m", "lvl_edu_poten_open"]


def make_demo(n: int = 12000, seed: int = RANDOM_STATE) -> pd.DataFrame:
    """Genera data sintetica con LAS MISMAS COLUMNAS del dataset real, con senal
    realista (target ligado a algunas variables) y un champion prob_malo ruidoso.
    Sirve para PROBAR el pipeline end-to-end sin la data productiva."""
    rng = np.random.default_rng(seed)
    rubros = ["FARMACIA", "RESTAURANTES", "GRIFOS", "SUPERMERCADO", "VESTIDO", "OTROS"]
    meses = [202301, 202302, 202303, 202304, 202305, 202306,
             202307, 202308, 202309, 202310, 202311, 202312]
    df = pd.DataFrame({c: np.nan for c in SCHEMA_COLUMNS}, index=range(n))

    df["key_value"] = np.arange(n)
    df["cod_cuc"] = rng.integers(10**6, 10**7, n)
    df["codmes_ejec"] = rng.choice(meses, n)
    df["nro_edad"] = rng.integers(21, 75, n)

    # features numericas (varias informativas)
    num_cols = [c for c in SCHEMA_COLUMNS if c not in (
        ["key_value", "cod_cuc", "codmes_ejec", "split", "target_60_12m",
         "prob_malo", "score"] + _CAT_COLS_DEMO + _FLAG_COLS_DEMO)]
    for c in num_cols:
        df[c] = rng.normal(0, 1, n).round(4)
    # inyecta nulos en algunas
    for c in rng.choice(num_cols, 6, replace=False):
        mask = rng.random(n) < 0.1
        df.loc[mask, c] = np.nan

    # categoricas y flags
    for c in _CAT_COLS_DEMO:
        df[c] = rng.choice(rubros, n)
    df["flag_bancarizado"] = rng.integers(0, 2, n)
    df["flg_clasi_dif_nor_1m"] = rng.integers(0, 2, n)
    df["lvl_edu_poten_open"] = rng.integers(1, 5, n)
    df["desc_grupo_carrera"] = rng.choice(["INGENIERIA", "SALUD", "ADMIN", "TECNICO", "OTRO"], n)

    # logit del target ligado a algunas variables (senal real)
    z = (-1.4
         + 0.9 * df["prm_datraso_rd_1a"].fillna(0)
         + 0.7 * df["max_sld_peor_clsf_1m_12m"].fillna(0)
         - 0.5 * df["ant_ult_prod_allsf"].fillna(0)
         + 0.4 * df["flg_clasi_dif_nor_1m"]
         - 0.3 * df["flag_bancarizado"]
         + 0.3 * df["rat_var_sld_tot_1m_3m"].fillna(0))
    p = 1 / (1 + np.exp(-z))
    df["target_60_12m"] = (rng.random(n) < p).astype(int)

    # champion ruidoso (discrimina pero descalibrado, como el real)
    df["prob_malo"] = np.clip(p * 1.5 + rng.normal(0, 0.05, n), 0, 1).round(4)
    df["score"] = (1000 - 800 * df["prob_malo"]).round(1)

    # particion temporal: ultimos 3 meses = oot ; resto train/test
    df["split"] = np.where(df["codmes_ejec"] >= 202310, "oot",
                           np.where(rng.random(n) < 0.75, "train", "test"))
    return df


# =============================================================================
# 14. MAIN (CLI)
# =============================================================================
def _in_notebook() -> bool:
    """True si se ejecuta dentro de Jupyter/IPython (evita que argparse choque
    con el argumento --f=...kernel.json que inyecta el kernel)."""
    try:
        from IPython import get_ipython
        ip = get_ipython()
        return ip is not None and ip.__class__.__name__ == "ZMQInteractiveShell"
    except Exception:
        return False


def _main_cli():
    import argparse
    ap = argparse.ArgumentParser(description="Modelo PD challenger vs champion(prob_malo)")
    ap.add_argument("--data", default="data_cliente.parquet", help="ruta a .parquet/.csv")
    ap.add_argument("--out", default="artefactos_modelo")
    ap.add_argument("--target", default="target_60_12m")
    ap.add_argument("--trials", type=int, default=40, help="iteraciones Optuna")
    ap.add_argument("--oot-months", type=int, default=4)
    ap.add_argument("--no-flags", action="store_true", help="excluye los flags del modelo")
    ap.add_argument("--demo", action="store_true",
                    help="genera data sintetica con las columnas reales y prueba el pipeline")
    ap.add_argument("--demo-n", type=int, default=12000)
    # parse_known_args ignora argumentos ajenos (p.ej. los del kernel de Jupyter)
    args, _ = ap.parse_known_args()

    cfg = Config(
        data_path=args.data, out_dir=args.out, target=args.target,
        optuna_trials=args.trials, oot_n_months=args.oot_months,
        use_flags=not args.no_flags,
    )

    if args.demo:
        log.info("MODO DEMO: generando data sintetica (%d filas) con el esquema real",
                 args.demo_n)
        os.makedirs(cfg.out_dir, exist_ok=True)
        df_demo = make_demo(args.demo_n)
        demo_path = os.path.join(cfg.out_dir, "demo_data.parquet")
        try:
            df_demo.to_parquet(demo_path)
            cfg.data_path = demo_path
        except Exception:
            demo_path = os.path.join(cfg.out_dir, "demo_data.csv")
            df_demo.to_csv(demo_path, index=False)
            cfg.data_path = demo_path

    run(cfg)


# Solo ejecuta el CLI si es un script de terminal; en notebook NO hace nada
# (ahi simplemente llamas:  modelar("mi_data.csv")  ).
if __name__ == "__main__" and not _in_notebook():
    _main_cli()
