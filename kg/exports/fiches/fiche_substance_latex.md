# Fiche pédagogique — **Latex naturel (protéines)**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Latex naturel (protéines)
- **Nom anglais** : Natural rubber latex
- **Catégorie** : biologique

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Asthme latex** | respiratoire | moderee | — |
| **Choc anaphylactique latex** | autre | moderee | — |
| **Urticaire latex** | autre | moderee | — |
| **Dermatite latex** | cutanee | legere | — |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RG-95`** | Affections professionnelles de mécanisme allergique provoquées par les protéines de latex | RG | — |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**SANTE** : Aide soignant, Dentiste, Infirmiere, Manipulateur radio, Soignant

## 5. Organes/systèmes cibles

- **Peau** (système tegumentaire)
- **Poumon** (système respiratoire)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Urticaire latex | **Examen dermatologique clinique** | 12 mois | `INRS-2018` | 2018 |
| Asthme latex | **Épreuves fonctionnelles respiratoires (EFR)** | 12 mois | `INRS-2017` | 2017 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Latex naturel (protéines)"]
    asthme_latex["Asthme latex"]
    S -->|CAUSE| asthme_latex
    choc_anaphylactique_latex["Choc anaphylactique latex"]
    S -->|CAUSE| choc_anaphylactique_latex
    urticaire_latex["Urticaire latex"]
    S -->|CAUSE| urticaire_latex
    dermatite_latex["Dermatite latex"]
    S -->|CAUSE| dermatite_latex
    RG_95["RG-95"]
    asthme_latex -.->|classifiée dans| RG_95
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_latex_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/latex
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance latex`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.