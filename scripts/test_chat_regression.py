import json
import urllib.request

BASE_URL = "http://127.0.0.1:8000/v1/chat"

with open("data/test_chat_regression.json", "r", encoding="utf-8-sig") as f:
    tests = json.load(f)

results = []

for test in tests:
    payload = {
        "session_id": "regression-" + test["id"],
        "user_input": test["input"],
        "model": "llama3.2:1b",
        "stream": False,
    }

    request = urllib.request.Request(
        BASE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))

        actual_intent = (
            data
            .get("understanding", {})
            .get("output", {})
            .get("intent", {})
            .get("intent")
        )

        confidence = (
            data
            .get("understanding", {})
            .get("output", {})
            .get("intent", {})
            .get("confidence")
        )

        results.append({
            "id": test["id"],
            "input": test["input"],
            "expected": test["expected_intent"],
            "actual": actual_intent,
            "confidence": confidence,
            "provider": data.get("provider_status"),
            "grounded": data.get("grounding", {}).get("grounded"),
            "match": actual_intent == test["expected_intent"],
        })

    except Exception as exc:
        results.append({
            "id": test["id"],
            "input": test["input"],
            "expected": test["expected_intent"],
            "actual": "ERROR",
            "confidence": 0,
            "provider": "-",
            "grounded": False,
            "match": False,
            "error": str(exc),
        })

print()
print("=" * 100)
print("NUSANTARA CORE — CHAT REGRESSION TEST")
print("=" * 100)

for r in results:
    status = "PASS" if r["match"] else "FAIL"

    print(
        f"[{status:4}] "
        f"{r['id']:18} "
        f"expected={r['expected']:28} "
        f"actual={str(r['actual']):28} "
        f"confidence={r['confidence']}"
    )

passed = sum(1 for r in results if r["match"])
total = len(results)

print()
print("=" * 100)
print(f"RESULT: {passed}/{total} intent tests passed")
print("=" * 100)

with open(
    "data/test_chat_regression_result.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
