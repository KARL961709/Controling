"""
EJEMPLO didáctico de lo que hace el .py en el paso de imputación de missing.
Simula el WoE de una variable y muestra:
  1) cómo quedan los valores antes/después de imputar
  2) por qué la ETIQUETA 'Missing' puede seguir apareciendo si no limpiamos woemap
No usa optbinning: arma un WoE de juguete para que se entienda la mecánica.
"""
import numpy as np
import pandas as pd

UMBRAL_MISSING_IMPUTA = 0.05
SIGN = 1   # 1 = RD (mayor riesgo = mayor WoE) ; -1 = score (mayor riesgo = menor WoE)


def cond_label_demo(woemap, var, lo, hi):
    """Versión recortada de cond_label: arma la etiqueta de un nodo (rango de WoE)."""
    info = woemap[var]
    vb, mv = info["vbins"], info["miss_val"]
    sel = [(low, high) for (w, low, high) in vb if (w > lo and w <= hi)]
    inc_miss = (mv is not None and mv > lo and mv <= hi)
    partes = []
    if sel:
        partes.append(f"({min(l for l, _ in sel):,.0f}, {max(h for _, h in sel):,.0f}]")
    if inc_miss:
        partes.append("Missing")
    return " + ".join(partes) if partes else "(ninguno)"


# ------------------------------------------------------------------
# Datos de juguete: variable "ingreso" con 30% de missing (NaN)
# ------------------------------------------------------------------
serie = pd.Series([100, 200, 300, np.nan, np.nan, np.nan, 250, 150, np.nan, 400])

# Tabla WoE simulada (lo que daría optbinning):
#   bin (lo, hi]  ->  WoE   (a mayor ingreso, mayor RD en este ejemplo -> WoE sube)
#   y el bin Missing tiene su PROPIO WoE = 0.20
vbins = [(-0.50, -np.inf, 200.0),   # WoE -0.50 para ingreso (-inf, 200]
         (0.10,  200.0,   300.0),   # WoE  0.10 para (200, 300]
         (0.90,  300.0,   np.inf)]  # WoE  0.90 para (300, inf]   <- bin de MAYOR riesgo
miss_val = 0.20                      # WoE de la bolsa Missing

woemap = {"ingreso": {"vbins": vbins, "miss_val": miss_val}}

# WoE crudo que devolvería optb.transform: cada valor a su bin, NaN -> miss_val(0.20)
def woe_de(v):
    if pd.isna(v):
        return miss_val
    for w, lo, hi in vbins:
        if lo < v <= hi:
            return w
    return vbins[-1][0]

col = serie.apply(woe_de).values.astype(float)
miss_mask = serie.isna().values

print("=" * 60)
print("ANTES de imputar")
print("=" * 60)
print(pd.DataFrame({"ingreso": serie, "WoE": col, "es_missing": miss_mask}))
print(f"\n% missing = {miss_mask.mean():.0%}  (umbral = {UMBRAL_MISSING_IMPUTA:.0%})")

# ------------------------------------------------------------------
# IMPUTACIÓN: >5% missing -> WoE del bin de MAYOR riesgo
# ------------------------------------------------------------------
if miss_mask.mean() > UMBRAL_MISSING_IMPUTA and vbins:
    woes = [w for (w, _, _) in vbins]
    woe_peor = max(woes) if SIGN == 1 else min(woes)   # RD: max ; score: min
    print(f"\nWoE de mayor riesgo (peor) = {woe_peor}")
    col[miss_mask] = woe_peor
    # CLAVE para que la etiqueta 'Missing' DESAPAREZCA de reglas/cuadros/árbol:
    woemap["ingreso"]["miss_val"] = None

print("\n" + "=" * 60)
print("DESPUÉS de imputar")
print("=" * 60)
print(pd.DataFrame({"ingreso": serie, "WoE_imputado": col, "era_missing": miss_mask}))

# ------------------------------------------------------------------
# Etiqueta de un nodo que cubre WoE en (0.5, inf]  -> ahí cae el bin peor
# ------------------------------------------------------------------
print("\n" + "=" * 60)
print("ETIQUETA del nodo WoE > 0.5 (donde caen los imputados)")
print("=" * 60)
print(" ->", cond_label_demo(woemap, "ingreso", 0.5, np.inf))
print("\nLos 4 NaN ahora valen 0.90 (bin > 300) y NO aparecen como 'Missing'.")
