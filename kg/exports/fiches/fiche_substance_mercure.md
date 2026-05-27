# Fiche pédagogique — **Mercure et composés**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Mercure et composés
- **Nom anglais** : Mercury and compounds
- **N° CAS** : `7439-97-6`
- **Catégorie** : metal
- **CMR (CLP)** : **Reprotoxique 1B** ⚠️
- **VLEP 8h** : `0.02 mg/m³`

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Intoxication mercurielle** | neurologique | moderee | IARC-2B |
| **Neuropathie mercure** | neurologique | moderee | IARC-2B |
| **Tremblement intentionnel mercure** | neurologique | moderee | IARC-2B |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RA-12`** | Affections provoquées par les dérivés mercuriels organiques (mercure) | RA | — |
| **`RG-2`** | Affections dues au mercure et à ses composés | RG | — |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**AGRICULTURE** : Orpaillage

**INDUSTRIE** : Instruments mesure, Thermometres

**SANTE** : Dentiste amalgames

## 5. Organes/systèmes cibles

- **Système nerveux** (système neurologique)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Neuropathie mercure | **Examen neurologique clinique** | 12 mois | `HAS-2021` | 2021 |
| Intoxication mercurielle | **Dosage mercure urinaire** | 12 mois | `INRS-2020` | 2020 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Mercure et composés"]
    intoxication_mercurielle["Intoxication mercurielle"]
    S -->|CAUSE| intoxication_mercurielle
    neuropathie_mercure["Neuropathie mercure"]
    S -->|CAUSE| neuropathie_mercure
    tremblement_intentionnel_mercure["Tremblement intentionnel mercure"]
    S -->|CAUSE| tremblement_intentionnel_mercure
    RA_12["RA-12"]
    intoxication_mercurielle -.->|classifiée dans| RA_12
    RG_2["RG-2"]
    intoxication_mercurielle -.->|classifiée dans| RG_2
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_mercure_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/mercure
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance mercure`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.