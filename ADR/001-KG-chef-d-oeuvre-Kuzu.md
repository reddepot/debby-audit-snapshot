# ADR-001 — GraphRAG Kuzu comme chef d'œuvre DEBBY

> **Statut** : Accepted  
> **Date** : 2026-05-27  
> **Auteur** : Claude Opus 4.7 (orchestrateur nuit 26-27/05) + panel 11+1 voix IA + cap stratégique @reddepot  
> **Supersede** : aucune ADR antérieure (premier formalisme architectural KG)  
> **Issue** : [#1 Phase 1 RECTIFIED](https://github.com/reddepot/debby-audit-snapshot/issues/1)

## Contexte

Information stratégique reçue de @reddepot fin de session 2026-05-26 :  
> *"Mon utilisation principale va être la réalisation du KG, possiblement destiné à la formation ; pas autant l'utilisation clinique directe."*

Cela renverse la priorisation issue de l'orchestration 11+1 voix IA (qui travaillait sur l'hypothèse "RAG opposable clinique"). Le **Knowledge Graph médical SST devient le chef d'œuvre cible**, pas une option P2 différée comme le proposait initialement GLM 5.1.

Le corpus DEBBY (2,6 M œuvres, 22,9 M chunks, qwen3-embedding-8b 4096-dim) avec ses side-tables d'enrichissement (notamment `entities.jsonl` — 251 521 works tagués avec extraction déterministe substance/CAS/pathologie/organe/métier/latence/tableau_mp) **est le matériau premium** pour construire le KG.

## Décision

