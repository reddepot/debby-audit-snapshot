#!/usr/bin/env python3
"""
DEBBY KG — Layer 3 fiche pédagogique opposable Pydantic

Génère une FicheOpposable validée Pydantic v2 depuis le KG Kuzu, avec :
- Sections opposables (chaque section au moins 1 source citée)
- Sources qualifiées niveau de preuve EBM 1-5 / REG-FR / AVIS-EXPERT / MCP-*
- Alternatives écartées explicitées (transparence raisonnement)
- Chaîne de raisonnement (chain-of-reasoning) pour traçabilité
- Audit check (méta : n_sources, n_chunks, lacunes connues)
- Disclaimer pédagogique opposable

ADR-002 Export pédagogique opposable KG → fiches DES MST / MdT.
Version : layer3-v0.1 (2026-05-27)

Usage:
    python3 kg/scripts/layer3_fiche_opposable.py --substance amiante
    python3 kg/scripts/layer3_fiche_opposable.py --all-pilots
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Literal, Optional

try:
    import kuzu
except ImportError:
    sys.exit("kuzu requis. `pip install kuzu`")

try:
    from pydantic import BaseModel, Field, field_validator
except ImportError:
    sys.exit("pydantic v2 requis. `pip install 'pydantic>=2'`")

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPO_ROOT / "kg" / "data" / "kuzu.db"
DEFAULT_OUT = REPO_ROOT / "kg" / "exports" / "fiches_opposables"

KG_VERSION = "kuzu-50sub-v0.2"
LAYER3_VERSION = "layer3-v0.1"

# Substances pilotes pour test (cf. mission A11)
PILOT_SUBSTANCES = ["amiante", "plomb", "benzene", "silice_cristalline", "glyphosate"]


# =====================================================================
# Pydantic v2 models
# =====================================================================

SourceType = Literal[
    "EBM-1a",      # Méta-analyse Cochrane / SR haute qualité
    "EBM-1b",      # Essai randomisé contrôlé
    "EBM-2",       # Étude cohorte ou cas-témoins
    "EBM-3",       # Étude écologique / série de cas
    "EBM-4",       # Avis comité experts avec preuves
    "EBM-5",       # Avis expert individuel sans preuve formelle
    "REG-FR",      # Texte réglementaire FR (décret, code travail)
    "AVIS-EXPERT", # Avis d'agence (HAS, INRS, ANSES)
    "MCP-INRS",    # Lookup MCP SSTinfo / INRS BDD
    "MCP-LEGIFRANCE",  # Lookup MCP SSTinfo / Légifrance
]


class SourceCitee(BaseModel):
    """Source citée avec qualification épistémique opposable."""

    type: SourceType
    titre: str = Field(min_length=3)
    annee: int = Field(ge=1900, le=2030)
    organisme: Optional[str] = None
    url: Optional[str] = None
    chunk_id: Optional[str] = Field(
        default=None,
        description="Pointeur Table A DEBBY (traçabilité BYOE)",
    )
    niveau_preuve_score: int = Field(
        ge=1,
        le=5,
        description="1=avis expert isolé, 5=méta-analyse Cochrane",
    )

    @field_validator("annee")
    @classmethod
    def _annee_plausible(cls, v: int) -> int:
        if v < 1900 or v > 2030:
            raise ValueError(f"Année {v} hors plage [1900-2030]")
        return v


class SectionOpposable(BaseModel):
    """Section d'une fiche opposable avec sources citées obligatoires."""

    titre: str = Field(min_length=3)
    contenu: str = Field(min_length=10)
    sources: list[SourceCitee] = Field(
        min_length=1,
        description="Au moins 1 source par section",
    )


class AlternativeEcartee(BaseModel):
    """Alternative envisagée puis écartée, avec raison explicite."""

    alternative: str = Field(min_length=3)
    raison_ecartement: str = Field(min_length=10)
    source: Optional[SourceCitee] = None


