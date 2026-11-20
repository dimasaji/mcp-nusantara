# A1-A9 EXECUTION REPORT

**Project:** Nusantara V1
**Contract:** deliverable A-12.22, addendum A-7 (restructuring execution)
**Date:** 2026-11-20
**Branch:** `codex/fullroot-control-20261007`
**Audit commit:** `fbb6f0fb` (audit + 6 gated fixes)
**Approved actions:** A1, A2, A3, A4, A7, A8, A9
**Deferred by owner:** A5 (`app\v2` removal), A6 (Grounding Guard negative-claim fix)

**Rule applied to every action:** measure, record, verify, do not claim a result that
was not observed. Every number below is copied from a log in this `evidence\`
directory or from a command whose output is reproduced here.

---

## 1. Result in one table

| # | Action | Scope approved | Executed | Measured result | Evidence |
|---|---|---|---|---|---|
| A1 | Archive legacy artifacts | 9,183 paths | **YES** | 9,170 archived+verified+removed, 177 restored as carve-outs, 5 absent, 8 excluded, 0 failed | `A1_archive_log.csv`, `A1_restore_carveout.csv` |
| A2 | Delete root shell accidents | 12 files | **YES** (11 deleted, 1 kept) | 11 deleted, `Modelfile` kept | `A2_deletion_log.csv` |
| A3 | Relocate contracts + verifiers | 26 files | **YES** | 26 moved (13 contracts, 13 verifiers), 0 failed | `A3_movement_log.csv` |
| A4 | `npm audit fix` + rebuild | `package-lock.json` | **YES** | 5 vulns -> 3 (high+moderate gone), 219/219 tests, `tsc` 0, build 0 | `A4_npm_audit_before.json`, `A4_npm_audit_after.json` |
| A7 | Untrack build caches | ~490 files | **YES** | 281 tracked cache files untracked, still on disk | `git status` (289 staged deletions = 281 A7 + 8 A2) |
| A8 | Pin base image + Python lock | `Dockerfile`, lock | **YES** | digest-pinned build, image healthy, `/v1/health` 200, `dist\` present | `A8_image_verification.txt`, `.audit_tmp\a8_build.log` |
| A9 | Add `/metrics` + readiness | `app\main.py` | **YES** | gate 66/66 (two passes), live regression 6/6, readiness `ready` | `A9_gate_pass1_no_model.txt`, `A9_gate_pass2_model_loaded.txt`, `A9_live_regression.txt`, `A9_live_health_ready_metrics.txt` |

---

## 2. A1 - archive of legacy AI artifacts

**Destination:** `C:\Users\dmaza\NUSANTARA_V1_ARCHIVE\` (290 MB, outside the repository)
**Method:** copy -> verify SHA-256 -> remove (`archive_exec.ps1`). No file was removed
before its copy was hash-verified at the destination.

Measured, from `A1_archive_log.csv` (9,183 rows):

| Outcome | Count |
|---|---:|
| `archived+verified+removed` | 9,170 |
| `absent` (already gone, nothing to do) | 5 |
| `EXCLUDED-test-coverage-kept` | 8 |
| Failed | 0 |

**Carve-out 1 - `tests\v2\` (8 files).** These tests exercise the still-present
`app\v2`. Archiving them would have removed test coverage before A5 was approved,
so they were kept in place and are marked `EXCLUDED-test-coverage-kept`.

**Carve-out 2 - `docs\reports\` fixtures (48 files, discovered after A1).** The
control-plane suite (`control-plane\tests\engineering-console.test.tsx`) reads real
files under `docs\reports\...`. Those files were untracked local evidence and A1
archived them, which broke 3 tests. The 48 files referenced by
`control-plane\src\engineering-evidence.ts` were restored from the archive:

- `docs\reports\human-console-recovery-20261009T200537\` (1 referenced file)
- `docs\reports\openrouter-workflow-20261009T184538\` (23)
- `docs\reports\v1-functional-closure-20261009-101736\` (1)
- `docs\reports\v1-remaining-20261009T182840\` (11)
- `docs\reports\weip-completion-20261009T104250Z\` (12)

Only the referenced files were restored, not the parent directories (2,933 files).
After restoration the suite returned to 219/219.

**Finding R-10 (new, disclosed):** the frontend suite depends on untracked
`docs\reports\` evidence. On a clean clone those 3 tests fail. The correct fix is to
replace the dependency with committed synthetic fixtures, which is a test change and
therefore requires approval. It was not done here.

**Carve-out 3 - agent tooling (129 files, classification correction).** The manifest
had classified all of `.agents\` (115 files) and `.claude\` (14 files) as
`obsolete-experiments`. That classification was wrong: `.agents\skills\` is the live
skill installation. Removing `.agents\skills\graphify\SKILL.md` and every other
`SKILL.md` broke the skill catalog referenced by `AGENTS.md` and
`docs\NUSANTARA_DEVELOPMENT_WORKFLOW.md` ("read each installed skill when its stage
applies"). All 129 files were restored from the archive; the skill catalog came back
immediately after restoration.

The two other manifest buckets were spot-checked and are genuinely obsolete:
`old-ai-generated` is 5,956 files under `docs\` plus one-off patch scripts,
`historical-audits` is 1,802 files under `reports\` and `perbaikanbukti\`, and the
`obsolete-experiments` remainder is backup copies (`*.bak`, `*.backup`), a 697-file
vendored `mcp-nusantara-upstream` tree, and duplicate launchers under `service\`.

Effective outcome of A1: 9,170 archived, 177 restored, **8,993 files removed from the
working tree**, 0 unconditional deletions without an archive copy.

**Rollback:** copy back from `C:\Users\dmaza\NUSANTARA_V1_ARCHIVE\` (mirror of the
original relative paths). Log rows contain both the source path and the archive path;
`A1_restore_carveout.csv` lists the 177 files that were put back, with their SHA-256.

---

## 3. A2 - deletion of root shell accidents

11 files deleted, all hash-verified against the backup copy before deletion
(`A2_deletion_log.csv`). They are captured by `git` for the 8 tracked ones and by
`E:\NUSANTARA_BACKUP\02_source\` for all 11.

**Deliberate deviation:** `Modelfile` (78 B) was on the deletion manifest but was
**kept**. It is a real project asset that points at
`model\Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf`; deleting it would have removed the
only in-repo description of the intended production model. Recorded as `KEPT` in the
log.

**Rollback:** `git checkout -- <path>` for tracked files, or copy from
`E:\NUSANTARA_BACKUP\02_source\`.

---

## 4. A3 - relocation of contracts and verifiers

26 `git mv` operations, 0 failures (`A3_movement_log.csv`):

- 13 contracts: `scripts\*.md` -> `docs\contracts\`
- 13 verifiers: `scripts\*.cjs` -> `tools\verification\`

Three references were repaired so the tools keep working:

| File | Change |
|---|---|
| `scripts\verify_chat_p0_canary.py:51` | path -> `tools\verification\` |
| `scripts\verify_control_plane_four.py:40` | path -> `tools\verification\` |
| `docs\operational\SOP-INGESTION-V1.md:13` | path -> `tools\verification\` |

Verified with `git grep` that no remaining reference points at the old locations.

**Rollback:** reverse the `git mv` pairs listed in the log.

---

## 5. A4 - frontend dependency audit and rebuild

**Before:** 5 vulnerabilities - 2 critical, 1 high, 2 moderate
(`A4_npm_audit_before.json`).
**After `npm audit fix`:** 3 vulnerabilities - 2 critical, 1 moderate; high and the
seroval moderate are gone (`A4_npm_audit_after.json`).

| Package | Before | After |
|---|---|---|
| `zod` (direct, production) | flagged high | **4.6.7 - fixed** |
| `seroval` (transitive) | flagged moderate | **1.8.2 - fixed** |
| `vitest` / `tinypool` / `@vitest/mocker` (dev only) | 2 critical + 1 moderate | **unchanged** |

The remaining 3 are test-runner packages. They require `vitest@5.1.1`, a **major**
upgrade (`npm audit fix --force`), which is outside the approved scope of `npm audit
fix` and changes the test toolchain. They are development dependencies only and are
not present in the runtime image. Documented as residual risk with the exact
remediation command; **not executed without approval**.

**Re-verification after the dependency change:**

| Check | Result |
|---|---|
| `npm test` (vitest) | **28 files / 219 tests passed** |
| `npx tsc --noEmit` | **exit 0** |
| `npm run build` | **exit 0**, 451 modules |
| `dist\` | 5 files, 965,759 B, rebuilt 2026-11-20 09:34 |

**Rollback:** restore `.audit_tmp\package-lock.before-A4.json` as
`control-plane\package-lock.json`, then `npm ci` and `npm run build`.

---

## 6. A7 - untracking generated build caches

281 tracked cache files were removed from the index while staying on disk:
`control-plane\.vite-temp\` (156) and
`control-plane\.build-temp-941059bf39fc4a9496f5b341a53ea75a\` (125).

`.gitignore` gained:

```
control-plane/.vite-temp/
control-plane/.build-temp-*/
```

They are regenerated by the Vite build, so nothing is lost. The build was re-run
afterwards (A4) and completed normally.

**Rollback:** `git add -f` the paths and revert the `.gitignore` lines.

---

## 7. A8 - reproducible container build

| Item | Before | After |
|---|---|---|
| Base image | `python:3.12-slim` (floating) | `python:3.12-slim@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b` |
| `haystack-ai` in image | `2.31.1` | `3.4.1` (matches the tested environment) |
| Python dependencies | unpinned install | `requirements-lock.txt`, 98 pins from `.venv` |
| Build context | ~5.4 GB (included the 4.7 GB model and the DB) | pinned excludes in `.dockerignore` |

Verification from `A8_image_verification.txt`:

```
image_id=sha256:9ad2dd41a3a143cb637d499d9bb5680caba94ddf4a58c082d7952a653a732149
haystack=3.4.1
dist_files=5
health=healthy
health_http=200
health_body={"status":"ok","service":"nusantara-core","version":"0.1.0",...}
```

The base image digest in `docker image inspect python:3.12-slim` is exactly
`sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b`, so the
`FROM` line is pinned to the image that was actually used. The `dist\` inside the
image contains the post-A4 bundle (`index-hiTn-gez.js`, `graph-ChG93DMa.js`).

The test container was removed after verification. Docker Desktop was then stopped
and `wsl --shutdown` run to return the machine to its normal memory profile.

**Rollback:** `git checkout -- Dockerfile .dockerignore` and rebuild; delete
`requirements-lock.txt`.

---

## 8. A9 - `/metrics` and a readiness probe that actually reads the database

Added to `app\main.py`:

- `GET /v1/metrics` - version, uptime, request counter, per-route p50/p95 latency,
  plus stage timings recorded by the V1 stage runner.
- `GET /v1/health/ready` - database and provider probes.

The readiness probe went through three iterations, each one failing honestly:

1. `store.connection()` - `{"status":"unverified","reason":"store has no connection()"}`.
2. `rag.get_store()` - `{"status":"unverified","reason":"no store with list_documents()"}`;
   `RAG` has no `get_store()`.
3. `_knowledge.list_documents()` with `len()` - `{"status":"error","error":"TypeError"}`;
   the method returns a `DocumentListResponse`, not a list.
4. **Final:** `_knowledge.list_documents()` then `getattr(listing, "total", None)`.
   This is the same public accessor the routes use, and it issues a real read-only
   query without starting the embedding worker.

**Live result (2026-11-20 09:39):**

```
ready_body={"status":"ready","components":{"knowledge_database":{"status":"ok","documents":65},"provider":{"status":"ok","http_status":200}}}

