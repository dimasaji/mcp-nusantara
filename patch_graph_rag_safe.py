from pathlib import Path
from datetime import datetime
import py_compile

path = Path("developer_core_engine.py")
text = path.read_text(encoding="utf-8")
lines = text.splitlines(keepends=True)

# Cari fungsi graph_rag
start = None

for i, line in enumerate(lines):
    if line.startswith("def graph_rag(query: str):"):
        start = i
        break

if start is None:
    print("ERROR: def graph_rag() tidak ditemukan.")
    raise SystemExit(1)

# Cari akhir fungsi:
# baris berikutnya yang tidak kosong dan kembali ke indent level 0
end = None

for i in range(start + 1, len(lines)):
    line = lines[i]

    if not line.strip():
        continue

    if not line.startswith((" ", "\t")):
        end = i
        break

if end is None:
    end = len(lines)

# Backup
backup = path.with_name(
    f"developer_core_engine.before_safe_graph_rag_"
    f"{datetime.now():%Y%m%d_%H%M%S}.py"
)

backup.write_text(text, encoding="utf-8")

new_function = '''def graph_rag(query: str):
    """
    Developer Core RAG aggregator.

    Menggabungkan:
    - Graph RAG
    - Source RAG
    - Production Knowledge RAG
    """

    graph_results = search_graph(
        query,
        12,
    )

    source_results = search_source(
        query,
        6,
    )

    production_evidence = search_production_knowledge(
        query=query,
        top_k=5,
    )

    production_evidence_text = (
        build_production_evidence_text(
            production_evidence
        )
    )

    context = (
        "=== DEVELOPER CORE EVIDENCE ===\\n\\n"
        "=== GRAPH RAG ===\\n"
        + str(graph_results)
        + "\\n\\n"
        "=== SOURCE RAG ===\\n"
        + str(source_results)
        + "\\n\\n"
        "=== PRODUCTION KNOWLEDGE EVIDENCE ===\\n"
        + production_evidence_text
    )

    return {
        "query": query,
        "graph": graph_results,
        "source": source_results,
        "production_knowledge": production_evidence,
        "production_evidence_text": production_evidence_text,
        "context": context,
    }


'''

new_lines = (
    lines[:start]
    + new_function.splitlines(keepends=True)
    + lines[end:]
)

path.write_text(
    "".join(new_lines),
    encoding="utf-8",
)

# Syntax validation
try:
    py_compile.compile(
        str(path),
        doraise=True,
    )
except Exception as e:
    print("PATCH GAGAL - SYNTAX ERROR")
    print(e)

    path.write_text(
        backup.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    print("FILE DIKEMBALIKAN KE BACKUP.")
    raise SystemExit(1)

# Pastikan struktur penting tetap ada
check = path.read_text(encoding="utf-8")

required = [
    "app = FastAPI",
    'def graph_rag(query: str):',
    'def search_production_knowledge(',
    'def build_production_evidence_text(',
    '@app.get("/v1/rag/context")',
]

missing = [
    item
    for item in required
    if item not in check
]

if missing:
    print("PATCH DIBATALKAN.")
    print("Bagian hilang:")

    for item in missing:
        print(" -", item)

    path.write_text(
        backup.read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    print("FILE DIKEMBALIKAN KE BACKUP.")
    raise SystemExit(1)

print()
print("=" * 60)
print("SAFE GRAPH RAG PATCH BERHASIL")
print("=" * 60)
print("Backup:", backup.name)
print()
print("[OK] Graph RAG")
print("[OK] Source RAG")
print("[OK] Production Knowledge RAG")
print("[OK] Evidence Context")
print("[OK] FastAPI app")
print("[OK] /v1/rag/context")
print("[OK] Syntax")
print("=" * 60)
