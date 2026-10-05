# MASTER ENGINEERING AUDIT — NUSANTARA AI V1

Phase 0. NO code changes. Architecture, runtime flow, dependency map, API map,
data flow, model flow, RAG flow, document flow, configuration flow, storage
flow, observability flow, security surface, test coverage, known bugs,
architectural risks, technical debt, duplicate components, dead code, missing
contracts, recommended fixes, risk level, priority.

---

## 1. Current Architecture (observed)

Source-of-truth files: `docs/architecture.md`, `docs/contracts/NUSANTARA-ARCHITECTURE-CONTRACT-V1.md`,
`docs/contracts/NUSANTARA-V1-VERIFICATION-WORK-CONTRACT.md`,
`app/main.py`, `app/api/routes.py`, `app/hermes/agent.py`.

### Logical architecture

```
Client / UI
    ↓
FastAPI (app/main.py)
    ├── /v1   (app/api/routes.py, 1532 LOC)
    └── /v2   (app/api/v2_routes.py)
    ↓
V1 Orchestrator: HermesAgent (app/hermes/agent.py, 37 LOC)
    ↓
LanguageEngine (app/language/engine.py)
    ↓
ProblemEngine (app/problem/engine.py)
    ↓
[ Knowledge / RAG via app/knowledge/* ]    (used by grounding safety gate in /v1/chat)
    ↓
ModelRouter (app/models/router.py)
    ↓
LLMProvider implementations:
    ├── OllamaProvider (app/models/ollama.py)
    ├── OpenAICompatibleProvider (app/models/openai_compatible.py)
    └── MockProvider (app/models/mock.py, app/models/mock_provider.py — see duplication section)
```

### Module inventory (active code only, excludes .bak / .backup)

| Module | File | LOC | Role |
|--------|------|-----|------|
| api | `app/api/routes.py` | 1532 | /v1 endpoints (chat, problem, knowledge, grounding) |
| api | `app/api/v2_routes.py` | (active) | /v2 endpoints |
| core | `app/main.py` | 59 | FastAPI app entry |
| core | `app/core/config.py` | 30 | Settings (Pydantic Settings, .env) |
| hermes | `app/hermes/agent.py` | 37 | V1 orchestrator |
| language | `app/language/engine.py` | ~1400 | Language pipeline |
| problem | `app/problem/engine.py` | (active) | Problem analysis |
| reasoning | `app/reasoning/engine.py` | (active) | Reasoning (facts + solutions) |
| knowledge | `app/knowledge/rag.py` | 716 | RAG pipeline |
| knowledge | `app/knowledge/grounding.py` | 1030 | EvidenceGroundingGuard |
| knowledge | `app/knowledge/production_kb.py` | 1423 | Production knowledge base (CLI + ingest) |
| knowledge | `app/knowledge/parser.py` | (active) | Parser registry (Text/MD/PDF/DOCX) |
| knowledge | `app/knowledge/store.py` | (active) | SQLiteVectorStore |
| knowledge | `app/knowledge/embeddings.py` | (active) | EmbeddingProvider |
| knowledge | `app/knowledge/chunker.py` | (active) | Chunker |
| knowledge | `app/knowledge/reranker.py` | (active) | Reranker (simple/cross-encoder/LLM) |
| knowledge | `app/knowledge/retriever.py` | (active) | Retriever |
| knowledge | `app/knowledge/indobert_embedding.py` | (active) | IndoBERT adapter |
| knowledge | `app/knowledge/official_knowledge_ingestion.py` | ~1100 | Official source ingestion CLI |
| knowledge | `app/knowledge/production_hybrid_rag.py` | (active) | Hybrid semantic + lexical |
| models | `app/models/base.py`, `ollama.py`, `openai_compatible.py`, `mock.py`, `mock_provider.py`, `router.py` | — | Provider abstraction |
| v2 | `app/v2/orchestrator.py`, `wiring.py` | — | V2 extension layer |
| developer_core | `app/developer_core/*.py` | 25 modules | Change-control / approval / Claude Code integration (governance layer) |

