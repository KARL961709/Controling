#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Construye un arbol HTML explicable a partir de la tabla de segmentacion del score.
import json

# --- Datos: cada fila = una hoja. Solo se listan las condiciones ACTIVAS (no "(todos)") ---
# claves: deuda, ent, entv, mora, edad, ring, txs3, txs6, ptxs3, ppas3, ppas6max, pcomp3, punt, seg, flg
R = [
 ({"ring":"> 3,372","ppas3":"> 221","punt":"<= 6","seg":"<= 2"}, 1786,0.1,927.7408,"G1"),
 ({"ring":"<= 3,372","ppas3":"> 221","punt":"<= 6","seg":"<= 2"}, 2512,0.1,918.4061,"G1"),
 ({"ent":"<= 2","edad":"> 58","ring":"> 3,098","ppas3":"<= 221","punt":"<= 6","seg":"<= 2"}, 3148,0.2,911.4828,"G1"),
 ({"ent":"<= 2","edad":"<= 58","ring":"> 3,098","ppas3":"<= 221","punt":"<= 6","seg":"<= 2"}, 2803,0.2,909.2947,"G1"),
 ({"ent":"> 2","ring":"> 3,098","ppas3":"<= 221","punt":"<= 6","seg":"<= 2"}, 1828,0.1,904.1822,"G1"),
 ({"ring":"<= 3,098","ppas3":"<= 221","punt":"<= 6","seg":"<= 2","flg":"> 0"}, 3661,0.2,902.8203,"G1"),
 ({"mora":"<= 2,256","ring":"<= 3,098","ppas3":"<= 221","punt":"<= 6","seg":"<= 2","flg":"<= 0"}, 2914,0.2,896.0614,"G1"),
 ({"mora":"(2,256, 3,162]","ring":"<= 3,098","ppas3":"<= 221","punt":"<= 6","seg":"<= 2","flg":"<= 0"}, 2439,0.1,895.9188,"G1"),
 ({"mora":"> 3,162","ring":"<= 3,098","ppas3":"<= 221","punt":"<= 6","seg":"<= 2","flg":"<= 0"}, 5614,0.3,894.3835,"G1"),
 ({"mora":"<= 3,418","ppas6max":"> 18","pcomp3":"> 10","punt":"<= 6","seg":"> 2"}, 19231,1.1,893.5797,"G1"),
 ({"mora":"<= 3,418","ppas6max":"> 18","pcomp3":"<= 10","punt":"<= 6","seg":"> 2"}, 2587,0.2,892.0128,"G1"),
 ({"ent":"<= 2","mora":"> 3,418","edad":"> 40","ppas6max":"> 18","punt":"<= 6","seg":"> 2"}, 7768,0.5,891.79,"G1"),
 ({"ent":"<= 2","mora":"> 3,418","edad":"<= 40","ppas6max":"> 18","punt":"<= 6","seg":"> 2"}, 1861,0.1,889.4331,"G1"),
 ({"ent":"> 2","mora":"> 3,418","ppas6max":"> 18","punt":"<= 6","seg":"> 2"}, 1866,0.1,886.4834,"G1"),
 ({"ent":"<= 2","entv":"<= 0","edad":"> 58","ppas6max":"<= 18","punt":"<= 6","seg":"(2, 4]"}, 33011,1.9,886.3796,"G1"),
 ({"ent":"> 2","entv":"<= 0","edad":"> 58","ppas6max":"<= 18","punt":"<= 6","seg":"(2, 4]"}, 4121,0.2,885.7508,"G1"),
 ({"entv":"<= 0","edad":"<= 58","ppas6max":"<= 18","punt":"<= 6","seg":"(2, 4]"}, 28028,1.7,884.963,"G1"),
 ({"entv":"> 0","mora":"<= 2,084","ppas6max":"<= 18","punt":"<= 6","seg":"(2, 4]"}, 14146,0.8,880.6282,"G1"),
 ({"ent":"<= 2","entv":"> 0","mora":"> 2,084","ppas6max":"<= 18","punt":"<= 6","seg":"(2, 4]"}, 25022,1.5,878.2592,"G1"),
 ({"ent":"> 2","entv":"> 0","mora":"> 2,084","ppas6max":"<= 18","punt":"<= 6","seg":"(2, 4]"}, 8762,0.5,877.9056,"G1"),
 ({"entv":"<= 0","edad":"> 40","ppas6max":"<= 18","punt":"<= 6","seg":"> 4"}, 10880,0.6,877.0254,"G1"),
 ({"entv":"<= 0","edad":"<= 40","ppas6max":"<= 18","punt":"<= 6","seg":"> 4"}, 9992,0.6,876.6161,"G1"),
 ({"entv":"> 0","mora":"<= 2,534","edad":"> 40","ppas6max":"<= 18","punt":"<= 6","seg":"> 4"}, 3679,0.2,871.3884,"G1"),
 ({"entv":"> 0","mora":"<= 2,534","edad":"<= 40","ppas6max":"<= 18","punt":"<= 6","seg":"> 4"}, 3421,0.2,866.8971,"G1"),
 ({"entv":"> 0","mora":"(2,534, 3,686]","ppas6max":"<= 18","punt":"<= 6","seg":"> 4"}, 3755,0.2,865.3358,"G1"),
 ({"entv":"> 0","mora":"> 3,686","ppas6max":"<= 18","punt":"<= 6","seg":"> 4"}, 2730,0.2,861.7465,"G1"),
 ({"mora":"<= 2,534","edad":"> 70","punt":"> 6","seg":"<= 2"}, 3316,0.2,789.2229,"G2"),
 ({"mora":"<= 2,084","edad":"(62, 70]","punt":"> 6","seg":"<= 2"}, 2119,0.1,781.1543,"G2"),
 ({"mora":"(2,084, 2,534]","edad":"(62, 70]","punt":"> 6","seg":"<= 2"}, 1797,0.1,775.828,"G2"),
 ({"mora":"<= 2,256","edad":"> 70","punt":"> 6","seg":"> 2"}, 9867,0.6,773.3973,"G2"),
 ({"mora":"(2,256, 2,534]","edad":"> 70","punt":"> 6","seg":"> 2"}, 4067,0.2,767.1495,"G2"),
 ({"mora":"<= 2,084","edad":"(62, 70]","punt":"> 6","seg":"> 2"}, 13413,0.8,763.4362,"G2"),
 ({"mora":"(2,084, 2,534]","edad":"(62, 70]","punt":"> 6","seg":"> 2","flg":"> 0"}, 1870,0.1,756.6909,"G2"),
 ({"mora":"(2,084, 2,534]","edad":"(62, 70]","punt":"> 6","seg":"> 2","flg":"<= 0"}, 10586,0.6,755.3861,"G2"),
 ({"mora":"(2,534, 3,162]","edad":"> 62","punt":"> 6","seg":"<= 4"}, 14222,0.8,754.3777,"G2"),
 ({"mora":"(3,162, 3,686]","edad":"> 62","punt":"> 6","seg":"<= 4","flg":"> 0"}, 1985,0.1,748.9597,"G2"),
 ({"mora":"> 3,686","edad":"> 62","punt":"> 6","seg":"<= 4","flg":"> 0"}, 9069,0.5,748.5645,"G2"),
 ({"mora":"(3,162, 3,418]","edad":"> 62","punt":"> 6","seg":"<= 4","flg":"<= 0"}, 4222,0.2,747.2991,"G2"),
 ({"mora":"(3,418, 3,686]","edad":"> 62","punt":"> 6","seg":"<= 4","flg":"<= 0"}, 4053,0.2,746.7945,"G2"),
 ({"mora":"> 3,686","edad":"> 62","punt":"> 6","seg":"<= 4","flg":"<= 0"}, 33995,2.0,745.958,"G2"),
 ({"mora":"(2,534, 3,686]","edad":"> 62","punt":"> 6","seg":"> 4"}, 24730,1.5,740.8469,"G2"),
 ({"mora":"> 3,686","edad":"> 62","punt":"> 6","seg":"> 4"}, 41980,2.5,733.312,"G2"),
 ({"mora":"<= 3,418","edad":"(52, 62]","ptxs3":"> 78","punt":"> 6","seg":"<= 4"}, 3424,0.2,732.0333,"G2"),
 ({"mora":"<= 3,418","edad":"(52, 62]","ptxs3":"<= 78","punt":"> 6","seg":"<= 4"}, 116962,6.9,731.417,"G2"),
 ({"mora":"<= 3,418","edad":"(52, 62]","punt":"> 6","seg":"> 4"}, 4148,0.2,720.4048,"G2"),
 ({"deuda":"<= 231","mora":"> 3,418","edad":"(52, 62]","punt":"> 6"}, 5911,0.3,714.946,"G2"),
 ({"deuda":"> 231","mora":"> 3,418","edad":"(52, 62]","txs3":"> 55","punt":"> 6"}, 5546,0.3,705.6394,"G2"),
 ({"deuda":"> 231","mora":"> 3,418","edad":"(52, 62]","txs3":"<= 55","punt":"> 6"}, 134758,7.9,703.716,"G2"),
 ({"mora":"<= 2,534","edad":"<= 52","punt":"> 6"}, 311816,18.4,701.2194,"G4"),
 ({"ent":"<= 2","mora":"> 2,534","edad":"(40, 52]","ppas3":"> 43","punt":"> 6"}, 28450,1.7,683.8642,"G5"),
 ({"ent":"<= 2","mora":"> 2,534","edad":"(40, 52]","ppas3":"<= 43","punt":"> 6"}, 294652,17.4,681.0835,"G5"),
 ({"ent":"<= 2","mora":"(2,534, 3,162]","edad":"<= 40","punt":"> 6"}, 92603,5.5,672.6847,"G5"),
 ({"ent":"<= 2","mora":"(3,162, 3,686]","edad":"<= 40","punt":"> 6"}, 43314,2.6,667.5225,"G5"),
 ({"ent":"<= 2","mora":"> 3,686","edad":"(34, 40]","ppas3":"> 43","punt":"> 6"}, 8367,0.5,665.6162,"G5"),
 ({"ent":"<= 2","mora":"> 3,686","edad":"(34, 40]","ppas3":"<= 43","punt":"> 6"}, 69503,4.1,663.128,"G5"),
 ({"ent":"<= 2","mora":"> 3,686","edad":"<= 34","txs6":"> 81","punt":"> 6"}, 2290,0.1,660.4677,"G5"),
 ({"ent":"<= 2","mora":"> 3,686","edad":"<= 34","txs6":"<= 81","punt":"> 6"}, 47087,2.8,658.1658,"G5"),
 ({"ent":"> 2","mora":"> 2,534","edad":"(40, 52]","txs6":"> 81","punt":"> 6"}, 4539,0.3,652.3098,"G5"),
 ({"ent":"> 2","mora":"> 2,534","edad":"(40, 52]","txs6":"<= 81","punt":"> 6"}, 79467,4.7,650.0858,"G5"),
 ({"ent":"> 2","mora":"(2,534, 3,686]","edad":"<= 40","punt":"> 6"}, 29365,1.7,630.6995,"G5"),
 ({"ent":"> 2","entv":"<= 0","mora":"> 3,686","edad":"(36, 40]","punt":"> 6"}, 1774,0.1,613.0862,"G5"),
 ({"ent":"> 2","entv":"> 0","mora":"> 3,686","edad":"(36, 40]","punt":"> 6"}, 9452,0.6,608.12,"G5"),
 ({"ent":"> 2","mora":"> 3,686","edad":"(34, 36]","punt":"> 6"}, 6034,0.4,604.1936,"G5"),
 ({"ent":"> 2","mora":"> 3,686","edad":"<= 34","flg":"> 0","punt":"> 6"}, 1804,0.1,576.949,"G5"),
 ({"ent":"> 2","mora":"> 3,686","edad":"<= 34","flg":"<= 0","punt":"> 6"}, 7626,0.4,575.3621,"G5"),
]

