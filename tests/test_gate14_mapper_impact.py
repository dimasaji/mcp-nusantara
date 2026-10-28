from pathlib import Path

from app.developer_core.mapper import RuntimeGraphMapper
from app.developer_core.impact import RuntimeImpactAnalyzer


def test_mapper_loads_existing_graph():
    mapper = RuntimeGraphMapper()

    result = mapper.map_runtime(
        gates={
            "language": {"status": "active"},
            "reasoning": {"status": "grounded"},
        },
        orchestration={
            "stages": [
                "language",
                "problem",
                "reasoning",
            ]
        },
    )

    assert "mapper" in result
    assert "mappings" in result
    assert result["mapper"]["mode"] == "read-only"


def test_mapper_has_engine_mapping():
    mapper = RuntimeGraphMapper()

    result = mapper.map_runtime()

    assert "language" in result["mappings"]
    assert "reasoning" in result["mappings"]
    assert "developer_core" in result["mappings"]


def test_impact_analyzer():
    analyzer = RuntimeImpactAnalyzer()

    result = analyzer.analyze([])

    assert "impact" in result
    assert result["impact"]["mode"] == "read-only"


def test_mapping_to_impact():
    mapper = RuntimeGraphMapper()

    mapping = mapper.map_runtime()

    analyzer = RuntimeImpactAnalyzer()

    result = analyzer.analyze_mapping(mapping)

    assert "dependency" in result
    assert "dependents" in result
    assert "risk" in result


def test_existing_graph_not_required_for_import():
    path = Path("graphify-out/graph.json")

    mapper = RuntimeGraphMapper(path)

    result = mapper.map_runtime()

    assert "graph" in result
