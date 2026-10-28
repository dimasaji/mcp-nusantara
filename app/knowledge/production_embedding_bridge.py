from app.runtime.indobert_cache import get_cached
from pathlib import Path
import sqlite3
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from app.knowledge.sqlite_backup import backup_sqlite_database

ROOT = Path(__file__).resolve().parents[2]

KB_ROOT = ROOT / "data" / "knowledge"
DB_PATH = KB_ROOT / "production_knowledge.db"
BACKUP_ROOT = KB_ROOT / "backup"

MODEL_NAME = "indobenchmark/indobert-base-p1"
EMBEDDING_VERSION = "indobert-base-p1-v1"
EMBEDDING_DIMENSION = 768

BATCH_SIZE = 4
MAX_LENGTH = 256


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def sha256_text(text):
    return hashlib.sha256(
        text.encode("utf-8", errors="ignore")
    ).hexdigest()


def backup_database():

    if not DB_PATH.exists():
        raise RuntimeError(
            f"Database tidak ditemukan: {DB_PATH}"
        )

    BACKUP_ROOT.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    backup = (
        BACKUP_ROOT
        / f"production_knowledge_{timestamp}.db"
    )

    backup_sqlite_database(DB_PATH, backup)

    return backup


def connect():

    conn = sqlite3.connect(
        str(DB_PATH)
    )

    conn.row_factory = sqlite3.Row

    conn.execute(
        "PRAGMA journal_mode=WAL"
    )

    conn.execute(
        "PRAGMA foreign_keys=ON"
    )

    return conn


