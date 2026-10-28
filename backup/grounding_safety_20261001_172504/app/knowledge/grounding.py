"""
Evidence Grounding Guard
========================
Menjaga agar jawaban LLM tetap berada dalam batas
evidence yang diberikan Knowledge Engine.

Versi:
- Aman untuk object Evidence maupun dictionary.
- Tidak menggunakan variabel global/free variable.
- Mendukung evidence kosong.
- Memiliki grounding instruction untuk Hermes/Ollama.
- Memiliki validasi berbasis token overlap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class GroundingResult:
    text: str
    grounded: bool
    reason: str
    unsupported_sentences: list[str]


class EvidenceGroundingGuard:
    """
    Guard untuk memastikan jawaban LLM tetap berdasarkan evidence.
    """

    FALLBACK_TEXT = (
        "Informasi tersebut belum tersedia dalam knowledge base."
    )

    MIN_WORD_LENGTH = 4
    MIN_COVERAGE = 0.20

    # Kata-kata umum yang tidak berguna untuk mengukur grounding.
    STOPWORDS = {
        "yang",
        "dan",
        "atau",
        "untuk",
        "dari",
        "dengan",
        "pada",
        "dalam",
        "adalah",
        "akan",
        "dapat",
        "bisa",
        "anda",
        "saya",
        "ini",
        "itu",
        "tersebut",
        "sebagai",
        "secara",
        "lebih",
        "sudah",
        "belum",
        "agar",
        "jika",
        "karena",
        "maka",
        "juga",
        "tidak",
        "telah",
        "oleh",
        "ke",
        "di",
        "se",
        "nya",
    }

    def build_grounded_context(
        self,
        evidence: list[Any] | None,
    ) -> str:
        """
        Mengubah evidence menjadi context yang aman untuk prompt LLM.
        """

        if not evidence:
            return (
                "TIDAK ADA EVIDENCE.\n"
                "Jangan membuat fakta dari pengetahuan model."
            )

        blocks: list[str] = []

        for index, evidence_item in enumerate(
            evidence,
            start=1,
        ):
            title = self._get_value(
                evidence_item,
                "title",
            )

            source = self._get_value(
                evidence_item,
                "source",
            )

            chunk = self._get_value(
                evidence_item,
                "chunk",
            )

            content = (
                str(chunk).strip()
                if chunk
                else str(source).strip()
            )

            blocks.append(
                f"[EVIDENCE {index}]\n"
                f"Judul: {title}\n"
                f"Isi: {content}"
            )

        if not blocks:
            return (
                "TIDAK ADA EVIDENCE.\n"
                "Jangan membuat fakta dari pengetahuan model."
            )

        return "\n\n".join(blocks)

    def build_system_instruction(self) -> str:
        """
        Instruksi grounding untuk Hermes/Ollama.
        """

        return """
ATURAN GROUNDING NUSANTARA AI:

1. Jawaban HARUS berdasarkan evidence yang diberikan.
2. Gunakan evidence sebagai sumber informasi utama.
3. Jangan menambahkan fakta yang tidak didukung evidence.
4. Jangan menggunakan pengetahuan umum model sebagai sumber fakta.
5. Jangan membuat prosedur, persyaratan, biaya, waktu, alamat,
   instansi, nomor, aturan, atau ketentuan yang tidak terdapat
   dalam evidence.
6. Evidence prosedural bukan bukti bahwa data pribadi pengguna
   sudah tersedia.
7. Jangan mengklaim telah mengecek status pribadi pengguna
   jika sistem tidak benar-benar memiliki data tersebut.
8. Jika evidence tidak cukup untuk menjawab pertanyaan,
   katakan:
   "Informasi tersebut belum tersedia dalam knowledge base."
9. Jangan menyangkal informasi yang secara jelas terdapat
   dalam evidence.
