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
SUBSTANCES_JSON = KG_DIR / "data" / "substances_pilotes_v0.2.json"
TABLEAUX_MP_JSON = KG_DIR / "data" / "tableaux_mp_v0.2.json"
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
    """Insert Tableau_MP nodes from tableaux_mp_v0.2.json (intitulés réels INRS).

    Stratégie A2 :
    - Source primaire = tableaux_mp_v0.2.json (192 tableaux INRS validés)
    - Tableaux additionnels cités par les substances mais absents du JSON → ajoutés
      avec intitulé générique (rare, principalement pour cohérence référentielle)
    - Stockage : intitule réel + agent_causal[] + pathologie_couverte[] +
      delai_prise_en_charge_jours quand renseignés dans le JSON.
    """
    tableaux_inserted = set()

    # Charger le référentiel JSON 192 tableaux
    if TABLEAUX_MP_JSON.exists():
        data = json.loads(TABLEAUX_MP_JSON.read_text(encoding="utf-8"))
        rows = data.get("tableaux", [])
        print(f"→ Loading {len(rows)} tableaux MP depuis {TABLEAUX_MP_JSON.name}…")
        for r in rows:
            t_id = r["id"]
            regime = r.get("regime") or ""
            numero = int(r.get("numero") or 0)
            variante = r.get("variante") or ""
            intitule = r.get("intitule") or f"Tableau {regime} n°{numero}" + (f" {variante}" if variante else "")
            agents = r.get("agent_causal") or []
            # Tolérance typo : pathologie_couverte / pathologie_couregistere (typo source A12)
            pathologies = r.get("pathologie_couverte") or r.get("pathologie_couregistere") or []
            delai = int(r.get("delai_prise_en_charge_jours") or 0)
            duree_min = int(r.get("duree_exposition_min_jours") or 0)
            liste_travaux = r.get("liste_travaux") or ""
            date_creation = r.get("date_creation") or ""
            date_derniere_revision = r.get("date_derniere_revision") or ""
            source_url = r.get("source_url") or "https://www.inrs.fr/publications/bdd/mp/listeTableaux.html"
            conn.execute(
                """
                CREATE (t:Tableau_MP {
                    id: $id,
                    regime: $regime,
                    numero: $numero,
                    variante: $variante,
                    intitule: $intitule,
                    agent_causal: $agents,
                    pathologie_couverte: $pathologies,
                    delai_prise_en_charge_jours: $delai,
                    duree_exposition_min_jours: $duree_min,
                    liste_travaux: $liste_travaux,
                    date_creation: $date_creation,
                    date_derniere_revision: $date_derniere_revision,
                    source_url: $source_url
                })
                """,
                parameters={
                    "id": t_id, "regime": regime, "numero": numero, "variante": variante,
                    "intitule": intitule, "agents": agents, "pathologies": pathologies,
                    "delai": delai, "duree_min": duree_min, "liste_travaux": liste_travaux,
                    "date_creation": date_creation, "date_derniere_revision": date_derniere_revision,
                    "source_url": source_url,
                },
            )
            tableaux_inserted.add(t_id)
    else:
        print(f"  ⚠️ {TABLEAUX_MP_JSON} introuvable — fallback aux seuls tableaux des substances", file=sys.stderr)

    # Compléter avec tableaux cités par les substances mais absents du JSON (cohérence)
    cited_by_substances = set()
    for sub in substances.values():
        for t_id in sub.get("tableaux_mp", []):
            cited_by_substances.add(t_id)
    missing = cited_by_substances - tableaux_inserted
    if missing:
        print(f"→ {len(missing)} tableau(x) cité(s) par substances mais absent(s) du JSON → ajout générique…")
        for t_id in sorted(missing):
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
            tableaux_inserted.add(t_id)

    return tableaux_inserted


