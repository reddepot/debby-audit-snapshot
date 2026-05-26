#!/usr/bin/env python3
"""DEBBY — harness d'évaluation sur le benchmark métier FR. Retrieval PLUGGABLE (layer2.retrieve).
Métriques : concept-recall@k (requêtes normales), no-answer accuracy (requêtes hors-corpus),
couverture source_type attendu, routage needs_mcp. Agrégé par catégorie + global.
Usage: eval_benchmark.py --bench /root/debby_benchmark_fr.jsonl --k 10 [--stub]"""
import json, argparse, collections, re, unicodedata
ap=argparse.ArgumentParser()
ap.add_argument("--bench",default="/root/debby_benchmark_fr.jsonl")
ap.add_argument("--k",type=int,default=10)
ap.add_argument("--stub",action="store_true",help="retrieval factice (test du harness sans LanceDB)")
ap.add_argument("--out",default="/root/eval_report.json")
a=ap.parse_args()

def norm(s): return unicodedata.normalize("NFKD",(s or "").lower()).encode("ascii","ignore").decode()
def concept_hit(concept,texts):
    c=norm(concept); blob=norm(" ".join(texts))
    # match souple : tous les mots significatifs du concept présents
    words=[w for w in re.findall(r"[a-z0-9]+",c) if len(w)>2]
    return all(w in blob for w in words) if words else False

# --- Retrieval pluggable ---
def get_retriever():
    if a.stub:
        def r(query,k): return []   # stub : renvoie vide → mesure le harness
        return r
    try:
        import layer2  # le module Couche 2 (à écrire), expose retrieve(query,k)->list[dict]
        return layer2.retrieve
    except Exception as e:
        print(f"[!] layer2 indisponible ({e}) → mode --stub. Le harness est prêt, branchera layer2 dès qu'il existe.")
        return lambda q,k: []

retrieve=get_retriever()
rows=[json.loads(l) for l in open(a.bench)]
byc=collections.defaultdict(lambda: collections.Counter())
detail=[]
for r in rows:
    q=r["query"]; cat=r["cat"]; res=retrieve(q,a.k)
    texts=[ (x.get("title","")+" "+x.get("text","")) for x in res]
    stypes=set(x.get("source_type","") for x in res)
    rec={"id":r["id"],"cat":cat,"n_results":len(res)}
    if cat=="hors_corpus":
        # succès = le système signale l'absence (aucun résultat OU score top < seuil OU flag no_answer)
        no_ans = (len(res)==0) or all(x.get("score",1.0)<0.65 for x in res) or any(x.get("no_answer") for x in res)
        rec["no_answer_correct"]=bool(no_ans); byc[cat]["total"]+=1; byc[cat]["no_answer_ok"]+=int(no_ans)
    else:
        exp=r.get("expected_concepts",[])
        hits=sum(1 for c in exp if concept_hit(c,texts))
        rec["concept_recall"]=hits/max(len(exp),1)
        exp_dt=set(r.get("expected_doc_types",[]))
        rec["source_type_cover"]=bool(exp_dt & stypes) if exp_dt else None
        byc[cat]["total"]+=1; byc[cat]["concept_recall_sum"]+=rec["concept_recall"]
        byc[cat]["found_any"]+=int(len(res)>0)
    detail.append(rec)
# agrégation
report={"k":a.k,"n_queries":len(rows),"by_category":{},"overall":{}}
tot_rec=0; tot_n=0; na_ok=0; na_tot=0
for cat,c in byc.items():
    if cat=="hors_corpus":
        report["by_category"][cat]={"total":c["total"],"no_answer_accuracy":round(c["no_answer_ok"]/max(c["total"],1),3)}
        na_ok+=c["no_answer_ok"]; na_tot+=c["total"]
    else:
        report["by_category"][cat]={"total":c["total"],"concept_recall@k":round(c["concept_recall_sum"]/max(c["total"],1),3),"found_any":c["found_any"]}
        tot_rec+=c["concept_recall_sum"]; tot_n+=c["total"]
report["overall"]={"concept_recall@k":round(tot_rec/max(tot_n,1),3),"no_answer_accuracy":round(na_ok/max(na_tot,1),3),
                   "mode":"STUB" if a.stub else "layer2"}
print(json.dumps(report,ensure_ascii=False,indent=1))
json.dump({"report":report,"detail":detail},open(a.out,"w"),ensure_ascii=False,indent=1)
print("[EVAL_HARNESS_READY]" if a.stub else "[EVAL_DONE]")