class FicheOpposable(BaseModel):
    """Fiche pédagogique opposable validée Pydantic, traçable Table A."""

    substance_id: str = Field(min_length=2)
    nom_fr: str = Field(min_length=2)
    generated_at: date
    kg_version: str
    layer3_version: str = LAYER3_VERSION
    sections: list[SectionOpposable] = Field(
        min_length=5,
        description=(
            "Au moins 5 sections (identification, patho, MP, métiers, surveillance)"
        ),
    )
    alternatives_ecartees: list[AlternativeEcartee] = Field(default_factory=list)
    chain_of_reasoning: str = Field(
        min_length=50,
        description=(
            "Chaîne de raisonnement explicite : pourquoi cette structure de fiche, "
            "quels arbitrages faits, quelles sources retenues vs écartées."
        ),
    )
    audit_check: dict = Field(
        default_factory=dict,
        description=(
            "Métadonnées audit : nb sources, nb chunks tracés, lacunes connues."
        ),
    )
    disclaimer: str = (
        "Cette fiche est un support pédagogique généré depuis le KG DEBBY. "
        "Elle agrège des sources de référence (INRS, HAS, décrets FR) mais "
        "ne remplace pas la lecture des textes primaires ni le jugement "
        "clinique du médecin du travail."
    )


# =====================================================================
# Helpers Kuzu
# =====================================================================

def fetch_one(conn, query: str, parameters: Optional[dict] = None):
    r = conn.execute(query, parameters or {})
    if r.has_next():
        return r.get_next()
    return None


def fetch_all(conn, query: str, parameters: Optional[dict] = None) -> list:
    r = conn.execute(query, parameters or {})
    rows = []
    while r.has_next():
        rows.append(r.get_next())
    return rows


# =====================================================================
# Sources réelles (INRS / HAS / décrets) — choisies selon substance
# =====================================================================

INRS_SOURCE_BASE = SourceCitee(
    type="AVIS-EXPERT",
    titre="Fiche INRS — Synthèse risque substance",
    annee=2024,
    organisme="INRS",
    url=None,  # url remplie dynamiquement depuis Substance.source_url
    niveau_preuve_score=4,
)

DECRET_VLEP_INRS = SourceCitee(
    type="REG-FR",
    titre=(
        "Code du travail — Art. R4412-149 et suivants — VLEP contraignantes "
        "et indicatives"
    ),
    annee=2023,
    organisme="Légifrance / Ministère du travail",
    url="https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006072050/LEGISCTA000018530338/",
    niveau_preuve_score=5,
)

TABLEAUX_MP_INRS = SourceCitee(
    type="MCP-INRS",
    titre="INRS — Base BDD MP (175 tableaux RG/RA), liste tableaux MP",
    annee=2026,
    organisme="INRS",
    url="https://www.inrs.fr/publications/bdd/mp/listeTableaux.html",
    niveau_preuve_score=5,
)

CIRC_MONO_BASE = SourceCitee(
    type="EBM-1a",
    titre="CIRC/IARC Monographs — classification cancérogène",
    annee=2024,
    organisme="IARC/WHO",
    url="https://monographs.iarc.who.int/",
    niveau_preuve_score=5,
)

HAS_SUIVI_POST_PRO = SourceCitee(
    type="AVIS-EXPERT",
    titre=(
        "HAS — Suivi post-professionnel des personnes exposées à des "
        "cancérogènes professionnels"
    ),
    annee=2020,
    organisme="HAS",
    url="https://www.has-sante.fr/jcms/c_1052483/fr/suivi-post-professionnel",
    niveau_preuve_score=4,
)

# Surveillance amiante HAS 2010 (actualisée)
HAS_AMIANTE = SourceCitee(
    type="AVIS-EXPERT",
    titre="HAS — Suivi post-professionnel après exposition à l'amiante (2010, mise à jour 2021)",
    annee=2021,
    organisme="HAS",
    url="https://www.has-sante.fr/jcms/c_993368/fr/suivi-post-professionnel-amiante",
    niveau_preuve_score=4,
)

# Code travail CMR R4412
CODE_TRAVAIL_CMR = SourceCitee(
    type="REG-FR",
    titre="Code du travail — Art. R4412-59 et suivants — Risque CMR",
    annee=2023,
    organisme="Légifrance",
    url="https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006072050/LEGISCTA000018530418/",
    niveau_preuve_score=5,
)