### Auxiliary modules (NOT in /v1/chat path by default)

policy, trust, memory, tools, mcp, handoff, workflow, observability, governance,
approval, research, experience, improvement, ui, schemas, security, skills,
runtime, runtime — defined but not all wired into `/v1/chat` execution path.
Per V1 Architecture Contract, these are extension layers.

---

## 2. Actual /v1 Runtime Flow

Verified via `graphify` traversal + V1 Architecture Contract §20.

```
POST /v1/chat  (app/api/routes.py L715 chat())
    ↓
_request_id + structured logging (observability)
    ↓
_language_engine.process()        (LanguageEngine)
    ↓
_problem_engine.resolve()         (ProblemEngine → ProblemResolution)
    ↓
_knowledge_engine.search()        (KnowledgeEngine)
    ↓
_apply_grounding_safety_gate()    (app/api/routes.py — uses EvidenceGroundingGuard)
    ↓
ModelRouter.route_and_generate()  (app/models/router.py)
    ↓
LLMProvider.generate()            (OllamaProvider | OpenAI | Mock)
    ↓
Response (validated, with request_id correlation)
```

---

## 3. Dependency Map

`pyproject.toml` core deps:

- fastapi>=0.115.0
- uvicorn[standard]>=0.30.0
- pydantic>=2.9.0
- pydantic-settings>=2.5.0
- python-dotenv>=1.0.0
- httpx>=0.27.0

Dev: pytest, pytest-asyncio, ruff, mypy, types-requests, pytest-cov.

Runtime-only imports discovered (not declared in `pyproject.toml` —
investigation required in Phase 0.5 to confirm whether they are
transitive or shadow-installed):

- `pypdf` (used by `PDFParser`)
- `python-docx` (used by `DOCXParser`)
- `sqlite3` (stdlib — fine)

Either raise:
- `pyproject.toml` is missing runtime imports (P1 — drift).
- These are installed transitively through another dep (P3 — needs lock file).

## 4. API Map (/v1)

