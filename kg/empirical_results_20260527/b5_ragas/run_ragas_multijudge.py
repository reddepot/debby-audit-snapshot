#!/usr/bin/env python3
"""
B5 RAGAS multi-juge orchestrator
================================

Évalue 15 requêtes du benchmark FR DEBBY × 3 CLI juges (kimi, codex, gemini)
sur 3 dimensions RAGAS : faithfulness, answer_relevance, context_precision.

Sorties :
- results.json (raw + agrégé)
- raw_responses.jsonl (réponses brutes de chaque appel)
- REPORT.md (tableau + analyse)

Usage :
    python3 run_ragas_multijudge.py [--queries N] [--judges j1,j2,...] [--dry-run]
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import re
import statistics
import subprocess
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
PAYLOAD = BASE_DIR / "payload.json"
RESULTS = BASE_DIR / "results.json"
RAW = BASE_DIR / "raw_responses.jsonl"
REPORT = BASE_DIR / "REPORT.md"
NO_MCP_CONFIG = Path("/tmp/no_mcp_ragas.json")

GTIMEOUT = "/opt/homebrew/bin/gtimeout"

# Per-CLI timeout in seconds (codex GPT-5.5 reasoning is slow)
CLI_TIMEOUT = {
    "kimi": 90,
    "codex": 180,
    "gemini": 120,
}

MAX_RETRIES = 3

PROMPT_TEMPLATE = """Tu es un évaluateur RAG médical SST. Évalue la qualité du retrieval pour la requête suivante.

REQUÊTE : {query}
CATÉGORIE : {category}

TOP-3 CHUNKS RETROUVÉS :
1. {title_1}
{text_1}

2. {title_2}
{text_2}

3. {title_3}
{text_3}

Évalue les 3 dimensions RAGAS, scores entre 0.0 et 1.0 (3 décimales), avec 1 phrase de justification par dimension :
- faithfulness : si on construisait une réponse à partir de ces chunks, serait-elle fidèle aux sources ?
- answer_relevance : ces chunks permettent-ils de répondre à la requête ?
- context_precision : tous les chunks sont-ils pertinents (pas de bruit) ?

