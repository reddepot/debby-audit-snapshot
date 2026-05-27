# Fiche pédagogique — **Vibrations transmises au système main-bras**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Vibrations transmises au système main-bras
- **Nom anglais** : Hand-arm vibration
- **Catégorie** : physique

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Arthrose coude poignet vibrations** | autre | moderee | — |
| **Atteinte osteoarticulaire vibrations** | autre | moderee | — |
| **Syndrome canal carpien vibrations** | autre | moderee | — |
| **Syndrome raynaud vibrations** | autre | moderee | — |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RG-69`** | Affections provoquées par les vibrations et chocs transmis par certaines machines-outils (vibrations main-bras) | RG | — |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**BTP** : Btp marteau piqueur

**AGRICULTURE** : Forestier tronconneuse

**INDUSTRIE** : Metallurgiste meuleuse, Mineur

## 5. Organes/systèmes cibles

- **Peau** (système tegumentaire)
- **Système nerveux** (système neurologique)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Syndrome canal carpien vibrations | **Électromyogramme (EMG)** | 12 mois | `HAS-2021` | 2021 |
| Syndrome raynaud vibrations | **Examen dermatologique clinique** | 12 mois | `INRS-2019` | 2019 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Vibrations transmises au système main-bras"]
    arthrose_coude_poignet_vibrations["Arthrose coude poignet vibrations"]
    S -->|CAUSE| arthrose_coude_poignet_vibrations
    atteinte_osteoarticulaire_vibrations["Atteinte osteoarticulaire vibrations"]
    S -->|CAUSE| atteinte_osteoarticulaire_vibrations
    syndrome_canal_carpien_vibrations["Syndrome canal carpien vibrations"]
    S -->|CAUSE| syndrome_canal_carpien_vibrations
    syndrome_raynaud_vibrations["Syndrome raynaud vibrations"]
    S -->|CAUSE| syndrome_raynaud_vibrations
    RG_69["RG-69"]
    arthrose_coude_poignet_vibrations -.->|classifiée dans| RG_69
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_vibrations_main_bras_v0.1.mermaid.md`

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
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance vibrations_main_bras`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.