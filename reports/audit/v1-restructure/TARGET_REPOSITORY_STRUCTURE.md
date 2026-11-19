# TARGET_REPOSITORY_STRUCTURE

**Project:** Nusantara V1
**Contract:** deliverable §12.18, §7.2 rule 6
**Date:** 2026-11-18
**Status:** PROPOSAL ONLY — nothing described here has been executed

---

## 1. What this document is, and is not

This is the **target** tree. It is a design proposal derived from measured evidence, not a report of what exists.

| | |
|---|---|
| Existing tree | `V1_REPOSITORY_INVENTORY.md`, `FILE_INVENTORY.csv` (19,804 rows) |
| What may be removed | `FILE_ARCHIVE_MANIFEST.csv` (9,183), `FILE_DELETION_MANIFEST.csv` (12) |
| What may be moved | `FILE_MOVEMENT_MANIFEST.csv` (26) |
| What is proposed here | the shape that results if all three are approved |
| Executed? | **No.** Zero files have been moved or deleted |

---

## 2. Current shape — the four problems

Measured, not asserted.

| # | Problem | Measurement |
|---|---|---|
| **P1** | Root directory is 84 % residue | 146 root files → 110 ARCHIVE, 11 DELETE-CANDIDATE |
| **P2** | One directory holds a third of all archive bytes | `docs\reports\` — 5,956 generated pages, ~150 MB |
| **P3** | Two parallel developer-core trees | `app\developer_core\` (29 modules) + `app\devcore\` (9 modules) |
| **P4** | A complete dead engine sits beside the live one | `app\v2\` (4 modules) + `app\api\v2_routes.py`, fan-out 23, never registered |

P3 and P4 are **not** addressed by the removal manifests. They are recorded as deferred because changing them changes code, not file location.

---

## 3. Target root — 25 files, down from 146

```
mcp-starter/
├── README.md
├── AGENTS.md
├── CLAUDE.md
├── CHANGELOG.md
├── PROJECT_BASELINE.md
├── RELEASE_NOTES.md
├── RISK_REGISTER.md
├── ROLLBACK_PLAN.md
├── ARCHITECTURE_CURRENT.md
├── RELEASE_READINESS_REPORT.md
├── start-nusantara.bat
├── stop-nusantara.bat
├── status-nusantara.bat
├── doctor-nusantara.bat
├── Dockerfile
├── docker-compose.yml
├── docker-compose.audit.yml
├── pyproject.toml
├── requirements-docling.lock
├── .env
├── .env.example
├── .gitignore
├── .gitattributes
├── .dockerignore
└── .graphifyignore
```

### 3.1 Why each group is in the root

| Group | Files | Reason it cannot move |
|---|---:|---|
| Source control + agent instructions | 3 | Must be discoverable at the root by convention |
| Release history | 7 | Contract §7.2 requires a readable root-level status |
| Official launchers | 4 | Contract §11 names these four exact paths |
| Container definition | 3 | `docker build .` and `docker compose` resolve at the root |
| Packaging + dependency lock | 2 | `pip install .` resolves `pyproject.toml` at the root |
| Secrets template + ignores | 5 | Tooling reads `.env`, `.gitignore`, `.dockerignore` at the root |

### 3.2 What leaves the root

| Destination | Files | Content |
|---|---:|---|
| `C:\Users\dmaza\NUSANTARA_V1_ARCHIVE\<bucket>\` | 110 | Patch scripts, generated reports, log dumps, screenshots, editor backups |
| Deleted (after approval, hash-verified) | 11 | Shell-accident files (`curl`, `git`, `Get-ChildItem`, PowerShell heredoc fragments) |
| — | 0 | Nothing else moves |

---

## 4. Target directory tree

```
mcp-starter/
├── app/                       247 modules — the runtime
│   ├── api/                   8    HTTP surface (61 routes)
│   ├── knowledge/             43   ingestion, retrieval, grounding, SOP review
│   ├── developer_core/        29   developer-control surface
│   ├── core/                  19   identity, config, error taxonomy
│   ├── models/                14   provider adapters
│   ├── language/              13   normalisation, intent
│   ├── research/              12   web evidence acquisition
│   ├── devcore/               9    second developer-core tree  ← P3
│   ├── hermes/                2    orchestrator
│   ├── security/              6    auth + V1 knowledge boundary
│   ├── approval/              6    runtime authorisation
│   ├── policy/                4    policy engine
│   ├── observability/         4    logging, correlation
│   ├── v2/                    4    dead engine               ← P4
│   └── … 21 more packages
│
├── control-plane/             36 src + 30 test + 12 e2e
│   ├── src/                   React 19 SPA
│   ├── tests/                 vitest
│   ├── e2e/                   Playwright (5 live specs)
│   └── dist/                  build artefact (rebuilt, 446 modules)
│
├── tests/                     160 active modules, 877 test functions
│
├── scripts/                   165 Python tools
│   └── (13 contracts → docs\contracts\, 13 .cjs → tools\verification\)
│
├── tools/
│   └── verification/          13 Node verifiers (relocated)
│
├── data/                      52.75 MB SQLite, 44 approved SOPs, 720 events
│
├── docs/
│   ├── contracts/             18 authoritative contracts
│   ├── architecture/          current architecture + ports
│   ├── audit/                 audit evidence
│   ├── forensic/              this audit's reports
│   ├── stabilization/         remediation history
│   └── reports/               ← P2: 5,956 generated pages → ARCHIVE
│
├── reports/
│   └── audit/v1-restructure/  ← the 27 deliverables + manifests
│
├── nusantara-models/          IndoBERT worker entry point
├── config/                    runtime configuration
└── output/                    generated golden-set artefacts → ARCHIVE
```

---

## 5. The two structural problems this proposal does **not** solve

### 5.1 P3 — two developer-core trees

| Tree | Modules | Imported by a registered router? |
|---|---:|---|
| `app\developer_core\` | 29 | yes — `gate.py`, `sandbox.py`, `worker_process.py` are on live paths |
| `app\devcore\` | 9 | yes — `control_plane_projection.py` is imported by `app\api\control_plane.py` |

Both are live. Neither is dead code. Merging them is a **code change with no equivalence test**, and the contract forbids business-logic changes without approval. It is recorded, not attempted.

Measured coupling: `api → devcore` and `api → developer_core` are separate edge sets in `MODULE_GRAPH_EDGES.csv`. There is no import between the two trees, which is why they have survived as parallel copies.

### 5.2 P4 — `app\v2\` is dead but load-bearing for tests

| Fact | Evidence |
|---|---|
| Never registered | `app\main.py:84-86` mounts three routers; `v2_routes` is not one |
| Fan-out 23 | Second-highest in the graph, behind only `routes` |
| A test asserts it stays unreachable | `tests\test_v2_disabled.py:58` |
| Three test modules import it directly | `test_fullroot_boundaries.py:14-15`, `test_trace_retention.py:5`, `test_v2_disabled.py` |

Deleting it breaks 3 test modules, one of which validates a V1 security boundary. **Precondition before removal: rewrite those three modules to assert the boundary without importing V2.** Precondition not met → deferred.

---

## 6. Effect of applying the proposal

| Metric | Now | After | Change |
|---|---:|---:|---:|
| Root files | 146 | **25** | −121 |
| Scanned files | 19,804 | **~10,213** | −9,591 |
| Archive share of scanned tree | 46.4 % | **0 %** | — |
| Tracked files touched by the removal commit | — | **387** | 8,522 of 9,183 are already gitignored |
| `app\` modules | 247 | 247 | unchanged — no code removed |

> Model weights and virtualenvs (~13.4 GB) are excluded from every number above. They are re-creatable and outside the scope of this restructure.

---

## 7. Ordering — copy, verify, then remove

The proposal is only safe in this order. This is the sequence `AI_LEGACY_CLEANUP_REPORT.md` §9.2 prescribes, and the one `ROLLBACK_AND_RESTORE_GUIDE.md` assumes.

1. **Create** `C:\Users\dmaza\NUSANTARA_V1_ARCHIVE\{historical-audits, superseded-contracts, old-ai-generated, obsolete-experiments, legacy-reports}`.
2. **Copy** (never move) every row of `FILE_ARCHIVE_MANIFEST.csv` into its bucket, preserving relative path.
3. **Verify** file count and per-file size against the manifest. Any mismatch stops the operation.
4. **Confirm** the second copy at `E:\NUSANTARA_BACKUP\02_source\` is intact.
5. **Remove** the archived sources.
6. **Delete** the 12 rows of `FILE_DELETION_MANIFEST.csv`.
7. **Relocate** the 26 rows of `FILE_MOVEMENT_MANIFEST.csv`.
8. **Rebuild** the frontend, re-run the core regression gate, re-run the Docker build.

No step is reversible after step 5 unless step 3 passed. That is why step 3 exists.

---

## 8. What is explicitly out of scope

| Item | Why |
|---|---|
| Splitting `app\api\routes.py` (fan-out 34) | Refactor, not restructure; no equivalence test |
| Merging `devcore` / `developer_core` | Code change, contract §3 |
| Removing `app\v2\` | Blocked by 3 test modules |
| Breaking the 4 import cycles | Changes initialisation order on a live path |
| Removing model weights / venvs | Re-creatable, not part of the tree |
| Changing the approval flow | Business logic, contract §3 |
| Dependency upgrades | `DEPENDENCY_AUDIT.md` §5 — approval required |

---

## 9. Verdict

| Criterion | Result |
|---|---|
| Target root defined | **YES** — 25 files, each justified |
| Target directory tree defined | **YES** — with per-package module counts |
| Every moved file has a destination | **YES** — `FILE_MOVEMENT_MANIFEST.csv` |
| Every archived file has a bucket | **YES** — `FILE_ARCHIVE_MANIFEST.csv` |
| Every deleted file justified | **YES** — `FILE_DELETION_MANIFEST.csv` |
| Structural debt disclosed rather than hidden | **YES** — P3, P4 |
| Executed | **NO** — proposal only, awaiting approval |
