# SECURITY_REGRESSION_REPORT

**Project:** Nusantara V1
**Contract:** addendum §5.E, §7; companion to `SECURITY_FORENSIC_AUDIT.md`
**Date:** 2026-11-18
**Scope:** re-verify every security property established in the forensic audit, **after** the changes made in this restructuring pass
**Penetration test:** deferred by the operator ("Pentest nanti saja") — **not performed, not claimed**

---

## 1. Purpose

`SECURITY_FORENSIC_AUDIT.md` established what the controls are. This report answers a narrower and harder question:

> After the edits made in this audit, does every security property still hold — and is there any property whose *test* was silently disabled?

That second clause matters. This audit modified two test modules. A reviewer is entitled to ask whether that reduced security coverage. §4 answers it assertion by assertion.

---

## 2. What changed that could possibly affect security

| Change | Security-relevant? | Argument |
|---|---|---|
| `control-plane/src/sop-review.tsx` — optional `onChanged` prop | **No** | UI callback only; no request, header or authorisation logic touched |
| `Dockerfile` — `COPY control-plane/dist` | **No** | Adds static assets; does not change the running server |
| `.gitignore` — `reports/*` + `!reports/audit/` | **Additive only** | Makes evidence committable; matches no secret path (`.env`, `*.pem`, `*.key` rules untouched) |
| `pyproject.toml` — version, description, 2 pins | **No runtime effect** | Metadata. Nothing was installed, upgraded or downgraded |
| `tests/test_v1_sop_boundary.py` — carry the rate limiter into the compiled namespace | **Increases coverage** | The compiled `chat()` now calls the **real** `_check_rate_limit`, which previously could not execute at all |
| `tests/test_evidence_runner_guards.py` — precondition skip | **Relocates coverage** | The 9 guard tests now run only through `run_evidence_tests_isolated.py`, where 7 of 9 pass and 2 fail honestly |

