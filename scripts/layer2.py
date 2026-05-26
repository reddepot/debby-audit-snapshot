#!/usr/bin/env python3
"""DEBBY — COUCHE 2 (retrieval intelligence). Expose retrieve(query,k)->list[dict] (compat eval_benchmark).
Intègre la délibération + le brainstorm :
- expansion requête FR→EN (dico SST) — D2, piège FR/EN du Tour 1
- recherche vectorielle LanceDB (+ BM25 optionnel, fusion RRF)
- boosts multi-niveaux : source_type SST, langue FR, récence, niveau EBM
- FILTRE DE FRANCISATION (pépite contrarian) : pénalise les sources US/UK-only sur question FR-juridique
- pénalité rétractation/abstract ; dédup par work_id
- seuil "je ne sais pas" (anti-illusion de complétude — angle mort #1)
- routage : needs_mcp (droit/tableau MP/substance → outils structurés vs littérature → RAG)
Config en tête, ajustable sur le benchmark FR sans ré-embed."""
import os, re, json, math, urllib.request
DB_PATH=os.environ.get("DEBBY_DB","/data/debby.lancedb"); TABLE="debby"
OR_KEY_PATH="/root/or.key"; EMB_MODEL="qwen/qwen3-embedding-8b"; DIM=int(os.environ.get("DEBBY_DIM","1024"))
NO_ANSWER_THRESHOLD=float(os.environ.get("DEBBY_NOANS","0.30"))   # score boosté min ; calibrer sur benchmark

# --- dictionnaire SST FR→EN (expansion requête ; BM25 monolingue + nuances techniques) ---
SST_DICT={"tms":"musculoskeletal disorder","inaptitude":"unfitness for work","aptitude":"fitness for work",
 "maladie professionnelle":"occupational disease","tableau":"occupational disease schedule","amiante":"asbestos",
 "silice":"silica","plomb":"lead","bruit":"noise","surdité":"hearing loss","rps":"psychosocial risks",
 "burnout":"burnout","canal carpien":"carpal tunnel syndrome","lombalgie":"low back pain","vlep":"occupational exposure limit",
 "surveillance":"medical surveillance","travail de nuit":"night shift work","grossesse":"pregnancy","soudeur":"welder"}
# marqueurs question FR-juridique (filtre francisation + routage MCP)
FR_LEGAL=re.compile(r"(?i)tableau|inaptitude|aptitude|code du travail|maladie professionnelle|\bMP\b|VLEP|r[ée]paration|jurisprudence|pr[ée]somption|CRRMP|d[ée]rogation|surveillance (?:post|médicale)|reclassement|R\d{4}|L\d{4}")
SUBST_Q=re.compile(r"(?i)\b\d{2,7}-\d{2}-\d\b|substance|CAS\b|VLEP|toxico|fiche")

def fr_legal(q): return bool(FR_LEGAL.search(q))
def needs_mcp(q): return bool(FR_LEGAL.search(q) or SUBST_Q.search(q))
def expand_query(q):
    ql=q.lower(); extra=[v for k,v in SST_DICT.items() if k in ql]
    return q if not extra else q+" "+" ".join(extra)   # requête bilingue enrichie (vecteur cross-lingual)

_orkey=None
def _embed(text):
    global _orkey
    if _orkey is None: _orkey=open(OR_KEY_PATH).read().strip()
    body=json.dumps({"model":EMB_MODEL,"input":[text]}).encode()
    req=urllib.request.Request("https://openrouter.ai/api/v1/embeddings",data=body,
        headers={"Authorization":"Bearer "+_orkey,"Content-Type":"application/json"})
    import numpy as np
    v=np.asarray(json.load(urllib.request.urlopen(req,timeout=60))["data"][0]["embedding"],dtype="float32")[:DIM]
    n=np.linalg.norm(v); return (v/n if n>1e-8 else v)

_tbl=None
def _table():
    global _tbl
    if _tbl is None:
        import lancedb; _tbl=lancedb.connect(DB_PATH).open_table(TABLE)
    return _tbl

SRC_BOOST={"toxico":2.6,"fiche_metier":2.4,"reglementaire":3.0,"sst":2.0,"clinique":1.2,"litterature":1.0}
EBM_BOOST={1:1.4,2:1.25,3:1.15,4:1.05,5:1.0,6:0.9,9:1.0}
def _boost(r,is_fr_legal):
    s=1.0
    s*=SRC_BOOST.get(r.get("source_type"),1.0)
    s*=EBM_BOOST.get(int(r.get("ebm",9)),1.0)
    lang=r.get("body_lang"); s*=(2.0 if is_fr_legal else 1.2) if lang=="fr" else 1.0
    yr=int(r.get("year") or 0); s*= 1.3 if yr>=2018 else (1.1 if yr>=2010 else 1.0)
    if int(r.get("has_sst",0)): s*=1.3
    if int(r.get("is_retracted",0)): s*=0.1                       # rétracté : enterré
    if int(r.get("doc_type")=="abstract") if isinstance(r.get("doc_type"),str) else False: s*=0.85
    # FILTRE FRANCISATION : question FR-juridique + source anglo non-SST → forte pénalité
    if is_fr_legal and lang!="fr" and r.get("source_type") in ("litterature","clinique"): s*=0.5
    return s

def retrieve(query,k=10,pool=80):
    isfl=fr_legal(query); qx=expand_query(query)
    try: qv=_embed(qx)
    except Exception as e: return [{"error":f"embed failed: {e}"}]
    hits=_table().search(qv).metric("cosine").limit(pool).to_list()
    seen={};
    for h in hits:
        base=1.0-float(h.get("_distance",0.0))                   # cosine sim
        sc=base*_boost(h,isfl)
        w=h.get("work_id")
        if w not in seen or sc>seen[w]["score"]:
            seen[w]={"work_id":w,"chunk_id":h.get("chunk_id"),"title":h.get("title"),"text":(h.get("text") or "")[:600],
                     "source_type":h.get("source_type"),"body_lang":h.get("body_lang"),"year":h.get("year"),
                     "doi":h.get("doi"),"venue":h.get("venue"),"ebm":h.get("ebm"),"is_retracted":h.get("is_retracted"),
                     "score":sc,"base_sim":base}
    ranked=sorted(seen.values(),key=lambda x:-x["score"])[:k]
    # seuil "je ne sais pas" / hors-corpus
    if not ranked or ranked[0]["score"]<NO_ANSWER_THRESHOLD:
        return [{"no_answer":True,"reason":"score sous seuil — preuve insuffisante / hors-corpus",
                 "needs_mcp":needs_mcp(query),"best_score":ranked[0]["score"] if ranked else 0.0}]
    for r in ranked: r["needs_mcp"]=needs_mcp(query)
    return ranked

if __name__=="__main__":
    import sys; q=sys.argv[1] if len(sys.argv)>1 else "exposition amiante et mésothéliome tableau"
    print(f"fr_legal={fr_legal(q)} needs_mcp={needs_mcp(q)} expand={expand_query(q)!r}")
    for r in retrieve(q,5): print(json.dumps(r,ensure_ascii=False)[:300])
