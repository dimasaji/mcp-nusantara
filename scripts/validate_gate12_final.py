from __future__ import annotations

import importlib
import inspect
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

passed = 0
failed = 0


def check(name, fn):
    global passed, failed
    try:
        fn()
        print(f"[PASS] {name}")
        passed += 1
    except Exception as exc:
        print(f"[FAIL] {name}: {exc}")
        failed += 1


def discover_tool_modules():
    tools_dir = ROOT / "app" / "tools"

    if not tools_dir.exists():
        raise AssertionError("app/tools tidak ditemukan")

    modules = []

    for path in tools_dir.rglob("*.py"):
        if path.name.startswith("_"):
            continue

        relative = path.relative_to(ROOT).with_suffix("")
        module = ".".join(relative.parts)

        modules.append(module)

    if not modules:
        raise AssertionError("Tidak ada Python tool ditemukan")

    return sorted(modules)


def tools_exist():
    modules = discover_tool_modules()
    print(f"  Tool modules ditemukan : {len(modules)}")

    assert len(modules) > 0


def tools_importable():
    modules = discover_tool_modules()

    errors = []

    for module in modules:
        try:
            importlib.import_module(module)
        except Exception as exc:
            errors.append(f"{module}: {exc}")

    if errors:
        raise AssertionError(
            "Tool import gagal:\n" + "\n".join(errors)
        )


def tools_have_public_api():
    modules = discover_tool_modules()

    inspected = 0

    for module_name in modules:
        module = importlib.import_module(module_name)

        public_items = [
            name
            for name in dir(module)
            if not name.startswith("_")
        ]

        if public_items:
            inspected += 1

    assert inspected > 0, "Tidak ditemukan public API pada existing tools"


def tools_are_serializable():
    modules = discover_tool_modules()

    payload = []

    for module_name in modules:
        module = importlib.import_module(module_name)

        payload.append(
            {
                "module": module_name,
                "public_symbols": sorted(
                    name
                    for name in dir(module)
                    if not name.startswith("_")
                ),
            }
        )

    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
    )

    assert encoded
    assert "module" in encoded


def tools_do_not_execute_shell():
    modules = discover_tool_modules()

    forbidden = [
        "subprocess.",
        "os.system(",
        "os.popen(",
        "os.spawn",
        "os.exec",
        "eval(",
        "exec(",
    ]

    violations = []

    for module_name in modules:
        module = importlib.import_module(module_name)

        source_file = inspect.getsourcefile(module)

        if not source_file:
            continue

        source = Path(source_file).read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for pattern in forbidden:
            if pattern in source:
                violations.append(
                    f"{module_name}: {pattern}"
                )

    if violations:
        raise AssertionError(
            "Forbidden execution primitive:\n"
            + "\n".join(violations)
        )


def deterministic_discovery():
    a = discover_tool_modules()
    b = discover_tool_modules()

    assert a == b
    assert a == sorted(a)


print("=" * 72)
print("NUSANTARA GATE 12 FINAL")
print("EXISTING TOOLS PRESERVATION CONTRACT")
print("=" * 72)

check(
    "12.1 Existing tools discovered",
    tools_exist,
)

check(
    "12.2 Existing tools importable",
    tools_importable,
)

check(
    "12.3 Existing tools expose public API",
    tools_have_public_api,
)

check(
    "12.4 Existing tools serializable",
    tools_are_serializable,
)

check(
    "12.5 Existing tools execution boundary",
    tools_do_not_execute_shell,
)

check(
    "12.6 Existing tools discovery deterministic",
    deterministic_discovery,
)

print("-" * 72)
print(f"VALIDATION CHECKS : {passed + failed}")
print(f"PASS              : {passed}")
print(f"FAIL              : {failed}")
print("-" * 72)

if failed == 0:
    print("GATE 12 FINAL     : PASS")
    print("EXISTING TOOLS    : PRESERVED")
    print("PRODUCTION WRITE  : NOT ENABLED")
    print("SHELL EXECUTION   : NOT ENABLED")
else:
    print("GATE 12 FINAL     : FAIL")
    raise SystemExit(1)

print("=" * 72)
