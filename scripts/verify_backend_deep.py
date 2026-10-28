"""Run backend verification with bounded execution and explicit offline limits.

This runner blocks subprocesses, production data, and writes outside its output.
Blocked operations are reported as isolation gaps, never silently skipped.
"""

import argparse
import hashlib
import importlib
import json
import os
import socket
import subprocess
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit
from urllib.request import url2pathname

ROOT = Path(__file__).resolve().parents[1]


def probe_local_hash(output):
    """Record actual ingestion outcomes, without changing a production store."""
    from app.core.nusantara_config import load_nusantara_config
    from app.knowledge.rag import RAG
    from app.knowledge.schemas import DocumentIngestRequest
    from app.knowledge.store import SQLiteVectorStore

    configuration = load_nusantara_config(project_root=output)
    store = SQLiteVectorStore(str(output / "hash-probe.db"))
    rag = RAG(nusantara_config=configuration, vector_store=store)
    request = DocumentIngestRequest(document_id="fixture-first", title="Fixture first",
                                    source="Informasi layanan sintetis untuk pemeriksaan offline. " * 8)
    first = rag.ingest_document(request)
    repeat = rag.ingest_document(request)
    second = rag.ingest_document(request.model_copy(update={"document_id": "fixture-second"}))
    chunks = store.get_chunks_by_document("fixture-first")
    observation = {
        "scope": "synthetic SQLite fixture, no model or production data",
        "declared_dimension": configuration.embedding.dimension,
        "declared_model": configuration.embedding.model,
        "legacy_model": configuration.legacy_declarations.embedding_model,
        "stored_dimensions": sorted({chunk.embedding.dimension for chunk in chunks}),
        "first": first.model_dump(), "repeat": repeat.model_dump(), "second": second.model_dump(),
    }
    (output / "local-hash-observation.json").write_text(json.dumps(observation, indent=2), encoding="utf-8")
    # Exit zero means the observation completed; inspect outcomes for correctness.
    return 0


