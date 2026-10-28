"""Grounding gate (workflow #17, #20): tandai klaim jawaban yang TIDAK didukung source.
Heuristik leksikal per kalimat; kalimat bernegasi ("tidak ada print()") dilewati. Bukan bukti kebenaran."""
from __future__ import annotations

import re
from dataclasses import dataclass

_NEG = re.compile(r"\b(tidak|bukan|tanpa|belum|tak|no|not|without|tiada)\b", re.I)
_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_EXT_URL = re.compile(r"https?://(?!127\.|localhost|0\.0\.0\.0|\[::1\])", re.I)

# (nama_rule, klaim_di_jawaban, bukti_di_source)
_RULES = [
    ("print/menampilkan hasil",
     re.compile(r"\bprint\b|mencetak|menampilkan (?:hasil|output|response|respons|isi)|tampilkan hasil|ke (?:layar|konsol)", re.I),
     re.compile(r"\bprint\s*\(|sys\.stdout|logging\.|logger\.")),
    ("retry/pengulangan",
     re.compile(r"\bretry\b|mencoba ulang|coba ulang|percobaan ulang", re.I),
     re.compile(r"retry|\bfor\b.+\bin\b|\bwhile\b|backoff|attempt", re.I)),
    ("penyimpanan response/file",
     re.compile(r"menyimpan|\bsimpan\b|menulis (?:ke )?(?:file|disk)", re.I),
     re.compile(r"\bopen\s*\(|\.write|\.dump|\bsave\b|sqlite|\.commit\(", re.I)),
    ("penanganan error",
     re.compile(r"menangani (?:error|exception|kesalahan)|penanganan (?:error|kesalahan)|try[- ]except", re.I),
     re.compile(r"\btry\b|\bexcept\b")),
]
_TIMEOUT_CLAIM = re.compile(r"timeout\D{0,20}?(\d+(?:[.,]\d+)?)", re.I)
_TIMEOUT_SRC = re.compile(r"timeout\s*[=:]\s*(\d+(?:\.\d+)?)", re.I)
_INTERNET = re.compile(r"internet|situs (?:web )?eksternal|server eksternal|layanan eksternal|remote server", re.I)


@dataclass
class Violation:
    rule: str
    sentence: str


def _num(s: str) -> float:
    return float(s.replace(",", "."))


def check_grounding(answer: str, source: str) -> list[Violation]:
    out: list[Violation] = []
    src_timeouts = {_num(m) for m in _TIMEOUT_SRC.findall(source)}
    for sent in (s.strip() for s in _SPLIT.split(answer)):
        if not sent or _NEG.search(sent):
            continue
        for name, claim, evidence in _RULES:
            if claim.search(sent) and not evidence.search(source):
                out.append(Violation(name, sent[:200]))
        if _INTERNET.search(sent) and not _EXT_URL.search(source):
            out.append(Violation("pengecekan internet/host eksternal", sent[:200]))
        for m in _TIMEOUT_CLAIM.findall(sent):
            if _num(m) not in src_timeouts:
                out.append(Violation("nilai timeout tidak sesuai source", sent[:200]))
    return out
