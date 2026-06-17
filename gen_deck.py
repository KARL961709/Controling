# -*- coding: utf-8 -*-
"""Genera comparacion_modelos.html: deck comparando Solo árbol (A) vs Optbinning+árbol (B),
ambos SIN edad_num ni rk_ing_num. Dibuja los árboles estilo flujo (como la imagen 1N)."""

# ----------------------------------------------------------------------------- árboles (export_text reales)
TREES = {}
TREES[("A","CAST")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- saldo_activo_actual <= -50000000.00
|   |   |--- segmentacion_gdp_v2 <= 2.50
|   |   |   |--- value: [803.44]
|   |   |--- segmentacion_gdp_v2 >  2.50
|   |   |   |--- max_dias_mora_castigo <= 2649.50
|   |   |   |   |--- max_dias_mora_castigo <= 2311.50
|   |   |   |   |   |--- value: [779.55]
|   |   |   |   |--- max_dias_mora_castigo >  2311.50
|   |   |   |   |   |--- value: [764.87]
|   |   |   |--- max_dias_mora_castigo >  2649.50
|   |   |   |   |--- nro_entidades_castigo <= 1.50
|   |   |   |   |   |--- max_dias_mora_castigo <= 3038.50
|   |   |   |   |   |   |--- value: [757.12]
|   |   |   |   |   |--- max_dias_mora_castigo >  3038.50
|   |   |   |   |   |   |--- value: [750.47]
|   |   |   |   |--- nro_entidades_castigo >  1.50
|   |   |   |   |   |--- value: [727.04]
|   |--- saldo_activo_actual >  -50000000.00
|   |   |--- value: [713.75]
|--- segmentacion_gdp_v2 >  4.50
|   |--- saldo_activo_actual <= -50000000.00
|   |   |--- max_dias_mora_castigo <= 4428.50
|   |   |   |--- monto_castigado_otros <= 931.90
|   |   |   |   |--- value: [713.75]
|   |   |   |--- monto_castigado_otros >  931.90
|   |   |   |   |--- value: [713.75]
|   |   |--- max_dias_mora_castigo >  4428.50
|   |   |   |--- value: [695.49]
|   |--- saldo_activo_actual >  -50000000.00
|   |   |--- prom_saldo_pasivo_u4m <= 88.37
|   |   |   |--- max_dias_mora_castigo <= 2473.50
|   |   |   |   |--- value: [670.44]
|   |   |   |--- max_dias_mora_castigo >  2473.50
|   |   |   |   |--- max_dias_mora_castigo <= 2991.50
|   |   |   |   |   |--- value: [637.74]
|   |   |   |   |--- max_dias_mora_castigo >  2991.50
|   |   |   |   |   |--- saldo_pasivo_actual <= 2.24
|   |   |   |   |   |   |--- value: [608.01]
|   |   |   |   |   |--- saldo_pasivo_actual >  2.24
|   |   |   |   |   |   |--- value: [625.47]
|   |   |--- prom_saldo_pasivo_u4m >  88.37
|   |   |   |--- value: [713.75]
"""
TREES[("B","CAST")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- max_dias_mora_castigo <= 2533.50
|   |   |--- segmentacion_gdp_v2 <= 3.50
|   |   |   |--- value: [794.59]
|   |   |--- segmentacion_gdp_v2 >  3.50
|   |   |   |--- max_dias_mora_castigo <= 2079.50
|   |   |   |   |--- value: [770.10]
|   |   |   |--- max_dias_mora_castigo >  2079.50
|   |   |   |   |--- value: [753.48]
|   |--- max_dias_mora_castigo >  2533.50
|   |   |--- max_dias_mora_castigo <= 2965.50
|   |   |   |--- max_dias_mora_castigo <= 2747.50
|   |   |   |   |--- value: [749.11]
|   |   |   |--- max_dias_mora_castigo >  2747.50
|   |   |   |   |--- value: [748.87]
|   |   |--- max_dias_mora_castigo >  2965.50
|   |   |   |--- prom_saldo_pasivo_u4m <= 17.06
|   |   |   |   |--- DEUDA_CAS <= 436.68
|   |   |   |   |   |--- value: [733.95]
|   |   |   |   |--- DEUDA_CAS >  436.68
|   |   |   |   |   |--- max_dias_mora_castigo <= 3661.50
|   |   |   |   |   |   |--- value: [730.91]
|   |   |   |   |   |--- max_dias_mora_castigo >  3661.50
|   |   |   |   |   |   |--- value: [727.45]
|   |   |   |--- prom_saldo_pasivo_u4m >  17.06
|   |   |   |   |--- value: [739.53]
|--- segmentacion_gdp_v2 >  4.50
|   |--- max_dias_mora_castigo <= 2470.50
|   |   |--- prom_saldo_pasivo_u4m <= 3.75
|   |   |   |--- value: [709.71]
|   |   |--- prom_saldo_pasivo_u4m >  3.75
|   |   |   |--- value: [711.06]
|   |--- max_dias_mora_castigo >  2470.50
|   |   |--- nro_entidades_castigo <= 1.50
|   |   |   |--- max_dias_mora_castigo <= 2995.50
|   |   |   |   |--- value: [690.71]
|   |   |   |--- max_dias_mora_castigo >  2995.50
|   |   |   |   |--- max_dias_mora_castigo <= 4675.50
|   |   |   |   |   |--- max_dias_mora_castigo <= 3673.50
|   |   |   |   |   |   |--- value: [681.48]
|   |   |   |   |   |--- max_dias_mora_castigo >  3673.50
|   |   |   |   |   |   |--- value: [676.50]
|   |   |   |   |--- max_dias_mora_castigo >  4675.50
|   |   |   |   |   |--- value: [669.61]
|   |   |--- nro_entidades_castigo >  1.50
|   |   |   |--- value: [635.44]
"""
TREES[("A","NOCAST")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- segmentacion_gdp_v2 <= 3.50
|   |   |--- segmentacion_gdp_v2 <= 2.50
|   |   |   |--- value: [826.65]
|   |   |--- segmentacion_gdp_v2 >  2.50
|   |   |   |--- meses_desde_ultimo_castigo <= 6.50
|   |   |   |   |--- value: [754.92]
|   |   |   |--- meses_desde_ultimo_castigo >  6.50
|   |   |   |   |--- meses_desde_ultimo_castigo <= 13.50
|   |   |   |   |   |--- value: [770.03]
|   |   |   |   |--- meses_desde_ultimo_castigo >  13.50
|   |   |   |   |   |--- value: [771.72]
|   |--- segmentacion_gdp_v2 >  3.50
|   |   |--- prom_saldo_pasivo_u4m <= 41.67
|   |   |   |--- meses_desde_primer_castigo <= 20.50
|   |   |   |   |--- value: [703.22]
|   |   |   |--- meses_desde_primer_castigo >  20.50
|   |   |   |   |--- DEUDA_CAS <= 505.87
|   |   |   |   |   |--- value: [737.94]
|   |   |   |   |--- DEUDA_CAS >  505.87
|   |   |   |   |   |--- value: [722.13]
|   |   |--- prom_saldo_pasivo_u4m >  41.67
|   |   |   |--- value: [754.69]
|--- segmentacion_gdp_v2 >  4.50
|   |--- meses_desde_primer_castigo <= 9.50
|   |   |--- value: [518.57]
|   |--- meses_desde_primer_castigo >  9.50
|   |   |--- prom_saldo_pasivo_u4m <= 54.50
|   |   |   |--- meses_desde_ultimo_castigo <= 17.50
|   |   |   |   |--- DEUDA_CAS <= 422.90
|   |   |   |   |   |--- value: [670.95]
|   |   |   |   |--- DEUDA_CAS >  422.90
|   |   |   |   |   |--- value: [658.08]
|   |   |   |--- meses_desde_ultimo_castigo >  17.50
|   |   |   |   |--- value: [681.42]
|   |   |--- prom_saldo_pasivo_u4m >  54.50
|   |   |   |--- value: [702.68]
"""
TREES[("B","NOCAST")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- segmentacion_gdp_v2 <= 3.50
|   |   |--- segmentacion_gdp_v2 <= 2.50
|   |   |   |--- value: [826.65]
|   |   |--- segmentacion_gdp_v2 >  2.50
|   |   |   |--- meses_desde_ultimo_castigo <= 6.50
|   |   |   |   |--- value: [754.92]
|   |   |   |--- meses_desde_ultimo_castigo >  6.50
|   |   |   |   |--- meses_desde_ultimo_castigo <= 13.50
|   |   |   |   |   |--- value: [770.03]
|   |   |   |   |--- meses_desde_ultimo_castigo >  13.50
|   |   |   |   |   |--- value: [771.72]
|   |--- segmentacion_gdp_v2 >  3.50
|   |   |--- prom_saldo_pasivo_u4m <= 41.67
|   |   |   |--- meses_desde_primer_castigo <= 20.50
|   |   |   |   |--- value: [703.22]
|   |   |   |--- meses_desde_primer_castigo >  20.50
|   |   |   |   |--- DEUDA_CAS <= 505.87
|   |   |   |   |   |--- value: [737.94]
|   |   |   |   |--- DEUDA_CAS >  505.87
|   |   |   |   |   |--- value: [722.13]
|   |   |--- prom_saldo_pasivo_u4m >  41.67
|   |   |   |--- value: [754.69]
|--- segmentacion_gdp_v2 >  4.50
|   |--- meses_desde_primer_castigo <= 9.50
|   |   |--- value: [518.57]
|   |--- meses_desde_primer_castigo >  9.50
|   |   |--- prom_saldo_pasivo_u4m <= 54.50
|   |   |   |--- meses_desde_ultimo_castigo <= 17.50
|   |   |   |   |--- DEUDA_CAS <= 422.90
|   |   |   |   |   |--- value: [670.95]
|   |   |   |   |--- DEUDA_CAS >  422.90
|   |   |   |   |   |--- value: [658.08]
|   |   |   |--- meses_desde_ultimo_castigo >  17.50
|   |   |   |   |--- value: [681.42]
|   |   |--- prom_saldo_pasivo_u4m >  54.50
|   |   |   |--- value: [702.68]
"""
TREES[("A","CASTfar")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- prom_saldo_pasivo_u4m <= 601.91
|   |   |--- saldo_activo_actual <= -50000000.00
|   |   |   |--- segmentacion_gdp_v2 <= 3.50
|   |   |   |   |--- max_dias_mora_castigo <= 3744.50
|   |   |   |   |   |--- value: [790.78]
|   |   |   |   |--- max_dias_mora_castigo >  3744.50
|   |   |   |   |   |--- value: [767.43]
|   |   |   |--- segmentacion_gdp_v2 >  3.50
|   |   |   |   |--- max_dias_mora_castigo <= 3050.50
|   |   |   |   |   |--- value: [762.46]
|   |   |   |   |--- max_dias_mora_castigo >  3050.50
|   |   |   |   |   |--- max_dias_mora_castigo <= 3786.50
|   |   |   |   |   |   |--- value: [730.98]
|   |   |   |   |   |--- max_dias_mora_castigo >  3786.50
|   |   |   |   |   |   |--- value: [729.39]
|   |   |--- saldo_activo_actual >  -50000000.00
|   |   |   |--- value: [711.60]
|   |--- prom_saldo_pasivo_u4m >  601.91
|   |   |--- value: [840.37]
|--- segmentacion_gdp_v2 >  4.50
|   |--- max_dias_mora_castigo <= 2479.50
|   |   |--- saldo_activo_actual <= -50000000.00
|   |   |   |--- value: [711.60]
|   |   |--- saldo_activo_actual >  -50000000.00
|   |   |   |--- max_dias_mora_castigo <= 2078.50
|   |   |   |   |--- value: [707.40]
|   |   |   |--- max_dias_mora_castigo >  2078.50
|   |   |   |   |--- value: [687.06]
|   |--- max_dias_mora_castigo >  2479.50
|   |   |--- saldo_activo_actual <= -50000000.00
|   |   |   |--- value: [685.19]
|   |   |--- saldo_activo_actual >  -50000000.00
|   |   |   |--- prom_saldo_pasivo_u4m <= 29.35
|   |   |   |   |--- max_dias_mora_castigo <= 3118.50
|   |   |   |   |   |--- value: [627.76]
|   |   |   |   |--- max_dias_mora_castigo >  3118.50
|   |   |   |   |   |--- max_dias_mora_castigo <= 4337.50
|   |   |   |   |   |   |--- value: [608.40]
|   |   |   |   |   |--- max_dias_mora_castigo >  4337.50
|   |   |   |   |   |   |--- value: [592.82]
|   |   |   |--- prom_saldo_pasivo_u4m >  29.35
|   |   |   |   |--- value: [685.18]
"""
TREES[("B","CASTfar")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- prom_saldo_pasivo_u4m <= 601.91
|   |   |--- max_dias_mora_castigo <= 2563.50
|   |   |   |--- max_dias_mora_castigo <= 2255.50
|   |   |   |   |--- nro_entidades_castigo <= 1.50
|   |   |   |   |   |--- value: [789.79]
|   |   |   |   |--- nro_entidades_castigo >  1.50
|   |   |   |   |   |--- value: [776.15]
|   |   |   |--- max_dias_mora_castigo >  2255.50
|   |   |   |   |--- value: [759.01]
|   |   |--- max_dias_mora_castigo >  2563.50
|   |   |   |--- max_dias_mora_castigo <= 2960.50
|   |   |   |   |--- value: [745.08]
|   |   |   |--- max_dias_mora_castigo >  2960.50
|   |   |   |   |--- prom_saldo_pasivo_u4m <= 45.24
|   |   |   |   |   |--- max_dias_mora_castigo <= 3660.50
|   |   |   |   |   |   |--- value: [726.94]
|   |   |   |   |   |--- max_dias_mora_castigo >  3660.50
|   |   |   |   |   |   |--- value: [720.67]
|   |   |   |   |--- prom_saldo_pasivo_u4m >  45.24
|   |   |   |   |   |--- value: [733.42]
|   |--- prom_saldo_pasivo_u4m >  601.91
|   |   |--- value: [840.37]
|--- segmentacion_gdp_v2 >  4.50
|   |--- max_dias_mora_castigo <= 2479.50
|   |   |--- prom_saldo_pasivo_u4m <= 0.69
|   |   |   |--- value: [711.57]
|   |   |--- prom_saldo_pasivo_u4m >  0.69
|   |   |   |--- value: [711.58]
|   |--- max_dias_mora_castigo >  2479.50
|   |   |--- nro_entidades_castigo <= 1.50
|   |   |   |--- prom_saldo_pasivo_u4m <= 14.66
|   |   |   |   |--- max_dias_mora_castigo <= 3792.50
|   |   |   |   |   |--- max_dias_mora_castigo <= 3028.50
|   |   |   |   |   |   |--- value: [672.70]
|   |   |   |   |   |--- max_dias_mora_castigo >  3028.50
|   |   |   |   |   |   |--- value: [665.23]
|   |   |   |   |--- max_dias_mora_castigo >  3792.50
|   |   |   |   |   |--- value: [651.12]
|   |   |   |--- prom_saldo_pasivo_u4m >  14.66
|   |   |   |   |--- value: [685.19]
|   |   |--- nro_entidades_castigo >  1.50
|   |   |   |--- value: [634.04]
"""
TREES[("A","NOCASTfar")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- segmentacion_gdp_v2 <= 2.50
|   |   |--- DEUDA_CAS <= 551.30
|   |   |   |--- value: [875.36]
|   |   |--- DEUDA_CAS >  551.30
|   |   |   |--- value: [834.84]
|   |--- segmentacion_gdp_v2 >  2.50
|   |   |--- segmentacion_gdp_v2 <= 3.50
|   |   |   |--- meses_desde_ultimo_castigo <= 5.50
|   |   |   |   |--- value: [770.92]
|   |   |   |--- meses_desde_ultimo_castigo >  5.50
|   |   |   |   |--- DEUDA_CAS <= 804.58
|   |   |   |   |   |--- value: [801.65]
|   |   |   |   |--- DEUDA_CAS >  804.58
|   |   |   |   |   |--- meses_desde_ultimo_castigo <= 13.50
|   |   |   |   |   |   |--- value: [786.32]
|   |   |   |   |   |--- meses_desde_ultimo_castigo >  13.50
|   |   |   |   |   |   |--- value: [788.43]
|   |   |--- segmentacion_gdp_v2 >  3.50
|   |   |   |--- prom_saldo_pasivo_u4m <= 10.27
|   |   |   |   |--- meses_desde_ultimo_castigo <= 6.50
|   |   |   |   |   |--- value: [719.40]
|   |   |   |   |--- meses_desde_ultimo_castigo >  6.50
|   |   |   |   |   |--- DEUDA_CAS <= 661.41
|   |   |   |   |   |   |--- value: [747.98]
|   |   |   |   |   |--- DEUDA_CAS >  661.41
|   |   |   |   |   |   |--- value: [734.81]
|   |   |   |--- prom_saldo_pasivo_u4m >  10.27
|   |   |   |   |--- value: [763.34]
|--- segmentacion_gdp_v2 >  4.50
|   |--- meses_desde_primer_castigo <= 11.50
|   |   |--- value: [561.88]
|   |--- meses_desde_primer_castigo >  11.50
|   |   |--- prom_saldo_pasivo_u4m <= 46.04
|   |   |   |--- DEUDA_CAS <= 260.86
|   |   |   |   |--- value: [691.47]
|   |   |   |--- DEUDA_CAS >  260.86
|   |   |   |   |--- meses_desde_ultimo_castigo <= 19.50
|   |   |   |   |   |--- DEUDA_CAS <= 500.31
|   |   |   |   |   |   |--- value: [663.25]
|   |   |   |   |   |--- DEUDA_CAS >  500.31
|   |   |   |   |   |   |--- value: [663.01]
|   |   |   |   |--- meses_desde_ultimo_castigo >  19.50
|   |   |   |   |   |--- value: [676.96]
|   |   |--- prom_saldo_pasivo_u4m >  46.04
|   |   |   |--- value: [718.60]
"""
TREES[("B","NOCASTfar")] = TREES[("A","NOCASTfar")]   # idéntico en este escenario

# ===== Corrida COMPLETA (con ingreso y edad) — sobrescribe los árboles =====
TREES[("A","CAST")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- saldo_activo_actual <= -50000000.00
|   |   |--- edad_num <= 57.50
|   |   |   |--- max_dias_mora_castigo <= 2933.50
|   |   |   |   |--- value: [761.01]
|   |   |   |--- max_dias_mora_castigo >  2933.50
|   |   |   |   |--- edad_num <= 51.50
|   |   |   |   |   |--- max_dias_mora_castigo <= 4089.50
|   |   |   |   |   |   |--- value: [727.24]
|   |   |   |   |   |--- max_dias_mora_castigo >  4089.50
|   |   |   |   |   |   |--- value: [718.60]
|   |   |   |   |--- edad_num >  51.50
|   |   |   |   |   |--- value: [740.35]
|   |   |--- edad_num >  57.50
|   |   |   |--- max_dias_mora_castigo <= 2640.50
|   |   |   |   |--- value: [796.72]
|   |   |   |--- max_dias_mora_castigo >  2640.50
|   |   |   |   |--- segmentacion_gdp_v2 <= 3.50
|   |   |   |   |   |--- value: [778.92]
|   |   |   |   |--- segmentacion_gdp_v2 >  3.50
|   |   |   |   |   |--- rk_ing_num <= 1657.50
|   |   |   |   |   |   |--- value: [762.65]
|   |   |   |   |   |--- rk_ing_num >  1657.50
|   |   |   |   |   |   |--- value: [771.48]
|   |--- saldo_activo_actual >  -50000000.00
|   |   |--- value: [713.75]
|--- segmentacion_gdp_v2 >  4.50
|   |--- saldo_activo_actual <= -50000000.00
|   |   |--- max_dias_mora_castigo <= 4428.50
|   |   |   |--- monto_castigado_total <= 931.90
|   |   |   |   |--- value: [713.75]
|   |   |   |--- monto_castigado_total >  931.90
|   |   |   |   |--- value: [713.75]
|   |   |--- max_dias_mora_castigo >  4428.50
|   |   |   |--- value: [695.49]
|   |--- saldo_activo_actual >  -50000000.00
|   |   |--- prom_saldo_pasivo_u4m <= 88.37
|   |   |   |--- rk_ing_num <= 2644.50
|   |   |   |   |--- max_dias_mora_castigo <= 2926.50
|   |   |   |   |   |--- value: [634.30]
|   |   |   |   |--- max_dias_mora_castigo >  2926.50
|   |   |   |   |   |--- value: [585.79]
|   |   |   |--- rk_ing_num >  2644.50
|   |   |   |   |--- value: [672.46]
|   |   |--- prom_saldo_pasivo_u4m >  88.37
|   |   |   |--- value: [713.75]
"""
TREES[("A","CASTfar")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- rk_ing_num <= 3425.50
|   |   |--- edad_num <= 59.50
|   |   |   |--- saldo_activo_actual <= -50000000.00
|   |   |   |   |--- max_dias_mora_castigo <= 4011.50
|   |   |   |   |   |--- value: [747.72]
|   |   |   |   |--- max_dias_mora_castigo >  4011.50
|   |   |   |   |   |--- max_dias_mora_castigo <= 4667.50
|   |   |   |   |   |   |--- value: [722.47]
|   |   |   |   |   |--- max_dias_mora_castigo >  4667.50
|   |   |   |   |   |   |--- value: [721.91]
|   |   |   |--- saldo_activo_actual >  -50000000.00
|   |   |   |   |--- value: [711.60]
|   |   |--- edad_num >  59.50
|   |   |   |--- saldo_activo_actual <= -50000000.00
|   |   |   |   |--- value: [778.80]
|   |   |   |--- saldo_activo_actual >  -50000000.00
|   |   |   |   |--- value: [754.30]
|   |--- rk_ing_num >  3425.50
|   |   |--- rk_ing_num <= 4093.50
|   |   |   |--- value: [797.12]
|   |   |--- rk_ing_num >  4093.50
|   |   |   |--- value: [851.68]
|--- segmentacion_gdp_v2 >  4.50
|   |--- max_dias_mora_castigo <= 2479.50
|   |   |--- saldo_activo_actual <= -50000000.00
|   |   |   |--- value: [711.60]
|   |   |--- saldo_activo_actual >  -50000000.00
|   |   |   |--- max_dias_mora_castigo <= 2078.50
|   |   |   |   |--- value: [707.40]
|   |   |   |--- max_dias_mora_castigo >  2078.50
|   |   |   |   |--- value: [687.06]
|   |--- max_dias_mora_castigo >  2479.50
|   |   |--- saldo_activo_actual <= -50000000.00
|   |   |   |--- value: [685.19]
|   |   |--- saldo_activo_actual >  -50000000.00
|   |   |   |--- prom_saldo_pasivo_u4m <= 29.35
|   |   |   |   |--- rk_ing_num <= 2667.50
|   |   |   |   |   |--- value: [585.69]
|   |   |   |   |--- rk_ing_num >  2667.50
|   |   |   |   |   |--- value: [645.30]
|   |   |   |--- prom_saldo_pasivo_u4m >  29.35
|   |   |   |   |--- value: [685.18]
"""
TREES[("A","NOCAST")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- rk_ing_num <= 3422.50
|   |   |--- segmentacion_gdp_v2 <= 3.50
|   |   |   |--- edad_num <= 56.50
|   |   |   |   |--- rk_ing_num <= 2044.50
|   |   |   |   |   |--- value: [746.98]
|   |   |   |   |--- rk_ing_num >  2044.50
|   |   |   |   |   |--- value: [763.51]
|   |   |   |--- edad_num >  56.50
|   |   |   |   |--- value: [781.15]
|   |   |--- segmentacion_gdp_v2 >  3.50
|   |   |   |--- edad_num <= 39.50
|   |   |   |   |--- edad_num <= 32.50
|   |   |   |   |   |--- value: [702.82]
|   |   |   |   |--- edad_num >  32.50
|   |   |   |   |   |--- value: [704.43]
|   |   |   |--- edad_num >  39.50
|   |   |   |   |--- meses_desde_ultimo_castigo <= 5.50
|   |   |   |   |   |--- value: [713.29]
|   |   |   |   |--- meses_desde_ultimo_castigo >  5.50
|   |   |   |   |   |--- DEUDA_CAS <= 571.77
|   |   |   |   |   |   |--- value: [729.70]
|   |   |   |   |   |--- DEUDA_CAS >  571.77
|   |   |   |   |   |   |--- value: [723.01]
|   |--- rk_ing_num >  3422.50
|   |   |--- rk_ing_num <= 4104.50
|   |   |   |--- value: [802.62]
|   |   |--- rk_ing_num >  4104.50
|   |   |   |--- value: [857.88]
|--- segmentacion_gdp_v2 >  4.50
|   |--- meses_desde_primer_castigo <= 9.50
|   |   |--- value: [518.57]
|   |--- meses_desde_primer_castigo >  9.50
|   |   |--- rk_ing_num <= 2823.50
|   |   |   |--- edad_num <= 35.50
|   |   |   |   |--- DEUDA_CAS <= 407.23
|   |   |   |   |   |--- value: [663.62]
|   |   |   |   |--- DEUDA_CAS >  407.23
|   |   |   |   |   |--- edad_num <= 28.50
|   |   |   |   |   |   |--- value: [644.08]
|   |   |   |   |   |--- edad_num >  28.50
|   |   |   |   |   |   |--- value: [652.46]
|   |   |   |--- edad_num >  35.50
|   |   |   |   |--- edad_num <= 40.50
|   |   |   |   |   |--- edad_num <= 37.50
|   |   |   |   |   |   |--- value: [666.28]
|   |   |   |   |   |--- edad_num >  37.50
|   |   |   |   |   |   |--- value: [668.57]
|   |   |   |   |--- edad_num >  40.50
|   |   |   |   |   |--- value: [680.43]
|   |   |--- rk_ing_num >  2823.50
|   |   |   |--- prom_saldo_pasivo_u4m <= 0.34
|   |   |   |   |--- value: [702.55]
|   |   |   |--- prom_saldo_pasivo_u4m >  0.34
|   |   |   |   |--- value: [702.69]
"""
TREES[("A","NOCASTfar")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- rk_ing_num <= 3443.50
|   |   |--- segmentacion_gdp_v2 <= 3.50
|   |   |   |--- rk_ing_num <= 1791.50
|   |   |   |   |--- value: [767.37]
|   |   |   |--- rk_ing_num >  1791.50
|   |   |   |   |--- DEUDA_CAS <= 1186.94
|   |   |   |   |   |--- value: [793.13]
|   |   |   |   |--- DEUDA_CAS >  1186.94
|   |   |   |   |   |--- value: [792.66]
|   |   |--- segmentacion_gdp_v2 >  3.50
|   |   |   |--- DEUDA_CAS <= 230.30
|   |   |   |   |--- value: [742.74]
|   |   |   |--- DEUDA_CAS >  230.30
|   |   |   |   |--- saldo_pasivo_actual <= 1.34
|   |   |   |   |   |--- value: [718.61]
|   |   |   |   |--- saldo_pasivo_actual >  1.34
|   |   |   |   |   |--- value: [720.07]
|   |--- rk_ing_num >  3443.50
|   |   |--- segmentacion_gdp_v2 <= 2.50
|   |   |   |--- value: [883.37]
|   |   |--- segmentacion_gdp_v2 >  2.50
|   |   |   |--- rk_ing_num <= 4507.50
|   |   |   |   |--- rk_ing_num <= 3827.50
|   |   |   |   |   |--- value: [796.99]
|   |   |   |   |--- rk_ing_num >  3827.50
|   |   |   |   |   |--- value: [816.28]
|   |   |   |--- rk_ing_num >  4507.50
|   |   |   |   |--- value: [850.96]
|--- segmentacion_gdp_v2 >  4.50
|   |--- meses_desde_primer_castigo <= 11.50
|   |   |--- value: [561.88]
|   |--- meses_desde_primer_castigo >  11.50
|   |   |--- rk_ing_num <= 2829.50
|   |   |   |--- prom_saldo_pasivo_u4m <= 25.08
|   |   |   |   |--- edad_num <= 35.50
|   |   |   |   |   |--- DEUDA_CAS <= 422.95
|   |   |   |   |   |   |--- value: [660.29]
|   |   |   |   |   |--- DEUDA_CAS >  422.95
|   |   |   |   |   |   |--- value: [643.79]
|   |   |   |   |--- edad_num >  35.50
|   |   |   |   |   |--- DEUDA_CAS <= 745.33
|   |   |   |   |   |   |--- value: [674.47]
|   |   |   |   |   |--- DEUDA_CAS >  745.33
|   |   |   |   |   |   |--- value: [672.54]
|   |   |   |--- prom_saldo_pasivo_u4m >  25.08
|   |   |   |   |--- value: [691.17]
|   |   |--- rk_ing_num >  2829.50
|   |   |   |--- saldo_pasivo_actual <= 0.15
|   |   |   |   |--- value: [718.09]
|   |   |   |--- saldo_pasivo_actual >  0.15
|   |   |   |   |--- value: [718.60]
"""
TREES[("B","CAST")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- edad_num <= 59.50
|   |   |--- rk_ing_num <= 2776.50
|   |   |   |--- monto_castigado_otros <= 439.61
|   |   |   |   |--- value: [726.35]
|   |   |   |--- monto_castigado_otros >  439.61
|   |   |   |   |--- value: [721.04]
|   |   |--- rk_ing_num >  2776.50
|   |   |   |--- prom_saldo_pasivo_u4m <= 0.53
|   |   |   |   |--- value: [751.73]
|   |   |   |--- prom_saldo_pasivo_u4m >  0.53
|   |   |   |   |--- value: [751.76]
|   |--- edad_num >  59.50
|   |   |--- max_dias_mora_castigo <= 2649.50
|   |   |   |--- value: [795.94]
|   |   |--- max_dias_mora_castigo >  2649.50
|   |   |   |--- edad_num <= 66.50
|   |   |   |   |--- max_dias_mora_castigo <= 3971.50
|   |   |   |   |   |--- value: [755.32]
|   |   |   |   |--- max_dias_mora_castigo >  3971.50
|   |   |   |   |   |--- value: [753.80]
|   |   |   |--- edad_num >  66.50
|   |   |   |   |--- value: [780.41]
|--- segmentacion_gdp_v2 >  4.50
|   |--- max_dias_mora_castigo <= 2470.50
|   |   |--- rk_ing_num <= 2484.50
|   |   |   |--- value: [707.92]
|   |   |--- rk_ing_num >  2484.50
|   |   |   |--- value: [713.73]
|   |--- max_dias_mora_castigo >  2470.50
|   |   |--- nro_entidades_castigo <= 1.50
|   |   |   |--- edad_num <= 41.50
|   |   |   |   |--- max_dias_mora_castigo <= 3473.50
|   |   |   |   |   |--- max_dias_mora_castigo <= 2848.50
|   |   |   |   |   |   |--- value: [682.20]
|   |   |   |   |   |--- max_dias_mora_castigo >  2848.50
|   |   |   |   |   |   |--- value: [681.65]
|   |   |   |   |--- max_dias_mora_castigo >  3473.50
|   |   |   |   |   |--- edad_num <= 34.50
|   |   |   |   |   |   |--- value: [662.49]
|   |   |   |   |   |--- edad_num >  34.50
|   |   |   |   |   |   |--- value: [671.18]
|   |   |   |--- edad_num >  41.50
|   |   |   |   |--- value: [689.90]
|   |   |--- nro_entidades_castigo >  1.50
|   |   |   |--- value: [635.44]
"""
TREES[("B","CASTfar")] = r"""
|--- segmentacion_gdp_v2 <= 4.50
|   |--- rk_ing_num <= 3425.50
|   |   |--- edad_num <= 59.50
|   |   |   |--- prom_saldo_pasivo_u4m <= 14.92
|   |   |   |   |--- rk_ing_num <= 2980.50
|   |   |   |   |   |--- DEUDA_CAS <= 487.23
|   |   |   |   |   |   |--- value: [716.37]
|   |   |   |   |   |--- DEUDA_CAS >  487.23
|   |   |   |   |   |   |--- value: [713.10]
|   |   |   |   |--- rk_ing_num >  2980.50
|   |   |   |   |   |--- value: [731.83]
|   |   |   |--- prom_saldo_pasivo_u4m >  14.92
|   |   |   |   |--- value: [747.72]
|   |   |--- edad_num >  59.50
|   |   |   |--- max_dias_mora_castigo <= 4228.50
|   |   |   |   |--- value: [778.79]
|   |   |   |--- max_dias_mora_castigo >  4228.50
|   |   |   |   |--- value: [765.12]
|   |--- rk_ing_num >  3425.50
|   |   |--- rk_ing_num <= 4093.50
|   |   |   |--- value: [797.12]
|   |   |--- rk_ing_num >  4093.50
|   |   |   |--- value: [851.68]
|--- segmentacion_gdp_v2 >  4.50
|   |--- max_dias_mora_castigo <= 2479.50
|   |   |--- rk_ing_num <= 2229.50
|   |   |   |--- value: [711.55]
|   |   |--- rk_ing_num >  2229.50
|   |   |   |--- value: [711.58]
|   |--- max_dias_mora_castigo >  2479.50
|   |   |--- rk_ing_num <= 2801.50
|   |   |   |--- nro_entidades_castigo <= 1.50
|   |   |   |   |--- max_dias_mora_castigo <= 3792.50
|   |   |   |   |   |--- value: [668.17]
|   |   |   |   |--- max_dias_mora_castigo >  3792.50
|   |   |   |   |   |--- edad_num <= 39.50
|   |   |   |   |   |   |--- value: [642.27]
|   |   |   |   |   |--- edad_num >  39.50
|   |   |   |   |   |   |--- value: [658.80]
|   |   |   |--- nro_entidades_castigo >  1.50
|   |   |   |   |--- value: [623.16]
|   |   |--- rk_ing_num >  2801.50
|   |   |   |--- value: [685.09]
"""
TREES[("B","NOCAST")] = TREES[("A","NOCAST")]
TREES[("B","NOCASTfar")] = TREES[("A","NOCASTfar")]

# importancia (peso %) por (modelo, escenario): lista (label, %)  — corrida COMPLETA
ART = "saldo_activo (=MISSING)"
IMP = {
 ("A","CAST"):[("segmentación",41.1),(ART,30.6),("ahorro prom 4m",8.6),("ingreso",7.7),("edad",6.1),("máx días mora",6.0)],
 ("B","CAST"):[("segmentación",59.2),("edad",19.2),("máx días mora",11.7),("nro entidades",6.0),("ingreso",3.8)],
 ("A","CASTfar"):[("segmentación",42.5),("ingreso",20.1),(ART,12.0),("edad",9.8),("máx días mora",9.3),("ahorro prom 4m",6.3)],
 ("B","CASTfar"):[("segmentación",50.5),("ingreso",23.1),("edad",11.9),("máx días mora",10.4),("ahorro prom 4m",2.2),("nro entidades",1.9)],
 ("A","NOCAST"):[("segmentación",59.0),("meses 1er castigo",19.7),("ingreso",18.3),("edad",2.7),("deuda cast.",0.3),("meses últ. castigo",0.1)],
 ("B","NOCAST"):[("segmentación",59.0),("meses 1er castigo",19.7),("ingreso",18.3),("edad",2.7),("deuda cast.",0.3),("meses últ. castigo",0.1)],
 ("A","NOCASTfar"):[("segmentación",64.1),("ingreso",23.6),("meses 1er castigo",9.8),("ahorro prom 4m",1.1),("edad",0.8),("deuda cast.",0.5)],
 ("B","NOCASTfar"):[("segmentación",64.1),("ingreso",23.6),("meses 1er castigo",9.8),("ahorro prom 4m",1.1),("edad",0.8),("deuda cast.",0.5)],
}
SCN = [("CAST","CAST_NOIBK_REP ≥ 5 años","1,695,395"),
       ("CASTfar","CAST_NOIBK_REP ≥ 5 años · far = 1","311,143"),
       ("NOCAST","NO_CAST_NOIBK_U24M","581,875"),
       ("NOCASTfar","NO_CAST_NOIBK_U24M · far = 1","141,869")]

PRETTY = {
    "segmentacion_gdp_v2": "segmentación", "max_dias_mora_castigo": "máx días mora",
    "nro_entidades_castigo": "nro entidades", "prom_saldo_pasivo_u4m": "ahorro prom 4m",
    "DEUDA_CAS": "deuda cast.", "meses_desde_ultimo_castigo": "meses últ. castigo",
    "meses_desde_primer_castigo": "meses 1er castigo", "saldo_pasivo_actual": "saldo pasivo",
    "monto_castigado_otros": "monto cast. otros", "monto_castigado_total": "monto cast. total",
    "edad_num": "edad", "rk_ing_num": "ingreso",
}

def color(s, lo=540.0, hi=890.0):
    t = max(0.0, min(1.0, (s - lo) / (hi - lo)))
    if t < 0.5:
        r, g, b = 224, int(120 + 100 * (t * 2)), 70
    else:
        r, g, b = int(224 - 150 * ((t - 0.5) * 2)), 176, 70
    return f"rgb({r},{g},{b})"

def fmt_cond(c):
    for op, sym in ((" <= ", "≤"), (" >  ", ">")):
        if op in c:
            var, thr = c.split(op)
            thr = float(thr)
            if var == "saldo_activo_actual":      # corte en el sentinel = flag de missing
                return ("⚑ saldo_activo = MISSING" if sym == "≤" else "saldo_activo = con dato"), (var == "saldo_activo_actual")
            v = PRETTY.get(var, var)
            if var == "segmentacion_gdp_v2":
                return f"{v} {sym} {int(round(thr))}", False
            return f"{v} {sym} {thr:,.0f}", False
    return c, False

def parse(text):
    root = {"label": None, "children": []}
    stack = [(-1, root)]
    for line in text.strip("\n").split("\n"):
        if "|---" not in line:
            continue
        idx = line.find("|---")
        depth = idx // 4
        content = line[idx + 4:].strip()
        node = {"label": content, "children": []}
        while stack and stack[-1][0] >= depth:
            stack.pop()
        stack[-1][1]["children"].append(node)
        stack.append((depth, node))
    return root

def render(node):
    kids = node["children"]
    if not kids:                                  # hoja
        s = float(node["label"].split("[")[1].split("]")[0])
        return f'<li><span class="leaf" style="background:{color(s)}">{s:.0f}</span></li>'
    cond, miss = fmt_cond(node["label"])
    cls = "cond miss" if miss else "cond"
    inner = "".join(render(k) for k in kids)
    return f'<li><span class="{cls}">{cond}</span><ul>{inner}</ul></li>'

def tree_html(key, title):
    root = parse(TREES[key])
    inner = "".join(render(k) for k in root["children"])
    return f'<ul class="tree"><li><span class="root">{title}</span><ul>{inner}</ul></li></ul>'

# ----------------------------------------------------------------------------- HTML
CSS = """
:root{--navy:#16366e;--navy2:#1f4e96;--green:#43b02a;--green-d:#2e7d1c;--ink:#2b2b2b;
--muted:#6b7280;--line:#cdd8e6;--soft:#eef3f9;--red:#c0392b;--amber:#e08e0b;}
*{box-sizing:border-box;margin:0;padding:0;}html,body{height:100%;}
body{font-family:"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:var(--ink);background:#0c1830;}
.deck{position:relative;width:100vw;height:100vh;overflow:hidden;}
.slide{position:absolute;inset:0;background:#fff;padding:42px 60px 64px;display:none;flex-direction:column;overflow:hidden;}
.slide.active{display:flex;animation:fade .35s ease;}
@keyframes fade{from{opacity:0;transform:translateY(8px);}to{opacity:1;transform:none;}}
.logo{position:absolute;top:30px;right:50px;font-weight:800;font-size:32px;color:var(--navy);}
.logo .n{color:var(--green);}
h1{color:var(--navy);font-size:40px;font-weight:800;line-height:1.05;}
h2{color:var(--navy);font-size:28px;font-weight:800;margin-bottom:4px;}
.sub{color:var(--green);font-size:20px;font-weight:600;margin-top:6px;}
.kicker{color:var(--green);font-weight:700;letter-spacing:2px;font-size:13px;text-transform:uppercase;margin-bottom:10px;}
p{font-size:17px;line-height:1.5;color:#37414f;}.lead{font-size:19px;}
ul.b{margin:8px 0 0 22px;}ul.b li{font-size:16px;line-height:1.5;margin-bottom:6px;color:#37414f;}
b,strong{color:var(--navy);}.green{color:var(--green-d);}.red{color:var(--red);}.amber{color:var(--amber);}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:16px;flex:1;min-height:0;}
.grid3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:18px;margin-top:16px;}
.card{border:1px solid var(--line);border-radius:14px;padding:20px 22px;background:#fff;box-shadow:0 6px 18px rgba(20,40,80,.06);}
.card.win{border:2px solid var(--green);}.card.warn{border:2px solid #e7c27a;background:#fffdf6;}
.card h3{font-size:20px;margin-bottom:4px;color:var(--navy);}
.tag{display:inline-block;font-size:12px;font-weight:700;padding:3px 10px;border-radius:20px;color:#fff;margin-bottom:8px;}
.tag.b{background:var(--green);}.tag.a{background:var(--navy2);}
table{width:100%;border-collapse:collapse;margin-top:12px;font-size:15px;}
th,td{border:1px solid var(--line);padding:7px 9px;text-align:center;}
th{background:var(--navy);color:#fff;}td.l{text-align:left;}tr:nth-child(even) td{background:var(--soft);}
.best{background:#e7f6e2!important;color:var(--green-d);font-weight:700;}
.bar-row{display:flex;align-items:center;gap:10px;margin:6px 0;font-size:13px;}
.bar-lab{width:170px;text-align:right;color:#37414f;}
.bar-wrap{flex:1;background:#eef2f7;border-radius:6px;overflow:hidden;height:19px;}
.bar{height:100%;border-radius:6px;}.bar.b{background:linear-gradient(90deg,#43b02a,#6fce53);}
.bar.a{background:linear-gradient(90deg,#1f4e96,#3f78c9);}.bar-val{width:50px;color:var(--navy);font-weight:700;}
.callout{margin-top:12px;border-left:5px solid var(--green);background:#f2faef;padding:12px 16px;border-radius:0 10px 10px 0;}
.callout.bad{border-color:var(--red);background:#fdf1f0;}.callout p{font-size:15px;}
.verdict{display:flex;align-items:center;gap:14px;background:var(--navy);color:#fff;border-radius:14px;padding:18px 24px;margin-top:auto;}
.verdict .big{font-size:21px;font-weight:800;}.verdict .big em{color:#7fe06a;font-style:normal;}
.foot{position:absolute;left:60px;bottom:20px;font-size:12px;color:var(--muted);}
.note{font-size:13px;color:var(--muted);margin-top:6px;}
.pill{display:inline-block;background:var(--soft);border:1px solid var(--line);border-radius:20px;padding:5px 12px;font-size:13px;color:var(--navy);font-weight:600;margin:3px 4px 0 0;}
.nav{position:fixed;bottom:16px;right:24px;display:flex;gap:12px;z-index:20;}
.nav button{border:none;background:var(--navy);color:#fff;width:38px;height:38px;border-radius:50%;font-size:18px;cursor:pointer;}
.nav button:hover{background:var(--green);}
.counter{position:fixed;bottom:22px;left:50%;transform:translateX(-50%);color:#fff;background:rgba(0,0,0,.35);padding:4px 14px;border-radius:20px;font-size:13px;z-index:20;}
/* árbol estilo flujo */
.treecol{overflow:auto;max-height:64vh;border:1px solid var(--line);border-radius:12px;padding:10px 8px;background:#fcfdff;}
.treehd{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;}
.tree,.tree ul{list-style:none;margin:0;padding:0;}
.tree{font-size:11.5px;}
.tree ul{margin-left:14px;padding-left:14px;position:relative;}
.tree ul::before{content:"";position:absolute;left:0;top:-6px;bottom:14px;border-left:2px solid var(--line);}
.tree li{position:relative;padding:3px 0 3px 14px;}
.tree li::before{content:"";position:absolute;left:0;top:13px;width:12px;border-top:2px solid var(--line);}
.tree>li{padding-left:0;}.tree>li::before{display:none;}.tree>li>ul::before{display:none;}.tree>li>ul{margin-left:0;padding-left:0;}
.root{display:inline-block;background:var(--navy);color:#fff;font-weight:700;padding:5px 12px;border-radius:8px;font-size:13px;}
.cond{display:inline-block;background:#eaf1fb;border:1px solid #cfe0f5;color:var(--navy);padding:3px 9px;border-radius:7px;white-space:nowrap;}
.cond.miss{background:#fdeceb;border-color:#f3c2bd;color:var(--red);font-weight:700;}
.leaf{display:inline-block;color:#1d1d1d;font-weight:800;padding:3px 10px;border-radius:14px;min-width:42px;text-align:center;box-shadow:inset 0 0 0 1px rgba(0,0,0,.08);}
.lgnd{font-size:12px;color:var(--muted);}
.lgnd .sw{display:inline-block;width:12px;height:12px;border-radius:3px;vertical-align:-1px;margin:0 3px 0 8px;}
/* flujo metodología */
.flow{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:14px;}
.step{background:#fff;border:1px solid var(--line);border-top:4px solid var(--green);border-radius:10px;padding:11px 12px;}
.step .num{background:var(--navy);color:#fff;width:23px;height:23px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:12px;margin-bottom:5px;}
.step h4{color:var(--navy);font-size:14px;margin-bottom:3px;}
.step p{font-size:12px;line-height:1.35;}
.step code{background:var(--soft);padding:0 4px;border-radius:4px;font-size:11px;}
/* ejemplo */
.exa{display:flex;align-items:stretch;gap:12px;margin-top:14px;}
.exa .col{flex:1;}
.exbox{border:1px solid var(--line);border-radius:10px;padding:12px 14px;background:#fff;height:100%;}
.exbox.win{border:2px solid var(--green);}
.exbox.mut{opacity:.6;}
.arrow{display:flex;align-items:center;font-size:30px;color:var(--green);font-weight:800;}
.kv{font-size:13px;margin:2px 0;color:#37414f;}.kv b{color:var(--navy);}
.path{font-size:12px;color:#37414f;line-height:1.5;}
.score{display:inline-block;font-weight:800;color:#1d1d1d;padding:3px 12px;border-radius:14px;margin-top:6px;}
"""

def slide(content):
    return f'<section class="slide">{content}</section>'

LOGO = '<div class="logo">1<span class="n">N</span></div>'
SHORT = {"CAST": "CAST ≥5a", "CASTfar": "CAST far1", "NOCAST": "NO_CAST", "NOCASTfar": "NO_CAST far1"}

def imp_bars(model, scn, cls):
    rows = IMP[(model, scn)]
    mx = max(p for _, p in rows)
    out = []
    for lab, p in rows:
        w = max(3, p / mx * 100)
        art = "saldo_activo" in lab
        bcss = "background:linear-gradient(90deg,#c0392b,#e57368)" if art else ""
        vcls = "bar-val red" if art else "bar-val"
        out.append(f'<div class="bar-row"><div class="bar-lab">{lab}</div>'
                   f'<div class="bar-wrap"><div class="bar {cls}" style="width:{w:.0f}%;{bcss}"></div></div>'
                   f'<div class="{vcls}">{p}%</div></div>')
    return "".join(out)

def weights_table(model):
    data, order = {}, []
    for key, _, _ in SCN:
        for lab, p in IMP[(model, key)]:
            data.setdefault(lab, {})[key] = p
            if lab not in order:
                order.append(lab)
    order.sort(key=lambda l: -max(data[l].values()))
    colmax = {key: max(data[l].get(key, 0) for l in order) for key, _, _ in SCN}
    head = "".join(f'<th>{SHORT[k]}</th>' for k, _, _ in SCN)
    rows = ""
    for lab in order:
        art = "saldo_activo" in lab
        lc = ' class="l red"' if art else ' class="l"'
        cells = ""
        for key, _, _ in SCN:
            v = data[lab].get(key)
            best = " class=\"best\"" if (v and v == colmax[key]) else ""
            cells += f"<td{best}>{v if v else '—'}</td>"
        rows += f"<tr><td{lc}>{lab}</td>{cells}</tr>"
    return f'<table><tr><th class="l">Variable / escenario</th>{head}</tr>{rows}</table>'

slides = []

# 1 portada
slides.append(f"""<section class="slide active">{LOGO}
<div style="margin-top:6vh">
<div class="kicker">Rebancarización Castigados · Modelo de segmentación</div>
<h1>Optbinning + Árbol &nbsp;vs.&nbsp; Solo Árbol</h1>
<div class="sub">Comparación con TODAS las variables (incluye ingreso y edad)</div>
<p class="lead" style="margin-top:20px;max-width:900px">Mismo dataset (~2.7&nbsp;MM, 4 escenarios) y mismas variables.
Proxy de riesgo: <b>puntaje_mod</b> (alto = menor riesgo). Objetivo: priorizar <b>grupos de bajo riesgo</b>,
deduplicados por <b>subject_id</b>.</p>
<div style="margin-top:18px"><span class="pill">2.7 MM registros</span><span class="pill">4 escenarios</span>
<span class="pill">Restricciones monótonas de negocio</span><span class="pill">Leads sin duplicados</span></div>
</div><div class="foot">Comparativo de modelos · uso interno</div></section>""")

# 2 metodología end-to-end
slides.append(slide("""<h2>Metodología de punta a punta</h2>
<div class="sub" style="font-size:16px">Del universo de castigados hasta el lead activable, paso a paso.</div>
<div class="flow">
<div class="step"><span class="num">1</span><h4>Universo</h4><p>Clientes con <b>saldo castigado</b> en los últimos 24 meses (~2.7&nbsp;MM con score).</p></div>
<div class="step"><span class="num">2</span><h4>Escenarios</h4><p>Se parte por <code>FLG_CAST_AP</code> (CAST / NO_CAST) y por <code>far=1</code> → <b>4 universos</b> que se modelan por separado.</p></div>
<div class="step"><span class="num">3</span><h4>Variables + missing</h4><p>Predictoras de castigo, mora, deuda, ahorro y segmento. Los <b>missing → valor especial</b> <code>-99,999,999</code> (rama propia).</p></div>
<div class="step"><span class="num">4</span><h4>Dirección + optbinning</h4><p>Se <b>fija la dirección de negocio</b>; optbinning exige <b>5 bins (o 2)</b>. Si no binariza → <b>se descarta</b> la variable.</p></div>
<div class="step"><span class="num">5</span><h4>Árbol monótono</h4><p>Árbol de regresión con <code>puntaje_mod</code> y restricciones monótonas → <b>hojas = segmentos</b> con score medio.</p></div>
<div class="step"><span class="num">6</span><h4>Banda de riesgo</h4><p>Cada hoja recibe banda (<b>CORTES G1–G5</b> / quintil). Se define el <b>corte top%</b> (10–30%) = bajo riesgo.</p></div>
<div class="step"><span class="num">7</span><h4>Leads + dedup</h4><p>Se rankean los <b>mejores segmentos</b> y se asigna cada <code>subject_id</code> a <b>una sola</b> estrategia (la de menor riesgo).</p></div>
<div class="step" style="border-top-color:var(--navy)"><span class="num">8</span><h4>Activación</h4><p>Salida: <b>hoja de Estrategia</b> + <b>CSV de leads</b> únicos, listos para campaña.</p></div>
</div>
<div class="callout"><p>Proxy de riesgo: <b>puntaje_mod</b> (alto = menor riesgo). Todo el pipeline está parametrizado y corre sobre los <b>~2.7&nbsp;MM</b> registros.</p></div>
<div class="foot">Metodología end-to-end</div>"""))

# 2b variables y sentido económico
slides.append(slide("""<h2>Variables y su sentido económico</h2>
<table>
<tr><th class="l">Variable</th><th class="l">Qué mide (negocio)</th><th>Dirección esperada</th></tr>
<tr><td class="l"><b>segmentacion_gdp_v2</b></td><td class="l">Segmento de valor/patrimonio del cliente (G1 mejor … G5 peor)</td><td>mejor segmento → <span class="green">menor riesgo</span></td></tr>
<tr><td class="l"><b>max_dias_mora_castigo</b></td><td class="l">Severidad de la mora del castigo</td><td>más mora → <span class="red">más riesgo</span></td></tr>
<tr><td class="l"><b>nro_entidades_castigo</b></td><td class="l">Nº de entidades donde fue castigado</td><td>más entidades → <span class="red">más riesgo</span></td></tr>
<tr><td class="l"><b>DEUDA_CAS / monto_castigado_*</b></td><td class="l">Monto de deuda castigada</td><td>más deuda → <span class="red">más riesgo</span></td></tr>
<tr><td class="l"><b>meses_desde_últ./primer_castigo</b></td><td class="l">Antigüedad del castigo</td><td>más antiguo → <span class="green">menor riesgo</span></td></tr>
<tr><td class="l"><b>saldo_pasivo_* / ahorro_prom</b></td><td class="l">Ahorros / depósitos del cliente</td><td>más ahorro → <span class="green">menor riesgo</span></td></tr>
<tr><td class="l"><b>nro_meses_con_pasivo_u6m</b></td><td class="l">Constancia del ahorro</td><td>más constancia → <span class="green">menor riesgo</span></td></tr>
<tr><td class="l"><b>rk_ing_num</b></td><td class="l">Nivel de ingreso del cliente</td><td>más ingreso → <span class="green">menor riesgo</span></td></tr>
<tr><td class="l"><b>edad_num</b></td><td class="l">Edad del cliente</td><td>mayor edad → <span class="green">menor riesgo</span> (detectada)</td></tr>
<tr><td class="l red">saldo_activo_actual</td><td class="l">Crédito vigente (señal ambigua)</td><td class="red">descartada por optbinning (no binariza)</td></tr>
</table>
<div class="callout"><p>Toda dirección tiene lectura de negocio. El árbol <b>se obliga</b> a respetarla (monótono) → no hay relaciones contraintuitivas. En esta corrida <b>ingreso y edad sí entran</b>.</p></div>
<div class="foot">Variables · sentido económico</div>"""))

# 3 metodologias
slides.append(slide("""<h2>Las dos metodologías</h2>
<div class="sub" style="font-size:17px">Misma estructura; cambia cómo se decide la dirección y qué variables entran.</div>
<div class="grid2">
<div class="card win"><span class="tag b">MODELO B · recomendado</span><h3>Optbinning + Árbol</h3>
<ul class="b"><li>Dirección <b>fijada por negocio</b> (castigo/mora/deuda ↓ ; ahorro ↑).</li>
<li>Optbinning exige <b>5 bins (o 2 mínimo)</b>; <b>si no binariza con esa dirección, descarta la variable.</b></li>
<li>El árbol solo usa variables <b>coherentes y estables</b>.</li></ul></div>
<div class="card"><span class="tag a">MODELO A</span><h3>Solo Árbol</h3>
<ul class="b"><li>Dirección inferida de datos (Spearman); <b>entran todas</b>.</li>
<li>Sin filtro de binarización → admite variables ruidosas o artefactos.</li>
<li>Más flexible, menos disciplinado para producción.</li></ul></div></div>
<div class="callout"><p>En esta corrida <b>entran todas las variables</b> (ingreso y edad incluidas). La diferencia clave: B las admite solo si <b>binarizan con su dirección de negocio</b>; A no filtra nada.</p></div>
<div class="foot">2 · Definición</div>"""))

# 3 hallazgo
slides.append(slide("""<h2>El hallazgo decisivo: ¿de qué se alimenta cada árbol?</h2>
<div class="grid2">
<div class="card win"><span class="tag b">MODELO B</span><h3 class="green">Señales reales de riesgo</h3>
<ul class="b"><li>Drivers: <b>segmentación</b>, <b>edad</b>, <b>severidad de mora</b>, <b>multi-entidad</b>, <b>ingreso</b>.</li>
<li>Incorpora <b>ingreso y edad</b> de forma coherente (ambas crecientes). Descarta <code>saldo_activo</code> (no binariza).</li>
<li>Reglas <b>explicables y auditables</b>.</li></ul></div>
<div class="card warn"><span class="tag a">MODELO A</span><h3 class="red">Usa el “dato faltante” como predictor</h3>
<ul class="b"><li>Su 2º driver es <code>saldo_activo ≤ -50,000,000</code> = clientes <b>SIN dato</b> (⚑ MISSING) — <b>30.6% del peso</b> en CAST.</li>
<li>Varias estrategias top se definen por <b>“no tener saldo activo”</b> (artefacto, no comportamiento).</li>
<li>Dirección de <code>saldo_activo</code> inconsistente entre escenarios (0 vs +1).</li></ul></div></div>
<div class="foot">3 · Coherencia</div>"""))

# 4 importancia CAST (barras)
slides.append(slide(f"""<h2>Importancia de variables · escenario CAST (1.7&nbsp;MM)</h2>
<div class="grid2">
<div class="card"><span class="tag b">MODELO B</span><div style="margin-top:10px">{imp_bars("B","CAST","b")}</div>
<div class="callout"><p>100% variables de <b>comportamiento</b>.</p></div></div>
<div class="card"><span class="tag a">MODELO A</span><div style="margin-top:10px">{imp_bars("A","CAST","a")}</div>
<div class="callout bad"><p>El <b>2º driver es un artefacto</b> (flag de dato faltante).</p></div></div></div>
<div class="foot">Importancia · CAST</div>"""))

# 4b pesos por escenario (B y A)
slides.append(slide(f"""<h2>Pesos de variables por escenario · Modelo B (Optbinning)</h2>
<div class="sub" style="font-size:16px">Peso % en el árbol (lo no listado = 0%).</div>
{weights_table("B")}
<div class="callout"><p><b>Segmentación</b> domina en todos; en castigados aparece <b>mora/entidades</b>, en no castigados <b>meses desde castigo</b>. Coherente con negocio.</p></div>
<div class="foot">Pesos · Modelo B</div>"""))

slides.append(slide(f"""<h2>Pesos de variables por escenario · Modelo A (Solo árbol)</h2>
<div class="sub" style="font-size:16px">Peso % en el árbol (lo no listado = 0%).</div>
{weights_table("A")}
<div class="callout bad"><p><b>saldo_activo (=MISSING)</b> entra como 2º-3º driver en los escenarios CAST (33% y 19%) → artefacto que el Modelo B evita.</p></div>
<div class="foot">Pesos · Modelo A</div>"""))

# 5 volumen
slides.append(slide("""<h2>Volumen de leads de bajo riesgo (deduplicados)</h2>
<table>
<tr><th>Corte (top % puntaje)</th><th>top 10%</th><th>top 15%</th><th>top 20%</th><th>top 30%</th></tr>
<tr><td class="l"><b>Modelo A · Solo árbol</b></td><td>112,222</td><td>156,505</td><td>198,562</td><td>269,613</td></tr>
<tr><td class="l"><b>Modelo B · Optbinning</b></td><td>104,372</td><td>142,350</td><td>178,494</td><td>238,483</td></tr>
<tr><td class="l">Diferencia (A − B)</td><td>+7,850</td><td>+14,155</td><td>+20,068</td><td>+31,130</td></tr>
</table>
<div class="grid2" style="margin-top:16px">
<div class="card warn"><h3 class="amber">A genera ~10% más… pero inflado</h3>
<ul class="b"><li>El extra de A (≈ 14k en top 15%) viene de <b>~6 estrategias definidas por <code>saldo_activo = MISSING</code></b> (≈ 77k clientes en total).</li>
<li>Son leads seleccionados por <b>un dato faltante</b>, no por comportamiento → volumen <b>poco defendible</b>.</li></ul></div>
<div class="card win"><h3 class="green">B: 142k leads 100% accionables</h3>
<ul class="b"><li>B incorpora <b>ingreso y edad</b> y entrega segmentos limpios y explicables.</li>
<li>Es preferible <b>142k defendibles</b> que 156k con ~14k frágiles.</li></ul></div></div>
<div class="foot">5 · Volumen de leads</div>"""))

# 5b selección de leads + ejemplo
slides.append(slide("""<h2>¿Cómo se elige un lead? (y qué pasa con un cliente repetido)</h2>
<div class="sub" style="font-size:16px">Regla: cada cliente entra a <b>una sola</b> estrategia — la de <b>menor riesgo</b> (mayor score del segmento).</div>
<div class="exa">
  <div class="col"><div class="exbox"><h4 style="color:var(--navy);margin-bottom:6px">Cliente #00123</h4>
     <div class="kv">Castigado <b>≥ 5 años</b> &amp; <b>far = 1</b></div>
     <div class="kv">segmentación: <b>G3</b></div>
     <div class="kv">edad: <b>63</b></div>
     <div class="kv">ingreso (rk): <b>3,000</b></div>
     <div class="kv">máx días mora: <b>2,200</b></div>
     <div class="kv">puntaje_mod: <b>792</b> (top 15%)</div>
     <p class="note">Por sus flags cae en <b>2 escenarios</b> a la vez.</p></div></div>
  <div class="arrow">→</div>
  <div class="col"><div class="exbox"><h4 style="color:var(--navy)">Escenario CAST ≥5a</h4>
     <div class="path">segmentación ≤4 → edad &gt;60 → mora ≤2,650</div>
     <span class="score" style="background:rgb(150,200,90)">hoja = 796</span>
     <p class="note">Estrategia “segmentación≤4 &amp; edad&gt;60 &amp; mora≤2,650”.</p></div>
     <div class="exbox mut" style="margin-top:10px"><h4 style="color:var(--navy)">Escenario CAST · far1</h4>
     <div class="path">segmentación ≤4 → ingreso ≤3,426 → edad &gt;60 → mora ≤4,228</div>
     <span class="score" style="background:rgb(165,205,95)">hoja = 779</span></div></div>
  <div class="arrow">→</div>
  <div class="col"><div class="exbox win"><h4 class="green">Deduplicación</h4>
     <div class="kv">CAST ≥5a → <b>796</b> &nbsp; vs &nbsp; far1 → 779</div>
     <div class="kv">Gana el <b>mayor score</b> (menor riesgo): <b class="green">796</b>.</div>
     <hr style="border:none;border-top:1px solid var(--line);margin:8px 0">
     <div class="kv">✔ Queda en <b>1 estrategia</b> (CAST ≥5a).</div>
     <div class="kv">✘ Se elimina de far1.</div>
     <p class="note">Resultado: <b>1 lead único</b>, sin doble conteo.</p></div></div>
</div>
<div class="callout"><p>Así, al unir los 4 escenarios, <b>ningún cliente se cuenta dos veces</b>: el total de leads es de clientes <b>distintos</b>.</p></div>
<div class="foot">Selección de leads · ejemplo</div>"""))

# 6 calidad segmentos
slides.append(slide("""<h2>Calidad de los segmentos top</h2>
<div class="grid2">
<div class="card win"><span class="tag b">MODELO B · reglas limpias</span>
<table><tr><th class="l">Regla del segmento</th><th>score</th></tr>
<tr><td class="l">segmentación ≤2 &amp; ingreso &gt;3,444</td><td class="best">883</td></tr>
<tr><td class="l">segmentación ≤4 &amp; ingreso &gt;4,104</td><td class="best">858</td></tr>
<tr><td class="l">segmentación ≤4 &amp; edad &gt;60 &amp; mora ≤2,650</td><td>796</td></tr>
<tr><td class="l">segmentación ≤4 &amp; edad &gt;66 &amp; mora &gt;2,650</td><td>780</td></tr></table>
<p class="note">Segmento + ingreso + edad + comportamiento de pago.</p></div>
<div class="card"><span class="tag a">MODELO A · varios con artefacto</span>
<table><tr><th class="l">Regla del segmento</th><th>n_leads</th></tr>
<tr><td class="l">segmentación ≤4 &amp; <span class="red">saldo_activo MISSING</span> &amp; edad &gt;58 &amp; mora ≤2,640</td><td>27,787</td></tr>
<tr><td class="l">segmentación ≤4 &amp; <span class="red">saldo_activo MISSING</span> &amp; edad ≤58 &amp; mora ≤2,934</td><td>30,521</td></tr>
<tr><td class="l">segmentación ≤4 &amp; <span class="red">saldo_activo MISSING</span> &amp; edad &gt;58 &amp; mora &gt;2,640</td><td>20,226</td></tr>
<tr><td class="l">segmentación(4,4] &amp; <span class="red">saldo_activo MISSING</span> &amp; edad &gt;58 …</td><td>13,118</td></tr></table>
<p class="note red">≈ 6 de las 20 estrategias dependen de “no tener saldo activo” (≈ 77k leads).</p></div></div>
<div class="foot">6 · Calidad de segmentación</div>"""))

# 7-8 árboles
LEG = ('<div class="lgnd">Hojas coloreadas por puntaje_mod: '
       '<span class="sw" style="background:rgb(74,176,70)"></span>menor riesgo · '
       '<span class="sw" style="background:rgb(224,176,70)"></span>medio · '
       '<span class="sw" style="background:rgb(224,60,70)"></span>mayor riesgo</div>')

CAPS = {
 "CAST": '<p>En A el <b>1º/2º corte</b> ya es <code>saldo_activo = MISSING</code> (rojo). En B la raíz es <b>segmentación</b> y luego <b>edad / mora / entidades</b> — señales reales.</p>',
 "CASTfar": '<p>A vuelve a apoyarse en <code>saldo_activo = MISSING</code>; B usa <b>ingreso + edad + mora</b>. Ambos coinciden en el mejor segmento (ingreso &gt;4,094 → 852).</p>',
 "NOCAST": '<p><b>A y B convergen al MISMO árbol</b>: segmentación + ingreso + edad + meses desde castigo. Sin castigo/mora (no aplican) y sin artefactos.</p>',
 "NOCASTfar": '<p>También <b>idénticos</b>: segmentación + ingreso + deuda + ahorro. Máxima estabilidad y coherencia.</p>',
}
CAPCLS = {"CAST": "bad", "CASTfar": "bad", "NOCAST": "", "NOCASTfar": ""}
for k, name, nn in SCN:
    slides.append(slide(f"""<h2>Árboles · {name} &nbsp;<span style="color:var(--muted);font-size:18px">(n = {nn})</span></h2>{LEG}
<div class="grid2">
<div><div class="treehd"><span class="tag a">MODELO A · Solo árbol</span></div>
<div class="treecol">{tree_html(("A",k), name+" · Solo árbol")}</div></div>
<div><div class="treehd"><span class="tag b">MODELO B · Optbinning</span></div>
<div class="treecol">{tree_html(("B",k), name+" · Optbinning")}</div></div></div>
<div class="callout {CAPCLS[k]}">{CAPS[k]}</div>
<div class="foot">Árboles · {name}</div>"""))

# 9 veredicto
slides.append(slide("""<h2>Veredicto comparativo</h2>
<table>
<tr><th>Criterio</th><th>Modelo B · Optbinning</th><th>Modelo A · Solo árbol</th></tr>
<tr><td class="l">Coherencia de negocio</td><td class="best">Alta — 100% coherente</td><td>Media — inconsistencias</td></tr>
<tr><td class="l">Artefacto (missing como predictor)</td><td class="best">Nulo</td><td class="red">Alto (30.6% del peso en CAST)</td></tr>
<tr><td class="l">Incorpora ingreso y edad coherentes</td><td class="best">Sí</td><td>Sí (pero junto al artefacto)</td></tr>
<tr><td class="l">Explicabilidad / auditoría</td><td class="best">Alta</td><td>Media</td></tr>
<tr><td class="l">Selección automática de variables</td><td class="best">Sí</td><td>No</td></tr>
<tr><td class="l">Volumen de leads (top 15%)</td><td>142,350</td><td>156,505 <span class="note">(+10%, ~14k vía artefacto)</span></td></tr>
<tr><td class="l">Robustez para producción 3&nbsp;MM</td><td class="best">Alta</td><td>Media</td></tr></table>
<div class="verdict"><div class="big">Se recomienda implementar el <em>Modelo B (Optbinning + Árbol)</em>: 142k leads limpios; el +10% de A es <em>volumen frágil</em> apoyado en el dato faltante.</div></div>
<div class="foot">9 · Veredicto</div>"""))

# 10 proximos pasos
slides.append(slide("""<h2>Conclusiones y resultados</h2>
<div class="grid2">
<div class="card win"><span class="tag b">Lo que confirma B</span>
<ul class="b">
<li><b>Incorpora ingreso y edad de forma coherente</b> (ambas crecientes) — valida la recomendación previa de sumar ingreso.</li>
<li><b>Cero artefactos:</b> descarta <code>saldo_activo</code> y, en no castigados, las variables de castigo que no aplican.</li>
<li>Segmentos <b>explicables</b>: segmentación + ingreso + edad + mora + ahorro.</li>
<li><b>142,350 leads</b> (top 15%) listos y defendibles.</li></ul></div>
<div class="card warn"><span class="tag a">Lo que arrastra A</span>
<ul class="b">
<li><code>saldo_activo = MISSING</code> es el <b>2º driver (30.6%)</b> en CAST y define <b>~6 estrategias</b> (≈ 77k leads).</li>
<li>Su ventaja de volumen (<b>+14k, +10%</b>) es casi toda <b>artefacto</b>.</li>
<li><b>Sobre-segmenta por edad</b> y deja la dirección de <code>saldo_activo</code> inconsistente entre escenarios.</li></ul></div></div>
<div class="grid2" style="margin-top:6px">
<div class="card"><h3 class="green">Hallazgo robusto</h3><p>En <b>las 3 corridas</b> (con y sin ingreso/edad), A siempre se apoya en el dato faltante y B nunca. Es un patrón <b>estructural</b>, no de azar.</p></div>
<div class="card"><h3>Convergencia sana</h3><p>En <b>no castigados</b> A y B dan el <b>mismo árbol</b> → cuando no hay artefacto disponible, ambos coinciden. La diferencia la hace el artefacto.</p></div></div>
<div class="foot">Conclusiones</div>"""))

slides.append(f"""<section class="slide">{LOGO}<h2>Recomendación e implementación</h2>
<div class="grid3">
<div class="card win"><h3 class="green">1 · Modelo base</h3><p>Adoptar <b>Optbinning + Árbol</b> con direcciones de negocio y descarte automático de variables.</p></div>
<div class="card"><h3>2 · Variables</h3><p>Mantener <b>ingreso y edad</b> (ya entran coherentes) y la <b>exclusión de saldo_activo</b> para no reintroducir el artefacto.</p></div>
<div class="card"><h3>3 · Activación</h3><p>Usar la <b>hoja de Estrategia</b> (top segmentos, sin duplicados) y el CSV de leads. Calibrar el corte 10–30% según campaña.</p></div></div>
<div class="callout" style="margin-top:20px"><p><b>Quick win:</b> el corte <b>top 15%</b> de B entrega <b>~142 mil leads de riesgo controlado</b>, 100% explicables, listos para desplegar.</p></div>
<div class="verdict" style="background:var(--green-d)"><div class="big">Misma cosecha de leads, base más limpia → menos pérdida y mejor tasa de aprobación.</div></div>
<div class="foot">10 · Próximos pasos</div></section>""")

HTML = f"""<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Comparación de Modelos — Rebancarización Castigados</title><style>{CSS}</style></head>
<body><div class="deck" id="deck">{''.join(slides)}</div>
<div class="counter" id="counter">1 / {len(slides)}</div>
<div class="nav"><button onclick="go(-1)">‹</button><button onclick="go(1)">›</button></div>
<script>
const slides=[...document.querySelectorAll('.slide')];let i=0;
function show(n){{slides[i].classList.remove('active');i=(n+slides.length)%slides.length;
slides[i].classList.add('active');document.getElementById('counter').textContent=(i+1)+' / '+slides.length;}}
function go(d){{show(i+d);}}
document.addEventListener('keydown',e=>{{if(e.key==='ArrowRight'||e.key===' ')go(1);if(e.key==='ArrowLeft')go(-1);}});
</script></body></html>"""

with open("comparacion_modelos.html", "w", encoding="utf-8") as f:
    f.write(HTML)
print(f"OK -> comparacion_modelos.html ({len(slides)} slides, {len(HTML)} chars)")
