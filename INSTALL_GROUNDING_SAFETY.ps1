$ErrorActionPreference = "Stop"

# ============================================================
# NUSANTARA AI
# Grounding Safety Installation / Patch
# ============================================================

$ProjectRoot = (Get-Location).Path

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " NUSANTARA AI - GROUNDING SAFETY INSTALLER" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project : $ProjectRoot"
Write-Host ""

# ------------------------------------------------------------
# Validate project
# ------------------------------------------------------------

if (-not (Test-Path ".\app")) {
    throw "Folder app tidak ditemukan. Jalankan script dari C:\Users\dmaza\mcp-starter"
}

if (-not (Test-Path ".\app\knowledge")) {
    throw "Folder app\knowledge tidak ditemukan."
}

if (-not (Test-Path ".\app\api")) {
    throw "Folder app\api tidak ditemukan."
}

# ------------------------------------------------------------
# Backup
# ------------------------------------------------------------

$BackupRoot = Join-Path $ProjectRoot ("backup\grounding_safety_" + (Get-Date -Format "yyyyMMdd_HHmmss"))

New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null

Write-Host "[1/8] Membuat backup..." -ForegroundColor Yellow

$BackupFiles = @(
    "app\knowledge\grounding.py",
    "app\api\routes.py",
    "scripts\test_e2e_grounding_ollama.py"
)

foreach ($File in $BackupFiles) {
    $Source = Join-Path $ProjectRoot $File

    if (Test-Path $Source) {
        $Destination = Join-Path $BackupRoot $File
        $DestinationDir = Split-Path $Destination -Parent

        New-Item -ItemType Directory -Force -Path $DestinationDir | Out-Null
        Copy-Item $Source $Destination -Force

        Write-Host "  BACKUP $File" -ForegroundColor DarkGray
    }
}

Write-Host "Backup: $BackupRoot" -ForegroundColor Green
Write-Host ""

# ------------------------------------------------------------
# Ensure scripts directory
# ------------------------------------------------------------

New-Item -ItemType Directory -Force -Path ".\scripts" | Out-Null

# ============================================================
# 2. WRITE grounding.py
# ============================================================

Write-Host "[2/8] Menulis app\knowledge\grounding.py..." -ForegroundColor Yellow

