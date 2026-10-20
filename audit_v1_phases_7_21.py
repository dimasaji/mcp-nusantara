from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent

PHASES = {
    7: {
        "name": "RAG / Grounding",
        "paths": [
            "app/knowledge",
            "tests/v2",
        ],
        "patterns": [
            "Grounding",
            "grounding",
            "evidence",
        ],
    },
    8: {
        "name": "MCP",
        "paths": [
            "app/mcp",
            "app",
            "tests",
        ],
        "patterns": [
            "MCP",
            "mcp",
        ],
    },
    9: {
        "name": "Tool Governance",
        "paths": [
            "app",
            "tests",
        ],
        "patterns": [
            "permission",
            "risk_level",
            "audit",
            "tool",
        ],
    },
    10: {
        "name": "Experience Layer",
        "paths": [
            "app/experience",
            "app",
        ],
        "patterns": [
            "metadata",
            "feedback",
            "analytics",
        ],
    },
    11: {
        "name": "Feedback",
        "paths": [
            "app",
            "tests",
        ],
        "patterns": [
            "feedback",
        ],
    },
    12: {
        "name": "Evaluation",
        "paths": [
            "tests/evaluation",
            "tests",
            "app",
        ],
        "patterns": [
            "evaluation",
            "correctness",
            "relevance",
            "groundedness",
        ],
    },
    13: {
        "name": "Failure Analysis",
        "paths": [
            "app",
            "tests",
        ],
        "patterns": [
            "failure",
            "failure_analysis",
        ],
    },
    14: {
        "name": "Gap Detection",
        "paths": [
            "app",
            "tests",
        ],
        "patterns": [
            "gap",
            "gap_detection",
        ],
    },
    15: {
        "name": "Knowledge Discovery",
        "paths": [
            "app",
            "tests",
        ],
        "patterns": [
            "knowledge_discovery",
            "discovery",
        ],
    },
    16: {
        "name": "Experiment",
        "paths": [
            "app",
            "tests",
        ],
        "patterns": [
            "experiment",
            "experiments",
        ],
    },
    17: {
        "name": "Improvement Proposal",
        "paths": [
            "app",
            "tests",
        ],
        "patterns": [
            "improvement",
            "proposal",
        ],
    },
    18: {
        "name": "Human Approval",
        "paths": [
            "app",
            "tests",
        ],
        "patterns": [
            "approval",
            "approve",
            "human",
        ],
    },
    19: {
        "name": "V1.x Development",
        "paths": [
            "app",
            "tests",
        ],
        "patterns": [
            "v1",
            "version",
        ],
    },
    20: {
        "name": "Regression / Security",
        "paths": [
            "tests",
            "app/security",
            "app",
        ],
        "patterns": [
            "security",
            "regression",
            "safe",
            "validator",
        ],
    },
    21: {
        "name": "Release / Rollback",
        "paths": [
            "docs",
            "app",
            "tests",
        ],
        "patterns": [
            "release",
            "rollback",
        ],
    },
}


def existing_files(paths):
    result = []

    for raw in paths:
        path = ROOT / raw

        if not path.exists():
            continue

        if path.is_file():
            result.append(path)
        else:
            result.extend(
                p for p in path.rglob("*")
                if p.is_file()
                and p.suffix.lower() in {
                    ".py", ".md", ".txt", ".yaml",
                    ".yml", ".json", ".toml"
                }
            )

    return list(dict.fromkeys(result))


def inspect_phase(phase_id, config):
    files = existing_files(config["paths"])

    matched_files = []
    matched_patterns = set()

    for file in files:
        try:
            text = file.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except Exception:
            continue

        lower = text.lower()

        local_matches = []

        for pattern in config["patterns"]:
            if pattern.lower() in lower:
                matched_patterns.add(pattern)
                local_matches.append(pattern)

        if local_matches:
            matched_files.append(
                (file.relative_to(ROOT), local_matches)
            )

    if not files:
        status = "NOT_FOUND"
    elif matched_files:
        status = "IMPLEMENTED_OR_PRESENT"
    else:
        status = "PRESENT_BUT_UNVERIFIED"

    return {
        "status": status,
        "files": files,
        "matched_files": matched_files,
        "matched_patterns": matched_patterns,
    }


def main():
    print("=" * 78)
    print("NUSANTARA AI V1 — PHASE 7-21 ARCHITECTURE AUDIT")
    print("=" * 78)
    print()
    print(f"ROOT: {ROOT}")
    print()

    results = {}

    for phase_id, config in PHASES.items():
        result = inspect_phase(phase_id, config)
        results[phase_id] = result

        print(
            f"PHASE {phase_id:02d} | "
            f"{config['name']:<28} | "
            f"{result['status']}"
        )

    print()
    print("=" * 78)
    print("DETAIL")
    print("=" * 78)

    for phase_id, config in PHASES.items():
        result = results[phase_id]

        print()
        print(f"PHASE {phase_id:02d} — {config['name']}")
        print(f"STATUS : {result['status']}")

        if result["matched_patterns"]:
            print(
                "MATCH  : "
                + ", ".join(sorted(result["matched_patterns"]))
            )

        if result["matched_files"]:
            print("FILES  :")

            for file, patterns in result["matched_files"][:10]:
                print(
                    f"  - {file} "
                    f"[{', '.join(patterns)}]"
                )

            if len(result["matched_files"]) > 10:
                print(
                    f"  ... +{len(result['matched_files']) - 10} files"
                )

        else:
            print("FILES  : none detected")

    print()
    print("=" * 78)
    print("AUDIT RULE")
    print("=" * 78)
    print(
        "IMPLEMENTED_OR_PRESENT bukan berarti PASS."
    )
    print(
        "PASS hanya diberikan setelah test/integration verification."
    )
    print(
        "Tidak ada source code Nusantara yang dimodifikasi oleh script ini."
    )
    print("=" * 78)


if __name__ == "__main__":
    main()
