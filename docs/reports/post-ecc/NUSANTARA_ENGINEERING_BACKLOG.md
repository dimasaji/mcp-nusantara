# Nusantara Engineering Backlog

Contract: `NUS-V1-POST-ECC-001`

Prioritization basis: risk and impact on V1/SOP Knowledge, not finding count.

Date: 2026-11-22

## 1. Top five actionable priorities

1. `ENG-P0-01` — Restore the IndoBERT worker so HTTP Knowledge ingest/search can run.
2. `ENG-P0-02` — Provide an approved Ollama/model runtime or an explicit unsupported-mode contract.
3. `ENG-P0-03` — Resolve R2/Windows/checksum/archive evidence blockers.
4. `ENG-P0-04` — Continue full-regression triage toward a green or explicitly baselined V1 suite.
5. `ENG-P1-01` — Normalize NBSP/NUL in OCR-derived text and fix the four ingestion tests.

No item in this backlog asks for a new service, architecture rewrite, or Nusantara V2.

## 2. P0 — Critical

| Task ID | ECC ref | Component | Root cause | Minimal fix | Acceptance criteria | Tests | Complexity | Dependencies |
|---|---|---|---|---|---|---|---|---|
| ENG-P0-01 | PF-07 | Knowledge / IndoBERT worker | `nusantara-models/.venv/bin/python` missing; HTTP knowledge path blocked | Provision the expected worker environment or update the configured worker path through an approved config change | Worker executable exists; synthetic ingest/search via HTTP returns evidence; no production data mutated | `tests/test_synthetic_rag_fixture.py`, HTTP knowledge smoke with temp DB | M | Approved runtime provisioning |
| ENG-P0-02 | PF-08, PF-27 | LLM / Ollama | No Ollama binary/service; `/v1/chat` cannot be verified with a real model | Provide approved local model runtime, or keep an explicit documented `503/unsupported` contract rather than implying success | `health_check()` reports available model; one SOP chat E2E returns grounded answer and citation; otherwise explicit unsupported behavior is asserted | `tests/test_backend_runtime_fixture.py`, selected `tests/test_v1_service_dialogue.py` E2E path | L | Model approval, resources |
| ENG-P0-03 | PF-11, PF-12, PF-13, PF-14 | Release evidence / Control Plane | Missing R2 acceptance, checksum mismatch, missing archived reports, Windows attestation unavailable | Restore or re-pin authoritative artifacts and execute Windows-only checks on the designated PC | R2 record present with pinned SHA; `REMAINING_GATES.json` checksum matches; console tests no longer hit ENOENT; Windows attestation result is `READY` | `control-plane/tests/engineering-console.test.tsx`, Windows attestation suite | L | Owner artifacts, Windows PC |
| ENG-P0-04 | PF-15 | Full Python regression | 93 failures and 30 errors remain from mixed baseline causes | Triage by failure family; fix or formally baseline each family without weakening assertions | Failure set strictly decreases; no new failures versus current HEAD; each remaining failure has an owner-approved disposition | Full `.venv/bin/python -m pytest -q --tb=no` | L | P0-01…P0-03 may unblock many cases |

## 3. P1 — High

| Task ID | ECC ref | Component | Root cause | Minimal fix | Acceptance criteria | Tests | Complexity | Dependencies |
|---|---|---|---|---|---|---|---|---|
| ENG-P1-01 | PF-21 | Knowledge ingestion / cleaning | Haystack regex handles only ASCII `[ \t]`; NBSP and NUL survive | Normalize `\u00a0` to space and `\x00` to space/removal before existing cleaner; preserve raw source | Four failing ingestion tests pass; citations no longer contain invisible characters | `tests/test_knowledge_preparation.py` | S | None |
| ENG-P1-02 | PF-19 | RAG configuration contract | `top_k` grouping expectation and baseline fixture path conflict | Decide authoritative top-k behavior from spec; restore `reports/CONFIGURATION_BASELINE_20261006.json` or update pinned reference with approval | Both `test_configuration_integration.py` failures pass or are reclassified with an approved spec change | RAG regression suite | M | Contract owner |
| ENG-P1-03 | PF-20 | V1 knowledge boundary / operator UX | Non-`Aktif` pilot SOP is silently excluded from chat | Surface publication status in operator UI and return an explicit chat reason for unavailable SOP | Operator can see `Aktif`/not `Aktif`; chat does not silently return empty evidence for a known non-active SOP | `tests/test_sop_review.py`, `tests/test_sop_dashboard.py`, new focused test if needed | M | Review state fixture |
| ENG-P1-04 | PF-10 | Frontend tests | Three missing historical evidence files and one order/timing-sensitive retry assertion | Restore fixtures/re-pin paths; await the retry state transition deterministically in the test | `CI=1 npm test -- --reporter=basic` exits 0 | Full frontend suite, retry test repeated 3x | M | ENG-P0-03 fixtures |

## 4. P2 — Medium

| Task ID | ECC ref | Component | Root cause | Minimal fix | Acceptance criteria | Tests | Complexity | Dependencies |
|---|---|---|---|---|---|---|---|---|
| ENG-P2-01 | PF-04 | RAG constants | Canonical values duplicated in multiple modules | Import one shared constants module in `rag.py`, `production_hybrid_rag.py`, and `production_semantic_retriever.py` | Single authoritative definition; all effective-profile assertions still pass | `tests/test_effective_rag_profile.py`, relevant production retriever tests | M | None |
| ENG-P2-02 | PF-25 | Static analysis | Ruff/mypy debt remains high | Incremental file-by-file burn-down with per-file baselines | Touched files have no new errors; global counts trend down | `ruff check`, `mypy` | L | None |
| ENG-P2-03 | PF-01, PF-02 | ECC governance | Rules not installed and skill telemetry absent | Record an explicit decision: install approved rules with hooks still declined, or formally waive rules and define measurement window | Decision document exists; no unexpected hook activation | Verification of install-state and telemetry after change | S | Owner approval |

## 5. P3 — Low

| Task ID | ECC ref | Component | Root cause | Minimal fix | Acceptance criteria | Tests | Complexity | Dependencies |
|---|---|---|---|---|---|---|---|---|
| ENG-P3-01 | PF-05 | Graphify tooling | `graphify-out/graph.json` and CLI are absent | Restore graph artifacts/tooling only if codebase navigation value justifies it | `graphify query` works or skip remains documented | No product test required | S | Tooling decision |
| ENG-P3-02 | PF-03 | Evidence automation | Evidence lives in reports rather than generated artifacts | Add report-generation script only if repeated manually more than twice | Reports reproducible from preserved commands and evidence files | Documentation review | S | None |

## 6. Sequencing rules

1. Do not start `ENG-P0-04` cleanup guesses before `ENG-P0-01`/`ENG-P0-02`; many failures are environment-driven.
2. Do not change frontend tests before `ENG-P0-03` confirms which historical artifacts are authoritative.
3. Do not “fix” `test_rag_actual_query_and_ingestion_use_config` by relaxing assertions; decide the top-k contract first.
4. Do not claim V1 E2E success from synthetic fixtures alone.
5. Keep all changes within existing V1 modules and APIs.
