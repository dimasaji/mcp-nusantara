from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"
TRUTH = OUT / "gate14_runtime_graph_truth.json"
RESULT = OUT / "gate14_3_runtime_graph_connectivity.json"

checks = [
    ("routes.py", "graph_bridge.py"),
    ("routes.py", "gate_integration.py"),
    ("KnowledgeEngine", "RAG"),
]

results = []

for source, target in checks:
    p = subprocess.run(
        ["graphify", "path", source, target],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    output = (p.stdout + "\n" + p.stderr).strip()
    passed = p.returncode == 0 and "Shortest path" in output

    results.append({
        "source": source,
        "target": target,
        "status": "PASS" if passed else "FAIL",
        "output": output,
    })

passed_count = sum(x["status"] == "PASS" for x in results)

data = {
    "gate": "14.3",
    "engine": "Developer Core Runtime Graph Connectivity",
    "version": "14.3.0",
    "source_of_truth": str(ROOT),
    "gate14_2": json.loads(TRUTH.read_text(encoding="utf-8")),
    "connectivity": results,
    "checks_total": len(results),
    "checks_passed": passed_count,
    "status": "PASS" if passed_count == len(results) else "NEEDS_INVESTIGATION",
}

RESULT.write_text(
    json.dumps(data, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print("=" * 72)
print("NUSANTARA GATE 14.3 — RUNTIME GRAPH CONNECTIVITY")
print("=" * 72)
for r in results:
    print(f"{r['source']} -> {r['target']} : {r['status']}")
print("-" * 72)
print(f"CHECKS PASSED : {passed_count}/{len(results)}")
print(f"GATE 14.3    : {data['status']}")
print(f"OUTPUT       : {RESULT}")
