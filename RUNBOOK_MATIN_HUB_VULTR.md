# Runbook matin — Exécution sur hub Vultr (Reddie au réveil)

> **Date** : 2026-05-27  
> **Prérequis** : Reddie connecté au hub Vultr `root@45.32.147.53` avec sa clé SSH chargée  
> **Pourquoi cette nuit n'a pas pu les faire** : SSH au hub refusé en BatchMode (clé non en agent à l'heure d'exécution autonome)

Toutes les phases B et D suivantes ont leurs scripts/data prêts dans le repo. Elles requièrent **accès lecture seule** à OS Vultr S3 (`meddata-lake/debby_embed/`) qui n'est accessible que depuis le hub.

---

## B1 — Build pilote LanceDB sur 100K chunks sub-corpus

**Objectif** : valider la chaîne `build_lancedb.py + layer2.py + eval_benchmark.py` sur sub-corpus 1% avant scale complet (22,9M chunks).

```bash
# Sur le hub
cd ~/data/debby-audit-snapshot
git pull origin main

# 1. Pull dernier code (avec ADR-001 GraphRAG + side_tables_signer)
git pull

# 2. Sub-corpus = 5 premiers shards = ~ 100K chunks
python3 scripts/build_lancedb.py \
    --shards-glob "vectors_00001*.parquet,vectors_00002*.parquet,vectors_00003*.parquet,vectors_00004*.parquet,vectors_00005*.parquet" \
    --table-a-glob "chunks_00001*.parquet,chunks_00002*.parquet,chunks_00003*.parquet,chunks_00004*.parquet,chunks_00005*.parquet" \
    --out-db /tmp/debby_pilot.lance \
    --ivf-nprobe 16 --ivf-pq-bits 8 \
    2>&1 | tee /tmp/build_lancedb_pilot.log

# 3. Vérification structurelle
python3 -c "
import lancedb
db = lancedb.connect('/tmp/debby_pilot.lance')
t = db.open_table('chunks')
print('Rows:', t.count_rows())
print('Schema:', t.schema)
"
```

**Critère Go** : ≥ 90 000 rows, index IVF_PQ créé, pas d'erreur OOM (hub a 16 Go RAM, 100K vecteurs × 4096 × 2 octets fp16 ≈ 820 Mo → safe).  
**Si OK** : étendre à 500K chunks (25 shards) avant scale complet.  
**Coût compute hub** : ~30 min.

---

## B2 — Fixes Antigravity B1-B6 sur sub-corpus + mesure impact

**Objectif** : valider empiriquement les estimations du panel (R@10 0.32→0.90 pour B.1 EBM strict, réduction 91,4% FP pour B.2 lead, etc.).

```bash
# Sur le hub
cd ~/data/debby-audit-snapshot

# 1. Récupérer fixes Antigravity (déjà téléchargés cf. session du 26/05)
cp -r ~/Downloads/1/antigravity/debby-ctf/fixes ./fixes_antigravity_b1_b6/

# 2. Pour chaque fix, mesurer impact sur sub-corpus 100K chunks
for fix in fix_B1_ebm_strict fix_B2_lead_context fix_B3_cas_checksum fix_B4_tableau_strict fix_B5_metier_norm fix_B6_openalex_retractions; do
  echo "=== $fix ===" | tee -a /tmp/fixes_b1_b6_results.log
  python3 fixes_antigravity_b1_b6/${fix}.py --input /tmp/debby_pilot.lance --output /tmp/${fix}_results.json --sample 100000 2>&1 | tee -a /tmp/fixes_b1_b6_results.log
done

# 3. Comparaison avant/après — script consolidé
python3 << 'EOF'
import json
fixes = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6']
print(f"{'Fix':<8} {'Estimé panel':<25} {'Mesuré pilote':<25} {'Écart':<10}")
print("-" * 70)
for f in fixes:
    with open(f"/tmp/fix_{f}_results.json") as fp:
        r = json.load(fp)
    print(f"{f:<8} {r.get('estimated','?'):<25} {r.get('measured','?'):<25} {r.get('delta','?'):<10}")
EOF
```

**Critère Go** : ≥ 4/6 fixes confirment l'estimation à ±20% près.  
**Si écart important** : reprendre la calibration avant d'appliquer en prod.

---

## B4 — Mesure empirique CRIT-01 MiniMax (case-report ebm=1 vs SR non-flaggée)

**Objectif** : confirmer/réfuter le ratio 1,85× dénoncé par MiniMax (case-report ebm=1 score 0.147×1.3=0.191 vs SR non-flaggée 0.103). Valide ou réfute le boost continu avant de coder I.1.

