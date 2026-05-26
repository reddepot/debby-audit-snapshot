#!/usr/bin/env python3
"""body_lang v2 STREAMING (memory-safe) — corrige le crash de la v1 (qui chargeait 2,6M textes en RAM).
Traite shard-par-shard ; ne garde que work_id→lang (petit). Pool PAR shard (fork d'un parent léger).
Side-table /root/body_lang_fix.json (appliquée au load LanceDB, 0 ré-embed)."""
import glob, json, collections, pyarrow.parquet as pq
from multiprocessing import Pool
try:
    from langdetect import detect, DetectorFactory; DetectorFactory.seed=0
except Exception: detect=None
def dl(txt):
    if not detect: return "und"
    s=(txt or "")[300:2600].strip() or (txt or "")[:2000]
    if len(s)<60: return "und"
    try: return detect(s)
    except Exception: return "und"
A=sorted(glob.glob("/root/embed/chunks/chunks_*.parquet"))
fix={}; orig={}; R=collections.Counter(); MIS=collections.Counter(); n=0
with Pool(8) as p:
    for f in A:
        t=pq.read_table(f,columns=["work_id","body_lang","text","chunk_index"])
        wid=t.column("work_id").to_pylist(); bl=t.column("body_lang").to_pylist()
        ci=t.column("chunk_index").to_pylist(); tx=t.column("text").to_pylist()
        # 1 échantillon par work (chunk_index 0 préféré), uniquement works pas encore vus
        idx=[i for i in range(len(wid)) if wid[i] not in fix and (ci[i]==0 or wid[i] not in orig)]
        texts=[tx[i] for i in idx]
        langs=p.map(dl, texts, chunksize=200)
        for j,i in enumerate(idx):
            w=wid[i]
            if w in fix: continue
            fix[w]=langs[j]; orig[w]=bl[i]; R[langs[j]]+=1
            if bl[i] and bl[i]!=langs[j]: MIS[f"{bl[i]}->{langs[j]}"]+=1
        n+=1
        if n%200==0: print(f"  {n}/{len(A)} shards | works={len(fix):,}",flush=True)
json.dump(fix,open("/root/body_lang_fix.json","w"))
mism=sum(MIS.values())
print(f"[BODYLANG_V2_DONE] works={len(fix):,} | langues={dict(R.most_common(8))}",flush=True)
print(f"  mismatch vs orig: {mism:,} ({100*mism/max(len(fix),1):.1f}%) top={dict(MIS.most_common(6))}",flush=True)
fr_o=sum(1 for w in fix if orig.get(w)=="fr"); fr_k=sum(1 for w in fix if orig.get(w)=="fr" and fix[w]=="fr")
print(f"  orig=fr {fr_o:,} → confirmés fr {fr_k:,} ({fr_o-fr_k:,} re-classés non-fr)",flush=True)
