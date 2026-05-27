# Fiche pédagogique — **Sulfure de carbone (CS2)**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Sulfure de carbone (CS2)
- **Nom anglais** : Carbon disulfide
- **N° CAS** : `75-15-0`
- **Catégorie** : solvant
- **CMR (CLP)** : **Reprotoxique 1B** ⚠️
- **VLEP 8h** : `15.0 mg/m³`

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Atherosclerose cs2** | autre | moderee | IARC-3 |
| **Encephalopathie cs2** | neurologique | moderee | IARC-3 |
| **Polynevrite cs2** | autre | moderee | IARC-3 |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RA-13`** | Sulfocarbonisme agricole (CS2) | RA | — |
| **`RG-22`** | Sulfocarbonisme professionnel (sulfure de carbone CS2) | RG | — |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**INDUSTRIE** : Cellophane, Viscose

**SERVICES** : Pesticides

## 5. Organes/systèmes cibles

- **Système nerveux** (système neurologique)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Polynevrite cs2 | **Électromyogramme (EMG)** | 12 mois | `HAS-2021` | 2021 |
| Encephalopathie cs2 | **Examen neurologique clinique** | 12 mois | `HAS-2021` | 2021 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Sulfure de carbone (CS2)"]
    atherosclerose_cs2["Atherosclerose cs2"]
    S -->|CAUSE| atherosclerose_cs2
    encephalopathie_cs2["Encephalopathie cs2"]
    S -->|CAUSE| encephalopathie_cs2
    polynevrite_cs2["Polynevrite cs2"]
    S -->|CAUSE| polynevrite_cs2
    RA_13["RA-13"]
    atherosclerose_cs2 -.->|classifiée dans| RA_13
    RG_22["RG-22"]
    atherosclerose_cs2 -.->|classifiée dans| RG_22
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_sulfure_carbone_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/cs2
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance sulfure_carbone`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.