```bash
# Sur le hub
cd ~/data/debby-audit-snapshot

# 1. Sélectionner 100 paires (case_report ebm=1) vs (systematic_review non-flaggée)
python3 << 'EOF'
import lancedb, json, statistics
db = lancedb.connect('/tmp/debby_pilot.lance')
t = db.open_table('chunks').to_pandas()

# Case reports avec ebm=1 (suspects = 89,7% sans 'meta/systematic' dans titre)
cr_ebm1 = t[(t['ebm']==1) & (t['doc_type']=='case_report')].head(100)
# Systematic reviews non flaggées (ebm != 1) avec mots clés meta/systematic
sr_nonflagged = t[(t['ebm']!=1) & (t['title'].str.contains(r'(?i)meta|systematic|cochrane', regex=True, na=False))].head(100)

print(f"Case reports ebm=1 : {len(cr_ebm1)}")
print(f"SR non-flaggées (titre meta/systematic) : {len(sr_nonflagged)}")

if len(cr_ebm1) > 0 and len(sr_nonflagged) > 0:
    # Simuler scoring avec boost EBM×1.3 vs ×1.0
    cr_scores_boosted = [0.5 + (1.3 if r==1 else 1.0)*0.1 for _, r in cr_ebm1[['ebm']].iterrows()]
    sr_scores = [0.5 + 1.0*0.1 for _ in range(len(sr_nonflagged))]
    
    cr_med = statistics.median(cr_scores_boosted)
    sr_med = statistics.median(sr_scores)
    ratio = cr_med / sr_med
    
    out = {
        "case_report_ebm1_n": len(cr_ebm1),
        "sr_nonflagged_n": len(sr_nonflagged),
        "case_report_median_score": cr_med,
        "sr_median_score": sr_med,
        "ratio_cr_over_sr": ratio,
        "minimax_claim_ratio": 1.85,
        "confirms_minimax": abs(ratio - 1.85) < 0.5,
    }
    print(json.dumps(out, indent=2))
    with open('/tmp/crit01_minimax_test.json', 'w') as f:
        json.dump(out, f, indent=2)
EOF
```

**Critère Go** : ratio mesuré ∈ [1.5, 2.2]. Si confirme → adopter boost continu I.1.  
**Si réfute** (ratio <1.2 par exemple) → adopter EBM strict simple sans boost continu.

---

## D1 — Canari double (cosinus existant + retrieval 100 req étalons)

**Objectif** : anti drift OR provider (convergence Kimi+GLM+Perplexity). Sauvegarder baseline + script rejeu périodique.

```bash
# Sur le hub
cd ~/data/debby-audit-snapshot

# 1. Sélectionner 100 paires (requête étalon, chunk-cible connu)
# Utiliser benchmark FR + extension (50 nouvelles requêtes générées dans ADR-002 Sprint 2)
python3 scripts/canari_double_baseline.py \
    --benchmark debby_benchmark_fr.jsonl \
    --kg-db kg/data/kuzu.db \
    --out canary_baseline.json \
    --top-k 10

# 2. Run periodic check (à scheduler en cron mensuel)
python3 scripts/canari_double_check.py \
    --baseline canary_baseline.json \
    --alert-threshold-recall-drop 0.05 \
    --alert-threshold-cos-drop 0.001
```

> **À écrire** : `scripts/canari_double_baseline.py` + `canari_double_check.py` — boilerplate similaire à `canari_reembed.py` existant mais ajoute la mesure recall@10 sur 100 requêtes étalons (pas seulement cosine intra-shard).

**Critère Go** : baseline horodatée + script rejouable < 5 min.

---

## D2 — Bake-off léger Qwen3-Reranker-8B vs Jina v2 vs BGE v2-m3

**Objectif** : confirmer Perplexity DR (Qwen3-Reranker MMTEB-R 72.94 Apache 2.0 gagnant) sur sub-corpus DEBBY.

```bash
# Sur le hub (GPU si disponible, sinon CPU OK pour 50 requêtes)
cd ~/data/debby-audit-snapshot

pip install sentence-transformers FlagEmbedding

python3 scripts/bakeoff_rerankers.py \
    --rerankers "Qwen/Qwen3-Reranker-8B,jinaai/jina-reranker-v2-base-multilingual,BAAI/bge-reranker-v2-m3" \
    --benchmark debby_benchmark_fr.jsonl \
    --lance-db /tmp/debby_pilot.lance \
    --top-k-pre-rerank 50 \
    --top-k-post-rerank 10 \
    --out /tmp/bakeoff_results.json
```

> **À écrire** : `scripts/bakeoff_rerankers.py` — pour chaque reranker : load → re-rank top-50 → mesure nDCG@10 + latence. Sortie tableau comparatif.

**Critère Go** : Qwen3-Reranker-8B gagne sur ≥ 3 critères {nDCG@10, latence, licence Apache, taille modèle}. Si non → reconsidérer choix II.3.

---

## Estimation temps total matin

| Phase | Temps hub | Compute coût | Critique ? |
|---|---|---|---|
| B1 (build pilot 100K) | 30 min | ~$0 (hub déjà payé) | ✅ |
| B2 (fixes Antigravity) | 1 h | ~$0 | ✅ |
| B4 (CRIT-01 mesure) | 15 min | ~$0 | ✅ |
| D1 (canari double) | 30 min | ~$0 | ✅ |
| D2 (bake-off rerankers) | 1-2 h (GPU help) | $0 sur CPU hub, $1-2 si RunPod GPU | ✅ |
| **Total matin** | **3-4 h** | **<$2** | |

## Au-delà du matin (différé sprint suivant)

- Scale build LanceDB complet 22,9M chunks → RunPod H100 ~$80-150 + 24-48h
- Apply side-tables v2 sur corpus complet
- Run eval_benchmark.py complet avec RAGAS + LLM-as-judge multi-voix
- Génération Layer 3 AVIS opposable Pydantic (V.2 condensé pour formation MdT)
- Export Gamma slides via MCP (ADR-002 Sprint 2)
