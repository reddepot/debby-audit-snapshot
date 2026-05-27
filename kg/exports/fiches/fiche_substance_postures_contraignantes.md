# Fiche pédagogique — **Postures contraignantes et hyperflexion**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Postures contraignantes et hyperflexion
- **Nom anglais** : Awkward postures
- **Catégorie** : ergonomique

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Epicondylite** | autre | moderee | — |
| **Syndrome canal carpien** | autre | moderee | — |
| **Tendinite epaule** | autre | moderee | — |
| **Tendinopathie genou** | autre | moderee | — |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RG-57`** | Affections péri-articulaires provoquées par certains gestes et postures de travail (TMS) | RG | — |
| **`RG-57-BIS`** | Affections péri-articulaires des membres supérieurs (variantes TMS récentes) | RG | BIS |
| **`RG-79`** | Lésions chroniques du ménisque (manutention) | RG | — |
| **`RG-98`** | Affections chroniques du rachis lombaire provoquées par la manutention manuelle habituelle de charges lourdes | RG | — |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**BTP** : Peintre batiment

**INDUSTRIE** : Coiffeur, Couturiere, Monteur chaine

**TRANSPORT_LOGISTIQUE** : Caissier

## 5. Organes/systèmes cibles

- **Os** (système musculo_squelettique)
- **Système nerveux** (système neurologique)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Syndrome canal carpien | **Électromyogramme (EMG)** | 12 mois | `HAS-2021` | 2021 |
| Tendinite epaule | **Examen neurologique clinique** | 12 mois | `INRS-TMS-2020` | 2020 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Postures contraignantes et hyperflexion"]
    epicondylite["Epicondylite"]
    S -->|CAUSE| epicondylite
    syndrome_canal_carpien["Syndrome canal carpien"]
    S -->|CAUSE| syndrome_canal_carpien
    tendinite_epaule["Tendinite epaule"]
    S -->|CAUSE| tendinite_epaule
    tendinopathie_genou["Tendinopathie genou"]
    S -->|CAUSE| tendinopathie_genou
    RG_57["RG-57"]
    epicondylite -.->|classifiée dans| RG_57
    RG_57_BIS["RG-57-BIS"]
    epicondylite -.->|classifiée dans| RG_57_BIS
    RG_79["RG-79"]
    epicondylite -.->|classifiée dans| RG_79
    RG_98["RG-98"]
    epicondylite -.->|classifiée dans| RG_98
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_postures_contraignantes_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/tms
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance postures_contraignantes`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.