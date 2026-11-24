"""Local engineering entrypoint; no application startup or production operations.

Reuses pytest and the application's source identity rather than duplicating engines.
Inspection reads source/metadata only. Cleanup is a proposal, never deletion.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SKIP = {".git", ".venv", "venv", "__pycache__", "node_modules", ".dev",
        ".pytest_cache", ".mypy_cache", ".ruff_cache", "graphify-out", "reports",
        "data", "nusantara-models", "audit_reports", ".developer_staging"}
CORE = ["app/main.py", "app/api/routes.py", "app/api/v2_routes.py",
        "app/v2/orchestrator.py", "app/v2/hermes_adapter.py", "app/models/router.py",
        "app/models/ollama.py", "app/knowledge/rag.py", "app/context/context_builder.py"]
SUITES = {
    "control": ["tests/test_developer_control.py"],
    "baseline": ["tests/test_configuration_contract.py", "tests/test_configuration_integration.py",
                 "tests/test_developer_core_engine_contract.py", "tests/test_v1_response_projection.py",
                 "tests/v2/test_v2_core.py", "tests/v2/test_context_budget.py"],
    "full": ["tests"],
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class DeveloperControl:
    def __init__(self, root=ROOT):
        self.root = Path(root).resolve()

    def output_path(self, relative):
        path = (self.root / relative).resolve()
        path.relative_to(self.root)
        return path

    def write_json(self, relative, value):
        path = self.output_path(relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        # Resolve again after creating parents, before writing through any link.
        path = self.output_path(relative)
        fd, temporary = tempfile.mkstemp(prefix=".control-", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(value, stream, indent=2, ensure_ascii=False)
                stream.write("\n")
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def read_json(self, relative, default=None):
        path = self.output_path(relative)
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default

    def git(self):
        executable = shutil.which("git") or os.environ.get("NUSANTARA_TEST_GIT")
        bundled = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd/git.exe"
        if not executable and bundled.is_file():
            executable = str(bundled)
        if not executable:
            return {"status": "UNAVAILABLE"}
        result = {}
        for key, args in [("branch", ["branch", "--show-current"]),
                          ("head", ["rev-parse", "HEAD"]),
                          ("working_tree", ["status", "--porcelain=v1"]),
                          ("recent_commits", ["log", "-4", "--oneline"])]:
            run = subprocess.run([executable, *args], cwd=self.root, capture_output=True,
                                 text=True, timeout=20, check=False)
            if run.returncode:
                return {"status": "UNAVAILABLE", "failed_operation": key}
            result[key] = run.stdout.strip()
        return {"status": "AVAILABLE", **result}

    def inventory(self):
        records, imports, errors = [], [], []
        for folder, dirs, names in os.walk(self.root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if d not in SKIP and
                             not (Path(folder) / d).is_symlink())
            for name in sorted(names):
                path = Path(folder) / name
                if path.is_symlink():
                    continue
                # Never inspect credential/environment contents.
                if name.startswith(".env"):
                    continue
                relative = path.relative_to(self.root).as_posix()
                record = {"path": relative, "bytes": path.stat().st_size,
                          "suffix": path.suffix, "classification": "UNKNOWN",
                          "authority": "NOT_PROVEN", "recoverable_cleanup": "NOT_APPROVED"}
                if relative.startswith(("app/", "tests/")):
                    record["classification"] = "KEEP"
                    record["authority"] = "APP_IMPLEMENTATION" if relative.startswith("app/") else "TEST"
                elif relative.startswith(("archive/", "backup/", "integration/", "app_backup_")):
                    record["authority"] = "HISTORICAL_OR_EXPERIMENTAL_REQUIRES_REFERENCE_REVIEW"
                if path.suffix == ".py":
                    raw = path.read_bytes()
                    record["sha256"] = hashlib.sha256(raw).hexdigest()
                    try:
                        tree = ast.parse(raw, filename=relative)
                        record["syntax"] = "PASS"
                        for node in ast.walk(tree):
                            if isinstance(node, ast.ImportFrom):
                                imports.append({"file": relative, "line": node.lineno,
                                                "module": node.module, "level": node.level,
                                                "names": [a.name for a in node.names]})
                            elif isinstance(node, ast.Import):
                                imports.extend({"file": relative, "line": node.lineno,
                                                "module": a.name, "level": 0, "names": []}
                                               for a in node.names)
                    except (SyntaxError, UnicodeError) as error:
                        record["syntax"] = "FAIL"
                        errors.append({"file": relative, "type": type(error).__name__})
                records.append(record)
        return {"status": "SCOPED_STATIC_INVENTORY", "files": records, "imports": imports,
                "syntax_errors": errors, "counts": dict(Counter(p["classification"] for p in records)),
                "excluded_roots": sorted(SKIP), "runtime_authority_proven": False}

    def build_identity(self):
        path = self.root / "app/core/runtime_identity.py"
        if not path.is_file():
            return "UNAVAILABLE"
        spec = importlib.util.spec_from_file_location("_control_identity", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.source_build_id(self.root)

    def architecture(self):
        inventory = self.inventory()
        internal = [v for v in inventory["imports"] if (v["module"] or "").startswith("app.")]
        missing = []
        for edge in internal:
            module = self.root.joinpath(*edge["module"].split("."))
            if not module.with_suffix(".py").is_file() and not module.is_dir():
                missing.append(edge)
        existing = [f for f in CORE if (self.root / f).is_file()]
        return {"status": "SCOPED_STATIC_ARCHITECTURE", "entrypoints": existing,
                "absolute_app_imports": internal, "missing_absolute_app_modules": missing,
                "active_syntax_errors": [v for v in inventory["syntax_errors"]
                                         if v["file"].startswith("app/")],
                "capabilities": {"HermesAdapter": "app/v2/hermes_adapter.py" in existing,
                                 "ModelRouter": "app/models/router.py" in existing,
                                 "named_ModelGateway": (self.root / "app/models/gateway.py").is_file(),
                                 "named_ExecutorInterface": (self.root / "app/execution/base.py").is_file()},
                "limits": "Imports/filenames do not prove live capability, dynamic resolution, or protocol equivalence"}

    def health(self):
        packages = {}
        for name in ("fastapi", "uvicorn", "pydantic", "pydantic-settings", "httpx", "pytest"):
            try:
                packages[name] = metadata.version(name)
            except metadata.PackageNotFoundError:
                packages[name] = "MISSING"
        return {"status": "LOCAL_DEPENDENCY_CHECK", "interpreter": sys.executable,
                "packages": packages, "source_build_id": self.build_identity(),
                "provider_health": "NOT_RUN", "worker_health": "NOT_RUN",
                "runtime_startup": "NOT_RUN", "database_connection": "NOT_RUN"}

    def status(self):
        return {"project_state": self.read_json(".dev/PROJECT_STATE.json", {"status": "NOT_CREATED"}),
                "tasks": self.read_json(".dev/TASKS.json", {"tasks": []}), "git": self.git()}

    def cleanup(self):
        inventory = self.inventory()
        groups = {}
        for record in inventory["files"]:
            if record.get("sha256"):
                groups.setdefault(record["sha256"], []).append(record["path"])
        return {"status": "DRY_RUN_ONLY", "deleted": [], "moved": [],
                "exact_duplicate_groups": [v for v in groups.values() if len(v) > 1],
                "candidates": [v for v in inventory["files"] if v["classification"] == "UNKNOWN"],
                "decision": "KEEP until imports/config/dynamic references and Git recoverability reviewed"}

    def test(self, suite):
        # Only reviewed, fixed test sets. No shell commands or arbitrary script dispatch.
        report = self.output_path(f".dev/test-{suite}.xml")
        report.parent.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, "-m", "pytest", *SUITES[suite], "-q",
                   f"--junitxml={report}"]
        started = utc_now()
        run = subprocess.run(command, cwd=self.root, check=False)
        record = {"suite": suite, "started_at": started, "finished_at": utc_now(),
                  "exit_code": run.returncode, "status": "PASS" if run.returncode == 0 else "FAIL",
                  "junit": report.relative_to(self.root).as_posix(), "command": command}
        self.write_json(f".dev/test-{suite}.json", record)
        return record

    def validate(self):
        architecture, health = self.architecture(), self.health()
        passed = not architecture["active_syntax_errors"] and not architecture["missing_absolute_app_modules"]
        passed = passed and all(v != "MISSING" for v in health["packages"].values())
        return {"status": "PASS_SCOPED_STATIC" if passed else "FAIL_SCOPED_STATIC",
                "architecture": architecture, "health": health,
                "overall_v1_acceptance": "NOT_EVALUATED_BY_THIS_STATIC_CHECK"}

    def report(self):
        inventory, architecture = self.inventory(), self.architecture()
        self.write_json(".dev/repo_inventory.json", inventory)
        result = {"generated_at": utc_now(), "architecture": architecture,
                  "health": self.health(), "git": self.git(),
                  "overall_v1_acceptance": "FAIL/HOLD", "production_verification": "NOT_RUN"}
        self.write_json(".dev/control_report.json", result)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["inspect", "inventory", "status", "health", "test",
                                           "architecture-check", "cleanup", "validate", "report"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--suite", choices=list(SUITES), default="baseline")
    args = parser.parse_args(argv)
    if args.command == "cleanup" and not args.dry_run:
        parser.error("cleanup requires --dry-run; destructive cleanup is not implemented")
    control = DeveloperControl()
    try:
        methods = {"inspect": control.inventory, "inventory": control.inventory,
                   "status": control.status, "health": control.health,
                   "architecture-check": control.architecture, "cleanup": control.cleanup,
                   "validate": control.validate, "report": control.report}
        result = control.test(args.suite) if args.command == "test" else methods[args.command]()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1 if result.get("status", "").startswith("FAIL") else 0
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "FAIL", "error_type": type(error).__name__}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