HUM = {
 "punt":"Puntuación calif. (cal_cat)","seg":"Segmentación GDP v2","edad":"Edad",
 "mora":"Máx. días mora castigo","ent":"N° entidades castigo","entv":"N° entidades castigo (vida)",
 "ppas6max":"Saldo prom. pasivo máx U6M","ppas3":"Saldo prom. pasivo U3M",
 "pcomp3":"Saldo pasivo componentes U3M","ring":"Rango ingreso","txs3":"Saldo fdp txs U3M",
 "txs6":"Saldo fdp txs U6M","ptxs3":"Saldo prom txs U3M","deuda":"Deuda castigada",
 "flg":"Flag trx presencial 12M (c216)",
}
# Orden de anidamiento (raiz -> hojas). punt primero (separa G1 del resto).
ORDER = ["punt","seg","edad","mora","ent","entv","ppas6max","ppas3","pcomp3","ring","txs3","txs6","ptxs3","deuda","flg"]

def new_node(var=None, val=None):
    return {"var":var,"val":val,"children":{},"own":None,"rules":None}

root = new_node()
TOTAL = sum(r[1] for r in R)
for conds, n, pct, score, q in R:
    path = [(c, conds[c]) for c in ORDER if c in conds]
    cur = root
    for edge in path:
        if edge not in cur["children"]:
            cur["children"][edge] = new_node(edge[0], edge[1])
        cur = cur["children"][edge]
    cur["own"] = {"n":n,"pct":pct,"score":score,"q":q}
    cur["rules"] = [(HUM[c], conds[c]) for c in ORDER if c in conds]

