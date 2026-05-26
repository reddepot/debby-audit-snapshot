#!/usr/bin/env python3
"""
DEBBY — Signature HMAC-SHA256 des side-tables (anti-X.1 Side-Table Poisoning).

Issue identifiée par GPT-5.5 reasoning lors de l'audit nuit 2026-05-26 :
les side-tables (source_type_refined, year, ebm, sst, retracted, body_lang_fix,
entities) sont des métadonnées post-embed mutables sans signature.
Un attaquant peut transformer un chunk médiocre en source prioritaire en
modifiant une side-table (`source_type_refined='official_fr'`, `year=2090`,
`ebm=1`, `sst=1`) sans détection.

Cette utilité :
- Calcule un HMAC-SHA256 par fichier side-table (clé symétrique stockée localement)
- Génère un MANIFEST.json signé avec horodatage + version sémantique V.7
- Vérifie l'intégrité à chaque load LanceDB (à intégrer dans build_lancedb.py)
- Lock-down : side-tables read-only après signature initiale

Usage:
    # Signer un dossier side-tables
    python3 side_tables_signer.py sign --side-tables-dir ./side_tables_v2/ --key-file ~/.debby/sidetables.key

    # Vérifier l'intégrité
    python3 side_tables_signer.py verify --side-tables-dir ./side_tables_v2/ --key-file ~/.debby/sidetables.key

    # Générer une clé (à faire une fois, stocker chmod 600)
    python3 side_tables_signer.py keygen --key-file ~/.debby/sidetables.key
"""
import argparse
import datetime
import hashlib
import hmac
import json
import os
import secrets
import sys
from pathlib import Path

CHUNK_SIZE = 1024 * 1024  # 1 MB pour streaming

SIDE_TABLES_SCHEMA = {
    "retracted_work_ids.json",
    "source_type_refined.json",
    "year_title_fix.db",
    "body_lang_fix.json",
    "entities.jsonl",
    # v2 corrections (Phase 1 RECTIFIED)
    "ebm_v2.json",
    "lead_filter_v2.json",
    "cas_validate_v2.json",
    "tableaux_mp_v2.json",
    "metiers_normalize_v2.json",
    "retractions_v2.json",
    "doc_type_v2.json",
    "temporal_validity_v2.json",  # GLM 5.1 I.7
}

MANIFEST_VERSION = "1.0"


def keygen(key_path: Path) -> None:
    """Génère une clé HMAC-SHA256 256 bits."""
    if key_path.exists():
        sys.exit(f"❌ Clé existe déjà : {key_path}. Supprimer manuellement avant régénération.")
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key = secrets.token_bytes(32)
    key_path.write_bytes(key)
    os.chmod(key_path, 0o600)
    print(f"✅ Clé HMAC générée : {key_path} (chmod 600)")
    print(f"   ⚠️ Sauvegarder cette clé sur le NAS (chiffrée sops/age) AVANT toute manipulation.")


