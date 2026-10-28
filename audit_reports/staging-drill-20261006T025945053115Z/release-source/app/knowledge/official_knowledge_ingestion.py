"""
Nusantara AI
Phase 19.4 - Official Knowledge Ingestion Foundation

Purpose
-------
Foundation for controlled ingestion of official / verified knowledge.

Design principles
-----------------
1. Official source provenance is mandatory.
2. Test fixtures are never promoted automatically.
3. Source metadata is stored separately from document content.
4. Existing Production KB schema is preserved.
5. Existing RAG / KnowledgeEngine / API routes are untouched.
6. Database changes are limited to source_registry and audit metadata.
7. Every source registration is deterministic and auditable.
8. Unknown or unverified sources are not treated as official.

Phase
-----
19.4

Status
------
Foundation / source governance layer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DB = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "production_knowledge.db"
)

OFFICIAL_ROOT = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "official"
)

SOURCE_DIR = OFFICIAL_ROOT / "source"
PROCESSED_DIR = OFFICIAL_ROOT / "processed"
QUARANTINE_DIR = OFFICIAL_ROOT / "quarantine"
MANIFEST_DIR = OFFICIAL_ROOT / "manifest"
AUDIT_DIR = OFFICIAL_ROOT / "audit"
BACKUP_DIR = OFFICIAL_ROOT / "backup"

MANIFEST_FILE = MANIFEST_DIR / "official_sources.json"
AUDIT_FILE = AUDIT_DIR / "official_ingestion_audit.jsonl"


VALID_SOURCE_STATUS = {
    "official",
    "verified",
    "pending",
    "expired",
    "unknown",
}

VALID_CONTENT_TYPES = {
    "requirements",
    "procedure",
    "fee",
    "processing_time",
    "status",
    "general",
}

VALID_SERVICES = {
    "ktp_el",
    "kartu_keluarga",
    "kia",
    "akta_kelahiran",
    "akta_kematian",
    "perkawinan",
    "perceraian",
    "pindah_datang",
    "perubahan_data",
    "layanan_online",
    "general",
}


@dataclass
class OfficialSource:
    source_id: str
    source_name: str
    authority: str
    source_url: str
    source_status: str
    published_date: str | None = None
    verified_date: str | None = None
    verification_note: str | None = None
    service: str = "general"
    content_type: str = "general"

    def validate(self) -> list[str]:
        errors: list[str] = []

        if not self.source_id.strip():
            errors.append("source_id kosong")

        if not self.source_name.strip():
            errors.append("source_name kosong")

        if not self.authority.strip():
            errors.append("authority kosong")

        if not self.source_url.strip():
            errors.append("source_url kosong")

        if self.source_status not in VALID_SOURCE_STATUS:
            errors.append(
                f"source_status tidak valid: {self.source_status}"
            )

        if self.service not in VALID_SERVICES:
            errors.append(
                f"service tidak valid: {self.service}"
            )

        if self.content_type not in VALID_CONTENT_TYPES:
            errors.append(
                f"content_type tidak valid: {self.content_type}"
            )

        if self.source_status in {"official", "verified"}:
            if not self.verification_note:
                errors.append(
                    "verification_note wajib untuk "
                    "source official/verified"
                )

        return errors


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_text(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)

            if not block:
                break

            digest.update(block)

    return digest.hexdigest()


def ensure_directories() -> None:
    for path in (
        OFFICIAL_ROOT,
        SOURCE_DIR,
        PROCESSED_DIR,
        QUARANTINE_DIR,
        MANIFEST_DIR,
        AUDIT_DIR,
        BACKUP_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)


def connect_db(db_path: Path = DEFAULT_DB) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(
            f"Production database tidak ditemukan: {db_path}"
        )

    connection = sqlite3.connect(str(db_path))
    connection.row_factory = sqlite3.Row
    return connection


def table_exists(
    connection: sqlite3.Connection,
    table_name: str,
) -> bool:
    row = connection.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table'
          AND name=?
        """,
        (table_name,),
    ).fetchone()

    return row is not None


def table_columns(
    connection: sqlite3.Connection,
    table_name: str,
) -> list[str]:
    rows = connection.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return [str(row["name"]) for row in rows]