$Grounding = @'
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

            strong_claim = (
                numeric_claim
                or requirement_claim
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
                r"^(?:[-*•]+|\d+[.)])\s*",
                "",
                piece,
            ).strip()

            if piece:
                result.append(piece)

        return result

    def _content_tokens(self, text: str) -> set[str]:
        tokens = re.findall(
            r"[a-zA-ZÀ-ÿ0-9][a-zA-ZÀ-ÿ0-9_-]*",
            text.lower(),
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
        Small phrase-level check.

        Uses 2- and 3-token shingles. This is intentionally simple
        and deterministic; it does not replace semantic retrieval.
        """

        sentence_tokens = list(self._content_tokens(sentence))
        evidence_tokens = self._content_tokens(evidence)

        if not sentence_tokens or not evidence_tokens:
            return 0.0

        sentence_lower = sentence.lower()
        evidence_lower = evidence.lower()

        score = 0.0
        count = 0

        raw_tokens = re.findall(
            r"[a-zA-ZÀ-ÿ0-9][a-zA-ZÀ-ÿ0-9_-]*",
            sentence_lower,
        )

        for n in (3, 2):
            if len(raw_tokens) < n:
                continue

            for i in range(len(raw_tokens) - n + 1):
                phrase = " ".join(raw_tokens[i:i+n])

                if phrase in evidence_lower:
                    score += 1.0
                    count += 1

        if count == 0:
            return 0.0

        return min(1.0, score / max(1, len(raw_tokens) - 1))

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
'@

Set-Content `
    -Path ".\app\knowledge\grounding.py" `
    -Value $Grounding `
    -Encoding UTF8

Write-Host "grounding.py OK" -ForegroundColor Green
Write-Host ""

# ============================================================
# 3. WRITE E2E TEST
# ============================================================

Write-Host "[3/8] Menulis E2E test..." -ForegroundColor Yellow

$E2E = @'
"""
Nusantara AI - E2E Grounding + Ollama Test

Tests:
1. Ollama health
2. Supported factual answer
3. Unsupported procedural/status claim
4. Unsupported requirements hallucination
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from app.knowledge.grounding import EvidenceGroundingGuard
from app.models.base import GenerateRequest
from app.models.ollama import OllamaProvider


MODEL = "llama3.2:1b"


def extract_content(response) -> str:
    """
    OllamaProvider.generate() returns a response object/dict whose
    generated answer is in 'content'.
    """

    if response is None:
        return ""

    if isinstance(response, dict):
        value = response.get("content")

        if value is not None:
            return str(value)

        value = response.get("text")

        if value is not None:
            return str(value)

    for attr in ("content", "text"):
        value = getattr(response, attr, None)

        if value is not None:
            return str(value)

    return str(response)


async def run_case(
    guard: EvidenceGroundingGuard,
    ollama: OllamaProvider,
    name: str,
    query: str,
    evidence: list[dict],
    expect_grounded: bool,
) -> bool:

    print()
    print("=" * 70)
    print(name)
    print("=" * 70)

    evidence_context = guard.build_grounded_context(evidence)

    system_instruction = guard.build_system_instruction()

    prompt = f"""
{system_instruction}

EVIDENCE:
{evidence_context}

PERTANYAAN PENGGUNA:
{query}

Jawab hanya berdasarkan EVIDENCE.
Jika informasi tidak tersedia dalam EVIDENCE,
katakan bahwa informasi tersebut belum tersedia.

JAWABAN:
""".strip()

    request = GenerateRequest(
        prompt=prompt,
        model=MODEL,
        stream=False,
    )

    response = await ollama.generate(request)

    answer = extract_content(response)

    print()
    print("ANSWER:")
    print(answer)

    result = guard.validate(
        answer,
        evidence,
    )

    print()
    print("GROUNDING:")
    print("  grounded :", result.grounded)
    print("  reason   :", result.reason)

    if result.unsupported_sentences:
        print("  unsupported:")

        for sentence in result.unsupported_sentences:
            print("   -", sentence)

    passed = result.grounded == expect_grounded

    print()
    print(
        "RESULT:",
        "PASS" if passed else "FAIL",
    )

    return passed


async def main() -> int:

    print("=" * 70)
    print("NUSANTARA AI - E2E GROUNDING + OLLAMA")
    print("=" * 70)
    print("Project :", PROJECT_ROOT)
    print("Model   :", MODEL)

    guard = EvidenceGroundingGuard()

    ollama = OllamaProvider(
        base_url="http://localhost:11434",
        model=MODEL,
        timeout=120.0,
    )

    # --------------------------------------------------------
    # Health
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("OLLAMA HEALTH")
    print("=" * 70)

    health = await ollama.health_check()

    print(health)

    if isinstance(health, dict):
        if not health.get("available", False):
            print()
            print("OLLAMA NOT AVAILABLE")
            return 2

    # --------------------------------------------------------
    # E2E-001
    # Supported factual information
    # --------------------------------------------------------

    evidence_ktp = [
        {
            "source": "Test KTP",
            "text": (
                "KTP-el adalah dokumen identitas penduduk. "
                "Status pengajuan KTP-el dapat diperiksa melalui "
                "layanan administrasi kependudukan."
            ),
        },
        {
            "source": "Test API KTP",
            "text": (
                "KTP-el merupakan dokumen identitas penduduk "
                "yang diterbitkan sesuai ketentuan administrasi "
                "kependudukan."
            ),
        },
    ]

    # --------------------------------------------------------
    # E2E-002
    # Status/procedure evidence is intentionally weak.
    # The answer must NOT be accepted merely because it talks
    # about KTP.
    # --------------------------------------------------------

    evidence_status_weak = [
        {
            "source": "Test KTP",
            "text": (
                "KTP-el adalah dokumen identitas penduduk. "
                "Status pengajuan KTP-el dapat diperiksa melalui "
                "layanan administrasi kependudukan."
            ),
        },
        {
            "source": "Test API KTP",
            "text": (
                "KTP-el merupakan dokumen identitas penduduk "
                "yang diterbitkan sesuai ketentuan administrasi "
                "kependudukan."
            ),
        },
    ]

    # --------------------------------------------------------
    # E2E-003
    # Requirements are NOT present in evidence.
    # Model may hallucinate them, but grounding must reject it.
    # --------------------------------------------------------

    cases = [
        (
            "E2E-001",
            "Apa itu KTP-el?",
            evidence_ktp,
            True,
        ),
        (
            "E2E-002",
            "Bagaimana cara mengecek status KTP?",
            evidence_status_weak,
            False,
        ),
        (
            "E2E-003",
            "Apa syarat membuat KTP-el?",
            evidence_ktp,
            False,
        ),
    ]

    passed = 0

    for name, query, evidence, expected in cases:

        ok = await run_case(
            guard=guard,
            ollama=ollama,
            name=name,
            query=query,
            evidence=evidence,
            expect_grounded=expected,
        )

        if ok:
            passed += 1

    print()
    print("=" * 70)
    print("FINAL RESULT")
    print("=" * 70)

    print(
        f"{passed}/{len(cases)} E2E grounding tests passed"
    )

    await ollama.close()

    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(
        asyncio.run(main())
    )
'@

Set-Content `
    -Path ".\scripts\test_e2e_grounding_ollama.py" `
    -Value $E2E `
    -Encoding UTF8

Write-Host "E2E test OK" -ForegroundColor Green
Write-Host ""

# ============================================================
# 4. PATCH routes.py
# ============================================================

Write-Host "[4/8] Menganalisis routes.py..." -ForegroundColor Yellow

$RoutesPath = ".\app\api\routes.py"

if (-not (Test-Path $RoutesPath)) {
    throw "routes.py tidak ditemukan."
}

$Routes = Get-Content $RoutesPath -Raw -Encoding UTF8

# ------------------------------------------------------------
# Ensure import
# ------------------------------------------------------------

if ($Routes -notmatch "from\s+app\.knowledge\.grounding\s+import\s+EvidenceGroundingGuard") {

    $ImportAnchor = "from app.knowledge"

    if ($Routes.Contains($ImportAnchor)) {

        $Lines = $Routes -split "`r?`n"

        $InsertIndex = -1

        for ($i = 0; $i -lt $Lines.Count; $i++) {
            if ($Lines[$i] -match "^from app\.knowledge") {
                $InsertIndex = $i
                break
            }
        }

        if ($InsertIndex -ge 0) {

            $NewLines = New-Object System.Collections.Generic.List[string]

            for ($i = 0; $i -lt $Lines.Count; $i++) {

                $NewLines.Add($Lines[$i])

                if ($i -eq $InsertIndex) {
                    $NewLines.Add(
                        "from app.knowledge.grounding import EvidenceGroundingGuard"
                    )
                }
            }

            $Routes = $NewLines -join "`r`n"

            Write-Host "  Import EvidenceGroundingGuard ditambahkan." -ForegroundColor Green
        }
    }
}

# ------------------------------------------------------------
# Create singleton guard after knowledge initialization.
# ------------------------------------------------------------

if ($Routes -notmatch "_grounding_guard\s*=") {

    $AnchorPatterns = @(
        "_knowledge\s*=",
        "_knowledge\s*:",
        "knowledge\s*=\s*KnowledgeEngine"
    )

    $Inserted = $false

    foreach ($Pattern in $AnchorPatterns) {

        if ($Routes -match $Pattern) {

            $Regex = [regex]::Match(
                $Routes,
                $Pattern
            )

            if ($Regex.Success) {

                $Position = $Regex.Index

                $LineEnd = $Routes.IndexOf("`n", $Position)

                if ($LineEnd -lt 0) {
                    $LineEnd = $Routes.Length
                }

                $InsertText = @"

# ============================================================
# GROUNDING SAFETY GUARD
# ============================================================

_grounding_guard = EvidenceGroundingGuard()

"@

                $Routes =
                    $Routes.Substring(0, $LineEnd + 1) +
                    $InsertText +
                    $Routes.Substring($LineEnd + 1)

                $Inserted = $true

                Write-Host "  _grounding_guard ditambahkan." -ForegroundColor Green

                break
            }
        }
    }

    if (-not $Inserted) {
        Write-Host ""
        Write-Host "WARNING: Tidak menemukan anchor knowledge engine." -ForegroundColor Yellow
        Write-Host "Grounding guard tidak dipaksakan masuk ke routes.py." -ForegroundColor Yellow
    }
}

