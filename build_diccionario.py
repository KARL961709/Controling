# -*- coding: utf-8 -*-
"""Diccionario de variables FINALES del SELECT (sin flags de caidas)."""
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

PEA = "202606"
R = []  # filas
def add(var, desc, tipo, origen, esquema, llave, periodo, ventana, desfase, part):
    R.append([var, desc, tipo, origen, esquema, llave, periodo, ventana, desfase, part])

# ---------------- BASE_PEA ----------------
add("subject_id","Identificador del cliente (tipo_doc-num_doc). Clave primaria de la base","texto",
    "ds_rtd_rskvol_indicadores_pea (PEA)","e_perm_aws","-","p_fecinformacion=20260616","foto","0","Clave; se parte en cod_tip_doc y key_value")
add("cod_tip_doc","Código de tipo de documento","texto","derivado de subject_id","-","-","-","-","0","split_part(subject_id,'-',1)")
add("key_value","Número de documento (clave de joins)","texto","derivado de subject_id","-","-","-","-","0","substring(subject_id,3)")
add("p_fecinformacion","Fecha de información de la PEA (yyyymmdd)","texto","PEA","e_perm_aws","-","=20260616","foto","0","Define el ancla temporal")
add("codmes_pea","Periodo de la PEA (yyyymm) = ancla del query","texto","derivado","-","-","=202606","foto","0","substring(p_fecinformacion,1,6)")
add("DEUDA_CAS","Saldo castigado asignado al cliente","numérico","t_fact_report_rcc_rsk (CTEs c/d/e/f)","e_perm_aws","subject_id","codmes=202604 / ventana 24m","act / U24M","-2 / 24m",
    "Cascada: 0 si CAST_IBK_REP (c) o NO_CAST_IBK_U24M (d); s_cast_noibk si CAST_NOIBK actual (e); sld_u24 si NO-IBK U24M (f); si no, 0")
add("sit_lab_ap","Situación laboral (PEA)","texto","PEA","e_perm_aws","-","20260616","foto","0","-")
add("RNG_ANT_UREPORT","Rango antigüedad del último reporte de castigo no-IBK U24M (0-6M..19-24M)","texto",
    "df_castigo_u24M_noibk (t_fact_report_rcc_rsk)","e_perm_aws","subject_id","cta 8113/8123/8133; condicion>30; ventana 24m ancla 20260401","U24M","hasta -1m",
    "Solo aplica a la rama f (NO_CAST_NOIBK_U24M); ant_ureporte = meses vs 202604")
add("RNG_EDAD","Rango de edad","texto","PEA (edad)","e_perm_aws","-","20260616","foto","0","-")
add("edad_num","Edad numérica (entra al árbol)","entero","PEA (edad)","e_perm_aws","-","20260616","foto","0","Valor crudo de 'edad'")
add("rk_ing","Rango de renta/ingreso","texto","PEA (renta)","e_perm_aws","-","20260616","foto","0","-")
add("rk_ing_num","Renta/ingreso numérica (entra al árbol)","numérico","PEA (renta)","e_perm_aws","-","20260616","foto","0","Valor crudo de 'renta'")
add("ANTI_CAST","Antigüedad del castigo no-IBK (<5años / [5años+)","texto","CTE e (dm_cast_noibk)","e_perm_aws","subject_id","codmes=202604","act","-2",
    "dm_cast_noibk = max por entidad de min(condicion); /360 ≈ años")
add("FLG_CAST_REP","Castigo reportado en cob_rcc (CASTIGOS_REP/NO_REP_CASTIGO)","texto","T_cob_rcc_consulta_hist (df_rcc_castigos_act b)","e_perm_aws","subject_id",
    "p_periodo=202604; CTA 8113/8123/8133 u 811925/812925/813925","act","-2","Marca presencia de castigo reportado")
add("FLG_CAST_TOT","Tiene castigo en RCC en U24M (CASTIGOS_TOT/NO_CASTIGO)","texto","t_fact_report_rcc_rsk (df_rcc_castigos_tot b1)","e_perm_aws","tip_doc+key_value",
    "cta 8113/8123/8133; condicion>30; ventana 24m ancla 20260401","U24M","0 / 24m","-")
