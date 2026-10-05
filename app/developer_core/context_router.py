from pathlib import Path
import json
import re
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]

FORBIDDEN = {
    ".developer_staging",
    ".env",
    ".git",
    ".venv",
    "data/production",
    "venv",
}

DOMAIN_TERMS = {
    "rag", "retrieval", "retrieve", "retriever",
    "semantic", "knowledge", "embedding", "embeddings",
    "grounding", "evidence", "search", "ranking",
    "rerank", "reranker", "chunk", "chunks",
    "vector", "fts", "indobert", "llm",
}


def tokens(text):
    return {
        x.lower()
        for x in re.findall(r"[A-Za-z0-9_]+", text or "")
        if len(x) >= 3
    }


def is_forbidden(path):
    value = str(path).replace("\\", "/").lower().lstrip("./")

    for blocked in FORBIDDEN:
        b = blocked.replace("\\", "/").lower().lstrip("./")
        if value == b or value.startswith(b + "/"):
            return True

    return False


def node_text(node):
    return " ".join(
        str(node.get(key, ""))
        for key in (
            "id",
            "name",
            "path",
            "label",
            "type",
            "file",
            "source",
        )
    ).lower()


def node_path(node):
    return str(
        node.get("path")
        or node.get("file")
        or node.get("source")
        or ""
    ).replace("\\", "/")


def score_node(node, search_terms, domain_terms):
    text = node_text(node)
    path = node_path(node).lower()

    score = 0

    for term in search_terms:
        if term in text:
            score += 1

    domain_hits = sum(
        1 for term in domain_terms
        if term in text
    )

    score += domain_hits * 4

    if path.startswith("app/knowledge/"):
        score += 8

    if (
        "rag" in path
        or "retriev" in path
        or "semantic" in path
    ):
        score += 8

    if path.startswith("docs/contracts/"):
        score += 3

    if path.startswith("app/developer_core/"):
        score -= 5

    return score


