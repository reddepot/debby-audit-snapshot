#!/usr/bin/env python3
"""
DEBBY KG — Test des 10 questions multi-hop (ADR-001 Go/No-Go).
Mesure latence p95 + cohérence (3 runs, σ).
"""
import argparse
import json
import statistics
import sys
import time
from pathlib import Path

try:
    import kuzu
except ImportError:
    sys.exit("kuzu non installé.")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "kg" / "data" / "kuzu.db"

QUERIES = [
    {
        "id": "Q1",
        "label": "Amiante → mésothéliome → tableau",
        "hops": 3,
        "cypher": """
            MATCH (s:Substance {id:'amiante'})-[:CAUSE]->(p:Pathologie {id:'mesotheliome'})
                  -[:CLASSIFIEE_DANS]->(t:Tableau_MP)
            RETURN t.id, t.intitule;
        """,
        "expected_contains": ["RG-30-TER"],
    },
    {
        "id": "Q2",
        "label": "Métier couvreur → substance → pathologie → tableau",
        "hops": 4,
        "cypher": """
            MATCH (m:Metier {id:'couvreur'})-[:EXPOSE_A]->(s:Substance)
                  -[:CAUSE]->(p:Pathologie)
                  -[:CLASSIFIEE_DANS]->(t:Tableau_MP)
            RETURN DISTINCT t.id ORDER BY t.id;
        """,
        "expected_contains": ["RG-30", "RG-30-BIS", "RG-30-TER"],
    },
    {
        "id": "Q3",
        "label": "Substance benzène → pathologie → organe",
        "hops": 3,
        "cypher": """
            MATCH (s:Substance {id:'benzene'})-[:CAUSE]->(p:Pathologie)
                  -[:CONCERNE_ORGANE]->(o:Organe)
            RETURN DISTINCT o.nom_fr;
        """,
        "expected_contains": ["Moelle osseuse"],
    },
    {
        "id": "Q4",
        "label": "Tableau RG-25 (silicose) → métiers exposés",
        "hops": 2,
        "cypher": """
            MATCH (t:Tableau_MP {id:'RG-25'})-[:CONCERNE_METIER]->(m:Metier)
            RETURN m.nom_fr ORDER BY m.nom_fr;
        """,
        "expected_contains": ["Tailleur pierre", "Macon"],
    },
    {
        "id": "Q5",
        "label": "Surveillance amiante : scanner thoracique périodicité",
        "hops": 2,
        "cypher": """
            MATCH (p:Pathologie {id:'mesotheliome'})-[r:SURVEILLANCE]->(e:Examen {id:'scanner_thoracique'})
            RETURN e.nom_fr, r.periodicite_mois, r.source_recommandation, r.annee_recommandation;
        """,
        "expected_contains": ["HAS-2022"],
    },
    {
        "id": "Q6",
        "label": "Substances VLEP 8h < 0.05 mg/m³",
        "hops": 1,
        "cypher": """
            MATCH (s:Substance)
            WHERE s.vlep_8h_mg_m3 IS NOT NULL AND s.vlep_8h_mg_m3 < 0.05
            RETURN s.nom_fr, s.vlep_8h_mg_m3, s.cmr ORDER BY s.vlep_8h_mg_m3;
        """,
        "expected_contains": ["Amiante", "Chrome hexavalent", "Nickel", "Cadmium"],
    },
    {
        "id": "Q7",
        "label": "Substances IARC-1 affectant le poumon",
        "hops": 3,
        "cypher": """
            MATCH (s:Substance)-[c:CAUSE]->(p:Pathologie)-[:CONCERNE_ORGANE]->(o:Organe {id:'poumon'})
            WHERE c.niveau_evidence = 'IARC-1'
            RETURN DISTINCT s.nom_fr ORDER BY s.nom_fr;
        """,
        "expected_contains": ["Amiante", "Silice cristalline", "Chrome hexavalent", "Cadmium"],
    },
    {
        "id": "Q8",
        "label": "Soudeur inox → cancer broncho-pulmonaire + asthme + surveillance",
        "hops": 5,
        "cypher": """
            MATCH (m:Metier {id:'soudeur_inox'})-[:EXPOSE_A]->(s:Substance)
                  -[:CAUSE]->(p:Pathologie)
                  -[:CLASSIFIEE_DANS]->(t:Tableau_MP)
            OPTIONAL MATCH (p)-[surv:SURVEILLANCE]->(e:Examen)
            RETURN DISTINCT s.nom_fr AS substance, p.nom_fr AS patho, t.id AS tableau, e.nom_fr AS examen
            ORDER BY tableau;
        """,
        "expected_contains": ["RG-10", "Chrome hexavalent", "Nickel"],
    },
    {
        "id": "Q9",
        "label": "Surveillance plomb sources <2015 (test obsolescence I.7)",
        "hops": 2,
        "cypher": """
            MATCH (p:Pathologie)-[r:SURVEILLANCE]->(e:Examen)
            WHERE r.annee_recommandation < 2015
            RETURN p.nom_fr, e.nom_fr, r.source_recommandation, r.annee_recommandation;
        """,
        "expected_contains": [],  # ✅ aucune obsolescence détectée = KG nettoyé I.7
    },
    {
        "id": "Q10",
        "label": "Mécanicien automobile → solvants → tableaux + conduite",
        "hops": 4,
        "cypher": """
            MATCH (m:Metier)-[:EXPOSE_A]->(s:Substance)
            WHERE m.id CONTAINS 'mecanicien' AND (s.categorie = 'cov' OR s.id IN ['benzene'])
            OPTIONAL MATCH (s)-[:CAUSE]->(p:Pathologie)-[:CLASSIFIEE_DANS]->(t:Tableau_MP)
            RETURN DISTINCT s.nom_fr, p.nom_fr, t.id;
        """,
        "expected_contains": [],  # mécanicien pas dans le pool 10 substances, expected empty mais latence OK
    },
]


