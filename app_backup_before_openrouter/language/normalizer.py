"""
Text Normalizer untuk Bahasa Indonesia.

Menangani: singkatan umum, typo, informal speech, repetisi, kapitalisasi, whitespace.
"""
from __future__ import annotations

import re
from typing import List, Optional

from app.language.schemas import NormalizeResult


# Kamus singkatan umum Bahasa Indonesia (informal/chat) ke bentuk baku
# Sumber: observasi umum chat Indonesia, not exhaustive
_ABBREVIATIONS: dict[str, str] = {
    # Pronoun/informal
    " gw ": " saya ",
    "gue": "saya",
    " lo ": " kamu ",
    "loh": "kamu",
    " lu ": " kamu ",
    "kmu": "kamu",
    "km": "kamu",
    "kita": "kita",
    "kta": "kita",
    "sy": "saya",
    "sya": "saya",
    "aku": "aku",
    "ak": "aku",
    # Negasi
    "gak": "tidak",
    "ga": "tidak",
    "gk": "tidak",
    "nggak": "tidak",
    "ngga": "tidak",
    "ngak": "tidak",
    "g": "tidak",  # Hati-hati: bisa juga 'g' sebagai huruf, tapi di context chat biasanya 'tidak'
    "tdk": "tidak",
    "tdak": "tidak",
    # Kata sambung/keterangan
    "krn": "karena",
    "krna": "karena",
    "karna": "karena",
    "dri": "dari",
    "dr": "dari",
    "utk": "untuk",
    "untk": "untuk",
    "buat": "untuk",  # Kadang 'buat' dipakai = 'untuk'
    "sbg": "sebagai",
    "bg": "banget",
    "bgt": "banget",
    "bngt": "banget",
    "jg": "jangan",
    "jgn": "jangan",
    "jga": "jangan",
    "aja": "saja",
    "ajah": "saja",
    "aj": "saja",
    "bd": "bisa",
    "bs": "bisa",
    "bgh": "bisa",
    # Nomer/time
    "kming": "kemarin",
    "kmrn": "kemarin",
    "lusa": "lusa",
    "besok": "besok",
    "skrng": "sekarang",
    "skr": "sekarang",
    "blm": "belum",
    "blum": "belum",
    "udh": "sudah",
    "udah": "sudah",
    "msh": "masih",
    "msh": "masih",
    "lagi": "lagi",
    "lg": "lagi",
    # Noun/verb informal
    "mn": "minum",
    "mkn": "makan",
    "mknan": "makanan",
    "skli": "sekali",
    "sl": "sekali",
    "gk": "ga",
}


# Kamus typo umum / kesalahan ketik
_TYPO_FIXES: dict[str, str] = {
    "karpet": "karpet",  # typo? actually correct
    "kartu": "kartu",
    "ktp": "KTP",
    "kk": "KK",
    "niik": "NIK",
    "npwp": "NPWP",
    "sim": "SIM",
    "ktp": "KTP",
    "herst": "Hermes",
    "hermes": "Hermes",
    "dokumen": "dokumen",
    "dokum": "dokumen",
    "surat": "surat",
    "sertifikat": "sertifikat",
    "ijazah": "ijazah",
    "kartu": "kartu",
    "keluarga": "keluarga",
    "pengantar": "pengantar",
    "keterangan": "keterangan",
    "pengurusan": "pengurusan",
    "pengajuan": "pengajuan",
    # Digit/typo
    "n0": "no",
    "nol": "no",
    "em": "en",
    "emang": "emang",  # slang, keep
}


# Pattern: huruf berulang >2 menjadi 2 (contoh: "sayaassss" -> "sayaas")
_REPEAT_PATTERN = re.compile(r"(.)\1{2,}")

# Pattern: whitespace berlebih
_WHITESPACE_PATTERN = re.compile(r"\s+")

# Pattern: strip tanda baca berlebih di awal/akhir kalimat
_PUNCTUATION_STRIP = re.compile(r"^[^\w\s]+|[^\w\s]+$", re.UNICODE)


class TextNormalizer:
    """
    Normalisasi teks masuk: lowercase, rapikan spasi, perbaiki singkatan/typo umum.
    """

    def __init__(self, abbreviations: Optional[dict[str, str]] = None, typo_fixes: Optional[dict[str, str]] = None) -> None:
        self.abbreviations = abbreviations or _ABBREVIATIONS
        self.typo_fixes = typo_fixes or _TYPO_FIXES

    def normalize(self, text: str) -> NormalizeResult:
        """
        Return NormalizeResult dengan teks original, normalized, dan list perubahan.
        """
        original = text
        changes: List[str] = []

        if not isinstance(text, str) or not text.strip():
            return NormalizeResult(original=original or "", normalized="", changes=["empty input"])

        # 1. Lowercase sementara untuk matching
        lowered = text.lower()

        # 2. Ganti singkatan
        normalized = lowered
        for abbr, fix in sorted(self.abbreviations.items(), key=lambda x: -len(x[0])):
            if abbr in normalized:
                count = normalized.count(abbr)
                normalized = normalized.replace(abbr, fix)
                changes.append(f"abbr: {abbr.strip()!r} -> {fix.strip()!r} (x{count})")

        # 3. Ganti typo
        for typo, fix in sorted(self.typo_fixes.items(), key=lambda x: -len(x[0])):
            if typo in normalized:
                count = normalized.count(typo)
                normalized = normalized.replace(typo, fix)
                changes.append(f"typo: {typo!r} -> {fix!r} (x{count})")

        # 4. Rapikan repetisi
        before = normalized
        normalized = _REPEAT_PATTERN.sub(r"\1\1", normalized)
        if normalized != before:
            changes.append("reduce_repeated_chars")

        # 5. Rapikan whitespace
        before = normalized
        normalized = _WHITESPACE_PATTERN.sub(" ", normalized).strip()
        if normalized != before:
            changes.append("normalize_whitespace")

        # 6. Potong tanda baca berlebih di ujung (hati-hati jangan hapus semua)
        before = normalized
        normalized = _PUNCTUATION_STRIP.sub("", normalized).strip()
        if normalized != before:
            changes.append("trim_surrounding_punctuation")

        # 7. Capitalize huruf pertama kalimat (opsional, biar konsisten)
        #    Tapi untuk NLP chain aslinya biasanya lowercase dulu, jadi skip capitalization
        #    kecuali user minta.

        if not normalized:
            normalized = ""
            changes.append("result_empty_after_normalize")

        return NormalizeResult(original=original, normalized=normalized, changes=changes)

    def normalize_batch(self, texts: List[str]) -> List[NormalizeResult]:
        return [self.normalize(t) for t in texts]


_default_normalizer = TextNormalizer()


def normalize_text(text: str) -> NormalizeResult:
    """Shortcut ke normalizer default."""
    return _default_normalizer.normalize(text)
