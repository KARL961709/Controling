# -*- coding: utf-8 -*-
import re, html as _html
import numpy as np
import pandas as pd
from collections import OrderedDict


def agregar_bucket(df, mapeo, default=None, col_nro="nro_estrategia",
                   col_bucket="bucket", normalizar=True, verbose=True):
    """
    Crea/actualiza `col_bucket` a partir de `col_nro` usando `mapeo`.
      - mapeo  : dict {nro_estrategia(int): 'Bucket'}
      - default: bucket para los nro que NO estén en el mapeo ('las demás').
                 Si es None, esos quedan como NaN.
    """
    norm = (lambda b: str(b).strip().upper()) if normalizar else (lambda b: b)
    m = {int(k): norm(v) for k, v in mapeo.items()}        # normaliza b1/B1 -> 'B1'
    s = pd.to_numeric(df[col_nro], errors="coerce")
    out = df.copy()
    out[col_bucket] = s.map(m)
    n_def = out[col_bucket].isna().sum()
    if default is not None:
        out[col_bucket] = out[col_bucket].fillna(norm(default))
    if verbose:
        print(f"  [{col_bucket}] {len(m)} nro mapeados | {n_def:,} fila(s) a default "
              f"({norm(default) if default is not None else 'NaN'})")
    return out


