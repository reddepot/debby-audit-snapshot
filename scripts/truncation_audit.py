#!/usr/bin/env python3
"""Audit troncature 4000 octets — quantifie l'impact réel par langue/source (le cap était pour vLLM,
sur-tronque côté OR). make_input = embed_or. Mesure % chunks dont l'input dépasse 4000 octets (=tronqué)
+ octets perdus médians, par body_lang et source_type. Décide si re-embed ciblé nécessaire."""
import glob, collections, pyarrow.parquet as pq
TAG_S={"toxico":"Fiche toxicologique","fiche_metier":"Fiche métier","reglementaire":"Fiche réglementaire","sst":"Santé-travail"}
TAG_D={"abstract":"Résumé","fiche":"Fiche"}
def payload(st,dt,ti,tx):
    tag=TAG_S.get(st) or TAG_D.get(dt) or "Article"; t=(ti or "").strip()[:300]
    return tag+(" : "+t if t else "")+"\n\n"+tx
A=sorted(glob.glob("/root/embed/chunks/chunks_*.parquet"))
tot=0; trunc=0; lost=[]; bylang=collections.Counter(); bylang_tr=collections.Counter()
bysrc=collections.Counter(); bysrc_tr=collections.Counter()
for cp in A:
    t=pq.read_table(cp,columns=["title","text","source_type","doc_type","body_lang"])
    st=t.column("source_type").to_pylist(); dt=t.column("doc_type").to_pylist()
    ti=t.column("title").to_pylist(); tx=t.column("text").to_pylist(); bl=t.column("body_lang").to_pylist()
    for i in range(t.num_rows):
        b=payload(st[i],dt[i],ti[i],tx[i]).encode("utf-8"); n=len(b); tot+=1
        bylang[bl[i]]+=1; bysrc[st[i]]+=1
        if n>4000:
            trunc+=1; lost.append(n-4000); bylang_tr[bl[i]]+=1; bysrc_tr[st[i]]+=1
import statistics as S
print(f"total chunks={tot:,}")
print(f"tronqués (>4000o)={trunc:,} ({100*trunc/tot:.2f}%) | octets perdus médian={int(S.median(lost)) if lost else 0} max={max(lost) if lost else 0}")
print("\n% tronqué par langue (langues avec ≥1000 chunks):")
for l,c in bylang.most_common(10):
    if c>=1000: print(f"  {l}: {100*bylang_tr[l]/c:.1f}% tronqués ({bylang_tr[l]:,}/{c:,})")
print("\n% tronqué par source_type:")
for s,c in bysrc.most_common():
    print(f"  {s}: {100*bysrc_tr[s]/max(c,1):.1f}% ({bysrc_tr[s]:,}/{c:,})")
print("[TRUNC_DONE]")