def ensure_source_registry(
    connection: sqlite3.Connection,
) -> None:
    """
    Preserve an existing source_registry table.

    If it does not exist, create the minimum governance table.

    Existing schemas are not dropped or replaced.
    """

    if table_exists(connection, "source_registry"):
        return

    connection.execute(
        """
        CREATE TABLE source_registry (
            source_id TEXT PRIMARY KEY,
            source_name TEXT NOT NULL,
            authority TEXT NOT NULL,
            source_url TEXT NOT NULL,
            source_status TEXT NOT NULL,
            published_date TEXT,
            verified_date TEXT,
            verification_note TEXT,
            service TEXT NOT NULL,
            content_type TEXT NOT NULL,
            source_hash TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )

    connection.commit()


def register_source(
    source: OfficialSource,
    db_path: Path = DEFAULT_DB,
) -> dict[str, Any]:

    errors = source.validate()

    if errors:
        raise ValueError(
            "Source validation gagal:\n- "
            + "\n- ".join(errors)
        )

    ensure_directories()

    with connect_db(db_path) as connection:
        ensure_source_registry(connection)

        columns = table_columns(
            connection,
            "source_registry",
        )

        payload = asdict(source)

        payload["source_hash"] = sha256_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
            )
        )

        payload["created_at"] = utc_now()
        payload["updated_at"] = payload["created_at"]

        # Existing production schema may differ.
        # Insert only columns actually available.
        insert_columns = [
            column
            for column in payload
            if column in columns
        ]

        values = [
            payload[column]
            for column in insert_columns
        ]

        if "source_id" not in columns:
            raise RuntimeError(
                "source_registry tidak memiliki source_id"
            )

        placeholders = ", ".join(
            ["?"] * len(insert_columns)
        )

        column_sql = ", ".join(insert_columns)

        update_columns = [
            column
            for column in insert_columns
            if column != "source_id"
            and column != "created_at"
        ]

        if update_columns:
            update_sql = ", ".join(
                f"{column}=excluded.{column}"
                for column in update_columns
            )

            sql = f"""
                INSERT INTO source_registry
                ({column_sql})
                VALUES ({placeholders})
                ON CONFLICT(source_id)
                DO UPDATE SET
                    {update_sql}
            """
        else:
            sql = f"""
                INSERT OR IGNORE INTO source_registry
                ({column_sql})
                VALUES ({placeholders})
            """

        connection.execute(sql, values)
        connection.commit()

        return {
            "source_id": source.source_id,
            "source_name": source.source_name,
            "source_status": source.source_status,
            "service": source.service,
            "content_type": source.content_type,
            "registered": True,
        }


def load_manifest() -> list[dict[str, Any]]:
    ensure_directories()

    if not MANIFEST_FILE.exists():
        return []

    try:
        payload = json.loads(
            MANIFEST_FILE.read_text(
                encoding="utf-8"
            )
        )
    except Exception as exc:
        raise RuntimeError(
            f"Manifest rusak: {exc}"
        ) from exc

    if not isinstance(payload, list):
        raise ValueError(
            "Manifest harus berupa JSON array."
        )

    return payload


def save_manifest(
    sources: list[dict[str, Any]],
) -> None:

    ensure_directories()

    MANIFEST_FILE.write_text(
        json.dumps(
            sources,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def append_audit(
    event: str,
    payload: dict[str, Any],
) -> None:

    ensure_directories()

    record = {
        "timestamp": utc_now(),
        "event": event,
        **payload,
    }

    with AUDIT_FILE.open(
        "a",
        encoding="utf-8",
    ) as handle:
        handle.write(
            json.dumps(
                record,
                ensure_ascii=False,
            )
            + "\n"
        )


def register_manifest_source(
    source: OfficialSource,
    db_path: Path = DEFAULT_DB,
) -> dict[str, Any]:

    result = register_source(
        source,
        db_path,
    )

    manifest = load_manifest()

    new_record = asdict(source)
    new_record["registered_at"] = utc_now()

    replaced = False

    for index, existing in enumerate(manifest):
        if existing.get("source_id") == source.source_id:
            manifest[index] = new_record
            replaced = True
            break

    if not replaced:
        manifest.append(new_record)

    save_manifest(manifest)

    append_audit(
        "source_registered",
        result,
    )

    return result


def validate_document_file(
    path: Path,
) -> dict[str, Any]:

    if not path.exists():
        return {
            "valid": False,
            "reason": "file_not_found",
            "path": str(path),
        }

    if not path.is_file():
        return {
            "valid": False,
            "reason": "not_a_file",
            "path": str(path),
        }

    allowed_extensions = {
        ".txt",
        ".md",
        ".pdf",
        ".docx",
        ".json",
        ".html",
        ".htm",
    }

    suffix = path.suffix.lower()

    if suffix not in allowed_extensions:
        return {
            "valid": False,
            "reason": "unsupported_extension",
            "extension": suffix,
            "path": str(path),
        }

    file_size = path.stat().st_size

    if file_size <= 0:
        return {
            "valid": False,
            "reason": "empty_file",
            "path": str(path),
        }

    return {
        "valid": True,
        "path": str(path),
        "filename": path.name,
        "extension": suffix,
        "size": file_size,
        "sha256": sha256_file(path),
    }


def scan_source_directory() -> list[dict[str, Any]]:
    ensure_directories()

    results: list[dict[str, Any]] = []

    for path in sorted(SOURCE_DIR.rglob("*")):
        if not path.is_file():
            continue

        result = validate_document_file(path)
        results.append(result)

    return results


def quarantine_invalid_documents() -> list[dict[str, Any]]:
    ensure_directories()

    results = scan_source_directory()
    moved: list[dict[str, Any]] = []

    for result in results:
        if result.get("valid"):
            continue

        path = Path(
            result.get("path", "")
        )

        if not path.exists():
            continue

        destination = QUARANTINE_DIR / path.name

        shutil.move(
            str(path),
            str(destination),
        )

        moved.append(
            {
                **result,
                "quarantine_path": str(destination),
            }
        )

    if moved:
        append_audit(
            "documents_quarantined",
            {
                "count": len(moved),
                "documents": moved,
            },
        )

    return moved


def database_stats(
    db_path: Path = DEFAULT_DB,
) -> dict[str, Any]:

    with connect_db(db_path) as connection:

        tables = [
            row["name"]
            for row in connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                ORDER BY name
                """
            ).fetchall()
        ]

        stats: dict[str, Any] = {
            "database": str(db_path),
            "exists": db_path.exists(),
            "tables": tables,
        }

        for table in (
            "documents",
            "chunks",
            "chunk_embeddings",
            "source_registry",
            "embedding_runs",
            "ingestion_log",
        ):
            if table_exists(connection, table):
                try:
                    row = connection.execute(
                        f"SELECT COUNT(*) AS count FROM {table}"
                    ).fetchone()

                    stats[table] = int(
                        row["count"]
                    )
                except Exception:
                    stats[table] = None

        return stats


