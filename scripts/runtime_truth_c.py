from pathlib import Path
import sys
import importlib
import json

ROOT = Path(__file__).resolve().parents[1]

# PAKSA SOURCE-OF-TRUTH PROJECT INI MENJADI PRIORITAS
ROOT_STR = str(ROOT)
sys.path = [ROOT_STR] + [p for p in sys.path if str(p).lower() != ROOT_STR.lower()]

OUT = ROOT / "graphify-out" / "runtime_truth_c.json"

TARGETS = [
    ("app.api.routes", "routes"),
    ("app.core", "core"),
    ("app.language.engine", "language"),
    ("app.problem.engine", "problem"),
    ("app.knowledge.engine", "knowledge"),
    ("app.reasoning.engine", "reasoning"),
]

print("=" * 72)
print("NUSANTARA RUNTIME TRUTH — C: SOURCE OF TRUTH")
print("=" * 72)
print(f"PROJECT ROOT : {ROOT}")
print(f"PYTHON       : {sys.executable}")

results = []

for module_name, label in TARGETS:
    item = {
        "label": label,
        "module": module_name,
        "imported": False,
        "file": None,
        "classes": [],
        "correct_root": False
    }

    try:
        # Bersihkan cache module agar hasil benar-benar berasal dari import ini
        for key in list(sys.modules):
            if key == "app" or key.startswith("app."):
                del sys.modules[key]

        module = importlib.import_module(module_name)

        file_path = Path(module.__file__).resolve()
        item["imported"] = True
        item["file"] = str(file_path)
        item["correct_root"] = str(file_path).lower().startswith(
            str(ROOT).lower()
        )

        item["classes"] = sorted([
            name for name, obj in vars(module).items()
            if isinstance(obj, type)
            and getattr(obj, "__module__", "") == module_name
        ])

        status = "OK" if item["correct_root"] else "WRONG ROOT"

        print()
        print(f"[{label.upper()}] {status}")
        print(f"  module : {module_name}")
        print(f"  file   : {file_path}")
        print(f"  classes: {', '.join(item['classes']) or '-'}")

    except Exception as exc:
        item["error"] = f"{type(exc).__name__}: {exc}"

        print()
        print(f"[{label.upper()}] ERROR")
        print(f"  {item['error']}")

    results.append(item)

all_correct = all(
    x["imported"] and x["correct_root"]
    for x in results
)

output = {
    "engine": "Nusantara Runtime Truth",
    "version": "2.0.0",
    "source_of_truth": str(ROOT),
    "python": sys.executable,
    "all_modules_from_source_of_truth": all_correct,
    "results": results
}

OUT.write_text(
    json.dumps(output, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print()
print("-" * 72)
print(
    "SOURCE OF TRUTH STATUS : "
    + ("VALID" if all_correct else "NEEDS INVESTIGATION")
)
print(f"Output : {OUT}")
print("RUNTIME TRUTH C: COMPLETE")
