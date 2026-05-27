# B5 RAGAS multi-juge — rapport

- Benchmark : 15 requêtes FR DEBBY × top-3 chunks retrieved (LanceDB pilot)
- Juges : codex, gemini, kimi (3 CLI locaux, coût $0)
- Date : 2026-05-27 02:07
- Méthode : prompt RAGAS standardisé FR, 3 dimensions notées 0.0-1.0, moyenne + écart-type sur 3 voix

## Résumé global

| Dimension | Moyenne (sur 15 requêtes) | Écart-type | N requêtes valides |
|-----------|-----:|-----:|-----:|
| faithfulness | 0.033 | 0.000 | 1 |
| answer_relevance | 0.000 | 0.000 | 1 |
| context_precision | 0.000 | 0.000 | 1 |

**Recommandation orchestrateur :** URGENT — faithfulness moyenne 0.033 < 0.5, retrieval insuffisant

## Biais par juge (moyennes sur 15 requêtes)

| Juge | faithfulness | answer_relevance | context_precision | N |
|------|-----:|-----:|-----:|---:|
| codex | 0.100 | 0.000 | 0.000 | 1 |
| gemini | 0.000 | 0.000 | 0.000 | 1 |
| kimi | 0.000 | 0.000 | 0.000 | 1 |

## Top 3 requêtes — meilleur retrieval (moyenne 3 dimensions)

- **apt01** (aptitude, avg=0.011) — salarié cariste avec épilepsie traitée stabilisée, apte à la conduite de chariot élévateur ?

## Top 3 requêtes — pire retrieval (moyenne 3 dimensions)

- **apt01** (aptitude, avg=0.011) — salarié cariste avec épilepsie traitée stabilisée, apte à la conduite de chariot élévateur ?

## Divergences fortes entre juges (σ > 0.2)

_Aucune divergence forte détectée (σ ≤ 0.2 partout)._

## Détail par requête

| ID | Catégorie | Voix | faith-c | faith-g | faith-k | faith-μ | faith-σ | answe-c | answe-g | answe-k | answe-μ | answe-σ | conte-c | conte-g | conte-k | conte-μ | conte-σ |
|----|-----------|-----|------:|------:|------:|------:|------:|------:|------:|------:|------:|------:|------:|------:|------:|------:|------:|
| apt01 | aptitude | 3/3 | 0.100 | 0.000 | 0.000 | 0.033 | 0.058 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Commentaires (extraits, requêtes les plus mal notées)

### apt01 — salarié cariste avec épilepsie traitée stabilisée, apte à la conduite de chariot élévateur ?

- *codex* : faith=0.1 rel=0.0 prec=0.0
  - comment_faithfulness: Une réponse sur l’aptitude d’un cariste épileptique serait largement non étayée par ces sources, qui ne parlent que de chutes, hypotension et polymédication.
  - comment_relevance: Les chunks ne fournissent aucune information sur l’épilepsie stabilisée, la conduite de chariot élévateur, l’aptitude médicale ou les recommandations SST.
  - comment_precision: Les trois chunks proviennent du même contenu hors sujet sur les chutes liées aux médicaments et constituent donc du bruit pour cette requête.
- *gemini* : faith=0.0 rel=0.0 prec=0.0
  - comment_faithfulness: Les sources ne contiennent aucune information sur l'épilepsie ou l'aptitude à la conduite, rendant impossible la construction d'une réponse fidèle aux faits demandés.
  - comment_relevance: Les documents traitent des risques de chutes liés à la polymédication en gériatrie, ce qui est totalement hors-sujet par rapport à la question d'aptitude du cariste.
  - comment_precision: Le système a extrait des segments portant sur un domaine médical sans lien avec les mots-clés 'épilepsie' ou 'chariot élévateur', constituant un bruit de 100%.
- *kimi* : faith=0.0 rel=0.0 prec=0.0
  - comment_faithfulness: Les chunks traitent exclusivement de polypharmacy et de chutes médicamenteuses, sans aucune mention de l'épilepsie, de la conduite de chariot élévateur ou des critères d'aptitude professionnelle ; toute réponse construite à partir de ces sources serait non fondée ou hallucinée.
  - comment_relevance: Le contenu porte sur les chutes liées aux médicaments chez les personnes polytraitées, ce qui est totalement orthogonal à la question d'aptitude d'un cariste épileptique stabilisé.
  - comment_precision: Aucun des 3 chunks n'est pertinent pour la requête ; il s'agit d'un bruit total (0 % de précision) avec un sujet médicamenteux sans lien avec l'épilepsie ou la médecine du travail pour caristes.

## Méthode

- Payload : `payload.json` (15 requêtes × top-3 chunks)
- Prompt : RAGAS standardisé FR, demande JSON strict en sortie.
- Appels parallèles (3 CLI simultanés par requête), 3 retries max.
- Timeouts : kimi 90s, codex 180s, gemini 120s.
- Kimi lancé avec `--mcp-config-file` pointant un fichier vide afin de désactiver les MCP RedAPI/SSTinfo (préservation de la diversité des sources, cf. memory `feedback_recherche_combo_kimi_codex`).
- Coût : $0 (CLI locaux/managed gratuits).

