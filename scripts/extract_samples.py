#!/usr/bin/env python3
"""Extraire des échantillons illustratifs de DEBBY pour le référentiel d'audit.
1 chunk par source_type (litterature/sst/clinique/toxico/fiche_metier/reglementaire) + 1 fiche/abstract,
avec métadonnées complètes + 700c de texte. Plus stats détaillées du corpus."""
import glob, json, random, collections, pyarrow.parquet as pq
A=sorted(glob.glob("/root/embed/chunks/chunks_*.parquet"))
random.seed(11); random.shuffle(A)
want={"litterature":1,"clinique":1,"sst":1,"fiche_metier":1,"toxico":1,"reglementaire":1}
samples={}
FIELDS=["chunk_id","work_id","title","title_en","authors","venue","year","doi","doc_type","source_type","body_lang","ebm","study_type","is_oh","has_sst","clin","is_foreign","origin","concepts","n_chunks","chunk_index"]
for f in A:
    if all(v==0 for v in want.values()): break
    t=pq.read_table(f,columns=FIELDS+["text"])
    rows=t.to_pylist(); random.shuffle(rows)
    for r in rows:
        st=r["source_type"]
        if want.get(st,0)<=0: continue
        tx=r.get("text") or ""; ti=(r.get("title") or "").strip()
        if len(tx)<500 or len(ti)<8: continue
        samples[st]=r; want[st]=0
        if all(v==0 for v in want.values()): break
print("=== ÉCHANTILLONS ILLUSTRATIFS PAR source_type ===")
for k,v in samples.items():
    print(f"\n──── source_type={k} ────")
    meta={fld:v[fld] for fld in FIELDS}
    print("METADATA:",json.dumps(meta,ensure_ascii=False)[:700])
    print("TEXT_EXCERPT[700c]:")
    print((v["text"] or "")[:700].replace("\r"," "))
print("\n=== STATS GLOBALES ===")
# distributions par work
seen=set(); R={"origin":collections.Counter(),"source_type":collections.Counter(),"body_lang":collections.Counter(),
    "doc_type":collections.Counter(),"ebm":collections.Counter(),"study_type":collections.Counter(),
    "has_sst":collections.Counter(),"is_oh":collections.Counter(),"year_bucket":collections.Counter()}
ncw={}; titles_with_venue=0; with_doi=0; w_total=0
for f in A:
    t=pq.read_table(f,columns=["work_id","origin","source_type","body_lang","doc_type","ebm","study_type","has_sst","is_oh","year","doi","title","venue","n_chunks"])
    for r in t.to_pylist():
        w=r["work_id"]
        if w in seen: continue
        seen.add(w); w_total+=1
        for c in ("origin","source_type","body_lang","doc_type","study_type"): R[c][r[c]]+=1
        R["ebm"][r["ebm"]]+=1; R["has_sst"][r["has_sst"]]+=1; R["is_oh"][r["is_oh"]]+=1
        y=int(r["year"] or 0); bk = "0" if y==0 else (f"{y//10*10}s" if y>=1900 else "ancien")
        R["year_bucket"][bk]+=1
        if r["doi"]: with_doi+=1
        if (r["title"] or "").strip() and (r["venue"] or "").strip(): titles_with_venue+=1
        ncw[w]=r["n_chunks"]
print(f"works uniques: {w_total:,}")
print("origin:",dict(R["origin"].most_common(8)))
print("source_type:",dict(R["source_type"].most_common(8)))
print("body_lang (top10):",dict(R["body_lang"].most_common(10)))
print("doc_type:",dict(R["doc_type"].most_common(8)))
print("ebm (1=meta..9=unknown):",dict(sorted(R["ebm"].items())))
print("study_type (top10):",dict(R["study_type"].most_common(10)))
print("has_sst=1:",R["has_sst"][1],"is_oh=1:",R["is_oh"][1])
print("year_bucket:",dict(sorted(R["year_bucket"].items())))
import statistics as S
ncv=sorted(ncw.values())
print(f"chunks/work: médiane={S.median(ncv)} moyenne={S.mean(ncv):.1f} p95={ncv[int(len(ncv)*0.95)]} max={max(ncv)}")
print(f"citabilité: avec DOI={with_doi:,} ({100*with_doi/w_total:.1f}%) | avec titre+venue={titles_with_venue:,} ({100*titles_with_venue/w_total:.1f}%)")
