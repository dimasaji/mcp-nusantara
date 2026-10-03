from pathlib import Path
import sys
import json
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from app.main import app

OUT = ROOT / "graphify-out" / "runtime_e2e_truth.json"

print("=" * 72)
print("NUSANTARA RUNTIME E2E TRUTH")
print("=" * 72)
print(f"ROOT   : {ROOT}")
print(f"PYTHON : {sys.executable}")

client = TestClient(app)

cases = [
    {
        "name": "basic_chat",
        "payload": {
            "user_input": "Halo, apakah Nusantara aktif?"
        }
    },
    {
        "name": "knowledge",
        "payload": {
            "user_input": "Apa itu KTP-el?"
        }
    },
    {
        "name": "problem",
        "payload": {
            "user_input": "Saya ingin mengetahui proses pengajuan KTP-el."
        }
    }
]

results = []

for case in cases:
    print()
    print(f"[{case['name'].upper()}]")

    started = time.perf_counter()

    try:
        response = client.post(
            "/v1/chat",
            json=case["payload"]
        )

        elapsed = round(
            (time.perf_counter() - started) * 1000,
            2
        )

        try:
            body = response.json()
        except Exception:
            body = response.text

        result = {
            "name": case["name"],
            "status_code": response.status_code,
            "elapsed_ms": elapsed,
            "success": response.status_code < 400,
            "response": body
        }

        print(f"  HTTP       : {response.status_code}")
        print(f"  LATENCY    : {elapsed} ms")
        print(f"  SUCCESS    : {result['success']}")

        if isinstance(body, dict):
            for key in [
                "intent",
                "intent_name",
                "confidence",
                "model",
                "answer",
                "response",
                "sources",
                "evidence",
                "reasoning"
            ]:
                if key in body:
                    value = body[key]

                    if isinstance(value, (dict, list)):
                        print(
                            f"  {key:<12}: "
                            f"{json.dumps(value, ensure_ascii=False)[:500]}"
                        )
                    else:
                        print(f"  {key:<12}: {value}")

        results.append(result)

    except Exception as exc:
        result = {
            "name": case["name"],
            "success": False,
            "error": f"{type(exc).__name__}: {exc}"
        }

        results.append(result)

        print(f"  ERROR      : {result['error']}")

passed = sum(
    1 for x in results
    if x.get("success") is True
)

total = len(results)

output = {
    "engine": "Nusantara Runtime E2E Truth",
    "version": "1.0.0",
    "source_of_truth": str(ROOT),
    "tests": results,
    "passed": passed,
    "total": total,
    "status": "PASS" if passed == total else "NEEDS_INVESTIGATION"
}

OUT.write_text(
    json.dumps(
        output,
        indent=2,
        ensure_ascii=False
    ),
    encoding="utf-8"
)

print()
print("-" * 72)
print(f"E2E RESULT : {passed}/{total}")
print(
    "STATUS     : "
    + ("PASS" if passed == total else "NEEDS INVESTIGATION")
)
print(f"Output     : {OUT}")
print("RUNTIME E2E TRUTH: COMPLETE")
