"""Run real PowerShell lifecycle logic with isolated OS/process fixtures."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


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
