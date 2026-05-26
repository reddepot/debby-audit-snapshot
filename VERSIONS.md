# DEBBY — Versioning sémantique

> **Pattern** : versioning explicite de chaque composant immutable pour reproductibilité long-terme (cf. chantier V.7 du panel 11+1 voix).  
> **Invariant BYOE** : `embed_version` peut changer sans toucher `corpus_version` ni `chunking_version` (Table A canonique préservée).  
> **Convention** : SemVer + date courte + provider/source.

## Versions actuelles (2026-05-27)

| Composant | Version | Date | Notes |
|---|---|---|---|
| `corpus_version` | **2.1** | 2026-05-26 | Phase 2 fusion canonique + cascade neuf 1,087M chunks intégrés (cf. `lessons_debby_neuf_integration_20260526.md`) |
| `chunking_version` | **pc-3600-v1** | 2026-05-23 | parent-child, child=3600 chars, pas d'overlap, séparation par paragraphes |
| `embed_version` | **qwen3-8b-or-fp16-L2-v1** | 2026-05-26 | qwen3-embedding-8b via OpenRouter, fp16 4096-dim, L2-normalisé |
| `side_tables_version` | **v1.0** | 2026-05-24 | Side-tables existantes : retracted_work_ids.json + source_type_refined.json + year_title_fix.db + body_lang_fix.json + entities.jsonl |
| `tableaux_mp_reference` | **inrs-175-v1.0** | 2026-05-27 | 122 RG + 53 RA = 175 tableaux (cf. TABLEAUX_MP_REFERENCE.md) — corrige le décompte initial erroné de 151 |
| `benchmark_version` | **fr-mdt-49-v1.0** | 2026-05-23 | 49 requêtes FR MdT, 13 catégories (cf. debby_benchmark_fr.jsonl) |

## Versions à venir (Phase 1 RECTIFIED post-cap KG/formation)

| Composant | Version cible | Phase | Statut |
|---|---|---|---|
| `side_tables_version` | **v2.0** | I.1-I.7 corrections + signature HMAC | 🔨 en cours nuit 27/05 |
| `corpus_version` | **2.2** | post side-tables v2 + tagging KG-ready | différé |
| `kg_version` | **kuzu-10sub-v0.1** | Prototype 10 substances pilotes | 🔨 en cours nuit 27/05 |
| `benchmark_version` | **fr-mdt-250-v2.0-formation** | IV.1 étendu 250-300 req pédagogiques | différé |
| `embed_version` | **qwen3-8b-or-fp16-L2-v1.1-pinned** | Provider pinning anti-drift OR (D'.4) | différé |
| `reranker_version` | **qwen3-reranker-8b-apache-v1** | II.3 (validé Perplexity + bake-off matin) | différé |

## Règles de versioning

1. **`corpus_version`** : minor++ à chaque ajout massif de works (cascade, fusion). Major++ si re-chunking ou changement de schéma Table A.
2. **`chunking_version`** : suffixe descriptif (`pc-3600-v1`, `pc-1800-v2`, `child-only-v3`). Major++ à chaque re-chunking complet.
3. **`embed_version`** : `<modèle>-<provider>-<précision>-<norme>-v<n>`. Le suffixe `-pinned` indique qu'on a épinglé le provider (anti-drift OR).
4. **`side_tables_version`** : SemVer simple `vX.Y`. Major si signature crypto change.
5. **`benchmark_version`** : `<lang>-<scope>-<nb_requetes>-v<n>-<usage>` (ex: `fr-mdt-250-v2.0-formation`).
6. **`kg_version`** : `<engine>-<scope>-v<n>` (ex: `kuzu-10sub-v0.1` → `kuzu-fullont-v1.0`).
7. **`tableaux_mp_reference`** : `<source>-<nb>-v<n>` (ex: `inrs-175-v1.0`).

## Tracking dans Table A

Chaque chunk doit porter (futures colonnes au load LanceDB) :
- `chunking_version` (déjà présent)
- Pointeurs vers `side_tables_version` actif au load
- Pointeurs vers `embed_version` actif

→ Permet de reconstituer **exactement** dans quelles conditions une requête a été servie pour reproductibilité long-terme.

## Snapshots Parquet immutables

À chaque bump de version, snapshot S3 Vultr en `s3://meddata-lake/debby_embed/snapshots/<corpus_version>/`.

## Pointeurs

- Chantier V.7 du panel 11+1 voix
- Issue GitHub #28 Phase 1 RECTIFIED
- Memory : `feedback_no_duplicates_principle.md` (zéro perte + propagation systématique)
