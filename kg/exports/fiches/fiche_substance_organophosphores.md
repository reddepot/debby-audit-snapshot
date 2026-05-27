# Fiche pédagogique — **Pesticides organophosphorés**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Pesticides organophosphorés
- **Nom anglais** : Organophosphate pesticides
- **Catégorie** : pesticide

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Intoxication aigue organophosphores** | neurologique | moderee | — |
| **Neuropathie retardee organophosphores** | neurologique | moderee | — |
| **Syndrome intermediaire** | autre | moderee | — |
| **Syndrome parkinsonien pesticides** | autre | moderee | — |

## 3. Tableaux de maladies professionnelles applicables

| Tableau | Intitulé | Régime | Variante |
|---|---|---|---|
| **`RA-11`** | Affections provoquées par les phosphates et phosphites organiques anticholinestérasiques (pesticides) | RA | — |

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**AGRICULTURE** : Agriculteur, Applicateur phytosanitaire, Jardinier, Viticulteur

## 5. Organes/systèmes cibles

- **Système nerveux** (système neurologique)

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Intoxication aigue organophosphores | **Cholinestérase érythrocytaire (pesticides)** | 12 mois | `INRS-pesticides` | 2020 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Pesticides organophosphorés"]
    intoxication_aigue_organophosphores["Intoxication aigue organophosphores"]
    S -->|CAUSE| intoxication_aigue_organophosphores
    neuropathie_retardee_organophosphores["Neuropathie retardee organophosphores"]
    S -->|CAUSE| neuropathie_retardee_organophosphores
    syndrome_intermediaire["Syndrome intermediaire"]
    S -->|CAUSE| syndrome_intermediaire
    syndrome_parkinsonien_pesticides["Syndrome parkinsonien pesticides"]
    S -->|CAUSE| syndrome_parkinsonien_pesticides
    RA_11["RA-11"]
    intoxication_aigue_organophosphores -.->|classifiée dans| RA_11
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_organophosphores_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/pesticides
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance organophosphores`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.