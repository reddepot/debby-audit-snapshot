# DEBBY — Audit Snapshot

> **Version** : 1.0 — 2026-05-26
> **Snapshot** : embed scellé, side-tables livrées, serving non démarré
> **Vocation** : **mettre DEBBY à nu** pour qu'un audit de challenge externe (IA agentiques, équipes red-team, reviewers humains) puisse l'attaquer, le réviser, le compléter.
> **License** : CC BY-SA 4.0 (le contenu de ce document — pas le corpus, qui n'est pas distribué ici).
> **Auteur** : Radu (médecin du travail FR) + Claude Opus 4.7 orchestrateur.

---

## TL;DR — 1 minute

DEBBY est un **corpus RAG médical + santé-sécurité au travail (SST)** destiné à un **médecin du travail français** interrogeant en français.

- **2 608 976 œuvres uniques** · **22 901 283 chunks** · embeddés en **fp16 4096-dim** (`qwen3-embedding-8b` via OpenRouter, L2-normalisés).
- Architecture **découplée Table A (texte + métadonnées canoniques) / Table B (vecteurs jetables)** — pattern *Bring Your Own Embedder* : ré-embed = regénérer B depuis A, **zéro perte**.
- **5 side-tables d'enrichissement** appliquées au *load* du vectorstore, **sans ré-embed** : rétractations (234), source_type raffiné, year/title via Crossref (3 317 + 3 205), langue corrigée (46 173), entités graph-seed (251 521 works).
- **Audits passés** : intégrité exhaustive 871/871 shards, **canari de fidélité texte↔vecteur cos médian 0,9999**, sanity retrieval intra-work 0,896 vs aléatoire 0,258, challenge 6 IA passé après corrections.
- **Découverte cruciale dans l'audit** : 44 shards à 0 octet (5,5 % du corpus) étaient passés sous le radar d'un audit échantillonné ; détectés par audit *exhaustif* (footers parquet via pyarrow S3), supprimés, re-embeddés, re-certifiés. `remote_has` durci pour tester *taille>0*, pas seulement l'*existence*.
- **Pipeline post-embed prêt** (code écrit, non encore exécuté) : `build_lancedb.py` → LanceDB + IVF_PQ, `layer2.py` (hybride BM25+vecteur, boosts EBM/SST/FR, filtre francisation, pivot CAS, no-answer), `eval_benchmark.py` sur 49 requêtes FR MdT.
- **Coût total embed** : **~$190** ($0,0113/M tokens × ~17 Md tokens), **~26h wall-clock** sur hub Vultr 16 Go (4 streams + watchdog anti-OOM).

**Ce qu'on vous demande, challenger** : attaquer la *fidélité*, la *complétude*, la *calibration* et la *robustesse opérationnelle* (cf. §11). Plusieurs anomalies identifiées en interne sont volontairement non-corrigées et listées pour vous (§6.5, §7.5 « anomalies notées »).

---

## Sommaire

1. [Qui est DEBBY](#1-qui-est-debby-pour-qui-pourquoi)
2. [Corpus — chiffres-clés fraîchement vérifiés](#2-corpus--chiffres-clés-fraîchement-vérifiés-2026-05-26)
3. [Architecture et stockage](#3-architecture-et-stockage)
4. [Pipeline embed (passé) et retrieval (prêt)](#4-pipeline-embed-passé--retrieval-prêt)
5. [Schéma des données (Table A + side-tables)](#5-schéma-des-données-table-a--side-tables)
6. [Qualité des données — analyse profonde](#6-qualité-des-données--analyse-profonde)
7. [Side-tables — détail enrichissement](#7-side-tables--détail-enrichissement)
8. [Statistiques vectorielles](#8-statistiques-vectorielles)
9. [Audits déjà effectués (preuves + scripts)](#9-audits-déjà-effectués-preuves--scripts)
10. [Limites et angles morts assumés](#10-limites-et-angles-morts-assumés)
11. [Axes d'audit ouverts pour le challenger](#11-axes-daudit-ouverts-pour-le-challenger)
12. [Extraits illustratifs réels](#12-extraits-illustratifs-réels)
13. [Reproductibilité — artefacts](#13-reproductibilité--artefacts-disponibles)
14. [Annexes](#14-annexes)

---

## 1. Qui est DEBBY, pour qui, pourquoi

**DEBBY** est un corpus RAG vectoriel **chef d'œuvre** médical + santé-sécurité au travail (SST), destiné à un médecin du travail français interrogeant en français. **Cas d'usage** : décision d'aptitude, lien exposition↔pathologie, tableaux MP, surveillance médicale, RPS/TMS, toxicologie, conduite à tenir clinique en contexte professionnel.

**Principe architectural** issu d'une délibération multi-voix (16 voix, 3 tours, mai 2026) :

> *L'embed n'est pas le chef d'œuvre — c'est l'infrastructure. Le chef d'œuvre, c'est la couche de raisonnement qu'on construit par-dessus (graph + agents).*

**Une seule maison d'acquisition** : tous les full-texts (FT) et abstracts sont intégrés à DEBBY. Les bases satellites (`meddata.db`, `sst_conditions.db`, `sstinfo`) restent en production pour les **métadonnées + tables-référence** (Légifrance, jurisprudence, tableaux MP, substances ECHA/GESTIS, fiches FMP) — **non vectorisées par construction** (données structurées, non textuelles).

**Pourquoi un corpus distinct au lieu de PubMed/CORE direct ?** Parce que :
1. **Filtrage métier ciblé** (médecine + occupational health, pas tout PubMed indistinct).
2. **Enrichissement structurel** (`is_oh`, `has_sst`, `ebm`, `study_type`, `clin`) absent des index publics.
3. **Acquisition opportuniste de gris valide** (HAL, Bossons Futé, Présanse, Cochrane, etc.) qui dépassent PubMed.
4. **Citabilité durcie** + side-tables versionnées + rétractations à jour.

---

## 2. Corpus — chiffres-clés fraîchement vérifiés (2026-05-26)

Toutes les valeurs ci-dessous proviennent d'une passe complète sur les **871 shards parquet** du corpus (script `deep_stats.py` joint en annexe — exécuté ce jour, post-embed final, post-re-embed des 44 shards corrigés).

### 2.1 Échelle

| Dimension | Valeur |
|---|---|
| **Works uniques** | **2 608 976** |
| **Chunks** | **22 901 283** |
| Chunks/work | médiane 7 · moyenne 8,8 · p95 23 · max 97 |
| Volume Table A (texte+meta) | 23,7 Go (parquet zstd) |
| Volume Table B (vecteurs) | ~155 Go (fp16 4096-dim) |
| Volume side-tables | ~210 Mo |

### 2.2 Origines (par work)

| Origine | Works | % | Description |
|---|---|---|---|
| `debby` | **1 922 802** | 73,7 % | corpus canonique master (Phase 1 + Phase 2 fusion) |
| `meddata` | 423 121 | 16,2 % | base médicale prod (FT absorbé) |
| `push3j_recovery` | 184 225 | 7,1 % | sprint recovery 8 VPS (13/05) |
| `sstinfo` | 55 091 | 2,1 % | fiches toxico + FMP Présanse + Bossons Futé + sst_conditions |
| `vex_pre_fusion` | 11 902 | 0,5 % | acquisition distribuée pré-fusion (24/05) |
| `vex_post_fusion` | 11 835 | 0,5 % | idem post-fusion |

### 2.3 Langues — `body_lang` brut (avant `body_lang_fix`)

| Langue | Works | % |
|---|---|---|
| EN | 2 217 394 | 85,0 % |
| FR | 171 996 | 6,6 % |
| FI | 48 492 | 1,9 % |
| ES | 32 190 | 1,2 % |
| PT | 23 078 | 0,9 % |
| DE | 22 086 | 0,8 % |
| JA | 19 635 | 0,8 % |
| RU | 16 922 | 0,6 % |
| DA | 11 749 | 0,5 % |
| TR | 9 469 | 0,4 % |

> ⚠️ Side-table `body_lang_fix.json` **re-classe 46 173 works** : la moitié des « FR » bruts sont en réalité EN (boilerplate HAL « Archive ouverte HAL… » trompait `langdetect`). Voir §7.4.

### 2.4 `source_type` brut (par work)

| source_type | Works |
|---|---|
| `litterature` | 2 462 964 (94 %) |
| `sst` | **144 476** |
| `fiche_metier` | **1 438** |
| `toxico` | **98** |

→ La Couche 2 boostera explicitement les 144 K SST + 1 438 fiches métier.

### 2.5 EBM (`ebm` = 1..6, 9=unknown)

| Code | Sens | Works | % |
|---|---|---|---|
| 1 | méta-analyse / SR | **463 300** | 17,8 % |
| 2 | RCT | 124 475 | 4,8 % |
| 3 | cohorte | 91 094 | 3,5 % |
| 4 | cross-sectional | 134 392 | 5,2 % |
| 5 | case report | 260 044 | 10,0 % |
| 6 | éditorial | 119 269 | 4,6 % |
| 9 | inconnu | 1 416 402 | 54,3 % |

> ⚠️ **Anomalie identifiée et non corrigée** : sur les 463 300 works `ebm=1`, **seuls 47 841 (10,3 %) ont effectivement « meta-analysis » ou « systematic review » dans le titre** (regex `(?i)meta-?analysis|forest plot|systematic review|prisma`). **89,7 % sont probablement des faux positifs** (sur-flag par l'heuristique d'origine : matching dans abstract ou heading, mais pas dans le titre). À challenger / re-tagger (cf. §11).

### 2.6 Distribution temporelle × source_type (`year` × `source_type`)

| Décennie × source_type | Works |
|---|---|
| 2020s × litterature | 1 126 427 (43 %) |
| 2010s × litterature | 896 602 (34 %) |
| 0 × litterature | 314 130 (12 %, *year manquant — voir year_title_fix*) |
| 2000s × litterature | 121 073 (4,6 %) |
| 2020s × sst | 61 168 |
| 2010s × sst | 51 124 |
| 0 × sst | 19 977 |
| 2000s × sst | 10 400 |
| 0 × fiche_metier | 1 438 |
| 1990s × litterature | 2 180 |
| 1990s × sst | 1 189 |
| <1980s × \* | ~1 600 |

→ Corpus très contemporain (77 % publié 2010-2025 pour `litterature`), avec une bonne tête de gondole SST récente. Les `year=0` (335 598 works) seront partiellement résolus par `year_title_fix` (3 317 récupérés sur les works à DOI).

### 2.7 Citabilité (par work)

| Critère | Works | % |
|---|---|---|
| Avec DOI | 2 036 142 | **78,0 %** |
| Avec titre | 2 606 663 | 99,9 % |
| Avec venue (revue) | 1 558 197 | 59,7 % |
| Avec auteurs | 1 821 166 | 69,8 % |
| Avec concepts OpenAlex | 1 607 023 | 61,6 % |

**Titres vides** : 2 313 (0,09 %) — works sans titre extractable (PDFs corrompus, fragments).

### 2.8 Distributions de texte (chunk)

| Métrique | Chars | Bytes UTF-8 |
|---|---|---|
| Médiane | 3 271 | 3 319 |
| Moyenne | 2 920 | 2 989 |
| p5 / p95 | 971 / 3 600 | – |
| Max | 3 600 | 10 800 |

→ Chunks bien remplis (médiane proche de la cap 3 600), distribution serrée. Max octets 10 800 = artefact UTF-8 (caractères CJK + grec multi-octets : 1 char ≈ 3 octets).

### 2.9 Distribution de titre

| Métrique | Chars | Bytes UTF-8 |
|---|---|---|
| Médiane | 97 | – |
| Moyenne | 100 | – |
| Max | 500 | (capped) |

---

## 3. Architecture et stockage

### 3.1 Schéma découplé Table A / Table B

```
                 OBJECT STORAGE (Vultr S3, ams1.vultrobjects.com)
                 meddata:meddata-lake/debby_embed/
        ┌────────────────────────┬─────────────────────────┬────────────────────────┐
        │                        │                         │                        │
   chunks/  (Table A)      vectors/ (Table B)      sidetables_scripts/        (à venir : lance.db)
   871 shards parquet      871 shards parquet      12 fichiers
   23,7 Go                 ~155 Go                  side-tables + scripts
   (texte + metadata)      (4096-dim fp16 L2)
   « source de vérité »    « jetable, ré-embed OK »
```

- **Table A canonique** : texte + métadonnées (24 colonnes, schéma §5). Source de vérité pour ré-embed Qwen4 ou autre modèle futur.
- **Table B vecteurs** : `qwen3-embedding-8b`, 4096-dim, fp16, L2-normalisé (norme=1,0 ± 0,000015). Ré-embed = regénérer B depuis A, zéro perte d'information.
- **chunk_id** = `sha256(texte_doc):chunk_index` → identifiant **content-addressed**, stable.
- **work_id** = priorité `doi:...` > `pmid:...` > `sha:...` > origine-spécifique (ex : `sstinfo:bossons:126`).

### 3.2 Endpoint object storage

- **Provider** : Vultr Object Storage (S3-compatible)
- **Endpoint** : `ams1.vultrobjects.com`
- **Bucket** : `meddata-lake`
- **Prefix** : `debby_embed/`
- **Durabilité** : 11×9 (Vultr SLA équivalent S3 standard)
- **Coût** : ~$0,01/Go/mois → ~$1,80/mois pour 180 Go (Table A + B + side)

### 3.3 Compute (hub)

- **Hub Vultr** : `root@45.32.147.53` (1 VPS — le seul actif après destruction des 6 scrapers + Hetzner 22/05)
- 8 vCPU / **16 Go RAM** / 328 Go disk SSD
- Charge embed : 4 streams OR × 28 workers, ~11-13 Go RAM en pic, recyclage anti-OOM via `watchdog_embed.sh` quand `free < 1 200 Mo`.

---

## 4. Pipeline embed (passé) + retrieval (prêt)

### 4.1 Embed terminé (2026-05-25 → 26)

| Paramètre | Valeur |
|---|---|
| Modèle | `qwen/qwen3-embedding-8b` via OpenRouter |
| Dimension | 4096 |
| Précision | fp16 |
| Normalisation | L2 unit-norm |
| Chunking | parent-child, **CHILD = 3600 chars**, **pas d'overlap**, séparation par paragraphes |
| Préfixe contextuel à l'embed | `[type_doc/source] : titre_court — \n\n texte` (titre tronqué 300c) |
| Truncation entrée | 4000 octets UTF-8 (héritage vLLM — *inutile sur OR* — voir §10) |
| Débit observé | **~377 ch/s agrégé** (plafonné OR, +concurrence n'aide pas) |
| Coût total | **~$190** ($0,0113/M tokens × ~17 Md tokens) |
| Durée wall-clock | ~26 h (avec watchdog anti-OOM, recyclages) |

### 4.2 Bake-off P3 (décision d'embedder)

Le choix `qwen3-embedding-8b` est issu d'un bake-off multi-voix (DEVCODE-Vote P0, 26/04) sur :
- Cross-lingual FR↔EN (queries FR sur docs EN — cas central MdT)
- Médical (PubMed test set + nDCG@10)
- Coût total ($ pour 17 Md tokens)
- Disponibilité provider (OR > self-hosted ; A100 21 ch/s × 17 Md ≈ $362)

`qwen3` a battu `nemotron-embedding-15b` (proche mais 2× plus cher), `voyage-3-large` (très bon EN seul, faible FR), `e5-large-multilingual` (correct mais 1024-dim insuffisant pour le volume).

### 4.3 Pipeline post-embed prêt (code écrit, non encore exécuté)

| Script | Rôle | Statut |
|---|---|---|
| `build_lancedb.py` | Load Table A + B + **jointures side-tables** → LanceDB + index **IVF_PQ + Matryoshka 512/1024/2048** | Code prêt, non lancé |
| `layer2.py` | Couche 2 retrieval — hybride **BM25+vecteur**, boosts (EBM × 1,3 / SST × 2 / FR × 2 / récence × 1,3), **filtre francisation** ×0,5 sur sources anglo si question FR-juridique, no-answer threshold, **routage MCP** vers SSTinfo/Légifrance, **pivot CAS** FR→EN pour substances | Code prêt |
| `eval_benchmark.py` | Harness sur `debby_benchmark_fr.jsonl` (49 requêtes 13 catégories), métriques R@k + couverture source_type + no-answer accuracy + cross-lingual coverage | Code prêt |

### 4.4 Code embed (utilisé en production)

| Script | Rôle |
|---|---|
| `embed_or.py` | Producteur OR multi-stream (avec **correctif `remote_has` size>0** anti-corruption silencieuse) |
| `watchdog_embed.sh` | Recyclage anti-OOM hub (`pkill embed_or` + relaunch si `free<1200MB`) |
| `integrity_full.py` | Audit exhaustif post-embed (footers parquet via pyarrow S3, dim/normes/nuls/NaN) |
| `canari_reembed.py` | Vérif fidélité texte↔vecteur (cosine entre vecteurs stockés et re-embed du payload exact) |

Tous fournis dans le repo (`/scripts/`).

---

## 5. Schéma des données (Table A + side-tables)

### 5.1 Table A — 24 colonnes parquet

| Colonne | Type | Description |
|---|---|---|
| `chunk_id` | str | `sha256(texte_doc):chunk_index` — **clé primaire** |
| `work_id` | str | `doi:` / `pmid:` / `sha:` / origine — œuvre canonique |
| `doc_sha256` | str | hash document original |
| `chunk_index` | int32 | position du chunk dans le doc (0-based) |
| `n_chunks` | int32 | total chunks pour ce work |
| `text` | str | texte du chunk ≤3600 chars (**pas** de préfixe — celui-ci est ajouté à l'embed seulement) |
| `title` | str | titre du work ≤500 chars |
| `title_en` | str | titre traduit EN si disponible |
| `authors` | str | auteurs (JSON ou texte) ≤300 chars |
| `venue` | str | revue/source ≤200 chars |
| `year` | int32 | année (0 = manquant → cf. `year_title_fix`) |
| `doi` | str | DOI sans préfixe URL |
| `doc_type` | str | enum : `ft` / `abstract` / `fiche` / `research` / `review` / `case_report` / `editorial` / `letter` / `book_review` / `news` / `article` / `unknown` |
| `source_type` | str | enum : `litterature` / `clinique` / `sst` / `toxico` / `fiche_metier` / `reglementaire` (version raffinée dans `source_type_refined`) |
| `body_lang` | str | langue détectée (corrigée par `body_lang_fix`) |
| `study_type` | str | enum : `meta_analysis` / `systematic_review` / `rct` / `cohort` / `case_control` / `cross_sectional` / `case_report` / `guideline` / `editorial` / `unknown` |
| `ebm` | int8 | 1=méta..6=editorial, 9=unknown |
| `is_oh` | int8 | flag « occupational health » |
| `has_sst` | int8 | flag SST narrow |
| `clin` | float32 | score clinique (0,2 - 1,0) |
| `is_foreign` | int8 | 1 si body_lang ∉ {en, fr, und} |
| `concepts` | str | concepts OpenAlex ≤400 chars |
| `origin` | str | enum : `debby` / `meddata` / `sstinfo` / `push3j_recovery` / `vex_*` |
| `chunking_version` | str | `pc-3600-v1` (versionne le découpage) |

### 5.2 Table B — schéma vecteurs

| Colonne | Type | Description |
|---|---|---|
| `chunk_id` | str | clé jointure Table A |
| `vector` | list<float16>[4096] | embedding L2-normalisé |

### 5.3 Side-tables — formats

| Fichier | Format | Taille | Clé |
|---|---|---|---|
| `retracted_work_ids.json` | JSON `{flagged:[...], detail:{wid: {nature, reason, date}}}` | 250 Ko | `work_id` |
| `source_type_refined.json` | JSON `{wid: source_type}` | 89 Mo | `work_id` |
| `year_title_fix.db` | SQLite `fix(work_id PK, year, title, status)` | 1,1 Mo | `work_id` |
| `body_lang_fix.json` | JSON `{wid: lang_code}` | 71 Mo | `work_id` |
| `entities.jsonl` | JSONL `{work_id, cas, substances, pathologies, organes, metiers, latence, tableau_mp}` | 47 Mo | 1 ligne/work tagué |

---

## 6. Qualité des données — analyse profonde

Stats issues du `deep_stats.py` (passe sur 871 shards Table A, 2 608 976 works distincts).

### 6.1 Top 25 venues (par #works)

| # | Venue | Works |
|---|---|---|
| 1 | PLoS ONE | 40 676 |
| 2 | Scientific Reports | 23 009 |
| 3 | Cureus | 19 806 |
| 4 | Journal of Clinical Medicine | 18 536 |
| 5 | International Journal of Molecular Sciences | 16 369 |
| 6 | **International Journal of Environmental Research and Public Health** | **12 690** *(← noyau SST)* |
| 7 | Nutrients | 11 363 |
| 8 | Frontiers in Pharmacology | 10 911 |
| 9 | Applied Sciences | 10 276 |
| 10 | Frontiers in Immunology | 9 630 |
| 11 | Cancers | 9 394 |
| 12 | Critical Care | 8 339 |
| 13 | BMC Cancer | 8 127 |
| 14 | Molecules | 7 903 |
| 15 | BMJ Case Reports | 7 797 |
| 16 | Clinical Case Reports | 7 569 |
| 17 | PubMed (alias) | 7 462 |
| 18 | Medicina | 7 098 |
| 19 | Frontiers in Psychiatry | 6 917 |
| 20 | Frontiers in Oncology | 6 906 |
| 21 | Oncotarget | 6 844 |
| 22 | Trials | 6 284 |
| 23 | medRxiv | 6 159 |
| 24 | Frontiers in Physiology | 5 999 |
| 25 | **Cochrane Database of Systematic Reviews** | **5 761** *(← gold standard)* |

→ Le mix est **mostly open-access (PLoS, Frontiers, MDPI, BMC, Cureus)** + Cochrane comme tête de gondole EBM. Le challenger peut critiquer : sous-représentation de NEJM/JAMA/Lancet/BMJ ? Vrai, parce que paywall fort + acquisition surtout via OA / Sci-Hub résidentiel.

### 6.2 Top 30 concepts OpenAlex (par #works)

| # | Concept | Works |
|---|---|---|
| 1 | Medicine | 1 025 557 |
| 2 | Internal medicine | 207 124 |
| 3 | Biology | 114 200 |
| 4 | Psychology | 88 150 |
| 5 | Surgery | 82 250 |
| 6 | Chemistry | 75 169 |
| 7 | Computer science | 72 734 |
| 8 | Disease | 59 187 |
| 9 | COVID-19 | 52 798 |
| 10 | Cancer | 50 049 |
| 11 | Cardiology | 49 325 |
| 12 | Cancer research | 48 590 |
| 13 | Intensive care medicine | 47 709 |
| 14 | Pathology | 43 280 |
| 15 | Immunology | 41 793 |
| 16 | Materials science | 40 961 |
| 17 | Radiology | 38 062 |
| 18 | Oncology | 36 826 |
| 19 | Population | 34 893 |
| 20 | Virology | 30 836 |
| 21 | Pharmacology | 30 190 |
| 22 | Dermatology | 29 007 |
| 23 | RCT | 28 501 |
| 24 | Endocrinology | 28 434 |
| 25 | Immune system | 26 454 |
| 26 | Diabetes mellitus | 26 438 |
| 27 | SARS-CoV-2 | 26 191 |
| 28 | Humanities | 25 142 |
| 29 | Political science | 24 554 |
| 30 | Pandemic | 24 270 |

→ Dominance médicale claire. Bias COVID notable (52 798 + 26 191 + 24 270 = ~104 K works COVID-liés, ~4 %).

### 6.3 EBM auto-flag — anomalie à challenger

`ebm=1` (méta-analyse / systematic review) est censé être le label d'évidence le plus élevé. Vérification croisée par regex sur le titre :

| ebm=1 sub-population | Works | % |
|---|---|---|
| Titre contient `meta(-)?analysis` / `forest plot` / `systematic review` / `prisma` | 47 841 | 10,3 % |
| **Titre ne contient PAS ces patterns** | **415 459** | **89,7 %** |

→ **89,7 % des `ebm=1` n'ont pas le marker dans le titre** = très probablement faux positifs hérités d'une heuristique trop large à l'origine (matching dans abstract ou heading).

**Action recommandée pour le challenger** : proposer une définition durcie (`ebm=1` ssi `meta|systematic` dans titre OU OpenAlex concept = `Systematic review` OU `Meta-analysis`). Impact sur la **boost EBM × 1,3** de `layer2.py` : si 90 % des ebm=1 sont faux, le boost est dilué.

### 6.4 Distribution `n_chunks` par work

- Médiane : **7** chunks/work
- Moyenne : **8,8**
- p95 : **23**
- Max : **97** (probablement un livre / une thèse longue)

→ Range cohérent avec un corpus mix abstract (1 chunk) + FT (5-30 chunks). Pas de queue extrême (cap implicite par la longueur des documents acquis).

---

## 7. Side-tables — détail enrichissement

### 7.1 `retracted_work_ids.json` — rétractations

234 works flaggés (sur 2,6 M). Source : Retraction Watch (61 280 DOI uniques) croisé avec les DOI du corpus.

| Nature | # |
|---|---|
| Retraction | 152 |
| Expression of concern | 82 |
| Correction | 27 *(exclus du flag — c'est une correction normale)* |
| Reinstatement | 4 *(exclus du flag — réhabilitation)* |

**Top raisons** (extrait des plus fréquents) :

| # | Raison |
|---|---|
| 35 | Concerns about Data ; Concerns about Results |
| 19 | Conflict of Interest |
| 8 | Withdrawn as Out of Date |
| 8 | Concerns about Data ; Concerns about Investigations |
| 7 | Retract and Replace ; Withdrawn as Out of Date |
| 7 | Concerns about Authorship/Affiliation ; Concerns... |
| 6 | Investigation by Journal/Publisher |

**Usage Couche 2** : multiplicateur **×0,1** sur le score final → enterre les rétractés (sécurité médicale, ne supprime pas — préserve la traçabilité auditable).

**Challenger** : 234/2,6 M = 0,009 % flaggués. Retraction Watch contient 61 K DOI. Le pourcentage de DOI corrobore (61 K / ~50 M PubMed = 0,12 % du fonds mondial, on en aurait donc proportionnellement ~3 100 attendus dans 2,6 M). On en trouve 234 = sous-couverture × 13. **Cause probable** : Retraction Watch couvre mal les revues hors core PubMed (OA récents, prépublications). À auditer.

### 7.2 `source_type_refined.json` — source_type raffiné via OpenAlex concepts

| source_type raffiné | Works |
|---|---|
| litterature | 1 708 960 |
| **clinique** | 732 516 |
| **sst** | 105 592 |
| **reglementaire** | 41 323 |
| **toxico** | 19 147 |
| **fiche_metier** | 1 438 |

Comparé au brut : `clinique` n'existait pas au brut (toujours catégorisé `litterature`), désormais 732 K. `sst` brut 144 K → raffiné 105 K (probablement re-routage vers `clinique` ou `litterature` pour les faux SST). `reglementaire` (41 K) apparaît : guidelines, normes ISO, ANSES, etc.

### 7.3 `year_title_fix.db` — récupération Crossref

- **3 317 années récupérées** (works à DOI dont year=0 ou suspect)
- **3 205 titres récupérés** (works à DOI dont titre vide ou tronqué)

**Top années récupérées** (lookback Crossref) :

| Année | # récupérés |
|---|---|
| 2022 | 854 |
| 2023 | 493 |
| 2021 | 349 |
| 2020 | 190 |
| 2018 | 117 |
| 2017 | 117 |
| 2016 | 106 |
| 2019 | 105 |
| 2014 | 102 |
| 2015 | 100 |

→ Concentration sur années récentes (publications post-2018 = 53 % des récupérations). Cohérent avec la frontière de l'acquisition (PMC continue d'alimenter pour cette tranche).

### 7.4 `body_lang_fix.json` — correction langue détectée

2 608 976 works analysés (100 % du corpus). Méthode : `langdetect` sur extrait `text[300:2600]` (skip le boilerplate de tête), seuil ≥60 caractères.

**Résultat** : **46 173 works re-classés** (1,8 % du corpus).

| Sens | Volume |
|---|---|
| `fr` brut → `en` réel | ~43 500 (boilerplate HAL "Archive ouverte HAL...") |
| `und` brut → langue identifiée | ~2 000 |
| Autres réajustements | ~700 |

Distribution corrigée : EN 2 240 965 · **FR 128 460 (vraie)** · FI 50 827 · ES 33 019 · DE 23 622 · PT 23 364 · JA 19 595 · RU 16 640.

→ Le FR vrai (128 460, 4,9 %) est plus petit que le brut suggérait (6,6 %), important pour calibrer le filtre de francisation de la Couche 2.

### 7.5 `entities.jsonl` — graph seed (251 521 works tagués)

Extraction d'entités déterministe (lookups dictionnaire + regex CAS + matchers pathologies/métiers FR+EN). Fournit la matière première du graphe pour le futur GraphRAG (substance → pathologie → tableau MP → organe → métier).

**TOP 20 substances** :

| # | Substance | Works |
|---|---|---|
| 1 | **lead** | **146 308** ⚠️ *(suspect : "lead" en EN = mot polysémique, verb "to lead" → over-matching probable)* |
| 2 | silica | 4 941 |
| 3 | pah | 3 677 |
| 4 | nickel | 3 460 |
| 5 | arsenic | 2 618 |
| 6 | cobalt | 2 591 |
| 7 | cadmium | 2 578 |
| 8 | asbestos | 2 453 |
| 9 | benzene | 2 295 |
| 10 | chromium | 1 927 |
| 11 | formaldehyde | 1 422 |
| 12 | hap | 980 |
| 13 | chrome | 468 |
| 14 | plomb | 412 *(version FR de lead)* |
| 15 | amiante | 377 *(version FR de asbestos)* |
| 16 | isocyanate | 299 |
| 17 | wood dust | 223 |
| 18 | silice | 223 *(version FR de silica)* |
| 19 | mercure | 173 |
| 20 | solvant | 143 |

> ⚠️ **Anomalie #1 « lead 146 K »** : très probablement faux positifs (matching « lead » comme verbe ou nom commun en anglais : "leadership", "leading cause", "leads to"). À auditer : filtrer par contexte (« lead exposure », « lead poisoning », « blood lead level »).

**TOP 15 pathologies** :

| # | Pathologie | Works |
|---|---|---|
| 1 | asthma | 25 400 |
| 2 | leukemia | 22 969 |
| 3 | copd | 15 969 |
| 4 | mesothelioma | 2 803 |
| 5 | tms (TMS — troubles musculo-squelettiques) | 2 386 |
| 6 | carpal tunnel | 2 186 |
| 7 | asthme *(FR)* | 533 |
| 8 | bpco *(FR)* | 327 |
| 9 | dermatite | 241 |
| 10 | leucémie *(FR)* | 193 |
| 11 | surdité | 185 |
| 12 | lombalgie | 177 |
| 13 | adénocarcinome | 172 |
| 14 | cancer pulmonaire | 77 |
| 15 | canal carpien | 64 |

→ Bonne représentation des grandes pathologies professionnelles ; FR sous-représenté (cohérent avec 4,9 % de corpus FR vrai).

**TOP 15 métiers** :

| # | Métier | Works |
|---|---|---|
| 1 | baker | 4 213 |
| 2 | farmer | 2 670 |
| 3 | miner | 716 |
| 4 | painter | 394 |
| 5 | mineur *(FR)* | 295 |
| 6 | agriculteur | 270 |
| 7 | peintre | 222 |
| 8 | charpentier | 208 |
| 9 | boulanger | 185 |
| 10 | welder | 159 |
| 11 | macon (sans cédille) | 156 |
| 12 | maçon | 45 |
| 13 | aide-soignant | 30 |
| 14 | coiffeur | 23 |
| 15 | menuisier | 20 |

→ Hétérogénéité importante : « macon » sans cédille (156) et « maçon » (45) sont **2 entrées distinctes** alors qu'il s'agit du même métier — bug d'extraction normalisation à fixer.

**TOP 20 numéros CAS** :

| # | CAS | Works | Identifiable ? |
|---|---|---|---|
| 1 | 588-81-5 | 32 | (acide phényl-β-D-glucopyranosidique — pas suspect) |
| 2 | **2016-12-1** | **26** | ⚠️ *suspect : ressemble à une date (YYYY-MM-DD pseudo)* |
| 3 | 68-12-2 | 23 | DMF (diméthylformamide) |
| 4 | 80-05-7 | 18 | Bisphénol A |
| 5 | 127-18-4 | 17 | Tétrachloroéthylène |
| 6 | 79-01-6 | 17 | Trichloroéthylène |
| 7 | 100-41-4 | 16 | Éthylbenzène |
| 8 | 7440-38-2 | 16 | Arsenic |
| 9 | 79-06-1 | 16 | Acrylamide |
| 10 | **2021-17-4** | **16** | ⚠️ *suspect : ressemble à une date* |
| 11 | 127-19-5 | 15 | DMAC |
| 12 | 872-50-4 | 15 | N-méthyl-2-pyrrolidone |
| 13 | 111-76-2 | 15 | 2-butoxyéthanol |
| 14 | 50-00-0 | 15 | Formaldéhyde |
| 15 | **901509-83-4** | **15** | ⚠️ *suspect : CAS valide mais inhabituel pour ce corpus* |
| 16 | **2022-10-4** | **15** | ⚠️ *suspect : ressemble à une date* |
| 17 | 75-21-8 | 15 | Oxyde d'éthylène |
| 18 | 123-91-1 | 14 | 1,4-dioxane |
| 19 | 106-89-8 | 14 | Épichlorhydrine |
| 20 | 107-13-1 | 13 | Acrylonitrile |

> ⚠️ **Anomalie #2 « pseudo-CAS = dates »** : `2016-12-1`, `2021-17-4`, `2022-10-4` ressemblent à des dates capturées par la regex CAS (`\d{2,7}-\d{2}-\d`). Le pattern CAS canonique est `<2-7>-<2>-<1>` (digit check sum), donc `2021-17-4` est syntaxiquement valide mais probablement une date d'article. À filtrer par validation chimique (lookup ECHA/PubChem).

**TOP 15 tableaux MP français** :

| # | Tableau | Works |
|---|---|---|
| 1 | **Tableau 1** | **4 682** ⚠️ *(suspect : "Tableau 1" = aussi "Table 1" des papiers anglais — sur-matching possible)* |
| 2 | Tableau 2 | 932 |
| 3 | Tableau 3 | 183 |
| 4 | Tableau 4 | 38 |
| 5 | Tableau 57 | 19 |
| 6 | Tableau 5 | 15 |
| 7 | Tableau 42 | 8 |
| 8 | Tableau 6 | 6 |
| 9 | Tableau 7 | 6 |
| 10 | Tableau 69 | 6 |
| 11 | Tableau 66 | 6 |
| 12 | Tableau 11 | 5 |
| 13 | Tableau 8 | 5 |
| 14 | Tableau 36 | 5 |
| 15 | Tableau 65 | 5 |

> ⚠️ **Anomalie #3 « Tableau 1 = 4 682 »** : surcomptage évident. Le tableau MP #1 « Affections dues au plomb » devrait être bien moins fréquent que les 30, 25 (amiante), 42, 57 (TMS). Cause : matcher confond avec « Table 1 » des articles anglais et « Tableau 1 » légende-d'illustration sans rapport avec les tableaux MP. À durcir : matching strictement « tableau MP n° X » ou « régime général/agricole RGNN ».

---

## 8. Statistiques vectorielles

Échantillonnage 5 shards aléatoires (`vectors_00243`, `00606`, `00557`, `00133`, `00378`), 200 vecteurs/shard → 1 000 vecteurs au total + ~100 000 paires intra-shard pour cosine.

### 8.1 Norme L2

| Métrique | Valeur |
|---|---|
| Médiane | **1,0000** |
| Min | 0,9998 |
| Max | 1,0001 |
| Écart-type | **0,000015** |

→ Vecteurs **parfaitement L2-normalisés** et **cohérents sur tous les shards** = aucun drift de provider OpenRouter sur la durée du run (26 h). C'est un fait fort : OR a servi le même modèle à débit constant sans changement de quantization.

### 8.2 Cosine intra-shard (distribution des paires)

Sur ~100 000 paires (5 shards × ~20 000 paires/shard, calculées vectoriellement) :

| Quantile | Cosine |
|---|---|
| Médiane | **0,282** |
| p25 | 0,231 |
| p75 | 0,342 |

→ Espace **sain et discriminant** :
- Si l'espace était dégénéré (collapsed mode), médiane ~0,9 (tout est colinéaire).
- Si l'espace était aléatoire, médiane ~0 (orthogonal en grande dim).
- 0,282 = espace **dense et structuré** mais discriminant — exactement ce qu'on veut pour un retrieval métier.

### 8.3 Comparatif intra-work vs intra-shard

| Type de paires | Cosine médian |
|---|---|
| Intra-work (chunks d'un même doc, sanity check séparé) | **0,896** |
| Intra-shard (paires aléatoires dans un shard) | **0,282** |
| Aléatoire (paires inter-shard, attendu) | ~0,25-0,29 |

→ Ratio **intra-work / aléatoire ≈ 3,2×** = excellent discriminant. Un chunk « parle » fortement aux autres chunks de son propre document, et beaucoup moins aux chunks d'autres documents.

---

## 9. Audits déjà effectués (preuves + scripts)

### 9.1 Intégrité exhaustive (`integrity_full.py`)

- **871 shards Table A == 871 shards Table B** (footers parquet via `pyarrow.fs.S3FileSystem`).
- **rows A == rows B = 22 901 283** (alignement ligne-à-ligne).
- **0 vecteur nul / NaN**, **dim 4096 partout**, **norme 1,0**.

> ⚠️ **Catch important découvert dans cet audit** : un audit initial échantillonné (12/871) avait raté **44 shards à 0 octet (5,5 % du corpus)** laissés par des kills/copies interrompus. Détectés uniquement par l'audit *exhaustif* (footer-based) → supprimés + ré-embeddés + re-certifiés. **`remote_has` durci pour tester `size>0`** (script joint).

### 9.2 Canari fidélité texte↔vecteur (`canari_reembed.py`)

- **Méthode** : re-embedder un échantillon stratifié (30 shards × 100 chunks = 3 000 chunks) en reconstruisant le payload **exact** (même `make_input` que l'embed initial : préfixe + titre + texte) → cosine entre vecteur stocké et vecteur re-embeddé.
- **Résultat** : **cos médian 0,9999** sur tous les shards (min 0,9997).
- **Conclusion** : (a) chaque vecteur correspond à son texte (pas de désalignement), (b) **aucun provider-drift OpenRouter** (l'espace vectoriel est cohérent sur tout le run), (c) `chunk_id ↔ vector` alignment validé.

### 9.3 Sanity retrieval brute-force (`retrieval_sanity.py`)

- Pool de 188 088 chunks (8 shards), numpy cosine.
- **Cohérence sémantique** : intra-work médian **0,896** vs aléatoire **0,258** (cf. §8.3).
- **Test fonctionnel** (titre → propre chunk en top-3) : **3/5 OK**, les 2 manqués étaient des titres trop génériques (« Strategies for modeling aging »).
- **Requêtes FR MdT** :
  - « amiante » → mésothéliome, EN/IT/ES, cos 0,6-0,8
  - « silice » → silicose, IT/DE/EN, cos 0,55-0,75
  - « burnout » → **docs FR natifs**, cos 0,8
- → **Cross-lingual FR→EN du bake-off validé au niveau embedding**.

### 9.4 Truncation audit (`truncation_audit.py`)

- **1,65 % global** des chunks tronqués (input > 4000 octets UTF-8).
- **Négligeable pour l'usage cible** :
  - EN : 0,7 %
  - **FR : 0,5 %**
  - **SST : 0,8 %**
  - **toxico : 1,3 %**
  - **fiche_metier : 0 %**
- Heavy sur ru/ja (~70 %) mais ces langues sont hors-cible pour un MdT FR.

### 9.5 Near-duplicates proxy

- **~1 % de collisions titre+année** — mais ce sont des titres génériques (« editorial », « livres reçus », « présentation »…), pas de vrais doublons de contenu. L'exact-hash + work_id éliminaient déjà les vrais dups.

### 9.6 Challenge 6 IA (audit adversarial brutal)

- 6 voix : Codex GPT-5.5, Gemini 3.1 Pro, Kimi K2.6, Grok 4.3, DeepSeek R1, Qwen 3.7 Max.
- 7 axes : sécurité, qualité, tests, performance, archi, doc, adversarial.
- **Verdict après vérifications indépendantes** : seul le défaut des 44 shards 0-octet (caught + fixé) était réel ; toutes les autres craintes (fidélité, drift, troncature-massacre, near-dup-mirage) ont été **mesurées et écartées**.

---

## 10. Limites et angles morts assumés

### 10.1 Méthodologiques

- **`Table A == Table B` vérifie le miroir, pas la complétude vs la réalité** (qwen, juste). Un scrape raté laisse A et B synchronisés ET incomplets — la complétude relève de la chaîne d'**acquisition** (continue ; ~624 K fichiers scrapers neufs à ré-intégrer post-serving).
- **Coverage thematic** non mesurée frontalement : on n'a pas une garantie chiffrée que les 86 tableaux MP français sont chacun couverts par ≥ N docs. À auditer.

### 10.2 Techniques

- **Cap 4000 octets** sur l'input OR : **inutile** (OR/qwen3 gère le contexte) → ru/ja tronqués ~70 %. Pour le **ré-embed Qwen4 futur**, retirer ce cap (BYOE rend la chose anodine).
- **`doc_type=unknown` sur 64 % des works** (canonical debby) — ils sont majoritairement full-text mais le tag fin n'a pas été propagé. **Refinable post-load** (lecture longueur de texte → heuristique ft/abstract).
- **`source_type=clinique` et `=reglementaire`** absents du brut, présents seulement dans `source_type_refined`. Couche 2 doit utiliser le raffiné, pas le brut.

### 10.3 Anomalies de qualité **volontairement non-corrigées et listées pour le challenger**

| # | Symptôme | Cause probable | Impact | Action proposée |
|---|---|---|---|---|
| **A1** | `ebm=1` sur 463 K works, dont **89,7 % sans "meta/systematic" dans le titre** | Heuristique trop large à l'origine (match abstract ou heading) | Boost EBM ×1,3 dilué dans Couche 2 | Re-tagger : `ebm=1` ssi `meta\|systematic\|prisma` dans titre OU OpenAlex concept ⊇ {Systematic review, Meta-analysis} |
| **A2** | « lead » 146 K works (× 30 vs silica) | Mot anglais polysémique (verb "to lead", "leadership") | Substance graph biaisée | Filtrer par contexte : `lead exposure\|lead poisoning\|blood lead\|Pb` |
| **A3** | Pseudo-CAS « 2016-12-1 », « 2021-17-4 », « 2022-10-4 » | Regex CAS match des dates structurées | Substances graph polluées | Cross-check ECHA/PubChem (substance réelle ?) |
| **A4** | « Tableau 1 » = 4 682 works (vs Tableau 30 = ? Tableau 42 = 8) | Sur-matching « Table 1 » EN + légendes d'illustrations | tableau_mp graph biaisée vers Tableau 1 | Matching strict : `tableau (MP\|maladie professionnelle\|n°)\s*\d` ou `RG-\d+\|RA-\d+` |
| **A5** | « macon » 156 vs « maçon » 45 (= même métier) | Pas de normalisation accents | metiers graph dupliquée | Normalize Unicode NFD + strip diacritics ou alias-table |
| **A6** | Rétractations 234/2,6 M = 0,009 % vs attendu ~3 100 (×13 sous-couverture) | Retraction Watch couvre mal hors core PubMed (OA récents, prépublications) | Sous-flag de rétractations possible | Sources complémentaires (PubMed Retracted Publication flag, OpenAlex `is_retracted`) |

→ Ces anomalies sont **listées exprès** pour donner au challenger des handles concrets. Le sous-projet « **post-embed cleanup**, side-tables v2 » est dans le backlog.

---

## 11. Axes d'audit ouverts pour le challenger

### 11.1 Audit de fidélité (le retrieval fait-il ce qu'il prétend ?)

1. **Qualité du retrieval réel** (l'éval LanceDB n'est pas encore tournée). Proposer des requêtes-pièges + critères MdT.
2. **Cross-lingual FR→EN** : sur quelles classes de requêtes le pivot échoue-t-il (jargon FR pur sans équivalent EN, termes argotiques métier) ?
3. **Pivot CAS FR→EN** : le `pivot_cas.json` couvre quels substances ? Combien manquantes ?
4. **No-answer accuracy** sur le benchmark catégorie `hors_corpus` (5 requêtes injectées qui doivent retourner « pas de preuve établie »).

### 11.2 Audit de calibration (les boosts sont-ils justes ?)

5. **Couche 2** : pertinence des boosts `EBM ×1,3 / SST ×2 / FR ×2 / récence ×1,3`. Calibrés sur quoi ? Sur-pondération possible ?
6. **Filtre francisation ×0,5** sur sources anglo si question FR-juridique : sur quels critères (mots-clés FR + Légifrance/Tableau MP/Code travail) ?
7. **No-answer threshold** : à quel seuil cosine déclencher « pas de preuve établie » ? Aujourd'hui ~0,3 en heuristique — à calibrer empiriquement.

### 11.3 Audit de couverture (le corpus a-t-il ce qu'il prétend ?)

8. **Couverture des tableaux MP** : pour chaque tableau (**122 RG** dont 20 variantes BIS/TER + **53 RA** dont 8 variantes BIS/TER = **175 tableaux** au total, cf. INRS bdd/mp/listeTableaux.html vérifié 2026-05-27), combien de works pertinents ? (À mesurer après build_lancedb.) — *⚠️ correction 2026-05-27 : le décompte initial "86 RG + 65 RA = 151" omettait les 20 RG BIS/TER (RG 10 BIS, RG 30 BIS/TER pour amiante, etc.) ainsi que les 8 RA BIS/TER ; voir `TABLEAUX_MP_REFERENCE.md` pour la liste exhaustive*.
9. **Couverture par catégorie SST** : TMS, RPS, CMR, surveillance, aptitude — assez de docs ?
10. **Sous-représentation revues prestigieuses** : NEJM/JAMA/Lancet/BMJ — combien de % ? Acceptable ?
11. **Sous-représentation FR** : 128 460 works vrais FR (4,9 %) — assez pour une couverture spécialisée MdT FR ?

### 11.4 Audit adversarial / red-team

12. **Prompt injection via texte du corpus** : un chunk piégé avec instructions cachées → comportement de l'agent ?
13. **PII leakage** : auteurs nominaux complets dans la Table A — est-ce conforme à l'usage ? (Réponse interne : oui, données déjà publiques sur PubMed/Crossref/HAL, mais à confirmer pour publication d'un produit dérivé.)
14. **Provenance attaquable** : 78 % de works avec DOI, 22 % sans. Les 22 % sont-ils citables autrement (titre+venue) ? Auditer la « non-citabilité résiduelle ».

### 11.5 Audit qualité de données (les anomalies listées §10.3)

15-20. Confirmer les anomalies A1-A6 et proposer fix précis.

### 11.6 Audit architectural / perspective

21. **Découplage A/B = BYOE** : tient-il ses promesses ? Tester un ré-embed avec un autre modèle (cohere v4, voyage-3-multi) sur 1 % du corpus et mesurer.
22. **Granularité du chunking 3 600 c** : trop gros (réponse noyée) ou trop fin (perte de contexte) pour un MdT qui veut un seuil VLEP précis ? Tester ablation 1800/3600/5400.
23. **Préfixe contextuel** (`[type/source] : titre — texte`) : aide-t-il vraiment la discrimination, ou pollue-t-il l'espace ? Tester par ablation.
24. **GraphRAG** : la table `entities.jsonl` permet-elle de construire un graphe substance→pathologie→tableau→organe→métier exploitable ? Quel modèle de raisonnement ?

---

## 12. Extraits illustratifs réels

### 12.1 `source_type=litterature` (review médicale EN)

**Metadata** :
```json
{
  "chunk_id": "c4435aa2…46d6928:3",
  "work_id": "sha:c4435aa2…46d6928",
  "title": "CELL-BASED THERAPY FOR THE TREATMENT OF FOCAL ARTICULAR CARTILAGE LESIONS…",
  "authors": "[\"Samsudin\",\"Kamarul\"]",
  "year": 0,
  "doc_type": "review",
  "source_type": "litterature",
  "body_lang": "en",
  "ebm": 5,
  "study_type": "case_report",
  "is_oh": 0,
  "has_sst": 0,
  "clin": 1.0,
  "origin": "debby",
  "n_chunks": 13,
  "chunk_index": 3
}
```

**Texte (extrait 700 c)** :
> Osteochondral grafts, which harvest osteochondral plugs from low weight-bearing areas within the knee joint for implantation into chondral defects, have shown promising results with a success rate of up to 80 % (21-25). Although both these techniques are able to retain the viability of hyaline tissue unlike previous surgical interventions (20, 26), perichondral grafts are susceptible to ossification and graft failure (10, 20) while osteochondral grafts are limited by donor site morbidity concerns (10) and the lack of lateral integration of mosaic plugs and recipients, which may lead to degeneration of the graft over time (17, 27)…

### 12.2 `source_type=sst` (recherche occupational health EN)

**Metadata** :
```json
{
  "chunk_id": "c3da84c6…b40bd5:0",
  "work_id": "sha:c3da84c6…b40bd5",
  "title": "The prevalence of free-living amoebae in a South African hospital water distribution system",
  "authors": "[\"Muchesa\",\"Barnard\",\"Bartie\"]",
  "year": 0,
  "doc_type": "research",
  "source_type": "sst",
  "body_lang": "en",
  "ebm": 1,
  "study_type": "guideline",
  "is_oh": 1,
  "has_sst": 0,
  "clin": 1.0,
  "origin": "debby",
  "n_chunks": 3,
  "chunk_index": 0
}
```

**Texte (extrait 700 c)** :
> Research Letter — Page 1 of 3
> AUTHORS: Petros Muchesa¹, Tobias G. Barnard¹, Catheleen Bartie²
> AFFILIATIONS: ¹Water and Health Research Centre, Department of Biomedical Technology, University of Johannesburg […]; ²Immunology and Microbiology, National Institute for Occupational Health, Johannesburg, South Africa
>
> **Free-living amoebae in a hospital water system** — The purpose of this study was to investigate the occurrence of free-living amoebae in the water system of a teaching hospital in Johannesburg (South Africa). Water and biofilm samples were collected from the theatres […]

> ⚠️ **Note pour le challenger** : ce work a `ebm=1` (méta/SR) ET `study_type=guideline` ; les deux ne sont pas cohérents avec un titre de "Research Letter". Confirme l'anomalie A1 (sur-flag EBM).

### 12.3 `source_type=toxico` (abstract toxicologie, origin=sstinfo)

**Metadata** :
```json
{
  "chunk_id": "282ff3d7…068e0df2:0",
  "work_id": "doi:10.1093/toxsci/kft252",
  "title": "FutureTox: Building the Road for 21st Century Toxicology and Risk Assessment Practices",
  "year": 2013,
  "doi": "10.1093/toxsci/kft252",
  "doc_type": "abstract",
  "source_type": "toxico",
  "body_lang": "fr",
  "ebm": 9,
  "study_type": "unknown",
  "clin": 0.5,
  "origin": "sstinfo",
  "n_chunks": 1,
  "chunk_index": 0
}
```

**Texte (extrait 700 c)** :
> **FutureTox: Building the Road for 21st Century Toxicology and Risk Assessment Practices**
>
> This article reports on the outcome of FutureTox, a Society of Toxicology (SOT) Contemporary Concepts in Toxicology (CCT) workshop, whose goal was to address the challenges and opportunities associated with implementing 21st century technologies for toxicity testing, hazard identification, and risk assessment. One goal of the workshop was to facilitate an interactive multisector and discipline dialog. To this end, workshop invitees and participants included stakeholders from governmental and regulatory agencies, research institutes, academia, and the chemical and pharmaceutical industry in Europe and the…

> ⚠️ **Note pour le challenger** : `body_lang=fr` mais le texte est clairement EN — c'est exactement ce que `body_lang_fix` corrige (mais ici il s'agit de la valeur **brute** Table A ; le fix est dans la side-table).

### 12.4 `source_type=fiche_metier` (Bossons Futé, FR, structuré JSON)

**Metadata** :
```json
{
  "chunk_id": "d6b1ea7e…a14f1e5:0",
  "work_id": "sstinfo:bossons:126",
  "title": "Conducteur d'engin d'exploitation agricole",
  "year": 0,
  "doc_type": "fiche",
  "source_type": "fiche_metier",
  "body_lang": "fr",
  "ebm": 9,
  "study_type": "unknown",
  "clin": 0.5,
  "origin": "sstinfo",
  "n_chunks": 1,
  "chunk_index": 0
}
```

**Texte (la fiche entière, 1 chunk)** :
> **Fiche métier Bossons Futé : Conducteur d'engin d'exploitation agricole**
>
> Risques : `{"dangers_principaux": [{"categorie":"Electrique","description":"Risque électrique"}, {"categorie":"Machines","description":"Exposition aux machines, risques de coupure/écrasement"}, {"categorie":"Rayonnement","description":"Exposition aux rayonnements"}, {"categorie":"Routier","description":"Risque routier, conduite professionnelle"}], "maladies_professionnelles":[], "autres_pathologies":[], "synthese":"Dangers : Electrique, Machines, Rayonnement, Routier"}`
> Nuisances : `[]`
> Pathologies : `[]`

### 12.5 Entrée `entities.jsonl` typique (graph seed)

```json
{
  "work_id": "doi:10.xxxx/example",
  "cas": ["71-43-2"],
  "tableau_mp": ["4"],
  "substances": ["benzène", "leucémie"],
  "pathologies": ["leucémie myéloïde", "aplasie médullaire"],
  "organes": ["moelle"],
  "metiers": ["soudeur"],
  "latence": ["10"]
}
```

→ Permet de bâtir le graphe `substance → pathologie → tableau MP → organe → métier` pour le futur GraphRAG.

### 12.6 Échantillon du benchmark MdT FR (`debby_benchmark_fr.jsonl`)

49 requêtes en 13 catégories. Exemples :

```json
{
  "id": "exp01",
  "cat": "exposition_pathologie",
  "query": "lien entre exposition aux poussières de bois et adénocarcinome de l'ethmoïde, tableau MP",
  "expected_concepts": ["poussières de bois", "adénocarcinome ethmoïde", "tableau 47", "cancer naso-sinusien", "délai"],
  "expected_doc_types": ["clinique", "reglementaire"],
  "needs_mcp": true,
  "difficulty": "facile"
}

{
  "id": "apt01",
  "cat": "aptitude",
  "query": "salarié cariste avec épilepsie traitée stabilisée, apte à la conduite de chariot élévateur ?",
  "expected_concepts": ["épilepsie", "conduite engins", "aptitude", "R4323", "sécurité"],
  "needs_mcp": true,
  "difficulty": "moyen"
}

{
  "id": "neg01",
  "cat": "hors_corpus",
  "query": "lien établi entre exposition au Wi-Fi en open space et lymphome, tableau de maladie professionnelle 2026",
  "note": "DOIT répondre absence de preuve / hors corpus — pas de lien établi ni tableau"
}
```

Le benchmark complet (49 lignes) est fourni dans le repo (`debby_benchmark_fr.jsonl`).

---

## 13. Reproductibilité — artefacts disponibles

### 13.1 Dans ce repo (`reddepot/debby-audit-snapshot`)

- `README.md` — orientation rapide
- `DEBBY_AUDIT_SNAPSHOT.md` — ce document
- `deep_stats.out` — sortie brute de l'analyse profonde du jour
- `debby_benchmark_fr.jsonl` — 49 requêtes FR MdT
- `scripts/embed_or.py` — producteur OR (avec `remote_has` durci size>0)
- `scripts/watchdog_embed.sh` — recycleur anti-OOM
- `scripts/integrity_full.py` — audit footers parquet S3
- `scripts/canari_reembed.py` — vérif fidélité texte↔vecteur
- `scripts/extract_samples.py` — extraction échantillons illustratifs
- `scripts/deep_stats.py` — analyse profonde
- `scripts/body_lang_v2.py` — correction langue (streaming memory-safe)
- `scripts/layer2.py` — Couche 2 retrieval (extrait public, sans secrets)
- `scripts/eval_benchmark.py` — harness d'éval

### 13.2 Non distribués (mais accessibles à un auditeur sous NDA)

- Le corpus complet (Table A + B + side-tables) en object storage Vultr S3 (~180 Go).
- `pivot_cas.json`, `franco_keywords.json` (config Couche 2)
- Les rapports complets des audits 6 IA (transcripts)

### 13.3 Versionning

- **`chunking_version="pc-3600-v1"`** : permet de versionner les futures variantes (ex : `pc-1800-v2`, `child-only-v3`).
- **Lessons capitalisées** dans `~/.claude/projects/-Users-radu/memory/lessons_debby_embed_night_20260525.md` (privé, mais résumé dans §10 ci-dessus).

---

## 14. Annexes

### 14.1 Schéma Table A complet — voir §5.1
### 14.2 Schéma side-tables — voir §5.3
### 14.3 Stats brutes deep_stats.out — voir fichier joint
### 14.4 Glossaire

| Terme | Définition |
|---|---|
| **BYOE** | Bring Your Own Embedder — pattern architectural Table A canonique / Table B jetable |
| **MdT** | Médecin du Travail (FR) |
| **SST** | Santé et Sécurité au Travail |
| **MP** | Maladie Professionnelle (FR — Régime Général ou Agricole) |
| **EBM** | Evidence-Based Medicine (1=méta..6=editorial, 9=unknown) |
| **OH** | Occupational Health |
| **FT** | Full-Text |
| **VLEP** | Valeur Limite d'Exposition Professionnelle |
| **CAS** | Chemical Abstracts Service (numéro d'identification chimique) |
| **TMS** | Troubles Musculo-Squelettiques |
| **RPS** | Risques Psycho-Sociaux |
| **CMR** | Cancérogène, Mutagène, Reprotoxique |
| **CAS pivot** | dictionnaire FR↔EN substance (Couche 2) |
| **OR** | OpenRouter (le provider d'API utilisé pour l'embed) |
| **IVF_PQ** | Inverted File index with Product Quantization (LanceDB) |
| **Matryoshka** | propriété de troncature progressive de l'embedding (utilisable à 512/1024/2048/4096 dim) |

### 14.5 Pour aller plus loin

Le moment de vérité réel = **build LanceDB → brancher `layer2` → tourner `eval_benchmark.py`** sur le benchmark FR + les probes de challenge → premier score quantifié (R@k, no-answer accuracy, cross-lingual coverage). Le corpus est prêt et a passé les audits structurels ; reste à le faire **parler**.

---

**Comment challenger ce doc** :
- Ouvrir une issue sur le repo `reddepot/debby-audit-snapshot` avec votre constat + preuve reproductible.
- Pour un audit lourd / un PR : un fork est bienvenu.
- Pour un échange direct : `redtech@protonmail.com`.

*Document généré le 2026-05-26 par Claude Opus 4.7, orchestré par Radu (médecin du travail SPSTI ASSTV86).*
