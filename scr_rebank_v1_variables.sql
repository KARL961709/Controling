-- =========================================================================
-- VARIABLES PARA disc_riesgos.scr_rebank_v1  (llave: key_value, codmes_ejec)
-- =========================================================================
-- AUTOMATIZABLE: codmes_ejec puede tener varios valores (YYYYMM). Todos los
-- periodos de las fuentes se calculan RELATIVOS a codmes_ejec con los MISMOS
-- desfases del query original PEA:
--   t_360 / principalidad / PEA / rm_cliente .... mismo mes (codmes_ejec)   [desfase 0]
--   maestro_score (puntaje_mod) ................. codmes_ejec - 1
--   RCC castigo (montos/deuda/mora) ............. codmes_ejec - 2  (ventana 24m)
--   INCA (flg_far_...) .......................... codmes_ejec - 2
--   segmentacion_gdp / profesiones .............. codmes_ejec - 3
--   castigo "vida" (entidades) .................. ventana [codmes_ejec-27, codmes_ejec-3]
-- Join SOLO por key_value (scr_rebank_v1 no tiene tipo de documento): cada
-- CTE se agrega por key_value para evitar fan-out.
-- Ventanas t_360 (ancladas en codmes_ejec): UM=mes; U3M=[-2,0]; U4M=[-3,0]; U6M=[-5,0]
-- =========================================================================
-- Para materializar:  CREATE TABLE <destino> WITH (...) AS  <este SELECT>
-- =========================================================================
WITH base AS (
    SELECT DISTINCT
        CAST(key_value   AS VARCHAR) AS key_value,
        CAST(codmes_ejec AS VARCHAR) AS codmes_ejec
    FROM disc_riesgos.scr_rebank_v1
)
, anchors AS (   -- todos los periodos derivados de codmes_ejec
    SELECT
        key_value,
        codmes_ejec,
        date_format(date_add('month', -1, dt), '%Y%m') AS m_modelo,   -- maestro_score
        date_format(date_add('month', -2, dt), '%Y%m') AS m_rcc,      -- castigo "actual"
        date_format(date_add('month', -2, dt), '%Y%m') AS m_inca,     -- inca
        date_format(date_add('month', -3, dt), '%Y%m') AS m_seg,      -- segmentacion
        date_format(date_add('month', -3, dt), '%Y%m') AS m_prof,     -- profesiones
        date_format(date_add('month', -2, dt), '%Y%m') AS lo_u3m,     -- t_360 U3M start
        date_format(date_add('month', -3, dt), '%Y%m') AS lo_u4m,     -- t_360 U4M start
        date_format(date_add('month', -5, dt), '%Y%m') AS lo_u6m,     -- t_360 U6M start
        date_add('day', -1, date_add('month', 1, dt))  AS fch_princ,  -- ultimo dia del mes (principalidad)
        date_format(date_add('month', -3,  dt), '%Y%m') AS vida_hi,   -- castigo vida corte (=ejec-3)
        date_format(date_add('month', -27, dt), '%Y%m') AS vida_lo,   -- castigo vida inicio (24m)
        date_format(date_add('month', -2,  dt), '%Y%m') AS rccnum_hi, -- = m_rcc
        date_format(date_add('month', -25, dt), '%Y%m') AS rccnum_lo, -- m_rcc - 23
        date_format(date_add('month', -3,  dt), '%Y%m') AS rccd_hi,   -- m_rcc - 1 (ventana u24m ibk/noibk)
        date_format(date_add('month', -25, dt), '%Y%m') AS rccd_lo    -- m_rcc - 23
    FROM (
        SELECT key_value, codmes_ejec,
               date_parse(codmes_ejec || '01', '%Y%m%d') AS dt
        FROM base
    )
)
-- ------------------------------------------------------------------ PEA
, pea_feats AS (   -- sit_lab_ap, edad_num, rk_ing_num  (periodo = codmes_ejec)
    SELECT
        split_part(CAST(subject_id AS VARCHAR), '-', 2) AS key_value,
        CAST(periodo AS VARCHAR)                         AS codmes_ejec,
        MAX(sit_lab_ap) AS sit_lab_ap,
        MAX(edad)       AS edad_num,
        MAX(renta)      AS rk_ing_num
    FROM awsdatacatalog.e_perm_aws.ds_rtd_rskvol_indicadores_pea
    GROUP BY split_part(CAST(subject_id AS VARCHAR), '-', 2), CAST(periodo AS VARCHAR)
)
-- ------------------------------------------------------------ MAESTRO SCORE
, modelo AS (   -- puntaje_mod  (periodo = codmes_ejec - 1)
    SELECT
        CAST(key_value AS VARCHAR) AS key_value,
        CAST(periodo   AS VARCHAR) AS periodo,
        MAX(puntaje)               AS puntaje_mod
    FROM awsdatacatalog.e_perm_aws.t_rsk_maestro_score
    WHERE nom_modelo IN ('Score Originación TC No Bank 2024','Score Originación TC Bank 2024')
    GROUP BY CAST(key_value AS VARCHAR), CAST(periodo AS VARCHAR)
)
-- ------------------------------------------------------------------ INCA
, inca AS (   -- flg_far_mto_trx_presencial_12m_c216  (cod_mes_join = codmes_ejec - 2)
    SELECT
        bc.key_value AS key_value,
        date_format(date_parse(CAST(i.process_date AS VARCHAR), '%Y%m'), '%Y%m') AS cod_mes_join,
        MAX(i.flg_far_mto_trx_presencial_12m_c216) AS flg_far_mto_trx_presencial_12m_c216
    FROM awsdatacatalog.e_perm_aws.t_inca_rf i
    JOIN awsdatacatalog.e_perm_aws.t_mst_inter_ibk_base_cliente bc
      ON CAST(i.party_id AS VARCHAR) = CAST(bc.inter_party_id AS VARCHAR)
    GROUP BY bc.key_value, date_format(date_parse(CAST(i.process_date AS VARCHAR), '%Y%m'), '%Y%m')
)
-- --------------------------------------------------------- SEGMENTACION GDP
, seg AS (   -- segmentacion_gdp_v2  (codmes = codmes_ejec - 3)
    SELECT
        CAST(key_value AS VARCHAR) AS key_value,
        CAST(codmes    AS VARCHAR) AS codmes,
        MAX(segmentacion_gdp)      AS segmentacion_gdp_v2
    FROM awsdatacatalog.e_perm_aws.t_rsk_segmentacion_gdp
    GROUP BY CAST(key_value AS VARCHAR), CAST(codmes AS VARCHAR)
)
-- -------------------------------------------------------------- PROFESIONES
, prof AS (   -- nivel_profesional, tipinstitucion  (codmes = codmes_ejec - 3)
    SELECT
        CAST(key_value AS VARCHAR) AS key_value,
        CAST(codmes    AS VARCHAR) AS codmes,
        MAX(nivel_profesional) AS nivel_profesional,
        MAX(tipinstitucion)    AS tipinstitucion
    FROM awsdatacatalog.e_perm_aws.t_profesiones_hist
    GROUP BY CAST(key_value AS VARCHAR), CAST(codmes AS VARCHAR)
)
-- ----------------------------------------------------------------- T_360
, t360 AS (   -- saldos txs/planilla/tc/pasivo (UM/U3M/U6M), flags _um, pasivo actual/u4m
    SELECT
        a.key_value, a.codmes_ejec, a.fch_princ,
        MAX(t.codunicocli) AS codunicocli,
        -- TXS
        MAX(CASE WHEN t.ym = a.codmes_ejec                  THEN t.saldo_fdp_tot_txs END)        AS saldo_fdp_tot_txs_um,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u3m AND a.codmes_ejec THEN t.saldo_fdp_tot_txs END)       AS saldo_fdp_tot_txs_u3m,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u6m AND a.codmes_ejec THEN t.saldo_fdp_tot_txs END)       AS saldo_fdp_tot_txs_u6m,
        MAX(CASE WHEN t.ym = a.codmes_ejec                  THEN t.saldo_prom_tot_txs END)       AS saldo_prom_tot_txs_um,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u3m AND a.codmes_ejec THEN t.saldo_prom_tot_txs END)      AS saldo_prom_tot_txs_u3m,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u6m AND a.codmes_ejec THEN t.saldo_prom_tot_txs END)      AS saldo_prom_tot_txs_u6m,
        -- PLANILLA
        MAX(CASE WHEN t.ym = a.codmes_ejec                  THEN t.saldo_fdp_tot_planilla END)   AS saldo_fdp_tot_planilla_um,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u3m AND a.codmes_ejec THEN t.saldo_fdp_tot_planilla END)  AS saldo_fdp_tot_planilla_u3m,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u6m AND a.codmes_ejec THEN t.saldo_fdp_tot_planilla END)  AS saldo_fdp_tot_planilla_u6m,
        MAX(CASE WHEN t.ym = a.codmes_ejec                  THEN t.saldo_prom_tot_planilla END)  AS saldo_prom_tot_planilla_um,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u3m AND a.codmes_ejec THEN t.saldo_prom_tot_planilla END) AS saldo_prom_tot_planilla_u3m,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u6m AND a.codmes_ejec THEN t.saldo_prom_tot_planilla END) AS saldo_prom_tot_planilla_u6m,
        -- TC
        MAX(CASE WHEN t.ym = a.codmes_ejec                  THEN t.saldo_fdp_tot_tc END)         AS saldo_fdp_tot_tc_um,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u3m AND a.codmes_ejec THEN t.saldo_fdp_tot_tc END)        AS saldo_fdp_tot_tc_u3m,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u6m AND a.codmes_ejec THEN t.saldo_fdp_tot_tc END)        AS saldo_fdp_tot_tc_u6m,
        MAX(CASE WHEN t.ym = a.codmes_ejec                  THEN t.saldo_prom_tot_tc END)        AS saldo_prom_tot_tc_um,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u3m AND a.codmes_ejec THEN t.saldo_prom_tot_tc END)       AS saldo_prom_tot_tc_u3m,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u6m AND a.codmes_ejec THEN t.saldo_prom_tot_tc END)       AS saldo_prom_tot_tc_u6m,
        -- PASIVO (promedio)
        MAX(CASE WHEN t.ym = a.codmes_ejec                  THEN t.saldo_prom_tot_pasivo END)    AS saldo_prom_tot_pasivo_um,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u3m AND a.codmes_ejec THEN t.saldo_prom_tot_pasivo END)   AS saldo_prom_tot_pasivo_u3m,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u6m AND a.codmes_ejec THEN t.saldo_prom_tot_pasivo END)   AS saldo_prom_tot_pasivo_u6m,
        MAX(CASE WHEN t.ym BETWEEN a.lo_u6m AND a.codmes_ejec THEN t.saldo_prom_tot_pasivo END)   AS saldo_prom_tot_pasivo_max_u6m,
        -- FLAGS (valor ultimo mes, 0/1/null)
        MAX(CASE WHEN t.ym = a.codmes_ejec THEN t.flg_colaborador END)        AS flg_colaborador_um,
        MAX(CASE WHEN t.ym = a.codmes_ejec THEN t.flg_cliente_cts END)        AS flg_cliente_cts_um,
        MAX(CASE WHEN t.ym = a.codmes_ejec THEN t.flg_cliente_inversion END)  AS flg_cliente_inversion_um,
        MAX(CASE WHEN t.ym = a.codmes_ejec THEN t.flg_cliente_millonaria END) AS flg_cliente_millonaria_um,
        MAX(CASE WHEN t.ym = a.codmes_ejec THEN t.flg_cliente_alcancia END)   AS flg_cliente_alcancia_um,
        MAX(CASE WHEN t.ym = a.codmes_ejec THEN t.flg_cliente_planilla END)   AS flg_cliente_planilla_um,
        -- PASIVO actual / u4m (estilo pasivo_num)
        MAX(CASE WHEN t.ym = a.codmes_ejec                  THEN t.saldo_fdp_tot_pasivo END)     AS saldo_pasivo_actual,
        MAX(CASE WHEN t.ym = a.codmes_ejec                  THEN t.saldo_prom_tot_pasivo END)    AS saldo_prom_pasivo,
        MAX(CASE WHEN t.ym = a.codmes_ejec                  THEN t.saldo_fdp_tot_activo END)     AS saldo_activo_actual,
        AVG(CASE WHEN t.ym BETWEEN a.lo_u4m AND a.codmes_ejec THEN t.saldo_fdp_tot_pasivo END)    AS prom_saldo_pasivo_u4m
    FROM anchors a
    JOIN (
        SELECT
            CAST(nro_documento AS VARCHAR) AS key_value,
            CAST(cod_mes       AS VARCHAR) AS ym,
            saldo_fdp_tot_txs,      saldo_prom_tot_txs,
            saldo_fdp_tot_planilla, saldo_prom_tot_planilla,
            saldo_fdp_tot_tc,       saldo_prom_tot_tc,
            saldo_prom_tot_pasivo,  saldo_fdp_tot_pasivo,  saldo_fdp_tot_activo,
            codunicocli,
            flg_colaborador, flg_cliente_cts, flg_cliente_inversion,
            flg_cliente_millonaria, flg_cliente_alcancia, flg_cliente_planilla
        FROM awsdatacatalog.e_perm_aws.t_360_cliente
        WHERE frecuencia = 1
    ) t
      ON t.key_value = a.key_value
     AND t.ym BETWEEN a.lo_u6m AND a.codmes_ejec
    GROUP BY a.key_value, a.codmes_ejec, a.fch_princ
)
-- -------------------------------------------------------- PRINCIPALIDAD
, princ AS (   -- motivo_principalidad (bridge codunicocli via t_360; fch_periodo = ultimo dia del mes)
    SELECT t.key_value, t.codmes_ejec,
           MAX(p.motivo_principalidad) AS motivo_principalidad
    FROM t360 t
    JOIN awsdatacatalog.e_perm_aws.t_nds_principalidad p
      ON p.codunicocli = t.codunicocli
     AND p.fch_periodo = t.fch_princ
    GROUP BY t.key_value, t.codmes_ejec
)
-- ----------------------------------------------- RCC CASTIGO (montos/mora/meses)
, rcc_num AS (   -- ventana [m_rcc-23, m_rcc] ; "actual" = m_rcc
    SELECT
        a.key_value, a.codmes_ejec,
        SUM(CASE WHEN r.ym = a.rccnum_hi THEN r.saldo END)                                      AS monto_castigado_total,
        SUM(CASE WHEN r.ym = a.rccnum_hi AND r.cod_instit_financiera =  '00002' THEN r.saldo END) AS monto_castigado_ibk,
        SUM(CASE WHEN r.ym = a.rccnum_hi AND r.cod_instit_financiera <> '00002' THEN r.saldo END) AS monto_castigado_otros,
        COUNT(DISTINCT CASE WHEN r.ym = a.rccnum_hi THEN r.cod_instit_financiera END)           AS nro_entidades_castigo,
        MAX(CASE WHEN r.ym = a.rccnum_hi THEN r.condicion END)                                  AS max_dias_mora_castigo,
        date_diff('month', date_parse(MAX(r.ym) || '01','%Y%m%d'), date_parse(a.rccnum_hi || '01','%Y%m%d')) AS meses_desde_ultimo_castigo,
        date_diff('month', date_parse(MIN(r.ym) || '01','%Y%m%d'), date_parse(a.rccnum_hi || '01','%Y%m%d')) AS meses_desde_primer_castigo
    FROM anchors a
    JOIN (
        SELECT CAST(key_value AS VARCHAR) AS key_value, CAST(codmes AS VARCHAR) AS ym,
               cod_instit_financiera, saldo, condicion
        FROM awsdatacatalog.e_perm_aws.t_fact_report_rcc_rsk
        WHERE SUBSTRING(cod_cuenta_rcc,1,4) IN ('8113','8123','8133')
          AND condicion > 30
    ) r
      ON r.key_value = a.key_value
     AND r.ym BETWEEN a.rccnum_lo AND a.rccnum_hi
    GROUP BY a.key_value, a.codmes_ejec, a.rccnum_hi
)
-- ----------------------------------------------- DEUDA_CAS (logica c/d/e/f original)
, cde AS (   -- c: ibk actual ; d: ibk u24m ; e: noibk actual (saldo)
    SELECT
        a.key_value, a.codmes_ejec,
        MAX(CASE WHEN r.cod_instit_financiera =  '00002' AND r.ym = a.m_rcc THEN 1 ELSE 0 END)                       AS flg_c,
        MAX(CASE WHEN r.cod_instit_financiera =  '00002' AND r.ym BETWEEN a.rccd_lo AND a.rccd_hi THEN 1 ELSE 0 END) AS flg_d,
        MAX(CASE WHEN r.cod_instit_financiera <> '00002' AND r.ym = a.m_rcc THEN 1 ELSE 0 END)                       AS flg_e,
        SUM(CASE WHEN r.cod_instit_financiera <> '00002' AND r.ym = a.m_rcc THEN r.saldo ELSE 0 END)                 AS e_saldo
    FROM anchors a
    JOIN (
        SELECT CAST(key_value AS VARCHAR) AS key_value, CAST(codmes AS VARCHAR) AS ym,
               cod_instit_financiera, saldo
        FROM awsdatacatalog.e_perm_aws.t_fact_report_rcc_rsk
        WHERE SUBSTRING(cod_cuenta_rcc,1,4) IN ('8113','8123','8133')
          AND condicion > 30
    ) r
      ON r.key_value = a.key_value
     AND r.ym BETWEEN a.rccd_lo AND a.m_rcc
    GROUP BY a.key_value, a.codmes_ejec
)
, f_pre AS (   -- f: noibk u24m, saldo por entidad/mes (ventana [m_rcc-23, m_rcc-1])
    SELECT a.key_value, a.codmes_ejec, r.cod_instit_financiera, r.ym, SUM(r.saldo) AS saldo
    FROM anchors a
    JOIN (
        SELECT CAST(key_value AS VARCHAR) AS key_value, CAST(codmes AS VARCHAR) AS ym,
               cod_instit_financiera, saldo
        FROM awsdatacatalog.e_perm_aws.t_fact_report_rcc_rsk
        WHERE SUBSTRING(cod_cuenta_rcc,1,4) IN ('8113','8123','8133')
          AND condicion > 30
          AND cod_instit_financiera <> '00002'
    ) r
      ON r.key_value = a.key_value
     AND r.ym BETWEEN a.rccd_lo AND a.rccd_hi
    GROUP BY a.key_value, a.codmes_ejec, r.cod_instit_financiera, r.ym
)
, f_rn AS (
    SELECT key_value, codmes_ejec, cod_instit_financiera, ym, saldo,
           row_number() OVER (PARTITION BY key_value, codmes_ejec, cod_instit_financiera ORDER BY ym DESC) AS rn
    FROM f_pre
)
, f_sum AS (   -- ultimo reporte por entidad, suma de saldos
    SELECT key_value, codmes_ejec, SUM(saldo) AS f_saldo, MAX(1) AS flg_f
    FROM f_rn WHERE rn = 1
    GROUP BY key_value, codmes_ejec
)
-- ----------------------------------------------- CASTIGO VIDA (entidades)
, vida AS (   -- def: cuenta 81 + 302/925 + tipo_credito ; ventana [ejec-27, ejec-3]
    SELECT
        a.key_value, a.codmes_ejec,
        COUNT(DISTINCT r.cod_instit_financiera) AS nro_entidades_castigo_vida,
        CASE WHEN MAX(CASE WHEN r.cod_instit_financiera IN ('00001','00002','00004','00006') THEN 1 ELSE 0 END) = 1
             THEN 'BIG FOUR' ELSE 'OTROS' END   AS tipo_entidad_castigo_vida
    FROM anchors a
    JOIN (
        SELECT CAST(key_value AS VARCHAR) AS key_value, CAST(codmes AS VARCHAR) AS ym,
               cod_instit_financiera
        FROM awsdatacatalog.e_perm_aws.t_fact_report_rcc_rsk
        WHERE SUBSTRING(cod_cuenta_rcc,1,2) = '81'
          AND SUBSTRING(cod_cuenta_rcc,4,3) IN ('302','925')
          AND (tipo_credito IN ('11','12','13') OR tipo_credito = '99')
    ) r
      ON r.key_value = a.key_value
     AND r.ym BETWEEN a.vida_lo AND a.vida_hi
    GROUP BY a.key_value, a.codmes_ejec
)
-- =========================================================================
-- SELECT FINAL
-- =========================================================================
SELECT
    a.key_value,
    a.codmes_ejec,
    -- ===== deuda castigada (c/d/e/f) =====
    CASE WHEN COALESCE(cde.flg_c,0) = 1 THEN 0
         WHEN COALESCE(cde.flg_d,0) = 1 THEN 0
         WHEN COALESCE(cde.flg_e,0) = 1 THEN cde.e_saldo
         WHEN COALESCE(f.flg_f,0)   = 1 THEN f.f_saldo
         ELSE 0 END AS deuda_cas,
    -- ===== PEA / score / inca / segmentacion =====
    pf.sit_lab_ap,
    ic.flg_far_mto_trx_presencial_12m_c216,
    mo.puntaje_mod,
    sg.segmentacion_gdp_v2,
    -- ===== t_360 saldos (UM/U3M/U6M) =====
    t.saldo_fdp_tot_txs_um,       t.saldo_fdp_tot_txs_u3m,       t.saldo_fdp_tot_txs_u6m,
    t.saldo_prom_tot_txs_um,      t.saldo_prom_tot_txs_u3m,      t.saldo_prom_tot_txs_u6m,
    t.saldo_fdp_tot_planilla_um,  t.saldo_fdp_tot_planilla_u3m,  t.saldo_fdp_tot_planilla_u6m,
    t.saldo_prom_tot_planilla_um, t.saldo_prom_tot_planilla_u3m, t.saldo_prom_tot_planilla_u6m,
    t.saldo_fdp_tot_tc_um,        t.saldo_fdp_tot_tc_u3m,        t.saldo_fdp_tot_tc_u6m,
    t.saldo_prom_tot_tc_um,       t.saldo_prom_tot_tc_u3m,       t.saldo_prom_tot_tc_u6m,
    t.saldo_prom_tot_pasivo_um,   t.saldo_prom_tot_pasivo_u3m,   t.saldo_prom_tot_pasivo_u6m, t.saldo_prom_tot_pasivo_max_u6m,
    -- ===== flags _um =====
    t.flg_colaborador_um,
    t.flg_cliente_cts_um,
    t.flg_cliente_inversion_um,
    t.flg_cliente_millonaria_um,
    t.flg_cliente_alcancia_um,
    t.flg_cliente_planilla_um,
    -- ===== ratios / derivados =====
    (t.saldo_prom_tot_planilla_u3m + t.saldo_prom_tot_txs_u3m + t.saldo_prom_tot_tc_u3m)       AS saldo_pasivo_componentes_u3m,
    t.saldo_prom_tot_tc_u3m       / nullif(t.saldo_prom_tot_pasivo_u3m, 0)                     AS ratio_tc_pasivo_u3m,
    t.saldo_prom_tot_planilla_u3m / nullif(t.saldo_prom_tot_pasivo_u3m, 0)                     AS ratio_planilla_pasivo_u3m,
    t.saldo_prom_tot_txs_u3m      / nullif(t.saldo_prom_tot_pasivo_u3m, 0)                     AS ratio_txs_pasivo_u3m,
    (t.saldo_prom_tot_pasivo_um - t.saldo_prom_tot_pasivo_u6m) / nullif(t.saldo_prom_tot_pasivo_u6m, 0) AS var_pasivo_um_vs_u6m,
    -- ===== principalidad / castigo vida =====
    pr.motivo_principalidad,
    COALESCE(vd.nro_entidades_castigo_vida, 0)            AS nro_entidades_castigo_vida,
    COALESCE(vd.tipo_entidad_castigo_vida, 'SIN CASTIGO') AS tipo_entidad_castigo_vida,
    -- ===== profesiones / PEA num =====
    prf.nivel_profesional,
    prf.tipinstitucion,
    pf.edad_num,
    pf.rk_ing_num,
    -- ===== RCC castigo numericas =====
    rn.monto_castigado_total,
    rn.monto_castigado_ibk,
    rn.monto_castigado_otros,
    rn.nro_entidades_castigo,
    rn.max_dias_mora_castigo,
    rn.meses_desde_ultimo_castigo,
    rn.meses_desde_primer_castigo,
    -- ===== pasivo actual / u4m =====
    t.saldo_pasivo_actual,
    t.saldo_prom_pasivo,
    t.saldo_activo_actual,
    t.prom_saldo_pasivo_u4m
