from pathlib import Path
import re
import shutil
from datetime import datetime

ROOT = Path(r"C:\Users\dmaza\mcp-starter")
TARGET = ROOT / "developer_core_engine.py"

if not TARGET.exists():
    raise SystemExit("developer_core_engine.py tidak ditemukan.")

text = TARGET.read_text(encoding="utf-8")

backup = TARGET.with_name(
    f"developer_core_engine.before_quality_{datetime.now():%Y%m%d_%H%M%S}.py"
)
shutil.copy2(TARGET, backup)

print(f"Backup dibuat: {backup.name}")

# ------------------------------------------------------------
# 1. collect_source_files
# ------------------------------------------------------------
start = text.find("def collect_source_files():")
end = text.find("\ndef build_source_index():", start)

if start == -1 or end == -1:
    raise SystemExit("Fungsi collect_source_files() tidak ditemukan dengan struktur yang diharapkan.")

new_collect = r'''def collect_source_files():
    """
    Mengambil source production yang relevan untuk Developer Core.

    Backup, cache, hasil eksperimen, repository metadata,
    dan file sementara tidak dijadikan knowledge utama.
    """

    files = []

    excluded_dirs = {
        "__pycache__",
        ".git",
        ".venv",
        "backup",
        "backups",
        "research",
        "archive",
        "archives",
        "quarantine",
        "benchmark",
        "node_modules",
        "graphify-out",
    }

    excluded_name_tokens = {
        ".bak",
        ".backup",
        "backup_",
        "_backup",
        "before_",
        "after_",
    }

    allowed_extensions = {
        ".py",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".md",
    }

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in allowed_extensions:
            continue

        relative = path.relative_to(ROOT)
        parts_lower = {part.lower() for part in relative.parts}

        if parts_lower.intersection(excluded_dirs):
            continue

        name_lower = path.name.lower()

        if any(token in name_lower for token in excluded_name_tokens):
            continue

        files.append(path)

    files.sort(key=lambda p: str(p).lower())

    return files
'''

text = text[:start] + new_collect + text[end:]

# ------------------------------------------------------------
# 2. search_graph
# ------------------------------------------------------------
start = text.find("def search_graph(")
end = text.find("\ndef get_node(", start)

if start == -1 or end == -1:
    raise SystemExit("Fungsi search_graph() tidak ditemukan.")

