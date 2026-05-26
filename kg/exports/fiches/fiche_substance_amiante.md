# Fiche pédagogique — **Amiante (chrysotile, amosite, crocidolite)**

> Auto-générée depuis DEBBY KG (kuzu-10sub-v0.1)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Amiante (chrysotile, amosite, crocidolite)
- **Nom anglais** : Asbestos
- **N° CAS** : `1332-21-4`
- **Catégorie** : mineral
- **CMR (CLP)** : **Cancérogène avéré 1A** ⚠️
- **VLEP 8h** : `0.01 mg/m³`

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Asbestose** | respiratoire | moderee | IARC-1 |
| **Plaques pleurales** | cutanee | legere | IARC-1 |
| **Cancer broncho pulmonaire amiante** | cancer | grave | IARC-1 |
| **Mesotheliome** | cancer | grave | IARC-1 |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RA-47`** | Tableau RA n°47 | RA | — |
| **`RA-47-BIS`** | Tableau RA n°47 BIS | RA | BIS |
| **`RA-47-TER`** | Tableau RA n°47 TER | RA | TER |
| **`RG-30`** | Tableau RG n°30 | RG | — |
| **`RG-30-BIS`** | Tableau RG n°30 BIS | RG | BIS |
| **`RG-30-TER`** | Tableau RG n°30 TER | RG | TER |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**BTP** : Couvreur

**INDUSTRIE** : Calorifugeur, Demolisseur, Mecanicien, Plombier

## 5. Organes/systèmes cibles

- **Plèvre** (système respiratoire)
- **Poumon** (système respiratoire)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Cancer broncho pulmonaire amiante | **Scanner thoracique** | 60 mois | `HAS-2022` | 2022 |
| Plaques pleurales | **Scanner thoracique** | 60 mois | `HAS-2022` | 2022 |
| Mesotheliome | **Scanner thoracique** | 60 mois | `HAS-2022` | 2022 |
| Asbestose | **Scanner thoracique** | 60 mois | `HAS-2022` | 2022 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-10sub-v0.1` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Amiante (chrysotile, amosite, crocidolite)"]
    asbestose["Asbestose"]
    S -->|CAUSE| asbestose
    plaques_pleurales["Plaques pleurales"]
    S -->|CAUSE| plaques_pleurales
    cancer_broncho_pulmonaire_amiante["Cancer broncho pulmonaire amiante"]
    S -->|CAUSE| cancer_broncho_pulmonaire_amiante
    mesotheliome["Mesotheliome"]
    S -->|CAUSE| mesotheliome
    RA_47["RA-47"]
    asbestose -.->|classifiée dans| RA_47
    RA_47_BIS["RA-47-BIS"]
    asbestose -.->|classifiée dans| RA_47_BIS
    RA_47_TER["RA-47-TER"]
    asbestose -.->|classifiée dans| RA_47_TER
    RG_30["RG-30"]
    asbestose -.->|classifiée dans| RG_30
    RG_30_BIS["RG-30-BIS"]
    asbestose -.->|classifiée dans| RG_30_BIS
    RG_30_TER["RG-30-TER"]
    asbestose -.->|classifiée dans| RG_30_TER
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_amiante_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/amiante
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-10sub-v0.1`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance amiante`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.