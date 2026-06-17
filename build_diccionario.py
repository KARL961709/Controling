import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = openpyxl.Workbook()

# ----------------------------------------------------------------------------
# Hoja 1: Diccionario de variables AGREGADAS
# ----------------------------------------------------------------------------
ws = wb.active
ws.title = "Diccionario_Variables"

headers = ["#", "Variable", "Descripcion", "Tipo", "Base / Tabla origen",
           "Esquema", "Llave de join", "Periodo / Filtro", "Ventana",
           "Desfase (vs codmes_pea=202606)"]

# (variable, descripcion, tipo, tabla, esquema, llave, periodo, ventana, desfase)
rows = [
    # ---- rm_cliente ----
    ("sexo", "Sexo del cliente", "varchar", "t_rm_cliente", "e_perm_aws",
     "tipdoc + key_value", "fecproceso='20260616'", "Foto", "0 (misma foto PEA)"),
    ("estado_civil", "Estado civil del cliente", "varchar", "t_rm_cliente", "e_perm_aws",
     "tipdoc + key_value", "fecproceso='20260616'", "Foto", "0 (misma foto PEA)"),
    # ---- profesiones ----
    ("nivel_profesional", "Nivel profesional del cliente", "varchar", "t_profesiones_hist", "e_perm_aws",
     "tipdoc + key_value", "codmes='202603'", "Foto", "-3 meses"),
    ("tipinstitucion", "Tipo de institucion (profesion)", "varchar", "t_profesiones_hist", "e_perm_aws",
     "tipdoc + key_value", "codmes='202603'", "Foto", "-3 meses"),
    # ---- t_360 saldos TXS ----
    ("saldo_fdp_tot_txs_um", "Saldo fin de periodo transacciones - ultimo mes", "decimal", "t_360_cliente", "e_perm_aws",
     "cod_tipo_documento + nro_documento", "frecuencia=1; cod_mes=202606", "UM", "0 (anclaje 202606)"),
    ("saldo_fdp_tot_txs_u3m", "Saldo fin de periodo transacciones - promedio U3M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202604", "U3M (prom)", "0 a -2 meses"),
    ("saldo_fdp_tot_txs_u6m", "Saldo fin de periodo transacciones - promedio U6M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202601", "U6M (prom)", "0 a -5 meses"),
    ("saldo_prom_tot_txs_um", "Saldo promedio transaccional - ultimo mes", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes=202606", "UM", "0 (anclaje 202606)"),
    ("saldo_prom_tot_txs_u3m", "Saldo promedio transaccional - promedio U3M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202604", "U3M (prom)", "0 a -2 meses"),
    ("saldo_prom_tot_txs_u6m", "Saldo promedio transaccional - promedio U6M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202601", "U6M (prom)", "0 a -5 meses"),
    # ---- t_360 saldos PLANILLA ----
    ("saldo_fdp_tot_planilla_um", "Saldo fin de periodo planilla - ultimo mes", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes=202606", "UM", "0 (anclaje 202606)"),
    ("saldo_fdp_tot_planilla_u3m", "Saldo fin de periodo planilla - promedio U3M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202604", "U3M (prom)", "0 a -2 meses"),
    ("saldo_fdp_tot_planilla_u6m", "Saldo fin de periodo planilla - promedio U6M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202601", "U6M (prom)", "0 a -5 meses"),
    ("saldo_prom_tot_planilla_um", "Saldo promedio planilla - ultimo mes", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes=202606", "UM", "0 (anclaje 202606)"),
    ("saldo_prom_tot_planilla_u3m", "Saldo promedio planilla - promedio U3M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202604", "U3M (prom)", "0 a -2 meses"),
    ("saldo_prom_tot_planilla_u6m", "Saldo promedio planilla - promedio U6M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202601", "U6M (prom)", "0 a -5 meses"),
    # ---- t_360 saldos TC ----
    ("saldo_fdp_tot_tc_um", "Saldo fin de periodo tarjeta credito - ultimo mes", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes=202606", "UM", "0 (anclaje 202606)"),
    ("saldo_fdp_tot_tc_u3m", "Saldo fin de periodo tarjeta credito - promedio U3M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202604", "U3M (prom)", "0 a -2 meses"),
    ("saldo_fdp_tot_tc_u6m", "Saldo fin de periodo tarjeta credito - promedio U6M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202601", "U6M (prom)", "0 a -5 meses"),
    ("saldo_prom_tot_tc_um", "Saldo promedio tarjeta credito - ultimo mes", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes=202606", "UM", "0 (anclaje 202606)"),
    ("saldo_prom_tot_tc_u3m", "Saldo promedio tarjeta credito - promedio U3M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202604", "U3M (prom)", "0 a -2 meses"),
    ("saldo_prom_tot_tc_u6m", "Saldo promedio tarjeta credito - promedio U6M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202601", "U6M (prom)", "0 a -5 meses"),
    # ---- t_360 saldos PASIVO ----
    ("saldo_prom_tot_pasivo_um", "Saldo promedio pasivo - ultimo mes", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes=202606", "UM", "0 (anclaje 202606)"),
    ("saldo_prom_tot_pasivo_u3m", "Saldo promedio pasivo - promedio U3M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202604", "U3M (prom)", "0 a -2 meses"),
    ("saldo_prom_tot_pasivo_u6m", "Saldo promedio pasivo - promedio U6M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202601", "U6M (prom)", "0 a -5 meses"),
    ("saldo_prom_tot_pasivo_max_u6m", "Saldo promedio pasivo - maximo U6M", "decimal", "t_360_cliente", "e_perm_aws",
     "doc", "cod_mes 202606-202601", "U6M (max)", "0 a -5 meses"),
]

# flags t_360 (UM + U6M)
flags = [
    ("flg_colaborador", "Indicador si es colaborador IBK"),
    ("flg_cliente_cts", "Flag cliente CTS"),
    ("flg_cliente_inversion", "Flag cliente Inversion"),
    ("flg_cliente_millonaria", "Flag cliente Millonaria"),
    ("flg_cliente_alcancia", "Flag cliente Alcancia"),
    ("flg_cliente_planilla", "Flag cliente Planilla"),
    ("flg_cliente_planilla_act_sal", "Flag cliente Planilla Actualiza Saldo"),
    ("flg_cliente_planilla_abon", "Flag cliente Planilla Abono"),
    ("flg_cliente_planilla_depo", "Flag cliente Planilla Deposito"),
    ("flg_cliente_plazo_fijo", "Flag cliente Plazo Fijo"),
]
for fname, fdesc in flags:
    rows.append((f"{fname}_um", f"{fdesc} - valor ultimo mes (0/1/null)", "int/varchar",
                 "t_360_cliente", "e_perm_aws", "doc", "cod_mes=202606", "UM", "0 (anclaje 202606)"))
    rows.append((f"{fname}_u6m", f"{fdesc} - tuvo (=1) en algun mes U6M", "int (0/1)",
                 "t_360_cliente", "e_perm_aws", "doc", "cod_mes 202606-202601", "U6M", "0 a -5 meses"))

# derivadas / ratios
rows += [
    ("saldo_pasivo_componentes_u3m", "Suma prom U3M de planilla+txs+tc", "decimal (derivada)", "t_360_cliente", "e_perm_aws",
     "doc", "calculo", "U3M", "0 a -2 meses"),
    ("ratio_tc_pasivo_u3m", "Saldo prom tc U3M / saldo prom pasivo U3M", "decimal (derivada)", "t_360_cliente", "e_perm_aws",
     "doc", "calculo", "U3M", "0 a -2 meses"),
    ("ratio_planilla_pasivo_u3m", "Saldo prom planilla U3M / saldo prom pasivo U3M", "decimal (derivada)", "t_360_cliente", "e_perm_aws",
     "doc", "calculo", "U3M", "0 a -2 meses"),
    ("ratio_txs_pasivo_u3m", "Saldo prom txs U3M / saldo prom pasivo U3M", "decimal (derivada)", "t_360_cliente", "e_perm_aws",
     "doc", "calculo", "U3M", "0 a -2 meses"),
    ("var_pasivo_um_vs_u6m", "(pasivo UM - prom pasivo U6M)/prom pasivo U6M", "decimal (derivada)", "t_360_cliente", "e_perm_aws",
     "doc", "calculo", "UM vs U6M", "0 a -5 meses"),
    ("flg_tiene_pasivo_u6m", "1 si prom pasivo U6M > 0", "int (0/1) (derivada)", "t_360_cliente", "e_perm_aws",
     "doc", "calculo", "U6M", "0 a -5 meses"),
    ("motivo_principalidad", "Motivo de principalidad del cliente", "varchar", "t_nds_principalidad", "e_perm_aws",
     "codunicocli (puente t_360_cliente)", "fch_periodo=2026-06-30", "Foto", "0 (anclaje 202606)"),
    ("nro_entidades_castigo_vida", "Nro entidades con castigo (U24M)", "bigint", "t_fact_report_rcc_rsk", "e_perm_aws",
     "tip_doc + key_value", "corte codmes<=202603; ventana>=202403", "U24M", "corte -3 / ventana 24M"),
    ("tipo_entidad_castigo_vida", "BIG FOUR / OTROS / SIN CASTIGO", "varchar", "t_fact_report_rcc_rsk", "e_perm_aws",
     "tip_doc + key_value", "corte codmes<=202603; ventana>=202403", "U24M", "corte -3 / ventana 24M"),
]

# estilos
hdr_fill = PatternFill("solid", fgColor="1F4E78")
hdr_font = Font(color="FFFFFF", bold=True, size=11)
center = Alignment(horizontal="center", vertical="center", wrap_text=True)
left = Alignment(horizontal="left", vertical="center", wrap_text=True)
thin = Side(style="thin", color="BFBFBF")
border = Border(left=thin, right=thin, top=thin, bottom=thin)

for c, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=c, value=h)
    cell.fill = hdr_fill; cell.font = hdr_font; cell.alignment = center; cell.border = border

for i, r in enumerate(rows, start=2):
    ws.cell(row=i, column=1, value=i-1)
    for c, val in enumerate(r, start=2):
        ws.cell(row=i, column=c, value=val)
    for c in range(1, len(headers)+1):
        cell = ws.cell(row=i, column=c)
        cell.border = border
        cell.alignment = center if c == 1 else left
        if c == 2:
            cell.font = Font(name="Consolas", size=10)
    if i % 2 == 0:
        for c in range(1, len(headers)+1):
            if ws.cell(row=i, column=c).fill.fgColor.rgb in (None, "00000000"):
                ws.cell(row=i, column=c).fill = PatternFill("solid", fgColor="F2F6FB")

widths = [5, 34, 46, 18, 22, 12, 30, 30, 22, 28]
for c, w in enumerate(widths, 1):
    ws.column_dimensions[get_column_letter(c)].width = w
ws.freeze_panes = "A2"
ws.row_dimensions[1].height = 30

# ----------------------------------------------------------------------------
# Hoja 2: Fuentes / parametros (bases y desfases)
# ----------------------------------------------------------------------------
ws2 = wb.create_sheet("Fuentes_y_Desfases")
h2 = ["Bloque / CTE", "Tabla origen", "Esquema", "Variables que aporta",
      "Periodo / Filtro", "Desfase vs 202606", "Parametro"]
data2 = [
    ("PEA (base)", "ds_rtd_rskvol_indicadores_pea", "e_perm_aws", "Poblacion PEA, edad, renta, sit_lab_ap",
     "p_fecinformacion=20260616", "0", "@FECHA_PEA"),
    ("castigos RCC (varias CTE)", "t_fact_report_rcc_rsk / t_cob_rcc_consulta_hist", "e_perm_aws",
     "FLG_CAST_*, RNG_*, DEUDA_CAS", "codmes/p_periodo=202604; ancla 20260401", "0 / U24M", "@CODMES_RCC/@ANCLA_RCC"),
    ("pivot caidas", "ds_rtd_rskvol_caidas_adquisicion + maestras motivo", "e_perm_aws",
     "flg_* de caidas (estado)", "FECHA_PROCESAMIENTO=20260616; p_fecinformacion=20260615", "0", "@FECHA_PEA"),
    ("inca_rf", "t_inca_rf + t_mst_inter_ibk_base_cliente", "e_perm_aws",
     "flg_far_mto_trx_presencial_12m_c216", "cod_mes_join=202604", "-2", "@CODMES_INCA"),
    ("ms (maestro score)", "t_rsk_maestro_score", "e_perm_aws",
     "GRUPO_SCORE, nom_modelo, puntaje_mod, sit_laboral_mod, fuente_ingreso_mod, segmentacion_gdp",
     "periodo=202605", "-1", "@CODMES_MODELO"),
    ("ms_var", "t_rsk_maestro_score", "e_perm_aws", "puntaje_var, nom_modelo_var",
     "periodo=202605", "-1", "@CODMES_MODELO"),
    ("ms_3m", "t_rsk_maestro_score", "e_perm_aws", "p/n mod y var por mes + min_*_3m",
     "periodo 202604,202603,202602", "-2 a -4", "@MESES_3M"),
    ("origenapp", "scr_origenapp1_rsk", "e_perm_aws", "trf_tip_segmentacion_gdp",
     "cod_mes=codmes_pea (202606)", "0", "codmes_pea"),
    ("segmentacion_gdp", "t_rsk_segmentacion_gdp", "e_perm_aws", "segmentacion_gdp_v2",
     "codmes=202603 (trimestral)", "-3", "@CODMES_SEG_GDP"),
    ("t360 (NUEVO)", "t_360_cliente", "e_perm_aws", "saldos txs/planilla/tc/pasivo + flags + ratios",
     "frecuencia=1; cod_mes 202606-202601", "0 a -5", "@U6M"),
    ("principalidad (NUEVO)", "t_nds_principalidad", "e_perm_aws", "motivo_principalidad",
     "fch_periodo=2026-06-30", "0", "@FCH_PRINCIPALIDAD"),
    ("variables_rcc (NUEVO)", "t_fact_report_rcc_rsk", "e_perm_aws", "nro/tipo entidad castigo vida",
     "corte codmes<=202603; ventana>=202403", "corte -3 / U24M", "@VENTANA_24M"),
    ("rm_cliente (NUEVO)", "t_rm_cliente", "e_perm_aws", "sexo, estado_civil",
     "fecproceso=20260616", "0", "@FECHA_PEA"),
    ("profesiones (NUEVO)", "t_profesiones_hist", "e_perm_aws", "nivel_profesional, tipinstitucion",
     "codmes=202603", "-3", "@CODMES_PROF"),
]
for c, h in enumerate(h2, 1):
    cell = ws2.cell(row=1, column=c, value=h)
    cell.fill = hdr_fill; cell.font = hdr_font; cell.alignment = center; cell.border = border
for i, r in enumerate(data2, start=2):
    for c, val in enumerate(r, start=1):
        cell = ws2.cell(row=i, column=c, value=val)
        cell.border = border; cell.alignment = left
    if i % 2 == 0:
        for c in range(1, len(h2)+1):
            ws2.cell(row=i, column=c).fill = PatternFill("solid", fgColor="F2F6FB")
widths2 = [26, 40, 12, 46, 38, 20, 22]
for c, w in enumerate(widths2, 1):
    ws2.column_dimensions[get_column_letter(c)].width = w
ws2.freeze_panes = "A2"
ws2.row_dimensions[1].height = 30

# ----------------------------------------------------------------------------
# Hoja 3: Notas
# ----------------------------------------------------------------------------
ws3 = wb.create_sheet("Notas")
notas = [
    ["Notas del diccionario", ""],
    ["", ""],
    ["Anclaje (codmes_pea)", "202606 (PEA p_fecinformacion=20260616)"],
    ["Ventana UM", "ultimo mes = 202606"],
    ["Ventana U3M", "202606, 202605, 202604 (promedio)"],
    ["Ventana U6M", "202606, 202605, 202604, 202603, 202602, 202601"],
    ["Desfase", "Meses hacia atras respecto a codmes_pea (negativo = atras)"],
    ["Llave 'doc'", "cod_tipo_documento + nro_documento (= cod_tip_doc + key_value en base)"],
    ["Flags t_360", "Dominio 0/1/null. _um = valor ultimo mes; _u6m = 1 si =1 en algun mes U6M"],
    ["Flag t_360 deteccion", "Se usa cast(flg as varchar)='1' para soportar int o varchar"],
    ["No incluido", "flg_activo / saldo activo (removido a pedido)"],
    ["Pendiente confirmar", "Tipo de fecproceso en t_rm_cliente (string vs date)"],
    ["Pendiente confirmar", "Nombre exacto de columnas doc en t_rm_cliente / t_profesiones_hist (tipdoc/key_value)"],
]
for i, (a, b) in enumerate(notas, start=1):
    ca = ws3.cell(row=i, column=1, value=a)
    cb = ws3.cell(row=i, column=2, value=b)
    if i == 1:
        ca.font = Font(bold=True, size=14, color="1F4E78")
    else:
        ca.font = Font(bold=True)
    cb.alignment = left
ws3.column_dimensions["A"].width = 26
ws3.column_dimensions["B"].width = 70

out = "/home/user/Controling/Diccionario_PEA202606_REP_V2_mod.xlsx"
wb.save(out)
print("OK ->", out)
print("Filas diccionario:", len(rows))
