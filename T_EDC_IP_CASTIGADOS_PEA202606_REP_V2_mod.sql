-- =========================================================================
-- TABLA: disc_model_owner.T_EDC_IP_CASTIGADOS_PEA202606_REP_V2_mod
-- Periodo PEA: 202606 (p_fecinformacion = 20260616) | RCC: 202604
-- Variables agregadas:
--   * t_360_cliente: saldos (txs/planilla/tc/pasivo) UM/U3M/U6M, flags (0/1/null) + ratios
--   * t_fact_report_rcc_rsk: nro/tipo entidad castigo (U24M)
--   * t_nds_principalidad: motivo_principalidad
--   * t_rm_cliente: sexo, estado_civil
--   * t_profesiones_hist: nivel_profesional, tipinstitucion
-- (No se incluye flg_activo / saldo activo)
-- =========================================================================
CREATE TABLE disc_model_owner.T_EDC_IP_CASTIGADOS_PEA202606_REP_V2_mod
WITH (format = 'PARQUET', parquet_compression = 'SNAPPY' , external_location = 's3://ibk-discovery-riesgos-us-east-1-339712995012-data/discovery/model_owner/B47515/estrategias/PEA202606VAR/')
AS
-- =========================================================================
-- 1) BASE CASTIGADOS PEA
-- =========================================================================
WITH PEA AS (
    select a.* from awsdatacatalog.e_perm_aws.ds_rtd_rskvol_indicadores_pea a
    WHERE p_fecinformacion = '20260616'                                  -- @FECHA_PEA
)
, df_rcc_castigos_act as (
    SELECT CODIGO_TIPO_DOCUMENTO || '-' || NUMERO_DOCUMENTO SUBJECT_ID,
        CASE WHEN MIN(DM) > 1800 THEN 1 ELSE 0 END FLG_ANTIGUEDAD_MAYOR_60_MESES,
        MAX(CASE WHEN CODIGO_ENTIDAD = '00002' THEN 1 ELSE 0 END) FLG_CASTIGO_IBK,
        1 FLG_CASTIGO_ACTUAL
    FROM e_perm_aws.T_cob_rcc_consulta_hist
    WHERE ((SUBSTR(CTA_CONTABLE,1,4) IN ('8113','8123','8133'))
        OR (SUBSTR(CTA_CONTABLE,1,6) IN ('811925','812925','813925')))
        and p_periodo='202604'                                           -- @CODMES_RCC
    GROUP BY CODIGO_TIPO_DOCUMENTO, NUMERO_DOCUMENTO
)
, df_rcc_castigos_tot as (
    SELECT DISTINCT key_value, tip_doc
    FROM AwsDataCatalog.e_perm_aws.t_fact_report_rcc_rsk
    WHERE SUBSTRING(cod_cuenta_rcc,1,4) IN ('8113','8123','8133')
      AND condicion > 30
      AND date_parse(concat(codmes,'01'), '%Y%m%d')
          BETWEEN date_add('month', -23, date_parse('20260401','%Y%m%d')) -- @ANCLA_RCC
              AND date_add('month',   0, date_parse('20260401','%Y%m%d')) -- @ANCLA_RCC
)
, df_castigo_ibk_act as (
    SELECT key_value, tip_doc, max(condicion) dm_cast_ibk
    FROM AwsDataCatalog.e_perm_aws.t_fact_report_rcc_rsk
    WHERE cod_instit_financiera = '00002'
      AND SUBSTRING(cod_cuenta_rcc,1,4) IN ('8113','8123','8133')
      AND condicion > 30
      AND codmes = '202604'                                              -- @CODMES_RCC
    group by key_value, tip_doc
)
, df_castigo_u24M_ibk as (
    SELECT DISTINCT key_value, tip_doc
    FROM AwsDataCatalog.e_perm_aws.t_fact_report_rcc_rsk
    WHERE cod_instit_financiera = '00002'
      AND SUBSTRING(cod_cuenta_rcc,1,4) IN ('8113','8123','8133')
      AND condicion > 30
      AND date_parse(concat(codmes,'01'), '%Y%m%d')
          BETWEEN date_add('month', -23, date_parse('20260401','%Y%m%d')) -- @ANCLA_RCC
              AND date_add('month',  -1, date_parse('20260401','%Y%m%d')) -- @ANCLA_RCC
)
, df_castigo_noibk_act as (
    SELECT key_value, tip_doc,
        max(condicion) dm_cast_noibk,
        sum(saldo)     s_cast_noibk
    FROM (
        select cod_instit_financiera, key_value, tip_doc,
               min(condicion) condicion, sum(saldo) saldo
        FROM AwsDataCatalog.e_perm_aws.t_fact_report_rcc_rsk
        WHERE codmes = '202604'                                          -- @CODMES_RCC
          AND cod_instit_financiera <> '00002'
          AND SUBSTRING(cod_cuenta_rcc,1,4) IN ('8113','8123','8133')
          AND condicion > 30
        group by cod_instit_financiera, key_value, tip_doc
    )
    group by key_value, tip_doc
)
, df_castigo_u24M_noibk as (
    SELECT key_value, tip_doc, codmes u_codmes,
        date_diff('month',
            CAST(date_parse(codmes,'%Y%m') AS date),
            CAST(date_parse('202604','%Y%m') AS date)                    -- @CODMES_RCC
        ) AS ant_ureporte,
        condicion dm_nocast_noibku24m,
        saldo sld_u24
    FROM (
        SELECT codmes, cod_instit_financiera, key_value, tip_doc,
            MIN(condicion) AS condicion,
            SUM(saldo)     AS saldo,
            ROW_NUMBER() OVER (
                PARTITION BY key_value, tip_doc, cod_instit_financiera
                ORDER BY codmes DESC
            ) AS rn
        FROM AwsDataCatalog.e_perm_aws.t_fact_report_rcc_rsk
        WHERE cod_instit_financiera <> '00002'
          AND SUBSTRING(cod_cuenta_rcc,1,4) IN ('8113','8123','8133')
          AND condicion > 30
          AND date_parse(concat(codmes,'01'), '%Y%m%d')
              BETWEEN date_add('month', -23, date_parse('20260401','%Y%m%d')) -- @ANCLA_RCC
                  AND date_add('month',  -1, date_parse('20260401','%Y%m%d')) -- @ANCLA_RCC
        GROUP BY codmes, cod_instit_financiera, key_value, tip_doc
    )
    WHERE rn = 1
)
, base_pea AS (
    select
        a.SUBJECT_ID
        ,split_part(a.SUBJECT_ID,'-',1) AS COD_TIP_DOC
        ,SUBSTRING(a.SUBJECT_ID,3)      AS KEY_VALUE
        ,A.p_fecinformacion
        ,SUBSTRING(A.p_fecinformacion,1,6) AS CODMES_PEA
        ,case when c.key_value is not null then 0
              when d.key_value is not null then 0
              when e.key_value is not null then s_cast_noibk
              when f.key_value is not null then sld_u24
              else 0 end DEUDA_CAS
        ,sit_lab_ap
        ,case when ant_ureporte is not null then
                case when ant_ureporte>0 and ant_ureporte<=6  then '0-6M'
                     when ant_ureporte>0 and ant_ureporte<=12 then '7-12M'
                     when ant_ureporte>0 and ant_ureporte<=18 then '13-18M'
                     when ant_ureporte>0 and ant_ureporte<=24 then '19-24M'
                end
         end RNG_ANT_UREPORT
        ,case when edad<=18 then '1.<18]'
              when edad<=21 then '2.<18-20]'
              when edad<=25 then '3.<20-25]'
              when edad<=35 then '4.<25-35]'
              when edad<=45 then '5.<35-45]'
              when edad<=65 then '6.<45-65]'
              when edad<=70 then '7.<65-70]'
              when edad<=75 then '8.<70-75]'
              when edad<=80 then '9.<75-80]'
              when edad>80  then '10.<80-+>' end RNG_EDAD
        ,case when renta>0 and renta<=750 then '0.<0-750]'
              when renta<=1000  then '1.<1k]'
              when renta<=1500  then '2.<1.5k]'
              when renta<=2000  then '3.<1.5k-2k]'
              when renta<=2500  then '4.<2k-2.5k]'
              when renta<=3000  then '5.<2.5k-3k]'
              when renta<=4000  then '6.<3k-4k]'
              when renta<=7000  then '7.<4k-7k]'
              when renta<=10000 then '8.<7k-10k]'
              when renta<=15000 then '9.<10k-15k]'
              when renta>15000  then '10.>15k'
              else '-' end rk_ing
        ,case when e.dm_cast_noibk/360 <5  then '0.<5años['
              when e.dm_cast_noibk/360 >=5 then '1.[5años+' end ANTI_CAST
        ,case when b.SUBJECT_ID is not null then 'CASTIGOS_REP' else 'NO_REP_CASTIGO' end FLG_CAST_REP
        ,case when b1.key_value is not null then 'CASTIGOS_TOT' else 'NO_CASTIGO' end FLG_CAST_TOT
        ,case when c.key_value is not null then 'CAST_IBK_REP'
              when d.key_value is not null then 'NO_CAST_IBK_U24M'
              when e.key_value is not null and e.dm_cast_noibk/360 <5  then 'CAST_NOIBK_REP<5anios'
              when e.key_value is not null and e.dm_cast_noibk/360 >=5 then 'CAST_NOIBK_REP>=5anios'
              when f.key_value is not null then 'NO_CAST_NOIBK_U24M'
              else 'NO_REP_CASTIGO' end FLG_CAST_AP
        ,case when c.key_value is not null then 'CAST_IBK_REP'
              when d.key_value is not null then 'NO_CAST_IBK_U24M'
              when e.key_value is not null then
                case when dm_cast_noibk>0 and dm_cast_noibk<0.5*360 then '0.]0-6m['
                     when dm_cast_noibk<1*360  then '3.[6m-1A['
                     when dm_cast_noibk<2*360  then '4.[1A-2A['
                     when dm_cast_noibk<3*360  then '5.[2A-3A['
                     when dm_cast_noibk<4*360  then '5.[3A-4A['
                     when dm_cast_noibk<5*360  then '6.[4A-5A['
                     when dm_cast_noibk>=5*360 then '7.[5A-+['
                end
              when f.key_value is not null then
                case when dm_nocast_noibku24m>0 and dm_nocast_noibku24m<=0.5*360 then '0.<0-6m['
                     when dm_nocast_noibku24m<1*360  then '3.[6m-1A['
                     when dm_nocast_noibku24m<2*360  then '4.[1A-2A['
                     when dm_nocast_noibku24m<3*360  then '5.[2A-3A['
                     when dm_nocast_noibku24m<4*360  then '5.[3A-4A['
                     when dm_nocast_noibku24m<5*360  then '6.[4A-5A['
                     when dm_nocast_noibku24m>=5*360 then '7.[5A-+['
                end
              else 'NO_REP_CASTIGO' end RNG_ANT_CAST
        ,case when c.key_value is not null then 'CAST_IBK_REP'
              when d.key_value is not null then 'NO_CAST_IBK_U24M'
              when e.key_value is not null then
                case when s_cast_noibk>0 and s_cast_noibk<=200 then '0.<0-200]'
                     when s_cast_noibk<=500   then '1.<200-500]'
                     when s_cast_noibk<=1000  then '2.<500-1000]'
                     when s_cast_noibk<=3000  then '3.<1000-3000]'
                     when s_cast_noibk<=5000  then '4.<3000-5000]'
                     when s_cast_noibk<=10000 then '5.<5000-10000]'
                     when s_cast_noibk>10000  then '6.<10000-+]'
                end
              when f.key_value is not null then
                case when sld_u24>0 and sld_u24<=200 then '0.<0-200]'
                     when sld_u24<=500   then '1.<200-500]'
                     when sld_u24<=1000  then '2.<500-1000]'
                     when sld_u24<=3000  then '3.<1000-3000]'
                     when sld_u24<=5000  then '4.<3000-5000]'
                     when sld_u24<=10000 then '5.<5000-10000]'
                     when sld_u24>10000  then '6.<10000-+]'
                end
              else 'NO_REP_CASTIGO' end RNG_DEUDA_CAST
        ,case when fa.key_value is not null and fa.estado = 'F' then 'Fallecido' end FLG_F
    from PEA a
    left join disc_model_owner.reniec_inhabilitados_csv fa
           on a.SUBJECT_ID = '1-' || fa.key_value
    left join df_rcc_castigos_act  b  on a.SUBJECT_ID = b.SUBJECT_ID
    left join df_rcc_castigos_tot  b1 on a.SUBJECT_ID = b1.tip_doc||'-'||b1.key_value
    left join df_castigo_ibk_act   c  on a.SUBJECT_ID = c.tip_doc ||'-'||c.key_value
    left join df_castigo_u24M_ibk  d  on a.SUBJECT_ID = d.tip_doc ||'-'||d.key_value
    left join df_castigo_noibk_act e  on a.SUBJECT_ID = e.tip_doc ||'-'||e.key_value
    left join (
        select tip_doc, key_value,
               min(u_codmes) u_codmes,
               max(ant_ureporte) ant_ureporte,
               min(dm_nocast_noibku24m) dm_nocast_noibku24m,
               sum(sld_u24) sld_u24
        from df_castigo_u24M_noibk
        group by tip_doc, key_value
    ) f on a.SUBJECT_ID = f.tip_doc||'-'||f.key_value
)
-- =========================================================================
-- 2) PIVOT DE CAIDAS  (FECHA_PROCESAMIENTO y p_fecinformacion = @FECHA_PEA)
-- =========================================================================
, caidas AS (
    SELECT ca.subject_id, mo.descripcion, MAX(es.estado) AS estado
    FROM awsdatacatalog.e_perm_aws.ds_rtd_rskvol_caidas_adquisicion ca
    LEFT JOIN awsdatacatalog.e_perm_aws.ms_rskvol_base_motivo_adq es
           ON  TRIM(CAST(ca.motcod AS VARCHAR)) = TRIM(CAST(es.motcod AS VARCHAR))
          AND es.basecod = 1                                            -- TC regular
          AND es.p_fecinformacion = '20260615'                          -- @FECHA_PEA
    LEFT JOIN awsdatacatalog.e_perm_aws.ms_rskvol_motivo_adq mo
           ON  TRIM(CAST(ca.motcod AS VARCHAR)) = TRIM(CAST(mo.motcod AS VARCHAR))
          AND mo.p_fecinformacion = '20260615'                          -- @FECHA_PEA
    WHERE ca.FECHA_PROCESAMIENTO = '20260616'                           -- @FECHA_PEA
      AND ca.basecod = 1                                                -- TC regular
    GROUP BY ca.subject_id, mo.descripcion
)
, pivot AS (
    SELECT
        subject_id
,MAX(CASE WHEN descripcion IN ('Primera Llamada','Primera llamada') THEN estado END) AS flg_primera_llamada
,MAX(CASE WHEN descripcion = 'Tiene Convenio' THEN estado END) AS flg_tiene_convenio
,MAX(CASE WHEN descripcion = 'Base Fraude' THEN estado END) AS flg_base_fraude
,MAX(CASE WHEN descripcion = 'Empresa Mala' THEN estado END) AS flg_empresa_mala
,MAX(CASE WHEN descripcion = 'Renta Sunat o Independiente NO HIT o Independiente renta <1000' THEN estado END) AS flg_renta_sunat_o_independiente_no_hit_o_independiente_renta_1000
,MAX(CASE WHEN descripcion = 'Buro Muy Bajo' THEN estado END) AS flg_buro_muy_bajo
,MAX(CASE WHEN descripcion = 'Sobreendeudamiento GYS' THEN estado END) AS flg_sobreendeudamiento_gys
,MAX(CASE WHEN descripcion = 'Mas de 7 Entidades' THEN estado END) AS flg_mas_de_7_entidades
,MAX(CASE WHEN descripcion = 'Prestamo IBK' THEN estado END) AS flg_prestamo_ibk
,MAX(CASE WHEN descripcion = 'Deuda En Banco No Permitido' THEN estado END) AS flg_deuda_en_banco_no_permitido
,MAX(CASE WHEN descripcion = 'Tiene Adelanto De Sueldo' THEN estado END) AS flg_tiene_adelanto_de_sueldo
,MAX(CASE WHEN descripcion = 'No tiene pasivos en IBK' THEN estado END) AS flg_no_tiene_pasivos_en_ibk
,MAX(CASE WHEN descripcion = 'Segunda llamada' THEN estado END) AS flg_segunda_llamada
,MAX(CASE WHEN descripcion = 'Primera llamada NB' THEN estado END) AS flg_primera_llamada_nb
,MAX(CASE WHEN descripcion = 'Mayor a 72 B' THEN estado END) AS flg_mayor_a_72_b
,MAX(CASE WHEN descripcion = 'INDEPENDIENTE_INFORMAL_NO_BANC' THEN estado END) AS flg_independiente_informal_no_banc
,MAX(CASE WHEN descripcion = 'Restricción venta cross PP' THEN estado END) AS flg_restricci_n_venta_cross_pp
,MAX(CASE WHEN descripcion = 'Sin abono U3M consecutivos' THEN estado END) AS flg_sin_abono_u3m_consecutivos
,MAX(CASE WHEN descripcion = 'Base aprobada PP Reg / PPRE' THEN estado END) AS flg_base_aprobada_pp_reg_ppre
,MAX(CASE WHEN descripcion = 'Sin abono UM' THEN estado END) AS flg_sin_abono_um
,MAX(CASE WHEN descripcion = 'Base Aprobada PPCD GEN o PG' THEN estado END) AS flg_base_aprobada_ppcd_gen_o_pg
,MAX(CASE WHEN descripcion = 'Recorte Recuadro Morado - PP' THEN estado END) AS flg_recorte_recuadro_morado_pp
,MAX(CASE WHEN descripcion = 'Recorte Recuadro Naranja - PP' THEN estado END) AS flg_recorte_recuadro_naranja_pp
,MAX(CASE WHEN descripcion = 'Caida gys nohit indep informal score orig bajo' THEN estado END) AS flg_caida_gys_nohit_indep_informal_score_orig_bajo
,MAX(CASE WHEN descripcion = 'Caida gys nohit mixto bajo' THEN estado END) AS flg_caida_gys_nohit_mixto_bajo
,MAX(CASE WHEN descripcion = 'CLIENTE_CONVENIO' THEN estado END) AS flg_cliente_convenio
,MAX(CASE WHEN descripcion = 'Lambayeque Piura y Libertad buro minimo' THEN estado END) AS flg_lambayeque_piura_y_libertad_buro_minimo
,MAX(CASE WHEN descripcion = 'Recorte coyuntura FEN - 4 Entidades a más con saldo - TC' THEN estado END) AS flg_recorte_coyuntura_fen_4_entidades_a_m_s_con_saldo_tc
,MAX(CASE WHEN descripcion = 'Recorte coyuntura FEN - 4 Entidades a más con saldo - PP' THEN estado END) AS flg_recorte_coyuntura_fen_4_entidades_a_m_s_con_saldo_pp
,MAX(CASE WHEN descripcion = 'Recorte Zona 3 4 5 e Ingreso < 1.5K' THEN estado END) AS flg_recorte_zona_3_4_5_e_ingreso_1_5k
,MAX(CASE WHEN descripcion = 'Recorte Apagado Zonas e Ingresos Bajos' THEN estado END) AS flg_recorte_apagado_zonas_e_ingresos_bajos
,MAX(CASE WHEN descripcion = 'Recorte coyuntura Ciclon Yaku' THEN estado END) AS flg_recorte_coyuntura_ciclon_yaku
,MAX(CASE WHEN descripcion = 'Recorte coyuntura FEN - 4 Entidades a más con saldo - PPRE' THEN estado END) AS flg_recorte_coyuntura_fen_4_entidades_a_m_s_con_saldo_ppre
,MAX(CASE WHEN descripcion = 'Recorte coyuntura FEN - PP' THEN estado END) AS flg_recorte_coyuntura_fen_pp
,MAX(CASE WHEN descripcion = 'Base Aprobada PP CP Intercorp' THEN estado END) AS flg_base_aprobada_pp_cp_intercorp
,MAX(CASE WHEN descripcion = 'Base Campaña PP y Pilotos' THEN estado END) AS flg_base_campa_a_pp_y_pilotos
,MAX(CASE WHEN descripcion = 'No cliente IBK - Sc Proactivo' THEN estado END) AS flg_no_cliente_ibk_sc_proactivo
,MAX(CASE WHEN descripcion = 'Edad No Permitida - Colab' THEN estado END) AS flg_edad_no_permitida_colab
,MAX(CASE WHEN descripcion = 'Sin Perfil de Saldo Pasivo minimo' THEN estado END) AS flg_sin_perfil_de_saldo_pasivo_minimo
,MAX(CASE WHEN descripcion = '1ra llam Banc - No Tiene Buro Mancomuno' THEN estado END) AS flg_1ra_llam_banc_no_tiene_buro_mancomuno
,MAX(CASE WHEN descripcion = '1ra llam Banc - Mal Comportamiento Mancomuno' THEN estado END) AS flg_1ra_llam_banc_mal_comportamiento_mancomuno
,MAX(CASE WHEN descripcion = '1ra llam Banc - Caida23' THEN estado END) AS flg_1ra_llam_banc_caida23
,MAX(CASE WHEN descripcion = 'BN_FRAUDE_UM' THEN estado END) AS flg_bn_fraude_um
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Reingreso' THEN estado END) AS flg_1ra_llam_no_banc_reingreso
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Pago Minimo' THEN estado END) AS flg_1ra_llam_no_banc_pago_minimo
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Caida 13' THEN estado END) AS flg_1ra_llam_no_banc_caida_13
,MAX(CASE WHEN descripcion IN ('CLIENTE_TIENE_TC','Cliente Tiene TC') THEN estado END) AS flg_cliente_tiene_tc
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Caida 22' THEN estado END) AS flg_1ra_llam_no_banc_caida_22
,MAX(CASE WHEN descripcion = '2da llam Banc - Feve Empresa' THEN estado END) AS flg_2da_llam_banc_feve_empresa
,MAX(CASE WHEN descripcion = '2da llam Banc - Base Recovery' THEN estado END) AS flg_2da_llam_banc_base_recovery
,MAX(CASE WHEN descripcion = '2da llam Banc - Re Ingreso' THEN estado END) AS flg_2da_llam_banc_re_ingreso
,MAX(CASE WHEN descripcion = '2da llam Banc - Convenio' THEN estado END) AS flg_2da_llam_banc_convenio
,MAX(CASE WHEN descripcion = '2da llam Banc - Caida 23' THEN estado END) AS flg_2da_llam_banc_caida_23
,MAX(CASE WHEN descripcion = 'Flag Mercury - Recorte 1ra ola' THEN estado END) AS flg_flag_mercury_recorte_1ra_ola
,MAX(CASE WHEN descripcion = 'Recorte Nuevo Sc. Origen TC Rechazo' THEN estado END) AS flg_recorte_nuevo_sc_origen_tc_rechazo
,MAX(CASE WHEN descripcion = 'Anticampaña Colaboradores' THEN estado END) AS flg_anticampa_a_colaboradores
,MAX(CASE WHEN descripcion = 'Sin abono U3M consecutivos - PP Colab CP' THEN estado END) AS flg_sin_abono_u3m_consecutivos_pp_colab_cp
,MAX(CASE WHEN descripcion = 'Repros IBK/SSFF' THEN estado END) AS flg_repros_ibk_ssff
,MAX(CASE WHEN descripcion = 'Recorte Zonas Bajas' THEN estado END) AS flg_recorte_zonas_bajas
,MAX(CASE WHEN descripcion = 'Edad Menor 18' THEN estado END) AS flg_edad_menor_18
,MAX(CASE WHEN descripcion = 'Mayor a 5 Entidades con Saldo' THEN estado END) AS flg_mayor_a_5_entidades_con_saldo
,MAX(CASE WHEN descripcion = 'Tiene Cobranza Judicial 24M' THEN estado END) AS flg_tiene_cobranza_judicial_24m
,MAX(CASE WHEN descripcion = 'Calificacion diferente a Normal y CPP Mes 2 a 6' THEN estado END) AS flg_calificacion_diferente_a_normal_y_cpp_mes_2_a_6
,MAX(CASE WHEN descripcion = 'Cliente con más de 8 días de mora en IBK' THEN estado END) AS flg_cliente_con_m_s_de_8_d_as_de_mora_en_ibk
,MAX(CASE WHEN descripcion = 'Saldo Castigo SSFF Reportado UM y Saldo Castigo SSFF Reportado (+ reciente por entidad) menor igual a 60 meses' THEN estado END) AS flg_saldo_castigo_ssff_reportado_um_y_saldo_castigo_ssff_reportado_reciente_por_entidad_menor_igual_a_60_meses
,MAX(CASE WHEN descripcion = 'Prestamo Facil con Garantia' THEN estado END) AS flg_prestamo_facil_con_garantia
,MAX(CASE WHEN descripcion = 'Cuotas pagadas' THEN estado END) AS flg_cuotas_pagadas
,MAX(CASE WHEN descripcion = 'Recorte Cluster 3 de PP' THEN estado END) AS flg_recorte_cluster_3_de_pp
,MAX(CASE WHEN descripcion = 'Buró muy bajo / Rechazo / No tiene' THEN estado END) AS flg_bur_muy_bajo_rechazo_no_tiene
,MAX(CASE WHEN descripcion = 'CEM + Cuotas < 50' THEN estado END) AS flg_cem_cuotas_50
,MAX(CASE WHEN descripcion = 'Cem/Ingreso > 50%' THEN estado END) AS flg_cem_ingreso_50_
,MAX(CASE WHEN descripcion = 'Retiro Bin 4 y 5 con G7 TC Bank' THEN estado END) AS flg_retiro_bin_4_y_5_con_g7_tc_bank
,MAX(CASE WHEN descripcion = 'Cliente sin D/I disponible' THEN estado END) AS flg_cliente_sin_d_i_disponible
,MAX(CASE WHEN descripcion = 'Caida FEN TC' THEN estado END) AS flg_caida_fen_tc
,MAX(CASE WHEN descripcion = 'Cliente con Clasificacion CPP o mas SSFF' THEN estado END) AS flg_cliente_con_clasificacion_cpp_o_mas_ssff
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta PPSESF' THEN estado END) AS flg_oferta_3000_recalculo_oferta_ppsesf
,MAX(CASE WHEN descripcion = 'Incremental menor al minimo - Recalculo Oferta PPRE' THEN estado END) AS flg_incremental_menor_al_minimo_recalculo_oferta_ppre
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta PPRESE' THEN estado END) AS flg_oferta_3000_recalculo_oferta_pprese
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC Caida doble' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_caida_doble
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC Colaborador' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_colaborador
,MAX(CASE WHEN descripcion = 'Oferta < 500 - Recalculo Oferta PPMP' THEN estado END) AS flg_oferta_500_recalculo_oferta_ppmp
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta PPCP NEI' THEN estado END) AS flg_oferta_3000_recalculo_oferta_ppcp_nei
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta Colab PP ISR' THEN estado END) AS flg_oferta_3000_recalculo_oferta_colab_pp_isr
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC ISR' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_isr
,MAX(CASE WHEN descripcion = 'Plazo Maximo No Cubre La CD PP - CD ROJO' THEN estado END) AS flg_plazo_maximo_no_cubre_la_cd_pp_cd_rojo
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC Vision Cliente' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_vision_cliente
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC Familia Salud' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_familia_salud
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC No Bank Informal Hospital Clinica' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_no_bank_informal_hospital_clinica
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC EMP MALA + FEVE' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_emp_mala_feve
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC NBANKINF_G1G2G3' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_nbankinf_g1g2g3
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC Bancarizados Ingresos Bajos' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_bancarizados_ingresos_bajos
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC No Bank G5' THEN estado END) AS flg_linea_700_rescate_tc_no_bank_g5
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC VC Exclusion' THEN estado END) AS flg_linea_700_rescate_tc_vc_exclusion
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC Caidas Multiples VC' THEN estado END) AS flg_linea_700_rescate_tc_caidas_multiples_vc
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC Caidas Multiples NB' THEN estado END) AS flg_linea_700_rescate_tc_caidas_multiples_nb
,MAX(CASE WHEN descripcion = 'Linea < 700 - TC NB Informal Rechazo CL1CL2' THEN estado END) AS flg_linea_700_tc_nb_informal_rechazo_cl1cl2
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC Indp Inf Farm G4 G5' THEN estado END) AS flg_linea_700_rescate_tc_indp_inf_farm_g4_g5
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC No Banc Vision Cliente' THEN estado END) AS flg_linea_700_rescate_tc_no_banc_vision_cliente
,MAX(CASE WHEN descripcion = 'Anticampañas' THEN estado END) AS flg_anticampa_as
,MAX(CASE WHEN descripcion = 'Moroso Ibk' THEN estado END) AS flg_moroso_ibk
,MAX(CASE WHEN descripcion = 'Cem menor igual 0' THEN estado END) AS flg_cem_menor_igual_0
,MAX(CASE WHEN descripcion = 'Edad menor 22 o mayor a 71' THEN estado END) AS flg_edad_menor_22_o_mayor_a_71
,MAX(CASE WHEN descripcion = 'Base Combo' THEN estado END) AS flg_base_combo
,MAX(CASE WHEN descripcion = 'Saldo PP RCC Menor a 2 Meses' THEN estado END) AS flg_saldo_pp_rcc_menor_a_2_meses
,MAX(CASE WHEN descripcion = 'Saldo Prestamos' THEN estado END) AS flg_saldo_prestamos
,MAX(CASE WHEN descripcion = 'Deuda Total Ingreso sin disponible' THEN estado END) AS flg_deuda_total_ingreso_sin_disponible
,MAX(CASE WHEN descripcion = 'Base Alertas' THEN estado END) AS flg_base_alertas
,MAX(CASE WHEN descripcion = 'Mancomuno' THEN estado END) AS flg_mancomuno
,MAX(CASE WHEN descripcion = 'Independiente Sunat Informal' THEN estado END) AS flg_independiente_sunat_informal
,MAX(CASE WHEN descripcion = 'Rechazo Ultimo Mes' THEN estado END) AS flg_rechazo_ultimo_mes
,MAX(CASE WHEN descripcion = 'Oferta menor a 3000 soles' THEN estado END) AS flg_oferta_menor_a_3000_soles
,MAX(CASE WHEN descripcion = 'Grupo Ibk Independiente' THEN estado END) AS flg_grupo_ibk_independiente
,MAX(CASE WHEN descripcion = 'Score Prestamo Bajo flujo independiente y no bancarizado' THEN estado END) AS flg_score_prestamo_bajo_flujo_independiente_y_no_bancarizado
,MAX(CASE WHEN descripcion = 'Sin Buro score prestamo medio flujo independiente' THEN estado END) AS flg_sin_buro_score_prestamo_medio_flujo_independiente
,MAX(CASE WHEN descripcion = 'NO_DNI_UM' THEN estado END) AS flg_no_dni_um
,MAX(CASE WHEN descripcion = 'Convenio X - PPCD' THEN estado END) AS flg_convenio_x_ppcd
,MAX(CASE WHEN descripcion = 'Flujo reenganche' THEN estado END) AS flg_flujo_reenganche
,MAX(CASE WHEN descripcion = 'TC IBK Activa' THEN estado END) AS flg_tc_ibk_activa
,MAX(CASE WHEN descripcion = 'Saldo TC IBK > 0' THEN estado END) AS flg_saldo_tc_ibk_0
,MAX(CASE WHEN descripcion = 'CEM <= 0 - PPCD TC' THEN estado END) AS flg_cem_0_ppcd_tc
,MAX(CASE WHEN descripcion = 'Desembolsos Hipotecarios' THEN estado END) AS flg_desembolsos_hipotecarios
,MAX(CASE WHEN descripcion = 'Menor a 21 B' THEN estado END) AS flg_menor_a_21_b
,MAX(CASE WHEN descripcion = 'Rechazo flujo' THEN estado END) AS flg_rechazo_flujo
,MAX(CASE WHEN descripcion = 'Ratio Deuda Ingreso' THEN estado END) AS flg_ratio_deuda_ingreso
,MAX(CASE WHEN descripcion = 'Ingresos menores a S/.2500 - Exclusion' THEN estado END) AS flg_ingresos_menores_a_s_2500_exclusion
,MAX(CASE WHEN descripcion = 'Saldo CDPP < 3K' THEN estado END) AS flg_saldo_cdpp_3k
,MAX(CASE WHEN descripcion = 'Saldo CDTC < 3K' THEN estado END) AS flg_saldo_cdtc_3k
,MAX(CASE WHEN descripcion = 'Caida gys indep formal buro bajo rech orig bajo' THEN estado END) AS flg_caida_gys_indep_formal_buro_bajo_rech_orig_bajo
,MAX(CASE WHEN descripcion = 'Caida gys nohit indep formal score orig bajo' THEN estado END) AS flg_caida_gys_nohit_indep_formal_score_orig_bajo
,MAX(CASE WHEN descripcion = 'No cumple perfil Sc TC/PP/Buro  - CP NEI sin campaña PP' THEN estado END) AS flg_no_cumple_perfil_sc_tc_pp_buro_cp_nei_sin_campa_a_pp
,MAX(CASE WHEN descripcion = 'Segmento 3 Informales' THEN estado END) AS flg_segmento_3_informales
,MAX(CASE WHEN descripcion = 'Oferta menor a 3000' THEN estado END) AS flg_oferta_menor_a_3000
,MAX(CASE WHEN descripcion = 'Ingreso < 7000 y Buro Bajo/Muy Bajo/Rechazo' THEN estado END) AS flg_ingreso_7000_y_buro_bajo_muy_bajo_rechazo
,MAX(CASE WHEN descripcion = 'Recorte Ingresos Bajos, Z5 y Subnivel B1 B2' THEN estado END) AS flg_recorte_ingresos_bajos_z5_y_subnivel_b1_b2
,MAX(CASE WHEN descripcion = 'Recorte Apagado SubZonas' THEN estado END) AS flg_recorte_apagado_subzonas
,MAX(CASE WHEN descripcion = 'Recorte Ubigeo No Permitidas, Zona 2 3 4, CS y Cliente digital' THEN estado END) AS flg_recorte_ubigeo_no_permitidas_zona_2_3_4_cs_y_cliente_digital
,MAX(CASE WHEN descripcion = 'Recorte Ind. con score de originacion Bajo' THEN estado END) AS flg_recorte_ind_con_score_de_originacion_bajo
,MAX(CASE WHEN descripcion = 'Recorte Dep. con Subnivel score Buro Bajo2' THEN estado END) AS flg_recorte_dep_con_subnivel_score_buro_bajo2
,MAX(CASE WHEN descripcion = 'ENT_SALDO_UM' THEN estado END) AS flg_ent_saldo_um
,MAX(CASE WHEN descripcion = 'Recorte coyuntura Ciclon Yaku - TC' THEN estado END) AS flg_recorte_coyuntura_ciclon_yaku_tc
,MAX(CASE WHEN descripcion = 'Producto TC+CD y No Bancarizado' THEN estado END) AS flg_producto_tc_cd_y_no_bancarizado
,MAX(CASE WHEN descripcion = 'Sin Saldo Pasivo minimo U6M' THEN estado END) AS flg_sin_saldo_pasivo_minimo_u6m
,MAX(CASE WHEN descripcion = 'Ratio Deuda/Ingreso > 50' THEN estado END) AS flg_ratio_deuda_ingreso_50
,MAX(CASE WHEN descripcion = 'Recorte Rechazo - Nuevo Sc TC Adm Bank' THEN estado END) AS flg_recorte_rechazo_nuevo_sc_tc_adm_bank
,MAX(CASE WHEN descripcion = 'CASTIGO_IBK_U24M' THEN estado END) AS flg_castigo_ibk_u24m
,MAX(CASE WHEN descripcion = 'BURO_RECHAZO_UM' THEN estado END) AS flg_buro_rechazo_um
,MAX(CASE WHEN descripcion = 'JUDICIAL_SSFF_U24M' THEN estado END) AS flg_judicial_ssff_u24m
,MAX(CASE WHEN descripcion = 'CLASIF_RCC_MAYOR_NORMAL_SB_UM' THEN estado END) AS flg_clasif_rcc_mayor_normal_sb_um
,MAX(CASE WHEN descripcion = '1ra llam Banc - No Tiene Buro Mayor CPP Ultimos 5 Meses' THEN estado END) AS flg_1ra_llam_banc_no_tiene_buro_mayor_cpp_ultimos_5_meses
,MAX(CASE WHEN descripcion = '1ra llam Banc - Caida19' THEN estado END) AS flg_1ra_llam_banc_caida19
,MAX(CASE WHEN descripcion = '1ra llam Banc - Caida20' THEN estado END) AS flg_1ra_llam_banc_caida20
,MAX(CASE WHEN descripcion = '1ra llam Banc - Caida21' THEN estado END) AS flg_1ra_llam_banc_caida21
,MAX(CASE WHEN descripcion = '1ra llam Banc - Caida22' THEN estado END) AS flg_1ra_llam_banc_caida22
,MAX(CASE WHEN descripcion = 'FEVE_EMPRESA_UM' THEN estado END) AS flg_feve_empresa_um
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Cliente Especial' THEN estado END) AS flg_1ra_llam_no_banc_cliente_especial
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Rechazo' THEN estado END) AS flg_1ra_llam_no_banc_rechazo
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Caida 16' THEN estado END) AS flg_1ra_llam_no_banc_caida_16
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Caida 18' THEN estado END) AS flg_1ra_llam_no_banc_caida_18
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Caida 21' THEN estado END) AS flg_1ra_llam_no_banc_caida_21
,MAX(CASE WHEN descripcion = '2da llam Banc - Empresa No Deseada' THEN estado END) AS flg_2da_llam_banc_empresa_no_deseada
,MAX(CASE WHEN descripcion = '2da llam Banc - Feve Ibk' THEN estado END) AS flg_2da_llam_banc_feve_ibk
,MAX(CASE WHEN descripcion = '2da llam Banc - R1R2' THEN estado END) AS flg_2da_llam_banc_r1r2
,MAX(CASE WHEN descripcion = '2da llam Banc - Caida 12' THEN estado END) AS flg_2da_llam_banc_caida_12
,MAX(CASE WHEN descripcion = '2da llam Banc - Base Alertas' THEN estado END) AS flg_2da_llam_banc_base_alertas
,MAX(CASE WHEN descripcion = 'BN_BURO_BAJO_AMAZ_LOR' THEN estado END) AS flg_bn_buro_bajo_amaz_lor
,MAX(CASE WHEN descripcion = '2da llam Banc - Caida 20' THEN estado END) AS flg_2da_llam_banc_caida_20
,MAX(CASE WHEN descripcion = 'Base Aprobada TC Regular' THEN estado END) AS flg_base_aprobada_tc_regular
,MAX(CASE WHEN descripcion = 'Altas TC ultimos 6 meses' THEN estado END) AS flg_altas_tc_ultimos_6_meses
,MAX(CASE WHEN descripcion = 'Caida diferente a rescates' THEN estado END) AS flg_caida_diferente_a_rescates
,MAX(CASE WHEN descripcion = 'Sin Informacion Campana' THEN estado END) AS flg_sin_informacion_campana
,MAX(CASE WHEN descripcion = 'Score Proactivo No Permitido' THEN estado END) AS flg_score_proactivo_no_permitido
,MAX(CASE WHEN descripcion = 'Score Buro Muy Bajo o Rechazo' THEN estado END) AS flg_score_buro_muy_bajo_o_rechazo
,MAX(CASE WHEN descripcion = 'Tiene Deuda Refinanciada 6M' THEN estado END) AS flg_tiene_deuda_refinanciada_6m
,MAX(CASE WHEN descripcion = 'Saldo Judicial Reportado último mes' THEN estado END) AS flg_saldo_judicial_reportado_ltimo_mes
,MAX(CASE WHEN descripcion = 'Cliente con saldo convenio vigente' THEN estado END) AS flg_cliente_con_saldo_convenio_vigente
,MAX(CASE WHEN descripcion = 'Rechazo/Aprobado ultimos 6 meses' THEN estado END) AS flg_rechazo_aprobado_ultimos_6_meses
,MAX(CASE WHEN descripcion = 'Recorte coyuntura Ciclon Yaku - PPRE' THEN estado END) AS flg_recorte_coyuntura_ciclon_yaku_ppre
,MAX(CASE WHEN descripcion = 'Desembolso EC/CDD U6M' THEN estado END) AS flg_desembolso_ec_cdd_u6m
,MAX(CASE WHEN descripcion = 'Clientes ISR Buro' THEN estado END) AS flg_clientes_isr_buro
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta' THEN estado END) AS flg_oferta_3000_recalculo_oferta
,MAX(CASE WHEN descripcion = 'Incremental menor al minimo - Recalculo Oferta PPRESE' THEN estado END) AS flg_incremental_menor_al_minimo_recalculo_oferta_pprese
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta PPCP' THEN estado END) AS flg_oferta_3000_recalculo_oferta_ppcp
,MAX(CASE WHEN descripcion = 'Plazo Maximo No Cubre La CD PP' THEN estado END) AS flg_plazo_maximo_no_cubre_la_cd_pp
,MAX(CASE WHEN descripcion = 'Oferta CD No Cubre CD PP SESF' THEN estado END) AS flg_oferta_cd_no_cubre_cd_pp_sesf
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC Pasivos' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_pasivos
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta Colab PP Resc MB/R' THEN estado END) AS flg_oferta_3000_recalculo_oferta_colab_pp_resc_mb_r
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta PP FEVE EMP' THEN estado END) AS flg_oferta_3000_recalculo_oferta_pp_feve_emp
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC Hiraoka' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_hiraoka
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta PPRE ISR' THEN estado END) AS flg_oferta_3000_recalculo_oferta_ppre_isr
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC No Bank Sunedu' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_no_bank_sunedu
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC FARM_INF' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_farm_inf
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC CMP EST INFORMAL' THEN estado END) AS flg_linea_700_rescate_tc_cmp_est_informal
,MAX(CASE WHEN descripcion = 'Linea < 700 - TC NB informal G4G5' THEN estado END) AS flg_linea_700_tc_nb_informal_g4g5
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC Ind Buro Bajo Banc' THEN estado END) AS flg_linea_700_rescate_tc_ind_buro_bajo_banc
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC Cuenta Sueldo Cross Sell sobreendeudado' THEN estado END) AS flg_linea_700_rescate_tc_cuenta_sueldo_cross_sell_sobreendeudado
,MAX(CASE WHEN descripcion = 'No Bancarizado sin planilla' THEN estado END) AS flg_no_bancarizado_sin_planilla
,MAX(CASE WHEN descripcion = 'Sectorista Malo' THEN estado END) AS flg_sectorista_malo
,MAX(CASE WHEN descripcion = 'Expendientes PP Aprobados y Rechazados ADQ' THEN estado END) AS flg_expendientes_pp_aprobados_y_rechazados_adq
,MAX(CASE WHEN descripcion = 'Base Recovery' THEN estado END) AS flg_base_recovery
,MAX(CASE WHEN descripcion = 'Renta <850' THEN estado END) AS flg_renta_850
,MAX(CASE WHEN descripcion = 'Cem menor a 50' THEN estado END) AS flg_cem_menor_a_50
,MAX(CASE WHEN descripcion = 'Con Adelanto de Sueldo' THEN estado END) AS flg_con_adelanto_de_sueldo
,MAX(CASE WHEN descripcion = 'Colaborador Ibk' THEN estado END) AS flg_colaborador_ibk
,MAX(CASE WHEN descripcion = 'Independiente Buro muy bajo o Rechazo' THEN estado END) AS flg_independiente_buro_muy_bajo_o_rechazo
,MAX(CASE WHEN descripcion = 'Renta Menor a 1000 y Score Prestamo Bajo o Muy Bajo' THEN estado END) AS flg_renta_menor_a_1000_y_score_prestamo_bajo_o_muy_bajo
,MAX(CASE WHEN descripcion = 'Castigo ibk ultimo mes' THEN estado END) AS flg_castigo_ibk_ultimo_mes
,MAX(CASE WHEN descripcion = 'Buro Bajo rechazo 2M' THEN estado END) AS flg_buro_bajo_rechazo_2m
,MAX(CASE WHEN descripcion = 'Score Prestamo Bajo y buro no alto' THEN estado END) AS flg_score_prestamo_bajo_y_buro_no_alto
,MAX(CASE WHEN descripcion = 'Score Prestamo Bajo y renta menor o igual 1500' THEN estado END) AS flg_score_prestamo_bajo_y_renta_menor_o_igual_1500
,MAX(CASE WHEN descripcion = 'Base Univ. Nacional Ucayali y Gobierno Ancash' THEN estado END) AS flg_base_univ_nacional_ucayali_y_gobierno_ancash
,MAX(CASE WHEN descripcion = 'Independiente Menor a 25 o Buro Muy Bajo' THEN estado END) AS flg_independiente_menor_a_25_o_buro_muy_bajo
,MAX(CASE WHEN descripcion = 'Menor a 21' THEN estado END) AS flg_menor_a_21
,MAX(CASE WHEN descripcion = 'Renta < 650 B' THEN estado END) AS flg_renta_650_b
,MAX(CASE WHEN descripcion = 'Base combo Score Rechazo' THEN estado END) AS flg_base_combo_score_rechazo
,MAX(CASE WHEN descripcion = 'Clientes Mix-Ind-Dep Inf no BANCARIZADO G4 con ingresos <=4M' THEN estado END) AS flg_clientes_mix_ind_dep_inf_no_bancarizado_g4_con_ingresos_4m
,MAX(CASE WHEN descripcion = 'No CS Riesgos' THEN estado END) AS flg_no_cs_riesgos
,MAX(CASE WHEN descripcion = 'Base Aprobada PPCSNB' THEN estado END) AS flg_base_aprobada_ppcsnb
,MAX(CASE WHEN descripcion = 'Recorte Recuadro Celeste - PP' THEN estado END) AS flg_recorte_recuadro_celeste_pp
,MAX(CASE WHEN descripcion = 'Zona No Permitida - PPRE' THEN estado END) AS flg_zona_no_permitida_ppre
,MAX(CASE WHEN descripcion = 'Antiguedad laboral menor 6M - CP NEI sin campaña PP' THEN estado END) AS flg_antiguedad_laboral_menor_6m_cp_nei_sin_campa_a_pp
,MAX(CASE WHEN descripcion = 'Caida dif normal ibk' THEN estado END) AS flg_caida_dif_normal_ibk
,MAX(CASE WHEN descripcion = 'Caida gys indep informal buro bajo muy bajo sinburo' THEN estado END) AS flg_caida_gys_indep_informal_buro_bajo_muy_bajo_sinburo
,MAX(CASE WHEN descripcion = 'Caida gys indep informal buro medio score orig medio renta <= 2000' THEN estado END) AS flg_caida_gys_indep_informal_buro_medio_score_orig_medio_renta_2000
,MAX(CASE WHEN descripcion = 'Caida gys indep informal orig bajo rechazo' THEN estado END) AS flg_caida_gys_indep_informal_orig_bajo_rechazo
,MAX(CASE WHEN descripcion = 'Caida gys nohit dep score orig rechazo' THEN estado END) AS flg_caida_gys_nohit_dep_score_orig_rechazo
,MAX(CASE WHEN descripcion = 'Caida gys nohit indep informal' THEN estado END) AS flg_caida_gys_nohit_indep_informal
,MAX(CASE WHEN descripcion = 'Lambayeque no hit ind informal score ori' THEN estado END) AS flg_lambayeque_no_hit_ind_informal_score_ori
,MAX(CASE WHEN descripcion = 'Libertad no hit ind formal score ori' THEN estado END) AS flg_libertad_no_hit_ind_formal_score_ori
,MAX(CASE WHEN descripcion = 'Piura dependiente score ori' THEN estado END) AS flg_piura_dependiente_score_ori
,MAX(CASE WHEN descripcion = 'Piura no hit ind formal score ori' THEN estado END) AS flg_piura_no_hit_ind_formal_score_ori
,MAX(CASE WHEN descripcion = 'COMPORTAMIENTO_IBK_DIF_NORMAL' THEN estado END) AS flg_comportamiento_ibk_dif_normal
,MAX(CASE WHEN descripcion = 'Grupo TC Sc Comp Muy Bajo/Rechazo' THEN estado END) AS flg_grupo_tc_sc_comp_muy_bajo_rechazo
,MAX(CASE WHEN descripcion = 'Recorte Ubigeo No Permitidas y Zona 5/Rechazo' THEN estado END) AS flg_recorte_ubigeo_no_permitidas_y_zona_5_rechazo
,MAX(CASE WHEN descripcion = 'Recorte Cluster 3 de EC y Zona 4 5 Rechazo' THEN estado END) AS flg_recorte_cluster_3_de_ec_y_zona_4_5_rechazo
,MAX(CASE WHEN descripcion = 'Recorte coyuntura FEN - TC' THEN estado END) AS flg_recorte_coyuntura_fen_tc
,MAX(CASE WHEN descripcion = 'Recorte coyuntura FEN - 4 Entidades a más con saldo' THEN estado END) AS flg_recorte_coyuntura_fen_4_entidades_a_m_s_con_saldo
,MAX(CASE WHEN descripcion = 'BURO_MUY_BAJO_UM' THEN estado END) AS flg_buro_muy_bajo_um
,MAX(CASE WHEN descripcion = 'ZONA NO PERMITA SEGUN SCORE COMPORTAMENTAL TC - PPRE' THEN estado END) AS flg_zona_no_permita_segun_score_comportamental_tc_ppre
,MAX(CASE WHEN descripcion = 'Anticampania - GL' THEN estado END) AS flg_anticampania_gl
,MAX(CASE WHEN descripcion = 'Incremento de Saldo SSF y Saldo NR entre 1 a 3 mes' THEN estado END) AS flg_incremento_de_saldo_ssf_y_saldo_nr_entre_1_a_3_mes
,MAX(CASE WHEN descripcion = '1ra llam Banc - Aprobo Buro Mayor 5 Bancos' THEN estado END) AS flg_1ra_llam_banc_aprobo_buro_mayor_5_bancos
,MAX(CASE WHEN descripcion = 'CLASIF_MAYOR_CPP_BURO_APROB_UM' THEN estado END) AS flg_clasif_mayor_cpp_buro_aprob_um
,MAX(CASE WHEN descripcion = 'REFINANCIADOS_RCC_SB_U6M' THEN estado END) AS flg_refinanciados_rcc_sb_u6m
,MAX(CASE WHEN descripcion = 'ENT_TOT_MAYOR_IGUAL_7_UM' THEN estado END) AS flg_ent_tot_mayor_igual_7_um
,MAX(CASE WHEN descripcion = '1ra llam Banc - Caida24' THEN estado END) AS flg_1ra_llam_banc_caida24
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Sectorista Malo' THEN estado END) AS flg_1ra_llam_no_banc_sectorista_malo
,MAX(CASE WHEN descripcion = 'EMPLEADO_SBS' THEN estado END) AS flg_empleado_sbs
,MAX(CASE WHEN descripcion = 'BN_RECOVERY_UM' THEN estado END) AS flg_bn_recovery_um
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Caida 17' THEN estado END) AS flg_1ra_llam_no_banc_caida_17
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Sunat' THEN estado END) AS flg_1ra_llam_no_banc_sunat
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Caida 23' THEN estado END) AS flg_1ra_llam_no_banc_caida_23
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Caida 24' THEN estado END) AS flg_1ra_llam_no_banc_caida_24
,MAX(CASE WHEN descripcion = '2da llam Banc - Anticampanas' THEN estado END) AS flg_2da_llam_banc_anticampanas
,MAX(CASE WHEN descripcion = '2da llam Banc - Linea Tc' THEN estado END) AS flg_2da_llam_banc_linea_tc
,MAX(CASE WHEN descripcion = '2da llam Banc - Caida 13' THEN estado END) AS flg_2da_llam_banc_caida_13
,MAX(CASE WHEN descripcion = '2da llam Banc - Empresa Mala' THEN estado END) AS flg_2da_llam_banc_empresa_mala
,MAX(CASE WHEN descripcion = '2da llam Banc - Caida 18' THEN estado END) AS flg_2da_llam_banc_caida_18
,MAX(CASE WHEN descripcion = '2da llam Banc - Renta Sunat < 1000' THEN estado END) AS flg_2da_llam_banc_renta_sunat_1000
,MAX(CASE WHEN descripcion = '2da llam Banc - Caida 24' THEN estado END) AS flg_2da_llam_banc_caida_24
,MAX(CASE WHEN descripcion = '2da llam Banc - Caida 25' THEN estado END) AS flg_2da_llam_banc_caida_25
,MAX(CASE WHEN descripcion = 'Clasificacion no normal RCC' THEN estado END) AS flg_clasificacion_no_normal_rcc
,MAX(CASE WHEN descripcion = 'Sobreendeudado Colaborador' THEN estado END) AS flg_sobreendeudado_colaborador
,MAX(CASE WHEN descripcion = 'Caida gys nohit dep score orig rechazo - Colaborador' THEN estado END) AS flg_caida_gys_nohit_dep_score_orig_rechazo_colaborador
,MAX(CASE WHEN descripcion = 'Lambayeque Piura y Libertad buro minimo - Colaborador' THEN estado END) AS flg_lambayeque_piura_y_libertad_buro_minimo_colaborador
,MAX(CASE WHEN descripcion = 'Sobreendeudado < 50 - Colaborador' THEN estado END) AS flg_sobreendeudado_50_colaborador
,MAX(CASE WHEN descripcion = 'No CS Riesgos - PP Colab CP' THEN estado END) AS flg_no_cs_riesgos_pp_colab_cp
,MAX(CASE WHEN descripcion = 'Sin abono UM - PP Colab CP' THEN estado END) AS flg_sin_abono_um_pp_colab_cp
,MAX(CASE WHEN descripcion = 'Base Campaña TC/C_DOBLE' THEN estado END) AS flg_base_campa_a_tc_c_doble
,MAX(CASE WHEN descripcion = 'Recorte Pasivos' THEN estado END) AS flg_recorte_pasivos
,MAX(CASE WHEN descripcion = 'Base Campaña TC/C_DOBLE/LIN_PEQUE/GL' THEN estado END) AS flg_base_campa_a_tc_c_doble_lin_peque_gl
,MAX(CASE WHEN descripcion = 'Deuda Catigada 24M' THEN estado END) AS flg_deuda_catigada_24m
,MAX(CASE WHEN descripcion = 'Deuda Reestructurada U6M' THEN estado END) AS flg_deuda_reestructurada_u6m
,MAX(CASE WHEN descripcion = 'Saldo Reestructurado IBK y/o SSFF Reportado último mes' THEN estado END) AS flg_saldo_reestructurado_ibk_y_o_ssff_reportado_ltimo_mes
,MAX(CASE WHEN descripcion = 'Rechazo/Aprobado ultimo mes' THEN estado END) AS flg_rechazo_aprobado_ultimo_mes
,MAX(CASE WHEN descripcion = 'CODMARCA COLAB 2102, 2202, 2602' THEN estado END) AS flg_codmarca_colab_2102_2202_2602
,MAX(CASE WHEN descripcion = '5 entidades o más con saldo - PPRE' THEN estado END) AS flg_5_entidades_o_m_s_con_saldo_ppre
,MAX(CASE WHEN descripcion = 'Incremento de Saldo SSF entre 1 a 3 mes' THEN estado END) AS flg_incremento_de_saldo_ssf_entre_1_a_3_mes
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta PPSE' THEN estado END) AS flg_oferta_3000_recalculo_oferta_ppse
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta PPRESESF' THEN estado END) AS flg_oferta_3000_recalculo_oferta_ppresesf
,MAX(CASE WHEN descripcion = 'OFERTA_LINEA_MENOR_MIN_UM' THEN estado END) AS flg_oferta_linea_menor_min_um
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta PPCSNB' THEN estado END) AS flg_oferta_3000_recalculo_oferta_ppcsnb
,MAX(CASE WHEN descripcion = 'Oferta CD No Cubre CD PP' THEN estado END) AS flg_oferta_cd_no_cubre_cd_pp
,MAX(CASE WHEN descripcion = 'Oferta CD No Cubre CD PP SE' THEN estado END) AS flg_oferta_cd_no_cubre_cd_pp_se
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta Colab PP' THEN estado END) AS flg_oferta_3000_recalculo_oferta_colab_pp
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC SE ROJO CDA' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_se_rojo_cda
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC FEVE EMP' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_feve_emp
,MAX(CASE WHEN descripcion = 'Incremental menor al minimo - Recalculo Oferta PPRE ISR' THEN estado END) AS flg_incremental_menor_al_minimo_recalculo_oferta_ppre_isr
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC No Bank G4' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_no_bank_g4
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC No Bank Informal Grifo' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_no_bank_informal_grifo
,MAX(CASE WHEN descripcion = 'Linea < 700 - Piloto pasivos 700 VC' THEN estado END) AS flg_linea_700_piloto_pasivos_700_vc
,MAX(CASE WHEN descripcion = 'Linea < 700 - TC NB informal G5' THEN estado END) AS flg_linea_700_tc_nb_informal_g5
,MAX(CASE WHEN descripcion = 'Linea < 700 - TC NB No Informal SUSALUD' THEN estado END) AS flg_linea_700_tc_nb_no_informal_susalud
,MAX(CASE WHEN descripcion = 'Linea < 700 - TC NB Informal Rechazo CL4CL5 Farmacia' THEN estado END) AS flg_linea_700_tc_nb_informal_rechazo_cl4cl5_farmacia
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC Indp Inf No Banc' THEN estado END) AS flg_linea_700_rescate_tc_indp_inf_no_banc
,MAX(CASE WHEN descripcion = 'Pago Minimo' THEN estado END) AS flg_pago_minimo
,MAX(CASE WHEN descripcion = 'Base Reingreso' THEN estado END) AS flg_base_reingreso
,MAX(CASE WHEN descripcion = 'Feve ibk' THEN estado END) AS flg_feve_ibk
,MAX(CASE WHEN descripcion = 'Feve Empresa' THEN estado END) AS flg_feve_empresa
,MAX(CASE WHEN descripcion = 'Trabajador SBS' THEN estado END) AS flg_trabajador_sbs
,MAX(CASE WHEN descripcion = 'Clientes Especiales R1 Ofac y R2 CC cerradas' THEN estado END) AS flg_clientes_especiales_r1_ofac_y_r2_cc_cerradas
,MAX(CASE WHEN descripcion = 'No Hit' THEN estado END) AS flg_no_hit
,MAX(CASE WHEN descripcion = 'Rechazo 6 Meses con buro bajo o muy bajo' THEN estado END) AS flg_rechazo_6_meses_con_buro_bajo_o_muy_bajo
,MAX(CASE WHEN descripcion = 'Zona Prestamo Roja o Vacia' THEN estado END) AS flg_zona_prestamo_roja_o_vacia
,MAX(CASE WHEN descripcion = 'Independiente menor a 25 años' THEN estado END) AS flg_independiente_menor_a_25_a_os
,MAX(CASE WHEN descripcion = 'Independiente Score Prestamos Bajo o Rechazo' THEN estado END) AS flg_independiente_score_prestamos_bajo_o_rechazo
,MAX(CASE WHEN descripcion = 'Renta Menor a 1000 y Buro Bajo o Muy Bajo o Rechazo' THEN estado END) AS flg_renta_menor_a_1000_y_buro_bajo_o_muy_bajo_o_rechazo
,MAX(CASE WHEN descripcion = 'Fenomeno del niño' THEN estado END) AS flg_fenomeno_del_ni_o
,MAX(CASE WHEN descripcion = 'Buro Bajo score prestamo medio flujo independient y bancarizado' THEN estado END) AS flg_buro_bajo_score_prestamo_medio_flujo_independient_y_bancarizado
,MAX(CASE WHEN descripcion = 'Prestamos con Garantia Hipotecaria IBK' THEN estado END) AS flg_prestamos_con_garantia_hipotecaria_ibk
,MAX(CASE WHEN descripcion = 'Saldo PP RCC Menor a 4 Meses' THEN estado END) AS flg_saldo_pp_rcc_menor_a_4_meses
,MAX(CASE WHEN descripcion = 'Saldo TC RCC Menor a 2 Meses' THEN estado END) AS flg_saldo_tc_rcc_menor_a_2_meses
,MAX(CASE WHEN descripcion = 'Flujo no bancarizado' THEN estado END) AS flg_flujo_no_bancarizado
,MAX(CASE WHEN descripcion = 'Mayor a 72' THEN estado END) AS flg_mayor_a_72
,MAX(CASE WHEN descripcion = 'RENTA_MENOR_1500' THEN estado END) AS flg_renta_menor_1500
,MAX(CASE WHEN descripcion = 'SOBREENDEUDADO_UM' THEN estado END) AS flg_sobreendeudado_um
,MAX(CASE WHEN descripcion = 'No usan la APP IBK' THEN estado END) AS flg_no_usan_la_app_ibk
,MAX(CASE WHEN descripcion = 'ORIG_TC_RECH' THEN estado END) AS flg_orig_tc_rech
,MAX(CASE WHEN descripcion = 'BANC_INDEP_BURO_B_SB_UM' THEN estado END) AS flg_banc_indep_buro_b_sb_um
,MAX(CASE WHEN descripcion = 'VENTA_CROSS_PP_UM' THEN estado END) AS flg_venta_cross_pp_um
,MAX(CASE WHEN descripcion = 'Zona PP 4 y 5 - Exclusion' THEN estado END) AS flg_zona_pp_4_y_5_exclusion
,MAX(CASE WHEN descripcion = 'Zona PPRE 4 y 5 - Exclusion' THEN estado END) AS flg_zona_ppre_4_y_5_exclusion
,MAX(CASE WHEN descripcion = 'BN_CLIENTES_ESPECIALES' THEN estado END) AS flg_bn_clientes_especiales
,MAX(CASE WHEN descripcion = 'Tiene Saldo Mancomuno' THEN estado END) AS flg_tiene_saldo_mancomuno
,MAX(CASE WHEN descripcion = 'Tope CEM/Ingreso' THEN estado END) AS flg_tope_cem_ingreso
,MAX(CASE WHEN descripcion = 'Antiguedad laboral menor 3M - CP NEI con campaña PP' THEN estado END) AS flg_antiguedad_laboral_menor_3m_cp_nei_con_campa_a_pp
,MAX(CASE WHEN descripcion = 'CLIENTE_BPE_UM' THEN estado END) AS flg_cliente_bpe_um
,MAX(CASE WHEN descripcion = 'Caida gys indep formal buro muy bajo sinburo' THEN estado END) AS flg_caida_gys_indep_formal_buro_muy_bajo_sinburo
,MAX(CASE WHEN descripcion = 'Caida gys nohit mixto dep score orig bajo' THEN estado END) AS flg_caida_gys_nohit_mixto_dep_score_orig_bajo
,MAX(CASE WHEN descripcion = 'Lambayeque dependiente score ori' THEN estado END) AS flg_lambayeque_dependiente_score_ori
,MAX(CASE WHEN descripcion = 'Lambayeque no hit ind formal score ori' THEN estado END) AS flg_lambayeque_no_hit_ind_formal_score_ori_2
,MAX(CASE WHEN descripcion = 'ANTICAMPANAS' THEN estado END) AS flg_anticampanas
,MAX(CASE WHEN descripcion = 'EMPRESA_NO_DESEADA' THEN estado END) AS flg_empresa_no_deseada
,MAX(CASE WHEN descripcion = 'Desembolsos 15D EC/CDD' THEN estado END) AS flg_desembolsos_15d_ec_cdd
,MAX(CASE WHEN descripcion = 'Piloto Convenios Sunat' THEN estado END) AS flg_piloto_convenios_sunat
,MAX(CASE WHEN descripcion = 'Recorte Independiente Buro Bajo' THEN estado END) AS flg_recorte_independiente_buro_bajo
,MAX(CASE WHEN descripcion = 'Recorte de independientes-zonas-ingresos' THEN estado END) AS flg_recorte_de_independientes_zonas_ingresos
,MAX(CASE WHEN descripcion = 'Recorte Desembolsos Exclusion U6M CDD/EC/PP' THEN estado END) AS flg_recorte_desembolsos_exclusion_u6m_cdd_ec_pp
,MAX(CASE WHEN descripcion = 'Recorte 5 entidades o más con saldo - PP' THEN estado END) AS flg_recorte_5_entidades_o_m_s_con_saldo_pp
,MAX(CASE WHEN descripcion = 'Recorte coyuntura FEN - PPRE' THEN estado END) AS flg_recorte_coyuntura_fen_ppre
,MAX(CASE WHEN descripcion = 'Recorte No Bancarizado segmento no cliente dependiente/independiente' THEN estado END) AS flg_recorte_no_bancarizado_segmento_no_cliente_dependiente_independiente
,MAX(CASE WHEN descripcion = 'ZONA NO PERMITA SEGUN SCORE COMPORTAMENTAL TC - PP' THEN estado END) AS flg_zona_no_permita_segun_score_comportamental_tc_pp
,MAX(CASE WHEN descripcion = 'Base Campaña TC/LIN_PEQUE' THEN estado END) AS flg_base_campa_a_tc_lin_peque
,MAX(CASE WHEN descripcion = 'EDAD_UM' THEN estado END) AS flg_edad_um
,MAX(CASE WHEN descripcion = 'Recorte G5, G6, G7, GR - TC SE' THEN estado END) AS flg_recorte_g5_g6_g7_gr_tc_se
,MAX(CASE WHEN descripcion = 'Recorte Rechazo Nuevo Sc PP Adm' THEN estado END) AS flg_recorte_rechazo_nuevo_sc_pp_adm
,MAX(CASE WHEN descripcion = 'Ratio Deuda/Ingreso > 50 - PP CD ROJO' THEN estado END) AS flg_ratio_deuda_ingreso_50_pp_cd_rojo
,MAX(CASE WHEN descripcion = 'RECORTE_INFORMAL_INDEP_BANC' THEN estado END) AS flg_recorte_informal_indep_banc
,MAX(CASE WHEN descripcion = '1ra llam Banc - Aprobo Buro Mancomuno' THEN estado END) AS flg_1ra_llam_banc_aprobo_buro_mancomuno
,MAX(CASE WHEN descripcion = 'CASTIGO_RCC_U24M' THEN estado END) AS flg_castigo_rcc_u24m
,MAX(CASE WHEN descripcion = 'REFINANCIADOS_RCC_TIENE_BURO_UM' THEN estado END) AS flg_refinanciados_rcc_tiene_buro_um
,MAX(CASE WHEN descripcion = '1ra llam Banc - No Tiene Buro Mayor 5 Bancos' THEN estado END) AS flg_1ra_llam_banc_no_tiene_buro_mayor_5_bancos
,MAX(CASE WHEN descripcion = '1ra llam Banc - No Bancarizado' THEN estado END) AS flg_1ra_llam_banc_no_bancarizado
,MAX(CASE WHEN descripcion = '1ra llam Banc - Aprobo Buro Mayor 7 Entidades' THEN estado END) AS flg_1ra_llam_banc_aprobo_buro_mayor_7_entidades
,MAX(CASE WHEN descripcion = '1ra llam Banc - Caida25' THEN estado END) AS flg_1ra_llam_banc_caida25
,MAX(CASE WHEN descripcion = 'EMPRESA_MALA_DUDOSO_PERD_UM' THEN estado END) AS flg_empresa_mala_dudoso_perd_um
,MAX(CASE WHEN descripcion = 'BN_CLIENTE_FEVE' THEN estado END) AS flg_bn_cliente_feve
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Caida 14' THEN estado END) AS flg_1ra_llam_no_banc_caida_14
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Caida 15' THEN estado END) AS flg_1ra_llam_no_banc_caida_15
,MAX(CASE WHEN descripcion = '1ra llam No Banc - Caida 25' THEN estado END) AS flg_1ra_llam_no_banc_caida_25
,MAX(CASE WHEN descripcion = '2da llam Banc - Sectorista Cobranza' THEN estado END) AS flg_2da_llam_banc_sectorista_cobranza
,MAX(CASE WHEN descripcion = 'RECH_ADQ_UM' THEN estado END) AS flg_rech_adq_um
,MAX(CASE WHEN descripcion = 'Mora TC mayor 30 dias' THEN estado END) AS flg_mora_tc_mayor_30_dias
,MAX(CASE WHEN descripcion = 'Renta menor a 1000' THEN estado END) AS flg_renta_menor_a_1000
,MAX(CASE WHEN descripcion = 'No DNI' THEN estado END) AS flg_no_dni
,MAX(CASE WHEN descripcion = 'Lambayeque dependiente score ori - Colaborador' THEN estado END) AS flg_lambayeque_dependiente_score_ori_colaborador
,MAX(CASE WHEN descripcion = 'Piura dependiente score ori - Colaborador' THEN estado END) AS flg_piura_dependiente_score_ori_colaborador
,MAX(CASE WHEN descripcion = 'Edad menor 21 o mayor a 72' THEN estado END) AS flg_edad_menor_21_o_mayor_a_72
,MAX(CASE WHEN descripcion = 'Base Campaña TC/C_DOBLE/LIN_PEQUE' THEN estado END) AS flg_base_campa_a_tc_c_doble_lin_peque
,MAX(CASE WHEN descripcion = 'Mayor a Normal UM' THEN estado END) AS flg_mayor_a_normal_um
,MAX(CASE WHEN descripcion = 'Mayor a 7 Entidades' THEN estado END) AS flg_mayor_a_7_entidades
,MAX(CASE WHEN descripcion = 'Deuda Vencida UM' THEN estado END) AS flg_deuda_vencida_um
,MAX(CASE WHEN descripcion = 'Saldo Refinanciado IBK y/o SSFF Reportado último mes' THEN estado END) AS flg_saldo_refinanciado_ibk_y_o_ssff_reportado_ltimo_mes
,MAX(CASE WHEN descripcion = 'Moneda extranjera' THEN estado END) AS flg_moneda_extranjera
,MAX(CASE WHEN descripcion = 'Amortizacion minima' THEN estado END) AS flg_amortizacion_minima
,MAX(CASE WHEN descripcion = 'Prestamo Express (3401)' THEN estado END) AS flg_prestamo_express_3401_
,MAX(CASE WHEN descripcion = 'Recorte Cluster 3 de EC - PPRE' THEN estado END) AS flg_recorte_cluster_3_de_ec_ppre
,MAX(CASE WHEN descripcion = 'Deuda/Ingreso > 25' THEN estado END) AS flg_deuda_ingreso_25
,MAX(CASE WHEN descripcion = 'Incremento de Saldo No Revolvente entre 1 a 3 mes' THEN estado END) AS flg_incremento_de_saldo_no_revolvente_entre_1_a_3_mes
,MAX(CASE WHEN descripcion = 'Deuda/Ingreso > 30' THEN estado END) AS flg_deuda_ingreso_30
,MAX(CASE WHEN descripcion = 'Clientes ISR con saldo hipotecario IBK' THEN estado END) AS flg_clientes_isr_con_saldo_hipotecario_ibk
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta PPRE' THEN estado END) AS flg_oferta_3000_recalculo_oferta_ppre_2
,MAX(CASE WHEN descripcion = 'Incremental menor al minimo - Recalculo Oferta PPRESESF' THEN estado END) AS flg_incremental_menor_al_minimo_recalculo_oferta_ppresesf
,MAX(CASE WHEN descripcion = 'Oferta < 3000 - Recalculo Oferta Colab PP CP' THEN estado END) AS flg_oferta_3000_recalculo_oferta_colab_pp_cp
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC SE' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_se
,MAX(CASE WHEN descripcion = 'Oferta CD No Cubre CD PP - CD ROJO' THEN estado END) AS flg_oferta_cd_no_cubre_cd_pp_cd_rojo
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC Telefonica' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_telefonica
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC No Bank Informal Debito' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_no_bank_informal_debito
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC No Bank Informal ITC Retail' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_no_bank_informal_itc_retail
,MAX(CASE WHEN descripcion = 'Linea < 700 - Recalculo Oferta TC EMP MALA' THEN estado END) AS flg_linea_700_recalculo_oferta_tc_emp_mala
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC CMP EST IND BB_SB' THEN estado END) AS flg_linea_700_rescate_tc_cmp_est_ind_bb_sb
,MAX(CASE WHEN descripcion = 'Linea < 700 - Piloto pasivos 700 no bank' THEN estado END) AS flg_linea_700_piloto_pasivos_700_no_bank
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC Exclusion NB' THEN estado END) AS flg_linea_700_rescate_tc_exclusion_nb
,MAX(CASE WHEN descripcion = 'Linea < 700 - TC NB informal SUSALUD' THEN estado END) AS flg_linea_700_tc_nb_informal_susalud
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC Indp Banc' THEN estado END) AS flg_linea_700_rescate_tc_indp_banc
,MAX(CASE WHEN descripcion = 'Linea < 700 - Rescate TC Cuenta Sueldo Cross Sell' THEN estado END) AS flg_linea_700_rescate_tc_cuenta_sueldo_cross_sell
    FROM caidas
    GROUP BY subject_id
)
-- =========================================================================
-- 3) FEATURE INCA (party_id -> key_value via base_cliente, con desfase -1 mes)
-- =========================================================================
, inca_rf AS (
    SELECT
        bc.tip_doc   AS cod_tip_doc,
        bc.key_value AS key_value,
        date_format(date_parse(CAST(inca.process_date AS VARCHAR), '%Y%m'), '%Y%m') AS cod_mes_join,
        MAX(inca.flg_far_mto_trx_presencial_12m_c216) AS flg_far_mto_trx_presencial_12m_c216
    FROM e_perm_aws.t_inca_rf inca
    JOIN e_perm_aws.t_mst_inter_ibk_base_cliente bc
      ON CAST(inca.party_id AS VARCHAR) = CAST(bc.inter_party_id AS VARCHAR)
    GROUP BY
        bc.tip_doc, bc.key_value,
        date_format(date_parse(CAST(inca.process_date AS VARCHAR), '%Y%m'), '%Y%m')
)
-- =========================================================================
-- 3b) MS_VAR: mejor modelo por puntaje (mira TODOS los modelos del cliente)
-- =========================================================================
, ms_var AS (
    SELECT key_value, tipdoc,
           MAX(puntaje)                AS puntaje_var,
           max_by(nom_modelo, puntaje) AS nom_modelo_var
    FROM awsdatacatalog.e_perm_aws.t_rsk_maestro_score
    WHERE periodo = '202605'                                     -- @CODMES_MODELO
    GROUP BY key_value, tipdoc
)
-- =========================================================================
-- 3c) MS_3M: historia de los 3 meses PREVIOS al modelo (202604, 202603, 202602)
-- =========================================================================
, ms_3m_mes AS (
    SELECT key_value, tipdoc, periodo,
           MAX(CASE WHEN nom_modelo IN ('Score Originación TC No Bank 2024','Score Originación TC Bank 2024') THEN puntaje END)         AS pmod,
           max_by(nom_modelo, CASE WHEN nom_modelo IN ('Score Originación TC No Bank 2024','Score Originación TC Bank 2024') THEN puntaje END) AS nmod,
           MAX(puntaje)                AS pvar,
           max_by(nom_modelo, puntaje) AS nvar
    FROM awsdatacatalog.e_perm_aws.t_rsk_maestro_score
    WHERE periodo IN ('202604','202603','202602')                -- @MESES_3M
    GROUP BY key_value, tipdoc, periodo
)
, ms_3m AS (
    SELECT key_value, tipdoc,
           MAX(CASE WHEN periodo='202604' THEN pmod END) AS pmod_202604,
           MAX(CASE WHEN periodo='202603' THEN pmod END) AS pmod_202603,
           MAX(CASE WHEN periodo='202602' THEN pmod END) AS pmod_202602,
           MAX(CASE WHEN periodo='202604' THEN nmod END) AS nmod_202604,
           MAX(CASE WHEN periodo='202603' THEN nmod END) AS nmod_202603,
           MAX(CASE WHEN periodo='202602' THEN nmod END) AS nmod_202602,
           MAX(CASE WHEN periodo='202604' THEN pvar END) AS pvar_202604,
           MAX(CASE WHEN periodo='202603' THEN pvar END) AS pvar_202603,
           MAX(CASE WHEN periodo='202602' THEN pvar END) AS pvar_202602,
           MAX(CASE WHEN periodo='202604' THEN nvar END) AS nvar_202604,
           MAX(CASE WHEN periodo='202603' THEN nvar END) AS nvar_202603,
           MAX(CASE WHEN periodo='202602' THEN nvar END) AS nvar_202602,
           MIN(pmod)          AS min_puntaje_mod_3m,
           min_by(nmod, pmod) AS nom_mod_3m,
           MIN(pvar)          AS min_puntaje_var_3m,
           min_by(nvar, pvar) AS nom_mod_var_3m
    FROM ms_3m_mes
    GROUP BY key_value, tipdoc
)
-- =========================================================================
-- 5) VARIABLES t_360_cliente: saldos (UM/U3M/U6M), flags (0/1/null) y ratios
--    + entidades castigo (U24M) + principalidad.
-- =========================================================================
, t360_base AS (                            -- foto U6M de t_360 (frecuencia mensual)
    SELECT
        cast(cod_tipo_documento as varchar) AS cod_tipo_documento,
        nro_documento,
        codunicocli,
        cod_mes,
        saldo_fdp_tot_txs,       saldo_prom_tot_txs,
        saldo_fdp_tot_planilla,  saldo_prom_tot_planilla,
        saldo_fdp_tot_tc,        saldo_prom_tot_tc,
        saldo_prom_tot_pasivo,
        flg_colaborador,             flg_cliente_cts,            flg_cliente_inversion,
        flg_cliente_millonaria,      flg_cliente_alcancia,       flg_cliente_planilla,
        flg_cliente_planilla_act_sal,flg_cliente_planilla_abon,  flg_cliente_planilla_depo,
        flg_cliente_plazo_fijo
    FROM AwsDataCatalog.e_perm_aws.t_360_cliente
    WHERE frecuencia = 1
      AND cod_mes IN ('202606','202605','202604','202603','202602','202601')  -- @U6M (anclaje 202606)
)
, t360_feats AS (
    SELECT
        cod_tipo_documento,
        nro_documento,
        max(codunicocli) AS codunicocli,
        -- ===================== SALDOS: UM / prom U3M / prom U6M =====================
        max(case when cod_mes='202606' then saldo_fdp_tot_txs end)                              AS saldo_fdp_tot_txs_um,
        avg(case when cod_mes in ('202606','202605','202604') then saldo_fdp_tot_txs end)       AS saldo_fdp_tot_txs_u3m,
        avg(saldo_fdp_tot_txs)                                                                  AS saldo_fdp_tot_txs_u6m,
        max(case when cod_mes='202606' then saldo_prom_tot_txs end)                             AS saldo_prom_tot_txs_um,
        avg(case when cod_mes in ('202606','202605','202604') then saldo_prom_tot_txs end)      AS saldo_prom_tot_txs_u3m,
        avg(saldo_prom_tot_txs)                                                                 AS saldo_prom_tot_txs_u6m,
        max(case when cod_mes='202606' then saldo_fdp_tot_planilla end)                         AS saldo_fdp_tot_planilla_um,
        avg(case when cod_mes in ('202606','202605','202604') then saldo_fdp_tot_planilla end)  AS saldo_fdp_tot_planilla_u3m,
        avg(saldo_fdp_tot_planilla)                                                             AS saldo_fdp_tot_planilla_u6m,
        max(case when cod_mes='202606' then saldo_prom_tot_planilla end)                        AS saldo_prom_tot_planilla_um,
        avg(case when cod_mes in ('202606','202605','202604') then saldo_prom_tot_planilla end) AS saldo_prom_tot_planilla_u3m,
        avg(saldo_prom_tot_planilla)                                                            AS saldo_prom_tot_planilla_u6m,
        max(case when cod_mes='202606' then saldo_fdp_tot_tc end)                               AS saldo_fdp_tot_tc_um,
        avg(case when cod_mes in ('202606','202605','202604') then saldo_fdp_tot_tc end)        AS saldo_fdp_tot_tc_u3m,
        avg(saldo_fdp_tot_tc)                                                                   AS saldo_fdp_tot_tc_u6m,
        max(case when cod_mes='202606' then saldo_prom_tot_tc end)                              AS saldo_prom_tot_tc_um,
        avg(case when cod_mes in ('202606','202605','202604') then saldo_prom_tot_tc end)       AS saldo_prom_tot_tc_u3m,
        avg(saldo_prom_tot_tc)                                                                  AS saldo_prom_tot_tc_u6m,
        max(case when cod_mes='202606' then saldo_prom_tot_pasivo end)                          AS saldo_prom_tot_pasivo_um,
        avg(case when cod_mes in ('202606','202605','202604') then saldo_prom_tot_pasivo end)   AS saldo_prom_tot_pasivo_u3m,
        avg(saldo_prom_tot_pasivo)                                                              AS saldo_prom_tot_pasivo_u6m,
        max(saldo_prom_tot_pasivo)                                                              AS saldo_prom_tot_pasivo_max_u6m,
        -- ===================== FLAGS (0/1/null): último mes + tuvo en U6M =====================
        max(case when cod_mes='202606' then flg_colaborador end)                          AS flg_colaborador_um,
        max(case when cast(flg_colaborador as varchar)='1' then 1 else 0 end)             AS flg_colaborador_u6m,
        max(case when cod_mes='202606' then flg_cliente_cts end)                          AS flg_cliente_cts_um,
        max(case when cast(flg_cliente_cts as varchar)='1' then 1 else 0 end)             AS flg_cliente_cts_u6m,
        max(case when cod_mes='202606' then flg_cliente_inversion end)                    AS flg_cliente_inversion_um,
        max(case when cast(flg_cliente_inversion as varchar)='1' then 1 else 0 end)       AS flg_cliente_inversion_u6m,
        max(case when cod_mes='202606' then flg_cliente_millonaria end)                   AS flg_cliente_millonaria_um,
        max(case when cast(flg_cliente_millonaria as varchar)='1' then 1 else 0 end)      AS flg_cliente_millonaria_u6m,
        max(case when cod_mes='202606' then flg_cliente_alcancia end)                     AS flg_cliente_alcancia_um,
        max(case when cast(flg_cliente_alcancia as varchar)='1' then 1 else 0 end)        AS flg_cliente_alcancia_u6m,
        max(case when cod_mes='202606' then flg_cliente_planilla end)                     AS flg_cliente_planilla_um,
        max(case when cast(flg_cliente_planilla as varchar)='1' then 1 else 0 end)        AS flg_cliente_planilla_u6m,
        max(case when cod_mes='202606' then flg_cliente_planilla_act_sal end)             AS flg_cliente_planilla_act_sal_um,
        max(case when cast(flg_cliente_planilla_act_sal as varchar)='1' then 1 else 0 end) AS flg_cliente_planilla_act_sal_u6m,
        max(case when cod_mes='202606' then flg_cliente_planilla_abon end)                AS flg_cliente_planilla_abon_um,
        max(case when cast(flg_cliente_planilla_abon as varchar)='1' then 1 else 0 end)   AS flg_cliente_planilla_abon_u6m,
        max(case when cod_mes='202606' then flg_cliente_planilla_depo end)                AS flg_cliente_planilla_depo_um,
        max(case when cast(flg_cliente_planilla_depo as varchar)='1' then 1 else 0 end)   AS flg_cliente_planilla_depo_u6m,
        max(case when cod_mes='202606' then flg_cliente_plazo_fijo end)                   AS flg_cliente_plazo_fijo_um,
        max(case when cast(flg_cliente_plazo_fijo as varchar)='1' then 1 else 0 end)      AS flg_cliente_plazo_fijo_u6m
    FROM t360_base
    GROUP BY cod_tipo_documento, nro_documento
)
, t360_final AS (
    SELECT
        f.*,
        (f.saldo_prom_tot_planilla_u3m + f.saldo_prom_tot_txs_u3m + f.saldo_prom_tot_tc_u3m)            AS saldo_pasivo_componentes_u3m,
        f.saldo_prom_tot_tc_u3m       / nullif(f.saldo_prom_tot_pasivo_u3m, 0)                          AS ratio_tc_pasivo_u3m,
        f.saldo_prom_tot_planilla_u3m / nullif(f.saldo_prom_tot_pasivo_u3m, 0)                          AS ratio_planilla_pasivo_u3m,
        f.saldo_prom_tot_txs_u3m      / nullif(f.saldo_prom_tot_pasivo_u3m, 0)                          AS ratio_txs_pasivo_u3m,
        (f.saldo_prom_tot_pasivo_um - f.saldo_prom_tot_pasivo_u6m) / nullif(f.saldo_prom_tot_pasivo_u6m, 0) AS var_pasivo_um_vs_u6m,
        case when f.saldo_prom_tot_pasivo_u6m > 0 then 1 else 0 end                                     AS flg_tiene_pasivo_u6m,
        pr.motivo_principalidad
    FROM t360_feats f
    LEFT JOIN (
        SELECT DISTINCT codunicocli, motivo_principalidad
        FROM AwsDataCatalog.e_perm_aws.t_nds_principalidad
        WHERE fch_periodo = date '2026-06-30'          -- @FCH_PRINCIPALIDAD (anclaje 202606)
    ) pr ON f.codunicocli = pr.codunicocli
)
, variables_rcc AS (                        -- nro_entidades y tipo_entidad de castigo (U24M)
    SELECT
        r.key_value,
        r.tip_doc,
        count(distinct
            case when substring(r.cod_cuenta_rcc,1,2) = '81'
                  and substring(r.cod_cuenta_rcc,4,3) in ('302','925')
                  and (r.tipo_credito in ('11','12','13') or r.tipo_credito = '99')
                  and r.codmes >= '202403'                       -- @VENTANA_24M
                 then r.cod_instit_financiera end
        )                                                                  AS nro_entidades_castigo_vida,
        case when max(case when r.cod_instit_financiera in ('00001','00002','00004','00006')
                            and substring(r.cod_cuenta_rcc,1,2) = '81'
                            and substring(r.cod_cuenta_rcc,4,3) in ('302','925')
                            and (r.tipo_credito in ('11','12','13') or r.tipo_credito = '99')
                            and r.codmes >= '202403'             -- @VENTANA_24M
                           then 1 else 0 end) = 1 then 'BIG FOUR'
             else 'OTROS' end                                              AS tipo_entidad_castigo_vida
    FROM AwsDataCatalog.e_perm_aws.t_fact_report_rcc_rsk r
    INNER JOIN (
        SELECT DISTINCT split_part(subject_id,'-',1) AS tip_doc,
                        substring(subject_id,3)       AS key_value
        FROM PEA
    ) pea_k ON r.tip_doc = pea_k.tip_doc AND r.key_value = pea_k.key_value
    WHERE r.codmes <= '202603'                                   -- @CODMES_RCC_VIDA
    GROUP BY r.key_value, r.tip_doc
)
-- =========================================================================
-- 6) RM_CLIENTE (sexo, estado_civil) y PROFESIONES (nivel_profesional, tipinstitucion)
-- =========================================================================
, rm_cliente AS (
    SELECT cast(tipdoc as varchar) AS tipdoc, key_value,
           max(sexo) AS sexo, max(estado_civil) AS estado_civil
    FROM AwsDataCatalog.e_perm_aws.t_rm_cliente
    WHERE fecproceso = '20260616'                                -- @FECHA_PEA (= p_fecinformacion)
    GROUP BY cast(tipdoc as varchar), key_value
)
, profesiones AS (
    SELECT cast(tipdoc as varchar) AS tipdoc, key_value,
           max(nivel_profesional) AS nivel_profesional, max(tipinstitucion) AS tipinstitucion
    FROM AwsDataCatalog.e_perm_aws.t_profesiones_hist
    WHERE codmes = '202603'                                      -- @CODMES_PROF
    GROUP BY cast(tipdoc as varchar), key_value
)
-- =========================================================================
-- 4) SELECT FINAL
-- =========================================================================
SELECT
    base.*,
    ms.concepto_nivel AS GRUPO_SCORE,
    ms.segmentacion_gdp,
    ms.nom_modelo,
    ms.sit_laboral    as sit_laboral_mod,
    ms.fuente_ingreso as fuente_ingreso_mod,
    ms.puntaje        as puntaje_mod,
    ir.flg_far_mto_trx_presencial_12m_c216,
    oa.trf_tip_segmentacion_gdp,
    sg.segmentacion_gdp as segmentacion_gdp_v2,
    mv.puntaje_var,
    mv.nom_modelo_var,
    m3.pmod_202604, m3.pmod_202603, m3.pmod_202602,
    m3.nmod_202604, m3.nmod_202603, m3.nmod_202602,
    m3.pvar_202604, m3.pvar_202603, m3.pvar_202602,
    m3.nvar_202604, m3.nvar_202603, m3.nvar_202602,
    m3.min_puntaje_mod_3m, m3.nom_mod_3m,
    m3.min_puntaje_var_3m, m3.nom_mod_var_3m,
    -- ===== t_360: saldos (UM / U3M / U6M) =====
    t3.saldo_fdp_tot_txs_um,        t3.saldo_fdp_tot_txs_u3m,        t3.saldo_fdp_tot_txs_u6m,
    t3.saldo_prom_tot_txs_um,       t3.saldo_prom_tot_txs_u3m,       t3.saldo_prom_tot_txs_u6m,
    t3.saldo_fdp_tot_planilla_um,   t3.saldo_fdp_tot_planilla_u3m,   t3.saldo_fdp_tot_planilla_u6m,
    t3.saldo_prom_tot_planilla_um,  t3.saldo_prom_tot_planilla_u3m,  t3.saldo_prom_tot_planilla_u6m,
    t3.saldo_fdp_tot_tc_um,         t3.saldo_fdp_tot_tc_u3m,         t3.saldo_fdp_tot_tc_u6m,
    t3.saldo_prom_tot_tc_um,        t3.saldo_prom_tot_tc_u3m,        t3.saldo_prom_tot_tc_u6m,
    t3.saldo_prom_tot_pasivo_um,    t3.saldo_prom_tot_pasivo_u3m,    t3.saldo_prom_tot_pasivo_u6m, t3.saldo_prom_tot_pasivo_max_u6m,
    -- ===== t_360: flags (UM + U6M) =====
    t3.flg_colaborador_um,              t3.flg_colaborador_u6m,
    t3.flg_cliente_cts_um,              t3.flg_cliente_cts_u6m,
    t3.flg_cliente_inversion_um,        t3.flg_cliente_inversion_u6m,
    t3.flg_cliente_millonaria_um,       t3.flg_cliente_millonaria_u6m,
    t3.flg_cliente_alcancia_um,         t3.flg_cliente_alcancia_u6m,
    t3.flg_cliente_planilla_um,         t3.flg_cliente_planilla_u6m,
    t3.flg_cliente_planilla_act_sal_um, t3.flg_cliente_planilla_act_sal_u6m,
    t3.flg_cliente_planilla_abon_um,    t3.flg_cliente_planilla_abon_u6m,
    t3.flg_cliente_planilla_depo_um,    t3.flg_cliente_planilla_depo_u6m,
    t3.flg_cliente_plazo_fijo_um,       t3.flg_cliente_plazo_fijo_u6m,
    -- ===== ratios / derivados =====
    t3.saldo_pasivo_componentes_u3m,
    t3.ratio_tc_pasivo_u3m, t3.ratio_planilla_pasivo_u3m, t3.ratio_txs_pasivo_u3m,
    t3.var_pasivo_um_vs_u6m, t3.flg_tiene_pasivo_u6m,
    t3.motivo_principalidad,
    -- ===== castigo (entidades) =====
    coalesce(vr.nro_entidades_castigo_vida, 0)            AS nro_entidades_castigo_vida,
    coalesce(vr.tipo_entidad_castigo_vida, 'SIN CASTIGO') AS tipo_entidad_castigo_vida,
    -- ===== rm_cliente + profesiones =====
    rmc.sexo,
    rmc.estado_civil,
    prof.nivel_profesional,
    prof.tipinstitucion
