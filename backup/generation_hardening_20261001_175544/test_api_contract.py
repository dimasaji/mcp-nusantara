import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]

API_URL = "http://127.0.0.1:8000/v1/chat"

REQUIRED_TOP_LEVEL = [
    "session_id",
    "response",
    "model",
    "provider_status",
    "latency_ms",
    "grounding",
    "understanding",
    "problem",
    "evidence",
    "timestamp",
]

REQUIRED_GROUNDING = [
    "enabled",
    "grounded",
    "reason",
]

REQUIRED_UNDERSTANDING = [
    "input",
    "output",
    "metadata",
]


def call_api():
    payload = {
        "session_id": "contract-test",
        "user_input": "Apa itu KTP-el?",
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
        return response.status, json.loads(
            response.read().decode("utf-8")
        )


def main():
    status, data = call_api()

    checks = []

    checks.append(("HTTP 200", status == 200))

    for key in REQUIRED_TOP_LEVEL:
        checks.append(
            (f"top-level:{key}", key in data)
        )

    grounding = data.get("grounding") or {}

    for key in REQUIRED_GROUNDING:
        checks.append(
            (f"grounding:{key}", key in grounding)
        )

    understanding = data.get("understanding") or {}

    for key in REQUIRED_UNDERSTANDING:
        checks.append(
            (f"understanding:{key}", key in understanding)
        )

    output = (
        understanding.get("output")
        if isinstance(understanding, dict)
        else None
    )

    intent = (
        output.get("intent")
        if isinstance(output, dict)
        else None
    )

    checks.append(
        (
            "understanding.output.intent",
            isinstance(intent, dict),
        )
    )

    checks.append(
        (
            "understanding.output.intent.intent",
            isinstance(intent, dict)
            and isinstance(intent.get("intent"), str),
        )
    )

    checks.append(
        (
            "understanding.output.intent.confidence",
            isinstance(intent, dict)
            and isinstance(
                intent.get("confidence"),
                (int, float),
            ),
        )
    )

    failed = [
        name
        for name, ok in checks
        if not ok
    ]

    print("=" * 72)
    print("NUSANTARA AI API CONTRACT TEST")
    print("=" * 72)

    for name, ok in checks:
        print(
            f"[{'PASS' if ok else 'FAIL'}] {name}"
        )

    print()
    print(
        f"RESULT: {len(checks) - len(failed)}/{len(checks)} PASS"
    )

    if failed:
        print("FAILED CONTRACTS:")
        for item in failed:
            print(f" - {item}")

        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())