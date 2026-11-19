# V1_FINAL_ARCHITECTURE

**Project:** Nusantara V1
**Contract:** deliverable §12.21, addendum §5.B
**Date:** 2026-11-18
**Status:** as-built. Every arrow below was read from a call site, not inferred from a name.
**Companions:** `RUNTIME_MODULE_MAP.md`, `FILE_DEPENDENCY_MAP.md`, `CONTROL_PLANE_FORENSIC_AUDIT.md`

---

## 1. One paragraph

Nusantara V1 is a **single-process, loopback-bound FastAPI service** that answers questions about Indonesian civil-registry SOPs using only documents a human has reviewed and approved. It has one HTTP backend (port 8000), one React control plane (port 5180), one local model runtime (Ollama, port 11434) and one SQLite database. There is no second engine, no microservice split, no message broker and no external API dependency at runtime. The knowledge base cannot be modified by the model: documents move `Upload → Processing → Review → Approve → Knowledge Active` and only a human moves them across the last two boundaries.

---

## 2. Runtime topology — five listeners, three of them ours

```
                        ┌──────────────────────────────┐
                        │  browser                     │
                        └───────────┬──────────────────┘
                                    │ HTTP 5180
                        ┌───────────▼──────────────────┐
                        │  Vite / React 19 SPA         │  node.exe  :5180
                        │  control-plane\src\          │  36 modules, 3,754 lines
                        └───────────┬──────────────────┘
                                    │ proxy /v1/*
                        ┌───────────▼──────────────────┐
                        │  uvicorn  :8000              │  python.exe
                        │  app.main:app                │  247 modules
                        │  61 HTTP routes              │
                        └───┬───────────────┬──────────┘
                            │               │
              stdio         │               │  HTTP 11434
        ┌───────────────────▼──┐      ┌─────▼──────────────┐
        │ IndoBERT worker      │      │ Ollama             │
        │ 768-dim embeddings   │      │ gemma3n:e2b-it-q4  │
        │ no socket            │      │ ~4.5 B params      │
        └──────────────────────┘      └────────────────────┘
                            │
        ┌───────────────────▼──────────────────────────────┐
        │  SQLite  data\knowledge\nusantara_knowledge.db    │
        │  65 documents · 722 chunks · 720 review events    │
        └───────────────────────────────────────────────────┘
```

| Listener | Process | Bind | External? |
|---|---|---:|---|
| 8000 | `uvicorn app.main:app` | 127.0.0.1 | no |
| 5180 | `vite` dev server | 127.0.0.1 | no |
| 11434 | Ollama | loopback | no |
| 8001 | **unrelated project** (`mcp-setup\pc_api_server.py`) | — | not Nusantara |
| — | IndoBERT worker | stdio | no socket |
| — | Tesseract / Docling | stdio | no socket |

**Every Nusantara listener is loopback-bound.** The product is not exposed to a network by default. This is why the shared admin token is an accepted risk rather than a critical one — and it is also why the product cannot be multi-tenant without an auth redesign.

---

## 3. Layers

| Layer | Package | Modules | Responsibility |
|---|---|---:|---|
| **Surface** | `app.api` | 8 | HTTP routes, request/response schemas, projection |
| **Orchestration** | `app.hermes` | 2 | `HermesAgent.run()` / `.execute_v1()` — 1,468 lines |
| **Domain** | `app.knowledge` | 43 | ingestion, chunking, embedding, retrieval, grounding, SOP review |
| | `app.research` | 12 | web evidence acquisition |
| | `app.language` | 13 | normalisation, intent |
| | `app.reasoning`, `app.problem`, `app.trust` | 13 | answer construction |
| **Governance** | `app.security` | 6 | `require_admin`, `V1KnowledgeBoundary` |
| | `app.approval` | 6 | runtime authorisation, approval state |
| | `app.policy` | 4 | policy evaluation |
| | `app.governance` | 4 | tool governance |
| **Providers** | `app.models` | 14 | Ollama primary, OpenAI-compatible, OpenRouter |
| **Platform** | `app.core` | 19 | identity, config, error taxonomy |
| | `app.observability` | 4 | logging, correlation context |
| | `app.memory`, `app.context` | 9 | session state |
| **Developer control** | `app.developer_core` | 29 | sandbox, gate, worker process |
| | `app.devcore` | 9 | control-plane projection |
| **Dead** | `app.v2` | 4 | complete engine, never registered |

