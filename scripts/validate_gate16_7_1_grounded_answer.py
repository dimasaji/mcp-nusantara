import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "graphify-out" / "gate16_7_pdf_to_answer_e2e.json"
OUT = ROOT / "graphify-out" / "gate16_7_1_grounded_answer_contract.json"

data = json.loads(INPUT.read_text(encoding="utf-8"))

response_obj = data.get("response")

if isinstance(response_obj, dict):
    answer = str(
        response_obj.get("response")
        or response_obj.get("answer")
        or response_obj.get("text")
        or ""
    ).strip()

    evidence_items = response_obj.get("evidence", [])
else:
    answer = str(response_obj or "").strip()
    evidence_items = data.get("evidence", [])

if not evidence_items:
    evidence_items = data.get("evidence", [])

answer_lower = answer.lower()

evidence_text = " ".join(
    str(item.get("source", "")) + " " +
    str(item.get("chunk", ""))
    for item in evidence_items
).lower()

abstention_phrases = [
    "informasi tersebut belum tersedia",
    "belum tersedia secara cukup",
    "tidak tersedia",
    "tidak ditemukan",
    "tidak ada informasi",
]

abstained = any(
    phrase in answer_lower
    for phrase in abstention_phrases
)

supported_fact = (
    "ktp-el adalah dokumen identitas penduduk"
    in evidence_text
    or
    "ktp-el merupakan dokumen identitas penduduk"
    in evidence_text
)

answer_contains_fact = (
    "ktp-el adalah dokumen identitas penduduk"
    in answer_lower
    or
    "ktp-el merupakan dokumen identitas penduduk"
    in answer_lower
)

checks = {
    "evidence_exists": len(evidence_items) > 0,
    "supported_fact_exists": supported_fact,
    "answer_exists": bool(answer),
    "not_abstained_with_evidence": not (
        supported_fact and abstained
    ),
    "answer_contains_supported_fact": answer_contains_fact,
}

passed = sum(checks.values())
total = len(checks)

status = "PASS" if passed == total else "FAIL"

result = {
    "gate": "16.7.1",
    "name": "Grounded Answer Contract",
    "status": status,
    "checks": {
        "passed": passed,
        "total": total,
        "results": checks,
    },
    "answer": answer,
    "evidence_count": len(evidence_items),
    "abstention_detected": abstained,
    "supported_fact_exists": supported_fact,
    "answer_contains_supported_fact": answer_contains_fact,
    "contract": {
        "evidence_required": True,
        "supported_fact_required": True,
        "answer_required": True,
        "abstention_for_supported_evidence_forbidden": True,
        "answer_must_reflect_evidence": True,
    },
}

OUT.write_text(
    json.dumps(
        result,
        indent=2,
        ensure_ascii=False
    ),
    encoding="utf-8"
)

print("=" * 70)
print("NUSANTARA GATE 16.7.1 - GROUNDED ANSWER CONTRACT")
print("=" * 70)
print()

for key, value in checks.items():
    print(
        f"{key:<32}: "
        f"{'PASS' if value else 'FAIL'}"
    )

print()
print("Actual answer:")
print(answer)
print()

print("Evidence count :", len(evidence_items))
print("Abstention     :", abstained)
print()
print(f"Checks              : {passed} / {total}")
print(f"GATE 16.7.1 STATUS  : {status}")
print(f"Output              : {OUT}")

if status != "PASS":
    raise SystemExit(1)
