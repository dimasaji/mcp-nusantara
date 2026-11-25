from pathlib import Path
import sys
import asyncio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.knowledge.engine import KnowledgeEngine
from app.knowledge.grounding import EvidenceGroundingGuard
from app.models.ollama import OllamaProvider

MODEL = "llama3.2:1b"


async def main():
    print("=" * 78)
    print("NUSANTARA AI — HERMES GROUNDING INTEGRATION TEST")
    print("=" * 78)

    # ============================================================
    # INIT
    # ============================================================

    engine = KnowledgeEngine()
    guard = EvidenceGroundingGuard()

    provider = OllamaProvider(
        base_url="http://localhost:11434",
        model=MODEL,
        timeout=120.0,
    )

    print("[IMPORT] KnowledgeEngine        : PASS")
    print("[IMPORT] EvidenceGroundingGuard : PASS")
    print("[IMPORT] OllamaProvider          : PASS")

    # ============================================================
    # OLLAMA
    # ============================================================

    print("")
    print("-" * 78)
    print("OLLAMA HEALTH")
    print("-" * 78)

    health = await provider.health_check()
    print(health)

    available = (
        health.get("available", False)
        if isinstance(health, dict)
        else getattr(health, "available", False)
    )

    if not available:
        await provider.close()
        raise SystemExit("OLLAMA: FAIL")

    print("OLLAMA: PASS")

    # ============================================================
    # RETRIEVAL
    # ============================================================

    query = "Apa itu KTP-el?"

    print("")
    print("-" * 78)
    print("KNOWLEDGE RETRIEVAL")
    print("-" * 78)
    print("QUERY:", query)

    # KnowledgeEngine API aktual
    results = engine.search_knowledge(query)

    print("RESULT TYPE:", type(results).__name__)
    print("EVIDENCE COUNT:", len(results))

    if not results:
        await provider.close()
        raise SystemExit("RETRIEVAL: FAIL")

    evidence_parts = []

    for i, item in enumerate(results, 1):
        title = getattr(item, "title", "Evidence")
        chunk = getattr(item, "chunk", None)

        if not chunk:
            chunk = getattr(item, "source", "")

        print("")
        print(f"[EVIDENCE {i}] {title}")
        print(chunk)

        if chunk:
            evidence_parts.append(str(chunk))

    evidence = "\n".join(evidence_parts)

    print("")
    print("RETRIEVAL: PASS")

    # ============================================================
    # SUPPORTED CLAIM
    # ============================================================

    supported_answer = "KTP-el adalah dokumen identitas penduduk."

    print("")
    print("-" * 78)
    print("SUPPORTED GROUNDING")
    print("-" * 78)
    print("ANSWER:", supported_answer)

    result = guard.validate(
        supported_answer,
        evidence,
    )

    print("")
    print("grounded :", result.grounded)
    print("reason   :", result.reason)

    if not result.grounded:
        await provider.close()
        raise SystemExit(
            "SUPPORTED GROUNDING: FAIL"
        )

    print("SUPPORTED GROUNDING: PASS")

    # ============================================================
    # UNSUPPORTED PROCEDURE
    # ============================================================

    unsupported_answer = (
        "Untuk mengecek status KTP, pengguna harus melakukan "
        "pemeriksaan status melalui sistem layanan."
    )

    print("")
    print("-" * 78)
    print("UNSUPPORTED PROCEDURE / ANTI-HALLUCINATION")
    print("-" * 78)
    print("ANSWER:", unsupported_answer)

    rejected = guard.validate(
        unsupported_answer,
        evidence,
    )

    print("")
    print("grounded :", rejected.grounded)
    print("reason   :", rejected.reason)
    print("unsupported:", rejected.unsupported_sentences)

    if rejected.grounded:
        await provider.close()
        raise SystemExit(
            "ANTI-HALLUCINATION: FAIL"
        )

    print("ANTI-HALLUCINATION: PASS")

    # ============================================================
    # CLEANUP
    # ============================================================

    await provider.close()

    print("")
    print("=" * 78)
    print("HERMES GROUNDING INTEGRATION RESULT")
    print("=" * 78)
    print("KnowledgeEngine         : PASS")
    print("OllamaProvider          : PASS")
    print("Knowledge Retrieval     : PASS")
    print("Supported Grounding     : PASS")
    print("Anti-Hallucination      : PASS")
    print("")
    print("RESULT: PASS")
    print("=" * 78)


if __name__ == "__main__":
    asyncio.run(main())
