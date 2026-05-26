# 10 questions multi-hop test — Go/No-Go ADR-001

> **Critère ADR-001** : ≥ 7/10 réponses correctes pour valider le prototype Kuzu 10 substances avant scale.  
> **Date** : 2026-05-27  
> **Auteur** : Claude Opus 4.7 (nuit) — questions co-construites sur la base du brief Prompt 1 (C.3 aptitude piégée) + Perplexity (C.5 surveillance obsolète) + cas concrets MdT FR.

## Format de chaque question

- **Q** : question en langage naturel MdT FR
- **Hops attendus** : 2-hop à 5-hop
- **Cypher target** : requête Kuzu cible à valider
- **Réponse attendue** : résultat attendu pour Go (avec sources)

---

## Q1 — Amiante → mésothéliome → tableau (3-hop)

**Q** : "Un patient avec mésothéliome a été exposé à l'amiante. Quel tableau MP s'applique ?"

**Cypher** :
```cypher
MATCH (s:Substance {id:'amiante'})-[:CAUSE]->(p:Pathologie {id:'mesotheliome'})
      -[:CLASSIFIEE_DANS]->(t:Tableau_MP)
RETURN t.id, t.intitule, t.delai_prise_en_charge_jours;
```

**Réponse attendue** : `RG-30-TER` (Mésothéliome malin primitif), délai PEC = 40 ans, durée d'exposition minimale = aucune.

---

## Q2 — Métier → substance → tableau (4-hop)

**Q** : "Un couvreur de 55 ans avec 30 ans d'expérience est inapte. À quels tableaux MP penser ?"

**Cypher** :
```cypher
MATCH (m:Metier {id:'couvreur'})-[:EXPOSE_A]->(s:Substance)
      -[:CAUSE]->(p:Pathologie)
      -[:CLASSIFIEE_DANS]->(t:Tableau_MP)
RETURN DISTINCT t.id, t.intitule, s.nom_fr, p.nom_fr
ORDER BY t.id;
```

**Réponse attendue** : RG-30, RG-30-BIS, RG-30-TER (amiante : asbestose, cancer pulmonaire, mésothéliome) — et potentiellement RG-44-BIS (sidérose si exposition fer).

---

## Q3 — Substance → pathologie → organe (3-hop)

**Q** : "Quels organes sont atteints par le benzène ?"

**Cypher** :
```cypher
MATCH (s:Substance {id:'benzene'})-[:CAUSE]->(p:Pathologie)
      -[:CONCERNE_ORGANE]->(o:Organe)
RETURN DISTINCT o.nom_fr, p.nom_fr;
```

**Réponse attendue** : Moelle osseuse / système hématopoïétique (leucémie, aplasie médullaire).

---

## Q4 — Tableau MP → liste métiers exposés (2-hop)

**Q** : "Quels métiers sont concernés par le tableau RG 25 (silicose) ?"

**Cypher** :
```cypher
MATCH (t:Tableau_MP {id:'RG-25'})-[:CONCERNE_METIER]->(m:Metier)
RETURN m.nom_fr, m.secteur;
```

**Réponse attendue** : Tailleur de pierre, maçon, carrier, fondeur, sableur (secteur BTP + industrie minérale).

---

## Q5 — Surveillance médicale (Pathologie → Examen → Périodicité)

**Q** : "Quelle est la périodicité recommandée du scanner thoracique pour la surveillance amiante ?"

**Cypher** :
```cypher
MATCH (p:Pathologie {id:'mesotheliome'})-[r:SURVEILLANCE]->(e:Examen {id:'scanner_thoracique'})
RETURN e.nom_fr, r.periodicite_mois, r.source_recommandation, r.annee_recommandation;
```

**Réponse attendue** : Scanner thoracique tous les 60 mois (5 ans), source HAS-2022 (boost temporel I.7 doit éliminer les recommandations OSHA 2003 = obsolètes).

---

## Q6 — VLEP comparaison (Substance → propriété)

**Q** : "Quelles substances ont une VLEP 8h < 0.05 mg/m³ ?"

**Cypher** :
```cypher
MATCH (s:Substance)
WHERE s.vlep_8h_mg_m3 IS NOT NULL AND s.vlep_8h_mg_m3 < 0.05
RETURN s.nom_fr, s.vlep_8h_mg_m3, s.cmr
ORDER BY s.vlep_8h_mg_m3 ASC;
```

**Réponse attendue** : Amiante (0.01), chrome hexavalent (0.001), nickel (0.001), cadmium (0.001), isocyanates (0.005). Tous CMR ou très toxiques.

---

## Q7 — Toxicité hépatique (filtre IARC + organe)