def hmac_file(file_path: Path, key: bytes) -> str:
    """Streaming HMAC-SHA256 d'un fichier."""
    h = hmac.new(key, digestmod=hashlib.sha256)
    with file_path.open("rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def sign_dir(side_tables_dir: Path, key: bytes, output_manifest: Path) -> dict:
    """Signe tous les fichiers connus dans le dossier, retourne le manifest."""
    if not side_tables_dir.is_dir():
        sys.exit(f"❌ Dossier introuvable : {side_tables_dir}")

    entries = []
    for fp in sorted(side_tables_dir.rglob("*")):
        if not fp.is_file():
            continue
        rel = fp.relative_to(side_tables_dir).as_posix()
        if fp.name not in SIDE_TABLES_SCHEMA and not fp.name.endswith((".json", ".db", ".jsonl", ".parquet")):
            # Ignore files hors-schéma
            continue
        digest = hmac_file(fp, key)
        size = fp.stat().st_size
        entries.append({
            "path": rel,
            "size_bytes": size,
            "hmac_sha256": digest,
            "schema_known": fp.name in SIDE_TABLES_SCHEMA,
        })

    manifest = {
        "version": MANIFEST_VERSION,
        "created_at": datetime.datetime.utcnow().isoformat() + "Z",
        "side_tables_dir": str(side_tables_dir),
        "algorithm": "HMAC-SHA256",
        "entries": entries,
        "entries_count": len(entries),
        "policy": "read-only after signature; any modification invalidates the manifest and triggers re-build process",
        "related_findings": ["X.1 Side-Table Poisoning (GPT-5.5 reasoning, audit nuit 2026-05-26)"],
    }

    # Sign the manifest itself with a final HMAC over canonical JSON
    canonical = json.dumps({k: v for k, v in manifest.items() if k != "manifest_hmac"}, sort_keys=True, separators=(",", ":")).encode("utf-8")
    manifest_hmac = hmac.new(key, canonical, digestmod=hashlib.sha256).hexdigest()
    manifest["manifest_hmac"] = manifest_hmac

    output_manifest.write_text(json.dumps(manifest, indent=2))
    print(f"✅ Manifest signé : {output_manifest}")
    print(f"   {len(entries)} fichiers signés, HMAC global = {manifest_hmac[:16]}…")
    return manifest


def verify_dir(side_tables_dir: Path, key: bytes, manifest_path: Path) -> bool:
    """Vérifie l'intégrité des side-tables contre le manifest signé."""
    if not manifest_path.is_file():
        sys.exit(f"❌ Manifest introuvable : {manifest_path}")
    manifest = json.loads(manifest_path.read_text())

    # Vérifier la signature globale du manifest
    expected_hmac = manifest.pop("manifest_hmac")
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode("utf-8")
    computed_hmac = hmac.new(key, canonical, digestmod=hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected_hmac, computed_hmac):
        print(f"❌ Signature manifest INVALIDE : attendu {expected_hmac[:16]}, obtenu {computed_hmac[:16]}")
        return False
    print("✅ Signature manifest VALIDE")

    # Vérifier chaque fichier
    n_ok = 0
    n_fail = 0
    n_missing = 0
    for entry in manifest["entries"]:
        fp = side_tables_dir / entry["path"]
        if not fp.is_file():
            print(f"❌ Fichier disparu : {entry['path']}")
            n_missing += 1
            continue
        digest = hmac_file(fp, key)
        if not hmac.compare_digest(digest, entry["hmac_sha256"]):
            print(f"❌ HMAC ALTÉRÉ pour {entry['path']}")
            print(f"   attendu: {entry['hmac_sha256'][:16]}…")
            print(f"   obtenu : {digest[:16]}…")
            n_fail += 1
        else:
            n_ok += 1

    total = n_ok + n_fail + n_missing
    print(f"\nRésultat : {n_ok}/{total} OK | {n_fail} altérés | {n_missing} manquants")
    if n_fail or n_missing:
        print("⚠️ Side-tables compromises — re-générer avant tout load LanceDB.")
        return False
    print("✅ Toutes les side-tables sont intègres.")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["sign", "verify", "keygen"])
    ap.add_argument("--side-tables-dir", default="./side_tables_v2/")
    ap.add_argument("--key-file", default=str(Path.home() / ".debby" / "sidetables.key"))
    ap.add_argument("--manifest", default=None, help="Chemin manifest (défaut: side-tables-dir/MANIFEST.signed.json)")
    args = ap.parse_args()

    key_path = Path(args.key_file)

    if args.action == "keygen":
        keygen(key_path)
        return

    if not key_path.is_file():
        sys.exit(f"❌ Clé non trouvée : {key_path}. Lancer d'abord `keygen`.")

    key = key_path.read_bytes()
    side_tables_dir = Path(args.side_tables_dir)
    manifest_path = Path(args.manifest) if args.manifest else side_tables_dir / "MANIFEST.signed.json"

    if args.action == "sign":
        sign_dir(side_tables_dir, key, manifest_path)
    elif args.action == "verify":
        ok = verify_dir(side_tables_dir, key, manifest_path)
        sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
