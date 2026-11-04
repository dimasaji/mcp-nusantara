"""Read-only DeveloperCore contract and filesystem boundaries."""
import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest

from app.developer_core.engine import DeveloperAnalysis, DeveloperCoreEngine


@pytest.fixture
def project(tmp_path):
    for relative in DeveloperCoreEngine.ENGINE_PATHS.values():
        directory = tmp_path / relative
        directory.mkdir(parents=True)
        (directory / "engine.py").write_text("# fixture\n", encoding="utf-8")
    graph = tmp_path / "graphify-out/graph.json"
    graph.parent.mkdir()
    graph.write_text(json.dumps({
        "nodes": [
            {"id": "language", "label": "Language", "source_file": "app/language/engine.py"},
            {"id": "reasoning", "label": "Reasoning", "source_file": "app/reasoning/engine.py"},
        ],
        "links": [{"source": "language", "target": "reasoning", "relation": "calls"}],
    }), encoding="utf-8")
    return tmp_path


def engine(root, **kwargs):
    return DeveloperCoreEngine(project_root=root, **kwargs)


def test_initialization_and_legacy_dataclass(project):
    core = engine(project)
    assert core.project_root == project
    assert core.graph_path == Path("graphify-out/graph.json")
    legacy = DeveloperAnalysis("ready", True, 1, 0)
    assert legacy.to_dict()["status"] == "ready"
    assert DeveloperCoreEngine(project / "graphify-out/graph.json", project_root=project).analyze().graph_loaded


def test_analyze_contract_and_graph_evidence(project):
    result = engine(project).analyze()
    assert isinstance(result, DeveloperAnalysis)
    assert set("version project_root timestamp summary architecture dependencies workflows impact candidates risk evidence recommendations".split()) <= result.to_dict().keys()
    assert result.status == "ready"
    assert result.dependencies["relationships"] == [
        {"source": "language", "target": "reasoning", "relation": "calls"}
    ]
    assert result.impact["related_node_ids"] == ["language", "reasoning"]
    assert not result.dependencies["runtime_dependencies_verified"]
    assert not result.workflows["execution_enabled"]
    assert len(result.summary["graph_sha256"]) == 64


def test_self_analysis_contract_and_legacy_keys(project):
    result = engine(project).self_analyze(runtime_gates={"8": {"status": "grounded"}})
    assert set("engine_version engine_identity engine_capabilities engine_limitations self_analysis health contracts improvement_candidates risk".split()) <= result.keys()
    assert {"developer_core", "graphify", "gates", "engines", "risks", "recommendations"} <= result.keys()
    assert result["gates"]["8"]["status"] == "grounded"
    assert result["developer_core"]["version"].startswith("14.")
    assert result["contracts"]["self_modifying"] is False
    assert result["contracts"]["human_approval_required"] is True


def test_deterministic_and_captured_root(project, monkeypatch, tmp_path):
    core = engine(project)
    first = core.self_analyze()
    monkeypatch.chdir(project / "app")
    assert first == core.self_analyze() == engine(project).self_analyze()
    graph = project / "graphify-out/graph.json"
    data = json.loads(graph.read_text(encoding="utf-8"))
    stamp = graph.stat().st_mtime_ns
    data["nodes"].reverse()
    graph.write_text(json.dumps(data), encoding="utf-8")
    os.utime(graph, ns=(stamp, stamp))
    # The source hash deliberately changes with bytes; relationship ordering doesn't.
    second = core.analyze()
    assert first["self_analysis"]["dependencies"] == second.dependencies
    assert first["self_analysis"]["evidence"][1:] == second.evidence[1:]


def test_nonexistent_root_proposes_only(tmp_path):
    result = engine(tmp_path / "missing").analyze()
    assert result.status == "degraded"
    assert result.timestamp == "1970-01-01T00:00:00+00:00"
    assert result.candidates
    assert set("candidate reason risk evidence impact rollback recommended_action".split()) <= result.candidates[0].keys()
    assert not (tmp_path / "missing").exists()


@pytest.mark.parametrize("path", [".env", ".env.production", ".git/config", "data/knowledge.db", "secrets/token.json", "../outside.json"])
def test_protected_or_traversal_graph_never_opened(project, path, monkeypatch):
    original = Path.open
    opened = []

    def spy(file, *args, **kwargs):
        opened.append(file)
        return original(file, *args, **kwargs)

    monkeypatch.setattr(Path, "open", spy)
    result = engine(project, graph_path=path).analyze()
    assert not result.graph_loaded
    assert "graph_path_blocked" in {item["type"] for item in result.risks}
    assert opened == []