| Endpoint | File:Line | Notes |
|----------|-----------|-------|
| POST /v1/chat | `routes.py:715` | Main chat orchestrator |
| POST /v1/problem/analyze | `routes.py:1235` | ProblemEngine-only |
| /v1/documents/* | (active) | Knowledge ingest / list |
| /v1/knowledge/* | (active) | Knowledge retrieval |
| /v1/metrics | (active) | Per PROJECT_BASELINE.md returns constant 0 |
| /v1/health/detail | (active) | Per PROJECT_BASELINE.md returns static "available" |

## 5. Data Flow

Pydantic v2 schemas in `app/knowledge/schemas.py`, `app/problem/problem_schema.py`,
`app/language/schemas.py`, `app/models/schemas.py`. Request → Pydantic
validation → engine call → Pydantic serialization. No raw dict round-trip in
the active path.

## 6. Model Flow

`ModelRouter` (`app/models/router.py:35`) is the single dispatch point. It
selects provider by config (`LLM_PROVIDER=ollama` default) and delegates to
the matching `LLMProvider` implementation. Provider failure paths return
fallback responses (per PROJECT_BASELINE.md).

## 7. RAG Flow

`RAG` (`app/knowledge/rag.py:196`) wires parser registry → Chunker →
EmbeddingProvider → SQLiteVectorStore → Retriever → Reranker. Production
hybrid (`app/knowledge/production_hybrid_rag.py`) mixes semantic (IndoBERT)
+ lexical (SQLite FTS5) with weights from `config/rag_runtime.json`.

EvidenceGroundingGuard (`app/knowledge/grounding.py:20`) is invoked at
`_apply_grounding_safety_gate()` in `routes.py`. Routines: claim
classification (procedure / requirement / numeric / general), evidence
matching, refusal / fallback paths.

## 8. Document Flow

`official_knowledge_ingestion.py` is the primary ingest CLI for V1.
Documents go through: extension dispatch → parser → normalize →
sha256 hash → SQLite dedup check → chunk → embed → store. Registry
sources + manifest + quarantine mechanism are present.

**MarkItDown (re-audited):** MarkItDown is **present** in the repo as an
isolated Claude Code inspection tool (`tools/markitdown/.venv/`,
`tools/markitdown/convert.ps1`, `.claude/skills/markitdown/SKILL.md`,
v0.1.8). It is **deliberately NOT** imported by `app/` and is **NOT**
declared in `pyproject.toml`. The skill contract explicitly states:
"Do not modify application runtime dependencies just to use MarkItDown."
"Do not automatically ingest converted documents into the production
knowledge database." This isolation is correct and matches Master
Developer §5 and §7. Detail in `docs/audit/MARKITDOWN_AUDIT.md`.

## 9. Configuration Flow

Single source of truth: `app/core/config.py` (Pydantic Settings, `.env`,
`get_settings()` singleton). `config/rag_runtime.json` is a secondary
non-Settings config (separate file, no Pydantic binding). This is the
**most likely "two-source" drift**: Settings declares `EMBEDDING_MODEL`,
`VECTOR_STORE_TYPE`, `CHUNK_SIZE`, `CHUNK_OVERLAP`, `RETRIEVAL_TOP_K`,
while `rag_runtime.json` declares `rag.semantic_weight`, `rag.lexical_weight`,
`rag.model.name`, `rag.model.device`, `rag.performance.*`.

Severity: P2 (configuration drift). Recommendation: bind `rag_runtime.json`
through Settings OR document that it is an explicit override layer.

## 10. Storage Flow

- Vector store: SQLite (in-memory by default via `VECTOR_STORE_TYPE=memory`).
  Production path uses SQLite files via `SQLiteVectorStore`.
- Session/Context: in-memory process state.
- Persistence on restart: NOT guaranteed for in-memory state; SQLite-backed
  chunks survive restart.

## 11. Observability Flow

`app/observability/logging.py` JsonFormatter + redact. `app/observability/context.py`
provides `request_context()` (request_id correlation). Middleware in
`app/main.py:39` propagates `X-Request-ID`.

Known issues (per PROJECT_BASELINE.md):
- `/v1/metrics` returns static `requests_total: 0`.
- `/v1/health/detail` returns static "available" for all components.

## 12. Security Surface

- No authn / authz on `/v1/*`. CORS restricted to localhost (NOT a substitute
  for auth).
- `LongTermMemory` pickle load risk noted in `PROJECT_BASELINE.md`. (V2 fix.)
- File ingest path: needs runtime trace to confirm Malicious-PDF / oversized /
  compressed-bomb guards are present. (Phase 11.)

## 13. Test Coverage

145 collected, 143 passed, 1 failed, 1 skipped (see `BASELINE.md`).
Coverage gap: `fail_under = 80` is configured but coverage was not run.
Subtests in `tests/unit/`, `tests/integration/` are empty directories —
all live tests are at `tests/test_*.py`, `tests/v2/test_*.py`, and
`tests/evaluation/`.

## 14. Known Bugs

1. `test_project_has_no_secrets` fails: hardcoded_credential in
   `scripts/validate_gate16_audit.py` lines 413–414.
2. `datetime.utcnow()` deprecation: 46 occurrences (PROJECT_BASELINE.md).
   Runtime hit at `app/handoff/engine.py:51`.
3. `app/handoff/engine.py` instantiates `HandoffEngine()` per request →
   handoff state likely lost (PROJECT_BASELINE.md).
4. `models/mock.py` vs `mock_provider.py`; `ollama.py` vs `ollama_provider.py`
   — duplicate provider implementations (see §16).
5. `workflow/schemas.py` vs `workflow_schema.py`; `problem/schemas.py` vs
   `problem_schema.py` — duplicate schema files.
6. `tests/unit/`, `tests/integration/` empty.

## 15. Architectural Risks

| # | Risk | Severity | Notes |
|---|------|----------|-------|
| R1 | Configuration source drift (Settings vs `rag_runtime.json`) | P2 | Single source of truth contract violation risk |
| R2 | Duplicate provider implementations | P1 | Mock / Ollama / OpenAI each have two files; only one is imported in active path — dead code in the other |
| R3 | MarkItDown missing / not bounded | P2 | Master Developer requires `DocumentConverter` interface — not present |
| R4 | XLSX / PPTX parsers missing | P1 | Parser registry only has Text/MD/PDF/DOCX |
| R5 | `/v1/metrics` static-zero | P2 | Observability broken at the metric endpoint |
| R6 | `/v1/health/detail` static-"available" | P2 | Health endpoint lies about component status |
| R7 | No authn/authz | P1 (security) | CORS ≠ auth |
| R8 | In-memory session state | P2 | Lost on restart |
| R9 | Pickle memory in Remote Code | P1 (security, if still active) | Code-execution risk if V1 path still loads pickle |
| R10 | Backup files in active paths | P2 | 20+ `.bak` files in `app/api/`, `app/knowledge/`, `app/language/` — risk of being re-imported or copied forward |

## 16. Duplicate Components

Active modules with name-collisions (need to confirm which is on the runtime
path and which is dead):

- `app/models/mock.py` vs `app/models/mock_provider.py`
- `app/models/ollama.py` vs `app/models/ollama_provider.py`
- `app/workflow/schemas.py` vs `app/workflow/workflow_schema.py`
- `app/problem/schemas.py` vs `app/problem/problem_schema.py`

Each pair should have exactly ONE active implementation. The other is
either dead code or a candidate for deletion per Master Developer rule 32.

## 17. Dead Code

Files in active module paths ending in `.bak`, `.backup`, `.before_*`,
`.tmp` — these are dead by definition but they live next to active code
and increase cognitive load. Examples:

- `app/api/routes.py.bak*` (16 files)
- `app/knowledge/rag.py.bak`, `rag.py.bak2`
- `app/knowledge/grounding.py.bak`, `schemas.py.bak`, `store.py.bak`,
  `store.py.lexical-v1.bak`
- `app/knowledge/production_kb.before_authority_patch.py`,
  `production_kb.before_metadata_authority_patch.py`,
  `production_semantic_retriever.before_authority_hydration.py`
- `app/language/engine.py.backup`, `engine.py.backup_1.3.0`,
  `engine.py.backup_1.4.0`, `engine.py.bak`, etc.
- `app/models/schemas_compat.tmp`
- Root-level: `app_backup_before_openrouter/`, `backup_indobert_*`,
  `legacy_v1_artifacts/`, `nusantara_master_engine_BACKUP_*.py`,
  `developer_core_engine_SOURCE_BACKUP.txt`, `engine_source.txt`,
  `routes_current_backup.txt`, `audit_engine.txt`, `build_all.py.backup_*`.

Severity: P3 (cosmetic, but increases change risk). Recommended action in
Phase 6.5: move all to `archive/`/`legacy/` with explicit ARCHIVED status
per V1 Architecture Contract §18.

## 18. Missing Contracts

| Contract | Status |
|---|---|
| `DocumentConverter` interface (Master Developer §7) | MISSING |
| `KnowledgeEngine` ↔ `HermesAgent` runtime integration evidence | IMPLICIT (grounding gate uses knowledge, but Hermes itself does not call RAG in all paths) — needs runtime trace |
| V1 `Memory` governance contract | PARTIAL (V2 fix noted) |
| Tool governance contract | PARTIAL (`governance/tools.py` exists; `/v1/chat` does not invoke tools by default) |
| MCP governance contract | PARTIAL (`app/mcp/mcp.py` exists; not on `/v1/chat`) |

## 19. Recommended Fixes (ranked)

### P0 — correctness / security / data corruption
- F1. Investigate and confirm whether the `LongTermMemory` pickle loader is
      still on a runtime path. If yes, replace pickle with JSON.
- F2. Add authn/authz to /v1 (decision required: keep open for local dev,
      or add token-based auth).
- F3. Confirm Malicious-PDF / oversized-file guards on document ingest path.

### P1 — runtime reliability
- F4. Fix `scripts/date` — actually, fix `test_project_has_no_secrets`
      by removing or rewriting the hardcoded credential in
      `scripts/validate_gate16_audit.py:413-414`.
- F5. Add XLSX + PPTX parsers (or document exclusion).
- F6. Decide and document which duplicate provider implementation is
      authoritative (Mock / Ollama); delete the other.
- F7. Make `/v1/metrics` and `/v1/health/detail` return live data.

### P2 — API contract
- F8. Bind `config/rag_runtime.json` to Pydantic Settings, OR document it
      as explicit override layer with precedence.

### P3 — RAG correctness
- F9. Test grounding guard against false-positive retrieval cases (Master
      Developer §19: "Apa itu Paspor?" must not return KTP evidence).

### P4 — observability
- F10. Replace 46 `datetime.utcnow()` with `datetime.now(timezone.utc)`.

### P5 — performance
- (no recommendation yet — measure first)

### P6 — maintainability
- F11. Move all `.bak`, `.backup`, `.before_*`, `.tmp` files in active
      module directories to `archive/` with ARCHIVED status per V1
      Architecture Contract §18.

### P7 — cosmetic
- F12. Decide which name pair wins: `models/{mock,mock_provider}`,
      `models/{ollama,ollama_provider}`,
      `workflow/{schemas,workflow_schema}`,
      `problem/{schemas,problem_schema}`.

## 20. Risk Level per File

| File | Risk | Notes |
|------|------|-------|
| `scripts/validate_gate16_audit.py` | LOW (audit script only) | Lines 413–414 hardcoded credential |
| `app/handoff/engine.py` | MEDIUM | datetime.utcnow + per-request instantiation |
| `app/main.py` | LOW | Stable entry point |
| `app/api/routes.py` | HIGH | 1532 LOC, primary /v1 surface |
| `app/hermes/agent.py` | MEDIUM | 37 LOC orchestrator; contract-sensitive |
| `app/knowledge/grounding.py` | HIGH | 1030 LOC; safety boundary |
| `app/knowledge/rag.py` | HIGH | 716 LOC; RAG pipeline |
| `app/knowledge/production_kb.py` | HIGH | 1423 LOC; ingestion CLI + library |
| `app/knowledge/official_knowledge_ingestion.py` | HIGH | ~1100 LOC; ingestion CLI |
| `app/language/engine.py` | HIGH | ~1400 LOC; intent/entity/normalizer |
| `app/developer_core/*` | MEDIUM | Governance layer; touched in current branch |

## 21. Priority

P0: F1, F2, F3
P1: F4, F5, F6, F7
P2: F8
P3: F9
P4: F10
P6: F11
P7: F12

## 22. V1 Readiness Verdict

**CONDITIONALLY READY**

Evidence:
- 143/145 tests pass; the single failure is in an audit script (not runtime).
- /v1 chat path is coherent (Language → Problem → Knowledge → Grounding → Model).
- Single source of truth for app config exists in `app/core/config.py`.
- Grounding safety gate is wired.
- MarkItDown absence is non-blocking for V1 SOP/regulation ingestion.

Blockers to "READY":
- F1 (pickle memory in active path?).
- F2 (no auth).
- F5 (XLSX/PPTX).
- F11 (`.bak` files still in active module paths — risk of accidental import).

## 23. Approval Required Before

- Any change to `app/knowledge/grounding.py`, `app/knowledge/rag.py`,
  `app/api/routes.py`, `app/hermes/agent.py`, `app/main.py`,
  `config/rag_runtime.json`, `pyproject.toml`, `app/core/config.py`,
  `scripts/validate_gate16_audit.py`.
- Adding `markitdown` to dependencies.
- Deleting any duplicate provider / schema file.