# FILE_DEPENDENCY_MAP

**Project:** Nusantara V1
**Contract:** deliverable §12.5
**Date:** 2026-11-18
**Method:** AST parse of every `app\*.py` module; only `app.*` → `app.*` edges retained
**Machine-readable output:** `MODULE_GRAPH_EDGES.csv` (302 edges)

---

## 1. What this map covers and what it does not

This document maps **intra-application Python import dependencies** — which module inside `app\` imports which other module inside `app\`.

| Dependency class | Covered here | Where it is covered instead |
|---|---|---|
| `app.*` → `app.*` imports | **Yes, exhaustively** | this document |
| `app.*` → third-party Python packages | No | `DEPENDENCY_AUDIT.md` |
| Frontend module → module | No | `FRONTEND_FORENSIC_AUDIT.md` |
| Frontend → backend HTTP calls | No | `CONTROL_PLANE_FORENSIC_AUDIT.md` |
| Runtime process → process | No | `RUNTIME_MODULE_MAP.md` |
| Data file → consumer | No | `DATABASE_SOP_FORENSIC_AUDIT.md` |

---

## 2. Scale

| Metric | Value |
|---|---:|
| Python modules under `app\` | **247** |
| Modules participating in an intra-app edge | **94** |
| Distinct import edges | **302** |
| Cycles | **4 real + 1 self-import** |
| Max dependency depth from a leaf | **12** (`app.main`) |

153 of the 247 modules are leaves (depth 0) — they import no other `app` module. That is a healthy shape: most modules are utilities, not orchestrators.

### 2.1 Depth distribution

| Depth | Modules | Reading |
|---:|---:|---|
| 0 | 153 | Leaves — models, helpers, constants |
| 1 | 32 | One level above a leaf |
| 2 | 22 | |
| 3 | 5 | |
| 4 | 11 | |
| 5 | 11 | |
| 6 | 5 | |
| 7 | 2 | `app.security.v1_knowledge`, `app.devcore` |
| 8 | 2 | `app.api.knowledge_pipeline`, `app.api.v2_routes` |
| 9 | 1 | `app.api.skills` |
| 10 | 1 | `app.api.routes` |
| 11 | 1 | `app.api.control_plane` |
| 12 | 1 | `app.main` |

The graph is shallow at the bottom and concentrated at the top. Only **3 modules** sit at depth ≥ 10, and they are exactly the three expected entry points (`main`, `routes`, `control_plane`).

---

## 3. Highest fan-out — modules that pull in the most of the system

| Rank | Module | Fan-out | Assessment |
|---:|---|---:|---|
| 1 | `app.api.routes` | 34 | **God module.** 1,686 lines. Declared debt, not refactored |
| 2 | `app.api.v2_routes` | 23 | **Dead** — router never registered |
| 3 | `app.hermes.agent` | 16 | Hermes orchestrator by design |
| 4 | `app.api.control_plane` | 12 | 16 endpoints, 493 lines |
| 5 | `app.main` | 11 | App assembly — expected |
| 6 | `app.devcore.core` | 9 | Developer core |
| 7 | `app.models.ollama` | 8 | Provider adapter |
| 8 | `app.api.knowledge_pipeline` | 7 | Pipeline API |
| 9 | `app.knowledge.rag` | 7 | Retrieval core |
| 10 | `app.api.runtime_readiness` | 6 | Readiness probes |

`app.api.v2_routes` at fan-out 23 while being unreachable is the clearest structural anomaly in the graph: a fully-wired parallel stack with no entry point.

---

## 4. Cycles — measured, all five recorded

Cycle detection was run with a three-colour DFS over all 302 resolved edges.

### 4.1 Cycle 1 — `routes` ↔ `knowledge_pipeline` (real, late-bound)

```
app.api.routes
  → app.api.knowledge_pipeline      routes.py:16   from app.api.knowledge_pipeline import create_knowledge_pipeline_router
  → app.api.routes                  knowledge_pipeline.py:43  from app.api.routes import _knowledge
                                    knowledge_pipeline.py:48  from app.api.routes import _gate_integration
```

The return edge is inside a function body, so it resolves at call time, not import time. Works, but it means `knowledge_pipeline` cannot be imported or tested without `routes` being importable, and `routes` reaches back into a module that reaches back into `routes`. Fragile.

### 4.2 Cycle 2 — `routes` ↔ `runtime_readiness` (real, late-bound)

```
app.api.routes
  → app.api.runtime_readiness       routes.py:18, 1533
  → app.api.routes                  runtime_readiness.py:27   from app.api.routes import _knowledge
```

Same pattern: the readiness router is mounted inside `routes`, and the readiness module reaches back for the shared `_knowledge` singleton.

### 4.3 Cycle 3 — `control_plane` ↔ `runtime_authorization` (real, late-bound)

```
app.api.control_plane
  → app.approval.runtime_authorization   control_plane.py:313
  → app.api.control_plane                runtime_authorization.py:335  from app.api.control_plane import snapshot, intention
