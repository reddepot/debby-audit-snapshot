#!/usr/bin/env python3
"""
DEBBY KG — Builder Kuzu v0.1 (10 substances pilotes)
ADR-001 GraphRAG Kuzu comme chef d'œuvre
Version: kuzu-10sub-v0.1

Usage:
    python3 build_kg.py [--rebuild] [--db-path ./kg/data/kuzu.db]

Le script :
1. Crée/recharge la base Kuzu
2. Applique le schéma depuis schema_v0.1.cypher
3. Peuple les nodes depuis substances_pilotes_v0.1.json
4. Charge la liste des 175 tableaux MP depuis TABLEAUX_MP_REFERENCE.md (parser simple)
5. Ajoute les relations CAUSE / CLASSIFIEE_DANS / CONCERNE_METIER / EXPOSE_A / SURVEILLANCE
6. Source les surveillance HAS-2022 / INRS-2017 / décret-2023 avec annee_recommandation
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

try:
    import kuzu
except ImportError:
    sys.exit("kuzu non installé. `pip install kuzu networkx`")

REPO_ROOT = Path(__file__).resolve().parents[2]
KG_DIR = REPO_ROOT / "kg"
SCHEMA_PATH = KG_DIR / "schema" / "schema_v0.1.cypher"
SUBSTANCES_JSON = KG_DIR / "data" / "substances_pilotes_v0.1.json"
TABLEAUX_MP_REF = REPO_ROOT / "TABLEAUX_MP_REFERENCE.md"
DEFAULT_DB = KG_DIR / "data" / "kuzu.db"


def apply_schema(conn: "kuzu.Connection") -> None:
    """Apply Cypher DDL schema, statement by statement."""
    raw = SCHEMA_PATH.read_text(encoding="utf-8")
    # Strip line comments
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("//")]
    body = "\n".join(lines)
    stmts = [s.strip() for s in body.split(";") if s.strip()]
    for stmt in stmts:
        try:
            conn.execute(stmt)
        except Exception as e:
            print(f"  ⚠️ schema stmt failed: {stmt[:80]}... → {e}", file=sys.stderr)


def load_substances(conn: "kuzu.Connection") -> dict:
    """Insert Substance nodes from substances_pilotes_v0.1.json. Returns dict id->row."""
    data = json.loads(SUBSTANCES_JSON.read_text(encoding="utf-8"))
    rows = data["substances"]
    print(f"→ Loading {len(rows)} substances pilotes…")
    for r in rows:
        conn.execute(
            """
            CREATE (s:Substance {
                id: $id,
                nom_fr: $nom_fr,
                nom_en: $nom_en,
                cas: $cas,
                chebi_id: $chebi_id,
                categorie: $categorie,
                cmr: $cmr,
                vlep_8h_mg_m3: $vlep_8h,
                vlep_ct_mg_m3: $vlep_ct,
                source_url: $source_url,
                source_chunk_ids: []
            })
            """,
            parameters={
                "id": r["id"],
                "nom_fr": r["nom_fr"],
                "nom_en": r.get("nom_en", ""),
                "cas": r.get("cas", ""),
                "chebi_id": r.get("chebi_id", ""),
                "categorie": r.get("categorie", ""),
                "cmr": r.get("cmr", ""),
                "vlep_8h": float(r["vlep_8h_mg_m3"]) if r.get("vlep_8h_mg_m3") is not None else None,
                "vlep_ct": float(r["vlep_ct_mg_m3"]) if r.get("vlep_ct_mg_m3") is not None else None,
                "source_url": r.get("source_url", ""),
            },
        )
    return {r["id"]: r for r in rows}


def load_pathologies(conn: "kuzu.Connection", substances: dict) -> set:
    """Insert Pathologie nodes derived from substances_pilotes_v0.1.json. Returns set of ids."""
    patho_seen = {}
    for sub in substances.values():
        for p_id in sub.get("pathologies", []):
            if p_id not in patho_seen:
                # Heuristique type / severite
                if any(k in p_id for k in ["cancer", "leucemie", "mesotheliome", "lymphome"]):
                    type_ = "cancer"
                    severite = "grave"
                elif any(k in p_id for k in ["asthme", "pneumopathie", "asbestose", "silicose", "broncho"]):
                    type_ = "respiratoire"
                    severite = "moderee"
                elif any(k in p_id for k in ["dermatite", "eczema", "ulceration", "plaques"]):
                    type_ = "cutanee"
                    severite = "legere"
                elif any(k in p_id for k in ["neuropathie", "encephalopathie", "tremblement", "intoxication"]):
                    type_ = "neurologique"
                    severite = "moderee"
                else:
                    type_ = "autre"
                    severite = "moderee"
                patho_seen[p_id] = {"id": p_id, "type": type_, "severite": severite}

    print(f"→ Loading {len(patho_seen)} pathologies dérivées…")
    for p in patho_seen.values():
        nom_fr = p["id"].replace("_", " ").capitalize()
        conn.execute(
            """
            CREATE (p:Pathologie {
                id: $id,
                nom_fr: $nom_fr,
                nom_en: '',
                icd11_code: '',
                snomed_ct_fr: '',
                mesh_id: '',
                type: $type,
                severite: $severite,
                reversibilite: 'variable',
                source_chunk_ids: []
            })
            """,
            parameters={"id": p["id"], "nom_fr": nom_fr, "type": p["type"], "severite": p["severite"]},
        )
    return set(patho_seen.keys())


def load_tableaux_mp(conn: "kuzu.Connection", substances: dict) -> set:
    """Insert Tableau_MP nodes for those referenced by 10 substances + key BIS/TER."""
    tableaux = set()
    for sub in substances.values():
        for t_id in sub.get("tableaux_mp", []):
            tableaux.add(t_id)

    print(f"→ Loading {len(tableaux)} tableaux MP cités par les 10 substances…")
    for t_id in sorted(tableaux):
        # Parse id ex 'RG-30-TER' → regime=RG, numero=30, variante=TER
        m = re.match(r"^(RG|RA)-(\d+)(?:-(BIS|TER))?$", t_id)
        if not m:
            print(f"  ⚠️ id tableau MP mal formé: {t_id}", file=sys.stderr)
            continue
        regime, numero, variante = m.group(1), int(m.group(2)), m.group(3) or ""
        intitule = f"Tableau {regime} n°{numero}" + (f" {variante}" if variante else "")
        conn.execute(
            """
            CREATE (t:Tableau_MP {
                id: $id,
                regime: $regime,
                numero: $numero,
                variante: $variante,
                intitule: $intitule,
                agent_causal: [],
                pathologie_couverte: [],
                delai_prise_en_charge_jours: 0,
                duree_exposition_min_jours: 0,
                liste_travaux: '',
                date_creation: '',
                date_derniere_revision: '',
                source_url: 'https://www.inrs.fr/publications/bdd/mp/listeTableaux.html'
            })
            """,
            parameters={"id": t_id, "regime": regime, "numero": numero, "variante": variante, "intitule": intitule},
        )
    return tableaux


def load_metiers(conn: "kuzu.Connection", substances: dict) -> set:
    metiers = set()
    for sub in substances.values():
        for m in sub.get("metiers_exposes", []):
            metiers.add(m)

    print(f"→ Loading {len(metiers)} métiers exposés…")
    for m_id in sorted(metiers):
        nom_fr = m_id.replace("_", " ").capitalize()
        # secteur heuristique
        if any(k in m_id for k in ["couvreur", "macon", "tailleur_pierre", "carrier"]):
            secteur = "BTP"
        elif any(k in m_id for k in ["soudeur", "fondeur", "chromage", "galvaniseur", "ouvrier", "metallurgiste"]):
            secteur = "industrie"
        elif any(k in m_id for k in ["dentiste", "personnel"]):
            secteur = "sante"
        elif any(k in m_id for k in ["agriculteur", "orpaillage"]):
            secteur = "agriculture"
        else:
            secteur = "industrie"
        conn.execute(
            """
            CREATE (m:Metier {
                id: $id,
                nom_fr: $nom_fr,
                nom_en: '',
                naf_codes: [],
                rome_codes: [],
                secteur: $secteur,
                source_chunk_ids: []
            })
            """,
            parameters={"id": m_id, "nom_fr": nom_fr, "secteur": secteur},
        )
    return metiers


def load_organes(conn: "kuzu.Connection") -> set:
    """Insert basic Organe nodes for the 10 pilot substances."""
    organes = [
        ("poumon", "Poumon", "respiratoire"),
        ("plevre", "Plèvre", "respiratoire"),
        ("voies_aeriennes_sup", "Voies aériennes supérieures", "respiratoire"),
        ("moelle_osseuse", "Moelle osseuse", "hematopoietique"),
        ("systeme_nerveux", "Système nerveux", "neurologique"),
        ("rein", "Rein", "urinaire"),
        ("peau", "Peau", "tegumentaire"),
        ("foie", "Foie", "digestif"),
        ("os", "Os", "musculo_squelettique"),
    ]
    print(f"→ Loading {len(organes)} organes…")
    for o_id, nom_fr, systeme in organes:
        conn.execute(
            "CREATE (o:Organe {id: $id, nom_fr: $nom_fr, nom_en: '', systeme: $systeme})",
            parameters={"id": o_id, "nom_fr": nom_fr, "systeme": systeme},
        )
    return {o[0] for o in organes}


def load_examens(conn: "kuzu.Connection") -> set:
    examens = [
        ("scanner_thoracique", "Scanner thoracique", "imagerie", 150.0, True, "HAS-2022"),
        ("radiographie_thoracique", "Radiographie thoracique", "imagerie", 30.0, True, "HAS-2010"),
        ("audiogramme", "Audiogramme", "fonctionnel", 35.0, False, "INRS-2021"),
        ("efr", "Épreuves fonctionnelles respiratoires (EFR)", "fonctionnel", 80.0, False, "INRS-2017"),
        ("plombemie", "Plombémie sanguine", "biologique", 25.0, False, "Décret-3-mai-2023"),
        ("dosage_chrome_urinaire", "Dosage chrome urinaire", "biologique", 30.0, False, "INRS-2020"),
        ("dosage_cadmium_urinaire", "Dosage cadmium urinaire", "biologique", 30.0, False, "INRS-2020"),
        ("creatinemie", "Créatininémie", "biologique", 10.0, False, "HAS-2020"),
    ]
    print(f"→ Loading {len(examens)} examens de surveillance…")
    for e_id, nom_fr, type_, cout, irradiant, source in examens:
        conn.execute(
            """
            CREATE (e:Examen {
                id: $id, nom_fr: $nom_fr, type: $type, cout_estime_eur: $cout,
                irradiant: $irradiant, source_recommandation: $source
            })
            """,
            parameters={"id": e_id, "nom_fr": nom_fr, "type": type_, "cout": cout, "irradiant": irradiant, "source": source},
        )
    return {e[0] for e in examens}


def link_relations(conn: "kuzu.Connection", substances: dict, patho_ids: set, tableaux: set, metiers: set, organes: set) -> None:
    """Create CAUSE, CLASSIFIEE_DANS, CONCERNE_METIER, EXPOSE_A, CONCERNE_ORGANE, SURVEILLANCE."""
    print("→ Creating relations…")

    # IARC normalization map
    def iarc_to_evidence(iarc: str) -> str:
        return {"1": "IARC-1", "2A": "IARC-2A", "2B": "IARC-2B", "3": "IARC-3", "4": "IARC-4"}.get(iarc, "")

    # CAUSE (Substance → Pathologie)
    for sub in substances.values():
        for p_id in sub.get("pathologies", []):
            conn.execute(
                """
                MATCH (s:Substance {id:$sid}), (p:Pathologie {id:$pid})
                CREATE (s)-[:CAUSE {niveau_evidence:$iarc, latence_mediane_annees:0.0, risque_relatif:0.0, source_chunk_ids:[]}]->(p)
                """,
                parameters={"sid": sub["id"], "pid": p_id, "iarc": iarc_to_evidence(sub.get("iarc", ""))},
            )

    # CLASSIFIEE_DANS (Pathologie → Tableau_MP) — derived from pathology naming and substance tableaux
    for sub in substances.values():
        for p_id in sub.get("pathologies", []):
            for t_id in sub.get("tableaux_mp", []):
                conn.execute(
                    """
                    MATCH (p:Pathologie {id:$pid}), (t:Tableau_MP {id:$tid})
                    CREATE (p)-[:CLASSIFIEE_DANS {completeness:'partielle', source_chunk_ids:[]}]->(t)
                    """,
                    parameters={"pid": p_id, "tid": t_id},
                )

    # CONCERNE_METIER (Tableau_MP → Metier) — tied via substance metiers_exposes
    for sub in substances.values():
        for t_id in sub.get("tableaux_mp", []):
            for m_id in sub.get("metiers_exposes", []):
                conn.execute(
                    """
                    MATCH (t:Tableau_MP {id:$tid}), (m:Metier {id:$mid})
                    CREATE (t)-[:CONCERNE_METIER {frequence_exposition:'quotidienne', source_chunk_ids:[]}]->(m)
                    """,
                    parameters={"tid": t_id, "mid": m_id},
                )

    # EXPOSE_A (Metier → Substance)
    for sub in substances.values():
        for m_id in sub.get("metiers_exposes", []):
            conn.execute(
                """
                MATCH (m:Metier {id:$mid}), (s:Substance {id:$sid})
                CREATE (m)-[:EXPOSE_A {niveau_exposition:'modere', poste_type:'', source_chunk_ids:[]}]->(s)
                """,
                parameters={"mid": m_id, "sid": sub["id"]},
            )

    # CONCERNE_ORGANE (Pathologie → Organe) — heuristic mapping
    patho_organe_map = {
        "mesotheliome": "plevre",
        "asbestose": "poumon",
        "cancer_broncho_pulmonaire_amiante": "poumon",
        "plaques_pleurales": "plevre",
        "saturnisme": "systeme_nerveux",
        "neuropathie_peripherique_plomb": "systeme_nerveux",
        "encephalopathie_plomb": "systeme_nerveux",
        "nephropathie_plomb": "rein",
        "leucemie_myeloide": "moelle_osseuse",
        "aplasie_medullaire": "moelle_osseuse",
        "lymphome_non_hodgkinien": "moelle_osseuse",
        "silicose": "poumon",
        "cancer_pulmonaire_silice": "poumon",
        "scleroderme_systemique": "peau",
        "asthme_isocyanates": "poumon",
        "pneumopathie_hypersensibilite": "poumon",
        "cancer_nasopharynx": "voies_aeriennes_sup",
        "asthme_formaldehyde": "poumon",
        "dermatite_formaldehyde": "peau",
        "asthme_chromates": "poumon",
        "cancer_broncho_pulmonaire_chrome": "poumon",
        "ulcerations_cutanees_chrome": "peau",
        "cancer_naso_sinusien_nickel": "voies_aeriennes_sup",
        "asthme_nickel": "poumon",
        "eczema_nickel": "peau",
        "cancer_pulmonaire_cadmium": "poumon",
        "nephropathie_cadmium": "rein",
        "osteomalacie_cadmium": "os",
        "intoxication_mercurielle": "systeme_nerveux",
        "neuropathie_mercure": "systeme_nerveux",
        "tremblement_intentionnel_mercure": "systeme_nerveux",
    }
    for p_id, o_id in patho_organe_map.items():
        if p_id in patho_ids and o_id in organes:
            atteinte = "cancereux" if "cancer" in p_id or "lymphome" in p_id or "leucemie" in p_id or "mesotheliome" in p_id else "lesion"
            conn.execute(
                """
                MATCH (p:Pathologie {id:$pid}), (o:Organe {id:$oid})
                CREATE (p)-[:CONCERNE_ORGANE {type_atteinte:$atteinte, source_chunk_ids:[]}]->(o)
                """,
                parameters={"pid": p_id, "oid": o_id, "atteinte": atteinte},
            )

    # SURVEILLANCE (Pathologie → Examen) — based on HAS-2022 / INRS-2017 / décret-2023
    surveillance_links = [
        ("mesotheliome", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("asbestose", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("cancer_broncho_pulmonaire_amiante", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("plaques_pleurales", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("saturnisme", "plombemie", 6, True, "Décret-3-mai-2023", 2023),
        ("neuropathie_peripherique_plomb", "plombemie", 6, True, "Décret-3-mai-2023", 2023),
        ("nephropathie_plomb", "creatinemie", 12, True, "Décret-3-mai-2023", 2023),
        ("silicose", "scanner_thoracique", 24, True, "INRS-2017", 2017),
        ("cancer_pulmonaire_silice", "scanner_thoracique", 24, True, "HAS-2022", 2022),
        ("asthme_isocyanates", "efr", 12, True, "INRS-2017", 2017),
        ("asthme_chromates", "efr", 12, True, "INRS-2017", 2017),
        ("cancer_broncho_pulmonaire_chrome", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("ulcerations_cutanees_chrome", "dosage_chrome_urinaire", 12, True, "INRS-2020", 2020),
        ("cancer_naso_sinusien_nickel", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("cancer_pulmonaire_cadmium", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("nephropathie_cadmium", "dosage_cadmium_urinaire", 12, True, "INRS-2020", 2020),
    ]
    for p_id, e_id, perio, oblig, source, annee in surveillance_links:
        if p_id in patho_ids:
            conn.execute(
                """
                MATCH (p:Pathologie {id:$pid}), (e:Examen {id:$eid})
                CREATE (p)-[:SURVEILLANCE {periodicite_mois:$perio, obligatoire:$oblig,
                                           source_recommandation:$source, annee_recommandation:$annee,
                                           source_chunk_ids:[]}]->(e)
                """,
                parameters={"pid": p_id, "eid": e_id, "perio": perio, "oblig": oblig, "source": source, "annee": annee},
            )


def stats(conn: "kuzu.Connection") -> None:
    print("\n=== STATS ===")
    for label in ["Substance", "Pathologie", "Tableau_MP", "Metier", "Organe", "Examen"]:
        r = conn.execute(f"MATCH (n:{label}) RETURN count(n)")
        cnt = r.get_next()[0]
        print(f"  {label:15s}: {cnt}")
    for rel in ["CAUSE", "CLASSIFIEE_DANS", "CONCERNE_METIER", "EXPOSE_A", "CONCERNE_ORGANE", "SURVEILLANCE"]:
        r = conn.execute(f"MATCH ()-[r:{rel}]->() RETURN count(r)")
        cnt = r.get_next()[0]
        print(f"  -{rel:15s}: {cnt}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default=str(DEFAULT_DB))
    ap.add_argument("--rebuild", action="store_true", help="Supprime la base existante avant rebuild")
    args = ap.parse_args()

    db_path = Path(args.db_path)
    if args.rebuild and db_path.exists():
        print(f"→ Suppression base existante {db_path}…")
        if db_path.is_dir():
            import shutil
            shutil.rmtree(db_path)
        else:
            db_path.unlink()

    db_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"→ Création/ouverture base Kuzu : {db_path}")
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)

    apply_schema(conn)
    substances = load_substances(conn)
    patho_ids = load_pathologies(conn, substances)
    tableaux = load_tableaux_mp(conn, substances)
    metiers = load_metiers(conn, substances)
    organes = load_organes(conn)
    examens = load_examens(conn)
    link_relations(conn, substances, patho_ids, tableaux, metiers, organes)
    stats(conn)

    print(f"\n✅ KG construit avec succès : {db_path}")
    print("   → Tester avec : python3 kg/scripts/query_kg.py")


if __name__ == "__main__":
    main()
