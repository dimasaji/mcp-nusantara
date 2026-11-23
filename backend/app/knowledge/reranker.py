"""
Reranker - Reranking evidence berdasarkan relevance.
Mendukung multiple reranker backend (cross-encoder, LLM-based, dll).
"""
from typing import List, Optional
from app.knowledge.schemas import Evidence, EvidencePack


class Reranker:
    """
    Base reranker - urutkan ulang evidence berdasarkan relevance.
    """

    def __init__(self, model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self._model = model
        self._dimension = 384

    def rerank(
        self,
        query: str,
        evidence: List[Evidence],
        top_k: Optional[int] = None,
    ) -> List[Evidence]:
        """
        Rerank evidence berdasarkan relevance dengan query.
        Default: simple TF-IDF-like scoring.
        """
        raise NotImplementedError("Subclass harus implement rerank()")

    def _compute_score(self, query: str, chunk: str) -> float:
        """Compute relevance score antara query dan chunk."""
        raise NotImplementedError


class SimpleReranker(Reranker):
    """
    Simple reranker menggunakan keyword overlap (TF-IDF-like).
    Cocok untuk fallback jika model reranker tidak tersedia.
    """

    def __init__(self):
        super().__init__()

    def rerank(
        self,
        query: str,
        evidence: List[Evidence],
        top_k: Optional[int] = None,
    ) -> List[Evidence]:
        """
        Rerank menggunakan keyword overlap sederhana.
        """
        query_words = set(query.lower().split())
        scored = []

        for ev in evidence:
            chunk_words = set(ev.chunk.lower().split())
            overlap = len(query_words & chunk_words)
            total_query_words = max(len(query_words), 1)
            score = overlap / total_query_words

            # Bonus: positional score (chunk yang lebih panjang mungkin lebih relevan)
            # Tidak terlalu kompleks

            ev.score = min(score, 1.0)
            scored.append(ev)

        scored.sort(key=lambda x: x.score, reverse=True)
        top_k = top_k or len(scored)
        return scored[:top_k]

    def _compute_score(self, query: str, chunk: str) -> float:
        """Compute score untuk query-chunk pair."""
        query_words = set(query.lower().split())
        chunk_words = set(chunk.lower().split())
        overlap = len(query_words & chunk_words)
        return overlap / max(len(query_words), 1)


class CrossEncoderReranker(Reranker):
    """
    Reranker menggunakan Cross Encoder model (Hugging Face).
    Lebih akurat daripada simple keyword overlap.
    Membutuhkan: pip install sentence-transformers
    """

    def __init__(
        self,
        model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
    ):
        super().__init__(model)
        self._cross_encoder = None
        self._load_model(model)

    def _load_model(self, model: str) -> None:
        """Load cross encoder model."""
        try:
            from sentence_transformers import CrossEncoder
            self._cross_encoder = CrossEncoder(model)
        except ImportError:
            self._cross_encoder = None
            print(f"Warning: CrossEncoder not available. "
                  f"Install with: pip install sentence-transformers")

    def rerank(
        self,
        query: str,
        evidence: List[Evidence],
        top_k: Optional[int] = None,
    ) -> List[Evidence]:
        """
        Rerank menggunakan cross encoder.
        """
        if self._cross_encoder is None:
            # Fallback ke simple reranker
            simple = SimpleReranker()
            return simple.rerank(query, evidence, top_k)

        pairs = [[query, ev.chunk] for ev in evidence]
        scores = self._cross_encoder.predict(pairs)

        for ev, score in zip(evidence, scores):
            ev.score = float(score)

        evidence.sort(key=lambda x: x.score, reverse=True)

        if top_k:
            return evidence[:top_k]
        return evidence


class LLMReranker(Reranker):
    """
    Reranker menggunakan LLM untuk menilai relevance.
    Menggunakan LLM call untuk setiap evidence pair.
    """

    def __init__(
        self,
        llm_client=None,
        prompt_template: Optional[str] = None,
    ):
        super().__init__()
        self._llm_client = llm_client
        self._prompt_template = prompt_template or self._default_prompt()

    def _default_prompt(self) -> str:
        """Default prompt untuk LLM reranking."""
        return """Anda adalah sistem penilaian relevansi. 
        Bandingkan query berikut dengan chunk teks dan beri score dari 0-100.
        Query: {query}
        Chunk: {chunk}
        Score (0-100):"""

    def rerank(
        self,
        query: str,
        evidence: List[Evidence],
        top_k: Optional[int] = None,
    ) -> List[Evidence]:
        """
        Rerank menggunakan LLM.
        """
        if self._llm_client is None:
            # Fallback ke simple reranker
            simple = SimpleReranker()
            return simple.rerank(query, evidence, top_k)

        scored = []
        for ev in evidence:
            prompt = self._prompt_template.format(query=query, chunk=ev.chunk)
            response = self._llm_client.generate(prompt)
            try:
                score = float(response.strip())
            except ValueError:
                score = 50.0  # Default jika gagal parse
            ev.score = score / 100.0
            scored.append(ev)

        scored.sort(key=lambda x: x.score, reverse=True)

        if top_k:
            return scored[:top_k]
        return scored


def create_reranker(
    model: str = "simple",
    llm_client=None,
) -> Reranker:
    """Factory untuk membuat reranker."""
    if model == "simple":
        return SimpleReranker()
    elif model == "cross-encoder":
        return CrossEncoderReranker()
    elif model == "llm":
        return LLMReranker(llm_client=llm_client)
    else:
        return SimpleReranker()
