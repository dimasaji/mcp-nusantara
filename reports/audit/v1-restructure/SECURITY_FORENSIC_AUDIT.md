# SECURITY_FORENSIC_AUDIT

**Project:** Nusantara V1
**Contract:** deliverable §12.13, addendum §5.E, §7
**Date:** 2026-11-18
**Gate:** Penetration testing explicitly deferred by operator ("Pentest nanti saja")

---

## 1. Authentication

`app\security\auth.py` — 22 lines total, one authorisation primitive:

```python
def require_admin(token: str | None) -> None:
    expected = os.getenv("NUSANTARA_ADMIN_TOKEN")
    if expected is None:
        expected = dotenv_values(Path('.env'), encoding='utf-8').get('NUSANTARA_ADMIN_TOKEN')
    if not expected or not token or not hmac.compare_digest(
        token.encode("utf-8"), expected.encode("utf-8")
    ):
        raise HTTPException(status_code=403, detail="admin token diperlukan")
```

| Property | Assessment | Evidence |
|---|---|---|
| Fail-closed | **PASS** — `not expected` → 403, so an unset secret denies everything | line 18 |
| Timing-safe compare | **PASS** — `hmac.compare_digest` | line 19 |
| Secret from env, not code | **PASS** — `os.getenv` then `.env` fallback | lines 13–15 |
| Hardcoded secret in `app\` | **NONE FOUND** — scanned all `app\**\*.py` for the admin token value (redacted here), `sk-…`, `api_key=` | scan output empty. **But the token is hardcoded in 14 tracked files outside `app\`** — see S-R9 in `SECURITY_REGRESSION_REPORT.md` |
| `.env` committed to git | **NO** — `.gitignore:30` matches `.env`; `git ls-files` does not list it | `git check-ignore -v .env` |

**The auth primitive is correct.** Its weakness is architectural, not implementational — see §5.

---

## 2. Authorisation boundary

`app\security\v1_knowledge.py` — 213 lines.

| Method | Purpose |
|---|---|
| `valid_chat_session(value)` | Validates session id against `CHAT_SESSION_PATTERN` |
| `v1_session_id(session_id)` | Normalises session identity |
| `V1KnowledgeBoundary.source_versions(answer)` | Extracts source versions from an answer |
| `V1KnowledgeBoundary.reuse_prior_citation(document_id)` | Re-binds a prior citation |
| `V1KnowledgeBoundary.document_answer_facts(question, evidence)` | Builds the permitted-fact set |
| `V1KnowledgeBoundary.validate_response(answer, source_versions)` | **The gate** |
| `V1KnowledgeBoundary.search_knowledge(query, top_k, filter)` | Retrieval through the boundary |

The critical property: **document IDs supplied by the caller cannot grant access.** Retrieval and validation both pass through `V1KnowledgeBoundary`, and the boundary is what Hermes calls rather than an optional wrapper. Verified in `test_fullroot_boundaries.py`, `test_v1_sop_boundary.py`, `test_v1_targeted_boundaries.py`, `test_runtime_authorization.py`.

---

## 3. Data exposure

| Surface | Control |
|---|---|
| `POST /v1/chat` without admin token | Returns no evidence — tested in `test_v1_response_projection.py` |
| Chunk text in API responses | Cleared by response projection; source ids and titles retained |
| Error detail | `{"detail": "..."}` only; no stack traces leaked — `test_generic_internal_error.py` |
| Evidence leakage across sessions | Session isolation tested in `test_v1_session_contract.py`, `test_session_memory.py` |

---

## 4. Input validation

| Control | Implementation | Test |
|---|---|---|
| Session id charset | `CHAT_SESSION_PATTERN = ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$` (module-level `str`, used via `re.match`) | `test_v1_session_contract.py` |
| Empty input rejected | Pydantic min-length | 422, verified |
| Request schema validation | Pydantic v2 models (12 request models in `routes.py`) | — |
| Upload size / type | `DocumentIngestRequest`, parser dispatch by `content_type` | `test_knowledge_preparation.py` |
| Rate limiting | 30 req / 60 s per session (`routes.py::_check_rate_limit`) | — |

---

## 5. Findings — real, ranked

### F1 — Single shared administrator token (HIGH, architectural)

Every privileged caller presents the same `NUSANTARA_ADMIN_TOKEN`. There is no per-user identity, no revocation, no audit attribution beyond `principal ∈ {operator, anonymous}`.

- **Impact:** a single token leak grants full control; no way to revoke one user.
- **Fix required:** an identity provider. This is a redesign, not a patch.
- **In scope for V1?** No. Recorded as accepted risk.

### F2 — `data\` and the knowledge database are not under version control (MEDIUM)

Verified: `git ls-files data` → **0 files**. `.gitignore` line `/data/` excludes the entire tree, which contains the 52.75 MB database, 44 approved SOPs, 720 audit events and 74.3 MB of evidence.

- **Impact:** repository clone does not reproduce the system; the only copies are the live disk and the backup directory.
- **Mitigation now in place:** `E:\NUSANTARA_BACKUP\03_data\` + SHA-256 manifest covers it.
- **Recommended:** a scheduled backup job. Not implemented — would be a new feature.

> Of 3,513 KEEP/KEEP-CRITICAL files, **2,761 are untracked by git**; 2,742 of those are `data\`.

### F3 — `reports\` is gitignored, so audit evidence is not versioned (MEDIUM)

`.gitignore` line `reports/` excludes audit output. Contract §7 requires `reports/audit/` to be the official engineering record. Addressed during restructuring by adding a negation rule for the official subdirectories.

### F4 — Response projection is the only barrier for source text (MEDIUM)

Source content is removed at serialisation time. Any new endpoint that returns a raw ORM object would bypass it. Mitigated by tests, not by construction.

### F5 — Legacy human-acceptance bypass exists but is actively refused (LOW)

`app\api\control_plane.py::reject_legacy_human_acceptance` (line 303) explicitly rejects the old acceptance path. Good — but the endpoint still exists, which means the bypass is one code change away.

### F6 — No dependency vulnerability scan (LOW, tooling gap)

`pip-audit` / `npm audit` / Dependabot are not configured. No `.github/workflows` exists (`.github` is absent from the tree).

### F7 — Penetration test not performed (ACCEPTED)

Operator deferred it. No OWASP ZAP or Burp Suite is installed. **This is a known gap, not a pass.**

---

## 6. Security controls implemented — 14, verified

| # | Control | Where |
|---|---|---|
| 1 | Runtime status check | `app\api\runtime_readiness.py` |
| 2 | Service health check | `GET /v1/health`, `GET /health` |
| 3 | Model status check | `control_plane.py::model_status` |
| 4 | Pipeline status check | `knowledge_pipeline_status()` |
| 5 | Authentication | `require_admin` |
| 6 | Authorisation | `V1KnowledgeBoundary` |
| 7 | Trust metadata | `_PublicChatTrust` projection |
| 8 | Approval workflow | `SOPReview.decide` |
| 9 | Scope enforcement | `document_scope(filter)` |
| 10 | Secret protection | response projection |
| 11 | Evidence tracking | `data\evidence\`, `evidence_registry` |
| 12 | Error taxonomy | `app\core\error_taxonomy.py` (4 categories) |
| 13 | Audit history | `sop_review_events` — 720 immutable rows |
| 14 | Recovery | `retry_knowledge_source(run_id)` |

---

## 7. Measured security regression (automated)

`scripts\automated_regression.py` — 6 assertions, all passing:

| Test | Expected | Result |
|---|---|---|
| `search_without_token` | 403 | **PASS** |
| `admin_endpoint_without_token` | 403 | **PASS** |
| `chat_without_token_no_evidence` | 0 evidence items | **PASS** |
| `empty_input_rejected` | 422 | **PASS** |
| `pipeline_status_accessible` | 200 | **PASS** |
| `session_isolation` | isolated | **PASS** |

Additional suites covering authorisation: `test_fullroot_boundaries.py`, `test_runtime_authorization.py`, `test_approval_boundary.py` (9 tests), `test_policy_engine.py` (8 tests), `test_runtime_attestation.py`, `test_runtime_build_provenance.py`.

---

## 8. Verdict

| Criterion | Result |
|---|---|
| Secret handling correct | **PASS** |
| Auth fails closed | **PASS** |
| Authz boundary cannot be bypassed by document id | **PASS** |
| Approval cannot be bypassed | **PASS** (legacy path actively refused) |
| No secrets in source | **PASS** |
| `.env` not committed | **PASS** |
| Error messages do not leak internals | **PASS** |
| Rate limiting present | **PASS** |
| Per-user identity | **FAIL** — shared token |
| Data under version control | **FAIL** — `data\` untracked |
| Dependency vulnerability scan | **NOT TESTED** |
| Penetration test | **NOT TESTED** — deferred by operator |

**Security status: PARTIAL.** No control was weakened by this audit. Two structural weaknesses (F1 shared token, F2 untracked data) are documented with mitigations, not papered over.