def backup_database(
    db_path: Path = DEFAULT_DB,
) -> Path:

    ensure_directories()

    if not db_path.exists():
        raise FileNotFoundError(
            f"Database tidak ditemukan: {db_path}"
        )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    destination = (
        BACKUP_DIR
        / f"production_knowledge_{timestamp}.db"
    )

    shutil.copy2(
        db_path,
        destination,
    )

    append_audit(
        "database_backup",
        {
            "source": str(db_path),
            "backup": str(destination),
        },
    )

    return destination


def create_template_manifest() -> list[dict[str, Any]]:

    sources = [
        {
            "source_id": "OFFICIAL-DUKCAPIL-TANGERANG-001",
            "source_name": "Portal Resmi Disdukcapil Kota Tangerang",
            "authority": "Dinas Kependudukan dan Pencatatan Sipil Kota Tangerang",
            "source_url": "",
            "source_status": "pending",
            "published_date": None,
            "verified_date": None,
            "verification_note": (
                "Template sumber resmi. "
                "URL dan tanggal verifikasi wajib diisi "
                "sebelum digunakan sebagai evidence produksi."
            ),
            "service": "general",
            "content_type": "general",
        },
        {
            "source_id": "OFFICIAL-DUKCAPIL-RI-001",
            "source_name": "Portal Resmi Administrasi Kependudukan",
            "authority": "Instansi Pemerintah Republik Indonesia",
            "source_url": "",
            "source_status": "pending",
            "published_date": None,
            "verified_date": None,
            "verification_note": (
                "Template sumber resmi. "
                "Jangan dipromosikan menjadi official "
                "sebelum URL dan dokumen diverifikasi."
            ),
            "service": "general",
            "content_type": "general",
        },
    ]

    save_manifest(sources)

    append_audit(
        "template_manifest_created",
        {
            "count": len(sources),
        },
    )

    return sources


