from pathlib import Path

p = Path(r"C:\Users\dmaza\mcp-starter\developer_core_engine.py")
text = p.read_text(encoding="utf-8")

start = text.index("def collect_source_files():")
end = text.index("\ndef build_source_index():", start)

new_collect = r'''def collect_source_files():
    """
    Mengambil source production yang relevan.
    Backup, cache, hasil eksperimen dan file sementara
    tidak dijadikan knowledge utama.
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
    }

    excluded_name_tokens = {
        ".bak",
        ".backup",
        "backup_",
        "_backup",
        "before_",
        "after_",
    }

    for base in SOURCE_DIRS:
        if not base.exists():
            continue

        for p in base.rglob("*"):

            if not p.is_file():
                continue

            if p.suffix.lower() not in {
                ".py",
                ".md",
                ".json",
                ".yaml",
                ".yml",
                ".toml",
                ".txt",
            }:
                continue

            parts_lower = {
                str(part).lower()
                for part in p.parts
            }

            if parts_lower.intersection(excluded_dirs):
                continue

            name_lower = p.name.lower()

            if any(
                token in name_lower
                for token in excluded_name_tokens
            ):
                continue

            files.append(p)

    return sorted(
        set(files),
        key=lambda x: str(x).lower()
    )
'''

text = text[:start] + new_collect + text[end:]

start = text.index("def search_graph(")
end = text.index("\ndef get_node(", start)

new_graph = r'''def search_graph(q: str, limit: int = 30):
    """
    Structural graph search.

    Prioritas:
    1. nama/path exact
    2. path relevan
    3. nama component
    4. type/engine/role
    5. generic symbol match

    Tujuan:
    menghindari hasil seperti Any, Path, BaseModel
    ketika query sebenarnya meminta architecture/component.
    """

    graph = load_graph()
    q = q.lower().strip()

    if not q:
        return []

    raw_terms = [
        x for x in re.findall(
            r"[a-zA-Z0-9_]+",
            q
        )
        if len(x) >= 3
    ]

    stopwords = {
        "apa",
        "yang",
        "dan",
        "dengan",
        "saya",
        "jelaskan",
        "jelaskanlah",
        "bagaimana",
        "struktur",
        "hubungan",
        "tentang",
        "developer",
        "core",
        "anda",
        "ini",
        "itu",
        "untuk",
        "dari",
        "pada",
        "dalam",
        "the",
        "how",
        "what",
        "show",
    }

    terms = [
        x for x in raw_terms
        if x not in stopwords
    ]

    if not terms:
        terms = raw_terms

    results = []

    for n in graph.get("nodes", []):

        nid = node_id(n)
        name = node_name(n)

        path = str(
            n.get("path")
            or n.get("file")
            or n.get("module")
            or ""
        )

        typ = str(n.get("type") or "")
        engine = str(n.get("engine") or "")
        role = str(n.get("role") or "")

        name_l = name.lower()
        path_l = path.lower()

        score = 0

        # Exact query
        if q in name_l:
            score += 100

        if q in path_l:
            score += 80

        for term in terms:

            if term == name_l:
                score += 90

            if term in name_l:
                score += 35

            if term in path_l:
                score += 25

            if term in typ.lower():
                score += 10

            if term in engine.lower():
                score += 10

            if term in role.lower():
                score += 8

        # Hindari symbol Python yang terlalu umum
        generic_names = {
            "any",
            "path",
            "dict",
            "list",
            "tuple",
            "set",
            "str",
            "int",
            "float",
            "bool",
            "base",
            "basemodel",
            "optional",
            "union",
            "iterable",
            "permissionerror",
            "valueerror",
        }

        if name_l in generic_names:
            score -= 40

        if score <= 0:
            continue

        results.append({
            "id": nid,
            "name": name,
            "type": n.get("type"),
            "engine": n.get("engine"),
            "role": n.get("role"),
            "path": path,
            "_score": score,
        })

    # Deduplicate by meaningful identity
    unique = {}

    for item in results:

        key = (
            item["path"].lower(),
            item["name"].lower(),
        )

        old = unique.get(key)

        if old is None or item["_score"] > old["_score"]:
            unique[key] = item

    results = list(unique.values())

    results.sort(
        key=lambda x: x["_score"],
        reverse=True
    )

    for item in results:
        item.pop("_score", None)

    return results[:limit]
'''

text = text[:start] + new_graph + text[end:]

start = text.index("def search_source(")
end = text.index("\ndef build_graph_context(", start)

