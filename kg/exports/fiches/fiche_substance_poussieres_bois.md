# Fiche pédagogique — **Poussières de bois (hêtre, chêne, exotiques)**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Poussières de bois (hêtre, chêne, exotiques)
- **Nom anglais** : Wood dust (hardwood)
- **Catégorie** : organique
- **CMR (CLP)** : **Cancérogène avéré 1A** ⚠️
- **VLEP 8h** : `1.0 mg/m³`

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Adenocarcinome ethmoide** | autre | moderee | IARC-1 |
| **Asthme bois** | respiratoire | moderee | IARC-1 |
| **Dermatite bois** | cutanee | legere | IARC-1 |
| **Cancer naso sinusien bois** | cancer | grave | IARC-1 |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RA-36`** | Affections respiratoires de mécanisme allergique provoquées par les bois en agriculture | RA | — |
| **`RA-47`** | Affections respiratoires professionnelles provoquées par les poussières de bois en agriculture | RA | — |
| **`RA-47-BIS`** | Affections cancéreuses provoquées par les poussières de bois en agriculture | RA | BIS |
| **`RA-47-TER`** | Cancer naso-sinusien provoqué par les poussières de bois en agriculture | RA | TER |
| **`RG-47`** | Affections professionnelles provoquées par les poussières de bois | RG | — |
| **`RG-47-BIS`** | Affections cancéreuses provoquées par les poussières de bois (adénocarcinome de l'ethmoïde, cancer naso-sinusien) | RG | BIS |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**BTP** : Charpentier, Parqueteur, Scieur

**INDUSTRIE** : Ebeniste, Menuisier

## 5. Organes/systèmes cibles

- **Peau** (système tegumentaire)
- **Poumon** (système respiratoire)
- **Voies aériennes supérieures** (système respiratoire)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Adenocarcinome ethmoide | **Examen ORL (rhinoscopie, nasofibroscopie)** | 24 mois | `INRS-bois` | 2017 |
| Cancer naso sinusien bois | **Examen ORL (rhinoscopie, nasofibroscopie)** | 24 mois | `INRS-bois` | 2017 |
| Asthme bois | **Épreuves fonctionnelles respiratoires (EFR)** | 12 mois | `INRS-2017` | 2017 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Poussières de bois (hêtre, chêne, exotiques)"]
    adenocarcinome_ethmoide["Adenocarcinome ethmoide"]
    S -->|CAUSE| adenocarcinome_ethmoide
    asthme_bois["Asthme bois"]
    S -->|CAUSE| asthme_bois
    dermatite_bois["Dermatite bois"]
    S -->|CAUSE| dermatite_bois
    cancer_naso_sinusien_bois["Cancer naso sinusien bois"]
    S -->|CAUSE| cancer_naso_sinusien_bois
    RA_36["RA-36"]
    adenocarcinome_ethmoide -.->|classifiée dans| RA_36
    RA_47["RA-47"]
    adenocarcinome_ethmoide -.->|classifiée dans| RA_47
    RA_47_BIS["RA-47-BIS"]
    adenocarcinome_ethmoide -.->|classifiée dans| RA_47_BIS
    RA_47_TER["RA-47-TER"]
    adenocarcinome_ethmoide -.->|classifiée dans| RA_47_TER
    RG_47["RG-47"]
    adenocarcinome_ethmoide -.->|classifiée dans| RG_47
    RG_47_BIS["RG-47-BIS"]
    adenocarcinome_ethmoide -.->|classifiée dans| RG_47_BIS
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_poussieres_bois_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/poussieres-bois
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance poussieres_bois`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.