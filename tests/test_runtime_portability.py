import shutil
from pathlib import Path

from app.developer_core import hermes_acp_connection
from app.knowledge import docling_config


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


def test_tesseract_command_prefers_environment(monkeypatch):
    monkeypatch.setenv('NUSANTARA_TESSERACT_CMD', '/fixture/tesseract')
    monkeypatch.setattr(shutil, 'which', lambda name: '/usr/bin/tesseract')

    assert docling_config.tesseract_command() == '/fixture/tesseract'


def test_tesseract_command_uses_path_without_environment(monkeypatch):
    monkeypatch.delenv('NUSANTARA_TESSERACT_CMD', raising=False)
    monkeypatch.setattr(shutil, 'which', lambda name: '/usr/bin/tesseract')

    assert docling_config.tesseract_command() == '/usr/bin/tesseract'


def test_hermes_command_uses_linux_default(monkeypatch, tmp_path):
    monkeypatch.delenv('NUSANTARA_HERMES_ROOT', raising=False)
    monkeypatch.delenv('LOCALAPPDATA', raising=False)
    monkeypatch.setattr(Path, 'home', classmethod(lambda cls: tmp_path))
    root = tmp_path / '.local/share/hermes/hermes-agent'
    (root / 'venv/bin').mkdir(parents=True)
    (root / 'hermes_cli').mkdir()
    (root / 'venv/bin/python').write_text('')
    (root / 'hermes_cli/main.py').write_text('')

    resolved_root, command = hermes_acp_connection._command()

    assert resolved_root == root.resolve()
    assert command[0] == str(root / 'venv/bin/python')
    assert 'C:' not in ' '.join(command)


def test_hermes_patch_payload_matches_linux_default():
    patch = (Path(__file__).resolve().parents[1]
             / 'Nusantara-Hermes-ACP-Connection-Patch/payload/app/developer_core/hermes_acp_connection.py')

    assert '.local/share/hermes/hermes-agent' in patch.read_text(encoding='utf-8')


def test_dockerfile_does_not_copy_missing_indobert_worker():
    dockerfile = Path(__file__).resolve().parents[1] / 'Dockerfile'

    text = dockerfile.read_text(encoding='utf-8')

    assert 'COPY nusantara-models/indobert_worker.py' not in text
    assert 'NUSANTARA_INDOBERT_WORKER=/opt/indobert-worker/indobert_worker.py' in text
