#!/usr/bin/env python3
"""
DEBBY KG — Export Kuzu → GraphML (Gephi/yEd/Cytoscape) + Mermaid (Markdown/Obsidian).
"""
import argparse
import sys
from pathlib import Path

try:
    import kuzu
    import networkx as nx
except ImportError:
    sys.exit("kuzu + networkx requis. `pip install kuzu networkx`")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "kg" / "data" / "kuzu.db"
DEFAULT_OUT = REPO_ROOT / "kg" / "exports"

NODE_LABELS = ["Substance", "Pathologie", "Tableau_MP", "Metier", "Organe", "Examen"]
REL_TYPES = ["CAUSE", "CLASSIFIEE_DANS", "CONCERNE_METIER", "EXPOSE_A", "CONCERNE_ORGANE", "SURVEILLANCE"]


def build_networkx(conn) -> nx.MultiDiGraph:
    """Construct an in-memory NetworkX MultiDiGraph from Kuzu."""
    g = nx.MultiDiGraph()

    # Nodes (Tableau_MP uses `intitule` not `nom_fr`)
    label_to_name_col = {
        "Substance": "nom_fr",
        "Pathologie": "nom_fr",
        "Tableau_MP": "intitule",
        "Metier": "nom_fr",
        "Organe": "nom_fr",
        "Examen": "nom_fr",
    }
    for label in NODE_LABELS:
        name_col = label_to_name_col.get(label, "nom_fr")
        r = conn.execute(f"MATCH (n:{label}) RETURN n.id, n.{name_col}")
        while r.has_next():
            nid, nom = r.get_next()
            g.add_node(f"{label}::{nid}", label=label, nom_fr=nom or nid, type=label)

    # Edges
    for rel in REL_TYPES:
        if rel == "CAUSE":
            q = "MATCH (s:Substance)-[r:CAUSE]->(p:Pathologie) RETURN s.id, p.id, r.niveau_evidence"
            tup = ("Substance", "Pathologie")
        elif rel == "CLASSIFIEE_DANS":
            q = "MATCH (p:Pathologie)-[r:CLASSIFIEE_DANS]->(t:Tableau_MP) RETURN p.id, t.id, r.completeness"
            tup = ("Pathologie", "Tableau_MP")
        elif rel == "CONCERNE_METIER":
            q = "MATCH (t:Tableau_MP)-[r:CONCERNE_METIER]->(m:Metier) RETURN t.id, m.id, r.frequence_exposition"
            tup = ("Tableau_MP", "Metier")
        elif rel == "EXPOSE_A":
            q = "MATCH (m:Metier)-[r:EXPOSE_A]->(s:Substance) RETURN m.id, s.id, r.niveau_exposition"
            tup = ("Metier", "Substance")
        elif rel == "CONCERNE_ORGANE":
            q = "MATCH (p:Pathologie)-[r:CONCERNE_ORGANE]->(o:Organe) RETURN p.id, o.id, r.type_atteinte"
            tup = ("Pathologie", "Organe")
        else:  # SURVEILLANCE
            q = "MATCH (p:Pathologie)-[r:SURVEILLANCE]->(e:Examen) RETURN p.id, e.id, r.source_recommandation"
            tup = ("Pathologie", "Examen")

        r = conn.execute(q)
        while r.has_next():
            src, dst, attr = r.get_next()
            src_n = f"{tup[0]}::{src}"
            dst_n = f"{tup[1]}::{dst}"
            if src_n in g.nodes and dst_n in g.nodes:
                g.add_edge(src_n, dst_n, key=rel, type=rel, attr=str(attr) if attr is not None else "")
    return g


def export_graphml(g: nx.MultiDiGraph, out_path: Path):
    nx.write_graphml(g, str(out_path))
    print(f"  → GraphML : {out_path}")


