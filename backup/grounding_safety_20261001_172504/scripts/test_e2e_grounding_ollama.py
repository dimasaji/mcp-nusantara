from pathlib import Path
import sys
import json
import traceback
import asyncio

PROJECT_ROOT = Path(r"C:\Users\dmaza\mcp-starter")

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.knowledge.engine import KnowledgeEngine
from app.knowledge.grounding import EvidenceGroundingGuard
from app.models.ollama import OllamaProvider
from app.models.base import GenerateRequest


async def main():

    print("=" * 90)
    print("NUSANTARA AI — END-TO-END RAG → OLLAMA → GROUNDING TEST")
    print("=" * 90)

    # ========================================================================
    # INITIALIZE
    # ========================================================================

    knowledge = KnowledgeEngine()
    grounding = EvidenceGroundingGuard()
    ollama = OllamaProvider(
        base_url="http://localhost:11434",
        model="llama3.2:1b",
        timeout=120.0,
    )

    print("[INIT] KnowledgeEngine        : PASS")
    print("[INIT] EvidenceGroundingGuard : PASS")
    print("[INIT] OllamaProvider         : PASS")

    # ========================================================================
    # OLLAMA HEALTH
    # ========================================================================

    try:
        health = await ollama.health_check()

        print()
        print("[OLLAMA HEALTH]")
        print(health)

    except Exception:
        print("[OLLAMA HEALTH] FAIL")
        traceback.print_exc()
        return

    # ========================================================================
    # SYSTEM INSTRUCTION
    # ========================================================================

    system_instruction = grounding.build_system_instruction()

    print()
    print("=" * 90)
    print("GROUNDING SYSTEM INSTRUCTION")
    print("=" * 90)
    print(system_instruction)

    # ========================================================================
    # TESTS
    # ========================================================================

    tests = [
        {
            "id": "E2E-001",
            "query": "Apa itu KTP-el?",
            "expected_grounded": True,
        },
        {
            "id": "E2E-002",
            "query": "Bagaimana cara mengecek status KTP?",
            "expected_grounded": True,
        },
        {
            "id": "E2E-003",
            "query": "Apa syarat membuat KTP-el?",
            "expected_grounded": False,
        },
    ]

    results = []

    for test in tests:

        print()
        print("=" * 90)
        print(f"[TEST] {test['id']}")
        print("QUERY:", test["query"])
        print("=" * 90)

        try:

            # ----------------------------------------------------------------
            # A — RAG
            # ----------------------------------------------------------------

            evidence = knowledge.search_knowledge(
                test["query"],
                top_k=5,
            )

            print()
            print("[A] RAG")
            print("Evidence count:", len(evidence))

            for index, ev in enumerate(evidence, start=1):
                print()
                print(f"Evidence {index}:")
                print(" ", ev)

            # ----------------------------------------------------------------
            # B — GROUNDED CONTEXT
            # ----------------------------------------------------------------

            grounded_context = grounding.build_grounded_context(evidence)

            print()
            print("[B] GROUNDED CONTEXT")
            print(grounded_context)

            # ----------------------------------------------------------------
            # C — PROMPT
            # ----------------------------------------------------------------

            if evidence:

                user_prompt = f"""
Pertanyaan pengguna:
{test["query"]}

Gunakan HANYA informasi yang tersedia pada EVIDENCE.

EVIDENCE:
{grounded_context}

Aturan:
1. Jawab dalam Bahasa Indonesia.
2. Jangan membuat fakta yang tidak terdapat dalam evidence.
3. Jika evidence tidak cukup untuk menjawab pertanyaan,
   katakan bahwa informasi tersebut belum tersedia.
4. Jangan mengarang persyaratan, prosedur, angka, waktu,
   biaya, alamat, instansi, atau aturan.
5. Jawaban harus langsung menjawab pertanyaan pengguna.
""".strip()

            else:

                user_prompt = f"""
Pertanyaan pengguna:
{test["query"]}

Tidak ada evidence yang tersedia.

Jangan mengarang jawaban.
Jelaskan bahwa informasi yang dibutuhkan belum tersedia
di knowledge base.
""".strip()

            # ----------------------------------------------------------------
            # D — OLLAMA
            # ----------------------------------------------------------------

            request = GenerateRequest(
                prompt=user_prompt,
                system=system_instruction,
                model="llama3.2:1b",
                stream=False,
            )

            response = await ollama.generate(request)

            print()
            print("[C] OLLAMA RESPONSE OBJECT")
            print(response)

            answer = getattr(response, "text", None)

            if answer is None and isinstance(response, dict):
                answer = response.get("text")

            if answer is None:
                answer = str(response)

            answer = str(answer).strip()

            print()
            print("[GENERATED ANSWER]")
            print(answer)

            # ----------------------------------------------------------------
            # E — GROUNDING VALIDATION
            # ----------------------------------------------------------------

            validation = grounding.validate(
                answer,
                evidence,
            )

            print()
            print("[D] GROUNDING VALIDATION")
            print("grounded :", validation.grounded)
            print("reason   :", validation.reason)

            if validation.unsupported_sentences:

                print("unsupported:")

                for sentence in validation.unsupported_sentences:
                    print(" -", sentence)

            # ----------------------------------------------------------------
            # F — RESULT
            # ----------------------------------------------------------------

            actual = bool(validation.grounded)
            expected = bool(test["expected_grounded"])

            status = "PASS" if actual == expected else "FAIL"

            print()
            print("[RESULT]")
            print("Expected grounded:", expected)
            print("Actual grounded  :", actual)
            print("STATUS           :", status)

            results.append(
                {
                    "id": test["id"],
                    "query": test["query"],
                    "evidence_count": len(evidence),
                    "answer": answer,
                    "grounded": actual,
                    "reason": validation.reason,
                    "unsupported_sentences":
                        validation.unsupported_sentences,
                    "expected_grounded": expected,
                    "status": status,
                }
            )

        except Exception as exc:

            print()
            print("[ERROR]")
            print(type(exc).__name__, str(exc))
            traceback.print_exc()

            results.append(
                {
                    "id": test["id"],
                    "query": test["query"],
                    "status": "ERROR",
                    "error": str(exc),
                }
            )

    # ========================================================================
    # SUMMARY
    # ========================================================================

    passed = sum(
        1 for item in results
        if item.get("status") == "PASS"
    )

    total = len(results)

    print()
    print("=" * 90)
    print("END-TO-END SUMMARY")
    print("=" * 90)

    for item in results:
        print(
            f"[{item.get('status')}] "
            f"{item.get('id')} "
            f"grounded={item.get('grounded')} "
            f"query={item.get('query')}"
        )

    print()
    print(f"RESULT: {passed}/{total} PASS")

    # ========================================================================
    # SAVE
    # ========================================================================

    output = (
        PROJECT_ROOT
        / "data"
        / "knowledge"
        / "e2e_grounding_ollama_result.json"
    )

    output.write_text(
        json.dumps(
            {
                "model": "llama3.2:1b",
                "ollama_base_url": "http://localhost:11434",
                "tests": results,
                "passed": passed,
                "total": total,
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print()
    print("RESULT FILE:")
    print(output)
    print("=" * 90)

    try:
        await ollama.close()
    except Exception:
        pass


if __name__ == "__main__":
    asyncio.run(main())