FROM anchors a
LEFT JOIN pea_feats pf ON pf.key_value = a.key_value AND pf.codmes_ejec = a.codmes_ejec
LEFT JOIN inca      ic ON ic.key_value = a.key_value AND ic.cod_mes_join = a.m_inca
LEFT JOIN modelo    mo ON mo.key_value = a.key_value AND mo.periodo      = a.m_modelo
LEFT JOIN seg       sg ON sg.key_value = a.key_value AND sg.codmes       = a.m_seg
LEFT JOIN t360      t  ON t.key_value  = a.key_value AND t.codmes_ejec   = a.codmes_ejec
LEFT JOIN princ     pr ON pr.key_value = a.key_value AND pr.codmes_ejec  = a.codmes_ejec
LEFT JOIN vida      vd ON vd.key_value = a.key_value AND vd.codmes_ejec  = a.codmes_ejec
LEFT JOIN prof      prf ON prf.key_value = a.key_value AND prf.codmes      = a.m_prof
LEFT JOIN rcc_num   rn ON rn.key_value = a.key_value AND rn.codmes_ejec  = a.codmes_ejec
LEFT JOIN cde          ON cde.key_value = a.key_value AND cde.codmes_ejec = a.codmes_ejec
LEFT JOIN f_sum     f  ON f.key_value  = a.key_value AND f.codmes_ejec   = a.codmes_ejec
;
