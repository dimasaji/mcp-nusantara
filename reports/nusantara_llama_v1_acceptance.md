# Nusantara V1 — Llama 3.2 1B Conversational RAG Acceptance Report

Contract: **NUS-V1-LLAMA-RAG-001** (12 Nov 2026) · PASAL 12 mandatory format.
Conclusion: **PARTIAL** (see §F). NOT production-ready. No automatic model change.

---

## A. Identitas Pengujian (Test Identity)

| Item | Value |
|---|---|
| Tanggal | 2026-11-13 → 2026-11-16 (verifikasi runtime terakhir) |
| Commit SHA (base) | `61ffd389` (A/B/C/D); `5fe714f0` (E); `ae8d4549` (F+G+H). Defect I (candidate window) + J (no context-dump self-validation) committed by the repo owner as `d1af1069`; `edd3807c` restricts `CHAT_SESSION_PATTERN`. The hybrid tie-break + Defect K (fail-safe pilot hydration) + I/J/K regression tests + these reports are committed as `ee9bd224` (this pass) under the operator's run-all authorization (**no push**). |
| Branch | `codex/fullroot-control-20261007` |
| Model runtime | `llama3.2:1b` via local Ollama, `127.0.0.1:11434` (serve pid 18064; runner `llama-server` pid 13824). An external actor briefly switched `.env` to `gemma3n:e2b-it-q4_K_M`; restored to `llama3.2:1b` per the operator's explicit choice (root_cause §17). |
| Model params (current, measured — NOT optimized this pass) | `num_ctx` 4096 default (`settings.llm_context_tokens`, `app/core/config.py:24`); `num_predict` 512 default; `keep_alive` "10m" (`app/models/ollama.py:154`); retrieval `top_k` 5 (`nusantara_config.py:106`); temperature from config (low/None) |
| Embedding | IndoBERT `indobenchmark/indobert-base-p1`, 768-dim, persistent worker subprocess (`nusantara-models/indobert_worker.py`); offline flags `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1` |
| Backend | FastAPI Nusantara Core, `127.0.0.1:8000` (pid 11664 during the I/J/K Stage A re-verification; build `719b0d18`), `OMP_NUM_THREADS=2 CUDA_VISIBLE_DEVICES=` |
| Runtime version | `nusantara-core` 0.1.0, build `sha256:719b0d18246174332de9694dd1685b033ba9c366a8f67f1ec585737bed3f5c16` (I+J+K + hybrid tie-break). Prior F+G+H build `f86b1318` preserved in `stage_a_piak03_runtime_f86b1318.json`. |
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

### Stage A — PIAK-03 (real llama3.2:1b, warm worker, one session, re-verified after I/J/K)

Evidence: `reports/repro/stage_a_piak03_runtime.json`, session
`web-222175f6-2235-4509-b5d4-3fad6d4c5795` (`operator_general_no_binding`), build
`sha256:719b0d18…`, pid 11664 (root_cause §17; log `backend_stage_b5.log`,
all POST 200, 0 tracebacks/409/500). The prior F+G+H run (build `f86b1318`,
session `web-9202bc10…`) is preserved in `stage_a_piak03_runtime_f86b1318.json`.
Genuine SOP `…d9ae50f8` (Aktif, score 1.0). Ground truth:
`reports/repro/piak03_capil01_versions.json` (Row 1 → "Surat Permohonan" p1; Row 15 →
"3 Hari Kerja" p2; **no Biaya column**; **no per-row actor**; 15-step flow).

