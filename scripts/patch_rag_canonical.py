from pathlib import Path
import ast
import shutil
import sys

path = Path(r"app/knowledge/rag.py")

if not path.exists():
    print("ERROR: app/knowledge/rag.py tidak ditemukan")
    sys.exit(1)

text = path.read_text(encoding="utf-8")

print("=" * 80)
print("NUSANTARA AI — RAG CANONICAL API PATCH")
print("=" * 80)

# ------------------------------------------------------------
# 1. BACKUP
# ------------------------------------------------------------

backup = path.with_suffix(".py.bak")

if not backup.exists():
    shutil.copy2(path, backup)
    print(f"[BACKUP] {backup}")
else:
    print(f"[BACKUP] sudah ada: {backup}")

# ------------------------------------------------------------
# 2. PARSE SOURCE
# ------------------------------------------------------------

try:
    tree = ast.parse(text)
except SyntaxError as exc:
    print("ERROR: rag.py memiliki syntax error")
    print(exc)
    sys.exit(1)

classes = []

for node in tree.body:
    if isinstance(node, ast.ClassDef):
        methods = {
            item.name
            for item in node.body
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        classes.append(
            {
                "name": node.name,
                "methods": methods,
                "line": node.lineno,
            }
        )

print()
print("CLASS YANG DITEMUKAN:")
for item in classes:
    print(
        f"  - {item['name']} "
        f"(line {item['line']}) "
        f"methods={sorted(item['methods'])}"
    )

# ------------------------------------------------------------
# 3. CARI IMPLEMENTASI RAG
# ------------------------------------------------------------

preferred_names = [
    "KnowledgeRAG",
    "RAGEngine",
    "RAG",
    "KnowledgeRetriever",
    "KnowledgeEngine",
]

candidate = None

# Prioritas nama class
for preferred in preferred_names:
    for item in classes:
        if item["name"] == preferred:
            candidate = item
            break
    if candidate:
        break

# Jika tidak ditemukan, gunakan capability-based detection
if candidate is None:
    required_method_groups = [
        {"search_knowledge"},
        {"search"},
        {"retrieve"},
        {"query"},
    ]

    scored = []

    for item in classes:
        methods = item["methods"]
        score = 0

        if methods & {"search_knowledge"}:
            score += 10

        if methods & {"search"}:
            score += 8

        if methods & {"retrieve"}:
            score += 8

        if methods & {"query"}:
            score += 5

        if methods & {"rerank", "rerank_evidence"}:
            score += 3

        if methods & {"_apply_relevance_gate"}:
            score += 5

        if score > 0:
            scored.append((score, item))

    if scored:
        scored.sort(
            key=lambda x: (
                x[0],
                -x[1]["line"],
            ),
            reverse=True,
        )
        candidate = scored[0][1]

if candidate is None:
    print()
    print("ERROR: Tidak ditemukan class RAG yang dapat dijadikan")
    print("       canonical HybridRAG.")
    print()
    print("Tidak ada perubahan source dilakukan.")
    sys.exit(2)

target_class = candidate["name"]

print()
print(f"[RAG IMPLEMENTATION] {target_class}")

# ------------------------------------------------------------
# 4. CEK APAKAH HybridRAG SUDAH ADA
# ------------------------------------------------------------

if any(item["name"] == "HybridRAG" for item in classes):
    print("[OK] HybridRAG sudah tersedia.")
else:
    alias_block = f'''

# ---------------------------------------------------------------------------
# NUSANTARA CANONICAL RAG API
# ---------------------------------------------------------------------------
# Compatibility alias.
#
# Nusantara Core menggunakan nama publik HybridRAG sebagai canonical
# interface. Implementasi RAG tetap berada pada class {target_class}.
# Alias ini tidak menggandakan implementasi dan tidak mengubah algoritma
# retrieval, embedding, reranking, atau relevance gate.
# ---------------------------------------------------------------------------

HybridRAG = {target_class}
'''

    # Jangan menambahkan alias jika file sudah memiliki marker
    if "NUSANTARA CANONICAL RAG API" not in text:
        path.write_text(
            text.rstrip() + alias_block + "\n",
            encoding="utf-8",
        )

        print("[PATCH] HybridRAG alias ditambahkan.")
    else:
        print("[SKIP] canonical RAG marker sudah ada.")

# ------------------------------------------------------------
# 5. COMPILE
# ------------------------------------------------------------

import py_compile

try:
    py_compile.compile(
        str(path),
        doraise=True,
    )
    print("[COMPILE] PASS")
except Exception as exc:
    print("[COMPILE] FAIL")
    print(exc)

    print()
    print("RESTORE BACKUP...")

    if backup.exists():
        shutil.copy2(backup, path)
        print("[RESTORE] rag.py dikembalikan dari backup.")

    sys.exit(3)

# ------------------------------------------------------------
# 6. IMPORT TEST
# ------------------------------------------------------------

try:
    import importlib

    if "app.knowledge.rag" in sys.modules:
        del sys.modules["app.knowledge.rag"]

    rag = importlib.import_module("app.knowledge.rag")

    if not hasattr(rag, "HybridRAG"):
        print("[IMPORT] FAIL: HybridRAG tidak tersedia")
        sys.exit(4)

    hybrid = getattr(rag, "HybridRAG")

    print(f"[IMPORT] PASS: HybridRAG -> {hybrid}")

except Exception as exc:
    print("[IMPORT] FAIL")
    print(exc)

    print()
    print("RESTORE BACKUP...")

    if backup.exists():
        shutil.copy2(backup, path)
        print("[RESTORE] rag.py dikembalikan dari backup.")

    sys.exit(5)

print()
print("=" * 80)
print("RAG CANONICAL API PATCH BERHASIL")
print("=" * 80)
print()
print(f"HybridRAG -> {target_class}")
print(f"Backup    -> {backup}")
print()
print("Nusantara Core sekarang memiliki canonical RAG interface:")
print("HybridRAG")
print("=" * 80)
