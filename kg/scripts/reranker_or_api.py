#!/usr/bin/env python3
"""B3 — Re-ranker production via OpenRouter API on-demand (économique).

Pattern décidé par Reddie 2026-05-27 : pas de GPU dédié continu ; appel API OR
à chaque requête réelle (~$0.001-0.005 par requête de retrieval).

Usage standalone (test) :
    python3 reranker_or_api.py --query "amiante mésothéliome" --chunks chunk1.txt chunk2.txt chunk3.txt

Usage intégration (depuis layer2.py futur) :
    from reranker_or_api import rerank_with_openrouter
    top_k = rerank_with_openrouter(query, candidates, top_k=10)

Modèles supportés (à jour 2026-05-27 OR catalog) :
- qwen/qwen3-reranker-8b (Apache 2.0, MMTEB-R 72.94, recommandation Perplexity DR)
- (fallback) BGE-reranker-v2-m3 si Qwen3 indispo
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

try:
    import httpx
except ImportError:
    sys.exit("httpx requis: pip install httpx")

# Charger clé OpenRouter depuis canonical location
KEY_FILE = Path.home() / "Developer" / "projects" / "mcp_redapi" / "env" / "ai-keys.env"
DEFAULT_MODEL = "qwen/qwen3.7-max"  # LLM chat pour rerank (qwen3-reranker-8b non exposé via /chat/completions sur OR)
FALLBACK_MODEL = "google/gemini-3.1-pro-preview"  # si Qwen3 max indispo
# Note: Pour vrai reranker dédié (Qwen3-Reranker-8B Apache 2.0), self-host requis
# (HuggingFace + FlagEmbedding + GPU). Coût compute ~$5-10/mois si volume <100K req/mois.
# L'approche LLM-judge via OR est pragmatique pour volume <30K req/mois (~$10-30/mois).
OR_BASE = "https://openrouter.ai/api/v1"


def load_or_key() -> str:
    """Lit la clé OpenRouter depuis le fichier dotenv canonique."""
    if not KEY_FILE.is_file():
        raise FileNotFoundError(f"Clé OpenRouter introuvable : {KEY_FILE}")
    for line in KEY_FILE.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise ValueError(f"OPENROUTER_API_KEY non trouvé dans {KEY_FILE}")


def rerank_with_openrouter(
    query: str,
    candidates: list[str],
    top_k: int = 10,
    model: str = DEFAULT_MODEL,
    api_key: Optional[str] = None,
    timeout_s: float = 30.0,
) -> list[tuple[int, float, str]]:
    """Re-rank candidates via OpenRouter API.

    Args:
        query: requête utilisateur (FR ou EN)
        candidates: liste de textes candidats (chunks LanceDB top-50)
        top_k: nombre de candidats à retourner (typique 10)
        model: modèle OR (défaut qwen/qwen3-reranker-8b)
        api_key: clé OR (défaut: depuis dotenv)
        timeout_s: timeout HTTP par requête

    Returns:
        liste de (idx_candidate, score, text) triée score décroissant, len = top_k

    Coût estimé:
        - ~$0.001 par requête de rerank 50 candidats (Qwen3-Reranker-8B via OR)
        - Total ~$10-30/mois si 30 000 requêtes (10 par jour × 30 j × 100 internes)
    """
    if api_key is None:
        api_key = os.environ.get("OPENROUTER_API_KEY") or load_or_key()

    if not candidates:
        return []

    # NOTE: OR n'expose pas (encore) une route /rerank standard.
    # Pour Qwen3-Reranker-8B, on simule le rerank via chat completion :
    # prompt = "Document is relevant to the query? Answer 'yes' or 'no'" → score = P(yes)
    # C'est moins efficace qu'un vrai endpoint /rerank mais ça marche.
    # Alternative production : self-hosting Jina v2 ou BGE local si volume justifie.

    scored = []
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://reddie.ovh",
        "X-Title": "DEBBY reranker on-demand",
    }

    t0 = time.time()
    with httpx.Client(timeout=timeout_s) as client:
        for i, cand in enumerate(candidates):
            prompt_msg = [
                {
                    "role": "system",
                    "content": (
                        "Tu es un évaluateur de pertinence. Réponds UNIQUEMENT par 'yes' ou 'no'. "
                        "Le document fourni est-il pertinent pour répondre à la requête utilisateur ?"
                    ),
                },
                {
                    "role": "user",
                    "content": f"Requête : {query}\n\nDocument :\n{cand[:1500]}\n\nLe document est-il pertinent ? Réponds yes ou no.",
                },
            ]
            try:
                r = client.post(
                    f"{OR_BASE}/chat/completions",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": prompt_msg,
                        "max_tokens": 5,
                        "temperature": 0,
                        "logprobs": True,
                        "top_logprobs": 5,
                    },
                )
                r.raise_for_status()
                data = r.json()
                # Extraire logprob de "yes" si dispo, sinon contenu réponse
                choice = data["choices"][0]
                msg_content = choice["message"]["content"].strip().lower()
                # Score binaire pragmatique : 1.0 si yes, 0.0 si no, 0.5 sinon
                if "yes" in msg_content[:5]:
                    score = 1.0
                elif "no" in msg_content[:5]:
                    score = 0.0
                else:
                    score = 0.5
                # Si logprobs dispos, raffine
                if choice.get("logprobs") and choice["logprobs"].get("content"):
                    for token_info in choice["logprobs"]["content"]:
                        for top in token_info.get("top_logprobs", []):
                            if top["token"].strip().lower() == "yes":
                                # logprob → probabilité
                                import math
                                score = math.exp(top["logprob"])
                                break
                        if score not in (0.0, 0.5, 1.0):
                            break
                scored.append((i, score, cand))
            except Exception as e:
                print(f"  ⚠️ Candidate {i} failed: {e}", file=sys.stderr)
                scored.append((i, 0.0, cand))

    scored.sort(key=lambda x: x[1], reverse=True)
    elapsed = time.time() - t0
    print(f"Re-ranked {len(candidates)} candidates in {elapsed:.1f}s (model={model})", file=sys.stderr)

    return scored[:top_k]


def main():
    ap = argparse.ArgumentParser(description="Re-ranker production via OpenRouter API")
    ap.add_argument("--query", required=True, help="Requête utilisateur")
    ap.add_argument("--chunks", nargs="+", required=True, help="Fichiers texte ou strings de candidats")
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    args = ap.parse_args()

    # Load candidates (file paths or raw strings)
    candidates = []
    for c in args.chunks:
        p = Path(c)
        if p.is_file():
            candidates.append(p.read_text(encoding="utf-8"))
        else:
            candidates.append(c)

    results = rerank_with_openrouter(args.query, candidates, top_k=args.top_k, model=args.model)
    print(json.dumps(
        [{"rank": i + 1, "idx": idx, "score": round(score, 4), "preview": text[:150]} for i, (idx, score, text) in enumerate(results)],
        indent=2,
        ensure_ascii=False,
    ))


if __name__ == "__main__":
    main()
