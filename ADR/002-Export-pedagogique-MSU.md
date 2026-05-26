# ADR-002 — Export pédagogique KG → supports formation + intégration kit MSU DES MST 2026

> **Statut** : Accepted  
> **Date** : 2026-05-27  
> **Auteur** : Claude Opus 4.7 (orchestrateur nuit 26-27/05) + cap stratégique @reddepot  
> **Issue** : [#1 Phase 1 RECTIFIED](https://github.com/reddepot/debby-audit-snapshot/issues/1)  
> **Dépend de** : ADR-001 (GraphRAG Kuzu)

## Contexte

Le KG (chef d'œuvre cible — cf. ADR-001) n'a de valeur que s'il alimente des **supports pédagogiques tangibles** pour la formation des MdT et internes DES MST. @reddepot a déjà livré un **kit MSU DES MST 2026** (59 fichiers, livraison 29/04, cf. memory `[[project_msu_interne_2026]]`) qui peut être :
- enrichi à partir du KG (sources actualisées, sources rétractées exclues, ontologies normalisées),
- versionné en sync avec le KG (un commit du KG → régénération du kit),
- étendu (fiches métier dynamiques, mind maps, quiz auto-générés).

## Décision

Adopter un **pipeline d'export du KG vers 4 formats pédagogiques cibles**, avec point d'entrée commun (une requête Cypher Kuzu) et points de sortie spécialisés selon l'usage :

### Format 1 — **Fiche métier dynamique Markdown + Mermaid** (priorité P0)

- **Cible** : intégrable directement dans Obsidian, GitHub, Gitea du NAS, le kit MSU.
- **Contenu** : titre + résumé + graphe Mermaid (substance → tableau → pathologie → surveillance) + liste sources avec niveaux de preuve + horodatage versioning V.7
- **Pipeline** : Cypher query → template Jinja2 → Markdown final
- **Cas d'usage** : un interne DES MST clique sur "fiche métier soudeur" et obtient en 1 page : agents causaux (Pb, Cr, Ni, fumées), tableaux MP applicables (RG 1, RG 10 BIS, RG 70 BIS, RG 4 BIS hémopathies benzène si soudage à l'arc avec dégraissants), surveillance (audiogramme, spirométrie, dosages biologiques), délais PEC, sources INRS/HAS récentes (boost temporel I.7)

### Format 2 — **Slides Gamma** (priorité P1)

- **Cible** : présentations pour cours DES MST, formations continues SPSTI, MSU
- **Pipeline** : KG → narration Markdown structurée → MCP `mcp__claude_ai_Gamma__generate` (déjà connecté chez @reddepot)
- **Cas d'usage** : générer en 1 commande un deck "Amiante : 1 substance → 6 tableaux MP → suivi 2024" prêt à présenter
- **Avantage** : Gamma a templates pédagogiques + visuels automatiques

### Format 3 — **Mind map interactive GraphML / Mermaid / Markmap** (priorité P1)

- **Cible** : exploration visuelle, supports de révision
- **Pipeline** : Cypher query subgraph → GraphML export → conversion Markmap (https://markmap.js.org/) ou D3.js
- **Cas d'usage** : un interne explore visuellement "substance amiante" → graphe interactif avec zoom sur tableaux, surveillance, métiers, latence

### Format 4 — **Quiz auto-généré JSON** (priorité P2)

- **Cible** : auto-évaluation interne DES MST, formation continue
- **Pipeline** : Cypher query → template question/réponse → JSON Quiz format (compatible Moodle, AnkiConnect, Kahoot)
- **Cas d'usage** : "Quel est le tableau MP pour mésothéliome amiante ? → RG 30 TER (réponse + sources + lien fiche détaillée)"

## Intégration kit MSU DES MST 2026

| Type de fichier kit existant | Lien KG |
|---|---|
| Fiches métier (existant ?) | Régénération automatique depuis KG |
| Fiches pathologie | Régénération automatique |
| Quizs internes | Auto-génération format 4 |
| Slides cours | Auto-génération format 2 (Gamma) |
| Glossaire SST | Extrait du KG (nœuds Substance + Pathologie + Métier) |

### Modèle de gouvernance

- **Source de vérité** : le KG Kuzu (versionné V.7)
- **Kit MSU** : artefact dérivé, régénéré à chaque bump `kg_version`
- **Permissions** : @reddepot pousse au KG, kit MSU régénéré par job CI
- **Validation pédagogique** : @reddepot + 1-2 collègues MdT formateurs valident le kit avant publication interne

## Alternatives évaluées et rejetées

| Alternative | Pourquoi rejetée |
|---|---|
| Génération directe LLM sans KG | Hallucinations + non-reproductible + pas de traçabilité sources |
| Pure base de données relationnelle | Pas de multi-hop natif, queries lourdes |
| Site web statique généré (Jekyll/Hugo) | Trop figé, pas de navigation graphique |
| Notion / Coda | Lock-in vendeur, pas de versioning git |

## Conséquences

### Positives
- **Réutilisation maximale** : un seul KG alimente 4 formats pédagogiques + le kit MSU existant
- **Versioning cohérent** : chaque update du KG (V.7) régénère les supports → pas de dérive
- **Opposabilité pédagogique** : chaque support cite ses sources avec niveau de preuve (transparence formation)
- **Auto-évolution** : ajout d'une substance dans le KG → fiche métier mise à jour automatiquement

### Négatives / risques
- **Maintenance pipeline** : 4 formats × KG = surface de bug. Mitigation : tests d'intégration CI à chaque bump KG.
- **Qualité variable des templates** : un template Gamma médiocre = supports médiocres. Mitigation : itération avec @reddepot + 1-2 formateurs MdT comme validateurs humains.

## Plan d'implémentation (post-ADR-001)

### Sprint 1 (nuit 26-27/05)
- ✅ ADR-001 GraphRAG Kuzu
- ✅ ADR-002 Export pédagogique (ce document)
- 🔨 Prototype Kuzu 10 substances pilotes
- 🔨 Format 1 (fiche métier Markdown + Mermaid) : 1 fiche pilote "amiante" depuis KG

### Sprint 2 (jours 1-7 après cap)
- Format 2 (Gamma slides) : 1 deck pilote "amiante" depuis KG via MCP Gamma
- Format 3 (Markmap) : 1 mind map pilote
- Inventaire kit MSU existant et identification des fichiers régénérables

### Sprint 3 (jours 7-21)
- Format 4 (Quiz) : prototype Anki / Moodle
- Pipeline régénération kit MSU complet depuis KG
- Validation @reddepot + 1-2 formateurs

## Go/No-Go

| Critère | Cible Sprint 1 |
|---|---|
| 1 fiche métier "amiante" générée depuis KG (Format 1) | ≥ 80 % contenu valide selon @reddepot |
| Mermaid affichable dans Obsidian/GitHub | ✅ |
| Sources citées avec niveau preuve | ✅ |
| Versioning V.7 présent | ✅ |

## Liens

- ADR-001 GraphRAG Kuzu
- Issue [#1 Phase 1 RECTIFIED](https://github.com/reddepot/debby-audit-snapshot/issues/1)
- Memory : `[[project_msu_interne_2026]]` (kit existant 59 fichiers)
- Memory : `[[user_medical_practice]]` (MdT SPSTI ASSTV86)
- MCP Gamma : `mcp__claude_ai_Gamma__generate` (déjà connecté)
- Markmap : https://markmap.js.org/
