from app.core.runtime_identity import BUILD_ID, source_build_id


def test_identity_changes_with_source_and_excludes_environment(tmp_path):
    app = tmp_path / "app"
    app.mkdir()
    source = app / "main.py"
    source.write_text("value = 1\n", encoding="utf-8")
    before = source_build_id(tmp_path)
    (tmp_path / ".env").write_text("private environment value", encoding="utf-8")
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "secret.json").write_text("private runtime data", encoding="utf-8")
    assert source_build_id(tmp_path) == before
    source.write_text("value = 2\n", encoding="utf-8")
    assert source_build_id(tmp_path) != before
    assert before.startswith("sha256:") and len(before) == 71
    assert str(tmp_path) not in before


def test_health_reports_same_loaded_build():
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        public = client.get("/health").json()
        v1 = client.get("/v1/health").json()
    assert public["build_id"] == v1["build_id"] == BUILD_ID
    assert "version" in v1 and v1["status"] == "ok"
