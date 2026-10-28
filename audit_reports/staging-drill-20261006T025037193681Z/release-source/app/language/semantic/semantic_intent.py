from __future__ import annotations

from typing import Any
import math
import threading

from app.language.semantic.indobert_client import IndoBERTClient
from app.language.semantic.intent_prototypes import INTENT_PROTOTYPES


class SemanticIntentEngine:
    """
    Semantic Intent Engine Nusantara AI.

    Pipeline:

        text
          ↓
        IndoBERTClient
          ↓
        768D embedding
          ↓
        cosine similarity
          ↓
        intent prototypes
          ↓
        semantic intent

    IndoBERT bersifat persistent dan lazy-loaded.
    """

    VERSION = "1.3.1-indobert"

    MODEL = "indobenchmark/indobert-base-p1"
    EMBEDDING_DIMENSION = 768

    def __init__(
        self,
        client: IndoBERTClient | None = None,
    ) -> None:

        self.client = client or IndoBERTClient()

        self.prototype_embeddings: dict[
            str,
            list[list[float]],
        ] = {}

        self.ready = False
        self.building = False
        self.build_error: str | None = None

        self._lock = threading.RLock()

    # ==========================================================
    # COSINE SIMILARITY
    # ==========================================================

    @staticmethod
    def cosine_similarity(
        vector_a: list[float],
        vector_b: list[float],
    ) -> float:

        if not vector_a or not vector_b:
            return 0.0

        if len(vector_a) != len(vector_b):
            return 0.0

        dot_product = 0.0
        norm_a = 0.0
        norm_b = 0.0

        for a, b in zip(vector_a, vector_b):
            try:
                a = float(a)
                b = float(b)
            except (TypeError, ValueError):
                return 0.0

            dot_product += a * b
            norm_a += a * a
            norm_b += b * b

        denominator = math.sqrt(norm_a) * math.sqrt(norm_b)

        if denominator <= 0.0:
            return 0.0

        similarity = dot_product / denominator

        if not math.isfinite(similarity):
            return 0.0

        return max(-1.0, min(1.0, similarity))

    # ==========================================================
    # VALIDATE EMBEDDING
    # ==========================================================

    @classmethod
    def _validate_embedding(
        cls,
        embedding: Any,
    ) -> bool:

        if not isinstance(embedding, list):
            return False

        if len(embedding) != cls.EMBEDDING_DIMENSION:
            return False

        for value in embedding:
            if not isinstance(value, (int, float)):
                return False

            if not math.isfinite(float(value)):
                return False

        return True

    # ==========================================================
    # BUILD PROTOTYPE INDEX
    # ==========================================================

    def build_index(self, force: bool = False) -> None:

        with self._lock:

            if self.ready and not force:
                return

            if self.building:
                return

            self.building = True
            self.build_error = None

            try:

                new_index: dict[
                    str,
                    list[list[float]],
                ] = {}

                for intent_name, examples in INTENT_PROTOTYPES.items():

                    if not isinstance(examples, (list, tuple)):
                        continue

                    embeddings: list[list[float]] = []

                    for example in examples:

                        example = str(example).strip()

                        if not example:
                            continue

                        result = self.client.encode(example)

                        if not result.get("ok"):
                            raise RuntimeError(
                                "Gagal membuat embedding prototype "
                                f"'{intent_name}': "
                                f"{result.get('error', 'unknown error')}"
                            )

                        embedding = result.get("embedding")

                        if not self._validate_embedding(
                            embedding
                        ):
                            raise RuntimeError(
                                "Embedding prototype tidak valid "
                                f"untuk intent '{intent_name}'. "
                                f"Diharapkan {self.EMBEDDING_DIMENSION}D."
                            )

                        embeddings.append(
                            [float(x) for x in embedding]
                        )

                    if embeddings:
                        new_index[intent_name] = embeddings

                if not new_index:
                    raise RuntimeError(
                        "Tidak ada prototype embedding yang berhasil dibuat."
                    )

                self.prototype_embeddings = new_index
                self.ready = True

            except Exception as exc:

                self.ready = False
                self.prototype_embeddings.clear()
                self.build_error = str(exc)

                raise

            finally:
                self.building = False

    # ==========================================================
    # CLASSIFY
    # ==========================================================

    def classify(
        self,
        text: str,
        top_k: int = 3,
    ) -> dict[str, Any]:

        text = str(text).strip()

        if not text:
            return {
                "ok": False,
                "engine": "indobert-semantic",
                "version": self.VERSION,
                "error": "text wajib diisi",
            }

        if top_k < 1:
            top_k = 1

        # ------------------------------------------------------
        # Ensure prototype index
        # ------------------------------------------------------

        try:

            if not self.ready:
                self.build_index()

        except Exception as exc:

            return {
                "ok": False,
                "engine": "indobert-semantic",
                "version": self.VERSION,
                "model": self.MODEL,
                "error": (
                    "IndoBERT semantic index gagal dibangun: "
                    f"{exc}"
                ),
            }

        # ------------------------------------------------------
        # Encode user query
        # ------------------------------------------------------

        try:

            result = self.client.encode(text)

        except Exception as exc:

            return {
                "ok": False,
                "engine": "indobert-semantic",
                "version": self.VERSION,
                "model": self.MODEL,
                "error": (
                    "IndoBERT client exception: "
                    f"{exc}"
                ),
            }

        if not result.get("ok"):

            return {
                "ok": False,
                "engine": "indobert-semantic",
                "version": self.VERSION,
                "model": self.MODEL,
                "error": result.get(
                    "error",
                    "Gagal melakukan embedding.",
                ),
            }

        query_embedding = result.get("embedding")

        if not self._validate_embedding(query_embedding):

            return {
                "ok": False,
                "engine": "indobert-semantic",
                "version": self.VERSION,
                "model": self.MODEL,
                "error": (
                    "Embedding input tidak valid. "
                    f"Diharapkan {self.EMBEDDING_DIMENSION}D."
                ),
            }

        # ------------------------------------------------------
        # Similarity
        # ------------------------------------------------------

        candidates: list[dict[str, Any]] = []

        for intent_name, embeddings in (
            self.prototype_embeddings.items()
        ):

            if not embeddings:
                continue

            similarities = [
                self.cosine_similarity(
                    query_embedding,
                    embedding,
                )
                for embedding in embeddings
            ]

            if not similarities:
                continue

            best_similarity = max(similarities)

            average_similarity = (
                sum(similarities)
                / len(similarities)
            )

            candidates.append(
                {
                    "intent": intent_name,
                    "similarity": round(
                        best_similarity,
                        6,
                    ),
                    "average_similarity": round(
                        average_similarity,
                        6,
                    ),
                }
            )

        candidates.sort(
            key=lambda item: item["similarity"],
            reverse=True,
        )

        top_candidates = candidates[:top_k]

        if not top_candidates:

            return {
                "ok": False,
                "engine": "indobert-semantic",
                "version": self.VERSION,
                "model": self.MODEL,
                "error": "Tidak ada prototype intent.",
            }

        best = top_candidates[0]

        confidence = float(
            best.get("similarity", 0.0)
        )

        return {
            "ok": True,
            "engine": "indobert-semantic",
            "version": self.VERSION,
            "model": self.MODEL,
            "text": text,
            "intent": best["intent"],
            "confidence": round(
                confidence,
                6,
            ),
            "top_candidates": top_candidates,
            "prototype_count": len(
                self.prototype_embeddings
            ),
            "prototype_examples": sum(
                len(values)
                for values in self.prototype_embeddings.values()
            ),
        }

    # ==========================================================
    # HEALTH
    # ==========================================================

    def health(self) -> dict[str, Any]:

        try:
            worker = self.client.health()
        except Exception as exc:
            worker = {
                "ok": False,
                "error": str(exc),
            }

        return {
            "ok": bool(
                self.ready
                and worker.get("ok", False)
            ),
            "engine": "indobert-semantic",
            "version": self.VERSION,
            "model": self.MODEL,
            "ready": self.ready,
            "building": self.building,
            "intent_count": len(
                self.prototype_embeddings
            ),
            "prototype_examples": sum(
                len(values)
                for values in self.prototype_embeddings.values()
            ),
            "embedding_dimension": self.EMBEDDING_DIMENSION,
            "build_error": self.build_error,
            "worker": worker,
        }

    # ==========================================================
    # STOP
    # ==========================================================

    def stop(self) -> None:

        try:
            self.client.stop()
        except Exception:
            pass

        with self._lock:
            self.ready = False
            self.building = False


__all__ = [
    "SemanticIntentEngine",
]
