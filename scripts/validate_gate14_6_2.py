import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"

p = OUT / "gate14_6_directional_impact.json"
d = json.loads(p.read_text(encoding="utf-8"))

impact = d.get("impact", [])
targets = d.get("targets", [])

checks = []

# 1. Semua impact harus directional
checks.append(
    d.get("impact_policy", {}).get("directional") is True
)

# 2. Semua relation harus termasuk allowed relation
allowed = set(
    d.get("impact_policy", {}).get("allowed_relations", [])
)

checks.append(
    all(x.get("relation") in allowed for x in impact)
)

# 3. Tidak boleh ada self-impact
checks.append(
    all(
        x.get("source_node") != x.get("affected_node")
        for x in impact
    )
)

# 4. Depth harus valid
checks.append(
    all(
        isinstance(x.get("depth"), int)
        and 1 <= x.get("depth") <= 3
        for x in impact
    )
)

# 5. Runtime targets harus ada
checks.append(len(targets) > 0)

# 6. Impact harus mempunyai sumber runtime
checks.append(
    all(
        x.get("source_module")
        and x.get("source_file")
        for x in impact
    )
)

relation_counts = Counter(
    x.get("relation")
    for x in impact
)

result = {
    "gate": "14.6.2",
    "engine": "Developer Core Impact Truth Validator",
    "source": str(p),
    "checks": {
        "passed": sum(checks),
        "total": len(checks)
    },
    "validation": {
        "directional": checks[0],
        "allowed_relations_only": checks[1],
        "no_self_impact": checks[2],
        "valid_depth": checks[3],
        "runtime_targets_present": checks[4],
        "runtime_source_present": checks[5]
    },
    "statistics": {
        "targets": len(targets),
        "impact_records": len(impact),
        "relations": dict(relation_counts)
    },
    "status": "PASS" if all(checks) else "FAIL"
}

output = OUT / "gate14_6_2_impact_truth.json"

output.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("=" * 64)
print("NUSANTARA GATE 14.6.2 - IMPACT TRUTH VALIDATION")
print("=" * 64)
print("Targets              :", len(targets))
print("Impact records       :", len(impact))
print("Validation checks    :", sum(checks), "/", len(checks))
print("Directional          :", checks[0])
print("Allowed relations    :", checks[1])
print("No self-impact       :", checks[2])
print("Valid depth          :", checks[3])
print("Runtime targets      :", checks[4])
print("Runtime source       :", checks[5])
print("STATUS               :", result["status"])
print("Output               :", output)