def test_absolute_outside_graph_denied(project, tmp_path):
    result = engine(project, graph_path=project.parent / "outside.json").analyze()
    assert not result.graph_loaded
    assert result.risk["level"] == "high"


def test_protected_root_denied(project):
    result = engine(project / ".git").analyze()
    assert not result.graph_loaded
    assert all(not item["exists"] for item in result.engines)


def test_junction_or_symlink_denied_before_enumeration(project, monkeypatch):
    blocked = project / "app/language"
    original = Path.is_junction
    monkeypatch.setattr(Path, "is_junction", lambda path: path == blocked or original(path))
    result = engine(project).analyze()
    assert not result.engines[0]["exists"]
    assert all(item.get("id") != "language" for item in result.evidence)
    assert "inventory_path_blocked" in {item["type"] for item in result.risks}


def test_bounded_depth_and_entry_count(project):
    directory = project / "app/language/nested"
    directory.mkdir()
    (directory / "deep.py").write_text("# deep", encoding="utf-8")
    core = engine(project)
    core.MAX_DEPTH = 1
    assert core.analyze().engines[0]["python_files"] == 1
    core.MAX_ENTRIES = 1
    first = core.analyze().to_dict()
    assert first == core.analyze().to_dict()
    assert "traversal_limit" in {item["type"] for item in first["risks"]}
    assert not first["impact"]["complete"]


@pytest.mark.parametrize("content", ["not json", "[]", '{"nodes": {}}', '{"nodes": [], "edges": {}}'])
def test_invalid_graph_degrades_safely(project, content):
    (project / "graphify-out/graph.json").write_text(content, encoding="utf-8")
    result = engine(project).analyze()
    assert not result.graph_loaded
    assert {item["type"] for item in result.risks} == {"graph_invalid"}


def test_graph_limits_and_permission_errors(project, monkeypatch):
    core = engine(project)
    core.MAX_GRAPH_BYTES = 2
    assert "graph_limit" in {item["type"] for item in core.analyze().risks}
    core.MAX_GRAPH_BYTES = DeveloperCoreEngine.MAX_GRAPH_BYTES
    core.MAX_GRAPH_NODES = 1
    assert not core.analyze().graph_loaded
    core.MAX_GRAPH_NODES = DeveloperCoreEngine.MAX_GRAPH_NODES

    def forbidden(*args, **kwargs):
        raise PermissionError("secret filesystem error")

    monkeypatch.setattr(Path, "open", forbidden)
    result = core.self_analyze()
    assert "secret filesystem error" not in json.dumps(result)
    assert result["health"]["status"] == "degraded"


def test_no_commands_no_source_database_or_config_writes(project, monkeypatch):
    protected = [project / ".env", project / "data/production.db"]
    protected[1].parent.mkdir()
    for path in protected:
        path.write_bytes(b"protected fixture")
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in project.rglob("*") if path.is_file()}

    def forbidden(*args, **kwargs):
        pytest.fail("analysis attempted execution or mutation")

    for name in ["run", "Popen", "call", "check_call", "check_output"]:
        monkeypatch.setattr(subprocess, name, forbidden)
    monkeypatch.setattr(os, "system", forbidden)
    for name in ["write_text", "write_bytes", "unlink", "rename", "replace", "mkdir"]:
        monkeypatch.setattr(Path, name, forbidden)
    core = engine(project)
    core.analyze()
    core.self_analyze()
    after = {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in project.rglob("*") if path.is_file()}
    assert before == after


def test_malformed_runtime_status_and_graph_labels_are_not_executed(project):
    core = engine(project)
    result = core.self_analyze(runtime_gates={"8": None, "9": {"status": {"execute": "evil"}}})
    assert result["gates"]["8"]["status"] == "known"
    assert result["gates"]["9"]["status"] == "known"
    graph = project / "graphify-out/graph.json"
    graph.write_text(json.dumps({"nodes": [None, {"id": [], "source_file": ".env"}],
                               "links": [None, {"source": {}, "target": []}]}), encoding="utf-8")
    assert core.analyze().dependencies["relationships"] == []
