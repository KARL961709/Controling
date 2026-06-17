# -*- coding: utf-8 -*-
import json
# claves: deuda, ppas3, ppas6, pact, score, seg
R = [
 ({"score":"> 734"}, 2464,5.4,0.0566,"G1"),
 ({"score":"(702, 734]"}, 2275,5.0,0.0614,"G1"),
 ({"pact":"> 1","score":"(670, 702]"}, 1383,3.0,0.0866,"G1"),
 ({"pact":"<= 1","score":"(670, 702]"}, 1637,3.6,0.0871,"G1"),
 ({"score":"(650, 670]"}, 2331,5.1,0.0969,"G1"),
 ({"ppas6":"> 712","score":"(452, 650]","seg":"<= 4"}, 2266,5.0,0.1578,"G3"),
 ({"deuda":"<= 264","ppas6":"<= 712","score":"(452, 650]","seg":"<= 4"}, 7142,15.7,0.1663,"G3"),
 ({"deuda":"> 264","ppas6":"<= 712","score":"(452, 650]","seg":"<= 4"}, 12876,28.3,0.1742,"G3"),
 ({"ppas3":"> 12","score":"(452, 650]","seg":"> 4"}, 1532,3.4,0.1808,"G4"),
 ({"ppas3":"<= 12","score":"(452, 650]","seg":"> 4"}, 2591,5.7,0.1876,"G4"),
 ({"score":"(374, 452]","seg":"Missing"}, 2747,6.0,0.2962,"G5"),
 ({"score":"(374, 452]"}, 1450,3.2,0.3532,"G5"),
 ({"score":"(242, 374]"}, 2281,5.0,0.6217,"G5"),
 ({"score":"<= 242"}, 2484,5.5,0.7035,"G5"),
]
HUM = {
 "deuda":"Deuda castigada","ppas3":"Saldo prom. pasivo U3M","ppas6":"Saldo prom. pasivo U6M",
 "pact":"Saldo pasivo actual","score":"Score (rango)","seg":"Segmentación GDP v2",
}
ORDER = ["score","seg","pact","ppas6","deuda","ppas3"]

def new_node(var=None,val=None): return {"var":var,"val":val,"children":{},"own":None,"rules":None}
root=new_node(); TOTAL=sum(r[1] for r in R)
for conds,n,pct,rd,q in R:
    path=[(c,conds[c]) for c in ORDER if c in conds]
    cur=root
    for e in path:
        cur=cur["children"].setdefault(e,new_node(e[0],e[1]))
    cur["own"]={"n":n,"pct":pct,"rd":rd,"q":q}
    cur["rules"]=[(HUM[c],conds[c]) for c in ORDER if c in conds]
def agg(node):
    n=0;rs=0.0;qc={}
    if node["own"]:
        o=node["own"];n+=o["n"];rs+=o["n"]*o["rd"];qc[o["q"]]=qc.get(o["q"],0)+o["n"]
    for e,ch in node["children"].items():
        agg(ch);n+=ch["_n"];rs+=ch["_n"]*ch["_rd"]
        for k,v in ch["_qc"].items():qc[k]=qc.get(k,0)+v
    node["_kids"]=sorted(node["children"].values(),key=lambda c:c["_rd"])
    node["_n"]=n;node["_rd"]=(rs/n if n else 0);node["_qc"]=qc
    node["_q"]=max(qc.items(),key=lambda kv:kv[1])[0] if qc else None
agg(root)
def tj(node,d=0):
    return {"var":HUM.get(node["var"],node["var"]) if node["var"] else None,"val":node["val"],
            "n":node["_n"],"pct":round(node["_n"]/TOTAL*100,2),"rd":round(node["_rd"],4),
            "q":node["_q"],"leaf":node["own"] is not None,
            "leafRd":node["own"]["rd"] if node["own"] else None,"leafQ":node["own"]["q"] if node["own"] else None,
            "rules":node["rules"] or [],"kids":[tj(c,d+1) for c in node["_kids"]]}
TREE=tj(root);TREE["var"]="Población total"
FLAT=sorted([{"rules":[(HUM[c],conds[c]) for c in ORDER if c in conds],"n":n,"pct":pct,"rd":rd,"q":q}
             for conds,n,pct,rd,q in R],key=lambda r:r["rd"])
open("arbol_rd_data.json","w").write(json.dumps({"tree":TREE,"flat":FLAT,"total":TOTAL},ensure_ascii=False))
print("hojas:",len(R),"| n total:",TOTAL,"| quintiles:",sorted({r[4] for r in R}),
      "| RD min/max:",min(r[3] for r in R),max(r[3] for r in R))
