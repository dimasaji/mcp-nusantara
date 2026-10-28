"""Exercise repository collection policy through the pytest CLI."""

import os
import subprocess
import sys
from pathlib import Path


def test_collection_keeps_active_tests_and_ignores_backup_modules(tmp_path):
    repository = Path(__file__).resolve().parents[1]
    (tmp_path / "pyproject.toml").write_bytes((repository / "pyproject.toml").read_bytes())
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_backup_restore.py").write_text(
        "def test_active_restore():\n    pass\n", encoding="utf-8"
    )
    (tests / "test_route.bak-20261021.py").write_text(
        "raise AssertionError('backup must never be imported')\n", encoding="utf-8"
    )
    environment = {key: value for key, value in os.environ.items() if key != "PYTEST_ADDOPTS"}
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "pytest_asyncio.plugin", "--collect-only", "-q"],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "test_backup_restore.py" in result.stdout
    assert "test_active_restore" in result.stdout
    assert "1 test collected" in result.stdout
