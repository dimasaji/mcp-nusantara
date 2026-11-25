import shutil
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.developer_core import hermes_acp_connection
from app.knowledge import docling_config
from app.language.semantic.indobert_client import IndoBERTClient


def test_effective_config_degrades_without_tesseract(monkeypatch, tmp_path):
    monkeypatch.delenv('NUSANTARA_TESSERACT_CMD', raising=False)
    monkeypatch.delenv('TESSDATA_PREFIX', raising=False)
    monkeypatch.setattr(shutil, 'which', lambda name: None)
    monkeypatch.setattr(docling_config, 'LEGACY_TESSERACT', tmp_path / 'missing-tesseract.exe')

    config = docling_config.effective_config()

    assert config['ocr'] == 'disabled'
    assert config['tesseract_cmd'] == ''
    assert config['tesseract_sha256'] is None
    assert config['tessdata_path'] == ''
    assert config['language_sha256'] == {}


def test_tesseract_command_prefers_environment(monkeypatch, tmp_path):
    executable = tmp_path / 'configured-tesseract'
    executable.write_text('fixture')
    monkeypatch.setenv('NUSANTARA_TESSERACT_CMD', str(executable))
    monkeypatch.setattr(shutil, 'which', lambda name: '/usr/bin/tesseract')

    assert docling_config.tesseract_command() == str(executable)


def test_tesseract_command_uses_path_without_environment(monkeypatch):
    monkeypatch.delenv('NUSANTARA_TESSERACT_CMD', raising=False)
    monkeypatch.setattr(shutil, 'which', lambda name: '/usr/bin/tesseract')

    assert docling_config.tesseract_command() == '/usr/bin/tesseract'


def test_indobert_default_paths_follow_the_source_layout(monkeypatch):
    monkeypatch.delenv('NUSANTARA_INDOBERT_PYTHON', raising=False)
    monkeypatch.delenv('NUSANTARA_INDOBERT_WORKER', raising=False)
    client = IndoBERTClient()
    root = Path(__file__).resolve().parents[1]
    assert Path(client.worker_path) == root / 'nusantara-models/indobert_worker.py'
    assert Path(client.python_executable).parents[2] == root / 'nusantara-models'


@pytest.mark.parametrize('platform', ['posix', 'nt'])
def test_hermes_command_uses_platform_default(monkeypatch, tmp_path, platform):
    monkeypatch.delenv('NUSANTARA_HERMES_ROOT', raising=False)
    monkeypatch.delenv('LOCALAPPDATA', raising=False)
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(hermes_acp_connection, 'os',
                        SimpleNamespace(name=platform, environ=os.environ))
    if platform == 'nt':
        monkeypatch.setenv('LOCALAPPDATA', str(tmp_path / 'local'))
        root = tmp_path / 'local/hermes/hermes-agent'
        python = root / 'venv/Scripts/python.exe'
    else:
        root = tmp_path / '.local/share/hermes/hermes-agent'
        python = root / 'venv/bin/python'
    python.parent.mkdir(parents=True)
    (root / 'hermes_cli').mkdir()
    python.write_text('')
    (root / 'hermes_cli/main.py').write_text('')

    resolved_root, command = hermes_acp_connection._command()

    assert resolved_root == root.resolve()
    assert command[0] == str(python)
    assert command[-1] == 'acp'


def test_hermes_patch_payload_matches_linux_default():
    root = Path(__file__).resolve().parents[1]
    candidates = [
        root / 'Nusantara-Hermes-ACP-Connection-Patch/payload/app/developer_core/hermes_acp_connection.py',
        root / 'backend/app/developer_core/hermes_acp_connection.py',
    ]
    patch = next((p for p in candidates if p.exists()), None)
    assert patch is not None, f'No Hermes ACP reference found: {candidates}'
    assert '.local/share/hermes/hermes-agent' in patch.read_text(encoding='utf-8')


def test_dockerfile_copies_the_restored_indobert_worker():
    dockerfile = Path(__file__).resolve().parents[1] / 'deploy/docker/Dockerfile'

    text = dockerfile.read_text(encoding='utf-8')

    worker = Path(__file__).resolve().parents[1] / 'nusantara-models/indobert_worker.py'
    assert worker.is_file()
    assert 'COPY nusantara-models/indobert_worker.py /opt/indobert-worker/indobert_worker.py' in text
    assert 'NUSANTARA_INDOBERT_WORKER=/opt/indobert-worker/indobert_worker.py' in text