Retourne UNIQUEMENT un JSON strict, sans markdown, sans bloc de code, sans texte avant/après :
{{"faithfulness": 0.000, "answer_relevance": 0.000, "context_precision": 0.000, "comment_faithfulness": "...", "comment_relevance": "...", "comment_precision": "..."}}"""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class CLIResponse:
    judge: str
    query_id: str
    success: bool
    raw_stdout: str
    raw_stderr: str
    duration_s: float
    attempt: int
    parsed: dict[str, Any] | None = None
    parse_error: str | None = None
    return_code: int | None = None


# ---------------------------------------------------------------------------
# CLI calls
# ---------------------------------------------------------------------------


def build_prompt(query: dict[str, Any]) -> str:
    chunks = query.get("top3_chunks", [])
    # pad if fewer than 3
    while len(chunks) < 3:
        chunks.append({"title": "(absent)", "text": "(absent)"})
    return PROMPT_TEMPLATE.format(
        query=query["query"],
        category=query["category"],
        title_1=chunks[0].get("title", "(sans titre)"),
        text_1=chunks[0].get("text", "(vide)"),
        title_2=chunks[1].get("title", "(sans titre)"),
        text_2=chunks[1].get("text", "(vide)"),
        title_3=chunks[2].get("title", "(sans titre)"),
        text_3=chunks[2].get("text", "(vide)"),
    )


def _ensure_no_mcp_config() -> None:
    if not NO_MCP_CONFIG.exists():
        NO_MCP_CONFIG.write_text(json.dumps({"mcpServers": {}}))


def run_cli(judge: str, prompt: str, query_id: str, attempt: int) -> CLIResponse:
    _ensure_no_mcp_config()
    timeout_s = CLI_TIMEOUT.get(judge, 90)
    start = time.monotonic()
    try:
        if judge == "kimi":
            cmd = [
                GTIMEOUT,
                str(timeout_s + 10),
                "kimi",
                "--print",
                "--quiet",
                "--mcp-config-file",
                str(NO_MCP_CONFIG),
                "--prompt",
                prompt,
            ]
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout_s + 15
            )
        elif judge == "codex":
            # codex exec writes the final reply at the very end of stdout
            cmd = [
                GTIMEOUT,
                str(timeout_s + 10),
                "codex",
                "exec",
                "--skip-git-repo-check",
                "--color",
                "never",
                prompt,
            ]
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout_s + 15
            )
        elif judge == "gemini":
            cmd = [
                GTIMEOUT,
                str(timeout_s + 10),
                "gemini",
                "-p",
                prompt,
            ]
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout_s + 15
            )
        else:
            return CLIResponse(
                judge=judge,
                query_id=query_id,
                success=False,
                raw_stdout="",
                raw_stderr=f"unknown judge: {judge}",
                duration_s=0.0,
                attempt=attempt,
                parse_error="unknown judge",
            )

        elapsed = time.monotonic() - start
        return CLIResponse(
            judge=judge,
            query_id=query_id,
            success=(proc.returncode == 0),
            raw_stdout=proc.stdout,
            raw_stderr=proc.stderr,
            duration_s=elapsed,
            attempt=attempt,
            return_code=proc.returncode,
        )

    except subprocess.TimeoutExpired as e:
        return CLIResponse(
            judge=judge,
            query_id=query_id,
            success=False,
            raw_stdout=(e.stdout or "") if isinstance(e.stdout, str) else "",
            raw_stderr=f"TIMEOUT after {timeout_s}s",
            duration_s=time.monotonic() - start,
            attempt=attempt,
            parse_error="timeout",
        )
    except Exception as e:  # noqa: BLE001
        return CLIResponse(
            judge=judge,
            query_id=query_id,
            success=False,
            raw_stdout="",
            raw_stderr=str(e),
            duration_s=time.monotonic() - start,
            attempt=attempt,
            parse_error=f"exception: {type(e).__name__}",
        )


# ---------------------------------------------------------------------------
# JSON extraction (each CLI wraps the JSON differently)
# ---------------------------------------------------------------------------


_FIELDS_REQUIRED = ("faithfulness", "answer_relevance", "context_precision")


def _try_parse(s: str) -> dict[str, Any] | None:
    try:
        d = json.loads(s)
    except Exception:
        return None
    if not isinstance(d, dict):
        return None
    if not all(k in d for k in _FIELDS_REQUIRED):
        return None
    return d


def extract_json(judge: str, stdout: str) -> tuple[dict[str, Any] | None, str | None]:
    """Pull the RAGAS JSON object out of a CLI's noisy stdout."""
    if not stdout:
        return None, "empty stdout"

    text = stdout

    # Strip codex tail like "tokens used\n22,211" and the codex preamble lines.
    # For codex, the actual reply lies between the last "codex" line and "tokens used"
    if judge == "codex":
        # The cleanest substring: between a line containing only "codex" and "tokens used"
        m = re.search(r"\bcodex\b\s*\n(.*?)\n\s*tokens used", text, re.DOTALL)
        if m:
            text = m.group(1).strip()
        else:
            # fallback: take whatever comes after the last "codex" header line
            parts = re.split(r"^codex\s*$", text, flags=re.MULTILINE)
            if len(parts) > 1:
                text = parts[-1].strip()
                text = re.split(r"\btokens used\b", text)[0].strip()

    # Strip kimi tail "To resume this session: kimi -r ..."
    text = re.sub(r"\nTo resume this session:.*$", "", text, flags=re.DOTALL).strip()

    # Strip markdown code fences
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())

    # 1) try as-is
    parsed = _try_parse(text.strip())
    if parsed:
        return parsed, None

    # 2) extract every {...} block (greedy), try from longest to shortest
    candidates = []
    # Use a simple brace matcher
    depth = 0
    start = -1
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and start >= 0:
                    candidates.append(text[start : i + 1])
                    start = -1

    candidates.sort(key=len, reverse=True)
    for cand in candidates:
        parsed = _try_parse(cand)
        if parsed:
            return parsed, None

    # 3) line-by-line fallback (in case judge spat a json line surrounded by prose)
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            parsed = _try_parse(line)
            if parsed:
                return parsed, None

    return None, "no valid RAGAS JSON found"


# ---------------------------------------------------------------------------
# Per-query runner
# ---------------------------------------------------------------------------


