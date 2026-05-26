# PROMPT #2 — DEBBY-EVOLVE · Amélioration continue / Développement / Prospective

> **À transmettre à un modèle agentique externe** (Kimi Agent Swarm, Google Antigravity, ChatGPT Agent, etc.)
> **Mode** : architecte senior + product visionary + chercheur RAG SOTA
> **Durée attendue** : 7-30 jours selon profondeur

---

## 1. Contexte

DEBBY est un corpus RAG médical + santé-sécurité au travail (SST) destiné à un **médecin du travail français**. 2,6 M œuvres, 22,9 M chunks, embeddés fp16 4096-dim (`qwen3-embedding-8b`). Architecture découplée Table A (texte+métadonnées canoniques) / Table B (vecteurs jetables) — pattern *Bring Your Own Embedder*. 5 side-tables d'enrichissement.

Le **référentiel complet** est sur https://github.com/reddepot/debby-audit-snapshot. L'embed est scellé ; les audits structurels (intégrité, canari fidélité, sanity retrieval) sont passés. **Le pipeline post-embed (LanceDB + Couche 2 + éval) est codé mais non encore exécuté.**

**Vision durable** :
> *L'embed n'est pas le chef d'œuvre — c'est l'infrastructure. Le chef d'œuvre, c'est la couche de raisonnement qu'on construit par-dessus (graphe + agents).*

DEBBY doit devenir le **socle RAG opposable** d'un médecin du travail français — fiabilité médicolégale, traçabilité, raisonnement clinique en contexte professionnel.

---

## 2. Ta mission

**Faire évoluer DEBBY.** Le rendre plus complet, mieux architecturé, plus rigoureux, plus innovant, progressiste. Tu produis une **feuille de route opérationnelle** et tu prototypes les chantiers prioritaires.

Posture exigée :
- **Architecte senior** : tu raisonnes en termes de tradeoffs (cohérence, scalabilité, maintenabilité, coût).
- **Product visionary** : tu places l'expérience MdT au centre — pas un benchmark abstrait.
- **Chercheur RAG SOTA** : tu connais l'état de l'art (GraphRAG, agentic RAG, multi-hop, re-ranking, LLM-as-judge, RAGAS, etc.) et tu sais ce qui s'applique vraiment ici.
- **Anti-bloat** : tu ne proposes pas 50 idées creuses. Tu en proposes **15-25 prioritisées** avec preuve, prototype, et chemin d'intégration.

---

## 3. Axes de progrès — 5 catégories

### CATÉGORIE I — Correctifs immédiats (semaines 1-2)

Sur la base des 6 anomalies déclarées (A1-A6 du doc), produire des **side-tables v2** correctives appliquées au load LanceDB :
- **I.1** EBM v2 : re-tagger `ebm=1` ssi `meta|systematic|prisma` dans titre OU concept OpenAlex ⊇ {Systematic review, Meta-analysis}.
- **I.2** Substances v2 : filtrer "lead" par contexte ; remplacer pseudo-CAS-dates par lookup ECHA/PubChem.
- **I.3** Tableaux MP v2 : matching strict `tableau (MP|n°|maladie professionnelle)\s*\d` + RG-XX/RA-XX.
- **I.4** Métiers v2 : normalisation Unicode NFD + strip diacritics + alias-table FR (maçon ≡ macon ≡ macons).
- **I.5** Rétractations v2 : sources complémentaires (PubMed Retracted flag, OpenAlex `is_retracted`).
- **I.6** doc_type v2 : ré-inférence ft/abstract via longueur de texte + heuristique structure.

Livrable : `side_tables_v2/` + `apply_v2.py` au load LanceDB.

### CATÉGORIE II — Architecture (semaines 3-6)

