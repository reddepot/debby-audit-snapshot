# Fiche pédagogique — **Silice cristalline (quartz, cristobalite, tridymite)**

> Auto-générée depuis DEBBY KG (kuzu-10sub-v0.1)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Silice cristalline (quartz, cristobalite, tridymite)
- **Nom anglais** : Crystalline silica
- **N° CAS** : `14808-60-7`
- **Catégorie** : mineral
- **CMR (CLP)** : **Cancérogène avéré 1A** ⚠️
- **VLEP 8h** : `0.1 mg/m³`

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Scleroderme systemique** | autre | moderee | IARC-1 |
| **Silicose** | respiratoire | moderee | IARC-1 |
| **Cancer pulmonaire silice** | cancer | grave | IARC-1 |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RA-22`** | Tableau RA n°22 | RA | — |
| **`RG-25`** | Tableau RG n°25 | RG | — |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**BTP** : Carrier, Macon, Tailleur pierre

**INDUSTRIE** : Fondeur, Sableur

## 5. Organes/systèmes cibles

- **Peau** (système tegumentaire)
- **Poumon** (système respiratoire)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Cancer pulmonaire silice | **Scanner thoracique** | 24 mois | `HAS-2022` | 2022 |
| Silicose | **Scanner thoracique** | 24 mois | `INRS-2017` | 2017 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-10sub-v0.1` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Silice cristalline (quartz, cristobalite, tridymite)"]
    scleroderme_systemique["Scleroderme systemique"]
    S -->|CAUSE| scleroderme_systemique
    silicose["Silicose"]
    S -->|CAUSE| silicose
    cancer_pulmonaire_silice["Cancer pulmonaire silice"]
    S -->|CAUSE| cancer_pulmonaire_silice
    RA_22["RA-22"]
    scleroderme_systemique -.->|classifiée dans| RA_22
    RG_25["RG-25"]
    scleroderme_systemique -.->|classifiée dans| RG_25
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_silice_cristalline_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/silice-cristalline
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-10sub-v0.1`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance silice_cristalline`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.