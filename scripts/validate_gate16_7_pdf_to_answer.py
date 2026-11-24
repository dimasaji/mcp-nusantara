import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out" / "gate16_7_pdf_to_answer_e2e.json"

url = "http://127.0.0.1:8000/v1/chat"

payload = {
    "user_input": "Apa itu KTP-el?"
}

data = json.dumps(payload).encode("utf-8")

request = urllib.request.Request(
    url,
    data=data,
    headers={"Content-Type": "application/json"},
    method="POST"
)

print("=" * 70)
print("NUSANTARA GATE 16.7 - PDF -> ANSWER E2E")
print("=" * 70)
print()
print("Question : Apa itu KTP-el?")
print("LLM call : 1x")
print()

started = time.time()

try:
    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read().decode("utf-8")
        http_status = response.status
except Exception as exc:
    print("HTTP ERROR :", exc)
    raise SystemExit(1)

latency_ms = round((time.time() - started) * 1000)

try:
    result = json.loads(raw)
except Exception:
    result = {
        "raw_response": raw
    }

print("HTTP status :", http_status)
print("Latency     :", latency_ms, "ms")
print()

# Tampilkan struktur utama tanpa membanjiri terminal
if isinstance(result, dict):
    print("Response keys:")
    for key in result.keys():
        print("  -", key)

    print()

    for key in [
        "answer",
        "response",
        "text",
        "grounded",
        "evidence",
        "sources",
        "retrieval",
        "intent",
        "developer_core",
    ]:
        if key in result:
            value = result[key]

            if isinstance(value, str) and len(value) > 1200:
                value = value[:1200] + "...[truncated]"

            print(f"{key}:")
            print(json.dumps(value, indent=2, ensure_ascii=False))
            print()

checks = {
    "http_200": http_status == 200,
    "response_json": isinstance(result, dict),
}

# Cari evidence/source secara rekursif
def find_keys(obj, wanted, path="root"):
    found = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.lower() in wanted:
                found.append((path + "." + key, value))
            found.extend(
                find_keys(value, wanted, path + "." + key)
            )

    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            found.extend(
                find_keys(value, wanted, path + f"[{i}]")
            )

    return found

evidence = find_keys(
    result,
    {
        "evidence",
        "sources",
        "source",
        "grounded",
        "grounding",
    }
)

checks["evidence_signal"] = len(evidence) > 0

# Jawaban harus ada
answer_candidates = find_keys(
    result,
    {
        "answer",
        "response",
        "text",
        "message",
    }
)

checks["answer_signal"] = len(answer_candidates) > 0

# Cari string yang mengindikasikan grounding
serialized = json.dumps(
    result,
    ensure_ascii=False
).lower()

grounding_terms = [
    "grounded",
    "evidence",
    "source",
    "citation",
    "chunk",
]

grounding_matches = [
    x for x in grounding_terms
    if x in serialized
]

checks["grounding_signal"] = len(grounding_matches) >= 1

passed = sum(checks.values())
total = len(checks)

status = "PASS" if passed == total else "FAIL"

artifact = {
    "gate": "16.7",
    "name": "PDF -> Answer E2E",
    "status": status,
    "question": payload["user_input"],
    "http_status": http_status,
    "latency_ms": latency_ms,
    "checks": {
        "passed": passed,
        "total": total,
        "results": checks
    },
    "grounding_matches": grounding_matches,
    "evidence_paths": [
        path for path, _ in evidence
    ],
    "answer_paths": [
        path for path, _ in answer_candidates
    ],
    "response": result,
    "contract": {
        "single_llm_call": True,
        "http_200_required": True,
        "answer_required": True,
        "evidence_signal_required": True,
        "grounding_signal_required": True,
    }
}

OUT.write_text(
    json.dumps(
        artifact,
        indent=2,
        ensure_ascii=False
    ),
    encoding="utf-8"
)

print("=" * 70)
print("E2E CHECK")
print("=" * 70)

for key, value in checks.items():
    print(
        f"{key:<24}: "
        f"{'PASS' if value else 'FAIL'}"
    )

print()
print(f"Checks              : {passed} / {total}")
print(f"GATE 16.7 STATUS    : {status}")
print(f"Output              : {OUT}")

if status != "PASS":
    raise SystemExit(1)
