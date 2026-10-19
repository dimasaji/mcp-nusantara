"""Run real PowerShell lifecycle logic with isolated OS/process fixtures."""
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_fixed_port_manifest():
    config = json.loads((ROOT / 'config/local-services.json').read_text())
    assert (config['host'], config['backendPort'], config['frontendPort']) == ('127.0.0.1', 8000, 5180)
    assert config['ollamaMode'] == 'external'


@pytest.mark.skipif(sys.platform != 'win32', reason='Windows lifecycle contract')
def test_lifecycle_ownership_and_recovery():
    result = subprocess.run(
        ['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', str(ROOT / 'tests/local-services-contract.ps1')],
        cwd=ROOT, capture_output=True, text=True, timeout=45,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'ALL LIFECYCLE CONTRACT TESTS PASS' in result.stdout
