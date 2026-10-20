"""Grounding gate (workflow #17, #20): tandai klaim jawaban yang TIDAK didukung source.
Heuristik leksikal per klaim; negasi hanya berlaku pada klaim setempat. Bukan bukti kebenaran."""
from __future__ import annotations

import re
from dataclasses import dataclass

_NEG = re.compile(r"\b(tidak|bukan|tanpa|belum|tak|no|not|without|tiada)\b", re.I)
_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
_CLAUSES = re.compile(r"(?<!\d),|,(?!\d)|[;:]|\b(?:tetapi|namun|tapi|dan|sedangkan|but|however|and|while)\b", re.I)
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


def _negated(sent: str, start: int) -> bool:
    # Negation after a claim, or belonging to an earlier claim, does not exempt it.
    preceding = [m.end() for pattern in [r[1] for r in _RULES] + [_INTERNET, _TIMEOUT_CLAIM]
                 for m in pattern.finditer(sent) if m.end() <= start]
    return bool(_NEG.search(sent[max(preceding, default=0):start]))


def check_grounding(answer: str, source: str) -> list[Violation]:
    out: list[Violation] = []
    src_timeouts = {_num(m) for m in _TIMEOUT_SRC.findall(source)}
    for sent in (s.strip() for sentence in _SPLIT.split(answer) for s in _CLAUSES.split(sentence)):
        if not sent:
            continue
        for name, claim, evidence in _RULES:
            if any(not _negated(sent, m.start()) for m in claim.finditer(sent)) and not evidence.search(source):
                out.append(Violation(name, sent[:200]))
        if any(not _negated(sent, m.start()) for m in _INTERNET.finditer(sent)) and not _EXT_URL.search(source):
            out.append(Violation("pengecekan internet/host eksternal", sent[:200]))
        for m in _TIMEOUT_CLAIM.finditer(sent):
            if not _negated(sent, m.start()) and _num(m.group(1)) not in src_timeouts:
                out.append(Violation("nilai timeout tidak sesuai source", sent[:200]))
    return out
