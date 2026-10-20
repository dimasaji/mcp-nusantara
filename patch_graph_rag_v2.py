from pathlib import Path
import shutil
from datetime import datetime

ROOT = Path(r"C:\Users\dmaza\mcp-starter")
TARGET = ROOT / "developer_core_engine.py"

backup = TARGET.with_name(
    f"developer_core_engine.before_graph_rag_v2_{datetime.now():%Y%m%d_%H%M%S}.py"
)
shutil.copy2(TARGET, backup)

text = TARGET.read_text(encoding="utf-8")

start = text.find("def search_graph(")
end = text.find("\ndef ", start + 10)

if start == -1:
    raise SystemExit("search_graph() tidak ditemukan.")

if end == -1:
    end = len(text)

new_function = r'''def search_graph(query: str, limit: int = 10):
    """
    Graph RAG v2.

    Menggunakan:
    - Graphify nodes
    - Graphify edges
    - semantic token matching sederhana
    - 1-hop relationship traversal

    Output dinormalisasi agar dapat digunakan oleh
    build_graph_context().
    """

    import json
    import re

    graph_path = ROOT / "graphify-out" / "graph.json"

    if not graph_path.exists():
        return []

    try:
        data = json.loads(
            graph_path.read_text(encoding="utf-8")
        )
    except Exception:
        return []

    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    blocked_tokens = {
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
        "object",
        "typing",
        "datetime",
        "json",
        "os",
        "sys",
        "re",
        "fastapi",
        "pydantic",
    }

    blocked_path_tokens = {
        "backup",
        "before_openrouter",
        "after_openrouter",
        "__pycache__",
        ".venv",
        "research",
        "archive",
        "quarantine",
        "benchmark",
    }

    def blocked_path(path):
        p = str(path or "").lower()

        return any(
            token in p
            for token in blocked_path_tokens
        )

    def tokenize(value):
        return {
            token
            for token in re.findall(
                r"[a-zA-Z0-9_]+",
                str(value or "").lower()
            )
            if len(token) >= 3
        }

    query_tokens = tokenize(query)

    if not query_tokens:
        return []

    node_map = {}

    for node in nodes:

        node_id = str(
            node.get("id") or ""
        )

        if not node_id:
            continue

        source_file = str(
            node.get("source_file") or ""
        )

        label = str(
            node.get("label") or ""
        )

        if blocked_path(source_file):
            continue

        if label.lower() in blocked_tokens:
            continue

        node_map[node_id] = node

    candidates = []

    for node_id, node in node_map.items():

        label = str(
            node.get("label") or ""
        )

        source_file = str(
            node.get("source_file") or ""
        )

        source_location = str(
            node.get("source_location") or ""
        )

        file_type = str(
            node.get("file_type") or ""
        )

        searchable = " ".join(
            [
                label,
                source_file,
                source_location,
                node_id,
            ]
        ).lower()

        node_tokens = tokenize(searchable)

        overlap = query_tokens.intersection(
            node_tokens
        )

        if not overlap:
            continue

        score = (
            len(overlap) * 100
        )

        if label.lower() in query_tokens:
            score += 300

        if source_file.lower().startswith("app/"):
            score += 50

        if file_type == "code":
            score += 20

        if file_type == "rationale":
            score += 5

        candidates.append(
            {
                "id": node_id,
                "name": label,
                "label": label,
                "path": source_file,
                "source_file": source_file,
                "source_location": source_location,
                "type": file_type,
                "origin": str(
                    node.get("_origin") or ""
                ),
                "score": score,
            }
        )

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    candidates = candidates[:limit]

    candidate_ids = {
        item["id"]
        for item in candidates
    }

    relationships = []

    for edge in edges:

        source = str(
            edge.get("source") or ""
        )

        target = str(
            edge.get("target") or ""
        )

        if (
            source not in node_map
            and source not in candidate_ids
        ):
            continue

        if (
            target not in node_map
            and target not in candidate_ids
        ):
            continue

        if (
            source in candidate_ids
            or target in candidate_ids
        ):

            relation = str(
                edge.get("relation") or ""
            )

            source_node = node_map.get(source, {})
            target_node = node_map.get(target, {})

            relationships.append(
                {
                    "source": source,
                    "target": target,
                    "source_name": str(
                        source_node.get("label") or source
                    ),
                    "target_name": str(
                        target_node.get("label") or target
                    ),
                    "source_file": str(
                        source_node.get("source_file") or
                        edge.get("source_file") or ""
                    ),
                    "target_file": str(
                        target_node.get("source_file") or ""
                    ),
                    "relation": relation,
                    "context": str(
                        edge.get("context") or ""
                    ),
                    "source_location": str(
                        edge.get("source_location") or
                        edge.get("source_location") or ""
                    ),
                    "weight": edge.get("weight", 1.0),
                }
            )

    relationship_seen = set()
    clean_relationships = []

    for item in relationships:

        key = (
            item["source"],
            item["target"],
            item["relation"],
        )

        if key in relationship_seen:
            continue

        relationship_seen.add(key)
        clean_relationships.append(item)

    clean_relationships.sort(
        key=lambda x: (
            x["source_name"],
            x["relation"],
            x["target_name"],
        )
    )

    result = []

    for item in candidates:
        result.append(item)

    for rel in clean_relationships[:30]:

        result.append(
            {
                "id": (
                    f"edge:"
                    f"{rel['source']}:"
                    f"{rel['target']}:"
                    f"{rel['relation']}"
                ),
                "name": (
                    f"{rel['source_name']} "
                    f"--{rel['relation']}--> "
                    f"{rel['target_name']}"
                ),
                "label": rel["relation"],
                "path": rel["source_file"],
                "source_file": rel["source_file"],
                "source_location": rel["source_location"],
                "type": "relationship",
                "origin": "graphify",
                "score": 50,
                "relation": rel["relation"],
                "source_node": rel["source"],
                "target_node": rel["target"],
                "target_file": rel["target_file"],
            }
        )

    return result[: max(limit, 10) + 30]


'''

text = text[:start] + new_function + text[end:]

TARGET.write_text(
    text,
    encoding="utf-8"
)

print("GRAPH RAG V2 PATCH BERHASIL")
print("Backup:", backup)
