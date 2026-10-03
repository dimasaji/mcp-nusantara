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

        # --------------------------------------------------------
        # VALID EVIDENCE-BASED ABSTENTION
        # --------------------------------------------------------
        # A pure abstention is allowed only when it does not contain
        # a requirement, procedure, or numeric claim. This prevents
        # the guard from treating a legitimate "information is not
        # available" response as hallucinated content while keeping
        # high-risk claims fail-closed.
        if (
            len(sentences) == 1
            and self._is_valid_abstention(sentences[0])
        ):
            return GroundingResult(
                text=text,
                grounded=True,
                reason="grounded_abstention",
                unsupported_sentences=[],
            )

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
    # ABSTENTION VALIDATION
    # ============================================================

    def _is_valid_abstention(
        self,
        sentence: str,
    ) -> bool:
        """
        Accept a pure evidence-based abstention without requiring
        lexical overlap with the evidence.

        This is intentionally narrow:
        - accepts statements that explicitly say information is
          unavailable / not present in evidence
        - rejects abstentions that themselves contain requirement,
          procedure, or numeric claims

        Example accepted:
            "Informasi tersebut belum tersedia dalam EVIDENCE."

        Example rejected:
            "Syarat membuat KTP-el adalah ..."
        """
        lower = self._normalize_text(sentence).lower()

        if not lower:
            return False

        abstention_markers = (
            "tidak tersedia",
            "belum tersedia",
            "tidak ada informasi",
            "belum ada informasi",
            "tidak ditemukan informasi",
            "belum ditemukan informasi",
            "informasi tidak tersedia",
            "informasi tersebut tidak tersedia",
            "informasi tersebut belum tersedia",
            "evidence tidak memenuhi",
            "evidence tidak memiliki",
            "tidak terdapat informasi",
            "tidak terdapat data",
            "belum terdapat informasi",
        )

        if not any(
            marker in lower
            for marker in abstention_markers
        ):
            return False

        # A refusal containing a concrete high-risk claim is NOT
        # a pure abstention and must still be grounded normally.
        if self._contains_requirement_claim(sentence):
            return False

        if self._contains_procedure_claim(sentence):
            return False

        if self._contains_numeric_claim(sentence):
            return False

        return True

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
        """
        Detect procedural/action claims.

        A sentence is procedural when it contains explicit
        action/instruction language OR an obligation combined
        with an action.
        """

        lower = self._normalize_text(sentence).lower()

        # Explicit procedural markers.
        explicit_markers = (
            "langkah",
            "cara",
            "prosedur",
            "tahapan",
            "ikuti",
            "lakukan",
            "melakukan",
            "klik",
            "buka",
            "pilih",
            "masukkan",
            "isi",
            "unggah",
            "upload",
            "ajukan",
            "mengajukan",
            "datang",
            "bawa",
            "periksa",
            "cek",
            "mengecek",
        )

        # Obligation + action is definitely procedural.
        obligation_markers = (
            "harus",
            "wajib",
            "perlu",
            "diharuskan",
        )

        has_explicit = any(
            marker in lower
            for marker in explicit_markers
        )

        has_obligation = any(
            marker in lower
            for marker in obligation_markers
        )

        # Critical rule:
        # "harus melakukan ...", "wajib mengajukan ...",
        # etc. are procedural claims.
        if has_obligation and has_explicit:
            return True

        return has_explicit

    def _evidence_contains_procedure_claim(
        self,
        evidence: str,
    ) -> bool:
        """
        Detect EXPLICIT procedural instructions in evidence.

        Capability/status statements such as:
            "status dapat diperiksa melalui layanan"

        are NOT considered procedural evidence.

        Procedural evidence requires explicit action/instruction
        language such as:
            langkah, cara, lakukan, klik, buka, pilih, masukkan,
            unggah, isi, ajukan, datang, bawa, ikuti, tahapan,
            prosedur.
        """

        lower = self._normalize_text(evidence).lower()

        explicit_procedure_markers = (
            "langkah",
            "cara",
            "prosedur",
            "tahapan",
            "ikuti",
            "lakukan",
            "melakukan langkah",
            "klik",
            "buka",
            "pilih",
            "masukkan",
            "isi",
            "unggah",
            "upload",
            "ajukan",
            "mengajukan",
            "datang",
            "bawa",
        )

        return any(
            marker in lower
            for marker in explicit_procedure_markers
        )

    def _procedure_claim_supported(
        self,
        sentence: str,
        evidence: str,
    ) -> bool:
        """
        Procedure claims require explicit procedural evidence.

        Lexical overlap of one token is NOT sufficient.
        Evidence must contain procedural language and provide
        meaningful lexical support for the claimed action.
        """

        if not self._contains_procedure_claim(sentence):
            return True

        # Evidence must explicitly describe a procedure/action.
        if not self._evidence_contains_procedure_claim(evidence):
            return False

        sentence_tokens = self._meaningful_tokens(sentence)
        evidence_tokens = self._meaningful_tokens(evidence)

        if not sentence_tokens or not evidence_tokens:
            return False

        overlap = sentence_tokens & evidence_tokens

        # One shared token is too weak for a procedural claim.
        # Require at least 2 meaningful overlapping tokens.
        if len(overlap) < 2:
            return False

        # Require meaningful lexical coverage of the claim.
        coverage = len(overlap) / max(len(sentence_tokens), 1)

        # Procedure claims need stronger evidence than ordinary
        # informational statements.
        return coverage >= 0.30


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
