import json
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "knowledge" / "production_knowledge.db"
OUT = ROOT / "graphify-out" / "gate16_4_sop_retrieval_truth.json"

print("=" * 70)
print("NUSANTARA GATE 16.4 - SOP RETRIEVAL TRUTH")
print("=" * 70)
print()

if not DB.exists():
    print("Production DB : FAIL - tidak ditemukan")
    raise SystemExit(1)

conn = sqlite3.connect(str(DB))
conn.row_factory = sqlite3.Row

tables = [
    r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
]

print("Database       :", DB.name)
print("Tables         :", ", ".join(tables))
print()

# Cari tabel yang kemungkinan menyimpan knowledge/chunk/document
candidate_tables = [
    t for t in tables
    if any(x in t.lower() for x in (
        "chunk", "document", "knowledge", "content", "embedding"
    ))
]

print("Candidate tables:", candidate_tables)
print()

queries = [
    "KTP-el",
    "dokumen identitas penduduk",
    "akta kematian",
    "informasi data penduduk",
]

records = []

for query in queries:
    hits = []

    for table in candidate_tables:
        try:
            columns = [
                r[1] for r in conn.execute(
                    f'PRAGMA table_info("{table}")'
                ).fetchall()
            ]

            text_columns = [
                c for c in columns
                if any(x in c.lower() for x in (
                    "text", "content", "chunk", "document",
                    "title", "source", "name"
                ))
            ]

            if not text_columns:
                continue

            for col in text_columns:
                sql = (
                    f'SELECT rowid, "{col}" '
                    f'FROM "{table}" '
                    f'WHERE lower(CAST("{col}" AS TEXT)) LIKE ? '
                    f'LIMIT 10'
                )

                rows = conn.execute(
                    sql,
                    (f"%{query.lower()}%",)
                ).fetchall()

                for row in rows:
                    value = row[1]
                    if value:
                        hits.append({
                            "table": table,
                            "column": col,
                            "rowid": row[0],
                            "preview": str(value)[:300]
                        })

        except Exception:
            continue

    unique = {}
    for h in hits:
        key = (
            h["table"],
            h["column"],
            h["rowid"]
        )
        unique[key] = h

    hits = list(unique.values())

    records.append({
        "query": query,
        "hit_count": len(hits),
        "hits": hits[:10],
        "status": "PASS" if hits else "FAIL"
    })

    print(
        f"{query:<35} "
        f"{'PASS' if hits else 'FAIL':<5} "
        f"hits={len(hits)}"
    )

conn.close()

passed_queries = sum(
    1 for r in records
    if r["status"] == "PASS"
)

# Minimal contract:
# setidaknya dua query harus benar-benar menemukan knowledge.
status = "PASS" if passed_queries >= 2 else "FAIL"

result = {
    "gate": "16.4",
    "name": "SOP Retrieval Truth",
    "status": status,
    "timestamp": datetime.now().isoformat(),
    "database": str(DB),
    "tables": tables,
    "candidate_tables": candidate_tables,
    "queries": records,
    "contract": {
        "database_required": True,
        "retrieval_hits_required": True,
        "minimum_passing_queries": 2,
        "llm_required": False
    }
}

OUT.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print()
print("Passing queries :", passed_queries, "/", len(queries))
print("GATE 16.4 STATUS :", status)
print("Output           :", OUT)

if status != "PASS":
    raise SystemExit(1)
