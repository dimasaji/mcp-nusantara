"""Own and bound the entire conversion process tree, including venv launchers."""
import os
import signal
import subprocess


def run_worker(args, *, cwd, env, timeout):
    process = subprocess.Popen(args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, shell=False, start_new_session=os.name != 'nt')
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        if os.name == 'nt':
            # The process is still owned by this Popen handle. Kill its tree
            # before the launcher exits and loses its actual Python child.
            if process.poll() is None:
                stopped = subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                                         capture_output=True, timeout=15, shell=False)
                if stopped.returncode and process.poll() is None:
                    raise RuntimeError('DOCLING_WORKER_TREE_STOP_FAILED')
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate(timeout=15)
        raise
    return subprocess.CompletedProcess(args, process.returncode, stdout, stderr)
