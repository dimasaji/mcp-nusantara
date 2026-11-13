# Nusantara V1 — Llama 3.2 1B Conversational RAG Acceptance Report

Contract: **NUS-V1-LLAMA-RAG-001** (12 Nov 2026) · PASAL 12 mandatory format.
Conclusion: **PARTIAL** (see §F). NOT production-ready. No automatic model change.

---

## A. Identitas Pengujian (Test Identity)

| Item | Value |
|---|---|
| Tanggal | 2026-11-13 |
| Commit SHA (base) | `61ffd389` (A/B/C/D committed). Defect E (engine.py, agent.py, grounding.py + facet tests) applied in working tree, **uncommitted** at report time. |
| Branch | `codex/fullroot-control-20261007` |
| Model runtime | `llama3.2:1b` via local Ollama, `127.0.0.1:11434` (serve pid 21088; runner `llama-server` holds ~973 MB weights) |
| Model params (current, measured — NOT optimized this pass) | `num_ctx` 4096 default (`settings.llm_context_tokens`, `app/core/config.py:24`); `num_predict` 512 default; `keep_alive` "10m" (`app/models/ollama.py:154`); retrieval `top_k` 5 (`nusantara_config.py:106`); temperature from config (low/None) |
| Embedding | IndoBERT `indobenchmark/indobert-base-p1`, 768-dim, persistent worker subprocess (`nusantara-models/indobert_worker.py`); offline flags `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` |
| Backend | FastAPI Nusantara Core, `127.0.0.1:8000` (pid 9276), `OMP_NUM_THREADS=2 CUDA_VISIBLE_DEVICES=` |
| Runtime version | `nusantara-core` 0.1.0, build `sha256:9809dcd900f28fcd607b9a2adf967d31a75417dfa1fe3f427cacbfd887a6b595` |
| RAM total | **7.68 GB** (8 GB host, CPU-only) |
| RAM available (during chat) | **0.07–0.27 GB** (near saturation; prior `ram_snapshot.json`, host unchanged this pass); `llama-server` 973 MB; Windows Memory Compression 1.3 GB |
| Jumlah SOP Aktif | **44** (contract baseline 34 → **+10** difference; `reports/repro/sop_inventory.json`) |
| Frontend | Chat UI dev server `127.0.0.1:5180` (prior run pid 10432; not re-verified this pass) — listening but HTTP unresponsive under RAM pressure (see §C/§F) |

Model freeze intact (PASAL 2): no model swap, no OpenRouter/paid API, no large
download, no embedding change. Architecture intact (PASAL 3): no new
service/UI/DB; only the genuine PIAK-03 SOP `…d9ae50f8` was approved
(operator-authorized, prior session); empty Aktif stub `…75d5b40d` left untouched.

---

## B. Hasil Pengujian Pertanyaan (Question Results)

### Stage A — PIAK-03 (real llama3.2:1b, warm worker, one session, after Defect E fix)

Evidence: `reports/repro/stage_a_piak03_runtime.json`, session
`web-d27dd551-f4f5-4ee7-9047-f951806b4a76`, build `sha256:9809dcd9…`, pid 9276.
Genuine SOP `…d9ae50f8` (Aktif, score 1.0). Ground truth:
`reports/repro/piak03_capil01_versions.json` (Row 1 → "Surat Permohonan" p1; Row 15 →
"3 Hari Kerja" p2; **no Biaya column**; **no per-row actor**; 15-step flow).