**I/J/K re-verification result: 10/10 grounded=True, all turns doc `d9ae50f8`
with the correct page citations and the same answers as the F+G+H run.** The
candidate-window widening (Defect I) initially regressed T02/T08 to a competing
partial-title SOP `a926fcf9` ("7 Hari Kerja"); the hybrid tie-break
(`(score, metadata.hybrid_score)`) restored the exact-title `d9ae50f8` to #1 and
the golden set to 10/10 (root_cause §17). **Latency caveat (honest):** this run's
non-LLM p95 ≈ **11.0 s** (T04 procedure 11008 ms, T01 7653 ms) — **above** the
PASAL 11 p95<5 s target, versus ≈3.9 s on the prior `f86b1318` run. The wider
candidate window (`max(limit*4, 20)` per batch) increases retrieval cost and the
host was RAM-variable; the golden-set accuracy target is MET but the latency
target is **NOT met on this build/run** (problem #5 — see §D/§F).

| Test ID | SOP | Pertanyaan | Jawaban Aktual | Jawaban Acuan (ground truth) | Sitasi | Status |
|---|---|---|---|---|---|---|
| T01 | PIAK-03 | Apa persyaratan permohonan data pribadi? | "Siapkan Surat Permohonan." | Surat Permohonan (Row 1) | d9ae50f8 p1 | **PASS** |
| T02 | PIAK-03 | Berapa lama? | "Menurut SOP: 3 Hari Kerja." | 3 Hari Kerja (Row 15) | d9ae50f8 p2 | **PASS** |
| T03 | PIAK-03 | Biayanya? | "Informasi biaya belum tercantum dalam SOP ini." | Abstain — cost not stated (no Biaya column) | d9ae50f8 p1+2 (ev=1) | **PASS** (Path C) |
| T04 | PIAK-03 | Bagaimana prosedurnya? | full 15-step procedure | 15-step activity flow | d9ae50f8 p1+2 | **PASS** |
| T05 | PIAK-03 | Siapa yang menangani? | "Informasi pelaksana belum tersedia dalam SOP ini." | Abstain — no per-row actor in table (swimlane headers only) | d9ae50f8 p1+2 (ev=1) | **PASS** (Path C) |
| T06 | PIAK-03 | Apa yang harus dibawa? | "Siapkan Surat Permohonan." | Surat Permohonan | d9ae50f8 p1 | **PASS** |
| T07 | PIAK-03 | Kalau persyaratannya kurang? | "Informasi ketentuan belum tercantum dalam SOP ini." | Abstain — conditional not stated (Path C, cited) | d9ae50f8 p1+2 (ev=1) | **PASS** (Path C; Defect F) |
| T08 | PIAK-03 | Berapa hari kerjanya? | "Menurut SOP: 3 Hari Kerja." | 3 Hari Kerja | d9ae50f8 p2 (ev=1) | **PASS** |
| T09 | PIAK-03 | Bisa dijelaskan lebih sederhana? | "Menurut SOP: 3 Hari Kerja." (reuse jawaban grounded sebelumnya, 144 ms) | reuse prior grounded answer — no new facts (Path A) | d9ae50f8 (ev=1, rebind) | **PASS** (Path A reuse; Defect F+G) |
| T10 | PIAK-03 | Dari halaman berapa informasi tersebut? | "Informasi tersebut berasal dari PERMOHONAN DATA PRIBADI, halaman 2." (153 ms) | halaman sumber jawaban sebelumnya (p2 durasi) | d9ae50f8 p2 (ev=1, rebind) | **PASS** (Path A citation; Defect F+G) |

**Stage A golden set: 10/10 PASS (100%) — real runtime, PASAL 11 golden-set target MET.**
T01/T02/T04/T06/T08 grounded with correct document + page citations; T03/T05/T07
are correct Path C abstentions WITH citation (cost not stated; no per-row actor;
conditional not stated); T09/T10 are deterministic Path-A reuse of the prior
grounded answer / its page citation (no LLM, no re-retrieval, no new facts).
**Unsupported factual claims: 0.** All 10 turns HTTP 200, grounded=True, ev=1,
doc d9ae50f8; backend log shows 0 tracebacks/409/500.
Progression: 2/10 (after C) → 4/10 (after D) → 7/10 (after E) → 8/10 (after F) →
**10/10 (after F+G+H)**. Runtime history (honest): the first residual restart
(build `03f05cb8`) exposed Defect G (reuse citation unbound ⇒ HTTP 409 on
T09/T10) and warmup exposed Defect H (worker inherits ambient `NO_PROXY=[::1]`
⇒ httpx InvalidURL at import); both fixed fail-closed and re-verified on build
`f86b1318` (root_cause §16). T09's reuse answers with the prior turn's grounded
text rather than a novel simplification — acceptable Path A (no fabrication);
a model-produced paraphrase remains unverified on the 1B and is not claimed.
Minor honest caveat: on T09/T10 the `trust` projection reports
`evidence_count=0` / `requires_human=true` (it is computed from this turn's
empty retrieval, before the reuse evidence is attached), while the final
`evidence` list carries the re-bound citation (d9ae50f8 p2) and
`grounding.grounded=true`. The signal is conservative, not a fabrication;
reconciling the trust projection with reuse evidence is a cosmetic follow-up,
not an acceptance blocker.

### Stage B — CAPIL-01 (comparison SOP) — PARTIAL (retrieval FIXED; answer blocked by document quality)

Evidence: `reports/repro/stage_b_capil01_runtime.json` (re-run on build `719b0d18`,
pid 11664), doc `…f9ad8a5d` ("Pelayanan Penerbitan Akta Kelahiran bagi WNI Via
Aplikasi Tangerang Live dan Portal", Aktif). The prior FAIL run (wrong KK top doc,
context-dump answers) is preserved in `stage_bc_runtime.json` (`stage_b`).

| Test ID | Pertanyaan | Jawaban Aktual | provider_status | ev / top doc | Status |
|---|---|---|---|---|---|
| B01 | Apa persyaratan pelayanan akta kelahiran … Tangerang Live? | "Informasi tersebut belum tersedia secara cukup dalam knowledge base." (34348 ms) | ollama | 4 / **f9ad8a5d (CORRECT — CAPIL-01, score 1.0, p2)** | retrieval PASS; answer abstains |
| B02 | Berapa lama? | "Informasi tersebut tidak ditemukan dalam dokumen yang dipilih." (517 ms) | local_rule | 0 | abstention (no dump) |
| B03 | Bagaimana prosedurnya? | "Informasi tersebut tidak ditemukan dalam dokumen yang dipilih." (382 ms) | local_rule | 0 | abstention (no dump) |
| B04 | Apa yang harus dibawa? | "Informasi tersebut tidak ditemukan dalam dokumen yang dipilih." (436 ms) | local_rule | 0 | abstention (no dump) |
| B05 | (follow-up) | "Informasi tersebut tidak ditemukan dalam dokumen yang dipilih." (365 ms) | local_rule | 0 | abstention (no dump) |

**What I/J/K fixed (verified):**
- **Defect I (retrieval):** CAPIL-01 `f9ad8a5d` now surfaces as **top evidence for
  its own service question** (B01 score 1.0, p2). Previously a KK doc `e490bcbe`
  won because the per-batch `top_k=limit` cutoff discarded CAPIL-01 before the
  title boost could rank it first (`search_probe_b01.json`: hybrid 0.527, cut at
  limit=5, ranks #1 at top_k=10). The wider candidate window fixes this.
- **Defect J (no context dumps):** B02–B05 no longer return the raw
  "Konteks bagian terpilih; 342 blok lain tidak dimuat…" block dump as a
  self-validated "answer". The last-resort recovery now skips rendered context
  selections (`docling_blocks`/`omitted_block_ids`) and abstains honestly.
- **Defect K (no 503):** an unreadable Aktif pilot no longer aborts the whole
  general search; B01 returns evidence (ev=4) instead of HTTP 503.

**Why the answer still abstains (root cause = DOCUMENT QUALITY, not code):**
CAPIL-01's OCR extraction shattered the PDF into **342 word-level blocks**
(`sop_rows=0`). `select_blocks` picks 29 fragmented keyword blocks
("persyaratan", "Aplikasi", "Tangerang", "Akta", "Kelahiran", "Live/Portal") and
omits 281 blocks that carry the requirements prose. There is no clean
"Persyaratan X: Y" line, so `document_answer_facts` returns `None`
(`diag_capil01_facts.py`: B01/B02/B04 all None) and no validatable fast-path fact
can be built → the router takes an honest **Path C abstention** rather than
fabricate (PASAL 7). Coherent prose exists in `full_document_text`, but block
selection picks fragments.

**Stage B = PARTIAL / NOT PASS** per PASAL 9: retrieval is fixed and dumps/503 are
eliminated, but there is still **no grounded answer and no verified per-row ground
truth** for CAPIL-01. Getting a grounded Stage B answer requires either **CAPIL-01
re-extraction** (document preparation) or a **context-selection / LLM-path change**
— both are **PASAL 14 stop-and-ask** territory. Grounding will NOT be loosened
(fabrication risk, PASAL 7) and source PDFs will NOT be changed (PASAL 3). No
cross-session leak observed (isolated session). **Decision point surfaced to the
operator (§F).**

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
| **Context resolution error** | Defect D (FIXED): conversation-classified follow-up stored `{}`, shadowing prior SOP identity (`memory/engine.py:187`); fixed at `agent.py:540-543`. Defect E (FIXED): "Biayanya?" (T03→cost), "Siapa yang menangani?" (T05→who), "Berapa hari kerjanya?" (T08→duration) now recognised as facets → `uses_context=True` → scope restored → fast path. Defect F (FIXED): non-facet follow-ups — conditional T07, simplification T09, page-citation T10 — restore prior SOP scope via `_contextual_scope_followup()`; T09/T10 reuse the prior grounded answer through Path A with fail-closed source rebind (Defect G). All 9 Stage A follow-ups now correct. |
| **Retrieval error** | **Defect I (FIXED):** the boundary searched each 20-doc batch with `top_k=limit`, so the engine cut by RAW hybrid rank BEFORE applying the title/keyword boost — an exact-service-title match below its batch cutoff never got the boost that would rank it first overall. CAPIL-01 B01 previously retrieved a KK doc; with the wider window (`max(limit*4,20)`) CAPIL-01 `f9ad8a5d` is now **top #1 (score 1.0)**. **Tie-break (FIXED):** widening alone let partial-title `a926fcf9` outrank exact-title `d9ae50f8` (both saturate at boosted 1.0, merge sorted by score only → batch order decided); merge key is now `(score, metadata.hybrid_score)` so the perfect-lexical exact title wins — Stage A restored to 10/10. Stage C precision@1 4/44 (prior smoke, not re-measured after I); empty stub `75d5b40d` and `155ba1e4f` still attract unrelated queries (problem #3, retrieval hygiene task). |
| **Extraction/source error** | **CAPIL-01 OCR word-shattering (root cause of Stage B abstention, NOT a code defect):** the PDF was extracted into 342 word-level blocks (`sop_rows=0`); `select_blocks` picks 29 fragmented keyword blocks and omits 281 carrying the requirements prose, so no clean "Persyaratan X: Y" line exists → `document_answer_facts` returns None → honest Path C abstention. Fixing needs CAPIL-01 re-extraction or a context-selection/LLM-path change (PASAL 14 stop-and-ask). Empty Aktif stub `…75d5b40d` (source_len 61, empty chunk) ranks first via exact-title boost. Genuine PIAK-03 `d9ae50f8` extraction is good (15 rows, 2 pages) but carries no per-row actor and no Biaya column. **Defect K (FIXED):** 7 of 44 Aktif pilots fail hydration (1 ValueError oversized-block, 6 DOCUMENT_EXTRACTION_PARTIAL 409); previously one unreadable pilot aborted the entire general search (503/409) — now skipped per-document so readable evidence still answers. |
| **Generation error** | RESOLVED for all Stage A turns: pre-E unscoped echoes/fabrications (T05 "User: …", T07 "Tidak.", T08 ungrounded "3 hari") are gone — T05/T08 grounded fast-path, T07 cited Path C abstention (Defect F), T09/T10 deterministic Path-A reuse of the prior grounded answer/citation (Defect F+G, no LLM, no new facts). **Defect J (FIXED):** the last-resort recovery no longer returns a rendered context-selection block dump ("Konteks bagian terpilih; N blok lain…") as a self-validated "answer" — Stage B B02–B05 now abstain honestly instead of dumping model context. **Unsupported factual claims: 0.** |
| **Citation error** | T03/T05/T07 Path C abstentions carry a citation (d9ae50f8 p1+2, ev=1). Fast-path citations correct for T01 (p1), T02/T08 (p2), T04 (p1+2), T06 (p1). T10 (page-citation follow-up) FIXED: re-cites the prior answer's page (p2) via the re-bound `last_answer` snapshot — 10/10 correct document + page. Minor residual: T09/T10 `trust.evidence_count=0` projection lag (see §B caveat); final evidence list is correct. |
| **Runtime/performance error** | Stage A re-verified on build `719b0d18` (I/J/K): 10/10 grounded, but non-LLM **p95 ≈ 11.0 s** (T04 procedure 11008 ms, T01 7653 ms) — **ABOVE** the PASAL 11 p95<5 s target, vs ≈3.9 s on the prior `f86b1318` run. The wider candidate window (`max(limit*4,20)` per batch, Defect I) increases retrieval cost; host RAM variable. **Accuracy target MET, latency target NOT met on this build/run** (problem #5). REMAINING: Stage C 29/44 errors (503/504) under sequential batch load on a RAM-saturated host (prior smoke); IndoBERT cold load ~30.6 s > 30 s stage timeout (warm-up required); frontend dev server HTTP-unresponsive under memory pressure → Browser E2E BLOCKED. Batch-load p95 not re-measured this pass; the window-widening latency cost needs a dedicated 8 GB measurement (PASAL 8 config experiments, not applied). |
| **Ground-truth ambiguity** | T03 cost: no Biaya column → correct answer is abstention, never "gratis" (PASAL 7 Path C) — now correct. T05 who: table has swimlane Pelaksana headers but NO per-row actor mapping → a specific handler is not verifiable → abstention is the safe correct answer (never invent from swimlane position). T08 now grounded "3 Hari Kerja" p2 (was ungrounded). CAPIL-01 / Stage C per-SOP ground truth still unavailable. |

---

## D. Metrik (Metrics)

| Metric | Value |
|---|---|
| Total live scenarios executed | 59 (Stage A 10 + Stage B 5 + Stage C 44). Stage A re-run after I/J/K (build `719b0d18`, pid 11664); Stage B re-run after I/J/K (5 turns, `stage_b_capil01_runtime.json`); Stage C from the prior smoke (not re-executed this pass). Full Stage C target 170 NOT reached. |
| Stage A golden set PASS/FAIL | **10 PASS / 0 FAIL** (100% accuracy — PASAL 11 golden-set target MET, re-verified on `719b0d18`) |
| Stage B | **PARTIAL** — retrieval FIXED (B01 top = CAPIL-01 `f9ad8a5d` score 1.0), dumps/503 eliminated (J/K); 0 grounded answers (OCR word-shattering → honest Path C abstention). NOT PASS per PASAL 9 (no grounded answer / verified ground truth). |
| Stage C | precision@1 4/44; grounded 2/44; 29/44 error/no-evidence (prior smoke; not re-measured after I) |
| Overall verdict | **PARTIAL** (Stage A accuracy MET; Stage B retrieval fixed but answer blocked by document quality; Stage C full batch + Browser E2E outstanding; latency target NOT met on `719b0d18`) |
| Unsupported factual claims (Stage A) | **0** (target MET) — T03/T05/T07 cited Path C abstentions; T09/T10 Path-A reuse of prior grounded answer/citation |
| Citation precision (Stage A) | **10/10** correct document + page (T01 p1; T02/T08/T09/T10 p2; T03/T05/T07 p1+2; T04 p1+2; T06 p1) |
| Retrieval Recall@k | Not computed corpus-wide (no per-SOP ground truth); Stage C precision@1 4/44 reported as availability smoke. Stage B B01 precision@1 now correct (CAPIL-01 #1) after Defect I. |
| Latency p50 / p95 — ALL turns (Stage A, build `719b0d18`) | **~1678 ms / ~11008 ms** (min 183, max 11008; nearest-rank p95). T04 procedure 11008 ms, T01 7653 ms, T06 4290 ms; reuse turns T09 288 ms / T10 183 ms. |
| Latency p50 / p95 — non-LLM fast path | **~1678 ms / ~11008 ms** → PASAL 11 p95<5 s target **NOT met on this build/run** (all 10 turns non-LLM). The wider candidate window (Defect I) adds retrieval cost vs the prior `f86b1318` run (p95 ≈3.9 s, MET). Caveat: single warm session, RAM-variable host, not a batch-load measurement; needs a dedicated 8 GB re-measurement + PASAL 8 config experiments (not applied). |
| Latency p50 / p95 — LLM path | Stage A: N/A (0 Ollama turns; T01–T08 fast path, T09/T10 Path-A reuse). Stage B B01: 1 Ollama turn, 34348 ms (abstention; OCR-blocked, RAM-variable). |
| RAM total / available (chat) | 7.68 GB / 0.07–0.27 GB (prior saturated measurement); `llama-server` ~973 MB when weights resident; Memory Compression 1.3 GB. Idle-only baseline not separately captured (host already saturated by co-resident apps). |
| Follow-up failure count (Stage A T02–T10) | **0 / 9** (was 2/9 before F+G; T09/T10 now Path-A reuse) |
| Runtime crashes | 0 backend crashes; Stage C 503/504 are handled error responses, not crashes |
| Cross-session leaks | 0 observed (isolated sessions per stage) |
| Unauthorized SOP changes | 0 (only operator-authorized `d9ae50f8` approval, prior session) |
| Unauthorized model changes | 0 |

---

## E. Perubahan Kode (Code Changes)

| File | Change | Reason | Proving tests | Regression risk | Rollback |
|---|---|---|---|---|---|
| `app/hermes/agent.py` | Defect A: persist `{topic, document_id, title}` from confident top retrieval on the general path (~L1088). Defect D: conversation-classified follow-up preserves `previous` identity instead of `{}` (L540-543). Defect E: add `'who':'ask_general_info'` to the service-facet intent map (L640). Defect F: `_contextual_scope_followup()` (anaphoric/possessive/conditional) + scope-restoration gate (L329) restores prior SOP scope for non-facet follow-ups, gated against new-service hints; F-residual: `last_answer` snapshot persistence + deterministic Path-A citation/simplification reuse. Defect G: reuse branch re-binds the prior source via `knowledge.reuse_prior_citation()` BEFORE citing; rejection ⇒ safe `local_rule` abstention (no unbound citation). **Defect J (~L1254-1268, committed `d1af1069`):** the last-resort recovery skips a rendered context selection (`metadata.docling_blocks`/`omitted_block_ids`) instead of returning `evidence[0].chunk[:400]` as a self-validated "answer"; abstains honestly when the only source is a block dump. | PASAL 5 context persistence; short follow-up must keep SOP identity; PASAL 7 Path A reuse without breaking the boundary's version guarantee; a context-selection dump is model context, not an answer | `tests/test_hermes_v1_context_persistence.py` (3), `tests/test_hermes_v1_context_preservation.py` (2), `tests/test_language_service_turn_facets.py`, `tests/test_hermes_v1_contextual_followup.py` (17), `tests/test_v1_recovery_context_dump.py` (2) | Low — zero new failures proven (below) | `git checkout -- app/hermes/agent.py` |
| `app/language/engine.py` | Defect E: `service_turn` adds `cost`/`who` aspects, extends `duration` with `hari(?:nya)?`/`kerjanya` (not bare "kerja"), facet priority + prefixes (L482-503). Defect F: general `conditional` flag (kalau/jika/bila/…). | PASAL 5 recognise short follow-ups so `uses_context=True` restores scope | `tests/test_language_service_turn_facets.py`, `tests/test_hermes_v1_contextual_followup.py` | Low | `git checkout -- app/language/engine.py` |
| `app/knowledge/grounding.py` | Defect B: table fast-path in `service_answer_facts` so pilot table facts fire on the multi-document general path. Defect E: `_cost_absence_fact` + `_who_absence_fact` Path C abstentions with citation on a single scoped table match; prose branch separates cost/channel; subject map adds cost/who. Defect F: `_conditional_absence()` cited Path C abstention for a conditional follow-up on a validated SOP table. | PASAL 7 Path A verified fast answer; Path C never infer "free"/invent an actor/invent a policy | `tests/test_service_facts_table_multipath.py` (3), `tests/test_language_service_turn_facets.py`, `tests/test_hermes_v1_contextual_followup.py` | Low | `git checkout -- app/knowledge/grounding.py` |
| `app/models/ollama.py` | Defect C: `trust_env=False` on the shared httpx client factory | Ambient `NO_PROXY` `[::1]` → `InvalidURL` → HTTP 500 on local provider | `tests/test_ollama_provider_proxy_env.py` (2) | Low | `git checkout -- app/models/ollama.py` |
| `app/security/v1_knowledge.py` | Defect G: `V1KnowledgeBoundary.reuse_prior_citation(document_id)` — fail-closed re-bind of a prior grounded citation for contextual reuse: operator+local-ollama guard; pilot ⇒ Aktif/trial-version check; non-pilot ⇒ document must exist; records the CURRENT version so `validate_response` keeps its guarantee. **Defect I (committed `d1af1069`):** each 20-doc batch now searches with `window=max(limit*4,20)` instead of `top_k=limit`, so a strong title/keyword match survives the engine's raw-rank cutoff and receives its boost. **Hybrid tie-break (this pass):** merge key `(item.score, metadata.hybrid_score)` so an exact-service-title match outranks a partial-title competitor that also saturates at boosted 1.0 (otherwise batch order decides). **Defect K (this pass):** pilot hydration wraps `review.evidence()` in try/except — skips an unreadable Aktif pilot (ValueError oversized-block, or 409 `Masalah pembacaan SOP:` partial extraction) per-document instead of aborting the whole general search; the bound single-doc path still propagates errors. | Reuse fast-path cited an unbound doc ⇒ HTTP 409 on T09/T10 (G). CAPIL-01 lost to a KK doc because the per-batch cutoff discarded it before the boost (I); widening alone regressed Stage A to partial-title `a926fcf9` (tie-break). One unreadable pilot among 44 aborted general search ⇒ 503/409 (K). | `tests/test_v1_knowledge_reuse_rebind.py` (4), `tests/test_hermes_v1_contextual_followup.py`, `tests/test_v1_search_candidate_window.py` (3), `tests/test_v1_hydration_failsafe.py` (3) | Low — additive window/tie-break/fail-safe; Stage A re-verified 10/10; zero new full-suite failures (below) | `git checkout -- app/security/v1_knowledge.py` |
| `app/language/semantic/indobert_client.py` | Defect H: worker spawn env strips all proxy variables (HTTP(S)_PROXY/ALL_PROXY/NO_PROXY, both cases) | Worker inherits ambient `NO_PROXY=[::1]` ⇒ huggingface_hub import-time httpx `InvalidURL: Invalid port: ':1]'` ⇒ worker dies, every embedding 503 (Defect C class, one layer deeper; worker is local/offline, never needs proxy) | `tests/test_indobert_worker_proxy_env.py` (1) | Low — child env only; worker/model/dimension unchanged | `git checkout -- app/language/semantic/indobert_client.py` |
| `tests/test_hermes_v1_context_persistence.py` (new) | A regression (harness stub later gained a `reuse_prior_citation` no-op for G) | — | 3 green | — | delete file |
| `tests/test_hermes_v1_context_preservation.py` (new) | D regression (TDD RED→GREEN) | — | 2 green | — | delete file |
| `tests/test_service_facts_table_multipath.py` (new) | B regression | — | 3 green | — | delete file |
| `tests/test_ollama_provider_proxy_env.py` (new) | C regression | — | 2 green | — | delete file |
| `tests/test_language_service_turn_facets.py` (new) | E regression (TDD RED→GREEN, generic table fixture, not PIAK-03) | — | 15 green | — | delete file |
| `tests/test_hermes_v1_contextual_followup.py` (new) | F regression (TDD RED→GREEN, generic fixtures + real GateIntegration harness) + F-residual reuse (citation/simplification/no-fabrication) + G (ev=0 reuse fires with rebind; rejected rebind ⇒ fail-closed abstention) | — | 17 green | — | delete file |
| `tests/test_v1_knowledge_reuse_rebind.py` (new) | G regression (TDD RED→GREEN): bind+validate passes; missing source ⇒ 409; operator/local-model guard; source-change after bind ⇒ validate 409 | — | 4 green | — | delete file |
| `tests/test_indobert_worker_proxy_env.py` (new) | H regression: spawn-env capture proves no proxy var leaks to the worker; UTF-8 vars preserved | — | 1 green | — | delete file |
| `tests/test_v1_search_candidate_window.py` (new) | I regression (TDD RED→GREEN): 25-doc neutral fake engine modeling cut-by-raw-rank-then-boost; strong-title target survives the batch cutoff; result bounded+sorted; equal-boost tie broken by raw hybrid (no PIAK-03/CAPIL-01 specifics) | — | 3 green | — | delete file |
| `tests/test_v1_recovery_context_dump.py` (new) | J regression (TDD RED→GREEN): recovery abstains instead of dumping a context selection (`docling_blocks`/`omitted_block_ids`); plain-prose source still returned | — | 2 green | — | delete file |
| `tests/test_v1_hydration_failsafe.py` (new) | K regression (TDD RED→GREEN): ValueError pilot skipped; 409 partial-extraction pilot skipped; readable pilots still hydrate (+source_versions) | — | 3 green | — | delete file |

No model/embedding/architecture/UI/DB change. No PIAK-03-only rule (fixes are
general). No SOP source/approval change beyond the authorized `d9ae50f8`.
**Commit state:** A/B/C/D committed as `61ffd389`; Defect E committed as
`5fe714f0`; F+G+H committed as `ae8d4549` (runtime-verified Stage A 10/10, build
`f86b1318`). **Defect I (candidate window) + J (no context-dump self-validation)
were committed by the repo owner as `d1af1069`**; `edd3807c` restricts
`CHAT_SESSION_PATTERN` to safe characters. The **hybrid tie-break + Defect K
(fail-safe pilot hydration) + the 3 I/J/K regression test files + these reports**
are committed as `ee9bd224` (this pass) under the operator's "Jalankan semua yang belum
selesai" run-all authorization (which includes backend restarts and focused
commits). **Not pushed** (push requires separate authorization). I/J/K are
runtime-verified on build `719b0d18` (Stage A 10/10 restored after the tie-break;
Stage B retrieval fixed, dumps/503 eliminated). See `root_cause_analysis.md` §16
(G/H) and §17 (I/J/K + the Stage B OCR document-quality root cause).

### Test-layer results (PASAL 10 — separated)

- **A. Unit:** A/B/C/D focused fixes **10/10 PASS** (A:3, B:3, C:2, D:2). Defect E
  facet tests **15/15 PASS** (`tests/test_language_service_turn_facets.py`, 0.25 s),
  including the strengthened who test requiring a clean cited abstention (not a
  clarify-dump). F+G+H focused: contextual-followup **17** + reuse-rebind **4** +
  context-persistence **3** + context-preservation **2** = **26 green**; proxy-env
  (worker **1** + ollama provider **2**) = **3 green**. I/J/K focused:
  candidate-window **3** + recovery-context-dump **2** + hydration-failsafe **3**
  = **8 green** (`tests/test_v1_search_candidate_window.py`,
  `tests/test_v1_recovery_context_dump.py`, `tests/test_v1_hydration_failsafe.py`,
  0.65 s, all TDD RED→GREEN, neutral fixtures).
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
  **F-residual full suite** (`reports/repro/regression_F_residual.log`): **92 failed,
  1518 passed, 9 skipped, 2 errors** (223 s). Normalized FAILED-set `comm` vs the
  prior full-suite baseline `full_suite_e2.log` (92 failed, 1503 passed): **identical
  92 = 92, zero only-in-baseline, zero only-in-current**; the +15 passed are exactly
  the new contextual-followup tests (12 F core + 3 residual reuse). **ZERO new
  regressions from F core + residual.**
  **F+G+H full suite** (`reports/repro/regression_F_rebind.log`, Ollama running,
  single clean run): **89 failed, 1527 passed, 10 skipped, 2 errors** (224.7 s).
  Normalized FAILED-set `comm` vs the same HEAD baseline (92): **zero
  only-in-current**; 3 only-in-baseline (`test_pdf_approval_activates_operator_retrieval_without_manual_chat`,
  `test_create_retriever`, `test_knowledge_search_still_works`) — the two langchain
  tests are the previously documented ordering-flaky pair (pass in isolation);
  the pipeline-api test passes in this run. **Attribution: ZERO new failures
  caused by F+G+H.** Methodology note (honest): three earlier attempts produced
  truncated logs — two concurrent suite runs accidentally shared one log file,
  and one run lost Ollama mid-suite (it had died under RAM saturation; the 4
  resulting 503 deltas passed in isolation once Ollama was restarted). Only the
  final single clean run with Ollama up is used for attribution.
  **I/J/K full suite** (`reports/repro/fullsuite_ijk.log`, build `719b0d18` working
  tree, single clean run): **89 failed, 1535 passed, 10 skipped, 2 errors**
  (201.1 s). The +8 passed vs the F+G+H run (1527) are exactly the 8 new I/J/K
  tests. Normalized FAILED-set `comm` vs `regression_F_rebind.log` (89): 89 = 89,
  with 4 only-in-current and 4 only-in-baseline. **Attribution of the 4
  only-in-current** (`test_backend_runtime_fixture::test_backend_process_ingestion_retrieval_chat_and_history`,
  `test_knowledge_pipeline_api::test_pdf_approval_activates_operator_retrieval_without_manual_chat`,
  `test_v1_operator_control::test_standalone_greeting_is_nonfactual_local_response[Selamat pagi]`
  and `[  HALLO!  ]`): the pipeline-api test **passes in isolation**
  (ordering-flaky); the other **3 fail in isolation at current HEAD with the
  uncommitted tie-break/K change stashed** (`git stash` attribution run: 3 failed,
  3 passed) ⇒ **pre-existing at HEAD (`edd3807c`), NOT caused by the tie-break/K
  change**. The 4 only-in-baseline deltas likewise pass/fail by ordering. **ZERO
  new failures caused by the I/J/K tie-break + Defect K change.** (HEAD moved
  since the F+G+H baseline via the owner's `d1af1069`/`edd3807c`/`430a8fba`/
  `f33c6d74`; the identical-scope baseline for the uncommitted change is current
  HEAD, verified by the stash run.)
- **C. Runtime (real Ollama + Knowledge):** Stage A re-run against `127.0.0.1:8000`
  with real `llama3.2:1b`, warm worker (no fixture substitution), build `719b0d18`
  (pid 11664): **10/10 PASS**, 0 unsupported claims, all turns grounded with
  doc d9ae50f8 + correct pages (T09/T10 via fail-closed prior-evidence rebind +
  Path-A reuse; root_cause §16/§17). The hybrid tie-break was essential — window
  widening alone regressed T02/T08 to partial-title `a926fcf9`. **Latency p95
  ≈11.0 s on this build (NOT <5 s; wider window cost, RAM-variable).** Stage B
  re-run (5 turns): retrieval FIXED (B01 top = CAPIL-01 `f9ad8a5d` score 1.0),
  dumps/503 eliminated (J/K), but 0 grounded answers — honest Path C abstention
  due to CAPIL-01 OCR word-shattering (document quality, PASAL 14 decision point).
  Stage C smoke 4/44 p@1 (prior run, not re-executed this pass). **PARTIAL overall
  (Stage A accuracy MET; Stage B retrieval fixed / answer blocked; latency target
  not met on this build).**
- **D. Browser End-to-End:** **BLOCKED (environmental).** Chat UI dev server
  `127.0.0.1:5180` listening but does not serve HTTP within 20 s under host RAM
  saturation (0.07 GB available). The user's dev server was NOT restarted and no
  co-resident apps were closed (unauthorized). Follow-up functionality IS proven at
  the API/runtime layer (Stage A T02/T03/T04/T05/T06/T08); the browser layer remains
  unverified.

---

## F. Kesimpulan (Conclusion)

**PARTIAL** — Stage A golden set **10/10 (100%) MET at real runtime** (re-verified
on build `719b0d18` after I/J/K); Stage B retrieval is FIXED but its answer is
blocked by CAPIL-01 document quality; full acceptance (PASAL 11) still requires
Stage B grounded answers, Stage C full batch, Browser E2E, and the latency target.

Bukti fungsi yang berjalan (real runtime, llama3.2:1b, build `719b0d18`, pid 11664):
- Core problems **#1 (first/follow-up), #2 (SOP context), #6 (Active SOP accuracy)**
  are FIXED for every Stage A turn: T01/T02/T04/T06/T08 grounded with correct
  document + page citations; T03 (cost), T05 (who), T07 (conditional) are correct
  Path C abstentions WITH citation; T09 (simplification) / T10 (page-citation)
  reuse the prior grounded answer via deterministic Path A with fail-closed
  source rebind (Defect F+G). Progression 2/10 → 4/10 → 7/10 → 8/10 → **10/10**,
  preserved after I/J/K (the hybrid tie-break restored exact-title `d9ae50f8`).
- **Problem #3 (retrieval), Stage B FIXED:** Defect I's wider candidate window
  surfaces CAPIL-01 `f9ad8a5d` as top #1 for its own service question (was a KK
  doc). Defect K makes pilot hydration fail-safe (one unreadable Aktif pilot no
  longer 503s the whole search). Defect J stops context-dump "answers".
- **Problem #4 (unsupported info): 0 unsupported factual claims** on Stage A
  (target MET) — pre-E fabrications T07 "Tidak." and T08 ungrounded "3 hari" are
  gone; no reuse turn invents facts; Stage B abstains honestly instead of dumping.
- Defect C (provider proxy-env HTTP 500) and Defect H (worker proxy-env crash,
  all embeddings 503) fixed; local provider + worker return healthy responses.
- Zero new test regressions from the I/J/K tie-break + Defect K change (full suite
  **89 failed, 1535 passed**; the 4 only-in-current deltas are 1 ordering-flaky +
  3 pre-existing at HEAD, proven by a stash attribution run). Model freeze and
  architecture constraints intact; 0 unauthorized SOP/model changes; 0
  cross-session leaks; 0 backend crashes.

Gap yang tersisa (honest):
- **Problem #5 (latency) NOT met on build `719b0d18`:** Stage A non-LLM p95 ≈
  **11.0 s** (T04 11008 ms, T01 7653 ms) **> 5 s target**, vs ≈3.9 s on the prior
  `f86b1318` run. The wider candidate window (Defect I) adds retrieval cost; the
  host is RAM-variable. Accuracy is preserved but the latency target regressed on
  this build — needs a dedicated 8 GB measurement + PASAL 8 config experiments
  (e.g. a smaller window or `num_ctx`/`num_predict` tuning), NOT applied here.
- **Stage B CAPIL-01 answer NOT PASS (document quality, PASAL 14 decision point):**
  retrieval is fixed (top #1) and dumps/503 are gone, but the OCR extraction is
  word-shattered (342 blocks, `sop_rows=0`); block selection picks 29 keyword
  fragments and omits the requirements prose, so `document_answer_facts` returns
  None → honest Path C abstention, no grounded answer, no verified per-row ground
  truth. **Getting a grounded Stage B answer requires either CAPIL-01
  re-extraction (document preparation) or a context-selection / LLM-path change —
  both PASAL 14 stop-and-ask.** Grounding will NOT be loosened (PASAL 7 fabrication
  risk); source PDFs will NOT be changed (PASAL 3). **Operator decision needed.**
- **Stage C full 170-scenario batch NOT executed** — only a 44-probe availability
  smoke (p@1 4/44, grounded 2/44, 29/44 errors under RAM-saturated batch load),
  not re-measured after Defect I. Per-SOP ground truth for the 44 Aktif SOPs is
  not yet captured; 7 of 44 pilots fail hydration (now skipped by K).
- **Retrieval precision** poor corpus-wide; empty Aktif stub `75d5b40d` and
  `155ba1e4f` act as attractors; duplicate/synthesized PIAK-03 entries
  (`sop_e4d43334`, `0e63a46b` .txt) compete with the genuine `d9ae50f8`
  (problem #3, retrieval hygiene task — no deletion, PASAL 3.8/13).
- **RAM/performance at batch scale** (problem #5): host saturated (0.07 GB free
  in prior measurements), IndoBERT cold load >30 s stage timeout, Stage C 29/44
  errors under sequential batch load; batch p95/stability unverified.
- **Browser E2E BLOCKED (environmental)** — dev server `127.0.0.1:5180`
  HTTP-unresponsive under memory pressure; user's dev server not restarted
  (unauthorized). Follow-up functionality IS proven at the API/runtime layer.
- Minor cosmetic: T09/T10 `trust` projection lags the reuse evidence (§B caveat).

Rekomendasi (tanpa pergantian model otomatis, PASAL 14):
1. ~~Restart + re-run Stage A for T09/T10~~ **DONE** — runtime 10/10 verified
   (Defect G/H found and fixed); F+G+H committed `ae8d4549`, not pushed.
2. ~~Stage B retrieval~~ **DONE (Defect I/J/K)** — CAPIL-01 top #1, no dumps, no
   503; I+J committed by owner `d1af1069`, tie-break+K committed `ee9bd224`, not
   pushed. **Stage B ANSWER still blocked** — see decision point below.
3. **Stage B decision (PASAL 14 stop-and-ask):** authorize CAPIL-01 re-extraction
   (document preparation, no source-PDF change) OR a context-selection/LLM-path
   change to assemble coherent prose from the word-shattered blocks. Until then
   Stage B remains an honest abstention (NOT PASS). Do NOT loosen grounding.
4. **Stage C ground truth + full batch** — capture verified per-SOP ground truth
   and adequate extraction, then run the full 170-scenario batch on a warmed
   backend; re-measure p@1 after Defect I.
5. **Retrieval hygiene** — exclude contentless evidence so the empty Aktif stub
   `75d5b40d` can never be cited as top grounding (general, data-free); investigate
   title-boost attractors and duplicate PIAK-03 entries. Do NOT mass-reindex before
   cause proven (PASAL 6.9); do NOT delete SOPs (PASAL 3.8/13).
6. **RAM/perf at batch scale + window-widening latency cost** — measure on a
   dedicated 8 GB runtime (close co-resident apps, operator action); consider a
   smaller candidate window or `num_ctx` 2048 / `num_predict` 128–256 experiments
   (PASAL 8) and warm-up; re-measure Stage A/batch p95 to recover the <5 s target.
   Config experiments, not applied here.
7. **Browser E2E** — re-run once the host has RAM headroom and the dev server responds.
8. Model swap is **NOT recommended**: per PASAL 14, retrieval/context/facet/grounding
   were checked first and are the proven causes; the 1B model is not the root cause.
   Stage B's blocker is document extraction quality, not the model.

**Dilarang menyatakan PRODUCTION READY** — Stage A golden set is 10/10 at real
runtime, but Stage B answers are blocked by document quality, Stage C full batch
and Browser E2E remain unverified, and the latency target is not met on build
`719b0d18`; full acceptance (PASAL 11) is NOT yet achieved.

---

## Deliverable index (PASAL 15)

1. Runtime baseline — `reports/runtime_baseline.md` (P0).
2. Multi-turn reproduction — `reports/repro/repro_operator_general_multiturn*.json`.
3. Root-cause analysis — `reports/root_cause_analysis.md` (Defects A–H, §10 langgraph, §13–14 Defect F, §15 historical, §16 G/H + runtime 10/10, **§17 I/J/K + Stage B OCR document-quality root cause + model-freeze restoration**).
4. Focused code fixes — `app/hermes/agent.py`, `app/language/engine.py`, `app/knowledge/grounding.py`, `app/models/ollama.py`, `app/security/v1_knowledge.py`, `app/language/semantic/indobert_client.py` (A/B/C/D `61ffd389`; E `5fe714f0`; F+G+H `ae8d4549`; I+J owner `d1af1069`; tie-break+K `ee9bd224`, **not pushed**).
5. Context Resolver / Retrieval tests — `tests/test_hermes_v1_context_*.py`, `tests/test_service_facts_table_multipath.py`, `tests/test_language_service_turn_facets.py` (E, 15), `tests/test_hermes_v1_contextual_followup.py` (F+G, 17), `tests/test_v1_knowledge_reuse_rebind.py` (G, 4), `tests/test_indobert_worker_proxy_env.py` (H, 1), **`tests/test_v1_search_candidate_window.py` (I, 3), `tests/test_v1_recovery_context_dump.py` (J, 2), `tests/test_v1_hydration_failsafe.py` (K, 3)**.
6. Real llama3.2:1b runtime results — `reports/repro/stage_a_piak03_runtime.json` (build `719b0d18`, 10/10); prior runs `stage_a_piak03_runtime_f86b1318.json`, `stage_a_piak03_runtime_bb166b4a.json`.
7. PIAK-03 / CAPIL-01 results — Stage A (§B), **`reports/repro/stage_b_capil01_runtime.json` (I/J/K re-run, retrieval fixed / answer abstains)**; prior `reports/repro/stage_bc_runtime.json` (stage_b); diagnostics `search_probe_b01.json`, `diag_capil01_facts.py`, `diag_hydration_valueerror.py`.
8. Active SOP report — `reports/repro/sop_inventory.json` (44 Aktif), `stage_bc_runtime.json` (stage_c).
9. Speed / RAM metrics — §D, `reports/repro/ram_snapshot.json`; I/J/K regression `reports/repro/fullsuite_ijk.log` (89 failed, 1535 passed).
10. Final PASS/PARTIAL/FAIL + recommendations — this report (**PARTIAL**).