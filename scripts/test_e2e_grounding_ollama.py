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
