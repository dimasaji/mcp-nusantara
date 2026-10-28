"""
Entity Extractor untuk Bahasa Indonesia.

Mengekstrak entity dari teks: dokumen, nomor, tanggal, nama orang, organisasi, lokasi, etc.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Pattern

from app.language.schemas import EntityResult, EntityType


# Pola regex untuk entity umum Bahasa Indonesia
_PATTERNS: Dict[EntityType, List[Pattern[str]]] = {
    EntityType.DATE: [
        re.compile(r"\b\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}\b"),
        re.compile(r"\b\d{1,2}\s(?:januari|februari|maret|april|mei|jun|i|juni|juli|agustus|september|oktober|november|desember)\s\d{4}\b", re.IGNORECASE),
        re.compile(r"\b(?:januari|februari|maret|april|mei|jun|i|juni|juli|agustus|september|oktober|november|desember)\s\d{1,2},?\s\d{4}\b", re.IGNORECASE),
        re.compile(r"\b(?:kemarin|besok|hari ini|lusa|tgl)\b", re.IGNORECASE),
    ],
    EntityType.NUMBER: [
        re.compile(r"\b\d{16}\b"),  # NIK 16 digit
        re.compile(r"\b\d{1,3}(\.\d{3})*\b"),  # angka dengan titik ribuan
        re.compile(r"\b\d{1,2}(\.\d{3})*,\d{2}\b"),  # angka desimal Indo
        re.compile(r"\b\d{10,16}\b"),  # KTP, HP, dll
        re.compile(r"\b\d{11,16}\b"),  # telp/HP panjang
        re.compile(r"\b08[1-9]\d{6,9}\b"),  # HP Indonesia
    ],
    EntityType.DOCUMENT: [
        re.compile(r"\b(KTP|ktp|NIB|nik|NIK|KK|kk|KIA|kia|NPP|NPP|NPWP|npwp|SIM|sim|AKTA|akte|ijazah|Ijazah|SKCK|skck|STNK|stnk|KIR|kir|KKP|kkp)\b", re.IGNORECASE),
        re.compile(r"\b(dokumen|surat|sertifikat|kartu|pengantar|keterangan|domisili|akte|nikah|lahir|meninggal|pernikahan|pindah|domisili|pengantar kerja)\b", re.IGNORECASE),
    ],
    EntityType.PERSON: [
        re.compile(r"\b(saya|aku|gue|lo|lu|kami|kita|dia|beliau|ayah|bapak|ibu|wanita|pria|psrn|pasien|nasabah|customer|client)\b", re.IGNORECASE),
        re.compile(r"\bNama[:\s]+\w[\w\s]+", re.IGNORECASE),
    ],
    EntityType.ORGANIZATION: [
        re.compile(r"\b(kantor|instansi|lembaga|pemerintah|dept|deps|kemenkeu|Kementerian|kementerian|kelurahan|desa|kecamatan|kabupaten|provinsi|bank|perum|perumda|CV|Yayasan|fondasi|PT|PT\.|Ltd|Limited|Inc|Corp| Corporation)\b", re.IGNORECASE),
    ],
    EntityType.LOCATION: [
        re.compile(r"\b(di|ke|from|dari)\s+([A-Z][a-z]+(?:[\s-][A-Z][a-z]+)*)\b"),
        re.compile(r"\b(Provinsi|Jawa|Bali|Sumatra|Kalsel|Kaltim|Kalbar|Kalut|Sulut|Sulbar|Sulsel|Sultra|Jateng|Jabart|Jatim|DKI|DIY|Babel|aakhirisil)\b", re.IGNORECASE),
    ],
    EntityType.EMAIL: [
        re.compile(r"\b[\w\.-]+@[\w\.-]+\.\w{2,}\b"),
    ],
    EntityType.PHONE: [
        re.compile(r"\b(?:08|\+62|62)\d{8,12}\b"),
        re.compile(r"\b\d{3,4}[-.]\d{3,4}[-.]\d{3,4}\b"),
    ],
    EntityType.ID: [
        re.compile(r"\b(no\.?\s*)?(nik|NIK|nokk|kktp|no\s*kta|no\s*ktp|no\s*kk|no\s*kia|no\s*npp|no\s*npwp|no\s*sim)\b[:\s]*(\d{10,16})", re.IGNORECASE),
    ],
}


@dataclass
class EntityMatch:
    value: str
    entity_type: EntityType
    start: int
    end: int
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class EntityExtractor:
    """
    Ekstraksi entity dari teks Bahasa Indonesia.
    """

    def __init__(self) -> None:
        self.patterns = _PATTERNS

    def extract(self, text: str) -> EntityResult:
        """
        Ekstraksi semua entity dari teks.
        """
        if not text or not text.strip():
            return EntityResult(doc_id=None, text="", entities=[])

        entities: List[EntityMatch] = []
        seen_ranges: List[tuple[int, int]] = []

        for etype, patterns in self.patterns.items():
            for pattern in patterns:
                for m in pattern.finditer(text):
                    start, end = m.start(), m.end()
                    # Hindari overlap signifikan
                    if any(s <= end and e >= start for s, e in seen_ranges):
                        continue
                    seen_ranges.append((start, end))
                    value = m.group(0).strip()
                    confidence = 1.0 if len(value) >= 3 else 0.5
                    entities.append(EntityMatch(
                        value=value,
                        entity_type=etype,
                        start=start,
                        end=end,
                        confidence=confidence,
                    ))

        return EntityResult(doc_id=None, text=text, entities=entities)

    def extract_batch(self, texts: List[str]) -> List[EntityResult]:
        return [self.extract(t) for t in texts]


_default_extractor = EntityExtractor()


def extract_entities(text: str) -> EntityResult:
    """Shortcut ke extractor default."""
    return _default_extractor.extract(text)
