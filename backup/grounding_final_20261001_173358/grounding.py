"""
Nusantara AI - Evidence Grounding Guard

Purpose
-------
Mencegah model menghasilkan jawaban yang tidak didukung oleh
knowledge/evidence yang diberikan.

Prinsip:
1. Evidence kosong -> jawaban tidak boleh dianggap grounded.
2. Klaim harus mempunyai overlap dengan evidence.
3. Klaim numerik/prosedural/requirements diperlakukan lebih ketat.
4. Sentence yang tidak didukung harus terdeteksi.
5. Validator tidak boleh mempercayai model hanya karena model
   menyebut kata "EVIDENCE".
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Iterable, Sequence

logger = logging.getLogger(__name__)


# ============================================================
# Result
# ============================================================

@dataclass
class GroundingResult:
    text: str
    grounded: bool
    reason: str
    unsupported_sentences: list[str]


# ============================================================
# Guard
# ============================================================

class EvidenceGroundingGuard:
    """
    Validates whether an answer is reasonably supported by evidence.

    This is deliberately conservative.

    The validator is not intended to prove factual truth.
    It is a safety gate against unsupported generation.
    """

    # Common Indonesian function words that do not help establish
    # factual overlap.
    STOPWORDS = {
        "yang",
        "dan",
        "atau",
        "di",
        "ke",
        "dari",
        "untuk",
        "dengan",
        "pada",
        "dalam",
        "adalah",
        "merupakan",
        "sebagai",
        "dapat",
        "akan",
        "telah",
        "sudah",
        "belum",
        "ini",
        "itu",
        "tersebut",
        "secara",
        "melalui",
        "oleh",
        "agar",
        "jika",
        "maka",
        "juga",
        "lebih",
        "bisa",
        "harus",
        "perlu",
        "saya",
        "anda",
        "kami",
        "kita",
        "mereka",
        "apa",
        "bagaimana",
        "cara",
        "yang",
        "sebuah",
        "suatu",
        "dengan",
        "bahwa",
        "dalam",
        "terhadap",
        "tentang",
        "dari",
        "pada",
        "atau",
        "dan",
        "ke",
        "untuk",
        "seperti",
        "misalnya",
    }

    # Words that indicate claims requiring stronger evidence.
    REQUIREMENT_MARKERS = {
        "syarat",
        "persyaratan",
        "ketentuan",
        "dokumen",
        "harus",
        "wajib",
        "minimal",
        "maksimal",
        "biaya",
        "tarif",
        "lama",
        "hari",
        "jam",
        "menit",
        "prosedur",
        "langkah",
        "tahapan",
        "cara",
        "mekanisme",
        "proses",
        "mengajukan",
        "pengajuan",
        "permohonan",
        "berkas",
        "pertama",
        "kedua",
        "ketiga",
        "selanjutnya",
        "kemudian",
        "setelah",
        "sebelum",
        "isi",
        "mengisi",
        "datang",
        "membawa",
        "serahkan",
        "menyerahkan",
    }

    PROCEDURE_MARKERS = {
        "prosedur",
        "langkah",
        "tahapan",
        "cara",
        "mekanisme",
        "proses",
        "pertama",
        "kedua",
        "ketiga",
        "selanjutnya",
        "kemudian",
        "setelah",
        "sebelum",
        "isi",
        "mengisi",
        "datang",
        "membawa",
        "serahkan",
        "menyerahkan",
        "mengajukan",
        "pengajuan",
        "permohonan",
    }

    # Statements that frequently introduce unsupported content.
    UNSAFE_PATTERNS = (
        r"\bmenurut\b",
        r"\bberdasarkan\b",
        r"\bwajib\b",
        r"\bharus\b",
        r"\bminimal\b",
        r"\bmaksimal\b",
        r"\bsetidaknya\b",
        r"\bsekitar\b",
        r"\bsebanyak\b",
        r"\bselama\b",
        r"\bdalam\s+\d+\s+(hari|jam|menit)",
        r"\b\d+\s+(hari|jam|menit|rupiah|tahun|bulan)\b",
    )

    def __init__(
        self,
        *,
        min_token_overlap: float = 0.18,
        min_strong_overlap: float = 0.30,
        min_sentence_tokens: int = 3,
    ) -> None:
        self.min_token_overlap = float(min_token_overlap)
        self.min_strong_overlap = float(min_strong_overlap)
        self.min_sentence_tokens = int(min_sentence_tokens)

    # ========================================================
    # Public API
    # ========================================================

    def build_grounded_context(
        self,
        evidence: list[Any] | None,
    ) -> str:
        """
        Convert evidence objects/dicts into a deterministic context
        that can be inserted into the LLM prompt.
        """

        if not evidence:
            return (
                "EVIDENCE KOSONG.\n"
                "Tidak ada informasi knowledge base yang tersedia.\n"
                "Jangan membuat fakta, persyaratan, prosedur, angka, "
                "biaya, waktu, atau status yang tidak diberikan."
            )

        blocks: list[str] = []

        for index, item in enumerate(evidence, start=1):
            text = self._extract_text(item)

            if not text:
                continue

            source = self._extract_source(item)

            header = f"[EVIDENCE {index}]"

            if source:
                header += f" SOURCE: {source}"

            blocks.append(
                f"{header}\n"
                f"{text.strip()}"
            )

        if not blocks:
            return (
                "EVIDENCE KOSONG.\n"
                "Tidak ada teks evidence yang dapat digunakan.\n"
                "Jangan mengarang informasi."
            )

        return "\n\n".join(blocks)

    def build_system_instruction(self) -> str:
        """
        System instruction used by the answer-generation stage.
        """

        return """
