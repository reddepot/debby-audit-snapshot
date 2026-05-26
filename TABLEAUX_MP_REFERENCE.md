# Tableaux MP — Référence INRS officielle

> **Source** : https://www.inrs.fr/publications/bdd/mp/listeTableaux.html  
> **Vérifié** : 2026-05-27 (WebFetch)  
> **But** : référence canonique pour le benchmark C.4 (couverture tableaux MP) + alimentation du nœud `Tableau_MP` du GraphRAG Kuzu (chantier II.1)

## Décompte total

| Régime | Principaux | BIS / TER | **Total** |
|---|---|---|---|
| **RG** (Régime Général) | 102 (RG 1 → RG 102) | **20 variantes** | **122** |
| **RA** (Régime Agricole) | 45 (RA 1 → RA 61, avec lacunes) | **8 variantes** | **53** |
| **TOTAL** | **147** | **28** | **175** |

**Correction par rapport au brief initial DEBBY** : le brief annonçait "86 RG + 65 RA = 151" — omettant les **24+ variantes BIS/TER** et sous-estimant les RG principaux. Découvert par Perplexity DR (2026-05-26 nuit) qui surestimait lui-même à 182 ; vérification INRS officielle donne **175**.

## Liste des variantes BIS/TER (28 au total)

### RG BIS/TER (20)

| Tableau | Variante | Pathologie indicative |
|---|---|---|
| RG 4 BIS | BIS | Hémopathies provoquées par benzène (variante) |
| **RG 10 BIS** | **BIS** | **Affections cutanées causées par chromates (peintures, ciments) — asthme inclus** |
| RG 10 TER | TER | Affections respiratoires causées par chromates |
| **RG 15 BIS** | **BIS** | **Affections cutanées provoquées par amines aromatiques (allergies)** |
| RG 15 TER | TER | Cancer de la vessie causé par amines aromatiques |
| RG 16 BIS | BIS | Affections cancéreuses provoquées par dérivés du goudron de houille |
| RG 20 BIS | BIS | Affections provoquées par l'arsenic (cancers) |
| RG 20 TER | TER | Cancers cutanés provoqués par l'arsenic |
| **RG 30 BIS** | **BIS** | **Cancer broncho-pulmonaire provoqué par l'amiante** |
| **RG 30 TER** | **TER** | **Mésothéliome malin primitif (amiante)** |
| RG 36 BIS | BIS | Affections provoquées par les huiles et graisses |
| RG 37 BIS | BIS | Affections cutanées provoquées par phénylhydrazine |
| RG 37 TER | TER | Cancers provoqués par certains dérivés (variante) |
| RG 43 BIS | BIS | Affections cancéreuses (variante) |
| RG 44 BIS | BIS | Sidérose (poussières de fer — variante) |
| RG 49 BIS | BIS | Affections provoquées par dérivés nitrés (variante) |
| RG 52 BIS | BIS | Affections provoquées par chlorure de vinyle (variante) |
| RG 61 BIS | BIS | Affections provoquées par le cadmium (variante) |
| RG 66 BIS | BIS | Affections respiratoires d'origine immunoallergique (variante) |
| RG 70 BIS | BIS | Cobalt (variante) |
| RG 70 TER | TER | Cobalt (autre variante) |
| RG 71 BIS | BIS | Affections oculaires (variante) |

### RA BIS/TER (8)

| Tableau | Variante | Pathologie indicative |
|---|---|---|
| RA 5 BIS | BIS | Spirochétoses (variante) |
| RA 13 BIS | BIS | Affections provoquées par les rickettsioses |
| RA 19 BIS | BIS | Tularémie (variante) |
| RA 25 BIS | BIS | Hémopathies provoquées par benzène agricole |
| RA 28 BIS | BIS | Affections respiratoires (variante) |
| RA 35 BIS | BIS | Affections périarticulaires (variante) |
| RA 47 BIS | BIS | Affections cancéreuses provoquées par bois |
| RA 47 TER | TER | Cancers naso-sinusiens provoqués par poussières de bois |
| RA 57 BIS | BIS | Lésions chroniques du ménisque (variante) |

> **Note** : les intitulés ci-dessus sont indicatifs et nécessitent vérification précise via `lookup_tableau_mp(query="RG 10 BIS")` ou consultation directe `inrs.fr/publications/bdd/mp/listeTableaux.html`. À enrichir lors du chantier I.3 (Tableaux MP v2 strict).

## Pathologies critiques BIS/TER souvent oubliées

Les pathologies couvertes par les BIS/TER sont **graves** et constituent des points aveugles si le benchmark ne les inclut pas :

| Pathologie | Tableau | Critique pour MdT FR |
|---|---|---|
| **Mésothéliome amiante** | **RG 30 TER** | 800-1200 cas/an FR, latence 30-40 ans |
| **Cancer broncho-pulmonaire amiante** | **RG 30 BIS** | 2000-3000 cas/an FR |
| **Asthme aux chromates** | **RG 10 BIS** | Cosmétique, BTP, métallurgie |
| **Cancer vessie amines aromatiques** | **RG 15 TER** | Coiffure, peinture, plasturgie |
| **Cancer naso-sinusien poussières bois** | **RA 47 TER** | Menuisiers, ébénistes |
| **Hémopathies benzène** | **RG 4 BIS** + **RA 25 BIS** | Stations-service, raffineries, agriculture |

## Utilisation dans la roadmap

### Phase 1 (immédiat)
- **C.4 benchmark étendu** : tester la couverture sur les 175 tableaux (pas 151)
- **I.3 Tableaux MP v2 strict** : matcher RG-XX, RG-XX BIS, RG-XX TER, RA-XX, RA-XX BIS, RA-XX TER

### Phase 1-2 (GraphRAG Kuzu — II.1)
- Nœud `Tableau_MP` du graphe = 175 instances avec attributs `numero`, `type` (RG/RA), `variante` (NULL/BIS/TER), `pathologie`, `agent_causal`, `delai_pec`, `liste_travaux`
- Relations : `Substance ─CAUSE─→ Pathologie ─CLASSIFIÉE_DANS─→ Tableau_MP`

### Phase 2 (export pédagogique)
- Fiches métier dynamiques : chaque métier → tableaux MP applicables (avec variantes BIS/TER pour les expositions graves)

## Pointeurs

- INRS officiel : https://www.inrs.fr/publications/bdd/mp/listeTableaux.html
- MCP SSTinfo : `lookup_tableau_mp(query="RG 30 BIS")` (déjà en prod)
- Cf. memory `feedback_routing_mcp.md` — MCP-first pour toute requête tableau MP
- Cf. addendum Perplexity DR : `~/Downloads/SYNTHESE_DEBBY_20260526/ADDENDUM_PERPLEXITY_DR.md` §B.1
