# Fiche pédagogique — **Cadmium et composés**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Cadmium et composés
- **Nom anglais** : Cadmium and compounds
- **N° CAS** : `7440-43-9`
- **Catégorie** : metal
- **CMR (CLP)** : **M2+C1B+R2** ⚠️
- **VLEP 8h** : `0.004 mg/m³`

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Nephropathie cadmium** | autre | moderee | IARC-1 |
| **Osteomalacie cadmium** | autre | moderee | IARC-1 |
| **Cancer pulmonaire cadmium** | cancer | grave | IARC-1 |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RA-42`** | Tableau RA n°42 | RA | — |
| **`RG-61`** | Maladies professionnelles provoquées par le cadmium et ses composés | RG | — |
| **`RG-61-BIS`** | Cancer broncho-pulmonaire primitif provoqué par l'inhalation de poussières ou de fumées renfermant du cadmium | RG | BIS |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**INDUSTRIE** : Metallurgiste, Ouvrier batteries, Soudeur brasure

## 5. Organes/systèmes cibles

- **Os** (système musculo_squelettique)
- **Poumon** (système respiratoire)
- **Rein** (système urinaire)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Cancer pulmonaire cadmium | **Scanner thoracique** | 60 mois | `HAS-2022` | 2022 |
| Nephropathie cadmium | **Dosage cadmium urinaire** | 12 mois | `INRS-2020` | 2020 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Cadmium et composés"]
    nephropathie_cadmium["Nephropathie cadmium"]
    S -->|CAUSE| nephropathie_cadmium
    osteomalacie_cadmium["Osteomalacie cadmium"]
    S -->|CAUSE| osteomalacie_cadmium
    cancer_pulmonaire_cadmium["Cancer pulmonaire cadmium"]
    S -->|CAUSE| cancer_pulmonaire_cadmium
    RA_42["RA-42"]
    nephropathie_cadmium -.->|classifiée dans| RA_42
    RG_61["RG-61"]
    nephropathie_cadmium -.->|classifiée dans| RG_61
    RG_61_BIS["RG-61-BIS"]
    nephropathie_cadmium -.->|classifiée dans| RG_61_BIS
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_cadmium_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/cadmium
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance cadmium`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.