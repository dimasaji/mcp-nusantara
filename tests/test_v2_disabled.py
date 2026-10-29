"""Exercise app.main's HTTP composition without starting model/index services."""
import builtins
import importlib.util
import sys
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient


def _module(name, **attributes):
    module = ModuleType(name)
    module.__dict__.update(attributes)
    return module


@pytest.mark.parametrize('read_only', [False, True])
def test_boot_does_not_import_or_expose_v2_and_preserves_v1(monkeypatch, read_only):
    # Only expensive startup services are fixtures. FastAPI, middleware, route
    # installation, and HTTP dispatch below execute the real main.py code.
    router = APIRouter(prefix='/v1')

    @router.post('/chat')
    def v1_chat():
        return {'route': 'v1-fixture'}

    control = APIRouter(prefix='/v1/control-plane')
    preview = APIRouter()

    @preview.post('/dev/inspection-preview')
    def inspection_preview():
        return {'route': 'preview-fixture'}

    @control.get('/status')
    def control_status():
        return {'route': 'control-fixture'}

    configuration = SimpleNamespace(runtime=SimpleNamespace(profile='NORMAL', log_level='INFO'))
    modules = {
        'app.core.config': _module('app.core.config', settings=SimpleNamespace(effective_configuration=configuration)),
        'app.api.routes': _module('app.api.routes', router=router),
        'app.api.control_plane': _module('app.api.control_plane', router=control),
        'app.api.inspection_preview': _module('app.api.inspection_preview', router=preview),
        'app.core.runtime_attestation': _module('app.core.runtime_attestation', install_runtime_attestation=lambda *args, **kwargs: None),
    }
    for name, module in modules.items():
        monkeypatch.setitem(sys.modules, name, module)
    if read_only:
        monkeypatch.setenv('NUSANTARA_CONTROL_PLANE_READ_ONLY', '1')
    else:
        monkeypatch.delenv('NUSANTARA_CONTROL_PLANE_READ_ONLY', raising=False)

    original_import = builtins.__import__

    def deny_v2_import(name, *args, **kwargs):
        if name == 'app.api.v2_routes' or name.startswith('app.v2'):
            raise AssertionError('V2 startup must remain disabled')
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, '__import__', deny_v2_import)
    source = Path(__file__).resolve().parents[1] / 'app/main.py'
    spec = importlib.util.spec_from_file_location('_nusantara_boot_test', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Lifespan is intentionally not entered: model workers/watchers are outside
    # this HTTP composition test, not proof of live runtime readiness.
    client = TestClient(module.app)
    assert client.get('/v1/control-plane/status').status_code == 200
    assert client.post('/v1/chat').status_code == (404 if read_only else 200)
    assert client.post('/v1/dev/inspection-preview').status_code == (404 if read_only else 200)
    for method, path in [('POST', '/v2/chat'), ('POST', '/v2/dev'),
                         ('GET', '/v2/health'), ('POST', '/v2/memory/sessions'),
                         ('POST', '/v2/discovery/candidates')]:
        assert client.request(method, path).status_code == 404
