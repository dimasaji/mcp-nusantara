import builtins
import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient


def _app(monkeypatch):
    monkeypatch.setenv('NUSANTARA_CONTROL_PLANE_READ_ONLY', '1')
    original_import = builtins.__import__

    def deny_v2_import(name, *args, **kwargs):
        if name == 'app.api.v2_routes' or name.startswith('app.v2'):
            raise AssertionError('V2 startup must remain disabled')
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', deny_v2_import)
    source = Path(__file__).resolve().parents[1] / 'backend/app/main.py'
    spec = importlib.util.spec_from_file_location('_nusantara_readyz_test', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.app


def test_readyz_alias_matches_canonical_readiness(monkeypatch):
    client = TestClient(_app(monkeypatch))
    health = client.get('/health')
    canonical = client.get('/v1/health/ready')
    alias = client.get('/readyz')
    assert health.status_code == 200
    assert canonical.status_code == 200
    assert alias.status_code == 200
    assert set(alias.json()) == set(canonical.json())
    assert alias.json()['status'] == canonical.json()['status']