```

`runtime_authorization` imports `snapshot` and `intention` **from the API module** — a policy layer depending on an HTTP layer. This is the most questionable cycle in the set: the dependency direction is inverted relative to the layering.

### 4.4 Cycle 4 — `v1_knowledge` → `engine` → `composition` → `v1_knowledge` (real, module-level)

```
app.security.v1_knowledge
  → app.knowledge.engine            v1_knowledge.py:159  from app.knowledge.engine import KnowledgeEngine
  → app.skills.composition          (engine imports composition)
  → app.security.v1_knowledge       composition.py:85    from app.security.v1_knowledge import V1KnowledgeBoundary
```

This is the only cycle closed at **module scope**. It imports successfully because Python tolerates a partially-initialised module as long as the cyclic name is only *used* later, not at import time. It works today; it is exactly the shape that breaks under reordering or circular-initialisation refactors.

### 4.5 Cycle 5 — `app.exceptions` → `app.exceptions` (self-import, harmless)

```python
# app\exceptions.py:57-62
def register_exception_handlers(app):
    """Register exception handlers."""
    from app.exceptions import (
        AppException, ValidationError, NotFoundError,
        NotAuthorizedError, ConflictError, InternalError, ProviderUnavailableError,
    )
```

A function inside `app\exceptions.py` imports from `app\exceptions.py`. Every one of those names is already a module global at that point, so the statement is a **no-op**. It is not a runtime defect; it is noise.

**Recommended one-line fix** (not applied — see §7): delete lines 59–62.

### 4.6 Why the cycles were not removed

Contract §3 forbids business-logic changes without explicit approval. Breaking a cycle requires moving a shared singleton (`_knowledge`) to a neutral module, which changes initialisation order — a real behavioural change on a live request path with no equivalence test. **Recorded as debt; not acted on.**

---

## 5. Highest fan-in — the spine

| Rank | Module | Fan-in | Role |
|---:|---|---:|---|
| 1 | `app.core.runtime_identity` | 12 | Build/commit identity — every layer stamps it |
| 2 | `app.observability.context` | 10 | Correlation context |
| 3 | `app.core.nusantara_config` | 8 | Settings |
| 4 | `app.governance.tools` | 8 | Tool governance |
| 5 | `app.models.ollama` | 7 | Provider |
| 6 | `app.security.auth` | 7 | `require_admin` |
| 7 | `app.observability.logging` | 7 | Structured logging |
| 8 | `app.models.base` | 7 | Provider protocol |
| 9 | `app.core.config` | 6 | Config primitives |
| 10 | `app.knowledge.sop_review` | 6 | Review state machine |

**This is the right shape.** The most depended-upon modules are identity, observability, config, security and the provider protocol — cross-cutting primitives. No business-logic module is imported by a large fraction of the system, which means the coupling is concentrated where coupling is cheap.

`app.models.ollama` sits in both top-10 lists (fan-out 8, fan-in 7). It is the single most central *concrete* module: everything that needs to talk to a model, and everything the model layer needs, passes through it. That makes it the natural seam for a provider abstraction if one is ever needed.

---

## 6. Package-level coupling

| From | To | Edges |
|---|---|---:|
| `api` | `core` | 15 |
| `api` | `models` | 11 |
| `api` | `knowledge` | 11 |
| `api` | `security` | 9 |
| `hermes` | `knowledge` | 6 |
| `models` | `core` | 6 |
| `api` | `research` | 5 |
| `api` | `v2` | 4 |
| `approval` | `observability` | 4 |
| `experience` | `observability` | 4 |
| `knowledge` | `core` | 4 |
| `main` | `api` | 4 |

Reading: `api` is the only package with wide outgoing coupling, which is what an API layer is for. The domain packages (`knowledge`, `hermes`, `models`, `approval`, `security`) depend mostly on `core` and `observability`, not on each other. **There is no cross-domain tangle.** The one exception is `api → v2` (4 edges) — dead code pulling the API layer toward an unregistered stack.

---

## 7. Findings

| # | Finding | Severity | Action |
|---|---|---|---|
| D1 | `app.api.routes` fan-out 34 | Medium | Debt, recorded. Not split |
| D2 | `app.api.v2_routes` fan-out 23 with no registration | High if shipped | ARCHIVE manifest |
| D3 | Cycle `routes ↔ knowledge_pipeline` | Medium | Recorded |
| D4 | Cycle `routes ↔ runtime_readiness` | Medium | Recorded |
| D5 | Cycle `control_plane ↔ runtime_authorization` (layering inverted) | Medium | Recorded |
| D6 | Module-scope cycle `v1_knowledge → engine → composition → v1_knowledge` | Medium | Recorded |
| D7 | `app.exceptions` self-import (no-op) | Low | One-line fix documented, not applied |
| D8 | 153 leaf modules, 3 entry modules at depth ≥ 10 | — | Healthy |

---

## 8. Reproducing this map

```powershell
.venv\Scripts\python.exe .audit_tmp\nusa_facts.py        # regenerates MODULE_GRAPH_EDGES.csv
.venv\Scripts\python.exe .audit_tmp\graph_analysis.py    # cycles, depth, package coupling
```

Both scripts are read-only AST parsers. Neither imports the application, so neither can trigger side effects.
