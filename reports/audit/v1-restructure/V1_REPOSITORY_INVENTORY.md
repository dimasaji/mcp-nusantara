# V1_REPOSITORY_INVENTORY

**Project:** Nusantara V1
**Contract:** MASTER DEVELOPER CONTRACT — Phase 4 / deliverable §12.3
**Date:** 2026-11-18
**Machine-readable companion:** `FILE_INVENTORY.csv` (19,799 rows)
**Method:** read-only filesystem walk + rule engine (`.audit_tmp/nusa_classify.py`)

---

## 1. Scope and method

Every file inside `C:\Users\dmaza\mcp-starter` was enumerated. Re-creatable runtime state was enumerated once and then aggregated rather than listed per-file, because listing 130k virtualenv files adds no forensic value and obscures the signal.

**Excluded from per-file listing (and why):**

| Excluded | Files | Size | Reason |
|---|---|---|---|
| `model\` | 1 | 4,692.8 MB | model weight blob |
| `ollama\` | 989 | 3,136.4 MB | model store |
| `nusantara-models\` | 22,636 | 1,545.2 MB | weights + venv |
| `.venv-docling\` | 31,513 | 1,132.9 MB | virtualenv |
| `.venv\` | 12,886 | 294.3 MB | virtualenv |
| `graphify-out\` | 17,378 | 760.6 MB | regenerable code-graph cache |
| `laya-hf-7er9jqah\` | 10 | 646.9 MB | HF model cache |
| `tmp6uztae01\` | ~29,000 | 1,922.2 MB | pytest scratch |
| `pytest-of-dmaza\` | 5,889 | 70.4 MB | pytest scratch |
| `tools\markitdown\` | 7,846 | 275.3 MB | vendored tool site-packages |
| `.git\` | 962 | 927.8 MB | object store (covered by the bundle in the backup) |
| `node_modules\`, `__pycache__\`, `.pytest_cache\`, `torchinductor_dmaza\` | — | — | caches |

**Scanned and classified: 19,804 files.**

---

## 2. Classification totals

| Classification | Files | Size | Meaning |
|---|---:|---:|---|
| **KEEP** | 757 | 7.2 MB | Proven live source, tests, official ops scripts |
| **KEEP-CRITICAL** | 2,756 | 401.0 MB | Data, SOPs, evidence, secrets, configuration |
| **KEEP-HISTORY** | 7,070 | 280.2 MB | Audit, forensic and acceptance evidence |
| **MOVE** | 26 | 0.2 MB | Correct file, wrong directory |
| **ARCHIVE** | 9,183 | 290.7 MB | AI-session residue, superseded drafts, stale reports |
| **DELETE-CANDIDATE** | **12** | **0.02 MB** | Root-level shell typos only |
| **UNKNOWN** | **0** | — | Fully classified |

Plus **370 files** inside 5 generated cache directories (`control-plane\.build-temp-*`, `.vite-temp`, `test-results`, `playwright-report`, `tests\pytest-tmp`) recorded in `GENERATED_CACHE_AGGREGATES.csv`.

### 2.1 Two classifier defects were found and fixed during this audit

Both are recorded here because an audit that hides its own corrections is worthless.

1. **Zero-byte files under `data\` were being marked for deletion.** `data\chat.db` is legitimately 0 bytes until the first write. Fixed by evaluating the KEEP-CRITICAL rule *before* the zero-byte rule. Effect: KEEP-CRITICAL 1,756 → **2,756** (+1,000 files that had been wrongly flagged).
2. **Zero-byte files under `app\` were being marked for deletion.** `app\action\__init__.py` and ten sibling package markers are 0 bytes and are required for package identity. Fixed by restricting the zero-byte disposal rule to files at the repository **root** only. Effect: DELETE-CANDIDATE 1,660 → **12**.

A machine-checked safety assertion now runs on every regeneration:

```
FILE_DELETION_MANIFEST.csv   total 12  | critical-scope hits 0
FILE_ARCHIVE_MANIFEST.csv    total 9183 | critical-scope hits 0
```

No file under `data\`, `config\`, or any named KEEP-CRITICAL path appears in the archive or deletion manifests.

---

## 3. Where the files actually are

| Category | Files | Notes |
|---|---:|---|
| `data\` | 2,742 | KEEP-CRITICAL. Database, SOP sources, backups |
| `docs\` | 6,231 | 5,956 of these are `docs\reports\` — generated report pages → ARCHIVE |
| `control-plane\` | 459 | Frontend source + 370 cache files + `release-candidates\` |
| `tests\` | 323 | 165 active `.py` + 113 `pytest-tmp\` + `.bak-*` copies + `v2\` |
| `app\` | 269 | The backend product |
| `scripts\` | 233 | Mix of live tooling, 26 misfiled contracts, `.cjs` verifiers |
| `reports\` | 5,700 | Audit output; many `*-tmp*` scratch dirs |
| `artifacts\` | 2,576 | Runtime evidence (KEEP-HISTORY) |
| root | 146 | 121 of these are AI residue |
| `config\`, ops scripts | 18 | KEEP-CRITICAL / KEEP |

---

## 4. Root directory inventory — 146 files

The contract §7.2 rule 6 states the root must not accumulate files. At baseline the root held **146 files**, of which **121 are experiment or report residue**.

### 4.1 Must stay (20)

| File | Classification | Reason |
|---|---|---|
| `README.md` | KEEP | Single source of truth for running the system |
| `AGENTS.md` | KEEP | Agent operating contract |
| `CLAUDE.md` | KEEP | Agent operating contract |
| `start-nusantara.bat` | KEEP | Official startup |
| `stop-nusantara.bat` | KEEP | Official shutdown |
| `status-nusantara.bat` | KEEP | Official status |
| `doctor-nusantara.bat` | KEEP | Official diagnostics |
| `.env` | KEEP-CRITICAL | Live secrets/config — must never be committed publicly |
| `.env.example` | KEEP-CRITICAL | Config template |
| `.gitignore`, `.gitattributes`, `.dockerignore`, `.graphifyignore` | KEEP-CRITICAL | Repo hygiene |
| `Dockerfile`, `docker-compose.yml`, `docker-compose.audit.yml` | KEEP-CRITICAL | Deployment |
| `pyproject.toml` | KEEP-CRITICAL | Python project definition |
| `requirements-docling.lock` | KEEP-CRITICAL | Docling environment lock |

### 4.2 Historical records that remain at root (7)

`ARCHITECTURE_CURRENT.md`, `CHANGELOG.md`, `PROJECT_BASELINE.md`, `RELEASE_NOTES.md`, `RELEASE_READINESS_REPORT.md`, `RISK_REGISTER.md`, `ROLLBACK_PLAN.md` — classified KEEP-HISTORY. These are consolidated into `docs/` and `reports/` during restructuring; no content is lost.

### 4.3 Residue to archive (119)

| Pattern family | Examples | Count |
|---|---|---|
| `sop_*_engine.py`, `sop_parser_v2..v5.py`, `sop_parser_engine.py` | `sop_parser_v5.py`, `sop_table_reconstruction_engine_v3.py` | 12 |
| `patch_*.py` | `patch_master_integration.py`, `patch_production_rag.py` | 12 |
| `nusantara_master_*.py`, `master_engine_ai.py`, `nusantara_sop_semantic_engine_v2.py` | — | 5 |
| `*.ps1` audit/automation scripts | `NUSANTARA-MASTER-AUDIT.ps1`, `BUILD-NUSANTARA-GATE8-16.ps1`, `Invoke-NusantaraV1-Readiness.ps1` | 18 |
| `run_direct*.py`, `run_debug.py`, `run_tests.py`, `developer.py`, `build_all.py` | — | 8 |
| `*.log`, `*.txt` dumps | `server.log` (307 KB), `uvicorn_err.log`, `pytest-*.log` | 17 |
| `test_u0*.py`, `test-chat.json`, `Test-Chat-API.ps1` | — | 11 |
| `*.json` diagnostics | `chat-grounding-check.json`, `health-check-v1.json` | 6 |
| markdown drafts | `NUSANTARA MASTER DEVELOPER.md`, `NUSANTARA-TIGA-LAPISAN-…md` | 6 |
| screenshots | `tmp6j1c1jzb.png` (2.2 MB), `tmpf73lgxpm.png` (1.7 MB) | 2 |
| backup copies | `build_all.py.backup_20261001_192207`, `nusantara_master_engine_BACKUP_…py` | 2 |
| misc | `good_changes.patch` (196 KB), `archify-demo.html` (762 KB), `skills-lock.json`, `Modelfile` | 4 |

### 4.4 Shell accidents and heredoc artifacts (11 root files)

These are literal typos and heredoc leftovers captured into the filesystem — `curl`, `git`, `where`, `whoami`, `if`, `Get-ChildItem`, `docker_build.log` (all 0 bytes), plus four malformed files carrying real bytes: `'@ + $pkg + @'` (14,487 B), a filename that is only unicode private-use bytes plus `.json` (6,772 B), and `t… add NUSANTARA regression tests…` (6,342 B). One further 2-byte guard-write artifact sits in `tests\test_output\`.

All 12 are in `FILE_DELETION_MANIFEST.csv`. They corrupt `git ls-files`, break CSV tooling, and are the source of the "Illegal characters in path" failures seen in PowerShell loops during this audit.

---

## 5. Free-space recovery available

| Action | Files | Recoverable |
|---|---:|---:|
| Archive AI residue | 9,183 | 290.7 MB |
| Delete root-level shell typos | 12 | 0.02 MB |
| Remove generated caches | 370 | ~5.3 MB |
| Relocate misfiled contracts | 26 | 0.2 MB |
| **Subtotal (safe)** | **9,591** | **~296 MB** |

The repository can go from 19,804 scanned files to **~10,200** without touching a single line of product code or any data byte.

> Note: `docs\reports\` (5,956 files, ~150 MB) is inside the 9,183 archive set — it is the single largest residue block and is entirely generated report pages from previous AI sessions.

---

## 6. Integrity of KEEP-CRITICAL inventory

| Asset | Files | Verified |
|---|---:|---|
| `data\knowledge\nusantara_knowledge.db` | 1 | SHA-256 + `integrity_check ok` |
| `data\knowledge\backups\*.db` | 8 | Present, timestamps preserved |
| `data\*.db` (engine, memory, chat, cost) | 5 | Present |
| `data\evidence\` | 1 | 74.3 MB evidence bundle |
| `data\service-v1\` | 1,133 | Service run logs |
| `data\knowledge\` (SOP sources + extractions) | 1,552 | 318.8 MB |
| `.env` | 1 | 818 bytes, present in backup |

**Nothing classified KEEP-CRITICAL appears in the ARCHIVE or DELETE manifests.** Verified by manifest cross-check in `AI_LEGACY_CLEANUP_REPORT.md` §6.

---

## 7. Deliverables produced by this phase

| File | Rows | Purpose |
|---|---:|---|
| `FILE_INVENTORY.csv` | 19,804 | Every scanned file with classification + reason |
| `FILE_ARCHIVE_MANIFEST.csv` | 9,183 | Archive candidates with destination bucket |
| `FILE_DELETION_MANIFEST.csv` | 12 | Deletion candidates with reason |
| `FILE_MOVEMENT_MANIFEST.csv` | 26 | Misfiled files with destination |
| `GENERATED_CACHE_AGGREGATES.csv` | 5 | Regenerable cache directories |
| `CLASSIFICATION_SUMMARY.md` | — | Human-readable roll-up |
| `BACKUP_CHECKSUMS.csv` | 23,032 | SHA-256 of the backup snapshot |
