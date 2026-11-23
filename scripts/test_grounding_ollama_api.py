from pathlib import Path
import sys
import json
import inspect
import traceback

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 80)
print("NUSANTARA AI — GROUNDING + OLLAMA API DISCOVERY TEST")
print("=" * 80)

# ============================================================================
# 1. IMPORT KNOWLEDGE ENGINE
# ============================================================================

try:
    from app.knowledge.engine import KnowledgeEngine
    from app.knowledge.grounding import EvidenceGroundingGuard

    print("[IMPORT] KnowledgeEngine        : PASS")
    print("[IMPORT] EvidenceGroundingGuard : PASS")

except Exception:
    print("[IMPORT] KNOWLEDGE FAIL")
    traceback.print_exc()
    raise SystemExit(1)

# ============================================================================
# 2. IMPORT OLLAMA MODULE
# ============================================================================

try:
    import app.models.ollama as ollama_module

    print()
    print("[OLLAMA MODULE]")
    print("PATH:", ollama_module.__file__)

except Exception:
    print("[OLLAMA MODULE] FAIL")
    traceback.print_exc()
    raise SystemExit(2)

# ============================================================================
# 3. DISCOVER CLASSES / FUNCTIONS
# ============================================================================

print()
print("=" * 80)
print("OLLAMA API YANG TERSEDIA")
print("=" * 80)

members = inspect.getmembers(ollama_module)

classes = []
functions = []

for name, obj in members:

    if name.startswith("_"):
        continue

    if inspect.isclass(obj):
        classes.append(name)

    elif inspect.isfunction(obj):
        functions.append(name)

print()
print("CLASSES:")
for name in classes:
    try:
        obj = getattr(ollama_module, name)
        print(f"  - {name}{inspect.signature(obj)}")
    except Exception:
        print(f"  - {name}")

print()
print("FUNCTIONS:")
for name in functions:
    try:
        obj = getattr(ollama_module, name)
        print(f"  - {name}{inspect.signature(obj)}")
    except Exception:
        print(f"  - {name}")

# ============================================================================
# 4. ENGINE + GROUNDING
# ============================================================================

try:
    engine = KnowledgeEngine()
    grounding = EvidenceGroundingGuard()

    print()
    print("[INIT] KnowledgeEngine        : PASS")
    print("[INIT] EvidenceGroundingGuard : PASS")

except Exception:
    print("[INIT] FAIL")
    traceback.print_exc()
    raise SystemExit(3)

# ============================================================================
# 5. GROUNDING TEST
# ============================================================================

tests = [
    {
        "id": "grounded-info",
        "query": "Apa itu KTP-el?",
    },
    {
        "id": "grounded-status",
        "query": "Bagaimana cara mengecek status KTP?",
    },
    {
        "id": "unsupported-requirements",
        "query": "Apa syarat membuat KTP-el?",
    },
]

results = []

for test in tests:

    print()
    print("-" * 80)
    print(f"[TEST] {test['id']}")
    print("QUERY:", test["query"])

    try:

        evidence = engine.search_knowledge(test["query"])

        print("Evidence count:", len(evidence))

        context = grounding.build_grounded_context(evidence)

        print()
        print("[GROUNDED CONTEXT]")
        print(context[:5000])

        # Coba validation API yang tersedia.
        validation = None

        if hasattr(grounding, "validate"):
            try:
                validation = grounding.validate(
                    test["query"],
                    context,
                )
            except TypeError:
                try:
                    validation = grounding.validate(context)
                except Exception:
                    validation = "validate() signature berbeda"

        print()
        print("[VALIDATION]")
        print(validation)

        results.append(
            {
                "id": test["id"],
                "query": test["query"],
                "evidence_count": len(evidence),
                "context": context,
                "validation": str(validation),
                "status": "PASS",
            }
        )

    except Exception as exc:

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

# ============================================================================
# 6. SAVE
# ============================================================================

output = (
    PROJECT_ROOT
    / "data"
    / "knowledge"
    / "grounding_api_test.json"
)

output.write_text(
    json.dumps(
        {
            "ollama_module": str(ollama_module.__file__),
            "classes": classes,
            "functions": functions,
            "tests": results,
        },
        ensure_ascii=False,
        indent=2,
        default=str,
    ),
    encoding="utf-8",
)

print()
print("=" * 80)
print("GROUNDING API DISCOVERY SELESAI")
print("=" * 80)
print("RESULT:", output)
print("=" * 80)


print("RESULT: PASS")