**153 of 247 modules are leaves** — they import no other `app` module. Only three sit at dependency depth ≥ 10, and they are exactly the three entry points (`main`, `routes`, `control_plane`). The graph is shallow at the bottom and concentrated at the top, which is the shape you want.

---

## 4. The request path — browser to answer

```
POST /v1/chat
  │
  ├─ app.security.auth.require_admin ................ only if admin scope requested
  ├─ app.api.routes._check_rate_limit ............... 30 req / 60 s / session
  ├─ app.security.v1_knowledge.valid_chat_session ... ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$
  │
  ▼
app.hermes.agent.HermesAgent.execute_v1(request)     ← the only orchestrator
  │
  ├─ deterministic branches (no model call)
  │   ├─ arithmetic
  │   ├─ greeting / smalltalk
  │   └─ SOP field composition  ← requires fields.get('title')
  │
  ├─ app.knowledge.engine.KnowledgeEngine.search_knowledge()
  │   ├─ lexical scoring (TF-IDF-like: idf = 1/(1+tf*0.1), tf capped at 3)
  │   ├─ IndoBERT cosine (768-dim, 722/722 chunks embedded)
  │   ├─ hybrid blend
  │   └─ app.security.v1_knowledge.document_scope(filter)
  │
  ├─ provider dispatch  →  app.models.ollama  →  :11434
  │
  └─ app.security.v1_knowledge.V1KnowledgeBoundary.validate_response()
      ├─ grounded      → answer released
      └─ not grounded  → abstain, no evidence, requires_human = true
```

### 4.1 Why the deterministic branches matter

Greetings, arithmetic and SOP field lookups never touch a model. On a machine with a 4.5 B parameter model, this is the difference between an instant answer and a several-second wait — and, more importantly, between an answer that can be wrong and one that cannot.

Measured live:

```json
POST /v1/chat  {"user_input": "halo"}
→ 200
  "response": "Halo! Ada yang bisa saya bantu?",
  "provider_status": "local_rule",
  "grounding": {"enabled": true, "grounded": true, "reason": "deterministic_response"},
  "trust": {"supports_claim": false, "confidence": 0.0, "requires_human": true,
            "evidence_count": 0, "evidence_available": false},
  "evidence": []
```

`provider_status: local_rule` proves no model was called. `evidence: []` proves nothing was retrieved. `requires_human: true` proves the answer is not presented as fact.

---

## 5. The approval boundary — the one rule that cannot be relaxed

```
  ┌────────┐   ┌────────────┐   ┌──────────┐   ┌─────────┐   ┌──────────────────┐
  │ Upload │──►│ Processing │──►│  Review  │──►│ Approve │──►│ Knowledge Active │
  └────────┘   └────────────┘   └──────────┘   └─────────┘   └──────────────────┘
       │              │               │             │                  │
   operator        pipeline        operator      operator          retrieval
   (admin token)   (no approval    (reads the    (explicit         will now
                    implied)        original)     decision)         return it
```

| Property | Enforcement | Test |
|---|---|---|
| A document cannot reach retrieval without an approve decision | `SOPReview.decide` state machine | `test_sop_review.py` |
| The model cannot approve anything | no code path from `HermesAgent` to `SOPReview.decide` | `test_approval_boundary.py` |
| An unapproved document cannot be retrieved even if selected | `document_scope()` + boundary | `test_review_publication_v1.py` |
| A revoked document cannot be released from a stale replay | boundary re-validation at generation time | `test_review_replay_v1.py` |
| The legacy human-acceptance shortcut is refused | `reject_legacy_human_acceptance` | `test_approval_boundary.py` |
| Execution requires authorisation, and fails closed without it | `POST /execute-reviewed` → `AuthorizationError` | `test_runtime_authorization.py` |

