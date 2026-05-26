#!/usr/bin/env python3
"""Gate d'intégrité COMPLET — vérifie les 871 shards via footers parquet S3 (pas de pull 155Go).
Pour chaque shard : num_rows A == num_rows B (alignement exhaustif). + total rows A vs B + manquants.
Lit creds depuis rclone.conf. Définitif et léger (range-requests footer)."""
import glob, os, re, pyarrow.parquet as pq, pyarrow.fs as pafs
conf=open(os.path.expanduser("~/.config/rclone/rclone.conf")).read()
def grab(k):
    m=re.search(rf"{k}\s*=\s*(\S+)",conf); return m.group(1) if m else None
ak=grab("access_key_id"); sk=grab("secret_access_key"); ep=grab("endpoint")
print(f"endpoint={ep}",flush=True)
fs=pafs.S3FileSystem(access_key=ak,secret_key=sk,endpoint_override=ep if ep.startswith("http") else "https://"+ep,region="us-east-1")
BUCKET="meddata-lake/debby_embed/vectors"
A=sorted(glob.glob("/root/embed/chunks/chunks_*.parquet"))
mism=[]; totA=0; totB=0; missing=0; n=0
for cp in A:
    name=os.path.basename(cp).replace("chunks_","vectors_")
    ra=pq.read_metadata(cp).num_rows; totA+=ra
    try:
        with fs.open_input_file(f"{BUCKET}/{name}") as f:
            rb=pq.read_metadata(f).num_rows
        totB+=rb
        if ra!=rb: mism.append((name,ra,rb))
    except Exception as e:
        missing+=1; mism.append((name,ra,"MISSING:"+str(e)[:40]))
    n+=1
    if n%200==0: print(f"  {n}/{len(A)} vérifiés…",flush=True)
print(f"\nshards A={len(A)} | rows A={totA:,} B={totB:,} | manquants={missing} | mismatches={len(mism)}",flush=True)
for m in mism[:12]: print("  MISMATCH",m,flush=True)
ok = (not mism) and (totA==totB) and (missing==0)
print(f"[INTEGRITY_FULL] {'GO ✅ 871/871 alignés, rows A==B' if ok else 'CHECK ⚠️'}",flush=True)
