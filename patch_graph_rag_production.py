from pathlib import Path
from datetime import datetime
import py_compile
import re

path = Path("developer_core_engine.py")

text = path.read_text(encoding="utf-8")

backup = path.with_name(
    f"developer_core_engine.before_graph_rag_production_"
    f"{datetime.now():%Y%m%d_%H%M%S}.py"
)

backup.write_text(text, encoding="utf-8")

pattern = re.compile(
    r'(?ms)^def graph_rag\(query: str\):\n.*?(?=^@app\.get\("/v1/graph/summary"\))'
)

replacement = '''def graph_rag(query: str):
    """
    Developer Core RAG aggregator.

    Menggabungkan:
    1. Graph RAG
    2. Source RAG
    3. Production Knowledge RAG

    Production Knowledge digunakan sebagai evidence resmi/
    terstruktur dan tidak menggantikan Graph atau Source RAG.
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

    return {
        "query": query,

        "graph": graph_results,

        "source": source_results,

        "production_knowledge": (
            production_evidence
        ),

        "production_evidence_text": (
            production_evidence_text
        ),

        "context": (
            "=== DEVELOPER CORE EVIDENCE ===\\n\\n"
            "=== GRAPH RAG ===\\n"
            + str(graph_results)
            + "\\n\\n"
            "=== SOURCE RAG ===\\n"
            + str(source_results)
            + "\\n\\n"
            "=== PRODUCTION KNOWLEDGE EVIDENCE ===\\n"
            + production_evidence_text
        ),
    }


'''

match = pattern.search(text)

if not match:
    print("ERROR: fungsi graph_rag() tidak ditemukan.")
    print("FILE TIDAK DIUBAH.")
    raise SystemExit(1)

new_text = text[:match.start()] + replacement + text[match.end():]

path.write_text(new_text, encoding="utf-8")

try:
    py_compile.compile(
        str(path),
        doraise=True,
    )
except Exception as e:
    print("ERROR SYNTAX:")
    print(e)
    path.write_text(
        backup.read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    print("FILE DIKEMBALIKAN DARI BACKUP.")
    raise SystemExit(1)

print("")
print("=" * 60)
print("PRODUCTION RAG BERHASIL DIINTEGRASIKAN")
print("=" * 60)
print("Backup :", backup.name)
print("File   :", path)
print("")
print("graph_rag() sekarang:")
print("  [OK] Graph RAG")
print("  [OK] Source RAG")
print("  [OK] Production Knowledge RAG")
print("  [OK] Evidence Context")
print("")
print("SYNTAX : OK")
print("=" * 60)
