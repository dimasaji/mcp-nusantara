# Nusantara V1 — Llama 3.2 1B Conversational RAG Acceptance Report

Contract: **NUS-V1-LLAMA-RAG-001** (12 Nov 2026) · PASAL 12 mandatory format.
Conclusion: **PARTIAL** (see §F). NOT production-ready. No automatic model change.

---

## A. Identitas Pengujian (Test Identity)

| Item | Value |
|---|---|
| Tanggal | 2026-11-13 |
| Commit SHA (base) | `c3ac1669cf7cbab0e4d0f3ad02daf0f5748f289b` (focused fixes A/B/C/D applied in working tree, uncommitted at report time) |
| Branch | `codex/fullroot-control-20261007` |
| Model runtime | `llama3.2:1b` via local Ollama, `127.0.0.1:11434` (pid 16700; runner `llama-server` pid 33972) |
| Model params (current, measured — NOT optimized this pass) | `num_ctx` 4096 default (`settings.llm_context_tokens`, `app/core/config.py:24`); `num_predict` 512 default; `keep_alive` "10m" (`app/models/ollama.py:154`); retrieval `top_k` 5 (`nusantara_config.py:106`); temperature from config (low/None) |
| Embedding | IndoBERT `indobenchmark/indobert-base-p1`, 768-dim, persistent worker subprocess (`nusantara-models/indobert_worker.py`); offline flags `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` |
| Backend | FastAPI Nusantara Core, `127.0.0.1:8000` (pid 31684), `OMP_NUM_THREADS=2 CUDA_VISIBLE_DEVICES=` |
| Runtime version | `nusantara-core` 0.1.0, build `sha256:80949b08a6f621a840135f171bd91e489fc9f50f912e334e11aa5246301e89dd` |
| RAM total | **7.68 GB** (8 GB host, CPU-only) |
| RAM available (during chat) | **0.07–0.27 GB** (near saturation); `llama-server` 973 MB; Windows Memory Compression 1.3 GB |
| Jumlah SOP Aktif | **44** (contract baseline 34 → **+10** difference; `reports/repro/sop_inventory.json`) |
| Frontend | Chat UI dev server `127.0.0.1:5180` (pid 10432) — listening but HTTP unresponsive under RAM pressure (see §C/§F) |

Model freeze intact (PASAL 2): no model swap, no OpenRouter/paid API, no large
download, no embedding change. Architecture intact (PASAL 3): no new
service/UI/DB; only the genuine PIAK-03 SOP `…d9ae50f8` was approved
(operator-authorized, prior session); empty Aktif stub `…75d5b40d` left untouched.

---

## B. Hasil Pengujian Pertanyaan (Question Results)

### Stage A — PIAK-03 (real llama3.2:1b, warm worker, one session, after Defect D fix)

Evidence: `reports/repro/stage_a_piak03_runtime.json`, session
`web-f2787751-05cb-4331-be17-955c6fc83014`. Genuine SOP `…d9ae50f8` (Aktif, score 1.0).
Ground truth: `reports/repro/piak03_capil01_versions.json` (Row 1 → "Surat Permohonan"
p1; Row 15 → "3 Hari Kerja" p2; **no Biaya column**; 15-step flow).

| Test ID | SOP | Pertanyaan | Jawaban Aktual | Jawaban Acuan (ground truth) | Sitasi | Status |
|---|---|---|---|---|---|---|
| T01 | PIAK-03 | Apa persyaratan permohonan data pribadi? | "Siapkan Surat Permohonan." | Surat Permohonan (Row 1) | d9ae50f8 p1 | **PASS** |
| T02 | PIAK-03 | Berapa lama? | "Menurut SOP: 3 Hari Kerja." | 3 Hari Kerja (Row 15) | d9ae50f8 p2 | **PASS** |
| T03 | PIAK-03 | Biayanya? | "Biaya permohonan data pribadi?" (echo) | Abstain — cost not stated (no Biaya column) | none (ev=0) | **FAIL** |
| T04 | PIAK-03 | Bagaimana prosedurnya? | full 15-step procedure | 15-step activity flow | d9ae50f8 p1+2 | **PASS** |
| T05 | PIAK-03 | Siapa yang menangani? | "User: Siapa yang menangani?" (echo) | Pelaksana roles (Kadis/Kabid PIAK/Kasi/OPR SIAK/ADB…) | none (ev=0) | **FAIL** |
| T06 | PIAK-03 | Apa yang harus dibawa? | "Siapkan Surat Permohonan." | Surat Permohonan | d9ae50f8 p1 | **PASS** |
| T07 | PIAK-03 | Kalau persyaratannya kurang? | "…Assistant: Tidak." | Abstain / clarify (not stated) | none (ev=0) | **FAIL** |
| T08 | PIAK-03 | Berapa hari kerjanya? | "Hari kerjanya adalah 3 hari." | 3 Hari Kerja | none (ev=0, ungrounded) | **FAIL** |
| T09 | PIAK-03 | Bisa dijelaskan lebih sederhana? | safe abstention | simplified procedure (or abstain) | none (ev=0) | **FAIL** (safe) |
| T10 | PIAK-03 | Dari halaman berapa informasi tersebut? | safe abstention | p1 (requirements) / p2 (duration) | none (ev=0) | **FAIL** (safe) |

