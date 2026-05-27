# Fiche pédagogique — **Stress thermique chaud (chaleur extrême)**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Stress thermique chaud (chaleur extrême)
- **Nom anglais** : Heat stress
- **Catégorie** : physique

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Coup chaleur** | autre | moderee | — |
| **Deshydratation professionnelle** | autre | moderee | — |
| **Insuffisance renale aigue chaleur** | autre | moderee | — |
| **Ipnea chaleur** | autre | moderee | — |
| **Syncope chaleur** | autre | moderee | — |

## 3. Tableaux de maladies professionnelles applicables

_Aucun tableau MP rattaché dans le KG._

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**BTP** : Btp canicule

**AGRICULTURE** : Agriculteur

**INDUSTRIE** : Cuisinier, Fonderie, Fondeur, Sider metallurgiste, Verrier

## 5. Organes/systèmes cibles

- **Rein** (système urinaire)
- **Système nerveux** (système neurologique)

## 6. Surveillance médicale recommandée

_Aucune surveillance recommandée renseignée dans le KG._

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Stress thermique chaud (chaleur extrême)"]
    coup_chaleur["Coup chaleur"]
    S -->|CAUSE| coup_chaleur
    deshydratation_professionnelle["Deshydratation professionnelle"]
    S -->|CAUSE| deshydratation_professionnelle
    insuffisance_renale_aigue_chaleur["Insuffisance renale aigue chaleur"]
    S -->|CAUSE| insuffisance_renale_aigue_chaleur
    ipnea_chaleur["Ipnea chaleur"]
    S -->|CAUSE| ipnea_chaleur
    syncope_chaleur["Syncope chaleur"]
    S -->|CAUSE| syncope_chaleur
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_stress_thermique_chaud_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/chaleur
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance stress_thermique_chaud`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.