metrics_body={"status":"ok","metrics":{"version":"0.1.0","uptime_seconds":570.9,
  "requests_total":51,"latency":{"http_request":{"count":50,"p50_ms":2.32,"p95_ms":121.35},
  "v1.stage.run":{"count":3,"p50_ms":8.37,"p95_ms":18.35},...}}}
```

`documents: 65` is the real corpus size, so the probe distinguishes a live database
from an empty or broken one.

### 8.1 Gate run - two passes, documented as a capacity workaround

The machine has 7.9 GB of RAM. The Ollama model is 6.9 GB and the IndoBERT worker is
about 0.7 GB; they cannot be resident at the same time. The suite was therefore run
in two passes:

| Pass | Condition | Modules | Result | Evidence |
|---|---|---|---|---|
| 1 | model unloaded | 9 | **53 passed** in 24.83 s | `A9_gate_pass1_no_model.txt` |
| 2 | model loaded | `test_langchain_hardening.py` | **13 passed** in 26.49 s | `A9_gate_pass2_model_loaded.txt` |

Combined: **66 passed, 0 failed.** This is a scheduling workaround, not a code
change; no test was skipped, edited, or marked xfail.

### 8.2 Live security regression

`scripts\automated_regression.py` against the running stack: **6/6 PASS**
(`A9_live_regression.txt`):

```
PASS: security_search_no_token
PASS: security_admin_no_token
PASS: security_chat_no_token_no_evidence
PASS: empty_input_rejected
PASS: pipeline_status_accessible
PASS: session_isolation
```

**Rollback:** remove the two route functions from `app\main.py`.

---

## 9. State of the repository after execution

| Item | Value |
|---|---|
| Branch | `codex/fullroot-control-20261007` |
| Audit commit | `fbb6f0fb` |
| Staged | 588 entries - 539 deletions (281 A7 caches + 8 A2 + 250 A1 files), 26 renames (A3), 13 additions, 10 modifications |
| Unstaged | 29 - 1 pre-existing `nusantara` gitlink marker, 28 untracked (mostly `docs\reports\`, `.audit_tmp\`, `.venv-laya\`) |
| Release gate | core 66/66, frontend 219/219, `tsc` 0, build 0, live security 6/6, container healthy |
| `/v1/health/ready` | `ready`, 65 documents, provider 200 |
| `/v1/metrics` | live, latency histogram populated |

**Not committed deliberately:** `docs\reports\` (untracked local evidence, see R-10),
`.audit_tmp\` (scratch), and the archive itself (outside the repository).

---

## 10. Residual risks carried forward

| ID | Risk | Severity | Mitigation |
|---|---|---|---|
| A5 | `app\v2` present with V2 routes unregistered; 3 `test_phase3_metrics_integration.py` tests still 404 | Medium | deferred by owner; removal requires rewriting those tests first |
| A6 | Grounding Guard accepts negative claims (12 tests) | High | deferred by owner; not weakened, not hidden |
| A4-R | `vitest`/`tinypool` critical advisories in dev tooling | Low-Medium | dev-only, not in image; `npm i -D vitest@5.1.1` pending approval |
| R-10 | frontend tests depend on untracked `docs\reports\` fixtures | Medium | 48 files restored locally; synthetic replacements pending approval |
| R-11 | archive manifest misclassified active agent tooling (`.agents\`, `.claude\`) as obsolete | High | **caught and corrected** - 129 files restored, skill catalog verified; manifest classification should be reviewed before any future archive run |
| RAM | model and embedding worker cannot coexist | Medium | two-pass gate; documented, not hidden |
| Model | `gemma3n:e2b` (4.5 B) caps answer quality; 8 B GGUF exists but is not registered in Ollama | Medium | operational choice, outside this contract |
| Pentest | not performed | High | explicitly deferred by owner |
| OCR | ground truth for 42 SOPs not measured | Medium | outside this contract |

---

## 11. Sign-off

| Criterion | Result |
|---|---|
| Every approved action executed | **YES** - A1, A2, A3, A4, A7, A8, A9 |
| Every action measured | **YES** - a log per action |
| Irreversible deletion without an archive copy | **NONE** |
| Test weakened to obtain a green result | **NONE** |
| Metric invented or rounded up | **NONE** |
| Deviations disclosed | **YES** - `Modelfile`, `tests\v2`, `docs\reports`, two-pass gate, vitest major deferred |
| Deferred actions named | **YES** - A5, A6 |
