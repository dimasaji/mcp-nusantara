import ctypes
import json
import os
import subprocess
import sys

import pytest

from app.knowledge.worker_process import run_worker


@pytest.mark.skipif(os.name != 'nt', reason='Windows venv process tree regression')
def test_timeout_stops_the_python_child_tree(tmp_path):
    pid_file = tmp_path / 'child.json'
    program = "import subprocess,sys,time,json; from pathlib import Path; p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(30)']); Path(sys.argv[1]).write_text(json.dumps(p.pid)); time.sleep(30)"
    with pytest.raises(subprocess.TimeoutExpired):
        run_worker([sys.executable, '-c', program, str(pid_file)], cwd=tmp_path, env=os.environ.copy(), timeout=2)
    child_pid = json.loads(pid_file.read_text())
    kernel = ctypes.windll.kernel32
    handle = kernel.OpenProcess(0x00100000, False, child_pid)
    if handle:
        try:
            assert kernel.WaitForSingleObject(handle, 3000) == 0
        finally:
            kernel.CloseHandle(handle)
