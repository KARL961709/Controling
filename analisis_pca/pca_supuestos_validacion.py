# -*- coding: utf-8 -*-
"""
PCA de las variables macro de los modelos PIT (PASIVERO / NATURAL / JURIDICA)
con verificacion formal de supuestos y validacion estadistica.

Supuestos verificados:
  1. Variables continuas y escala comparable -> se estandariza (matriz de correlacion).
  2. Linealidad / correlacion suficiente entre variables (matriz R, determinante).
  3. Adecuacion muestral: KMO global y por variable (MSA).
  4. Esfericidad: test de Bartlett (H0: R = identidad).
  5. Ausencia de outliers multivariados: distancia de Mahalanobis vs chi2.
  6. Tamano muestral: n y ratio n/p.

Validacion de la solucion PCA:
  - Autovalores y varianza explicada (criterio de Kaiser: autovalor > 1).
  - Analisis paralelo de Horn (autovalores vs datos aleatorios, percentil 95).
  - Cargas (loadings) y comunalidades por variable.
"""
import numpy as np
import pandas as pd
from scipy import stats

RUTA_XLSX = "decision_final_sin_contraintuitiva.xlsx"
SEMILLA = 42

# ---------- 1. Extraccion de las series macro desde las hojas de explicabilidad ----------
def extraer_series(xl, hoja):
    df = xl.parse(hoja, header=None)
    hdr = None
    for i, fila in df.iterrows():
        vals = [str(v).strip() for v in fila]
        if vals[0] == "codmes" and "residuo" in vals:
            hdr = i
            break
    cols = [str(v).strip() for v in df.iloc[hdr]]
    data = df.iloc[hdr + 1:].copy()
    data.columns = cols
    data = data[pd.to_numeric(data["codmes"], errors="coerce").notna()]
    data["codmes"] = data["codmes"].astype(int)
    macros = [c for c in cols[cols.index("residuo") + 1:] if c and c != "nan"]
    return data[["codmes"] + macros].set_index("codmes").astype(float)

xl = pd.ExcelFile(RUTA_XLSX)
hojas = ["explicacion_variable_PASIVERO", "explicacion_variable_NATURAL", "explicacion_variable_JURIDICA"]
X = None
for h in hojas:
    f = extraer_series(xl, h)
    X = f if X is None else X.join(f, how="outer")
X = X.dropna()
n, p = X.shape
print(f"Matriz de datos: n={n} meses ({X.index.min()}-{X.index.max()}), p={p} variables")
print("Variables:", *[f"  - {c}" for c in X.columns], sep="\n")

# ---------- 2. Estandarizacion y matriz de correlacion ----------
Z = (X - X.mean()) / X.std(ddof=1)
R = np.corrcoef(Z.values, rowvar=False)
det_R = np.linalg.det(R)

print("\n== SUPUESTO: correlacion suficiente entre variables ==")
print("Matriz de correlacion:")
print(pd.DataFrame(R, index=X.columns, columns=X.columns).round(3).to_string())
print(f"Determinante de R = {det_R:.6f}  (cercano a 0 => variables correlacionadas, PCA tiene sentido; "
      f"si fuera ~1, PCA no aportaria)")

# ---------- 3. Test de esfericidad de Bartlett ----------
chi2_bart = -(n - 1 - (2 * p + 5) / 6) * np.log(det_R)
gl_bart = p * (p - 1) / 2
p_bart = stats.chi2.sf(chi2_bart, gl_bart)
print("\n== SUPUESTO: esfericidad (Bartlett) ==")
print(f"chi2 = {chi2_bart:.2f}, gl = {gl_bart:.0f}, p-valor = {p_bart:.3e}")
print("H0: la matriz de correlacion es la identidad (variables no correlacionadas).")
print("p < 0.05 =>", "SE RECHAZA H0: hay correlaciones significativas, PCA es aplicable."
      if p_bart < 0.05 else "NO se rechaza H0: PCA NO es apropiado.")

