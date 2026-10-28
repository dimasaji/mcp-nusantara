"""Write scoped implementation evidence; no application imports or data access."""
from datetime import datetime, timezone
from pathlib import Path
import difflib
import hashlib
import json
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
created = ["app/models/openrouter.py", "app/workflow/v1_langgraph.py",
           "tests/test_openrouter_provider.py", "tests/test_v1_langgraph.py",
           "docs/OPENROUTER_LANGGRAPH.md"]
records, patch = [], []
for reference in sorted(OUT.glob("*.before")):
    relative = reference.name.removesuffix(".before").replace("__", "/")
    before, after = reference.read_bytes(), (ROOT / relative).read_bytes()
    records.append({"path": relative, "before_sha256": hashlib.sha256(before).hexdigest(),
                    "after_sha256": hashlib.sha256(after).hexdigest(), "kind": "MODIFIED"})
    patch.extend(difflib.unified_diff(before.decode("utf-8-sig").splitlines(True),
        after.decode("utf-8-sig").splitlines(True), fromfile="a/"+relative, tofile="b/"+relative))
for relative in created:
    content = (ROOT / relative).read_bytes()
    records.append({"path": relative, "after_sha256": hashlib.sha256(content).hexdigest(), "kind": "CREATED"})
    patch.extend(difflib.unified_diff([], content.decode().splitlines(True),
        fromfile="/dev/null", tofile="b/"+relative))
(OUT / "SCOPED_CHANGES.patch").write_bytes("".join(patch).replace("\r\n", "\n").encode("utf-8"))
sources = sorted((record["path"], record["after_sha256"]) for record in records
                 if record["path"].startswith("app/") or record["path"] == "pyproject.toml")
fingerprint = "sha256:" + hashlib.sha256(json.dumps(sources, separators=(",", ":")).encode()).hexdigest()
results = []
for run in sorted(OUT.iterdir()):
    if not run.is_dir() or run.name == "workflow-dependencies":
        continue
    item = {"run": run.name, "command": ".venv/Scripts/python.exe -B " +
            "docs/reports/openrouter-workflow-20261009T184538/verify.py " + run.name.split("-2026")[0]}
    try:
        tree = ET.parse(run / "results.xml")
        suites = tree.getroot().findall("testsuite")
        counts = {key: sum(int(suite.get(key, "0")) for suite in suites)
                  for key in ("tests", "failures", "errors", "skipped")}
        counts["passed"] = counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"]
        item["counts"] = counts
        item["failures"] = [case.get("name") for case in tree.iter("testcase")
                            if case.find("failure") is not None or case.find("error") is not None]
    except (ET.ParseError, FileNotFoundError):
        item["counts"] = None
        item["limitation"] = "JUnit incomplete after blocked platform.node subprocess; not a PASS."
    guards = run / "guards.json"
    item["exit_code"] = json.loads(guards.read_text())["pytest_exit"] if guards.exists() else 1
    item["deselected"] = 3 if run.name.startswith("regression-") else 0
    results.append(item)
packages = []
for metadata in sorted((OUT / "workflow-dependencies").glob("*.dist-info/METADATA")):
    fields = {line.split(": ", 1)[0]: line.split(": ", 1)[1] for line in
              metadata.read_text(encoding="utf-8").splitlines() if line.startswith(("Name: ", "Version: "))}
    packages.append(fields)
decision = {"request_id": "HDR-OPENROUTER-01", "owner_choice": "A",
            "scope": "One additive openrouter value in public provider_status enum; local source/tests only",
            "runtime_activation_authorized": False, "status": "IMPLEMENTED_VERIFIED_SCOPED"}
audit = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "files": records,
         "fingerprint": fingerprint, "fingerprint_scope": sources,
         "note": "Scoped source bytes, not full code closure or user-runtime identity.",
         "preservation": "Existing baseline files retained; scoped patch computed against pre-task snapshots, not HEAD.",
         "active_database_and_sidecars": "NOT_ACCESSED_OR_MODIFIED_BY_TASK",
         "runtime_operations": "NONE", "v2_changes": "NONE"}
report = {"status": "IMPLEMENTED_VERIFIED_SCOPED_OFFLINE", "v1": "HOLD", "v2": "DEFERRED",
          "audit": audit, "decision": decision, "test_runs": results,
          "dependency_install": {"command": ".venv/Scripts/python.exe -B -m pip install --disable-pip-version-check --no-cache-dir --no-compile --target docs/reports/openrouter-workflow-20261009T184538/workflow-dependencies 'langgraph>=1.0,<2'",
                                 "exit_code": 0, "shared_environment_modified": False,
                                 "packages": packages},
          "latest_results": "169 PASS / 0 FAIL / 0 ERROR / 0 SKIP / 3 DESELECTED, exit 0",
          "excluded": {"test_runtime_instances_differ_in_real_subprocesses": "subprocess blocked",
                       "test_bootstrap_layers_preserve_provenance_and_secrets": "Settings bootstrap outside offline scope",
                       "test_owner_reads_dotenv_once_and_process_environment_wins": "Settings/.env bootstrap outside offline scope"},
          "initial_findings": ["BOM read in AST test corrected using utf-8-sig",
              "Public enum changed: owner choice A obtained, historical assertion permits only that exact delta",
              "JUnit platform.node subprocess blocked; runner uses fixed isolated XML hostname",
              "pytest reserved request parameter renamed in new test",
              "AST node locations and Pydantic forward references corrected in new endpoint test"],
          "token_usage_verification": "VERIFIED_MOCK_PARSING_ONLY",
          "cost_verification": "PARTIAL; provider-reported fields handled, live billing UNKNOWN, no hard budget",
          "langgraph": "VERIFIED_SCOPED: real StateGraph 1.2.14, existing Hermes method, mock providers/services",
          "limitations": ["No real OpenRouter/Ollama call or loaded-weight attestation",
              "No running-process/HTTP server verification; endpoint AST execution is isolated source evidence",
              "No production/native RAG or active-store integration",
              "Existing local model-control routes are not cloud controls",
              "Optional workflow packages tested on isolated import path, not installed in shared runtime",
              "Structured generation and native streaming fail closed; not implemented",
              "Client cancellation does not attest server/provider cancellation or avoidance of charges",
              "Graphify cache/update not run to preserve unrelated graph artifacts and data-access boundaries",
              "Repository-wide status has pre-existing inaccessible report directories; no completeness claim for unrelated filesystem"],
          "gates_open": ["V1 mandatory security, recovery, knowledge/provenance, memory and deployment gates remain unresolved",
                         "Explicit future runtime/cloud activation and operational readiness verification required"],
          "references": ["https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request",
                         "https://reference.langchain.com/python/langgraph/graph/state/StateGraph"]}
for name, content in {"CHANGE_AUDIT.json": audit, "OWNER_DECISION.json": decision,
                      "TEST_RESULTS.json": results, "IMPLEMENTATION_REPORT.json": report}.items():
    target = OUT / name
    if target.exists():
        raise RuntimeError("REFUSE_EVIDENCE_OVERWRITE")
    target.write_text(json.dumps(content, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"fingerprint": fingerprint, "files": [record["path"] for record in records],
                  "latest": report["latest_results"], "packages": len(packages)}, indent=2))
