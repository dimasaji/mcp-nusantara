from __future__ import annotations

import json
import math
import os
import sqlite3
import struct
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .schemas import DocumentInfo, StoredChunk


class _BorrowedConnection:
    """Store calls inside an explicit transaction must not commit independently."""
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, *args):
        return False


class SQLiteVectorStore:
    """Persistent local vector store menggunakan SQLite."""

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._transaction_connection = ContextVar(f"store_transaction_{id(self)}", default=None)
        self.db_path = Path(
            db_path
            or os.getenv(
                "NUSANTARA_KNOWLEDGE_DB",
                "data/knowledge/nusantara_knowledge.db",
            )
        )

        if not self.db_path.is_absolute():
            self.db_path = Path.cwd() / self.db_path

        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        active = self._transaction_connection.get()
        if active is not None:
            return _BorrowedConnection(active)
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @contextmanager
    def transaction(self):
        """Opt-in atomic operation across existing store methods; no schema change."""
        if self._transaction_connection.get() is not None:
            raise RuntimeError("NESTED_STORE_TRANSACTION_NOT_SUPPORTED")
        conn = self._connect()
        token = self._transaction_connection.set(conn)
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield self
            conn.commit()
        except BaseException:
            conn.rollback()
            raise
        finally:
            self._transaction_connection.reset(token)
            conn.close()

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    source TEXT,
                    content_type TEXT,
                    chunks_count INTEGER DEFAULT 0,
                    size_bytes INTEGER DEFAULT 0,
                    metadata_json TEXT,
                    created_at TEXT,
                    updated_at TEXT
                );

                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    chunk_index INTEGER DEFAULT 0,
                    start_char INTEGER DEFAULT 0,
                    end_char INTEGER DEFAULT 0,
                    tokens_estimate INTEGER DEFAULT 0,
                    metadata_json TEXT,
                    embedding BLOB NOT NULL,
                    embedding_dimension INTEGER NOT NULL,
                    embedding_model TEXT DEFAULT 'indobenchmark/indobert-base-p1',
                    stored_at TEXT,
                    store_id TEXT,
                    FOREIGN KEY(document_id)
                        REFERENCES documents(document_id)
                        ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_chunks_document
                    ON chunks(document_id);

                CREATE INDEX IF NOT EXISTS idx_chunks_dimension
                    ON chunks(embedding_dimension);
                """
            )

    @staticmethod
    def _serialize_embedding(vector: List[float]) -> bytes:
        values = [float(v) for v in vector]
        return struct.pack(f"<{len(values)}f", *values)

    @staticmethod
    def _deserialize_embedding(blob: bytes, dimension: int) -> List[float]:
        return list(struct.unpack(f"<{dimension}f", blob))

    @staticmethod
    def _json(value) -> str:
        return json.dumps(value or {}, ensure_ascii=False)

    @staticmethod
    def _parse_json(value) -> dict:
        if not value:
            return {}
        try:
            result = json.loads(value)
            return result if isinstance(result, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def _similarity(a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return -1.0

        dot = 0.0
        norm_a = 0.0
        norm_b = 0.0

        for x, y in zip(a, b):
            dot += x * y
            norm_a += x * x
            norm_b += y * y

        if norm_a <= 0.0 or norm_b <= 0.0:
            return 0.0

        return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))

    def store_chunk(self, chunk: StoredChunk) -> str:
        embedding = chunk.embedding

        if embedding is None:
            raise ValueError("Chunk tidak memiliki embedding.")

        vector = [float(v) for v in embedding.vector]
        dimension = len(vector)

        if dimension == 0:
            raise ValueError("Embedding kosong.")

        chunk_id = chunk.chunk_id
        document_id = chunk.document_id

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO chunks (
                    chunk_id,
                    document_id,
                    content,
                    chunk_index,
                    start_char,
                    end_char,
                    tokens_estimate,
                    metadata_json,
                    embedding,
                    embedding_dimension,
                    embedding_model,
                    stored_at,
                    store_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    chunk_id,
                    document_id,
                    chunk.content,
                    getattr(chunk, "chunk_index", 0),
                    getattr(chunk, "start_char", 0),
                    getattr(chunk, "end_char", 0),
                    getattr(chunk, "tokens_estimate", 0),
                    self._json(getattr(chunk, "metadata", {})),
                    self._serialize_embedding(vector),
                    dimension,
                    getattr(embedding, "model", "indobenchmark/indobert-base-p1"),
                    getattr(chunk, "stored_at", datetime.utcnow()).isoformat(),
                    getattr(chunk, "store_id", None),
                ),
            )

        return chunk_id

    def store_document_info(self, document: DocumentInfo) -> str:
        document_id = document.document_id

        metadata = getattr(document, "metadata", {}) or {}

        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO documents (
                    document_id,
                    title,
                    source,
                    content_type,
                    chunks_count,
                    size_bytes,
                    metadata_json,
                    created_at,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_id,
                    document.title,
                    getattr(document, "source", ""),
                    getattr(document, "content_type", "text/plain"),
                    getattr(document, "chunks_count", 0),
                    getattr(document, "size_bytes", 0),
                    self._json(metadata),
                    getattr(
                        document,
                        "created_at",
                        datetime.utcnow(),
                    ).isoformat(),
                    datetime.utcnow().isoformat(),
                ),
            )

        return document_id

    def update_document_chunks_count(self, document_id: str, count: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE documents SET chunks_count = ?, updated_at = ? WHERE document_id = ?",
                (int(count), datetime.utcnow().isoformat(), document_id),
            )
        return cursor.rowcount > 0

    def get_chunk(self, chunk_id: str) -> Optional[StoredChunk]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM chunks WHERE chunk_id = ?",
                (chunk_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_chunk(row)

    def get_chunks_by_document(self, document_id: str) -> List[StoredChunk]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM chunks
                WHERE document_id = ?
                ORDER BY chunk_index ASC
                """,
                (document_id,),
            ).fetchall()

        return [self._row_to_chunk(row) for row in rows]

    def get_document_info(self, document_id: str) -> Optional[DocumentInfo]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE document_id = ?",
                (document_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_document(row)

    def search_similarity(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[tuple]:
        results = []

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM chunks
                WHERE embedding_dimension = ?
                """,
                (len(query_embedding),),
            ).fetchall()

        for row in rows:
            vector = self._deserialize_embedding(
                row["embedding"],
                row["embedding_dimension"],
            )

            score = self._similarity(query_embedding, vector)

            chunk = self._row_to_chunk(row)
            results.append((chunk, score))

        results.sort(key=lambda item: item[1], reverse=True)

        return results[: max(1, int(top_k))]

    def search_lexical(
        self,
        query: str,
        top_k: int = 20,
    ) -> List[tuple]:
        """
        Lexical Retrieval V2.

        Fitur:
        - lowercase
        - regex tokenization
        - stopword sederhana Bahasa Indonesia
        - exact token matching
        - read-only terhadap database
        """

        import re

        STOPWORDS = {
            "yang", "dan", "atau", "untuk", "dari", "dengan",
            "pada", "dalam", "adalah", "itu", "ini", "ke",
            "di", "dapat", "bisa", "akan", "sebagai", "oleh",
            "cara", "bagaimana", "apa", "apa", "sebuah",
            "suatu", "lebih", "agar", "juga", "sudah",
            "telah", "saya", "anda", "kita", "mereka",
        }

        def tokenize(text: str) -> set:
            tokens = re.findall(
                r"\b[a-zA-Z0-9_]+\b",
                text.lower(),
                re.UNICODE,
            )

            return {
                token
                for token in tokens
                if token not in STOPWORDS
            }

        query_words = tokenize(query)

        if not query_words:
            return []

        results = []

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM chunks
                """
            ).fetchall()

        for row in rows:
            chunk = self._row_to_chunk(row)
            content_words = tokenize(chunk.content)

            if not content_words:
                continue

            overlap = len(query_words & content_words)

            if overlap == 0:
                continue

            score = overlap / len(query_words)

            results.append(
                (
                    chunk,
                    min(score, 1.0),
                )
            )

        results.sort(
            key=lambda item: item[1],
            reverse=True,
        )

        return results[: max(1, int(top_k))]

    def delete_document(self, document_id: str) -> bool:
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM documents WHERE document_id = ?",
                (document_id,),
            )

        return cursor.rowcount > 0

    def list_documents(self) -> List[DocumentInfo]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM documents
                ORDER BY updated_at DESC
                """
            ).fetchall()

        return [self._row_to_document(row) for row in rows]

    def _row_to_chunk(self, row: sqlite3.Row) -> StoredChunk:
        from .schemas import EmbeddingResult

        vector = self._deserialize_embedding(
            row["embedding"],
            row["embedding_dimension"],
        )

        embedding = EmbeddingResult(
            vector=vector,
            dimension=row["embedding_dimension"],
            model=row["embedding_model"],
            metadata={},
        )

        return StoredChunk(
            chunk_id=row["chunk_id"],
            document_id=row["document_id"],
            content=row["content"],
            chunk_index=row["chunk_index"],
            start_char=row["start_char"],
            end_char=row["end_char"],
            tokens_estimate=row["tokens_estimate"],
            metadata=self._parse_json(row["metadata_json"]),
            embedding=embedding,
            stored_at=datetime.fromisoformat(row["stored_at"]),
            store_id=row["store_id"],
        )

    def _row_to_document(self, row: sqlite3.Row) -> DocumentInfo:
        return DocumentInfo(
            document_id=row["document_id"],
            title=row["title"],
            source=row["source"],
            content_type=row["content_type"],
            chunks_count=row["chunks_count"],
            size_bytes=row["size_bytes"],
            metadata=self._parse_json(row["metadata_json"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
