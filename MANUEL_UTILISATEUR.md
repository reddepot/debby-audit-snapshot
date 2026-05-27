# DEBBY — Manuel utilisateur

> Guide d'usage pour **médecins du travail formateurs** et **internes DES MST**.
> Pas besoin d'être développeur. Le manuel explique chaque commande à copier-coller.
>
> Version : 2026-05-27 — KG `kuzu-50sub-v0.2`
> Contact : redtech@protonmail.com

---

## Sommaire

1. [Qu'est-ce que DEBBY ?](#1-quest-ce-que-debby-)
2. [À quoi ça sert pour ma pratique MdT / formation ?](#2-à-quoi-ça-sert-pour-ma-pratique-mdt--formation-)
3. [Comment naviguer dans les fiches pédagogiques](#3-comment-naviguer-dans-les-fiches-pédagogiques)
4. [Comment générer une nouvelle fiche substance](#4-comment-générer-une-nouvelle-fiche-substance)
5. [Comment ajouter une nouvelle substance au KG](#5-comment-ajouter-une-nouvelle-substance-au-kg)
6. [Comment cross-valider une fiche via MCP SSTinfo](#6-comment-cross-valider-une-fiche-via-mcp-sstinfo)
7. [Comment exporter pour différents formats (Markdown / Mermaid / Markmap / HTML)](#7-comment-exporter-pour-différents-formats)
8. [Versioning et reproductibilité](#8-versioning-et-reproductibilité)
9. [Limites connues](#9-limites-connues)
10. [Maintenance trimestrielle recommandée](#10-maintenance-trimestrielle-recommandée)

---

## 1. Qu'est-ce que DEBBY ?

**DEBBY** est une base de connaissances structurée en santé-sécurité au travail (SST), pensée pour appuyer la formation des **médecins du travail** et des **internes DES Médecine et Santé au Travail**.

Concrètement, DEBBY regroupe trois choses :

- **Un Knowledge Graph (KG)** — c'est-à-dire un graphe de connaissances qui relie entre elles : substances/agents (chimiques, biologiques, physiques, RPS), pathologies professionnelles, tableaux de maladies professionnelles (MP), métiers exposés, organes cibles et examens de surveillance. Le moteur du graphe s'appelle **Kuzu** (équivalent moderne de Neo4j, embarqué dans un fichier).
- **Un corpus documentaire massif** : 2,6 millions d'articles scientifiques (PubMed, OpenAlex, INRS, HAS, etc.) découpés en 22,9 millions de fragments (« chunks »), embeddés en vecteurs pour la recherche sémantique. C'est ce que les ingénieurs appellent un système RAG (Retrieval-Augmented Generation, recherche assistée par IA).
- **Des supports pédagogiques** — des fiches Markdown auto-générées depuis le KG, prêtes à être utilisées en formation initiale ou continue.

> **Pour résumer en une phrase :** DEBBY transforme automatiquement un graphe de connaissances SST + un corpus documentaire en supports pédagogiques pour la médecine du travail.

L'usage est local et souverain : **aucune donnée patient ne sort de votre poste**. Les seules requêtes IA externes (optionnelles) servent à enrichir les fiches avec des recommandations à jour.

---

## 2. À quoi ça sert pour ma pratique MdT / formation ?

### Use case 1 — Préparer une visite médicale

> « Je vois demain un soudeur inox. Quels risques je dois cibler ? »

1. Ouvrir `kg/exports/INDEX_METIERS.md` (la table des matières par métier)
2. Chercher « soudeur inox »
3. La fiche pointe vers les substances auxquelles il est exposé (chrome hexavalent, nickel…) et les fiches détaillées de chacune

### Use case 2 — Animer une séance pour internes DES MST

> « Cette semaine, séance sur l'amiante. »

1. Ouvrir `kg/exports/fiches/fiche_substance_amiante.md` — vous avez : identification chimique, pathologies, tableaux MP RG-30 + RA-47, métiers, surveillance HAS 2022, sources
2. Ouvrir `kg/exports/markmaps/amiante.mm.md` (en utilisant [Markmap REPL](https://markmap.js.org/repl)) — vous avez une **mind map interactive** projetable au tableau

### Use case 3 — Décider d'une déclaration MP

> « Patient avec cancer pulmonaire, exposition au chrome hexavalent : quel tableau ? »

1. Ouvrir `kg/exports/INDEX_TABLEAUX_MP.md`
2. Chercher « RG-10 » — l'index donne pathologies couvertes, substances liées, lien direct INRS
3. Pour les conditions précises (délai de prise en charge, durée d'exposition minimale, liste limitative/indicative) : suivre le lien INRS

### Use case 4 — Construire une fiche entreprise

> « Carrosserie 12 salariés, peintres + tôliers. »

1. Ouvrir `kg/exports/INDEX_ORGANES.md` (entrée par système / pathologie)
2. Filtrer par catégorie pathologie (asthme, dermatite, cancer) → liste des substances concernées
3. Croiser avec les substances présentes dans l'atelier (isocyanates, toluène, peintures plomb-zinc)

### Use case 5 — Veille personnelle

Les fiches sont **versionnées et datées**. Si vous voyez une fiche datée de plus de 6 mois, c'est le signal pour relancer le pipeline (cf. §10 — Maintenance) afin d'intégrer les dernières recommandations HAS, décrets, mises à jour INRS.

---

## 3. Comment naviguer dans les fiches pédagogiques

Toutes les fiches et index sont dans `kg/exports/`. Vous avez **5 portes d'entrée** :

| Porte d'entrée | Fichier | Pour qui / quel usage |
|---|---|---|
| **HTML statique** | `kg/exports/INDEX.html` | Le plus visuel — recherche live JavaScript, onglets, badges CMR. Ouvrir avec un double-clic dans votre navigateur. Aucun serveur requis. |
| **Index maître Markdown** | `kg/exports/INDEX_MASTER.md` | Vue d'ensemble + statistiques globales |
| **Index par substance (A-Z)** | `kg/exports/INDEX_SUBSTANCES.md` | « j'ai une substance précise en tête » |
| **Index par métier / secteur** | `kg/exports/INDEX_METIERS.md` | « je connais le métier, pas les substances » |
| **Index par tableau MP** | `kg/exports/INDEX_TABLEAUX_MP.md` | « je veux comprendre un tableau précis » |
| **Index par organe / type de pathologie** | `kg/exports/INDEX_ORGANES.md` | « je connais la pathologie ou l'organe cible » |

### Comment ouvrir un fichier Markdown ?

- **macOS** : double-clic → s'ouvre dans TextEdit (lisible mais brut). Mieux : installer [Obsidian](https://obsidian.md/) (gratuit) ou [VS Code](https://code.visualstudio.com/) (gratuit) — rendu joli, liens cliquables, navigation graphe.
- **Windows / Linux** : pareil, Obsidian ou VS Code recommandé.
- **Dans le navigateur** : ouvrir directement le repo sur GitHub ou Gitea NAS — le rendu Markdown est automatique.

### Comment ouvrir le fichier HTML ?

Double-clic sur `kg/exports/INDEX.html`. Il s'ouvre dans votre navigateur, **sans connexion Internet requise** (sauf pour Bootstrap CSS qui est chargé via CDN — c'est-à-dire un serveur public). Si vous voulez le rendre 100 % hors-ligne, dites-le, c'est faisable en 5 min.

---

## 4. Comment générer une nouvelle fiche substance

Vous voulez une fiche pour une substance **déjà présente** dans le KG mais sans fiche encore produite ? Une seule ligne de commande.

### Pré-requis (à faire une seule fois)

Ouvrir l'application **Terminal** (macOS : Cmd+Espace → taper « Terminal »). Vérifier que Python est installé :

```bash
python3 --version
```

Vous devez voir quelque chose comme `Python 3.10.x` ou supérieur. Si pas installé, demandez à votre informaticien.

Installer la librairie Kuzu (graphe) :

```bash
pip install kuzu
```

### Générer la fiche

```bash
cd /Users/radu/Developer/projects/debby-audit-snapshot
python3 kg/scripts/export_fiche_pedagogique.py --substance amiante
```

Remplacer `amiante` par l'**ID de la substance** (voir la colonne ID dans `INDEX_SUBSTANCES.md`, ex : `plomb`, `chrome_hexavalent`, `benzene`, `formaldehyde`…).

La fiche est créée dans `kg/exports/fiches/fiche_substance_<ID>.md`.

### Régénérer TOUS les index après ajout

```bash
python3 kg/scripts/build_index.py
```

Cela met à jour les 4 index + INDEX.html + INDEX_MASTER.md.

---

## 5. Comment ajouter une nouvelle substance au KG

Vous voulez **ajouter une substance qui n'existe pas encore dans le KG** ? La source de vérité est un fichier JSON éditable à la main.

### Étape 1 — Éditer le fichier source

Ouvrir `kg/data/substances_pilotes_v0.2.json` avec votre éditeur préféré (TextEdit, VS Code, Obsidian, Sublime Text…). Vous verrez une liste de substances au format suivant :

```json
{
  "id": "amiante",
  "nom_fr": "Amiante (chrysotile, amosite, crocidolite)",
  "nom_en": "Asbestos",
  "cas": "1332-21-4",
  "categorie": "mineral",
  "cmr": "C1A",
  "vlep_8h_mg_m3": 0.01,
  "source_url": "https://www.inrs.fr/risques/amiante",
  "tableaux_mp": ["RG-30", "RG-30-BIS", "RG-30-TER", "RA-47", "RA-47-BIS", "RA-47-TER"],
  "pathologies": ["mesotheliome", "asbestose", "cancer_broncho_pulmonaire_amiante", "plaques_pleurales"],
  "metiers_exposes": ["couvreur", "calorifugeur", "mecanicien"],
  "iarc": "1"
}
```

**Champs obligatoires** :
- `id` : identifiant court, minuscules, sans espace ni accent (ex : `formaldehyde`, `n_hexane`)
- `nom_fr` : nom français complet
- `categorie` : `mineral` / `metal` / `cov` / `solvant` / `pesticide` / `biologique` / `physique` / `ergonomique` / `rps` / `organisationnel`
- `source_url` : URL de la fiche INRS de référence (ou autre source officielle)

**Champs recommandés** :
- `cas` : numéro CAS officiel
- `cmr` : classification CLP (`C1A`, `C1B`, `C2`, `M1A`, `M2`, `R1A`, `R1B`, `R2`) — laisser `null` si non CMR
- `vlep_8h_mg_m3` : valeur limite d'exposition professionnelle 8h (en mg/m³) — laisser `null` si non applicable (ex : RPS, ergonomique)
- `tableaux_mp` : liste des codes tableaux MP applicables (ex : `["RG-30", "RA-47"]`)
- `pathologies` : liste des identifiants pathologies provoquées (utiliser des IDs cohérents, ex : `cancer_broncho_pulmonaire_amiante`)
- `metiers_exposes` : liste des identifiants métiers

> ⚠️ **Bien vérifier la cohérence** : si vous mettez un tableau MP qui n'existe pas dans `tableaux_mp_v0.2.json`, il sera ignoré.

### Étape 2 — Reconstruire le KG

```bash
cd /Users/radu/Developer/projects/debby-audit-snapshot
python3 kg/scripts/build_kg.py --rebuild
```

L'option `--rebuild` repart d'une base vide et recharge tout. Durée : ~10 secondes pour 50 substances.

### Étape 3 — Générer la fiche puis les index

```bash
python3 kg/scripts/export_fiche_pedagogique.py --substance <nouveau_id>
python3 kg/scripts/build_index.py
python3 kg/scripts/export_markmap.py --only <nouveau_id>
```

### Étape 4 — Valider avant publication

Ouvrir la fiche, contrôler :
- Pathologies attendues bien présentes
- Tableaux MP corrects (cf. INRS BDD MP)
- VLEP correct (cf. ED 984 INRS)
- Surveillance médicale recommandée à jour (cf. HAS)

Pour gagner du temps, voir §6 (cross-validation MCP SSTinfo).

---

## 6. Comment cross-valider une fiche via MCP SSTinfo

**MCP SSTinfo** est un serveur de requêtes SST que vous pouvez interroger directement depuis Claude (l'IA d'Anthropic dans VS Code, le navigateur ou l'application). Cela permet de **vérifier** chaque élément d'une fiche contre une base de référence indépendante.

> **MCP = Model Context Protocol** : un standard ouvert qui connecte une IA à des outils externes (bases de données, calculatrices, etc.). Pas besoin de comprendre les détails techniques pour l'utiliser.

### Si vous utilisez Claude Code, Claude Desktop ou claude.ai

Posez simplement la question — par exemple :

> « Vérifie la fiche amiante : VLEP, tableaux MP applicables, recommandations HAS de suivi. Utilise lookup_substance, lookup_tableau_mp, et search_documents. »

L'IA va appeler les bons outils MCP et vous donner un retour structuré.

### Commandes MCP utiles (à mentionner explicitement à l'IA)

| Outil MCP | Quand l'utiliser |
|---|---|
| `lookup_substance` | Vérifier identifiants chimiques, CAS, VLEP, classification CMR |
| `lookup_tableau_mp` | Conditions exactes d'un tableau MP (délai, durée, liste travaux) |
| `lookup_metier` | Risques associés à un métier précis |
| `search_documents` | Trouver une brochure INRS ou ED précise |
| `aide_decision` | Suivi médical post-exposition, inaptitude, CMR |
| `legifrance_search` | Vérifier un texte législatif (Code du travail, décret) |

### Validation rapide d'une fiche (workflow type)

1. Ouvrir la fiche substance à valider
2. Dans Claude, dire : « Audit la fiche `kg/exports/fiches/fiche_substance_<id>.md` en vérifiant via MCP SSTinfo chaque tableau MP, la VLEP, et les pathologies. Liste les écarts. »
3. Claude renvoie une liste d'écarts (si la VLEP diffère, si un tableau manque, si une pathologie est absente du KG) — vous corrigez à la main le JSON, puis vous reconstruisez.

---

## 7. Comment exporter pour différents formats

### Format Markdown (par défaut)

Fiches pédagogiques + index, lisibles dans GitHub, Obsidian, VS Code. Déjà générés.

### Format Mermaid (graphe dans la fiche)

Mermaid est un langage de diagrammes qui s'affiche dans Obsidian, GitHub, GitLab, VS Code (avec l'extension Mermaid). Le graphe est généré automatiquement dans chaque fiche (section 7).

Pour exporter le graphe global ou un sous-graphe par substance :

```bash
python3 kg/scripts/export_graph.py
# Génère :
# - kg/exports/debby_kg_full_v0.1.graphml (Gephi/yEd/Cytoscape)
# - kg/exports/debby_kg_full_v0.1.mermaid.md (rendu Markdown)
# - kg/exports/debby_kg_<substance>_v0.1.mermaid.md (sous-graphes focalisés)
```

### Format Markmap (mind maps interactives)

Markmap = mind map à partir de Markdown structuré. Les 49 fichiers `.mm.md` sont dans `kg/exports/markmaps/`.

**Pour visualiser une mind map :**

- **Online** : aller sur [markmap.js.org/repl](https://markmap.js.org/repl), copier-coller le contenu du fichier `.mm.md`
- **VS Code** : installer l'extension `markmap-vscode`, ouvrir le fichier, bouton « Open as Markmap »
- **CLI** : `npx markmap-cli kg/exports/markmaps/amiante.mm.md`

### Format HTML statique (Bootstrap)

```bash
python3 kg/scripts/build_index.py
# Génère kg/exports/INDEX.html (Bootstrap + recherche JS)
```

Double-cliquer pour ouvrir dans le navigateur. Aucun serveur requis. Peut être hébergé sur n'importe quel hébergement statique (GitHub Pages, NAS Synology, Nginx).

### Format GraphML (Gephi / yEd / Cytoscape)

Le fichier `kg/exports/debby_kg_full_v0.1.graphml` est compatible avec :
- [Gephi](https://gephi.org/) — analyse de réseau, layouts automatiques
- [yEd](https://www.yworks.com/products/yed) — éditeur graphique fluide
- [Cytoscape](https://cytoscape.org/) — analyse réseaux biologiques

---

## 8. Versioning et reproductibilité

DEBBY utilise un **versioning sémantique** pour chaque composant. Cela permet de **savoir exactement** dans quelle configuration une fiche a été générée, et de retrouver ce qu'il y avait à un moment donné.

### Les versions à connaître

| Composant | Version actuelle (au 2026-05-27) | Quand ça change ? |
|---|---|---|
| `kg_version` | `kuzu-50sub-v0.2` | À chaque ajout/modification de substance dans le KG |
| `corpus_version` | `2.1` | À chaque ajout massif de documents au corpus RAG |
| `chunking_version` | `pc-3600-v1` | À chaque re-découpage des documents en fragments |
| `embed_version` | `qwen3-8b-or-fp16-L2-v1` | À chaque re-calcul des vecteurs sémantiques |
| `tableaux_mp_reference` | `inrs-175-v1.0` | À chaque mise à jour de la liste INRS des tableaux MP |
| `benchmark_version` | `fr-mdt-49-v1.0` | À chaque évolution du benchmark FR (49 questions test) |

Toutes les versions sont listées dans `VERSIONS.md` à la racine.

### Pourquoi c'est important ?

Si dans 18 mois quelqu'un (vous, un audit, un collègue MdT, un juriste) demande « comment as-tu produit cette fiche amiante du 27 mai 2026 ? », vous pouvez répondre :

> « KG version kuzu-50sub-v0.2, corpus 2.1, chunking pc-3600-v1, embeddings Qwen3-8B fp16. Tous les scripts sont versionnés dans Git, je peux régénérer à l'identique. »

C'est ce qu'on appelle **la reproductibilité scientifique**. C'est utile pour :
- Soutenir une déclaration MP devant la CPAM (audit traçable)
- Publier un article ou un poster avec méthodologie transparente
- Permettre à un collègue de reproduire votre démarche

### Snapshot avant chaque modification importante

Avant d'éditer le JSON des substances, faire un commit Git :

```bash
cd /Users/radu/Developer/projects/debby-audit-snapshot
git add -A
git commit -m "Snapshot avant ajout substance XYZ"
```

Si vous cassez quelque chose, vous pouvez revenir en arrière avec `git checkout <hash>`.

---

## 9. Limites connues

DEBBY est un outil pédagogique en évolution constante. Voici les **limites identifiées au 2026-05-27** :

### Limites de couverture du KG

- **49 substances pilotes seulement** dans le KG. Beaucoup de substances importantes ne sont pas encore couvertes (ex : poussières alvéolaires, fluides de coupe, certains pesticides). Voir backlog dans `DEBBY_AUDIT_SNAPSHOT.md` §10.
- **68 tableaux MP couverts sur 175 référencés INRS**. Les autres tableaux sont présents dans le KG comme nodes mais sans pathologie/substance rattachée.
- **Certains tableaux BIS/TER restent à valider** par lecture des textes INRS primaires. Les liens INRS dans les index permettent ce contrôle.

### Limites de surveillance médicale

- Les recommandations de surveillance proviennent principalement de **HAS 2022** (scanner thoracique amiante) et **INRS 2017**. Pour les autres substances, les recommandations sont **à compléter manuellement** — c'est noté dans la fiche par « _Aucune surveillance recommandée renseignée dans le KG._ »
- **Pas de calcul de score de risque individuel** — DEBBY donne le cadre général, pas une stratification individuelle.

### Limites du corpus documentaire (couche RAG)

- **Sources rares pour certaines substances** spécialisées (ex : nouvelles molécules industrielles). Le retrieval peut renvoyer peu de résultats.
- **Biais de langue** : 60 % du corpus est en anglais. La couche 2 (retrieval) francise les requêtes EN→FR mais les réponses peuvent contenir des termes anglais.
- **Rétractations** : 13 913 articles rétractés sont identifiés et marqués, mais l'identification n'est pas exhaustive (cf. limites Retraction Watch).
- **Voir détail complet dans `DEBBY_AUDIT_SNAPSHOT.md` §10.3** (24 anomalies listées pour audit externe).

### Limites pédagogiques

- **DEBBY ne remplace JAMAIS** :
  - La lecture des textes primaires (INRS, HAS, Légifrance)
  - Le jugement clinique du médecin du travail
  - L'expertise pluridisciplinaire (IPRP, ergonome, toxicologue)
- Les fiches sont des **points de départ** pour la formation, pas des références opposables.

### Limites techniques

- **Pas de SSO/multi-utilisateurs** : DEBBY est aujourd'hui un outil personnel/équipe restreinte. Pour usage SPSTI complet, prévoir une couche d'authentification.
- **Pas de mobile-first** : l'HTML est responsive mais conçu pour écran de bureau.
- **Aucun traitement de données patient** : DEBBY est uniquement un référentiel de connaissances génériques. Toute pseudonymisation/anonymisation de données réelles est hors-scope.

---

## 10. Maintenance trimestrielle recommandée

Pour que DEBBY reste utile, prévoir une **petite session de maintenance tous les 3 mois** (~1 heure).

### Checklist trimestrielle

#### A — Mises à jour réglementaires (15 min)

- [ ] Consulter [INRS — Actualités](https://www.inrs.fr/actualites.html) → nouveaux tableaux MP, nouvelles VLEP
- [ ] Consulter [HAS — Recommandations professionnelles](https://www.has-sante.fr/jcms/c_1018787/fr/recommandations-de-bonne-pratique) → nouvelles recos surveillance MdT
- [ ] Consulter [Légifrance — Code du travail](https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006072050) → décrets/arrêtés récents

#### B — Mise à jour KG (15 min)

- [ ] Éditer `kg/data/substances_pilotes_v0.2.json` si nouvelles substances/VLEP/tableaux
- [ ] Éditer `kg/data/tableaux_mp_v0.2.json` si nouveaux tableaux INRS
- [ ] Lancer `python3 kg/scripts/build_kg.py --rebuild`
- [ ] Lancer `python3 kg/scripts/query_kg.py` (test 10 questions multi-hop, doit rester ≥ 7/10)

#### C — Régénération des supports (5 min)

- [ ] `python3 kg/scripts/export_graph.py`
- [ ] `python3 kg/scripts/export_fiche_pedagogique.py --substance <id>` pour chaque substance modifiée
- [ ] `python3 kg/scripts/export_markmap.py`
- [ ] `python3 kg/scripts/build_index.py`

#### D — Audit rétractations corpus (15 min)

- [ ] Télécharger la dernière CSV Retraction Watch
- [ ] Lancer la mise à jour `scripts/body_lang_v2.py` ou équivalent (cf. RUNBOOK_MATIN_HUB_VULTR.md)

#### E — Cross-validation MCP (10 min, optionnel)

- [ ] Pour 3-5 fiches modifiées, lancer une cross-validation via MCP SSTinfo (cf. §6)
- [ ] Lister les écarts → corriger le JSON, rebuild

#### F — Commit Git + push (5 min)

```bash
cd /Users/radu/Developer/projects/debby-audit-snapshot
git add -A
git commit -m "Maintenance trimestrielle Q<n> 2026 — KG v<x>"
git push
```

### Si vous voyez une fiche datée de > 6 mois

C'est le **signal d'alerte** : repasser la checklist ci-dessus avant d'utiliser la fiche en formation.

---

## Annexe — En cas de problème

### Commandes ne fonctionnent pas ?

1. Vérifier que vous êtes bien dans le bon dossier : `cd /Users/radu/Developer/projects/debby-audit-snapshot`
2. Vérifier Python : `python3 --version` (doit être ≥ 3.10)
3. Vérifier Kuzu : `python3 -c "import kuzu; print(kuzu.__version__)"`

### Fichier corrompu ?

Si le KG plante, supprimer puis recharger :

```bash
rm -rf kg/data/kuzu.db
python3 kg/scripts/build_kg.py --rebuild
```

Le JSON `substances_pilotes_v0.2.json` est la source de vérité, vous ne perdez aucune donnée.

### Besoin d'aide ?

- Issues GitHub : [reddepot/debby-audit-snapshot/issues](https://github.com/reddepot/debby-audit-snapshot/issues)
- Contact : redtech@protonmail.com
- Audit externe : voir `prompts/PROMPT_2_AMELIORATION_CONTINUE.md` pour confier l'amélioration à une IA agentique

---

**Document écrit pour le médecin du travail formateur. Si un terme reste obscur, c'est que je n'ai pas fait mon travail — signalez-le-moi.**

— Radu, MdT (ASSTV86, Vienne FR) · `redtech@protonmail.com` · 2026-05-27
