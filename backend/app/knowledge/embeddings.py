"""
Embeddings - Generate embedding dari teks.
Provider-independent: mendukung multiple embedding model.
"""
from typing import List, Optional
import numpy as np


class EmbeddingProvider:
    """
    Abstraksi provider embedding.
    Mendukung multiple backend: sentence-transformers, OpenAI, dll.
    """

    def __init__(self, model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self._model = model
        self._dimension = self._detect_dimension(model)

    def _detect_dimension(self, model: str) -> int:
        """Detect dimensi embedding berdasarkan model."""
        known_dims = {
            "sentence-transformers/all-MiniLM-L6-v2": 384,
            "sentence-transformers/all-mpnet-base-v2": 768,
            "sentence-transformers/all-T5-base": 768,
            "BAAI/bge-small-en-v1.5": 384,
            "BAAI/bge-base-en-v1.5": 768,
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }
        return known_dims.get(model, 384)

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed(self, text: str) -> List[float]:
        """
        Generate embedding dasar yang deterministik.

        Base provider menyediakan fallback agar komponen/evaluator yang
        membutuhkan EmbeddingProvider langsung tetap dapat berjalan.
        Provider nyata seperti SentenceTransformerEmbedder dan
        OpenAIEmbeddingProvider tetap melakukan override method ini.
        """
        import hashlib

        text = "" if text is None else str(text)
        result: List[float] = []

        for i in range(self._dimension):
            digest = hashlib.sha256(f"{text}|{i}".encode("utf-8")).digest()
            value = int.from_bytes(digest[:4], "big") / 4294967295.0
            result.append(value)

        return result

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding batch."""
        return [self.embed(text) for text in texts]

    def embed_documents(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Embed multiple documents dengan chunking."""
        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            results.extend(self.embed_batch(batch))
        return results


class SentenceTransformerEmbedder(EmbeddingProvider):
    """
    Embedder menggunakan Sentence Transformers (Hugging Face).
    Membutuhkan: pip install sentence-transformers
    """

    def __init__(self, model: str = "sentence-transformers/all-MiniLM-L6-v2"):
        super().__init__(model)
        self._client = None
        self._load_model(model)

    def _load_model(self, model: str) -> None:
        """Load model sentence transformers."""
        try:
            from sentence_transformers import SentenceTransformer
            self._client = SentenceTransformer(model)
        except ImportError:
            self._client = None
            print(f"Warning: sentence-transformers not installed. "
                  f"Install with: pip install sentence-transformers")

    def embed(self, text: str) -> List[float]:
        """Generate embedding menggunakan sentence transformers."""
        if self._client is None:
            # Fallback: hash-based embedding
            return self._fallback_embedding(text)

        embedding = self._client.encode(text)
        return embedding.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed batch menggunakan sentence transformers."""
        if self._client is None:
            return [self._fallback_embedding(text) for text in texts]

        embeddings = self._client.encode(texts)
        return embeddings.tolist()

    def _fallback_embedding(self, text: str) -> List[float]:
        """Fallback embedding menggunakan hash."""
        import hashlib
        hash_bytes = hashlib.md5(text.encode()).digest()
        dim = self._dimension
        result = []
        for i in range(dim):
            if i < len(hash_bytes):
                result.append(float(hash_bytes[i]) / 255.0)
            else:
                result.append(0.0)
        return result


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """
    Embedder menggunakan OpenAI API.
    Membutuhkan API key.
    """

    def __init__(
        self,
        model: str = "text-embedding-ada-002",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        super().__init__(model)
        self._api_key = api_key
        self._base_url = base_url

    def embed(self, text: str) -> List[float]:
        """Embed menggunakan OpenAI API."""
        import openai

        client = openai.OpenAI(
            api_key=self._api_key or "",
            base_url=self._base_url,
        )

        response = client.embeddings.create(
            input=text,
            model=self._model,
        )

        return response.data[0].embedding


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Mock embedding provider untuk testing.
    Menghasilkan embedding acak yang deterministik berdasarkan teks.
    """

    def __init__(self, dimension: int = 384):
        # Gunakan model generic tapi kita set dimension manual
        super().__init__("mock")
        self._dimension = dimension

    def embed(self, text: str) -> List[float]:
        """Generate pseudo-embedding deterministik."""
        import hashlib
        import struct

        hash_bytes = hashlib.md5(text.encode()).digest()
        result = []
        for i in range(self._dimension):
            if i < len(hash_bytes):
                val = float(hash_bytes[i]) / 255.0
            else:
                # Generate dari hash yang lebih panjang
                combined = hashlib.md5(f"{text}_{i}".encode()).digest()
                val = float(combined[i % len(combined)]) / 255.0
            result.append(val)
        return result


class EmbeddingService:
    """
    Service yang menggabungkan multiple embedding provider.
    Provider-independent: bisa swap provider tanpa mengubah kode.
    """

    def __init__(
        self,
        provider: Optional[EmbeddingProvider] = None,
        config: Optional[dict] = None,
    ):
        self._provider = provider or MockEmbeddingProvider()
        self._config = config or {}

    def embed(self, text: str) -> List[float]:
        """Embed teks."""
        return self._provider.embed(text)

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed batch teks."""
        return self._provider.embed_batch(texts)

    def set_provider(self, provider: EmbeddingProvider) -> None:
        """Ganti provider embedding."""
        self._provider = provider

    def get_provider(self) -> EmbeddingProvider:
        """Get current provider."""
        return self._provider


def create_embedder(
    model: str = "sentence-transformers/all-MiniLM-L6-v2",
    api_key: Optional[str] = None,
) -> EmbeddingProvider:
    """Factory untuk membuat embedder berdasarkan model."""
    if "openai" in model or "text-embedding" in model:
        return OpenAIEmbeddingProvider(model=model, api_key=api_key)
    else:
        return SentenceTransformerEmbedder(model=model)
