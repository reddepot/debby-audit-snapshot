# Fiche pédagogique — **Travail de nuit et travail posté**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Travail de nuit et travail posté
- **Nom anglais** : Night work / shift work
- **Catégorie** : organisationnel
- **CMR (CLP)** : **2A_IARC** ⚠️

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Depression travail nuit** | autre | moderee | IARC-2A |
| **Maladies cardiovasculaires nuit** | autre | moderee | IARC-2A |
| **Syndrome metabolique nuit** | autre | moderee | IARC-2A |
| **Troubles sommeil chroniques** | autre | moderee | IARC-2A |
| **Cancer sein femme travail nuit** | cancer | grave | IARC-2A |

## 3. Tableaux de maladies professionnelles applicables

_Aucun tableau MP rattaché dans le KG._

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**INDUSTRIE** : Boulanger, Industrie continue

**SANTE** : Soignant

**SERVICES** : Securite

**TERTIAIRE** : Journaliste

**TRANSPORT_LOGISTIQUE** : Transport

## 5. Organes/systèmes cibles

_Aucun organe cible renseigné._

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Syndrome metabolique nuit | **Bilan métabolique (glycémie, lipides, IMC, TA)** | 12 mois | `HAS-2023` | 2023 |
| Maladies cardiovasculaires nuit | **Électrocardiogramme (ECG)** | 12 mois | `HAS-2023` | 2023 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Travail de nuit et travail posté"]
    depression_travail_nuit["Depression travail nuit"]
    S -->|CAUSE| depression_travail_nuit
    maladies_cardiovasculaires_nuit["Maladies cardiovasculaires nuit"]
    S -->|CAUSE| maladies_cardiovasculaires_nuit
    syndrome_metabolique_nuit["Syndrome metabolique nuit"]
    S -->|CAUSE| syndrome_metabolique_nuit
    troubles_sommeil_chroniques["Troubles sommeil chroniques"]
    S -->|CAUSE| troubles_sommeil_chroniques
    cancer_sein_femme_travail_nuit["Cancer sein femme travail nuit"]
    S -->|CAUSE| cancer_sein_femme_travail_nuit
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_travail_nuit_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/travail-de-nuit
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance travail_nuit`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.