**Adopter Kuzu** (https://kuzudb.com, license MIT, in-process embedded, columnar storage) comme moteur de GraphRAG pour DEBBY, avec **ontologies médicales formelles** intégrées (ICD-11, SNOMED-CT, MeSH, NAF, Tableaux MP 175).

### Schéma cible

```
(Substance) ─[CAUSE]─→ (Pathologie) ─[CLASSIFIÉE_DANS]─→ (Tableau_MP)
                            │                                 │
                            ├─[CONCERNE]─→ (Organe)            └─[CONCERNE]─→ (Metier)
                            │
                            └─[SURVEILLANCE]─→ (Examen) ─[PÉRIODICITÉ]─→ (Délai)

(Metier) ─[EXERCE]─→ (Salarié_anonyme — future V.3 conditionnel)

Annotations sur arêtes (pattern Gemini "chunks comme propriétés de preuve") :
- chunk_id pointers (vers Table A canonique, BYOE strict)
- niveau_preuve (EBM-1a à REG-FR)
- corpus_version + side_tables_version (versioning V.7)
```

### Alternatives évaluées et rejetées

| Moteur | Pourquoi rejeté |
|---|---|
| **Neo4j Community** | OPS lourd (serveur dédié), licence GPL v3 contraignante en commercial, latence path query 374× plus lente que Kuzu (cf. benchmark Vela Partners cité par Perplexity DR) |
| **Neo4j Aura cloud** | Coût récurrent, lock-in vendeur, exclu par souveraineté |
| **NetworkX in-memory pur** | Acceptable pour PoC ≤ 10 substances, mais non scalable à 175 tableaux MP × 1000+ substances + millions d'arêtes Crossref ; pas de query language déclaratif (Cypher) |
| **ArcadeDB embedded** | Solide mais communauté plus petite que Kuzu, moins de docs Python |
| **TigerGraph / JanusGraph** | OPS lourds, sur-dimensionnés pour DEBBY (1M-10M nœuds projetés, pas milliard) |
| **Apache AGE (PostgreSQL)** | Couplage Postgres lourd, performance path queries inférieure |

### Justifications principales Kuzu

1. **Performance** : Kuzu est 374× plus rapide que Neo4j sur les path queries (référence cross-validée Perplexity DR + DeepSeek + Gemini + Qwen + Antigravity dans le panel nuit 26/05).
2. **Architecture embedded** : pas de serveur à maintenir, fichier `.kuzu` portable, compatible BYOE (le graphe = side-table relationnelle, pas modification de Table A/B).
3. **Cypher-compatible** : permet des requêtes multi-hop naturelles (`MATCH (s:Substance {nom:'amiante'})-[:CAUSE]->(p:Pathologie)-[:CLASSIFIÉE_DANS]->(t:Tableau_MP) RETURN p, t`).
4. **License MIT** : pas de friction commerciale future.
5. **Python natif** : intégration directe avec le pipeline DEBBY existant.
6. **Storage columnar Parquet** : compatible avec l'écosystème Parquet déjà utilisé (Table A en parquet zstd).

## Conséquences

### Positives
- **KG chef d'œuvre** : DEBBY devient un graphe médical SST navigable, base de tous les supports pédagogiques futurs (mind maps, slides, fiches métier dynamiques)
- **Multi-hop natif** : questions du type "amiante → quelle pathologie + quel tableau + quelle surveillance + quel délai PEC ?" résolues en une seule requête Cypher
- **BYOE préservé** : Table A et Table B ne sont pas touchées ; le KG est une side-table relationnelle qui pointe vers `chunk_id`
- **Pas d'OPS** : un fichier `.kuzu`, gestion versionable par git (avec versioning V.7)
- **Latence acceptable** : <500ms pour path queries 3-hop selon docs Kuzu

### Négatives / risques
- **Dette ontologique** : intégrer ICD-11/SNOMED-CT/MeSH/NAF/Tableaux MP demande de la curation manuelle initiale (estimation : 5-10 jours pour les 10 substances pilotes, 30-60 jours pour le scale complet)
- **Hallucinations multi-hop si retrieval pollué** : risque pointé par GLM 5.1 (rétrogradation P2 initiale) — mitigé par garde-fou strict 10 substances avant scale + chunks-propriétés-preuve (pattern Gemini)
- **Maintenance ontologies** : ICD-11 évolue, Tableaux MP français peuvent être modifiés par décret (cf. I.7 Temporal Validity GLM 5.1) — nécessite job de mise à jour mensuel

### Mitigations
1. **PoC strict 10 substances pilotes** avant scale (amiante, plomb, benzène, silice, isocyanates, formaldéhyde, chrome, nickel, cadmium, mercure)
2. **10 questions multi-hop test** comme gate Go/No-Go avant extension (cf. ADR-001 Antigravity + Kimi)
3. **Pattern Gemini** : chunks LanceDB = annotations d'arêtes déterministes (pas extraction LLM bruitée). Le graphe est construit à partir de **référentiels normalisés** (INRS, Tableaux MP 175, ECHA, GESTIS), pas par extraction LLM ouverte.
4. **Versioning sémantique** (V.7) : chaque évolution du KG est versionnée (`kuzu-10sub-v0.1` → `kuzu-fullont-v1.0`)
5. **Job cron mensuel** : vérification consistance ontologies (INRS RSS pour Tableaux MP, WHO API pour ICD-11)

## Go/No-Go Phase 1 (10 substances pilotes)

| Critère | Cible |
|---|---|
| Schéma Kuzu créé et peuplé pour 10 substances | ✅ |
| Extraction triplets depuis entities.jsonl + INRS Tableaux MP 175 | ≥ 200 triplets validés |
| 10 questions multi-hop test (3-hop minimum) | ≥ 7/10 réponses correctes |
| Latence requête multi-hop | < 500 ms p95 |
| Export GraphML + Mermaid pour visualisation | ✅ |
| Tests reproductibles (3 runs, σ < 0.05) | ✅ |

**Si critères atteints** → étendre vers les 1000+ substances connues, intégrer SNOMED-CT FR complet, brancher MCP SSTinfo `lookup_tableau_mp` pour validation continue.

**Si critères non atteints** → revenir à l'option NetworkX in-memory (frugal GLM 5.1) et restreindre la couverture KG à 50 substances majeures.

## Dépendances

- ✅ Side-tables v2 (chantiers I.1-I.6) — calibration qualité avant ingestion KG
- ✅ X.1 Side-Table Hardening (signature HMAC) — sécurité side-tables avant manipulation
- ✅ TABLEAUX_MP_REFERENCE.md (175 tableaux INRS) — base ontologique Tableau_MP
- 🔨 entities.jsonl (251K works tagués) — déjà existant
- 🔨 Ontologies externes : ICD-11 (WHO API), SNOMED-CT FR (LeRedouté ?), MeSH (Entrez), NAF (INSEE)

## Liens

- Issue tracker : [#1 Phase 1 RECTIFIED](https://github.com/reddepot/debby-audit-snapshot/issues/1)
- Référence : `~/Downloads/SYNTHESE_DEBBY_20260526/CHANGEMENT_DE_CAP_KG_FORMATION.md`
- Convergence panel : Kimi K2.6 + DeepSeek + Gemini 3.1 Pro + Qwen 3.7 + Antigravity + Perplexity DR (6/12 voix Kuzu, dissensus restant accepté avec mitigation)
- Memory : `[[lessons_orchestration_11_voix_debby_20260526]]`
