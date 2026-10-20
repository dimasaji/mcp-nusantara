# NUSANTARA V1 fixed ports and Windows autostart

Contract: NCP-V1-AUTOSTART-001. Port source: `config/local-services.json`.
Backend binds `127.0.0.1:8000`; Vite binds `127.0.0.1:5180` with strict port selection.
Vite proxies to Backend 8000. Its target override remains available for isolated proxy tests.
The launcher supplies the canonical runtime HOST/PORT aliases to the existing configuration owner;
it does not edit `.env`, model selection, governance, or Core Engine defaults for other profiles.

## Commands

Run from the repository root in PowerShell. No build is required.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File service/nusantara-service.ps1 status
powershell.exe -NoProfile -ExecutionPolicy Bypass -File service/nusantara-service.ps1 health
powershell.exe -NoProfile -ExecutionPolicy Bypass -File service/nusantara-service.ps1 start
powershell.exe -NoProfile -ExecutionPolicy Bypass -File service/install-nusantara-task.ps1 -PlanOnly
powershell.exe -NoProfile -ExecutionPolicy Bypass -File service/nusantara-service.ps1 install-autostart
powershell.exe -NoProfile -ExecutionPolicy Bypass -File service/nusantara-service.ps1 uninstall-autostart
```

After inspecting status and obtaining permission to stop the verified NUSANTARA processes:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File service/nusantara-service.ps1 stop -AllowStop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File service/nusantara-service.ps1 restart -AllowStop
```

Stop disables recovery through `desired-state`; start enables it again and resumes the installed task.
Uninstall unregisters only the task owned by this repository, disables its monitor cooperatively,
and leaves application processes running. Existing Ollama processes are never stopped.
Compatibility entrypoints `scripts/Start-NusantaraV1.ps1`, `scripts/Stop-NusantaraV1.ps1`, and
the service batch files delegate to the same lifecycle implementation.

## Task and permissions

For the current OpenRouter configuration, run this single installation command in
**PowerShell Administrator**. Enter the intended Windows `dmaza` account in the local
credential prompt; do not paste a password/API key into the command or chat:

```powershell
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -Command "& 'C:\Users\dmaza\mcp-starter\service\install-nusantara-task.ps1' -Credential (Get-Credential)"
```

The installer now checks Administrator rights before attempting boot-task registration.
It does not request or bypass UAC automatically. The task itself uses Limited rights,
and its stored arguments contain only the hidden supervisor invocation. Application
API keys continue to be loaded by the app privately. This command does not reboot or
stop the currently running Backend/Frontend. Installing the task also does not reload
Python modules in an existing Backend; applying a source fix to that process requires
a separately approved restart of the verified Backend.

Task name: `NUSANTARA-V1-Autostart`. Startup trigger with 45-second delay, passwordless S4U
logon as the installing Windows user, LeastPrivilege, noninteractive hidden PowerShell,
IgnoreNew instance policy, three supervisor retries at one-minute intervals.
Registration of a boot/S4U task can require administrator approval, but the task itself does
not run as administrator or SYSTEM. Registration fails safely on an unrelated task with the
same name or another enabled legacy NUSANTARA supervisor. No existing task is overwritten.
Executable paths are resolved at install time into `data/service-v1/runtime.json` so a boot
task does not depend on an interactive terminal PATH. No credentials are stored there.
Microsoft documents S4U as having no network or encrypted-file access. Therefore the
passwordless plan establishes local-service boot only; do not promise OpenRouter inference
under that identity before testing it. See [Microsoft TASK_LOGON_TYPE](https://learn.microsoft.com/en-us/windows/win32/api/taskschd/ne-taskschd-task_logon_type).
For an explicitly approved network-capable batch logon, the installer also accepts a
`PSCredential` supplied locally by the installing human:

```powershell
# Approved elevated installation session; never put a password in this command.
& .\service\install-nusantara-task.ps1 -Credential (Get-Credential)
```

This mode uses Password logon with Limited privileges; Windows Task Scheduler stores the
credential, never repository files or evidence. No credential was requested or collected
during this implementation. Task runtime remains hidden and noninteractive. Switching an
installed task's logon policy requires explicit uninstall/reinstall. The repository must be
readable by the chosen user; app API credentials continue to be loaded privately by Uvicorn
using the existing `.env` mechanism.

## Ollama

Inspection found `Ollama.lnk` and `start-ollama.bat` in Windows Startup, with Ollama already
healthy on 11434. Both existing entries are preserved. `ollamaMode: external` delegates
startup to those existing owners; the monitor checks readiness without launching a second
server. Thus Ollama is expected after user login, not guaranteed before login. Current
application model selection is OpenRouter, so local Ollama readiness is separately reported.
Do not claim pre-login local inference readiness without a separately approved migration
of those existing Ollama startup owners and a real boot test.

## Health and controlled recovery

Monitor interval: 15 seconds. Backend, Frontend, proxy, process ownership and Ollama readiness
are recorded in `data/service-v1/health.json`. Owned launches write separate timestamped stdout
and stderr logs there. Preserve log privacy; automated connection evidence excludes response
text and credential values. Error records store only exception type.

Ownership requires the exact repository virtualenv Python command or the repository Vite
entrypoint, expected executable name, loopback host and configured port. Stop rechecks PID
and process creation time immediately before acting. Port occupancy alone never authorizes
termination. Lifecycle and supervisor mutexes serialize cooperating launches across sessions.
An occupied foreign port, an initializing instance, or a running unhealthy instance produces
HOLD; recovery never kills it. Absent processes/listeners may be started up to three times
per ten-minute window. Cooldown permits another bounded attempt window later.

## Validation and reboot acceptance

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Test-NusantaraV1Connection.ps1
# Optional actual model test: creates two new chat sessions; may use provider credits.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/Test-NusantaraV1Connection.ps1 -IncludeChat
```

Tests do not ingest/delete SOPs or rebuild Core/Frontend. Lifecycle tests use simulated OS
operations in `tests/local-services-contract.ps1`; no real process is terminated to test
recovery. Live crash/stop/restart verification remains HOLD until separately approved.

Reboot acceptance requires explicit user permission. After an actual restart:

1. Record `Win32_OperatingSystem.LastBootUpTime` and task LastRunTime/LastTaskResult.
2. Confirm task runs under the expected user with LeastPrivilege/S4U and no open terminal.
3. Run status and connection checks; verify exactly one listener at 8000 and 5180, matching
   repository process identities, and API proxy health.
4. After login, verify Ollama 11434 and model/RAG checks. Distinguish API reachability from
   successful Chat AI inference and grounded retrieval.
5. Only then mark reboot autostart PASS. Saved task XML or manually running a task is not
   proof that Windows boot execution works.
