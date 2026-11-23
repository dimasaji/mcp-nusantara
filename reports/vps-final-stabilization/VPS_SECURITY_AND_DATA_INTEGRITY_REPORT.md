# VPS Security and Data Integrity Report — Nusantara V1

- Commit SHA: `d2cfc60a0d88c93ce561f40c01d67e5f53910770`
- Branch: `codex/vps-final-stabilization-20261123`
- Evidence: `/data/workspace/nus-v1-vps-final-20261123/evidence/`
- Collected: 2026-11-23T22:20:14Z–22:20:55Z

## Gate E verdict

**PASS** — admin boundaries reject missing/invalid tokens, no credential material was introduced or printed, active DB mtime/hash/quick_check are unchanged from forensic baseline, backup/restore tests pass, and isolated runtime has been stopped without touching active services.

## Secret and disclosure scan

- Path-only scans were used; no matched line values were printed.
- `e_secret_diff` broad scan matched only two historical final-consolidation reports because they describe the scan terms themselves.
- `e_secret_reports` broad scan matched only `VPS_FORENSIC_BASELINE.md` lines stating that no secrets were disclosed.
- `e_secret_diff_precise` still listed `reports/final-consolidation/POST_MERGE_VERIFICATION.md` and `INDEPENDENT_VERIFICATION_REPORT.md`; inspection confirms these are self-referential lines such as `Secret scan | 0 match untuk ... api_key ... console.log`, not credentials.
- `e_secret_reports_precise` matched 0 files in `reports/vps-final-stabilization/`.
- `console.log` was not introduced in V1 source changes; no `sk-...` token, `api_key=` assignment, or `NUSANTARA_ADMIN_TOKEN=` literal appeared in changed source.
- No production `.env`, personal data, DB dump, or real admin token was copied. The only token used was synthetic `local-verification-only` in the isolated runtime.

## Authorization probes

| Probe | Endpoint | Result |
|---|---|---|
| `e_auth_ingest_no_token` | `POST /v1/documents/ingest` | HTTP 403 `{"detail":"admin token diperlukan"}` |
| `e_auth_ingest_invalid_token` | `POST /v1/documents/ingest` with invalid token | HTTP 403 same detail |
| `e_auth_cost_no_token` | `GET /v1/control-plane/cost-summary` | HTTP 403 same detail |
| `e_auth_cost_valid_token` | `GET /v1/control-plane/cost-summary` with synthetic token | HTTP 200 `status=UNAVAILABLE`, `source=CostLedger` |
| `d2_synthetic_ingest` | Valid token, valid payload | HTTP 400 from missing IndoBERT worker, i.e. authorization passed before the environment failure |

The `UNAVAILABLE` cost summary is the known V1 chat-process boundary: the ledger is not attached to this process. It is not an authentication or authorization defect.

## Targeted security/audit tests

`e_security_tests`: `4 failed, 65 passed, 12 warnings in 0.96s`.

The 4 failures are the same known V2-route residual IDs already recorded in Phase D:
- `test_privileged_api_denies_before_access[False-None-/v2/dev-payload0]`
- `test_privileged_api_denies_before_access[True-None-/v2/dev-payload0]`
- `test_privileged_api_denies_before_access[True-invalid-/v2/dev-payload0]`
- `test_authorized_developer_lists_workspace`

All admin-token source, audit writer, approval boundary, backup/restore, SQLite WAL backup, and V1 SOP boundary tests in that run passed. No new security regression vs baseline.

## Data integrity

| Item | Active DB | Isolated DB |
|---|---|---|
| Path | `/data/workspace/nus-v1-postmerge-ec76a9ed/runtime/verify-final/staging-db/verify.db` | `/data/workspace/nus-v1-vps-final-20261123/runtime/isolated/data/knowledge.db` |
| Size | `94208` | `94208` |
| mtime | `2026-11-23 17:53:05.461642521 +0000` | `2026-11-23 22:19:20.743718824 +0000` |
| SHA-256 | `32eb169f79dfe021e5dd4fd007e43e816369dcd80685c7b8dc4375df7b9cf122` | `aefd3fa222c445bd685a1811044ddc6fb5cf85a34a88f647c9f99d1254fcc72f` |
| `PRAGMA quick_check` | `ok` | `ok` |
| Tables | `9` | `9` |

Active DB mtime still matches forensic evidence (`a_filesystem_scan.out`, line 96), so no active DB write occurred. All pragmas were opened with `mode=ro`; no migration, deletion, or overwrite was performed.

## Isolation teardown

- `e_stop_isolated` stopped only isolated PIDs `15715`, `15740`, `15721`, `15714`, `15720`.
- `e_wait_stopped` confirmed ports `18211` and `15284` were free.
- `e_ports_after_stop` shows only active `18201` (PID `7680`), `15274` (PID `7740`), Ollama `11434`, and unrelated system listeners.
- `e_active_after_stop` returned active `/health` HTTP 200 with the same build ID `sha256:e3900af27d8d15759f44228547024aed14b110bb7e1e9c0b4754f87478480331`.

## Worktree hygiene

- The temporary `frontend/node_modules` symlink was removed (`e_cleanup_symlink`).
- `e_status_clean` is empty for tracked/unignored paths; stable source remains at `d2cfc60a`.
- New reports are ignored by `.gitignore:76 reports/*`; they will be added explicitly with `git add -f` in the final commit, with no `.gitignore` change.

## Command evidence index

`e_secret_diff.*`, `e_secret_reports.*`, `e_secret_diff_precise.*`, `e_secret_reports_precise.*`, `e_auth_ingest_no_token.*`, `e_auth_ingest_invalid_token.*`, `e_auth_cost_no_token.*`, `e_auth_cost_valid_token.*`, `e_db_stat.*`, `e_db_hash.*`, `e_db_pragmas.*`, `e_security_tests.*`, `e_git_diff_check_scoped.*`, `e_git_status_scoped.*`, `e_stop_isolated.*`, `e_wait_stopped.*`, `e_ports_after_stop.*`, `e_active_after_stop.*`, `e_cleanup_symlink.*`, `e_status_clean.*`. Full commands, exit codes, and timestamps: `evidence/commands.tsv`.
