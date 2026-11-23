import json
import urllib.request
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"

URL_BASIC = "http://127.0.0.1:8000/v1/health"
URL_DETAIL = "http://127.0.0.1:8000/v1/health/detail"


def get_json(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


print("=" * 68)
print("NUSANTARA GATE 15.1 - RUNTIME HEALTH TRUTH")
print("=" * 68)

checks = {}

try:
    basic = get_json(URL_BASIC)
    basic_ok = (
        basic.get("status") == "ok"
        and basic.get("service") == "nusantara-core"
    )
except Exception as exc:
    basic = {"error": str(exc)}
    basic_ok = False

checks["basic_health"] = basic_ok

try:
    detail = get_json(URL_DETAIL)
    detail_ok = detail.get("status") == "ok"
except Exception as exc:
    detail = {"error": str(exc)}
    detail_ok = False

checks["detail_health"] = detail_ok

components = detail.get("components", {}) if detail_ok else {}

expected_components = [
    "api",
    "language_engine",
    "problem_engine",
    "knowledge_engine",
    "reasoning_engine",
    "workflow_engine",
    "policy_engine",
    "trust_engine",
    "memory",
    "tools",
    "mcp",
    "handoff",
]

component_results = {}

for name in expected_components:
    component_results[name] = (
        components.get(name) == "available"
    )

checks["components"] = all(component_results.values())

llm = detail.get("llm", {}) if detail_ok else {}

checks["llm"] = (
    llm.get("status") == "ok"
    and llm.get("available") is True
    and bool(llm.get("model"))
)

passed = sum(
    1 for value in checks.values()
    if value
)

total = len(checks)

status = "PASS" if passed == total else "FAIL"

result = {
    "gate": "15.1",
    "name": "Runtime Health Truth",
    "version": "15.1.0",
    "timestamp": datetime.now().isoformat(),

    "status": status,

    "checks": {
        "basic_health": checks["basic_health"],
        "detail_health": checks["detail_health"],
        "components": checks["components"],
        "llm": checks["llm"],
    },

    "component_results": component_results,

    "runtime": {
        "basic": basic,
        "detail": detail,
    },

    "contract": {
        "api_must_be_healthy": True,
        "detail_endpoint_must_be_healthy": True,
        "required_components_must_be_available": True,
        "llm_must_be_available": True,
        "no_chat_generation_required": True,
    },
}

output = OUT / "gate15_1_runtime_health_truth.json"

output.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print()
print("Basic health        :", "PASS" if checks["basic_health"] else "FAIL")
print("Detail health       :", "PASS" if checks["detail_health"] else "FAIL")
print(
    "Components          :",
    "PASS" if checks["components"] else "FAIL"
)
print("LLM                 :", "PASS" if checks["llm"] else "FAIL")

print()
print("Checks              :", f"{passed} / {total}")
print("GATE 15.1 STATUS    :", status)
print("Output              :", output)

if status != "PASS":
    raise SystemExit(1)
