from __future__ import annotations

import json
import os
import subprocess
import threading
import queue
import math
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
        response_timeout_s: float = 60.0,
    ) -> None:

        project_root = Path(__file__).resolve().parents[3]

        if python_executable is None:
            python_executable = os.getenv(
                "NUSANTARA_INDOBERT_PYTHON",
                str(project_root / "nusantara-models" / ".venv"
                    / ("Scripts" if os.name == "nt" else "bin")
                    / ("python.exe" if os.name == "nt" else "python")),
            )

        if worker_path is None:
            worker_path = os.getenv(
                "NUSANTARA_INDOBERT_WORKER",
                str(project_root / "nusantara-models" / "indobert_worker.py"),
            )

        self.python_executable = python_executable
        self.worker_path = worker_path
        if not math.isfinite(response_timeout_s) or response_timeout_s <= 0:
            raise ValueError("response timeout must be finite and positive")
        self.response_timeout_s = response_timeout_s

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
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
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
                process = self._process
                responses = queue.Queue(maxsize=1)
                def exchange():
                    try:
                        process.stdin.write(json.dumps(request, ensure_ascii=False) + "\n")
                        process.stdin.flush()
                        responses.put(process.stdout.readline())
                    except Exception as exc:
                        responses.put(exc)
                threading.Thread(target=exchange, daemon=True).start()
                try:
                    response_line = responses.get(timeout=self.response_timeout_s)
                except queue.Empty:
                    self.stop()
                    return {"ok": False, "engine": "indobert-client", "error": "Worker response timeout"}
                if isinstance(response_line, Exception):
                    raise response_line

                if not response_line:
                    self.stop()

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
                self.stop()

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
            process.terminate()
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=2)
        finally:
            for pipe in (process.stdin, process.stdout):
                if pipe:
                    pipe.close()

        self._process = None
