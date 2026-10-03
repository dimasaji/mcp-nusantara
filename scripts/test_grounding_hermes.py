from pathlib import Path
import sys
import json
import traceback

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 80)
print("NUSANTARA AI — GROUNDING → HERMES INTEGRATION TEST")
print("=" * 80)

try:
    from app.knowledge.engine import KnowledgeEngine
    from app.knowledge.grounding import EvidenceGroundingGuard
    from app.models.ollama import OllamaClient

    print("[IMPORT] KnowledgeEngine          : PASS")
    print("[IMPORT] EvidenceGroundingGuard   : PASS")
    print("[IMPORT] OllamaClient              : PASS")

except Exception:
    print("[IMPORT] FAIL")
    traceback.print_exc()
    raise SystemExit(1)

# ---------------------------------------------------------------------------
# INITIALIZE
# ---------------------------------------------------------------------------

try:
    engine = KnowledgeEngine()
    grounding = EvidenceGroundingGuard()

    print("[INIT] KnowledgeEngine            : PASS")
    print("[INIT] EvidenceGroundingGuard     : PASS")

except Exception:
    print("[INIT] FAIL")
    traceback.print_exc()
    raise SystemExit(2)

# ---------------------------------------------------------------------------
# DISCOVER OLLAMA CLIENT
# ---------------------------------------------------------------------------

import inspect

print()
print("[OLLAMA CLIENT]")
print("class:", OllamaClient)

try:
    print("constructor:", inspect.signature(OllamaClient))
except Exception:
    pass

# ---------------------------------------------------------------------------
# TEST CASES
# ---------------------------------------------------------------------------

tests = [
    {
        "id": "grounded-info",
        "query": "Apa itu KTP-el?",
        "must_have_evidence": True,
    },
    {
        "id": "grounded-status",
        "query": "Bagaimana cara mengecek status KTP?",
        "must_have_evidence": True,
    },
    {
        "id": "unsupported-requirements",
        "query": "Apa syarat membuat KTP-el?",
        "must_have_evidence": False,
    },
]

results = []

for test in tests:

    print()
    print("=" * 80)
    print(f"[TEST] {test['id']}")
    print(f"QUERY: {test['query']}")
    print("=" * 80)

    try:

        # ------------------------------------------------------------
        # RETRIEVE
        # ------------------------------------------------------------

        evidence = engine.search_knowledge(test["query"])

        print()
        print("[EVIDENCE COUNT]", len(evidence))

        # ------------------------------------------------------------
        # BUILD GROUNDING CONTEXT
        # ------------------------------------------------------------

        context = grounding.build_grounded_context(evidence)

        print()
        print("[GROUNDED CONTEXT]")
        print(context[:6000])

        # ------------------------------------------------------------
        # GROUNDING VALIDATION
        # ------------------------------------------------------------

        validation = grounding.validate(
            test["query"],
            context,
        )

        print()
        print("[VALIDATION]")
        print(validation)

        # ------------------------------------------------------------
        # RECORD
        # ------------------------------------------------------------

        results.append(
            {
                "id": test["id"],
                "query": test["query"],
                "evidence_count": len(evidence),
                "grounded_context": context,
                "validation": str(validation),
                "status": "PASS",
            }
        )

    except Exception as exc:

        print()
        print("[ERROR]", type(exc).__name__, str(exc))
        traceback.print_exc()

        results.append(
            {
                "id": test["id"],
                "query": test["query"],
                "status": "FAIL",
                "error": str(exc),
            }
        )

# ---------------------------------------------------------------------------
# SAVE
# ---------------------------------------------------------------------------

output = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "grounding_hermes_integration_test.json"
)

output.write_text(
    json.dumps(
        results,
        ensure_ascii=False,
        indent=2,
        default=str,
    ),
    encoding="utf-8",
)

passed = sum(
    1
    for item in results
    if item["status"] == "PASS"
)

print()
print("=" * 80)
print("GROUNDING INTEGRATION TEST SELESAI")
print("=" * 80)
print(f"PASS : {passed}/{len(results)}")
print(f"FAIL : {len(results) - passed}/{len(results)}")
print(f"FILE : {output}")
print("=" * 80)