def load_metiers(conn: "kuzu.Connection", substances: dict) -> set:
    metiers = set()
    for sub in substances.values():
        for m in sub.get("metiers_exposes", []):
            metiers.add(m)

    print(f"→ Loading {len(metiers)} métiers exposés…")

    def classify_secteur(m_id: str) -> str:
        """Heuristique secteur étendue 49 substances."""
        if any(k in m_id for k in ["BTP", "couvreur", "macon", "tailleur_pierre", "carrier", "demolisseur",
                                    "calorifugeur", "plombier", "charpentier", "parqueteur", "peintre_batiment",
                                    "peintre_renovation", "scieur", "etancheur"]):
            return "BTP"
        if any(k in m_id for k in ["soignant", "infirmier", "aide_soignant", "dentiste", "personnel_morgue",
                                    "personnel_anatomopathologie", "veterinaire", "manipulateur_radio",
                                    "radiologue", "cardiologue", "ophtalmologue", "pharmacien", "aidant",
                                    "sante", "soignant_urgences", "irm_irmiste", "laboratoire_histo",
                                    "prothesiste_dentaire"]):
            return "sante"
        if any(k in m_id for k in ["agriculteur", "applicateur_phytosanitaire", "viticulteur", "jardinier",
                                    "eleveur", "forestier", "orpaillage"]):
            return "agriculture"
        if any(k in m_id for k in ["bureau_tertiaire", "developpeur", "secretaire", "centre_appels",
                                    "graphiste", "cadre", "commercial", "banquier", "journaliste",
                                    "enseignant", "enseignement"]):
            return "tertiaire"
        if any(k in m_id for k in ["caissier", "demenageur", "logistique", "camionneur", "transport",
                                    "cariste", "chauffeur_taxi", "conducteur_engins", "conducteur_tractopelle",
                                    "routier"]):
            return "transport_logistique"
        if any(k in m_id for k in ["soudeur", "fondeur", "chromage", "galvaniseur", "ouvrier", "metallurg",
                                    "raffinerie", "raffineur", "fonderie", "verrier", "verrerie", "mineur",
                                    "plasturgiste", "polymerisation", "chimiste", "imprimeur", "tanneur",
                                    "decapage", "degraissage", "ramoneur", "coke", "incinerateur",
                                    "fabricant_piles", "aeronautique", "electronique", "nucleaire",
                                    "industrie_continue", "industrie_decoupe", "industrie_metallurgie",
                                    "industrie_nucleaire", "alliages_speciaux", "aiguiseur", "affutage",
                                    "bijoutier", "menuisier", "ebeniste", "boulanger", "patissier", "meunier",
                                    "ouvrier_alimentation", "ouvrier_agroalimentaire", "ouvrier_batteries",
                                    "ouvrier_mousses_polyurethane", "ouvrier_petrochimie", "applicateur_resines",
                                    "peintre", "peintre_carrosserie", "cordonnier", "couturiere", "coiffeur",
                                    "decolorateur", "monteur_chaine", "emballeur", "cellophane", "viscose",
                                    "marin", "pompiste", "pressing", "colle", "extraction_huiles",
                                    "cuisinier", "sider_metallurgiste", "fer_metallurg", "thermometres",
                                    "instruments_mesure", "gammagraphe", "technicien_telecom",
                                    "electricien_haute_tension", "radar", "metrologie", "esthetique",
                                    "cabines_uv", "egoutier", "musicien_pro", "plongeur_pro", "scaphandrier",
                                    "tubiste", "caissonnier", "entrepots_frigorifique", "peche_industrie",
                                    "fondeur_aluminium", "fondeur_metaux", "menuisier_panneaux"]):
            return "industrie"
        if any(k in m_id for k in ["aeroport", "tonnerre_textile", "conditionnement", "controleur",
                                    "securite", "forces_ordre", "secretaire_clavier", "pesticides",
                                    "collectivites_voirie", "aerosols", "tous_secteurs",
                                    "plus_frequent_tertiaire"]):
            return "services"
        return "industrie"  # défaut

    for m_id in sorted(metiers):
        nom_fr = m_id.replace("_", " ").capitalize()
        secteur = classify_secteur(m_id)
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
        ("examen_dermatologique", "Examen dermatologique clinique", "clinique", 50.0, False, "INRS-2020"),
        ("nfs_plaquettes", "Numération formule sanguine + plaquettes", "biologique", 15.0, False, "INRS-benzène"),
        ("examen_orl", "Examen ORL (rhinoscopie, nasofibroscopie)", "clinique", 80.0, False, "INRS-bois"),
        ("dosage_arsenic_urinaire", "Dosage arsenic urinaire", "biologique", 35.0, False, "INRS-2019"),
        ("examen_neurologique", "Examen neurologique clinique", "clinique", 60.0, False, "HAS-2021"),
        ("emg", "Électromyogramme (EMG)", "fonctionnel", 90.0, False, "HAS-2021"),
        ("dosage_mercure_urinaire", "Dosage mercure urinaire", "biologique", 35.0, False, "INRS-2020"),
        ("dosage_solvants_urinaires", "Dosage métabolites solvants (acide hippurique, acide mandélique)", "biologique", 40.0, False, "INRS-2018"),
        ("dosage_cs2_urinaire", "Dosage CS2 urinaire (TTCA)", "biologique", 35.0, False, "INRS-2017"),
        ("ecg", "Électrocardiogramme (ECG)", "fonctionnel", 30.0, False, "HAS-2020"),
        ("acetylcholinesterase", "Cholinestérase érythrocytaire (pesticides)", "biologique", 30.0, False, "INRS-pesticides"),
        ("dosimetre_passif", "Dosimétrie passive (rayonnements ionisants)", "biologique", 20.0, False, "Code-santé-publique-R1333"),
        ("examen_visuel", "Bilan visuel / acuité / FO", "fonctionnel", 60.0, False, "HAS-écran"),
        ("evaluation_rps", "Évaluation RPS (questionnaires WOCCQ, Karasek)", "clinique", 0.0, False, "INRS-RPS-2023"),
        ("bilan_metabolique", "Bilan métabolique (glycémie, lipides, IMC, TA)", "biologique", 30.0, False, "HAS-2022"),
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

    # CONCERNE_ORGANE (Pathologie → Organe) — heuristic mapping étendue 49 substances
    patho_organe_map = {
        # Amiante
        "mesotheliome": "plevre",
        "asbestose": "poumon",
        "cancer_broncho_pulmonaire_amiante": "poumon",
        "plaques_pleurales": "plevre",
        # Plomb
        "saturnisme": "systeme_nerveux",
        "neuropathie_peripherique_plomb": "systeme_nerveux",
        "encephalopathie_plomb": "systeme_nerveux",
        "nephropathie_plomb": "rein",
        # Benzène
        "leucemie_myeloide": "moelle_osseuse",
        "aplasie_medullaire": "moelle_osseuse",
        "lymphome_non_hodgkinien": "moelle_osseuse",
        # Silice
        "silicose": "poumon",
        "cancer_pulmonaire_silice": "poumon",
        "scleroderme_systemique": "peau",
        # Isocyanates
        "asthme_isocyanates": "poumon",
        "pneumopathie_hypersensibilite": "poumon",
        # Formaldéhyde
        "cancer_nasopharynx": "voies_aeriennes_sup",
        "asthme_formaldehyde": "poumon",
        "dermatite_formaldehyde": "peau",
        # Chrome
        "asthme_chromates": "poumon",
        "cancer_broncho_pulmonaire_chrome": "poumon",
        "ulcerations_cutanees_chrome": "peau",
        # Nickel
        "cancer_naso_sinusien_nickel": "voies_aeriennes_sup",
        "asthme_nickel": "poumon",
        "eczema_nickel": "peau",
        # Cadmium
        "cancer_pulmonaire_cadmium": "poumon",
        "nephropathie_cadmium": "rein",
        "osteomalacie_cadmium": "os",
        # Mercure
        "intoxication_mercurielle": "systeme_nerveux",
        "neuropathie_mercure": "systeme_nerveux",
        "tremblement_intentionnel_mercure": "systeme_nerveux",
        # Arsenic
        "cancer_cutane_arsenic": "peau",
        "cancer_bronchique_arsenic": "poumon",
        "angiosarcome_foie": "foie",
        "neuropathie_arsenic": "systeme_nerveux",
        # Béryllium
        "berylliose": "poumon",
        "cancer_pulmonaire_beryllium": "poumon",
        # Cobalt
        "asthme_cobalt": "poumon",
        "fibrose_pulmonaire_cobalt": "poumon",
        "cancer_pulmonaire_cobalt": "poumon",
        # Manganèse
        "syndrome_parkinsonien_manganese": "systeme_nerveux",
        "manganisme": "systeme_nerveux",
        "neuropathie_manganese": "systeme_nerveux",
        # Poussières bois
        "adenocarcinome_ethmoide": "voies_aeriennes_sup",
        "cancer_naso_sinusien_bois": "voies_aeriennes_sup",
        "asthme_bois": "poumon",
        "dermatite_bois": "peau",
        # HAP
        "cancer_cutane_hap": "peau",
        "cancer_bronchique_hap": "poumon",
        "cancer_vessie_hap": "rein",
        # Chlorure de vinyle
        "acro_osteolyse": "os",
        "syndrome_raynaud_cvm": "peau",
        "cancer_hepatique": "foie",
        # TCE
        "cancer_renal_tce": "rein",
        "encephalopathie_tce": "systeme_nerveux",
        # Toluène / Xylène / n-Hexane / MEK / CS2
        "encephalopathie_toluene": "systeme_nerveux",
        "neuropathie_toluene": "systeme_nerveux",
        "atteinte_auditive_solvants": "systeme_nerveux",
        "encephalopathie_solvants": "systeme_nerveux",
        "dermatite_xylene": "peau",
        "polynevrite_hexane": "systeme_nerveux",
        "encephalopathie_hexane": "systeme_nerveux",
        "dermatite_mek": "peau",
        "encephalopathie_cs2": "systeme_nerveux",
        "polynevrite_cs2": "systeme_nerveux",
        # DCM
        "atteinte_hepatique_dcm": "foie",
        # Organophosphorés / Glyphosate
        "intoxication_aigue_organophosphores": "systeme_nerveux",
        "neuropathie_retardee_organophosphores": "systeme_nerveux",
        "syndrome_parkinsonien_pesticides": "systeme_nerveux",
        "lymphome_non_hodgkinien_glyphosate": "moelle_osseuse",
        "maladie_parkinson_pesticides": "systeme_nerveux",
        # Latex
        "asthme_latex": "poumon",
        "urticaire_latex": "peau",
        "dermatite_latex": "peau",
        # Persulfates / farines
        "asthme_persulfates": "poumon",
        "dermatite_coiffeur": "peau",
        "asthme_boulanger": "poumon",
        # Bio
        "tuberculose_professionnelle": "poumon",
        "hepatites_virales_professionnelles": "foie",
        # Rayonnements ionisants
        "leucemie_radio_induite": "moelle_osseuse",
        "cancer_thyroide_radio_induit": "voies_aeriennes_sup",
        # UV / laser
        "cancer_cutane_uv": "peau",
        "melanome_uv": "peau",
        "keratose_actinique": "peau",
        "lesion_cutanee_laser": "peau",
        # Bruit
        "surdite_professionnelle": "systeme_nerveux",
        # Vibrations
        "syndrome_raynaud_vibrations": "peau",
        "syndrome_canal_carpien_vibrations": "systeme_nerveux",
        "lombalgie_chronique_vibrations": "os",
        "hernie_discale_vibrations": "os",
        "sciatique_vibrations": "os",
        # TMS / ergonomie
        "lombalgie_chronique": "os",
        "hernie_discale": "os",
        "sciatique": "os",
        "cruralgie": "os",
        "tendinite_epaule": "os",
        "syndrome_canal_carpien": "systeme_nerveux",
        "epicondylite": "os",
        # Thermique
        "coup_chaleur": "systeme_nerveux",
        "deshydratation_professionnelle": "rein",
        "hypothermie": "peau",
        "gelures": "peau",
        "engelures": "peau",
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
        # Amiante
        ("mesotheliome", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("asbestose", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("cancer_broncho_pulmonaire_amiante", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("plaques_pleurales", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        # Plomb
        ("saturnisme", "plombemie", 6, True, "Décret-3-mai-2023", 2023),
        ("neuropathie_peripherique_plomb", "plombemie", 6, True, "Décret-3-mai-2023", 2023),
        ("nephropathie_plomb", "creatinemie", 12, True, "Décret-3-mai-2023", 2023),
        # Silice
        ("silicose", "scanner_thoracique", 24, True, "INRS-2017", 2017),
        ("cancer_pulmonaire_silice", "scanner_thoracique", 24, True, "HAS-2022", 2022),
        # Isocyanates, asthmes pro
        ("asthme_isocyanates", "efr", 12, True, "INRS-2017", 2017),
        ("asthme_chromates", "efr", 12, True, "INRS-2017", 2017),
        ("asthme_nickel", "efr", 12, True, "INRS-2017", 2017),
        ("asthme_cobalt", "efr", 12, True, "INRS-2017", 2017),
        ("asthme_latex", "efr", 12, True, "INRS-2017", 2017),
        ("asthme_persulfates", "efr", 12, True, "INRS-2017", 2017),
        ("asthme_boulanger", "efr", 12, True, "INRS-2017", 2017),
        ("asthme_bois", "efr", 12, True, "INRS-2017", 2017),
        ("asthme_formaldehyde", "efr", 12, True, "INRS-2017", 2017),
        # Chrome
        ("cancer_broncho_pulmonaire_chrome", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("ulcerations_cutanees_chrome", "dosage_chrome_urinaire", 12, True, "INRS-2020", 2020),
        # Nickel
        ("cancer_naso_sinusien_nickel", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("cancer_naso_sinusien_nickel", "examen_orl", 12, True, "INRS-2020", 2020),
        # Cadmium
        ("cancer_pulmonaire_cadmium", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("nephropathie_cadmium", "dosage_cadmium_urinaire", 12, True, "INRS-2020", 2020),
        # Mercure
        ("intoxication_mercurielle", "dosage_mercure_urinaire", 12, True, "INRS-2020", 2020),
        ("neuropathie_mercure", "examen_neurologique", 12, True, "HAS-2021", 2021),
        # Benzène / hémopathies
        ("leucemie_myeloide", "nfs_plaquettes", 6, True, "INRS-benzène", 2020),
        ("aplasie_medullaire", "nfs_plaquettes", 6, True, "INRS-benzène", 2020),
        ("lymphome_non_hodgkinien", "nfs_plaquettes", 12, True, "INRS-benzène", 2020),
        # Bois
        ("adenocarcinome_ethmoide", "examen_orl", 24, True, "INRS-bois", 2017),
        ("cancer_naso_sinusien_bois", "examen_orl", 24, True, "INRS-bois", 2017),
        # Arsenic
        ("cancer_bronchique_arsenic", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("cancer_cutane_arsenic", "examen_dermatologique", 12, True, "INRS-2019", 2019),
        ("neuropathie_arsenic", "dosage_arsenic_urinaire", 12, True, "INRS-2019", 2019),
        # Béryllium
        ("berylliose", "scanner_thoracique", 24, True, "INRS-2018", 2018),
        # Cobalt
        ("cancer_pulmonaire_cobalt", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("fibrose_pulmonaire_cobalt", "efr", 12, True, "INRS-2018", 2018),
        # Manganèse
        ("syndrome_parkinsonien_manganese", "examen_neurologique", 12, True, "HAS-2021", 2021),
        # HAP
        ("cancer_bronchique_hap", "scanner_thoracique", 60, True, "HAS-2022", 2022),
        ("cancer_cutane_hap", "examen_dermatologique", 12, True, "INRS-2020", 2020),
        # Solvants chlorés / aromatiques / aliphatiques
        ("cancer_renal_tce", "creatinemie", 12, True, "HAS-2022", 2022),
        ("encephalopathie_tce", "examen_neurologique", 12, True, "HAS-2021", 2021),
        ("encephalopathie_toluene", "examen_neurologique", 12, True, "HAS-2021", 2021),
        ("encephalopathie_solvants", "examen_neurologique", 12, True, "HAS-2021", 2021),
        ("atteinte_auditive_solvants", "audiogramme", 12, True, "INRS-2021", 2021),
        ("polynevrite_hexane", "emg", 12, True, "HAS-2021", 2021),
        ("encephalopathie_cs2", "examen_neurologique", 12, True, "HAS-2021", 2021),
        ("polynevrite_cs2", "emg", 12, True, "HAS-2021", 2021),
        # Pesticides / glyphosate
        ("intoxication_aigue_organophosphores", "acetylcholinesterase", 12, True, "INRS-pesticides", 2020),
        ("lymphome_non_hodgkinien_glyphosate", "nfs_plaquettes", 12, True, "INRS-pesticides", 2020),
        ("maladie_parkinson_pesticides", "examen_neurologique", 12, True, "HAS-2021", 2021),
        # Latex
        ("urticaire_latex", "examen_dermatologique", 12, False, "INRS-2018", 2018),
        # Chlorure de vinyle
        ("angiosarcome_foie", "scanner_thoracique", 24, True, "INRS-2017", 2017),
        # Rayonnements ionisants
        ("leucemie_radio_induite", "dosimetre_passif", 12, True, "Code-santé-publique-R1333", 2023),
        ("leucemie_radio_induite", "nfs_plaquettes", 12, True, "Code-santé-publique-R1333", 2023),
        # Bruit
        ("surdite_professionnelle", "audiogramme", 36, True, "INRS-2021", 2021),
        # Vibrations
        ("syndrome_raynaud_vibrations", "examen_dermatologique", 12, True, "INRS-2019", 2019),
        ("syndrome_canal_carpien_vibrations", "emg", 12, True, "HAS-2021", 2021),
        ("lombalgie_chronique_vibrations", "examen_neurologique", 12, True, "INRS-2019", 2019),
        # TMS / ergonomie
        ("syndrome_canal_carpien", "emg", 12, True, "HAS-2021", 2021),
        ("tendinite_epaule", "examen_neurologique", 12, False, "INRS-TMS-2020", 2020),
        ("lombalgie_chronique", "examen_neurologique", 12, False, "INRS-TMS-2020", 2020),
        # Travail écran
        ("fatigue_visuelle", "examen_visuel", 24, False, "INRS-écran", 2019),
        # RPS
        ("burn_out", "evaluation_rps", 12, False, "INRS-RPS-2023", 2023),
        ("depression_reactionnelle", "evaluation_rps", 12, False, "INRS-RPS-2023", 2023),
        ("stress_post_traumatique", "evaluation_rps", 6, False, "INRS-RPS-2023", 2023),
        # Travail nuit / sédentarité
        ("syndrome_metabolique_nuit", "bilan_metabolique", 12, True, "HAS-2023", 2023),
        ("maladies_cardiovasculaires_nuit", "ecg", 12, True, "HAS-2023", 2023),
        ("syndrome_metabolique_sedentarite", "bilan_metabolique", 12, False, "HAS-2022", 2022),
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
