from pathlib import Path
import json
import re
from datetime import datetime, timezone

ENGINE = Path("scripts/nusantara_master_engine.py")

if not ENGINE.exists():
    raise SystemExit("ERROR: scripts/nusantara_master_engine.py tidak ditemukan.")

text = ENGINE.read_text(encoding="utf-8")

if "--v2-audit" in text:
    print("INFO: --v2-audit sudah ada. Tidak melakukan patch ulang.")
    raise SystemExit(0)

audit_function = r'''

def run_v2_capability_audit(root: Path) -> dict:
    """
    Read-only V2 capability audit.

    Tidak melakukan:
    - source modification
    - delete
    - git operation
    - autonomous patch
    - runtime mutation

    Tujuan:
    memetakan kemampuan V2 yang benar-benar terdapat di repository.
    """

    audit_dir = root / "docs" / "audit"
    audit_dir.mkdir(parents=True, exist_ok=True)

    scan_roots = [
        root / "app",
        root / "scripts",
        root / "tests",
        root / "docs",
        root / "graphify-out",
        root / "nusantara-models",
    ]

    files = []
    for base in scan_roots:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file():
                try:
                    rel = p.relative_to(root)
                except ValueError:
                    continue
                if any(part in {".git", "__pycache__", ".pytest_cache"} for part in rel.parts):
                    continue
                files.append(p)

    files = sorted(set(files))

    text_cache = {}
    for p in files:
        try:
            if p.stat().st_size > 2_000_000:
                continue
            text_cache[p] = p.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        except Exception:
            continue

    def evidence(patterns, path_patterns=None):
        hits = []
        for p, content in text_cache.items():
            rel = str(p.relative_to(root)).replace("\\", "/").lower()
            if path_patterns:
                if not any(x.lower() in rel for x in path_patterns):
                    continue
            for pattern in patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    hits.append(rel)
                    break
        return sorted(set(hits))

    def status(hits, runtime=False):
        if runtime:
            return "RUNTIME_VERIFIED" if hits else "UNVERIFIED"
        if len(hits) >= 3:
            return "IMPLEMENTED"
        if hits:
            return "PARTIAL"
        return "MISSING"

    capabilities = {}

    checks = {
        "v2_orchestration": {
            "patterns": [
                r"orchestrat",
                r"workflow",
                r"graph",
                r"router",
                r"planner",
            ],
            "paths": ["app/", "graphify-out/", "scripts/"],
        },
        "graphify_hermes_integration": {
            "patterns": [
                r"graphify",
                r"hermes",
            ],
            "paths": ["app/", "graphify-out/", "scripts/"],
        },
        "architecture_enforcement": {
            "patterns": [
                r"architecture",
                r"protected",
                r"contract",
                r"dependency",
                r"layer",
            ],
            "paths": ["app/", "scripts/", "docs/"],
        },
        "contract_enforcement": {
            "patterns": [
                r"contract",
                r"schema",
                r"validation",
                r"gate",
            ],
            "paths": ["app/", "scripts/", "docs/", "tests/"],
        },
        "autonomous_development": {
            "patterns": [
                r"masterdeveloper",
                r"developer.?core",
                r"self.?analy",
                r"patch",
                r"regression",
                r"rollback",
            ],
            "paths": ["app/", "scripts/", "tests/", "docs/"],
        },
        "governance": {
            "patterns": [
                r"trust",
                r"policy",
                r"human.?approval",
                r"verification",
                r"audit",
            ],
            "paths": ["app/", "scripts/", "docs/", "tests/"],
        },
        "memory": {
            "patterns": [
                r"memory",
                r"persistent",
                r"session",
                r"long.?term",
            ],
            "paths": ["app/", "tests/", "docs/"],
        },
        "rag_knowledge": {
            "patterns": [
                r"rag",
                r"knowledge",
                r"retriev",
                r"embedding",
                r"grounding",
            ],
            "paths": ["app/", "tests/", "docs/"],
        },
        "tool_mcp": {
            "patterns": [
                r"\bmcp\b",
                r"tool",
                r"adapter",
                r"registry",
            ],
            "paths": ["app/", "tests/", "docs/"],
        },
        "observability": {
            "patterns": [
                r"observability",
                r"metric",
                r"logging",
                r"trace",
                r"request.?id",
            ],
            "paths": ["app/", "tests/", "docs/"],
        },
    }

    for name, spec in checks.items():
        hits = evidence(spec["patterns"], spec["paths"])
        capabilities[name] = {
            "status": status(hits),
            "evidence_files": hits[:30],
            "evidence_count": len(hits),
        }

    # Stronger structural checks for the two most important V2 relationships.
    graphify_files = evidence(
        [r"graphify"],
        ["app/", "graphify-out/", "scripts/"],
    )

    hermes_files = evidence(
        [r"hermes"],
        ["app/", "graphify-out/", "scripts/"],
    )

    graphify_hermes_same_files = []
    for rel in sorted(set(graphify_files) & set(hermes_files)):
        graphify_hermes_same_files.append(rel)

    if graphify_hermes_same_files:
        capabilities["graphify_hermes_integration"]["status"] = "PARTIAL"
        capabilities["graphify_hermes_integration"][
            "integration_evidence"
        ] = graphify_hermes_same_files[:20]
    else:
        capabilities["graphify_hermes_integration"][
            "integration_evidence"
        ] = []

    contracts = [
        "architecture",
        "api",
        "data",
        "intelligence",
        "governance",
        "development",
    ]

    contract_results = {}
    for contract in contracts:
        patterns = [
            rf"{contract}.{{0,40}}contract",
            rf"contract.{{0,40}}{contract}",
            rf"{contract}[_ -]?contract",
        ]
        hits = evidence(patterns, ["docs/", "app/", "tests/", "scripts/"])
        contract_results[contract] = {
            "status": status(hits),
            "evidence_files": hits[:20],
            "evidence_count": len(hits),
        }

    runtime_candidates = {
        "health_endpoint": any(
            "/health" in content or '"/health"' in content
            for content in text_cache.values()
        ),
        "v1_chat": any(
            "/v1/chat" in content
            for content in text_cache.values()
        ),
        "graphify_runtime": any(
            re.search(r"graphify.*runtime|runtime.*graphify", content, re.I)
            for content in text_cache.values()
        ),
        "hermes_runtime": any(
            re.search(r"hermes.*runtime|runtime.*hermes", content, re.I)
            for content in text_cache.values()
        ),
    }

    gaps = []

    for name, item in capabilities.items():
        if item["status"] in {"MISSING", "UNVERIFIED"}:
            gaps.append({
                "capability": name,
                "status": item["status"],
                "priority": (
                    "P0"
                    if name in {
                        "v2_orchestration",
                        "graphify_hermes_integration",
                        "architecture_enforcement",
                        "contract_enforcement",
                    }
                    else "P1"
                ),
                "reason": "Belum ditemukan bukti repository yang cukup.",
            })
        elif item["status"] == "PARTIAL":
            gaps.append({
                "capability": name,
                "status": "PARTIAL",
                "priority": "P1",
                "reason": "Bukti ada tetapi implementasi belum dapat dianggap lengkap.",
            })

    roadmap = [
        {
            "order": 1,
            "capability": "v2_orchestration",
            "goal": "Membangun orchestration V2 yang benar-benar menjadi jalur eksekusi Graphify.",
        },
        {
            "order": 2,
            "capability": "graphify_hermes_integration",
            "goal": "Menghubungkan Graphify sebagai orchestrator dengan Hermes sebagai core tanpa duplicate engine.",
        },
        {
            "order": 3,
            "capability": "architecture_enforcement",
            "goal": "Menegakkan batas V1/V2, adapter boundary, dependency direction, dan protected paths.",
        },
        {
            "order": 4,
            "capability": "contract_enforcement",
            "goal": "Menegakkan enam kontrak V2 secara machine-checkable.",
        },
        {
            "order": 5,
            "capability": "autonomous_development",
            "goal": "OBSERVE → ANALYZE → GAP → DESIGN → PATCH → TEST → REGRESSION → EVIDENCE.",
        },
        {
            "order": 6,
            "capability": "governance",
            "goal": "Trust, Policy, Verification, Human Approval, Audit.",
        },
    ]

    result = {
        "audit": {
            "name": "NUSANTARA V2 CAPABILITY AUDIT",
            "version": "1.0.0",
            "engine_version": "3.0.0",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "read_only": True,
        },
        "repository": {
            "root": str(root),
            "scanned_files": len(files),
        },
        "capabilities": capabilities,
        "six_contracts": contract_results,
        "runtime_candidates": runtime_candidates,
        "gaps": gaps,
        "roadmap": roadmap,
    }

    (audit_dir / "V2_IMPLEMENTATION_MATRIX.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    (audit_dir / "V2_GAPS.json").write_text(
        json.dumps(gaps, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    (audit_dir / "V2_ROADMAP.json").write_text(
        json.dumps(roadmap, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        "# NUSANTARA V2 CAPABILITY AUDIT",
        "",
        f"- Engine: v3.0.0",
        f"- Audit: {result['audit']['timestamp_utc']}",
        f"- Read-only: YES",
        f"- Files scanned: {len(files)}",
        "",
        "## Capability Matrix",
        "",
        "| Capability | Status | Evidence |",
        "|---|---|---:|",
    ]

    for name, item in capabilities.items():
        lines.append(
            f"| `{name}` | **{item['status']}** | "
            f"{item['evidence_count']} files |"
        )

    lines += [
        "",
        "## Six V2 Contracts",
        "",
        "| Contract | Status | Evidence |",
        "|---|---|---:|",
    ]

    for name, item in contract_results.items():
        lines.append(
            f"| `{name.title()} Contract` | **{item['status']}** | "
            f"{item['evidence_count']} files |"
        )

    lines += [
        "",
        "## Runtime Candidates",
        "",
    ]

    for name, value in runtime_candidates.items():
        lines.append(
            f"- `{name}`: **{'YES' if value else 'NO/UNVERIFIED'}**"
        )

    lines += [
        "",
        "## Priority Gaps",
        "",
    ]

    if gaps:
        for gap in gaps:
            lines.append(
                f"- **{gap['priority']}** `{gap['capability']}` — "
                f"{gap['status']}: {gap['reason']}"
            )
    else:
        lines.append("- No gaps detected by static audit.")

    lines += [
        "",
        "## Recommended Build Order",
        "",
    ]

    for item in roadmap:
        lines.append(
            f"{item['order']}. **{item['capability']}** — {item['goal']}"
        )

    lines += [
        "",
        "## Important",
        "",
        "This document is a capability audit, not proof that every capability "
        "works at runtime. Runtime verification must be performed separately "
        "for capabilities classified as UNVERIFIED or PARTIAL.",
        "",
    ]

    (audit_dir / "V2_CAPABILITY_AUDIT.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print("NUSANTARA V2 CAPABILITY AUDIT")
    print("=" * 72)
    for name, item in capabilities.items():
        print(f"{name:32} {item['status']}")
    print()
    print(f"Artifacts: {audit_dir}")
    print("=" * 72)

    return result
'''

