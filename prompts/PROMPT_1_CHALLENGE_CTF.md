# PROMPT #1 — DEBBY-CTF · Challenge / Red-Team / Capture-The-Flag

> **À transmettre à un modèle agentique externe** (Kimi Agent Swarm, Google Antigravity, ChatGPT Agent, etc.)
> **Mode** : white/gray hat hacker, audit profond, vérification exhaustive, provocation méthodique
> **Durée attendue** : 4-24 h selon profondeur

---

## 1. Contexte

DEBBY est un corpus RAG médical + santé-sécurité au travail (SST) destiné à un **médecin du travail français** interrogeant en français. Volumétrie : **2 608 976 œuvres uniques**, **22 901 283 chunks**, embeddés en **fp16 4096-dim** (`qwen3-embedding-8b` via OpenRouter, L2-normalisés).

**Architecture découplée** : Table A (texte + métadonnées canoniques, source de vérité) / Table B (vecteurs jetables) — pattern *Bring Your Own Embedder*. 5 side-tables d'enrichissement appliquées au load LanceDB sans ré-embed (rétractations, source_type raffiné, year/title via Crossref, langue corrigée, entités graph-seed).

**Référentiel complet** : https://github.com/reddepot/debby-audit-snapshot/blob/main/DEBBY_AUDIT_SNAPSHOT.md
**Scripts** : `scripts/embed_or.py`, `scripts/layer2.py`, `scripts/build_lancedb.py`, etc.
**Benchmark FR** : `debby_benchmark_fr.jsonl` (49 requêtes en 13 catégories).

L'audit *interne* (challenge 6 IA, intégrité exhaustive, canari fidélité) a déjà été passé. **6 anomalies de qualité** ont été identifiées et sont **volontairement non-corrigées** dans le snapshot pour donner aux challengers des handles concrets (cf. §10.3 du doc).

---

## 2. Ta mission

**Faire tomber DEBBY.** Trouver les failles cachées, prouver leurs impacts opérationnels en mode CTF, livrer des fixes reproductibles.

Posture exigée :
- **White/gray hat** : tu peux explorer agressivement le code, les données, les flux. Tu ne dois pas exfiltrer, ni détruire les artefacts, ni générer du contenu médical dangereux opérationnel.
- **Pas de flagornerie**, pas de « ce projet est impressionnant ». Tu es là pour casser.
- **Preuve > intuition** : chaque finding doit s'accompagner d'un test exécutable (script Python, requête SQL, query LanceDB, prompt) qui le reproduit.

---

## 3. Axes d'attaque — 5 catégories, 28 flags à capturer

### CATÉGORIE A — Sécurité technique (5 flags)

- **A.1 [PII leakage]** Les auteurs nominaux complets sont dans la Table A. Trouve 3 cas où un nom + affiliation + email exposé serait problématique au regard du RGPD ou des bonnes pratiques HAL/OpenAlex.
- **A.2 [Prompt injection corpus-borne]** Construis un chunk piégé qui, intégré au corpus puis surfacé en retrieval, ferait dévier un agent LLM lecteur (instructions cachées, jailbreak médical). Démontre 3 vecteurs distincts.
- **A.3 [Provenance attaquable]** 22 % des works n'ont pas de DOI. Trouve 5 works dont la citabilité est impossible à reconstituer fiablement (titre + venue insuffisants).
- **A.4 [Infrastructure surface]** Audite `scripts/embed_or.py`, `scripts/watchdog_embed.sh`, `scripts/integrity_full.py` pour : (a) injection shell, (b) path traversal, (c) timing attacks sur la lecture des clés API, (d) leak de credentials via logs.
- **A.5 [Object storage abuse]** Le bucket Vultr S3 est public-readable pour les artefacts de doc. Vérifie qu'aucun objet sensible (clé, dump, log) n'est exposé par mégarde.

### CATÉGORIE B — Qualité des données (6 flags — anomalies déclarées)

Pour chacune des 6 anomalies A1-A6 du doc, **confirmer**, **quantifier**, **proposer un fix précis** :