# Sources spécifiques par substance (à valider en review humaine)
SPECIFIC_SOURCES: dict[str, list[SourceCitee]] = {
    "amiante": [
        SourceCitee(
            type="REG-FR",
            titre="Code du travail — Art. R4412-94 à R4412-148 — Amiante",
            annee=2022,
            organisme="Légifrance",
            url="https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006072050/LEGISCTA000018530386/",
            niveau_preuve_score=5,
        ),
        HAS_AMIANTE,
        SourceCitee(
            type="EBM-1a",
            titre="CIRC Monographs Vol. 100C — Amiante (chrysotile, amosite, crocidolite)",
            annee=2012,
            organisme="IARC/WHO",
            url="https://publications.iarc.fr/120",
            niveau_preuve_score=5,
        ),
    ],
    "plomb": [
        SourceCitee(
            type="REG-FR",
            titre=(
                "Code du travail — Art. R4412-152 — VLEP plomb 0,05 mg/m³ "
                "et VLB plombémie 400 µg/L (H) / 300 µg/L (F âge fertile)"
            ),
            annee=2023,
            organisme="Légifrance",
            url="https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000018532213/",
            niveau_preuve_score=5,
        ),
        SourceCitee(
            type="AVIS-EXPERT",
            titre="INRS ED 6201 — Plomb et ses composés, prévention du risque",
            annee=2023,
            organisme="INRS",
            url="https://www.inrs.fr/publications/edition/ed6201.html",
            niveau_preuve_score=4,
        ),
        SourceCitee(
            type="EBM-2",
            titre="CIRC Monographs Vol. 87 — Inorganic and Organic Lead Compounds",
            annee=2006,
            organisme="IARC/WHO",
            url="https://publications.iarc.fr/107",
            niveau_preuve_score=4,
        ),
    ],
    "benzene": [
        SourceCitee(
            type="REG-FR",
            titre=(
                "Code du travail — VLEP benzène 1 ppm (3,25 mg/m³) sur 8h, CMR 1A"
            ),
            annee=2023,
            organisme="Légifrance",
            url="https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006072050/LEGISCTA000018530352/",
            niveau_preuve_score=5,
        ),
        SourceCitee(
            type="AVIS-EXPERT",
            titre="INRS — Fiche toxicologique FT 49 — Benzène",
            annee=2024,
            organisme="INRS",
            url="https://www.inrs.fr/publications/bdd/fichetox/fiche.html?refINRS=FT%2049",
            niveau_preuve_score=4,
        ),
        SourceCitee(
            type="EBM-1a",
            titre="CIRC Monographs Vol. 120 — Benzene",
            annee=2018,
            organisme="IARC/WHO",
            url="https://publications.iarc.fr/576",
            niveau_preuve_score=5,
        ),
    ],
    "silice_cristalline": [
        SourceCitee(
            type="REG-FR",
            titre=(
                "Code du travail — Art. R4412-149 — VLEP silice cristalline "
                "fraction alvéolaire 0,1 mg/m³ (quartz)"
            ),
            annee=2021,
            organisme="Légifrance",
            url="https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000043337891/",
            niveau_preuve_score=5,
        ),
        SourceCitee(
            type="AVIS-EXPERT",
            titre="INRS ED 6373 — Silice cristalline, prévention",
            annee=2024,
            organisme="INRS",
            url="https://www.inrs.fr/publications/edition/ed6373.html",
            niveau_preuve_score=4,
        ),
        SourceCitee(
            type="EBM-1a",
            titre=(
                "CIRC Monographs Vol. 100C — Silica dust, crystalline "
                "(quartz, cristobalite)"
            ),
            annee=2012,
            organisme="IARC/WHO",
            url="https://publications.iarc.fr/120",
            niveau_preuve_score=5,
        ),
    ],
    "glyphosate": [
        SourceCitee(
            type="EBM-1a",
            titre="CIRC Monographs Vol. 112 — Glyphosate (classement 2A)",
            annee=2017,
            organisme="IARC/WHO",
            url="https://publications.iarc.fr/549",
            niveau_preuve_score=4,
        ),
        SourceCitee(
            type="AVIS-EXPERT",
            titre=(
                "EFSA — Conclusion peer review glyphosate, divergence avec CIRC "
                "(à valider)"
            ),
            annee=2023,
            organisme="EFSA",
            url="https://www.efsa.europa.eu/en/efsajournal/pub/8164",
            niveau_preuve_score=4,
        ),
        SourceCitee(
            type="REG-FR",
            titre=(
                "Décret n° 2020-1257 — Tableau RA-59 lymphome non hodgkinien "
                "et pesticides"
            ),
            annee=2020,
            organisme="Légifrance",
            url="https://www.legifrance.gouv.fr/loda/id/JORFTEXT000042424802/",
            niveau_preuve_score=5,
        ),
    ],
}