def comparar_buckets_html(
    escenarios, mapas,
    salida_html='comparacion_buckets.html',
    titulo='Buckets definidos — distribución V1/V2/V3',
    default=None,                       # 'las demás' capturadas SIN bucket -> este bucket (ej. 'B6'); None -> Rechazo
    normalizar=True,
    col_id='nro_estrategia', col_regla='regla',
    col_target='target_60_12m', col_prob='prob_malo', col_fecha='p_fecinformacion',
    col_probjd='prob_jd', col_score='score', col_tipo='tipo',
):
    """mapas: {nro: 'B#'}  (un solo map para todos)  ó  {escenario: {nro: 'B#'}} (uno por escenario).

    Nota sobre 'Rechazo':
      - Fuente 1: filas de `rd` con nro_estrategia NULO -> no matchearon ninguna regla (población distinta a V2).
      - Fuente 2: estrategias capturadas cuyo número NO está en el map.
        Con `default` seteado, la Fuente 2 se manda a ese bucket y Rechazo queda solo con la Fuente 1 (nulos).
    """
    def esc(t): return _html.escape(str(t), quote=True)
    def _isnum(v): return v == v  # False si NaN
    norm = (lambda b: str(b).strip().upper()) if normalizar else (lambda b: b)

    # ¿mapas es por-escenario o uno solo?
    por_escenario = bool(mapas) and all(isinstance(v, dict) for v in mapas.values())
    def get_map(nombre):
        if por_escenario:
            return {int(k): v for k, v in mapas.get(nombre, {}).items()}
        return {int(k): v for k, v in mapas.items()}

    def _res(rd):
        r0 = rd.copy()
        r0[col_regla] = r0[col_regla].fillna('(sin regla)') if col_regla in r0.columns else '(sin regla)'
        agg = dict(cantidad=(col_target, 'size'), malos=(col_target, 'sum'), prob=(col_prob, 'mean'))
        if col_probjd in r0.columns:                          # prob_jd si viene en la base rd
            agg['probjd'] = (col_probjd, 'mean')
        r = r0.groupby([col_id, col_regla], dropna=False).agg(**agg).reset_index()
        r['malos'] = r['malos'].fillna(0)
        r['tasa'] = r['malos'] / r['cantidad']
        if 'probjd' not in r.columns:
            r['probjd'] = np.nan
        return r

    def colbucket(k, K):
        if K <= 1: return 'hsl(130,55%,80%)'
        hue = 130 - (k-1)/(K-1)*130
        return f'hsl({hue:.0f},60%,78%)'

    def _ordkey(lbl):
        m = re.search(r'(\d+)', str(lbl))
        return (int(m.group(1)) if m else 10**9, str(lbl))

    def _wmean(pairs):
        pairs = [(w, p) for w, p in pairs if w and _isnum(p)]
        wn = sum(w for w, _ in pairs)
        return (sum(w*p for w, p in pairs)/wn) if wn else float('nan')

    # prob_jd por estrategia: usa rd (res) si lo trae; si no, cae a las bases V (v2 -> v1 -> v3)
    def _pjd_map(d, res):
        if 'probjd' in res.columns and res['probjd'].notna().any():
            return {int(k): float(v) for k, v in zip(res[col_id], res['probjd']) if _isnum(v)}
        for key in ('v2', 'v1', 'v3'):
            b = d.get(key)
            if b is not None and (col_probjd in b.columns) and (col_id in b.columns):
                g = b.dropna(subset=[col_id]).groupby(col_id)[col_probjd].mean()
                return {int(k): float(v) for k, v in g.items() if _isnum(v)}
        return {}

    # ---- V1 (fecha x bucket) y V2/V3 (por bucket) usando el MAP completo ----
    def v1_html(vdf, mlbl, cols):
        if vdf is None or col_fecha not in vdf.columns:
            return '<p class="muted">V1 sin columna p_fecinformacion.</p>'
        t = vdf.copy(); t['__b'] = t[col_id].map(mlbl).fillna('Rechazo')
        colsr = cols + ['Rechazo']
        ct = pd.crosstab(t[col_fecha], t['__b']).reindex(columns=colsr, fill_value=0).sort_index()
        th = ''.join(f'<th{" class=rj" if c=="Rechazo" else ""}>{esc(c)}</th>' for c in colsr) + '<th class="tot">Total</th>'
        trs = ''
        for idx, rw in ct.iterrows():
            tds = ''.join(f'<td{" class=rj" if c=="Rechazo" else ""}>{int(rw[c]):,}</td>' for c in colsr)
            trs += f'<tr><td class="b">{esc(idx)}</td>{tds}<td class="tot">{int(rw.sum()):,}</td></tr>'
        tot = ct.sum()
        tds = ''.join(f'<td{" class=rj" if c=="Rechazo" else ""}>{int(tot[c]):,}</td>' for c in colsr)
        trs += f'<tr class="totr"><td class="b">Total</td>{tds}<td class="tot">{int(tot.sum()):,}</td></tr>'
        return f'<div class="tw"><table class="t"><thead><tr><th>p_fecinformacion</th>{th}</tr></thead><tbody>{trs}</tbody></table></div>'

    # ---- V1 desglosado por p_fecinformacion x tipo x bucket ----
    def v1_tipo_html(vdf, mlbl, cols):
        if vdf is None or col_id not in vdf.columns:
            return '<p class="muted">V1 no disponible.</p>'
        if col_tipo not in vdf.columns:
            return f'<p class="muted">V1 sin columna <code>{esc(col_tipo)}</code>.</p>'
        t = vdf.copy(); t['__b'] = t[col_id].map(mlbl).fillna('Rechazo')
        colsr = cols + ['Rechazo']
        has_f = col_fecha in t.columns
        keys = ([t[col_fecha]] if has_f else []) + [t[col_tipo]]
        ct = pd.crosstab(keys, t['__b']).reindex(columns=colsr, fill_value=0).sort_index()
        idx_names = ([col_fecha] if has_f else []) + [col_tipo]
        span = len(idx_names)
        hidx = ''.join(f'<th>{esc(n)}</th>' for n in idx_names)
        th = ''.join(f'<th{" class=rj" if c=="Rechazo" else ""}>{esc(c)}</th>' for c in colsr) + '<th class="tot">Total</th>'
        trs = ''
        for idx, rw in ct.iterrows():
            idx_t = idx if isinstance(idx, tuple) else (idx,)
            tdi = ''.join(f'<td class="b">{esc(v)}</td>' for v in idx_t)
            tds = ''.join(f'<td{" class=rj" if c=="Rechazo" else ""}>{int(rw[c]):,}</td>' for c in colsr)
            trs += f'<tr>{tdi}{tds}<td class="tot">{int(rw.sum()):,}</td></tr>'
        tot = ct.sum()
        tds = ''.join(f'<td{" class=rj" if c=="Rechazo" else ""}>{int(tot[c]):,}</td>' for c in colsr)
        trs += f'<tr class="totr"><td class="b" colspan="{span}">Total</td>{tds}<td class="tot">{int(tot.sum()):,}</td></tr>'
        return f'<div class="tw"><table class="t"><thead><tr>{hidx}{th}</tr></thead><tbody>{trs}</tbody></table></div>'

    def vb_html(vdf, mlbl, cols, lbl):
        if vdf is None or col_id not in vdf.columns:
            return f'<p class="muted">{lbl} no disponible.</p>'
        t = vdf.copy(); t['__b'] = t[col_id].map(mlbl).fillna('Rechazo')
        colsr = cols + ['Rechazo']
        c = t.groupby('__b').size().reindex(colsr, fill_value=0); tot = int(c.sum()) or 1
        has_p = col_probjd in t.columns; has_s = col_score in t.columns
        pmean = t.groupby('__b')[col_probjd].mean().reindex(colsr) if has_p else None
        smean = t.groupby('__b')[col_score].mean().reindex(colsr) if has_s else None
        def num(v, fmt): return f'<td>{fmt(v)}</td>' if _isnum(v) else '<td>-</td>'
        extra_h = (f'<th>{esc(col_probjd)}<br><small>prom</small></th>' if has_p else '') + \
                  (f'<th>{esc(col_score)}<br><small>prom</small></th>' if has_s else '')
        trs = ''
        for cc in colsr:
            ex = (num(pmean[cc], lambda x: f'{x:.4f}') if has_p else '') + \
                 (num(smean[cc], lambda x: f'{x:,.1f}') if has_s else '')
            trs += (f'<tr{" class=rjr" if cc=="Rechazo" else ""}><td class="b">{esc(cc)}</td>'
                    f'<td>{int(c[cc]):,}</td><td>{c[cc]/tot*100:.1f}%</td>{ex}</tr>')
        ex = (num(t[col_probjd].mean(), lambda x: f'{x:.4f}') if has_p else '') + \
             (num(t[col_score].mean(), lambda x: f'{x:,.1f}') if has_s else '')
        trs += f'<tr class="totr"><td class="b">Total</td><td>{tot:,}</td><td>100.0%</td>{ex}</tr>'
        return f'<div class="tw"><table class="t"><thead><tr><th>bucket</th><th>cantidad</th><th>%</th>{extra_h}</tr></thead><tbody>{trs}</tbody></table></div>'

    # ---------- construir bloques por escenario ----------
    scn_blocks, opts = [], []
    sid = 0
    for nombre in escenarios:
        d = escenarios[nombre]
        rd_full = d['rd']
        cap_mask = rd_full[col_id].notna()
        rd_cap = rd_full[cap_mask]; rd_rech = rd_full[~cap_mask]
        n_rech = int(len(rd_rech)); m_rech = int(rd_rech[col_target].sum()) if n_rech else 0
        # --- diagnóstico de Rechazo: nº de filas con nro_estrategia NULO por base ---
        diag = []
        for _base in ('rd', 'v1', 'v2', 'v3'):
            _df = d.get(_base)
            if _df is not None and col_id in _df.columns:
                _nn = int(_df[col_id].isna().sum())
                diag.append(f"{_base}={_nn:,}/{len(_df):,}")
        print(f"  [rechazo] {nombre}: filas con {col_id} NULO -> " + " | ".join(diag)
              + ("   (0 en todas = no debería salir Rechazo)" if all(x.split('=')[1].startswith('0/') for x in diag) else ""))
        res = _res(rd_cap)
        reglamap = dict(zip(res[col_id], res[col_regla]))
        ncl = dict(zip(res[col_id], res['cantidad'])); mal = dict(zip(res[col_id], res['malos']))
        pjd = _pjd_map(d, res)                                   # prob_jd por estrategia
        pjd_rech = float(rd_rech[col_probjd].mean()) if (col_probjd in rd_full.columns and n_rech) else float('nan')
        tot_n = (sum(ncl.values()) + n_rech) or 1

        # map normalizado + default para 'las demás' capturadas
        mp = {int(k): norm(v) for k, v in get_map(nombre).items()}
        default_b = norm(default) if default is not None else None
        sin_map = [int(i) for i in ncl if int(i) not in mp]      # capturadas sin bucket
        if sin_map and default_b is not None:
            for i in sin_map: mp[int(i)] = default_b             # -> bucket default
            print(f"  [info] {nombre}: {len(sin_map)} estrategia(s) sin bucket -> default '{default_b}': {sin_map[:12]}")
            sin = []
        elif sin_map:
            print(f"  [aviso] {nombre}: {len(sin_map)} estrategia(s) capturadas SIN bucket -> Rechazo: {sin_map[:12]}")
            sin = sin_map
        else:
            sin = []

        # agrupar por bucket (solo estrategias presentes en rd)
        grupos = {}
        for i in ncl:
            b = mp.get(int(i))
            if b is None: continue
            grupos.setdefault(b, []).append(int(i))
        cols = sorted(grupos, key=_ordkey)                      # buckets con data (risk table / chips / reglas)
        cols_v = sorted(set(mp.values()) | set(cols), key=_ordkey)  # todos los buckets del map (tablas V)
        mlbl = {int(k): v for k, v in mp.items()}               # <-- MAP COMPLETO para V1/V2/V3

        info = []
        for b in cols:
            ids = sorted(grupos[b]); n = sum(ncl[i] for i in ids); m = sum(mal[i] for i in ids)
            info.append((ids, n, m/n if n else 0))
        pj_bucket = [_wmean([(ncl[i], pjd.get(i, float('nan'))) for i in ids]) for (ids, _, _) in info]

        # estrategias sin bucket (solo si default es None) -> suman a Rechazo
        n_sin = sum(int(ncl[i]) for i in sin); m_sin = sum(mal[i] for i in sin)
        n_rech2 = n_rech + n_sin; m_rech2 = m_rech + m_sin
        t_rech2 = m_rech2 / n_rech2 if n_rech2 else 0
        parts_rech = ([(n_rech, pjd_rech)] if (n_rech and _isnum(pjd_rech)) else []) + \
                     [(ncl[i], pjd.get(i, float('nan'))) for i in sin]
        pj_rech2 = _wmean(parts_rech)
        K = len(cols)
        mono = all(info[i][2] <= info[i+1][2] + 1e-12 for i in range(len(info)-1))

        # --- chips ---
        chips = ''
        for k, (b, (ids, n, t)) in enumerate(zip(cols, info), 1):
            chips += (f'<span class="chip" style="background:{colbucket(k,K)}">'
                      f'<b>{esc(b)}</b> · [{", ".join(map(str,ids))}] · {t*100:.1f}% · n={n:,}</span>')
        if n_rech2:
            chips += f'<span class="chip rj"><b>Rechazo</b> · {t_rech2*100:.1f}% · n={n_rech2:,}</span>'
        badge = '<span class="ok">monótona</span>' if mono else '<span class="bad">NO monótona</span>'
        mapa = f'<div class="mrow"><span class="mname">Mis buckets <small>({K})</small> {badge}</span><div class="chips">{chips}</div></div>'

        # --- tabla tasa por bucket (+ prob_jd promedio) ---
        trs = ''
        for k, (b, (ids, n, t)) in enumerate(zip(cols, info), 1):
            pj = pj_bucket[k-1]; pjtxt = f'{pj:.4f}' if _isnum(pj) else '-'
            trs += (f'<tr><td class="b" style="background:{colbucket(k,K)}">{esc(b)}</td>'
                    f'<td>{t*100:.2f}%</td><td>{pjtxt}</td><td>{n:,}</td><td>{n/tot_n*100:.1f}%</td></tr>')
        if n_rech2:
            pjtxt = f'{pj_rech2:.4f}' if _isnum(pj_rech2) else '-'
            trs += (f'<tr><td class="b rj">Rechazo</td><td class="rj">{t_rech2*100:.2f}%</td>'
                    f'<td class="rj">{pjtxt}</td><td class="rj">{n_rech2:,}</td><td class="rj">{n_rech2/tot_n*100:.1f}%</td></tr>')
        NT = sum(i[1] for i in info) + n_rech2; MT = sum(i[1]*i[2] for i in info) + m_rech2
        parts_tot = [(info[k][1], pj_bucket[k]) for k in range(len(info))] + ([(n_rech2, pj_rech2)] if n_rech2 else [])
        pj_tot = _wmean(parts_tot); pjtxt = f'{pj_tot:.4f}' if _isnum(pj_tot) else '-'
        trs += (f'<tr class="totr"><td class="b">Total</td><td>{MT/NT*100:.2f}%</td>'
                f'<td>{pjtxt}</td><td>{NT:,}</td><td>100.0%</td></tr>')
        tabla = (f'<table class="cmp"><thead><tr><th>bucket</th><th>tasa malos</th>'
                 f'<th>{esc(col_probjd)}<br><small>prom</small></th><th>N</th><th>% del total</th></tr></thead>'
                 f'<tbody>{trs}</tbody></table>')

        # --- reglas por bucket ---
        bloques = ''
        for k, (b, (ids, n, t)) in enumerate(zip(cols, info), 1):
            rrows = ''
            for nro in sorted(ids):
                ni = int(ncl[nro]); ti = mal[nro]/ni if ni else 0
                rrows += (f'<tr><td class="rule">[{nro}] {esc(reglamap.get(nro,""))}</td>'
                          f'<td>{ti*100:.1f}%</td><td>{ni/tot_n*100:.1f}%</td><td>{ni:,}</td></tr>')
            bloques += (f'<div class="bk"><div class="bkh" style="background:{colbucket(k,K)}">'
                        f'{esc(b)} · {len(ids)} regla(s) · tasa {t*100:.1f}% · n={n:,}</div>'
                        f'<div class="tw"><table class="t"><thead><tr><th>estrategia</th>'
                        f'<th>tasa malos</th><th>% del total</th><th>N</th></tr></thead>'
                        f'<tbody>{rrows}</tbody></table></div></div>')
        if n_rech2:
            bloques += (f'<div class="bk"><div class="bkh rj">Rechazo · nro_estrategia nulo (no capturado por ninguna regla) · '
                        f'tasa {t_rech2*100:.1f}% · n={n_rech2:,}</div>'
                        f'<div class="tw"><table class="t"><thead><tr><th>estrategia</th><th>tasa malos</th><th>% del total</th><th>N</th></tr></thead>'
                        f'<tbody><tr><td class="rule">(sin nro_estrategia)</td><td>{t_rech2*100:.1f}%</td><td>{n_rech2/tot_n*100:.1f}%</td><td>{n_rech2:,}</td></tr></tbody></table></div></div>')

        v1  = v1_html(d.get('v1'), mlbl, cols_v)
        v1t = v1_tipo_html(d.get('v1'), mlbl, cols_v)
        v2  = vb_html(d.get('v2'), mlbl, cols_v, 'V2')
        v3  = vb_html(d.get('v3'), mlbl, cols_v, 'V3')

        scn_blocks.append(
            f'<div class="scn" id="s{sid}">'
            f'<h2>{esc(nombre)}</h2>'
            f'<h3>Mis buckets <small>(map definido)</small></h3><div class="mapa">{mapa}</div>'
            f'<h3>Tasa de riesgo por bucket <small>(con prob_jd promedio)</small></h3>{tabla}'
            f'<h3>Reglas por bucket</h3><div class="det">{bloques}</div>'
            f'<h3>V1 · base de campañas (p_fecinformacion × bucket)</h3>{v1}'
            f'<h3>V1 · base de campañas (p_fecinformacion × {esc(col_tipo)} × bucket)</h3>{v1t}'
            f'<h3>V2 · base inicial (por bucket)</h3>{v2}'
            f'<h3>V3 · no campaña (por bucket)</h3>{v3}'
            f'</div>')
        opts.append(f'<option value="s{sid}">{esc(nombre)}</option>')
        sid += 1

    CSS = """
*{box-sizing:border-box;margin:0;padding:0;font-family:"Segoe UI",Roboto,Arial,sans-serif}
body{background:#eef2f1;color:#10241f;font-size:14px}
header{background:linear-gradient(90deg,#007a72,#00a499);color:#fff;padding:18px 4vw}
header h1{font-size:22px}.sub{opacity:.92;font-size:13px;margin-top:4px}
.selwrap{margin-top:14px} select{padding:10px 14px;border-radius:10px;border:none;font-size:15px;font-weight:600;color:#007a72;min-width:380px}
.wrap{padding:18px 4vw 80px} .scn{display:none}.scn.on{display:block}
h2{color:#007a72;font-size:22px;margin:8px 0 6px}
h3{color:#23433c;font-size:16px;margin:26px 0 10px;border-left:4px solid #00a499;padding-left:9px;line-height:1.2}
h3 small{color:#7c8c88;font-weight:400;font-size:12.5px}
.mapa{display:flex;flex-direction:column;gap:8px;margin-bottom:6px}
.mrow{display:flex;gap:14px;align-items:flex-start;background:#fff;border:1px solid #d8e3df;border-radius:10px;padding:9px 13px}
.mname{flex:0 0 200px;font-weight:700;color:#23433c;font-size:13.5px;line-height:1.5}
.chips{display:flex;flex-wrap:wrap;gap:6px;flex:1}
.chip{border-radius:8px;padding:4px 9px;font-size:12px;color:#10241f;border:1px solid #0000001f;white-space:nowrap}
.ok{background:#c6efce;color:#1a7a4a;border-radius:8px;padding:2px 8px;font-size:11px;font-weight:700;margin-left:6px}
.bad{background:#ffc7ce;color:#b23b30;border-radius:8px;padding:2px 8px;font-size:11px;font-weight:700;margin-left:6px}
.tw{overflow-x:auto;margin:6px 0 4px;border-radius:10px;border:1px solid #d8e3df}
table.t,table.cmp{border-collapse:collapse;background:#fff;font-size:13px;width:auto}
table.t th,table.cmp th{background:#0a7d74;color:#fff;padding:8px 13px;text-align:center;font-weight:600;border:1px solid #0a7d74;white-space:nowrap}
table.t td,table.cmp td{padding:6px 13px;border:1px solid #dde7e4;white-space:nowrap}
table.t td{text-align:right}
table.t td.b{text-align:left;background:#eef7f5;font-weight:700;color:#23433c}
table.t td.rule{text-align:left;white-space:normal;max-width:560px;font-size:12px;color:#23433c;font-family:Consolas,monospace}
table.t tbody tr:nth-child(even){background:#f6faf9}
table.cmp{margin-bottom:4px}
table.cmp td{text-align:center;line-height:1.35}
table.cmp td.b{text-align:left;font-weight:700;color:#23433c}
.chip.rj{background:#e2e6e5;border:1px solid #00000026;color:#4a5a56}
table.t td.rj,table.t th.rj,table.cmp td.rj,table.cmp th.rj{background:#eceff0;color:#4a5a56}
table.cmp td.b.rj{background:#e2e6e5;color:#4a5a56}
.bkh.rj{background:#e2e6e5;color:#4a5a56}
tr.rjr td{background:#eceff0;color:#4a5a56}
.tot,td.tot,th.tot{background:#dff0ed !important;font-weight:700;color:#0a5a52}
tr.totr td{background:#cfe9e4 !important;font-weight:700;color:#084b44;border-top:2px solid #0a7d74}
.det{display:flex;flex-direction:column}
.bk{margin:8px 0 12px;border:1px solid #d8e3df;border-radius:8px;overflow:hidden}
.bkh{padding:6px 11px;font-weight:700;font-size:12.5px;color:#10241f}
.bk .tw{margin:0;border:none;border-top:1px solid #d8e3df;border-radius:0}
.muted{color:#9aa8a4;font-size:12.5px;font-style:italic;padding:6px 2px}
"""
    JS = "function showScn(id){document.querySelectorAll('.scn').forEach(d=>d.classList.toggle('on',d.id===id));}" \
         "window.onload=function(){var s=document.querySelector('.scn');if(s)showScn(s.id);};"
    doc = (f'<!DOCTYPE html><html lang="es"><head><meta charset="UTF-8">'
           f'<meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{esc(titulo)}</title>'
           f'<style>{CSS}</style></head><body>'
           f'<header><h1>{esc(titulo)}</h1><div class="sub">Buckets definidos por ti (map) aplicados a V1/V2/V3. Verde = menor riesgo, rojo = mayor.</div>'
           f'<div class="selwrap"><select onchange="showScn(this.value)">{"".join(opts)}</select></div></header>'
           f'<div class="wrap">{"".join(scn_blocks)}</div><script>{JS}</script></body></html>')
    with open(salida_html, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"OK -> {salida_html}  ({sid} escenarios)")
    return salida_html
