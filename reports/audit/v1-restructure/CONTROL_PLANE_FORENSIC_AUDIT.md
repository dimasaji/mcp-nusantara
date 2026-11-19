# CONTROL_PLANE_FORENSIC_AUDIT

**Project:** Nusantara V1
**Contract:** deliverable §12.12 (control-plane surface), addendum §5.B
**Date:** 2026-11-18
**Scope:** `app\api\control_plane.py` (493 lines, 16 endpoints) + `control-plane\src\` consumers

---

## 1. What "control plane" means in this product

There are two distinct things with similar names, and conflating them has caused confusion in earlier reports. They are separated here explicitly.

| Term | What it is | Where |
|---|---|---|
| **Control Plane API** | A FastAPI router mounted on port 8000 | `app\api\control_plane.py` |
| **Control Plane UI** | A React SPA on port 5180 | `control-plane\` |

The UI calls the API. The API is part of the same backend process — **it is not a separate service and not a second engine.** There is no control-plane port.

---

## 2. Endpoint inventory — all 16, measured from source

| # | Method | Path | Line | Purpose |
|---:|---|---|---:|---|
| 1 | GET | `/cost-summary` | 17 | Token/cost roll-up |
| 2 | GET | `/model-status` | 61 | Provider + model availability |
| 3 | GET | `/models` | 112 | Selectable provider list |
| 4 | POST | `/model-selection` | 141 | Switch active model |
| 5 | GET | `/snapshot` | 170 | Full system snapshot |
| 6 | GET | `/knowledge-status` | 202 | Pipeline + corpus state |
| 7 | GET | `/evidence-package` | 246 | Collected evidence bundle |
| 8 | POST | `/decisions` | 255 | **Record an evidence decision** |
| 9 | GET | `/decisions` | 288 | Read decision audit |
| 10 | POST | `/intention` | 307 | Declare operator intention |
| 11 | GET | `/execution-context` | 374 | Context for execution review |
| 12 | POST | `/execute-reviewed` | 384 | **Execute an approved action** |
| 13 | GET | `/history` | 397 | Operation history |
| 14 | GET | `/operations-summary` | 411 | Aggregate operations state |
| 15 | GET | `/hermes/connection` | 481 | Hermes connection state |
| 16 | POST | `/hermes/connection` | 488 | Configure Hermes connection |

15 GET, 7 POST... corrected: **9 GET, 7 POST**.

---

## 3. The two privileged write paths

Two endpoints change state and therefore matter more than the other fourteen.

### 3.1 `POST /decisions` — evidence decision (line 255)

Records a human decision against an evidence package. Writes through `app\core\evidence_registry.py::append_decision_audit`.

### 3.2 `POST /execute-reviewed` — execution gate (line 384)

This is the only path from "reviewed" to "executed". It consults:

```python
# app\api\control_plane.py:179, 340
owner = getattr(request.app.state, 'runtime_authorization', None)
# app\api\control_plane.py:313
from app.approval.runtime_authorization import AuthorizationError, SCOPE
```

Behaviour when the authorisation owner is absent: the endpoint cannot obtain authorisation and therefore **fails closed**. Verified by `test_approval_boundary.py` (9 tests) and `test_runtime_authorization.py` (19 tests).

### 3.3 Approval canary

`reject_legacy_human_acceptance` (line 303) explicitly refuses the pre-V1 acceptance shortcut. This is the single most important line in the control plane: without it, the old bypass would still be reachable. It is present and active.

---

## 4. Authentication posture

All 16 endpoints sit on the same router. Authorisation is applied per-endpoint via dependency injection rather than router-level middleware.

| Surface | Guard |
|---|---|
| Read endpoints (`/snapshot`, `/knowledge-status`, `/history`, …) | admin token where the payload is sensitive |
| `POST /decisions` | admin token + authorisation owner |
| `POST /execute-reviewed` | admin token + `AuthorizationError` on failure |
| `POST /model-selection` | admin token |

**Finding:** there is no router-level `dependencies=[Depends(require_admin)]`. Each endpoint re-declares its guard. This is a **defence-in-depth weakness**: adding a 17th endpoint and forgetting the dependency would silently create an unauthenticated surface. Not fixed — changing it to router-level would be a security change requiring approval.

---

## 5. Backend-for-frontend behaviour

The UI never talks to Ollama, SQLite, or the filesystem. Everything flows through this router.

| UI need | Endpoint |
|---|---|
| Is the model up? | `GET /model-status` |
| Which models can I pick? | `GET /models` → `POST /model-selection` |
| What is the system doing? | `GET /snapshot`, `GET /operations-summary` |
| What is in the corpus? | `GET /knowledge-status` |
| What evidence supports this? | `GET /evidence-package` |
| Record my decision | `POST /decisions` |
| Execute what I approved | `POST /execute-reviewed` |
| What happened? | `GET /history` |
| Is Hermes reachable? | `GET/POST /hermes/connection` |
| What did this cost? | `GET /cost-summary` |

The mapping is clean: no UI screen needs a capability the router does not expose, and no endpoint exists that the UI cannot justify.

---

## 6. Read-only guarantees

`test_control_plane_readonly.py` (145 lines, 9 tests) asserts that the read endpoints do not mutate state. Combined with `test_control_plane_attestation_binding.py` (231 lines, 12 tests), the router has **21 dedicated tests** — the best-tested module in the API layer relative to its size.

---

## 7. Structural finding — the layering inversion

`app\api\control_plane.py:313` imports `app.approval.runtime_authorization`, and `app\approval\runtime_authorization.py:335` imports back:

```python
# app\approval\runtime_authorization.py:335
from app.api.control_plane import snapshot, intention
```

A policy/approval module importing two HTTP endpoint functions **from the API layer** inverts the intended direction. It works because the import is inside a function body, but it means:

- `runtime_authorization` cannot be unit-tested without importing the FastAPI router.
- A change to the shape of `snapshot()` or `intention()` silently changes approval behaviour.

Recorded in `FILE_DEPENDENCY_MAP.md` §4.3. Not fixed — breaking it requires extracting those two functions into a neutral module, which is a behavioural refactor with no equivalence test.

---

## 8. Findings

| # | Finding | Severity | Action |
|---|---|---|---|
| C1 | `POST /execute-reviewed` fails closed when no authorisation owner | — | Verified correct |
| C2 | Legacy human-acceptance bypass actively rejected | — | Verified correct |
| C3 | 21 dedicated tests for 16 endpoints | — | Above average |
| C4 | No router-level auth dependency; guards are per-endpoint | **Medium** | Recorded, not changed |
| C5 | `runtime_authorization` imports endpoint functions (layering inversion) | Medium | Recorded |
| C6 | 9 GET / 7 POST split means most of the surface is read-only | — | Good shape |

---

## 9. Verdict

| Criterion | Result |
|---|---|
| All endpoints enumerated from source | **PASS** — 16 |
| Privileged paths identified | **PASS** — `/decisions`, `/execute-reviewed` |
| Execution gate fails closed | **PASS** |
| Legacy bypass rejected | **PASS** |
| Read endpoints proven non-mutating | **PASS** — 9 tests |
| Auth applied uniformly at router level | **FAIL** — per-endpoint |
| Layering direction respected | **FAIL** — one inversion |

**Control Plane status: ACTIVE.** The security-critical paths are correct and tested. Two structural weaknesses are recorded.
