// DEBBY KG — Schema Kuzu v0.1 (10 substances pilotes)
// ADR-001 GraphRAG Kuzu comme chef d'œuvre
// Version: kuzu-10sub-v0.1
// Date: 2026-05-27

// =====================================================================
// NODE TABLES
// =====================================================================

// Substance : agent chimique / biologique / physique avec CAS si disponible
CREATE NODE TABLE Substance (
    id STRING PRIMARY KEY,           // ex: 'amiante', 'plomb', 'benzene'
    nom_fr STRING,
    nom_en STRING,
    cas STRING,                       // numéro CAS officiel validé (Modulo 10)
    chebi_id STRING,                  // ChEBI ID si disponible
    categorie STRING,                 // 'mineral', 'metal', 'cov', 'biologique', 'physique'
    cmr STRING,                       // 'C1A', 'C1B', 'C2', 'M1A', 'M1B', 'M2', 'R1A', 'R1B', 'R2', null
    vlep_8h_mg_m3 DOUBLE,             // VLEP 8h (mg/m³) FR si applicable
    vlep_ct_mg_m3 DOUBLE,             // VLEP court terme
    source_url STRING,                // ECHA, INRS, ANSES
    source_chunk_ids STRING[]         // pointeurs vers Table A canonique (BYOE)
);

// Pathologie : diagnostic médical avec codes normalisés
CREATE NODE TABLE Pathologie (
    id STRING PRIMARY KEY,            // ex: 'mesotheliome', 'silicose'
    nom_fr STRING,
    nom_en STRING,
    icd11_code STRING,                // ICD-11 WHO
    snomed_ct_fr STRING,              // SNOMED-CT FR si disponible
    mesh_id STRING,                   // MeSH NLM
    type STRING,                      // 'cancer', 'respiratoire', 'cutanee', 'neurologique', 'tms', 'rps'
    severite STRING,                  // 'fatale', 'grave', 'moderee', 'legere'
    reversibilite STRING,             // 'irreversible', 'reversible', 'variable'
    source_chunk_ids STRING[]
);

// Tableau_MP : tableau de maladie professionnelle FR (175 au total)
CREATE NODE TABLE Tableau_MP (
    id STRING PRIMARY KEY,            // ex: 'RG-30', 'RG-30-BIS', 'RG-30-TER', 'RA-47-TER'
    regime STRING,                    // 'RG' ou 'RA'
    numero INT32,                     // 30 (numéro principal)
    variante STRING,                  // null, 'BIS', 'TER'
    intitule STRING,
    agent_causal STRING[],            // ex: ['amiante']
    pathologie_couverte STRING[],     // ex: ['mesotheliome', 'asbestose']
    delai_prise_en_charge_jours INT32,
    duree_exposition_min_jours INT32,
    liste_travaux STRING,             // texte court des travaux concernés
    date_creation STRING,
    date_derniere_revision STRING,
    source_url STRING                 // inrs.fr/publications/bdd/mp/...
);

// Metier : profession exposée, idéalement avec code NAF/ROME
CREATE NODE TABLE Metier (
    id STRING PRIMARY KEY,            // ex: 'soudeur', 'mecanicien', 'agriculteur'
    nom_fr STRING,
    nom_en STRING,
    naf_codes STRING[],               // codes NAF FR
    rome_codes STRING[],              // codes ROME FR
    secteur STRING,                   // 'BTP', 'industrie', 'agriculture', 'sante', 'tertiaire'
    source_chunk_ids STRING[]
);

// Organe : organe ou système cible
CREATE NODE TABLE Organe (
    id STRING PRIMARY KEY,            // ex: 'poumon', 'foie', 'systeme_nerveux'
    nom_fr STRING,
    nom_en STRING,
    systeme STRING                    // 'respiratoire', 'hematopoietique', etc.
);

// Examen : examen de surveillance médicale
CREATE NODE TABLE Examen (
    id STRING PRIMARY KEY,            // ex: 'scanner_thoracique', 'audiogramme', 'plombemie'
    nom_fr STRING,
    type STRING,                      // 'biologique', 'imagerie', 'fonctionnel', 'clinique'
    cout_estime_eur DOUBLE,
    irradiant BOOLEAN,
    source_recommandation STRING      // 'HAS-2022', 'INRS-2017', 'OSHA-2003'
);

// Source : référence bibliographique (alimentée depuis Table A)
CREATE NODE TABLE Source (
    chunk_id STRING PRIMARY KEY,      // = Table A chunk_id (BYOE strict)
    work_id STRING,
    titre STRING,
    annee INT32,
    venue STRING,
    doi STRING,
    niveau_preuve STRING,             // 'EBM-1a', 'EBM-1b', ..., 'REG-FR', 'AVIS-EXPERT'
    is_retracted BOOLEAN,
    obsolescence_year INT32,          // I.7 Temporal Validity GLM 5.1
    corpus_version STRING,
    side_tables_version STRING
);

// =====================================================================
// RELATIONSHIP TABLES
// =====================================================================

CREATE REL TABLE CAUSE (
    FROM Substance TO Pathologie,
    niveau_evidence STRING,           // 'IARC-1', 'IARC-2A', 'IARC-2B', 'IARC-3', 'IARC-4'
    latence_mediane_annees DOUBLE,    // I.7 critique : latence avant apparition
    risque_relatif DOUBLE,
    source_chunk_ids STRING[]
);

CREATE REL TABLE CLASSIFIEE_DANS (
    FROM Pathologie TO Tableau_MP,
    completeness STRING,              // 'complete', 'partielle' (la pathologie n'est qu'un cas du tableau)
    source_chunk_ids STRING[]
);

CREATE REL TABLE CONCERNE_ORGANE (
    FROM Pathologie TO Organe,
    type_atteinte STRING,             // 'lesion', 'fonctionnel', 'cancereux'
    source_chunk_ids STRING[]
);

CREATE REL TABLE CONCERNE_METIER (
    FROM Tableau_MP TO Metier,
    frequence_exposition STRING,      // 'quotidienne', 'occasionnelle'
    source_chunk_ids STRING[]
);

CREATE REL TABLE EXPOSE_A (
    FROM Metier TO Substance,
    niveau_exposition STRING,         // 'eleve', 'modere', 'faible'
    poste_type STRING,                // exemple de poste exposant
    source_chunk_ids STRING[]
);

CREATE REL TABLE SURVEILLANCE (
    FROM Pathologie TO Examen,
    periodicite_mois INT32,           // ex: 24 = bisannuel, 12 = annuel
    obligatoire BOOLEAN,
    source_recommandation STRING,     // 'HAS-2022', 'INRS-2017'
    annee_recommandation INT32,       // I.7 critique : date de la reco
    source_chunk_ids STRING[]
);

CREATE REL TABLE DOCUMENTE (
    FROM Source TO Substance,
    confiance DOUBLE                  // 0.0-1.0 score de pertinence Source ↔ Substance
);

CREATE REL TABLE DOCUMENTE_PATHO (
    FROM Source TO Pathologie,
    confiance DOUBLE
);

CREATE REL TABLE DOCUMENTE_TABLEAU (
    FROM Source TO Tableau_MP,
    confiance DOUBLE
);