- **II.1 [GraphRAG avec ontologie médicale]** Construire le graphe `substance → pathologie → tableau MP → organe → métier → latence` à partir de `entities.jsonl` ET d'une **ontologie médicale formelle** (ICD-11 + SNOMED-CT + MeSH + NAF FR). Choix : Neo4j ? Kuzu ? in-memory NetworkX ? Architecte le pipeline graph-augmented retrieval (graph traversal + vector + BM25). Cible : multi-hop queries (« amiante → quelle pathologie + quel tableau + quelle surveillance ? »). **NB Gemini** : pas de GraphRAG décoratif — ton schéma doit répondre à 10 vraies questions MdT.
- **II.2 [Agentic Retrieval — top-k itératif]** Passer d'un top-k statique à une **recherche itérative agentique** : l'agent évalue la qualité du top-k initial, reformule, re-cherche, croise sources, demande explicitement no-answer si insuffisant. Sous-agents spécialisés : sous-agent toxico (lookup CAS, VLEP), sous-agent juridique (Légifrance, jurisprudence), sous-agent clinique (PubMed, Cochrane). Orchestrateur LLM (Claude / GPT-5.5 / Kimi).
- **II.3 [Re-ranking]** Ajouter un re-ranker post-retrieval (cross-encoder type Jina rerank-v2, ou LLM-as-judge mini sur le top-50). Mesurer le gain nDCG@10.
- **II.4 [Multi-modal]** Les fiches Bossons Futé contiennent du JSON structuré. Tester une voie multi-modale (texte + structured) au lieu de tout aplatir en texte.
- **II.5 [Hybrid Storage]** LanceDB pour les vecteurs + SQLite WAL pour les métadonnées + Parquet pour archive — tracer une architecture de référence avec rôles séparés.

### CATÉGORIE III — Couverture (semaines 4-10)

- **III.1 [Acquisition continue]** La frontière full-text est ~5 %/scrapper. Architecte un pipeline d'acquisition durable : (a) PMC efetch pour le bulk, (b) HAL/OpenAire pour le gris valide, (c) Légifrance pour le réglementaire FR, (d) un fallback Sci-Hub résidentiel pour le paywall *uniquement éthiquement justifié*.
- **III.2 [Multilinguisme sémantique sans perte FR]** Étendre la couverture FR (priorité MdT FR) et EU (DE, ES, IT) + sources internationales (OMS, ILO, IARC, NIOSH). Cible : 250 K works FR vrais (vs 128 K actuels). **Contrainte Gemini** : pas de perte de précision métier FR (le filtre francisation Couche 2 doit rester opérant).
- **III.3 [Sources prestigieuses]** Cibler NEJM/JAMA/Lancet/BMJ via licences instutionnelles (CHU partenariats, ASSTV86 abonnements). Pas tout PubMed open : focaliser sur SST/médecine du travail/épidémio.
- **III.4 [Données structurées]** Tableaux MP RG/RA, tableaux ECHA, GESTIS, IARC, NIOSH — non vectorisés mais accessibles via MCP. Industrialiser cette voie.

### CATÉGORIE IV — Rigueur méthodologique (semaines 6-12)

- **IV.1 [Benchmark étendu]** Passer de 49 à 300+ requêtes FR MdT. Catégories supplémentaires : visite de pré-reprise, restriction médicale, mi-temps thérapeutique, inaptitude, RQTH, télétravail.
- **IV.2 [Évaluation rigoureuse]** Adopter RAGAS (faithfulness, answer relevance, context precision) + LLM-as-judge multi-voix (Claude + GPT-5.5 + Kimi) sur le benchmark. Mesurer la reproductibilité (3 runs, écarts).
- **IV.3 [Bake-off embedders]** Tester périodiquement nouveaux modèles (Qwen4, Voyage-4, Cohere v4, modèles FR spécialisés). Comparer cross-lingual FR↔EN + médical sur benchmark. Décision gold standard à 6 mois.
- **IV.4 [Calibration empirique des boosts]** Grid search ou bayes opt sur les boosts Couche 2 (EBM×1,3 / SST×2 / FR×2 / récence×1,3). Critère cible nDCG@10 + diversité.
- **IV.5 [No-answer threshold]** Calibrer empiriquement le seuil cosine pour « pas de preuve établie » en fonction de la catégorie de requête.
- **IV.6 [Audit retrieval métier mensuel]** Routine MdT qui chaque mois auditer 30 requêtes random + rapport gravity-based.

### CATÉGORIE V — Innovation / Prospective (semaines 12+)

