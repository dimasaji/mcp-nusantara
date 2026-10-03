from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path
from typing import Any


class IndoBERTClient:
    """
    Bridge Nusantara Core -> IndoBERT Worker.

    IndoBERT berjalan pada virtual environment terpisah,
    sehingga Nusantara Core tidak membutuhkan torch/transformers.
    """

    def __init__(
        self,
        python_executable: str | None = None,
        worker_path: str | None = None,
    ) -> None:

        project_root = Path(__file__).resolve().parents[3]

        if python_executable is None:
            python_executable = str(
                project_root
                / "nusantara-models"
                / ".venv"
                / "Scripts"
                / "python.exe"
            )

        if worker_path is None:
            worker_path = str(
                project_root
                / "nusantara-models"
                / "indobert_worker.py"
            )

        self.python_executable = python_executable
        self.worker_path = worker_path

        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()

    def start(self) -> None:
        """Menjalankan IndoBERT worker."""

        if self.is_running():
            return

        self._process = subprocess.Popen(
            [
                self.python_executable,
                self.worker_path,
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            encoding="utf-8",
            bufsize=1,
        )

    def is_running(self) -> bool:
        """Memeriksa apakah worker IndoBERT aktif."""

        return (
            self._process is not None
            and self._process.poll() is None
        )

    def encode(self, text: str) -> dict[str, Any]:
        """Mengirim teks ke IndoBERT dan menerima embedding."""

        if not isinstance(text, str):
            text = str(text)

        text = text.strip()

        if not text:
            return {
                "ok": False,
                "engine": "indobert-client",
                "error": "text wajib diisi",
            }

        with self._lock:

            self.start()

            if self._process is None:
                return {
                    "ok": False,
                    "engine": "indobert-client",
                    "error": "Worker IndoBERT gagal dimulai.",
                }

            if (
                self._process.stdin is None
                or self._process.stdout is None
            ):
                return {
                    "ok": False,
                    "engine": "indobert-client",
                    "error": "Pipe IndoBERT tidak tersedia.",
                }

            request = {
                "text": text,
            }

            try:
                self._process.stdin.write(
                    json.dumps(
                        request,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

                self._process.stdin.flush()

                response_line = self._process.stdout.readline()

                if not response_line:
                    self._process = None

                    return {
                        "ok": False,
                        "engine": "indobert-client",
                        "error": (
                            "Worker IndoBERT "
                            "tidak memberikan response."
                        ),
                    }

                return json.loads(response_line)

            except BrokenPipeError:

                self._process = None

                return {
                    "ok": False,
                    "engine": "indobert-client",
                    "error": "Pipe IndoBERT terputus.",
                }

            except json.JSONDecodeError as exc:

                return {
                    "ok": False,
                    "engine": "indobert-client",
                    "error": (
                        f"Response JSON tidak valid: {exc}"
                    ),
                }

            except Exception as exc:

                return {
                    "ok": False,
                    "engine": "indobert-client",
                    "error": str(exc),
                }

    def health(self) -> dict[str, Any]:
        """Status koneksi ke IndoBERT worker."""

        running = self.is_running()

        return {
            "ok": running,
            "engine": "indobert-client",
            "worker_running": running,
            "python": self.python_executable,
            "worker": self.worker_path,
        }

    def stop(self) -> None:
        """Menghentikan worker IndoBERT."""

        process = self._process

        if process is None:
            return

        try:
            if process.stdin:
                process.stdin.close()
        except Exception:
            pass

        try:
            process.terminate()
            process.wait(timeout=5)
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

        self._process = None