def sources_for(substance_id: str, substance_url: Optional[str]) -> list[SourceCitee]:
    """Retourne une liste de sources opposables pour la substance."""
    out: list[SourceCitee] = []
    # Source INRS générique avec URL spécifique
    inrs = INRS_SOURCE_BASE.model_copy()
    if substance_url:
        inrs.url = substance_url
        inrs.titre = f"Fiche INRS — {substance_id} — Synthèse risque"
    out.append(inrs)
    out.extend(SPECIFIC_SOURCES.get(substance_id, []))
    return out


# =====================================================================
# Construction de la fiche opposable
# =====================================================================

def build_section_identification(
    nom_fr: str, cas: Optional[str], categorie: Optional[str],
    cmr: Optional[str], vlep_8h: Optional[float], vlep_ct: Optional[float],
    sources: list[SourceCitee],
) -> SectionOpposable:
    parts = [f"**Nom français** : {nom_fr}"]
    if cas:
        parts.append(f"**N° CAS** : `{cas}`")
    if categorie:
        parts.append(f"**Catégorie** : {categorie}")
    if cmr:
        cmr_label = {
            "C1A": "Cancérogène avéré 1A", "C1B": "Cancérogène présumé 1B",
            "C2": "Cancérogène suspecté 2",
            "M1A": "Mutagène 1A", "M1B": "Mutagène 1B", "M2": "Mutagène suspecté",
            "R1A": "Reprotoxique 1A", "R1B": "Reprotoxique 1B",
            "R2": "Reprotoxique suspecté 2",
        }.get(cmr, cmr)
        parts.append(f"**Classification CMR (CLP)** : {cmr_label}")
    if vlep_8h is not None:
        parts.append(f"**VLEP 8h** : `{vlep_8h} mg/m³`")
    if vlep_ct is not None:
        parts.append(f"**VLEP court terme** : `{vlep_ct} mg/m³`")
    contenu = " — ".join(parts)
    return SectionOpposable(
        titre="1. Identification chimique et classification réglementaire",
        contenu=contenu,
        sources=[s for s in sources if s.type in ("AVIS-EXPERT", "REG-FR", "MCP-INRS")],
    )


def build_section_pathologies(
    pathologies: list, sources: list[SourceCitee],
) -> SectionOpposable:
    if pathologies:
        lines = []
        for row in pathologies:
            p_id, p_nom, p_type, p_sev, niveau = row
            niveau_lbl = niveau or "à valider"
            lines.append(
                f"- **{p_nom}** ({p_type}, sévérité={p_sev}, niveau de preuve={niveau_lbl})"
            )
        contenu = "Pathologies professionnelles induites :\n" + "\n".join(lines)
    else:
        contenu = (
            "Aucune pathologie spécifique associée dans le KG DEBBY actuellement. "
            "À compléter par recherche MCP SSTinfo lookup_substance."
        )
    return SectionOpposable(
        titre="2. Pathologies professionnelles induites (niveau de preuve)",
        contenu=contenu,
        sources=[s for s in sources if s.type in ("EBM-1a", "EBM-1b", "EBM-2", "AVIS-EXPERT")] or sources[:1],
    )


