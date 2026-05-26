#!/usr/bin/env python3
"""CANARI re-embed — vérifie fidélité texte↔vecteur + provider-drift d'un coup.
Échantillon stratifié par shard : reconstruit le payload EXACT (make_input = embed_or) → re-embed OR
→ cosine vs vecteur stocké. cos~1.0 = fidèle & espace cohérent ; bas/clusters = désalignement ou drift.
+ audit troncature 4000 octets (par langue/source)."""
import glob, os, subprocess, tempfile, json, random, urllib.request, numpy as np
import pyarrow.parquet as pq
REMOTE="meddata:meddata-lake/debby_embed/vectors"; OR=open("/root/or.key").read().strip()
TAG_S={"toxico":"Fiche toxicologique","fiche_metier":"Fiche métier","reglementaire":"Fiche réglementaire","sst":"Santé-travail"}
TAG_D={"abstract":"Résumé","fiche":"Fiche"}
def make_input(st,dt,ti,tx):   # IDENTIQUE à embed_or.py
    tag=TAG_S.get(st) or TAG_D.get(dt) or "Article"; t=(ti or "").strip()[:300]
    s=tag+(" : "+t if t else "")+"\n\n"+tx; b=s.encode("utf-8")
    return b[:4000].decode("utf-8","ignore") if len(b)>4000 else s
def embed(q):
    body=json.dumps({"model":"qwen/qwen3-embedding-8b","input":[q]}).encode()
    for a in range(4):
        try:
            r=urllib.request.urlopen(urllib.request.Request("https://openrouter.ai/api/v1/embeddings",data=body,headers={"Authorization":"Bearer "+OR,"Content-Type":"application/json"}),timeout=60)
            v=np.array(json.load(r)["data"][0]["embedding"],dtype=np.float32)[:4096]; return v/(np.linalg.norm(v)+1e-9)
        except Exception:
            import time; time.sleep(2**a)
    return None
A=sorted(glob.glob("/root/embed/chunks/chunks_*.parquet"))
random.seed(7); shards=sorted(random.sample(range(len(A)),30))   # 30 shards répartis
cos=[]; low=[]; byshard={}
for k in shards:
    cp=A[k]; name=os.path.basename(cp).replace("chunks_","vectors_")
    d=tempfile.mkdtemp(); subprocess.run(["rclone","copy",f"{REMOTE}/{name}",d],timeout=300); vp=os.path.join(d,name)
    if not os.path.exists(vp): continue
    tb=pq.read_table(vp); ta=pq.read_table(cp,columns=["chunk_id","title","text","source_type","doc_type","body_lang"])
    am={r["chunk_id"]:r for r in ta.to_pylist()}
    vm={cid:i for i,cid in enumerate(tb.column("chunk_id").to_pylist())}
    sample=random.sample(list(am.keys()),min(100,len(am)))   # 100 chunks/shard
    sc=[]
    for cid in sample:
        m=am[cid]; j=vm.get(cid)
        if j is None: continue
        stored=np.array(tb.column("vector")[j].as_py(),dtype=np.float32); stored/=np.linalg.norm(stored)+1e-9
        fresh=embed(make_input(m["source_type"],m["doc_type"],m["title"],m["text"]))
        if fresh is None: continue
        c=float(stored@fresh); cos.append(c); sc.append(c)
        if c<0.98: low.append((name,cid,round(c,3),m["body_lang"]))
    if sc: byshard[name]=round(float(np.median(sc)),4)
    import shutil; shutil.rmtree(d,ignore_errors=True)
    print(f"  {name}: n={len(sc)} cos_med={byshard.get(name)}",flush=True)
cos=np.array(cos)
print(f"\n=== CANARI : {len(cos)} chunks re-embeddés ===",flush=True)
print(f"cosine vs stocké : médian={np.median(cos):.4f} min={cos.min():.4f} p5={np.percentile(cos,5):.4f}",flush=True)
print(f"cos<0.995 : {(cos<0.995).sum()} ({100*(cos<0.995).mean():.1f}%) | cos<0.98 : {(cos<0.98).sum()} ({100*(cos<0.98).mean():.1f}%)",flush=True)
print(f"médiane par shard (drift si écarts) : min={min(byshard.values()):.4f} max={max(byshard.values()):.4f}",flush=True)
for l in low[:10]: print("  LOW",l,flush=True)
v="GO ✅ fidèle & cohérent" if np.median(cos)>0.99 and (cos<0.98).mean()<0.02 else "CHECK ⚠️"
print(f"[CANARI] {v}",flush=True)
