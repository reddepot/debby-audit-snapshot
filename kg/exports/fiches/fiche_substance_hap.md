# Fiche pédagogique — **Hydrocarbures aromatiques polycycliques (HAP, brais de houille)**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Hydrocarbures aromatiques polycycliques (HAP, brais de houille)
- **Nom anglais** : Polycyclic aromatic hydrocarbons
- **Catégorie** : organique
- **CMR (CLP)** : **Cancérogène avéré 1A** ⚠️
- **VLEP 8h** : `0.15 mg/m³`

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Cancer bronchique hap** | cancer | grave | IARC-1 |
| **Cancer cutane hap** | cancer | grave | IARC-1 |
| **Cancer vessie hap** | cancer | grave | IARC-1 |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RG-16`** | Affections cutanées et cancers cutanés provoqués par les goudrons de houille, brais, suies de combustion | RG | — |
| **`RG-16-BIS`** | Affections cancéreuses provoquées par les dérivés suivants du pétrole (cancers cutanés, broncho-pulmonaires) | RG | BIS |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**BTP** : Routier etancheur

**INDUSTRIE** : Coke, Fondeur aluminium, Ramoneur

## 5. Organes/systèmes cibles

- **Peau** (système tegumentaire)
- **Poumon** (système respiratoire)
- **Rein** (système urinaire)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Cancer bronchique hap | **Scanner thoracique** | 60 mois | `HAS-2022` | 2022 |
| Cancer cutane hap | **Examen dermatologique clinique** | 12 mois | `INRS-2020` | 2020 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Hydrocarbures aromatiques polycycliques (HAP, brais de houille)"]
    cancer_bronchique_hap["Cancer bronchique hap"]
    S -->|CAUSE| cancer_bronchique_hap
    cancer_cutane_hap["Cancer cutane hap"]
    S -->|CAUSE| cancer_cutane_hap
    cancer_vessie_hap["Cancer vessie hap"]
    S -->|CAUSE| cancer_vessie_hap
    RG_16["RG-16"]
    cancer_bronchique_hap -.->|classifiée dans| RG_16
    RG_16_BIS["RG-16-BIS"]
    cancer_bronchique_hap -.->|classifiée dans| RG_16_BIS
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_hap_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/hap
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance hap`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.