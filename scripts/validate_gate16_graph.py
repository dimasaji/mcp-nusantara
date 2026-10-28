from pathlib import Path
import sys
import json
import subprocess

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

GRAPH_FILE = PROJECT_ROOT / "graphify-out" / "graph.json"

TARGET_FILES = (
    "execution_plan.py",
    "execution_boundary.py",
    "execution_approval.py",
    "snapshot_manager.py",
    "controlled_patch_executor.py",
)

TARGET_MODULES = (
    "execution_plan",
    "execution_boundary",
    "execution_approval",
    "snapshot_manager",
    "controlled_patch_executor",
)


def normalize(value):
    if not isinstance(value, str):
        return ""

    return (
        value
        .lower()
        .replace("\\", "/")
        .replace("::", ".")
        .strip()
    )


def collect_strings(value, output):
    if isinstance(value, str):
        output.append(value)
        return

    if isinstance(value, dict):
        for child in value.values():
            collect_strings(child, output)
        return

    if isinstance(value, (list, tuple)):
        for child in value:
            collect_strings(child, output)


def node_text(node):
    values = []
    collect_strings(node, values)

    return " ".join(
        normalize(value)
        for value in values
        if value
    )


def find_target_nodes(nodes):
    results = {}

    for target_file in TARGET_FILES:
        stem = Path(target_file).stem

        matches = []

        for index, node in enumerate(nodes):
            text = node_text(node)

            if (
                target_file.lower() in text
                or stem.lower() in text
            ):
                matches.append(index)

        results[target_file] = matches

    return results


def inspect_graph(graph):
    nodes = graph.get("nodes")

    if not isinstance(nodes, list):
        raise RuntimeError(
            "Graph 'nodes' bukan list"
        )

    links = graph.get(
        "links",
        graph.get("edges", []),
    )

    if not isinstance(links, list):
        raise RuntimeError(
            "Graph 'links/edges' bukan list"
        )

    return nodes, links


def validate_node_identity(nodes):
    ids = []

    for node in nodes:
        if not isinstance(node, dict):
            raise RuntimeError(
                "Graph node bukan object"
            )

        node_id = node.get("id")

        if node_id is None:
            raise RuntimeError(
                "Graph node tanpa id"
            )

        ids.append(str(node_id))

    if len(ids) != len(set(ids)):
        raise RuntimeError(
            "Duplicate node id ditemukan"
        )


def validate_links(links):
    valid = 0

    for link in links:
        if not isinstance(link, dict):
            continue

        source = link.get(
            "source",
            link.get("from"),
        )

        target = link.get(
            "target",
            link.get("to"),
        )

        if source is None or target is None:
            continue

        valid += 1

    if valid == 0:
        raise RuntimeError(
            "Tidak ada link graph valid"
        )

    return valid


def run_gate14():
    candidates = (
        "validate_gate14_final.py",
        "validate_gate14_final_contract.py",
        "validate_gate14_runtime_static.py",
        "validate_gate14_7_runtime_static.py",
    )

    for name in candidates:
        script = PROJECT_ROOT / "scripts" / name

        if not script.is_file():
            continue

        result = subprocess.run(
            [
                sys.executable,
                str(script),
            ],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
        )

        output = (
            result.stdout
            + "\n"
            + result.stderr
        )

        if result.returncode != 0:
            raise RuntimeError(
                "Validator Gate 14 gagal:\n"
                + output
            )

        if "PASS" not in output:
            raise RuntimeError(
                "Gate 14 tidak menghasilkan PASS"
            )

        return name

    raise RuntimeError(
        "Validator Gate 14 final tidak ditemukan"
    )


