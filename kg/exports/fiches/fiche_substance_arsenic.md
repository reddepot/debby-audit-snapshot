# Fiche pédagogique — **Arsenic et composés**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Arsenic et composés
- **Nom anglais** : Arsenic and compounds
- **N° CAS** : `7440-38-2`
- **Catégorie** : metal
- **CMR (CLP)** : **Cancérogène avéré 1A** ⚠️
- **VLEP 8h** : `0.01 mg/m³`

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Angiosarcome foie** | autre | moderee | IARC-1 |
| **Neuropathie arsenic** | neurologique | moderee | IARC-1 |
| **Cancer bronchique arsenic** | cancer | grave | IARC-1 |
| **Cancer cutane arsenic** | cancer | grave | IARC-1 |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RA-10`** | Affections provoquées par l'arsenic et ses composés agricoles | RA | — |
| **`RG-20`** | Affections provoquées par l'arsenic et ses composés | RG | — |
| **`RG-20-BIS`** | Cancers broncho-pulmonaires primitifs causés par l'inhalation de poussières renfermant des arséniates | RG | BIS |
| **`RG-20-TER`** | Cancer cutané provoqué par l'arsenic et ses composés minéraux | RG | TER |
| **`RG-52`** | Affections provoquées par le chlorure de vinyle monomère (CVM) | RG | — |
| **`RG-52-BIS`** | Hémangiosarcome du foie provoqué par le chlorure de vinyle monomère | RG | BIS |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**AGRICULTURE** : Viticulteur

**INDUSTRIE** : Fondeur metaux, Incinerateur, Verrerie

## 5. Organes/systèmes cibles

- **Foie** (système digestif)
- **Peau** (système tegumentaire)
- **Poumon** (système respiratoire)
- **Système nerveux** (système neurologique)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Cancer bronchique arsenic | **Scanner thoracique** | 60 mois | `HAS-2022` | 2022 |
| Neuropathie arsenic | **Dosage arsenic urinaire** | 12 mois | `INRS-2019` | 2019 |
| Cancer cutane arsenic | **Examen dermatologique clinique** | 12 mois | `INRS-2019` | 2019 |
| Angiosarcome foie | **Scanner thoracique** | 24 mois | `INRS-2017` | 2017 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Arsenic et composés"]
    angiosarcome_foie["Angiosarcome foie"]
    S -->|CAUSE| angiosarcome_foie
    neuropathie_arsenic["Neuropathie arsenic"]
    S -->|CAUSE| neuropathie_arsenic
    cancer_bronchique_arsenic["Cancer bronchique arsenic"]
    S -->|CAUSE| cancer_bronchique_arsenic
    cancer_cutane_arsenic["Cancer cutane arsenic"]
    S -->|CAUSE| cancer_cutane_arsenic
    RA_10["RA-10"]
    angiosarcome_foie -.->|classifiée dans| RA_10
    RG_20["RG-20"]
    angiosarcome_foie -.->|classifiée dans| RG_20
    RG_20_BIS["RG-20-BIS"]
    angiosarcome_foie -.->|classifiée dans| RG_20_BIS
    RG_20_TER["RG-20-TER"]
    angiosarcome_foie -.->|classifiée dans| RG_20_TER
    RG_52["RG-52"]
    angiosarcome_foie -.->|classifiée dans| RG_52
    RG_52_BIS["RG-52-BIS"]
    angiosarcome_foie -.->|classifiée dans| RG_52_BIS
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_arsenic_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/arsenic
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance arsenic`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.