def build_section_tableaux_mp(
    tableaux: list, sources: list[SourceCitee],
) -> SectionOpposable:
    if tableaux:
        lines = []
        for row in tableaux:
            t_id, t_intitule, t_regime, t_num, t_variante = row
            variante_lbl = t_variante if t_variante else ""
            lines.append(
                f"- **{t_id}** (régime {t_regime}, n° {t_num} {variante_lbl}) : {t_intitule}"
            )
        contenu = "Tableaux MP applicables :\n" + "\n".join(lines)
    else:
        contenu = (
            "Aucun tableau MP référencé dans le KG pour cette substance. "
            "Vérifier via MCP SSTinfo `lookup_tableau_mp` ou CRRMP pour reconnaissance hors tableau."
        )
    tableaux_sources = [s for s in sources if s.type in ("REG-FR", "MCP-INRS", "MCP-LEGIFRANCE")]
    if not tableaux_sources:
        tableaux_sources = [TABLEAUX_MP_INRS]
    return SectionOpposable(
        titre="3. Tableaux de maladies professionnelles applicables (FR)",
        contenu=contenu,
        sources=tableaux_sources,
    )


def build_section_metiers(
    metiers: list, sources: list[SourceCitee],
) -> SectionOpposable:
    if metiers:
        by_secteur: dict[str, list[str]] = {}
        for row in metiers:
            m_id, m_nom, m_secteur = row
            by_secteur.setdefault(m_secteur or "non classé", []).append(m_nom)
        lines = []
        for secteur, names in sorted(by_secteur.items()):
            lines.append(f"- **{secteur.upper()}** : {', '.join(names)}")
        contenu = "Métiers et secteurs exposés :\n" + "\n".join(lines)
    else:
        contenu = (
            "Aucun métier rattaché dans le KG. À compléter via MCP SSTinfo "
            "`lookup_metier` ou fiches FMP Présanse."
        )
    return SectionOpposable(
        titre="4. Métiers et secteurs exposés",
        contenu=contenu,
        sources=[s for s in sources if s.type in ("AVIS-EXPERT", "MCP-INRS")] or sources[:1],
    )


def build_section_surveillance(
    surveillances: list, organes: list, sources: list[SourceCitee],
) -> SectionOpposable:
    lines = []
    if organes:
        organes_str = ", ".join(f"{o[0]} ({o[1]})" for o in organes)
        lines.append(f"**Organes cibles** : {organes_str}")
    if surveillances:
        lines.append("**Surveillance médicale recommandée** :")
        for patho, examen, perio, reco, annee in surveillances:
            perio_lbl = f"tous les {perio} mois" if perio else "périodicité à valider"
            lines.append(
                f"- Pathologie ciblée : {patho} → examen **{examen}** "
                f"({perio_lbl}, source {reco} {annee})"
            )
    if not lines:
        lines.append(
            "Surveillance médicale à définir selon recommandations HAS/INRS spécifiques "
            "et niveau d'exposition. Voir MCP SSTinfo `aide_decision`."
        )
    contenu = "\n".join(lines)
    surveillance_sources = [
        s for s in sources if s.type in ("AVIS-EXPERT", "REG-FR", "EBM-1a", "EBM-1b")
    ]
    if not surveillance_sources:
        surveillance_sources = [HAS_SUIVI_POST_PRO]
    return SectionOpposable(
        titre="5. Surveillance médicale recommandée et organes cibles",
        contenu=contenu,
        sources=surveillance_sources,
    )


