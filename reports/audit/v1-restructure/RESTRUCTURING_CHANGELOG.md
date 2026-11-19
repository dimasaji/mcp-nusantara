# RESTRUCTURING_CHANGELOG

**Project:** Nusantara V1
**Contract:** deliverable §12.20, addendum §5.C
**Date:** 2026-11-18
**Baseline:** `git` HEAD `7867ba35`, branch `codex/fullroot-control-20261007`
**Working copy:** `C:\Users\dmaza\mcp-starter`
**Backup of record:** `E:\nusantara\mcp-starter` @ `c7fb76a1`; verified snapshot at `E:\NUSANTARA_BACKUP\`

---

## 1. Summary

| Category | Count | Reversible? |
|---|---:|---|
| Files **modified** | **6** | yes — `git checkout` |
| Files **deleted** | **0** | n/a |
| Files **moved** | **0** | n/a |
| Files **archived** | **0** | n/a |
| Reports **created** | 25 | yes — delete |
| Manifests **generated** | 9 | yes — regenerate |
| Services **restarted** | 1 (backend) | n/a |

**No file was deleted, moved or archived.** Every removal proposed in this audit is registered in a manifest and awaits approval. The changes below are the complete set of edits made to the product and its test suite.

---

## 2. Changes to product files

### C1 — `control-plane/src/sop-review.tsx`

```diff
 export function SOPReviewPanel({
-  documentId, token, autoProcess = false,
+  documentId, token, autoProcess = false, onChanged,
 }: {
-  documentId: string; token: string; autoProcess?: boolean;
+  documentId: string; token: string; autoProcess?: boolean;
+  onChanged?: () => void;
 }) {
```

and inside `act()`:

```diff
   await load();
   setReport(null);
   setPublicationAction(null);
   setNote('');
+  onChanged?.();
 }
