#!/usr/bin/env python3
"""DEBBY — build LanceDB depuis Table A (chunks) + Table B (vecteurs OS) + side-tables.
Jointure par chunk_id ; applique side-tables (is_retracted, source_type raffiné, body_lang, year/title)
SANS ré-embed. Matryoshka optionnel (--dim) + index IVF_PQ. Streamé shard par shard (léger disque).
Le full fp16 4096 = ~187 Go ; Matryoshka-1024 + IVF_PQ rend l'index servable.

Usage: build_lancedb.py --db /data/debby.lancedb --dim 1024 [--vectors-remote meddata:.../vectors]
       [--chunks /root/embed/chunks] [--limit N]"""
import os, glob, json, sqlite3, subprocess, tempfile, argparse, numpy as np
import pyarrow as pa, pyarrow.parquet as pq
ap=argparse.ArgumentParser()
ap.add_argument("--db",default="/data/debby.lancedb")
ap.add_argument("--table",default="debby")
ap.add_argument("--chunks",default="/root/embed/chunks")
ap.add_argument("--vectors-remote",default="meddata:meddata-lake/debby_embed/vectors")
ap.add_argument("--vectors-local",default="")  # si déjà local, sinon pull depuis remote
ap.add_argument("--dim",type=int,default=1024,help="Matryoshka : tronque le vecteur (0=full 4096)")
ap.add_argument("--limit",type=int,default=0)
ap.add_argument("--no-index",action="store_true")
a=ap.parse_args()
import lancedb
# --- side-tables ---
def load_json(p):
    try: return json.load(open(p))
    except Exception: return {}
retr=set(load_json("/root/retracted_work_ids.json").get("flagged",[]))
stype=load_json("/root/source_type_refined.json")             # work_id->source_type
blang=load_json("/root/body_lang_fix.json")                   # work_id->lang
ytfix={}
if os.path.exists("/root/year_title_fix.db"):
    c=sqlite3.connect("/root/year_title_fix.db")
    for w,y,t,s in c.execute("SELECT work_id,year,title,status FROM fix WHERE status='ok'"):
        ytfix[w]=(y,t)
print(f"side-tables: retracted={len(retr):,} source_type={len(stype):,} body_lang={len(blang):,} year_title={len(ytfix):,}",flush=True)
DIM=a.dim or 4096
db=lancedb.connect(a.db); tbl=None; total=0
def pull_vec(name):
    if a.vectors_local: return os.path.join(a.vectors_local,name)
    d=tempfile.mkdtemp(); subprocess.run(["rclone","copy",f"{a.vectors_remote}/{name}",d],timeout=300); return os.path.join(d,name)
chunk_shards=sorted(glob.glob(f"{a.chunks}/chunks_*.parquet"))
if a.limit: chunk_shards=chunk_shards[:a.limit]
for cp in chunk_shards:
    name=os.path.basename(cp).replace("chunks_","vectors_")
    vp=pull_vec(name)
    if not os.path.exists(vp): print(f"  ⚠️ vecteurs absents {name}, skip"); continue
    ca=pq.read_table(cp); cb=pq.read_table(vp,columns=["chunk_id","vector"])
    # index vecteurs par chunk_id
    vmap={cid:i for i,cid in enumerate(cb.column("chunk_id").to_pylist())}
    vecs=cb.column("vector")
    recs=[]
    cols={n:ca.column(n).to_pylist() for n in ca.schema.names}
    for i,cid in enumerate(cols["chunk_id"]):
        j=vmap.get(cid)
        if j is None: continue
        w=cols["work_id"][i]
        v=np.asarray(vecs[j].as_py(),dtype=np.float32)
        if DIM<4096:
            v=v[:DIM]; n=np.linalg.norm(v); v=v/n if n>1e-8 else v   # re-normalise après Matryoshka
        yr=cols["year"][i]; ti=cols["title"][i]
        if w in ytfix:
            yy,tt=ytfix[w]
            if (not yr) and yy: yr=yy
            if (not ti or not ti.strip()) and tt: ti=tt
        recs.append({"chunk_id":cid,"work_id":w,"vector":v.astype(np.float32),
            "text":cols["text"][i],"title":ti or "","authors":cols["authors"][i],"venue":cols["venue"][i],
            "year":int(yr or 0),"doi":cols["doi"][i],"doc_type":cols["doc_type"][i],
            "source_type":stype.get(w,cols["source_type"][i]),"body_lang":blang.get(w,cols["body_lang"][i]),
            "ebm":int(cols["ebm"][i]),"study_type":cols["study_type"][i],"is_oh":int(cols["is_oh"][i]),
            "has_sst":int(cols["has_sst"][i]),"clin":float(cols["clin"][i]),
            "is_retracted":1 if w in retr else 0,"concepts":cols["concepts"][i],"origin":cols["origin"][i]})
    if not recs: continue
    if tbl is None: tbl=db.create_table(a.table,data=recs,mode="overwrite")
    else: tbl.add(recs)
    total+=len(recs)
    if a.vectors_remote and not a.vectors_local:
        import shutil; shutil.rmtree(os.path.dirname(vp),ignore_errors=True)
    print(f"  +{len(recs)} ({name}) → total {total:,}",flush=True)
print(f"[LOADED] {total:,} chunks dans {a.db}/{a.table}",flush=True)
if not a.no_index and tbl is not None:
    npart=max(256,int(total**0.5)); nsub=DIM//8
    print(f"index IVF_PQ: partitions={npart} sub_vectors={nsub} metric=cosine",flush=True)
    tbl.create_index(metric="cosine",index_type="IVF_PQ",num_partitions=npart,num_sub_vectors=nsub)
    print("[INDEX_DONE]",flush=True)