def build_alternatives_ecartees(
    substance_id: str, cmr: Optional[str],
) -> list[AlternativeEcartee]:
    """Construit la liste des alternatives écartées et leur raison."""
    out = []
    cmr_categorie_1 = cmr in ("C1A", "C1B", "M1A", "M1B", "R1A", "R1B")
    if cmr_categorie_1:
        out.append(
            AlternativeEcartee(
                alternative=(
                    f"Maintien à l'identique du procédé exposant à un agent CMR {cmr}"
                ),
                raison_ecartement=(
                    "Obligation réglementaire de substitution (Code du travail "
                    "R4412-66) — l'employeur doit rechercher activement un produit "
                    "ou procédé de substitution moins dangereux."
                ),
                source=CODE_TRAVAIL_CMR,
            )
        )
        out.append(
            AlternativeEcartee(
                alternative="Surveillance médicale standard (visite tous les 5 ans)",
                raison_ecartement=(
                    f"CMR catégorie {cmr} impose Suivi Individuel Renforcé (SIR) "
                    "avec examens spécifiques selon HAS et INRS. Cf. R4624-23."
                ),
                source=DECRET_VLEP_INRS,
            )
        )
    if cmr and cmr.startswith("R"):
        out.append(
            AlternativeEcartee(
                alternative=(
                    "Maintien de l'exposition pour femme enceinte/allaitante ou "
                    "en âge de procréer"
                ),
                raison_ecartement=(
                    f"Substance classée reprotoxique {cmr} : interdiction "
                    "d'exposition pour femmes enceintes ou allaitantes (Code du "
                    "travail D4152-9 et suivants). Retrait obligatoire du poste "
                    "exposant ou aménagement immédiat."
                ),
                source=CODE_TRAVAIL_CMR,
            )
        )
    if substance_id == "glyphosate":
        out.append(
            AlternativeEcartee(
                alternative="Reconnaissance comme cancérogène avéré (C1A)",
                raison_ecartement=(
                    "Classement CIRC 2A (cancérogène probable) basé sur preuves "
                    "limitées chez l'homme et suffisantes chez l'animal. Divergence "
                    "EFSA/ECHA qui classent non cancérogène. À valider en review "
                    "humaine - controverse active."
                ),
                source=CIRC_MONO_BASE,
            )
        )
    if substance_id == "amiante":
        out.append(
            AlternativeEcartee(
                alternative="Reprise d'activité sans suivi post-professionnel",
                raison_ecartement=(
                    "HAS 2010 (mise à jour 2021) recommande suivi post-exposition "
                    "amiante (scanner thoracique tous les 5-10 ans selon exposition "
                    "cumulée) pour dépistage précoce mésothéliome et cancer bronchique."
                ),
                source=HAS_AMIANTE,
            )
        )
    return out


def build_chain_of_reasoning(
    substance_id: str, nom_fr: str, cmr: Optional[str],
    n_patho: int, n_tableaux: int, n_sources: int,
) -> str:
    lines = [
        f"Cette fiche opposable pour {nom_fr} a été construite selon la logique suivante :",
        f"1. **Identification** : récupération depuis KG Kuzu (id={substance_id}) "
        f"des propriétés CAS, catégorie, classification CMR, VLEP.",
        f"2. **Pathologies** : {n_patho} pathologie(s) référencée(s) via la relation "
        f"Substance-[CAUSE]->Pathologie. Niveau de preuve hérité du KG ; à valider "
        f"face aux dernières méta-analyses Cochrane/CIRC.",
        f"3. **Tableaux MP** : {n_tableaux} tableau(x) MP applicable(s) via la "
        f"relation Pathologie-[CLASSIFIEE_DANS]->Tableau_MP. Toujours vérifier "
        f"délai de prise en charge, durée d'exposition minimale, liste limitative "
        f"des travaux sur INRS BDD MP (175 tableaux au 2026-05).",
        f"4. **Métiers** : extraction via Metier-[EXPOSE_A]->Substance ; "
        f"complémenter par fiche FMP Présanse spécifique au cas d'espèce.",
        f"5. **Surveillance** : recommandations issues du KG (HAS/INRS) ; vérifier "
        f"actualité (cycle 6 mois) et adapter au niveau d'exposition individuel.",
    ]
    if cmr in ("C1A", "C1B"):
        lines.append(
            f"6. **CMR {cmr}** : applique la grille CMR (substitution obligatoire, "
            f"SIR, fiche d'exposition, attestation au départ)."
        )
    lines.append(
        f"Total : {n_sources} source(s) primaire(s) citée(s). "
        f"Cette fiche n'écarte aucune source connue — toute lacune est listée "
        f"dans audit_check.lacunes_connues."
    )
    return "\n".join(lines)