| Test ID | SOP | Pertanyaan | Jawaban Aktual | Jawaban Acuan (ground truth) | Sitasi | Status |
|---|---|---|---|---|---|---|
| T01 | PIAK-03 | Apa persyaratan permohonan data pribadi? | "Siapkan Surat Permohonan." | Surat Permohonan (Row 1) | d9ae50f8 p1 | **PASS** |
| T02 | PIAK-03 | Berapa lama? | "Menurut SOP: 3 Hari Kerja." | 3 Hari Kerja (Row 15) | d9ae50f8 p2 | **PASS** |
| T03 | PIAK-03 | Biayanya? | "Informasi biaya belum tercantum dalam SOP ini." | Abstain — cost not stated (no Biaya column) | d9ae50f8 p1+2 (ev=1) | **PASS** (Path C) |
| T04 | PIAK-03 | Bagaimana prosedurnya? | full 15-step procedure | 15-step activity flow | d9ae50f8 p1+2 | **PASS** |
| T05 | PIAK-03 | Siapa yang menangani? | "Informasi pelaksana belum tersedia dalam SOP ini." | Abstain — no per-row actor in table (swimlane headers only) | d9ae50f8 p1+2 (ev=1) | **PASS** (Path C) |
| T06 | PIAK-03 | Apa yang harus dibawa? | "Siapkan Surat Permohonan." | Surat Permohonan | d9ae50f8 p1 | **PASS** |
| T07 | PIAK-03 | Kalau persyaratannya kurang? | "Saya tidak memiliki informasi tentang SOP ini." | Abstain / clarify (conditional not stated) | none (ev=0) | **FAIL** (safe; conversational, not a facet) |
| T08 | PIAK-03 | Berapa hari kerjanya? | "Menurut SOP: 3 Hari Kerja." | 3 Hari Kerja | d9ae50f8 p2 (ev=1) | **PASS** |
| T09 | PIAK-03 | Bisa dijelaskan lebih sederhana? | safe abstention | simplified procedure (or abstain) | none (ev=0) | **FAIL** (safe; conversational) |
| T10 | PIAK-03 | Dari halaman berapa informasi tersebut? | safe abstention | p1 (requirements) / p2 (duration) | none (ev=0) | **FAIL** (safe; citation follow-up) |

**Stage A golden set: 7/10 PASS (70%).** T01/T02/T04/T06/T08 grounded with correct
document + page citations; T03/T05 are correct Path C abstentions WITH citation
(cost not stated; no per-row actor). **Unsupported factual claims: 0** — T07 now
abstains (pre-E "Tidak."), T08 is grounded (pre-E ungrounded "3 hari"). T07/T09/T10
produce the safe abstention text (no fabrication, `requires_human=True`).
Progression: 2/10 (after C) → 4/10 (after D) → **7/10 (after E)**. Residual 3 failures
are conversational/meta follow-ups (conditional, simplification, page-citation), not
service facets — outside Defect E's facet-recognition scope (see §C/§F).

### Stage B — CAPIL-01 (comparison SOP) — NOT PASS

