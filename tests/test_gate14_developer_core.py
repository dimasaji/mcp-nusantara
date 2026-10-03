from pathlib import Path

from app.developer_core.engine import DeveloperCoreEngine
from app.developer_core.graph_bridge import GraphifyBridge


def test_gate14_engine_loads():
    engine = DeveloperCoreEngine()

    result = engine.self_analyze()

    assert "developer_core" in result
    assert result["developer_core"]["version"].startswith("14.")


def test_gate14_engine_inventory():
    engine = DeveloperCoreEngine()

    result = engine.self_analyze()

    names = {
        item["name"]
        for item in result["engines"]
    }

    assert "Reasoning Engine" in names
    assert "Policy Engine" in names
    assert "Memory Engine" in names
    assert "Action Engine" in names
    assert "Orchestration Engine" in names


def test_gate14_graph_bridge():
    bridge = GraphifyBridge()

    result = bridge.inspect()

    assert "graph_bridge" in result
    assert result["graph_bridge"]["mode"] == "read-only"


def test_gate14_existing_graphify():
    path = Path("graphify-out/graph.json")

    if not path.exists():
        return

    bridge = GraphifyBridge(path)

    result = bridge.inspect()

    assert result["graphify"]["loaded"] is True
    assert result["graphify"]["nodes"] > 0


def test_gate14_runtime_gate_mapping():
    engine = DeveloperCoreEngine()

    runtime = {
        "8": {"status": "grounded"},
        "9": {"status": "allow"},
        "10": {"status": "active"},
        "11": {"status": "ready"},
        "12": {"status": "preserved"},
        "13": {"status": "completed"},
        "14": {"status": "active"},
    }

    result = engine.self_analyze(
        runtime_gates=runtime
    )

    assert result["gates"]["8"]["status"] == "grounded"
    assert result["gates"]["9"]["status"] == "allow"
    assert result["gates"]["13"]["status"] == "completed"
