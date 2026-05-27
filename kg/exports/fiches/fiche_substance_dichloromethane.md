# Fiche pédagogique — **Dichlorométhane**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Dichlorométhane
- **Nom anglais** : Dichloromethane
- **N° CAS** : `75-09-2`
- **Catégorie** : solvant_chlore
- **CMR (CLP)** : **Cancérogène suspecté** ⚠️
- **VLEP 8h** : `178.0 mg/m³`
- **VLEP court terme** : `356.0 mg/m³`

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Atteinte hepatique dcm** | autre | moderee | IARC-2A |
| **Intoxication co secondaire dcm** | neurologique | moderee | IARC-2A |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RG-12`** | Affections provoquées par les dérivés halogénés des hydrocarbures aliphatiques (trichloréthylène, dichlorométhane, etc.) | RG | — |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**INDUSTRIE** : Decapage peinture

**SANTE** : Pharmacien

**SERVICES** : Aerosols

## 5. Organes/systèmes cibles

- **Foie** (système digestif)

## 6. Surveillance médicale recommandée

_Aucune surveillance recommandée renseignée dans le KG._

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Dichlorométhane"]
    atteinte_hepatique_dcm["Atteinte hepatique dcm"]
    S -->|CAUSE| atteinte_hepatique_dcm
    intoxication_co_secondaire_dcm["Intoxication co secondaire dcm"]
    S -->|CAUSE| intoxication_co_secondaire_dcm
    RG_12["RG-12"]
    atteinte_hepatique_dcm -.->|classifiée dans| RG_12
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_dichloromethane_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/dichloromethane
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance dichloromethane`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.