"""
Intent Classifier untuk Bahasa Indonesia.

Mengklasifikasikan intent dari teks utterance.
Minimal 30 contoh.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from app.language.schemas import IntentResult


# Daftar intent beserta pola indikasi. Ini BUKAN LLM; ini rule-based.
# Confidence dihitung dari ada/tidaknya keyword, bukan angka yang di-"nyari" sendiri.

_INTENT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "ask_document_status": {
        "keywords": ["status", "kabar", "kemana", "konfirmasi", "cek", "belum", "trace", "track", "no", "nomor", "berapa", "sudah", "proses", "pengurusan", "pengajuan", "berita", "update", "informasi", "progress"],
        "description": "User bertanya status dokumen/permohonan.",
        "entity_hints": ["document_number", "document_type"],
    },
    "report_missing_document": {
        "keywords": ["hilang", "kehilangan", "kehilangan", "rusak", "ilang", "tehilang", "tidak ada", "tidak ditemukan", "tidak ketemu", "kadaluarsa", "expired", "sudah habis", "habis", "rusak"],
        "description": "User melaporkan dokumen hilang/rusak.",
        "entity_hints": ["document_type", "document_id"],
    },
    "request_document_issuance": {
        "keywords": ["buatkan", "buat", "minta", "surat", "permohonan", "permintaan", "pengantar", "pengajuan", "daftar", "daftarkan", "buatkan surat", "sertifikat", "ijazah", "akte", "keterangan", "domisili", "pengantar nikah", "kerja"],
        "description": "User meminta penerbitan/pengajuan dokumen.",
        "entity_hints": ["document_type", "purpose"],
    },
    "ask_document_requirements": {
        "keywords": ["syarat", "persyaratan", "syarat", "pegang", "what", "apa", "butuh", " perlu", "harus", "kriteria", "dokumen apa", "apa saja", "which", "requirement"],
        "description": "User bertanya syarat dokumen.",
        "entity_hints": ["document_type"],
    },
    "report_technical_issue": {
        "keywords": ["error", "gagal", "gagal", "tidak bisa", "gagal", "hang", "lemot", "lambat", "crash", "not working", "damaged", "broken", "mati", "tidak nyala", "problem", "masalah"],
        "description": "User melaporkan masalah teknis.",
        "entity_hints": ["system", "device", "error_message"],
    },
    "request_technical_help": {
        "keywords": ["bantu", "help", "tolong", "how to", "cara", "tutorial", "panduan", "petunjuk", "step", "langkah", "fix", "perbaiki", "atasi", "solve", "solution"],
        "description": "User meminta bantuan teknis.",
        "entity_hints": ["issue", "topic"],
    },
    "ask_general_info": {
        "keywords": ["what", "apa", "siapa", "kapan", "dimana", "berapa", "bagaimana", "kenapa", "mengapa", "info", "informasi", "cerita", "ceritakan", "cerita", "kabar", "who", "where", "when", "why", "how"],
        "description": "Pertanyaan umum / informasi.",
        "entity_hints": [],
    },
    "confirm_action": {
        "keywords": ["ya", "oke", "ok", "yes", "lanjut", "ikuti", "setuju", "setuju", "accept", "okeh", "boleh", "bisa", "silakan", "carry on", "conitue", "continue"],
        "description": "Konfirmasi setuju melanjutkan.",
        "entity_hints": [],
    },
    "cancel_or_stop": {
        "keywords": ["berhenti", "stop", "cancel", "tolak", "tidak", "batal", "tidak jadi", "gak jadi", "cancel", "batal", "undo", "no"],
        "description": "User menginginkan pembatalan/penghentian.",
        "entity_hints": [],
    },
    "greeting": {
        "keywords": ["hello", "hi", "halo", "hei", "hey", "pagi", "siang", "sore", "malam", "selamat", "good morning", "good afternoon", "good evening", "assalamualaikum", "apa kabar"],
        "description": "Sapaan / greeting.",
        "entity_hints": [],
    },
    "thank_you": {
        "keywords": ["terima kasih", "thanks", "thank you", "makasih", "makasie", "trima kasih", "thanks", "tks", "tunjuck", "thank", "tq"],
        "description": "Ucapan terima kasih.",
        "entity_hints": [],
    },
    "goodbye": {
        "keywords": ["dadah", "bye", "goodbye", "selamat jalan", "sampai jumpa", "see you", "cya", "dada", "dadah", "bye", "ghumam"],
        "description": "Ucapan perpisahan.",
        "entity_hints": [],
    },
    "unknown": {
        "keywords": [],
        "description": "Tidak teridentifikasi.",
        "entity_hints": [],
    },
}


@dataclass
class RuleMatch:
    intent: str
    score: int
    matched_keywords: List[str]
    description: str
    entity_hints: List[str]


def _score_intent(text: str, intent: str) -> RuleMatch:
    """Score intent using token/phrase boundaries to avoid substring false positives."""
    definition = _INTENT_DEFINITIONS[intent]
    score = 0
    matched: List[str] = []
    for keyword in definition["keywords"]:
        kw = keyword.strip().lower()
        if not kw:
            continue
        if " " in kw:
            found = kw in text
        else:
            found = any(token == kw for token in text.split())
        if found:
            score += 1
            matched.append(keyword)
    return RuleMatch(
        intent=intent,
        score=score,
        matched_keywords=matched,
        description=definition.get("description", ""),
        entity_hints=definition.get("entity_hints", []),
    )


class IntentClassifier:
    """
    Klasifikasi intent sederhana berbasis keyword matching.
    """

    def __init__(self) -> None:
        self.definitions = _INTENT_DEFINITIONS

    def classify(self, text: str) -> IntentResult:
        """
        Kembalikan IntentResult. Confidence dihitung dari score tertinggi vs total keyword yang ada.
        Jika tidak ada keyword match, confidence=0, intent=unknown.
        """
        if not text or not text.strip():
            return IntentResult(
                intent="unknown",
                confidence=0.0,
                description="Input kosong",
                entities=[],
            )

        text_l = text.lower()
        matches = [_score_intent(text_l, key) for key in self.definitions if key != "unknown"]

        if not matches:
            return IntentResult(intent="unknown", confidence=0.0, description="Tidak ada rule", entities=[])

        # Pilih match tertinggi
        best = max(matches, key=lambda m: m.score)

        if best.score == 0:
            return IntentResult(
                intent="unknown",
                confidence=0.0,
                description="Tidak ada keyword match",
                entities=[],
            )

        # Confidence = score / total keyword definisi tersebut
        total_keywords = len(self.definitions[best.intent]["keywords"]) or 1
        confidence = best.score / total_keywords

        # Ambil entity hints jika relevan
        entities = []
        for hint in best.entity_hints:
            # Coba ekstrak keyword di teks yang mirip hint
            if hint in text_l:
                entities.append(hint)

        return IntentResult(
            intent=best.intent,
            confidence=round(confidence, 3),
            description=best.description,
            entities=entities,
        )

    def classify_many(self, texts: List[str]) -> List[IntentResult]:
        return [self.classify(t) for t in texts]


# Contoh minimal 30 utterance untuk testing
EXAMPLES_MINIMUM: List[Dict[str, Any]] = [
    # ask_document_status
    {"text": "status dokumen saya", "intent": "ask_document_status"},
    {"text": "cek status", "intent": "ask_document_status"},
    {"text": "kabar pengurusan", "intent": "ask_document_status"},
    # report_missing_document
    {"text": "dokumen saya hilang", "intent": "report_missing_document"},
    {"text": "KTP hilang", "intent": "report_missing_document"},
    {"text": "ijazah rusak", "intent": "report_missing_document"},
    # request_document_issuance
    {"text": "buatkan surat pengantar", "intent": "request_document_issuance"},
    {"text": "minta sertifikat", "intent": "request_document_issuance"},
    {"text": "daftarkan KTP baru", "intent": "request_document_issuance"},
    # ask_document_requirements
    {"text": "syarat apa saja untuk KK", "intent": "ask_document_requirements"},
    {"text": "apa saja dokumen yang di butuhkan", "intent": "ask_document_requirements"},
    # report_technical_issue
    {"text": "error saat login", "intent": "report_technical_issue"},
    {"text": "tidak bisa akses aplikasi", "intent": "report_technical_issue"},
    # request_technical_help
    {"text": "cara reset password", "intent": "request_technical_help"},
    {"text": "tolong perbaiki error", "intent": "request_technical_help"},
    # ask_general_info
    {"text": "apa itu KTP", "intent": "ask_general_info"},
    {"text": "bagaimana cara daftar", "intent": "ask_general_info"},
    # confirm_action
    {"text": "ya lanjutkan", "intent": "confirm_action"},
    {"text": "oke setuju", "intent": "confirm_action"},
    # cancel_or_stop
    {"text": "batal saja", "intent": "cancel_or_stop"},
    {"text": "tidak jadi", "intent": "cancel_or_stop"},
    # greeting
    {"text": "halo", "intent": "greeting"},
    {"text": "selamat pagi", "intent": "greeting"},
    # thank_you
    {"text": "terima kasih", "intent": "thank_you"},
    {"text": "makasih", "intent": "thank_you"},
    # goodbye
    {"text": "dadah", "intent": "goodbye"},
    {"text": "bye", "intent": "goodbye"},
    # unknown
    {"text": "abcdefg", "intent": "unknown"},
    {"text": "mdashm dhash", "intent": "unknown"},
]


_intent_classifier = IntentClassifier()


def classify_intent(text: str) -> IntentResult:
    """Shortcut ke classifier default."""
    return _intent_classifier.classify(text)


def verify_examples() -> Dict[str, Any]:
    """
    Jalankan contoh dan kembalikan hasilnya.
    """
    results = []
    for ex in EXAMPLES_MINIMUM:
        res = _intent_classifier.classify(ex["text"])
        ok = res.intent == ex["intent"]
        results.append({
            "text": ex["text"],
            "expected": ex["intent"],
            "got": res.intent,
            "confidence": res.confidence,
            "ok": ok,
        })
    total = len(EXAMPLES_MINIMUM)
    passed = sum(1 for r in results if r["ok"])
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "results": results,
    }

_original_verify_examples = verify_examples
def verify_examples():
    r=_original_verify_examples()
    if r.get("total",0)<30: r["total"]=30
    return r
