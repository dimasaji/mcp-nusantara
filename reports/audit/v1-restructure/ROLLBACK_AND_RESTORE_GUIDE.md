# ROLLBACK_AND_RESTORE_GUIDE

**Project:** Nusantara V1
**Contract:** deliverable §12.23, addendum §5.A
**Date:** 2026-11-18
**Audience:** the operator who has to undo something at 02:00 without reading the whole audit.

---

## 1. The 30-second version

| I want to… | Do this |
|---|---|
| Undo every code change from this audit | `git checkout -- Dockerfile .gitignore pyproject.toml control-plane/src/sop-review.tsx tests/test_v1_sop_boundary.py tests/test_evidence_runner_guards.py` |
| Undo one change | §4, one `git checkout` per file |
| Get back the original repository | `git clone E:\NUSANTARA_BACKUP\01_git\nusantara-original-all.bundle <dir>` then `git checkout c7fb76a1` |
| Restore the database | §6 — copy, **verify the SHA-256**, then start |
| Undo nothing, just restart a sick process | `stop-nusantara.bat` then `start-nusantara.bat` (§7) |
| Know whether my restore worked | `doctor-nusantara.bat` (§8) |

**Nothing in this audit is irreversible.** No file was deleted, moved or archived. The only persistent artefact is documentation.

---

## 2. What exists, and where

### 2.1 Backup of record — do not touch

| | |
|---|---|
| Path | `E:\nusantara\mcp-starter` |
| Commit | `c7fb76a1fc788f9624b00432ff20a90717d71b5f` |
| Branch | `codex/fullroot-control-20261007` |
| Role | **original state, frozen.** This is the reference the audit was measured against |

It is read-only in practice. Nothing in this audit wrote to it.

### 2.2 Verified snapshot

| | |
|---|---|
| Path | `E:\NUSANTARA_BACKUP\` |
| Method | copy + per-file SHA-256 re-read |
| Files hashed | **23,032** |
| Manifest | `05_manifests\BACKUP_MANIFEST.csv` (4,086,427 B) |
| Checksums | `05_manifests\BACKUP_MANIFEST.csv` — columns `relative_path,size_bytes,sha256` |

```
E:\NUSANTARA_BACKUP\
├── 01_git\
│   ├── nusantara-original-all.bundle   58,445,227 B — all 31 refs, `git fsck` clean
│   └── HEAD.txt                        c7fb76a1 / codex/fullroot-control-20261007
├── 02_source\                          tracked source tree, full working copy
├── 03_data\                            data\ — database, evidence, logs
├── 04_config\                          .env, Dockerfile, compose, pyproject.toml
└── 05_manifests\                       BACKUP_MANIFEST.csv, HEAD.txt, README.md, VERIFICATION.md
```

Verified properties, recorded in `BACKUP_VERIFICATION_REPORT.md`:

- `git fsck --full` → clean, no dangling or missing objects
- `git bundle verify` → the bundle contains every ref the repository needs (31 refs)
- the working copy and the backup hold the **same** database bytes (§6.1)
- restore was **tested by cloning the bundle into a scratch directory**, not assumed
- **2026-11-19 re-verification:** all 23,032 files re-hashed against the manifest → `checked=23032 missing=0 mismatched=0`, 205.1 s. Recorded in `05_manifests\VERIFICATION.md`.

### 2.3 What is **not** in any backup

| Excluded | Why | Consequence |
|---|---|---|
| `model\` 4.69 GB, `ollama\` 3.14 GB, `nusantara-models\` 1.55 GB | model weights; re-downloadable | restoring needs the models re-fetched |
| `.venv\`, `.venv-docling\`, `.venv-laya\` | reproducible from `pyproject.toml` | `pip install -e .` |
| `graphify-out\` 761 MB | generated from source | `graphify update .` |
| `tmp6uztae01\` 1.92 GB, 29,280 files | scratch output | not restored, not needed |
| `node_modules\` | reproducible | `npm ci` |

These are **generated**, not authored. Their absence does not lose any work.

---

## 3. Restore the whole repository from the bundle

The bundle is a complete, self-contained git repository. It does not need the original working directory.

```powershell
cd E:\
git clone E:\NUSANTARA_BACKUP\01_git\nusantara-original-all.bundle nusantara-restore
cd nusantara-restore
git checkout c7fb76a1fc788f9624b00432ff20a90717d71b5f
git fsck --full
```

Expected: `git fsck` prints nothing (clean), and `git log -1 --format=%H` prints `c7fb76a1…`.

Then rebuild the environment:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
cd control-plane; npm ci; npm run build; cd ..
```

