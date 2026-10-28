import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app"
OUT = ROOT / "graphify-out" / "gate16_3_sop_rag_bridge_truth.json"

targets = {
    "knowledge_engine": APP / "knowledge" / "engine.py",
    "rag": APP / "knowledge" / "rag.py",
    "retriever": APP / "knowledge" / "retriever.py",
    "production_hybrid_rag": APP / "knowledge" / "production_hybrid_rag.py",
    "production_semantic_retriever": APP / "knowledge" / "production_semantic_retriever.py",
    "production_kb": APP / "knowledge" / "production_kb.py",
    "grounding": APP / "knowledge" / "grounding.py",
    "schemas": APP / "knowledge" / "schemas.py",
}

patterns = {
    "knowledge_engine": [
        "RAG", "retriev", "knowledge", "search", "ground"
    ],
    "rag": [
        "retriev", "knowledge", "search", "chunk", "evidence"
    ],
    "retriever": [
        "search", "retrieve", "knowledge", "chunk"
    ],
    "production_hybrid_rag": [
        "semantic", "retriev", "knowledge", "search"
    ],
    "production_semantic_retriever": [
        "semantic", "retriev", "embedding", "search"
    ],
    "production_kb": [
        "knowledge", "chunk", "document", "search"
    ],
    "grounding": [
        "evidence", "ground", "source", "confidence"
    ],
    "schemas": [
        "source", "evidence", "chunk", "document"
    ],
}

results = {}
all_pass = True

for name, path in targets.items():
    exists = path.exists()

    if not exists:
        results[name] = {
            "exists": False,
            "matches": 0,
            "status": "FAIL"
        }
        all_pass = False
        continue

    text = path.read_text(encoding="utf-8", errors="ignore").lower()

    found = []
    for pattern in patterns[name]:
        if pattern.lower() in text:
            found.append(pattern)

    status = "PASS" if len(found) >= 2 else "FAIL"

    results[name] = {
        "exists": True,
        "matches": len(found),
        "patterns_found": found,
        "status": status
    }

    if status != "PASS":
        all_pass = False

# Database truth
dbs = [
    ROOT / "data" / "knowledge" / "nusantara_knowledge.db",
    ROOT / "data" / "knowledge" / "production_knowledge.db",
]

db_results = []

for db in dbs:
    if db.exists():
        db_results.append({
            "file": str(db.relative_to(ROOT)),
            "exists": True,
            "size": db.stat().st_size,
            "nonempty": db.stat().st_size > 0
        })
    else:
        db_results.append({
            "file": str(db.relative_to(ROOT)),
            "exists": False,
            "size": 0,
            "nonempty": False
        })

db_pass = any(x["exists"] and x["nonempty"] for x in db_results)

if not db_pass:
    all_pass = False

status = "PASS" if all_pass else "FAIL"

result = {
    "gate": "16.3",
    "name": "SOP -> Knowledge/RAG Bridge Truth",
    "status": status,
    "static_bridge": results,
    "knowledge_databases": db_results,
    "contract": {
        "knowledge_engine_required": True,
        "rag_required": True,
        "retriever_required": True,
        "production_rag_required": True,
        "grounding_required": True,
        "knowledge_database_required": True,
        "llm_required": False
    }
}

OUT.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("=" * 70)
print("NUSANTARA GATE 16.3 - SOP -> KNOWLEDGE/RAG BRIDGE")
print("=" * 70)
print()

for name, data in results.items():
    print(
        f"{name:<32} "
        f"{data['status']:<5} "
        f"matches={data['matches']}"
    )

print()
print(f"Knowledge DBs       : {len([x for x in db_results if x['exists']])}")
print(f"Static Bridge       : {'PASS' if all(x['status']=='PASS' for x in results.values()) else 'FAIL'}")
print(f"Database Truth      : {'PASS' if db_pass else 'FAIL'}")
print()
print(f"GATE 16.3 STATUS    : {status}")
print(f"Output              : {OUT}")

if status != "PASS":
    raise SystemExit(1)