new_source = r'''def search_source(query: str, limit: int = 8):
    """
    Production-oriented lexical source retrieval.

    File path mendapat bobot tinggi.
    Symbol generic mendapat bobot rendah.
    Hasil duplicate dihapus.
    """

    index = load_json(
        INDEX_FILE,
        {"documents": []}
    )

    query = query.lower().strip()

    if not query:
        return []

    terms = [
        x for x in re.findall(
            r"[a-zA-Z0-9_]+",
            query
        )
        if len(x) >= 3
    ]

    stopwords = {
        "apa",
        "yang",
        "dan",
        "dengan",
        "saya",
        "jelaskan",
        "bagaimana",
        "struktur",
        "hubungan",
        "tentang",
        "developer",
        "core",
        "ini",
        "itu",
        "untuk",
        "dari",
        "dalam",
    }

    terms = [
        x for x in terms
        if x not in stopwords
    ]

    if not terms:
        return []

    results = []

    for doc in index.get("documents", []):

        path = str(doc.get("path", ""))
        content = str(doc.get("content", ""))

        low = content.lower()
        path_low = path.lower()

        score = 0

        # Path relevance
        for term in terms:

            if term in path_low:
                score += 40

            score += min(
                low.count(term),
                20
            )

        # Production source lebih penting
        if path_low.startswith("app\\"):
            score += 15

        # API / core / knowledge source
        priority_tokens = {
            "routes.py": 35,
            "engine.py": 20,
            "rag.py": 20,
            "workflow": 15,
            "hermes": 15,
            "ollama": 15,
            "knowledge": 20,
        }

        for token, weight in priority_tokens.items():
            if token in path_low:
                score += weight

        if score <= 0:
            continue

        # Ambil lokasi match terbaik
        positions = []

        for term in terms:
            pos = low.find(term)

            if pos >= 0:
                positions.append(pos)

        position = (
            min(positions)
            if positions
            else 0
        )

        start_pos = max(
            0,
            position - 700
        )

        end_pos = min(
            len(content),
            position + 2200
        )

        snippet = content[
            start_pos:end_pos
        ]

        results.append({
            "path": path,
            "score": score,
            "lines": doc.get("lines"),
            "snippet": snippet,
        })

    # Deduplicate path
    unique = {}

    for item in results:

        key = item["path"].lower()

        old = unique.get(key)

        if old is None or item["score"] > old["score"]:
            unique[key] = item

    results = list(unique.values())

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:limit]
'''

text = text[:start] + new_source + text[end:]

start = text.index("def build_graph_context(")
end = text.index("\ndef graph_rag(", start)

new_context = r'''def build_graph_context(query: str):
    """
    Context Builder untuk Graph RAG + Source RAG.

    Context dibuat ringkas dan terstruktur supaya
    llama3.2:1b tidak menerima ribuan baris source.
    """

    graph_results = search_graph(
        query,
        15
    )

    source_results = search_source(
        query,
        5
    )

    context = []

    context.append(
        "=== NUSANTARA DEVELOPER CORE CONTEXT ==="
    )

    context.append(
        "QUERY: " + query
    )

    if graph_results:

        context.append(
            "\n=== GRAPH STRUCTURE ==="
        )

        for item in graph_results:

            context.append(
                "- "
                + item["name"]
                + " | "
                + "type="
                + str(item.get("type"))
                + " | "
                + "engine="
                + str(item.get("engine"))
                + " | "
                + "role="
                + str(item.get("role"))
                + " | path="
                + str(item.get("path"))
            )

    else:

        context.append(
            "\n=== GRAPH STRUCTURE ==="
        )

        context.append(
            "Tidak ditemukan node graph yang relevan."
        )

    if source_results:

        context.append(
            "\n=== SOURCE CODE ==="
        )

        for item in source_results:

            snippet = item.get(
                "snippet",
                ""
            )

            # Batasi setiap source
            snippet = snippet[:3500]

            context.append(
                "\nFILE: "
                + item["path"]
                + "\n"
                + snippet
            )

    else:

        context.append(
            "\n=== SOURCE CODE ==="
        )

        context.append(
            "Tidak ditemukan source code yang relevan."
        )

    return "\n".join(context)
'''

text = text[:start] + new_context + text[end:]

# Replace prompt to make Ollama obey evidence
old_prompt_start = text.index('    prompt = f"""', text.index("def developer_chat"))
old_prompt_end = text.index('    """', old_prompt_start) + len('    """')

new_prompt = r'''    prompt = f"""
Anda adalah Nusantara Developer Core Engine.

Anda menjawab pertanyaan tentang source code
Nusantara berdasarkan bukti yang diberikan.

ATURAN WAJIB:

1. Jangan mengarang file atau component.
2. Jangan mengulang file yang sama.
3. Jangan menyebut component hanya karena namanya
   muncul sebagai import Python umum seperti Any,
   Path, BaseModel atau Parser.
4. Prioritaskan file app/ dan component production.
5. Jika Graph Structure dan Source Code berbeda,
   jelaskan perbedaannya.
6. Jangan menyatakan Graphify melakukan sesuatu
   yang tidak dibuktikan oleh context.
7. Bedakan:
   - fakta dari source code
   - hubungan dari graph
   - inferensi engineering.
8. Jawab Bahasa Indonesia.
9. Gunakan daftar yang konkret.
10. Jika bukti tidak cukup, katakan:
    "Bukti pada Developer Core belum cukup."

PERTANYAAN:
{query}

BUKTI DEVELOPER CORE:
{context}

FORMAT JAWABAN:

Ringkasan:
...

Struktur:
...

Hubungan Graphify:
...

Bukti Source Code:
...

Catatan:
...

Jangan membuat nama file/component baru.
"""
'''

text = text[:old_prompt_start] + new_prompt + text[old_prompt_end:]

p.write_text(
    text,
    encoding="utf-8"
)

print("PATCH DEVELOPER CORE BERHASIL")
print(p)
