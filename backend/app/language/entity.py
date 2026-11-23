"""
Nusantara Language Engine - Entity Extraction.

Rule-based entity extractor yang:
- ringan untuk CPU
- deterministic
- aman untuk pipeline LanguageEngine
- kompatibel dengan EntityResult pada schemas.py
- dapat dikembangkan menjadi hybrid Rule + IndoBERT/NLP model

Entity yang didukung:
- DOCUMENT
- NIK / ID
- PERSON
- DATE
- PHONE
- LOCATION
- EMAIL
- NUMBER
- ORGANIZATION
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.language.schemas import EntityResult


# ============================================================
# ENTITY MATCH RESULT
# ============================================================


@dataclass
class EntityMatch:
    """Entity internal sebelum dikonversi menjadi EntityResult."""

    value: str
    entity_type: str
    start: int
    end: int
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "value": self.value,
            "entity_type": self.entity_type,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "metadata": self.metadata,
        }


# ============================================================
# CONSTANTS
# ============================================================


DOCUMENT_PATTERNS = {
    "KTP": "document",
    "KTP-EL": "document",
    "KK": "document",
    "KIA": "document",
    "AKTA": "document",
    "AKTA KEMATIAN": "document",
    "AKTA KELAHIRAN": "document",
    "AKTA PERKAWINAN": "document",
    "AKTA PERCERAIAN": "document",
    "SKCK": "document",
    "SIM": "document",
    "STNK": "document",
    "NPWP": "document",
    "NIB": "document",
    "IJAZAH": "document",
    "SERTIFIKAT": "document",
    "PASPOR": "document",
    "SURAT KETERANGAN": "document",
}

# Kata ganti yang JANGAN pernah dianggap sebagai nama/person.
PRONOUNS = {
    "saya",
    "aku",
    "kami",
    "kita",
    "anda",
    "kamu",
    "dia",
    "mereka",
    "beliau",
    "nya",
    "ku",
    "mu",
}

# Kata umum yang tidak boleh menjadi PERSON.
PERSON_STOPWORDS = PRONOUNS | {
    "yang",
    "ini",
    "itu",
    "mau",
    "ingin",
    "tolong",
    "bisa",
    "tidak",
    "sudah",
    "belum",
    "akan",
    "untuk",
    "dari",
    "dengan",
    "pada",
    "dalam",
    "cek",
    "status",
    "dokumen",
    "pengurusan",
    "pengajuan",
    "permohonan",
    "syarat",
    "aplikasi",
    "admin",
    "operator",
}

# Kata yang sering muncul setelah label nama.
NAME_LABELS = (
    "nama",
    "atas nama",
    "a.n",
    "an",
)


# ============================================================
# REGEX
# ============================================================


EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)

PHONE_RE = re.compile(
    r"(?<!\d)(?:\+62|62|0)8\d{7,12}(?!\d)"
)

NIK_RE = re.compile(
    r"(?<!\d)\d{16}(?!\d)"
)

# Tanggal Indonesia:
# 15/08/1986
# 15-08-1986
# 15.08.1986
DATE_NUMERIC_RE = re.compile(
    r"(?<!\d)(?:0?[1-9]|[12]\d|3[01])"
    r"[\/\-.]"
    r"(?:0?[1-9]|1[0-2])"
    r"[\/\-.]"
    r"(?:19|20)\d{2}(?!\d)"
)

DATE_TEXT_RE = re.compile(
    r"\b(?:"
    r"\d{1,2}\s+"
    r"(?:januari|februari|maret|april|mei|juni|juli|agustus|"
    r"september|oktober|november|desember)"
    r"(?:\s+\d{4})?"
    r")\b",
    re.IGNORECASE,
)

NUMBER_RE = re.compile(
    r"(?<![\w])\d+(?:[.,]\d+)?(?![\w])"
)


# ============================================================
# ENTITY EXTRACTOR
# ============================================================


class EntityExtractor:
    """
    Entity extractor untuk Nusantara Language Engine.

    Urutan ekstraksi:
    1. Email
    2. Phone
    3. NIK
    4. Document
    5. Date
    6. Person
    7. Number

    Entity yang sudah dikenali dilindungi agar tidak
    terdeteksi ulang sebagai entity lain.
    """

    def __init__(self) -> None:
        self.document_patterns = sorted(
            DOCUMENT_PATTERNS.keys(),
            key=len,
            reverse=True,
        )

    # ========================================================
    # PUBLIC API
    # ========================================================

    def extract(self, text: str) -> EntityResult:
        """
        Ekstraksi entity dari teks.

        Return selalu EntityResult sehingga kompatibel
        dengan LanguageEngine.
        """

        if not isinstance(text, str):
            text = "" if text is None else str(text)

        if not text.strip():
            return EntityResult(
                entities=[],
                confidence=0.0,
                raw_matches=[],
                text=text,
            )

        matches: List[EntityMatch] = []
        occupied: List[tuple[int, int]] = []

        # Prioritas entity
        self._extract_regex(
            text,
            EMAIL_RE,
            "email",
            matches,
            occupied,
            confidence=1.0,
        )

        self._extract_regex(
            text,
            PHONE_RE,
            "phone",
            matches,
            occupied,
            confidence=1.0,
        )

        self._extract_regex(
            text,
            NIK_RE,
            "nik",
            matches,
            occupied,
            confidence=1.0,
        )

        self._extract_documents(
            text,
            matches,
            occupied,
        )

        self._extract_dates(
            text,
            matches,
            occupied,
        )

        self._extract_persons(
            text,
            matches,
            occupied,
        )

        self._extract_numbers(
            text,
            matches,
            occupied,
        )

        matches = self._deduplicate(matches)

        # Urutkan berdasarkan posisi di teks.
        matches.sort(key=lambda x: (x.start, x.end))

        entities = [m.to_dict() for m in matches]

        if matches:
            confidence = sum(m.confidence for m in matches) / len(matches)
        else:
            confidence = 0.0

        return EntityResult(
            entities=entities,
            confidence=round(confidence, 3),
            raw_matches=[],
            text=text,
        )

    # ========================================================
    # REGEX EXTRACTION
    # ========================================================

    def _extract_regex(
        self,
        text: str,
        pattern: re.Pattern[str],
        entity_type: str,
        matches: List[EntityMatch],
        occupied: List[tuple[int, int]],
        confidence: float = 1.0,
    ) -> None:

        for match in pattern.finditer(text):
            start = match.start()
            end = match.end()

            if self._overlaps(start, end, occupied):
                continue

            value = match.group(0).strip()

            if not value:
                continue

            entity = EntityMatch(
                value=value,
                entity_type=entity_type,
                start=start,
                end=end,
                confidence=confidence,
            )

            matches.append(entity)
            occupied.append((start, end))

    # ========================================================
    # DOCUMENT
    # ========================================================

    def _extract_documents(
        self,
        text: str,
        matches: List[EntityMatch],
        occupied: List[tuple[int, int]],
    ) -> None:

        upper_text = text.upper()

        for document in self.document_patterns:
            pattern = re.compile(
                rf"(?<![A-Z0-9]){re.escape(document)}(?![A-Z0-9])",
                re.IGNORECASE,
            )

            for match in pattern.finditer(upper_text):
                start = match.start()
                end = match.end()

                if self._overlaps(start, end, occupied):
                    continue

                value = text[start:end]

                matches.append(
                    EntityMatch(
                        value=value.upper(),
                        entity_type="document",
                        start=start,
                        end=end,
                        confidence=1.0,
                        metadata={
                            "document_type": document.lower(),
                        },
                    )
                )

                occupied.append((start, end))

    # ========================================================
    # DATE
    # ========================================================

    def _extract_dates(
        self,
        text: str,
        matches: List[EntityMatch],
        occupied: List[tuple[int, int]],
    ) -> None:

        for pattern in (DATE_NUMERIC_RE, DATE_TEXT_RE):
            for match in pattern.finditer(text):
                start = match.start()
                end = match.end()

                if self._overlaps(start, end, occupied):
                    continue

                matches.append(
                    EntityMatch(
                        value=match.group(0),
                        entity_type="date",
                        start=start,
                        end=end,
                        confidence=0.98,
                    )
                )

                occupied.append((start, end))

    # ========================================================
    # PERSON
    # ========================================================

    def _extract_persons(
        self,
        text: str,
        matches: List[EntityMatch],
        occupied: List[tuple[int, int]],
    ) -> None:
        """
        Ekstraksi nama sederhana.

        Sengaja konservatif.

        Kita TIDAK menganggap semua kata kapital sebagai PERSON,
        karena Bahasa Indonesia banyak menggunakan kapital untuk
        dokumen seperti KTP, KK, NIK, dll.

        Untuk tahap rule-based, nama hanya dideteksi pada pola:

            nama Budi
            nama: Budi
            atas nama Budi
            a.n. Budi

        IndoBERT/NER dapat ditambahkan kemudian untuk pola
        nama yang lebih kompleks.
        """

        # Pola:
        # nama Budi
        # nama: Budi
        # atas nama Budi
        # a.n. Budi
        pattern = re.compile(
            r"\b(?:nama|atas\s+nama|a\.n\.?|an)\s*[:\-]?\s*"
            r"([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+){0,3})"
        )

        for match in pattern.finditer(text):
            value = match.group(1).strip()

            if not value:
                continue

            # Jangan ambil pronoun / stopword.
            words = {
                word.lower()
                for word in value.split()
            }

            if words & PERSON_STOPWORDS:
                continue

            start = match.start(1)
            end = match.end(1)

            if self._overlaps(start, end, occupied):
                continue

            matches.append(
                EntityMatch(
                    value=value,
                    entity_type="person",
                    start=start,
                    end=end,
                    confidence=0.90,
                    metadata={
                        "source": "name_pattern",
                    },
                )
            )

            occupied.append((start, end))

    # ========================================================
    # NUMBER
    # ========================================================

    def _extract_numbers(
        self,
        text: str,
        matches: List[EntityMatch],
        occupied: List[tuple[int, int]],
    ) -> None:

        for match in NUMBER_RE.finditer(text):
            start = match.start()
            end = match.end()

            if self._overlaps(start, end, occupied):
                continue

            value = match.group(0)

            # Hindari angka yang sebenarnya bagian dari
            # nomor telepon / NIK / tanggal.
            if self._looks_like_id_context(text, start, end):
                continue

            matches.append(
                EntityMatch(
                    value=value,
                    entity_type="number",
                    start=start,
                    end=end,
                    confidence=0.95,
                )
            )

            occupied.append((start, end))

    # ========================================================
    # HELPERS
    # ========================================================

    @staticmethod
    def _overlaps(
        start: int,
        end: int,
        occupied: List[tuple[int, int]],
    ) -> bool:

        for existing_start, existing_end in occupied:
            if start < existing_end and end > existing_start:
                return True

        return False

    @staticmethod
    def _looks_like_id_context(
        text: str,
        start: int,
        end: int,
    ) -> bool:

        # Jika angka 16 digit, sudah seharusnya ditangkap NIK.
        value = text[start:end]

        if len(re.sub(r"\D", "", value)) == 16:
            return True

        # Cek konteks sekitar.
        context_start = max(0, start - 5)
        context_end = min(len(text), end + 5)
        context = text[context_start:context_end].lower()

        if "nik" in context:
            return True

        if "telp" in context:
            return True

        if "telepon" in context:
            return True

        if "wa" in context:
            return True

        return False

    @staticmethod
    def _deduplicate(
        matches: List[EntityMatch],
    ) -> List[EntityMatch]:

        result: List[EntityMatch] = []

        seen = set()

        for match in matches:
            key = (
                match.start,
                match.end,
                match.entity_type,
                match.value.lower(),
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(match)

        return result


# ============================================================
# PUBLIC FACTORY
# ============================================================


def create_entity_extractor() -> EntityExtractor:
    """Factory untuk membuat EntityExtractor."""
    return EntityExtractor()


# ============================================================
# MANUAL TEST
# ============================================================


if __name__ == "__main__":

    extractor = EntityExtractor()

    examples = [
        "Saya mau cek status KTP saya",
        "NIK saya 3671234567890123",
        "Nomor HP saya 081234567890",
        "Email saya dimas@example.com",
        "Tanggal lahir saya 15 Agustus 1986",
        "Nama: Dimas Aji Kurnia",
        "Atas nama Budi Santoso",
        "Saya mau mengurus KK",
    ]

    print("=" * 70)
    print("NUSANTARA LANGUAGE ENGINE - ENTITY TEST")
    print("=" * 70)

    for text in examples:
        result = extractor.extract(text)

        print()
        print(f"INPUT: {text}")

        for entity in result.entities:
            print(
                f"  {entity['entity_type']:15} "
                f"{entity['value']!r:30} "
                f"confidence={entity['confidence']}"
            )

    print()
    print("=" * 70)
# ============================================================
# LEGACY COMPATIBILITY API
# ============================================================

def extract_entities(text: str):
    """
    Backward-compatible wrapper untuk evaluation/test lama.

    API baru:
        create_entity_extractor().extract(text)

    API legacy:
        extract_entities(text)

    Return:
        EntityResult
    """
    return create_entity_extractor().extract(text)

