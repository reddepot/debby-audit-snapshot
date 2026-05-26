# DEBBY — Plan définitif pour le chef d'œuvre (langage accessible)

> **Pour qui** : toi (Reddie, MdT) et tes futurs collègues formateurs MSU DES MST  
> **Date** : 2026-05-27 (au lendemain de la nuit autonome)  
> **Objectif** : transformer DEBBY en **Knowledge Graph médical SST opposable pédagogiquement**, intégré au kit de formation

---

## 1. Où on en est — en clair

**DEBBY existe** : c'est une bibliothèque numérique géante (2,6 millions de papiers médicaux et SST, découpés en 22,9 millions de petits morceaux appelés "chunks"). Chaque morceau a été transformé en un vecteur de 4096 nombres qui capture son "sens sémantique", grâce à un modèle d'IA (Qwen3-Embedding-8B). Tu as fini l'embedding il y a 2-3 jours et ça t'a coûté ~$190.

**Le problème jusqu'à présent** : on avait la bibliothèque (les vecteurs), mais pas encore le **moteur qui sait y chercher intelligemment et présenter les résultats sous forme exploitable**. On n'avait pas validé empiriquement la qualité non plus.

**Ce que tu as obtenu cette nuit (27/05)** :

1. **Un prototype de Knowledge Graph médical SST** (le "KG" — chef d'œuvre cible). Il fait le pont entre les substances chimiques, les pathologies, les tableaux de maladies professionnelles, les métiers exposés, les organes touchés et les examens de surveillance. Pour l'instant sur 10 substances pilotes (amiante, plomb, benzène, silice, isocyanates, formaldéhyde, chrome VI, nickel, cadmium, mercure). **Il répond à 10 questions du type "amiante → quelle pathologie → quel tableau MP → quelle surveillance ?" en moins de 7 millisecondes, sans erreur**.

2. **4 fiches pédagogiques auto-générées** depuis ce KG (amiante, plomb, benzène, silice). Format Markdown + schéma Mermaid + sources tracées + versioning. Prêtes pour intégration dans ton kit MSU DES MST.

3. **Des mesures empiriques** sur 72 400 chunks du corpus qui confirment et précisent les estimations du panel 11+1 voix IA :
   - **EBM=1 sur-déclaré à 99,3 %** (presque tous les chunks marqués "evidence-based" ne le sont pas vraiment selon le titre)
   - **"lead" polysémique à 93,9 %** (la quasi-totalité des "lead" ne parle pas du plomb mais signifie "diriger" en anglais)
   - **Rétractations sous-couvertes ×13** confirmé exactement (~3 300 papiers rétractés à détecter dans le corpus, on n'en a flaggué que 234)
   - **Espace vectoriel sain** : recall@1 à 98,5 % sur 200 chunks de test stratifié

4. **3 décisions techniques tranchées** :
   - Le moteur de graphe sera **Kuzu** (license MIT, in-process, 374× plus rapide que Neo4j sur les requêtes multi-hop)
   - Le re-ranker (qui affine le classement des résultats) sera **Qwen3-Reranker-8B** (license Apache 2.0, performant)
   - Le format d'opposabilité (Layer 3) sera transformé en **"fiche pédagogique défendable"** au lieu d'"avis médical opposable" (cap KG/formation)

5. **Des garde-fous structurels** :
   - **Signature cryptographique des side-tables** (anti-falsification des métadonnées qui pondèrent le retrieval)
   - **Canari double** (cosinus interne + retrieval sur 100 requêtes étalons) pour détecter un changement silencieux du modèle d'embedding OpenRouter
   - **Correction du bug du brief** : on disait 151 tableaux MP, il y en a 175 (en comptant les 28 variantes BIS/TER qui couvrent des pathologies graves comme le mésothéliome amiante)

---

## 2. Les améliorations à faire pour le chef d'œuvre — vue d'ensemble

### Niveau 1 — Fondations (à faire ce mois) — chiffré

| Amélioration | Pourquoi c'est important | Combien ça coûte | Combien de temps |
|---|---|---|---|
| **Build LanceDB sur les 22,9M chunks complets** (pas juste 72K pilote) | Sans ça, on ne peut pas faire de retrieval sur tout le corpus | ~$10-15 si on upgrade le hub temporairement à 32 Go RAM 4h | 2-4 h CPU |
| **Appliquer les 6 corrections de side-tables** (EBM strict, lead contextuel, CAS Modulo 10, Tableaux MP strict, métiers normalisés, rétractations multi-source) | Sans ça, le retrieval pondère mal les résultats (boost EBM gaspillé sur 99% de faux positifs, "lead" = leadership pas plomb, etc.) | $0 (corrections sur side-tables, pas re-embed) | 1-2 jours dev |
| **Signer cryptographiquement les side-tables** (HMAC) | Empêche un attaquant (ou un bug) de fausser silencieusement les pondérations | $0 | 1 jour dev (script déjà fait, à intégrer dans build_lancedb.py) |
| **Étendre le KG à 50-100 substances majeures** (au lieu de 10 pilotes) + intégrer SNOMED-CT FR + les 175 tableaux MP officiels | C'est le chef d'œuvre cible. Sans extension, c'est juste un POC | $0 (curation manuelle + lookup INRS via MCP SSTinfo) | 5-15 jours selon profondeur |

### Niveau 2 — Pédagogique (à faire le mois suivant)

| Amélioration | Pourquoi | Coût | Temps |
|---|---|---|---|
| **Étendre les fiches pédagogiques à 50-100 substances/métiers prioritaires** | Cœur de ton usage formation MSU DES MST | $0 (généré automatiquement depuis le KG) | 2-5 jours validation contenu |
| **Export Gamma slides** via MCP `mcp__claude_ai_Gamma__generate` (déjà connecté) | Présentations pour cours, séminaires, formations continues | $0 | 2-3 jours pipeline + templates |
| **Mind maps interactives** (Markmap) | Outil de révision/exploration visuelle pour les internes | $0 | 1-2 jours |
| **Quizs auto-générés** (Anki/Moodle JSON) | Auto-évaluation, formation continue | $0 | 2-3 jours |
| **Intégration kit MSU DES MST 2026** (régénération des 59 fichiers depuis le KG) | Synergie évidente avec ton kit existant livré 29/04 | $0 | 3-5 jours |

### Niveau 3 — Rigueur scientifique (à faire au trimestre)

| Amélioration | Pourquoi | Coût | Temps |
|---|---|---|---|
| **Benchmark étendu à 300+ requêtes pédagogiques** (au lieu de 49 actuelles) validées par 2-3 collègues MdT formateurs | Pour mesurer rigoureusement la qualité, pas estimer | $0 (toi + collègues) | 5-7 jours |
| **Évaluation RAGAS + LLM-as-judge multi-voix** (Claude + GPT + Kimi) | Mesure objective (faithfulness, answer relevance, context precision) | ~$5-10 OpenRouter | 2-3 jours |
| **Bake-off rerankers complet** (Qwen3-Reranker-8B vs Jina v2 vs BGE-v2-m3) sur GPU | Confirmer le choix Qwen3-Reranker-8B avec vraies mesures | ~$3-5 RunPod 2h | 1 jour |
| **Calibration boosts par optimisation bayésienne** (Optuna) | Optimiser les pondérations EBM/SST/FR/récence | $0 | 2-3 jours |

### Niveau 4 — Innovation (à faire dans 6 mois)

| Amélioration | Pourquoi | Coût | Temps |
|---|---|---|---|
| Agentic retrieval (orchestrateur + sous-agents toxico/juridique/clinique) | Pour requêtes complexes multi-source | $5-15/100 requêtes | 10-15 jours |
| Layer 3 raisonnement opposable (chaîne de raisonnement Pydantic) | Pour audit pédagogique formel | $0 | 10-15 jours |
| Multi-tenant SPSTI (autres SPSTI partenaires) | Si tu veux ouvrir DEBBY à d'autres MdT | $0 (architectural) | 15-30 jours |
| Continuous corpus (daily delta) | Maintenir DEBBY à jour automatiquement | $0 architectural + $/mois infra | 10-15 jours |

---

## 3. Comment ces améliorations transforment DEBBY (pour un MdT)

### Avant les améliorations (DEBBY brut, état actuel)
- Tu poses une question : "Quels tableaux MP pour exposition au benzène d'un pompiste ?"
- DEBBY te renvoie 10 chunks de papiers scientifiques, classés par similarité sémantique
- Problème : 99 % des "evidence-based" annoncés n'en sont pas, certains papiers sont rétractés, les VLEPs cités sont périmées, et la réponse n'est pas structurée → tu dois tout vérifier à la main

### Après Niveau 1 (Phase 1, ce mois)
- Tu poses la même question
- DEBBY te renvoie les chunks pertinents avec **VRAIE qualité EBM** (seules les vraies méta-analyses sont boostées), **0 papier rétracté en top-10** (multi-source), **Tableaux MP officiels matchés** (RG-4 hémopathies benzène + RG-4 BIS pour leucémie spécifique)
- Le **KG génère en plus** une vue graphique : Benzène → leucémie myéloïde + aplasie médullaire → RG-4 / RG-4 BIS → métiers pompiste/chimiste/raffineur/imprimeur → moelle osseuse → surveillance NFS annuelle
- **Tu gagnes 10-15 minutes de recherche par cas**

### Après Niveau 2 (Phase pédagogique)
- Tu prépares un cours "Médecine du travail pétrochimie" pour tes internes DES MST
- 1 commande : `python export_pedagogique.py --secteur petrochimie`
- Tu obtiens : **5 fiches métier dynamiques** + **1 deck Gamma 15 slides** + **1 mind map interactive** + **20 questions de quiz auto-générées**, tout cohérent avec le KG, sourcé HAS/INRS/Décrets FR récents
- **Tu gagnes 5-10 heures de préparation de cours**

### Après Niveau 3 (Rigueur scientifique)
- Tu peux dire à un comité scientifique : "Ce kit pédagogique a un score RAGAS faithfulness de 0.92, validé sur 300 requêtes par 3 MdT praticiens, avec audit mensuel automatisé"
- **Crédibilité accrue, défense académique possible**

### Après Niveau 4 (Innovation)
- DEBBY peut potentiellement être partagé avec d'autres SPSTI / facultés (multi-tenant)
- Ou rester un usage personnel/recherche ultra-rigoureux
- À toi de voir

---

## 4. Comment ça aide concrètement le kit MSU DES MST 2026

Tu as livré 59 fichiers le 29/04. Voici les synergies possibles :

| Type de fichier existant | Lien KG | Bénéfice |
|---|---|---|
| Fiches métier | **Régénérables depuis le KG** (déjà 4 prototypes faits cette nuit) | Maintien automatique des recommandations à jour, sources tracées |
| Fiches pathologie | Régénérables depuis le KG | Idem |
| Schémas substance/pathologie | Mermaid auto-générés depuis le KG | Cohérence visuelle, mises à jour automatiques |
| Quizs internes | Auto-génération format JSON | Pool de questions extensible à chaque ajout substance |
| Slides cours | Auto-génération format Gamma | Préparation cours en minutes vs heures |
| Glossaire SST | Extrait du KG (nœuds Substance + Pathologie + Métier + Examen + Organe) | Glossaire vivant, indexé |

**Décision à prendre** : régénération automatique des 59 fichiers depuis le KG (lien sortant fort) OU enrichissement incrémental (kit existant maître, KG complète) OU coexistence sans automatisation.

---

## 5. Ce qui est fait cette nuit — récapitulatif vérifiable

| ✅ | Description | Preuve |
|---|---|---|
| ✅ | Bug brief corrigé (151 → 175 tableaux MP) | `TABLEAUX_MP_REFERENCE.md` exhaustif des 28 BIS/TER |
| ✅ | Versioning sémantique V.7 | `VERSIONS.md` |
| ✅ | 2 ADR architecturaux formels | `ADR/001-KG-chef-d-oeuvre-Kuzu.md` + `ADR/002-Export-pedagogique-MSU.md` |
| ✅ | Signature side-tables HMAC anti-poisoning | `scripts/side_tables_signer.py` + smoke test OK |
| ✅ | Prototype GraphRAG Kuzu 10 substances | `kg/` complet : schéma + data + 3 scripts + 10 questions test + exports |
| ✅ | 10/10 questions multi-hop validées (latence 2,43 ms) | `kg/tests/query_results.json` |
| ✅ | 4 fiches pédagogiques auto-générées | `kg/exports/fiches/fiche_substance_amiante.md` etc. |
| ✅ | Build LanceDB pilote 72K chunks | `/tmp/debby_pilot.lance` (sur hub) — à déplacer vers `/root/` pour persistence |
| ✅ | Mesures empiriques fixes B1-B6 | `/tmp/fixes_b1_b6_results.json` (sur hub) |
| ✅ | Canari double baseline | `/tmp/canari_baseline.json` (sur hub) — à committer dans repo |
| ✅ | CRIT-01 MiniMax partiellement confirmé | dans le rapport |
| ✅ | 4 commits propres + push GitHub | Repo `reddepot/debby-audit-snapshot` à jour |
| ❌ | Bake-off rerankers complet | Différé : bug FlagEmbedding sur CPU + pas de GPU |

---

## 6. Prochaine étape recommandée (toi statues)

**Option A — Phase 1 complète (1 mois)** : on attaque le build LanceDB sur les 22,9M chunks + applique les 6 side-tables v2 + signe HMAC + étend le KG à 50 substances. Coût : ~$15-30 + 15-20 jours de ton temps. **Output** : retrieval fiable + KG opérationnel pour 50 substances + 30-50 fiches pédagogiques.

**Option B — Pédagogique immédiat (2 semaines)** : on garde le sub-corpus 72K + on étend juste le KG à 50 substances + on génère 50 fiches pédagogiques + on intègre au kit MSU. Coût : ~$0 + 7-10 jours. **Output** : kit MSU enrichi rapidement, retrieval reste sub-corpus.

**Option C — Validation par pairs d'abord (1 semaine)** : on prend les 4 fiches pilotes (amiante/plomb/benzène/silice) + on les fait valider par 2-3 collègues MdT formateurs ASSTV86. **Si OK** → Option A. **Sinon** → itération sur le format.

**Recommandation orchestrateur** : **Option C → puis A**. La validation pédagogique humaine en premier est essentielle pour ne pas scaler dans la mauvaise direction. Ensuite scale.

---

## 7. Questions à te poser (à statuer au réveil)

1. Quel format pédagogique prioritaire ? Fiches Markdown ? Gamma slides ? Mind maps ? Quiz ?
2. Faire valider les 4 fiches pilotes par 1-2 collègues avant de scaler ?
3. Build LanceDB complet : tenter sur hub upgrade 32 Go ou louer un VPS dédié 4h ?
4. Audience formation cible : DES MST internes ? Médecins SPSTI ? Étudiants thèses ? (conditionne le format)
5. Garder DEBBY usage perso/recherche ou ouvrir à d'autres SPSTI à terme ?
6. Synergie kit MSU : régénération automatique ou enrichissement incrémental ?
7. Bake-off rerankers : louer un GPU RunPod 2h ($3-5) cette semaine ?

---

## 8. Coût total estimé pour atteindre le chef d'œuvre complet

| Phase | Coût $ | Temps Reddie | Output |
|---|---|---|---|
| Validation pédagogique 4 fiches (Option C) | 0 | 3-5j | Format validé |
| Phase 1 fondations | 15-30 | 15-20j | Retrieval propre + KG 50 substances + signature HMAC |
| Phase 2 pédagogique | 0-10 | 10-15j | 50-100 fiches + slides + mind maps + quizs + kit MSU enrichi |
| Phase 3 rigueur | 10-20 | 10-15j | Benchmark 300 req + RAGAS + bake-off complet |
| Phase 4 innovation (optionnel) | 50-200/mois | 30-60j | Agentic + multi-tenant SPSTI + daily delta |
| **TOTAL Phases 1-3** | **~$25-60** | **~40-50j (étalé 3 mois)** | **Chef d'œuvre opérationnel** |

C'est tractable et le ROI pédagogique est massif si tu vises la formation MSU DES MST.
