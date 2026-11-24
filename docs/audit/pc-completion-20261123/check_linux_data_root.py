"""Run inside an isolated Linux container with ephemeral /data and /tmp."""
import importlib.util
import json
import sys
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("audited_engine", "/audit/engine.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def fixture(root):
    root.mkdir()
    for relative in module.DeveloperCoreEngine.ENGINE_PATHS.values():
        directory = root / relative
        directory.mkdir(parents=True)
        (directory / "engine.py").write_text("# fixture\n")
    graph = root / "graphify-out"
    graph.mkdir()
    (graph / "graph.json").write_text('{"nodes": [], "links": []}')
    return module.DeveloperCoreEngine(project_root=root)


with tempfile.TemporaryDirectory(dir="/data") as allowed_parent, tempfile.TemporaryDirectory(dir="/tmp") as ordinary_parent:
    allowed_root = Path(allowed_parent) / "project"
    allowed = fixture(allowed_root)
    blocked = fixture(Path(ordinary_parent) / "data")
    protected = allowed_root / "data" / "knowledge.db"
    protected.parent.mkdir()
    protected.write_text('{"nodes": [], "links": []}')
    protected_result = module.DeveloperCoreEngine(
        project_root=allowed_root, graph_path="data/knowledge.db").analyze()
    checks = {
        "linux_data_graph_allowed": allowed.analyze().graph_loaded,
        "relative_data_denied": not protected_result.graph_loaded and "graph_path_blocked" in {
            risk["type"] for risk in protected_result.risks},
        "ordinary_data_root_denied": not blocked.analyze().graph_loaded,
    }
    print(json.dumps(checks, sort_keys=True))
    assert all(checks.values()), checks
