#!/usr/bin/env python3
"""
DEBBY KG — Export mind maps Markmap-compatibles par substance.

Chantier A7 (audit DEBBY 2026-05-27).

Markmap (https://markmap.js.org/) prend en entrée un Markdown structuré en
hiérarchie de titres (# / ## / ###) et le rend en mind map interactif HTML.

Pour chaque substance du KG (49), on génère un fichier `.mm.md` qui visualise :

    # <substance>
    ## Pathologies
    ### <pathologie> (sévérité / niveau évidence)
    #### Organes : <organe1>, <organe2>
    #### Tableaux MP : <RG-x>, ...
    #### Surveillance : <examen> (périodicité)
    ## Métiers exposés
    ### <secteur>
    #### <metier>, ...
    ## Identification
    ### CAS, CMR, VLEP, source

Markmap est ouvert dans le navigateur via la CDN officielle, sans serveur.

Usage :
    python3 kg/scripts/export_markmap.py
    python3 kg/scripts/export_markmap.py --only amiante,plomb,benzene
"""
from __future__ import annotations

import argparse
import datetime
import sys
from collections import defaultdict
from pathlib import Path

try:
    import kuzu
except ImportError:
    sys.exit("kuzu requis. `pip install kuzu`")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "kg" / "data" / "kuzu.db"
DEFAULT_OUT = REPO_ROOT / "kg" / "exports" / "markmaps"
KG_VERSION = "kuzu-50sub-v0.2"

# Front-matter Markmap : options de rendu (markmap.js lit ce YAML embarqué)
# Doc : https://markmap.js.org/docs/json-options
FRONT_MATTER = """\
---
title: {title}
markmap:
  colorFreezeLevel: 2
  initialExpandLevel: 3
  maxWidth: 320
  spacingHorizontal: 80
  spacingVertical: 12
---

"""


# ---------------------------------------------------------------------------
# Helpers Kuzu
# ---------------------------------------------------------------------------

def fetch_one(conn, q, p=None):
    r = conn.execute(q, p or {})
    return r.get_next() if r.has_next() else None


def fetch_all(conn, q, p=None):
    r = conn.execute(q, p or {})
    rows = []
    while r.has_next():
        rows.append(r.get_next())
    return rows


# ---------------------------------------------------------------------------
# Échappement Markmap : éviter casser le Markdown (pipes, crochets, etc.)
# ---------------------------------------------------------------------------

def mm_text(s: str) -> str:
    """Markmap autorise du Markdown inline (gras, italique). On garde simple."""
    if s is None:
        return ""
    # Échappe les caractères qui pourraient casser le rendu Markmap
    return str(s).replace("|", "/").replace("\n", " ").strip()


# ---------------------------------------------------------------------------
# Génération mind map pour une substance
# ---------------------------------------------------------------------------