# ------------------------------------------------------------
# Safety helper function.
#
# This helper can be called by the chat pipeline immediately
# after Ollama generates an answer.
# ------------------------------------------------------------

if ($Routes -notmatch "def _apply_grounding_safety_gate\(") {

    $Helper = @'

# ============================================================
# GROUNDING SAFETY GATE
# ============================================================

def _apply_grounding_safety_gate(
    answer,
    evidence,
):
    """
    Validate final LLM answer against evidence.

    Returns:
        tuple[str, bool, str]

    If unsupported:
        returns a safe fallback instead of exposing the
        hallucinated answer.
    """

    try:
        guard = globals().get("_grounding_guard")

        if guard is None:
            guard = EvidenceGroundingGuard()

        result = guard.validate(
            answer=answer,
            evidence=evidence,
        )

        if result.grounded:
            return (
                result.text,
                True,
                result.reason,
            )

        logger.warning(
            "GROUNDING SAFETY BLOCK: reason=%s unsupported=%s",
            result.reason,
            result.unsupported_sentences,
        )

        fallback = (
            "Informasi yang dibutuhkan untuk menjawab pertanyaan "
            "tersebut belum tersedia atau belum cukup didukung "
            "oleh knowledge base Nusantara AI."
        )

        return (
            fallback,
            False,
            result.reason,
        )

    except Exception:
        logger.exception(
            "Grounding safety gate failed closed."
        )

        fallback = (
            "Informasi belum dapat diberikan karena validasi "
            "knowledge belum berhasil dilakukan."
        )

        return (
            fallback,
            False,
            "grounding_validation_error",
        )

'@

    # Insert before first route decorator.
    $RouteMatch = [regex]::Match(
        $Routes,
        "(?m)^@(?:router|app)\."
    )

    if ($RouteMatch.Success) {

        $Routes =
            $Routes.Substring(0, $RouteMatch.Index) +
            $Helper +
            "`r`n" +
            $Routes.Substring($RouteMatch.Index)

        Write-Host "  _apply_grounding_safety_gate ditambahkan." -ForegroundColor Green

    } else {

        # Safe fallback: append helper to file.
        $Routes += "`r`n" + $Helper

        Write-Host "  Helper ditambahkan di akhir routes.py." -ForegroundColor Yellow
    }
}

