import json
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "knowledge" / "production_knowledge.db"
OUT = ROOT / "graphify-out" / "gate16_5_evidence_grounding_truth.json"

print("=" * 70)
print("NUSANTARA GATE 16.5 - EVIDENCE & GROUNDING TRUTH")
print("=" * 70)
print()

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row

tables = [
    r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
]

checks = {}

# ------------------------------------------------------------
# 1. Documents
# ------------------------------------------------------------
checks["documents_table"] = "documents" in tables
checks["chunks_table"] = "chunks" in tables
checks["source_registry_table"] = "source_registry" in tables

print(
    "Documents table       :",
    "PASS" if checks["documents_table"] else "FAIL"
)
print(
    "Chunks table          :",
    "PASS" if checks["chunks_table"] else "FAIL"
)
print(
    "Source registry       :",
    "PASS" if checks["source_registry_table"] else "FAIL"
)

# ------------------------------------------------------------
# 2. Inspect columns
# ------------------------------------------------------------
schema = {}

for table in ["documents", "chunks", "source_registry", "chunk_embeddings"]:
    if table in tables:
        cols = [
            {
                "name": r[1],
                "type": r[2]
            }
            for r in conn.execute(
                f'PRAGMA table_info("{table}")'
            ).fetchall()
        ]
        schema[table] = cols

print()

# ------------------------------------------------------------
# 3. Count records
# ------------------------------------------------------------
counts = {}

for table in ["documents", "chunks", "source_registry", "chunk_embeddings"]:
    if table in tables:
        try:
            counts[table] = conn.execute(
                f'SELECT COUNT(*) FROM "{table}"'
            ).fetchone()[0]
        except Exception:
            counts[table] = 0

print("Record counts:")
for table, count in counts.items():
    print(f"  {table:<22}: {count}")

checks["documents_nonempty"] = counts.get("documents", 0) > 0
checks["chunks_nonempty"] = counts.get("chunks", 0) > 0
checks["source_registry_nonempty"] = counts.get("source_registry", 0) > 0

# ------------------------------------------------------------
# 4. Check provenance-like fields
# ------------------------------------------------------------
provenance_keywords = [
    "source",
    "document",
    "doc",
    "file",
    "path",
    "title",
    "page",
    "chunk",
    "section",
    "metadata",
]

provenance_fields = {}

for table, cols in schema.items():
    found = [
        c["name"]
        for c in cols
        if any(k in c["name"].lower() for k in provenance_keywords)
    ]
    provenance_fields[table] = found

for table in ["documents", "chunks", "source_registry"]:
    found = provenance_fields.get(table, [])
    print(
        f"Provenance {table:<14}: "
        f"{'PASS' if found else 'FAIL'} "
        f"{found}"
    )
    checks[f"provenance_{table}"] = bool(found)

# ------------------------------------------------------------
# 5. Check grounding implementation
# ------------------------------------------------------------
grounding_file = ROOT / "app" / "knowledge" / "grounding.py"
rag_file = ROOT / "app" / "knowledge" / "rag.py"

grounding_text = (
    grounding_file.read_text(
        encoding="utf-8",
        errors="ignore"
    ).lower()
    if grounding_file.exists()
    else ""
)

rag_text = (
    rag_file.read_text(
        encoding="utf-8",
        errors="ignore"
    ).lower()
    if rag_file.exists()
    else ""
)

grounding_patterns = [
    "evidence",
    "ground",
    "source",
    "confidence",
    "citation",
]

grounding_found = [
    p for p in grounding_patterns
    if p in grounding_text
]

rag_evidence_found = [
    p for p in [
        "evidence",
        "source",
        "chunk",
        "retriev",
    ]
    if p in rag_text
]

checks["grounding_implementation"] = len(grounding_found) >= 2
checks["rag_evidence_support"] = len(rag_evidence_found) >= 2

print()
print(
    "Grounding implementation:",
    "PASS" if checks["grounding_implementation"] else "FAIL",
    grounding_found
)

print(
    "RAG evidence support   :",
    "PASS" if checks["rag_evidence_support"] else "FAIL",
    rag_evidence_found
)

# ------------------------------------------------------------
# 6. Sample actual chunk provenance
# ------------------------------------------------------------
samples = []

if "chunks" in tables:
    try:
        rows = conn.execute(
            'SELECT * FROM "chunks" LIMIT 5'
        ).fetchall()

        for row in rows:
            item = {}
            for key in row.keys():
                value = row[key]

                if isinstance(value, bytes):
                    value = f"<binary:{len(value)} bytes>"

                if isinstance(value, str) and len(value) > 300:
                    value = value[:300]

                item[key] = value

            samples.append(item)

    except Exception as exc:
        samples.append({"error": str(exc)})

checks["chunk_samples_available"] = len(samples) > 0

print(
    "Chunk samples         :",
    "PASS" if checks["chunk_samples_available"] else "FAIL"
)

conn.close()

passed = sum(bool(v) for v in checks.values())
total = len(checks)

status = "PASS" if passed == total else "FAIL"

result = {
    "gate": "16.5",
    "name": "Evidence & Grounding Truth",
    "status": status,
    "timestamp": datetime.now().isoformat(),
    "database": str(DB),
    "tables": tables,
    "counts": counts,
    "schema": schema,
    "provenance_fields": provenance_fields,
    "grounding_patterns": grounding_found,
    "rag_evidence_patterns": rag_evidence_found,
    "chunk_samples": samples,
    "checks": {
        "passed": passed,
        "total": total,
        "results": checks,
    },
    "contract": {
        "documents_required": True,
        "chunks_required": True,
        "source_registry_required": True,
        "provenance_required": True,
        "grounding_required": True,
        "rag_evidence_required": True,
        "llm_required": False,
    }
}

OUT.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print()
print(f"Checks              : {passed} / {total}")
print(f"GATE 16.5 STATUS    : {status}")
print(f"Output              : {OUT}")

if status != "PASS":
    raise SystemExit(1)
