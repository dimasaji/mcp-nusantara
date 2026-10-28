from __future__ import annotations

from typing import List

from app.language.semantic.indobert_client import IndoBERTClient


class IndoBERTEmbeddingAdapter:
    """
    Adapter embedding untuk RAG.

    RAG hanya membutuhkan:
        text -> List[float]

    IndoBERTClient menangani worker persistent
    pada environment nusantara-models.
    """

    def __init__(self) -> None:
        self.client = IndoBERTClient()

    def __call__(self, text: str) -> List[float]:
        result = self.client.encode(text)

        if not result.get("ok"):
            raise RuntimeError(
                "IndoBERT embedding gagal: "
                + str(result.get("error", "unknown error"))
            )

        embedding = result.get("embedding")

        if not isinstance(embedding, list):
            raise RuntimeError(
                "Response IndoBERT tidak memiliki embedding yang valid."
            )

        if len(embedding) != 768:
            raise RuntimeError(
                f"Dimensi embedding IndoBERT tidak sesuai: "
                f"{len(embedding)} != 768"
            )

        return [float(value) for value in embedding]

    def health(self) -> dict:
        return self.client.health()

    def stop(self) -> None:
        self.client.stop()
