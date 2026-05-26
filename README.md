# DEBBY Audit Snapshot

> **Snapshot public** d'un corpus RAG médical + santé-sécurité au travail (SST), conçu pour permettre un **audit de challenge externe** par des IA agentiques, équipes red-team ou reviewers humains.

## En 30 secondes

- **2 608 976 œuvres uniques** · **22 901 283 chunks**
- Embeddés en **fp16 4096-dim** (`qwen3-embedding-8b` via OpenRouter, L2-normalisés)
- Architecture **découplée Table A (texte+métadonnées canoniques) / Table B (vecteurs jetables)** — pattern *Bring Your Own Embedder*
- **5 side-tables d'enrichissement** appliquées au load sans ré-embed
- **Audits passés** : intégrité exhaustive, fidélité texte↔vecteur (canari cos médian 0,9999), sanity retrieval, challenge 6 IA
- **Anomalies de qualité identifiées et listées** pour le challenger (cf. §10.3 du doc principal)

## Contenu du repo

```
debby-audit-snapshot/
├── DEBBY_AUDIT_SNAPSHOT.md     ← Le document principal (référentiel complet ~50 Ko)
├── README.md                    ← Ce fichier
├── deep_stats.out               ← Sortie brute de l'analyse profonde 2026-05-26
├── debby_benchmark_fr.jsonl     ← 49 requêtes FR MdT pour évaluer le retrieval
├── prompts/                     ← Prompts agentiques copy-paste-ready
│   ├── README.md                ←   Orientation : quel prompt pour quel usage
│   ├── PROMPT_1_CHALLENGE_CTF.md         ←   Challenge / Red-team / CTF (28 flags)
│   └── PROMPT_2_AMELIORATION_CONTINUE.md ←   Roadmap / Architecture / Prospective
└── scripts/                     ← Code source de l'embed + audits + Couche 2
    ├── embed_or.py              ← Producteur OpenRouter (avec correctif remote_has size>0)
    ├── watchdog_embed.sh        ← Recyclage anti-OOM pendant l'embed
    ├── integrity_full.py        ← Audit footers parquet via pyarrow S3
    ├── canari_reembed.py        ← Vérif fidélité texte↔vecteur (re-embed échantillon)
    ├── retrieval_sanity.py      ← Sanity check brute-force sans LanceDB
    ├── truncation_audit.py      ← Audit des chunks tronqués à 4000 octets
    ├── extract_samples.py       ← Échantillons illustratifs par source_type
    ├── deep_stats.py            ← Analyse profonde (le script qui a produit deep_stats.out)
    ├── body_lang_v2.py          ← Correction langue détectée (streaming memory-safe)
    ├── build_lancedb.py         ← Load Table A + B + side-tables → LanceDB IVF_PQ Matryoshka
    ├── layer2.py                ← Couche 2 retrieval — hybride BM25+vecteur, boosts, francisation, pivot CAS
    └── eval_benchmark.py        ← Harness d'éval sur le benchmark FR (49 requêtes)
```

## 🎯 Pour les modèles agentiques externes

Si vous arrivez sur ce repo en tant que **modèle agentique** (Kimi Agent Swarm, Antigravity, ChatGPT Agent, etc.), lisez :

- **`prompts/PROMPT_1_CHALLENGE_CTF.md`** si on vous a missionné pour **casser DEBBY** (CTF, red-team, audit profond).
- **`prompts/PROMPT_2_AMELIORATION_CONTINUE.md`** si on vous a missionné pour **faire évoluer DEBBY** (roadmap, GraphRAG, agentification, fine-tuning).
- **`prompts/README.md`** pour orienter votre choix.

Les 2 prompts sont co-rédigés par Claude Opus 4.7 + Kimi K2.6 + Codex GPT-5.5 + Gemini 3 Pro (consolidé 2026-05-26).

## Comment l'auditer

### Lecture rapide
Lire `DEBBY_AUDIT_SNAPSHOT.md` (§TL;DR puis §11 « Axes d'audit ouverts pour le challenger »).

### Audit ciblé
Les sections §10.3 (« anomalies non corrigées et listées pour le challenger ») et §11 fournissent des handles concrets — 24 axes ouverts numérotés.

### Audit profond
1. Forker le repo
2. Auditer `scripts/layer2.py` (la Couche 2 retrieval — c'est là que la valeur métier MdT se joue)
3. Auditer `scripts/build_lancedb.py` (la jointure side-tables avant load LanceDB)
4. Reproduire les stats via `deep_stats.py` (le corpus n'est pas distribué ici mais accessible sous NDA pour un audit lourd)
5. Ouvrir une issue avec votre constat + preuve reproductible

### Audit adversarial / red-team
Cf. §11.4 — axes spécifiques (prompt injection via corpus, PII leakage, provenance attaquable).

## Configuration des scripts

Tous les scripts lisent leurs credentials depuis des fichiers locaux (pas de hardcode) :

- **OpenRouter API key** : `/root/or.key` (ou variable d'env, configurable en haut de chaque script)
- **Vultr S3 (rclone)** : `~/.config/rclone/rclone.conf` section `meddata` avec `access_key_id`, `secret_access_key`, `endpoint = ams1.vultrobjects.com`, `region = us-east-1`

Aucune clé n'est embarquée dans le repo (vérifié par scan secrets avant push).

## Contraintes de reproduction

- Le **corpus complet** (Table A + B + side-tables, ~180 Go) n'est PAS dans ce repo. Il est en object storage Vultr S3 (`meddata-lake/debby_embed/`).
- L'auditeur sous NDA peut demander un accès lecture-seule (read-only credentials par IP) à `redtech@protonmail.com`.
- Les scripts fonctionnent sur **n'importe quel hub Linux ≥16 Go RAM** avec Python 3.11+ et `pyarrow`, `numpy`, `rclone`, `langdetect`.

## Antécédents

Le pattern d'audit publié ici suit celui de [`reddepot/polybuild-audit-snapshot`](https://github.com/reddepot/polybuild-audit-snapshot) (publié en mai 2026 pour le projet POLYBUILD).

## Licence

- **Documentation** (`README.md`, `DEBBY_AUDIT_SNAPSHOT.md`) : CC BY-SA 4.0
- **Code** (`scripts/`) : MIT (réutilisation libre, attribution appréciée)
- **Corpus** : non distribué — usage interne MdT + audit sous NDA

## Contact

`redtech@protonmail.com` — Radu, médecin du travail (SPSTI ASSTV86, Vienne FR)

---

*Ce snapshot a été généré le 2026-05-26 par Claude Opus 4.7 orchestré par Radu. Si vous trouvez une faille ou une anomalie, ouvrez une issue — c'est le but du repo.*