def evaluate_query(
    query: dict[str, Any], judges: list[str], raw_fp
) -> dict[str, Any]:
    qid = query["id"]
    prompt = build_prompt(query)

    per_judge: dict[str, dict[str, Any] | None] = {}

    # Run all judges in parallel for this query
    with cf.ThreadPoolExecutor(max_workers=len(judges)) as pool:
        futures = {}
        for judge in judges:
            futures[pool.submit(_run_with_retry, judge, prompt, qid, raw_fp)] = judge

        for fut in cf.as_completed(futures):
            judge = futures[fut]
            try:
                per_judge[judge] = fut.result()
            except Exception as e:  # noqa: BLE001
                per_judge[judge] = {"error": str(e)}

    # Aggregate
    agg = aggregate(per_judge)
    return {
        "id": qid,
        "category": query["category"],
        "query": query["query"],
        "judges": per_judge,
        "aggregate": agg,
    }


def _run_with_retry(
    judge: str, prompt: str, qid: str, raw_fp
) -> dict[str, Any]:
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        resp = run_cli(judge, prompt, qid, attempt)
        if resp.success and resp.raw_stdout:
            parsed, perr = extract_json(judge, resp.raw_stdout)
            resp.parsed = parsed
            resp.parse_error = perr
            # log
            raw_fp.write(json.dumps(asdict(resp), ensure_ascii=False) + "\n")
            raw_fp.flush()
            if parsed:
                return {
                    "attempt": attempt,
                    "duration_s": round(resp.duration_s, 2),
                    "faithfulness": parsed.get("faithfulness"),
                    "answer_relevance": parsed.get("answer_relevance"),
                    "context_precision": parsed.get("context_precision"),
                    "comment_faithfulness": parsed.get("comment_faithfulness", ""),
                    "comment_relevance": parsed.get("comment_relevance", ""),
                    "comment_precision": parsed.get("comment_precision", ""),
                }
            last_error = perr or "parse failed"
        else:
            raw_fp.write(json.dumps(asdict(resp), ensure_ascii=False) + "\n")
            raw_fp.flush()
            last_error = resp.parse_error or resp.raw_stderr[:200]
        # back-off briefly
        time.sleep(2 * attempt)
    return {"error": last_error or "unknown failure", "attempts": MAX_RETRIES}


