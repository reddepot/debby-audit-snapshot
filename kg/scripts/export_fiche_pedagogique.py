#!/usr/bin/env python3
"""
DEBBY KG — Export fiche métier pédagogique Markdown + Mermaid
ADR-002 Export pédagogique KG → supports formation MdT / DES MST.

Usage:
    python3 kg/scripts/export_fiche_pedagogique.py --substance amiante
    python3 kg/scripts/export_fiche_pedagogique.py --metier soudeur_inox
"""
import argparse
import datetime
import sys
from pathlib import Path

try:
    import kuzu
except ImportError:
    sys.exit("kuzu requis. `pip install kuzu`")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "kg" / "data" / "kuzu.db"
DEFAULT_OUT = REPO_ROOT / "kg" / "exports" / "fiches"

KG_VERSION = "kuzu-10sub-v0.1"


def fetch_one(conn, query, parameters=None):
    r = conn.execute(query, parameters or {})
    if r.has_next():
        return r.get_next()
    return None


def fetch_all(conn, query, parameters=None):
    r = conn.execute(query, parameters or {})
    rows = []
    while r.has_next():
        rows.append(r.get_next())
    return rows


def generate_fiche_substance(conn, sid: str) -> str:
    """Génère une fiche pédagogique Markdown pour une substance donnée."""
    s = fetch_one(conn, "MATCH (s:Substance {id:$id}) RETURN s.nom_fr, s.nom_en, s.cas, s.cmr, s.vlep_8h_mg_m3, s.vlep_ct_mg_m3, s.categorie, s.source_url", {"id": sid})
    if not s:
        raise SystemExit(f"Substance {sid} non trouvée dans le KG")

    nom_fr, nom_en, cas, cmr, vlep_8h, vlep_ct, categorie, source_url = s

    pathologies = fetch_all(conn, "MATCH (s:Substance {id:$id})-[c:CAUSE]->(p:Pathologie) RETURN p.id AS p_id, p.nom_fr AS p_nom, p.type AS p_type, p.severite AS p_sev, c.niveau_evidence AS niveau ORDER BY p_sev DESC, p_nom", {"id": sid})

    tableaux = fetch_all(conn, "MATCH (s:Substance {id:$id})-[:CAUSE]->(p:Pathologie)-[:CLASSIFIEE_DANS]->(t:Tableau_MP) RETURN DISTINCT t.id AS t_id, t.intitule AS t_intitule, t.regime AS t_regime, t.numero AS t_num, t.variante AS t_variante ORDER BY t_regime, t_num, t_variante", {"id": sid})

    metiers = fetch_all(conn, "MATCH (m:Metier)-[:EXPOSE_A]->(s:Substance {id:$id}) RETURN m.id AS m_id, m.nom_fr AS m_nom, m.secteur AS m_secteur ORDER BY m_secteur, m_nom", {"id": sid})

    organes = fetch_all(conn, "MATCH (s:Substance {id:$id})-[:CAUSE]->(p:Pathologie)-[:CONCERNE_ORGANE]->(o:Organe) RETURN DISTINCT o.nom_fr AS o_nom, o.systeme AS o_sys ORDER BY o_nom", {"id": sid})

    surveillances = fetch_all(conn, """
        MATCH (s:Substance {id:$id})-[:CAUSE]->(p:Pathologie)-[r:SURVEILLANCE]->(e:Examen)
        RETURN DISTINCT p.nom_fr AS patho, e.nom_fr AS examen, r.periodicite_mois AS perio,
                        r.source_recommandation AS reco, r.annee_recommandation AS annee
        ORDER BY annee DESC
        """, {"id": sid})

    today = datetime.date.today().isoformat()

    md_lines = []
    md_lines.append(f"# Fiche pédagogique — **{nom_fr}**")
    md_lines.append("")
    md_lines.append(f"> Auto-générée depuis DEBBY KG ({KG_VERSION})  ")
    md_lines.append(f"> Date : {today}  ")
    md_lines.append("> Usage : formation MdT / DES MST. **Ne remplace pas le jugement clinique.**  ")
    md_lines.append("> Sources primaires : INRS, HAS, Décrets FR. Cf. liens en bas de page.  ")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # Section 1 — Identification
    md_lines.append("## 1. Identification chimique")
    md_lines.append("")
    md_lines.append(f"- **Nom français** : {nom_fr}")
    if nom_en:
        md_lines.append(f"- **Nom anglais** : {nom_en}")
    if cas:
        md_lines.append(f"- **N° CAS** : `{cas}`")
    if categorie:
        md_lines.append(f"- **Catégorie** : {categorie}")
    if cmr:
        cmr_label = {
            "C1A": "Cancérogène avéré 1A", "C1B": "Cancérogène présumé 1B", "C2": "Cancérogène suspecté",
            "M1A": "Mutagène 1A", "M1B": "Mutagène 1B", "M2": "Mutagène suspecté",
            "R1A": "Reprotoxique 1A", "R1B": "Reprotoxique 1B", "R2": "Reprotoxique suspecté",
        }.get(cmr, cmr)
        md_lines.append(f"- **CMR (CLP)** : **{cmr_label}** ⚠️")
    if vlep_8h is not None:
        md_lines.append(f"- **VLEP 8h** : `{vlep_8h} mg/m³`")
    if vlep_ct is not None:
        md_lines.append(f"- **VLEP court terme** : `{vlep_ct} mg/m³`")
    md_lines.append("")

    # Section 2 — Pathologies
    md_lines.append("## 2. Pathologies professionnelles induites")
    md_lines.append("")
    if pathologies:
        md_lines.append("| Pathologie | Type | Sévérité | Niveau de preuve |")
        md_lines.append("|---|---|---|---|")
        for row in pathologies:
            p_id, p_nom, p_type, p_sev, niveau = row
            niveau_lbl = niveau or "—"
            md_lines.append(f"| **{p_nom}** | {p_type} | {p_sev} | {niveau_lbl} |")
    else:
        md_lines.append("_Aucune pathologie connue dans le KG._")
    md_lines.append("")

    # Section 3 — Tableaux MP
    md_lines.append("## 3. Tableaux de maladies professionnelles applicables")
    md_lines.append("")
    if tableaux:
        md_lines.append("| Tableau | Intitulé | Régime | Variante |")
        md_lines.append("|---|---|---|---|")
        for row in tableaux:
            t_id, t_intitule, t_regime, t_num, t_variante = row
            variante_lbl = t_variante or "—"
            md_lines.append(f"| **`{t_id}`** | {t_intitule} | {t_regime} | {variante_lbl} |")
    else:
        md_lines.append("_Aucun tableau MP rattaché dans le KG._")
    md_lines.append("")
    md_lines.append("> ℹ️ Pour chaque tableau, vérifier :")
    md_lines.append("> - Délai de prise en charge")
    md_lines.append("> - Durée d'exposition minimale")
    md_lines.append("> - Liste limitative ou indicative des travaux")
    md_lines.append("> via [INRS BDD MP](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) ou MCP SSTinfo `lookup_tableau_mp`.")
    md_lines.append("")

    # Section 4 — Métiers exposés
    md_lines.append("## 4. Métiers et secteurs exposés")
    md_lines.append("")
    if metiers:
        # Group by secteur
        by_secteur = {}
        for row in metiers:
            m_id, m_nom, m_secteur = row
            by_secteur.setdefault(m_secteur or "non classé", []).append(m_nom)
        for secteur, names in sorted(by_secteur.items()):
            md_lines.append(f"**{secteur.upper()}** : {', '.join(names)}")
            md_lines.append("")
    else:
        md_lines.append("_Aucun métier exposé renseigné dans le KG._")
        md_lines.append("")

    # Section 5 — Organes cibles
    md_lines.append("## 5. Organes/systèmes cibles")
    md_lines.append("")
    if organes:
        for row in organes:
            o_nom, o_sys = row
            md_lines.append(f"- **{o_nom}** (système {o_sys})")
    else:
        md_lines.append("_Aucun organe cible renseigné._")
    md_lines.append("")

    # Section 6 — Surveillance médicale
    md_lines.append("## 6. Surveillance médicale recommandée")
    md_lines.append("")
    if surveillances:
        md_lines.append("| Pathologie ciblée | Examen | Périodicité | Source | Année |")
        md_lines.append("|---|---|---|---|---|")
        for patho, examen, perio, reco, annee in surveillances:
            perio_lbl = f"{perio} mois" if perio else "—"
            md_lines.append(f"| {patho} | **{examen}** | {perio_lbl} | `{reco}` | {annee} |")
        md_lines.append("")
        md_lines.append("> ⚠️ **Toujours vérifier la dernière édition des recommandations** (HAS, INRS, décrets en vigueur).")
        md_lines.append("> Cette fiche est versionnée KG=`" + KG_VERSION + "` — si > 6 mois, ré-exécuter le pipeline KG pour intégrer les mises à jour réglementaires.")
    else:
        md_lines.append("_Aucune surveillance recommandée renseignée dans le KG._")
    md_lines.append("")

    # Section 7 — Graphe Mermaid focalisé
    md_lines.append("## 7. Vue graphique focalisée")
    md_lines.append("")
    md_lines.append("```mermaid")
    md_lines.append("graph LR")
    md_lines.append(f'    S["{nom_fr}"]')
    for row in pathologies[:5]:
        p_id, p_nom = row[0], row[1]
        md_lines.append(f'    {p_id}["{p_nom}"]')
        md_lines.append(f"    S -->|CAUSE| {p_id}")
    for row in tableaux[:8]:
        t_id = row[0]
        t_slug = t_id.replace("-", "_")
        md_lines.append(f'    {t_slug}["{t_id}"]')
        # link first pathology that maps to this tableau (heuristic: visual only)
        if pathologies:
            md_lines.append(f"    {pathologies[0][0]} -.->|classifiée dans| {t_slug}")
    md_lines.append("    classDef substance fill:#ffcccc,stroke:#990000")
    md_lines.append("    classDef patho fill:#fff2cc,stroke:#cc7700")
    md_lines.append("    classDef tableau fill:#ccebff,stroke:#0066cc")
    md_lines.append("    class S substance")
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("> Pour la vue complète : `kg/exports/debby_kg_" + sid + "_v0.1.mermaid.md`")
    md_lines.append("")

    # Section 8 — Sources et traçabilité
    md_lines.append("## 8. Sources et traçabilité")
    md_lines.append("")
    md_lines.append(f"- **Source officielle substance** : {source_url or 'INRS'}")
    md_lines.append("- **Tableaux MP** : [INRS bdd/mp/listeTableaux.html](https://www.inrs.fr/publications/bdd/mp/listeTableaux.html) (vérifié 2026-05-27, 175 tableaux dont 28 BIS/TER)")
    md_lines.append("- **VLEP** : [INRS ED 984 — Valeurs limites](https://www.inrs.fr/publications/outils/aide-substances-cmr.html)")
    md_lines.append("- **Recommandations HAS** : [has-sante.fr](https://www.has-sante.fr/)")
    md_lines.append("- **MCP SSTinfo** : `lookup_substance`, `lookup_tableau_mp`, `lookup_metier` pour validation en ligne")
    md_lines.append("- **Corpus DEBBY** : 2,6 M œuvres, 22,9 M chunks (cf. `DEBBY_AUDIT_SNAPSHOT.md`)")
    md_lines.append("")
    md_lines.append("## 9. Versioning")
    md_lines.append("")
    md_lines.append(f"- `kg_version` : `{KG_VERSION}`")
    md_lines.append("- `corpus_version` : `2.1` (cf. `VERSIONS.md`)")
    md_lines.append(f"- `fiche_generated_at` : `{today}`")
    md_lines.append(f"- `pipeline` : `kg/scripts/export_fiche_pedagogique.py --substance {sid}`")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("**Avertissement** : Cette fiche est un support pédagogique généré automatiquement depuis le KG DEBBY. Elle agrège des sources de référence (INRS, HAS, décrets FR) mais ne remplace pas la lecture des textes primaires ni le jugement clinique du médecin du travail. Toujours vérifier les recommandations en vigueur pour la prise de décision.")

    return "\n".join(md_lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default=str(DEFAULT_DB))
    ap.add_argument("--substance", required=True, help="ID substance (ex: amiante, plomb, benzene)")
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    db = kuzu.Database(args.db_path)
    conn = kuzu.Connection(db)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"fiche_substance_{args.substance}.md"

    md = generate_fiche_substance(conn, args.substance)
    out_path.write_text(md, encoding="utf-8")
    print(f"✅ Fiche pédagogique générée : {out_path}")
    print(f"   {len(md)} chars, {len(md.splitlines())} lignes")


if __name__ == "__main__":
    main()