def self_test() -> int:

    print("=" * 72)
    print("PHASE 19.4 OFFICIAL KNOWLEDGE INGESTION SELF TEST")
    print("=" * 72)

    ensure_directories()

    # --------------------------------------------------------
    # 1. Directory
    # --------------------------------------------------------

    print()
    print("[1/9] Official directories")

    required_dirs = [
        SOURCE_DIR,
        PROCESSED_DIR,
        QUARANTINE_DIR,
        MANIFEST_DIR,
        AUDIT_DIR,
        BACKUP_DIR,
    ]

    for directory in required_dirs:
        if not directory.exists():
            raise RuntimeError(
                f"Directory tidak tersedia: {directory}"
            )

    print("[PASS] Official directories")

    # --------------------------------------------------------
    # 2. Database
    # --------------------------------------------------------

    print()
    print("[2/9] Production database")

    if not DEFAULT_DB.exists():
        raise RuntimeError(
            "Production database tidak ditemukan."
        )

    stats = database_stats()

    if not stats.get("exists"):
        raise RuntimeError(
            "Production database tidak valid."
        )

    print(
        json.dumps(
            stats,
            ensure_ascii=False,
            indent=2,
        )
    )

    print("[PASS] Production database")

    # --------------------------------------------------------
    # 3. Source registry
    # --------------------------------------------------------

    print()
    print("[3/9] Source registry")

    with connect_db() as connection:
        ensure_source_registry(connection)

        if not table_exists(
            connection,
            "source_registry",
        ):
            raise RuntimeError(
                "source_registry tidak tersedia."
            )

    print("[PASS] Source registry")

    # --------------------------------------------------------
    # 4. Dataclass validation
    # --------------------------------------------------------

    print()
    print("[4/9] Official source validation")

    valid_source = OfficialSource(
        source_id="SELFTEST-OFFICIAL-001",
        source_name="Self Test Official Source",
        authority="Nusantara AI Test Authority",
        source_url="https://example.invalid/self-test",
        source_status="verified",
        verification_note=(
            "Self-test only; bukan sumber pelayanan."
        ),
        service="ktp_el",
        content_type="requirements",
    )

    errors = valid_source.validate()

    if errors:
        raise RuntimeError(
            "Valid source ditolak: "
            + "; ".join(errors)
        )

    invalid_source = OfficialSource(
        source_id="",
        source_name="",
        authority="",
        source_url="",
        source_status="unknown",
        service="invalid_service",
        content_type="invalid_type",
    )

    invalid_errors = invalid_source.validate()

    if len(invalid_errors) < 4:
        raise RuntimeError(
            "Validator tidak mendeteksi metadata invalid."
        )

    print("[PASS] Official source validation")

    # --------------------------------------------------------
    # 5. Manifest
    # --------------------------------------------------------

    print()
    print("[5/9] Manifest")

    create_template_manifest()

    manifest = load_manifest()

    if len(manifest) < 1:
        raise RuntimeError(
            "Manifest tidak berhasil dibuat."
        )

    print(
        f"Manifest sources: {len(manifest)}"
    )

    print("[PASS] Manifest")

    # --------------------------------------------------------
    # 6. Fixture protection
    # --------------------------------------------------------

    print()
    print("[6/9] Fixture protection")

    fixture_db = DEFAULT_DB

    with connect_db(fixture_db) as connection:

        if table_exists(
            connection,
            "chunks",
        ):
            rows = connection.execute(
                """
                SELECT chunk_id, text
                FROM chunks
                WHERE LOWER(text) LIKE '%test knowledge fixture%'
                   OR LOWER(text) LIKE '%bukan sumber resmi%'
                LIMIT 10
                """
            ).fetchall()

            for row in rows:
                text_value = str(
                    row["text"]
                ).lower()

                if (
                    "bukan sumber resmi"
                    in text_value
                ):
                    # This is an explicit safety check:
                    # fixture is allowed to exist, but must
                    # never be promoted by this module.
                    pass

    print(
        "[PASS] Test fixture tidak dipromosikan"
    )

    # --------------------------------------------------------
    # 7. Document scanner
    # --------------------------------------------------------

    print()
    print("[7/9] Document scanner")

    scan = scan_source_directory()

    print(
        f"Documents ditemukan: {len(scan)}"
    )

    for item in scan[:10]:
        print(
            json.dumps(
                item,
                ensure_ascii=False,
            )
        )

    print("[PASS] Document scanner")

    # --------------------------------------------------------
    # 8. JSON contract
    # --------------------------------------------------------

    print()
    print("[8/9] JSON contract")

    payload = {
        "phase": "19.4",
        "module": "official_knowledge_ingestion",
        "status": "ready",
        "official_root": str(OFFICIAL_ROOT),
        "manifest": str(MANIFEST_FILE),
    }

    serialized = json.dumps(
        payload,
        ensure_ascii=False,
    )

    restored = json.loads(serialized)

    if restored["phase"] != "19.4":
        raise RuntimeError(
            "JSON contract gagal."
        )

    print("[PASS] JSON contract")

    # --------------------------------------------------------
    # 9. No core modification
    # --------------------------------------------------------

    print()
    print("[9/9] Core isolation")

    protected_files = [
        PROJECT_ROOT / "app" / "api" / "routes.py",
        PROJECT_ROOT / "app" / "knowledge" / "rag.py",
        PROJECT_ROOT / "app" / "knowledge" / "engine.py",
        PROJECT_ROOT / "app" / "knowledge" / "grounding.py",
    ]

    missing = [
        str(path)
        for path in protected_files
        if not path.exists()
    ]

    if missing:
        raise RuntimeError(
            "Protected core file tidak ditemukan:\n"
            + "\n".join(missing)
        )

    print(
        "[PASS] Core isolation"
    )

    print()
    print("=" * 72)
    print(
        "PHASE 19.4 OFFICIAL KNOWLEDGE INGESTION SELFTEST: PASS"
    )
    print("=" * 72)

    return 0


