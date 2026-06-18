# -*- coding: utf-8 -*-
"""Presentación: TODOS los escenarios en un solo HTML con selector."""
from viz_lib import build_multi, parse_tabla
from build_arbol_html import leaves as leaves_global   # escenario global (ya parseado)
from build_escenario_24m import RAW as RAW_24M
from datos_60m import RAW_60M

escenarios = [
    ("Global (toda la base)", leaves_global),
    ("≤ 24 meses", parse_tabla(RAW_24M)),
    ("≥ 60 meses", parse_tabla(RAW_60M)),
]

build_multi(escenarios, "presentacion_segmentacion.html", titulo="Segmentación de riesgo — Escenarios")
