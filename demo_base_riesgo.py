"""Genera una base sintética con el esquema real para probar desagregacion_riesgo.py."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
n = 4000

sit = rng.choice(["INDEPENDIENTE", "DEPENDIENTE", "MIXTO"], n, p=[0.7, 0.2, 0.1])
edad = rng.integers(21, 76, n)
rk_ing = rng.integers(900, 8000, n)
deuda = np.round(rng.lognormal(7.2, 1.1, n), 2)
nro_ent = rng.integers(1, 5, n)
max_mora = rng.integers(1800, 10000, n)
m_ult = rng.integers(0, 24, n)
m_pri = rng.integers(5, 24, n)
flg_far = rng.choice([0, 1], n, p=[0.85, 0.15])
seg_gdp = rng.choice(["G1", "G2", "G3", "G4", "G5"], n, p=[0.05, 0.1, 0.2, 0.35, 0.3])

# FLG_CAST_AP: castigados tienen montos; no-castigados muchos campos vacíos
flg_cast = rng.choice(["CAST_NOIBK_REP>=5anios", "NO_CAST_NOIBK_U24M"], n, p=[0.78, 0.22])
es_cast = flg_cast == "CAST_NOIBK_REP>=5anios"

monto_total = np.where(es_cast, deuda, deuda)
monto_ibk = np.where(es_cast, np.nan, np.nan)               # casi siempre vacío
monto_otros = np.where(es_cast, deuda, np.nan)

# saldos: a veces vacíos (sobre todo si no-castigado)
tiene_saldo = rng.random(n) < np.where(es_cast, 0.45, 0.3)
saldo_pas = np.where(tiene_saldo, np.round(rng.lognormal(3, 2.5, n), 2), np.nan)
saldo_prom = saldo_pas
saldo_act = np.zeros(n)
prom_u4m = np.where(tiene_saldo, saldo_pas * rng.uniform(0.8, 1.2, n), np.nan)
max_u6m = np.where(tiene_saldo, saldo_pas * rng.uniform(1, 1.5, n), np.nan)
nro_meses_pas = np.where(tiene_saldo, rng.integers(1, 7, n), 0)

# puntaje_mod: alto = menor riesgo. Depende de ingreso, deuda, mora, segmento
seg_num = pd.Series(seg_gdp).map({"G1": 5, "G2": 4, "G3": 3, "G4": 2, "G5": 1}).values
base = (700 + 0.02 * rk_ing - 0.0006 * deuda - 0.008 * max_mora
        + 18 * seg_num - 10 * nro_ent + rng.normal(0, 40, n))
puntaje = np.clip(np.round(base), 160, 985).astype(int)

df = pd.DataFrame({
    "subject_id": np.arange(1, n + 1),
    "puntaje_mod": puntaje, "sit_laboral_mod": sit, "edad_num": edad,
    "rk_ing_num": rk_ing, "deuda_cas": deuda, "monto_castigado_total": monto_total,
    "monto_castigado_ibk": monto_ibk, "monto_castigado_otros": monto_otros,
    "nro_entidades_castigo": nro_ent, "max_dias_mora_castigo": max_mora,
    "meses_desde_ultimo_castigo": m_ult, "meses_desde_primer_castigo": m_pri,
    "saldo_pasivo_actual": saldo_pas, "saldo_prom_pasivo": saldo_prom,
    "saldo_activo_actual": saldo_act, "prom_saldo_pasivo_u4m": prom_u4m,
    "max_saldo_pasivo_u6m": max_u6m, "nro_meses_con_pasivo_u6m": nro_meses_pas,
    "flg_far_mto_trx_presencial_12m_c216": flg_far,
    "segmentacion_gdp_v2": seg_gdp, "FLG_CAST_AP": flg_cast,
})
df.to_csv("base_riesgo.tsv", sep="\t", index=False)
print(df.head())
print("\nFilas:", len(df), "| missing saldo_pasivo_actual:", df.saldo_pasivo_actual.isna().mean().round(2))
