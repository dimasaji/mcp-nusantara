from pathlib import Path
import ast
import shutil
import sys
import py_compile
import importlib

path = Path(r"app/knowledge/rag.py")
backup = path.with_suffix(".py.bak")

print("=" * 80)
print("NUSANTARA AI — FIX RAG BOM + CANONICAL HYBRIDRAG")
print("=" * 80)

if not path.exists():
    print("ERROR: app/knowledge/rag.py tidak ditemukan")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 1. BACKUP
# ---------------------------------------------------------------------------
if not backup.exists():
    shutil.copy2(path, backup)
    print(f"[BACKUP] dibuat: {backup}")
else:
    print(f"[BACKUP] tersedia: {backup}")

# ---------------------------------------------------------------------------
# 2. READ RAW BYTES
# ---------------------------------------------------------------------------
raw = path.read_bytes()

print(f"[FILE] ukuran: {len(raw)} bytes")

# UTF-8 BOM = EF BB BF
if raw.startswith(b"\xef\xbb\xbf"):
    print("[BOM] ditemukan: UTF-8 BOM")
    raw = raw[3:]
    path.write_bytes(raw)
    print("[BOM] berhasil dihapus")
else:
    print("[BOM] tidak ditemukan")

# ---------------------------------------------------------------------------
# 3. READ AS UTF-8
# ---------------------------------------------------------------------------
text = path.read_text(encoding="utf-8")

# Safety: remove accidental FEFF anywhere at beginning
if text.startswith("\ufeff"):
    text = text.lstrip("\ufeff")
    path.write_text(text, encoding="utf-8")
    print("[BOM] karakter U+FEFF tambahan dihapus")

# ---------------------------------------------------------------------------
# 4. AST CHECK
# ---------------------------------------------------------------------------
try:
    tree = ast.parse(text)
    print("[AST] PASS")
except SyntaxError as exc:
    print()
    print("[AST] FAIL")
    print(exc)
    print()
    print("Tidak ada perubahan lanjutan dilakukan.")
    print("Backup tetap tersedia:", backup)
    sys.exit(2)

# ---------------------------------------------------------------------------
# 5. DISCOVER RAG CLASSES
# ---------------------------------------------------------------------------
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
print("CLASS DALAM rag.py:")
for item in classes:
    print(
        f"  - {item['name']} "
        f"(line {item['line']}) "
        f"methods={sorted(item['methods'])}"
    )

# ---------------------------------------------------------------------------
# 6. FIND CANONICAL RAG IMPLEMENTATION
# ---------------------------------------------------------------------------
preferred_names = [
    "KnowledgeRAG",
    "RAGEngine",
    "RAG",
    "KnowledgeRetriever",
    "KnowledgeEngine",
]

candidate = None

for preferred in preferred_names:
    for item in classes:
        if item["name"] == preferred:
            candidate = item
            break

    if candidate:
        break

# Capability-based fallback
if candidate is None:
    scored = []

    for item in classes:
        methods = item["methods"]
        score = 0

        if "search_knowledge" in methods:
            score += 10

        if "search" in methods:
            score += 8

        if "retrieve" in methods:
            score += 8

        if "query" in methods:
            score += 5

        if "rerank" in methods or "rerank_evidence" in methods:
            score += 3

        if "_apply_relevance_gate" in methods:
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
    print("[ERROR] Tidak ditemukan class RAG yang dapat dijadikan HybridRAG.")
    print()
    print("RAG TIDAK DIUBAH.")
    sys.exit(3)

target_class = candidate["name"]

print()
print(f"[RAG IMPLEMENTATION] {target_class}")

# ---------------------------------------------------------------------------
# 7. ADD CANONICAL ALIAS
# ---------------------------------------------------------------------------
if any(item["name"] == "HybridRAG" for item in classes):
    print("[HYBRIDRAG] sudah ada")
else:
    alias_block = f'''

# ---------------------------------------------------------------------------
# NUSANTARA CANONICAL RAG API
# ---------------------------------------------------------------------------
# Canonical public interface for Nusantara Core.
# The implementation remains in {target_class}.
# This is only a compatibility alias.
# ---------------------------------------------------------------------------

HybridRAG = {target_class}
'''

    path.write_text(
        text.rstrip() + alias_block + "\n",
        encoding="utf-8",
    )

    print(f"[HYBRIDRAG] alias ditambahkan -> {target_class}")

# ---------------------------------------------------------------------------
# 8. COMPILE
# ---------------------------------------------------------------------------
try:
    py_compile.compile(
        str(path),
        doraise=True,
    )
    print("[COMPILE] PASS")
except Exception as exc:
    print()
    print("[COMPILE] FAIL")
    print(exc)
    print()
    print("[RESTORE] mengembalikan backup...")

    shutil.copy2(backup, path)

    print("[RESTORE] selesai")
    sys.exit(4)

# ---------------------------------------------------------------------------
# 9. IMPORT
# ---------------------------------------------------------------------------
try:
    if "app.knowledge.rag" in sys.modules:
        del sys.modules["app.knowledge.rag"]

    rag = importlib.import_module("app.knowledge.rag")

    if not hasattr(rag, "HybridRAG"):
        print("[IMPORT] FAIL: HybridRAG tidak ditemukan")
        sys.exit(5)

    hybrid = rag.HybridRAG

    print(f"[IMPORT] PASS")
    print(f"[IMPORT] HybridRAG = {hybrid}")
    print(f"[IMPORT] module     = {rag.__file__}")

except Exception as exc:
    print()
    print("[IMPORT] FAIL")
    print(exc)
    print()
    print("[RESTORE] mengembalikan backup...")

    shutil.copy2(backup, path)

    print("[RESTORE] selesai")
    sys.exit(6)

# ---------------------------------------------------------------------------
# 10. KNOWLEDGE ENGINE IMPORT
# ---------------------------------------------------------------------------
try:
    from app.knowledge.engine import KnowledgeEngine
    from app.knowledge.grounding import EvidenceGroundingGuard

    print("[ENGINE IMPORT] PASS")
    print("[GROUNDING IMPORT] PASS")

except Exception as exc:
    print()
    print("[KNOWLEDGE IMPORT] FAIL")
    print(exc)
    sys.exit(7)

print()
print("=" * 80)
print("NUSANTARA RAG FIX BERHASIL")
print("=" * 80)
print("BOM              : FIXED")
print("RAG SYNTAX       : PASS")
print("HybridRAG        : AVAILABLE")
print("KnowledgeEngine  : IMPORT PASS")
print("GroundingGuard   : IMPORT PASS")
print("=" * 80)
