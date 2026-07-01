# -*- coding: utf-8 -*-
import re, math, html as _html
import numpy as np
import pandas as pd
from collections import OrderedDict


def comparar_metodos_html(
    escenarios,
    salida_html='comparacion_metodos.html',
    titulo='Comparación de métodos de agrupamiento',
    n_grupos=8, min_pct=2.0, umbral_min=500, shrink_k=500,
    col_id='nro_estrategia', col_regla='regla',
    col_target='target_60_12m', col_prob='prob_malo', col_fecha='p_fecinformacion',
    col_probjd='prob_jd', col_score='score', col_tipo='tipo',
):
    def esc(t): return _html.escape(str(t), quote=True)
    def rate(p, d): return p/d if d else 0
    def _isnum(v): return v == v  # False si NaN

    def _res(rd):
        r0 = rd.copy()
        r0[col_regla] = r0[col_regla].fillna('(sin regla)')   # capturadas con regla nula no se pierden
        agg = dict(cantidad=(col_target, 'size'), malos=(col_target, 'sum'), prob=(col_prob, 'mean'))
        if col_probjd in r0.columns:                          # prob_jd si viene en la base rd
            agg['probjd'] = (col_probjd, 'mean')
        r = r0.groupby([col_id, col_regla], dropna=False).agg(**agg).reset_index()
        r['malos'] = r['malos'].fillna(0)
        r['tasa'] = r['malos'] / r['cantidad']
        if 'probjd' not in r.columns:
            r['probjd'] = np.nan
        return r

    # ---------- métodos ----------
    def _chi2(b1, n1, b2, n2):
        O = np.array([[b1, n1-b1], [b2, n2-b2]], float); Nn = O.sum()
        if Nn == 0: return 0.0
        Ex = O.sum(1, keepdims=True)*O.sum(0, keepdims=True)/Nn
        return np.where(Ex > 0, (O-Ex)**2/Ex, 0).sum()

    def m_cascada(res):
        d = res.sort_values(col_id).reset_index(drop=True); blq = []
        for i in range(len(d)):
            blq.append([int(d['malos'][i]), int(d['cantidad'][i]), [int(d[col_id][i])]])
            while len(blq) >= 2 and rate(blq[-2][0], blq[-2][1]) > rate(blq[-1][0], blq[-1][1]):
                x = blq.pop(); blq[-1][0]+=x[0]; blq[-1][1]+=x[1]; blq[-1][2]+=x[2]
        while len(blq) > n_grupos:
            g = [abs(rate(blq[i+1][0], blq[i+1][1])-rate(blq[i][0], blq[i][1])) for i in range(len(blq)-1)]
            i = int(np.argmin(g)); blq[i] = [blq[i][0]+blq[i+1][0], blq[i][1]+blq[i+1][1], blq[i][2]+blq[i+1][2]]; del blq[i+1]
        return [b[2] for b in blq]

    def _chimerge_core(res):
        d = res.sort_values('tasa').reset_index(drop=True); minn = d['cantidad'].sum()*min_pct/100
        blq = [[int(r['malos']), int(r['cantidad']), [int(r[col_id])]] for _, r in d.iterrows()]; cambio = True
        while cambio and len(blq) > 1:
            cambio = False
            for i in range(len(blq)):
                if blq[i][1] < minn:
                    cand = ([(i-1, i)] if i > 0 else []) + ([(i, i+1)] if i < len(blq)-1 else [])
                    j, k = min(cand, key=lambda p: _chi2(blq[p[0]][0], blq[p[0]][1], blq[p[1]][0], blq[p[1]][1]))
                    blq[j] = [blq[j][0]+blq[k][0], blq[j][1]+blq[k][1], blq[j][2]+blq[k][2]]; del blq[k]; cambio = True; break
            blq.sort(key=lambda x: x[0]/x[1])
        while len(blq) > n_grupos:
            ch = [_chi2(blq[i][0], blq[i][1], blq[i+1][0], blq[i+1][1]) for i in range(len(blq)-1)]
            i = int(np.argmin(ch)); blq[i] = [blq[i][0]+blq[i+1][0], blq[i][1]+blq[i+1][1], blq[i][2]+blq[i+1][2]]; del blq[i+1]; blq.sort(key=lambda x: x[0]/x[1])
        blq.sort(key=lambda x: x[0]/x[1]); return [b[2] for b in blq]

    def m_chimerge(res):
        if not umbral_min or umbral_min <= 0: return _chimerge_core(res)
        conf = res[res['cantidad'] >= umbral_min]; peque = res[res['cantidad'] < umbral_min]
        if len(conf) == 0: return _chimerge_core(res)
        buckets = _chimerge_core(conf)
        prob = dict(zip(res[col_id], res['prob'])); ncl = dict(zip(res[col_id], res['cantidad'])); mal = dict(zip(res[col_id], res['malos']))
        bprob = [sum(prob[i]*ncl[i] for i in b)/sum(ncl[i] for i in b) for b in buckets]
        for _, r in peque.iterrows():
            buckets[int(np.argmin([abs(r['prob']-bp) for bp in bprob]))].append(int(r[col_id]))
        buckets.sort(key=lambda b: sum(mal[i] for i in b)/sum(ncl[i] for i in b)); return buckets

    def _optbin_heur(res):
        d = res.sort_values('prob').reset_index(drop=True); minn = d['cantidad'].sum()*min_pct/100
        blq = [[int(r['malos']), int(r['cantidad']), [int(r[col_id])]] for _, r in d.iterrows()]; i = 0
        while i < len(blq)-1:
            if rate(blq[i][0], blq[i][1]) > rate(blq[i+1][0], blq[i+1][1]):
                blq[i] = [blq[i][0]+blq[i+1][0], blq[i][1]+blq[i+1][1], blq[i][2]+blq[i+1][2]]; del blq[i+1]; i = max(0, i-1)
            else: i += 1
        cambio = True
        while cambio and len(blq) > 1:
            cambio = False
            for i in range(len(blq)):
                if blq[i][1] < minn:
                    if i == 0: j = 1
                    elif i == len(blq)-1: j = i-1
                    else: j = i-1 if abs(rate(blq[i-1][0], blq[i-1][1])-rate(blq[i][0], blq[i][1])) <= abs(rate(blq[i+1][0], blq[i+1][1])-rate(blq[i][0], blq[i][1])) else i+1
                    lo, hi = min(i, j), max(i, j); blq[lo] = [blq[lo][0]+blq[hi][0], blq[lo][1]+blq[hi][1], blq[lo][2]+blq[hi][2]]; del blq[hi]; cambio = True; break
        while len(blq) > n_grupos:
            g = [abs(rate(blq[i+1][0], blq[i+1][1])-rate(blq[i][0], blq[i][1])) for i in range(len(blq)-1)]
            i = int(np.argmin(g)); blq[i] = [blq[i][0]+blq[i+1][0], blq[i][1]+blq[i+1][1], blq[i][2]+blq[i+1][2]]; del blq[i+1]
        blq.sort(key=lambda x: x[0]/x[1]); return [b[2] for b in blq]

    def m_optbin(res):
        # OptBin real (librería optbinning, binning categórico). Si no está instalada -> heurística.
        try:
            from optbinning import OptimalBinning
        except Exception:
            return _optbin_heur(res)
        ncl = {int(r[col_id]): int(r['cantidad']) for _, r in res.iterrows()}
        mal = {int(r[col_id]): int(r['malos'])    for _, r in res.iterrows()}
        # reconstruir (x, y) por observación a partir de los agregados por estrategia
        cats, ys = [], []
        for nro, n in ncl.items():
            m = mal[nro]; cats += [nro]*n; ys += [1]*m + [0]*(n-m)
        if not cats:
            return _optbin_heur(res)
        x = np.array(cats); y = np.array(ys, dtype=int)
        mbs = min(0.5, max(0.0, min_pct/100.0))
        try:
            ob = OptimalBinning(name=str(col_id), dtype='categorical',
                                max_n_bins=n_grupos, min_bin_size=mbs,
                                monotonic_trend='ascending')
            ob.fit(x, y)
            if ob.status != 'OPTIMAL' or not len(ob.splits):
                return _optbin_heur(res)
            buckets = [sorted(int(v) for v in np.atleast_1d(g)) for g in ob.splits]
        except Exception:
            return _optbin_heur(res)
        # asegurar que ninguna estrategia quede fuera (asignar a la de tasa más cercana)
        asignadas = {i for b in buckets for i in b}
        faltan = [i for i in ncl if i not in asignadas]
        if faltan:
            brate = [sum(mal[i] for i in b)/sum(ncl[i] for i in b) for b in buckets]
            for i in faltan:
                ri = mal[i]/ncl[i] if ncl[i] else 0
                buckets[int(np.argmin([abs(ri-br) for br in brate]))].append(i)
        buckets.sort(key=lambda b: sum(mal[i] for i in b)/sum(ncl[i] for i in b))
        return buckets

    def m_shrink(res):
        p0 = res['malos'].sum()/res['cantidad'].sum() if res['cantidad'].sum() else 0
        d = res.copy(); d['adj'] = (d['malos']+shrink_k*p0)/(d['cantidad']+shrink_k); d = d.sort_values('adj').reset_index(drop=True)
        blq = [[int(r['malos']), int(r['cantidad']), [int(r[col_id])], float(r['adj'])] for _, r in d.iterrows()]; i = 0
        while i < len(blq)-1:
            if blq[i][3] > blq[i+1][3]:
                w1, w2 = blq[i][1], blq[i+1][1]; blq[i] = [blq[i][0]+blq[i+1][0], blq[i][1]+blq[i+1][1], blq[i][2]+blq[i+1][2], (blq[i][3]*w1+blq[i+1][3]*w2)/(w1+w2)]; del blq[i+1]; i = max(0, i-1)
            else: i += 1
        while len(blq) > n_grupos:
            g = [abs(blq[i+1][3]-blq[i][3]) for i in range(len(blq)-1)]
            i = int(np.argmin(g)); w1, w2 = blq[i][1], blq[i+1][1]; blq[i] = [blq[i][0]+blq[i+1][0], blq[i][1]+blq[i+1][1], blq[i][2]+blq[i+1][2], (blq[i][3]*w1+blq[i+1][3]*w2)/(w1+w2)]; del blq[i+1]
        blq.sort(key=lambda x: x[0]/x[1]); return [b[2] for b in blq]

    def m_mdlp(res):
        d = res.sort_values('prob').reset_index(drop=True)
        seg0 = [[int(r['malos']), int(r['cantidad'])-int(r['malos']), [int(r[col_id])]] for _, r in d.iterrows()]
        def ent(pos, neg):
            n = pos+neg
            if n == 0: return 0.0
            e = 0.0
            for c in (pos, neg):
                if c > 0: p = c/n; e -= p*math.log2(p)
            return e
        def rec(seg):
            pos = sum(x[0] for x in seg); neg = sum(x[1] for x in seg); Nt = pos+neg
            if len(seg) == 1 or Nt == 0: return [seg]
            Es = ent(pos, neg); best = None
            for cut in range(1, len(seg)):
                L, R = seg[:cut], seg[cut:]; lp = sum(x[0] for x in L); ln = sum(x[1] for x in L); rp = sum(x[0] for x in R); rn = sum(x[1] for x in R)
                nl, nr = lp+ln, rp+rn
                if nl == 0 or nr == 0: continue
                Eq = (nl*ent(lp, ln)+nr*ent(rp, rn))/Nt; gain = Es-Eq
                if best is None or gain > best[0]: best = (gain, cut, ent(lp, ln), ent(rp, rn), (lp > 0)+(ln > 0), (rp > 0)+(rn > 0))
            if best is None: return [seg]
            gain, cut, El, Er, kl, kr = best; k = (pos > 0)+(neg > 0)
            delta = math.log2(3**k-2)-(k*Es-kl*El-kr*Er); um = (math.log2(Nt-1)+delta)/Nt if Nt > 1 else 0
            if gain <= um: return [seg]
            return rec(seg[:cut])+rec(seg[cut:])
        blq = [[sum(x[0] for x in q), sum(x[0]+x[1] for x in q), [i for x in q for i in x[2]]] for q in rec(seg0)]
        blq.sort(key=lambda x: x[0]/x[1]); return [b[2] for b in blq]

    METODOS = [("Cascada", m_cascada), ("ChiMerge", m_chimerge), ("OptBin", m_optbin), ("Shrinkage", m_shrink), ("MDLP", m_mdlp)]

    def _split(n):
        m = re.match(r'^(.*)_([^_]+)$', n)
        return (m.group(1), m.group(2)) if (m and m.group(2).isdigit()) else (n, '')

    def _familias(nombres):
        fam = OrderedDict()
        for n in nombres:
            f, p = _split(n); fam.setdefault(f, []).append((p, n))
        for f in fam: fam[f].sort(key=lambda x: (x[0] == '', x[0]))
        return fam

    # color verde(bajo riesgo) -> rojo(alto) por posicion del bucket
    def colbucket(k, K):
        if K <= 1: return 'hsl(130,55%,80%)'
        hue = 130 - (k-1)/(K-1)*130
        return f'hsl({hue:.0f},60%,78%)'

    # prob_jd por estrategia: usa rd (res) si lo trae; si no, cae a las bases V (v2 -> v1 -> v3)
    def _pjd_map(d, res):
        if col_probjd in res.columns and res['probjd'].notna().any():
            return {int(k): float(v) for k, v in zip(res[col_id], res['probjd']) if _isnum(v)}
        for key in ('v2', 'v1', 'v3'):
            b = d.get(key)
            if b is not None and (col_probjd in b.columns) and (col_id in b.columns):
                g = b.dropna(subset=[col_id]).groupby(col_id)[col_probjd].mean()
                return {int(k): float(v) for k, v in g.items() if _isnum(v)}
        return {}

    def _wmean(pairs):
        pairs = [(w, p) for w, p in pairs if w and _isnum(p)]
        wn = sum(w for w, _ in pairs)
        return (sum(w*p for w, p in pairs)/wn) if wn else float('nan')

    # ---- tablas V1 (fecha x bucket) y V2/V3 (por bucket) mapeadas a los buckets del metodo ----
    def v1_html(vdf, mlbl, cols):
        if vdf is None or col_fecha not in vdf.columns:
            return '<p class="muted">V1 sin columna p_fecinformacion.</p>'
        t = vdf.copy(); t['__b'] = t[col_id].map(mlbl).fillna('Rechazo')   # no capturadas -> Rechazo
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

    def vb_html(vdf, mlbl, cols, lbl):
        if vdf is None or col_id not in vdf.columns:
            return f'<p class="muted">{lbl} no disponible.</p>'
        t = vdf.copy(); t['__b'] = t[col_id].map(mlbl).fillna('Rechazo')   # no capturadas -> Rechazo
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

    # ---- V3 desglosado por p_fecinformacion x tipo x bucket ----
    def v3_tipo_html(vdf, mlbl, cols):
        if vdf is None or col_id not in vdf.columns:
            return '<p class="muted">V3 no disponible.</p>'
        if col_tipo not in vdf.columns:
            return f'<p class="muted">V3 sin columna <code>{esc(col_tipo)}</code>.</p>'
        t = vdf.copy(); t['__b'] = t[col_id].map(mlbl).fillna('Rechazo')   # no capturadas -> Rechazo
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

    # ---------- construir bloques por escenario ----------
    scn_blocks, opts = [], []
    fams = _familias(escenarios.keys())
    sid = 0
    for fam, items in fams.items():
        grp = [f'<optgroup label="{esc(fam)}">']
        for prof, nombre in items:
            d = escenarios[nombre]
            rd_full = d['rd']
            cap_mask = rd_full[col_id].notna()                       # capturadas por alguna estrategia
            rd_cap = rd_full[cap_mask]
            rd_rech = rd_full[~cap_mask]                             # Rechazo = no capturadas
            n_rech = int(len(rd_rech)); m_rech = int(rd_rech[col_target].sum()) if n_rech else 0
            t_rech = m_rech / n_rech if n_rech else 0
            res = _res(rd_cap)
            reglamap = dict(zip(res[col_id], res[col_regla]))
            ncl = dict(zip(res[col_id], res['cantidad'])); mal = dict(zip(res[col_id], res['malos']))
            pjd = _pjd_map(d, res)                                   # prob_jd por estrategia
            pjd_rech = float(rd_rech[col_probjd].mean()) if (col_probjd in rd_full.columns and n_rech) else float('nan')
            tot_n = (sum(ncl.values()) + n_rech) or 1                # % del total = sobre población completa (incl. Rechazo)
            metodos_res = []
            for nom, fn in METODOS:
                bks = fn(res)
                info = []; pjs = []                                  # pjs[k] = prob_jd promedio (ponderado) del bucket k
                for ids in bks:
                    ids_s = sorted(ids)
                    n = sum(ncl[i] for i in ids_s); m = sum(mal[i] for i in ids_s)
                    info.append((ids_s, n, m/n if n else 0))
                    pjs.append(_wmean([(ncl[i], pjd.get(i, float('nan'))) for i in ids_s]))
                mono = all(info[i][2] <= info[i+1][2]+1e-12 for i in range(len(info)-1))
                metodos_res.append((nom, info, mono, pjs))

            # --- mapa de agrupacion (chips) ---
            mapa = ''
            for nom, info, mono, pjs in metodos_res:
                chips = ''
                K = len(info)
                for k, (ids, n, t) in enumerate(info, 1):
                    chips += (f'<span class="chip" style="background:{colbucket(k,K)}">'
                              f'<b>B{k}</b> · [{", ".join(map(str,ids))}] · {t*100:.1f}% · n={n:,}</span>')
                if n_rech:
                    chips += (f'<span class="chip rj"><b>Rechazo</b> · sin estrategia · '
                              f'{t_rech*100:.1f}% · n={n_rech:,}</span>')
                badge = '<span class="ok">monótona</span>' if mono else '<span class="bad">NO monótona</span>'
                mapa += f'<div class="mrow"><span class="mname">{esc(nom)} <small>({K})</small> {badge}</span><div class="chips">{chips}</div></div>'

            # --- tabla tasa por bucket (+ prob_jd promedio) ---
            maxk = max(len(info) for _, info, _, _ in metodos_res)
            th = ''.join(f'<th>{esc(nom)}</th>' for nom, _, _, _ in metodos_res)
            trs = ''
            for k in range(maxk):
                tds = ''
                for nom, info, mono, pjs in metodos_res:
                    if k < len(info):
                        ids, n, t = info[k]; pj = pjs[k]
                        pjtxt = f'<br><small class="pjd">prob_jd {pj:.4f}</small>' if _isnum(pj) else ''
                        tds += f'<td style="background:{colbucket(k+1,len(info))}">{t*100:.1f}%<br><small>n={n:,}</small>{pjtxt}</td>'
                    else:
                        tds += '<td class="empty"></td>'
                trs += f'<tr><td class="b">B{k+1}</td>{tds}</tr>'
            if n_rech:                                              # fila Rechazo (igual en todos los métodos)
                pjtxt = f'<br><small class="pjd">prob_jd {pjd_rech:.4f}</small>' if _isnum(pjd_rech) else ''
                tdr = ''.join(f'<td class="rj">{t_rech*100:.1f}%<br><small>n={n_rech:,}</small>{pjtxt}</td>' for _ in metodos_res)
                trs += f'<tr><td class="b rj">Rechazo</td>{tdr}</tr>'
            tdt = ''                                                # fila Total = capturados + Rechazo
            for nom, info, mono, pjs in metodos_res:
                nt = sum(i[1] for i in info) + n_rech; mt = sum(i[1]*i[2] for i in info) + m_rech
                parts = [(i[1], pj) for i, pj in zip(info, pjs)]
                if n_rech: parts.append((n_rech, pjd_rech))
                pjt = _wmean(parts)
                pjtxt = f'<br><small class="pjd">prob_jd {pjt:.4f}</small>' if _isnum(pjt) else ''
                tdt += f'<td class="tot">{mt/nt*100:.1f}%<br><small>n={nt:,}</small>{pjtxt}</td>'
            trs += f'<tr class="totr"><td class="b">Total</td>{tdt}</tr>'
            tabla = f'<table class="cmp"><thead><tr><th>bucket</th>{th}</tr></thead><tbody>{trs}</tbody></table>'

            # --- por metodo (desplegable): reglas + V1/V2/V3 con SUS buckets ---
            det = ''
            for nom, info, mono, pjs in metodos_res:
                K = len(info)
                mlbl = {}; cols = []
                for k, (ids, n, t) in enumerate(info, 1):
                    lbl = f"Bucket {k}"; cols.append(lbl)
                    for nro in ids: mlbl[nro] = lbl
                bloques = ''
                for k, (ids, n, t) in enumerate(info, 1):
                    rrows = ''
                    for nro in sorted(ids):
                        ni = int(ncl[nro]); mi = int(mal[nro]); ti = mi/ni if ni else 0
                        rrows += (f'<tr><td class="rule">[{nro}] {esc(reglamap.get(nro,""))}</td>'
                                  f'<td>{ti*100:.1f}%</td><td>{ni/tot_n*100:.1f}%</td><td>{ni:,}</td></tr>')
                    bloques += (f'<div class="bk"><div class="bkh" style="background:{colbucket(k,K)}">'
                                f'Bucket {k} · {len(ids)} regla(s) · tasa {t*100:.1f}% · n={n:,}</div>'
                                f'<div class="tw"><table class="t"><thead><tr><th>estrategia</th>'
                                f'<th>tasa malos</th><th>% del total</th><th>N</th></tr></thead>'
                                f'<tbody>{rrows}</tbody></table></div></div>')
                if n_rech:
                    bloques += (f'<div class="bk"><div class="bkh rj">'
                                f'Rechazo · sin estrategia · tasa {t_rech*100:.1f}% · n={n_rech:,}</div>'
                                f'<div class="tw"><table class="t"><thead><tr><th>estrategia</th>'
                                f'<th>tasa malos</th><th>% del total</th><th>N</th></tr></thead>'
                                f'<tbody><tr><td class="rule">(no capturado por ninguna estrategia)</td>'
                                f'<td>{t_rech*100:.1f}%</td><td>{n_rech/tot_n*100:.1f}%</td><td>{n_rech:,}</td>'
                                f'</tr></tbody></table></div></div>')
                v1 = v1_html(d.get('v1'), mlbl, cols)
                v2 = vb_html(d.get('v2'), mlbl, cols, 'V2')
                v3 = vb_html(d.get('v3'), mlbl, cols, 'V3')
                v3t = v3_tipo_html(d.get('v3'), mlbl, cols)
                det += (f'<details><summary>{esc(nom)} — {K} buckets {"✓" if mono else "✗"}</summary>'
                        f'<h4>Reglas por bucket</h4>{bloques}'
                        f'<h4>V1 · base de campañas (p_fecinformacion × bucket)</h4>{v1}'
                        f'<h4>V2 · base inicial (por bucket)</h4>{v2}'
                        f'<h4>V3 · no campaña (por bucket)</h4>{v3}'
                        f'<h4>V3 · no campaña (p_fecinformacion × {esc(col_tipo)} × bucket)</h4>{v3t}'
                        f'</details>')

            scn_blocks.append(
                f'<div class="scn" id="s{sid}">'
                f'<h2>{esc(nombre)}</h2>'
                f'<h3>Mapa de agrupación <small>(qué estrategias junta cada método)</small></h3><div class="mapa">{mapa}</div>'
                f'<h3>Tasa de riesgo por bucket <small>(con prob_jd promedio)</small></h3>{tabla}'
                f'<h3>Por método <small>(reglas + distribución V1 / V2 / V3 con los buckets de cada método)</small></h3><div class="det">{det}</div>'
                f'</div>')
            grp.append(f'<option value="s{sid}">{esc(nombre)}</option>')
            sid += 1
        grp.append('</optgroup>')
        opts.append("".join(grp))

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
/* ---- mapa ---- */
.mapa{display:flex;flex-direction:column;gap:8px;margin-bottom:6px}
.mrow{display:flex;gap:14px;align-items:flex-start;background:#fff;border:1px solid #d8e3df;border-radius:10px;padding:9px 13px}
.mname{flex:0 0 200px;font-weight:700;color:#23433c;font-size:13.5px;line-height:1.5}
.chips{display:flex;flex-wrap:wrap;gap:6px;flex:1}
.chip{border-radius:8px;padding:4px 9px;font-size:12px;color:#10241f;border:1px solid #0000001f;white-space:nowrap}
.ok{background:#c6efce;color:#1a7a4a;border-radius:8px;padding:2px 8px;font-size:11px;font-weight:700;margin-left:6px}
.bad{background:#ffc7ce;color:#b23b30;border-radius:8px;padding:2px 8px;font-size:11px;font-weight:700;margin-left:6px}
/* ---- tablas (con bordes en TODAS las celdas) ---- */
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
table.cmp td.b{background:#eef7f5;font-weight:700;color:#23433c}
table.cmp td.empty{background:#fafbfb}
table.cmp small{color:#7c8c88}
table.cmp small.pjd{color:#0a5a52;font-weight:600}
/* ---- Rechazo (gris) y Total ---- */
.chip.rj{background:#e2e6e5;border:1px solid #00000026;color:#4a5a56}
table.t td.rj,table.t th.rj,table.cmp td.rj,table.cmp th.rj{background:#eceff0;color:#4a5a56}
table.cmp td.b.rj{background:#e2e6e5;color:#4a5a56}
.bkh.rj{background:#e2e6e5;color:#4a5a56}
tr.rjr td{background:#eceff0;color:#4a5a56}
.tot,td.tot,th.tot{background:#dff0ed !important;font-weight:700;color:#0a5a52}
tr.totr td{background:#cfe9e4 !important;font-weight:700;color:#084b44;border-top:2px solid #0a7d74}
/* ---- detalle por metodo ---- */
.det details{background:#fff;border:1px solid #d8e3df;border-radius:10px;margin:8px 0;padding:6px 14px}
.det summary{cursor:pointer;font-weight:700;color:#007a72;padding:8px 2px;font-size:14px}
.det h4{color:#23433c;font-size:13px;margin:14px 0 6px;text-transform:uppercase;letter-spacing:.3px}
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
           f'<header><h1>{esc(titulo)}</h1><div class="sub">5 métodos · chips = bucket [estrategias] · tasa · n. Verde = menor riesgo, rojo = mayor.</div>'
           f'<div class="selwrap"><select onchange="showScn(this.value)">{"".join(opts)}</select></div></header>'
           f'<div class="wrap">{"".join(scn_blocks)}</div><script>{JS}</script></body></html>')

    with open(salida_html, "w", encoding="utf-8") as f:
        f.write(doc)
    print(f"OK -> {salida_html}  ({sid} escenarios)")
    return salida_html