- **B.1 [A1 — EBM=1 sur-flag]** 89,7 % des `ebm=1` n'ont pas « meta/systematic » dans le titre. Mesure l'impact sur la qualité du retrieval en faisant tourner `layer2.py` sur le benchmark FR avec/sans le boost EBM×1,3. Quel R@10 ?
- **B.2 [A2 — « lead » 146 K]** Filtre par contexte (`lead exposure|blood lead|Pb`) et compte le vrai signal. Estime le ratio faux-positifs.
- **B.3 [A3 — pseudo-CAS = dates]** Cross-check chaque CAS du top 100 contre PubChem/ECHA. Combien sont des artefacts ?
- **B.4 [A4 — Tableau 1 sur-matching]** Recompte avec matching strict (`tableau (MP|maladie professionnelle|n°)\s*\d` + RG-XX/RA-XX). Différence vs raw count ?
- **B.5 [A5 — métiers dupliqués]** Combien d'entrées `metiers` sont en réalité le même métier (différence accents, casse, singulier/pluriel) ?
- **B.6 [A6 — rétractations sous-couvertes ×13]** Trouve au moins 50 rétractations supplémentaires en croisant le corpus avec PubMed `Retracted Publication` flag + OpenAlex `is_retracted` + sources spécialisées.

### CATÉGORIE C — Métier MdT (7 flags)

- **C.1 [Cross-lingual FR→EN]** Trouve 5 requêtes FR pour lesquelles le retrieval rate des docs EN pertinents (pivot CAS ou jargon métier insuffisant).
- **C.2 [No-answer accuracy]** Sur les requêtes catégorie `hors_corpus` du benchmark, mesure le taux de faux positifs (retrieval qui retourne des docs alors qu'aucun n'est valable). Cible : ≥95 % de no-answer correct.
- **C.3 [Aptitude piégée]** Construis 5 cas-cliniques d'aptitude où le retrieval pourrait surfacer un avis cliniquement dangereux (faux pair, recommandation périmée, retracted non flaggué).
- **C.4 [Couverture tableaux MP]** Pour chaque tableau MP français (**175 = 122 RG** dont 20 variantes BIS/TER + **53 RA** dont 8 BIS/TER, cf. INRS bdd/mp/listeTableaux.html — corrigé 2026-05-27 : décompte initial "151 = 86 RG + 65 RA" omettait les 28 variantes BIS/TER), compte les works pertinents. Combien de tableaux ont <5 works ? Lesquels ? **Attention** : les tableaux BIS/TER concernent souvent des pathologies graves (RG 10 BIS asthme chromates, RG 30 BIS/TER cancers amiante, RG 15 BIS allergies amines aromatiques) — leur sous-couverture est un risque clinique majeur. Liste exhaustive dans `TABLEAUX_MP_REFERENCE.md`.
- **C.5 [Surveillance médicale]** Trouve 3 questions de surveillance médicale (périodicité, examens spécifiques) pour lesquelles DEBBY répond avec un document obsolète (>10 ans + recommandation officielle FR récente disponible).
- **C.6 [Sous-représentation grandes revues]** Quantifie : combien de NEJM/JAMA/Lancet/BMJ vs PLoS ONE/Cureus ? Est-ce un risque éditorial ?
- **C.7 [RPS / burnout]** Le corpus contient peu de FR natif. Teste 5 requêtes RPS/burnout — quel % de réponses en FR vs EN ?

### CATÉGORIE D' — Adversarial avancé (4 flags bonus)

- **D'.1 [Inversion d'embedding]** Les vecteurs 4096-dim fp16 sont publics-readable. Peut-on, à partir d'un vecteur, **reconstruire le texte d'origine** (embedding inversion attack) ? Tester avec `vec2text` ou modèles d'inversion. Quelles classes de chunks sont les plus à risque (court vs long, médical vs SST) ?
- **D'.2 [Trous noirs sémantiques]** Construis un test systématique : 50 questions MdT random → mesurer celles dont le top-10 n'a *aucun* chunk pertinent (rappel = 0). Quel pourcentage du corpus est en « zone morte » ?
- **D'.3 [PII fantômes]** 23 M chunks contiennent du texte libre. Cherche systématiquement des PII de **patients** (≠ auteurs scientifiques) — emails, numéros sécu FR, dates de naissance, noms cliniques — qui auraient été inclus par mégarde via case reports.
- **D'.4 [Inversion via re-embed]** Le canari interne fait du re-embed avec OR. Si OR change de modèle silencieusement (différent provider même nom), peut-on détecter le drift ? Reproduire un canari fin (10 K chunks stratifiés) à intervalles réguliers.