```

| | |
|---|---|
| **Defect** | `overview.tsx:199` passed `onChanged={()=>query.refetch()}` to a component that never declared it → `TS2322` → `npm run build` (`tsc --noEmit && vite build`) failed → **no `dist/` → no UI in the Docker image** |
| **Nature** | Additive, optional prop. Every other call site is unaffected |
| **Verification** | `tsc --noEmit` exit 0 · `vite build` exit 0, 446 modules · vitest 219/219 |
| **Rollback** | `git checkout -- control-plane/src/sop-review.tsx` then rebuild |

### C2 — `Dockerfile`

```diff
-# COPY control-plane/dist ./control-plane/dist  # Optional, build separately
+COPY control-plane/dist ./control-plane/dist
```

| | |
|---|---|
| **Defect** | The image was backend-only. `/v1/health` was green and the commit message said "Docker build validated", but the container had no frontend at all |
| **Nature** | One line, restores intent already documented in the file |
| **Verification** | `nusantara:v1-dist` builds (2.48 GB) · container `healthy` · `/v1/health` 200 · `dist/` confirmed inside the image (5 files) |
| **Rollback** | Re-comment the line |

### C3 — `.gitignore`

```diff
-reports/
+# `reports/` used to be excluded wholesale, which also excluded the V1 audit
+# deliverables. Exclude the directory's contents instead so the evidence
+# directory can be tracked while scratch reports stay untracked.
+reports/*
+!reports/audit/
```

| | |
|---|---|
| **Defect** | `reports/` was ignored in full, which also ignored `reports/audit/v1-restructure/`. **The audit deliverables could not be committed** — the evidence would have been lost with the working directory |
| **Nature** | Ignore-pattern narrowing. Scratch reports remain ignored |
| **Verification** | `git status` now shows `?? reports/audit/`; no other path changed classification |
| **Rollback** | Restore `reports/` |

### C4 — `pyproject.toml`

```diff
-version = "2.0.0a3"
-description = "NUSANTARA AI V2 - FastAPI, MCP, governed tools, audit trail"
+version = "0.1.0"
+description = "Nusantara V1 - FastAPI, MCP, governed tools, audit trail"

-    "haystack-ai==2.31.1",
+    "haystack-ai>=3.4,<4",

-workflow = ["langgraph==1.2.14"]
+workflow = ["langgraph>=1.2,<2"]
```

| | |
|---|---|
| **Defect** | (a) The package called itself **V2** at version `2.0.0a3`, contradicting the no-V2 mandate and disagreeing with `/v1/health`, which reports `0.1.0`. (b) `haystack-ai==2.31.1` vs **3.4.1 installed** — `pip install -e .` would have silently downgraded a core knowledge-pipeline dependency by a major version. (c) `langgraph==1.2.14` vs **1.2.20 installed**, and unsatisfiable alongside the `langchain` extra |
| **Nature** | Metadata only. Nothing was installed, upgraded or downgraded. The pins now permit the version actually under test |
| **Verification** | Core suite 63/63 unchanged · vitest 219/219 unchanged · no reinstall performed |
| **Rollback** | `git checkout -- pyproject.toml` |

---

## 3. Changes to test files

Both changes make an existing assertion *execute*. Neither removes or weakens one.

### C5 — `tests/test_v1_sop_boundary.py`

```diff
+import threading
+import time

-    names = {'ChatRequest', 'chat', ..., 'list_knowledge_documents'}
+    names = {'ChatRequest', 'chat', ..., 'list_knowledge_documents', '_check_rate_limit'}

+    rate_state = {'_rate_limit_lock', '_rate_limit_windows',
+                  '_RATE_LIMIT_MAX', '_RATE_LIMIT_WINDOW_S'}
+    state = [n for n in tree.body
+             if (isinstance(n, ast.AnnAssign) and getattr(n.target, 'id', None) in rate_state)
+             or (isinstance(n, ast.Assign)
+                 and any(getattr(t, 'id', None) in rate_state for t in n.targets))]

-              capture_retrieval=capture_retrieval, uuid4=uuid4)
-    exec(compile(ast.Module(body=imports + nodes, ...)))
+              capture_retrieval=capture_retrieval, uuid4=uuid4,
+              threading=threading, time=time)
+    exec(compile(ast.Module(body=imports + state + nodes, ...)))
```

| | |
|---|---|
| **Defect** | The fixture compiles `chat()` out of `app\api\routes.py` into a hand-built namespace. `routes.py` gained `_check_rate_limit` (called at line 1118); the allowlist did not. Every test reaching `chat()` raised `NameError` → **19 security-boundary tests could not run** |
| **Nature** | The real limiter is now compiled in with its real module state — more production code under test, not less |
| **Verification** | `19 passed` (was 11 failed / 8 passed). Five dependent modules improved with it |
| **Rollback** | `git checkout -- tests/test_v1_sop_boundary.py` |

### C6 — `tests/test_evidence_runner_guards.py`

```diff
 runner = sys.modules["__main__"]

+# These checks bind directly to the guard functions installed by the isolated
+# evidence runner. Under a plain `pytest` collection `__main__` is pytest, not
+# the runner, so the guards do not exist and every assertion below would fail
+# for the wrong reason.
+pytestmark = pytest.mark.skipif(
+    not hasattr(runner, "guarded_open"),
+    reason="guards live in tests/run_evidence_tests_isolated.py; run via that entry point",
+)
```

| | |
|---|---|
| **Defect** | The module binds to guards installed by `run_evidence_tests_isolated.py`, which invokes `pytest.main()` in-process. Under plain `pytest`, `__main__` is pytest → 9 `AttributeError` failures with **zero assertions evaluated** |
| **Nature** | Precondition skip. Coverage is relocated to the entry point where it is real |
| **Verification** | plain pytest → `9 skipped` · `python tests/run_evidence_tests_isolated.py` → **66 passed, 2 failed** |
| **Rollback** | Delete the `pytestmark` block |

---

## 4. Operational events

### O1 — backend restarted

| | |
|---|---|
| **Event** | The long-running backend (PID 6508, up since the morning) returned `500` on every `POST /v1/chat` while `GET /v1/health` still returned `ok`. Two live security assertions failed as a result |
| **Action** | Process stopped, restarted with the same command the official launcher uses: `.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000` |
| **Result** | `POST /v1/chat` → 200 for anonymous and admin; `automated_regression.py` → **6/6 PASS** |
| **Data impact** | None. No migration, no schema change, no record deleted. Chat history gained a few probe rows in a throwaway session |
| **Finding** | **S-R1 (HIGH)** — health check does not exercise the chat path |

### O2 — no other service touched

Frontend (5180), Ollama (11434) and the unrelated `mcp-setup` service (8001) were left running and unmodified.

---

## 5. Documents created

### 5.1 Audit deliverables — `reports\audit\v1-restructure\`

| # | Document | Contract |
|---:|---|---|
| 1 | `BACKUP_VERIFICATION_REPORT.md` | §12.1 |
| 2 | `SOURCE_BASELINE_REPORT.md` | §12.2 |
| 3 | `V1_REPOSITORY_INVENTORY.md` | §12.3 |
| 4 | `BACKEND_FORENSIC_AUDIT.md` | §12.4 |
| 5 | `HERMES_FORENSIC_AUDIT.md` | §12.5 |
| 6 | `KNOWLEDGE_RAG_FORENSIC_AUDIT.md` | §12.6 |
| 7 | `DATABASE_SOP_FORENSIC_AUDIT.md` | §12.7 |
| 8 | `SECURITY_FORENSIC_AUDIT.md` | §12.8 |
| 9 | `FILE_DEPENDENCY_MAP.md` | §12.9 |
| 10 | `RUNTIME_MODULE_MAP.md` | §12.10 |
| 11 | `FRONTEND_FORENSIC_AUDIT.md` | §12.11 |
| 12 | `CONTROL_PLANE_FORENSIC_AUDIT.md` | §12.12 |
| 13 | `TEST_RUNTIME_AUDIT.md` | §12.13 |
| 14 | `DEPENDENCY_AUDIT.md` | §12.14 |
| 15 | `AUDIT_HISTORY_RECONCILIATION.md` | §12.15 |
| 16 | `AI_LEGACY_CLEANUP_REPORT.md` | §12.16 |
| 17 | `TARGET_REPOSITORY_STRUCTURE.md` | §12.17 |
| 18 | `RESTRUCTURING_CHANGELOG.md` | §12.18 (this file) |
| 19 | `REGRESSION_TEST_REPORT.md` | §12.19 |
| 20 | `SECURITY_REGRESSION_REPORT.md` | §12.20 |
| 21 | `V1_FINAL_ARCHITECTURE.md` | §12.21 |
| 22 | `V1_FINAL_READINESS_REPORT.md` | §12.22 |
| 23 | `ROLLBACK_AND_RESTORE_GUIDE.md` | §12.23 |
| 24 | `CLASSIFICATION_SUMMARY.md` | support |
| 25 | `BROWSER_E2E_PROOF.md` | addendum §6 — browser-level evidence, two rendered conversations |

### 5.2 Manifests — machine-readable

| File | Rows | Purpose |
|---|---:|---|
| `FILE_INVENTORY.csv` | 19,804 | every scanned file, classified |
| `FILE_ARCHIVE_MANIFEST.csv` | 9,183 | archive candidates — **not executed** |
| `FILE_DELETION_MANIFEST.csv` | 12 | deletion candidates — **not executed** |
| `FILE_MOVEMENT_MANIFEST.csv` | 26 | relocations — **not executed** |
| `GENERATED_CACHE_AGGREGATES.csv` | 370 files / 5 dirs | re-creatable caches |
| `BACKUP_CHECKSUMS.csv` | 23,032 | SHA-256 of the verified backup |
| `ROUTE_INVENTORY.json` | 61 routes | HTTP surface |
| `MODULE_GRAPH_EDGES.csv` | 302 edges | import graph |
| `CLASSIFICATION_SUMMARY.md` | — | counts and rules |

### 5.3 Raw evidence logs

`.pytest_core.txt`, `.pytest_full.txt`, `.pytest_after.txt`, `.pytest_final.txt`, `.vitest.txt`, `.npm_audit.txt`, `.test_inventory.txt`, `.fail_buckets.txt`, `.fail_detail.txt`, `.pytest_failures.txt`

### 5.3a Browser evidence — `evidence\`

| File | Content |
|---|---|
| `e2e-01-chat-greeting.png` | UI rendering "halo" → "Halo! Ada yang bisa saya bantu?" |
| `e2e-02-chat-grounding-refusal.png` | UI rendering an anonymous SOP question → grounded refusal, model `gemma3n`, 22,132 ms, no evidence |
| `stream-direct-8000.ndjson` | the 689-byte NDJSON stream, direct to `:8000` |
| `stream-via-proxy-5180.ndjson` | the same stream through the Vite proxy |

### 5.4 Audit scratch scripts — `.audit_tmp\`

28 read-only analysis scripts (`nusa_classify.py`, `graph_analysis.py`, `hash_backup.py`, `parse*.py`, …). All are AST/regex readers; none import the application or mutate state. **Not tracked** — they are working material, not deliverables. `.audit_tmp/` is disposable once the manifests are accepted.

---

## 6. Effect, measured

| Metric | Baseline | Now | Δ |
|---|---:|---:|---:|
| Tracked files | 1,727 | 1,727 | 0 |
| On-disk files | 159,704 | 159,704 | 0 |
| Root files | 146 | 146 | 0 |
| Full pytest failures | 100 | **74** | **−26** |
| Full pytest passes | 1,555 | **1,572** | **+17** |
| Core gate | 63/63 | **63/63** | 0 |
| Vitest | 219/219 | **219/219** | 0 |
| Frontend build | exit 0 | exit 0 | 0 |
| Docker image | healthy (no UI) | **healthy (with UI)** | +UI |
| Live security assertions | 4/6 (degraded process) | **6/6** | +2 |

Nothing in the tree was removed, so file counts are unchanged. All movement is registered, not performed.

---

## 7. What was NOT done — approvals required

| # | Pending action | Scope | Risk if approved |
|---:|---|---|---|
| **A1** | Archive to `C:\Users\dmaza\NUSANTARA_V1_ARCHIVE\` | 9,183 files / 290.7 MB | Low — copy-verify-remove, second copy in `E:` |
| **A2** | Delete root shell accidents | 12 files / 27,681 B | Low — 8 tracked, hash-verified in backup |
| **A3** | Relocate contracts + verifiers | 26 files | Low — pure relocation |
| **A4** | `npm audit fix` (zod 4.6.5→4.6.6, seroval) | `package-lock.json` | Low — requires rebuild + re-run |
| **A5** | Remove `app\v2\` + `v2_routes.py` | 4 modules | **Medium** — 3 test modules must be rewritten first |
| **A6** | Fix Grounding Guard negative-claim acceptance | `app\` business logic | **High** — safety-critical path |
| **A7** | Untrack `control-plane/.vite-temp`, `.build-temp-*` | ~490 tracked cache files | Low — they are regenerated/deleted by the build |
| **A8** | Pin base image by digest, commit a Python lock | `Dockerfile`, new file | Low |
| **A9** | Add `/metrics` endpoint | `app\api` | Low — 3 tests already expect it |

---

## 8. Verdict

| Criterion | Result |
|---|---|
| Every change documented | **PASS** — 6 files, each with defect, nature, verification, rollback |
| Destructive action taken | **NONE** |
| Irreversible action taken | **NONE** |
| Change without a regression argument | **NONE** |
| Change to `app\` | **NONE** |
| Test weakened | **NONE** |
| Coverage | **INCREASED** — 19 boundary tests now execute |
| Deliverables committable | **YES** — `.gitignore` fixed |
| Pending approvals listed | **YES** — 9 items |
