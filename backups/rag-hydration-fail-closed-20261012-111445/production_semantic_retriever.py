"""
Nusantara AI - Production Semantic Retriever
Phase 19.2

Tujuan:
- Production lexical retrieval menggunakan SQLite FTS5.
- Production semantic retrieval menggunakan IndoBERT bridge.
- Hybrid scoring semantic + lexical.
- Metadata filtering.
- Relevance gate.
- Evidence-compatible output.
- Tidak menggantikan legacy RAG.
- Tidak mengubah routes.py / KnowledgeEngine / rag.py.

Arsitektur:

    Query
      |
      +--------------------+
      |                    |
      v                    v
    FTS5             IndoBERT Bridge
      |                    |
      +---------+----------+
                |
                v
         Hybrid Scoring
                |
                v
          Relevance Gate
                |
                v
        Evidence-compatible
             results

Default:
    semantic_weight = 0.70
    lexical_weight  = 0.30

Database:
    data/knowledge/production_knowledge.db

Bridge:
    app.knowledge.production_embedding_bridge.search_semantic()
"""

from __future__ import annotations

import argparse
import json
import logging
import math
import re
import sqlite3
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Iterable, Optional


# ---------------------------------------------------------------------------
# PATHS
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DB = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "production_knowledge.db"
)


# ---------------------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------------------

logger = logging.getLogger("nusantara.production_semantic_retriever")


# ---------------------------------------------------------------------------
# IMPORT PRODUCTION SEMANTIC BRIDGE
# ---------------------------------------------------------------------------

try:
    from app.knowledge.production_embedding_bridge import (
        search_semantic,
    )
except Exception as exc:  # pragma: no cover
    search_semantic = None
    _BRIDGE_IMPORT_ERROR = str(exc)
else:
    _BRIDGE_IMPORT_ERROR = None


# ---------------------------------------------------------------------------
# DATA MODEL
# ---------------------------------------------------------------------------


@dataclass
class RetrievalEvidence:
    """
    Evidence-compatible result.

    Field names intentionally remain generic so this object can later
    be adapted to the existing KnowledgeEngine/RAG Evidence schema
    without changing this module.
    """

    chunk_id: str
    text: str
    score: float

    semantic_score: float = 0.0
    lexical_score: float = 0.0

    source_id: Optional[str] = None
    source_name: Optional[str] = None
    source_status: Optional[str] = None

    service: Optional[str] = None
    content_type: Optional[str] = None

    authority: Optional[str] = None
    source_url: Optional[str] = None

    score_explanation: str = ""

    metadata: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# UTILITY
# ---------------------------------------------------------------------------


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        if math.isfinite(number):
            return number
    except (TypeError, ValueError):
        pass

    return default


def _normalize_score(value: Any) -> float:
    """
    Normalize an arbitrary score into [0, 1].

    Handles:
    - already normalized values
    - negative similarity values
    - cosine-like [-1, 1]
    - distances where possible through caller-specific conversion
    """

    score = _safe_float(value)

    if score < 0.0:
        score = (score + 1.0) / 2.0

    if score > 1.0:
        score = 1.0

    if score < 0.0:
        score = 0.0

    return score


def _tokenize(text: str) -> list[str]:
    if not text:
        return []

    return re.findall(
        r"[a-zA-Z0-9À-ÿ_]+",
        text.lower(),
    )


def _token_set(text: str) -> set[str]:
    return set(_tokenize(text))


def _lexical_overlap(query: str, text: str) -> float:
    """
    Simple deterministic lexical relevance.

    This intentionally does not use an LLM.
    """

    query_tokens = _token_set(query)
    text_tokens = _token_set(text)

    if not query_tokens or not text_tokens:
        return 0.0

    overlap = query_tokens & text_tokens

    return min(
        1.0,
        len(overlap) / max(1, len(query_tokens)),
    )


def _first_value(
    row: sqlite3.Row | dict[str, Any],
    candidates: Iterable[str],
    default: Any = None,
) -> Any:
    keys = row.keys()

    for candidate in candidates:
        if candidate in keys:
            value = row[candidate]
            if value is not None and str(value).strip():
                return value

    return default


def _quote_fts_token(token: str) -> str:
    token = token.replace('"', '""')
    return f'"{token}"'


