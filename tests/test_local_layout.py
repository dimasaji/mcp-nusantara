"""Deployment paths must resolve in the source checkout and container layout."""
import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize('relative', ['backend/app/main.py', 'app/main.py'])
def test_application_assets_resolve_from_project_root(tmp_path, relative):
    project = tmp_path / 'project'
    main = project / relative
    main.parent.mkdir(parents=True)
    (project / 'config').mkdir()
    (project / 'config/local-services.json').write_text('{}')
    (project / 'frontend/dist').mkdir(parents=True)
    tree = ast.parse((ROOT / 'backend/app/main.py').read_text(encoding='utf-8'))
    start = next(i for i, node in enumerate(tree.body)
                 if isinstance(node, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id in {'PROJECT_ROOT', 'UI_FILE'}
                         for t in node.targets))
    end = next(i for i, node in enumerate(tree.body)
               if isinstance(node, ast.Assign)
               and any(isinstance(t, ast.Name) and t.id == '_LOCAL_SERVICES_FILE'
                       for t in node.targets))
    import os
    namespace = {'Path': Path, 'os': os, '__file__': str(main)}
    exec(compile(ast.Module(body=tree.body[start:end + 1], type_ignores=[]),
                 str(main), 'exec'), namespace)
    assert namespace['CONTROL_PLANE_BUNDLE'] == project / 'frontend/dist'
    assert namespace['_LOCAL_SERVICES_FILE'].is_file()


def test_compose_build_context_contains_backend():
    import yaml
    compose = ROOT / 'deploy/docker/docker-compose.yml'
    service = yaml.safe_load(compose.read_text())['services']['nusantara-api']
    context = (compose.parent / service['build']['context']).resolve()
    assert (context / 'backend/app/main.py').is_file()
    assert (context / service['build']['dockerfile']).is_file()
    assert (compose.parent / service['env_file'][0]['path']).resolve() == ROOT / '.env'


def test_windows_launcher_targets_existing_frontend_and_backend():
    launcher = (ROOT / 'start-nusantara.bat').read_text()
    assert 'control-plane' not in launcher
    assert '--app-dir backend' in launcher
    assert '%~dp0frontend' in launcher
    assert '%~dp0.venv' in launcher


def test_bundled_ui_is_served_without_a_development_server():
    import os
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, '-B', '-c', '''
import os, tempfile
from pathlib import Path
temporary = tempfile.TemporaryDirectory()
bundle = Path(temporary.name)
(bundle / 'assets').mkdir()
(bundle / 'assets/test.js').write_text('window.test = true;')
(bundle / 'index.html').write_text('<html><script src="/assets/test.js"></script></html>')
os.environ['NUSANTARA_FRONTEND_DIST'] = str(bundle)
import app.main as main
from fastapi.testclient import TestClient
main._READ_ONLY_EVIDENCE = False
client = TestClient(main.app, follow_redirects=False)
response = client.get('/')
assert response.status_code == 200, response.status_code
assert 'text/html' in response.headers['content-type']
assert '/assets/' in response.text
assert client.get('/assets/test.js').status_code == 200
client.close()
temporary.cleanup()
'''], cwd=ROOT, capture_output=True, text=True, timeout=20,
        env={**os.environ, 'PYTHONPATH': str(ROOT / 'backend'),
             'NUSANTARA_CONTROL_PLANE_READ_ONLY': '1',
             'NUSANTARA_SERVE_BUNDLE': '1'},
    )
    assert result.returncode == 0, result.stdout + result.stderr
