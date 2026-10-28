"""
Nusantara AI - Production Hybrid RAG Bridge
Phase 19.3

Purpose
-------
Bridge ProductionSemanticRetriever into a stable,
evidence-oriented interface without modifying the legacy RAG.

Architecture
------------
Query
  |
  v
ProductionSemanticRetriever
  |
  +--> IndoBERT semantic retrieval
  |
  +--> FTS5 lexical retrieval
  |
  v
Hybrid evidence
  |
  +--> metadata filters
  +--> source-status policy
  +--> score explanation
  |
  v
ProductionEvidencePack

Important
---------
This module does NOT:
- modify app/knowledge/rag.py
- modify app/knowledge/engine.py
- modify app/api/routes.py
- generate answers with an LLM
- modify the production database schema
- silently fabricate evidence

The bridge is intentionally isolated so it can be
benchmarked before integration into /v1/chat.
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional


LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_DB = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "production_knowledge.db"
)


# ============================================================
# DATA MODELS
# ============================================================


@dataclass
class ProductionEvidence:
    """
    Stable evidence representation used by Phase 19.3.

    This intentionally does not depend on the legacy Evidence
    class from app.knowledge.schemas.
    """

    chunk_id: str
    text: str

    score: float
    semantic_score: float
    lexical_score: float

    source_id: Optional[str] = None
    source_name: Optional[str] = None
    source_status: Optional[str] = None

    service: Optional[str] = None
    content_type: Optional[str] = None

    authority: Optional[str] = None
    source_url: Optional[str] = None

    score_explanation: str = ""

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProductionEvidencePack:
    """
    Stable evidence container for downstream grounding.

    No answer generation occurs here.
    """

    query: str
    evidence: list[ProductionEvidence]

    count: int

    retrieval_source: str = "production_hybrid"

    semantic_weight: float = 0.70
    lexical_weight: float = 0.30

    min_score: float = 0.30
    relative_threshold: float = 0.50

    filters: dict[str, Any] = field(default_factory=dict)

    grounded_candidate: bool = False

    reason: str = ""

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "count": self.count,
            "retrieval_source": self.retrieval_source,
            "semantic_weight": self.semantic_weight,
            "lexical_weight": self.lexical_weight,
            "min_score": self.min_score,
            "relative_threshold": self.relative_threshold,
            "filters": self.filters,
            "grounded_candidate": self.grounded_candidate,
            "reason": self.reason,
            "evidence": [
                item.to_dict()
                for item in self.evidence
            ],
            "metadata": self.metadata,
        }


# ============================================================
# HYBRID RAG BRIDGE
# ============================================================


class ProductionHybridRAG:
    """
    Phase 19.3 production bridge.

    It consumes ProductionSemanticRetriever and converts its
    results into a stable evidence pack.

    No legacy RAG code is touched.
    """

    DEFAULT_SEMANTIC_WEIGHT = 0.70
    DEFAULT_LEXICAL_WEIGHT = 0.30
    DEFAULT_MIN_SCORE = 0.30
    DEFAULT_RELATIVE_THRESHOLD = 0.50

    ALLOWED_SOURCE_STATUSES = {
        "official",
        "verified",
    }

    def __init__(
        self,
        db_path: str | Path = DEFAULT_DB,
        semantic_weight: float = DEFAULT_SEMANTIC_WEIGHT,
        lexical_weight: float = DEFAULT_LEXICAL_WEIGHT,
        min_score: float = DEFAULT_MIN_SCORE,
        relative_threshold: float = DEFAULT_RELATIVE_THRESHOLD,
        allow_unknown_sources: bool = False,
    ) -> None:

        self.db_path = Path(db_path)

        self.semantic_weight = float(semantic_weight)
        self.lexical_weight = float(lexical_weight)

        self.min_score = float(min_score)
        self.relative_threshold = float(relative_threshold)

        self.allow_unknown_sources = bool(
            allow_unknown_sources
        )

        self._validate_config()

        self._retriever = None

    # --------------------------------------------------------
    # CONFIGURATION
    # --------------------------------------------------------

    def _validate_config(self) -> None:

        if self.semantic_weight < 0:
            raise ValueError(
                "semantic_weight tidak boleh negatif."
            )

        if self.lexical_weight < 0:
            raise ValueError(
                "lexical_weight tidak boleh negatif."
            )

        total = (
            self.semantic_weight
            + self.lexical_weight
        )

        if total <= 0:
            raise ValueError(
                "semantic_weight + lexical_weight harus > 0."
            )

        if abs(total - 1.0) > 0.000001:
            raise ValueError(
                "semantic_weight + lexical_weight "
                "harus sama dengan 1.0."
            )

        if not 0 <= self.min_score <= 1:
            raise ValueError(
                "min_score harus berada pada 0..1."
            )

        if not 0 <= self.relative_threshold <= 1:
            raise ValueError(
                "relative_threshold harus berada pada 0..1."
            )

    # --------------------------------------------------------
    # RETRIEVER LOADING
    # --------------------------------------------------------

    def _get_retriever(self):
        """
        Lazy import.

        This prevents importing IndoBERT until an actual
        retrieval operation is requested.
        """

        if self._retriever is not None:
            return self._retriever

        try:
            from app.knowledge.production_semantic_retriever import (
                ProductionSemanticRetriever,
            )
        except Exception as exc:
            raise RuntimeError(
                "ProductionSemanticRetriever tidak dapat diimport: "
                f"{exc}"
            ) from exc

        self._retriever = ProductionSemanticRetriever(
            db_path=self.db_path,
            semantic_weight=self.semantic_weight,
            lexical_weight=self.lexical_weight,
            min_score=self.min_score,
            relative_threshold=self.relative_threshold,
        )

        return self._retriever

    # --------------------------------------------------------
    # DATABASE
    # --------------------------------------------------------

    def database_exists(self) -> bool:
        return self.db_path.exists()

    def database_stats(self) -> dict[str, Any]:
        """
        Read-only database statistics.

        This function never modifies the database.
        """

        result = {
            "database": str(self.db_path),
            "exists": self.db_path.exists(),
            "documents": 0,
            "chunks": 0,
            "embeddings": 0,
            "source_registry": 0,
        }

        if not self.db_path.exists():
            return result

        connection = sqlite3.connect(
            str(self.db_path)
        )

        try:
            tables = {
                row[0]
                for row in connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table'
                    """
                ).fetchall()
            }

            for table_name, result_key in (
                ("documents", "documents"),
                ("chunks", "chunks"),
                ("chunk_embeddings", "embeddings"),
                ("source_registry", "source_registry"),
            ):
                if table_name not in tables:
                    continue

                result[result_key] = int(
                    connection.execute(
                        f"SELECT COUNT(*) FROM [{table_name}]"
                    ).fetchone()[0]
                )

        finally:
            connection.close()

        return result

    # --------------------------------------------------------
    # NORMALIZATION HELPERS
    # --------------------------------------------------------

    @staticmethod
    def _get_value(
        item: Any,
        *names: str,
        default: Any = None,
    ) -> Any:

        if isinstance(item, dict):
            for name in names:
                if name in item:
                    return item[name]
            return default

        for name in names:
            if hasattr(item, name):
                return getattr(item, name)

        return default

    @staticmethod
    def _safe_float(
        value: Any,
        default: float = 0.0,
    ) -> float:

        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_text(
        value: Any,
        default: str = "",
    ) -> str:

        if value is None:
            return default

        return str(value).strip()

    # --------------------------------------------------------
    # SOURCE POLICY
    # --------------------------------------------------------

    def _source_allowed(
        self,
        evidence: ProductionEvidence,
    ) -> bool:
        """Fail closed for strict authoritative-evidence filtering."""
        metadata = evidence.metadata
        if not isinstance(metadata, dict):
            return False

        hydrated_from = self._safe_text(
            metadata.get("authority_hydrated_from", "")
        ).lower()
        if hydrated_from != "documents":
            return False

        status = self._safe_text(
            evidence.source_status or metadata.get("source_status", "")
        ).lower()
        if status not in {"official", "verified"}:
            return False

        authority = self._safe_text(
            evidence.authority or metadata.get("authority", "")
        ).lower()
        if authority in {
            "", "unknown", "none", "null", "false",
            "test", "untrusted", "unverified"
        }:
            return False

        verified = metadata.get(
            "verified_raw",
            metadata.get("verified", False),
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

    # --------------------------------------------------------
    # METADATA FILTER
    # --------------------------------------------------------

    def _metadata_matches(
        self,
        evidence: ProductionEvidence,
        service: Optional[str] = None,
        content_type: Optional[str] = None,
        source_status: Optional[str] = None,
    ) -> bool:

        if service:
            if (
                self._safe_text(evidence.service).lower()
                != service.strip().lower()
            ):
                return False

        if content_type:
            if (
                self._safe_text(
                    evidence.content_type
                ).lower()
                != content_type.strip().lower()
            ):
                return False

        if source_status:
            if (
                self._safe_text(
                    evidence.source_status
                ).lower()
                != source_status.strip().lower()
            ):
                return False

        return True

    # --------------------------------------------------------
    # EVIDENCE NORMALIZATION
    # --------------------------------------------------------

    def _normalize_evidence(
        self,
        item: Any,
    ) -> Optional[ProductionEvidence]:

        chunk_id = self._safe_text(
            self._get_value(
                item,
                "chunk_id",
                "id",
                "chunk",
            )
        )

        text = self._safe_text(
            self._get_value(
                item,
                "text",
                "chunk_text",
                "content",
                "source",
            )
        )

        if not chunk_id or not text:
            return None

        score = self._safe_float(
            self._get_value(
                item,
                "score",
                "hybrid_score",
                "similarity",
                default=0.0,
            )
        )

        semantic_score = self._safe_float(
            self._get_value(
                item,
                "semantic_score",
                "semantic",
                default=0.0,
            )
        )

        lexical_score = self._safe_float(
            self._get_value(
                item,
                "lexical_score",
                "lexical",
                default=0.0,
            )
        )

        source_id = self._get_value(
            item,
            "source_id",
            "document_id",
        )

        source_name = self._get_value(
            item,
            "source_name",
            "document_name",
            "title",
        )

        source_status = self._get_value(
            item,
            "source_status",
            "status",
        )

        service = self._get_value(
            item,
            "service",
            "service_name",
        )

        content_type = self._get_value(
            item,
            "content_type",
            "category",
        )

        authority = self._get_value(
            item,
            "authority",
        )

        source_url = self._get_value(
            item,
            "source_url",
            "url",
        )

        score_explanation = self._safe_text(
            self._get_value(
                item,
                "score_explanation",
                "explanation",
            )
        )

        metadata = self._get_value(
            item,
            "metadata",
            default={},
        )

        if not isinstance(metadata, dict):
            metadata = {
                "raw_metadata": str(metadata)
            }

        return ProductionEvidence(
            chunk_id=chunk_id,
            text=text,
            score=score,
            semantic_score=semantic_score,
            lexical_score=lexical_score,
            source_id=(
                str(source_id)
                if source_id is not None
                else None
            ),
            source_name=(
                str(source_name)
                if source_name is not None
                else None
            ),
            source_status=(
                str(source_status)
                if source_status is not None
                else None
            ),
            service=(
                str(service)
                if service is not None
                else None
            ),
            content_type=(
                str(content_type)
                if content_type is not None
                else None
            ),
            authority=(
                str(authority)
                if authority is not None
                else None
            ),
            source_url=(
                str(source_url)
                if source_url is not None
                else None
            ),
            score_explanation=score_explanation,
            metadata=metadata,
        )

    # --------------------------------------------------------
    # RAW RETRIEVAL
    # --------------------------------------------------------

    def _retrieve_raw(
        self,
        query: str,
        top_k: int, require_authoritative_source: bool = False) -> Iterable[Any]:

        retriever = self._get_retriever()

        if hasattr(retriever, "search"):

            search_kwargs = {"query": query, "top_k": top_k}

            if require_authoritative_source:

                search_kwargs["require_authoritative_source"] = True

            result = retriever.search(**search_kwargs)

        elif hasattr(retriever, "retrieve"):

            if require_authoritative_source:

                raise RuntimeError(

                    "Validasi sumber resmi memerlukan retriever.search() "

                    "yang mendukung require_authoritative_source."

                )

            result = retriever.retrieve(
                query=query,
                top_k=top_k,
            )

        else:
            raise RuntimeError(
                "ProductionSemanticRetriever tidak memiliki "
                "method search() atau retrieve()."
            )

        if result is None:
            return []

        if isinstance(result, dict):

            for key in (
                "results",
                "evidence",
                "items",
                "data",
            ):
                if key in result:
                    value = result[key]

                    if isinstance(value, list):
                        return value

                    if value is None:
                        return []

            return []

        if isinstance(result, (list, tuple)):
            return result

        return [result]

    # --------------------------------------------------------
    # MAIN RETRIEVAL
    # --------------------------------------------------------

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        service: Optional[str] = None,
        content_type: Optional[str] = None,
        source_status: Optional[str] = None,
        require_authoritative_source: bool = False,
    ) -> ProductionEvidencePack:

        query = self._safe_text(query)

        if not query:
            return ProductionEvidencePack(
                query="",
                evidence=[],
                count=0,
                semantic_weight=self.semantic_weight,
                lexical_weight=self.lexical_weight,
                min_score=self.min_score,
                relative_threshold=self.relative_threshold,
                filters={
                    "service": service,
                    "content_type": content_type,
                    "source_status": source_status,
                },
                grounded_candidate=False,
                reason="empty_query",
            )

        if top_k < 1:
            raise ValueError(
                "top_k harus >= 1."
            )

        raw_results = self._retrieve_raw(
            query=query,
            top_k=top_k,
            require_authoritative_source=require_authoritative_source,
        )

        normalized: list[ProductionEvidence] = []

        for item in raw_results:

            evidence = self._normalize_evidence(
                item
            )

            if evidence is None:
                continue

            if not self._metadata_matches(
                evidence,
                service=service,
                content_type=content_type,
                source_status=source_status,
            ):
                continue

            if require_authoritative_source:
                if not self._source_allowed(
                    evidence
                ):
                    continue

            normalized.append(evidence)

        normalized.sort(
            key=lambda item: item.score,
            reverse=True,
        )

        normalized = normalized[:top_k]

        if not normalized:

            if require_authoritative_source:
                reason = (
                    "no_authoritative_evidence"
                )
            else:
                reason = "no_relevant_evidence"

            return ProductionEvidencePack(
                query=query,
                evidence=[],
                count=0,
                semantic_weight=self.semantic_weight,
                lexical_weight=self.lexical_weight,
                min_score=self.min_score,
                relative_threshold=self.relative_threshold,
                filters={
                    "service": service,
                    "content_type": content_type,
                    "source_status": source_status,
                    "require_authoritative_source":
                        require_authoritative_source,
                },
                grounded_candidate=False,
                reason=reason,
            )

        return ProductionEvidencePack(
            query=query,
            evidence=normalized,
            count=len(normalized),
            semantic_weight=self.semantic_weight,
            lexical_weight=self.lexical_weight,
            min_score=self.min_score,
            relative_threshold=self.relative_threshold,
            filters={
                "service": service,
                "content_type": content_type,
                "source_status": source_status,
                "require_authoritative_source":
                    require_authoritative_source,
            },
            grounded_candidate=True,
            reason="relevant_evidence_found",
            metadata={
                "retrieval_source":
                    "production_hybrid",
                "top_score":
                    normalized[0].score,
                "evidence_count":
                    len(normalized),
            },
        )

    # --------------------------------------------------------
    # INTENT-AWARE RETRIEVAL
    # --------------------------------------------------------

    def retrieve_for_intent(
        self,
        query: str,
        intent_name: Optional[str] = None,
        service: Optional[str] = None,
        top_k: int = 5,
        require_authoritative_source: bool = False,
    ) -> ProductionEvidencePack:

        content_type = None

        intent_map = {
            "ask_document_requirements":
                "requirements",

            "ask_processing_time":
                "processing_time",

            "ask_service_fee":
                "fee",

            "ask_document_status":
                "status",

            "ask_procedure":
                "procedure",

            "ask_general_info":
                None,
        }

        if intent_name:
            content_type = intent_map.get(
                intent_name
            )

        return self.retrieve(
            query=query,
            top_k=top_k,
            service=service,
            content_type=content_type,
            require_authoritative_source=(
                require_authoritative_source
            ),
        )

    # --------------------------------------------------------
    # GROUNDING TEXT
    # --------------------------------------------------------

    def build_grounding_context(
        self,
        pack: ProductionEvidencePack,
        max_chars_per_evidence: int = 4000,
    ) -> str:

        if not pack.evidence:
            return ""

        blocks = []

        for index, evidence in enumerate(
            pack.evidence,
            start=1,
        ):

            text = evidence.text.strip()

            if len(text) > max_chars_per_evidence:
                text = (
                    text[:max_chars_per_evidence]
                    + "..."
                )

            blocks.append(
                "\n".join(
                    [
                        f"[EVIDENCE {index}]",
                        f"chunk_id: {evidence.chunk_id}",
                        f"score: {evidence.score:.4f}",
                        (
                            "semantic_score: "
                            f"{evidence.semantic_score:.4f}"
                        ),
                        (
                            "lexical_score: "
                            f"{evidence.lexical_score:.4f}"
                        ),
                        (
                            "service: "
                            f"{evidence.service or '-'}"
                        ),
                        (
                            "content_type: "
                            f"{evidence.content_type or '-'}"
                        ),
                        (
                            "source_status: "
                            f"{evidence.source_status or '-'}"
                        ),
                        (
                            "authority: "
                            f"{evidence.authority or '-'}"
                        ),
                        (
                            "source_url: "
                            f"{evidence.source_url or '-'}"
                        ),
                        "text:",
                        text,
                    ]
                )
            )

        return "\n\n".join(blocks)

    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    def retrieve_json(
        self,
        query: str,
        **kwargs: Any,
    ) -> str:

        pack = self.retrieve(
            query=query,
            **kwargs,
        )

        return json.dumps(
            pack.to_dict(),
            ensure_ascii=False,
            indent=2,
        )