10. Jawab dalam bahasa pengguna.
11. Jawab singkat, jelas, dan langsung.
""".strip()

    def validate(
        self,
        answer: str | None,
        evidence: list[Any] | None,
    ) -> GroundingResult:
        """
        Memeriksa apakah jawaban mempunyai dukungan token
        yang memadai dari evidence.

        Ini adalah guard sederhana, bukan semantic entailment penuh.
        """

        answer_text = str(answer or "").strip()

        if not answer_text:
            return GroundingResult(
                text=self.FALLBACK_TEXT,
                grounded=False,
                reason="empty_answer",
                unsupported_sentences=[],
            )

        if not evidence:
            return GroundingResult(
                text=self.FALLBACK_TEXT,
                grounded=False,
                reason="no_evidence",
                unsupported_sentences=[answer_text],
            )

        evidence_text = self._build_evidence_text(
            evidence
        )

        if not evidence_text:
            return GroundingResult(
                text=self.FALLBACK_TEXT,
                grounded=False,
                reason="empty_evidence_content",
                unsupported_sentences=[answer_text],
            )

        sentences = self._split_sentences(
            answer_text
        )

        unsupported: list[str] = []

        for sentence in sentences:
            normalized_sentence = self._normalize(
                sentence
            )

            if not normalized_sentence:
                continue

            words = self._meaningful_words(
                normalized_sentence
            )

            if not words:
                continue

            matched_words = sum(
                1
                for word in words
                if word in evidence_text
            )

            coverage = (
                matched_words / len(words)
            )

            if coverage < self.MIN_COVERAGE:
                unsupported.append(
                    sentence
                )

        if unsupported:
            return GroundingResult(
                text=answer_text,
                grounded=False,
                reason="possible_unsupported_content",
                unsupported_sentences=unsupported,
            )

        return GroundingResult(
            text=answer_text,
            grounded=True,
            reason="grounded",
            unsupported_sentences=[],
        )

    def _build_evidence_text(
        self,
        evidence: list[Any],
    ) -> str:
        """
        Menggabungkan seluruh isi evidence.
        """

        parts: list[str] = []

        for evidence_item in evidence:
            chunk = self._get_value(
                evidence_item,
                "chunk",
            )

            source = self._get_value(
                evidence_item,
                "source",
            )

            title = self._get_value(
                evidence_item,
                "title",
            )

            if chunk:
                parts.append(str(chunk))

            if source:
                parts.append(str(source))

            if title:
                parts.append(str(title))

        return self._normalize(
            " ".join(parts)
        )

    def _meaningful_words(
        self,
        normalized_text: str,
    ) -> list[str]:
        """
        Mengambil kata bermakna untuk pemeriksaan overlap.
        """

        words: list[str] = []

        for word in normalized_text.split():
            if len(word) < self.MIN_WORD_LENGTH:
                continue

            if word in self.STOPWORDS:
                continue

            words.append(word)

        return words

    @staticmethod
    def _get_value(
        evidence_item: Any,
        field_name: str,
    ) -> Any:
        """
        Mendukung object dataclass/Pydantic maupun dictionary.
        """

        if evidence_item is None:
            return ""

        if isinstance(
            evidence_item,
            dict,
        ):
            return evidence_item.get(
                field_name,
                "",
            )

        return getattr(
            evidence_item,
            field_name,
            "",
        )

    @staticmethod
    def _normalize(
        text: str,
    ) -> str:
        """
        Normalisasi teks untuk pencocokan.
        """

        text = str(text or "").lower()

        text = re.sub(
            r"[^a-z0-9\s-]",
            " ",
            text,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    @staticmethod
    def _split_sentences(
        text: str,
    ) -> list[str]:
        """
        Memecah jawaban menjadi kalimat.
        """

        parts = re.split(
            r"(?<=[.!?])\s+",
            str(text or "").strip(),
        )

        return [
            part.strip()
            for part in parts
            if part.strip()
        ]


__all__ = [
    "GroundingResult",
    "EvidenceGroundingGuard",
]