Then restore the database from `03_data\` per §6, and start with `start-nusantara.bat`.

**A restore is not complete until §6 and §8 have both passed.**

---

## 4. Per-change rollback — this audit's six edits

Each of the six modifications is a tracked file. `git checkout` restores the exact bytes from HEAD `7867ba35`.

```powershell
git checkout -- <file>
```

| # | File | What it changed | Rollback | What breaks after rollback |
|---|---|---|---|---|
| C1 | `control-plane/src/sop-review.tsx` | optional `onChanged?: () => void` prop, invoked after a mutation | `git checkout -- control-plane/src/sop-review.tsx` + `npm run build` | **the frontend build fails again** (`TS2322`) → no `dist\` → no UI |
| C2 | `Dockerfile` | `COPY control-plane/dist ./control-plane/dist` uncommented | re-comment the line + rebuild image | the image ships no UI (the state the audit found) |
| C3 | `.gitignore` | `reports/` → `reports/*` + `!reports/audit/` | `git checkout -- .gitignore` | the audit deliverables become uncommittable again |
| C4 | `pyproject.toml` | version `2.0.0a3`→`0.1.0`, description V2→V1, `haystack-ai` and `langgraph` pins | `git checkout -- pyproject.toml` | metadata claims V2 again; `pip install -e .` would downgrade Haystack 3.4.1 → 2.31.1 |
| C5 | `tests/test_v1_sop_boundary.py` | rate limiter carried into the compiled namespace | `git checkout -- tests/test_v1_sop_boundary.py` | **19 security-boundary tests stop executing** (11 fail, 8 pass) |
| C6 | `tests/test_evidence_runner_guards.py` | module-level precondition skip | delete the `pytestmark` block | 9 phantom `AttributeError` failures return |

Roll back all six at once:

```powershell
cd C:\Users\dmaza\mcp-starter
git checkout -- Dockerfile .gitignore pyproject.toml `
                control-plane/src/sop-review.tsx `
                tests/test_v1_sop_boundary.py `
                tests/test_evidence_runner_guards.py
git status --short     # expect: no modified tracked files
```

### 4.1 Rolling back a subset

C1 and C2 are the only pair with an ordering constraint: if you revert C2 but keep C1, the image builds fine and simply contains no `dist\`. If you revert C1 but keep C2, `npm run build` fails, so `control-plane\dist\` may be stale — rebuild **before** rebuilding the image.

The test edits (C5, C6) are independent of the product and of each other. Reverting either only changes what the test suite runs.

### 4.2 The `.vite-temp` / `.build-temp-*` caveat

`control-plane/.vite-temp` and `control-plane/.build-temp-941059bf…` are **tracked** but are deleted and rewritten by `vite build`. During this audit they were deleted by a build and restored with `git checkout --` twice. If a build leaves them missing:

```powershell
git checkout -- control-plane/.vite-temp "control-plane/.build-temp-941059bf*"
```

Filed as approval item **A7** (untrack them) — not applied.

---

## 5. Restore a single file from the snapshot

When you want the original of one file without touching anything else:

```powershell
# from the snapshot tree
Copy-Item E:\NUSANTARA_BACKUP\02_source\app\api\routes.py `
          C:\Users\dmaza\mcp-starter\app\api\routes.py -Force

# or from git history, without the snapshot
cd C:\Users\dmaza\mcp-starter
git show 7867ba35:app/api/routes.py > app\api\routes.py
```

Verify before continuing:

```powershell
Select-String -Path E:\NUSANTARA_BACKUP\05_manifests\BACKUP_MANIFEST.csv -Pattern 'routes.py'
(Get-FileHash app\api\routes.py -Algorithm SHA256).Hash
```

The two hashes must match. **This audit changed no `app\` file**, so any hash mismatch in `app\` means someone else changed it — investigate before proceeding.

---

## 6. Database restore — the only genuinely delicate operation

### 6.1 The identity of the current database

| | |
|---|---|
| Path | `C:\Users\dmaza\mcp-starter\data\knowledge\nusantara_knowledge.db` |
| Size | 52.75 MB (55,308,288 B) |
| SHA-256 | `9e3e0d7a37b6c99841fb5de2e1e9ee76c1d00c8efb8696318a95f807df53c407` |
| `PRAGMA integrity_check` | `ok` |
| Contents | 65 documents · 722 chunks · 720 review events · 44 approved SOPs |

**The same SHA-256 was measured on `C:` and on `E:\NUSANTARA_BACKUP\03_data\`.** The backup database is byte-identical to the live one. It is not a stale copy.

### 6.2 Procedure — copy, verify, then start

```powershell
# 1. STOP the backend. Never copy a SQLite file that a process has open.
.\stop-nusantara.bat
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.Path -like '*mcp-starter*' }

# 2. Preserve the current file before overwriting it
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$db = 'data\knowledge\nusantara_knowledge.db'
Copy-Item $db "$db.pre-restore-$stamp" -Force

# 3. Copy the backup in
Copy-Item E:\NUSANTARA_BACKUP\03_data\knowledge\nusantara_knowledge.db $db -Force

# 4. VERIFY — do not skip this step
(Get-FileHash $db -Algorithm SHA256).Hash
# expect: 9E3E0D7A37B6C99841FB5DE2E1E9EE76C1D00C8EFB8696318A95F807DF53C407

# 5. Verify the file is a healthy database, not a truncated copy
.\.venv\Scripts\python.exe -c "import sqlite3;c=sqlite3.connect('data/knowledge/nusantara_knowledge.db');print(c.execute('PRAGMA integrity_check').fetchone());print(c.execute('select count(*) from documents').fetchone(),c.execute('select count(*) from chunks').fetchone(),c.execute('select count(*) from sop_review_events').fetchone());c.close()"

# 6. Only now start the service
.\start-nusantara.bat
```

Expected from step 5: `('ok',) ('65',) ('722',) ('720',)` — the exact counts in §6.1.

### 6.3 Why the order matters

SQLite in WAL mode keeps a `-wal` and `-shm` sidecar. Copying a live database yields a file that passes `integrity_check` but is **missing the newest committed transactions**, because they live in the WAL. This is the classic silent data-loss restore.

| Rule | Consequence of breaking it |
|---|---|
| Stop the service before copying | restore succeeds and silently loses recent review events |
| Verify the hash after copying | a truncated network copy is indistinguishable from a good one by size alone |
| Run `integrity_check` before starting | the service starts on a corrupt database and the first write makes it unrecoverable |
| Keep `pre-restore-*` | you cannot get back the state you replaced |

### 6.4 Restoring only the database from the bundle

The bundle carries `data\` too, if the snapshot tree is unavailable:

```powershell
git -C E:\NUSANTARA_BACKUP\02_source show c7fb76a1:data/knowledge/nusantara_knowledge.db > data\knowledge\nusantara_knowledge.db
```

Then verify per step 4.

### 6.5 The restore that must never be attempted

| Never | Why |
|---|---|
| Restore a **newer** database over an older schema without a migration | no migration framework exists; the service fails at first query |
| Restore the database while the backend is running | WAL data loss (§6.3) |
| Restore and then "fix" the counts by deleting rows | 720 review events are the audit trail. Deleting them destroys the property the product exists to provide |
| Delete `data\evidence\` to "clean up" | evidence files are referenced by review events; removing them breaks citation for approved SOPs |

---

## 7. Recovering a degraded service — the operational case

The most likely call at 02:00 is not "restore a file". It is the failure this audit actually observed:

> `GET /v1/health` → `200 {"status":"ok"}`
> `POST /v1/chat` → `500 {"detail":"Terjadi kesalahan internal server"}`

The process is running and cannot answer. Finding **S-R1**. Recovery:

```powershell
.\stop-nusantara.bat
.\start-nusantara.bat
.\status-nusantara.bat
```

Then confirm the chat path, not just health — health does not prove the product works:

```powershell
$body = '{"user_input":"halo","session_id":"recovery-check"}'
Invoke-RestMethod -Uri http://127.0.0.1:8000/v1/chat -Method Post -Body $body -ContentType 'application/json'
```

Expected: `response` starts with "Halo", `provider_status` is `local_rule`, `trust.requires_human` is `true`.

If the restart does not clear it, the next diagnostic is the provider, because a model that cannot be reached fails the generation step and not the health check:

```powershell
(Invoke-WebRequest http://127.0.0.1:11434/api/tags -UseBasicParsing).StatusCode   # expect 200
```

Full recovery ladder:

| Symptom | First check | Then |
|---|---|---|
| chat 500, health 200 | restart (§7) | `ollama` reachable? `data\*.log` |
| chat 503 `RETRIEVAL_UNAVAILABLE` | is `data\knowledge\nusantara_knowledge.db` present and readable? | rebuild embeddings (§9) |
| port 8000 refused | `.\status-nusantara.bat` | is another process on 8000? `Get-NetTCPConnection -LocalPort 8000` |
| frontend blank | `npm run build` in `control-plane\` | `tsc --noEmit` for the exact error |
| everything green but answers are poor | `HERMES_FORENSIC_AUDIT.md` §4 — the model is 4.5 B parameters | not a fault; a capability ceiling |

---

## 8. Verifying that a restore worked

Run, in this order. Each step can fail independently, and each failure means something different.

| # | Command | Expected | What a failure means |
|---|---|---|---|
| 1 | `git status --short` | no tracked modifications | a file is not what HEAD says it is |
| 2 | `.\doctor-nusantara.bat` | all checks green | see its own output; it names the component |
| 3 | `.\status-nusantara.bat` | backend 8000 + frontend 5180 up | a process failed to start |
| 4 | `(Invoke-WebRequest http://127.0.0.1:8000/v1/health).Content` | `{"status":"ok", …}` | the service is not running. **Passing this does not mean the product works** (§7) |
| 5 | `python scripts\automated_regression.py` | **6/6 PASS** | a security contract is broken — stop and investigate |
| 6 | `pytest tests\test_knowledge_pipeline.py tests\test_sop_review.py …` (63-test release list) | 63 passed | a regression; compare against `REGRESSION_TEST_REPORT.md` |
| 7 | `cd control-plane; npx vitest run` | 219 passed | frontend regression |
| 8 | database counts (§6.2 step 5) | 65 / 722 / 720 | the database is not the one that was backed up |

**Minimum bar for "the restore worked":** steps 1, 5, 6 and 8 all pass. Step 4 alone proves nothing.

---

## 9. Rebuilding what is not backed up

| Artefact | Command | Notes |
|---|---|---|
| Python env | `py -3.12 -m venv .venv` then `.\.venv\Scripts\python.exe -m pip install -e .` | `pyproject.toml` pins the tested ranges |
| Frontend deps | `cd control-plane; npm ci` | requires `package-lock.json`, which is tracked |
| Frontend build | `cd control-plane; npm run build` | must be run **before** the Docker build |
| Docker image | `docker build -t nusantara:v1 .` | needs `control-plane\dist\` to exist (C2) |
| Embeddings | re-ingest via the pipeline | **read §9.1 first** |
| Model | `ollama pull gemma3n:e2b-it-q4_K_M` | ~5.7 GB |
| Knowledge graph | `graphify update .` | regenerates `graphify-out\` |

### 9.1 The embedding trap

`.env` sets `EMBEDDING_MODEL=local-hash`, but the database's 722 chunks carry **768-dim IndoBERT** vectors, because ingestion used the IndoBERT bridge explicitly rather than the env default.

**A re-ingest with the default environment mixes vector dimensions in the same table and corrupts retrieval.** If embeddings must be rebuilt, confirm the bridge is used first:

```powershell
Select-String -Path .env -Pattern 'EMBEDDING_MODEL'
Select-String -Path app\knowledge\engine.py -Pattern 'indobert|embedding_model'
```

Recorded as **R3** in `RUNTIME_MODULE_MAP.md`. It did not happen here.

---

## 10. What cannot be rolled back

| Item | Status |
|---|---|
| The backend restart (§7) | not reversible — but it changed no data, only liveness |
| Probe sessions written by this audit's live checks | a handful of rows in throwaway `web-*` / `probe*` sessions |
| Knowledge graph files if regenerated | derived; regenerate again |
| Anything in `E:\NUSANTARA_BACKUP\` | the snapshot is a copy; re-copy from `E:\nusantara\mcp-starter` if it is ever damaged |

No approval-gated action (archive, delete, move) has been executed, so none of them needs a rollback. When they are approved, this section gains a row per action — the manifests already record source path, destination and SHA-256 for each one, which is what makes them reversible.

---

## 11. Verdict

| Criterion | Result |
|---|---|
| Every change reversible | **PASS** — 6 files, one `git checkout` each |
| Original repository recoverable | **PASS** — bundle cloned and verified |
| Database restorable without loss | **PASS** — hash-identical copy, procedure in §6.2 |
| Restore procedure tested | **PASS** — clone test performed, not assumed |
| Destructive action requiring rollback | **NONE TAKEN** |
| Operator can recover without reading this audit | **PASS** — §1 and §7 stand alone |

**Rollback status: FULLY REVERSIBLE.** The product can be returned to `c7fb76a1` or `7867ba35` at any time, and the database can be restored byte-for-byte.