add("FLG_CAST_AP","Segmento principal de castigo (usado para los escenarios)","texto","CTEs c/d/e/f","e_perm_aws","subject_id","varios","act / U24M","-2 / 24m",
    "Jerarquía: CAST_IBK_REP(c) > NO_CAST_IBK_U24M(d) > CAST_NOIBK_REP<5/>=5años(e, por dm/360) > NO_CAST_NOIBK_U24M(f) > NO_REP_CASTIGO")
add("RNG_ANT_CAST","Rango de antigüedad del castigo (buckets de días/360)","texto","CTEs e/f (dm_cast_noibk / dm_nocast_noibku24m)","e_perm_aws","subject_id","-","act / U24M","-2 / 24m",
    "Rama e usa dm_cast_noibk; rama f usa dm_nocast_noibku24m")
add("RNG_DEUDA_CAST","Rango de saldo castigado (buckets en soles)","texto","CTEs e/f (s_cast_noibk / sld_u24)","e_perm_aws","subject_id","-","act / U24M","-2 / 24m","-")
add("FLG_F","Marca de fallecido ('Fallecido' o null)","texto","reniec_inhabilitados_csv","disc_model_owner","'1-'||key_value","estado='F'","foto","0",
    "Join solo para DNI (tip_doc='1')")

# ---------------- MS (maestro_score, modelo) ----------------
MS = ("t_rsk_maestro_score","e_perm_aws","key_value+tipdoc",
      "periodo=202605; nom_modelo in (Score Orig. TC Bank/No Bank 2024)","foto","-1")
add("GRUPO_SCORE","Grupo/nivel del score del modelo (concepto_nivel)","texto",*MS,"Banda del score del modelo aplicado")
add("segmentacion_gdp","Segmentación GDP (según maestro_score)","texto",*MS,"-")
add("nom_modelo","Nombre del modelo aplicado","texto",*MS,"Bank o No Bank 2024")
add("sit_laboral_mod","Situación laboral según el modelo","texto",*MS,"-")
add("fuente_ingreso_mod","Fuente de ingreso según el modelo","texto",*MS,"-")
add("puntaje_mod","Puntaje/score del modelo — OBJETIVO del árbol (proxy de riesgo)","numérico",*MS,"Mayor score = menor riesgo")

# ---------------- INCA ----------------
add("flg_far_mto_trx_presencial_12m_c216","Feature INCA: indicador FAR de monto/trx presencial 12m (c216)","numérico",
    "t_inca_rf (join t_mst_inter_ibk_base_cliente)","e_perm_aws","key_value+cod_tip_doc; cod_mes_join=202604","process_date=202604","12m","-2",
    "party_id→key_value vía base_cliente; agregado con MAX")

# ---------------- ORIGENAPP ----------------
add("trf_tip_segmentacion_gdp","Tipo de segmentación GDP (origen app)","texto","scr_origenapp1_rsk","e_perm_aws","cod_mes(=codmes_pea)+cod_tip_doc+key_value","cod_mes=202606","foto","0","Join relativo a codmes_pea")

# ---------------- SEGMENTACION GDP v2 ----------------
add("segmentacion_gdp_v2","Segmentación GDP (tabla trimestral)","texto","t_rsk_segmentacion_gdp","e_perm_aws","codmes+key_value+tipdoc","codmes=202603","trimestral","-3","Última foto trimestral disponible")

# ---------------- MS_VAR ----------------
MV = ("t_rsk_maestro_score","e_perm_aws","key_value+tipdoc","periodo=202605 (todos los modelos)","foto","-1")
add("puntaje_var","Puntaje máximo entre TODOS los modelos del cliente","numérico",*MV,"MAX(puntaje); sin filtrar nom_modelo")
add("nom_modelo_var","Modelo correspondiente al puntaje_var","texto",*MV,"max_by(nom_modelo, puntaje)")

# ---------------- MS_3M ----------------
def m3(var, desc, mes, part):
    des = {"202604":"-2","202603":"-3","202602":"-4"}[mes]
    add(var, desc, "numérico/texto","t_rsk_maestro_score (ms_3m)","e_perm_aws","key_value+tipdoc",
        f"periodo={mes}","mensual",des, part)
