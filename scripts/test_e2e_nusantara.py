import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]

API_URL = "http://127.0.0.1:8000/v1/chat"

TESTS = [
    {
        "id": "E2E-001",
        "input": "Apa itu KTP-el?",
        "intent": "ask_general_info",
        "provider": "ollama",
        "grounded": True,
        "reason": "grounded",
    },
    {
        "id": "E2E-002",
        "input": "Bagaimana cara mengecek status KTP?",
        "intent": "ask_document_status",
        "provider": "local_rule",
        "grounded": True,
        "reason": "deterministic_response",
    },
    {
        "id": "E2E-003",
        "input": "Apa syarat membuat KTP-el?",
        "intent": "ask_document_requirements",
        "provider": "ollama",
        "grounded": False,
        "reason": "requirement_evidence_missing",
    },
    {
        "id": "E2E-004",
        "input": "Saya mau cek status KTP saya",
        "intent": "ask_document_status",
        "provider": "local_rule",
        "grounded": True,
        "reason": "deterministic_response",
    },
]


def call_api(user_input: str):
    payload = {
        "session_id": "e2e-regression",
        "user_input": user_input,
        "model": "llama3.2:1b",
        "stream": False,
    }

    body = json.dumps(payload).encode("utf-8")

    request = Request(
        API_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=120) as response:
        raw = response.read().decode("utf-8")
        return response.status, json.loads(raw)


def main():
    passed = 0
    failed = 0
    results = []

    print("=" * 72)
    print("NUSANTARA AI E2E REGRESSION")
    print("=" * 72)

    for test in TESTS:

        try:
            status, response = call_api(test["input"])

            understanding = response.get("understanding") or {}
            output = understanding.get("output") or {}
            intent_obj = output.get("intent") or {}

            actual_intent = intent_obj.get("intent")
            confidence = intent_obj.get("confidence")

            actual_provider = response.get("provider_status")

            grounding = response.get("grounding") or {}

            actual_grounded = grounding.get("grounded")
            actual_reason = grounding.get("reason")

            checks = {
                "http": status == 200,
                "intent": actual_intent == test["intent"],
                "provider": actual_provider == test["provider"],
                "grounded": actual_grounded == test["grounded"],
                "reason": actual_reason == test["reason"],
            }

            ok = all(checks.values())

            if ok:
                passed += 1
                mark = "PASS"
            else:
                failed += 1
                mark = "FAIL"

            print()
            print(
                f"[{mark}] {test['id']} | "
                f"{test['input']}"
            )
            print(
                f"  intent={actual_intent} "
                f"confidence={confidence}"
            )
            print(f"  provider={actual_provider}")
            print(f"  grounded={actual_grounded}")
            print(f"  reason={actual_reason}")

            if not ok:
                print(f"  CHECKS={checks}")

            results.append({
                "id": test["id"],
                "input": test["input"],
                "expected": test,
                "actual": {
                    "http": status,
                    "intent": actual_intent,
                    "confidence": confidence,
                    "provider": actual_provider,
                    "grounded": actual_grounded,
                    "reason": actual_reason,
                },
                "checks": checks,
                "passed": ok,
            })

        except Exception as exc:
            failed += 1

            print()
            print(f"[FAIL] {test['id']} | API ERROR")
            print(f"  {exc}")

            results.append({
                "id": test["id"],
                "input": test["input"],
                "passed": False,
                "error": str(exc),
            })

    result_path = (
        ROOT
        / "data"
        / "knowledge"
        / "benchmark"
        / "e2e_regression_result.json"
    )

    result_path.write_text(
        json.dumps(
            {
                "passed": passed,
                "failed": failed,
                "total": len(TESTS),
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 72)
    print(f"RESULT: {passed}/{len(TESTS)} PASS")
    print(f"FAILED: {failed}")
    print(f"RESULT FILE: {result_path}")
    print("=" * 72)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())