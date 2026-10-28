# Existing lifecycle analysis — scripts not executed

PID 32796 is referenced from completed pre-flight evidence only. No restart, stop, live listener re-probe, scheduled-task mutation, Ollama start or application import was performed in this design.

| Existing mechanism | Observed behavior | Suitability for minimum future load |
| --- | --- | --- |
| `service/nusantara-service.ps1` | Start may start Ollama, stop existing matching processes/port owners, write PID/log files; restart invokes stop/start | Too broad to execute unchanged under a one-process load authorization |
| `service/nusantara-supervisor.ps1` | Repeatedly starts Ollama/app if ports disappear and writes supervisor logs | Automatic replacement/retry conflicts with a bounded manual lifecycle; avoid executing it |
| `service/install-nusantara-task.ps1` | Registers/replaces highest-privilege logon task and starts it | Not a minimal load; scheduled-task changes forbidden |
| `scripts/start-nusantara.bat` | Starts Ollama if absent, creates log directory and launches app | Additional provider/console/process effects |
| `scripts/start_windows.ps1` | Copies env if absent, creates venv, installs packages, runs tests and starts reload-enabled Uvicorn | Out of scope; configuration/dependency/reload effects |

The narrowest existing launch primitive is the interpreter/Uvicorn invocation already visible in the service source: `.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1`, working directory repository. It is identified, not executed or represented as a safe ready-to-run command. The normal import behind that command constructs protected DB owners.

## Proposed future operator procedure, conditional on a new authorization

1. Confirm current listener PID/parent/start and actual controlling launcher/supervisor ownership read-only. Historical parent/launcher evidence is not enough. Any automatic restart race must be resolved by the human; do not change scheduled tasks or terminate broad process matches.
2. Approve the diagnostic initialization profile, snapshot handling, permit-injection channel, precise allowed file/console effects and claim boundary. Prove its import closure in isolated tests first. Normal default initialization is not presumed safe.
3. Authorize only the specifically identified app process tree lifecycle and replacement load at 127.0.0.1:8000; no service helper hard-clean, Ollama start, model change, config file edit, install/rebuild/deploy or hotpatch.
4. Start once with reload disabled and no automatic retries. Explicitly approved existing evidence-only process environment may select the diagnostic profile; no setting change is implied by this document. The old process cannot coexist on the same listener and its memory permit must not be carried over.
5. Correlate the new listener PID/start with its attestation. Loading does not itself authorize generation. If startup touches protected state, fails, or creates an unknown listener, STOP; no recovery/retry/revert without authorization.
6. Restore normal runtime only through a separately approved lifecycle action. Default normal startup may touch SQLite, so restoration is not an automatically safe rollback step.

## Status

**LIFECYCLE_NOT_AUTHORIZED / NOT_EXECUTED.** Existing broad scripts cannot be treated as an approved minimum mechanism. A controlled operator procedure can be designed around the existing launch primitive, but the runtime profile, permit channel and supervisory control decisions remain prerequisites.