def build_context(task):
    graph_path = ROOT / "graphify-out" / "graph.json"

    if not graph_path.exists():
        raise RuntimeError(
            f"Graph tidak ditemukan: {graph_path}"
        )

    with graph_path.open(
        "r",
        encoding="utf-8-sig"
    ) as f:
        graph = json.load(f)

    nodes = graph.get("nodes", [])
    edges = graph.get(
        "edges",
        graph.get("links", [])
    )

    task_tokens = tokens(task)

    aliases = {
        "context": ["context_router"],
        "router": ["context_router"],
        "approval": ["approval_controller"],
        "controller": ["approval_controller"],
        "controlled": ["controlled_write"],
        "write": ["controlled_write"],
        "regression": ["automatic_regression_gate"],
        "gate": ["automatic_regression_gate"],
        "execution": [
            "execution_audit",
            "execution_audit_integration",
        ],
        "audit": [
            "execution_audit",
            "execution_audit_integration",
        ],
        "self": ["self_improvement_loop"],
        "improvement": ["self_improvement_loop"],
        "health": ["health"],
        "developer": ["developer_core"],
        "core": ["developer_core"],
    }

    search_terms = set(task_tokens)

    for token in task_tokens:
        search_terms.update(
            aliases.get(token, [])
        )

    domain_terms = (
        set(DOMAIN_TERMS)
        & search_terms
    )

    rag_task = bool(
        domain_terms.intersection({
            "rag",
            "retrieval",
            "retrieve",
            "retriever",
            "semantic",
            "knowledge",
            "embedding",
            "embeddings",
            "grounding",
            "evidence",
            "rerank",
            "reranker",
        })
    )

    scored_nodes = []

    for node in nodes:
        score = score_node(
            node,
            search_terms,
            domain_terms,
        )

        if rag_task:
            path = node_path(node).lower()

            if path.startswith(
                "app/knowledge/"
            ):
                score += 12

            if "production_hybrid_rag" in path:
                score += 12

            if "production_semantic_retriever" in path:
                score += 12

            if (
                path.endswith("/rag.py")
                or path.endswith("\\rag.py")
            ):
                score += 10

            if path.startswith(
                "app/developer_core/"
            ):
                score -= 10

        if score > 0:
            scored_nodes.append(
                (score, node)
            )

    scored_nodes.sort(
        key=lambda item: (
            -item[0],
            str(
                item[1].get("path")
                or item[1].get("file")
                or item[1].get("name")
                or ""
            ).lower(),
        )
    )

    relevant_nodes = [
        node
        for _, node in scored_nodes[:40]
    ]

    relevant_files = []

    for node in relevant_nodes:
        candidate = node_path(node)

        if not candidate:
            continue

        if is_forbidden(candidate):
            continue

        if candidate not in relevant_files:
            relevant_files.append(candidate)

    # ============================================================
    # RAG DOMAIN OVERRIDE
    # ============================================================
    # Graphify ranking is useful for discovery, tetapi untuk task RAG
    # implementation layer harus selalu masuk ke context package.
    if rag_task:
        rag_priority = [
            "app/knowledge/production_hybrid_rag.py",
            "app/knowledge/production_semantic_retriever.py",
            "app/knowledge/rag.py",
            "app/knowledge/reranker.py",
            "app/knowledge/grounding.py",
        ]

        prioritized = []

        for candidate in rag_priority:
            if (
                (ROOT / candidate).exists()
                and not is_forbidden(candidate)
            ):
                prioritized.append(candidate)

        for candidate in relevant_files:
            if candidate not in prioritized:
                prioritized.append(candidate)

        relevant_files = prioritized

    if not relevant_files:
        fallback_files = [
            "app/developer_core/context_router.py",
            "app/developer_core/approval_controller.py",
            "app/developer_core/controlled_write.py",
            "app/developer_core/automatic_regression_gate.py",
        ]

        for candidate in fallback_files:
            if (
                (ROOT / candidate).exists()
                and not is_forbidden(candidate)
            ):
                relevant_files.append(candidate)

    relevant_files = relevant_files[:25]

    # Candidate context.
    # BELUM merupakan izin write.
    candidate_files = relevant_files[:10]

    return {
        "schema": "nusantara.context_package.v1",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "mode": "CONTROLLED",
        "task": task,

        "intent": {
            "rag_task": rag_task,
            "domain_terms": sorted(
                domain_terms
            ),
        },

        "graph": {
            "path": str(graph_path),
            "nodes": len(nodes),
            "edges": len(edges),
        },

        "relevant_files": relevant_files,
        "candidate_files": candidate_files,
        "relevant_nodes": relevant_nodes,

        # Keamanan tetap fail-closed.
        "allowed_files": candidate_files,

        "forbidden_paths": sorted(
            FORBIDDEN
        ),

        "shell_execution": False,
        "production_write": False,
        "automatic_patch": False,
        "approval_required": True,
        "fail_closed": True,
        "claude_code_role": "CONTROLLED_PROGRAMMER",
    }


def main():
    task = " ".join(
        sys.argv[1:]
    ).strip()

    if not task:
        print(
            "ERROR: Task wajib diberikan."
        )
        sys.exit(1)

    result = build_context(task)

    output = (
        ROOT
        / "data"
        / "developer_core"
        / "context"
        / "context_package.json"
    )

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print("=" * 64)
    print("NUSANTARA CONTEXT ROUTER V1.3")
    print("=" * 64)
    print(
        f"Task            : {task}"
    )
    print(
        f"Graph nodes     : {result['graph']['nodes']}"
    )
    print(
        f"Graph edges     : {result['graph']['edges']}"
    )
    print(
        f"RAG intent      : {result['intent']['rag_task']}"
    )
    print(
        f"Relevant files  : {len(result['relevant_files'])}"
    )
    print(
        f"Candidate files : {len(result['candidate_files'])}"
    )
    print(
        f"Relevant nodes  : {len(result['relevant_nodes'])}"
    )
    print(
        "Shell execution : BLOCKED"
    )
    print(
        "Production write: BLOCKED"
    )
    print(
        "Auto patch      : BLOCKED"
    )
    print(
        "Approval        : REQUIRED"
    )
    print(
        "Fail-closed     : ENABLED"
    )
    print(
        f"OUTPUT          : {output}"
    )
    print(
        "STATUS          : READY"
    )


if __name__ == "__main__":
    main()
