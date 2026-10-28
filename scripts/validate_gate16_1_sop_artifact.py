import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SOP = ROOT / "data" / "knowledge" / "sop"

checks = {}

original = list((SOP / "original").glob("*.pdf"))
parsed = list((SOP / "parsed").rglob("*.json"))
semantic_master = list((SOP / "semantic_master").rglob("*.json"))
semantic_output = list((SOP / "semantic_output").rglob("*.json"))
engine_output = list((SOP / "engine_output").rglob("*.json"))
quality = list((SOP / "engine_output").rglob("quality_gate.json"))

checks["original_pdf"] = len(original) > 0
checks["parsed_artifacts"] = len(parsed) > 0
checks["semantic_master"] = len(semantic_master) > 0
checks["semantic_output"] = len(semantic_output) > 0
checks["engine_output"] = len(engine_output) > 0
checks["quality_gates"] = len(quality) > 0

passed = sum(checks.values())
total = len(checks)

status = "PASS" if passed == total else "FAIL"

result = {
    "gate": "16.1",
    "name": "SOP Artifact Truth",
    "version": "16.1.0",
    "timestamp": datetime.now().isoformat(),
    "status": status,
    "checks": {
        "passed": passed,
        "total": total,
        "results": checks
    },
    "artifacts": {
        "original_pdf": len(original),
        "parsed_json": len(parsed),
        "semantic_master_json": len(semantic_master),
        "semantic_output_json": len(semantic_output),
        "engine_output_json": len(engine_output),
        "quality_gate_json": len(quality)
    },
    "contract": {
        "pdf_source_must_exist": True,
        "parsed_representation_must_exist": True,
        "semantic_representation_must_exist": True,
        "engine_output_must_exist": True,
        "quality_gate_must_exist": True
    }
}

OUT = ROOT / "graphify-out" / "gate16_1_sop_artifact_truth.json"
OUT.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("=" * 70)
print("NUSANTARA GATE 16.1 - SOP ARTIFACT TRUTH")
print("=" * 70)
print()
print(f"Original PDF       : {len(original)}")
print(f"Parsed JSON        : {len(parsed)}")
print(f"Semantic Master    : {len(semantic_master)}")
print(f"Semantic Output    : {len(semantic_output)}")
print(f"Engine Output      : {len(engine_output)}")
print(f"Quality Gates      : {len(quality)}")
print()
print(f"Checks             : {passed} / {total}")
print(f"GATE 16.1 STATUS   : {status}")
print(f"Output             : {OUT}")

if status != "PASS":
    raise SystemExit(1)
