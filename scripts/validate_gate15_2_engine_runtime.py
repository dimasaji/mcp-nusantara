import json
import importlib
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out"

ENGINES = {
    "language_engine": (
        "app.language.engine",
        "LanguageEngine",
    ),
    "problem_engine": (
        "app.problem.engine",
        "ProblemEngine",
    ),
    "knowledge_engine": (
        "app.knowledge.engine",
        "KnowledgeEngine",
    ),
    "reasoning_engine": (
        "app.reasoning.engine",
        "ReasoningEngine",
    ),
}

print("=" * 68)
print("NUSANTARA GATE 15.2 - ENGINE RUNTIME TRUTH")
print("=" * 68)

results = {}

for name, (module_name, class_name) in ENGINES.items():
    item = {
        "module": module_name,
        "class": class_name,
        "module_loaded": False,
        "class_found": False,
        "file": None,
        "status": "FAIL",
    }

    try:
        module = importlib.import_module(module_name)

        item["module_loaded"] = True
        item["file"] = str(
            Path(module.__file__).resolve()
        )

        cls = getattr(module, class_name, None)

        if cls is not None:
            item["class_found"] = True
            item["status"] = "PASS"

    except Exception as exc:
        item["error"] = str(exc)

    results[name] = item

    print(
        f"{item['status']:<5} "
        f"{name:<24} "
        f"{module_name}"
    )

passed = sum(
    1
    for item in results.values()
    if item["status"] == "PASS"
)

total = len(results)

status = "PASS" if passed == total else "FAIL"

result = {
    "gate": "15.2",
    "name": "Engine Runtime Truth",
    "version": "15.2.0",
    "timestamp": datetime.now().isoformat(),
    "status": status,

    "checks": {
        "engine_count": total,
        "passed": passed,
        "all_loaded": passed == total,
    },

    "engines": results,

    "contract": {
        "language_engine": "app.language.engine.LanguageEngine",
        "problem_engine": "app.problem.engine.ProblemEngine",
        "knowledge_engine": "app.knowledge.engine.KnowledgeEngine",
        "reasoning_engine": "app.reasoning.engine.ReasoningEngine",
        "must_load_from_source": True,
        "must_resolve_class": True,
    },
}

output = OUT / "gate15_2_engine_runtime_truth.json"

output.write_text(
    json.dumps(result, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

print()
print("Engines validated   :", f"{passed} / {total}")
print("GATE 15.2 STATUS    :", status)
print("Output              :", output)

if status != "PASS":
    raise SystemExit(1)