def build_markmap_for_substance(conn, sid: str) -> tuple[str, str] | None:
    s = fetch_one(
        conn,
        """
        MATCH (s:Substance {id:$id})
        RETURN s.nom_fr, s.nom_en, s.cas, s.cmr, s.vlep_8h_mg_m3, s.vlep_ct_mg_m3,
               s.categorie, s.source_url
        """,
        {"id": sid},
    )
    if not s:
        return None
    nom_fr, nom_en, cas, cmr, vlep_8h, vlep_ct, categorie, source_url = s

    pathologies = fetch_all(
        conn,
        """
        MATCH (s:Substance {id:$id})-[c:CAUSE]->(p:Pathologie)
        RETURN p.id, p.nom_fr, p.type, p.severite, c.niveau_evidence
        ORDER BY p.severite DESC, p.nom_fr
        """,
        {"id": sid},
    )

    # Pour chaque pathologie : organes / tableaux / surveillance
    patho_details = {}
    for p_id, p_nom, p_type, p_sev, niveau in pathologies:
        organes = fetch_all(
            conn,
            """
            MATCH (p:Pathologie {id:$id})-[:CONCERNE_ORGANE]->(o:Organe)
            RETURN DISTINCT o.nom_fr, o.systeme
            """,
            {"id": p_id},
        )
        tableaux = fetch_all(
            conn,
            """
            MATCH (p:Pathologie {id:$id})-[:CLASSIFIEE_DANS]->(t:Tableau_MP)
            RETURN DISTINCT t.id, t.regime
            ORDER BY t.regime, t.id
            """,
            {"id": p_id},
        )
        examens = fetch_all(
            conn,
            """
            MATCH (p:Pathologie {id:$id})-[r:SURVEILLANCE]->(e:Examen)
            RETURN DISTINCT e.nom_fr, r.periodicite_mois, r.source_recommandation, r.annee_recommandation
            """,
            {"id": p_id},
        )
        patho_details[p_id] = {
            "nom": p_nom,
            "type": p_type,
            "sev": p_sev,
            "niveau": niveau,
            "organes": organes,
            "tableaux": tableaux,
            "examens": examens,
        }

    metiers = fetch_all(
        conn,
        """
        MATCH (m:Metier)-[r:EXPOSE_A]->(s:Substance {id:$id})
        RETURN m.id, m.nom_fr, m.secteur, r.niveau_exposition
        ORDER BY m.secteur, m.nom_fr
        """,
        {"id": sid},
    )

    # ---------------------------------------------------------------- assemble
    title = f"{nom_fr}"
    out = [FRONT_MATTER.format(title=mm_text(title))]

    # Racine (niveau # = la substance)
    out.append(f"# {mm_text(nom_fr)}")
    out.append("")

    # Branche 1 — Identification
    out.append("## Identification")
    out.append("")
    if cas:
        out.append(f"- N° CAS : `{cas}`")
    if nom_en:
        out.append(f"- Nom EN : {mm_text(nom_en)}")
    if categorie:
        out.append(f"- Catégorie : {categorie}")
    if cmr:
        cmr_label = {
            "C1A": "C1A — cancérogène avéré",
            "C1B": "C1B — cancérogène présumé",
            "C2": "C2 — cancérogène suspecté",
            "M1A": "M1A — mutagène avéré",
            "M1B": "M1B — mutagène présumé",
            "M2": "M2 — mutagène suspecté",
            "R1A": "R1A — reprotoxique avéré",
            "R1B": "R1B — reprotoxique présumé",
            "R2": "R2 — reprotoxique suspecté",
        }.get(cmr, cmr)
        out.append(f"- **CMR : {cmr_label}**")
    if vlep_8h is not None:
        out.append(f"- VLEP 8h : `{vlep_8h} mg/m³`")
    if vlep_ct is not None:
        out.append(f"- VLEP court terme : `{vlep_ct} mg/m³`")
    if source_url:
        out.append(f"- [Fiche INRS]({source_url})")
    out.append("")

    # Branche 2 — Pathologies (niveau ##), avec sous-branches ###
    out.append(f"## Pathologies ({len(pathologies)})")
    out.append("")
    if not pathologies:
        out.append("- _aucune pathologie renseignée_")
        out.append("")
    else:
        for p_id, p_nom, p_type, p_sev, niveau in pathologies:
            det = patho_details[p_id]
            badges = []
            if p_type and p_type != "autre":
                badges.append(p_type)
            if p_sev:
                badges.append(p_sev)
            if niveau:
                badges.append(niveau)
            badge_str = f" _({' / '.join(badges)})_" if badges else ""
            out.append(f"### {mm_text(p_nom)}{badge_str}")
            out.append("")
            if det["organes"]:
                organes_str = ", ".join(mm_text(o[0]) for o in det["organes"])
                out.append(f"- Organes : {organes_str}")
            if det["tableaux"]:
                # Regroupe par régime pour clarté
                rg = [t[0] for t in det["tableaux"] if t[1] == "RG"]
                ra = [t[0] for t in det["tableaux"] if t[1] == "RA"]
                tab_parts = []
                if rg:
                    tab_parts.append(f"RG : {', '.join(rg)}")
                if ra:
                    tab_parts.append(f"RA : {', '.join(ra)}")
                if tab_parts:
                    out.append(f"- Tableaux MP : {' | '.join(tab_parts)}")
            if det["examens"]:
                for e_nom, perio, reco, annee in det["examens"]:
                    perio_str = f" tous les {perio} mois" if perio else ""
                    src_str = f" ({reco} {annee})" if reco else ""
                    out.append(f"- Surveillance : **{mm_text(e_nom)}**{perio_str}{src_str}")
            out.append("")

    # Branche 3 — Métiers exposés (groupés par secteur)
    by_sec = defaultdict(list)
    for m_id, m_nom, m_secteur, niveau in metiers:
        sec = m_secteur or "non_classe"
        by_sec[sec].append((m_nom or m_id, niveau))

    out.append(f"## Métiers exposés ({len(metiers)})")
    out.append("")
    if not metiers:
        out.append("- _aucun métier renseigné_")
        out.append("")
    else:
        sec_order = ["BTP", "industrie", "sante", "agriculture", "non_classe"]
        sec_label = {
            "BTP": "BTP",
            "industrie": "Industrie",
            "sante": "Santé",
            "agriculture": "Agriculture",
            "non_classe": "Autres / transverse",
        }
        for sec in sec_order:
            if sec not in by_sec:
                continue
            out.append(f"### {sec_label[sec]} ({len(by_sec[sec])})")
            out.append("")
            for nom, niveau in by_sec[sec]:
                niv_str = f" _({niveau})_" if niveau else ""
                out.append(f"- {mm_text(nom)}{niv_str}")
            out.append("")

    # Branche 4 — Liens DEBBY
    today = datetime.date.today().isoformat()
    out.append("## Aller plus loin")
    out.append("")
    out.append(f"- [Fiche pédagogique complète](../fiches/fiche_substance_{sid}.md)")
    out.append(f"- [Sous-graphe Mermaid](../debby_kg_{sid}_v0.1.mermaid.md)")
    out.append(f"- KG version : `{KG_VERSION}` — généré : `{today}`")
    out.append("")

    return mm_text(nom_fr), "\n".join(out)