def build_audit_check(
    n_sections: int, n_sources: int, n_chunks_traces: int,
    pathologies: list, tableaux: list, metiers: list, surveillances: list,
) -> dict:
    lacunes = []
    if not pathologies:
        lacunes.append("Aucune pathologie liée dans KG — à enrichir via MCP")
    if not tableaux:
        lacunes.append("Aucun tableau MP rattaché — vérifier CRRMP")
    if not metiers:
        lacunes.append("Aucun métier rattaché — compléter via FMP Présanse")
    if not surveillances:
        lacunes.append(
            "Aucune recommandation surveillance dans KG — voir HAS / INRS spécifique"
        )
    if n_chunks_traces == 0:
        lacunes.append(
            "Aucun chunk Table A tracé (BYOE pending) — pointeurs source_chunk_ids vides"
        )
    return {
        "n_sections": n_sections,
        "n_sources_total": n_sources,
        "n_chunks_traces": n_chunks_traces,
        "n_pathologies_kg": len(pathologies),
        "n_tableaux_mp_kg": len(tableaux),
        "n_metiers_kg": len(metiers),
        "n_surveillances_kg": len(surveillances),
        "lacunes_connues": lacunes,
        "kg_version": KG_VERSION,
        "layer3_version": LAYER3_VERSION,
        "review_humaine_requise": True,
    }


def generate_fiche_opposable(
    substance_id: str, kuzu_db_path: str = str(DEFAULT_DB),
) -> FicheOpposable:
    """Génère une FicheOpposable Pydantic validée depuis le KG Kuzu."""
    db = kuzu.Database(kuzu_db_path, read_only=True)
    conn = kuzu.Connection(db)

    s = fetch_one(
        conn,
        """
        MATCH (s:Substance {id:$id})
        RETURN s.nom_fr, s.nom_en, s.cas, s.cmr, s.vlep_8h_mg_m3,
               s.vlep_ct_mg_m3, s.categorie, s.source_url,
               s.source_chunk_ids
        """,
        {"id": substance_id},
    )
    if not s:
        raise ValueError(f"Substance '{substance_id}' non trouvée dans le KG")

    (nom_fr, nom_en, cas, cmr, vlep_8h, vlep_ct, categorie,
     source_url, source_chunk_ids) = s

    pathologies = fetch_all(
        conn,
        """
        MATCH (s:Substance {id:$id})-[c:CAUSE]->(p:Pathologie)
        RETURN p.id AS p_id, p.nom_fr AS p_nom, p.type AS p_type,
               p.severite AS p_sev, c.niveau_evidence AS niveau
        ORDER BY p_sev DESC, p_nom
        """,
        {"id": substance_id},
    )

    tableaux = fetch_all(
        conn,
        """
        MATCH (s:Substance {id:$id})-[:CAUSE]->(p:Pathologie)-[:CLASSIFIEE_DANS]->(t:Tableau_MP)
        RETURN DISTINCT t.id AS t_id, t.intitule AS t_intitule, t.regime AS t_regime,
                        t.numero AS t_num, t.variante AS t_variante
        ORDER BY t_regime, t_num, t_variante
        """,
        {"id": substance_id},
    )

    metiers = fetch_all(
        conn,
        """
        MATCH (m:Metier)-[:EXPOSE_A]->(s:Substance {id:$id})
        RETURN m.id AS m_id, m.nom_fr AS m_nom, m.secteur AS m_secteur
        ORDER BY m_secteur, m_nom
        """,
        {"id": substance_id},
    )

    organes = fetch_all(
        conn,
        """
        MATCH (s:Substance {id:$id})-[:CAUSE]->(p:Pathologie)-[:CONCERNE_ORGANE]->(o:Organe)
        RETURN DISTINCT o.nom_fr AS o_nom, o.systeme AS o_sys
        ORDER BY o_nom
        """,
        {"id": substance_id},
    )

    surveillances = fetch_all(
        conn,
        """
        MATCH (s:Substance {id:$id})-[:CAUSE]->(p:Pathologie)-[r:SURVEILLANCE]->(e:Examen)
        RETURN DISTINCT p.nom_fr AS patho, e.nom_fr AS examen,
                        r.periodicite_mois AS perio,
                        r.source_recommandation AS reco,
                        r.annee_recommandation AS annee
        ORDER BY annee DESC
        """,
        {"id": substance_id},
    )

    # Construire sources opposables pour la substance
    base_sources = sources_for(substance_id, source_url)
    # Ajouter source globale tableaux MP si tableaux trouvés
    if tableaux:
        base_sources.append(TABLEAUX_MP_INRS)
    # CMR : ajouter référence code travail CMR
    if cmr:
        base_sources.append(CODE_TRAVAIL_CMR)

    # Chunks tracés depuis substance + transitivement pour info
    n_chunks_traces = len(source_chunk_ids or [])
    # Compter total chunks transitivement (Substance + Pathologies + Source)
    chunk_counts = fetch_one(
        conn,
        """
        MATCH (s:Substance {id:$id})
        OPTIONAL MATCH (s)-[:CAUSE]->(p:Pathologie)
        RETURN size(s.source_chunk_ids) AS s_chunks,
               count(DISTINCT p) AS n_patho_for_chunks
        """,
        {"id": substance_id},
    )
    if chunk_counts:
        n_chunks_traces = max(n_chunks_traces, int(chunk_counts[0] or 0))

    # Construire les sections (≥5)
    sections = [
        build_section_identification(
            nom_fr, cas, categorie, cmr, vlep_8h, vlep_ct, base_sources,
        ),
        build_section_pathologies(pathologies, base_sources),
        build_section_tableaux_mp(tableaux, base_sources),
        build_section_metiers(metiers, base_sources),
        build_section_surveillance(surveillances, organes, base_sources),
    ]

    alternatives = build_alternatives_ecartees(substance_id, cmr)

    cor = build_chain_of_reasoning(
        substance_id, nom_fr, cmr,
        len(pathologies), len(tableaux), len(base_sources),
    )

    audit = build_audit_check(
        n_sections=len(sections),
        n_sources=sum(len(sec.sources) for sec in sections),
        n_chunks_traces=n_chunks_traces,
        pathologies=pathologies,
        tableaux=tableaux,
        metiers=metiers,
        surveillances=surveillances,
    )

    fiche = FicheOpposable(
        substance_id=substance_id,
        nom_fr=nom_fr,
        generated_at=date.today(),
        kg_version=KG_VERSION,
        sections=sections,
        alternatives_ecartees=alternatives,
        chain_of_reasoning=cor,
        audit_check=audit,
    )

    return fiche


