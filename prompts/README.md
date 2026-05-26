# Prompts agentiques DEBBY

Deux prompts copy-paste-ready à transmettre à des **modèles agentiques externes** (Kimi Agent Swarm, Google Antigravity, ChatGPT Agent, Manus, etc.) pour challenger ou faire évoluer DEBBY.

Co-rédigés par 4 voix : **Claude Opus 4.7** (orchestrateur) + **Kimi K2.6** (CLI) + **Codex GPT-5.5** (CLI) + **Gemini 3 Pro** (CLI). Consolidation 2026-05-26.

---

## Quel prompt pour quel usage ?

| Vous voulez… | Utilisez |
|---|---|
| Trouver les failles, casser DEBBY, prouver les anomalies, capturer des flags CTF | **`PROMPT_1_CHALLENGE_CTF.md`** |
| Faire évoluer DEBBY, proposer roadmap, GraphRAG, agentification, fine-tuning | **`PROMPT_2_AMELIORATION_CONTINUE.md`** |
| Les deux en cascade | Prompt 1 d'abord (capture flags), puis Prompt 2 pour les fixer + aller au-delà |

---

## Comment les utiliser

### Avec Kimi Agent Swarm

```bash
# Tu fournis à l'agent le repo cloné + le prompt
git clone git@github.com:reddepot/debby-audit-snapshot.git
cd debby-audit-snapshot
kimi --agent-swarm --workdir . -p "$(cat prompts/PROMPT_1_CHALLENGE_CTF.md)"
```

### Avec ChatGPT Agent / Antigravity

Copier-coller le contenu du prompt dans l'interface agent + uploader le repo (ou pointer son URL).

### Avec Claude Code en mode autonome

```bash
claude code -p "$(cat prompts/PROMPT_1_CHALLENGE_CTF.md)" --workdir .
```

---

## Différences clés entre les 2 prompts

| Dimension | Prompt 1 (CTF) | Prompt 2 (Evolve) |
|---|---|---|
| **Posture** | White/gray hat hacker | Architecte senior + visionary |
| **Objectif** | Prouver la fragilité | Proposer le progrès |
| **Métriques** | Taux de succès attaques, gravité, exploitabilité | Impact × effort × risque + nDCG/MRR/groundedness |
| **Output** | FINDINGS.md + JSON flags + PoCs | ROADMAP.md + JSON chantiers + 3 PoCs minimum |
| **Durée** | 14 jours | 30 jours (ROADMAP) + 90 jours (PoCs) |
| **Phrase-clé** | « Trouver où DEBBY ment avec assurance » | « Augmenter la confiance mesurable » |

---

## Contributions par voix consultée

- **Kimi K2.6** — verdict ternaire ✅/⚠️/❌, JSON structuré, template d'attaque CVSS qualitatif, matrice de risque Impact×Exploitabilité, 7 familles d'attaques red-team.
- **Codex GPT-5.5** — phrases-clés directes (« trouver où il ment avec assurance », « DEBBY doit savoir dire non, citer juste, et expliquer pourquoi »), anti-patterns ciselés, focus opposabilité MdT FR.
- **Gemini 3 Pro** — angle inversion d'embedding, trous noirs sémantiques, PII fantômes patients, GraphRAG avec ontologie médicale formelle, agentic retrieval itératif.
- **Claude Opus 4.7** — orchestration, consolidation, structure 11 sections, garde-fous éthiques.

---

## Garde-fous (les 2 prompts)

- **PAS de PII exfiltration** : signaler en privé (`redtech@protonmail.com`).
- **PAS de destruction** : fork OK, mais pas de write sur l'object storage.
- **PAS de génération médicale opérationnelle dangereuse**.
- **NDA standard** pour accéder au corpus complet.

---

## Feedback

Si vous utilisez ces prompts et obtenez des résultats intéressants, ouvrez une issue ou PR sur le repo principal. Les meilleurs livrables seront référencés ici comme exemples.