def aggregate(per_judge: dict[str, dict[str, Any] | None]) -> dict[str, Any]:
    dims = ["faithfulness", "answer_relevance", "context_precision"]
    out: dict[str, Any] = {"voices": 0, "errors": [], "by_dim": {}}
    valid_scores: dict[str, list[float]] = {d: [] for d in dims}
    valid_voices = 0
    for judge, res in per_judge.items():
        if not res or res.get("error") or any(res.get(d) is None for d in dims):
            out["errors"].append({"judge": judge, "err": (res or {}).get("error", "no scores")})
            continue
        ok = True
        per_dim: dict[str, float] = {}
        for d in dims:
            v = res.get(d)
            try:
                fv = float(v)
                if not (0.0 <= fv <= 1.0):
                    ok = False
                    break
                per_dim[d] = fv
            except Exception:
                ok = False
                break
        if not ok:
            out["errors"].append({"judge": judge, "err": "non-numeric or out of range"})
            continue
        for d, fv in per_dim.items():
            valid_scores[d].append(fv)
        valid_voices += 1

    out["voices"] = valid_voices
    for d in dims:
        scores = valid_scores[d]
        if scores:
            mean = statistics.fmean(scores)
            stdev = statistics.stdev(scores) if len(scores) >= 2 else 0.0
            out["by_dim"][d] = {
                "mean": round(mean, 3),
                "stdev": round(stdev, 3),
                "n": len(scores),
                "scores": [round(x, 3) for x in scores],
            }
        else:
            out["by_dim"][d] = {"mean": None, "stdev": None, "n": 0, "scores": []}
    return out


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def build_global_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    dims = ["faithfulness", "answer_relevance", "context_precision"]
    judges = sorted({j for r in rows for j in r["judges"].keys()})

    # global mean per dim (mean of means)
    global_means: dict[str, float] = {}
    global_voices_per_dim: dict[str, int] = {d: 0 for d in dims}
    per_judge_means: dict[str, dict[str, list[float]]] = {
        j: {d: [] for d in dims} for j in judges
    }
    div_alerts: list[dict[str, Any]] = []

    for r in rows:
        for d in dims:
            agg = r["aggregate"]["by_dim"].get(d, {})
            if agg.get("mean") is not None:
                global_voices_per_dim[d] += agg.get("n", 0)
                # collect for global mean
                global_means.setdefault(d, [])
                global_means[d].append(agg["mean"])  # type: ignore[arg-type]
            if (agg.get("stdev") or 0.0) > 0.2 and agg.get("n", 0) >= 2:
                div_alerts.append(
                    {
                        "id": r["id"],
                        "dim": d,
                        "stdev": agg["stdev"],
                        "scores": agg.get("scores", []),
                    }
                )

        for j in judges:
            jres = r["judges"].get(j, {}) or {}
            if jres.get("error"):
                continue
            for d in dims:
                v = jres.get(d)
                try:
                    per_judge_means[j][d].append(float(v))
                except Exception:
                    continue

    g_means_final: dict[str, dict[str, float | int | None]] = {}
    for d in dims:
        vals = global_means.get(d, [])
        if vals:
            g_means_final[d] = {
                "mean_of_query_means": round(statistics.fmean(vals), 3),
                "stdev_of_query_means": round(
                    statistics.stdev(vals) if len(vals) >= 2 else 0.0, 3
                ),
                "n_queries": len(vals),
            }
        else:
            g_means_final[d] = {
                "mean_of_query_means": None,
                "stdev_of_query_means": None,
                "n_queries": 0,
            }

    per_judge_final: dict[str, dict[str, dict[str, float | int]]] = {}
    for j in judges:
        per_judge_final[j] = {}
        for d in dims:
            vals = per_judge_means[j][d]
            if vals:
                per_judge_final[j][d] = {
                    "mean": round(statistics.fmean(vals), 3),
                    "n": len(vals),
                }
            else:
                per_judge_final[j][d] = {"mean": None, "n": 0}

    # Top 3 best / worst by faithfulness mean (fallback to mean of means if missing)
    def avg_score(r: dict[str, Any]) -> float | None:
        means = []
        for d in dims:
            v = r["aggregate"]["by_dim"].get(d, {}).get("mean")
            if v is not None:
                means.append(v)
        return statistics.fmean(means) if means else None

    scored = [(r, avg_score(r)) for r in rows]
    scored = [(r, s) for r, s in scored if s is not None]
    scored.sort(key=lambda x: x[1], reverse=True)
    top_best = [
        {"id": r["id"], "category": r["category"], "avg": round(s, 3), "query": r["query"]}
        for r, s in scored[:3]
    ]
    top_worst = [
        {"id": r["id"], "category": r["category"], "avg": round(s, 3), "query": r["query"]}
        for r, s in scored[-3:][::-1]
    ]

    # Reco
    faith = g_means_final["faithfulness"]["mean_of_query_means"]
    if faith is None:
        reco = "INDÉTERMINÉ (aucun score faithfulness valide)"
    elif faith >= 0.7:
        reco = f"OK — faithfulness moyenne {faith} >= 0.7"
    elif faith >= 0.5:
        reco = f"À SURVEILLER — faithfulness moyenne {faith} entre 0.5 et 0.7"
    else:
        reco = f"URGENT — faithfulness moyenne {faith} < 0.5, retrieval insuffisant"

    return {
        "global_means": g_means_final,
        "per_judge_means": per_judge_final,
        "judges": judges,
        "divergences_sigma_gt_0_2": div_alerts,
        "top3_best": top_best,
        "top3_worst": top_worst,
        "recommendation": reco,
    }


