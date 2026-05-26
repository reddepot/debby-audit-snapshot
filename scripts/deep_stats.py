#!/usr/bin/env python3
"""Analyse profonde de DEBBY pour le référentiel d'audit. Stats riches, multi-axes.
Une passe Table A (chunks 871 shards) + side-tables + sample vector shards depuis OS.
Sortie JSON + tableaux markdown-friendly."""
import glob, json, collections, re, statistics as S, subprocess, tempfile, os
import pyarrow.parquet as pq
A=sorted(glob.glob("/root/embed/chunks/chunks_*.parquet"))
print(f"=== DEEP STATS DEBBY — {len(A)} shards ===",flush=True)

# === PASSE TABLE A (metadata + text length seulement, memory-safe) ===
W=set()  # work_ids vus
TLEN=[]; TBYTES=[]  # texte: chars, bytes
TITLE_LEN=[]; TITLE_BYTES=[]
NCHUNKS=collections.Counter(); CHUNKS_PER_WORK={}
ORIG=collections.Counter(); STYPE=collections.Counter(); BLANG=collections.Counter()
DTYPE=collections.Counter(); EBM=collections.Counter(); SSTUDY=collections.Counter()
YEAR_BUCKET=collections.Counter()
HAS_SST=0; IS_OH=0; FOREIGN=0
DOI_PRESENT=0; TITLE_PRESENT=0; VENUE_PRESENT=0; AUTHORS_PRESENT=0; CONCEPTS_PRESENT=0
VENUE=collections.Counter(); CONCEPT=collections.Counter()
# crosstab year×source_type
YEAR_X_STYPE=collections.Counter()
# EBM check : titre dit-il vraiment "meta-analysis"/"systematic review" pour ebm=1 ?
EBM1_TITLE_OK=0; EBM1_TITLE_KO=0
META_PAT=re.compile(r"(?i)meta-?analysis|forest plot|systematic review|prisma")
n=0; chk=0
for f in A:
    t=pq.read_table(f,columns=["work_id","title","text","authors","venue","year","doi","doc_type","source_type","body_lang","ebm","study_type","is_oh","has_sst","is_foreign","origin","concepts","n_chunks","chunk_index"])
    rows=t.to_pylist()
    for r in rows:
        chk+=1
        tx=r["text"] or ""; ti=(r["title"] or "").strip()
        TLEN.append(len(tx)); TBYTES.append(len(tx.encode("utf-8")))
        w=r["work_id"]
        if w in W: continue
        W.add(w)
        # title
        TITLE_LEN.append(len(ti)); TITLE_BYTES.append(len(ti.encode("utf-8")))
        # distributions par work
        ORIG[r["origin"]]+=1; STYPE[r["source_type"]]+=1; BLANG[r["body_lang"]]+=1
        DTYPE[r["doc_type"]]+=1; EBM[r["ebm"]]+=1; SSTUDY[r["study_type"]]+=1
        if r["has_sst"]: HAS_SST+=1
        if r["is_oh"]: IS_OH+=1
        if r["is_foreign"]: FOREIGN+=1
        y=r["year"] or 0; bk = "0" if y==0 else (f"{y//10*10}s" if y>=1900 else "ancien")
        YEAR_BUCKET[bk]+=1
        YEAR_X_STYPE[(bk,r["source_type"])]+=1
        # citabilité
        if r["doi"]: DOI_PRESENT+=1
        if ti: TITLE_PRESENT+=1
        if (r["venue"] or "").strip(): VENUE_PRESENT+=1; VENUE[(r["venue"] or "").strip()[:60]]+=1
        if (r["authors"] or "").strip(): AUTHORS_PRESENT+=1
        if (r["concepts"] or "").strip():
            CONCEPTS_PRESENT+=1
            for c in re.split(r",\s*",(r["concepts"] or "")[:300])[:6]:
                if c and len(c)>2: CONCEPT[c.strip()[:40]]+=1
        CHUNKS_PER_WORK[w]=r["n_chunks"]
        # EBM check
        if r["ebm"]==1:
            if META_PAT.search(ti or ""): EBM1_TITLE_OK+=1
            else: EBM1_TITLE_KO+=1
    n+=1
    if n%200==0: print(f"  {n}/{len(A)} shards processed",flush=True)

