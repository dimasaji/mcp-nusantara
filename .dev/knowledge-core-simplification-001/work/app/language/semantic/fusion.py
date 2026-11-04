from __future__ import annotations

from typing import Any

from app.language.intent import IntentClassifier
from app.language.semantic.semantic_intent import (
    SemanticIntentEngine,
)


class IntentFusion:
    """
    Intent Fusion Nusantara Core.

    Menggabungkan:
    - Rule Intent
    - IndoBERT Semantic Intent
    - Context Conflict Resolution

    intent.py tidak dimodifikasi.
    """

    SEMANTIC_MIN_THRESHOLD = 0.70
    SEMANTIC_MARGIN = 0.08

    # Intent yang sangat sensitif terhadap konteks.
    REQUIREMENT_INTENT = "ask_document_requirements"
    ISSUANCE_INTENT = "request_document_issuance"
    STATUS_INTENT = "ask_document_status"
    MISSING_INTENT = "report_missing_document"
    TECHNICAL_ISSUE_INTENT = "report_technical_issue"
    TECHNICAL_HELP_INTENT = "request_technical_help"

    def __init__(
        self,
        rule_classifier: IntentClassifier | None = None,
        semantic_engine: SemanticIntentEngine | None = None,
    ) -> None:

        self.rule_classifier = (
            rule_classifier
            or IntentClassifier()
        )

        self.semantic_engine = (
            semantic_engine
            or SemanticIntentEngine()
        )

    @staticmethod
    def _extract_value(
        result: Any,
        key: str,
        default: Any = None,
    ) -> Any:

        if isinstance(result, dict):
            return result.get(key, default)

        return getattr(
            result,
            key,
            default,
        )

    def _normalize_rule_result(
        self,
        result: Any,
    ) -> dict[str, Any]:

        intent = self._extract_value(
            result,
            "intent",
            "unknown",
        )

        confidence = self._extract_value(
            result,
            "confidence",
            0.0,
        )

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        return {
            "intent": intent or "unknown",
            "confidence": confidence,
            "raw": result,
        }

    @staticmethod
    def _has_requirement_context(
        text: str,
    ) -> bool:

        keywords = (
            "syarat",
            "syaratnya",
            "persyaratan",
            "berkas",
            "dokumen yang diperlukan",
            "dokumen yang harus",
            "dokumen apa",
            "berkas apa",
            "yang diperlukan",
            "yang dibutuhkan",
            "yang harus disiapkan",
            "harus saya siapkan",
            "perlu disiapkan",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _has_issuance_context(
        text: str,
    ) -> bool:

        keywords = (
            "membuat",
            "buat",
            "mengurus",
            "urus",
            "mengajukan",
            "ajukan",
            "penerbitan",
            "pengajuan",
            "mendaftarkan",
            "daftar",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _has_status_context(
        text: str,
    ) -> bool:

        keywords = (
            "status",
            "sudah jadi",
            "sudah selesai",
            "belum selesai",
            "sampai mana",
            "cek pengajuan",
            "cek status",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _has_missing_context(
        text: str,
    ) -> bool:

        keywords = (
            "belum menerima",
            "belum saya terima",
            "belum sampai",
            "tidak sampai",
            "belum diterima",
            "hilang",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _has_technical_problem_context(
        text: str,
    ) -> bool:

        keywords = (
            "error",
            "tidak bisa",
            "gagal",
            "tidak dapat",
            "bermasalah",
            "tidak berjalan",
            "tidak bisa dibuka",
            "tidak bisa login",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    @staticmethod
    def _has_technical_help_context(
        text: str,
    ) -> bool:

        keywords = (
            "bagaimana cara",
            "cara menggunakan",
            "cara login",
            "cara upload",
            "tolong bantu",
            "ajari saya",
            "bagaimana menggunakan",
        )

        return any(
            keyword in text
            for keyword in keywords
        )

    def _resolve_context_conflict(
        self,
        text: str,
        rule_intent: str,
        rule_confidence: float,
        semantic_intent: str,
        semantic_confidence: float,
    ) -> dict[str, Any] | None:
        """
        Menangani konflik intent yang secara semantik
        memiliki konteks khusus.

        Return None jika tidak ada conflict khusus.
        """

        normalized = text.lower().strip()

        # ==================================================
        # REQUIREMENTS vs ISSUANCE
        # ==================================================

        if (
            semantic_intent
            == self.REQUIREMENT_INTENT
            and rule_intent
            == self.ISSUANCE_INTENT
            and self._has_requirement_context(
                normalized
            )
        ):

            if semantic_confidence >= 0.78:

                return {
                    "intent": self.REQUIREMENT_INTENT,
                    "confidence": semantic_confidence,
                    "decision": (
                        "semantic_requirement_override"
                    ),
                    "reason": (
                        "Konteks kalimat menunjukkan "
                        "permintaan persyaratan/berkas."
                    ),
                }

        # ==================================================
        # ISSUANCE vs TECHNICAL HELP
        # ==================================================

        if (
            semantic_intent
            == self.ISSUANCE_INTENT
            and rule_intent
            == self.TECHNICAL_HELP_INTENT
            and self._has_issuance_context(
                normalized
            )
            and not self._has_technical_problem_context(
                normalized
            )
        ):

            if semantic_confidence >= 0.78:

                return {
                    "intent": self.ISSUANCE_INTENT,
                    "confidence": semantic_confidence,
                    "decision": (
                        "semantic_issuance_override"
                    ),
                    "reason": (
                        "Konteks menunjukkan "
                        "pengajuan/pembuatan dokumen."
                    ),
                }

        # ==================================================
        # MISSING vs STATUS
        # ==================================================

        if (
            semantic_intent
            == self.MISSING_INTENT
            and rule_intent
            == self.STATUS_INTENT
            and self._has_missing_context(
                normalized
            )
        ):

            if semantic_confidence >= 0.75:

                return {
                    "intent": self.MISSING_INTENT,
                    "confidence": semantic_confidence,
                    "decision": (
                        "semantic_missing_override"
                    ),
                    "reason": (
                        "Konteks menunjukkan "
                        "dokumen belum diterima."
                    ),
                }

        # ==================================================
        # TECHNICAL ISSUE vs TECHNICAL HELP
        # ==================================================

        if (
            semantic_intent
            == self.TECHNICAL_ISSUE_INTENT
            and rule_intent
            == self.TECHNICAL_HELP_INTENT
            and self._has_technical_problem_context(
                normalized
            )
        ):

            if semantic_confidence >= 0.70:

                return {
                    "intent": (
                        self.TECHNICAL_ISSUE_INTENT
                    ),
                    "confidence": semantic_confidence,
                    "decision": (
                        "semantic_technical_issue_override"
                    ),
                    "reason": (
                        "Konteks menunjukkan "
                        "masalah teknis."
                    ),
                }

        return None

    def classify(
        self,
        text: str,
    ) -> dict[str, Any]:

        text = str(text).strip()

        if not text:
            return {
                "ok": False,
                "engine": "intent-fusion",
                "error": "text wajib diisi",
            }

        # ==================================================
        # RULE
        # ==================================================

        rule_raw = self.rule_classifier.classify(text)

        rule = self._normalize_rule_result(
            rule_raw
        )

        rule_intent = rule["intent"]
        rule_confidence = rule["confidence"]

        # ==================================================
        # SEMANTIC
        # ==================================================

        semantic = self.semantic_engine.classify(
            text
        )

        if not semantic.get("ok"):

            return {
                "ok": True,
                "engine": "intent-fusion",
                "text": text,
                "intent": rule_intent,
                "confidence": rule_confidence,
                "decision": "rule_fallback",
                "rule": {
                    "intent": rule_intent,
                    "confidence": rule_confidence,
                },
                "semantic": semantic,
            }

        semantic_intent = semantic.get(
            "intent",
            "unknown",
        )

        semantic_confidence = float(
            semantic.get(
                "confidence",
                0.0,
            )
        )

        # ==================================================
        # CONTEXT CONFLICT RESOLUTION
        # ==================================================

        context_decision = (
            self._resolve_context_conflict(
                text=text,
                rule_intent=rule_intent,
                rule_confidence=rule_confidence,
                semantic_intent=semantic_intent,
                semantic_confidence=semantic_confidence,
            )
        )

        if context_decision is not None:

            return {
                "ok": True,
                "engine": "intent-fusion",
                "text": text,
                "intent": context_decision["intent"],
                "confidence": round(
                    context_decision[
                        "confidence"
                    ],
                    6,
                ),
                "decision": context_decision[
                    "decision"
                ],
                "reason": context_decision[
                    "reason"
                ],
                "rule": {
                    "intent": rule_intent,
                    "confidence": round(
                        rule_confidence,
                        6,
                    ),
                },
                "semantic": {
                    "intent": semantic_intent,
                    "confidence": round(
                        semantic_confidence,
                        6,
                    ),
                    "top_candidates": semantic.get(
                        "top_candidates",
                        [],
                    ),
                },
            }

        # ==================================================
        # NORMAL FUSION
        # ==================================================

        final_intent = rule_intent
        final_confidence = rule_confidence
        decision = "rule_default"

        # Rule + semantic sepakat
        if (
            rule_intent != "unknown"
            and rule_intent == semantic_intent
        ):

            final_intent = rule_intent

            final_confidence = (
                (rule_confidence * 0.60)
                + (semantic_confidence * 0.40)
            )

            decision = "agreement"

        # Rule tidak tahu -> semantic recovery
        elif (
            rule_intent == "unknown"
            and semantic_confidence
            >= self.SEMANTIC_MIN_THRESHOLD
        ):

            final_intent = semantic_intent
            final_confidence = semantic_confidence
            decision = "semantic_recovery"

        # Semantic cukup kuat mengalahkan rule
        elif (
            semantic_confidence
            >= self.SEMANTIC_MIN_THRESHOLD
            and (
                semantic_confidence
                - rule_confidence
            )
            >= self.SEMANTIC_MARGIN
        ):

            final_intent = semantic_intent
            final_confidence = semantic_confidence
            decision = "semantic_override"

        # Default rule
        else:

            final_intent = rule_intent
            final_confidence = rule_confidence
            decision = "rule_fallback"

        return {
            "ok": True,
            "engine": "intent-fusion",
            "text": text,
            "intent": final_intent,
            "confidence": round(
                float(final_confidence),
                6,
            ),
            "decision": decision,
            "rule": {
                "intent": rule_intent,
                "confidence": round(
                    rule_confidence,
                    6,
                ),
            },
            "semantic": {
                "intent": semantic_intent,
                "confidence": round(
                    semantic_confidence,
                    6,
                ),
                "top_candidates": semantic.get(
                    "top_candidates",
                    [],
                ),
            },
        }

    def health(self) -> dict[str, Any]:

        return {
            "ok": True,
            "engine": "intent-fusion",
            "rule": {
                "available": (
                    self.rule_classifier
                    is not None
                ),
            },
            "semantic": (
                self.semantic_engine.health()
            ),
        }

    def stop(self) -> None:

        self.semantic_engine.stop()