# ============================================================
# SELF TEST
# ============================================================


def run_self_test() -> int:

    print("=" * 72)
    print("PHASE 19.3 PRODUCTION HYBRID RAG SELF TEST")
    print("=" * 72)

    bridge = ProductionHybridRAG()

    # --------------------------------------------------------
    # TEST 1 - DATABASE
    # --------------------------------------------------------

    print("\n[1/8] Database")

    stats = bridge.database_stats()

    print(
        json.dumps(
            stats,
            ensure_ascii=False,
            indent=2,
        )
    )

    if not stats["exists"]:
        print("[FAIL] Production database tidak ditemukan.")
        return 1

    print("[PASS] Database")

    # --------------------------------------------------------
    # TEST 2 - CONFIG
    # --------------------------------------------------------

    print("\n[2/8] Configuration")

    assert (
        abs(
            bridge.semantic_weight
            + bridge.lexical_weight
            - 1.0
        )
        < 0.000001
    )

    print(
        "semantic_weight =",
        bridge.semantic_weight,
    )

    print(
        "lexical_weight  =",
        bridge.lexical_weight,
    )

    print(
        "min_score       =",
        bridge.min_score,
    )

    print(
        "relative_threshold =",
        bridge.relative_threshold,
    )

    print("[PASS] Configuration")

    # --------------------------------------------------------
    # TEST 3 - RETRIEVER IMPORT
    # --------------------------------------------------------

    print("\n[3/8] Retriever import")

    try:
        retriever = bridge._get_retriever()
    except Exception as exc:
        print(
            "[FAIL] Retriever tidak dapat dibuat:",
            exc,
        )
        return 1

    if retriever is None:
        print("[FAIL] Retriever None.")
        return 1

    print(
        "[PASS] ProductionSemanticRetriever"
    )

    # --------------------------------------------------------
    # TEST 4 - RETRIEVAL
    # --------------------------------------------------------

    print("\n[4/8] Retrieval")

    try:
        pack = bridge.retrieve(
            "persyaratan KTP-el",
            top_k=5,
        )
    except Exception as exc:
        print(
            "[FAIL] Retrieval error:",
            exc,
        )
        return 1

    print(
        "Evidence count:",
        pack.count,
    )

    if pack.count == 0:
        print(
            "[WARNING] Tidak ada evidence. "
            "Self-test tetap melanjutkan karena "
            "database dapat berisi knowledge kosong."
        )
    else:
        print(
            "[PASS] Retrieval menghasilkan evidence"
        )

    # --------------------------------------------------------
    # TEST 5 - EVIDENCE CONTRACT
    # --------------------------------------------------------

    print("\n[5/8] Evidence contract")

    if pack.evidence:

        first = pack.evidence[0]

        required_fields = (
            "chunk_id",
            "text",
            "score",
            "semantic_score",
            "lexical_score",
            "metadata",
        )

        for field_name in required_fields:

            if not hasattr(
                first,
                field_name,
            ):
                print(
                    "[FAIL] Missing field:",
                    field_name,
                )
                return 1

        print(
            "[PASS] Evidence contract"
        )

    else:

        print(
            "[PASS] Evidence contract "
            "(empty result is valid)"
        )

    # --------------------------------------------------------
    # TEST 6 - EMPTY QUERY
    # --------------------------------------------------------

    print("\n[6/8] Empty query safety")

    empty_pack = bridge.retrieve(
        "",
        top_k=5,
    )

    if (
        empty_pack.count != 0
        or empty_pack.reason != "empty_query"
    ):
        print(
            "[FAIL] Empty query safety"
        )
        return 1

    print(
        "[PASS] Empty query safety"
    )

    # --------------------------------------------------------
    # TEST 7 - GROUNDING CONTEXT
    # --------------------------------------------------------

    print("\n[7/8] Grounding context")

    context = bridge.build_grounding_context(
        pack
    )

    if pack.evidence and not context:
        print(
            "[FAIL] Evidence ada tetapi "
            "grounding context kosong."
        )
        return 1

    print(
        "[PASS] Grounding context"
    )

    # --------------------------------------------------------
    # TEST 8 - JSON CONTRACT
    # --------------------------------------------------------

    print("\n[8/8] JSON contract")

    try:
        json_payload = json.loads(
            bridge.retrieve_json(
                "persyaratan KTP-el",
                top_k=5,
            )
        )
    except Exception as exc:
        print(
            "[FAIL] JSON contract:",
            exc,
        )
        return 1

    required_json_keys = (
        "query",
        "count",
        "retrieval_source",
        "semantic_weight",
        "lexical_weight",
        "evidence",
        "reason",
    )

    for key in required_json_keys:

        if key not in json_payload:
            print(
                "[FAIL] Missing JSON key:",
                key,
            )
            return 1

    print(
        "[PASS] JSON contract"
    )

    print("")
    print("=" * 72)
    print(
        "PHASE 19.3 PRODUCTION HYBRID RAG SELFTEST: PASS"
    )
    print("=" * 72)

    return 0