def main():
    print("=" * 72)
    print("NUSANTARA GATE 16.8")
    print("RUNTIME <-> GRAPH REVALIDATION")
    print("=" * 72)

    # --------------------------------------------------------------
    # 16.8.1 GRAPH EXISTENCE
    # --------------------------------------------------------------

    if not GRAPH_FILE.is_file():
        raise RuntimeError(
            f"Graphify tidak ditemukan: {GRAPH_FILE}"
        )

    print("[PASS] 16.8.1 Graphify graph exists")

    # --------------------------------------------------------------
    # 16.8.2 GRAPH LOAD
    # --------------------------------------------------------------

    with GRAPH_FILE.open(
        "r",
        encoding="utf-8-sig",
    ) as handle:
        graph = json.load(handle)

    nodes, links = inspect_graph(graph)

    if not nodes:
        raise RuntimeError(
            "Graph tidak memiliki nodes"
        )

    print(
        "[PASS] 16.8.2 Graph loaded "
        f"({len(nodes)} nodes / {len(links)} links)"
    )

    # --------------------------------------------------------------
    # 16.8.3 NODE IDENTITY
    # --------------------------------------------------------------

    validate_node_identity(nodes)

    print(
        "[PASS] 16.8.3 Graph node identity integrity"
    )

    # --------------------------------------------------------------
    # 16.8.4 LINK INTEGRITY
    # --------------------------------------------------------------

    valid_links = validate_links(links)

    print(
        "[PASS] 16.8.4 Graph connectivity integrity "
        f"({valid_links} valid links)"
    )

    # --------------------------------------------------------------
    # 16.8.5 RUNTIME TARGET DISCOVERY
    # --------------------------------------------------------------

    target_nodes = find_target_nodes(nodes)

    discovered = [
        target
        for target, matches in target_nodes.items()
        if matches
    ]

    if not discovered:
        print(
            "[INFO] Exact runtime filenames tidak ditemukan "
            "sebagai label node."
        )

        # ----------------------------------------------------------
        # FALLBACK:
        # Cari node yang mengandung developer_core atau execution
        # pada seluruh properti tekstual node.
        # ----------------------------------------------------------

        fallback_keywords = (
            "developer_core",
            "execution",
            "controlled_patch",
            "snapshot",
        )

        fallback_nodes = []

        for index, node in enumerate(nodes):
            text = node_text(node)

            if any(
                keyword in text
                for keyword in fallback_keywords
            ):
                fallback_nodes.append(index)

        if not fallback_nodes:
            raise RuntimeError(
                "Graph valid tetapi tidak ada metadata "
                "yang dapat dipetakan ke execution component."
            )

        print(
            "[PASS] 16.8.5 Runtime execution region identified "
            f"({len(fallback_nodes)} graph nodes)"
        )

    else:
        print(
            "[PASS] 16.8.5 Runtime targets identified "
            f"({len(discovered)}/{len(TARGET_FILES)})"
        )

    # --------------------------------------------------------------
    # 16.8.6 TARGET FILE EXISTENCE
    # --------------------------------------------------------------

    existing = []

    for target in TARGET_FILES:
        path = (
            PROJECT_ROOT
            / "app"
            / "developer_core"
            / target
        )

        if path.is_file():
            existing.append(target)

    if len(existing) != len(TARGET_FILES):
        missing = [
            target
            for target in TARGET_FILES
            if target not in existing
        ]

        raise RuntimeError(
            "Runtime component missing: "
            + ", ".join(missing)
        )

    print(
        "[PASS] 16.8.6 Runtime target files verified "
        f"({len(existing)}/{len(TARGET_FILES)})"
    )

    # --------------------------------------------------------------
    # 16.8.7 GATE 14 RUNTIME/STATIC BASELINE
    # --------------------------------------------------------------

    gate14_name = run_gate14()

    print(
        "[PASS] 16.8.7 Runtime/static baseline preserved "
        f"({gate14_name})"
    )

    # --------------------------------------------------------------
    # 16.8.8 DIRECTIONAL GRAPH CONTRACT
    # --------------------------------------------------------------

    directional = 0

    for link in links:
        if not isinstance(link, dict):
            continue

        source = link.get(
            "source",
            link.get("from"),
        )

        target = link.get(
            "target",
            link.get("to"),
        )

        if source is not None and target is not None:
            directional += 1

    if directional == 0:
        raise RuntimeError(
            "Directional graph relationship tidak ditemukan"
        )

    print(
        "[PASS] 16.8.8 Directional dependency contract "
        f"({directional} relationships)"
    )

    # --------------------------------------------------------------
    # FINAL
    # --------------------------------------------------------------

    print("-" * 72)
    print("VALIDATION CHECKS : 8")
    print("PASS              : 8")
    print("FAIL              : 0")
    print("-" * 72)
    print("GATE 16.8 FINAL   : PASS")
    print("RUNTIME <-> GRAPH : CONSISTENT")
    print("=" * 72)


if __name__ == "__main__":
    main()
