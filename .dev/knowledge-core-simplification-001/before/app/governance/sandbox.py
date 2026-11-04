"""Phase 9 - eksekusi proses terbatas: allowlist path absolut, tanpa shell, env minimal, timeout.

BUKAN isolasi tingkat OS (tanpa namespace/seccomp/container). Untuk kode tak tepercaya gunakan
container terpisah; modul ini hanya mencegah LLM menjalankan perintah di luar allowlist.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from dataclasses import dataclass


class SandboxDenied(PermissionError):
    pass


@dataclass
class SandboxResult:
    returncode: int | None
    stdout: str
    stderr: str
    timed_out: bool = False


def run_allowlisted(argv: list[str], *, allow: set[str], timeout_s: float = 5.0,
                    max_output: int = 20000) -> SandboxResult:
    if not argv or not all(isinstance(a, str) for a in argv):
        raise SandboxDenied("argv tidak valid")
    exe = argv[0]
    if not os.path.isabs(exe) or exe not in allow:
        raise SandboxDenied("executable tidak ada di allowlist")
    with tempfile.TemporaryDirectory() as cwd:
        try:
            p = subprocess.run(argv, shell=False, cwd=cwd, capture_output=True, timeout=timeout_s,
                               env={"PATH": "", "LANG": "C.UTF-8"}, stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired as exc:
            return SandboxResult(None, "", (exc.stderr or b"").decode("utf-8", "replace")[:max_output], True)
    return SandboxResult(p.returncode, p.stdout.decode("utf-8", "replace")[:max_output],
                         p.stderr.decode("utf-8", "replace")[:max_output])