def export_mermaid(g: nx.MultiDiGraph, out_path: Path):
    """Export a focused Mermaid graph for the 10 pilot substances."""
    lines = ["```mermaid", "graph LR"]
    color_class = {
        "Substance": "fill:#ffcccc,stroke:#990000",
        "Pathologie": "fill:#fff2cc,stroke:#cc7700",
        "Tableau_MP": "fill:#ccebff,stroke:#0066cc",
        "Metier": "fill:#d9ead3,stroke:#34a853",
        "Organe": "fill:#d9d2e9,stroke:#674ea7",
        "Examen": "fill:#fce5cd,stroke:#e69138",
    }
    # Slugify node ids for Mermaid
    def slug(n):
        return n.replace("::", "_").replace("-", "_")

    # Nodes (with labels)
    for n, data in g.nodes(data=True):
        lbl = data.get("nom_fr", n)
        # Truncate long labels
        if len(lbl) > 30:
            lbl = lbl[:27] + "…"
        lines.append(f'    {slug(n)}["{lbl}"]')

    # Edges
    for u, v, k, data in g.edges(keys=True, data=True):
        et = data.get("type", k)
        # Mermaid edge label
        lbl = et[:15]
        lines.append(f"    {slug(u)} -->|{lbl}| {slug(v)}")

    # Class definitions for coloring
    lines.append("")
    for label, css in color_class.items():
        lines.append(f"    classDef {label.lower()} {css}")

    # Apply classes
    for n, data in g.nodes(data=True):
        lines.append(f"    class {slug(n)} {data['label'].lower()}")

    lines.append("```")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → Mermaid : {out_path}")


def export_subgraph_substance(conn, substance_id: str, out_path: Path):
    """Export a focused subgraph centered on a single substance (e.g. 'amiante')."""
    g_sub = nx.MultiDiGraph()

    # Get substance + linked pathologies + tableaux + metiers + organes + examens
    queries = [
        ("Substance", "MATCH (s:Substance {id:$id}) RETURN s.id, s.nom_fr"),
        ("Pathologie", "MATCH (s:Substance {id:$id})-[:CAUSE]->(p:Pathologie) RETURN p.id, p.nom_fr"),
        ("Tableau_MP", "MATCH (s:Substance {id:$id})-[:CAUSE]->(p:Pathologie)-[:CLASSIFIEE_DANS]->(t:Tableau_MP) RETURN DISTINCT t.id, t.intitule"),
        ("Metier", "MATCH (m:Metier)-[:EXPOSE_A]->(s:Substance {id:$id}) RETURN m.id, m.nom_fr"),
        ("Organe", "MATCH (s:Substance {id:$id})-[:CAUSE]->(p:Pathologie)-[:CONCERNE_ORGANE]->(o:Organe) RETURN DISTINCT o.id, o.nom_fr"),
        ("Examen", "MATCH (s:Substance {id:$id})-[:CAUSE]->(p:Pathologie)-[:SURVEILLANCE]->(e:Examen) RETURN DISTINCT e.id, e.nom_fr"),
    ]
    for label, q in queries:
        r = conn.execute(q, parameters={"id": substance_id})
        while r.has_next():
            nid, nom = r.get_next()
            g_sub.add_node(f"{label}::{nid}", label=label, nom_fr=nom or nid, type=label)

    # Edges (filtered to nodes in subgraph)
    nodes_in_sub = set(g_sub.nodes)
    full = build_networkx(conn)
    for u, v, k, data in full.edges(keys=True, data=True):
        if u in nodes_in_sub and v in nodes_in_sub:
            g_sub.add_edge(u, v, key=k, **data)

    export_mermaid(g_sub, out_path)
    print(f"     [{substance_id}] nodes={len(g_sub.nodes)}, edges={len(g_sub.edges)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default=str(DEFAULT_DB))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--substances", nargs="*", default=["amiante", "plomb", "benzene", "silice_cristalline"],
                    help="Substances pour subgraphs Mermaid focalisés")
    args = ap.parse_args()

    db = kuzu.Database(args.db_path)
    conn = kuzu.Connection(db)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("DEBBY KG — Export GraphML + Mermaid")
    print("=" * 80)

    g = build_networkx(conn)
    print(f"\nGraphe global : {len(g.nodes)} nodes, {len(g.edges)} edges")

    print("\n--- Export full graph ---")
    export_graphml(g, out_dir / "debby_kg_full_v0.1.graphml")
    export_mermaid(g, out_dir / "debby_kg_full_v0.1.mermaid.md")

    print("\n--- Export subgraphs focalisés par substance ---")
    for s in args.substances:
        export_subgraph_substance(conn, s, out_dir / f"debby_kg_{s}_v0.1.mermaid.md")

    print("\n✅ Export terminé.")


if __name__ == "__main__":
    main()