new_search_graph = r'''def search_graph(query: str, limit: int = 30):
    """
    Pencarian Graphify yang memprioritaskan symbol production
    dan mengurangi noise dari generic/import symbols.
    """

    q = (query or "").strip().lower()

    if not q:
        return []

    terms = [
        x for x in re.findall(r"[a-zA-Z0-9_]+", q)
        if x not in {
            "apa", "bagaimana", "dimana", "mana", "yang",
            "dengan", "untuk", "dari", "dan", "atau",
            "saya", "ingin", "mau", "cek", "jelaskan",
            "jelaskanlah", "tentang", "struktur",
        }
    ]

    generic_symbols = {
        "any", "path", "dict", "list", "str", "int",
        "float", "bool", "set", "tuple", "bytes",
        "basemodel", "request", "response",
    }

    results = []

    graph_nodes = GRAPH.get("nodes", [])

    for node in graph_nodes:
        name = str(node.get("name") or "")
        node_id = str(node.get("id") or "")
        path = str(
            node.get("path")
            or node.get("file")
            or node.get("source")
            or ""
        )

        haystack = f"{name} {path} {node_id}".lower()
        score = 0

        if q == name.lower():
            score += 1000

        if q in name.lower():
            score += 250

        if q in path.lower():
            score += 180

        for term in terms:
            if term in name.lower():
                score += 80

            if term in path.lower():
                score += 45

            if term in haystack:
                score += 10

        if name.lower() in generic_symbols:
            score -= 40

        if path.lower().startswith("app\\") or path.lower().startswith("app/"):
            score += 20

        if score <= 0:
            continue

        results.append({
            "id": node_id,
            "name": name,
            "path": path,
            "score": score,
            "type": node.get("type"),
            "engine": node.get("engine"),
            "role": node.get("role"),
        })

    results.sort(
        key=lambda x: (
            -x["score"],
            x["path"].lower(),
            x["name"].lower(),
        )
    )

    deduped = []
    seen = set()

    for item in results:
        key = (
            item.get("path") or "",
            item.get("name") or "",
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

# ------------------------------------------------------------
# 3. search_source
# ------------------------------------------------------------
start = text.find("def search_source(")
end = text.find("\ndef build_graph_context(", start)

if start == -1 or end == -1:
    raise SystemExit("Fungsi search_source() tidak ditemukan.")

new_search_source = r'''def search_source(query: str, limit: int = 8):
    """
    Pencarian source code production.
    File app/ dan engine inti diberi prioritas.
    """

    q = (query or "").strip().lower()

    if not q:
        return []

    terms = [
        x for x in re.findall(r"[a-zA-Z0-9_]+", q)
        if len(x) >= 2
    ]

    priority_tokens = {
        "routes.py": 35,
        "engine.py": 20,
        "rag.py": 20,
        "workflow": 15,
        "hermes": 15,
        "ollama": 15,
        "knowledge": 20,
    }

    results = []

    for path in collect_source_files():
        try:
            relative = str(path.relative_to(ROOT))
            content = path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except Exception:
            continue

        path_lower = relative.lower()
        content_lower = content.lower()

        score = 0

        if q in path_lower:
            score += 120

        for term in terms:
            if term in path_lower:
                score += 45

            occurrences = content_lower.count(term)
            if occurrences:
                score += min(occurrences, 8) * 5

        if path_lower.startswith("app\\") or path_lower.startswith("app/"):
            score += 15

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
        key=lambda x: (
            -x["score"],
            x["path"].lower(),
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

# ------------------------------------------------------------
# 4. build_graph_context
# ------------------------------------------------------------
start = text.find("def build_graph_context(")
end = text.find("\ndef graph_rag(", start)

if start == -1 or end == -1:
    raise SystemExit("Fungsi build_graph_context() tidak ditemukan.")

new_context = r'''def build_graph_context(query: str):
    """
    Membentuk context ringkas dari Graph RAG + Source RAG.
    """

    graph_results = search_graph(query, limit=15)
    source_results = search_source(query, limit=5)

    lines = []

    lines.append("=== DEVELOPER CORE EVIDENCE ===")
    lines.append("")

    lines.append("GRAPH RESULTS:")

    if graph_results:
        for item in graph_results:
            lines.append(
                f"- {item.get('name')} | "
                f"path={item.get('path')} | "
                f"type={item.get('type')} | "
                f"score={item.get('score')}"
            )
    else:
        lines.append("- Tidak ada graph result yang relevan.")

    lines.append("")
    lines.append("SOURCE RESULTS:")

    if source_results:
        for item in source_results:
            content = item.get("content", "")
            snippet = content[:3500]

            lines.append(
                f"\n--- {item.get('path')} "
                f"(score={item.get('score')}) ---"
            )
            lines.append(snippet)
    else:
        lines.append("- Tidak ada source result yang relevan.")

    return "\n".join(lines)
'''

text = text[:start] + new_context + text[end:]

# ------------------------------------------------------------
# 5. pastikan import re tersedia
# ------------------------------------------------------------
if not re.search(r"^\s*import re\s*$", text, re.MULTILINE):
    import_match = re.search(r"^(import .+|from .+ import .+)$", text, re.MULTILINE)

    if import_match:
        pos = import_match.end()
        text = text[:pos] + "\nimport re" + text[pos:]
    else:
        text = "import re\n" + text

TARGET.write_text(text, encoding="utf-8")

print("")
print("PATCH BERHASIL.")
print(f"File: {TARGET}")
print(f"Backup: {backup}")
print("")
print("Fungsi yang diperbarui:")
print("  - collect_source_files")
print("  - search_graph")
print("  - search_source")
print("  - build_graph_context")
