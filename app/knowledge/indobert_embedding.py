from __future__ import annotations

from typing import List

from app.language.semantic.indobert_client import IndoBERTClient
from app.core.nusantara_config import ConfigurationError, NusantaraConfig


class IndoBERTEmbeddingAdapter:
    """
    Adapter embedding untuk RAG.

    RAG hanya membutuhkan:
        text -> List[float]

    IndoBERTClient menangani worker persistent
    pada environment nusantara-models.
    """

    @staticmethod
    def validate_configuration(config: NusantaraConfig) -> None:
        if (config.embedding.provider != "indobert" or
                config.embedding.model != "indobenchmark/indobert-base-p1" or
                config.embedding.dimension != 768):
            raise ConfigurationError("EMBEDDING_PROFILE_UNSUPPORTED")

    def __init__(self, *, nusantara_config: NusantaraConfig | None = None) -> None:
        if nusantara_config is None:
            self.client = IndoBERTClient()
        else:
            # The existing worker/model/index remains fixed. Configuration must
            # not pretend a new model/dimension is implemented by this adapter.
            self.validate_configuration(nusantara_config)
            self.client = IndoBERTClient(
                python_executable=str(nusantara_config.paths.worker_python),
                worker_path=str(nusantara_config.paths.worker),
                response_timeout_s=nusantara_config.embedding.timeout_s,
            )

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