Evidence: `reports/repro/stage_bc_runtime.json` (`stage_b`), doc `…f9ad8a5d`
("Pelayanan Penerbitan Akta Kelahiran bagi WNI Via Aplikasi Tangerang Live dan
Portal", Aktif). Per PASAL 9, CAPIL-01 must NOT be marked PASS while extraction /
ground truth is inadequate — its version snapshot has `pages: []` and no verified
ground-truth text was captured.

| Test ID | Pertanyaan | Jawaban Aktual | provider_status | ev / top doc | Status |
|---|---|---|---|---|---|
| B01 | Apa persyaratan pelayanan akta kelahiran … Tangerang Live? | safe abstention (33056 ms) | ollama | 5 / **e490bcbe (WRONG — a KK doc)** | FAIL (retrieval) |
| B02 | Berapa lama? | "Konteks bagian terpilih; 342 blok lain tidak dimuat…" | evidence_fast_path | 0 | FAIL (no real answer) |
| B03 | Bagaimana prosedurnya? | "Konteks bagian terpilih; 343 blok lain…" | evidence_fast_path | 0 | FAIL |
| B04 | Apa yang harus dibawa? | "Konteks bagian terpilih; 337 blok lain…" | evidence_fast_path | 0 | FAIL |

CAPIL-01 did not surface as top evidence for its own service question (B01 retrieved
a different KK document). **Stage B = FAIL / NOT PASS** (retrieval + extraction +
ground-truth inadequacy). No cross-session leak observed (isolated session).

### Stage C — Active SOP corpus (actual count 44, not 34)

Evidence: `reports/repro/stage_bc_runtime.json` (`stage_c`). **Scope honesty:** the
PASAL 9 minimum target is 5 scenarios × 34 SOP = 170 + multi-turn/cross-SOP. This
pass executed a **retrieval-availability smoke: 1 title-based requirements probe ×
44 Aktif SOPs = 44 probes**, NOT the full 170-scenario golden set (per-SOP ground
truth is not available for the whole corpus). Titles in inventory are truncated.

| Metric | Value |
|---|---|
| Aktif count (actual) | **44** (contract 34, +10) |
| Probes executed | 44 (1 per SOP) |
| Error / no-evidence responses (`provider_status` absent) | **29 / 44** |
| Evidence-bearing responses | 15 / 44 |
| Retrieval precision@1 (correct top doc) | **4 / 44** |
| Grounded answers | 2 / 44 |

The 29 error responses coincide with backend 503/504 (retrieval-unavailable /
stage-timeout) under sequential batch load on a RAM-saturated host — a
runtime/performance stability finding (problem #5), not a code regression (§E).
Among evidence-bearing rows, wrong top documents include the empty Aktif stub
`…75d5b40d` and `…155ba1e4f` acting as attractors (problem #3). Methodology caveat:
the fixed "Apa persyaratan <truncated title>?" template and the duplicate
"PERMOHONAN DATA PRIBADI" entries (genuine `d9ae50f8` vs empty stub `75d5b40d`)
make precision@1 a harsh probe; it measures retrieval availability, not answer
accuracy. **Stage C = PARTIAL inventory + smoke; full 170-scenario batch NOT executed.**

---

## C. Analisis Kesalahan (Error Analysis — 7 categories, PASAL 12 C)

| Category | Findings |
|---|---|
| **Context resolution error** | Defect D (FIXED): conversation-classified follow-up stored `{}`, shadowing prior SOP identity (`memory/engine.py:187`); fixed at `agent.py:540-543`. Defect E (FIXED): "Biayanya?" (T03→cost), "Siapa yang menangani?" (T05→who), "Berapa hari kerjanya?" (T08→duration) now recognised as facets → `uses_context=True` → scope restored → fast path. REMAINING (broader PASAL 5, not facet scope): conversational/meta follow-ups T07 (conditional "kalau persyaratan kurang"), T09 (simplification), T10 (page-citation) are not service facets and still fall to the unscoped general path. |
| **Retrieval error** | Stage C precision@1 4/44; CAPIL-01 B01 retrieved a KK doc instead of `f9ad8a5d`; empty stub `75d5b40d` and `155ba1e4f` attract unrelated queries (problem #3). Stage A scoped retrieval correct for all 7 passing turns (top doc d9ae50f8, score 1.0). |
| **Extraction/source error** | Empty Aktif stub `…75d5b40d` (source_len 61, empty chunk) ranks first via exact-title boost; CAPIL-01 version snapshot `pages: []` (inadequate extraction). Genuine PIAK-03 `d9ae50f8` extraction is good (15 rows, 2 pages) but carries no per-row actor and no Biaya column. |
| **Generation error** | RESOLVED for service facets: pre-E unscoped echoes/fabrications (T05 "User: …", T07 "Tidak.", T08 ungrounded "3 hari") are gone — T05/T08 now grounded fast-path, T07 abstains. **Unsupported factual claims: 0.** Default path abstains safely when no evidence (T07/T09/T10, `requires_human=True`). |
| **Citation error** | T03/T05 Path C abstentions now carry a citation (d9ae50f8 p1+2, ev=1). Fast-path citations correct for T01 (p1), T02/T08 (p2), T04 (p1+2), T06 (p1). REMAINING: T10 (page-citation follow-up) abstains instead of re-citing the prior answer's page — conversational citation handling, not facet scope. |
| **Runtime/performance error** | Stage C 29/44 errors (503/504) under RAM saturation; IndoBERT cold load ~30.6 s > 30 s stage timeout (warm-up required); non-LLM p95 dominated by T04 11.7 s procedure rendering > 5 s target; frontend dev server HTTP-unresponsive under memory pressure → Browser E2E BLOCKED (problem #5). |
| **Ground-truth ambiguity** | T03 cost: no Biaya column → correct answer is abstention, never "gratis" (PASAL 7 Path C) — now correct. T05 who: table has swimlane Pelaksana headers but NO per-row actor mapping → a specific handler is not verifiable → abstention is the safe correct answer (never invent from swimlane position). T08 now grounded "3 Hari Kerja" p2 (was ungrounded). CAPIL-01 / Stage C per-SOP ground truth still unavailable. |

---

## D. Metrik (Metrics)

| Metric | Value |
|---|---|
| Total live scenarios executed | 58 (Stage A 10 + Stage B 4 + Stage C 44). Stage A re-run after E; Stage B/C from the prior run (not re-executed this pass). Full Stage C target 170 NOT reached. |
| Stage A golden set PASS/FAIL | **7 PASS / 3 FAIL** (70% accuracy) |
| Stage B | 0 PASS / 4 FAIL (NOT PASS per PASAL 9) |
| Stage C | precision@1 4/44; grounded 2/44; 29/44 error/no-evidence |
| Overall verdict | **PARTIAL** |
| Unsupported factual claims (Stage A) | **0** (target MET) — T07/T09/T10 safe abstentions; T08 grounded |
| Citation precision (Stage A fast path + Path C) | 7/7 correct document + page (T01,T02,T03,T04,T05,T06,T08) |
| Retrieval Recall@k | Not computed corpus-wide (no per-SOP ground truth); Stage C precision@1 4/44 reported as availability smoke |
| Latency p50 / p95 — ALL turns | **2924 ms / ~8968 ms** (min 294, max 11675) |
| Latency p50 / p95 — non-LLM fast path | **2267 ms / ~9870 ms** → PASAL 11 p95<5 s target **NOT met** (T04 11.7 s 15-step procedure rendering dominates p95; T01 5.7 s / T06 5.1 s marginal; steady-state T02 1.7 s / T03 0.4 s / T05 0.3 s / T08 2.3 s < 5 s) |
| Latency p50 / p95 — LLM path | 3164 ms / ~4509 ms (T07/T09/T10) |
| RAM total / available (chat) | 7.68 GB / 0.07–0.27 GB; `llama-server` 973 MB; Memory Compression 1.3 GB. Idle-only baseline not separately captured (host already saturated by co-resident apps). |
| Follow-up failure count (Stage A T02–T10) | **3 / 9** (T07, T09, T10 — conversational/meta, not facets) |
| Runtime crashes | 0 backend crashes; Stage C 503/504 are handled error responses, not crashes |
| Cross-session leaks | 0 observed (isolated sessions per stage) |
| Unauthorized SOP changes | 0 (only operator-authorized `d9ae50f8` approval, prior session) |
| Unauthorized model changes | 0 |

---

## E. Perubahan Kode (Code Changes)

| File | Change | Reason | Proving tests | Regression risk | Rollback |
|---|---|---|---|---|---|
| `app/hermes/agent.py` | Defect A: persist `{topic, document_id, title}` from confident top retrieval on the general path (~L1088). Defect D: conversation-classified follow-up preserves `previous` identity instead of `{}` (L540-543). Defect E: add `'who':'ask_general_info'` to the service-facet intent map (L640). | PASAL 5 context persistence; short follow-up must keep SOP identity | `tests/test_hermes_v1_context_persistence.py` (3), `tests/test_hermes_v1_context_preservation.py` (2), `tests/test_language_service_turn_facets.py` | Low — zero new failures proven (below) | `git checkout -- app/hermes/agent.py` |
| `app/language/engine.py` | Defect E: `service_turn` adds `cost`/`who` aspects, extends `duration` with `hari(?:nya)?`/`kerjanya` (not bare "kerja"), facet priority + prefixes (L482-503). | PASAL 5 recognise short follow-ups so `uses_context=True` restores scope | `tests/test_language_service_turn_facets.py` (facet recognition + "cara kerja"→procedure regression) | Low | `git checkout -- app/language/engine.py` |
| `app/knowledge/grounding.py` | Defect B: table fast-path in `service_answer_facts` so pilot table facts fire on the multi-document general path. Defect E: `_cost_absence_fact` + `_who_absence_fact` Path C abstentions with citation on a single scoped table match; prose branch separates cost/channel; subject map adds cost/who. | PASAL 7 Path A verified fast answer; Path C never infer "free"/invent an actor | `tests/test_service_facts_table_multipath.py` (3), `tests/test_language_service_turn_facets.py` (cost/who abstention + citation) | Low | `git checkout -- app/knowledge/grounding.py` |
| `app/models/ollama.py` | Defect C: `trust_env=False` on the shared httpx client factory | Ambient `NO_PROXY` `[::1]` → `InvalidURL` → HTTP 500 on local provider | `tests/test_ollama_provider_proxy_env.py` (2) | Low | `git checkout -- app/models/ollama.py` |
| `tests/test_hermes_v1_context_persistence.py` (new) | A regression | — | 3 green | — | delete file |
| `tests/test_hermes_v1_context_preservation.py` (new) | D regression (TDD RED→GREEN) | — | 2 green | — | delete file |
| `tests/test_service_facts_table_multipath.py` (new) | B regression | — | 3 green | — | delete file |
| `tests/test_ollama_provider_proxy_env.py` (new) | C regression | — | 2 green | — | delete file |
| `tests/test_language_service_turn_facets.py` (new) | E regression (TDD RED→GREEN, generic table fixture, not PIAK-03) | — | 15 green | — | delete file |

No model/embedding/architecture/UI/DB change. No PIAK-03-only rule (fixes are
general). No SOP source/approval change beyond the authorized `d9ae50f8`.
**Commit state:** A/B/C/D committed as `61ffd389`; Defect E (engine.py, agent.py,
grounding.py + facet tests) applied in the working tree, **NOT yet committed** —
the prior commit authorization covered only the A/B/C/D bundle; E needs fresh
operator confirmation.

### Test-layer results (PASAL 10 — separated)

- **A. Unit:** A/B/C/D focused fixes **10/10 PASS** (A:3, B:3, C:2, D:2). Defect E
  facet tests **15/15 PASS** (`tests/test_language_service_turn_facets.py`, 0.25 s),
  including the strengthened who test requiring a clean cited abstention (not a
  clarify-dump).
- **B. Integration / regression:** full suite `pytest tests/ -q --tb=no -rf` with
  E+who: **92 failed, 1503 passed, 9 skipped, 2 errors** (184.9 s). Identical-scope
  HEAD baseline (`reports/repro/failures_head_full.txt`): **92 failed**. Normalized
  FAILED-set comparison (`comm`): the only deltas are 2 langchain tests
  (`test_create_retriever`, `test_knowledge_search_still_works`) present in E2 but
  not HEAD, and 2 `test_review_publication_v1` tests present in HEAD but not E2 —
  all in modules **unrelated to E**. The 2 langchain tests **pass in isolation**
  with E+who present (2 passed, 20.46 s) ⇒ test-ordering/shared-state flakiness,
  **not regressions**. **Attribution: ZERO new failures caused by E+who.** The
  pre-existing `test_v1_langgraph.py::test_existing_grounding_rejects_missing_evidence_and_unsupported_claim[True-None]`
  failure persists (independently attributed to HEAD, §10 of root-cause report).
  Targeted E-module run (`-k "service_answer or grounding or service_turn or facet
  or abstention or clarify or table_facts or pdf_sop or document_answer"`): 70 passed,
  1 failed (the same pre-existing langgraph test).
- **C. Runtime (real Ollama + Knowledge):** Stage A re-run against `127.0.0.1:8000`
  with real `llama3.2:1b`, warm worker (no fixture substitution): **7/10 PASS**,
  0 unsupported claims. Stage B FAIL; Stage C smoke 4/44 p@1 (prior run, not
  re-executed this pass). **PARTIAL.**
- **D. Browser End-to-End:** **BLOCKED (environmental).** Chat UI dev server
  `127.0.0.1:5180` listening but does not serve HTTP within 20 s under host RAM
  saturation (0.07 GB available). The user's dev server was NOT restarted and no
  co-resident apps were closed (unauthorized). Follow-up functionality IS proven at
  the API/runtime layer (Stage A T02/T03/T04/T05/T06/T08); the browser layer remains
  unverified.

---

## F. Kesimpulan (Conclusion)

**PARTIAL.**

Bukti fungsi yang berjalan (real runtime, llama3.2:1b):
- Core problems **#1 (first/follow-up), #2 (SOP context), #3 (wrong/missing evidence),
  #6 (Active SOP accuracy)** are FIXED for every service-facet follow-up: Stage A
  T01/T02/T04/T06/T08 grounded with correct document + page citations; T03 (cost) and
  T05 (who) are correct Path C abstentions WITH citation. Progression 2/10 (after C)
  → 4/10 (after D) → **7/10 (after E)**.
- **Problem #4 (unsupported info): 0 unsupported factual claims** on Stage A (target
  MET) — pre-E fabrications T07 "Tidak." and T08 ungrounded "3 hari" are gone.
- Defect C (proxy-env HTTP 500) fixed; local provider returns HTTP 200.
- Zero new test regressions (full-suite identical-scope HEAD comparison; 2 apparent
  deltas pass in isolation ⇒ flaky); model freeze and architecture constraints intact;
  0 unauthorized SOP/model changes; 0 cross-session leaks; 0 backend crashes.

Gap yang tersisa (honest):
- Stage A golden set **7/10** (<100% ⇒ not full PASS, PASAL 11). The 3 residual
  failures (T07 conditional "kalau persyaratan kurang", T09 simplification request,
  T10 page-citation follow-up) are **conversational/meta follow-ups, not service
  facets** — outside Defect E's facet-recognition scope. All three abstain safely
  (no fabrication, `requires_human=True`); they need broader PASAL 5/7 handling that
  re-uses the prior grounded answer for conditional/simplification/citation turns.
- **Retrieval precision** poor corpus-wide (Stage C p@1 4/44; CAPIL-01 wrong top doc);
  empty Aktif stub `75d5b40d` still an attractor (problem #3, extraction/source).
- **RAM/performance** (problem #5): host saturated (0.07 GB free), non-LLM p95 ~9.9 s
  (>5 s target, dominated by T04 15-step procedure rendering), IndoBERT cold load
  >30 s timeout, Stage C 29/44 errors under batch load, frontend HTTP-unresponsive
  ⇒ Browser E2E BLOCKED.
- Stage B CAPIL-01 NOT PASS (extraction/ground-truth inadequate). Full Stage C
  170-scenario batch NOT executed. Stage B/C not re-run after E (Stage A only).

Rekomendasi (tanpa pergantian model otomatis, PASAL 14):
1. **Conversational/meta follow-ups** (next leverage for Stage A 7/10 → higher):
   recognise conditional ("kalau … kurang?"), simplification ("lebih sederhana"),
   and citation ("dari halaman berapa?") follow-ups and re-use the prior grounded
   answer/evidence instead of falling to the unscoped general path (PASAL 5/7).
   No model change.
2. **Retrieval hygiene** — exclude contentless evidence so the empty Aktif stub
   `75d5b40d` can never be cited as top grounding (general, data-free); investigate
   title-boost attractors. Do NOT mass-reindex before cause proven (PASAL 6.9).
3. **RAM/perf** — measure on a dedicated 8 GB runtime (close co-resident apps);
   consider `num_ctx` 2048 / `num_predict` 128–256 experiments (PASAL 8) and warm-up;
   re-measure p95 (esp. the T04 procedure-rendering turn) and Stage C stability.
   These are config experiments, not applied here.
4. **CAPIL-01 / Stage C ground truth** — capture verified per-SOP ground truth and
   adequate extraction before claiming PASS; then run the full 170-scenario batch.
5. **Browser E2E** — re-run once the host has RAM headroom and the dev server responds.
6. Model swap is **NOT recommended**: per PASAL 14, retrieval/context/facet/grounding
   were checked first and are the proven causes; the 1B model is not the root cause.

**Dilarang menyatakan PRODUCTION READY** — unit tests alone do not establish it;
runtime golden set is 7/10 and Browser E2E is blocked.

---

## Deliverable index (PASAL 15)

1. Runtime baseline — `reports/runtime_baseline.md` (P0).
2. Multi-turn reproduction — `reports/repro/repro_operator_general_multiturn*.json`.
3. Root-cause analysis — `reports/root_cause_analysis.md` (Defects A–E, §10 langgraph).
4. Focused code fixes — `app/hermes/agent.py`, `app/language/engine.py`, `app/knowledge/grounding.py`, `app/models/ollama.py` (A/B/C/D committed `61ffd389`; E uncommitted).
5. Context Resolver / Retrieval tests — `tests/test_hermes_v1_context_*.py`, `tests/test_service_facts_table_multipath.py`, `tests/test_language_service_turn_facets.py` (E, 15 tests).
6. Real llama3.2:1b runtime results — `reports/repro/stage_a_piak03_runtime.json`.
7. PIAK-03 / CAPIL-01 results — Stage A (§B), `reports/repro/stage_bc_runtime.json` (stage_b).
8. Active SOP report — `reports/repro/sop_inventory.json` (44 Aktif), `stage_bc_runtime.json` (stage_c).
9. Speed / RAM metrics — §D, `reports/repro/ram_snapshot.json`.
10. Final PASS/PARTIAL/FAIL + recommendations — this report (**PARTIAL**).