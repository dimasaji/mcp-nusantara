"""Control-plane checks: no application/network/data execution needed."""
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location("developer_control", Path(__file__).parents[1] / "developer.py")
developer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(developer)


def test_inspection_ignores_runtime_data_and_secrets(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app/main.py").write_text("from app.models import provider\n")
    (tmp_path / "data").mkdir()
    (tmp_path / "data/private.py").write_text("not valid python credential-sentinel")
    (tmp_path / ".env").write_text("KEY=credential-sentinel")
    result = developer.DeveloperControl(tmp_path).inventory()
    assert [v["path"] for v in result["files"]] == ["app/main.py"]
    assert "credential-sentinel" not in json.dumps(result)
    assert not (tmp_path / ".dev").exists()


def test_cleanup_proposes_duplicates_without_deleting(tmp_path):
    (tmp_path / "old.py").write_text("answer = 42\n")
    (tmp_path / "new.py").write_text("answer = 42\n")
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    result = developer.DeveloperControl(tmp_path).cleanup()
    assert result["exact_duplicate_groups"] == [["new.py", "old.py"]]
    assert result["deleted"] == []
    assert all(v["classification"] == "UNKNOWN" for v in result["candidates"])
    assert before == {p.name: p.read_bytes() for p in tmp_path.iterdir()}


def test_output_path_rejects_escape_and_atomic_json_preserves_previous_on_error(tmp_path):
    control = developer.DeveloperControl(tmp_path)
    with pytest.raises(ValueError):
        control.write_json("../escaped.json", {})
    control.write_json(".dev/state.json", {"previous": True})
    with pytest.raises(TypeError):
        control.write_json(".dev/state.json", {"invalid": object()})
    assert control.read_json(".dev/state.json") == {"previous": True}
    assert not list((tmp_path / ".dev").glob("*.tmp"))


def test_missing_internal_imports_are_reported_without_importing(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app/main.py").write_text("import app.nonexistent\nraise RuntimeError('must not execute')\n")
    result = developer.DeveloperControl(tmp_path).architecture()
    assert result["missing_absolute_app_modules"][0]["module"] == "app.nonexistent"
    assert result["active_syntax_errors"] == []


def test_active_syntax_failure_and_historical_failure_are_separated(tmp_path):
    (tmp_path / "app").mkdir()
    (tmp_path / "app/main.py").write_text("def invalid(\n")
    (tmp_path / "old.py").write_text("def invalid(\n")
    result = developer.DeveloperControl(tmp_path).architecture()
    assert result["active_syntax_errors"] == [{"file": "app/main.py", "type": "SyntaxError"}]


def test_cleanup_requires_explicit_dry_run():
    with pytest.raises(SystemExit) as error:
        developer.main(["cleanup"])
    assert error.value.code == 2


def test_status_reads_without_creating_state(tmp_path, monkeypatch):
    control = developer.DeveloperControl(tmp_path)
    monkeypatch.setattr(control, "git", lambda: {"status": "UNAVAILABLE"})
    assert control.status()["project_state"]["status"] == "NOT_CREATED"
    assert not (tmp_path / ".dev").exists()


def test_invalid_existing_state_is_not_replaced(tmp_path):
    control = developer.DeveloperControl(tmp_path)
    (tmp_path / ".dev").mkdir()
    (tmp_path / ".dev/PROJECT_STATE.json").write_text("broken state")
    with pytest.raises(ValueError):
        control.read_json(".dev/PROJECT_STATE.json")
    assert (tmp_path / ".dev/PROJECT_STATE.json").read_text() == "broken state"