def worker(output, paths, collect_only, hash_probe, integration=False):
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    sys.dont_write_bytecode = True
    # Retain host execution essentials, never inherit provider/operator secrets.
    keep = {"path", "systemroot", "windir", "comspec", "pathext", "systemdrive"}
    environment = {key: value for key, value in os.environ.items() if key.lower() in keep}
    os.environ.clear()
    os.environ.update(environment)
    home = output / "home"
    home.mkdir()
    os.environ.update(
        PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", PYTHONDONTWRITEBYTECODE="1",
        TEMP=str(output), TMP=str(output), USERPROFILE=str(home), HOME=str(home),
        NUSANTARA_DATA_DIR=str(output / "runtime"),
        NUSANTARA_KNOWLEDGE_DB=str(output / "knowledge" / "fixture.db"),
        NUSANTARA_ADMIN_TOKEN="deep-verification-fixture-only",
    )
    if integration:
        bootstrap = output / "child-bootstrap"
        bootstrap.mkdir()
        (bootstrap / "sitecustomize.py").write_text(
            "import os,sys\nsys.path.insert(0," + repr(str(ROOT)) + ")\n"
            "from scripts.backend_integration_guard import install\n"
            "install(os.environ['NUSANTARA_VERIFICATION_OUTPUT'],"
            "os.environ['NUSANTARA_VERIFICATION_REPOSITORY']," + repr(str(bootstrap)) + ")\n",
            encoding="utf-8")
        from scripts.backend_integration_guard import install
        install(output, ROOT, bootstrap)
    import dotenv
    import pytest
    from pydantic_settings.sources.providers.dotenv import DotEnvSettingsSource

    original_dotenv = dotenv.dotenv_values
    original_source = DotEnvSettingsSource._read_env_files
    production_data = ROOT / "data"
    violations = []
    reports = []
    collections = []
    local = threading.local()
    from scripts.backend_integration_guard import READ_ONLY_SOURCE_FIXTURES

    def resolved(value):
        return Path(os.path.realpath(os.fsdecode(value)))

    def inside(path, directory):
        return path == directory or directory in path.parents

    def forbidden(reason):
        violations.append(reason)
        raise RuntimeError("BACKEND_ISOLATION_BLOCKED: " + reason)

    def audit(event, args):
        if event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
            path = resolved(args[0])
            readonly_fixture = integration and path in {ROOT / relative for relative in READ_ONLY_SOURCE_FIXTURES}
            if (inside(path, production_data) and not readonly_fixture) or (
                path.name.startswith(".env") and path.name != ".env.example" and not inside(path, output)):
                forbidden("production_data_or_dotenv")
            mode, flags = args[1:3]
            writing = (isinstance(mode, str) and any(char in mode for char in "wax+")) or (
                isinstance(flags, int) and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
            )
            null_device = integration and str(args[0]).lower() == os.devnull.lower()
            if writing and not inside(path, output) and not null_device:
                forbidden("write_outside_run")
        if event == "sqlite3.connect" and args and str(args[0]) != ":memory:":
            database = args[0]
            if str(database).startswith("file:"):
                uri = urlsplit(str(database))
                if uri.netloc not in {"", "localhost"}:
                    forbidden("remote_database_uri")
                if uri.path == ":memory:" or parse_qs(uri.query).get("mode") == ["memory"]:
                    return
                database = url2pathname(uri.path)
            if not inside(resolved(database), output):
                forbidden("database_outside_run")
        if event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.truncate"}:
            if args and not inside(resolved(args[0]), output):
                forbidden("filesystem_mutation_outside_run")
        if event in {"os.rename", "os.link", "os.symlink"}:
            if any(not inside(resolved(value), output) for value in args[:2]):
                forbidden("filesystem_move_or_link_outside_run")
        if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "os.spawn"}:
            if not integration or event != "subprocess.Popen":
                forbidden("subprocess_requires_separate_verification")
        if event in {"socket.connect", "socket.bind", "socket.getaddrinfo"}:
            if not integration and not getattr(local, "socketpair", False):
                forbidden("live_network")

    original_socketpair = socket.socketpair

    def event_loop_socketpair(*args, **kwargs):
        local.socketpair = True
        try:
            return original_socketpair(*args, **kwargs)
        finally:
            local.socketpair = False

    def fixture_dotenv(path=None, *args, **kwargs):
        if path is not None and resolved(path) == ROOT / ".env":
            return {}
        return original_dotenv(path, *args, **kwargs)

    def fixture_env_files(source):
        if source.env_file == ".env" and Path.cwd() == ROOT:
            return {}
        return original_source(source)

    class Results:
        def pytest_collectreport(self, report):
            if report.failed:
                collections.append({"nodeid": report.nodeid, "detail": str(report.longrepr)})

        def pytest_runtest_logreport(self, report):
            if report.failed or report.when == "call" or report.skipped:
                reports.append({"nodeid": report.nodeid, "phase": report.when,
                                "outcome": report.outcome, "duration": report.duration,
                                "detail": str(report.longrepr) if report.longrepr else ""})

        def pytest_sessionfinish(self, session, exitstatus):
            terminal = session.config.pluginmanager.get_plugin("terminalreporter")
            (output / "results.json").write_text(json.dumps({
                "exit_code": int(exitstatus), "collected": session.testscollected,
                "outcome_counts": {name: len(terminal.stats.get(name, []))
                                   for name in ("passed", "failed", "skipped", "error")},
                "collection_errors": collections, "reports": reports,
                "isolation_blocks": violations,
            }, indent=2), encoding="utf-8")

    sys.addaudithook(audit)
    with (patch.object(Path, "home", return_value=home),
          patch.object(dotenv, "dotenv_values", fixture_dotenv),
          patch.object(DotEnvSettingsSource, "_read_env_files", fixture_env_files),
          patch.object(socket, "socketpair", event_loop_socketpair)):
        configuration = importlib.import_module("app.core.config")
        configuration.settings.compose_configuration(
            dotenv_environment={}, environment={},
            overrides={"knowledge": {"root": str(output / "knowledge"),
                                     "database": str(output / "knowledge" / "fixture.db")}},
        )
        if hash_probe:
            return probe_local_hash(output)
        arguments = ["-p", "pytest_asyncio.plugin", "-p", "no:cacheprovider",
                     "-o", "addopts=", "--ignore-glob=*.bak-*.py", "-q", "--tb=short",
                     "--continue-on-collection-errors", "--basetemp", str(output / "pytest-tmp"),
                     "--log-file", str(output / "pytest.log")]
        if collect_only:
            arguments.append("--collect-only")
        if integration:
            # These tests require run_evidence_tests_isolated.py as __main__.
            # test_evidence_runner_subprocess executes and checks all nine there.
            arguments.extend(["--ignore", "tests/test_evidence_runner_guards.py"])
        return pytest.main([*arguments, *(paths or ["tests"])], plugins=[Results()])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*")
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--collect-only", action="store_true")
    parser.add_argument("--probe-local-hash", action="store_true")
    parser.add_argument("--integration", action="store_true", help="allow guarded Python subprocesses and fixture loopback")
    parser.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if not args.worker.resolve().is_relative_to(ROOT / "artifacts" / "backend-deep"):
            parser.error("worker output must be inside artifacts/backend-deep")
        return worker(args.worker.resolve(), args.paths, args.collect_only, args.probe_local_hash, args.integration)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "artifacts" / "backend-deep" / stamp
    output.mkdir(parents=True)
    runner_source = Path(__file__).read_bytes()
    (output / "runner-source.py").write_bytes(runner_source)
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "--worker", str(output)]
    if args.collect_only:
        command.append("--collect-only")
    if args.probe_local_hash:
        command.append("--probe-local-hash")
    if args.integration:
        command.append("--integration")
    command.extend(args.paths)
    print("Verification output: " + str(output), flush=True)
    with (output / "pytest-output.txt").open("w", encoding="utf-8") as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        try:
            code = process.wait(timeout=args.timeout)
        except subprocess.TimeoutExpired:
            if os.name == "nt":
                taskkill = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32/taskkill.exe"
                try:
                    subprocess.run([str(taskkill), "/PID", str(process.pid), "/T", "/F"],
                                   stdout=log, stderr=subprocess.STDOUT, timeout=10, check=False,
                                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
                except (OSError, subprocess.TimeoutExpired) as error:
                    log.write("Process-tree cleanup failed: " + type(error).__name__ + "\n")
            if process.poll() is None:
                process.kill()
            process.wait(timeout=10)
            code = 124
    (output / "run.json").write_text(json.dumps({
        "exit_code": code, "timeout_s": args.timeout, "paths": args.paths or ["tests"],
        "collect_only": args.collect_only,
        "local_hash_probe": args.probe_local_hash,
        "integration": args.integration,
        "runner_sha256": hashlib.sha256(runner_source).hexdigest(),
        "limits": ["loopback allowed except reserved service ports" if args.integration else "no live network",
                   "guarded Python/fixture Git subprocesses" if args.integration else "no subprocesses in worker",
                   "no production data", "no writes outside output", "fixture configuration and credentials"],
    }, indent=2), encoding="utf-8")
    print("Worker exit code: " + str(code), flush=True)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