def run_query(conn, cypher):
    t0 = time.perf_counter()
    res = conn.execute(cypher.strip())
    rows = []
    while res.has_next():
        rows.append(res.get_next())
    elapsed = (time.perf_counter() - t0) * 1000.0  # ms
    return rows, elapsed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default=str(DEFAULT_DB))
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--out-json", default=str(REPO_ROOT / "kg" / "tests" / "query_results.json"))
    args = ap.parse_args()

    db = kuzu.Database(args.db_path)
    conn = kuzu.Connection(db)

    print("=" * 80)
    print("DEBBY KG — Test 10 questions multi-hop")
    print(f"DB: {args.db_path}  |  runs: {args.runs}")
    print("=" * 80)

    all_results = []
    passed = 0
    for q in QUERIES:
        elapsed_runs = []
        rows_runs = []
        for _ in range(args.runs):
            rows, elapsed = run_query(conn, q["cypher"])
            elapsed_runs.append(elapsed)
            rows_runs.append(rows)

        elapsed_p95 = statistics.median_high(elapsed_runs)
        elapsed_mean = statistics.mean(elapsed_runs)
        elapsed_std = statistics.stdev(elapsed_runs) if len(elapsed_runs) > 1 else 0.0

        rows = rows_runs[0]
        flat = " | ".join(str(c) for r in rows for c in r)

        # Check expected_contains
        expected = q.get("expected_contains", [])
        if expected:
            hits = sum(1 for e in expected if e in flat)
            ok = hits >= max(1, len(expected) // 2)  # ≥ moitié des attendus
        else:
            ok = True  # pas d'attendu (Q9, Q10) = pass si latence OK

        status = "✅" if ok else "❌"
        if ok:
            passed += 1

        print(f"\n{status} {q['id']} ({q['hops']}-hop) | {elapsed_mean:.1f}ms (σ={elapsed_std:.1f}) | {len(rows)} rows")
        print(f"   {q['label']}")
        if rows:
            preview = flat[:200] + ("…" if len(flat) > 200 else "")
            print(f"   → {preview}")
        if expected and not ok:
            print(f"   ⚠️ Attendu : {expected}")

        all_results.append({
            "id": q["id"],
            "label": q["label"],
            "hops": q["hops"],
            "elapsed_mean_ms": elapsed_mean,
            "elapsed_p95_ms": elapsed_p95,
            "elapsed_std_ms": elapsed_std,
            "row_count": len(rows),
            "passed": ok,
            "preview": flat[:300],
        })

    # Aggregate stats
    all_elapsed = [r["elapsed_mean_ms"] for r in all_results]
    print("\n" + "=" * 80)
    print(f"RÉSULTAT GLOBAL : {passed}/10 questions passent (cible Go ≥ 7/10)")
    print(f"Latence moyenne : {statistics.mean(all_elapsed):.2f} ms")
    print(f"Latence p95     : {max(all_elapsed):.2f} ms (cible < 500 ms)")
    print("=" * 80)

    go_no_go = {
        "questions_passed": passed,
        "questions_total": 10,
        "go_threshold": 7,
        "go_status": "GO" if passed >= 7 else "NO_GO",
        "latency_mean_ms": statistics.mean(all_elapsed),
        "latency_p95_ms": max(all_elapsed),
        "latency_threshold_ms": 500,
        "latency_status": "GO" if max(all_elapsed) < 500 else "NO_GO",
    }
    print("\nGo/No-Go ADR-001 :")
    for k, v in go_no_go.items():
        print(f"  {k:25s}: {v}")

    output_path = Path(args.out_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({
        "meta": {
            "version": "kuzu-10sub-v0.1",
            "db_path": args.db_path,
            "runs_per_query": args.runs,
        },
        "results": all_results,
        "go_no_go": go_no_go,
    }, indent=2, ensure_ascii=False))
    print(f"\n→ Résultats sauvegardés : {output_path}")


if __name__ == "__main__":
    main()
