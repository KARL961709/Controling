"""Genera datos sintéticos de ejemplo para probar arbol_riesgo.py."""
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
n = 2000

edad        = rng.integers(18, 75, n)
ingreso     = rng.normal(2500, 900, n).clip(600, 8000)
antiguedad  = rng.integers(0, 240, n)            # meses
monto       = rng.normal(5000, 2500, n).clip(500, 20000)
ratio_deuda = rng.beta(2, 5, n)                  # 0-1
region      = rng.choice(["Norte", "Centro", "Sur"], n, p=[0.3, 0.5, 0.2])
producto    = rng.choice(["Tarjeta", "Prestamo", "Hipoteca"], n)
genero      = rng.choice(["M", "F"], n)

# Score "verdadero": más riesgo si ratio_deuda alto, ingreso bajo, poca antiguedad
riesgo = (
    1.8 * ratio_deuda
    - 0.00025 * ingreso
    - 0.0015 * antiguedad
    + 0.10 * (producto == "Hipoteca")
    - 0.08 * (region == "Norte")
    + rng.normal(0, 0.15, n)
)
# Escala a un score 300-850 (alto = MENOS riesgo, estilo crediticio)
score = 850 - (riesgo - riesgo.min()) / (riesgo.max() - riesgo.min()) * 550

df = pd.DataFrame({
    "edad": edad, "ingreso": ingreso.round(0), "antiguedad": antiguedad,
    "monto": monto.round(0), "ratio_deuda": ratio_deuda.round(3),
    "genero": genero, "region": region, "producto": producto,
    "score": score.round(0),
})
df.to_csv("clientes.csv", index=False)
print(df.head())
print("\nscore: min", df.score.min(), "max", df.score.max())