WS=len(W); CHK=chk
print(f"\n=== ÉCHELLE ===")
print(f"works={WS:,} chunks={CHK:,}")
print(f"\n=== TEXTE (chunk) ===")
print(f"chars  : médiane={int(S.median(TLEN))} moy={int(S.mean(TLEN))} p5={int(sorted(TLEN)[int(len(TLEN)*0.05)])} p95={int(sorted(TLEN)[int(len(TLEN)*0.95)])} max={max(TLEN)}")
print(f"bytes  : médiane={int(S.median(TBYTES))} moy={int(S.mean(TBYTES))} max={max(TBYTES)}")
print(f"\n=== TITRE ===")
print(f"chars  : médiane={int(S.median(TITLE_LEN))} moy={int(S.mean(TITLE_LEN))} max={max(TITLE_LEN)}")
print(f"titres vides : {sum(1 for x in TITLE_LEN if x==0):,} ({100*sum(1 for x in TITLE_LEN if x==0)/WS:.2f}%)")
print(f"\n=== CITABILITÉ (par work) ===")
print(f"DOI présent : {DOI_PRESENT:,} ({100*DOI_PRESENT/WS:.1f}%)")
print(f"titre présent : {TITLE_PRESENT:,} ({100*TITLE_PRESENT/WS:.1f}%)")
print(f"venue présent : {VENUE_PRESENT:,} ({100*VENUE_PRESENT/WS:.1f}%)")
print(f"authors présent : {AUTHORS_PRESENT:,} ({100*AUTHORS_PRESENT/WS:.1f}%)")
print(f"concepts présent : {CONCEPTS_PRESENT:,} ({100*CONCEPTS_PRESENT/WS:.1f}%)")
print(f"\n=== TOP 25 VENUES ===")
for v,c in VENUE.most_common(25): print(f"  {c:>6,}  {v}")
print(f"\n=== TOP 30 CONCEPTS (OpenAlex) ===")
for c,n in CONCEPT.most_common(30): print(f"  {n:>6,}  {c}")
print(f"\n=== EBM=1 (méta/SR) — vérif titre ===")
print(f"ebm=1 avec titre 'meta'/'systematic' : {EBM1_TITLE_OK:,} | sans ces mots dans titre : {EBM1_TITLE_KO:,}")
print(f"  → faux-positifs possibles ebm=1 : {EBM1_TITLE_KO:,} ({100*EBM1_TITLE_KO/max(EBM1_TITLE_OK+EBM1_TITLE_KO,1):.1f}%)")
print(f"\n=== CROSSTAB YEAR × SOURCE_TYPE (top 20) ===")
for k,c in sorted(YEAR_X_STYPE.items(),key=lambda x:-x[1])[:20]: print(f"  {c:>7,}  {k[0]} × {k[1]}")
print(f"\n=== SIDE-TABLES (deep-dive) ===")
# rétractations
rt=json.load(open("/root/retracted_work_ids.json")) if os.path.exists("/root/retracted_work_ids.json") else {}
print(f"rétractations flaggées : {len(rt.get('flagged',[])):,}")
detail=rt.get("detail",{})
nat=collections.Counter(d["nature"] for d in detail.values())
print(f"  natures: {dict(nat.most_common())}")
top_reason=collections.Counter(d["reason"][:50] for d in detail.values() if d.get("reason"))
print(f"  top raisons:")
for r,c in top_reason.most_common(8): print(f"    {c:>3}  {r}")
# year_title_fix
import sqlite3
if os.path.exists("/root/year_title_fix.db"):
    c=sqlite3.connect("/root/year_title_fix.db")
    okn=c.execute("SELECT COUNT(*) FROM fix WHERE status='ok' AND year IS NOT NULL").fetchone()[0]
    okt=c.execute("SELECT COUNT(*) FROM fix WHERE status='ok' AND title!=''").fetchone()[0]
    years=collections.Counter(r[0] for r in c.execute("SELECT year FROM fix WHERE status='ok' AND year IS NOT NULL"))
    print(f"year_title_fix : {okn:,} years + {okt:,} titles récupérés via Crossref")
    print(f"  top années récupérées: {dict(years.most_common(10))}")
