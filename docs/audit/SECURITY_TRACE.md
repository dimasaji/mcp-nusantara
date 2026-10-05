# SECURITY TRACE — NUSANTARA AI V1

Phase 11. NO source code changes. Read-only runtime trace via static analysis
of test coverage and direct inspection of call paths.

## Scope

Investigate 4 HIGH-severity mypy errors in `app/api/routes.py` flagged
during Phase 1.5 lint pass:

1. `app/api/routes.py:624` — `Name "logger" is not defined`
2. `app/api/routes.py:643` — `Name "logger" is not defined`
3. `app/api/routes.py:782` — `"ProblemEngine" has no attribute "analyze"`
4. `app/api/routes.py:1246` — `"ProblemEngine" has no attribute "analyze"`
5. `app/api/routes.py:1392-1398` — `KnowledgeSearchRequest.session_id`,
   `user_input`, `gate_context`, `model_status`, `latency_ms` not defined

## Findings (per item)

### F-S1. `logger` not defined (routes.py:624, 643)

**File context**: lines 624 and 643 are inside the body of
`_apply_grounding_safety_gate` (defined at line 591).

**Call-graph inspection**:

```
grep "_apply_grounding_safety_gate" app/api/routes.py
   → 1 match: definition at line 591. NO CALLERS.
grep "grounding_guard" app/api/routes.py
   → 4 matches: line 39 (init), 607 (fallback inside dead code),
                992 (direct call), 1043 (direct call).
```

`_apply_grounding_safety_gate()` is **defined and never invoked**. Active
paths use `_grounding_guard.validate(...)` directly at lines 992 and 1043.

**Verdict**: DEAD CODE (P7). `logger` NameError cannot fire on the current
runtime path. The function is also missing `logger = logging.getLogger(__name__)`
at module top — confirming dead status.

**Risk if revived**: HIGH. Reviving this function without adding
`logger = logging.getLogger(__name__)` would cause NameError when grounding
is unsupported.

**Action**: Either delete dead function OR add module-level `logger` when
revived. Recommend deletion in Phase 6.5 cleanup.

### F-S2. `ProblemEngine.analyze` AttributeError (routes.py:782, 1246)

**File context**:
- routes.py:782 — inside `chat()` (line 715), `agent.problem.analyze(...)`
- routes.py:1246 — inside `analyze_problem()` (line 1235), `engine.analyze(...)`
- ALSO: `app/hermes/agent.py:34` — `self.problem.analyze(...)` inside
  `HermesAgent.run(...)`

**Method presence check**:

```
grep "^\s*def " app/problem/engine.py
   → resolve(_infer_goal, _generate_goal_text, _generate_outcome,
     _generate_constraints, _generate_success_criteria, _build_missing,
     _generate_solutions, _select_solution)
   → NO `analyze` method defined.
```

`ProblemEngine` only has `resolve()`. `analyze()` does not exist.

**Test coverage check**:

- `tests/v2/test_devcore_routes.py` — uses `integration/routes_with_devcore.py`
  and `integration/routes_live_original.py`, **NOT** `app/api/routes.py`.
- `tests/evaluation/test_smoke.py` — calls only `/health` and module-level
  imports; does **NOT** invoke `/v1/chat`.
- 144 pytest pass without ever hitting `app/api/routes.py:715 chat()` or
  `app/api/routes.py:1235 analyze_problem()`.

**Verdict**: **HIGH (P0) latent runtime defect.** Production hit on either
endpoint will raise `AttributeError: 'ProblemEngine' object has no attribute
'analyze'` → 500 response. Test suite green gives **false confidence**.

**Minimum safe fix** (when approved):
- Replace `analyze(...)` with `resolve(...)` in:
  - `app/api/routes.py:782` (passing appropriate args from ChatRequest)
  - `app/api/routes.py:1246`
  - `app/hermes/agent.py:34`
- Verify `ProblemResolution` (return type of `resolve()`) is the expected
  shape for downstream consumers.
- Add regression test that exercises `/v1/chat` and `/v1/problem/analyze`
  end-to-end (with MockProvider).

### F-S3. `KnowledgeSearchRequest` missing attrs (routes.py:1392-1398)

**File context**: lines 1392-1398 reference
`request.session_id`, `request.user_input`, `gate_context`, `model_status`,
`latency_ms`.

**Schema check**:

```
grep -n "class KnowledgeSearchRequest" app/knowledge/schemas.py
   → NO RESULT
```

`KnowledgeSearchRequest` is **not defined** in `app/knowledge/schemas.py`.
The endpoint at line 1392 must be referencing a class that does not exist
in the canonical schema location.

Possible explanations (need confirmation at runtime):
- The endpoint was inlined with a local `BaseModel` definition elsewhere.
- The class is imported under a different name.
- The endpoint is broken (post-patch regression).

`gate_context`, `model_status`, `latency_ms` (lines 1394-1398) are not
imported module-level symbols in `routes.py` — they would raise NameError
when the endpoint body executes.

**Test coverage check**: this endpoint at line 1392 is also not exercised
by the 145-test suite (which only hits `/health`, devcore routes via
patched integration routes, and other module-level tests).

**Verdict**: **HIGH (P0) latent runtime defect.** Endpoint is broken at
multiple points: missing schema class, undefined request attributes,
undefined module-level variables.

**Action**: requires investigation of intent — was this endpoint intended
to exist? Does it have an alternative implementation? Options:
- Delete the broken endpoint (if unused).
- Repair the endpoint by defining `KnowledgeSearchRequest` with
  `session_id` and `user_input` fields, and importing/initializing
  `gate_context`, `model_status`, `latency_ms` correctly.
- Both options require a human decision on scope.

## Summary

| ID | Issue | Initial severity (mypy) | After trace | Status |
|----|---|---|---|---|
| F-S1 | `logger` undefined | HIGH | **DEAD CODE (P7)** | No runtime impact |
| F-S2 | `ProblemEngine.analyze` missing | HIGH | **HIGH (P0) latent defect** | Will 500 on /v1/chat and /v1/problem/analyze |
| F-S3 | `KnowledgeSearchRequest` missing schema + undefined symbols | HIGH | **HIGH (P0) latent defect** | Will NameError / AttributeError on /v1/knowledge endpoint |

## Decision Required

Per Master Developer §30 (HIGH-RISK APPROVAL GATE):

- **F-S2 fix** touches `app/api/routes.py`, `app/hermes/agent.py`, and
  `app/problem/engine.py` (return-type compatibility check). Public
  `/v1` API contract surface. Requires:
  - RISK: API behavior change (response shape from `resolve()` vs `analyze()`).
  - WHY: latent AttributeError on production.
  - FILES: `app/api/routes.py:782,1246`, `app/hermes/agent.py:34`.
  - EXPECTED IMPACT: /v1/chat + /v1/problem/analyze no longer 500.
  - ROLLBACK: revert diff.
  - RECOMMENDATION: minimal safe fix — replace `analyze(...)` with
    `resolve(...)` at the 3 sites after manual shape verification.

- **F-S3 fix** is bigger scope (possibly delete-vs-repair). Requires
  separate approval.

## Test Suite Gap

The 145-test suite **never exercises the real `app/api/routes.py`** live.
This is the root cause why 4 HIGH-severity mypy errors went undetected
despite "all tests pass." The /v1 endpoints may have been broken from a
recent patch without any regression test catching it.

Recommended: add a single integration test that calls
`TestClient(app).post("/v1/chat", json={"user_input": "halo", "session_id": "s1"})`
with a MockProvider to catch this class of regression.