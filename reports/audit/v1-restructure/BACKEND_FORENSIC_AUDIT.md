# BACKEND_FORENSIC_AUDIT

**Project:** Nusantara V1
**Contract:** deliverable §12.7
**Date:** 2026-11-18
**Scope:** `app\` — 247 Python modules, 52,431 lines, 36 packages

---

## 1. Application assembly

`app\main.py` — 147 lines. This is the only FastAPI application object.

| Element | Line | Evidence |
|---|---|---|
| `lifespan(app)` | 42 | Startup/shutdown hook |
| `request_id_middleware(request, call_next)` | 92 | Correlation ID propagation |
| `health_check()` | 111 | Root `GET /health` |
| `dashboard(request)` | 120 | Serves UI |
| `app.include_router(api_router)` | 84 | Main API surface |
| `app.include_router(inspection_preview_router, prefix='/v1')` | 85 | Preview endpoints |
| `app.include_router(control_plane_router)` | 86 | Control Plane |

Explicit V1-only guard at line 27–28:

```python
# V1-only runtime: keep V2 code archived in place without importing its
# model/index services or registering any /v2 endpoints.
```

**Verdict:** single application entry point, correct. `GET /v1/health` responds `{"status":"ok","service":"nusantara-core","version":"0.1.0","build_id":"sha256:d28af30a…"}` (measured).

---

## 2. API layer — `app\api\` (8 modules, 61 routes)

| Module | Lines | Role |
|---|---:|---|
| `routes.py` | 1,686 | Chat, ingest, search, health, metrics, handoff |
| `knowledge_pipeline.py` | — | SOP review + pipeline endpoints |
| `control_plane.py` | 493 | 20 Control Plane endpoints |
| `runtime_readiness.py` | — | Readiness probes |
| `runtime_verification.py` | — | Verification probe |
| `inspection_preview.py` | — | PDF/preview inspection |
| `skills.py` | — | Executable skills |
| `v2_routes.py` | — | **Dead** — router never registered |

### 2.1 `routes.py` structure

**Request models (12):** `ChatRequest`, `_PublicChatModel` + 7 projections (`Trust`, `Evidence`, `Grounding`, `Understanding`, `Problem`, `Response`), `ProblemAnalyzeRequest`, `WorkflowCreateRequest`, `DocumentIngestRequest`, `KnowledgeSearchRequest`, `HumanHandoffRequest`, `HealthResponse`.

**Endpoints (14):** `health_check`, `health_detail`, `chat_history`, `chat`, `analyze_problem`, `create_workflow`, `get_workflow`, `ingest_document`, `search_knowledge`, `list_knowledge_documents`, `request_handoff`, `get_metrics`, `developer_core_status`.

### 2.2 Finding — god module

`app.api.routes` has **fan-out 34**: it imports 34 distinct `app.*` modules. `chat` alone is 313 lines (line 1103 → 1416). This is the highest-risk maintenance point in the codebase.

**Disposition:** not refactored. Splitting a live request path under a "no business-logic change" contract would be a business-logic change with no test that proves equivalence. Recorded as debt, not acted on.

### 2.3 Finding — dead V2 router

`app\api\v2_routes.py` declares 10 routes under `prefix="/v2"` and imports 23 `app.*` modules, including the whole `app.v2` parallel stack. `main.py` never registers it. `tests\test_v2_disabled.py` asserts it stays unregistered, by monkeypatching imports:

```python
if name == 'app.api.v2_routes' or name.startswith('app.v2'):
```

**Disposition:** ARCHIVE in the manifest. Deletion deferred — see `AI_LEGACY_CLEANUP_REPORT.md` §7.

---

## 3. Authentication and authorisation

`app\security\auth.py` — 22 lines, one function:

```python
def require_admin(token):   # line 12
```

Comparison is `hmac.compare_digest` (timing-safe). Header: `X-Admin-Token`. Secret source: `NUSANTARA_ADMIN_TOKEN` env var.

| Endpoint class | Guard |
|---|---|
| `POST /v1/chat` | `x_admin_token` optional (operator mode); non-operator path returns no evidence |
| `POST /v1/documents/ingest` | `require_admin` |
| `POST /v1/knowledge/search` | `require_admin` |
| `GET /v1/knowledge/documents` | `require_admin` |
| `GET /v1/chat/history` | `X-Chat-Session` + optional admin |

### Finding — single shared token

There is no per-user identity. Every caller presents the same token. Audit trail records `principal`, but the principal is either `operator` (token present) or `anonymous`. This is a **known, documented limitation**, not a defect introduced by this audit. It requires an identity provider to fix and is out of V1 scope.

---

## 4. Error handling and observability

| Mechanism | Location |
|---|---|
| Error taxonomy (TRANSIENT / PERMANENT / NEEDS_HUMAN / POLICY_DENIED) | `app\core\error_taxonomy.py` |
| Structured logging | `app\observability\logging.py` (fan-in 7) |
| Correlation context | `app\observability\context.py` (fan-in 10) |
| Request ID middleware | `app\main.py:92` |
| Runtime identity | `app\core\runtime_identity.py` (fan-in 12 — the spine) |

Worst-connected modules in the system are all observability/identity primitives. That is the correct shape: the cross-cutting concerns are the ones everything shares.

---

## 5. Background work

| Mechanism | Evidence |
|---|---|
| Knowledge folder watcher | `KnowledgeEngine.set_knowledge_watch`, `.scan_knowledge_watch`, `.knowledge_pipeline_status` |
| Watcher config table | `knowledge_pipeline_config` (1 row: `watch_enabled`, `watch_folder`) |
| Retry | `KnowledgeEngine.retry_knowledge_source(run_id)` |
| Worker subprocess | `app\knowledge\worker_process.py`, `app\knowledge\docling_worker.py` |

There is **no task queue** (no Celery/RQ/Arq). Background work is in-process or subprocess. This is a legitimate design for a single-node V1 and is not a gap.

---

## 6. Data access layer

There is **no repository abstraction**. SQLite is accessed directly from:

- `app\knowledge\store.py` — vector/chunk persistence
- `app\knowledge\rag.py` `MemoriaVectorStore` — 8 methods including `search_similarity`
- `app\knowledge\sop_review.py` — review state, trials, events
- `app\knowledge\sqlite_backup.py` — backup via the SQLite online backup API

**Verdict:** direct SQL is acceptable at this size, but it means the DB schema is a de-facto API contract. Schema changes are therefore high-risk and were not performed.

---

## 7. Module inventory risk table

| Risk | Modules | Severity | Actioned |
|---|---|---|---|
| Parallel "developer core" trees | `app\developer_core\` (29) vs `app\devcore\` (9) | High (duplication) | No — needs functional diff |
| Dead V2 stack | `app\v2\` (4) + `app\api\v2_routes.py` | High (contract violation if shipped) | ARCHIVE in manifest |
| God module | `app\api\routes.py` (34 imports) | Medium | No — out of scope |
| Source-tree backups | 11 `.backup*` files inside `app\` | Low | ARCHIVE |
| Pre-patch snapshots | 3 `.before_*_patch.py` inside `app\knowledge\` | Low | ARCHIVE |
| Unused package dirs | `app\sop_semantic`, `app\semantic`, `app\ui` contain no importable module tested by a suite | Unknown | Recorded |

---

## 8. Backend verdict

| Criterion | Result | Evidence |
|---|---|---|
| Single entry point | **PASS** | `app\main.py`, uvicorn `app.main:app` |
| Health endpoint | **PASS** | `GET /v1/health` → 200, measured |
| Authentication present | **PASS** | `require_admin`, `hmac.compare_digest` |
| Authorisation boundary | **PASS** | `V1KnowledgeBoundary` gates pilot docs |
| Error taxonomy | **PASS** | 4 categories implemented |
| Correlation ID | **PASS** | `request_id_middleware` |
| Background work defined | **PASS** | watcher + retry + worker subprocess |
| No second engine | **PASS for runtime**, **FAIL for source tree** | `app\v2\` present but unregistered |
| No duplicate auth path | **PASS** | one `require_admin` |
| Import graph acyclic | **FAIL** | 4 real cycles + 1 self-import — see `FILE_DEPENDENCY_MAP.md` §4 |

**Backend status: ACTIVE / PARTIAL.** The product runs and serves its contract. The source tree still contains a complete, unregistered V2 implementation and a duplicated developer-core subtree — both recorded, neither removed without approval.

> **Correction to an earlier draft of this report:** an initial version claimed the import graph was acyclic. A cycle-detection pass over all 302 resolved edges found **4 genuine cycles** plus 1 self-import. The claim was wrong and is corrected here; see `FILE_DEPENDENCY_MAP.md` for the full analysis. The cycles are all late-bound (imports inside function bodies) except `v1_knowledge → engine → composition → v1_knowledge`, which is a module-level cycle that Python resolves by partial initialisation and which works only because the cycle is closed through attribute access rather than class inheritance.
