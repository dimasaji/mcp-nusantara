from pathlib import Path
import json
import re
from collections import Counter

src = Path("reports/CONFIGURATION_DISCOVERY_20261006.json")
out = Path("reports/CONFIGURATION_CLASSIFICATION_20261006.json")

d = json.loads(src.read_text(encoding="utf-8"))
candidates = d["candidates"]

rules = [
    ("backup", r"(^|[\\/_\.-])(backup|bak|old|copy|archive)([\\/_\.-]|$)|backup|archive|_old|\.bak$"),
    ("historical", r"(^|[\\/_\.-])(reports?|historical|legacy|checkpoint|snapshot|graphify-out)([\\/_\.-]|$)|historical|legacy"),
    ("test", r"(^|[\\/_\.-])(tests?|fixtures?|mocks?|examples?)([\\/_\.-]|$)|test_|_test|fixture|mock"),
    ("false_positive", r"(^|[\\/_\.-])(\.git|\.venv|venv|__pycache__|node_modules)([\\/_\.-]|$)")
]

result = []
counts = Counter()

for item in candidates:
    file_name = str(item.get("file", "")).replace("\\", "/").lower()
    name = str(item.get("name", "")).lower()
    kind = str(item.get("kind", "")).lower()

    search_text = f"{file_name} {name} {kind}"
    classification = "active_candidate"

    for label, pattern in rules:
        if re.search(pattern, search_text, re.I):
            classification = label
            break

    if classification == "active_candidate" and (
        file_name.endswith(".example") or "/.env.example" in file_name
    ):
        classification = "active_candidate"

    if (
        classification == "active_candidate"
        and item.get("default") == "VALUE_NOT_RECORDED"
        and kind not in (
            "environment_declaration",
            "structured_key_candidate",
            "assignment",
            "constant",
            "setting",
        )
    ):
        classification = "unknown"

    classified = dict(item)
    classified["classification"] = classification

    result.append(classified)
    counts[classification] += 1

payload = {
    "date": "20261006",
    "phase": "2-classification",
    "status": "COMPLETED_READ_ONLY",
    "source": str(src),
    "candidate_count": len(candidates),
    "classification_counts": dict(counts),
    "classifications": result,
    "notes": [
        "Heuristic classification only. No source/runtime files modified.",
        "active_candidate requires Phase 3 ownership/consumer verification.",
        "active_candidate does not prove active runtime configuration.",
        "unknown requires manual review."
    ]
}

out.write_text(
    json.dumps(payload, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print("=== NUSANTARA CONFIGURATION PHASE 2 ===")
print("Status     :", payload["status"])
print("Candidates :", len(candidates))
print("Output     :", out)
print()
print("CLASSIFICATION")
for key, value in sorted(counts.items()):
    print(f"  {key:18} : {value}")

print()
print("Next       : REVIEW CLASSIFICATION BEFORE PHASE 3")
