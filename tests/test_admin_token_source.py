import pytest
from fastapi import HTTPException
from app.security import auth


def test_dotenv_operator_token_when_launcher_does_not_load_environment(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('NUSANTARA_ADMIN_TOKEN', raising=False)
    (tmp_path / '.env').write_text('NUSANTARA_ADMIN_TOKEN=fixture-dotenv\n')
    auth.require_admin('fixture-dotenv')
    for token in (None, '', 'wrong'):
        with pytest.raises(HTTPException) as error:
            auth.require_admin(token)
        assert error.value.status_code == 403


def test_environment_overrides_dotenv_including_explicit_empty(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / '.env').write_text('NUSANTARA_ADMIN_TOKEN=fixture-dotenv\n')
    monkeypatch.setenv('NUSANTARA_ADMIN_TOKEN', 'fixture-env')
    auth.require_admin('fixture-env')
    with pytest.raises(HTTPException):
        auth.require_admin('fixture-dotenv')
    monkeypatch.setenv('NUSANTARA_ADMIN_TOKEN', '')
    with pytest.raises(HTTPException):
        auth.require_admin('fixture-dotenv')


def test_no_configured_token_fails_closed(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv('NUSANTARA_ADMIN_TOKEN', raising=False)
    with pytest.raises(HTTPException):
        auth.require_admin('anything')