**The approval flow was not modified in this audit.** No `app\` file was touched.

---

## 6. Data model

| Object | Count | Meaning |
|---|---:|---|
| documents | **65** | ingested SOPs and fixtures |
| chunks | **722** | retrieval units; **722/722 carry a 768-dim IndoBERT vector** |
| review events | **720** | immutable `sop_review_events` rows — the audit trail |
| approved SOPs | **44** | retrievable |
| database size | **52.75 MB** | `data\knowledge\nusantara_knowledge.db` (55,308,288 B) |
| DB integrity | `integrity_check ok` | verified |
| SHA-256 (C: and E:) | `9e3e0d7a…c407` | **byte-identical** across working copy and backup |

### 6.1 The corpus-consistency trap

`.env` sets `EMBEDDING_MODEL=local-hash`, but the database contains 722 chunks embedded with **IndoBERT 768-dim**. They are consistent only because ingestion used the IndoBERT bridge explicitly rather than the env default.

**A fresh ingest with the default environment would write `local-hash` vectors into the same table and produce a mixed-dimension corpus.** Recorded as R3 in `RUNTIME_MODULE_MAP.md`. It did not happen here; it is one operator mistake away.

---

## 7. Retrieval quality — measured

| Metric | Value | Source |
|---|---:|---|
| Recall@5 | **0.824** | `reports\search_eval_report.json` (160 queries) |
| MRR@10 | **0.6377** | same |
| Precision@1 | **0.55** | same |
| Median latency | 178.9 ms | same |
| p95 latency | 261.7 ms | same |
| Golden set, 40 questions | P@1 **0.40**, R@5 **0.625** | `reports\golden_set_retrieval_eval.json` |

Read honestly: **the right SOP is in the top 5 for 82.4 % of queries**, and ranks first just over half the time. The failure mode is confusion between 44 near-duplicate Dukcapil SOPs that share vocabulary — not absence of the document.

`Precision@5` is **retracted** as a metric: the implementation divides by `len(top5)` (results returned) rather than `k`, so 41 of 160 queries have a denominator below 5. See `AUDIT_HISTORY_RECONCILIATION.md` §2.4.

---

## 8. Provider abstraction

| Property | Value |
|---|---|
| Primary | Ollama `gemma3n:e2b-it-q4_K_M` (~4.5 B, Q4) |
| Module | `app.models.ollama` — **fan-out 8, fan-in 7**, the most central concrete module |
| Alternatives | OpenAI-compatible, OpenRouter (configured, not the default) |
| Selection | `POST /v1/control-plane/model-selection` |
| Binding | the model is bound **per request**; a mid-flight change cannot rebind the in-progress answer |

`app.models.ollama` is the natural seam if the provider ever needs to be swapped. Everything that talks to a model, and everything the model layer needs, passes through it.

### 8.1 The honest limitation

The shipping model is ~4.5 B parameters. It abstains rather than hallucinates on hard questions, and the Grounding Guard catches most of what it does produce — but its answer quality is the ceiling on the product, not the retrieval layer. `HERMES_FORENSIC_AUDIT.md` §4 records this. Raising it needs a 7 B+ model or internet access, neither of which is available in this environment.

---

## 9. Observability

| Signal | Implementation |
|---|---|
| Structured logging | `app.observability.logging` (fan-in 7) |
| Correlation context | `app.observability.context` (fan-in **10**) |
| Runtime identity | `app.core.runtime_identity` (fan-in **12** — most depended-on module) |
| Health | `GET /v1/health` → `{status, service, version, build_id}` |
| Service logs | `data\service-v1\` (1,133 run logs) |
| Review audit | `sop_review_events` — 720 immutable rows |
| Grounding telemetry | `NUSANTARA_EVIDENCE_SCORE_GATE input_count=… threshold=0.50` on each chat |

### 9.1 The observability gap

**`/metrics` does not exist.** Three tests assert it (`test_phase3_metrics_integration.py`) and fail with 404. `/v1/health` reports process liveness only — it returned `200 ok` while every `POST /v1/chat` returned `500` (finding S-R1). There is no readiness probe that exercises retrieval or generation.

---

## 10. Deployment

| Target | Artefact | Measured |
|---|---|---|
| Local | `start-nusantara.bat` | backend 8000 + frontend 5180 + Ollama |
| Container | `Dockerfile` | image `nusantara:v1-dist`, **2.48 GB**, `healthy` |
| Frontend bundle | `control-plane\dist\` | 446 modules, `index-Bg4-yd-G.js` 689.90 kB / 206.31 kB gzip |

Container composition:

```
python:3.12-slim                                   ~130 MB
  ├── pip install fastapi uvicorn … haystack-ai     (hardcoded, ignores pyproject.toml)
  ├── /opt/indobert venv: torch CPU + transformers  (largest layer)
  ├── /app/app, /app/docs, /app/scripts
  ├── /app/control-plane/dist                       5 files — verified inside the image
  └── user appuser (uid 10001), HEALTHCHECK scripts/healthcheck.py
