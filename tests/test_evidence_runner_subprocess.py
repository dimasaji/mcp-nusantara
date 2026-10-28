"""Exercise guard-specific tests in the runner that owns their __main__ API."""
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def test_evidence_guards_in_their_own_runner(tmp_path):
    root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, '-B', str(root / 'tests/run_evidence_tests_isolated.py'),
         str(tmp_path), '--guards-only'], cwd=root, capture_output=True, text=True,
        timeout=60, env={**os.environ, 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1'},
    )
    assert result.returncode == 0, result.stdout + result.stderr
    suites = ET.parse(tmp_path / 'python-results.xml').getroot()
    cases = suites.findall('.//testcase')
    assert len(cases) == 9
    assert all(case.find('failure') is None and case.find('error') is None
               and case.find('skipped') is None for case in cases)