- **V.1 [Fine-tuning ciblé MdT]** Évaluer la valeur d'un mini fine-tuning (LoRA) sur un modèle d'embedding ou de raisonnement pour spécialisation MdT FR. ROI à mesurer.
- **V.2 [Raisonnement clinique opposable]** Layer 3 : pour chaque réponse, générer une « chaîne de raisonnement opposable » (sources citées, niveau de preuve, alternatives considérées, raison du choix). Format AVIS médical défendable.
- **V.3 [Mémoire patient-anonyme]** Garder mémoire de cas-clinique anonymisés (pseudonymisés, EDS-Pseudo style) pour informer les futures requêtes du même MdT — micro-RAG personnel.
- **V.4 [Multi-tenant SPSTI]** Architecturer pour ouvrir DEBBY à d'autres médecins du travail FR (SPSTI partenariats). Gouvernance, sécurité, isolation.
- **V.5 [Continuous corpus]** Daily delta : un nouveau full-text intégré le matin → embeddé → mergé → dispo le soir. Streaming pipeline.
- **V.6 [Multi-modal images médicales]** Pour les fiches métier + cas-cliniques avec photos / schémas — utiliser CLIP / SigLIP / Voyage-multimodal pour ouvrir la recherche multi-modale.
- **V.7 [Versioning sémantique]** `corpus_version=2.1`, `chunking_version=pc-3600-v1`, `embed_version=qwen3-1`, etc. Reproductibilité long-terme + comparaisons.

---

## 4. Critères de succès

Tes propositions sont jugées sur :

| Critère | Pondération |
|---|---|
| **Impact MdT FR** (résout un vrai problème du MdT en routine) | 30 % |
| **Faisabilité court terme** (PoC réalisable en ≤2 semaines de dev) | 20 % |
| **Rigueur méthodologique** (mesurable, reproductible, ablation possible) | 20 % |
| **Innovation justifiée** (SOTA appliqué pertinent, pas hype) | 15 % |
| **Préservation archi découplée** (respecte BYOE Table A/B) | 10 % |
| **Documentation / opposabilité** (livrable directement intégrable) | 5 % |

---

## 5. Livrables attendus

À déposer dans une PR sur https://github.com/reddepot/debby-audit-snapshot ou via email :

1. **`ROADMAP.md`** — feuille de route 12 mois priorisée (15-25 chantiers, effort × impact).
2. **`ADR/`** — un ADR (Architecture Decision Record) par chantier majeur des catégories II + V.
3. **`prototypes/`** — au moins **3 PoC fonctionnels** parmi les catégories II et V (code + démo).
4. **`benchmark_extended.jsonl`** — extension du benchmark FR (+ 50 requêtes minimum).
5. **`side_tables_v2/`** — fixes des catégories I (correctifs immédiats, **livrables ≤2 semaines**).
6. **`VISION.md`** — synthèse stratégique (5-10 pages) : où DEBBY peut être dans 2 ans, conditions de succès, risques.
7. **`benchmarks_results.md`** — résultats reproductibles des évals catégorie IV.2 / IV.3.

---

## 6. Garde-fous

- **Anti-scope-creep** : si une proposition dépasse 6 semaines de dev solo, splitter en sous-chantiers ou la classer V (prospective long-terme).
- **Respect du découplage BYOE** : aucune proposition ne doit recoupler Table A et Table B (genre « ré-embed obligatoire pour mettre à jour le source_type »). Side-tables sinon rien.
- **Pas de re-architecture for-the-sake-of-it** : si LanceDB suffit, ne pas proposer Milvus/Weaviate sans bénéfice mesurable.
- **Anti-hype** : si tu proposes du fine-tuning, donne le ROI mesuré attendu (% gain métrique). Sinon, défère.
- **Honneur les anomalies déclarées** : ne pas redéclarer une anomalie déjà listée comme un finding original.
- **Conformité RGPD/HDS** : le médical FR a un cadre. PII, hébergement, conservation — chaque proposition doit être conforme ou explicitement signaler le gap.

---

## 7. Comment commencer

```bash
# 1. Fork + clone
git clone git@github.com:reddepot/debby-audit-snapshot.git
cd debby-audit-snapshot

# 2. Lire le doc principal + scripts/layer2.py + scripts/build_lancedb.py
$EDITOR DEBBY_AUDIT_SNAPSHOT.md scripts/layer2.py scripts/build_lancedb.py

# 3. Lancer un retrieval brute-force sur 1 % du corpus (depuis accès NDA)
python3 scripts/retrieval_sanity.py

# 4. Catégoriser : I (correctifs) → II/III (archi/couverture) → IV (rigueur) → V (innovation)
# 5. Pour chaque chantier : ADR_<chantier_id>.md + PoC code + benchmark mesuré

# 6. Livrer en plusieurs PR par catégorie (pas un big-bang PR)
```

