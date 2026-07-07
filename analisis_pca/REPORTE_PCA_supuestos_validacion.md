# PCA de las variables macro — supuestos y validación estadística

**Datos:** series mensuales de las 5 variables macro de los modelos finales (PASIVERO, NATURAL, JURIDICA), extraídas de las hojas `explicacion_variable_*` de `decision_final_sin_contraintuitiva.xlsx`.
**Ventana común:** 202201–202504 (n = 40 meses, p = 5 variables).
**Script reproducible:** `pca_supuestos_validacion.py` (genera los CSV de este directorio).

## 0. Contexto: rol del PCA en esta metodología

La selección de variables de los modelos PIT **no** usó PCA: se hizo con el embudo de filtros objetivos + OLS documentado en las hojas `Metodologia_*` (elegibilidad estadística → relación estable con la mora → exclusión a priori → significancia y signo intuitivo). El PCA de este análisis es un **diagnóstico complementario**: verifica si las 5 variables macro seleccionadas comparten un factor sistémico común, lo cual respalda la lógica del modelo Vasicek de un solo factor (PIT = Φ((Φ⁻¹(pd_ttc) − √ρ·λ·F)/√(1−ρ))).

## 1. Supuestos del PCA y su verificación

| # | Supuesto | Cómo se verifica | Resultado en estos datos | ¿Cumple? |
|---|----------|------------------|--------------------------|----------|
| 1 | Variables continuas, medidas en escala de intervalo/razón | Inspección | Las 5 son índices/ratios/volúmenes continuos | ✅ |
| 2 | Escalas comparables (o estandarizar) | Las escalas difieren en órdenes de magnitud (volúmenes vs índices) | Se estandarizó (z-score) y el PCA se hizo sobre la **matriz de correlación** | ✅ (resuelto) |
| 3 | Correlación suficiente entre variables (linealidad) | Matriz de correlación y su determinante | Correlaciones entre 0.24 y 0.82; det(R) = 0.033 (lejos de 1) | ✅ |
| 4 | Esfericidad: R ≠ identidad | **Test de Bartlett** | χ² = 124.87, gl = 10, **p = 5.2e-22** → se rechaza H0 | ✅ |
| 5 | Adecuación muestral | **KMO** global y MSA por variable | KMO global = **0.649** (aceptable); MSA por variable entre 0.558 y 0.855, todas > 0.5 | ✅ (aceptable) |
| 6 | Ausencia de outliers multivariados | Distancia de Mahalanobis vs χ²(5, 0.999) = 20.52 | Máxima d² observada = 14.48 → **ningún outlier** | ✅ |
| 7 | Tamaño muestral suficiente | n y ratio n/p | n = 40, n/p = 8.0 (regla práctica: ≥5 aceptable, ≥10 bueno) | ✅ (aceptable) |

**Interpretación de los tests clave:**

- **Bartlett (esfericidad):** contrasta H0 = "las variables no están correlacionadas entre sí" (matriz de correlación = identidad). Con p ≈ 10⁻²², se rechaza contundentemente: existen correlaciones reales que el PCA puede resumir. Si no se rechazara, el PCA sería inaplicable.
- **KMO (Kaiser–Meyer–Olkin):** compara correlaciones observadas vs parciales. Valores: <0.5 inaceptable, 0.5–0.6 aceptable, 0.6–0.7 mediocre-aceptable, 0.7–0.8 bueno, >0.8 muy bueno. El 0.649 global indica que la estructura de correlación es suficientemente "compacta" para PCA, aunque no ideal (esperable con solo 5 variables y una de ellas — ratio de capital — menos ligada al resto).

## 2. Resultados del PCA

### Autovalores y varianza explicada

| Componente | Autovalor | % varianza | % acumulado | Kaiser (>1) | Horn p95 | Decisión |
|------------|-----------|-----------|-------------|-------------|----------|----------|
| PC1 | 3.337 | 66.7% | 66.7% | ✅ | 1.698 | **RETENER** |
| PC2 | 0.837 | 16.7% | 83.5% | ✗ | 1.335 | descartar |
| PC3 | 0.456 | 9.1% | 92.6% | ✗ | 1.086 | descartar |
| PC4 | 0.278 | 5.6% | 98.2% | ✗ | 0.909 | descartar |
| PC5 | 0.092 | 1.8% | 100% | ✗ | 0.731 | descartar |

