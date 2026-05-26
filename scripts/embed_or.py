#!/usr/bin/env python3
"""DEBBY P3 — PASSE 2 via OpenRouter (hub). Lit Table A (chunks) → embed qwen3-embedding-8b 4096-fp16
→ Table B → stream object storage + rm local. RÉSUMABLE via object storage (remote_has → skip).
Partition multi-stream : traite shards où (index % nstreams == stream_id). --reverse pour descendant.
make_input IDENTIQUE à embed_vllm.py (vecteurs cohérents entre OR et vLLM). Hybride convergent.

Usage: embed_or.py --nstreams 6 --stream-id 0 [--reverse] [--workers 32]"""
import os, glob, time, argparse, subprocess, json, threading, urllib.request, numpy as np
import pyarrow as pa, pyarrow.parquet as pq
from concurrent.futures import ThreadPoolExecutor, as_completed
ap=argparse.ArgumentParser()
ap.add_argument("--chunks",default="/root/embed/chunks")
ap.add_argument("--out",default="/root/embed/vectors")
ap.add_argument("--remote",default="meddata:meddata-lake/debby_embed/vectors")
ap.add_argument("--nstreams",type=int,default=1)
ap.add_argument("--stream-id",type=int,default=0)
ap.add_argument("--workers",type=int,default=32)
ap.add_argument("--reverse",action="store_true")
ap.add_argument("--orbatch",type=int,default=48)
a=ap.parse_args()
OR_KEY=open("/root/or.key").read().strip(); MODEL="qwen/qwen3-embedding-8b"; DIM=4096
_cost=[0.0]; _toks=[0]; _lock=threading.Lock()
TAG_BY_SOURCE={"toxico":"Fiche toxicologique","fiche_metier":"Fiche métier","reglementaire":"Fiche réglementaire","sst":"Santé-travail"}
TAG_BY_DOC={"abstract":"Résumé","fiche":"Fiche"}
def make_input(st,dt,ti,tx):
    tag=TAG_BY_SOURCE.get(st) or TAG_BY_DOC.get(dt) or "Article"
    t=(ti or "").strip()[:300]
    s=tag+(" : "+t if t else "")+"\n\n"+tx
    b=s.encode("utf-8")
    return b[:4000].decode("utf-8","ignore") if len(b)>4000 else s
def or_embed(texts):
    body=json.dumps({"model":MODEL,"input":texts}).encode()
    for at in range(6):
        try:
            req=urllib.request.Request("https://openrouter.ai/api/v1/embeddings",data=body,
                headers={"Authorization":"Bearer "+OR_KEY,"Content-Type":"application/json"})
            with urllib.request.urlopen(req,timeout=180) as r: d=json.load(r)
            if "data" not in d: raise RuntimeError(str(d)[:200])
            u=d.get("usage",{})
            with _lock: _cost[0]+=u.get("cost",0.0); _toks[0]+=u.get("total_tokens",0)
            return [e["embedding"] for e in d["data"]]
        except Exception as e:
            if at==5: raise
            time.sleep(min(2**at,20))
SCHEMA=pa.schema([("chunk_id",pa.string()),("vector",pa.list_(pa.float16(),DIM)),
                  ("embed_model",pa.string()),("embed_dim",pa.int32())])
try:
    _o=subprocess.run(["rclone","lsf","--format","sp",a.remote],capture_output=True,text=True,timeout=180).stdout
    _DONE=set(l.split(";",1)[1] for l in _o.splitlines() if ";" in l and l.split(";",1)[0].isdigit() and int(l.split(";",1)[0])>0)
except Exception: _DONE=set()
def remote_has(name): return name in _DONE   # prefetch 1× ; EXCLUT les 0-octet (taille>0) → re-embed les corrompus
os.makedirs(a.out,exist_ok=True)
allshards=sorted(glob.glob(f"{a.chunks}/chunks_*.parquet"))
mine=[s for i,s in enumerate(allshards) if i%a.nstreams==a.stream_id]
if a.reverse: mine=mine[::-1]
print(f"[or{a.stream_id}] {len(mine)} shards (reverse={a.reverse})",flush=True)
t0=time.time(); tot=0; done=0
for cp in mine:
    name=os.path.basename(cp).replace("chunks_","vectors_"); vp=f"{a.out}/{name}"
    if remote_has(name): done+=1; continue
    t=pq.read_table(cp,columns=["chunk_id","source_type","doc_type","title","text"]); n=t.num_rows
    if n==0:
        pq.write_table(pa.table({c:[] for c in SCHEMA.names},schema=SCHEMA),vp)
        subprocess.run(["rclone","copy",vp,a.remote],timeout=120); os.remove(vp); done+=1; continue
    cid=t.column("chunk_id").to_pylist(); st=t.column("source_type").to_pylist()
    dt=t.column("doc_type").to_pylist(); ti=t.column("title").to_pylist(); tx=t.column("text").to_pylist()
    inp=[make_input(st[i],dt[i],ti[i],tx[i]) for i in range(n)]
    vecs=[None]*n; idx=list(range(0,n,a.orbatch))
    def w(i): return i,or_embed(inp[i:i+a.orbatch])
    try:
        with ThreadPoolExecutor(max_workers=a.workers) as ex:
            for f in as_completed([ex.submit(w,i) for i in idx]):
                i,oe=f.result()
                for j,e in enumerate(oe):
                    v=np.asarray(e,dtype=np.float32)[:DIM]; nm=np.linalg.norm(v)
                    vecs[i+j]=(v/nm if nm>1e-8 else v).astype(np.float16)
    except Exception as e:
        print(f"[or{a.stream_id}] ÉCHEC {name}: {str(e)[:160]}",flush=True); break  # ex: crédit épuisé → laisser à RunPod
    tbl=pa.table({"chunk_id":pa.array(cid),
        "vector":pa.FixedSizeListArray.from_arrays(pa.array(np.concatenate(vecs),type=pa.float16()),DIM),
        "embed_model":pa.array(["Qwen/Qwen3-Embedding-8B"]*n),"embed_dim":pa.array([DIM]*n,pa.int32())},schema=SCHEMA)
    tmp=vp+".tmp"; pq.write_table(tbl,tmp,compression="zstd"); os.replace(tmp,vp)
    if subprocess.run(["rclone","copy",vp,a.remote],timeout=300).returncode==0: os.remove(vp)
    tot+=n; done+=1; dt2=time.time()-t0
    print(f"[or{a.stream_id}] {name} +{n} | tot={tot:,} | ${_cost[0]:.2f} | {tot/max(1,dt2):.0f} v/s | {dt2:.0f}s | {done}/{len(mine)}",flush=True)
print(f"[or{a.stream_id}] DONE tot={tot:,} | ${_cost[0]:.2f} | {_toks[0]/1e6:.1f}M tok | {time.time()-t0:.0f}s",flush=True)