**Zero files under `app\` were modified.** Every security control in the product is byte-identical to the state the forensic audit examined.

---

## 3. Live security assertions — the gate that matters

`scripts/automated_regression.py` exercises six security properties against the running backend.

| # | Assertion | Property being proven | Result |
|---|---|---|---|
| 1 | `security_search_no_token` | `POST /v1/knowledge/search` without a token → **403** | **PASS** |
| 2 | `security_admin_no_token` | `GET /v1/knowledge/pipeline/status` without a token → **403** | **PASS** |
| 3 | `security_chat_no_token_no_evidence` | anonymous `POST /v1/chat` returns **0 evidence items** | **PASS** |
| 4 | `empty_input_rejected` | empty `user_input` → **422** | **PASS** |
| 5 | `pipeline_status_accessible` | admin token grants access | **PASS** |
| 6 | `session_isolation` | two sessions never see each other's data | **PASS** |

```
=== AUTOMATED REGRESSION: 6/6 PASS ===
```

### 3.1 First run was 4/6 — and that is the more interesting result

The first execution returned **4/6**, with assertions 3 and 6 failing on `HTTP 500` from `POST /v1/chat`. An initial reading might be "this audit broke chat". It did not.

| Probe | Result |
|---|---|
| `GET /v1/health` on the degraded process | **200** `{"status":"ok"}` |
| `POST /v1/chat` on the degraded process, anon | **500** |
| `POST /v1/chat` on the degraded process, admin | **500** |
| Same request, fresh in-process `TestClient` | **200** |
| Same request after restarting the process | **200** |

**This is a fail-open in the health signal, not a fail-open in security.** The process answered 500 — it refused to serve, which is the safe direction. But `/v1/health` continued to report `ok` while the product could not answer a single question.

Recorded as finding **S-R1 (HIGH)** in §6. It is an availability blind spot with a security consequence: an operator watching only the health endpoint would not know the service was unusable, and a supervisor restarting only on health failure would never fire.

After restart: **6/6**. Recovery is operational. No code was changed to obtain the pass.

---

## 4. Did the test edits reduce security coverage?

This is the question a careful reviewer must ask. Answered per module.

### 4.1 `test_v1_sop_boundary.py` — coverage **increased**

| | Before the edit | After the edit |
|---|---|---|
| Tests that executed | 8 of 19 | **19 of 19** |
| `chat()` body executed | partially — died at the rate-limiter call | **fully** |
| `_check_rate_limit` under test | never | **for real, with real module state** |
| Assertions removed | — | **none** |
| Assertions weakened | — | **none** |

The 11 tests that previously could not run were the boundary assertions: `test_public_unscoped_chat_never_enters_restricted_retrieval`, `test_external_public_chat_never_retrieves_internal_evidence`, `test_operator_and_public_history_have_separate_security_namespaces`, `test_stream_failure_does_not_reveal_internal_exception`, `test_actual_http_boundary_denies_public_document_scope_before_lookup`, and six others. **These are the security assertions.** They now execute.

`19 passed`.

### 4.2 `test_evidence_runner_guards.py` — coverage **relocated, and previously fictional**

| | Before | After |
|---|---|---|
| Under plain `pytest` | 9 failures, all `AttributeError` — **zero assertions actually evaluated** | 9 skips with a stated reason |
| Under `run_evidence_tests_isolated.py` | — | **66 passed, 2 failed** |
| Real guards under test | 0 | **7 of 9** |

The 9 tests were never passing. They were failing at the first line because `runner = sys.modules["__main__"]` did not resolve to the runner. The skip does not remove coverage that existed — it removes 9 phantom failures and points the reader at the entry point where the coverage is real.

**Two guards genuinely fail** through that entry point:

```
FAILED tests\test_evidence_runner_guards.py::test_output_descriptor_and_pytest_style_duplicate_are_allowed
FAILED tests\test_evidence_runner_guards.py::test_descriptor_number_reuse_does_not_retain_authorization
```

Recorded as **S-R2 (MEDIUM)** — the descriptor-authorisation guard does not retain/release file-descriptor authorisation exactly as specified. This is a real, reproducible guard defect that was previously invisible because the whole module was drowned in 9 spurious failures.

### 4.3 Net coverage statement

| Control area | Coverage before this audit | After |
|---|---|---|
| V1 knowledge boundary (11 assertions) | **not executing** | **executing, passing** |
| Evidence file guards | 9 phantom failures | 7 passing, **2 real failures surfaced** |
| Core security gate (63 tests) | passing | passing |
| Live security assertions | 4/6 (degraded process) | **6/6** |

**Coverage went up.** Two real defects were uncovered by making the tests executable again.

---

## 5. The 14 controls — re-verified as unmodified

Every control listed in `SECURITY_FORENSIC_AUDIT.md` §6 lives in `app\`. No `app\` file was touched, so all 14 are byte-identical. Spot-checked at runtime where a live path exists:

| # | Control | Runtime evidence in this pass |
|---|---|---|
| 1 | Runtime status check | `runtime_readiness` router mounted, reachable |
| 2 | Service health check | `GET /v1/health` → 200 |
| 3 | Model status check | reachable via control-plane router |
| 4 | Pipeline status check | 403 without token, 200 with — **verified live** |
| 5 | Authentication `require_admin` | 403 on two endpoints — **verified live** |
| 6 | Authorisation `V1KnowledgeBoundary` | 11 boundary tests now execute and pass |
| 7 | Trust metadata projection | anonymous chat returns `trust.requires_human: true`, `evidence_available: false` — **verified live** |
| 8 | Approval workflow `SOPReview.decide` | core gate 63/63 |
| 9 | Scope enforcement `document_scope(filter)` | boundary tests |
| 10 | Secret protection (response projection) | anonymous chat returns `evidence: []` — **verified live** |
| 11 | Evidence tracking | `data\evidence\`, registry |
| 12 | Error taxonomy | `{"detail": "Terjadi kesalahan internal server"}` — **no stack trace leaked** on the 500 observed in §3.1 |
| 13 | Audit history | 720 immutable `sop_review_events` rows, unchanged |
| 14 | Recovery `retry_knowledge_source` | untouched |

> Control 12 is worth noting: the 500 in §3.1 returned `{"detail":"Terjadi kesalahan internal server"}` with no traceback, no file path and no exception class. The failure leaked nothing.

---

## 6. Findings

| # | Finding | Severity | Status |
|---|---|---|---|
| **S-R1** | `/v1/health` returns `ok` while `POST /v1/chat` returns 500 on every request. Health does not exercise the chat path | **HIGH** | **Recorded.** Restart clears it. No code changed |
| **S-R2** | Evidence runner descriptor guard fails 2 of 9 checks when run through its real entry point (`test_output_descriptor_and_pytest_style_duplicate_are_allowed`, `test_descriptor_number_reuse_does_not_retain_authorization`) | **MEDIUM** | **Recorded.** Newly visible because the module now executes |
| **S-R3** | Grounding Guard accepts unproven *negative* claims — 12 tests assert it must not | **HIGH** | **Recorded** in `TEST_RUNTIME_AUDIT.md` §4.3. Fix requires approval |
| S-R4 | No router-level auth dependency; guards are per-endpoint | Medium | Unchanged from forensic audit |
| S-R5 | Shared admin token, no per-user identity | Medium | Unchanged; mitigations in `SECURITY_FORENSIC_AUDIT.md` |
| S-R6 | 1 high + 1 moderate npm advisory, patch available | HIGH | Unchanged; `npm audit fix` withheld pending approval |
| S-R7 | Python CVE scan not performed (`pip-audit` absent) | **NOT TESTED** | No claim made |
| S-R8 | Penetration test deferred by operator | **NOT PERFORMED** | No claim made |
| S-R9 | The shared admin token is hardcoded in **14 tracked files** outside `app\` (`scripts\`, `tests\`, `app\ui\index.html`, root test scripts) | **HIGH** | **Recorded, not fixed.** Pre-existing; rotating the token now would break those scripts. Filed under A6-adjacent work — needs a coordinated rotation plus a `.env`-only read path |

---

## 7. What this report does **not** claim

| Claim | Status |
|---|---|
| Penetration tested | **NO** — operator deferred |
| OWASP Top 10 coverage | **NO** — no scanner run |
| Python dependency CVEs absent | **NO** — `pip-audit` not installed |
| npm advisories fixed | **NO** — withheld for approval |
| Multi-user isolation proven under load | **NO** — single-operator assumption |
| Linux hardening verified | **NO** — Windows only |
| Container hardened against escape | **NO** — not tested |
| TLS / transport security | **NO** — loopback-only deployment, no TLS |

---

## 8. Verdict

| Criterion | Result |
|---|---|
| Auth primitive unmodified and correct | **PASS** |
| Authorisation boundary tests execute and pass | **PASS** — was 8/19, now 19/19 |
| Anonymous chat leaks no evidence | **PASS** — verified live |
| Admin endpoints deny without token | **PASS** — 403 verified live |
| Session isolation holds | **PASS** — verified live |
| No stack trace leaks on 500 | **PASS** — verified during S-R1 |
| Evidence file guards | **PARTIAL** — 7/9, two real failures |
| Grounding guard rejects unproven absence claims | **FAIL** — 12 tests |
| Health signal reflects service usability | **FAIL** — S-R1 |
| No security coverage removed by this audit | **PASS** — coverage increased |
| Dependency security | **FAIL** — 2 npm advisories open, Python untested |
| Penetration tested | **NOT PERFORMED** |

**Security regression status: NO REGRESSION, THREE OPEN DEFECTS DISCLOSED.** Every control the product had before this audit it still has. Four new facts were established — one availability blind spot, two guard-level defects — and none of them were introduced here.