def agg(node):
    n=0; ssum=0.0; qc={}
    if node["own"]:
        o=node["own"]; n+=o["n"]; ssum+=o["n"]*o["score"]; qc[o["q"]]=qc.get(o["q"],0)+o["n"]
    kids=[]
    for edge,ch in node["children"].items():
        agg(ch); kids.append(ch)
        n+=ch["_n"]; ssum+=ch["_n"]*ch["_score"]
        for k,v in ch["_qc"].items(): qc[k]=qc.get(k,0)+v
    kids.sort(key=lambda c: -c["_score"])
    node["_kids"]=kids; node["_n"]=n; node["_score"]=(ssum/n if n else 0); node["_qc"]=qc
    node["_q"]=max(qc.items(), key=lambda kv: kv[1])[0] if qc else None
agg(root)

def to_json(node, depth=0):
    return {
        "var": HUM.get(node["var"], node["var"]) if node["var"] else None,
        "val": node["val"],
        "n": node["_n"], "pct": round(node["_n"]/TOTAL*100,2), "score": round(node["_score"],1),
        "q": node["_q"], "depth": depth,
        "leaf": node["own"] is not None,
        "leafScore": node["own"]["score"] if node["own"] else None,
        "leafQ": node["own"]["q"] if node["own"] else None,
        "rules": node["rules"] or [],
        "kids": [to_json(c, depth+1) for c in node["_kids"]],
    }
TREE = to_json(root)
TREE["var"]="Población total"

# tabla plana (hojas) ordenada por score desc
FLAT = sorted([
    {"rules":[(HUM[c],conds[c]) for c in ORDER if c in conds],"n":n,"pct":pct,"score":score,"q":q}
    for conds,n,pct,score,q in R], key=lambda r:-r["score"])

payload = {"tree":TREE,"flat":FLAT,"total":TOTAL}
open("arbol_data.json","w").write(json.dumps(payload, ensure_ascii=False))
print("hojas:",len(R),"| poblacion total n:",TOTAL,"| quintiles:",sorted({r[4] for r in R}))
