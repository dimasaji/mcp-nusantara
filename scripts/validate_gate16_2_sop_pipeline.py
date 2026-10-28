import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
SOP = ROOT / "data" / "knowledge" / "sop"

def load(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None

checks = {}
documents = []

for pdf in sorted((SOP / "original").glob("*.pdf")):
    stem = pdf.stem

    # Cari seluruh artefak yang berhubungan dengan dokumen
    related = list(SOP.rglob(f"*{stem}*"))

    documents.append({
        "pdf": pdf.name,
        "size": pdf.stat().st_size,
        "related_artifacts": len(related),
    })

checks["pdf_sources"] = len(documents) > 0
checks["all_pdfs_nonempty"] = all(d["size"] > 0 for d in documents)

parsed_files = list((SOP / "parsed").rglob("*.json"))
semantic_master_files = list((SOP / "semantic_master").rglob("*.json"))
semantic_output_files = list((SOP / "semantic_output").rglob("*.json"))
quality_files = list((SOP / "engine_output").rglob("quality_gate.json"))

checks["parsed_available"] = len(parsed_files) >= len(documents)
checks["semantic_master_available"] = len(semantic_master_files) >= 1
checks["semantic_output_available"] = len(semantic_output_files) >= 1
checks["quality_gate_available"] = len(quality_files) >= len(documents)

# Validasi JSON inti
json_targets = (
    parsed_files[:20]
    + semantic_master_files[:20]
    + semantic_output_files[:20]
    + quality_files[:20]
)

valid_json = 0
invalid_json = []

for path in json_targets:
    data = load(path)
    if data is not None:
        valid_json += 1
    else:
        invalid_json.append(str(path))

checks["core_json_valid"] = len(invalid_json) == 0

passed = sum(checks.values())
total = len(checks)
status = "PASS" if passed == total else "FAIL"

result = {
    "gate": "16.2",
    "name": "SOP Pipeline Integrity",
    "version": "16.2.0",
    "timestamp": datetime.now().isoformat(),
    "status": status,
    "checks": {
        "passed": passed,
        "total": total,
        "results": checks
    },
    "documents": documents,
    "artifacts": {
        "parsed": len(parsed_files),
        "semantic_master": len(semantic_master_files),
        "semantic_output": len(semantic_output_files),
        "quality_gates": len(quality_files),
        "validated_json": len(json_targets),
        "valid_json": valid_json,
        "invalid_json": invalid_json,
    },
    "contract": {
        "pdf_sources_required": True,
        "pdfs_must_be_nonempty": True,
        "parsed_representation_required": True,
        "semantic_representation_required": True,
        "quality_gate_required": True,
        "core_json_must_be_valid": True,
        "no_llm_required": True,
    }
}

OUT = ROOT / "graphify-out" / "gate16_2_sop_pipeline_integrity.json"
OUT.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print("=" * 70)
print("NUSANTARA GATE 16.2 - SOP PIPELINE INTEGRITY")
print("=" * 70)
print()
print(f"PDF Sources         : {len(documents)}")
print(f"Parsed Artifacts    : {len(parsed_files)}")
print(f"Semantic Master     : {len(semantic_master_files)}")
print(f"Semantic Output     : {len(semantic_output_files)}")
print(f"Quality Gates       : {len(quality_files)}")
print(f"Valid JSON          : {valid_json}/{len(json_targets)}")
print()
print(f"Checks              : {passed} / {total}")
print(f"GATE 16.2 STATUS    : {status}")
print(f"Output              : {OUT}")

if status != "PASS":
    raise SystemExit(1)
