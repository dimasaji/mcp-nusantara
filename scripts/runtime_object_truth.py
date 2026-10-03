from pathlib import Path
import sys
import json
import importlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

print("=" * 72)
print("NUSANTARA RUNTIME OBJECT TRUTH")
print("=" * 72)
print(f"ROOT   : {ROOT}")
print(f"PYTHON : {sys.executable}")

results = {}

def inspect_module(name):
    print()
    print(f"[{name}]")

    try:
        mod = importlib.import_module(name)

        print(f"  FILE : {Path(mod.__file__).resolve()}")

        result = {
            "module": name,
            "file": str(Path(mod.__file__).resolve()),
            "objects": {}
        }

        targets = [
            "LanguageEngine",
            "ProblemEngine",
            "KnowledgeEngine",
            "ReasoningEngine",
            "RAG",
            "ProductionHybridRAG",
            "GraphifyBridge",
            "GateIntegration"
        ]

        for target in targets:
            obj = getattr(mod, target, None)

            if obj is not None:
                try:
                    result["objects"][target] = {
                        "type": str(type(obj)),
                        "module": getattr(obj, "__module__", None),
                        "name": getattr(obj, "__name__", target)
                    }

                    print(
                        f"  {target:<22} "
                        f"module={getattr(obj, '__module__', '-')}"
                    )
                except Exception:
                    pass

        results[name] = result

    except Exception as exc:
        results[name] = {
            "module": name,
            "error": f"{type(exc).__name__}: {exc}"
        }

        print(f"  ERROR: {type(exc).__name__}: {exc}")

modules = [
    "app.api.routes",
    "app.language.engine",
    "app.problem.engine",
    "app.knowledge.engine",
    "app.reasoning.engine",
    "app.developer_core.graph_bridge",
    "app.core.gate_integration",
]

for name in modules:
    inspect_module(name)

print()
print("-" * 72)
print("RUNTIME OBJECT SUMMARY")
print("-" * 72)

for module, data in results.items():
    if "error" in data:
        print(f"{module:<45} ERROR")
    else:
        count = len(data["objects"])
        print(f"{module:<45} objects={count}")

OUT = ROOT / "graphify-out" / "runtime_object_truth.json"

OUT.write_text(
    json.dumps(
        {
            "engine": "Nusantara Runtime Object Truth",
            "version": "1.0.0",
            "source_of_truth": str(ROOT),
            "results": results
        },
        indent=2,
        ensure_ascii=False
    ),
    encoding="utf-8"
)

print()
print(f"Output : {OUT}")
print("RUNTIME OBJECT TRUTH: COMPLETE")