# body_lang_fix
if os.path.exists("/root/body_lang_fix.json"):
    bl=json.load(open("/root/body_lang_fix.json"))
    print(f"body_lang_fix : {len(bl):,} works analysés")
# entities
if os.path.exists("/root/entities.jsonl"):
    CAS=collections.Counter(); SUB=collections.Counter(); MP=collections.Counter(); MET=collections.Counter(); PAT=collections.Counter()
    n=0
    for l in open("/root/entities.jsonl"):
        try: e=json.loads(l)
        except: continue
        n+=1
        for k in e.get("cas",[]): CAS[k]+=1
        for k in e.get("substances",[]): SUB[k]+=1
        for k in e.get("tableau_mp",[]): MP[k]+=1
        for k in e.get("metiers",[]): MET[k]+=1
        for k in e.get("pathologies",[]): PAT[k]+=1
    print(f"\n=== ENTITÉS (graph seed) — sur {n:,} works ===")
    print(f"TOP 20 substances :");
    for s,c in SUB.most_common(20): print(f"  {c:>5,}  {s}")
    print(f"TOP 15 pathologies :")
    for p,c in PAT.most_common(15): print(f"  {c:>5,}  {p}")
    print(f"TOP 15 métiers :")
    for m,c in MET.most_common(15): print(f"  {c:>5,}  {m}")
    print(f"TOP 20 CAS :")
    for k,c in CAS.most_common(20): print(f"  {c:>5,}  {k}")
    print(f"TOP 15 tableaux MP :")
    for k,c in MP.most_common(15): print(f"  {c:>5,}  Tableau {k}")
print("\n=== VECTEURS — stats sur 5 shards échantillonnés ===")
import numpy as np, random
random.seed(3); sample_idx=random.sample(range(len(A)),5)
all_norms=[]; pairwise_cos=[]
for k in sample_idx:
    cp=A[k]; name=os.path.basename(cp).replace("chunks_","vectors_")
    d=tempfile.mkdtemp(); subprocess.run(["rclone","copy",f"meddata:meddata-lake/debby_embed/vectors/{name}",d],timeout=300)
    vp=os.path.join(d,name)
    if not os.path.exists(vp): continue
    tb=pq.read_table(vp,columns=["vector"])
    n_rows=tb.num_rows
    # sample 200 vectors from this shard
    idx_s=random.sample(range(n_rows),min(200,n_rows))
    vecs=np.array([tb.column("vector")[i].as_py() for i in idx_s],dtype=np.float32)
    norms=np.linalg.norm(vecs,axis=1)
    all_norms.extend(norms.tolist())
    # pairwise cos (intra-shard)
    vecs_n=vecs/(norms[:,None]+1e-9)
    cos_mat=vecs_n@vecs_n.T
    upper=cos_mat[np.triu_indices_from(cos_mat,k=1)]
    pairwise_cos.extend(upper.tolist())
    import shutil; shutil.rmtree(d,ignore_errors=True)
    print(f"  {name}: n={len(idx_s)} norme_med={float(np.median(norms)):.4f} cos_med_intra={float(np.median(upper)):.3f}",flush=True)
print(f"\nNORME L2 (1000 vec) : médiane={S.median(all_norms):.4f} min={min(all_norms):.4f} max={max(all_norms):.4f} std={S.stdev(all_norms):.6f}")
print(f"COSINE intra-shard (~100K pairs) : médiane={S.median(pairwise_cos):.3f} p25={sorted(pairwise_cos)[len(pairwise_cos)//4]:.3f} p75={sorted(pairwise_cos)[3*len(pairwise_cos)//4]:.3f}")
print("[DEEP_STATS_DONE]")
