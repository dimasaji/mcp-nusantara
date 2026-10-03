from pathlib import Path
import ast
import json

ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "app" / "api" / "routes.py"
OUT = ROOT / "graphify-out" / "runtime_class_truth.json"

TARGET_FILES = [
    ROOT / "app" / "api" / "routes.py",
    ROOT / "app" / "language" / "engine.py",
    ROOT / "app" / "problem" / "engine.py",
    ROOT / "app" / "knowledge" / "engine.py",
    ROOT / "app" / "reasoning" / "engine.py",
]

def collect_imports(tree):
    result = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result.append({
                    "type": "import",
                    "module": alias.name,
                    "name": alias.asname or alias.name
                })

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""

            for alias in node.names:
                result.append({
                    "type": "from",
                    "module": module,
                    "name": alias.name,
                    "alias": alias.asname
                })

    return result

def collect_classes(tree):
    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ClassDef)
    ]

def collect_functions(tree):
    return [
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]

print("=" * 72)
print("NUSANTARA RUNTIME CLASS TRUTH")
print("=" * 72)

files = []

for path in TARGET_FILES:
    if not path.exists():
        continue

    source = path.read_text(encoding="utf-8-sig", errors="replace")
    tree = ast.parse(source)

    imports = collect_imports(tree)
    classes = collect_classes(tree)
    functions = collect_functions(tree)

    item = {
        "file": str(path),
        "classes": classes,
        "functions": functions,
        "imports": imports
    }

    files.append(item)

    print()
    print(f"[{path.relative_to(ROOT)}]")
    print(f"  Classes   : {', '.join(classes) or '-'}")
    print(f"  Functions : {len(functions)}")

    print("  Relevant imports:")

    for imp in imports:
        text = (
            f"{imp['module']}.{imp['name']}"
            if imp["type"] == "from"
            else imp["module"]
        )

        keywords = (
            "language", "problem", "knowledge",
            "reasoning", "rag", "engine", "core"
        )

        if any(k in text.lower() for k in keywords):
            print(f"    {text}")

routes_source = ROUTES.read_text(
    encoding="utf-8",
    errors="replace"
)

tree = ast.parse(routes_source)

chat_functions = []

for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        name = node.name.lower()

        if "chat" in name or "message" in name:
            chat_functions.append(node.name)

output = {
    "engine": "Nusantara Runtime Class Truth",
    "version": "1.0.0",
    "source_of_truth": str(ROOT),
    "files": files,
    "chat_related_functions": chat_functions
}

OUT.write_text(
    json.dumps(output, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print()
print("-" * 72)
print("CHAT RELATED FUNCTIONS")
print("-" * 72)

for name in chat_functions:
    print(f"  {name}")

print()
print(f"Output : {OUT}")
print("RUNTIME CLASS TRUTH: COMPLETE")

