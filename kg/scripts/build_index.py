#!/usr/bin/env python3
"""
DEBBY KG — Construction des index navigables pour les fiches pédagogiques.

Chantier A6 (audit DEBBY 2026-05-27) : index Markdown + HTML statique
permettant aux MdT formateurs de retrouver une fiche substance par :
  - ordre alphabétique de substance
  - secteur d'activité du métier exposé (BTP / industrie / santé / agriculture)
  - tableau de maladies professionnelles (RG d'abord, RA ensuite)
  - organe/système cible (respiratoire, neurologique, cancer, etc.)

Génère également :
  - INDEX.html (Bootstrap CDN + recherche JavaScript simple)
  - INDEX_MASTER.md (point d'entrée unique avec statistiques globales)

Usage :
    python3 kg/scripts/build_index.py
    python3 kg/scripts/build_index.py --db-path kg/data/kuzu.db --fiches-dir kg/exports/fiches
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from collections import defaultdict
from pathlib import Path

try:
    import kuzu
except ImportError:
    sys.exit("kuzu requis. `pip install kuzu`")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "kg" / "data" / "kuzu.db"
DEFAULT_FICHES_DIR = REPO_ROOT / "kg" / "exports" / "fiches"
DEFAULT_OUT_DIR = REPO_ROOT / "kg" / "exports"

KG_VERSION = "kuzu-50sub-v0.2"

# Ordre canonique secteurs (BTP en premier — secteur prioritaire MdT)
SECTEUR_ORDER = ["BTP", "industrie", "sante", "agriculture", "non_classe"]
SECTEUR_LABEL = {
    "BTP": "BTP (bâtiment, travaux publics)",
    "industrie": "Industrie (métallurgie, chimie, agroalimentaire, etc.)",
    "sante": "Santé (soignants, laboratoires, vétérinaire)",
    "agriculture": "Agriculture (agriculteurs, viticulteurs, élevage)",
    "non_classe": "Non classé / Transverse",
}

# Mapping pathologie type → label humain
TYPE_LABEL = {
    "cancer": "Cancers",
    "respiratoire": "Pathologies respiratoires",
    "neurologique": "Pathologies neurologiques",
    "cutanee": "Pathologies cutanées",
    "autre": "Autres pathologies",
}

# Ordre canonique systèmes organes
SYSTEME_ORDER = [
    "respiratoire",
    "neurologique",
    "hematopoietique",
    "tegumentaire",
    "urinaire",
    "digestif",
    "musculo_squelettique",
]
SYSTEME_LABEL = {
    "respiratoire": "Appareil respiratoire (poumon, plèvre, VAS)",
    "neurologique": "Système nerveux",
    "hematopoietique": "Système hématopoïétique (moelle osseuse)",
    "tegumentaire": "Téguments (peau)",
    "urinaire": "Appareil urinaire (rein)",
    "digestif": "Appareil digestif (foie)",
    "musculo_squelettique": "Appareil locomoteur (os, articulations)",
}


# ---------------------------------------------------------------------------
# Helpers Kuzu
# ---------------------------------------------------------------------------

def fetch_all(conn, query, parameters=None):
    r = conn.execute(query, parameters or {})
    rows = []
    while r.has_next():
        rows.append(r.get_next())
    return rows


# ---------------------------------------------------------------------------
# Collecte data
# ---------------------------------------------------------------------------

def list_fiches(fiches_dir: Path) -> dict[str, Path]:
    """Liste les fiches Markdown existantes. Clé = substance_id."""
    out = {}
    if not fiches_dir.exists():
        return out
    for path in sorted(fiches_dir.glob("fiche_substance_*.md")):
        sid = path.stem.replace("fiche_substance_", "")
        out[sid] = path
    return out


def collect_substance_index(conn) -> list[dict]:
    """Retourne pour chaque substance : id, nom_fr, cmr, categorie, vlep_8h."""
    rows = fetch_all(
        conn,
        """
        MATCH (s:Substance)
        RETURN s.id, s.nom_fr, s.cmr, s.categorie, s.vlep_8h_mg_m3
        ORDER BY s.nom_fr
        """,
    )
    return [
        {
            "id": r[0],
            "nom_fr": r[1],
            "cmr": r[2] or "",
            "categorie": r[3] or "",
            "vlep_8h": r[4],
        }
        for r in rows
    ]


def collect_metier_index(conn) -> dict[str, list[dict]]:
    """Pour chaque secteur : liste de (metier_nom, substances exposées)."""
    rows = fetch_all(
        conn,
        """
        MATCH (m:Metier)-[:EXPOSE_A]->(s:Substance)
        RETURN m.id, m.nom_fr, m.secteur, collect(DISTINCT [s.id, s.nom_fr]) AS subs
        ORDER BY m.secteur, m.nom_fr
        """,
    )
    by_secteur: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        m_id, m_nom, m_secteur, subs = r
        secteur_key = m_secteur if m_secteur in SECTEUR_ORDER else "non_classe"
        by_secteur[secteur_key].append(
            {
                "id": m_id,
                "nom": m_nom or m_id,
                "substances": [{"id": s[0], "nom": s[1]} for s in subs],
            }
        )
    return by_secteur


def collect_tableau_index(conn) -> dict[str, list[dict]]:
    """Pour chaque régime (RG/RA) : liste de (tableau_id, intitule, substances liées)."""
    rows = fetch_all(
        conn,
        """
        MATCH (t:Tableau_MP)<-[:CLASSIFIEE_DANS]-(p:Pathologie)<-[:CAUSE]-(s:Substance)
        RETURN t.id, t.intitule, t.regime, t.numero, t.variante,
               collect(DISTINCT [s.id, s.nom_fr]) AS subs,
               collect(DISTINCT [p.id, p.nom_fr]) AS pathos
        ORDER BY t.regime, t.numero, t.variante
        """,
    )
    by_regime: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        t_id, intitule, regime, num, variante, subs, pathos = r
        # Forçage tri numérique stable : numero peut être int ou None
        try:
            num_int = int(num) if num is not None else 999
        except (TypeError, ValueError):
            num_int = 999
        by_regime[regime].append(
            {
                "id": t_id,
                "intitule": intitule or t_id,
                "regime": regime,
                "numero": num_int,
                "variante": variante or "",
                "substances": [{"id": s[0], "nom": s[1]} for s in subs],
                "pathologies": [{"id": p[0], "nom": p[1]} for p in pathos],
            }
        )
    # Tri secondaire intra-régime : numéro puis variante
    for reg in by_regime:
        by_regime[reg].sort(key=lambda x: (x["numero"], x["variante"]))
    return by_regime


def collect_organe_index(conn) -> dict[str, list[dict]]:
    """Pour chaque organe : liste pathologies + substances impliquées."""
    rows = fetch_all(
        conn,
        """
        MATCH (o:Organe)<-[:CONCERNE_ORGANE]-(p:Pathologie)<-[:CAUSE]-(s:Substance)
        RETURN o.id, o.nom_fr, o.systeme,
               p.id, p.nom_fr, p.type,
               collect(DISTINCT [s.id, s.nom_fr]) AS subs
        ORDER BY o.systeme, o.nom_fr, p.nom_fr
        """,
    )
    by_systeme: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        o_id, o_nom, o_sys, p_id, p_nom, p_type, subs = r
        sys_key = o_sys if o_sys in SYSTEME_ORDER else "autre"
        by_systeme[sys_key].append(
            {
                "organe_id": o_id,
                "organe_nom": o_nom or o_id,
                "pathologie_id": p_id,
                "pathologie_nom": p_nom or p_id,
                "pathologie_type": p_type or "autre",
                "substances": [{"id": s[0], "nom": s[1]} for s in subs],
            }
        )
    return by_systeme


def collect_pathologie_type_index(conn) -> dict[str, list[dict]]:
    """Pathologies groupées par type (cancer, respiratoire, etc.) avec substances."""
    rows = fetch_all(
        conn,
        """
        MATCH (s:Substance)-[:CAUSE]->(p:Pathologie)
        RETURN p.id, p.nom_fr, p.type, p.severite,
               collect(DISTINCT [s.id, s.nom_fr]) AS subs
        ORDER BY p.type, p.nom_fr
        """,
    )
    by_type: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        p_id, p_nom, p_type, p_sev, subs = r
        by_type[p_type or "autre"].append(
            {
                "id": p_id,
                "nom": p_nom or p_id,
                "severite": p_sev or "—",
                "substances": [{"id": s[0], "nom": s[1]} for s in subs],
            }
        )
    return by_type


def compute_stats(conn) -> dict:
    """Stats globales pour INDEX_MASTER.md et HTML."""
    def count(query):
        rows = fetch_all(conn, query)
        return rows[0][0] if rows else 0

    return {
        "n_substances": count("MATCH (s:Substance) RETURN count(s)"),
        "n_pathologies": count("MATCH (p:Pathologie) RETURN count(p)"),
        # Total tableaux référentiels INRS chargés
        "n_tableaux_mp_ref": count("MATCH (t:Tableau_MP) RETURN count(t)"),
        # Tableaux effectivement reliés à au moins une pathologie via les 49 substances pilotes
        "n_tableaux_mp_couverts": count(
            "MATCH (t:Tableau_MP)<-[:CLASSIFIEE_DANS]-(p:Pathologie) RETURN count(DISTINCT t.id)"
        ),
        "n_metiers": count("MATCH (m:Metier) RETURN count(m)"),
        "n_organes": count("MATCH (o:Organe) RETURN count(o)"),
        "n_examens": count("MATCH (e:Examen) RETURN count(e)"),
        "n_rg_couverts": count(
            "MATCH (t:Tableau_MP)<-[:CLASSIFIEE_DANS]-(p:Pathologie) WHERE t.regime = 'RG' RETURN count(DISTINCT t.id)"
        ),
        "n_ra_couverts": count(
            "MATCH (t:Tableau_MP)<-[:CLASSIFIEE_DANS]-(p:Pathologie) WHERE t.regime = 'RA' RETURN count(DISTINCT t.id)"
        ),
        "n_cmr_c1": count("MATCH (s:Substance) WHERE s.cmr IN ['C1A','C1B'] RETURN count(s)"),
    }


# ---------------------------------------------------------------------------
# Helpers Markdown
# ---------------------------------------------------------------------------

def md_header(title: str, subtitle: str = "") -> list[str]:
    today = datetime.date.today().isoformat()
    lines = [f"# {title}", ""]
    if subtitle:
        lines.append(f"> {subtitle}")
    lines.append(f"> Auto-généré depuis le KG DEBBY ({KG_VERSION}) — {today}")
    lines.append("> Pipeline : `kg/scripts/build_index.py`")
    lines.append("")
    lines.append("---")
    lines.append("")
    return lines


def fiche_link(sid: str, fiches: dict[str, Path], anchor_label: str = "") -> str:
    """Lien Markdown vers la fiche pédagogique si elle existe, sinon texte simple."""
    label = anchor_label or sid
    if sid in fiches:
        rel_path = f"fiches/fiche_substance_{sid}.md"
        return f"[{label}]({rel_path})"
    return f"{label} _(fiche non générée)_"


# ---------------------------------------------------------------------------
# Génération INDEX_SUBSTANCES.md
# ---------------------------------------------------------------------------

def write_index_substances(substances: list[dict], fiches: dict[str, Path], out_dir: Path) -> Path:
    lines = md_header(
        "Index des substances et agents par ordre alphabétique",
        "Toutes les substances/agents du KG DEBBY, classés A→Z. Cliquer pour ouvrir la fiche pédagogique.",
    )

    lines.append(f"**{len(substances)} substances/agents** ({len(fiches)} fiches générées)")
    lines.append("")
    lines.append("| Substance | CMR | Catégorie | VLEP 8h (mg/m³) | Fiche |")
    lines.append("|---|---|---|---|---|")

    for s in substances:
        cmr_lbl = s["cmr"] if s["cmr"] else "—"
        vlep_lbl = f"`{s['vlep_8h']}`" if s["vlep_8h"] is not None else "—"
        cmr_warn = " ⚠️" if s["cmr"] in ("C1A", "C1B") else ""
        link = fiche_link(s["id"], fiches, "Voir fiche") if s["id"] in fiches else "_à générer_"
        lines.append(
            f"| **{s['nom_fr']}** | {cmr_lbl}{cmr_warn} | {s['categorie']} | {vlep_lbl} | {link} |"
        )

    lines.append("")
    lines.append("## Légende CMR (règlement CLP)")
    lines.append("")
    lines.append("- **C1A** : cancérogène avéré pour l'homme")
    lines.append("- **C1B** : cancérogène présumé pour l'homme")
    lines.append("- **C2** : cancérogène suspecté")
    lines.append("- **M1A/M1B/M2** : mutagène (mêmes catégories)")
    lines.append("- **R1A/R1B/R2** : reprotoxique (mêmes catégories)")
    lines.append("")
    lines.append("[← Retour INDEX_MASTER](INDEX_MASTER.md)")
    lines.append("")

    out_path = out_dir / "INDEX_SUBSTANCES.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Génération INDEX_METIERS.md
# ---------------------------------------------------------------------------

def write_index_metiers(by_secteur: dict[str, list[dict]], fiches: dict[str, Path], out_dir: Path) -> Path:
    lines = md_header(
        "Index des métiers et secteurs exposés",
        "Quels métiers sont exposés à quelles substances. Groupés par secteur d'activité.",
    )

    total_metiers = sum(len(v) for v in by_secteur.values())
    lines.append(f"**{total_metiers} métiers indexés**, {len(by_secteur)} secteurs.")
    lines.append("")

    # TOC
    lines.append("## Sommaire des secteurs")
    lines.append("")
    for sec in SECTEUR_ORDER:
        if sec in by_secteur:
            n = len(by_secteur[sec])
            slug = sec.replace("_", "-").lower()
            lines.append(f"- [{SECTEUR_LABEL[sec]}](#{slug}) — {n} métiers")
    lines.append("")
    lines.append("---")
    lines.append("")

    for sec in SECTEUR_ORDER:
        if sec not in by_secteur:
            continue
        slug = sec.replace("_", "-").lower()
        lines.append(f"## {SECTEUR_LABEL[sec]} <a id=\"{slug}\"></a>")
        lines.append("")
        lines.append("| Métier | Substances exposantes |")
        lines.append("|---|---|")
        for m in by_secteur[sec]:
            subs_links = ", ".join(
                fiche_link(s["id"], fiches, s["nom"]) for s in m["substances"]
            )
            lines.append(f"| **{m['nom']}** | {subs_links} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("[← Retour INDEX_MASTER](INDEX_MASTER.md)")
    lines.append("")

    out_path = out_dir / "INDEX_METIERS.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Génération INDEX_TABLEAUX_MP.md
# ---------------------------------------------------------------------------

def write_index_tableaux_mp(by_regime: dict[str, list[dict]], fiches: dict[str, Path], out_dir: Path) -> Path:
    lines = md_header(
        "Index des tableaux de maladies professionnelles (MP)",
        "Tableaux MP du régime général (RG) puis du régime agricole (RA). Source : INRS — décompte canonique 175 tableaux (cf. TABLEAUX_MP_REFERENCE.md).",
    )

    total_in_kg = sum(len(v) for v in by_regime.values())
    lines.append(
        f"**{total_in_kg} tableaux couverts** (au moins une substance pilote du KG y est rattachée) sur les 175 tableaux INRS référentiels."
    )
    lines.append("")

    # TOC
    lines.append("## Sommaire")
    lines.append("")
    if "RG" in by_regime:
        lines.append(f"- [Régime général (RG)](#rg) — {len(by_regime['RG'])} tableaux")
    if "RA" in by_regime:
        lines.append(f"- [Régime agricole (RA)](#ra) — {len(by_regime['RA'])} tableaux")
    lines.append("")
    lines.append("---")
    lines.append("")

    # RG d'abord
    for regime in ("RG", "RA"):
        if regime not in by_regime:
            continue
        slug = regime.lower()
        title = "Régime général (RG)" if regime == "RG" else "Régime agricole (RA)"
        lines.append(f"## {title} <a id=\"{slug}\"></a>")
        lines.append("")
        lines.append("| Tableau | Intitulé court | Pathologies (extraits) | Substances déclenchantes |")
        lines.append("|---|---|---|---|")
        for t in by_regime[regime]:
            patho_str = ", ".join(p["nom"] for p in t["pathologies"][:3])
            if len(t["pathologies"]) > 3:
                patho_str += f" (+{len(t['pathologies'])-3})"
            subs_links = ", ".join(
                fiche_link(s["id"], fiches, s["nom"]) for s in t["substances"]
            )
            inrs_url = f"https://www.inrs.fr/publications/bdd/mp/tableau.html?refINRS={t['id']}"
            lines.append(
                f"| **[`{t['id']}`]({inrs_url})** | {t['intitule']} | {patho_str} | {subs_links} |"
            )
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Vérification d'un tableau (rappel utile)")
    lines.append("")
    lines.append("Pour chaque tableau, contrôler systématiquement :")
    lines.append("")
    lines.append("- **Délai de prise en charge** (depuis cessation d'exposition)")
    lines.append("- **Durée d'exposition minimale** requise pour reconnaissance")
    lines.append("- **Liste limitative ou indicative** des travaux exposants")
    lines.append("")
    lines.append("Sources de référence :")
    lines.append("- [INRS BDD MP — liste tableaux](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html)")
    lines.append("- MCP SSTinfo (outil `lookup_tableau_mp`)")
    lines.append("")
    lines.append("[← Retour INDEX_MASTER](INDEX_MASTER.md)")
    lines.append("")

    out_path = out_dir / "INDEX_TABLEAUX_MP.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Génération INDEX_ORGANES.md
# ---------------------------------------------------------------------------

def write_index_organes(by_systeme: dict[str, list[dict]],
                        by_patho_type: dict[str, list[dict]],
                        fiches: dict[str, Path],
                        out_dir: Path) -> Path:
    lines = md_header(
        "Index par organe/système cible et par type de pathologie",
        "Entrée par organe cible (poumon, rein, système nerveux…) ou par type de pathologie (cancer, asthme, neuropathie…).",
    )

    # TOC
    lines.append("## Sommaire")
    lines.append("")
    lines.append("- [Partie 1 — Par système / organe cible](#par-systeme)")
    lines.append("- [Partie 2 — Par type de pathologie](#par-type)")
    lines.append("")
    lines.append("---")
    lines.append("")

    # PART 1: par système
    lines.append("## Partie 1 — Par système et organe cible <a id=\"par-systeme\"></a>")
    lines.append("")
    for sys_key in SYSTEME_ORDER:
        if sys_key not in by_systeme:
            continue
        label = SYSTEME_LABEL.get(sys_key, sys_key)
        lines.append(f"### {label}")
        lines.append("")
        lines.append("| Organe | Pathologie | Type | Substances déclenchantes |")
        lines.append("|---|---|---|---|")
        # Dédup par (organe, pathologie)
        seen = set()
        for row in by_systeme[sys_key]:
            key = (row["organe_id"], row["pathologie_id"])
            if key in seen:
                continue
            seen.add(key)
            subs_links = ", ".join(
                fiche_link(s["id"], fiches, s["nom"]) for s in row["substances"]
            )
            lines.append(
                f"| **{row['organe_nom']}** | {row['pathologie_nom']} | {row['pathologie_type']} | {subs_links} |"
            )
        lines.append("")

    lines.append("---")
    lines.append("")

    # PART 2: par type de pathologie
    lines.append("## Partie 2 — Par type de pathologie <a id=\"par-type\"></a>")
    lines.append("")
    type_order = ["cancer", "respiratoire", "neurologique", "cutanee", "autre"]
    for ptype in type_order:
        if ptype not in by_patho_type:
            continue
        label = TYPE_LABEL.get(ptype, ptype)
        items = by_patho_type[ptype]
        lines.append(f"### {label} ({len(items)})")
        lines.append("")
        lines.append("| Pathologie | Sévérité | Substances déclenchantes |")
        lines.append("|---|---|---|")
        for p in items:
            subs_links = ", ".join(
                fiche_link(s["id"], fiches, s["nom"]) for s in p["substances"]
            )
            lines.append(f"| **{p['nom']}** | {p['severite']} | {subs_links} |")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("[← Retour INDEX_MASTER](INDEX_MASTER.md)")
    lines.append("")

    out_path = out_dir / "INDEX_ORGANES.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Génération INDEX_MASTER.md
# ---------------------------------------------------------------------------

def write_index_master(stats: dict, fiches: dict[str, Path], out_dir: Path) -> Path:
    today = datetime.date.today().isoformat()
    lines = [
        "# DEBBY KG — Index maître des supports pédagogiques",
        "",
        "> Point d'entrée unique vers toutes les ressources pédagogiques DEBBY.",
        f"> KG version : `{KG_VERSION}` — Généré : {today}",
        "> Pour les non-développeurs : commencer par [MANUEL_UTILISATEUR.md](../../MANUEL_UTILISATEUR.md)",
        "",
        "---",
        "",
        "## Statistiques du KG",
        "",
        "| Indicateur | Valeur |",
        "|---|---|",
        f"| Substances/agents indexés | **{stats['n_substances']}** |",
        f"| Pathologies professionnelles | **{stats['n_pathologies']}** |",
        f"| Tableaux MP référentiels (INRS) chargés | **{stats['n_tableaux_mp_ref']}** |",
        f"| Tableaux MP couverts par >=1 substance pilote | **{stats['n_tableaux_mp_couverts']}** |",
        f"| &nbsp;&nbsp;&nbsp;&nbsp;dont régime général (RG) | {stats['n_rg_couverts']} |",
        f"| &nbsp;&nbsp;&nbsp;&nbsp;dont régime agricole (RA) | {stats['n_ra_couverts']} |",
        f"| Métiers/secteurs exposés | **{stats['n_metiers']}** |",
        f"| Organes/systèmes cibles | **{stats['n_organes']}** |",
        f"| Examens de surveillance | **{stats['n_examens']}** |",
        f"| Substances CMR catégorie 1 (avéré / présumé) | **{stats['n_cmr_c1']}** ⚠️ |",
        f"| Fiches pédagogiques générées | **{len(fiches)}** |",
        "",
        "---",
        "",
        "## Les 4 index navigables",
        "",
        "### 1. [Index par substance (A→Z)](INDEX_SUBSTANCES.md)",
        "",
        "Toutes les substances et agents (chimiques, biologiques, physiques, organisationnels, RPS) par ordre alphabétique. Utile pour : « j'ai un patient exposé au benzène, quelle est sa fiche ? »",
        "",
        "### 2. [Index par métier / secteur](INDEX_METIERS.md)",
        "",
        "Liste des métiers groupés par secteur (BTP, industrie, santé, agriculture) avec les substances auxquelles ils sont exposés. Utile pour : « je vois demain un peintre carrosserie, qu'est-ce qui le menace ? »",
        "",
        "### 3. [Index par tableau de maladies professionnelles](INDEX_TABLEAUX_MP.md)",
        "",
        "Tableaux MP du régime général (RG) puis du régime agricole (RA), avec pathologies et substances rattachées. Utile pour : « le tableau RG-30 BIS, ça couvre quoi exactement ? »",
        "",
        "### 4. [Index par organe / système / type de pathologie](INDEX_ORGANES.md)",
        "",
        "Entrée par organe cible (poumon, rein, système nerveux…) ou par type de pathologie (cancer, asthme, neuropathie…). Utile pour : « les substances neurotoxiques en milieu professionnel, qu'est-ce qu'on a ? »",
        "",
        "---",
        "",
        "## Ressources connexes",
        "",
        "- **[INDEX.html](INDEX.html)** : version navigable HTML statique (Bootstrap + recherche JavaScript)",
        "- **[Mind maps Markmap](markmaps/INDEX.md)** : 49 mind maps interactives par substance (visualisation hiérarchique)",
        "- **[Graphe global GraphML](debby_kg_full_v0.1.graphml)** : import Gephi / yEd / Cytoscape",
        "- **[Graphe Mermaid global](debby_kg_full_v0.1.mermaid.md)** : rendu dans Obsidian / GitHub",
        "- **[Manuel utilisateur MdT](../../MANUEL_UTILISATEUR.md)** : guide d'usage non-développeur",
        "",
        "## Sources de référence (au-delà du KG)",
        "",
        "- [INRS — Tableaux MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)",
        "- [INRS — Valeurs limites d'exposition (ED 984)](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)",
        "- [HAS — Recommandations professionnelles](https://www.has-sante.fr/)",
        "- [Légifrance — Code du travail (santé/sécurité)](https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006072050/LEGISCTA000006144094)",
        "- MCP SSTinfo (validation en ligne via Claude) : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier`, `aide_decision`",
        "",
        "---",
        "",
        "## Avertissement",
        "",
        "Ces supports pédagogiques sont **auto-générés** depuis le Knowledge Graph DEBBY. Ils agrègent des sources de référence (INRS, HAS, décrets FR) mais **ne remplacent pas** la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.",
        "",
        f"Dernière régénération : **{today}** — KG version : `{KG_VERSION}`",
        "",
    ]

    out_path = out_dir / "INDEX_MASTER.md"
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Génération INDEX.html (Bootstrap CDN + recherche JS)
# ---------------------------------------------------------------------------

def write_index_html(substances: list[dict],
                     by_secteur: dict[str, list[dict]],
                     by_regime: dict[str, list[dict]],
                     by_systeme: dict[str, list[dict]],
                     by_patho_type: dict[str, list[dict]],
                     fiches: dict[str, Path],
                     stats: dict,
                     out_dir: Path) -> Path:
    """Page HTML statique standalone (Bootstrap CDN + recherche JS)."""
    today = datetime.date.today().isoformat()

    # JSON embarqué pour recherche client-side
    search_index = []
    # Substances
    for s in substances:
        has_fiche = s["id"] in fiches
        search_index.append({
            "type": "substance",
            "label": s["nom_fr"],
            "id": s["id"],
            "tag": s["cmr"] or s["categorie"],
            "link": f"fiches/fiche_substance_{s['id']}.md" if has_fiche else "",
        })
    # Métiers
    for sec, metiers in by_secteur.items():
        for m in metiers:
            search_index.append({
                "type": "metier",
                "label": m["nom"],
                "id": m["id"],
                "tag": SECTEUR_LABEL.get(sec, sec),
                "link": "",
            })
    # Tableaux
    for reg, tx in by_regime.items():
        for t in tx:
            search_index.append({
                "type": "tableau_mp",
                "label": f"{t['id']} — {t['intitule']}",
                "id": t["id"],
                "tag": reg,
                "link": f"https://www.inrs.fr/publications/bdd/mp/tableau.html?refINRS={t['id']}",
            })

    search_json = json.dumps(search_index, ensure_ascii=False)

    # Tableau HTML helper
    def table_row(cells):
        return "<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"

    # Onglet substances
    sub_rows = []
    for s in substances:
        link = f'<a href="fiches/fiche_substance_{s["id"]}.md">Voir fiche</a>' if s["id"] in fiches else '<span class="text-muted">à générer</span>'
        cmr_badge = ""
        if s["cmr"] in ("C1A", "C1B"):
            cmr_badge = f'<span class="badge bg-danger">{s["cmr"]}</span>'
        elif s["cmr"]:
            cmr_badge = f'<span class="badge bg-warning text-dark">{s["cmr"]}</span>'
        else:
            cmr_badge = '<span class="text-muted">—</span>'
        vlep = f'<code>{s["vlep_8h"]}</code>' if s["vlep_8h"] is not None else '<span class="text-muted">—</span>'
        sub_rows.append(table_row([
            f'<strong>{s["nom_fr"]}</strong>',
            cmr_badge,
            s["categorie"],
            vlep,
            link,
        ]))

    # Onglet métiers
    metier_blocks = []
    for sec in SECTEUR_ORDER:
        if sec not in by_secteur:
            continue
        header = f'<h3 class="mt-4">{SECTEUR_LABEL[sec]}</h3>'
        rows = []
        for m in by_secteur[sec]:
            subs_html = ", ".join(
                f'<a href="fiches/fiche_substance_{s["id"]}.md">{s["nom"]}</a>' if s["id"] in fiches else s["nom"]
                for s in m["substances"]
            )
            rows.append(table_row([f'<strong>{m["nom"]}</strong>', subs_html]))
        table = (
            '<table class="table table-sm table-striped">'
            '<thead><tr><th>Métier</th><th>Substances exposantes</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
        )
        metier_blocks.append(header + table)

    # Onglet tableaux MP
    tableau_blocks = []
    for reg in ("RG", "RA"):
        if reg not in by_regime:
            continue
        title = "Régime général (RG)" if reg == "RG" else "Régime agricole (RA)"
        header = f'<h3 class="mt-4">{title}</h3>'
        rows = []
        for t in by_regime[reg]:
            patho_str = ", ".join(p["nom"] for p in t["pathologies"][:3])
            if len(t["pathologies"]) > 3:
                patho_str += f' (+{len(t["pathologies"])-3})'
            subs_html = ", ".join(
                f'<a href="fiches/fiche_substance_{s["id"]}.md">{s["nom"]}</a>' if s["id"] in fiches else s["nom"]
                for s in t["substances"]
            )
            inrs_url = f"https://www.inrs.fr/publications/bdd/mp/tableau.html?refINRS={t['id']}"
            rows.append(table_row([
                f'<a href="{inrs_url}" target="_blank"><code>{t["id"]}</code></a>',
                t["intitule"],
                patho_str,
                subs_html,
            ]))
        table = (
            '<table class="table table-sm table-striped">'
            '<thead><tr><th>Tableau</th><th>Intitulé</th><th>Pathologies</th><th>Substances</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
        )
        tableau_blocks.append(header + table)

    # Onglet organes
    organe_blocks = []
    for sys_key in SYSTEME_ORDER:
        if sys_key not in by_systeme:
            continue
        label = SYSTEME_LABEL.get(sys_key, sys_key)
        header = f'<h3 class="mt-4">{label}</h3>'
        rows = []
        seen = set()
        for row in by_systeme[sys_key]:
            key = (row["organe_id"], row["pathologie_id"])
            if key in seen:
                continue
            seen.add(key)
            subs_html = ", ".join(
                f'<a href="fiches/fiche_substance_{s["id"]}.md">{s["nom"]}</a>' if s["id"] in fiches else s["nom"]
                for s in row["substances"]
            )
            rows.append(table_row([
                f'<strong>{row["organe_nom"]}</strong>',
                row["pathologie_nom"],
                row["pathologie_type"],
                subs_html,
            ]))
        table = (
            '<table class="table table-sm table-striped">'
            '<thead><tr><th>Organe</th><th>Pathologie</th><th>Type</th><th>Substances</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>'
        )
        organe_blocks.append(header + table)

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DEBBY KG — Index navigable des supports pédagogiques MdT</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
  <style>
    body {{ padding-top: 1.5rem; padding-bottom: 4rem; }}
    .stat-card {{ font-size: 0.95rem; }}
    .stat-value {{ font-size: 1.6rem; font-weight: 700; color: #0066cc; }}
    .search-result {{ padding: 6px 10px; border-bottom: 1px solid #eee; }}
    .search-result:hover {{ background: #f5f5f5; }}
    .badge-substance {{ background: #e74c3c; }}
    .badge-metier {{ background: #27ae60; }}
    .badge-tableau {{ background: #2980b9; }}
    code {{ background: #f8f9fa; padding: 1px 5px; border-radius: 3px; }}
  </style>
</head>
<body>
<div class="container">

  <h1>DEBBY KG — Supports pédagogiques médecine du travail</h1>
  <p class="text-muted">Auto-généré le {today} depuis le Knowledge Graph DEBBY (<code>{KG_VERSION}</code>).</p>

  <div class="alert alert-info">
    <strong>Pour démarrer :</strong> utiliser la barre de recherche ci-dessous, ou parcourir les 4 onglets.
    Pour les usages métier, voir aussi <a href="../../MANUEL_UTILISATEUR.md">MANUEL_UTILISATEUR.md</a>.
  </div>

  <!-- Stats -->
  <div class="row g-3 mb-4">
    <div class="col-md-3"><div class="card stat-card"><div class="card-body text-center"><div class="stat-value">{stats['n_substances']}</div>Substances/agents</div></div></div>
    <div class="col-md-3"><div class="card stat-card"><div class="card-body text-center"><div class="stat-value">{stats['n_tableaux_mp_couverts']}</div>Tableaux MP couverts</div></div></div>
    <div class="col-md-3"><div class="card stat-card"><div class="card-body text-center"><div class="stat-value">{stats['n_metiers']}</div>Métiers indexés</div></div></div>
    <div class="col-md-3"><div class="card stat-card"><div class="card-body text-center"><div class="stat-value">{stats['n_pathologies']}</div>Pathologies</div></div></div>
  </div>

  <!-- Recherche -->
  <div class="mb-4">
    <label for="searchInput" class="form-label"><strong>Rechercher</strong> (substance, métier, tableau MP, pathologie…) :</label>
    <input type="text" id="searchInput" class="form-control form-control-lg" placeholder="ex : amiante, soudeur, RG-30, mésothéliome…">
    <div id="searchResults" class="mt-2" style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; border-radius: 4px; display: none;"></div>
  </div>

  <!-- Onglets -->
  <ul class="nav nav-tabs" id="myTab" role="tablist">
    <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#substances">Substances ({stats['n_substances']})</button></li>
    <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#metiers">Métiers ({stats['n_metiers']})</button></li>
    <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tableaux">Tableaux MP ({stats['n_tableaux_mp_couverts']})</button></li>
    <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#organes">Organes/Pathologies</button></li>
  </ul>

  <div class="tab-content" id="myTabContent">
    <div class="tab-pane fade show active" id="substances" role="tabpanel">
      <h2 class="mt-3">Substances et agents (ordre alphabétique)</h2>
      <table class="table table-sm table-striped table-hover">
        <thead><tr><th>Substance</th><th>CMR</th><th>Catégorie</th><th>VLEP 8h (mg/m³)</th><th>Fiche</th></tr></thead>
        <tbody>{"".join(sub_rows)}</tbody>
      </table>
    </div>

    <div class="tab-pane fade" id="metiers" role="tabpanel">
      <h2 class="mt-3">Métiers exposés par secteur</h2>
      {"".join(metier_blocks)}
    </div>

    <div class="tab-pane fade" id="tableaux" role="tabpanel">
      <h2 class="mt-3">Tableaux de maladies professionnelles</h2>
      <p>Source : INRS — décompte canonique 175 tableaux (cf. <code>TABLEAUX_MP_REFERENCE.md</code>).</p>
      {"".join(tableau_blocks)}
    </div>

    <div class="tab-pane fade" id="organes" role="tabpanel">
      <h2 class="mt-3">Pathologies par organe / système cible</h2>
      {"".join(organe_blocks)}
    </div>
  </div>

  <footer class="mt-5 pt-3 border-top text-muted small">
    <p>
      <strong>Avertissement :</strong> ces supports sont auto-générés et ne remplacent ni les textes primaires (INRS, HAS, Légifrance)
      ni le jugement clinique. Toujours vérifier la dernière édition des recommandations.
    </p>
    <p>
      Index générés : <a href="INDEX_MASTER.md">INDEX_MASTER.md</a> ·
      <a href="INDEX_SUBSTANCES.md">INDEX_SUBSTANCES.md</a> ·
      <a href="INDEX_METIERS.md">INDEX_METIERS.md</a> ·
      <a href="INDEX_TABLEAUX_MP.md">INDEX_TABLEAUX_MP.md</a> ·
      <a href="INDEX_ORGANES.md">INDEX_ORGANES.md</a>
    </p>
  </footer>
</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
<script>
  const SEARCH_INDEX = {search_json};

  const input = document.getElementById('searchInput');
  const results = document.getElementById('searchResults');

  function badgeClass(type) {{
    if (type === 'substance') return 'badge-substance';
    if (type === 'metier') return 'badge-metier';
    if (type === 'tableau_mp') return 'badge-tableau';
    return 'bg-secondary';
  }}

  input.addEventListener('input', function() {{
    const q = this.value.trim().toLowerCase();
    if (q.length < 2) {{
      results.style.display = 'none';
      results.innerHTML = '';
      return;
    }}
    const hits = SEARCH_INDEX.filter(it =>
      it.label.toLowerCase().includes(q) ||
      it.id.toLowerCase().includes(q) ||
      (it.tag && it.tag.toLowerCase().includes(q))
    ).slice(0, 30);

    if (hits.length === 0) {{
      results.innerHTML = '<div class="search-result text-muted">Aucun résultat</div>';
    }} else {{
      results.innerHTML = hits.map(it => {{
        const linkHtml = it.link
          ? `<a href="${{it.link}}" target="${{it.link.startsWith('http') ? '_blank' : '_self'}}">${{it.label}}</a>`
          : `<span>${{it.label}}</span>`;
        return `<div class="search-result">
          <span class="badge ${{badgeClass(it.type)}}">${{it.type}}</span>
          ${{linkHtml}}
          <span class="text-muted small">— ${{it.tag || ''}}</span>
        </div>`;
      }}).join('');
    }}
    results.style.display = 'block';
  }});

  // Cacher résultats quand on clique en dehors
  document.addEventListener('click', function(e) {{
    if (!input.contains(e.target) && !results.contains(e.target)) {{
      results.style.display = 'none';
    }}
  }});
</script>
</body>
</html>
"""

    out_path = out_dir / "INDEX.html"
    out_path.write_text(html, encoding="utf-8")
    return out_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default=str(DEFAULT_DB))
    ap.add_argument("--fiches-dir", default=str(DEFAULT_FICHES_DIR))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    args = ap.parse_args()

    db = kuzu.Database(args.db_path)
    conn = kuzu.Connection(db)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    fiches = list_fiches(Path(args.fiches_dir))

    print("=" * 80)
    print("DEBBY KG — Construction des index navigables")
    print(f"DB     : {args.db_path}")
    print(f"Fiches : {args.fiches_dir} ({len(fiches)} fiches détectées)")
    print(f"Out    : {args.out_dir}")
    print("=" * 80)

    print("\n→ Collecte des données KG…")
    substances = collect_substance_index(conn)
    by_secteur = collect_metier_index(conn)
    by_regime = collect_tableau_index(conn)
    by_systeme = collect_organe_index(conn)
    by_patho_type = collect_pathologie_type_index(conn)
    stats = compute_stats(conn)
    print(f"  Substances : {len(substances)}")
    print(f"  Métiers    : {sum(len(v) for v in by_secteur.values())} en {len(by_secteur)} secteurs")
    print(f"  Tableaux   : {sum(len(v) for v in by_regime.values())} ({len(by_regime.get('RG', []))} RG + {len(by_regime.get('RA', []))} RA)")
    print(f"  Organes    : {len(by_systeme)} systèmes")

    print("\n→ Génération des index Markdown…")
    p1 = write_index_substances(substances, fiches, out_dir)
    print(f"   {p1}")
    p2 = write_index_metiers(by_secteur, fiches, out_dir)
    print(f"   {p2}")
    p3 = write_index_tableaux_mp(by_regime, fiches, out_dir)
    print(f"   {p3}")
    p4 = write_index_organes(by_systeme, by_patho_type, fiches, out_dir)
    print(f"   {p4}")

    print("\n→ Génération INDEX_MASTER.md…")
    p_master = write_index_master(stats, fiches, out_dir)
    print(f"   {p_master}")

    print("\n→ Génération INDEX.html…")
    p_html = write_index_html(substances, by_secteur, by_regime, by_systeme,
                              by_patho_type, fiches, stats, out_dir)
    print(f"   {p_html}")

    print("\n✅ 6 fichiers générés. Récap stats KG :")
    for k, v in stats.items():
        print(f"   {k:20s} = {v}")


if __name__ == "__main__":
    main()