# ------------------------------------------------------------
# Try to patch final answer assignment.
#
# We deliberately only patch recognizable patterns.
# ------------------------------------------------------------

$PatchedFinalAnswer = $false

$Patterns = @(
    'response_text\s*=\s*response\.text',
    'answer\s*=\s*response\.text',
    'response_text\s*=\s*getattr\(response,\s*["'']text["'']',
    'answer\s*=\s*getattr\(response,\s*["'']text["'']'
)

foreach ($Pattern in $Patterns) {

    if ($Routes -match $Pattern) {

        Write-Host "  Menemukan final answer assignment: $Pattern" -ForegroundColor DarkGray

        # Do not automatically replace arbitrary routes code.
        # Instead, mark the location for explicit integration.
        $PatchedFinalAnswer = $true
        break
    }
}

if (-not $PatchedFinalAnswer) {

    Write-Host ""
    Write-Host "INFO: Final answer assignment routes.py tidak dikenali secara otomatis." -ForegroundColor Yellow
    Write-Host "Helper grounding sudah tersedia." -ForegroundColor Yellow
    Write-Host "Installer tidak melakukan blind replacement." -ForegroundColor Yellow
}

Set-Content `
    -Path $RoutesPath `
    -Value $Routes `
    -Encoding UTF8

Write-Host "routes.py tersimpan." -ForegroundColor Green
Write-Host ""

# ============================================================
# 5. Compile
# ============================================================

Write-Host "[5/8] Python compile..." -ForegroundColor Yellow

python -m py_compile `
    .\app\knowledge\grounding.py `
    .\app\api\routes.py `
    .\scripts\test_e2e_grounding_ollama.py

