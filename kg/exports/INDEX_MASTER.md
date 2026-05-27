# DEBBY KG — Index maître des supports pédagogiques

> Point d'entrée unique vers toutes les ressources pédagogiques DEBBY.
> KG version : `kuzu-50sub-v0.2` — Généré : 2026-05-27
> Pour les non-développeurs : commencer par [MANUEL_UTILISATEUR.md](../../MANUEL_UTILISATEUR.md)

---

## Statistiques du KG

| Indicateur | Valeur |
|---|---|
| Substances/agents indexés | **49** |
| Pathologies professionnelles | **167** |
| Tableaux MP référentiels (INRS) chargés | **192** |
| Tableaux MP couverts par >=1 substance pilote | **68** |
| &nbsp;&nbsp;&nbsp;&nbsp;dont régime général (RG) | 51 |
| &nbsp;&nbsp;&nbsp;&nbsp;dont régime agricole (RA) | 17 |
| Métiers/secteurs exposés | **164** |
| Organes/systèmes cibles | **9** |
| Examens de surveillance | **23** |
| Substances CMR catégorie 1 (avéré / présumé) | **16** ⚠️ |
| Fiches pédagogiques générées | **4** |

---

## Les 4 index navigables

### 1. [Index par substance (A→Z)](INDEX_SUBSTANCES.md)

Toutes les substances et agents (chimiques, biologiques, physiques, organisationnels, RPS) par ordre alphabétique. Utile pour : « j'ai un patient exposé au benzène, quelle est sa fiche ? »

### 2. [Index par métier / secteur](INDEX_METIERS.md)

Liste des métiers groupés par secteur (BTP, industrie, santé, agriculture) avec les substances auxquelles ils sont exposés. Utile pour : « je vois demain un peintre carrosserie, qu'est-ce qui le menace ? »

### 3. [Index par tableau de maladies professionnelles](INDEX_TABLEAUX_MP.md)

Tableaux MP du régime général (RG) puis du régime agricole (RA), avec pathologies et substances rattachées. Utile pour : « le tableau RG-30 BIS, ça couvre quoi exactement ? »

### 4. [Index par organe / système / type de pathologie](INDEX_ORGANES.md)

Entrée par organe cible (poumon, rein, système nerveux…) ou par type de pathologie (cancer, asthme, neuropathie…). Utile pour : « les substances neurotoxiques en milieu professionnel, qu'est-ce qu'on a ? »

---

## Ressources connexes

- **[INDEX.html](INDEX.html)** : version navigable HTML statique (Bootstrap + recherche JavaScript)
- **[Mind maps Markmap](markmaps/INDEX.md)** : 49 mind maps interactives par substance (visualisation hiérarchique)
- **[Graphe global GraphML](debby_kg_full_v0.1.graphml)** : import Gephi / yEd / Cytoscape
- **[Graphe Mermaid global](debby_kg_full_v0.1.mermaid.md)** : rendu dans Obsidian / GitHub
- **[Manuel utilisateur MdT](../../MANUEL_UTILISATEUR.md)** : guide d'usage non-développeur

## Sources de référence (au-delà du KG)

- [INRS — Tableaux MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- [INRS — Valeurs limites d'exposition (ED 984)](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- [HAS — Recommandations professionnelles](https://www.has-sante.fr/)
- [Légifrance — Code du travail (santé/sécurité)](https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006072050/LEGISCTA000006144094)
- MCP SSTinfo (validation en ligne via Claude) : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier`, `aide_decision`

---

## Avertissement

Ces supports pédagogiques sont **auto-générés** depuis le Knowledge Graph DEBBY. Ils agrègent des sources de référence (INRS, HAS, décrets FR) mais **ne remplacent pas** la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.

Dernière régénération : **2026-05-27** — KG version : `kuzu-50sub-v0.2`