Anda adalah Hermes, reasoning assistant untuk Nusantara AI.

ATURAN GROUNDING WAJIB:

1. Jawaban HARUS berdasarkan EVIDENCE yang diberikan.
2. Jangan membuat fakta dari pengetahuan internal model.
3. Jangan mengarang persyaratan, prosedur, langkah, biaya, tarif,
   durasi, angka, tanggal, alamat, nomor, nama layanan, atau status.
4. Jika informasi yang ditanyakan tidak tersedia dalam EVIDENCE,
   katakan secara eksplisit bahwa informasi tersebut belum tersedia
   pada knowledge base.
5. Jangan mengubah pertanyaan pengguna menjadi fakta baru.
6. Jangan menganggap kemiripan topik sebagai bukti.
7. Jangan menggunakan kalimat seperti "berdasarkan evidence"
   sebagai pengganti bukti faktual.
8. Jika EVIDENCE tidak cukup untuk menjawab pertanyaan, jangan
   melengkapi kekurangannya dengan pengetahuan umum model.
9. Untuk pertanyaan persyaratan/prosedur, semua poin utama harus
   mempunyai dukungan dari EVIDENCE.
10. Untuk pertanyaan status pribadi, jangan membuat status.
11. Jawaban harus singkat, langsung, dan hanya menyampaikan
    informasi yang dapat dipertanggungjawabkan dari EVIDENCE.