# =====================================================================
# CLI
# =====================================================================

def save_fiche(fiche: FicheOpposable, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{fiche.substance_id}.json"
    # Pydantic v2 dump JSON
    out_path.write_text(
        fiche.model_dump_json(indent=2, exclude_none=False),
        encoding="utf-8",
    )
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db-path", default=str(DEFAULT_DB))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT))
    ap.add_argument("--substance", help="ID substance (ex: amiante)")
    ap.add_argument(
        "--all-pilots", action="store_true",
        help=f"Génère pour les pilotes : {PILOT_SUBSTANCES}",
    )
    args = ap.parse_args()

    out_dir = Path(args.out_dir)

    targets: list[str] = []
    if args.all_pilots:
        targets = list(PILOT_SUBSTANCES)
    elif args.substance:
        targets = [args.substance]
    else:
        ap.error("Donner --substance ou --all-pilots")

    results = []
    for sid in targets:
        try:
            fiche = generate_fiche_opposable(sid, args.db_path)
            path = save_fiche(fiche, out_dir)
            n_sources = sum(len(s.sources) for s in fiche.sections)
            n_chunks = fiche.audit_check.get("n_chunks_traces", 0)
            print(
                f"OK {sid}: {path.name} "
                f"({len(fiche.sections)} sections, {n_sources} sources, "
                f"{n_chunks} chunks tracés, "
                f"{len(fiche.alternatives_ecartees)} alternatives écartées)"
            )
            results.append({
                "substance_id": sid,
                "path": str(path),
                "n_sections": len(fiche.sections),
                "n_sources": n_sources,
                "n_chunks_traces": n_chunks,
                "n_alternatives": len(fiche.alternatives_ecartees),
            })
        except Exception as e:
            print(f"ERREUR {sid}: {e}", file=sys.stderr)
            raise

    print("\nRécap :")
    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
