from pathlib import Path
import shutil
from datetime import datetime

ROOT = Path(r"C:\Users\dmaza\mcp-starter")
TARGET = ROOT / "developer_core_engine.py"

text = TARGET.read_text(encoding="utf-8")

backup = TARGET.with_name(
    f"developer_core_engine.before_graph_adapter_{datetime.now():%Y%m%d_%H%M%S}.py"
)
shutil.copy2(TARGET, backup)

# ============================================================
# FIX 1 — search_graph() untuk format Graphify aktual
# ============================================================

start = text.find("def search_graph(")
end = text.find("\ndef get_node(", start)

if start == -1 or end == -1:
    raise SystemExit("search_graph() tidak ditemukan.")

new_search_graph = r'''def search_graph(query: str, limit: int = 30):
    """
    Graph RAG adapter untuk format graph.json Graphify.

    Format node Graphify:
      id
      label
      file_type
      source_file
      source_location
      _origin
    """

    q = (query or "").strip().lower()

    if not q:
        return []

    graph = load_graph()

    nodes = graph.get("nodes", [])

    if not isinstance(nodes, list):
        return []

    stopwords = {
        "apa", "bagaimana", "dimana", "mana", "yang",
        "dengan", "untuk", "dari", "dan", "atau",
        "saya", "ingin", "mau", "cek", "jelaskan",
        "jelaskanlah", "tentang", "struktur", "sistem",
    }

    terms = [
        token
        for token in re.findall(r"[a-zA-Z0-9_]+", q)
        if token not in stopwords and len(token) >= 2
    ]

    generic_symbols = {
        "any",
        "path",
        "dict",
        "list",
        "str",
        "int",
        "float",
        "bool",
        "set",
        "tuple",
        "bytes",
        "basemodel",
        "request",
        "response",
        "optional",
        "union",
    }

    results = []

    for node in nodes:

        if not isinstance(node, dict):
            continue

        node_id_value = str(node.get("id") or "")
        label = str(node.get("label") or "")
        source_file = str(node.get("source_file") or "")
        source_location = str(node.get("source_location") or "")
        file_type = str(node.get("file_type") or "")
        origin = str(node.get("_origin") or "")

        # Jangan tampilkan node yang sama sekali tidak punya identitas.
        if not node_id_value and not label and not source_file:
            continue

        haystack = " ".join([
            node_id_value,
            label,
            source_file,
            source_location,
            file_type,
            origin,
        ]).lower()

        score = 0

        label_lower = label.lower()
        source_lower = source_file.lower()
        id_lower = node_id_value.lower()

        # Exact match
        if q == label_lower:
            score += 1000

        if q == source_lower:
            score += 900

        # Query ditemukan sebagai substring
        if q in label_lower:
            score += 300

        if q in source_lower:
            score += 250

        if q in id_lower:
            score += 150

        # Token matching
        for term in terms:

            if term in label_lower:
                score += 100

            if term in source_lower:
                score += 80

            if term in id_lower:
                score += 40

            elif term in haystack:
                score += 15

        # Production application diberi prioritas.
        if (
            source_lower.startswith("app/")
            or source_lower.startswith("app\\")
        ):
            score += 30

        # Jangan biarkan generic AST symbols mendominasi.
        if label_lower in generic_symbols:
            score -= 100

        # Backup/research/archive harus dikeluarkan.
        blocked_tokens = (
            "backup",
            "before_openrouter",
            "after_openrouter",
            "__pycache__",
            ".venv",
            "research",
            "archive",
            "quarantine",
            "benchmark",
        )

        if any(token in source_lower for token in blocked_tokens):
            continue

        if score <= 0:
            continue

        results.append({
            "id": node_id_value,
            "name": label,
            "label": label,
            "path": source_file,
            "source_file": source_file,
            "source_location": source_location,
            "type": file_type,
            "origin": origin,
            "score": score,
        })

    results.sort(
        key=lambda item: (
            -item["score"],
            item["path"].lower(),
            item["name"].lower(),
        )
    )

    deduped = []
    seen = set()

    for item in results:

        key = (
            item.get("path", "").lower(),
            item.get("name", "").lower(),
        )

        if key in seen:
            continue

        seen.add(key)
        deduped.append(item)

        if len(deduped) >= limit:
            break

    return deduped
'''

text = text[:start] + new_search_graph + text[end:]

# ============================================================
# FIX 2 — search_source()
# ============================================================

start = text.find("def search_source(")
end = text.find("\ndef build_graph_context(", start)

if start == -1 or end == -1:
    raise SystemExit("search_source() tidak ditemukan.")

new_search_source = r'''def search_source(query: str, limit: int = 8):
    """
    Source RAG production-only search.

    Backup, archive, research, quarantine dan hasil eksperimen
    tidak boleh menjadi evidence utama.
    """

    q = (query or "").strip().lower()

    if not q:
        return []

    terms = [
        token
        for token in re.findall(r"[a-zA-Z0-9_]+", q)
        if len(token) >= 2
    ]

    priority_tokens = {
        "routes.py": 35,
        "engine.py": 20,
        "rag.py": 20,
        "workflow": 15,
        "hermes": 15,
        "ollama": 15,
        "knowledge": 20,
        "developer_core": 30,
    }

    blocked_tokens = {
        "backup",
        "backups",
        "before_openrouter",
        "after_openrouter",
        "research",
        "archive",
        "archives",
        "quarantine",
        "benchmark",
        "__pycache__",
        ".venv",
        "node_modules",
    }

    results = []

    for path in collect_source_files():

        try:
            relative = str(path.relative_to(ROOT))
        except ValueError:
            continue

        path_lower = relative.lower()

        if any(token in path_lower for token in blocked_tokens):
            continue

        try:
            content = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except Exception:
            continue

        content_lower = content.lower()

        score = 0

        if q in path_lower:
            score += 150

        for term in terms:

            if term in path_lower:
                score += 50

            occurrences = content_lower.count(term)

            if occurrences:
                score += min(occurrences, 8) * 5

        if (
            path_lower.startswith("app/")
            or path_lower.startswith("app\\")
        ):
            score += 25

        for token, weight in priority_tokens.items():
            if token in path_lower:
                score += weight

        if score <= 0:
            continue

        results.append({
            "path": relative,
            "score": score,
            "content": content,
        })

    results.sort(
        key=lambda item: (
            -item["score"],
            item["path"].lower(),
        )
    )

    deduped = []
    seen = set()

    for item in results:

        key = item["path"].lower()

        if key in seen:
            continue

        seen.add(key)
        deduped.append(item)

        if len(deduped) >= limit:
            break

    return deduped
'''

text = text[:start] + new_search_source + text[end:]

TARGET.write_text(text, encoding="utf-8")

print("============================================================")
print("GRAPHIFY ADAPTER PATCH BERHASIL")
print("============================================================")
print(f"Target : {TARGET}")
print(f"Backup : {backup}")
print("")
print("search_graph() -> format Graphify aktual")
print("search_source() -> production-only")
print("backup/research/archive -> excluded")