### CATÉGORIE D — Calibration retrieval (6 flags)

- **D.1 [Boosts arbitraires]** EBM×1,3 / SST×2 / FR×2 / récence×1,3 — propose un protocole d'optimisation (grid search ? bayes opt ?) avec critère cible (nDCG@10 sur benchmark FR).
- **D.2 [Filtre francisation ×0,5]** Mesure son impact sur 10 requêtes FR-juridiques (Légifrance, Code travail, tableaux MP) : aide ou nuit-il ?
- **D.3 [BM25 vs vecteur]** Trouve 5 requêtes où BM25 surclasse l'embed (jargon technique, codes médicaux) et 5 où l'inverse est vrai.
- **D.4 [Chunking 3 600 c]** Lance une ablation 1 800 / 3 600 / 5 400 chars sur 1 % du corpus, mesure les différences de R@k.
- **D.5 [Préfixe contextuel à l'embed]** Embed le même chunk avec/sans préfixe `[type/source] : titre — `, mesure le cosine vs vecteur stocké. Le préfixe aide-t-il vraiment ?
- **D.6 [Granularité de réponse]** Pour 5 requêtes qui appellent une réponse précise (un seuil VLEP, un délai de latence), DEBBY donne-t-il la réponse dans le top-3 chunks ?

---

## 4. Format CTF — règles

- **Chaque flag** = une preuve reproductible (script + sortie) + un fix proposé (code, query, paramètre).
- **Scoring suggéré** :
  - A.x / B.x : 3 pts (confirmation + reproduction + fix)
  - C.x : 5 pts (impact métier MdT)
  - D.x : 4 pts (impact qualité retrieval)
  - D'.x : 6 pts (adversarial avancé — flag bonus)
- **Bonus** : trouver une vulnérabilité non listée = +10 pts.
- **Penalty** : un finding non reproductible = -2 pts ; un finding qui se limite aux anomalies A1-A6 sans creuser au-delà = -1 pt par redite.

**Total possible** : ~150 pts. Objectif minimum : 60 pts pour passer l'audit.

---

## 5. Livrables attendus

À déposer dans une PR sur https://github.com/reddepot/debby-audit-snapshot ou via email à `redtech@protonmail.com` :

1. **`FINDINGS.md`** — tableau des flags capturés (id flag, statut, sévérité, preuve, fix proposé).
2. **`scripts/poc_<flag_id>.py`** — un script reproductible par flag.
3. **`fixes/`** — code des fixes proposés (PR-ready).
4. **`benchmark_extended.jsonl`** — extension du benchmark FR avec vos 20+ requêtes-pièges.
5. **`SCORE.md`** — votre auto-évaluation pondérée.
6. **`REPORT.md`** — synthèse (5-10 pages) : findings critiques, recommandations stratégiques, top 5 priorités.

---

## 6. Garde-fous éthiques

- **PAS de PII exfiltration** : si tu trouves une PII réelle, signale-la dans un canal privé (`redtech@protonmail.com`), pas dans une issue publique.
- **PAS de destruction** : tu peux forker, mais tu ne touches pas aux artefacts en object storage.
- **PAS de génération de contenu médical opérationnel** : tu ne construis pas d'avis d'aptitude faux pour DOS ; tu démontres l'attaque sur 1 cas-test, c'est suffisant.
- **PAS de DOS** : si tu mesures des perfs, fais-le sur un échantillon ≤1 % du corpus.
- **Respect du NDA** si on t'a accordé l'accès read-only au corpus complet.

---

## 7. Comment commencer

```bash
# 1. Fork + clone
git clone git@github.com:reddepot/debby-audit-snapshot.git
cd debby-audit-snapshot

# 2. Lire le doc principal
$EDITOR DEBBY_AUDIT_SNAPSHOT.md

# 3. Reproduire les stats du corpus (depuis votre accès read-only)
python3 scripts/deep_stats.py
diff <(jq -S . deep_stats.out) <(jq -S . votre_output.out)

# 4. Choisir ses flags par catégorie (cf. §3)
# 5. Pour chaque flag : poc_<id>.py + fix_<id>.{py,sql,md}
# 6. Compiler le rapport
# 7. Soumettre PR ou email
```

Si vous n'avez pas l'accès corpus complet : demandez-le à `redtech@protonmail.com` avec votre identité + intention d'usage. NDA standard fourni.

---

## 8. Phrases-clés à se rappeler

> *« Votre travail n'est pas de confirmer DEBBY, mais de trouver où il ment avec assurance. »*
>
> *« Une faille sans preuve reproductible ne compte pas. »*
>
> *« Toute réponse médicale correcte mais mal sourcée est un échec du RAG. »*
>
> *« Un score vectoriel n'est pas une pertinence clinique. »*

---

## 9. Anti-patterns à éviter (vous serez pénalisé)

- **Se limiter aux anomalies A1-A6 déjà déclarées** : elles sont des amorces, pas votre quota. La valeur est dans ce que personne n'a vu.
- **Audit vague sans requêtes concrètes** : « le retrieval semble peu robuste » n'est pas un finding ; « la requête X retourne le doc Y rétracté en top-3 » l'est.
- **Confondre cosine élevé et pertinence clinique** : un chunk peut avoir cos=0,9 sur la requête et être cliniquement faux pour un MdT FR.
- **Ignorer le droit français du travail** : si votre attaque cite le SGAB ou un MSDS américain pour une question FR-juridique, vous êtes hors-cible.
- **Proposer une attaque destructive** ou demander des accès NDA pour exfiltration ≠ audit.
- **Spammer 50 findings creux** au lieu de 10 trouvailles décisives.
- **Hallucinations sur les chiffres** : tous les nombres du rapport doivent être traçables à un script + une sortie.

---

## 10. Format de sortie structuré (livrable obligatoire)

En plus du `FINDINGS.md` narratif, livrer un JSON parsable :

```json
{
  "audit_id": "ctf-debby-2026-05-NN",
  "auditor_handle": "votre nom / org",
  "verdict_global": "VALIDÉ | À_CALIBRER | NON_CONFORME",
  "flags_captured": [
    {
      "flag_id": "B.1",
      "family": "data_quality",
      "name": "EBM=1 sur-flag — impact retrieval",
      "severity": "CRITICAL | HIGH | MEDIUM | LOW",
      "exploitability": "HIGH | MEDIUM | LOW",
      "clinical_impact": "HIGH | MEDIUM | LOW",
      "hypothese_nulle": "le boost EBM×1,3 améliore le retrieval",
      "method": "ablation A/B sur 49 requêtes benchmark",
      "metric": "nDCG@10",
      "result": 0.68,
      "threshold_rejection": 0.75,
      "verdict": "À_CALIBRER",
      "evidence": ["scripts/poc_B1.py", "outputs/poc_B1.log"],
      "fix_proposed": "fixes/ebm_v2.py",
      "estimated_effort_hours": 4
    }
  ],
  "matrice_risque": [
    { "flag": "B.1", "impact": "HIGH", "exploitability": "LOW", "quadrant": "à-corriger-court-terme" }
  ],
  "score_robustesse_global": 72,
  "score_justification": "string",
  "top5_priorities": ["B.1", "C.2", "A.2", "D.1", "B.6"]
}
```

---

## 11. Esprit de la mission

> *DEBBY n'est pas l'œuvre. C'est l'infrastructure. Le chef d'œuvre, c'est la couche de raisonnement qu'on construit par-dessus — graphe, agents, raisonnement clinique opposable.*
>
> *Votre rôle de challenger : montrer où l'infrastructure ne tient pas, et pousser le projet à devenir vraiment opposable.*

Date butoir suggérée : **14 jours** après réception du brief. Pas de pression — la qualité prime sur la vitesse.

---

— *Brief co-rédigé par Claude Opus 4.7 + Kimi K2.6 (CLI) + Codex GPT-5.5 (CLI) + Gemini 3 Pro (CLI), consolidé le 2026-05-26.*