""".strip()

    def validate(
        self,
        answer: str | None,
        evidence: list[Any] | None,
    ) -> GroundingResult:
        """
        Conservative grounding validation.

        Important:
        - Empty evidence => never grounded.
        - Empty answer => never grounded.
        - Requirement/procedure questions are held to a higher bar.
        - Numeric/procedural claims require stronger evidence.
        """

        text = self._clean_text(answer)

        if not text:
            return GroundingResult(
                text="",
                grounded=False,
                reason="empty_answer",
                unsupported_sentences=[],
            )

        evidence_texts = self._normalise_evidence(evidence)

        if not evidence_texts:
            return GroundingResult(
                text=text,
                grounded=False,
                reason="no_evidence",
                unsupported_sentences=self._split_sentences(text),
            )

        combined_evidence = " ".join(evidence_texts)

        # Detect sentences.
        sentences = self._split_sentences(text)

        if not sentences:
            return GroundingResult(
                text=text,
                grounded=False,
                reason="no_sentences",
                unsupported_sentences=[text],
            )

        unsupported: list[str] = []

        question_type = self._detect_question_type(text)

        for sentence in sentences:
            if self._is_meta_sentence(sentence):
                # "Berikut..." / "Dengan demikian..." are not themselves
                # evidence-bearing factual claims.
                continue

            tokens = self._content_tokens(sentence)

            if len(tokens) < self.min_sentence_tokens:
                continue

            overlap = self._token_overlap(tokens, combined_evidence)

            phrase_overlap = self._phrase_overlap(
                sentence,
                combined_evidence,
            )

            numeric_claim = self._contains_numeric_claim(sentence)

            requirement_claim = self._contains_requirement_claim(sentence)

            procedure_claim = self._contains_procedure_claim(sentence)

            strong_claim = (
                numeric_claim
                or requirement_claim
                or procedure_claim
                or question_type in {
                    "requirements",
                    "procedure",
                    "status",
                }
            )

            if strong_claim:
                supported = (
                    overlap >= self.min_strong_overlap
                    or phrase_overlap >= 0.25
                )
            else:
                supported = (
                    overlap >= self.min_token_overlap
                    or phrase_overlap >= 0.20
                )

            # Explicitly reject common hallucination patterns if
            # evidence does not contain the corresponding factual
            # vocabulary.
            if numeric_claim and not self._numeric_values_supported(
                sentence,
                combined_evidence,
            ):
                supported = False

            if requirement_claim and not self._requirement_terms_supported(
                sentence,
                combined_evidence,
            ):
                supported = False

            if procedure_claim and not self._procedure_terms_supported(
                sentence,
                combined_evidence,
            ):
                supported = False

            if not supported:
                unsupported.append(sentence)

        # ----------------------------------------------------
        # Whole-answer checks
        # ----------------------------------------------------

        # If user asked for requirements/procedure/status and the
        # model generated substantive claims but the evidence does
        # not contain the relevant concepts, reject.
        if question_type in {"requirements", "procedure", "status"}:
            if not self._evidence_covers_question(
                text,
                combined_evidence,
                question_type,
            ):
                unsupported.extend(
                    self._substantive_sentences(sentences)
                )

        unsupported = self._deduplicate(unsupported)

        if unsupported:
            logger.warning(
                "Grounding rejected answer: reason=possible_unsupported_content "
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

    # ========================================================
    # Evidence extraction
    # ========================================================

    def _normalise_evidence(
        self,
        evidence: list[Any] | None,
    ) -> list[str]:
        if not evidence:
            return []

        result: list[str] = []

        for item in evidence:
            text = self._extract_text(item)

            if text:
                result.append(self._clean_text(text))

        return result

    def _extract_text(self, item: Any) -> str:
        if item is None:
            return ""

        if isinstance(item, str):
            return item

        if isinstance(item, dict):
            for key in (
                "text",
                "content",
                "chunk",
                "document_text",
                "evidence",
                "page_content",
            ):
                value = item.get(key)

                if value:
                    return str(value)

            return ""

        for attr in (
            "text",
            "content",
            "chunk",
            "document_text",
            "evidence",
            "page_content",
        ):
            value = getattr(item, attr, None)

            if value:
                return str(value)

        return ""

    def _extract_source(self, item: Any) -> str:
        if isinstance(item, dict):
            for key in (
                "source",
                "document",
                "document_name",
                "filename",
                "file_name",
            ):
                value = item.get(key)

                if value:
                    return str(value)

        for attr in (
            "source",
            "document",
            "document_name",
            "filename",
            "file_name",
        ):
            value = getattr(item, attr, None)

            if value:
                return str(value)

        return ""

    # ========================================================
    # Text processing
    # ========================================================

    def _clean_text(self, text: Any) -> str:
        if text is None:
            return ""

        value = str(text)

        value = value.replace("\x00", " ")
        value = re.sub(r"\s+", " ", value)

        return value.strip()

    def _split_sentences(self, text: str) -> list[str]:
        if not text:
            return []

        # Preserve numbered lists as individual claims where possible.
        text = re.sub(r"\s*(?:\r?\n)+\s*", "\n", text)

        pieces = re.split(
            r"(?:\n+)|(?<=[.!?])\s+",
            text,
        )

        result = []

        for piece in pieces:
            piece = piece.strip()

            # Remove bullet prefix only for analysis.
            piece = re.sub(
                r"^(?:[-*â€¢]+|\d+[.)])\s*",
                "",
                piece,
            ).strip()

            if piece:
                result.append(piece)

        return result

    def _content_tokens(self, text: str) -> set[str]:
        """
        Unicode-safe tokenization.

        Do NOT use ranges such as ?-? here because source files can
        become mojibake when an UTF-8 file is decoded incorrectly.

        Python's default Unicode word matching is Unicode-aware, so it safely handles
        Indonesian text such as:
        KTP-el, dokumen, persyaratan, penduduk, administrasi.
        """

        tokens = re.findall(
            r"\b\w+\b",
            text.lower(),
            flags=re.UNICODE,
        )

        return {
            token
            for token in tokens
            if len(token) >= 3
            and token not in self.STOPWORDS
        }

    def _token_overlap(
        self,
        answer_tokens: set[str],
        evidence_text: str,
    ) -> float:
        if not answer_tokens:
            return 0.0

        evidence_tokens = self._content_tokens(evidence_text)

        if not evidence_tokens:
            return 0.0

        intersection = answer_tokens & evidence_tokens

        return len(intersection) / len(answer_tokens)

    def _phrase_overlap(
        self,
        sentence: str,
        evidence: str,
    ) -> float:
        """
        Unicode-safe phrase overlap.

        Uses 2- and 3-token shingles without hard-coded character
        ranges. This avoids UTF-8/mojibake regex failures.
        """

        evidence_lower = evidence.lower()

        raw_tokens = re.findall(
            r"\b\w+\b",
            sentence.lower(),
            flags=re.UNICODE,
        )

        if not raw_tokens:
            return 0.0

        score = 0
        total = 0

        for n in (3, 2):
            if len(raw_tokens) < n:
                continue

            for i in range(len(raw_tokens) - n + 1):
                phrase = " ".join(raw_tokens[i:i+n])
                total += 1

                if phrase in evidence_lower:
                    score += 1

        if total == 0:
            return 0.0

        return min(1.0, score / total)

    # ========================================================
    # Claim detection
    # ========================================================

    def _detect_question_type(self, text: str) -> str:
        value = text.lower()

        if any(
            word in value
            for word in (
                "syarat",
                "persyaratan",
                "ketentuan",
            )
        ):
            return "requirements"

        if any(
            word in value
            for word in (
                "bagaimana cara",
                "cara ",
                "prosedur",
                "langkah",
                "tahapan",
                "mekanisme",
            )
        ):
            return "procedure"

        if any(
            word in value
            for word in (
                "status",
                "sudah selesai",
                "sudah jadi",
                "cek status",
            )
        ):
            return "status"

        return "general"

    def _contains_requirement_claim(self, sentence: str) -> bool:
        tokens = self._content_tokens(sentence)

        return bool(tokens & self.REQUIREMENT_MARKERS)

    def _contains_numeric_claim(self, sentence: str) -> bool:
        value = sentence.lower()

        return bool(
            re.search(
                r"\b\d+(?:[.,]\d+)?\b",
                value,
            )
            or re.search(
                r"\b\d+\s*(?:hari|jam|menit|bulan|tahun|rupiah|rp)\b",
                value,
            )
        )

    def _contains_procedure_claim(self, sentence: str) -> bool:
        """
        Detect statements that describe an operational procedure.

        Example:
            "Langkah pertama adalah mengisi formulir."
            "Kemudian datang ke kantor pelayanan."
            "Pemohon harus menyerahkan dokumen."

        These are treated as factual procedural claims and therefore
        require explicit support from evidence.
        """

        tokens = self._content_tokens(sentence)

        if tokens & self.PROCEDURE_MARKERS:
            return True

        value = sentence.lower().strip()

        procedure_prefixes = (
            "langkah pertama",
            "langkah kedua",
            "langkah ketiga",
            "tahap pertama",
            "tahap kedua",
            "tahap ketiga",
            "selanjutnya",
            "kemudian",
            "setelah itu",
            "sebelum itu",
        )

        return value.startswith(procedure_prefixes)

    def _numeric_values_supported(
        self,
        sentence: str,
        evidence: str,
    ) -> bool:
        answer_numbers = set(
            re.findall(
                r"\b\d+(?:[.,]\d+)?\b",
                sentence,
            )
        )

        if not answer_numbers:
            return True

        evidence_numbers = set(
            re.findall(
                r"\b\d+(?:[.,]\d+)?\b",
                evidence,
            )
        )

        return answer_numbers.issubset(evidence_numbers)

    def _requirement_terms_supported(
        self,
        sentence: str,
        evidence: str,
    ) -> bool:
        sentence_terms = (
            self._content_tokens(sentence)
            & self.REQUIREMENT_MARKERS
        )

        if not sentence_terms:
            return True

        evidence_terms = self._content_tokens(evidence)

        # At least one requirement concept must be explicitly present.
        return bool(sentence_terms & evidence_terms)

    def _procedure_terms_supported(
        self,
        sentence: str,
        evidence: str,
    ) -> bool:
        """
        Procedure claims require procedural vocabulary to exist
        explicitly in the evidence.

        Topic similarity alone is insufficient.

        Example:
            Evidence: "KTP-el adalah dokumen identitas penduduk."
            Answer: "Langkah pertama adalah mengisi formulir."

        Result:
            False
        """

        sentence_tokens = self._content_tokens(sentence)
        evidence_tokens = self._content_tokens(evidence)

        procedure_terms = (
            sentence_tokens & self.PROCEDURE_MARKERS
        )

        if not procedure_terms:
            return True

        evidence_procedure_terms = (
            evidence_tokens & self.PROCEDURE_MARKERS
        )

        if not evidence_procedure_terms:
            return False

        # Require the operational action vocabulary to overlap as well.
        operational_terms = {
            "mengisi",
            "isi",
            "datang",
            "membawa",
            "serahkan",
            "menyerahkan",
            "mengajukan",
            "pengajuan",
            "permohonan",
            "mendaftar",
            "pendaftaran",
            "verifikasi",
            "validasi",
            "mengambil",
            "ambil",
            "mencetak",
            "cetak",
        }

        sentence_actions = sentence_tokens & operational_terms

        if sentence_actions:
            evidence_actions = evidence_tokens & operational_terms

            if not sentence_actions.issubset(evidence_actions):
                return False

        return True

    def _evidence_covers_question(
        self,
        answer: str,
        evidence: str,
        question_type: str,
    ) -> bool:
        answer_tokens = self._content_tokens(answer)
        evidence_tokens = self._content_tokens(evidence)

        if not answer_tokens or not evidence_tokens:
            return False

        if question_type == "requirements":
            relevant = (
                answer_tokens
                & self.REQUIREMENT_MARKERS
            )

            # If the answer claims requirements, evidence must have
            # requirement vocabulary.
            if relevant:
                evidence_requirement_terms = (
                    evidence_tokens
                    & self.REQUIREMENT_MARKERS
                )

                if not evidence_requirement_terms:
                    return False

        overlap = len(
            answer_tokens & evidence_tokens
        ) / max(1, len(answer_tokens))

        return overlap >= 0.18

    # ========================================================
    # Sentence classification
    # ========================================================

    def _is_meta_sentence(self, sentence: str) -> bool:
        value = sentence.lower().strip()

        prefixes = (
            "berikut beberapa",
            "berikut adalah",
            "berikut ini",
            "sebagai berikut",
            "dengan demikian",
            "kesimpulannya",
        )

        return value.startswith(prefixes)

    def _substantive_sentences(
        self,
        sentences: Sequence[str],
    ) -> list[str]:
        return [
            sentence
            for sentence in sentences
            if len(self._content_tokens(sentence))
            >= self.min_sentence_tokens
        ]

    def _deduplicate(
        self,
        values: Iterable[str],
    ) -> list[str]:
        result = []
        seen = set()

        for value in values:
            normalized = value.strip().lower()

            if not normalized or normalized in seen:
                continue

            seen.add(normalized)
            result.append(value.strip())

        return result