def render_report(rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    dims = ["faithfulness", "answer_relevance", "context_precision"]
    judges = summary["judges"]

    lines: list[str] = []
    lines.append("# B5 RAGAS multi-juge — rapport")
    lines.append("")
    lines.append(
        f"- Benchmark : 15 requêtes FR DEBBY × top-3 chunks retrieved (LanceDB pilot)"
    )
    lines.append(f"- Juges : {', '.join(judges)} (3 CLI locaux, coût $0)")
    lines.append(
        f"- Date : {time.strftime('%Y-%m-%d %H:%M', time.localtime())}"
    )
    lines.append(
        "- Méthode : prompt RAGAS standardisé FR, 3 dimensions notées 0.0-1.0, "
        "moyenne + écart-type sur 3 voix"
    )
    lines.append("")
    lines.append("## Résumé global")
    lines.append("")
    lines.append("| Dimension | Moyenne (sur 15 requêtes) | Écart-type | N requêtes valides |")
    lines.append("|-----------|-----:|-----:|-----:|")
    for d in dims:
        g = summary["global_means"].get(d, {})
        m = g.get("mean_of_query_means")
        s = g.get("stdev_of_query_means")
        n = g.get("n_queries", 0)
        m_s = f"{m:.3f}" if m is not None else "—"
        s_s = f"{s:.3f}" if s is not None else "—"
        lines.append(f"| {d} | {m_s} | {s_s} | {n} |")
    lines.append("")
    lines.append(f"**Recommandation orchestrateur :** {summary['recommendation']}")
    lines.append("")

    lines.append("## Biais par juge (moyennes sur 15 requêtes)")
    lines.append("")
    header = "| Juge | " + " | ".join(dims) + " | N |"
    sep = "|------|" + "|".join(["-----:"] * len(dims)) + "|---:|"
    lines.append(header)
    lines.append(sep)
    for j in judges:
        row = [j]
        n_val = 0
        for d in dims:
            v = summary["per_judge_means"][j][d]["mean"]
            n_val = summary["per_judge_means"][j][d]["n"]
            row.append(f"{v:.3f}" if v is not None else "—")
        row.append(str(n_val))
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")

    lines.append("## Top 3 requêtes — meilleur retrieval (moyenne 3 dimensions)")
    lines.append("")
    for r in summary["top3_best"]:
        lines.append(
            f"- **{r['id']}** ({r['category']}, avg={r['avg']:.3f}) — {r['query']}"
        )
    lines.append("")
    lines.append("## Top 3 requêtes — pire retrieval (moyenne 3 dimensions)")
    lines.append("")
    for r in summary["top3_worst"]:
        lines.append(
            f"- **{r['id']}** ({r['category']}, avg={r['avg']:.3f}) — {r['query']}"
        )
    lines.append("")

    lines.append("## Divergences fortes entre juges (σ > 0.2)")
    lines.append("")
    if summary["divergences_sigma_gt_0_2"]:
        lines.append("| Requête | Dimension | σ | Scores |")
        lines.append("|---------|-----------|---:|--------|")
        for d in summary["divergences_sigma_gt_0_2"]:
            lines.append(
                f"| {d['id']} | {d['dim']} | {d['stdev']:.3f} | {d['scores']} |"
            )
    else:
        lines.append("_Aucune divergence forte détectée (σ ≤ 0.2 partout)._")
    lines.append("")

    lines.append("## Détail par requête")
    lines.append("")
    # tableau compact
    header = "| ID | Catégorie | Voix | "
    for d in dims:
        for j in judges:
            header += f"{d[:5]}-{j[0]} | "
        header += f"{d[:5]}-μ | {d[:5]}-σ | "
    header = header.rstrip("| ").rstrip() + " |"
    lines.append(header)
    sep = "|----|-----------|-----|" + ("------:|" * (len(dims) * (len(judges) + 2)))
    lines.append(sep)
    for r in rows:
        agg = r["aggregate"]
        row = f"| {r['id']} | {r['category']} | {agg['voices']}/{len(judges)} | "
        for d in dims:
            for j in judges:
                jres = r["judges"].get(j, {}) or {}
                v = jres.get(d)
                row += f"{v:.3f} | " if isinstance(v, (int, float)) else "— | "
            agg_d = agg["by_dim"].get(d, {})
            m = agg_d.get("mean")
            s = agg_d.get("stdev")
            row += f"{m:.3f} | " if m is not None else "— | "
            row += f"{s:.3f} | " if s is not None else "— | "
        row = row.rstrip("| ").rstrip() + " |"
        lines.append(row)
    lines.append("")

    lines.append("## Commentaires (extraits, requêtes les plus mal notées)")
    lines.append("")
    for r in summary["top3_worst"]:
        full = next((x for x in rows if x["id"] == r["id"]), None)
        if not full:
            continue
        lines.append(f"### {full['id']} — {full['query']}")
        lines.append("")
        for j in judges:
            jres = full["judges"].get(j, {}) or {}
            if jres.get("error"):
                lines.append(f"- *{j}* : ERREUR — {jres.get('error')}")
                continue
            lines.append(
                f"- *{j}* : faith={jres.get('faithfulness')} "
                f"rel={jres.get('answer_relevance')} "
                f"prec={jres.get('context_precision')}"
            )
            for ck in ("comment_faithfulness", "comment_relevance", "comment_precision"):
                c = jres.get(ck)
                if c:
                    lines.append(f"  - {ck}: {c}")
        lines.append("")

    # Méthode
    lines.append("## Méthode")
    lines.append("")
    lines.append(
        f"- Payload : `payload.json` (15 requêtes × top-3 chunks)"
    )
    lines.append(
        f"- Prompt : RAGAS standardisé FR, demande JSON strict en sortie."
    )
    lines.append(
        f"- Appels parallèles (3 CLI simultanés par requête), {MAX_RETRIES} retries max."
    )
    lines.append(
        f"- Timeouts : kimi {CLI_TIMEOUT['kimi']}s, codex {CLI_TIMEOUT['codex']}s, gemini {CLI_TIMEOUT['gemini']}s."
    )
    lines.append(
        f"- Kimi lancé avec `--mcp-config-file` pointant un fichier vide afin de désactiver "
        f"les MCP RedAPI/SSTinfo (préservation de la diversité des sources, cf. memory "
        f"`feedback_recherche_combo_kimi_codex`)."
    )
    lines.append(
        f"- Coût : $0 (CLI locaux/managed gratuits)."
    )
    lines.append("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--queries",
        type=int,
        default=None,
        help="Limit number of queries (smoke test).",
    )
    parser.add_argument(
        "--judges",
        type=str,
        default="kimi,codex,gemini",
        help="Comma-separated list of judges.",
    )
    parser.add_argument(
        "--ids",
        type=str,
        default=None,
        help="Comma-separated query ids to run (overrides --queries).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip queries already present in existing results.json",
    )
    args = parser.parse_args()

    if not PAYLOAD.exists():
        print(f"ERROR: payload not found: {PAYLOAD}", file=sys.stderr)
        return 2

    payload = json.loads(PAYLOAD.read_text())
    judges = [j.strip() for j in args.judges.split(",") if j.strip()]

    if args.ids:
        wanted = {x.strip() for x in args.ids.split(",")}
        payload = [q for q in payload if q["id"] in wanted]
    elif args.queries:
        payload = payload[: args.queries]

    existing_rows: list[dict[str, Any]] = []
    done_ids: set[str] = set()
    if args.resume and RESULTS.exists():
        try:
            existing = json.loads(RESULTS.read_text())
            existing_rows = existing.get("rows", [])
            done_ids = {r["id"] for r in existing_rows}
            print(f"Resume mode: {len(done_ids)} queries already done.")
        except Exception:
            pass

    print(
        f"Running RAGAS multi-juge: {len(payload)} queries x {len(judges)} judges "
        f"({', '.join(judges)})"
    )
    print(f"Results -> {RESULTS}")
    print(f"Raw responses -> {RAW}")
    print(f"Report -> {REPORT}")

    rows: list[dict[str, Any]] = list(existing_rows)
    start_total = time.monotonic()

    with RAW.open("a") as raw_fp:
        for i, q in enumerate(payload, 1):
            if q["id"] in done_ids:
                print(f"  [{i}/{len(payload)}] {q['id']:7} — SKIP (already done)")
                continue
            t0 = time.monotonic()
            print(
                f"  [{i}/{len(payload)}] {q['id']:7} [{q['category']:22}] "
                f"{q['query'][:60]}..."
            )
            res = evaluate_query(q, judges, raw_fp)
            rows.append(res)
            # Persist after each query (safety)
            summary = build_global_summary(rows)
            RESULTS.write_text(
                json.dumps(
                    {"summary": summary, "rows": rows},
                    indent=2,
                    ensure_ascii=False,
                )
            )
            agg = res["aggregate"]
            voices = agg["voices"]
            means = " | ".join(
                f"{d[:5]}={agg['by_dim'][d]['mean']}" if agg["by_dim"][d]["mean"] is not None else f"{d[:5]}=NA"
                for d in ("faithfulness", "answer_relevance", "context_precision")
            )
            print(
                f"      voices={voices}/{len(judges)} {means} "
                f"({time.monotonic()-t0:.1f}s)"
            )

    summary = build_global_summary(rows)
    RESULTS.write_text(
        json.dumps(
            {"summary": summary, "rows": rows},
            indent=2,
            ensure_ascii=False,
        )
    )
    REPORT.write_text(render_report(rows, summary))

    total = time.monotonic() - start_total
    print(f"\nDONE in {total/60:.1f} min")
    print(f"  results -> {RESULTS}")
    print(f"  report  -> {REPORT}")
    print(f"  recommendation: {summary['recommendation']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