**Q** : "Quelles substances cancérogènes IARC-1 affectent le poumon ?"

**Cypher** :
```cypher
MATCH (s:Substance {iarc:'1'})-[:CAUSE]->(p:Pathologie)
      -[:CONCERNE_ORGANE]->(o:Organe {id:'poumon'})
RETURN DISTINCT s.nom_fr, p.nom_fr;
```

**Réponse attendue** : amiante (cancer broncho-pulmonaire amiante), silice cristalline (cancer pulmonaire silice), benzène (potentiellement non — touche hémato), formaldéhyde (cancer nasopharynx non poumon), chrome hexavalent (cancer broncho-pulmonaire), nickel (cancer naso-sinusien), cadmium (cancer pulmonaire). **Note pédagogique** : permet de discuter la spécificité organique.

---

## Q8 — Multi-substance, multi-tableau (5-hop, le plus complexe)

**Q** : "Un soudeur inox de 50 ans présente un cancer broncho-pulmonaire et un asthme. Quels tableaux MP appliquer et quels examens de surveillance prévoir ?"

**Cypher** :
```cypher
MATCH (m:Metier {id:'soudeur_inox'})-[:EXPOSE_A]->(s:Substance)
      -[:CAUSE]->(p:Pathologie)
      -[:CLASSIFIEE_DANS]->(t:Tableau_MP)
OPTIONAL MATCH (p)-[surv:SURVEILLANCE]->(e:Examen)
RETURN DISTINCT 
    s.nom_fr AS substance, 
    p.nom_fr AS pathologie, 
    t.id AS tableau_mp, 
    e.nom_fr AS examen_surveillance,
    surv.periodicite_mois;
```

**Réponse attendue** : Chrome hexavalent → cancer broncho-pulmonaire chrome (RG-10-TER) + asthme chromates (RG-10-BIS) ; Nickel → cancer naso-sinusien (RG-37-BIS) + asthme nickel ; Cadmium → cancer pulmonaire (RG-61) + nephropathie. **Surveillance** : scanner thoracique HAS-2022, EFR annuelle, dosage urinaire chrome/nickel/cadmium.

---

## Q9 — Détection obsolescence (I.7 Temporal Validity)

**Q** : "Quelles sources de surveillance plomb datent de plus de 10 ans dans le KG ?"

**Cypher** :
```cypher
MATCH (p:Pathologie)-[r:SURVEILLANCE]->(e:Examen)
WHERE p.nom_fr CONTAINS 'plomb' OR p.nom_fr CONTAINS 'saturnisme'
  AND r.annee_recommandation < 2015
RETURN p.nom_fr, e.nom_fr, r.source_recommandation, r.annee_recommandation;
```

**Réponse attendue** : Aucune (idéalement) car le KG doit être nettoyé via I.7 ; ou alerte explicite "obsolète, voir décret 3 mai 2023 VBE 200 µg/L plombémie" si présent. **Test du boost temporel obsolescence.**

---

## Q10 — Aptitude piégée (cas C.3 du Prompt 1, version pédagogique)

**Q** : "Un mécanicien automobile présente une intoxication aux solvants. Quelles substances responsables ? Quels tableaux ? Quelle conduite à tenir ?"

**Cypher** :
```cypher
MATCH (m:Metier {id:'mecanicien'})-[:EXPOSE_A]->(s:Substance)
WHERE s.categorie = 'cov' OR s.id IN ['benzene']
OPTIONAL MATCH (s)-[:CAUSE]->(p:Pathologie)-[:CLASSIFIEE_DANS]->(t:Tableau_MP)
RETURN DISTINCT s.nom_fr, p.nom_fr, t.id;
```

**Réponse attendue** : Benzène (RG-4), isocyanates pour les peintures (RG-62). **Conduite** : éviction substance + dosages biologiques + EFR + scanner si exposition longue.

---

## Critères Go/No-Go

| Critère | Cible | Outcome |
|---|---|---|
| Questions répondues correctement | ≥ 7/10 | À mesurer après load |
| Latence requête multi-hop p95 | < 500 ms | À mesurer |
| Reproductibilité (3 runs, σ Cypher) | < 0.05 | À mesurer |
| Sources citées (source_chunk_ids présents) | ≥ 80 % requêtes | À mesurer |
| Export GraphML / Mermaid OK | ✅ | À implémenter |

**Si Go** → étendre à 50 substances, intégrer SNOMED-CT FR, brancher MCP SSTinfo `lookup_tableau_mp` pour enrichissement continu.

**Si No-Go** → mitiger en réduisant scope (5 substances) ou changer pour NetworkX in-memory (GLM 5.1 frugal).
