# PC / VPS Acceptance Checklist

- Status: **PARTIAL**
- Purpose: separate evidence proven on this VPS from evidence that can only be accepted on the owner PC, approved CI, or with owner-supplied artifacts.

| Item | Environment | Status | Evidence / requirement |
|---|---|---|---|
| Linux startup, build, auth and control-plane portability | VPS | PASS | `CROSS_PLATFORM_ACCEPTANCE_REPORT.md` |
| 37 Windows-native IPC authorization cases | PC / CI Windows | BLOCKED | `windows_only` skip reason `WINDOWS_NATIVE_IPC_REQUIRED`; Linux results do not substitute. |
| R2 owner acceptance hash | PC / owner artifact | BLOCKED | Restored `FINAL_OWNER_ACCEPTANCE_RECORD.json` SHA `9d370512...` does not match R2-recorded `bac54cbfb...`; projection keeps R2 `NOT_VERIFIED`. |
| R3 Windows temporary evidence path | PC | BLOCKED | `frontend/evidence-sources.json` references `C:/Users/dmaza/AppData/Local/Temp/MDA_R3_...`; absent on VPS; projection keeps R3 `NOT_VERIFIED`. |
| PIAK-03 official SOP acceptance | PC / approved source | BLOCKED | Synthetic KTPEL fixture is not authoritative; official SOP must be supplied by owner. |
| IndoBERT/Docling worker | approved host/artifact | BLOCKED | Required path `backend/nusantara-models/.venv/bin/python` missing. |
| Live knowledge E2E operator credential | owner-supplied credential | BLOCKED | `scripts/run_eval.py:11` requires configured operator credential; none injected. |
| Docker staging at RC `f4f8b7f5` | VPS Docker | PASS | `reports/release-integration-rc/STAGING_ACCEPTANCE_REPORT.md` |
| Docker staging at final WP-03 tree | VPS Docker | NOT_VERIFIED | No fresh build/staging run after WP-03 changes. |
| Ollama production topology | owner decision | BLOCKED | Bridge compose uses `host.docker.internal`; active Ollama binds `127.0.0.1:11434`; staging used host network. |
| PR #19 merge | GitHub | BLOCKED | Owner approval required; PR remains OPEN/MERGEABLE. |
| Production deploy | approved environment | BLOCKED | Owner approval required; not executed. |

## VPS evidence already accepted

- Full regression ID accounting: `new_ids=0`, `fixed_ids=59`, 3 remaining external blockers.
- Secret scan at RC: 0 real credentials in 1698 tracked files.
- Active runtime and DB were untouched throughout WP-03.
- Ruff/mypy pre-existing findings are recorded, not hidden.

Final status: **PARTIAL** — VPS engineering evidence is complete for code review; PC/owner/artifact items remain required before production acceptance.