# ============================================================
# CLI
# ============================================================


def build_parser() -> argparse.ArgumentParser:

    parser = argparse.ArgumentParser(
        description=(
            "Nusantara AI Production Hybrid RAG "
            "Bridge - Phase 19.3"
        )
    )

    subparsers = parser.add_subparsers(
        dest="command"
    )

    subparsers.add_parser(
        "self-test",
        help="Run Phase 19.3 self-test",
    )

    subparsers.add_parser(
        "stats",
        help="Show production KB statistics",
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Retrieve production evidence",
    )

    search_parser.add_argument(
        "query",
        help="User query",
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
        "--require-authoritative-source",
        action="store_true",
    )

    context_parser = subparsers.add_parser(
        "context",
        help="Build grounding context",
    )

    context_parser.add_argument(
        "query",
        help="User query",
    )

    context_parser.add_argument(
        "--top-k",
        type=int,
        default=5,
    )

    context_parser.add_argument(
        "--service",
        default=None,
    )

    context_parser.add_argument(
        "--content-type",
        default=None,
    )

    context_parser.add_argument(
        "--require-authoritative-source",
        action="store_true",
    )

    return parser


def main() -> int:

    parser = build_parser()

    args = parser.parse_args()

    if args.command == "self-test":

        return run_self_test()

    bridge = ProductionHybridRAG()

    if args.command == "stats":

        print(
            json.dumps(
                bridge.database_stats(),
                ensure_ascii=False,
                indent=2,
            )
        )

        return 0

    if args.command == "search":

        pack = bridge.retrieve(
            query=args.query,
            top_k=args.top_k,
            service=args.service,
            content_type=args.content_type,
            source_status=args.source_status,
            require_authoritative_source=(
                args.require_authoritative_source
            ),
        )

        print(
            json.dumps(
                pack.to_dict(),
                ensure_ascii=False,
                indent=2,
            )
        )

        return 0

    if args.command == "context":

        pack = bridge.retrieve(
            query=args.query,
            top_k=args.top_k,
            service=args.service,
            content_type=args.content_type,
            require_authoritative_source=(
                args.require_authoritative_source
            ),
        )

        print(
            bridge.build_grounding_context(
                pack
            )
        )

        return 0

    parser.print_help()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
