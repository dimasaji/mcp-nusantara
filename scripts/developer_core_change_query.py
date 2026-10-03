import json
import re
from collections import deque
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRAPH_DIR = ROOT / "graphify-out"

GRAPH_FILE = GRAPH_DIR / "graph.json"
IMPACT_FILE = GRAPH_DIR / "gate14_6_2_impact_truth.json"
SELF_FILE = GRAPH_DIR / "gate14_5_self_analysis_runtime.json"
CONSISTENCY_FILE = GRAPH_DIR / "gate14_7_runtime_static_consistency.json"


ALLOWED_RELATIONS = {
    "imports",
    "imports_from",
    "calls",
    "indirect_call",
    "uses",
    "depends_on",
    "inherits",
    "re_exports",
}


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(path)

    return json.loads(path.read_text(encoding="utf-8"))


def node_text(node):
    return " ".join(
        str(node.get(k, "") or "")
        for k in (
            "id",
            "name",
            "label",
            "path",
            "file",
            "module",
        )
    ).lower()


def build_graph(graph):
    nodes = graph.get("nodes", [])
    links = graph.get("links", [])

    node_map = {}
    text_index = {}

    for node in nodes:
        node_id = str(node.get("id", ""))
        if not node_id:
            continue

        node_map[node_id] = node
        text_index[node_id] = node_text(node)

    adjacency = {}

    for link in links:
        source = str(
            link.get("source")
            if link.get("source") is not None
            else link.get("from", "")
        )

        target = str(
            link.get("target")
            if link.get("target") is not None
            else link.get("to", "")
        )

        relation = str(
            link.get("relation")
            or link.get("type")
            or link.get("label")
            or ""
        ).lower()

        if not source or not target:
            continue

        if source not in node_map or target not in node_map:
            continue

        if relation not in ALLOWED_RELATIONS:
            continue

        adjacency.setdefault(source, []).append(
            {
                "target": target,
                "relation": relation,
            }
        )

    return node_map, text_index, adjacency


def resolve_target(query, node_map, text_index):
    q = query.strip().lower()

    # Exact ID
    if q in node_map:
        return q

    # Exact module/path/name match
    exact = []

    for node_id, text in text_index.items():
        node = node_map[node_id]

        candidates = [
            str(node.get("id", "")).lower(),
            str(node.get("name", "")).lower(),
            str(node.get("label", "")).lower(),
            str(node.get("module", "")).lower(),
            str(node.get("path", "")).lower(),
            str(node.get("file", "")).lower(),
        ]

        if q in candidates:
            exact.append(node_id)

    if exact:
        return exact[0]

    # Filename / module partial match
    partial = []

    for node_id, text in text_index.items():
        if q in text:
            partial.append(node_id)

    if partial:
        # Prefer actual source-like nodes over arbitrary text matches.
        ranked = sorted(
            partial,
            key=lambda node_id: (
                0 if "/" in str(node_map[node_id].get("path", "")) else 1,
                len(text_index[node_id]),
            ),
        )
        return ranked[0]

    return None


def extract_target(query):
    q = query.strip()

    patterns = [
        r"impact\s+(.+)",
        r"impact\s+analysis\s+(.+)",
        r"affected\s+(.+)",
        r"apa yang terdampak jika\s+(.+?)(?:\s+berubah)?$",
        r"jika\s+(.+?)\s+berubah",
        r"perubahan\s+(.+)",
    ]

    for pattern in patterns:
        m = re.search(pattern, q, re.IGNORECASE)
        if m:
            return m.group(1).strip().rstrip("?.")

    return q


def traverse(start, node_map, adjacency, max_depth=3):
    queue = deque([(start, 0)])
    visited = {start}
    records = []

    while queue:
        current, depth = queue.popleft()

        if depth >= max_depth:
            continue

        for edge in adjacency.get(current, []):
            target = edge["target"]

            if target in visited:
                continue

            visited.add(target)

            records.append(
                {
                    "source": current,
                    "target": target,
                    "relation": edge["relation"],
                    "depth": depth + 1,
                }
            )

            queue.append((target, depth + 1))

    return records


def query_change(query, max_depth=3):
    graph = load_json(GRAPH_FILE)

    node_map, text_index, adjacency = build_graph(graph)

    target_query = extract_target(query)

    target_id = resolve_target(
        target_query,
        node_map,
        text_index,
    )

    if not target_id:
        return {
            "status": "NOT_FOUND",
            "query": query,
            "target_query": target_query,
            "message": "Target tidak ditemukan di Graphify.",
        }

    target_node = node_map[target_id]

    impact = traverse(
        target_id,
        node_map,
        adjacency,
        max_depth=max_depth,
    )

    return {
        "status": "PASS",
        "query": query,
        "target_query": target_query,
        "target": {
            "id": target_id,
            "label": target_node.get("label"),
            "name": target_node.get("name"),
            "module": target_node.get("module"),
            "path": target_node.get("path"),
            "file": target_node.get("file"),
        },
        "analysis": {
            "direction": "SOURCE -> TARGET",
            "max_depth": max_depth,
            "allowed_relations": sorted(ALLOWED_RELATIONS),
            "impact_count": len(impact),
        },
        "impact": [
            {
                "target": node_map[r["target"]].get("id"),
                "label": node_map[r["target"]].get("label"),
                "name": node_map[r["target"]].get("name"),
                "relation": r["relation"],
                "depth": r["depth"],
            }
            for r in impact
        ],
        "source": {
            "graph": str(GRAPH_FILE),
            "deterministic": True,
            "llm_used": False,
        },
    }


def main():
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print(
            "python scripts/developer_core_change_query.py "
            '"impact KnowledgeEngine"'
        )
        raise SystemExit(1)

    query = " ".join(sys.argv[1:])

    result = query_change(query)

    print("=" * 64)
    print("NUSANTARA DEVELOPER CORE - DETERMINISTIC CHANGE QUERY")
    print("=" * 64)

    print("Query        :", result["query"])
    print("Status       :", result["status"])

    if result["status"] != "PASS":
        print("Target       :", result.get("target_query"))
        print("Message      :", result.get("message"))
        raise SystemExit(2)

    target = result["target"]

    print("Target ID    :", target["id"])
    print("Target Label :", target["label"])
    print("Direction    :", result["analysis"]["direction"])
    print("Max depth    :", result["analysis"]["max_depth"])
    print("Impact count :", result["analysis"]["impact_count"])
    print("LLM used     :", result["source"]["llm_used"])
    print()

    for item in result["impact"]:
        print(
            f"[depth={item['depth']}] "
            f"{item['relation']:<16} "
            f"{item['label'] or item['name'] or item['target']}"
        )

    output = GRAPH_DIR / "gate14_8_change_query_last.json"

    output.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print("Output       :", output)


if __name__ == "__main__":
    main()
