"""Run real PowerShell lifecycle logic with isolated OS/process fixtures."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows restart wrapper')
def test_restart_wrapper_delegates_and_preserves_failure(tmp_path):
    scripts = tmp_path / 'scripts'
    service = tmp_path / 'service'
    scripts.mkdir()
    service.mkdir()
    shutil.copyfile(ROOT / 'scripts/Restart-NusantaraV1.ps1', scripts / 'Restart-NusantaraV1.ps1')
    (service / 'nusantara-service.ps1').write_text('''param($Action,[switch]$AllowStop,[switch]$NoOllama)
@{action=$Action;allowStop=[bool]$AllowStop;noOllama=[bool]$NoOllama} | ConvertTo-Json | Set-Content "$PSScriptRoot/probe.json"
exit 7
''')
    powershell = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    result = subprocess.run([str(powershell), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-File', str(scripts / 'Restart-NusantaraV1.ps1'), '-AllowStop', '-NoOllama'], cwd=tmp_path,
        capture_output=True, text=True, timeout=15)
    assert result.returncode == 7, result.stdout + result.stderr
    assert json.loads((service / 'probe.json').read_text(encoding='utf-8-sig')) == {
        'action':'restart', 'allowStop':True, 'noOllama':True}


def test_fixed_port_manifest():
    config = json.loads((ROOT / 'config/local-services.json').read_text())
    assert (config['host'], config['backendPort'], config['frontendPort']) == ('127.0.0.1', 8000, 5180)
    assert config['ollamaMode'] == 'external'


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows lifecycle contract')
def test_lifecycle_ownership_and_recovery(tmp_path):
    for relative in ('tests/local-services-contract.ps1', 'service/local-services.ps1',
                     'service/task-registration.ps1', 'config/local-services.json'):
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    powershell = Path(os.environ.get('SystemRoot', r'C:\Windows')) / 'System32/WindowsPowerShell/v1.0/powershell.exe'
    result = subprocess.run(
        [str(powershell), '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(tmp_path / 'tests/local-services-contract.ps1')],
        cwd=tmp_path, capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'ALL LIFECYCLE CONTRACT TESTS PASS' in result.stdout
