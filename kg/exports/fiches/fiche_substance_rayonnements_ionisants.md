# Fiche pédagogique — **Rayonnements ionisants (X, gamma, neutron)**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Rayonnements ionisants (X, gamma, neutron)
- **Nom anglais** : Ionizing radiation
- **Catégorie** : physique
- **CMR (CLP)** : **Cancérogène avéré 1A** ⚠️

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Cataracte radio induite** | autre | moderee | IARC-1 |
| **Syndrome aigu irradiation** | autre | moderee | IARC-1 |
| **Cancer thyroide radio induit** | cancer | grave | IARC-1 |
| **Leucemie radio induite** | cancer | grave | IARC-1 |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RG-6`** | Affections provoquées par les rayonnements ionisants | RG | — |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**INDUSTRIE** : Gammagraphe, Industrie nucleaire

**SANTE** : Cardiologue interventionnel, Manipulateur radio, Radiologue

## 5. Organes/systèmes cibles

- **Moelle osseuse** (système hematopoietique)
- **Voies aériennes supérieures** (système respiratoire)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Leucemie radio induite | **Numération formule sanguine + plaquettes** | 12 mois | `Code-santé-publique-R1333` | 2023 |
| Leucemie radio induite | **Dosimétrie passive (rayonnements ionisants)** | 12 mois | `Code-santé-publique-R1333` | 2023 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Rayonnements ionisants (X, gamma, neutron)"]
    cataracte_radio_induite["Cataracte radio induite"]
    S -->|CAUSE| cataracte_radio_induite
    syndrome_aigu_irradiation["Syndrome aigu irradiation"]
    S -->|CAUSE| syndrome_aigu_irradiation
    cancer_thyroide_radio_induit["Cancer thyroide radio induit"]
    S -->|CAUSE| cancer_thyroide_radio_induit
    leucemie_radio_induite["Leucemie radio induite"]
    S -->|CAUSE| leucemie_radio_induite
    RG_6["RG-6"]
    cataracte_radio_induite -.->|classifiée dans| RG_6
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_rayonnements_ionisants_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/rayonnements-ionisants
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance rayonnements_ionisants`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.