FROM (
    SELECT *
    FROM base_pea m
    LEFT JOIN pivot p USING (subject_id)
) base
LEFT JOIN awsdatacatalog.e_perm_aws.t_rsk_maestro_score ms
       ON ms.periodo    = '202605'                                  -- @CODMES_MODELO
      AND ms.key_value  = base.key_value
      AND ms.tipdoc     = base.cod_tip_doc
      AND ms.nom_modelo IN ('Score Originación TC No Bank 2024','Score Originación TC Bank 2024')
LEFT JOIN inca_rf ir
       ON ir.key_value    = base.key_value
      AND ir.cod_tip_doc  = base.cod_tip_doc
      AND ir.cod_mes_join = '202604'                              -- @CODMES_INCA
LEFT JOIN awsdatacatalog.e_perm_aws.scr_origenapp1_rsk oa
       ON oa.cod_mes      = base.codmes_pea
      AND oa.cod_tip_doc  = base.cod_tip_doc
      AND oa.key_value    = base.key_value
LEFT JOIN awsdatacatalog.e_perm_aws.t_rsk_segmentacion_gdp sg
       ON sg.codmes     = '202603'                                  -- @CODMES_SEG_GDP
      AND sg.key_value  = base.key_value
      AND sg.tipdoc     = base.cod_tip_doc
LEFT JOIN ms_var mv
       ON mv.key_value  = base.key_value
      AND mv.tipdoc     = base.cod_tip_doc
LEFT JOIN ms_3m m3
       ON m3.key_value  = base.key_value
      AND m3.tipdoc     = base.cod_tip_doc
LEFT JOIN t360_final t3
       ON t3.cod_tipo_documento = base.cod_tip_doc
      AND t3.nro_documento      = base.key_value
LEFT JOIN variables_rcc vr
       ON vr.tip_doc   = base.cod_tip_doc
      AND vr.key_value = base.key_value
LEFT JOIN rm_cliente rmc
       ON rmc.tipdoc    = base.cod_tip_doc
      AND rmc.key_value = base.key_value
LEFT JOIN profesiones prof
       ON prof.tipdoc    = base.cod_tip_doc
      AND prof.key_value = base.key_value
;
