# -*- coding: utf-8 -*-
from viz_lib import build_html

RAW = """deuda_cas	nro_entidades_castigo_vida	meses_desde_ultimo_castigo	meses_desde_primer_castigo	edad_num	rk_ing_num	saldo_fdp_tot_txs_u3m	saldo_fdp_tot_txs_u6m	saldo_prom_tot_txs_u6m	saldo_prom_tot_pasivo_u6m	saldo_prom_tot_pasivo_max_u6m	saldo_pasivo_componentes_u3m	prom_saldo_pasivo_u4m	ratio_txs_pasivo_u3m	puntuacion_cal_cat	segmentacion_gdp_v2	flg_far_mto_trx_presencial_12m_c216	n	%	score_medio	quintil
(todos)	(todos)	(todos)	(todos)	(todos)	> 3,824	(todos)	(todos)	(todos)	> 89	(todos)	(todos)	(todos)	(todos)	<= 2	(todos)	(todos)	781	0.1	980.0384	G1
(todos)	(todos)	(todos)	(todos)	(todos)	> 3,824	(todos)	(todos)	(todos)	<= 89	(todos)	(todos)	(todos)	(todos)	<= 2	(todos)	(todos)	621	0.1	978.1449	G1
(todos)	(todos)	(todos)	(todos)	(todos)	<= 3,824	(todos)	(todos)	(todos)	(todos)	(todos)	> 53	(todos)	(todos)	<= 2	(todos)	(todos)	661	0.1	977.8669	G1
(todos)	(todos)	(todos)	(todos)	(todos)	<= 3,824	(todos)	(todos)	(todos)	(todos)	(todos)	<= 53	(todos)	(todos)	<= 2	(todos)	(todos)	667	0.1	975.3748	G1
(todos)	(todos)	(todos)	(todos)	(todos)	> 3,824	> 57	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 2]	(todos)	(todos)	608	0.1	960.903	G1
(todos)	(todos)	> 8	(todos)	(todos)	> 3,824	<= 57	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 2]	(todos)	(todos)	1313	0.2	958.8629	G1
(todos)	(todos)	<= 8	(todos)	(todos)	> 3,824	<= 57	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 2]	(todos)	(todos)	587	0.1	958.1704	G1
(todos)	(todos)	> 8	(todos)	(todos)	<= 3,824	> 3	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 2]	(todos)	(todos)	1020	0.2	957.9647	G1
(todos)	(todos)	> 8	(todos)	(todos)	<= 3,824	<= 3	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 2]	(todos)	(todos)	2516	0.4	956.7874	G1
(todos)	(todos)	<= 8	(todos)	(todos)	(2,746, 3,824]	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 2]	(todos)	(todos)	604	0.1	956.2897	G1
(todos)	(todos)	<= 8	(todos)	(todos)	<= 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 2]	(todos)	(todos)	772	0.1	955.4119	G1
(todos)	(todos)	> 8	(todos)	(todos)	> 3,282	(todos)	> 12	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 4]	(todos)	(todos)	840	0.1	928.7821	G1
(todos)	(todos)	<= 8	(todos)	(todos)	> 3,282	(todos)	> 12	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 4]	(todos)	(todos)	604	0.1	927.2285	G1
(todos)	(todos)	> 8	(todos)	(todos)	> 3,824	(todos)	<= 12	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 4]	(todos)	(todos)	1687	0.3	925.1292	G1
(todos)	(todos)	<= 8	(todos)	(todos)	> 3,824	(todos)	<= 12	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 4]	(todos)	(todos)	1087	0.2	922.7516	G1
(todos)	(todos)	(todos)	(todos)	(todos)	(3,282, 3,824]	(todos)	<= 12	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 4]	(todos)	(todos)	1627	0.3	919.6202	G1
(todos)	(todos)	(todos)	(todos)	(todos)	<= 3,282	(todos)	(todos)	> 162	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 4]	<= 4	(todos)	640	0.1	918.5172	G1
(todos)	(todos)	(todos)	(todos)	(todos)	<= 3,282	(todos)	(todos)	> 162	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 4]	> 4	(todos)	1076	0.2	917.9312	G1
(todos)	(todos)	> 22	(todos)	(todos)	<= 3,282	(todos)	(todos)	<= 162	(todos)	(todos)	(todos)	(todos)	(todos)	(2, 4]	(todos)	(todos)	1238	0.2	915.0743	G1
(todos)	(todos)	<= 22	(todos)	(todos)	<= 3,282	(todos)	(todos)	<= 162	(todos)	> 188	(todos)	(todos)	(todos)	(2, 4]	(todos)	(todos)	1772	0.3	912.9221	G1
(todos)	(todos)	<= 22	(todos)	(todos)	<= 3,282	(todos)	(todos)	<= 162	(todos)	<= 188	(todos)	(todos)	(todos)	(2, 4]	<= 2	(todos)	2684	0.5	912.7992	G1
(todos)	(todos)	<= 22	(todos)	(todos)	<= 3,282	(todos)	(todos)	<= 162	(todos)	<= 188	(todos)	(todos)	(todos)	(2, 4]	> 2	(todos)	8304	1.4	912.6527	G1
<= 75	(todos)	> 8	(todos)	(todos)	> 1,378	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 4]	(todos)	(todos)	1285	0.2	912.3339	G1
> 75	(todos)	> 8	(todos)	> 50	> 3,022	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 4]	(todos)	(todos)	1534	0.3	910.4505	G1
> 75	(todos)	> 8	(todos)	> 50	(1,378, 3,022]	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 4]	(todos)	(todos)	4872	0.8	910.2999	G1
> 75	(todos)	> 8	(todos)	<= 50	> 3,282	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 4]	(todos)	(todos)	2384	0.4	909.6204	G1
> 75	(todos)	> 8	(todos)	<= 50	(1,378, 3,282]	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 4]	(todos)	(todos)	5756	1	908.8617	G1
(todos)	(todos)	(4, 8]	(todos)	> 50	> 1,378	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 4]	(todos)	(todos)	2928	0.5	908.7162	G1
(todos)	(todos)	(4, 8]	(todos)	<= 50	> 1,378	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 345	(todos)	(4, 4]	(todos)	(todos)	623	0.1	908.1108	G1
(todos)	(todos)	(4, 8]	(todos)	<= 50	> 1,378	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	<= 345	(todos)	(4, 4]	(todos)	(todos)	2808	0.5	907.5545	G1
(todos)	(todos)	<= 4	(todos)	(todos)	> 1,378	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 0	(4, 4]	(todos)	(todos)	712	0.1	907.1854	G1
(todos)	(todos)	<= 4	(todos)	(todos)	> 1,378	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	<= 0	(4, 4]	(todos)	(todos)	1467	0.3	906.6626	G1
(todos)	(todos)	(todos)	(todos)	(todos)	<= 1,378	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 4]	(todos)	(todos)	715	0.1	901.7077	G1
(todos)	(todos)	> 8	(todos)	> 60	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	(todos)	(todos)	5886	1	871.7275	G1
(todos)	(todos)	> 8	(todos)	(54, 60]	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	(todos)	(todos)	3512	0.6	870.1241	G1
(todos)	(todos)	<= 8	(todos)	> 54	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	<= 4	(todos)	2036	0.3	868.8905	G1
(todos)	(todos)	<= 8	(todos)	> 54	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	> 4	(todos)	3033	0.5	868.82	G1
(todos)	<= 2	(todos)	(todos)	<= 54	> 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	(todos)	(todos)	9152	1.6	868.7326	G1
(todos)	> 2	(todos)	(todos)	<= 54	> 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	(todos)	> 0	591	0.1	867.6751	G1
(todos)	> 2	(todos)	(todos)	<= 54	> 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	(todos)	<= 0	688	0.1	867.6337	G1
(todos)	<= 2	> 8	(todos)	<= 54	<= 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	<= 4	(todos)	4658	0.8	867.4948	G1
(todos)	<= 2	> 8	(todos)	<= 54	<= 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	> 4	(todos)	8900	1.5	867.3506	G1
(todos)	<= 2	(2, 8]	(todos)	(34, 54]	<= 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	(todos)	(todos)	3944	0.7	866.1298	G1
(todos)	<= 2	(2, 8]	(todos)	(30, 34]	<= 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	(todos)	(todos)	657	0.1	865.7519	G1
(todos)	<= 2	(2, 8]	(todos)	<= 30	<= 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	(todos)	(todos)	1428	0.2	865.687	G1
(todos)	<= 2	<= 2	(todos)	<= 54	<= 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	(todos)	(todos)	1201	0.2	864.8143	G1
(todos)	> 2	(todos)	(todos)	<= 54	<= 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(4, 6]	(todos)	(todos)	1108	0.2	862.4296	G1
(todos)	(todos)	(todos)	> 10	> 60	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	<= 2	> 0	1281	0.2	758.1756	G2
(todos)	(todos)	(todos)	> 10	> 60	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	<= 2	<= 0	3491	0.6	744.9542	G2
(todos)	(todos)	(todos)	> 10	> 60	> 3,022	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(2, 4]	> 0	649	0.1	735.4838	G2
(todos)	(todos)	(todos)	> 10	> 60	<= 3,022	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(2, 4]	> 0	1985	0.3	734.1093	G2
(todos)	(todos)	(todos)	> 10	> 60	> 3,282	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(2, 4]	<= 0	763	0.1	728.5845	G2
(todos)	(todos)	(todos)	> 10	> 60	<= 3,282	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(2, 4]	<= 0	9543	1.6	726.788	G2
(todos)	<= 2	(todos)	> 10	> 60	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(4, 4]	(todos)	14426	2.5	718.8569	G2
(todos)	> 2	(todos)	> 10	> 60	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(4, 4]	(todos)	1520	0.3	709.0368	G2
(todos)	(todos)	(todos)	> 10	(54, 60]	> 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	<= 4	(todos)	7031	1.2	704.4221	G2
(todos)	(todos)	(todos)	> 10	<= 54	> 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	<= 4	(todos)	33254	5.7	699.7238	G2
(todos)	(todos)	(todos)	> 10	(50, 60]	(1,378, 2,746]	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	<= 4	(todos)	39777	6.8	688.9778	G2
(todos)	(todos)	(todos)	> 10	(50, 60]	<= 1,378	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	<= 4	(todos)	4940	0.8	688.401	G3
(todos)	(todos)	(todos)	> 10	<= 50	<= 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	<= 4	(todos)	58932	10.1	668.9955	G2
(todos)	(todos)	(todos)	> 10	(todos)	> 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	> 4	(todos)	50311	8.6	667.1445	G3
(todos)	(todos)	(todos)	> 10	> 34	(1,378, 2,746]	(todos)	(todos)	(todos)	> 89	(todos)	> 53	(todos)	(todos)	> 6	> 4	(todos)	6235	1.1	653.3355	G5
(todos)	(todos)	(todos)	> 10	> 34	(1,378, 2,746]	(todos)	(todos)	(todos)	> 89	(todos)	<= 53	(todos)	(todos)	> 6	> 4	(todos)	1717	0.3	651.4642	G4
(todos)	(todos)	(todos)	> 10	> 34	(1,378, 2,746]	(todos)	(todos)	(todos)	<= 89	(todos)	(todos)	(todos)	(todos)	> 6	> 4	(todos)	90923	15.6	646.6774	G5
(todos)	(todos)	(todos)	> 10	> 34	<= 1,378	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	> 4	(todos)	7511	1.3	640.9113	G5
(todos)	<= 2	(todos)	> 10	(28, 34]	<= 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	> 53	(todos)	(todos)	> 6	> 4	(todos)	5374	0.9	635.7547	G5
(todos)	<= 2	(todos)	> 10	(28, 34]	<= 2,746	(todos)	(todos)	(todos)	(todos)	(todos)	<= 53	(todos)	(todos)	> 6	> 4	(todos)	50921	8.7	634.8423	G5
(todos)	<= 2	(todos)	> 10	<= 28	<= 2,746	> 3	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	> 4	(todos)	6463	1.1	633.8046	G5
(todos)	<= 2	(todos)	> 10	<= 28	<= 2,746	<= 3	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	> 4	(todos)	37762	6.5	633.1562	G5
(todos)	> 2	(todos)	> 10	<= 34	<= 2,746	> 3	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	> 4	(todos)	1466	0.3	625.9591	G5
(todos)	> 2	(todos)	> 10	<= 34	<= 2,746	<= 3	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	> 4	(todos)	10623	1.8	621.8753	G5
(todos)	(todos)	> 4	<= 10	> 34	(todos)	(todos)	> 12	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(todos)	(todos)	1146	0.2	603.8647	G5
(todos)	(todos)	> 4	<= 10	> 34	(todos)	(todos)	<= 12	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(todos)	(todos)	9168	1.6	589.7508	G5
(todos)	(todos)	<= 4	<= 10	> 34	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 53	(todos)	(todos)	> 6	(todos)	(todos)	862	0.1	572.7668	G5
(todos)	(todos)	(2, 4]	<= 10	> 34	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	<= 53	(todos)	(todos)	> 6	(todos)	(todos)	2189	0.4	563.4244	G5
(todos)	(todos)	<= 2	<= 10	> 34	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	<= 53	(todos)	(todos)	> 6	(todos)	(todos)	4367	0.7	553.6757	G5
(todos)	(todos)	> 4	<= 10	(30, 34]	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(todos)	(todos)	2174	0.4	545.9048	G5
(todos)	(todos)	> 4	<= 10	(28, 30]	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(todos)	(todos)	1696	0.3	544.2447	G5
(todos)	(todos)	> 4	<= 10	<= 28	(todos)	> 3	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(todos)	(todos)	650	0.1	532.0169	G5
(todos)	(todos)	> 4	<= 10	<= 28	(todos)	<= 3	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(todos)	(todos)	4005	0.7	517.0839	G5
(todos)	(todos)	(2, 4]	<= 10	(26, 34]	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(todos)	(todos)	1286	0.2	511.07	G5
(todos)	(todos)	<= 2	<= 10	(30, 34]	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(todos)	(todos)	1042	0.2	506.6315	G5
(todos)	(todos)	<= 2	<= 10	(28, 30]	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(todos)	(todos)	782	0.1	503.3427	G5
(todos)	(todos)	<= 2	<= 10	(26, 28]	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(todos)	(todos)	913	0.2	501.9474	G5
(todos)	(todos)	(2, 4]	<= 10	<= 26	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(todos)	(todos)	640	0.1	483.3172	G5
(todos)	(todos)	<= 2	<= 10	<= 26	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	(todos)	> 6	(todos)	(todos)	1522	0.3	466.2589	G5"""

build_html("≤ 24 meses", RAW, "segmentacion_riesgo_24meses.html", apetito_def=730)
