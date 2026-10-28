# Live service blocker observation

Observed 2026-10-27 around 09:10–09:13 UTC, using elevated read-only process/port queries.

| Port | Listener | Finding |
|---|---:|---|
| 8000 | PID 3244 | `python.exe`, image `C:\Users\dmaza\AppData\Local\Programs\Python\Python313\python.exe`; started 15:09 local. Its parent PID 9120 is `python.exe` at `C:\Users\dmaza\mcp-starter\.venv\Scripts\python.exe`, same start time. |
| 5180 | PID 6368 | Existing frontend listener. |

Safe command-line traits for PID 3244 and its parent: both contain `uvicorn app.main:app`, loopback host, and port 8000; neither command line contains the repository path or the V1 service's expected `--workers 1` / `--env-file` flags. The service owner matcher therefore does not claim them as a managed backend. These traits do not prove which working directory or configuration the process loaded.

Direct backend and frontend health probes timed out/refused during this observation. The supported service start refuses to replace an existing listener, by design; status remains HOLD. This is consistent with an unresponsive, unmanaged listener on the configured backend port, but process provenance is not proven. No process was terminated, no ACL or lock was changed, and no database approval was submitted.

The process must be identified by the operator before it is stopped or adopted. After the port is safely freed or the process is verified and the service ownership check is corrected, retry the supported start and review/Chat E2E.