def ensure_schema(conn):

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS source_registry (
            source_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            source_status TEXT NOT NULL DEFAULT 'unknown',
            authority TEXT,
            source_url TEXT,
            effective_date TEXT,
            expiry_date TEXT,
            verification_note TEXT,
            registered_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY(document_id)
                REFERENCES documents(document_id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS
            idx_source_registry_document
            ON source_registry(document_id);

        CREATE INDEX IF NOT EXISTS
            idx_source_registry_status
            ON source_registry(source_status);

        CREATE TABLE IF NOT EXISTS chunk_embeddings (
            chunk_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            model_name TEXT NOT NULL,
            embedding_version TEXT NOT NULL,
            dimension INTEGER NOT NULL,
            vector BLOB NOT NULL,
            vector_norm REAL NOT NULL,
            text_hash TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(chunk_id)
                REFERENCES chunks(chunk_id)
                ON DELETE CASCADE,
            FOREIGN KEY(document_id)
                REFERENCES documents(document_id)
                ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS
            idx_embeddings_document
            ON chunk_embeddings(document_id);

        CREATE INDEX IF NOT EXISTS
            idx_embeddings_model
            ON chunk_embeddings(model_name);

        CREATE TABLE IF NOT EXISTS embedding_runs (
            run_id TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            embedding_version TEXT NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL,
            total_chunks INTEGER NOT NULL DEFAULT 0,
            embedded_chunks INTEGER NOT NULL DEFAULT 0,
            skipped_chunks INTEGER NOT NULL DEFAULT 0,
            failed_chunks INTEGER NOT NULL DEFAULT 0,
            error_message TEXT
        );
        """
    )

    conn.commit()


def ensure_source_registry(conn):

    rows = conn.execute(
        """
        SELECT
            document_id,
            source_file
        FROM documents
        WHERE active = 1
        """
    ).fetchall()

    now = utc_now()

    for row in rows:

        document_id = row["document_id"]

        exists = conn.execute(
            """
            SELECT source_id
            FROM source_registry
            WHERE document_id = ?
            LIMIT 1
            """,
            (document_id,),
        ).fetchone()

        if exists:
            continue

        source_id = (
            "SRC-"
            + hashlib.sha256(
                document_id.encode("utf-8")
            ).hexdigest()[:16].upper()
        )

        conn.execute(
            """
            INSERT INTO source_registry (
                source_id,
                document_id,
                source_status,
                authority,
                source_url,
                effective_date,
                expiry_date,
                verification_note,
                registered_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                document_id,
                "unknown",
                None,
                None,
                None,
                None,
                "Auto-created during production KB hardening.",
                now,
                now,
            ),
        )

    conn.commit()


def load_model():

    try:
        import torch
        from transformers import (
            AutoTokenizer,
            AutoModel,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Dependency IndoBERT belum tersedia. "
            "Jalankan: "
            "python -m pip install torch transformers sentencepiece"
        ) from exc

    print()
    print("=" * 72)
    print("LOADING INDOBERT")
    print("=" * 72)
    print(f"MODEL: {MODEL_NAME}")
    print("DEVICE: CPU")

    tokenizer = get_cached(AutoTokenizer,
        MODEL_NAME
    )

    model = get_cached(AutoModel,
        MODEL_NAME
    )

    model.eval()
    model.to("cpu")

    return torch, tokenizer, model


def mean_pooling(
    model_output,
    attention_mask,
    torch,
):
    token_embeddings = model_output.last_hidden_state

    mask = attention_mask.unsqueeze(-1).expand(
        token_embeddings.size()
    ).float()

    masked = token_embeddings * mask

    summed = torch.sum(
        masked,
        dim=1,
    )

    counts = torch.clamp(
        mask.sum(dim=1),
        min=1e-9,
    )

    return summed / counts


def normalize_vectors(
    vectors,
    torch,
):
    norms = torch.linalg.norm(
        vectors,
        dim=1,
        keepdim=True,
    )

    norms = torch.clamp(
        norms,
        min=1e-12,
    )

    return vectors / norms


def embed_texts(
    texts,
    torch,
    tokenizer,
    model,
):

    encoded = tokenizer(
        texts,
        padding=True,
        truncation=True,
        max_length=MAX_LENGTH,
        return_tensors="pt",
    )

    with torch.no_grad():

        output = model(
            **encoded
        )

        vectors = mean_pooling(
            output,
            encoded["attention_mask"],
            torch,
        )

        vectors = normalize_vectors(
            vectors,
            torch,
        )

    return vectors.cpu()


def vector_to_blob(
    vector,
):
    import array

    values = [
        float(x)
        for x in vector.tolist()
    ]

    arr = array.array(
        "f",
        values,
    )

    return arr.tobytes()


def blob_to_vector(
    blob,
):
    import array

    arr = array.array(
        "f"
    )

    arr.frombytes(blob)

    return list(arr)


def cosine_similarity(
    a,
    b,
):

    if len(a) != len(b):
        return -1.0

    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0

    for x, y in zip(a, b):

        dot += x * y
        norm_a += x * x
        norm_b += y * y

    denominator = (
        math.sqrt(norm_a)
        * math.sqrt(norm_b)
    )

    if denominator <= 1e-12:
        return 0.0

    return dot / denominator


def get_missing_chunks(
    conn,
):

    rows = conn.execute(
        """
        SELECT
            c.chunk_id,
            c.document_id,
            c.text,
            c.text_hash
        FROM chunks c
        LEFT JOIN chunk_embeddings e
          ON e.chunk_id = c.chunk_id
         AND e.model_name = ?
         AND e.embedding_version = ?
        WHERE e.chunk_id IS NULL
        ORDER BY
            c.document_id,
            c.chunk_index
        """,
        (
            MODEL_NAME,
            EMBEDDING_VERSION,
        ),
    ).fetchall()

    return rows


def create_run_id():

    timestamp = (
        datetime.now()
        .strftime("%Y%m%d%H%M%S")
    )

    return (
        "EMB-"
        + timestamp
        + "-"
        + hashlib.sha256(
            timestamp.encode()
        ).hexdigest()[:8].upper()
    )


def embed_database():

    backup = backup_database()

    conn = connect()

    try:

        ensure_schema(conn)
        ensure_source_registry(conn)

        torch, tokenizer, model = load_model()

        rows = get_missing_chunks(conn)

        total = len(rows)

        print()
        print(
            f"CHUNKS TO EMBED: {total}"
        )

        run_id = create_run_id()
        started = utc_now()

        conn.execute(
            """
            INSERT INTO embedding_runs (
                run_id,
                model_name,
                embedding_version,
                started_at,
                status,
                total_chunks
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                MODEL_NAME,
                EMBEDDING_VERSION,
                started,
                "running",
                total,
            ),
        )

        conn.commit()

        embedded = 0
        skipped = 0
        failed = 0

        for start in range(
            0,
            total,
            BATCH_SIZE,
        ):

            batch = rows[
                start:start + BATCH_SIZE
            ]

            texts = [
                row["text"]
                for row in batch
            ]

            try:

                vectors = embed_texts(
                    texts,
                    torch,
                    tokenizer,
                    model,
                )

                for row, vector in zip(
                    batch,
                    vectors,
                ):

                    blob = vector_to_blob(
                        vector
                    )

                    norm = math.sqrt(
                        sum(
                            x * x
                            for x in vector.tolist()
                        )
                    )

                    conn.execute(
                        """
                        INSERT OR REPLACE INTO
                        chunk_embeddings (
                            chunk_id,
                            document_id,
                            model_name,
                            embedding_version,
                            dimension,
                            vector,
                            vector_norm,
                            text_hash,
                            created_at
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            row["chunk_id"],
                            row["document_id"],
                            MODEL_NAME,
                            EMBEDDING_VERSION,
                            EMBEDDING_DIMENSION,
                            blob,
                            norm,
                            row["text_hash"],
                            utc_now(),
                        ),
                    )

                    embedded += 1

                conn.commit()

                print(
                    f"[EMBEDDED] "
                    f"{min(start + BATCH_SIZE, total)}"
                    f"/{total}"
                )

            except Exception as exc:

                failed += len(batch)

                print(
                    f"[ERROR] batch {start}: {exc}"
                )

        finished = utc_now()

        status = (
            "success"
            if failed == 0
            else "partial"
        )

        conn.execute(
            """
            UPDATE embedding_runs
            SET
                finished_at = ?,
                status = ?,
                embedded_chunks = ?,
                skipped_chunks = ?,
                failed_chunks = ?
            WHERE run_id = ?
            """,
            (
                finished,
                status,
                embedded,
                skipped,
                failed,
                run_id,
            ),
        )

        conn.commit()

        print()
        print("=" * 72)
        print("INDOBERT EMBEDDING RESULT")
        print("=" * 72)
        print(f"RUN       : {run_id}")
        print(f"MODEL     : {MODEL_NAME}")
        print(f"DIMENSION : {EMBEDDING_DIMENSION}")
        print(f"TOTAL     : {total}")
        print(f"EMBEDDED  : {embedded}")
        print(f"SKIPPED   : {skipped}")
        print(f"FAILED    : {failed}")
        print(f"STATUS    : {status}")
        print(f"BACKUP    : {backup}")

        if failed:
            return 2

        return 0

    finally:
        conn.close()


def search_semantic(
    query,
    top_k=5,
):

    conn = connect()

    try:

        ensure_schema(conn)

        torch, tokenizer, model = load_model()

        query_vector = embed_texts(
            [query],
            torch,
            tokenizer,
            model,
        )[0].tolist()

        rows = conn.execute(
            """
            SELECT
                e.chunk_id,
                e.document_id,
                e.vector,
                c.text,
                d.title,
                d.source_file,
                d.service,
                d.content_type
            FROM chunk_embeddings e
            JOIN chunks c
              ON c.chunk_id = e.chunk_id
            JOIN documents d
              ON d.document_id = e.document_id
            WHERE e.model_name = ?
              AND e.embedding_version = ?
              AND d.active = 1
            """,
            (
                MODEL_NAME,
                EMBEDDING_VERSION,
            ),
        ).fetchall()

        scored = []

        for row in rows:

            vector = blob_to_vector(
                row["vector"]
            )

            score = cosine_similarity(
                query_vector,
                vector,
            )

            scored.append(
                {
                    "chunk_id": row["chunk_id"],
                    "document_id": row["document_id"],
                    "title": row["title"],
                    "source_file": row["source_file"],
                    "service": row["service"],
                    "content_type": row["content_type"],
                    "score": score,
                    "text": row["text"],
                }
            )

        scored.sort(
            key=lambda x: x["score"],
            reverse=True,
        )

        return scored[:top_k]

    finally:
        conn.close()


def stats():

    conn = connect()

    try:

        ensure_schema(conn)

        documents = conn.execute(
            """
            SELECT COUNT(*)
            FROM documents
            WHERE active = 1
            """
        ).fetchone()[0]

        chunks = conn.execute(
            """
            SELECT COUNT(*)
            FROM chunks
            """
        ).fetchone()[0]

        embeddings = conn.execute(
            """
            SELECT COUNT(*)
            FROM chunk_embeddings
            WHERE model_name = ?
              AND embedding_version = ?
            """,
            (
                MODEL_NAME,
                EMBEDDING_VERSION,
            ),
        ).fetchone()[0]

        sources = conn.execute(
            """
            SELECT
                source_status,
                COUNT(*)
            FROM source_registry
            GROUP BY source_status
            ORDER BY source_status
            """
        ).fetchall()

        print()
        print("=" * 72)
        print("PRODUCTION KB + INDOBERT STATUS")
        print("=" * 72)

        print(
            f"DOCUMENTS       : {documents}"
        )

        print(
            f"CHUNKS          : {chunks}"
        )

        print(
            f"EMBEDDINGS      : {embeddings}"
        )

        print(
            f"MODEL           : {MODEL_NAME}"
        )

        print(
            f"DIMENSION       : {EMBEDDING_DIMENSION}"
        )

        print()
        print("SOURCE STATUS")

        for row in sources:
            print(
                f"  {row[0]}: {row[1]}"
            )

        print()
        print(
            f"DATABASE: {DB_PATH}"
        )

    finally:
        conn.close()


def self_test():

    conn = connect()

    try:

        ensure_schema(conn)
        ensure_source_registry(conn)

        required_tables = {
            "documents",
            "chunks",
            "source_registry",
            "chunk_embeddings",
            "embedding_runs",
        }

        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
            """
        ).fetchall()

        tables = {
            row["name"]
            for row in rows
        }

        missing = (
            required_tables - tables
        )

        if missing:
            raise RuntimeError(
                "Table missing: "
                + ", ".join(
                    sorted(missing)
                )
            )

        print(
            "[PASS] Production KB schema"
        )

        row = conn.execute(
            """
            SELECT COUNT(*)
            FROM chunks
            """
        ).fetchone()

        assert row[0] >= 0

        print(
            "[PASS] Chunk table accessible"
        )

        row = conn.execute(
            """
            SELECT COUNT(*)
            FROM source_registry
            """
        ).fetchone()

        assert row[0] >= 0

        print(
            "[PASS] Source registry"
        )

        row = conn.execute(
            """
            SELECT COUNT(*)
            FROM chunk_embeddings
            """
        ).fetchone()

        assert row[0] >= 0

        print(
            "[PASS] Embedding storage"
        )

        print()
        print(
            "INDOBERT_BRIDGE_SCHEMA_TEST: PASS"
        )

        return 0

    finally:
        conn.close()


def usage():

    print(
        """
Nusantara AI Production IndoBERT Bridge

Commands:

  python -m app.knowledge.production_embedding_bridge self-test

  python -m app.knowledge.production_embedding_bridge stats

  python -m app.knowledge.production_embedding_bridge embed

  python -m app.knowledge.production_embedding_bridge search "Apa itu KTP-el?"

"""
    )


def main():

    command = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "help"
    )

    if command == "self-test":
        raise SystemExit(
            self_test()
        )

    if command == "stats":
        stats()
        return

    if command == "embed":
        raise SystemExit(
            embed_database()
        )

    if command == "search":

        if len(sys.argv) < 3:
            print(
                "Query wajib diberikan."
            )
            raise SystemExit(2)

        query = " ".join(
            sys.argv[2:]
        )

        results = search_semantic(
            query,
            top_k=5,
        )

        print(
            json.dumps(
                results,
                ensure_ascii=False,
                indent=2,
            )
        )

        return

    usage()


if __name__ == "__main__":
    main()

