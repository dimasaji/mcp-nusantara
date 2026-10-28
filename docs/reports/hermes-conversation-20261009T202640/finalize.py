"""Record scoped diffs and actual XML test results, without application imports."""
import difflib
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
files = ["app/hermes/agent.py", "app/workflow/v1_langgraph.py", "tests/test_hermes_v1_conversation.py"]
audit, patch = [], []
for name in files:
    before_file = OUT / (name.replace("/", "__") + ".before")
    before = before_file.read_bytes() if before_file.exists() else b""
    after = (ROOT / name).read_bytes()
    audit.append({"path": name, "before_sha256": hashlib.sha256(before).hexdigest() if before_file.exists() else None,
        "after_sha256": hashlib.sha256(after).hexdigest(), "baseline": str(before_file) if before_file.exists() else "NEW_FILE"})
    patch.extend(difflib.unified_diff([line + "\n" for line in before.decode("utf-8-sig").splitlines()],
        [line + "\n" for line in after.decode("utf-8-sig").splitlines()], fromfile="before/"+name, tofile="after/"+name))
(OUT / "SCOPED_CHANGES.patch").write_text("".join(patch), encoding="utf-8", newline="\n")
runs = []
for result in sorted(OUT.glob("*/results.xml")):
    suites = list(ET.parse(result).getroot().iter("testsuite"))
    counts = {key: sum(int(s.get(key, 0)) for s in suites) for key in ("tests", "failures", "errors", "skipped")}
    counts["passed"] = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
    guard = json.loads((result.parent / "guards.json").read_text())
    mode = result.parent.name.rsplit("-", 2)[0]
    runs.append({"command": f".venv/Scripts/python.exe {OUT.relative_to(ROOT).as_posix()}/verify.py {mode}",
        "evidence": str(result), "counts": counts, "exit_code": guard["pytest_exit"], "guard": guard})
report = {
    "status": "IMPLEMENTED_TARGETED_VERIFIED / BROADER_REGRESSION_REVIEW_REQUIRED",
    "files": audit, "test_runs": runs,
    "final_source_tests": ["targeted-20261009-203602", "regression-core-20261009-203606"],
    "final_targeted": {"pass": 50, "fail": 0, "skip": 0, "exit": 0},
    "final_core_regression": {"pass": 232, "fail": 0, "skip": 0, "deselected": 3, "exit": 0},
    "excluded_core_cases": ["runtime_instances_differ_in_real_subprocesses", "bootstrap_layers", "owner_reads"],
    "unresolved": [
        {"finding": "TEMPORARY_MEMORY_REPLACE_ACCESS_DENIED", "status": "REVIEW_REQUIRED",
         "evidence": ["regression-20261009-203229/results.xml", "regression-final-20261009-203330/results.xml"],
         "detail": "Windows WinError 5 in two temporary-memory os.replace cases; one isolated rerun passed. Cause unknown; no memory code changed."},
        {"finding": "HTTP_MEMORY_TEST_STARTUP_BLOCKED", "status": "NOT_VERIFIED / OUT_OF_SCOPE_V2",
         "detail": "Existing test imports app.main before substituting fixtures. SQLite guard stopped active-store initialization before connection. Excluded thereafter; no V2 requests executed."}
    ],
    "behavior": "Explicit non-evidence conversation uses the already selected provider; repeat is local. Official/unknown requests and sensitive generated claims retain the unchanged evidence guard. Empty evidence never earns conversational grounding or trust.",
    "limits": ["Conservative rules: unrecognized requests retain evidence requirements", "No live API or real provider test", "No full-suite claim", "No loaded-process/build identity claim"],
    "preservation": {"runtime_operations": 0, "database_connections_to_active_store": 0,
        "v2_source_changes": 0, "dependency_installations": 0, "public_schema_changes": 0,
        "source_changes": files[:2], "new_test": files[2], "other_writes": "This new evidence directory only",
        "git_destructive_operations": 0, "graph_queries_updates": 0, "test_cache": "pytest cache provider disabled",
        "note": "Original source bytes retained in .before snapshots; patch is relative to those snapshots, not HEAD. Pre-existing working-tree changes retained; restricted historical directories produce Git permission warnings."},
    "rollback": "Reverse SCOPED_CHANGES.patch only after inspecting subsequent edits. Do not restore from HEAD or overwrite either source wholesale; pre-existing changes are in the .before snapshots.",
    "v1_acceptance": "HOLD", "v2": "DEFERRED"
}
(OUT / "IMPLEMENTATION_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"report": str(OUT / "IMPLEMENTATION_REPORT.json"), "files": audit}, indent=2))