# ---------------------------------------------------------------------------
# RETRIEVER
# ---------------------------------------------------------------------------


class ProductionSemanticRetriever:
    """
    Production retrieval layer for Phase 19.2.

    It does NOT replace legacy RAG.

    Retrieval:
        semantic = production_embedding_bridge.search_semantic()
        lexical  = SQLite FTS5
        final    = semantic_weight * semantic
                 + lexical_weight * lexical
    """

    def __init__(
        self,
        db_path: str | Path = DEFAULT_DB,
        semantic_weight: float = 0.70,
        lexical_weight: float = 0.30,
        min_score: float = 0.30,
        relative_threshold: float = 0.50,
    ) -> None:

        self.db_path = Path(db_path)

        self.semantic_weight = float(semantic_weight)
        self.lexical_weight = float(lexical_weight)

        self.min_score = float(min_score)
        self.relative_threshold = float(relative_threshold)

        self._validate_weights()

    # ------------------------------------------------------------------
    # CONFIG
    # ------------------------------------------------------------------

    def _validate_weights(self) -> None:
        if self.semantic_weight < 0:
            raise ValueError("semantic_weight tidak boleh negatif.")

        if self.lexical_weight < 0:
            raise ValueError("lexical_weight tidak boleh negatif.")

        total = self.semantic_weight + self.lexical_weight

        if total <= 0:
            raise ValueError(
                "semantic_weight + lexical_weight harus > 0."
            )

        self.semantic_weight /= total
        self.lexical_weight /= total

    # ------------------------------------------------------------------
    # DATABASE
    # ------------------------------------------------------------------

    def _connect(self) -> sqlite3.Connection:
        if not self.db_path.exists():
            raise FileNotFoundError(
                f"Production database tidak ditemukan: {self.db_path}"
            )

        conn = sqlite3.connect(str(self.db_path))

        conn.row_factory = sqlite3.Row

        return conn

    def _table_exists(
        self,
        conn: sqlite3.Connection,
        table_name: str,
    ) -> bool:

        row = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = ?
            """,
            (table_name,),
        ).fetchone()

        return row is not None

    def _table_columns(
        self,
        conn: sqlite3.Connection,
        table_name: str,
    ) -> list[str]:

        if not self._table_exists(conn, table_name):
            return []

        rows = conn.execute(
            f'PRAGMA table_info("{table_name}")'
        ).fetchall()

        return [
            str(row["name"])
            for row in rows
        ]

    # ------------------------------------------------------------------
    # FTS5
    # ------------------------------------------------------------------

    def _detect_fts_table(
        self,
        conn: sqlite3.Connection,
    ) -> Optional[str]:

        preferred = [
            "chunks_fts",
            "chunk_fts",
            "chunks_fts5",
        ]

        for table in preferred:
            if self._table_exists(conn, table):
                return table

        rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name LIKE '%fts%'
            ORDER BY name
            """
        ).fetchall()

        if rows:
            return str(rows[0]["name"])

        return None

    def _fts_search(
        self,
        conn: sqlite3.Connection,
        query: str,
        top_k: int,
        service: Optional[str] = None,
        content_type: Optional[str] = None,
        source_status: Optional[str] = None,
    ) -> list[dict[str, Any]]:

        table = self._detect_fts_table(conn)

        if not table:
            logger.warning(
                "Tidak ada tabel FTS5 ditemukan."
            )
            return []

        tokens = _tokenize(query)

        if not tokens:
            return []

        # OR semantics memberikan recall lebih baik untuk Bahasa Indonesia.
        fts_query = " OR ".join(
            _quote_fts_token(token)
            for token in tokens
        )

        try:
            rows = conn.execute(
                f"""
                SELECT *
                FROM "{table}"
                WHERE "{table}" MATCH ?
                LIMIT ?
                """,
                (fts_query, max(top_k * 5, top_k)),
            ).fetchall()

        except sqlite3.Error as exc:
            logger.warning(
                "FTS search gagal: %s",
                exc,
            )
            return []

        results: list[dict[str, Any]] = []

        for row in rows:

            text = _first_value(
                row,
                [
                    "chunk",
                    "text",
                    "content",
                    "body",
                    "document",
                ],
                "",
            )

            score = _lexical_overlap(
                query,
                str(text),
            )

            result = {
                "chunk_id": _first_value(
                    row,
                    [
                        "chunk_id",
                        "id",
                        "rowid",
                    ],
                ),
                "text": str(text),
                "lexical_score": score,
                "source_id": _first_value(
                    row,
                    [
                        "source_id",
                        "document_id",
                        "doc_id",
                    ],
                ),
                "source_name": _first_value(
                    row,
                    [
                        "source_name",
                        "document_name",
                        "filename",
                        "file_name",
                    ],
                ),
                "source_status": _first_value(
                    row,
                    [
                        "source_status",
                        "status",
                    ],
                ),
                "service": _first_value(
                    row,
                    [
                        "service",
                        "service_type",
                    ],
                ),
                "content_type": _first_value(
                    row,
                    [
                        "content_type",
                        "type",
                    ],
                ),
                "authority": _first_value(
                    row,
                    [
                        "authority",
                    ],
                ),
                "source_url": _first_value(
                    row,
                    [
                        "source_url",
                        "url",
                    ],
                ),
            }

            # Metadata filters are applied after retrieval so that
            # varying FTS schemas remain supported.
            if service:
                if str(result.get("service") or "").lower() != service.lower():
                    continue

            if content_type:
                if (
                    str(result.get("content_type") or "").lower()
                    != content_type.lower()
                ):
                    continue

            if source_status:
                if (
                    str(result.get("source_status") or "").lower()
                    != source_status.lower()
                ):
                    continue

            results.append(result)

        results.sort(
            key=lambda item: float(
                item.get("lexical_score", 0.0)
            ),
            reverse=True,
        )

        return results[:top_k]

    # ------------------------------------------------------------------
    # SEMANTIC
    # ------------------------------------------------------------------

    def _semantic_search(
        self,
        query: str,
        top_k: int,
    ) -> list[dict[str, Any]]:

        if search_semantic is None:
            logger.warning(
                "Production semantic bridge tidak dapat diimport: %s",
                _BRIDGE_IMPORT_ERROR,
            )
            return []

        try:
            raw = search_semantic(
                query,
                top_k=top_k,
            )

        except Exception as exc:
            logger.warning(
                "Semantic search gagal: %s",
                exc,
            )
            return []

        if raw is None:
            return []

        if isinstance(raw, dict):

            for key in (
                "results",
                "items",
                "data",
                "matches",
            ):
                if isinstance(raw.get(key), list):
                    raw = raw[key]
                    break
            else:
                raw = [raw]

        if not isinstance(raw, (list, tuple)):
            return []

        results: list[dict[str, Any]] = []

        for item in raw:

            if hasattr(item, "model_dump"):
                item = item.model_dump()

            elif hasattr(item, "dict"):
                item = item.dict()

            elif hasattr(item, "__dict__") and not isinstance(
                item,
                dict,
            ):
                item = vars(item)

            if not isinstance(item, dict):
                continue

            text = _first_value(
                item,
                [
                    "text",
                    "chunk",
                    "content",
                    "body",
                ],
                "",
            )

            raw_score = _first_value(
                item,
                [
                    "score",
                    "similarity",
                    "cosine_similarity",
                    "semantic_score",
                ],
                0.0,
            )

            result = dict(item)

            result["text"] = str(text)

            result["semantic_score"] = _normalize_score(
                raw_score
            )

            result["chunk_id"] = _first_value(
                item,
                [
                    "chunk_id",
                    "id",
                ],
            )

            results.append(result)

        results.sort(
            key=lambda item: float(
                item.get("semantic_score", 0.0)
            ),
            reverse=True,
        )

        return results[:top_k]

    # ------------------------------------------------------------------
    # HYBRID
    # ------------------------------------------------------------------

    def _merge_results(
        self,
        query: str,
        semantic_results: list[dict[str, Any]],
        lexical_results: list[dict[str, Any]],
    ) -> list[RetrievalEvidence]:

        merged: dict[str, RetrievalEvidence] = {}

        # --------------------------------------------------------------
        # Semantic results
        # --------------------------------------------------------------

        for index, item in enumerate(semantic_results):

            chunk_id = item.get("chunk_id")

            if chunk_id is None:
                chunk_id = (
                    f"semantic:{index}:"
                    f"{hash(str(item.get('text', '')))}"
                )

            key = str(chunk_id)

            evidence = merged.get(key)

            if evidence is None:

                evidence = RetrievalEvidence(
                    chunk_id=key,
                    text=str(
                        item.get("text")
                        or item.get("chunk")
                        or ""
                    ),
                    score=0.0,
                    semantic_score=_normalize_score(
                        item.get("semantic_score", 0.0)
                    ),
                    lexical_score=0.0,
                    source_id=_first_value(
                        item,
                        [
                            "source_id",
                            "document_id",
                            "doc_id",
                        ],
                    ),
                    source_name=_first_value(
                        item,
                        [
                            "source_name",
                            "document_name",
                            "filename",
                            "file_name",
                        ],
                    ),
                    source_status=_first_value(
                        item,
                        [
                            "source_status",
                            "status",
                        ],
                    ),
                    service=_first_value(
                        item,
                        [
                            "service",
                            "service_type",
                        ],
                    ),
                    content_type=_first_value(
                        item,
                        [
                            "content_type",
                            "type",
                        ],
                    ),
                    authority=_first_value(
                        item,
                        [
                            "authority",
                        ],
                    ),
                    source_url=_first_value(
                        item,
                        [
                            "source_url",
                            "url",
                        ],
                    ),
                    metadata={
                        "retrieval_source": "semantic",
                    },
                )

                merged[key] = evidence

        # --------------------------------------------------------------
        # Lexical results
        # --------------------------------------------------------------

        for item in lexical_results:

            chunk_id = item.get("chunk_id")

            if chunk_id is None:
                chunk_id = (
                    f"lexical:"
                    f"{hash(str(item.get('text', '')))}"
                )

            key = str(chunk_id)

            evidence = merged.get(key)

            if evidence is None:

                evidence = RetrievalEvidence(
                    chunk_id=key,
                    text=str(
                        item.get("text")
                        or ""
                    ),
                    score=0.0,
                    semantic_score=0.0,
                    lexical_score=_normalize_score(
                        item.get("lexical_score", 0.0)
                    ),
                    source_id=item.get("source_id"),
                    source_name=item.get("source_name"),
                    source_status=item.get("source_status"),
                    service=item.get("service"),
                    content_type=item.get("content_type"),
                    authority=item.get("authority"),
                    source_url=item.get("source_url"),
                    metadata={
                        "retrieval_source": "lexical",
                    },
                )

                merged[key] = evidence

            else:

                evidence.lexical_score = _normalize_score(
                    item.get("lexical_score", 0.0)
                )

                if not evidence.text:
                    evidence.text = str(
                        item.get("text") or ""
                    )

                for attr in (
                    "source_id",
                    "source_name",
                    "source_status",
                    "service",
                    "content_type",
                    "authority",
                    "source_url",
                ):
                    current = getattr(
                        evidence,
                        attr,
                    )

                    if current is None:
                        setattr(
                            evidence,
                            attr,
                            item.get(attr),
                        )

                if evidence.metadata is None:
                    evidence.metadata = {}

                evidence.metadata[
                    "retrieval_source"
                ] = "hybrid"

        # --------------------------------------------------------------
        # Calculate hybrid score
        # --------------------------------------------------------------

        for evidence in merged.values():

            evidence.score = (
                self.semantic_weight
                * evidence.semantic_score
                + self.lexical_weight
                * evidence.lexical_score
            )

            evidence.score_explanation = (
                f"hybrid={evidence.score:.4f}; "
                f"semantic={evidence.semantic_score:.4f}"
                f"×{self.semantic_weight:.2f}; "
                f"lexical={evidence.lexical_score:.4f}"
                f"×{self.lexical_weight:.2f}"
            )

            if evidence.metadata is None:
                evidence.metadata = {}

            evidence.metadata.update(
                {
                    "semantic_weight": self.semantic_weight,
                    "lexical_weight": self.lexical_weight,
                    "query": query,
                }
            )

        results = list(merged.values())

        # --------------------------------------------------------------
        # AUTHORITY METADATA HYDRATION
        # --------------------------------------------------------------
        # Pastikan metadata authority berasal dari database production,
        # bukan hanya dari FTS5 atau semantic bridge.
        results = self._hydrate_document_metadata(
            results
        )

        results.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        return results

    # ------------------------------------------------------------------
    # AUTHORITY METADATA HYDRATION
    # ------------------------------------------------------------------

    def _hydrate_document_metadata(
        self,
        evidence: list[RetrievalEvidence],
    ) -> list[RetrievalEvidence]:
        """
        Mengambil metadata authority langsung dari tabel documents.

        FTS5 dan semantic bridge tidak selalu membawa seluruh metadata
        dokumen. Karena Authority Engine membutuhkan source_status,
        authority dan verified yang dapat dipercaya, metadata dokumen
        di-hydrate ulang dari database produksi sebelum evidence
        diteruskan ke layer berikutnya.
        """

        if not evidence:
            return evidence

        try:
            conn = self._connect()
        except Exception as exc:
            logger.warning(
                "Authority metadata hydration: database gagal dibuka: %s",
                exc,
            )
            return evidence

        try:
            document_columns = set(
                self._table_columns(conn, "documents")
            )

            if "document_id" not in document_columns:
                logger.warning(
                    "Authority metadata hydration: "
                    "kolom documents.document_id tidak ditemukan."
                )
                return evidence

            chunk_columns = set(
                self._table_columns(conn, "chunks")
            )

            for item in evidence:

                document_id = None

                # ------------------------------------------------------
                # 1. Coba source_id
                # ------------------------------------------------------

                source_id = getattr(
                    item,
                    "source_id",
                    None,
                )

                if source_id:
                    row = conn.execute(
                        """
                        SELECT *
                        FROM documents
                        WHERE document_id = ?
                        LIMIT 1
                        """,
                        (str(source_id),),
                    ).fetchone()

                    if row is not None:
                        document_id = str(
                            row["document_id"]
                        )

                # ------------------------------------------------------
                # 2. Coba chunk_id -> chunks.document_id
                # ------------------------------------------------------

                if document_id is None and chunk_columns:
                    chunk_id = getattr(
                        item,
                        "chunk_id",
                        None,
                    )

                    if chunk_id:
                        chunk_row = None

                        candidate_columns = [
                            column
                            for column in (
                                "chunk_id",
                                "id",
                            )
                            if column in chunk_columns
                        ]

                        for column in candidate_columns:
                            try:
                                chunk_row = conn.execute(
                                    f"""
                                    SELECT *
                                    FROM chunks
                                    WHERE "{column}" = ?
                                    LIMIT 1
                                    """,
                                    (str(chunk_id),),
                                ).fetchone()
                            except sqlite3.Error:
                                chunk_row = None

                            if chunk_row is not None:
                                break

                        if chunk_row is not None:
                            if "document_id" in chunk_columns:
                                try:
                                    document_id = str(
                                        chunk_row["document_id"]
                                    )
                                except Exception:
                                    document_id = None

                # ------------------------------------------------------
                # 3. Cari berdasarkan source_name / source_file
                # ------------------------------------------------------

                if document_id is None:
                    source_name = getattr(
                        item,
                        "source_name",
                        None,
                    )

                    if source_name and "source_file" in document_columns:
                        row = conn.execute(
                            """
                            SELECT *
                            FROM documents
                            WHERE source_file = ?
                            LIMIT 1
                            """,
                            (str(source_name),),
                        ).fetchone()

                        if row is not None:
                            document_id = str(
                                row["document_id"]
                            )

                if document_id is None:
                    continue

                # ------------------------------------------------------
                # 4. Ambil metadata authoritative dari documents
                # ------------------------------------------------------

                row = conn.execute(
                    """
                    SELECT *
                    FROM documents
                    WHERE document_id = ?
                    LIMIT 1
                    """,
                    (document_id,),
                ).fetchone()

                if row is None:
                    continue

                def row_value(name, default=None):
                    if name not in document_columns:
                        return default

                    try:
                        return row[name]
                    except Exception:
                        return default

                source_status = row_value(
                    "source_status",
                    "unknown",
                )

                authority = row_value(
                    "authority",
                    "unknown",
                )

                verified = row_value(
                    "verified",
                    0,
                )

                service = row_value(
                    "service",
                    None,
                )

                content_type = row_value(
                    "content_type",
                    None,
                )

                source_type = row_value(
                    "source_type",
                    None,
                )

                source_file = row_value(
                    "source_file",
                    None,
                )

                # ------------------------------------------------------
                # 5. Override metadata evidence dengan DB authority
                # ------------------------------------------------------

                if source_status is not None:
                    item.source_status = str(
                        source_status
                    ).strip().lower()

                if authority is not None:
                    item.authority = str(
                        authority
                    ).strip().lower()

                if service is not None:
                    item.service = str(
                        service
                    ).strip()

                if content_type is not None:
                    item.content_type = str(
                        content_type
                    ).strip()

                if source_file:
                    item.source_name = str(
                        source_file
                    )

                # ------------------------------------------------------
                # 6. Simpan verified + provenance ke metadata
                # ------------------------------------------------------

                if item.metadata is None:
                    item.metadata = {}

                item.metadata.update(
                    {
                        "document_id": document_id,
                        "source_status": item.source_status,
                        "authority": item.authority,
                        "verified": bool(verified),
                        "verified_raw": verified,
                        "service": item.service,
                        "content_type": item.content_type,
                        "source_type": source_type,
                        "authority_hydrated_from": "documents",
                    }
                )

            return evidence

        except Exception as exc:
            logger.exception(
                "Authority metadata hydration gagal: %s",
                exc,
            )
            return evidence

        finally:
            conn.close()

    # ------------------------------------------------------------------
    # METADATA FILTER
    # ------------------------------------------------------------------

    @staticmethod
    def _passes_filters(
        evidence: RetrievalEvidence,
        service: Optional[str],
        content_type: Optional[str],
        source_status: Optional[str],
    ) -> bool:

        if service:
            if (
                str(evidence.service or "").lower()
                != service.lower()
            ):
                return False

        if content_type:
            if (
                str(evidence.content_type or "").lower()
                != content_type.lower()
            ):
                return False

        if source_status:
            if (
                str(evidence.source_status or "").lower()
                != source_status.lower()
            ):
                return False

        return True

    # ------------------------------------------------------------------
    # RELEVANCE GATE
    # ------------------------------------------------------------------

    def _apply_relevance_gate(
        self,
        evidence: list[RetrievalEvidence],
    ) -> list[RetrievalEvidence]:

        if not evidence:
            return []

        evidence = sorted(
            evidence,
            key=lambda item: item.score,
            reverse=True,
        )

        top_score = float(
            evidence[0].score
        )

        threshold = max(
            self.min_score,
            top_score * self.relative_threshold,
        )

        filtered = [
            item
            for item in evidence
            if item.score >= threshold
        ]

        logger.info(
            "Production semantic relevance gate: "
            "top_score=%.4f threshold=%.4f before=%d after=%d",
            top_score,
            threshold,
            len(evidence),
            len(filtered),
        )

        return filtered

    # ------------------------------------------------------------------
    # PUBLIC SEARCH
    # ------------------------------------------------------------------

    @staticmethod
    def _authority_valid(item) -> bool:
        """Fail closed unless source authority was hydrated and verified."""
        metadata = getattr(item, "metadata", None)
        if not isinstance(metadata, dict):
            return False

        hydrated_from = str(
            metadata.get("authority_hydrated_from", "")
        ).strip().lower()
        if hydrated_from != "documents":
            return False

        status = str(
            getattr(item, "source_status", None)
            or metadata.get("source_status", "")
        ).strip().lower()

        authority = str(
            getattr(item, "authority", None)
            or metadata.get("authority", "")
        ).strip().lower()

        # Status must explicitly indicate an official/verified source.
        if status not in {"official", "verified"}:
            return False

        # Reject missing or explicitly untrusted authority labels.
        if authority in {
            "", "unknown", "none", "null", "false",
            "test", "untrusted", "unverified"
        }:
            return False

        # Parse verification values safely; bool("false") is True in Python.
        verified = metadata.get(
            "verified_raw",
            metadata.get("verified", False)
        )

        if isinstance(verified, bool):
            is_verified = verified
        elif isinstance(verified, int):
            is_verified = verified == 1
        elif isinstance(verified, str):
            is_verified = verified.strip().lower() in {
                "1", "true", "yes", "verified"
            }
        else:
            is_verified = False

        return is_verified

    def search(
        self,
        query: str,
        top_k: int = 5,
        lexical_k: Optional[int] = None,
        semantic_k: Optional[int] = None,
        service: Optional[str] = None,
        content_type: Optional[str] = None,
        source_status: Optional[str] = None,
        apply_gate: bool = True,
        require_authoritative_source: bool = False,
    ) -> list[RetrievalEvidence]:

        query = str(query or "").strip()

        if not query:
            return []

        top_k = max(1, int(top_k))

        lexical_k = lexical_k or max(
            top_k * 3,
            10,
        )

        semantic_k = semantic_k or max(
            top_k * 3,
            10,
        )

        semantic_results = self._semantic_search(
            query,
            semantic_k,
        )

        try:
            with self._connect() as conn:

                lexical_results = self._fts_search(
                    conn,
                    query,
                    lexical_k,
                    service=service,
                    content_type=content_type,
                    source_status=source_status,
                )

        except FileNotFoundError:
            raise

        except Exception as exc:
            logger.warning(
                "Lexical retrieval gagal: %s",
                exc,
            )
            lexical_results = []

        merged = self._merge_results(
            query,
            semantic_results,
            lexical_results,
        )

        merged = [
            item
            for item in merged
            if self._passes_filters(
                item,
                service,
                content_type,
                source_status,
            )
        ]

        if apply_gate:
            merged = self._apply_relevance_gate(
                merged
            )

        if require_authoritative_source:
            merged = [
                item
                for item in merged
                if self._authority_valid(item)
            ]

        return merged[:top_k]

    # ------------------------------------------------------------------
    # STATS
    # ------------------------------------------------------------------

    def stats(self) -> dict[str, Any]:

        result: dict[str, Any] = {
            "database": str(self.db_path),
            "database_exists": self.db_path.exists(),
            "bridge_available": search_semantic is not None,
            "bridge_import_error": _BRIDGE_IMPORT_ERROR,
            "semantic_weight": self.semantic_weight,
            "lexical_weight": self.lexical_weight,
            "min_score": self.min_score,
            "relative_threshold": self.relative_threshold,
        }

        if not self.db_path.exists():
            return result

        with self._connect() as conn:

            tables = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                ORDER BY name
                """
            ).fetchall()

            table_names = [
                str(row["name"])
                for row in tables
            ]

            result["tables"] = table_names

            for table in (
                "documents",
                "chunks",
                "source_registry",
                "chunk_embeddings",
                "embedding_runs",
            ):

                if self._table_exists(
                    conn,
                    table,
                ):
                    row = conn.execute(
                        f'SELECT COUNT(*) AS count FROM "{table}"'
                    ).fetchone()

                    result[f"{table}_count"] = int(
                        row["count"]
                    )

            result["fts_table"] = (
                self._detect_fts_table(conn)
            )

        return result

    # ------------------------------------------------------------------
    # SELF TEST
    # ------------------------------------------------------------------

    def self_test(self) -> int:

        print(
            "Nusantara AI Production Semantic Retriever"
        )
        print(
            "Phase 19.2"
        )
        print()

        # --------------------------------------------------------------
        # Config
        # --------------------------------------------------------------

        total = (
            self.semantic_weight
            + self.lexical_weight
        )

        assert abs(total - 1.0) < 1e-9

        print(
            "[PASS] Hybrid weights"
        )

        assert 0.0 <= self.min_score <= 1.0

        print(
            "[PASS] Relevance configuration"
        )

        # --------------------------------------------------------------
        # DB
        # --------------------------------------------------------------

        assert self.db_path.exists(), (
            f"Database tidak ditemukan: {self.db_path}"
        )

        print(
            "[PASS] Production database exists"
        )

        with self._connect() as conn:

            assert self._table_exists(
                conn,
                "chunks",
            )

            print(
                "[PASS] chunks table"
            )

            assert self._table_exists(
                conn,
                "chunk_embeddings",
            )

            print(
                "[PASS] chunk_embeddings table"
            )

            assert self._table_exists(
                conn,
                "source_registry",
            )

            print(
                "[PASS] source_registry table"
            )

            fts_table = self._detect_fts_table(
                conn
            )

            if fts_table:
                print(
                    f"[PASS] FTS table: {fts_table}"
                )
            else:
                print(
                    "[WARN] FTS5 table belum ditemukan"
                )

        # --------------------------------------------------------------
        # Bridge
        # --------------------------------------------------------------

        if search_semantic is not None:
            print(
                "[PASS] IndoBERT semantic bridge import"
            )
        else:
            print(
                "[WARN] Semantic bridge unavailable"
            )

        # --------------------------------------------------------------
        # Deterministic lexical scoring
        # --------------------------------------------------------------

        lexical_score = _lexical_overlap(
            "status KTP",
            "Status pengajuan KTP dapat diperiksa",
        )

        assert lexical_score > 0.0

        print(
            "[PASS] Lexical scoring"
        )

        # --------------------------------------------------------------
        # Hybrid scoring
        # --------------------------------------------------------------

        semantic = 0.8
        lexical = 0.6

        hybrid = (
            self.semantic_weight * semantic
            + self.lexical_weight * lexical
        )

        assert 0.0 <= hybrid <= 1.0

        print(
            f"[PASS] Hybrid scoring = {hybrid:.4f}"
        )

        # --------------------------------------------------------------
        # Gate
        # --------------------------------------------------------------

        sample = [
            RetrievalEvidence(
                chunk_id="a",
                text="high",
                score=0.90,
            ),
            RetrievalEvidence(
                chunk_id="b",
                text="medium",
                score=0.55,
            ),
            RetrievalEvidence(
                chunk_id="c",
                text="low",
                score=0.10,
            ),
        ]

        gated = self._apply_relevance_gate(
            sample
        )

        assert len(gated) >= 1
        assert gated[0].chunk_id == "a"

        print(
            "[PASS] Relevance gate"
        )

        # --------------------------------------------------------------
        # Empty query
        # --------------------------------------------------------------

        assert self.search("") == []

        print(
            "[PASS] Empty query handling"
        )

        print()
        print(
            "PRODUCTION_SEMANTIC_RETRIEVER_SELFTEST: PASS"
        )

        return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Nusantara AI Production Semantic Retriever "
            "Phase 19.2"
        )
    )

    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB),
        help="Path production knowledge database.",
    )

    parser.add_argument(
        "--semantic-weight",
        type=float,
        default=0.70,
    )

    parser.add_argument(
        "--lexical-weight",
        type=float,
        default=0.30,
    )

    parser.add_argument(
        "--min-score",
        type=float,
        default=0.30,
    )

    parser.add_argument(
        "--relative-threshold",
        type=float,
        default=0.50,
    )

    sub = parser.add_subparsers(
        dest="command"
    )

    sub.add_parser(
        "self-test",
        help="Run Phase 19.2 self-test.",
    )

    sub.add_parser(
        "stats",
        help="Show production retriever statistics.",
    )

    search_parser = sub.add_parser(
        "search",
        help="Run hybrid production search.",
    )

    search_parser.add_argument(
        "query",
        nargs="+",
    )

    search_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
    )

    search_parser.add_argument(
        "--service",
        default=None,
    )

    search_parser.add_argument(
        "--content-type",
        default=None,
    )

    search_parser.add_argument(
        "--source-status",
        default=None,
    )

    search_parser.add_argument(
        "--no-gate",
        action="store_true",
    )

    return parser


def main() -> int:

    parser = build_parser()

    args = parser.parse_args()

    retriever = ProductionSemanticRetriever(
        db_path=args.db,
        semantic_weight=args.semantic_weight,
        lexical_weight=args.lexical_weight,
        min_score=args.min_score,
        relative_threshold=args.relative_threshold,
    )

    if args.command == "self-test":

        return retriever.self_test()

    if args.command == "stats":

        print(
            json.dumps(
                retriever.stats(),
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )

        return 0

    if args.command == "search":

        query = " ".join(
            args.query
        )

        results = retriever.search(
            query,
            top_k=args.top_k,
            service=args.service,
            content_type=args.content_type,
            source_status=args.source_status,
            apply_gate=not args.no_gate,
        )

        payload = {
            "query": query,
            "count": len(results),
            "config": {
                "semantic_weight": retriever.semantic_weight,
                "lexical_weight": retriever.lexical_weight,
                "min_score": retriever.min_score,
                "relative_threshold": retriever.relative_threshold,
            },
            "results": [
                item.to_dict()
                for item in results
            ],
        }

        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )

        return 0

    parser.print_help()

    return 0


if __name__ == "__main__":
    raise SystemExit(
        main()
    )
