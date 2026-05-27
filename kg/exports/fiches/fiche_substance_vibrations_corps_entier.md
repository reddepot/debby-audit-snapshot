# Fiche pédagogique — **Vibrations corps entier**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Vibrations corps entier
- **Nom anglais** : Whole-body vibration
- **Catégorie** : physique

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Hernie discale vibrations** | autre | moderee | — |
| **Lombalgie chronique vibrations** | autre | moderee | — |
| **Sciatique vibrations** | autre | moderee | — |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RG-97`** | Affections chroniques du rachis lombaire provoquées par les vibrations corps entier | RG | — |
| **`RG-98`** | Affections chroniques du rachis lombaire provoquées par la manutention manuelle habituelle de charges lourdes | RG | — |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**TRANSPORT_LOGISTIQUE** : Camionneur, Cariste, Conducteur engins, Conducteur tractopelle

## 5. Organes/systèmes cibles

- **Os** (système musculo_squelettique)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Lombalgie chronique vibrations | **Examen neurologique clinique** | 12 mois | `INRS-2019` | 2019 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Vibrations corps entier"]
    hernie_discale_vibrations["Hernie discale vibrations"]
    S -->|CAUSE| hernie_discale_vibrations
    lombalgie_chronique_vibrations["Lombalgie chronique vibrations"]
    S -->|CAUSE| lombalgie_chronique_vibrations
    sciatique_vibrations["Sciatique vibrations"]
    S -->|CAUSE| sciatique_vibrations
    RG_97["RG-97"]
    hernie_discale_vibrations -.->|classifiée dans| RG_97
    RG_98["RG-98"]
    hernie_discale_vibrations -.->|classifiée dans| RG_98
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_vibrations_corps_entier_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/vibrations
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance vibrations_corps_entier`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.