m3("pmod_202604","Máx puntaje del mes (solo Bank/No Bank) — 202604","202604","MAX por mes")
m3("pmod_202603","Máx puntaje del mes (solo Bank/No Bank) — 202603","202603","MAX por mes")
m3("pmod_202602","Máx puntaje del mes (solo Bank/No Bank) — 202602","202602","MAX por mes")
m3("nmod_202604","Modelo del máx (Bank/No Bank) — 202604","202604","max_by")
m3("nmod_202603","Modelo del máx (Bank/No Bank) — 202603","202603","max_by")
m3("nmod_202602","Modelo del máx (Bank/No Bank) — 202602","202602","max_by")
m3("pvar_202604","Máx puntaje del mes (todos los modelos) — 202604","202604","MAX por mes")
m3("pvar_202603","Máx puntaje del mes (todos los modelos) — 202603","202603","MAX por mes")
m3("pvar_202602","Máx puntaje del mes (todos los modelos) — 202602","202602","MAX por mes")
m3("nvar_202604","Modelo del máx (todos) — 202604","202604","max_by")
m3("nvar_202603","Modelo del máx (todos) — 202603","202603","max_by")
m3("nvar_202602","Modelo del máx (todos) — 202602","202602","max_by")
add("min_puntaje_mod_3m","Mín entre 3 meses del máx mensual (solo Bank/No Bank)","numérico","t_rsk_maestro_score (ms_3m)","e_perm_aws","key_value+tipdoc","periodo in 202602-202604","3m","-4 a -2","Por mes MAX, entre meses MIN (resultado _mod)")
add("nom_mod_3m","Modelo del min_puntaje_mod_3m","texto","ms_3m","e_perm_aws","key_value+tipdoc","202602-202604","3m","-4 a -2","min_by(nmod,pmod)")
add("min_puntaje_var_3m","Mín entre 3 meses del máx mensual (todos los modelos)","numérico","ms_3m","e_perm_aws","key_value+tipdoc","202602-202604","3m","-4 a -2","Resultado _var")
add("nom_mod_var_3m","Modelo del min_puntaje_var_3m","texto","ms_3m","e_perm_aws","key_value+tipdoc","202602-202604","3m","-4 a -2","min_by(nvar,pvar)")

# ---------------- RCC numéricas castigo ----------------
RC = ("t_fact_report_rcc_rsk (rcc_castigo_num)","e_perm_aws","key_value+tip_doc")
add("monto_castigado_total","Suma de saldo castigado (mes 202604)","numérico",*RC,"cta 8113/8123/8133; codmes=202604","act","-2","SUM(saldo) del mes; tabla filtra ventana 24m ancla 20260401")
add("monto_castigado_ibk","Saldo castigado en IBK (00002)","numérico",*RC,"codmes=202604; entidad=00002","act","-2","-")
add("monto_castigado_otros","Saldo castigado en entidades no-IBK","numérico",*RC,"codmes=202604; entidad<>00002","act","-2","-")
add("nro_entidades_castigo","Nro de entidades distintas con castigo (202604)","entero",*RC,"codmes=202604","act","-2","COUNT(DISTINCT entidad)")
add("max_dias_mora_castigo","Máximo de condición (días de mora) del castigo (202604)","entero",*RC,"codmes=202604","act","-2","MAX(condicion)")
add("meses_desde_ultimo_castigo","Meses desde el último mes con castigo (vs 202604)","entero",*RC,"ventana 24m ancla 20260401","U24M","-2","date_diff(MAX(codmes),202604)")
add("meses_desde_primer_castigo","Meses desde el primer mes con castigo (vs 202604)","entero",*RC,"ventana 24m ancla 20260401","U24M","-2","date_diff(MIN(codmes),202604)")