**Stage A golden set: 4/10 PASS (40%).** T01/T02/T04/T06 grounded with correct
document + page citations. T09/T10 produced the safe abstention text (no
fabrication). T07 ("Tidak.") and T08 ("3 hari", ungrounded) are unsupported claims.
Before Defect D the warm run passed only T01/T02 (2/10); D raised it to 4/10
(T04, T06 now restore scope after conversation-classified T03/T05).

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
| **Context resolution error** | Defect D (FIXED): conversation-classified follow-up stored `{}`, shadowing prior SOP identity (`memory/engine.py:187`); fixed at `agent.py:540-543`. Defect E (REMAINING): short follow-ups "Biayanya?" (T03), "Siapa yang menangani?" (T05), "Berapa hari kerjanya?" (T08) not recognised as a facet → `uses_context=False` → scope not restored. Note "Berapa lama?" (T02) IS recognised but "Berapa hari kerjanya?" (T08) is not. |
| **Retrieval error** | Stage C precision@1 4/44; CAPIL-01 B01 retrieved a KK doc instead of `f9ad8a5d`; empty stub `75d5b40d` and `155ba1e4f` attract unrelated queries (problem #3). |
| **Extraction/source error** | Empty Aktif stub `…75d5b40d` (source_len 61, empty chunk) ranks first via exact-title boost; CAPIL-01 version snapshot `pages: []` (inadequate extraction). Genuine PIAK-03 `d9ae50f8` extraction is good (15 rows, 2 pages). |
| **Generation error** | Unscoped `llama3.2:1b` echoes/fabricates: T05 "User: …", T07 "Tidak.", T08 "3 hari" (ungrounded, value coincidentally correct) — problem #4. Default path DOES abstain safely when no evidence (T09/T10). |
| **Citation error** | T10 (page question) abstained instead of citing p1/p2. Fast-path citations correct for T01 (p1), T02 (p2), T04 (p1+2), T06 (p1). |
| **Runtime/performance error** | Stage C 29/44 errors (503/504) under RAM saturation; IndoBERT cold load ~30.6 s > 30 s stage timeout (warm-up required); non-LLM p95 13.7 s > 5 s target; frontend dev server HTTP-unresponsive under memory pressure → Browser E2E BLOCKED (problem #5). |
| **Ground-truth ambiguity** | T03 cost: no Biaya column → correct answer is abstention, never "gratis" (PASAL 7 Path C). CAPIL-01 ground truth not captured. Stage C per-SOP ground truth unavailable. T08 value matches ground truth but is ungrounded (still a FAIL per PASAL 11 "0 unsupported claims"). |

---

## D. Metrik (Metrics)

| Metric | Value |
|---|---|
| Total live scenarios executed | 58 (Stage A 10 + Stage B 4 + Stage C 44). Full Stage C target 170 NOT reached. |
| Stage A golden set PASS/FAIL | **4 PASS / 6 FAIL** (40% accuracy) |
| Stage B | 0 PASS / 4 FAIL (NOT PASS per PASAL 9) |
| Stage C | precision@1 4/44; grounded 2/44; 29/44 error/no-evidence |
| Overall verdict | **PARTIAL** |
| Citation precision (Stage A fast path) | 4/4 correct document + page |
| Retrieval Recall@k | Not computed corpus-wide (no per-SOP ground truth); Stage C precision@1 4/44 reported as availability smoke |
| Latency p50 / p95 — ALL turns | **3606 ms / 12693 ms** (min 1439, max 14225) |
| Latency p50 / p95 — non-LLM fast path | **7414 ms / 13714 ms** → PASAL 11 p95<5 s target **NOT met** (T01 14.2 s first-turn cold residue; T04 10.8 s 15-step procedure; steady-state T02 2.8 s / T06 4.0 s < 5 s) |
| Latency p50 / p95 — LLM path | 2967 ms / 7324 ms |
| RAM total / available (chat) | 7.68 GB / 0.07–0.27 GB; `llama-server` 973 MB; Memory Compression 1.3 GB. Idle-only baseline not separately captured (host already saturated by co-resident apps). |
| Follow-up failure count (Stage A T02–T10) | **6 / 9** (T03, T05, T07, T08, T09, T10) |
| Runtime crashes | 0 backend crashes; Stage C 503/504 are handled error responses, not crashes |
| Cross-session leaks | 0 observed (isolated sessions per stage) |
| Unauthorized SOP changes | 0 (only operator-authorized `d9ae50f8` approval, prior session) |
| Unauthorized model changes | 0 |

---

## E. Perubahan Kode (Code Changes)

| File | Change | Reason | Proving tests | Regression risk | Rollback |
|---|---|---|---|---|---|
| `app/hermes/agent.py` | Defect A: persist `{topic, document_id, title}` from confident top retrieval on the general path (~L1088). Defect D: conversation-classified follow-up preserves `previous` identity instead of `{}` (L540-543). | PASAL 5 context persistence; short follow-up must keep SOP identity | `tests/test_hermes_v1_context_persistence.py` (3), `tests/test_hermes_v1_context_preservation.py` (2) | Low — zero new failures proven (below) | `git checkout -- app/hermes/agent.py` |
| `app/knowledge/grounding.py` | Defect B: table fast-path in `service_answer_facts` so pilot table facts fire on the multi-document general path | PASAL 7 Path A verified fast answer | `tests/test_service_facts_table_multipath.py` (3) | Low | `git checkout -- app/knowledge/grounding.py` |
| `app/models/ollama.py` | Defect C: `trust_env=False` on the shared httpx client factory | Ambient `NO_PROXY` `[::1]` → `InvalidURL` → HTTP 500 on local provider | `tests/test_ollama_provider_proxy_env.py` (2) | Low | `git checkout -- app/models/ollama.py` |
| `tests/test_hermes_v1_context_persistence.py` (new) | A regression | — | 3 green | — | delete file |
| `tests/test_hermes_v1_context_preservation.py` (new) | D regression (TDD RED→GREEN) | — | 2 green | — | delete file |
| `tests/test_service_facts_table_multipath.py` (new) | B regression | — | 3 green | — | delete file |
| `tests/test_ollama_provider_proxy_env.py` (new) | C regression | — | 2 green | — | delete file |

No model/embedding/architecture/UI/DB change. No PIAK-03-only rule (fixes are
general). No SOP source/approval change beyond the authorized `d9ae50f8`.

### Test-layer results (PASAL 10 — separated)

- **A. Unit:** focused fixes **10/10 PASS** (A:3, B:3, C:2, D:2), `pytest -q`, 2.44 s.
- **B. Integration / regression:** broad suite `-k "v1 or hermes or grounding or
  langgraph or knowledge or ollama or service_facts"`:
  - With changes: **41 failed, 454 passed, 4 skipped, 2 errors**.
  - At HEAD (changes stashed, new tests excluded): **43 failed, 442 passed, 4 skipped, 2 errors**.
  - **Attribution: ZERO new failures caused by the changes** — the with-changes
    FAILED set is a strict subset of HEAD's (`comm -23` empty). All 12 distinct
    failed functions are **pre-existing at HEAD**, including
    `test_v1_langgraph.py::test_existing_grounding_rejects_missing_evidence_and_unsupported_claim[True-None]`
    (independently attributed to HEAD in prior session). The lower with-changes
    failure count is test-ordering/shared-state flakiness, **not claimed as fixes**.
- **C. Runtime (real Ollama + Knowledge):** Stage A/B/C executed against
  `127.0.0.1:8000` with real `llama3.2:1b` (no fixture substitution). Stage A 4/10;
  Stage B FAIL; Stage C smoke 4/44 p@1. **PARTIAL.**
- **D. Browser End-to-End:** **BLOCKED (environmental).** Chat UI dev server
  `127.0.0.1:5180` (pid 10432) is listening but does not serve HTTP within 20 s
  (urllib TimeoutError) and the in-app browser page stays blank (navigate timed out
  30 s). Root cause: host RAM saturation (0.07 GB available). The user's dev server
  was NOT restarted and no co-resident apps were closed (unauthorized). Follow-up
  functionality IS proven at the API/runtime layer (Stage A T02/T04/T06); the
  browser layer remains unverified.

---

## F. Kesimpulan (Conclusion)

**PARTIAL.**

Bukti fungsi yang berjalan (real runtime, llama3.2:1b):
- Core problems **#1 (first/follow-up), #2 (SOP context), #6 (Active SOP accuracy)**
  are FIXED for the requirements/duration/procedure fast-path facets: Stage A
  T01/T02/T04/T06 grounded with correct document + page citations; short follow-up
  "Berapa lama?" resolves to "3 Hari Kerja" from the genuine SOP. Defect D measurably
  improved Stage A from 2/10 → 4/10.
- Defect C (proxy-env HTTP 500) fixed; local provider returns HTTP 200.
- Zero new test regressions; model freeze and architecture constraints intact;
  0 unauthorized SOP/model changes; 0 cross-session leaks; 0 backend crashes.

Gap yang tersisa (honest):
- Stage A golden set 4/10 (<100% ⇒ not full PASS, PASAL 11). 6 follow-up failures
  from **Defect E** (facet-recognition gaps) → unscoped 1B echo/fabrication
  (problems #3/#4). 2 unsupported claims (T07, T08) ⇒ "0 unsupported claims" NOT met.
- **Retrieval precision** poor corpus-wide (Stage C p@1 4/44; CAPIL-01 wrong top doc);
  empty Aktif stub `75d5b40d` still an attractor (problem #3, extraction/source).
- **RAM/performance** (problem #5): host saturated (0.07 GB free), non-LLM p95 13.7 s
  (>5 s target), IndoBERT cold load >30 s timeout, Stage C 29/44 errors under batch
  load, frontend HTTP-unresponsive ⇒ Browser E2E BLOCKED.
- Stage B CAPIL-01 NOT PASS (extraction/ground-truth inadequate). Full Stage C
  170-scenario batch NOT executed.

Rekomendasi (tanpa pergantian model otomatis, PASAL 14):
1. **Defect E** — general facet/context recognition for cost/who/duration-phrasing
   follow-ups so scope restores and the fast path fires (PASAL 5/7). Highest leverage
   for Stage A 4/10 → higher; no model change.
2. **Retrieval hygiene** — exclude contentless evidence so the empty Aktif stub
   `75d5b40d` can never be cited as top grounding (general, data-free); investigate
   title-boost attractors. Do NOT mass-reindex before cause proven (PASAL 6.9).
3. **RAM/perf** — measure on a dedicated 8 GB runtime (close co-resident apps);
   consider `num_ctx` 2048 / `num_predict` 128–256 experiments (PASAL 8) and warm-up;
   re-measure p95 and Stage C stability. These are config experiments, not applied here.
4. **CAPIL-01 / Stage C ground truth** — capture verified per-SOP ground truth and
   adequate extraction before claiming PASS; then run the full 170-scenario batch.
5. **Browser E2E** — re-run once the host has RAM headroom and the dev server responds.
6. Model swap is **NOT recommended**: per PASAL 14, retrieval/context/facet/grounding
   were checked first and are the proven causes; the 1B model is not the root cause.

**Dilarang menyatakan PRODUCTION READY** — unit tests alone do not establish it;
runtime golden set is 4/10 and Browser E2E is blocked.

---

## Deliverable index (PASAL 15)

1. Runtime baseline — `reports/runtime_baseline.md` (P0).
2. Multi-turn reproduction — `reports/repro/repro_operator_general_multiturn*.json`.
3. Root-cause analysis — `reports/root_cause_analysis.md` (Defects A–E, §10 langgraph).
4. Focused code fixes — `app/hermes/agent.py`, `app/knowledge/grounding.py`, `app/models/ollama.py`.
5. Context Resolver / Retrieval tests — `tests/test_hermes_v1_context_*.py`, `tests/test_service_facts_table_multipath.py`.
6. Real llama3.2:1b runtime results — `reports/repro/stage_a_piak03_runtime.json`.
7. PIAK-03 / CAPIL-01 results — Stage A (§B), `reports/repro/stage_bc_runtime.json` (stage_b).
8. Active SOP report — `reports/repro/sop_inventory.json` (44 Aktif), `stage_bc_runtime.json` (stage_c).
9. Speed / RAM metrics — §D, `reports/repro/ram_snapshot.json`.
10. Final PASS/PARTIAL/FAIL + recommendations — this report (**PARTIAL**).