from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Iterable


logger = logging.getLogger(__name__)


@dataclass
class GroundingResult:
    text: str
    grounded: bool
    reason: str
    unsupported_sentences: list[str]


class EvidenceGroundingGuard:
    """
    Validates whether an LLM response is sufficiently supported
    by retrieved knowledge evidence.

    Design principles:
    1. Generic topic overlap is NOT sufficient.
    2. Requirement questions require requirement evidence.
    3. Procedure questions require procedure evidence.
    4. Numeric claims require matching numeric evidence.
    5. Every substantive answer sentence must have evidence support.
    6. Empty evidence fails closed.
    7. Deterministic/local-rule responses can bypass this validator
       at the API routing layer.
    """

    STOPWORDS = {
        "yang",
        "dan",
        "atau",
        "dengan",
        "untuk",
        "dari",
        "pada",
        "dalam",
        "adalah",
        "merupakan",
        "dapat",
        "akan",
        "telah",
        "sudah",
        "bisa",
        "bagi",
        "sebagai",
        "secara",
        "melalui",
        "oleh",
        "ini",
        "itu",
        "saya",
        "anda",
        "kami",
        "kita",
        "tersebut",
        "agar",
        "jika",
        "karena",
        "maka",
        "ke",
        "di",
        "dengan",
        "sebuah",
        "suatu",
    }

    GENERIC_DOMAIN_TERMS = {
        "ktp",
        "ktp-el",
        "ktpel",
        "dokumen",
        "penduduk",
        "identitas",
        "administrasi",
        "kependudukan",
        "layanan",
        "status",
        "pengajuan",
        "sistem",
        "informasi",
        "pemerintah",
        "data",
        "pelayanan",
    }

    REQUIREMENT_MARKERS = (
        "syarat",
        "persyaratan",
        "persyaratan dokumen",
        "dokumen yang diperlukan",
        "dokumen yang dibutuhkan",
        "dokumen yang harus",
        "dokumen wajib",
        "wajib",
        "harus membawa",
        "harus melampirkan",
        "harus menyerahkan",
        "diperlukan",
        "dibutuhkan",
        "melampirkan",
        "membawa",
        "menyerahkan",
        "ketentuan persyaratan",
    )

    # Sengaja TIDAK memasukkan "ketentuan".
    # Kata "ketentuan" saja bukan bukti adanya persyaratan.
    PROCEDURE_MARKERS = (
        "langkah",
        "langkah pertama",
        "langkah berikutnya",
        "cara",
        "caranya",
        "prosedur",
        "tahapan",
        "tahap",
        "ikuti",
        "mengisi",
        "isi formulir",
        "mengajukan",
        "ajukan",
        "mendaftar",
        "daftar",
        "datang ke",
        "kunjungi",
        "buka",
        "pilih",
        "masukkan",
        "unggah",
        "upload",
        "kirim",
        "serahkan",
        "tunggu",
        "kemudian",
        "selanjutnya",
    )

    NUMBER_PATTERN = re.compile(
        r"\b\d+(?:[.,]\d+)?\b",
        re.UNICODE,
    )

    SENTENCE_PATTERN = re.compile(
        r"(?<=[.!?])\s+|\n+",
        re.UNICODE,
    )

    def __init__(
        self,
        min_sentence_overlap: float = 0.30,
        min_meaningful_tokens: int = 1,
    ) -> None:
        self.min_sentence_overlap = float(
            min_sentence_overlap
        )
        self.min_meaningful_tokens = int(
            min_meaningful_tokens
        )

    # ============================================================
    # PUBLIC API
    # ============================================================

    def validate(
        self,
        answer: Any,
        evidence: Any,
        intent_name: str | None = None,
    ) -> GroundingResult:
        """
        Validate an answer against retrieved evidence.

        intent_name is important for high-risk semantic categories:
        - ask_document_requirements
        - procedure/how-to questions
        - status questions
        - general information
        """

        text = self._normalize_text(answer)

        if not text:
            return GroundingResult(
                text="",
                grounded=False,
                reason="empty_answer",
                unsupported_sentences=[],
            )

        evidence_items = self._normalize_evidence(evidence)

        if not evidence_items:
            logger.warning(
                "Grounding rejected: no evidence."
            )
            return GroundingResult(
                text=text,
                grounded=False,
                reason="no_evidence",
                unsupported_sentences=[text],
            )

        evidence_texts = [
            item["text"]
            for item in evidence_items
            if item["text"]
        ]

        combined_evidence = " ".join(evidence_texts)

        question_type = self._normalize_intent(
            intent_name
        )

        sentences = self._split_sentences(text)

        if not sentences:
            sentences = [text]

        unsupported: list[str] = []

        # --------------------------------------------------------
        # INTENT-SPECIFIC SAFETY
        # --------------------------------------------------------

        if question_type == "ask_document_requirements":
            if not self._evidence_contains_requirement_claim(
                combined_evidence
            ):
                logger.warning(
                    "Requirement validation failed: "
                    "evidence contains no explicit requirements."
                )
                return GroundingResult(
                    text=text,
                    grounded=False,
                    reason="requirement_evidence_missing",
                    unsupported_sentences=sentences,
                )

        # --------------------------------------------------------
        # SENTENCE VALIDATION
        # --------------------------------------------------------

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            if self._is_low_information_sentence(sentence):
                continue

            if self._contains_unsafe_claim(sentence):
                if not self._claim_supported(
                    sentence,
                    combined_evidence,
                    question_type,
                ):
                    unsupported.append(sentence)
                    continue

            if self._contains_numeric_claim(sentence):
                if not self._numbers_supported(
                    sentence,
                    combined_evidence,
                ):
                    unsupported.append(sentence)
                    continue

            if self._contains_requirement_claim(sentence):
                if not self._requirement_claim_supported(
                    sentence,
                    combined_evidence,
                ):
                    unsupported.append(sentence)
                    continue

            if self._contains_procedure_claim(sentence):
                if not self._procedure_claim_supported(
                    sentence,
                    combined_evidence,
                ):
                    unsupported.append(sentence)
                    continue

            if not self._general_sentence_supported(
                sentence,
                evidence_texts,
            ):
                unsupported.append(sentence)

        if unsupported:
            logger.warning(
                "Grounding rejected answer: "
                "reason=possible_unsupported_content "
                "unsupported=%d",
                len(unsupported),
            )

            return GroundingResult(
                text=text,
                grounded=False,
                reason="possible_unsupported_content",
                unsupported_sentences=unsupported,
            )

        return GroundingResult(
            text=text,
            grounded=True,
            reason="grounded",
            unsupported_sentences=[],
        )

    def build_grounded_context(
        self,
        evidence: Any,
    ) -> str:
        evidence_items = self._normalize_evidence(
            evidence
        )

        if not evidence_items:
            return (
                "Tidak ada evidence knowledge base "
                "yang tersedia."
            )

        parts: list[str] = []

        for index, item in enumerate(
            evidence_items,
            start=1,
        ):
            title = item.get(
                "title",
                "Knowledge Base",
            )
            content = item.get("text", "")

            parts.append(
                f"[EVIDENCE {index}] "
                f"{title}\n"
                f"{content}"
            )

        return "\n\n".join(parts)

    def build_system_instruction(self) -> str:
        return (
            "Jawab hanya berdasarkan EVIDENCE yang diberikan. "
            "Jangan membuat persyaratan, prosedur, angka, "
            "durasi, biaya, alamat, atau langkah layanan "
            "yang tidak terdapat secara eksplisit dalam "
            "EVIDENCE. Jika informasi tidak tersedia, "
            "katakan bahwa informasi tersebut belum tersedia "
            "dalam knowledge base."
        )

    # ============================================================
    # EVIDENCE NORMALIZATION
    # ============================================================

    def _normalize_evidence(
        self,
        evidence: Any,
    ) -> list[dict[str, str]]:
        if evidence is None:
            return []

        if isinstance(evidence, str):
            text = evidence.strip()
            return (
                [{"title": "Evidence", "text": text}]
                if text
                else []
            )

        if isinstance(evidence, dict):
            return self._normalize_evidence_item(
                evidence
            )

        if isinstance(evidence, Iterable):
            result: list[dict[str, str]] = []

            for item in evidence:
                normalized = (
                    self._normalize_evidence_item(item)
                )

                result.extend(normalized)

            return result

        normalized = self._normalize_evidence_item(
            evidence
        )

        return normalized

    def _normalize_evidence_item(
        self,
        item: Any,
    ) -> list[dict[str, str]]:
        if item is None:
            return []

        if isinstance(item, str):
            text = item.strip()

            return (
                [{"title": "Evidence", "text": text}]
                if text
                else []
            )

        if isinstance(item, dict):
            title = str(
                item.get(
                    "title",
                    item.get(
                        "document_id",
                        "Evidence",
                    ),
                )
                or "Evidence"
            )

            text = (
                item.get("chunk")
                or item.get("source")
                or item.get("text")
                or item.get("content")
                or ""
            )

            text = self._normalize_text(text)

            if not text:
                return []

            return [
                {
                    "title": title,
                    "text": text,
                }
            ]

        title = str(
            getattr(
                item,
                "title",
                getattr(
                    item,
                    "document_id",
                    "Evidence",
                ),
            )
            or "Evidence"
        )

        text = (
            getattr(item, "chunk", None)
            or getattr(item, "source", None)
            or getattr(item, "text", None)
            or getattr(item, "content", None)
            or ""
        )

        text = self._normalize_text(text)

        if not text:
            return []

        return [
            {
                "title": title,
                "text": text,
            }
        ]

    # ============================================================
    # TEXT PROCESSING
    # ============================================================

    def _normalize_text(
        self,
        value: Any,
    ) -> str:
        if value is None:
            return ""

        return re.sub(
            r"\s+",
            " ",
            str(value),
        ).strip()

    def _split_sentences(
        self,
        text: str,
    ) -> list[str]:
        parts = self.SENTENCE_PATTERN.split(
            text.strip()
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]

    def _content_tokens(
        self,
        text: str,
    ) -> set[str]:
        tokens = re.findall(
            r"\b\w+\b",
            text.lower(),
            flags=re.UNICODE,
        )

        return {
            token
            for token in tokens
            if len(token) > 1
            and token not in self.STOPWORDS
        }

    def _meaningful_tokens(
        self,
        text: str,
    ) -> set[str]:
        return (
            self._content_tokens(text)
            - self.GENERIC_DOMAIN_TERMS
        )

    # ============================================================
    # INTENT
    # ============================================================

    def _normalize_intent(
        self,
        intent_name: str | None,
    ) -> str:
        if not intent_name:
            return ""

        return str(intent_name).strip().lower()

    # ============================================================
    # REQUIREMENT VALIDATION
    # ============================================================

    def _contains_requirement_claim(
        self,
        sentence: str,
    ) -> bool:
        lower = sentence.lower()

        return any(
            marker in lower
            for marker in self.REQUIREMENT_MARKERS
        )

    def _evidence_contains_requirement_claim(
        self,
        evidence: str,
    ) -> bool:
        lower = evidence.lower()

        return any(
            marker in lower
            for marker in self.REQUIREMENT_MARKERS
        )

    def _requirement_claim_supported(
        self,
        sentence: str,
        evidence: str,
    ) -> bool:
        """
        Requirement claims require explicit requirement
        language in the evidence.

        Generic words such as KTP, dokumen, administrasi,
        status, diterbitkan, or ketentuan are insufficient.
        """

        if not self._contains_requirement_claim(
            sentence
        ):
            return True

        if not self._evidence_contains_requirement_claim(
            evidence
        ):
            return False

        sentence_tokens = (
            self._meaningful_tokens(sentence)
        )

        evidence_tokens = (
            self._meaningful_tokens(evidence)
        )

        overlap = (
            sentence_tokens
            & evidence_tokens
        )

        return len(overlap) >= 1

    # ============================================================
    # PROCEDURE VALIDATION
    # ============================================================

    def _contains_procedure_claim(
        self,
        sentence: str,
    ) -> bool:
        lower = sentence.lower()

        return any(
            marker in lower
            for marker in self.PROCEDURE_MARKERS
        )

    def _evidence_contains_procedure_claim(
        self,
        evidence: str,
    ) -> bool:
        lower = evidence.lower()

        return any(
            marker in lower
            for marker in self.PROCEDURE_MARKERS
        )

    def _procedure_claim_supported(
        self,
        sentence: str,
        evidence: str,
    ) -> bool:
        if not self._contains_procedure_claim(
            sentence
        ):
            return True

        if not self._evidence_contains_procedure_claim(
            evidence
        ):
            return False

        sentence_tokens = (
            self._meaningful_tokens(sentence)
        )

        evidence_tokens = (
            self._meaningful_tokens(evidence)
        )

        overlap = (
            sentence_tokens
            & evidence_tokens
        )

        return len(overlap) >= 1

    # ============================================================
    # NUMERIC VALIDATION
    # ============================================================

    def _contains_numeric_claim(
        self,
        sentence: str,
    ) -> bool:
        return bool(
            self.NUMBER_PATTERN.search(sentence)
        )

    def _numbers_supported(
        self,
        sentence: str,
        evidence: str,
    ) -> bool:
        answer_numbers = set(
            self.NUMBER_PATTERN.findall(
                sentence
            )
        )

        if not answer_numbers:
            return True

        evidence_numbers = set(
            self.NUMBER_PATTERN.findall(
                evidence
            )
        )

        return answer_numbers.issubset(
            evidence_numbers
        )

    # ============================================================
    # GENERAL VALIDATION
    # ============================================================

    def _general_sentence_supported(
        self,
        sentence: str,
        evidence_texts: list[str],
    ) -> bool:
        sentence_tokens = (
            self._content_tokens(sentence)
        )

        if not sentence_tokens:
            return True

        best_overlap = 0.0

        for evidence in evidence_texts:
            evidence_tokens = (
                self._content_tokens(evidence)
            )

            if not evidence_tokens:
                continue

            overlap = (
                sentence_tokens
                & evidence_tokens
            )

            score = (
                len(overlap)
                / max(
                    len(sentence_tokens),
                    1,
                )
            )

            best_overlap = max(
                best_overlap,
                score,
            )

        return (
            best_overlap
            >= self.min_sentence_overlap
        )

    def _claim_supported(
        self,
        sentence: str,
        evidence: str,
        intent_name: str,
    ) -> bool:
        if self._contains_requirement_claim(
            sentence
        ):
            return self._requirement_claim_supported(
                sentence,
                evidence,
            )

        if self._contains_procedure_claim(
            sentence
        ):
            return self._procedure_claim_supported(
                sentence,
                evidence,
            )

        if self._contains_numeric_claim(
            sentence
        ):
            return self._numbers_supported(
                sentence,
                evidence,
            )

        return self._general_sentence_supported(
            sentence,
            [evidence],
        )

    # ============================================================
    # SAFETY
    # ============================================================

    def _contains_unsafe_claim(
        self,
        sentence: str,
    ) -> bool:
        lower = sentence.lower()

        markers = (
            self.REQUIREMENT_MARKERS
            + self.PROCEDURE_MARKERS
            + (
                "biaya",
                "rp",
                "rupiah",
                "hari kerja",
                "jam",
                "menit",
                "usia",
                "berlaku",
                "masa berlaku",
            )
        )

        return any(
            marker in lower
            for marker in markers
        )

    def _is_low_information_sentence(
        self,
        sentence: str,
    ) -> bool:
        tokens = self._content_tokens(
            sentence
        )

        return len(tokens) < 2


# Backward-compatible alias if other modules import
# the class using a different name.
GroundingGuard = EvidenceGroundingGuard
