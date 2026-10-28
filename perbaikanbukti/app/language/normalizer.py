"""
Text Normalizer untuk Bahasa Indonesia.

Menangani: singkatan umum, typo, informal speech, repetisi, kapitalisasi, whitespace.

Prinsip: preserve meaning > aggressive correction. Semua penggantian berbasis
TOKEN (word-boundary), bukan substring, sehingga kata seperti "singkat" atau
"bagaimana" tidak pernah rusak. Email/URL dan token yang berisi angka (NIK, HP)
dilindungi dari penggantian.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Pattern, Tuple

from app.language.schemas import NormalizeResult


# Kamus singkatan umum Bahasa Indonesia (informal/chat) ke bentuk baku.
# Key disimpan sebagai TOKEN (tanpa spasi literal); pencocokan memakai word-boundary.
# Sengaja TIDAK memuat rule yang bisa mengubah makna (mis. "g", "buat", "loh").
_ABBREVIATIONS: dict[str, str] = {
    # Pronoun/informal
    "gw": "saya",
    "gue": "saya",
    "lo": "kamu",
    "lu": "kamu",
    "kmu": "kamu",
    "km": "kamu",
    "kta": "kita",
    "sy": "saya",
    "sya": "saya",
    "ak": "aku",
    # Negasi
    "gak": "tidak",
    "ga": "tidak",
    "gk": "tidak",
    "nggak": "tidak",
    "ngga": "tidak",
    "ngak": "tidak",
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
    "sbg": "sebagai",
    "bgt": "banget",
    "bngt": "banget",
    "jg": "juga",
    "jga": "juga",
    "jgn": "jangan",
    "aja": "saja",
    "ajah": "saja",
    "aj": "saja",
    "bs": "bisa",
    # Waktu
    "kming": "kemarin",
    "kmrn": "kemarin",
    "skrng": "sekarang",
    "skr": "sekarang",
    "blm": "belum",
    "blum": "belum",
    "udh": "sudah",
    "udah": "sudah",
    "msh": "masih",
    "lg": "lagi",
    # Noun/verb informal
    "mkn": "makan",
    "mknan": "makanan",
    "skli": "sekali",
}


# Kamus typo umum + token domain (dokumen) yang ditulis konsisten.
_TYPO_FIXES: dict[str, str] = {
    # Token domain
    "ktp": "KTP",
    "kk": "KK",
    "nik": "NIK",
    "niik": "NIK",
    "npwp": "NPWP",
    "sim": "SIM",
    "nib": "NIB",
    "kia": "KIA",
    "stnk": "STNK",
    "skck": "SKCK",
    # Typo
    "dokum": "dokumen",
    "herst": "Hermes",
    "hermes": "Hermes",
    "n0": "no",
}


# Pattern: karakter berulang >2 menjadi 2 (contoh: "sayaaaa" -> "sayaa")
_REPEAT_PATTERN = re.compile(r"(.)\1{2,}")

# Pattern: whitespace berlebih
_WHITESPACE_PATTERN = re.compile(r"\s+")

# Tanda baca di awal / akhir teks
_LEADING_PUNCT = re.compile(r"^[^\w\s]+", re.UNICODE)
_TRAILING_PUNCT = re.compile(r"[^\w\s]+$", re.UNICODE)

_NON_SPACE = re.compile(r"\S+")

# Bagian teks yang tidak boleh disentuh penggantian kata (email, URL)
_PROTECTED = r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+|https?://\S+|www\.\S+"


def _compile_token_map(mapping: Dict[str, str]) -> Tuple[Optional[Pattern[str]], Dict[str, str]]:
    """
    Kompilasi kamus jadi satu regex word-boundary.

    Key dinormalkan (strip + lowercase) sehingga key berspasi seperti " gw "
    tetap bekerja tanpa bergantung pada spasi literal. Entri identitas dibuang.
    """
    table: Dict[str, str] = {}
    for key, value in mapping.items():
        k = key.strip().lower()
        v = value.strip()
        if k and k != v:
            table[k] = v
    if not table:
        return None, table
    alternation = "|".join(re.escape(k) for k in sorted(table, key=lambda x: (-len(x), x)))
    regex = re.compile(
        rf"(?P<prot>{_PROTECTED})|(?<!\w)(?P<tok>{alternation})(?!\w)",
        re.IGNORECASE,
    )
    return regex, table


def _apply_token_map(
    regex: Optional[Pattern[str]],
    table: Dict[str, str],
    text: str,
    label: str,
    changes: List[str],
) -> str:
    if regex is None:
        return text
    counts: Dict[str, int] = {}

    def _repl(m: "re.Match[str]") -> str:
        tok = m.group("tok")
        if tok is None:  # bagian terlindungi (email/URL)
            return m.group(0)
        key = tok.lower()
        counts[key] = counts.get(key, 0) + 1
        return table[key]

    result = regex.sub(_repl, text)
    for key, n in counts.items():
        changes.append(f"{label}: {key!r} -> {table[key]!r} (x{n})")
    return result


def _reduce_repeats(text: str) -> str:
    """Kurangi karakter berulang, tetapi jangan sentuh token berisi angka/email/URL (NIK, HP, dll)."""

    def _repl(m: "re.Match[str]") -> str:
        tok = m.group(0)
        if any(c.isdigit() for c in tok) or "@" in tok or "://" in tok or tok.startswith("www."):
            return tok
        return _REPEAT_PATTERN.sub(r"\1\1", tok)

    return _NON_SPACE.sub(_repl, text)


class TextNormalizer:
    """
    Normalisasi teks masuk: lowercase, rapikan spasi, perbaiki singkatan/typo umum.
    """

    def __init__(self, abbreviations: Optional[dict[str, str]] = None, typo_fixes: Optional[dict[str, str]] = None) -> None:
        self.abbreviations = abbreviations or _ABBREVIATIONS
        self.typo_fixes = typo_fixes or _TYPO_FIXES
        self._abbr_regex, self._abbr_table = _compile_token_map(self.abbreviations)
        self._typo_regex, self._typo_table = _compile_token_map(self.typo_fixes)

    def normalize(self, text: str) -> NormalizeResult:
        """
        Return NormalizeResult dengan teks original, normalized, dan list perubahan.
        """
        original = text
        changes: List[str] = []

        if not isinstance(text, str) or not text.strip():
            return NormalizeResult(original=original or "", normalized="", changes=["empty input"])

        # 1. Lowercase sementara untuk matching
        normalized = text.lower()

        # 2. Ganti singkatan (token-based)
        normalized = _apply_token_map(self._abbr_regex, self._abbr_table, normalized, "abbr", changes)

        # 3. Ganti typo / token domain (token-based)
        normalized = _apply_token_map(self._typo_regex, self._typo_table, normalized, "typo", changes)

        # 4. Rapikan repetisi (token berisi angka/email/URL dilewati)
        before = normalized
        normalized = _reduce_repeats(normalized)
        if normalized != before:
            changes.append("reduce_repeated_chars")

        # 5. Rapikan whitespace
        before = normalized
        normalized = _WHITESPACE_PATTERN.sub(" ", normalized).strip()
        if normalized != before:
            changes.append("normalize_whitespace")

        # 6. Potong tanda baca di ujung; '?' dan '!' penutup kalimat dipertahankan
        before = normalized
        normalized = _LEADING_PUNCT.sub("", normalized).strip()
        m = _TRAILING_PUNCT.search(normalized)
        if m:
            run = m.group(0)
            keep = "?" if "?" in run else ("!" if "!" in run else "")
            normalized = (normalized[: m.start()].rstrip() + keep).strip()
        if normalized != before:
            changes.append("trim_surrounding_punctuation")

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
