# Fiche pédagogique — **Violence externe (clientèle, public)**

> Auto-générée depuis DEBBY KG (kuzu-49sub-v0.2)  
> Date : 2026-05-27  
> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  
> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  

---

## 1. Identification chimique

- **Nom français** : Violence externe (clientèle, public)
- **Nom anglais** : External workplace violence
- **Catégorie** : rps

## 2. Pathologies professionnelles induites

| Pathologie | Type | Sévérité | Niveau de preuve |
|---|---|---|---|
| **Depression reactionnelle** | autre | moderee | — |
| **Stress post traumatique** | autre | moderee | — |
| **Traumatismes physiques** | autre | moderee | — |
| **Troubles anxieux** | autre | moderee | — |

## 3. Tableaux de maladies professionnelles applicables

_Aucun tableau MP rattaché dans le KG._

> ℹ️ Pour chaque tableau, vérifier :
> - Délai de prise en charge
> - Durée d'exposition minimale
> - Liste limitative ou indicative des travaux
> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.

## 4. Métiers et secteurs exposés

**SANTE** : Soignant urgences

**SERVICES** : Controleur, Forces ordre

**TERTIAIRE** : Banquier, Enseignant

**TRANSPORT_LOGISTIQUE** : Caissier

## 5. Organes/systèmes cibles

_Aucun organe cible renseigné._

## 6. Surveillance médicale recommandée

| Pathologie ciblée | Examen | Périodicité | Source | Année |
|---|---|---|---|---|
| Depression reactionnelle | **Évaluation RPS (questionnaires WOCCQ, Karasek)** | 12 mois | `INRS-RPS-2023` | 2023 |
| Stress post traumatique | **Évaluation RPS (questionnaires WOCCQ, Karasek)** | 6 mois | `INRS-RPS-2023` | 2023 |

> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).
> Cette fiche est versionnée KG=`kuzu-49sub-v0.2` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.

## 7. Vue graphique focalisée

```mermaid
graph LR
    S["Violence externe (clientèle, public)"]
    depression_reactionnelle["Depression reactionnelle"]
    S -->|CAUSE| depression_reactionnelle
    stress_post_traumatique["Stress post traumatique"]
    S -->|CAUSE| stress_post_traumatique
    traumatismes_physiques["Traumatismes physiques"]
    S -->|CAUSE| traumatismes_physiques
    troubles_anxieux["Troubles anxieux"]
    S -->|CAUSE| troubles_anxieux
    classDef substance fill:#ffcccc,stroke:#990000
    classDef patho fill:#fff2cc,stroke:#cc7700
    classDef tableau fill:#ccebff,stroke:#0066cc
    class S substance
```

> Pour la vue complète : `kg/exports/debby_kg_violence_externe_v0.1.mermaid.md`

## 8. Sources et traçabilité

- **Source officielle substance** : https://www.inrs.fr/risques/agression
- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)
- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)
- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)
- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne
- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)

## 9. Versioning

- `kg_version` : `kuzu-49sub-v0.2`
- `corpus_version` : `2.1` (cf. `VERSIONS.md`)
- `fiche_generated_at` : `2026-05-27`
- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance violence_externe`

---

**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.