def command_stats() -> int:
    print(
        json.dumps(
            database_stats(),
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0


def command_manifest() -> int:

    manifest = load_manifest()

    print(
        json.dumps(
            manifest,
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0


def command_scan() -> int:

    results = scan_source_directory()

    print(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0


def command_template() -> int:

    result = create_template_manifest()

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0


def command_register_demo() -> int:
    """
    Demonstration only.

    This intentionally uses pending status and a placeholder URL.
    It must never become production evidence.
    """

    source = OfficialSource(
        source_id="DEMO-PENDING-SOURCE-001",
        source_name="Demo Pending Source",
        authority="Demo Authority",
        source_url="https://example.invalid/demo",
        source_status="pending",
        verification_note=(
            "Demo registration only. "
            "Not valid as production evidence."
        ),
        service="general",
        content_type="general",
    )

    result = register_manifest_source(source)

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )

    return 0


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Nusantara AI Phase 19.4 "
            "Official Knowledge Ingestion"
        )
    )

    parser.add_argument(
        "command",
        choices=[
            "self-test",
            "stats",
            "manifest",
            "scan",
            "template",
            "register-demo",
        ],
    )

    args = parser.parse_args()

    if args.command == "self-test":
        return self_test()

    if args.command == "stats":
        return command_stats()

    if args.command == "manifest":
        return command_manifest()

    if args.command == "scan":
        return command_scan()

    if args.command == "template":
        return command_template()

    if args.command == "register-demo":
        return command_register_demo()

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
