#!/usr/bin/env python3
"""Sanity retrieval brute-force (sans LanceDB) sur un échantillon de shards.
A) Test fonctionnel : embedder le TITRE d'un chunk → son propre vecteur doit être dans le top-3 (le
   retrieval marche-t-il du tout ?). B) Cohérence : cosine intra-work >> cosine aléatoire.
C) Requêtes FR MdT → top-5 (jugement). Embed requête via OR (même modèle). Numpy cosine sur le pool."""
import glob, os, subprocess, tempfile, json, random, urllib.request, numpy as np
import pyarrow.parquet as pq
REMOTE="meddata:meddata-lake/debby_embed/vectors"; OR=open("/root/or.key").read().strip()
A=sorted(glob.glob("/root/embed/chunks/chunks_*.parquet"))
random.seed(1); idx=sorted(random.sample(range(len(A)),8))
vecs=[]; meta=[]
for k in idx:
    cp=A[k]; name=os.path.basename(cp).replace("chunks_","vectors_")
    d=tempfile.mkdtemp(); subprocess.run(["rclone","copy",f"{REMOTE}/{name}",d],timeout=300)
    vp=os.path.join(d,name)
    if not os.path.exists(vp): continue
    tb=pq.read_table(vp); ta=pq.read_table(cp,columns=["chunk_id","title","text","source_type","body_lang","work_id"])
    am={r["chunk_id"]:r for r in ta.to_pylist()}
    for i,cid in enumerate(tb.column("chunk_id").to_pylist()):
        if cid in am:
            vecs.append(np.array(tb.column("vector")[i].as_py(),dtype=np.float32)); meta.append(am[cid])
    import shutil; shutil.rmtree(d,ignore_errors=True)
V=np.vstack(vecs); V/=np.linalg.norm(V,axis=1,keepdims=True)+1e-9
print(f"pool: {len(V):,} chunks de {len(idx)} shards",flush=True)
def embed(q):
    body=json.dumps({"model":"qwen/qwen3-embedding-8b","input":[q]}).encode()
    r=urllib.request.urlopen(urllib.request.Request("https://openrouter.ai/api/v1/embeddings",data=body,headers={"Authorization":"Bearer "+OR,"Content-Type":"application/json"}),timeout=60)
    v=np.array(json.load(r)["data"][0]["embedding"],dtype=np.float32)[:4096]; return v/(np.linalg.norm(v)+1e-9)
# A) test fonctionnel titre→chunk
print("\n=== A) RETRIEVAL FONCTIONNEL (titre → rang de son propre chunk) ===",flush=True)
hits=0; tested=0
for j in random.sample(range(len(meta)),6):
    t=(meta[j]["title"] or "").strip()
    if len(t)<15: continue
    qv=embed(t); sims=V@qv; rank=int((sims>sims[j]).sum())+1; tested+=1; hits+= (rank<=3)
    print(f"  rang={rank} (cos_self={sims[j]:.3f}) | {t[:70]!r}",flush=True)
print(f"  → titre retrouve son chunk dans le top-3 : {hits}/{tested}",flush=True)
# B) cohérence intra-work vs aléatoire
print("\n=== B) COHÉRENCE SÉMANTIQUE (intra-work vs aléatoire) ===",flush=True)
byw={}
for i,m in enumerate(meta): byw.setdefault(m["work_id"],[]).append(i)
multi=[w for w,l in byw.items() if len(l)>=2][:200]
intra=[float(V[byw[w][0]]@V[byw[w][1]]) for w in multi]
rnd=[float(V[random.randrange(len(V))]@V[random.randrange(len(V))]) for _ in range(200)]
print(f"  cosine intra-work médian={np.median(intra):.3f} | aléatoire médian={np.median(rnd):.3f}  (intra >> alea attendu)",flush=True)
# C) requêtes FR
print("\n=== C) REQUÊTES FR MdT → top-3 ===",flush=True)
for q in ["exposition amiante et mésothéliome pleural","syndrome du canal carpien gestes répétitifs",
          "silice cristalline silicose surveillance","burnout épuisement professionnel soignants"]:
    qv=embed(q); sims=V@qv; top=np.argsort(-sims)[:3]
    print(f"  Q: {q}",flush=True)
    for t in top: print(f"     [{sims[t]:.3f}] {meta[t]['source_type']}/{meta[t]['body_lang']} — {(meta[t]['title'] or '')[:65]!r}",flush=True)
print("\n[SANITY_DONE]",flush=True)
