from pathlib import Path
import sys

# ============================================================================
# FORCE NUSANTARA PROJECT ROOT
# ============================================================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Pastikan project aktif menjadi prioritas pertama.
sys.path.insert(0, str(PROJECT_ROOT))

# Hapus kemungkinan path project Nusantara lain yang mengganggu.
sys.path[:] = [
    p for p in sys.path
    if str(Path(p).resolve()) != r"E:\nusantara\mcp-starter"
]

print("=" * 80)
print("NUSANTARA AI — KNOWLEDGE ENGINE RETRIEVAL TEST")
print("=" * 80)
print()
print("[PROJECT ROOT]", PROJECT_ROOT)
print("[PYTHON]", sys.executable)

# ============================================================================
# IMPORT
# ============================================================================
try:
    import app.knowledge.rag as rag_module

    print()
    print("[RAG MODULE]", rag_module.__file__)

    # SAFETY CHECK
    expected_rag = PROJECT_ROOT / "app" / "knowledge" / "rag.py"

    actual_rag = Path(rag_module.__file__).resolve()

    if actual_rag != expected_rag.resolve():
        print()
        print("[ERROR] Python masih mengambil rag.py dari lokasi yang salah.")
        print("EXPECTED:", expected_rag)
        print("ACTUAL  :", actual_rag)
        raise SystemExit(1)

    from app.knowledge.engine import KnowledgeEngine
    from app.knowledge.grounding import EvidenceGroundingGuard

    HybridRAG = getattr(rag_module, "HybridRAG", None)

    if HybridRAG is None:
        print()
        print("[ERROR] HybridRAG tidak tersedia pada project aktif.")
        print()
        print("Class yang tersedia:")
        for name in dir(rag_module):
            obj = getattr(rag_module, name)
            if isinstance(obj, type):
                print("  -", name)

        raise SystemExit(2)

    print("[IMPORT] KnowledgeEngine : PASS")
    print("[IMPORT] EvidenceGroundingGuard : PASS")
    print("[IMPORT] HybridRAG       :", HybridRAG)

except Exception:
    import traceback
    print()
    print("[IMPORT] FAIL")
    traceback.print_exc()
    raise SystemExit(3)

# ============================================================================
# ENGINE
# ============================================================================
import inspect
import json
import traceback

print()
print("[ENGINE] constructor:")
print(inspect.signature(KnowledgeEngine))

try:
    engine = KnowledgeEngine()
    print("[ENGINE] initialization: PASS")
except Exception:
    print("[ENGINE] initialization: FAIL")
    traceback.print_exc()
    raise SystemExit(4)

# ============================================================================
# DISCOVER RETRIEVAL API
# ============================================================================
public_methods = [
    name
    for name in dir(engine)
    if not name.startswith("_")
]

print()
print("[ENGINE METHODS]")
print(public_methods)

# ============================================================================
# TEST QUERIES
# ============================================================================
tests = [
    {
        "id": "ktp-001",
        "query": "Apa itu KTP-el?",
    },
    {
        "id": "ktp-002",
        "query": "Apa syarat membuat KTP-el?",
    },
    {
        "id": "ktp-003",
        "query": "Bagaimana cara mengecek status KTP?",
    },
    {
        "id": "paspor-001",
        "query": "Apa persyaratan membuat paspor?",
    },
    {
        "id": "alamat-001",
        "query": "Bagaimana cara perubahan alamat?",
    },
]

results = []

print()
print("=" * 80)
print("RETRIEVAL TEST")
print("=" * 80)

# ============================================================================
# RETRIEVAL METHOD DETECTION
# ============================================================================
retrieval_method = None

for candidate in [
    "search_knowledge",
    "search",
    "retrieve",
    "query",
]:
    if hasattr(engine, candidate):
        retrieval_method = candidate
        break

if retrieval_method is None:
    print()
    print("[ERROR] Tidak ditemukan API retrieval pada KnowledgeEngine.")
    raise SystemExit(5)

print()
print("[RETRIEVAL API]", retrieval_method)

# ============================================================================
# EXECUTE TEST
# ============================================================================
for test in tests:

    print()
    print("-" * 80)
    print(f"[TEST] {test['id']}")
    print(f"QUERY : {test['query']}")

    try:
        method = getattr(engine, retrieval_method)

        result = method(test["query"])

        print("[RESULT TYPE]", type(result).__name__)

        if isinstance(result, dict):
            payload = result

        elif isinstance(result, list):
            payload = {
                "items": result,
            }

        else:
            payload = {
                "value": str(result),
            }

        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
                default=str,
            )[:12000]
        )

        results.append(
            {
                "id": test["id"],
                "query": test["query"],
                "status": "PASS",
                "result": payload,
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
# SAVE RESULT
# ============================================================================
output = PROJECT_ROOT / "data" / "knowledge" / "retrieval_test_result.json"
output.parent.mkdir(parents=True, exist_ok=True)

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

failed = len(results) - passed

print()
print("=" * 80)
print("RETRIEVAL TEST SELESAI")
print("=" * 80)
print(f"PROJECT : {PROJECT_ROOT}")
print(f"RAG     : {rag_module.__file__}")
print(f"RESULT  : {output}")
print(f"PASS    : {passed}/{len(results)}")
print(f"FAIL    : {failed}/{len(results)}")
print("=" * 80)
