from pathlib import Path
import json
import sys
import importlib

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "graphify-out" / "runtime_truth.json"

TARGETS = [
    ("app.api.routes", "routes"),
    ("app.core", "core"),
    ("app.agent", "agent"),
    ("app.language.engine", "language"),
    ("app.problem.engine", "problem"),
    ("app.rag", "rag"),
    ("app.knowledge.engine", "knowledge"),
    ("app.reasoning.engine", "reasoning"),
]

print("=" * 72)
print("NUSANTARA RUNTIME TRUTH")
print("=" * 72)

results = []

for module_name, label in TARGETS:
    item = {
        "label": label,
        "module": module_name,
        "imported": False,
        "file": None,
        "classes": []
    }

    try:
        module = importlib.import_module(module_name)
        item["imported"] = True
        item["file"] = str(
            Path(module.__file__).resolve()
        ) if getattr(module, "__file__", None) else None

        item["classes"] = sorted([
            name for name, obj in vars(module).items()
            if isinstance(obj, type)
            and getattr(obj, "__module__", "") == module_name
        ])

        print()
        print(f"[{label.upper()}]")
        print(f"  module : {module_name}")
        print(f"  file   : {item['file']}")
        print(f"  classes: {', '.join(item['classes']) or '-'}")

    except Exception as exc:
        item["error"] = f"{type(exc).__name__}: {exc}"

        print()
        print(f"[{label.upper()}]")
        print(f"  ERROR: {item['error']}")

    results.append(item)

output = {
    "engine": "Nusantara Runtime Truth",
    "version": "1.0.0",
    "python": sys.version,
    "executable": sys.executable,
    "root": str(ROOT),
    "results": results
}

OUT.write_text(
    json.dumps(output, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print()
print("-" * 72)
print(f"Python     : {sys.executable}")
print(f"Output     : {OUT}")
print("RUNTIME TRUTH: COMPLETE")
