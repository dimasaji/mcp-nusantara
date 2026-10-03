from pathlib import Path
import sys
import json
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out" / "runtime_e2e_lite.json"

url = "http://127.0.0.1:8000/v1/chat"

payload = json.dumps({
    "user_input": "Apa itu KTP-el?"
}).encode("utf-8")

request = urllib.request.Request(
    url,
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

print("=" * 72)
print("NUSANTARA RUNTIME E2E LITE")
print("=" * 72)
print(f"URL     : {url}")
print("TIMEOUT : 30 seconds")
print("INPUT   : Apa itu KTP-el?")
print()
print("Menjalankan 1 request...")

started = time.perf_counter()

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        elapsed = round((time.perf_counter() - started) * 1000, 2)
        body = response.read().decode("utf-8", errors="replace")

        print()
        print(f"HTTP    : {response.status}")
        print(f"LATENCY : {elapsed} ms")
        print()
        print("RESPONSE:")
        print(body[:3000])

        result = {
            "status": "PASS",
            "http_status": response.status,
            "latency_ms": elapsed,
            "response": body
        }

except Exception as exc:
    elapsed = round((time.perf_counter() - started) * 1000, 2)

    print()
    print(f"ERROR   : {type(exc).__name__}: {exc}")
    print(f"LATENCY : {elapsed} ms")

    result = {
        "status": "TIMEOUT_OR_ERROR",
        "latency_ms": elapsed,
        "error": f"{type(exc).__name__}: {exc}"
    }

OUT.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print()
print("-" * 72)
print(f"Output : {OUT}")
print("E2E LITE: COMPLETE")