# ---------- 4. KMO (Kaiser-Meyer-Olkin) ----------
R_inv = np.linalg.inv(R)
D = np.diag(1.0 / np.sqrt(np.diag(R_inv)))
P_part = -D @ R_inv @ D          # matriz de correlaciones parciales (fuera de la diagonal)
np.fill_diagonal(P_part, 0.0)
R_off = R.copy(); np.fill_diagonal(R_off, 0.0)
kmo_global = (R_off**2).sum() / ((R_off**2).sum() + (P_part**2).sum())
kmo_var = (R_off**2).sum(axis=0) / ((R_off**2).sum(axis=0) + (P_part**2).sum(axis=0))
print("\n== SUPUESTO: adecuacion muestral (KMO) ==")
print(f"KMO global = {kmo_global:.3f}  (>=0.5 aceptable, >=0.6 mediocre-aceptable, >=0.7 bueno, >=0.8 muy bueno)")
for c, k in zip(X.columns, kmo_var):
    print(f"  MSA {c}: {k:.3f}")

# ---------- 5. Outliers multivariados (Mahalanobis) ----------
S_inv = np.linalg.inv(np.cov(Z.values, rowvar=False))
d2 = np.array([z @ S_inv @ z for z in (Z.values - Z.values.mean(axis=0))])
umbral = stats.chi2.ppf(0.999, p)
outliers = X.index[d2 > umbral].tolist()
print("\n== SUPUESTO: outliers multivariados (Mahalanobis, corte chi2 0.999) ==")
print(f"Umbral chi2(p={p}, 0.999) = {umbral:.2f}; max d2 observado = {d2.max():.2f}")
print("Outliers detectados:", outliers if outliers else "ninguno")

# ---------- 6. Tamano muestral ----------
print("\n== SUPUESTO: tamano muestral ==")
print(f"n = {n}, p = {p}, ratio n/p = {n/p:.1f}  (regla practica: >=5 aceptable, >=10 bueno)")

# ---------- 7. PCA por descomposicion espectral de R ----------
eigval, eigvec = np.linalg.eigh(R)
orden = np.argsort(eigval)[::-1]
eigval, eigvec = eigval[orden], eigvec[:, orden]
var_exp = eigval / p
print("\n== PCA: autovalores y varianza explicada ==")
acum = 0
for i, (ev, ve) in enumerate(zip(eigval, var_exp), 1):
    acum += ve
    kaiser = "<- retener (Kaiser >1)" if ev > 1 else ""
    print(f"  PC{i}: autovalor={ev:.3f}  var={ve:6.1%}  acumulada={acum:6.1%}  {kaiser}")

# ---------- 8. Analisis paralelo de Horn ----------
rng = np.random.default_rng(SEMILLA)
sims = np.array([np.sort(np.linalg.eigvalsh(np.corrcoef(rng.standard_normal((n, p)), rowvar=False)))[::-1]
                 for _ in range(2000)])
p95 = np.percentile(sims, 95, axis=0)
retener_pa = int((eigval > p95).sum())
print("\n== VALIDACION: analisis paralelo de Horn (2000 simulaciones, percentil 95) ==")
for i, (ev, u) in enumerate(zip(eigval, p95), 1):
    print(f"  PC{i}: autovalor={ev:.3f} vs umbral aleatorio={u:.3f} -> {'RETENER' if ev > u else 'descartar'}")
print(f"Componentes a retener segun analisis paralelo: {retener_pa}")

# ---------- 9. Cargas y comunalidades ----------
k = max(retener_pa, 1)
cargas = eigvec[:, :k] * np.sqrt(eigval[:k])
comunal = (cargas**2).sum(axis=1)
tabla = pd.DataFrame(cargas, index=X.columns, columns=[f"PC{i+1}" for i in range(k)])
tabla["comunalidad"] = comunal
print(f"\n== VALIDACION: cargas (loadings) de los {k} componentes retenidos y comunalidades ==")
print(tabla.round(3).to_string())

# ---------- 10. Guardar resultados ----------
X.to_csv("analisis_pca/series_macro_mensuales.csv")
tabla.to_csv("analisis_pca/pca_cargas_comunalidades.csv")
pd.DataFrame({"autovalor": eigval, "var_explicada": var_exp,
              "umbral_horn_p95": p95}).to_csv("analisis_pca/pca_autovalores.csv", index=False)
print("\nResultados guardados en analisis_pca/*.csv")
