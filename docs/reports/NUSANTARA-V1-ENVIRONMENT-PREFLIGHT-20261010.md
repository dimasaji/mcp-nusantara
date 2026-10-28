# V1-ENVIRONMENT-PREFLIGHT — 2026-10-10

## Decision

`PARTIAL`: offline Python work is executable through the repository `.venv`, with a relocation warning; Docker candidate access is `BLOCKED`.

## Read-only checks

- Repository root: `C:\Users\dmaza\mcp-starter`; `git rev-parse --show-toplevel` succeeded.
- Git worktree: already contains many modified and untracked user/repository files, including `app/main.py`, Docker files, application source, tests, prior reports, and data. This continuation preserved those changes. Git status also reported access denied for several historical temp folders; no cleanup or restore was attempted.
- `.venv\pyvenv.cfg` points `home` and `executable` to `C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe`; that base path is not resolvable. Its `command` records creation from `E:\AI\mcp-starter\.venv`, consistent with a relocated virtual environment.
- `.venv\Scripts\python.exe -B -c "import sys,pytest,fastapi; ..."` exited 0 and reported Python 3.13.15, pytest 9.1.1, FastAPI 0.141.1. Each invocation prints `Failed to find real location of C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe`. Offline tests still execute. `py -0p` reported `No installed Pythons found!`.
- Codex-bundled Python 3.12.14 is available but lacks pytest and FastAPI. The IndoBERT worker venv imports `torch`, `transformers`, and `tokenizers`; its own `pyvenv.cfg` has the same missing base interpreter warning. No model was loaded and no network download was attempted.
- Docker pipe `\\.\pipe\dockerDesktopLinuxEngine` exists, but `docker ps --format '{{.Names}}'` exited 1: `permission denied while trying to connect to the Docker API at npipe:////./pipe/dockerDesktopLinuxEngine`. No container names/state could be read in this session. Docker Desktop/backend processes and `com.docker.service` were not observable through the read-only process/service query.
- C: had 142,772,051,968 bytes free. Evidence run directories were writable as demonstrated by creation of pytest XML results and package snapshot.

## Environment action needed

Restore the original Python 3.13 base installation or provide an authorized stable Python environment to remove the venv relocation warning. Provide an already-authorized session that can read the Docker engine pipe for candidate inspection; no escalation or permission bypass was attempted. Do not alter or restart candidate resources as part of that access fix.
