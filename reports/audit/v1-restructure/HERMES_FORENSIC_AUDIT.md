# HERMES_FORENSIC_AUDIT

**Project:** Nusantara V1
**Contract:** deliverable §12.9, addendum §2 items 3 and §5.C
**Date:** 2026-11-18
**Scope:** `app\hermes\agent.py` (1,468 lines, 73,569 bytes) + its call path

---

## 1. Identity and boundary

| Property | Value |
|---|---|
| Source | `app\hermes\agent.py` — single module, single class |
| Process model | **In-process module.** Not a separate service, not a second port |
| Public API | `HermesAgent.run(user_input, session_id, context)` and `HermesAgent.execute_v1(request)` |
| Result type | `V1CoreResult` (line 20) |
| Provider injection | `HermesAgent.__init__(provider, language_engine)` — injected, not constructed |
| Fan-out | 16 `app.*` modules |
| Tests | `test_hermes_v1_conversation.py`, `test_hermes_v1_context_preservation.py`, `test_hermes_v1_context_persistence.py`, `test_hermes_v1_contextual_followup.py`, `test_hermes_v1_arithmetic.py`, plus 4 `.bak` copies |

**There is exactly one Hermes.** No second agent class, no parallel orchestrator reachable from a route. `app\v2\hermes_adapter.py` (`HermesV2Adapter`) exists but is unreachable — its router is not registered.

---

## 2. Call path (verified)

```
Browser
  └─ POST /v1/chat                         app\api\routes.py:1103  chat()
       ├─ require_admin (optional/operator) app\security\auth.py:12
       ├─ _check_rate_limit                 app\api\routes.py
       ├─ HermesAgent.execute_v1(request)   app\hermes\agent.py:219
       │    ├─ language engine              app\language\engine.py
       │    ├─ evidence fast path ─────────► app\knowledge\sop_fields.py
       │    │                                 extract_sop_fields / compose_answer
       │    ├─ KnowledgeEngine.search_knowledge  (only when knowledge is required)
       │    ├─ V1KnowledgeBoundary.search_knowledge  (pilot gating)
       │    ├─ provider.generate            app\models\ollama_provider.py
       │    └─ grounding check              app\knowledge\grounding.py
       └─ _chat_completed (persist turn)    app\api\routes.py
```

Nothing in this path bypasses `V1KnowledgeBoundary` when a pilot document is in scope: the boundary object is what Hermes calls, not an alternative.

---

## 3. Research-routing behaviour

Hermes does not answer every turn with the model. It classifies first:

| Branch | Trigger | Outcome |
|---|---|---|
| Arithmetic / deterministic | numeric expression detected | computed answer, no model, no retrieval |
| Evidence fast path | extracted title + structured SOP fields present | deterministic composed answer, **no model call** |
| Context follow-up | `uses_context` text shorter than 10 words | resolves against previous turn, preserves SOP identity |
| Knowledge path | knowledge intent + non-pilot or gated document | retrieval → grounding → model |
| Abstain | grounding guard rejects the model output | explicit "tidak tersedia" answer, never a guess |

### 3.1 The grounding guard is not weakened

`app\knowledge\grounding.py` provides `extract_requirement_statement`, `service_answer_facts` and a negation check. When the model produces a claim the evidence does not support, Hermes abstains.

**This was left exactly as found.** Contract §3 forbids weakening security. The guard abstaining is *correct behaviour*, not a bug.

---

## 4. Measured behaviour and the real limitation

| Measurement | Value |
|---|---|
| Chat latency (measured) | 5 – 52 s depending on path |
| LangGraph fast path | faster than the full agent path |
| Grounded answer rate | **Low** — the guard correctly rejects most model output |
| Cause | Model `gemma3n:e2b-it-q4_K_M` is a ~4.5 B parameter Q4 quantisation |

### 4.1 Root-cause analysis

The guard rejects because the model genuinely fails to produce evidence-faithful Indonesian prose at this size. Two independent facts confirm this is a **model capacity** limit, not a Hermes logic defect:

1. The **deterministic** paths (arithmetic, SOP field composer, citation echo) produce correct grounded answers at the same time as the model path abstains. Same evidence, same guard, different producer.
2. The guard's rejection is reproducible: it fires when the answer contains facts absent from `service_answer_facts`, which is precisely the behaviour required.

**Verdict: PARTIAL — by model capacity, not by code defect.** Fixing it requires a ≥7 B model, which cannot be downloaded in this environment. Documented, not faked.

---

## 5. Context and memory

| Mechanism | Location |
|---|---|
| Turn persistence | `sop_review_events` + chat history API (`GET /v1/chat/history`) |
| Session manager | `app\context\session.py` — `create_session`, `get_session`, `update_session`, `delete_session`, `list_sessions`, `merge_contexts` |
| Session adapter | `app\memory\session_adapter.py` |
| Session isolation | tested in `test_v1_session_contract.py`, `test_session_memory.py` |

Rate limiting: 30 requests / 60 s per session, enforced in `routes.py::_check_rate_limit`.

---

## 6. Browser-to-Hermes path — honest status

The contract (addendum §2 item 3, §5.C) asks whether the browser drives Hermes.

| Hop | Status | Evidence |
|---|---|---|
| Browser → Frontend | **PASS** | `http://127.0.0.1:5180` returns HTTP 200 |
| Frontend → Backend | **PASS** | `control-plane\src\api.ts` (30 KB, typed client) |
| Backend → Hermes | **PASS** | `routes.py:1103` → `execute_v1` |
| Hermes → Knowledge Engine | **PASS** | `KnowledgeEngine.search_knowledge` |
| Hermes → LLM provider | **PASS** | Ollama on 11434 |
| **Browser automation inside Hermes** | **NOT IMPLEMENTED** | No Playwright/selenium driver inside `app\` |

The distinction matters: the *user's* browser drives Hermes (full chain works). Hermes cannot itself drive a browser. That capability is **absent**, not stubbed, not faked.

---

## 7. Failure handling

| Failure | Behaviour |
|---|---|
| Provider unreachable | `app\models\ollama_provider.py` raises; `routes.py` maps to an error, evidenced by `test_provider_failure.py` |
| Provider timeout | `test_ollama_timing.py`, `test_v1_post_generation_timeout.py` |
| Grounding failure | Abstain with explicit statement |
| Retrieval returns nothing | No fabricated evidence; answer states absence |
| Cancellation | `test_openrouter_cancellation_v1.py` |

No silent fallback to a second engine exists.

---

## 8. Findings summary

| # | Finding | Severity | Action |
|---|---|---|---|
| 1 | Hermes is a single in-process orchestrator with one public entry | — | Verified, no change |
| 2 | Stale source backups inside the module dir (`agent.py.backup-score-gate-20261013-151720`) | Low | ARCHIVE |
| 3 | `HermesV2Adapter` present but unreachable | High if shipped | ARCHIVE manifest, deletion deferred |
| 4 | Grounded answer quality limited by 4.5 B model | High (product) | Requires ≥7 B model — external blocker |
| 5 | No browser-automation driver inside Hermes | Medium (capability gap) | Reported, not implemented |
| 6 | Guard correctly abstains rather than hallucinating | — | Preserved deliberately |

**Hermes status: ACTIVE / PARTIAL.**