Accès corpus complet sous NDA : `redtech@protonmail.com` (intention d'usage + identité).

---

## 8. Phrases-clés à se rappeler

> *« L'objectif n'est pas d'ajouter de la complexité, mais d'augmenter la confiance mesurable. »*
>
> *« Toute innovation doit améliorer au moins une métrique : retrieval, citation, sécurité, maintenabilité, ou valeur métier MdT. Sinon, défère. »*
>
> *« DEBBY doit savoir dire non, citer juste, et expliquer pourquoi. »*
>
> *« Un GraphRAG décoratif vaut moins qu'une side-table v2 livrée. »*

---

## 9. Anti-patterns à éviter (vous serez recadré)

- **Roadmap futuriste sans séquençage** : « dans 5 ans on aura X » sans étapes intermédiaires = inutile.
- **GraphRAG décoratif sans schéma métier** : si le graphe ne répond pas à une vraie question MdT (« amiante → tableau ? → délai ? »), il n'a pas sa place.
- **Fine-tuning proposé avant benchmark solide** : sans baseline mesurée, l'amélioration n'est pas démontrable.
- **Optimiser la latence avant la qualité clinique** : un MdT préfère attendre 5 s pour une bonne réponse que 500 ms pour une mauvaise.
- **Confondre complétude corpus et fiabilité réponse** : ajouter 10 M docs sans curating est anti-progrès.
- **Négliger rétractations, réglementation, no-answer** : ce sont les trois piliers de l'opposabilité MdT.
- **Recoupler Table A et Table B** : si une de vos propositions casse l'invariant BYOE, c'est non.
- **Re-architecturer for-the-sake-of-it** : LanceDB / Milvus / Weaviate — argumente le passage avec mesure, pas avec mode.

---

## 10. Format de sortie structuré (livrable obligatoire)

En plus du `ROADMAP.md` narratif, livrer un JSON parsable :

```json
{
  "roadmap_id": "evolve-debby-2026-05-NN",
  "author_handle": "votre nom / org",
  "horizon_jours": 365,
  "chantiers": [
    {
      "chantier_id": "I.1",
      "category": "correctif_immediat | architecture | couverture | rigueur | innovation",
      "name": "EBM v2 — durcissement du tag ebm=1",
      "objectif_metric": "nDCG@10 sur benchmark FR",
      "baseline": 0.68,
      "target": 0.80,
      "effort_jours": 3,
      "impact_score": 9,
      "risk_score": 2,
      "priority_p0_p1_p2_p3": "P0",
      "depends_on": [],
      "preserve_byoe": true,
      "deliverables": ["side_tables_v2/ebm.json", "scripts/apply_ebm_v2.py", "benchmarks/ebm_ablation.md"],
      "go_no_go_criteria": "delta nDCG@10 ≥ +0.05 sur 30 requêtes test"
    }
  ],
  "vision_2_ans": "string (5-10 phrases)",
  "risks": [
    {"risk": "scope creep si GraphRAG mal cadré", "mitigation": "PoC sur 10 substances seulement avant scale"}
  ],
  "top10_priorities": ["I.1", "I.2", "IV.1", "..."]
}
```

---

## 11. Esprit de la mission

> *Tu ne réinventes pas DEBBY. Tu le fais grandir, intelligemment.*
>
> *Ce qui rend DEBBY remarquable n'est pas la taille (2,6 M works n'est pas extraordinaire), mais la **rigueur architecturale** (découplage BYOE, side-tables, content-addressed IDs) et la **cible métier précise** (MdT FR). Ton apport doit prolonger ces deux qualités.*
>
> *Le critère ultime : un MdT français doit, après tes améliorations, **gagner un acte clinique opposable en moins de 5 minutes** sur un cas où DEBBY actuellement échoue ou répond partiellement.*

Date butoir suggérée : **30 jours** pour la ROADMAP + **90 jours** pour les PoC catégorie I + II prioritaires.

---

— *Brief co-rédigé par Claude Opus 4.7 + Kimi K2.6 (CLI) + Codex GPT-5.5 (CLI) + Gemini 3 Pro (CLI), consolidé le 2026-05-26.*
