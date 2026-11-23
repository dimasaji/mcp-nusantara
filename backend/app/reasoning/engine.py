from __future__ import annotations

from typing import Any

from app.reasoning.schemas import Fact, Inference, ReasoningResult


class ReasoningEngine:
    VERSION = "8.2.0-evidence-compatible"
    MIN_EVIDENCE_SCORE = 0.50
    MIN_GROUNDED_CONFIDENCE = 0.50

    def _text(self, item: Any) -> str:
        if item is None:
            return ""

        if isinstance(item, str):
            return item.strip()

        if isinstance(item, dict):
            keys = (
                "text",
                "content",
                "snippet",
                "source_text",
                "chunk_text",
                "document_text",
                "evidence",
                "page_content",
                "body",
            )

            for key in keys:
                value = item.get(key)
                if value is not None and str(value).strip():
                    return str(value).strip()

        keys = (
            "text",
            "content",
            "snippet",
            "source_text",
            "chunk_text",
            "document_text",
            "evidence",
            "page_content",
            "body",
        )

        for key in keys:
            try:
                value = getattr(item, key, None)
            except Exception:
                value = None

            if value is not None and str(value).strip():
                return str(value).strip()

        return str(item).strip()

    def _score(self, item: Any) -> float:
        keys = (
            "score",
            "relevance_score",
            "similarity",
            "confidence",
            "relevance",
            "retrieval_score",
            "semantic_score",
            "final_score",
        )

        try:
            if isinstance(item, dict):
                for key in keys:
                    value = item.get(key)
                    if value is not None:
                        return max(
                            0.0,
                            min(1.0, float(value)),
                        )

            for key in keys:
                value = getattr(item, key, None)
                if value is not None:
                    return max(
                        0.0,
                        min(1.0, float(value)),
                    )

        except (TypeError, ValueError):
            return 0.0

        return 0.0

    def _evidence_id(self, item: Any, index: int) -> str:
        if isinstance(item, dict):
            for key in (
                "id",
                "evidence_id",
                "chunk_id",
                "document_id",
                "source_id",
            ):
                value = item.get(key)
                if value is not None and str(value).strip():
                    return str(value).strip()

        for key in (
            "id",
            "evidence_id",
            "chunk_id",
            "document_id",
            "source_id",
        ):
            value = getattr(item, key, None)
            if value is not None and str(value).strip():
                return str(value).strip()

        return f"evidence-{index + 1}"

    def _build_facts(self, evidence: list[Any]) -> list[Fact]:
        facts: list[Fact] = []

        for index, item in enumerate(evidence):
            text = self._text(item)
            score = self._score(item)

            if not text:
                continue

            # Evidence without an explicit score is accepted when it is
            # supplied directly to the ReasoningEngine. The upstream
            # relevance gate remains responsible for filtering retrieval.
            if score <= 0.0:
                score = 1.0

            if score < self.MIN_EVIDENCE_SCORE:
                continue

            evidence_id = self._evidence_id(item, index)

            facts.append(
                Fact(
                    subject="evidence",
                    predicate="states",
                    value=text,
                    evidence_ids=(evidence_id,),
                    confidence=score,
                )
            )

            low = text.lower()

            if (
                any(term in low for term in ("ktp", "ktp-el", "ktp el"))
                and any(
                    term in low
                    for term in (
                        "status",
                        "diperiksa",
                        "dapat diperiksa",
                        "melalui",
                        "prosedur",
                        "pengajuan",
                        "layanan",
                        "cek",
                    )
                )
            ):
                facts.append(
                    Fact(
                        subject="KTP-el",
                        predicate="procedure_available",
                        value=True,
                        evidence_ids=(evidence_id,),
                        confidence=score,
                    )
                )

        return facts

    def analyze(
        self,
        user_input: str,
        *,
        evidence: list[Any] | None = None,
        intent_name: str = "",
        intent_confidence: float = 0.0,
    ) -> ReasoningResult:

        del user_input

        evidence = list(evidence or [])

        if not evidence:
            return ReasoningResult(
                status="insufficient_evidence",
                facts=[],
                inferences=[],
                confidence=0.0,
                explanation="No evidence available.",
                blocked_reason="no_evidence",
            )

        facts = self._build_facts(evidence)

        if not facts:
            return ReasoningResult(
                status="insufficient_evidence",
                facts=[],
                inferences=[],
                confidence=0.0,
                explanation="Evidence exists but contains no usable facts.",
                blocked_reason="no_usable_fact",
            )

        best_score = max(
            float(getattr(fact, "confidence", 0.0) or 0.0)
            for fact in facts
        )

        intent_confidence = max(
            0.0,
            min(1.0, float(intent_confidence or 0.0)),
        )

        confidence = round(
            (best_score * 0.70)
            + (intent_confidence * 0.30),
            6,
        )

        inference = Inference(
            conclusion="answer_from_evidence",
            confidence=confidence,
            rule_name="evidence_first",
        )

        return ReasoningResult(
            status="grounded",
            facts=facts,
            inferences=[inference],
            confidence=confidence,
            explanation=(
                f"Reasoning grounded on "
                f"{len(facts)} evidence-supported fact(s)."
            ),
            blocked_reason=None,
        )