```

**Not in the image:** Tesseract, Docling. OCR paths are available on the host only.

---

## 11. The five architectural debts, honestly stated

| # | Debt | Severity | Why it was not fixed |
|---|---|---|---|
| **D1** | `app\api\routes.py` — 1,686 lines, fan-out 34, god module | Medium | Refactor with no equivalence test |
| **D2** | `app\v2\` + `v2_routes.py` — complete dead engine, fan-out 23, never registered | High if shipped | 3 test modules import it |
| **D3** | 4 real import cycles + 1 self-import | Medium | Breaking one changes initialisation order on a live path |
| **D4** | Two parallel developer-core trees (`developer_core` 29 + `devcore` 9) | Medium | Both live; merging is a code change |
| **D5** | `runtime_authorization` imports endpoint functions from `api.control_plane` — layering inverted | Medium | Same reason |

### 11.1 The cycles, precisely

```
app.api.routes              ↔ app.api.knowledge_pipeline
app.api.routes              ↔ app.api.runtime_readiness
app.api.control_plane       ↔ app.approval.runtime_authorization
app.security.v1_knowledge   → app.knowledge.engine → app.skills.composition → back
app.exceptions              → app.exceptions            (self-import, no-op)
```

Four are late-bound (imports inside function bodies). The fourth is module-scope and works only because Python tolerates a partially-initialised module when the cyclic name is used later rather than at import time. It is exactly the shape that breaks under a reorder.

The fifth is a no-op: `register_exception_handlers()` imports seven names from its own module that are already globals. **One-line fix, documented, not applied** (`FILE_DEPENDENCY_MAP.md` §4.5).

---

## 12. Invariants — what must remain true

| Invariant | Enforced by | Status |
|---|---|---|
| Exactly one backend process serves the product | runtime inspection | **holds** — one listener on 8000 |
| No second engine | `test_v2_disabled.py` | **holds at runtime**; source tree still contains V2 |
| Only a human can approve | `SOPReview.decide` | **holds** |
| Revoked knowledge cannot be released | boundary re-validation | **holds** |
| Execution fails closed without authorisation | `AuthorizationError` | **holds** |
| Every listener is loopback-bound | bind configuration | **holds** |
| No secret in `app\` source | scan | **holds** |
| Audit history is immutable and retained | 720 `sop_review_events` rows | **holds** |
| Grounding Guard is enabled on every answer | boundary | **holds** — never disabled |
| The guard rejects every unsupported claim | boundary | **FAILS for negative claims** — 12 tests |

---

## 13. Verdict

| Criterion | Result |
|---|---|
| Architecture documented from evidence | **PASS** |
| Single engine, single backend | **PASS** |
| Approval flow intact and enforced | **PASS** |
| Import graph acyclic | **FAIL** — 4 cycles + 1 self-import |
| No dead engine in the tree | **FAIL** — `app\v2\` |
| Point-to-point coupling disciplined | **PASS** — 153 leaves, 3 entry modules at depth ≥ 10 |
| Retrieval quality measured | **PASS** — Recall@5 0.824 |
| Observability sufficient to detect failure | **FAIL** — no `/metrics`, health blind to chat |
| Deployment reproducible | **PARTIAL** — no Python lock, base image floats |
| Grounding Guard complete | **FAIL** — negative claims accepted |

**Architecture status: ACTIVE, SINGLE-ENGINE, WITH FIVE RECORDED DEBTS.** The product is one process doing one job, and the safety boundaries that matter — approval, revocation, execution, grounding — are enforced in code and covered by tests. The debts are structural, disclosed, and each has a stated precondition for removal.