# ---------------------------------------------------------------------------
# Génération INDEX.md des mind maps
# ---------------------------------------------------------------------------

CDN_HOST = "https://markmap.js.org/repl"


def write_markmap_index(generated: list[tuple[str, str, str]], out_dir: Path) -> Path:
    """generated = [(sid, nom_fr, filename)]"""
    today = datetime.date.today().isoformat()
    lines = [
        "# DEBBY KG — Index des mind maps Markmap",
        "",
        "> Mind maps interactives par substance (visualisation hiérarchique).",
        f"> Auto-générées le {today} depuis le KG (`{KG_VERSION}`).",
        "> Format Markmap : Markdown avec hiérarchie de titres. Voir [markmap.js.org](https://markmap.js.org/).",
        "",
        "---",
        "",
        "## Comment visualiser une mind map",
        "",
        "**Option 1 — En ligne (le plus simple, aucun setup) :**",
        "",
        f"1. Ouvrir [Markmap REPL]({CDN_HOST})",
        "2. Copier le contenu d'un fichier `.mm.md` ci-dessous",
        "3. Coller dans la fenêtre de gauche → la mind map s'affiche à droite",
        "",
        "**Option 2 — VS Code :**",
        "",
        "1. Installer l'extension `markmap-vscode` (Gera Mas)",
        "2. Ouvrir un fichier `.mm.md` → bouton « Open as Markmap » en haut à droite",
        "",
        "**Option 3 — CLI :**",
        "",
        "```bash",
        "npx markmap-cli kg/exports/markmaps/amiante.mm.md  # ouvre dans navigateur",
        "```",
        "",
        "---",
        "",
        f"## Mind maps disponibles ({len(generated)})",
        "",
        "| Substance | Fichier | Aperçu Markmap |",
        "|---|---|---|",
    ]
    for sid, nom_fr, fname in generated:
        lines.append(
            f"| **{nom_fr}** | [`{fname}`]({fname}) | [Visualiser]({CDN_HOST}) (copier le fichier) |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("[← Retour INDEX_MASTER](../INDEX_MASTER.md)")
    lines.append("")

    out_path = out_dir / "INDEX.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Validation Markmap : on vérifie la structure attendue
# ---------------------------------------------------------------------------

def validate_markmap_syntax(text: str) -> list[str]:
    """Retourne la liste d'erreurs (vide si OK). Markmap attend :
       - front-matter YAML valide (optionnel)
       - au moins un titre racine `#`
       - pas de saut de niveau (e.g. # puis ###)
    """
    errors = []
    lines = text.splitlines()
    if not any(ln.startswith("# ") for ln in lines):
        errors.append("Aucun titre racine `# ` détecté")

    # Vérifie qu'on n'a pas de saut de niveau brutal
    last_level = 0
    for i, ln in enumerate(lines, 1):
        if ln.startswith("#"):
            # Compter nombre de # initial
            level = len(ln) - len(ln.lstrip("#"))
            if level > last_level + 1 and last_level > 0:
                errors.append(f"L{i} : saut de niveau {last_level} → {level} ('{ln[:40]}')")
            last_level = level

    # Vérifie front-matter ouvert/fermé
    if text.strip().startswith("---"):
        # On doit avoir au moins 2 marqueurs `---`
        markers = [i for i, ln in enumerate(lines) if ln.strip() == "---"]
        if len(markers) < 2:
            errors.append("Front-matter ouvert (---) mais non fermé")

    return errors


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default=str(DEFAULT_DB))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--only", default="", help="Liste IDs séparés par virgule (ex: amiante,plomb)")
    args = ap.parse_args()

    db = kuzu.Database(args.db_path)
    conn = kuzu.Connection(db)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.only:
        targets = [s.strip() for s in args.only.split(",") if s.strip()]
    else:
        rows = fetch_all(conn, "MATCH (s:Substance) RETURN s.id ORDER BY s.id")
        targets = [r[0] for r in rows]

    print("=" * 80)
    print(f"DEBBY KG — Export mind maps Markmap ({len(targets)} substances)")
    print(f"DB  : {args.db_path}")
    print(f"Out : {args.out_dir}")
    print("=" * 80)

    generated = []
    validation_errors = 0

    for sid in targets:
        result = build_markmap_for_substance(conn, sid)
        if result is None:
            print(f"  ⚠️  {sid}: substance non trouvée dans le KG — skip")
            continue
        nom_fr, md = result

        # Validation syntaxe
        errs = validate_markmap_syntax(md)
        if errs:
            validation_errors += 1
            for e in errs:
                print(f"  ⚠️  {sid}: {e}")

        fname = f"{sid}.mm.md"
        out_path = out_dir / fname
        out_path.write_text(md, encoding="utf-8")
        generated.append((sid, nom_fr, fname))
        print(f"  ✅ {sid:30s} → {fname} ({len(md):5d} chars)")

    # Index : on rescanne TOUS les .mm.md sur disque pour que --only ne supprime
    # pas les autres entrées de l'index existant.
    all_on_disk = []
    for p in sorted(out_dir.glob("*.mm.md")):
        sid = p.stem.replace(".mm", "")
        # Récupère nom_fr depuis le titre H1 du fichier
        nom_fr = sid
        try:
            for ln in p.read_text(encoding="utf-8").splitlines():
                if ln.startswith("# "):
                    nom_fr = ln[2:].strip()
                    break
        except OSError:
            pass
        all_on_disk.append((sid, nom_fr, p.name))

    print(f"\n→ Génération INDEX.md ({len(all_on_disk)} mind maps présentes sur disque)…")
    idx_path = write_markmap_index(all_on_disk, out_dir)
    print(f"   {idx_path}")

    # Validation finale : 3 substances clés (amiante, plomb, benzène)
    print("\n→ Validation Markmap des 3 substances clés…")
    for sid in ("amiante", "plomb", "benzene"):
        p = out_dir / f"{sid}.mm.md"
        if not p.exists():
            print(f"  ❌ {sid}: fichier manquant")
            continue
        txt = p.read_text(encoding="utf-8")
        errs = validate_markmap_syntax(txt)
        if errs:
            print(f"  ❌ {sid}: {len(errs)} erreur(s)")
            for e in errs:
                print(f"     - {e}")
        else:
            # Compte les niveaux
            n_h1 = sum(1 for ln in txt.splitlines() if ln.startswith("# "))
            n_h2 = sum(1 for ln in txt.splitlines() if ln.startswith("## "))
            n_h3 = sum(1 for ln in txt.splitlines() if ln.startswith("### "))
            n_h4 = sum(1 for ln in txt.splitlines() if ln.startswith("#### "))
            print(f"  ✅ {sid:15s}: H1={n_h1} H2={n_h2} H3={n_h3} H4={n_h4}, taille={len(txt)} chars")

    print(f"\n✅ {len(generated)} mind maps générées, {validation_errors} avec warnings.")


if __name__ == "__main__":
    main()