# ---------------- PASIVO (pasivo_num) ----------------
PN = ("t_360_cliente (pasivo_num)","e_perm_aws","cod_tipo_documento+nro_documento","frecuencia=1; cod_mes 202601-202606")
add("saldo_pasivo_actual","Saldo fdp total pasivo (último mes 202606)","numérico",*PN,"UM","0","MAX del mes 202606")
add("saldo_prom_pasivo","Saldo promedio total pasivo (último mes 202606)","numérico",*PN,"UM","0","MAX del mes 202606")
add("saldo_activo_actual","Saldo fdp total activo (último mes 202606)","numérico",*PN,"UM","0","MAX del mes 202606")
add("prom_saldo_pasivo_u4m","Promedio del saldo fdp pasivo U4M (202603-202606)","numérico",*PN,"U4M","0","AVG 4 meses")
add("max_saldo_pasivo_u6m","Máximo saldo fdp pasivo en U6M","numérico",*PN,"U6M","0","MAX 6 meses")
add("nro_meses_con_pasivo_u6m","Nro de meses con pasivo>0 en U6M","entero",*PN,"U6M","0","COUNT distinct meses con saldo>0")

# ---------------- t_360 saldos ----------------
SAL = {
 "saldo_fdp_tot_txs":"Saldo fin de período total transaccional (TXS)",
 "saldo_prom_tot_txs":"Saldo promedio total transaccional (TXS)",
 "saldo_fdp_tot_planilla":"Saldo fin de período total planilla",
 "saldo_prom_tot_planilla":"Saldo promedio total planilla",
 "saldo_fdp_tot_tc":"Saldo fin de período total tarjeta de crédito (TC)",
 "saldo_prom_tot_tc":"Saldo promedio total tarjeta de crédito (TC)",
 "saldo_prom_tot_pasivo":"Saldo promedio total pasivo",
}
T3 = ("t_360_cliente (t360_feats)","e_perm_aws","cod_tipo_documento+nro_documento","frecuencia=1; cod_mes 202601-202606")
for b, d in SAL.items():
    add(f"{b}_um", f"{d} — último mes (202606)","numérico",*T3,"UM","0","MAX del mes 202606")
    add(f"{b}_u3m", f"{d} — promedio U3M (202604-202606)","numérico",*T3,"U3M","0","AVG 3 meses")
    add(f"{b}_u6m", f"{d} — promedio U6M (202601-202606)","numérico",*T3,"U6M","0","AVG 6 meses")
add("saldo_prom_tot_pasivo_max_u6m","Saldo promedio total pasivo — máximo en U6M","numérico",*T3,"U6M","0","MAX 6 meses")

# ---------------- t_360 flags ----------------
FLG = {
 "flg_colaborador":"Cliente colaborador IBK",
 "flg_cliente_cts":"Cliente con CTS",
 "flg_cliente_inversion":"Cliente con inversión",
 "flg_cliente_millonaria":"Cliente cuenta millonaria",
 "flg_cliente_alcancia":"Cliente con alcancía",
 "flg_cliente_planilla":"Cliente con planilla",
 "flg_cliente_planilla_act_sal":"Cliente planilla activa con saldo",
 "flg_cliente_planilla_abon":"Cliente planilla con abono",
 "flg_cliente_planilla_depo":"Cliente planilla con depósito",
 "flg_cliente_plazo_fijo":"Cliente con plazo fijo",
}
for b, d in FLG.items():
    add(f"{b}_um", f"{d} — último mes (202606)","0/1/null",*T3,"UM","0","Valor del mes 202606")
    add(f"{b}_u6m", f"{d} — tuvo en U6M","0/1",*T3,"U6M","0","1 si tuvo en algún mes de U6M")

# ---------------- t_360 ratios / derivados ----------------
add("saldo_pasivo_componentes_u3m","Suma de saldos prom U3M (planilla + txs + tc)","numérico",*T3,"U3M","0","Derivado: planilla_u3m+txs_u3m+tc_u3m")
add("ratio_tc_pasivo_u3m","Ratio TC / pasivo (U3M)","numérico",*T3,"U3M","0","tc_u3m / nullif(pasivo_u3m,0); null si pasivo=0")
add("ratio_planilla_pasivo_u3m","Ratio planilla / pasivo (U3M)","numérico",*T3,"U3M","0","planilla_u3m / nullif(pasivo_u3m,0)")
add("ratio_txs_pasivo_u3m","Ratio transaccional / pasivo (U3M)","numérico",*T3,"U3M","0","txs_u3m / nullif(pasivo_u3m,0)")
add("var_pasivo_um_vs_u6m","Variación del pasivo: (UM - U6M)/U6M","numérico",*T3,"UM vs U6M","0","null si pasivo_u6m=0")
add("flg_tiene_pasivo_u6m","Marca: tuvo saldo pasivo>0 en U6M","0/1",*T3,"U6M","0","1 si saldo_prom_tot_pasivo_u6m>0")
add("motivo_principalidad","Motivo de principalidad del cliente","texto","t_nds_principalidad (join por codunicocli)","e_perm_aws","codunicocli","fch_periodo=2026-06-30","foto","0","DISTINCT por codunicocli; anclaje 202606")