# Insert audit function immediately before main().
marker = "\ndef main() -> int:\n"

if marker not in text:
    raise SystemExit("ERROR: def main() ditemukan dalam format yang tidak dikenali.")

text = text.replace(
    marker,
    audit_function + marker,
    1,
)

# Add CLI argument after --status block.
status_block = '''    parser.add_argument(
        "--status",
        action="store_true",
    )
'''

audit_arg = status_block + '''
    parser.add_argument(
        "--v2-audit",
        action="store_true",
        help="Read-only audit kemampuan V2 dan enforcement architecture/contracts.",
    )
'''

if status_block not in text:
    raise SystemExit("ERROR: blok --status tidak ditemukan.")

text = text.replace(
    status_block,
    audit_arg,
    1,
)

# Include --v2-audit in the no-command condition.
old_condition = '''    if (
        not args.status
        and not args.phase
        and not args.all
    ):
'''

new_condition = '''    if (
        not args.status
        and not args.phase
        and not args.all
        and not args.v2_audit
    ):
'''

if old_condition not in text:
    raise SystemExit("ERROR: kondisi CLI utama tidak ditemukan.")

text = text.replace(
    old_condition,
    new_condition,
    1,
)

# Execute audit before creating the normal engine object.
old_engine = '''    engine = MasterDeveloperEngine(
        root=root,
        apply=args.apply,
        docker=args.docker,
        api=args.api,
        model=args.model,
        ollama_url=args.ollama_url,
        max_iterations=args.max_iterations,
    )

    try:
'''

new_engine = '''    if args.v2_audit:
        run_v2_capability_audit(root)
        return 0

    engine = MasterDeveloperEngine(
        root=root,
        apply=args.apply,
        docker=args.docker,
        api=args.api,
        model=args.model,
        ollama_url=args.ollama_url,
        max_iterations=args.max_iterations,
    )

    try:
'''

if old_engine not in text:
    raise SystemExit("ERROR: blok MasterDeveloperEngine tidak ditemukan.")

text = text.replace(
    old_engine,
    new_engine,
    1,
)

ENGINE.write_text(text, encoding="utf-8")

print("PATCH OK: --v2-audit ditambahkan ke Nusantara Master Developer Engine v3.0.0")