### Validación del número de componentes

Dos criterios independientes coinciden en **retener 1 solo componente**:

1. **Criterio de Kaiser:** solo PC1 tiene autovalor > 1.
2. **Análisis paralelo de Horn** (2 000 simulaciones de datos aleatorios N(0,1) de la misma dimensión 40×5, umbral = percentil 95 de los autovalores simulados): solo PC1 (3.337) supera su umbral aleatorio (1.698). Este es el criterio más riguroso de la literatura, porque corrige el sesgo de Kaiser al comparar contra lo que produciría puro ruido.

### Cargas (loadings) y comunalidades — PC1

| Variable | Carga PC1 | Comunalidad |
|----------|-----------|-------------|
| SBS_bm_creditos_contingentes_MA12_L2_PL1 | −0.872 | 0.760 |
| BCRP_expectativas_economía_3m_Comercio_MA3_L2 | −0.889 | 0.790 |
| BCRP_expectativas_economía_3m_Comercio_MA12_L2 | −0.833 | 0.694 |
| SBS_ibk_ratio_capital_global_MA3_L2 | −0.597 | 0.357 |
| BCRP_expectativas_economía_12m_Servicios_MA3_L2 | −0.858 | 0.737 |

- Todas las cargas tienen el **mismo signo** y magnitud > 0.55: PC1 es un **factor sistémico común** del ciclo macro-crediticio (expectativas económicas + holgura de crédito + solvencia del sistema). El signo global del componente es arbitrario en PCA (multiplicar por −1 es equivalente).
- Comunalidades: 4 de 5 variables tienen ≥ 0.69 (bien representadas por PC1). El ratio de capital global (0.357) es la variable con más varianza propia — es una serie de solvencia, no de ciclo, coherente con su MSA más bajo (0.558).

## 3. Conclusiones

1. **Todos los supuestos formales del PCA se cumplen** en estos datos: Bartlett rechaza esfericidad (p≈10⁻²²), KMO = 0.649 (aceptable), sin outliers multivariados por Mahalanobis, n/p = 8.
2. **Existe un único factor sistémico** que explica el 66.7% de la varianza conjunta de las 5 variables macro, validado por Kaiser y por análisis paralelo de Horn. Esto **respalda empíricamente el uso del modelo Vasicek de un factor** (un solo factor sistémico F por driver) en la construcción de la PIT.
3. Las dos transformaciones de la misma serie base (expectativas Comercio 3m en MA3 y MA12) cargan casi igual en PC1 (−0.889 y −0.833), confirmando que aportan la misma señal de ciclo; su asignación a drivers distintos (PASIVERO vs NATURAL) evita colinealidad dentro de cada regresión (VIF = 1.07 en PASIVERO).

## 4. Limitaciones y advertencias (importantes para el sustento)

- **Series de tiempo, no observaciones i.i.d.:** las variables llevan medias móviles (MA3/MA12) y rezagos, lo que induce fuerte autocorrelación. Los p-valores de Bartlett asumen independencia entre observaciones, por lo que están **sobreestimados en significancia** (la evidencia sigue siendo abrumadora, pero el p-valor literal no debe citarse como exacto). El análisis paralelo de Horn es menos sensible a esto y coincide en la conclusión.
- **Las medias móviles inflan las correlaciones** entre variables (suavizado común). El 66.7% de varianza compartida debe leerse como propiedad de las variables *transformadas tal como entran a los modelos*, no de las series macro crudas.
- **n = 40** es un tamaño aceptable pero no holgado; los resultados de cargas son estables (un componente dominante y claro), pero no se recomienda extraer conclusiones de PC2 en adelante.
- El PCA aquí es **diagnóstico/sustento**, no un paso de la selección: los modelos finales usan las variables originales (interpretables ante el regulador), no los componentes.