if ($LASTEXITCODE -ne 0) {
    throw "Python compile gagal. Restore backup: $BackupRoot"
}

Write-Host "COMPILE PASS" -ForegroundColor Green
Write-Host ""

# ============================================================
# 6. Import test
# ============================================================

Write-Host "[6/8] Import test..." -ForegroundColor Yellow

python -c "from app.knowledge.grounding import EvidenceGroundingGuard; print('GROUNDING_IMPORT_OK'); from app.api import routes; print('ROUTES_IMPORT_OK')"

if ($LASTEXITCODE -ne 0) {
    throw "Import test gagal. Restore backup: $BackupRoot"
}

Write-Host "IMPORT PASS" -ForegroundColor Green
Write-Host ""

# ============================================================
# 7. Grounding unit tests
# ============================================================

Write-Host "[7/8] Grounding safety unit test..." -ForegroundColor Yellow

@'
from app.knowledge.grounding import EvidenceGroundingGuard

g = EvidenceGroundingGuard()

evidence = [
    {
        "source": "Test KTP",
        "text": (
            "KTP-el adalah dokumen identitas penduduk. "
            "Status pengajuan KTP-el dapat diperiksa melalui "
            "layanan administrasi kependudukan."
        )
    }
]

tests = [
    (
        "supported",
        "KTP-el adalah dokumen identitas penduduk.",
        True,
    ),
    (
        "unsupported_requirements",
        "Syarat membuat KTP-el adalah membawa pas foto 1x1.",
        False,
    ),
    (
        "unsupported_number",
        "KTP-el selesai dalam 3 hari.",
        False,
    ),
]

passed = 0

for name, answer, expected in tests:
    result = g.validate(answer, evidence)

    ok = result.grounded == expected

    print(
        "[PASS]" if ok else "[FAIL]",
        name,
        "grounded=",
        result.grounded,
        "reason=",
        result.reason,
    )

    if ok:
        passed += 1

print(f"RESULT: {passed}/{len(tests)}")

raise SystemExit(
    0 if passed == len(tests) else 1
)
'@ | python -

if ($LASTEXITCODE -ne 0) {
    throw "Grounding unit test gagal. Restore backup: $BackupRoot"
}

Write-Host "GROUNDING UNIT TEST PASS" -ForegroundColor Green
Write-Host ""

# ============================================================
# 8. Final
# ============================================================

Write-Host "[8/8] Instalasi selesai." -ForegroundColor Yellow
Write-Host ""

Write-Host "============================================================" -ForegroundColor Green
Write-Host " INSTALLATION SUCCESS" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Backup:" -ForegroundColor Cyan
Write-Host "  $BackupRoot"
Write-Host ""

Write-Host "File yang dibuat/diperbarui:" -ForegroundColor Cyan
Write-Host "  app\knowledge\grounding.py"
Write-Host "  app\api\routes.py"
Write-Host "  scripts\test_e2e_grounding_ollama.py"
Write-Host ""

Write-Host "LANGKAH BERIKUTNYA:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Restart FastAPI/Nusantara Core."
Write-Host ""
Write-Host "2. Jalankan:"
Write-Host ""
Write-Host "   python .\scripts\test_e2e_grounding_ollama.py"
Write-Host ""
Write-Host "3. Jika server sudah berjalan:"
Write-Host ""
Write-Host "   python .\scripts\test_chat_regression.py"
Write-Host ""
Write-Host "============================================================"