# ---------------- variables_rcc (castigo vida U24M) ----------------
VR = ("t_fact_report_rcc_rsk (variables_rcc)","e_perm_aws","tip_doc+key_value")
add("nro_entidades_castigo_vida","Nro entidades distintas con castigo 'vida' (U24M)","entero",*VR,
    "cod_cuenta 81..(302/925); tipo_credito 11/12/13/99; codmes>=202403 y <=202604","vida / U24M","0 / 24m",
    "COALESCE(...,0): 0 = sin castigo. Conteo distinct de entidades")
add("tipo_entidad_castigo_vida","Tipo de entidad del castigo vida (BIG FOUR / OTROS / SIN CASTIGO)","texto",*VR,
    "BIG FOUR si entidad in 00001/00002/00004/00006; codmes>=202404","vida / U24M","0 / 24m",
    "COALESCE(...,'SIN CASTIGO') para clientes sin castigo")

# ---------------- rm_cliente ----------------
add("sexo","Sexo del cliente","texto","t_rm_cliente","e_perm_aws","tipdoc+key_value","fecproceso=20260616","foto","0","MAX")
add("estado_civil","Estado civil del cliente","texto","t_rm_cliente","e_perm_aws","tipdoc+key_value","fecproceso=20260616","foto","0","MAX")

# ---------------- profesiones ----------------
add("nivel_profesional","Nivel profesional","texto","t_profesiones_hist","e_perm_aws","tipdoc+key_value","codmes=202603","foto","-3","MAX")
add("tipinstitucion","Tipo de institución","texto","t_profesiones_hist","e_perm_aws","tipdoc+key_value","codmes=202603","foto","-3","MAX")

# ==================== ESCRIBIR EXCEL ====================
HEAD = ["#","Variable","Descripcion","Tipo","Base / Tabla origen","Esquema",
        "Llave de join","Periodo / Filtro","Ventana","Desfase (vs codmes_pea=202606)","Particularidad"]
wb = Workbook(); ws = wb.active; ws.title = "Diccionario"
fill = PatternFill("solid", fgColor="007A72"); bold = Font(bold=True, color="FFFFFF")
bd = Border(*[Side(style="thin", color="D9D9D9")]*4)
for j, h in enumerate(HEAD, 1):
    c = ws.cell(1, j, h); c.font = bold; c.fill = fill; c.alignment = Alignment(wrap_text=True, vertical="center"); c.border = bd
for i, row in enumerate(R, start=2):
    ws.cell(i, 1, i-1).border = bd
    for j, v in enumerate(row, start=2):
        c = ws.cell(i, j, v); c.border = bd
        c.alignment = Alignment(wrap_text=True, vertical="top")
    if i % 2 == 0:
        for j in range(1, len(HEAD)+1):
            ws.cell(i, j).fill = PatternFill("solid", fgColor="F1F7F5")
ws.freeze_panes = "A2"
anchos = [5,34,52,12,34,14,26,30,12,16,46]
for j, w in enumerate(anchos, 1):
    ws.column_dimensions[get_column_letter(j)].width = w
ws.auto_filter.ref = f"A1:{get_column_letter(len(HEAD))}{len(R)+1}"
wb.save("diccionario_variables.xlsx")

import csv
with open("diccionario_variables.csv","w",newline="",encoding="utf-8-sig") as f:
    w = csv.writer(f); w.writerow(HEAD)
    for i, row in enumerate(R, 1): w.writerow([i]+row)
print(f"OK -> {len(R)} variables documentadas")
