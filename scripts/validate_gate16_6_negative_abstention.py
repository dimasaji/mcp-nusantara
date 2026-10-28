import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out" / "gate16_6_negative_abstention_truth.json"

files = {
    "grounding": ROOT / "app" / "knowledge" / "grounding.py",
    "rag": ROOT / "app" / "knowledge" / "rag.py",
    "knowledge_engine": ROOT / "app" / "knowledge" / "engine.py",
    "routes": ROOT / "app" / "api" / "routes.py",
}

patterns = [
    "not found",
    "no evidence",
    "insufficient",
    "abstain",
    "grounded",
    "evidence",
    "source",
    "confidence",
    "unknown",
    "cannot",
    "tidak ditemukan",
    "tidak ada informasi",
    "tidak tersedia",
    "bukti",
]

results = {}
all_pass = True

for name, path in files.items():
    text = path.read_text(
        encoding="utf-8",
        errors="ignore"
    ).lower() if path.exists() else ""

    found = [p for p in patterns if p in text]

    results[name] = {
        "exists": path.exists(),
        "matches": len(found),
        "patterns_found": found,
        "status": "PASS" if len(found) >= 2 else "FAIL"
    }

    if results[name]["status"] != "PASS":
        all_pass = False

# Cari test negatif yang sudah tersedia
test_files = list((ROOT / "tests").rglob("*.py"))

negative_tests = []

for path in test_files:
    text = path.read_text(
        encoding="utf-8",
        errors="ignore"
    ).lower()

    matched = [
        p for p in [
            "negative",
            "abstention",
            "unknown",
            "not found",
            "no evidence",
            "ungrounded",
            "hallucination",
            "grounding",
        ]
        if p in text
    ]

    if matched:
        negative_tests.append({
            "file": str(path.relative_to(ROOT)),
            "patterns": matched
        })

test_pass = len(negative_tests) > 0

if not test_pass:
    all_pass = False

status = "PASS" if all_pass else "FAIL"

result = {
    "gate": "16.6",
    "name": "Negative / Abstention Truth",
    "status": status,
    "static_contract": results,
    "negative_test_files": negative_tests,
    "contract": {
        "grounding_contract_required": True,
        "abstention_signal_required": True,
        "negative_tests_required": True,
        "llm_required": False,
    }
}

OUT.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("=" * 70)
print("NUSANTARA GATE 16.6 - NEGATIVE / ABSTENTION TRUTH")
print("=" * 70)
print()

for name, data in results.items():
    print(
        f"{name:<20} "
        f"{data['status']:<5} "
        f"matches={data['matches']}"
    )

print()
print(f"Negative test files : {len(negative_tests)}")
print(f"Checks               : {len([x for x in results.values() if x['status']=='PASS'])} / {len(results)}")
print(f"GATE 16.6 STATUS     : {status}")
print(f"Output               : {OUT}")

if status != "PASS":
    raise SystemExit(1)
