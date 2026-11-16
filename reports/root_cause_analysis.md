# Root Cause Analysis — NUS-V1-LLAMA-RAG-001 (P2)

Contract: NUS-V1-LLAMA-RAG-001 (12 Nov 2026). Model freeze: `llama3.2:1b` via local
Ollama (restored to revision 2 during P0; runtime confirmed `llama3.2:1b`).
Scope: prove why the first question is answered but a short follow-up is wrong,
then fix the root cause minimally (PASAL 5, PASAL 13 P2/P3, PASAL 14).

## 1. Reproduction (evidence)

`reports/repro/repro_operator_general_multiturn.json`
Session `web-0ba54109-b54c-4092-90dc-929b1674195d`, operator GENERAL chat (no SOP binding).

| Turn | Question | Top evidence | provider_status | Response | Latency |
|------|----------|--------------|-----------------|----------|---------|
| T01 | Apa persyaratan permohonan data pribadi? | `…75d5b40d` "PERMOHONAN DATA PRIBADI" score **1.0** | ollama | abstention (`possible_unsupported_content`) | 44962 ms |
| T02 | Berapa lama? | none (`evidence=[]`) | local_rule | "Layanan apa yang Anda maksud?" | 582 ms |
| T03 | Biayanya? | none | ollama | echo "Biaya data pribadi?" | 1438 ms |
| T04 | Bagaimana prosedurnya? | none | local_rule | "Layanan apa yang Anda maksud?" | 164 ms |

CORRECTION (proven by `reports/repro/diag_defect_b.py` + `diag_piak03_docs.py`,
13 Nov 2026): the score-1.0 top hit `…75d5b40d` is an **empty stub**, NOT the right
document. Retrieval ranks it first only because of the exact-title boost
(`engine.py:117-118`). The genuine PIAK-03 SOP is a *different* document that is
**not Aktif**, so it is excluded from chat retrieval. See §3 for the full chain.
The context-persistence failure (Defect A) is real and independent of this.

## 2. Confirmed causal chain (Defect A — primary, context persistence)

Context Resolver (`app/hermes/agent.py`):
- L315 `previous = memory.service_context(session_id)` — last persisted SOP identity, else `{}`.
- L328 `turn = LanguageEngine.service_turn(user_input, previous.get('topic',''), intent)`.
- L329–331 scope is restored **only if** `previous['document_id']` AND `turn['uses_context']`.

`app/language/engine.py:504`:
`uses_context = bool(facet and not hint and previous_topic)`.
A short follow-up ("Berapa lama?") has `facet='duration'`, `hint=''`, so
`uses_context` is True **only when `previous_topic` is non-empty**.

Therefore restoring scope requires BOTH `previous['document_id']` and
`previous['topic']` to be present.

Where SOP identity is persisted (`service_context`):
- L539 init: `service_context = {} if conversation or (turn.facet and turn.topic_hint) else None`.
- L755 clarification branch: `{}` or `previous`.
- **L763 verified fast-path facts branch: `{topic, document_id, title}` — the ONLY place a real identity is stored.**
- L540 `/cari`: `previous`.
- **General Ollama/Hermes path (L818–L1101): `service_context` is NEVER assigned.** It keeps the L539 value (`{}` or `None`).
- L1176–1178 `remember_response(service_context=…)` → `gate_integration.py:107` → `memory.remember(..., service_context=…)`. `memory.service_context` (`engine.py:187`) returns `{}` when nothing usable was stored.

Why T01 took the general path instead of the fast path:
`service_answer_facts` (`grounding.py:46`) returns `None` when the turn has no
facet (L52) or when no evidence source matches the literal `^Persyaratan …:` line
(L65–74). The "PERMOHONAN DATA PRIBADI" source does not expose that exact pattern,
so `service_facts=None` → branch L759 skipped → general path L818 → identity not stored.

Result: T02 reads `previous={}` → `previous_topic=''` → `uses_context=False` →
scope not restored → unscoped retrieval on "Berapa lama?" returns nothing →
clarification. This is contract problem #2 (chat does not maintain SOP context)
and the follow-up half of problem #1.

## 3. Defect B — first-answer abstention: PROVEN root cause (data / approval)

Runtime probes (read-only, no data changed):
`reports/repro/diag_defect_b.py` replicates the live general-operator
`V1KnowledgeBoundary.search_knowledge`; `reports/repro/diag_piak03_docs.py`
inspects the PIAK-03 document cluster. Full text dumps: `reports/repro/docdump_*.txt`.

The PIAK-03 "Permohonan Data Pribadi" cluster contains THREE relevant documents:

| document_id | title | status | content | sop_rows |
|---|---|---|---|---|
| `…75d5b40d` | PERMOHONAN_DATA_PRIBADI.pdf | **Aktif** | `source_len=61`, extracted chunk **EMPTY** | 0 |
| `…d9ae50f8` | PERMOHONAN DATA PRIBADI | **Siap disetujui (approval perlu diperbarui)** — NOT Aktif | full SOP, 5220 chars | **15** |
| `…55e8c2f3` | Dasar Hukum Kualifikasi Pelaksana | Aktif | different service prose | 4 |

`…d9ae50f8` is the genuine PIAK-03 SOP (dump confirms `Nomor SOP: PIAK-03`,
`Nama S.O.P: PERMOHONAN DATA PRIBADI`). It holds every Stage-A ground truth:
- Row 1 `Menyampaikan Surat Permohonan` → Kelengkapan **`Surat Permohonan`** (T01).
- Row 15 `Proses pelayanan permohonan data selesai` → Waktu **`3 Hari Kerja`** (T02).
- No `Biaya` column → cost is **not stated**; must abstain, never "gratis" (T03, PASAL 7 Path C).
- 15-step activity flow (T04).

Causal chain for the T01 abstention:
1. The boundary eligibility gate (`app/security/v1_knowledge.py:138-141`) admits a
   pilot SOP only when `review.detail(...)['status'] == 'Aktif'`. `…d9ae50f8` is
   "Siap disetujui", so the **real source is correctly excluded** from chat.
2. The empty Aktif stub `…75d5b40d` matches the query title exactly and receives the
   +0.50 title boost (`engine.py:117-118`) → score 1.0 → ranks first, but its chunk
   and source are empty, so it grounds nothing.
3. `service_answer_facts` / `extract_requirement_statement` only recognise the prose
   `^Persyaratan <scope>: …` line. The pilot table projection instead renders
   `Kelengkapan pemohon pada tahap pengajuan: …` (`document_context.py:38-39`), and
   `table_facts` (which DOES read the table) is gated on `len(evidence)==1`
   (`pdf_sop.py:72`) — false in the 5-document general path. So `service_facts=None`.
4. The verified fast path (PASAL 7 Path A) never fires; the turn falls through to
   `llama3.2:1b`, which returns a generic greeting; `EvidenceGroundingGuard.validate`
   correctly rejects it (`possible_unsupported_content`) → honest abstention.

This is contract problem #6 ("Active SOP status does not guarantee accuracy")
manifesting as a data-integrity condition: **the Aktif document is empty while the
content-bearing document is pending approval.** The model is NOT the cause; per
PASAL 14 retrieval/approval/ground-truth were checked first and no model change is
warranted.

Resolution blocker (authorization): approving `…d9ae50f8` (or re-activating the
correct PIAK-03 source and retiring the empty stub) is an **SOP approval-status
change**, forbidden without operator authorization (PASAL 3.8, PASAL 11 "0
unauthorized SOP changes"). It must NOT be done unilaterally, and the approval gate
must NOT be bypassed in code. A general, data-free hygiene improvement (excluding
contentless evidence so an empty Aktif stub can never be cited as top grounding) is
safe but does NOT by itself restore PIAK-03 accuracy, because the genuine source
remains unapproved. Full Stage-A golden-set accuracy is therefore BLOCKED on this
operator decision.

## 4. Minimal fix (P3, Defect A)

Persist the SOP identity from confident top retrieval in the general model path,
mirroring the fast-path shape `{topic, document_id, title}`, guarded so it never
overrides an identity already set by another branch and never persists for
conversation / general-knowledge (no-evidence) turns. No new service/UI/DB, no
model swap, no embedding change, no public-knowledge-boundary change
(`app/security/v1_knowledge.py:116` fail-closed stays intact — public chat still
receives no evidence, so there is no identity to persist there).

## 5. Verification plan

- Unit (TDD): `tests/test_hermes_v1_context_persistence.py` with the real in-memory
  `GateIntegration` — (a) T01 general path persists identity; (b) T02 restores
  document scope into `search_knowledge(filter={'document_ids':[…]})`.
- Regression: existing `tests/test_hermes_v1_conversation.py`, `tests/test_v1_langgraph.py`.
- Runtime (real `llama3.2:1b`): re-run the operator general multi-turn reproduction
  against `127.0.0.1:8000`; confirm T02+ resolve the SOP instead of clarifying.

## 6. Defect C — HTTP 500 on the general Ollama path (FIXED, runtime-proven)

Root cause: `OllamaProvider._get_client` built `httpx.AsyncClient` with the default
`trust_env=True`. The ambient `NO_PROXY` contains an IPv6 entry `[::1]`; httpx parses
it into a URLPattern mount and raises `InvalidURL: Invalid port ':1]'` on the first
local request, surfacing as HTTP 500 (`routes.py:1375`). The local provider must
never inherit ambient proxy env.

Fix (minimal, `app/models/ollama.py`): `trust_env=False` on the single shared client
factory used by both `generate` and `health_check`. TDD regression:
`tests/test_ollama_provider_proxy_env.py` (RED before fix, GREEN after). Runtime:
T01 now returns HTTP 200 with `model_status=INFERENCE_VERIFIED`, `llama3.2:1b`.

## 7. Defect D — conversation-classified follow-up erases SOP identity (FIXED, runtime-proven)

Root cause (`app/memory/engine.py:187-191`): `service_context()` scans history
backwards and returns the FIRST item whose `metadata.service_context` is a dict.
`{}` **is** a dict, so a stored `{}` shadows any earlier real identity.

At `agent.py:539` a conversation-classified turn stores `service_context={}`.
A short follow-up that the language engine classifies as conversation (e.g.
"Biayanya?", "Siapa yang menangani?") therefore wrote `{}`, erasing the SOP
identity established at T01. The NEXT facet-bearing turn ("Bagaimana
prosedurnya?", "Apa yang harus dibawa?") then read `previous={}` →
`uses_context=False` → scope not restored → unscoped retrieval → failure.

Fix (minimal, general, `agent.py:540-543`, PASAL 5):
```python
# PASAL 5: a conversation-classified follow-up stores no new identity;
# {} would shadow the prior SOP identity in memory.service_context().
if conversation and previous.get('document_id'):
    service_context = previous
```
Conditioned on `previous['document_id']` so a genuine conversation with no prior
SOP still stores `{}` (existing `test_conversation_turn_does_not_persist_sop_identity`
remains green). TDD: `tests/test_hermes_v1_context_preservation.py` (2 tests, RED
before fix, GREEN after). No model/embedding/architecture change.

Runtime proof (Stage A, §9): before D the warm-worker run passed only T01/T02
(2/10); after D, T04 and T06 also pass (4/10). T04 follows conversation-classified
T03 and T06 follows conversation-classified T05 — both now restore scope because
D preserved the identity through those turns.

## 8. Defect E — facet-recognition gaps → unscoped 1B generation (FIXED, general; runtime-proven, Stage A 7/10)

Several short follow-ups were not recognised as a service facet, so
`uses_context=False` (`engine.py:504`), scope was never restored, retrieval returned
`ev=0`, and the unscoped `llama3.2:1b` path echoed or fabricated:

| Turn | Question | Before E | After E (runtime-proven) |
|---|---|---|---|
| T02 | "Berapa lama?" | duration ✓ fast path | unchanged |
| T08 | "Berapa hari kerjanya?" | **no** → unscoped 1B "3 hari" (ungrounded) | duration ✓ → table fast path "3 Hari Kerja" p2, ev=1 |
| T03 | "Biayanya?" | **no** → unscoped 1B echo | cost ✓ → Path C abstention "biaya belum tercantum" + citation, ev=1 |
| T05 | "Siapa yang menangani?" | **no** → unscoped 1B echo | who ✓ → Path C abstention "pelaksana belum tersedia" + citation, ev=1 |

Root cause: `service_turn` recognised only requirements/procedure/duration/channel;
"biaya", "siapa/menangani", and the "hari/kerjanya" duration phrasing fell through to
`facet=None`, leaving residual words in `topic_hint` so `uses_context=False`.

Minimal GENERAL fix (operator-authorized "Commit, then fix Defect E"; no model change,
no PIAK-03-only rule — PASAL 3.7/14):
- `app/language/engine.py` `service_turn`: add `cost` (biaya/tarif/harga/gratis/pungutan/
  retribusi) and `who` (siapa/pelaksana/petugas/menangani/penanggung jawab) aspects;
  extend `duration` with `hari(?:nya)?`/`kerjanya` (NOT bare "kerja", so "cara kerja"
  stays procedure); facet priority `duration,cost,who,channel,requirements,procedure`;
  prefixes `cost:'biaya'`, `who:'pelaksana'`.
- `app/hermes/agent.py:640`: add `'who':'ask_general_info'` to the intent map (KeyError guard).
- `app/knowledge/grounding.py`: `_cost_absence_fact` mirrors the proven general rule in
  `document_answers.py:48-50` — abstain only when the full source states no fee at all
  (never infer "free" from an empty cost column, PASAL 7 Path C); `_who_absence_fact`
  abstains with a citation when the activity table exposes no per-row actor (never
  invent a handler from a swimlane position, and never dump raw table-context
  scaffolding to the user). Both hooks fire only on a single scoped table match.
  Prose branch separates `cost`/`channel` so cost/who never reuse the channel quote;
  abstention subject map adds `cost:'biaya'`, `who:'pelaksana'`. `table_facts` still
  excludes cost/who (no invented cells).

Tests: `tests/test_language_service_turn_facets.py` 15/15 (RED→GREEN, generic table fixture,
not PIAK-03; who test strengthened to require a clean cited abstention, not a clarify-dump).
Targeted regression `-k "service_answer or grounding or service_turn or facet or abstention
or clarify or table_facts or pdf_sop or document_answer"`: 70 passed, 1 failed — the single
failure is the pre-existing langgraph wrapper test (§10), not a new regression. Full-suite
identical-scope HEAD comparison (zero new failures from E) and live Stage A re-run recorded
in §9 / acceptance report.

## 9. Stage A runtime results (real llama3.2:1b, warm worker, after Defect E fix)

`reports/repro/stage_a_piak03_runtime.json`, session
`web-d27dd551-f4f5-4ee7-9047-f951806b4a76`, build `sha256:9809dcd9…`, pid 9276,
operator GENERAL chat (no binding), genuine PIAK-03 SOP `…d9ae50f8` (Aktif, score 1.0).
Ground truth from `piak03_capil01_versions.json` (Row 1 → "Surat Permohonan" p1;
Row 15 → "3 Hari Kerja" p2; no Biaya column; no per-row actor; 15-step flow).

| Turn | Question | provider_status | grounded | ev / doc | Response (abridged) | wall_ms | Verdict |
|---|---|---|---|---|---|---|---|
| T01 | Apa persyaratan permohonan data pribadi? | evidence_fast_path | True | 1 / d9ae50f8 p1 | "Siapkan Surat Permohonan." | 5660 | **PASS** |
| T02 | Berapa lama? | evidence_fast_path | True | 1 / d9ae50f8 p2 | "Menurut SOP: 3 Hari Kerja." | 1721 | **PASS** |
| T03 | Biayanya? | evidence_fast_path | True | 1 / d9ae50f8 p1+2 | "Informasi biaya belum tercantum dalam SOP ini." | 373 | **PASS** (Path C abstention + citation) |
| T04 | Bagaimana prosedurnya? | evidence_fast_path | True | 1 / d9ae50f8 p1+2 | full 15-step procedure | 11675 | **PASS** |
| T05 | Siapa yang menangani? | evidence_fast_path | True | 1 / d9ae50f8 p1+2 | "Informasi pelaksana belum tersedia dalam SOP ini." | 294 | **PASS** (Path C abstention + citation) |
| T06 | Apa yang harus dibawa? | evidence_fast_path | True | 1 / d9ae50f8 p1 | "Siapkan Surat Permohonan." | 5106 | **PASS** |
| T07 | Kalau persyaratannya kurang? | ollama | False | 0 | "Saya tidak memiliki informasi tentang SOP ini." | 2683 | FAIL-helpfulness / SAFE (conditional, not a facet) |
| T08 | Berapa hari kerjanya? | evidence_fast_path | True | 1 / d9ae50f8 p2 | "Menurut SOP: 3 Hari Kerja." | 2267 | **PASS** |
| T09 | Bisa dijelaskan lebih sederhana? | ollama | False | 0 | safe abstention | 3164 | FAIL-helpfulness / SAFE (conversational) |
| T10 | Dari halaman berapa informasi tersebut? | ollama | False | 0 | safe abstention | 4658 | FAIL-helpfulness / SAFE (citation follow-up) |

**Golden set: 7/10 PASS (T01, T02, T03, T04, T05, T06, T08)** — up from 4/10 after D.
Core problems #1 (first/follow-up), #2 (SOP context), #3 (wrong/missing evidence) and
#6 (Active SOP accuracy) are FIXED for every service-facet follow-up
(requirements/duration/procedure/cost/who), with correct page citations.
**Unsupported factual claims: 0** (target MET) — T07 now abstains instead of the
pre-E "Tidak."; T08 is grounded "3 Hari Kerja" p2 instead of the pre-E ungrounded
"3 hari". T07/T09/T10 produce the safe abstention text (no fabrication,
`requires_human=True`). 0 crashes, 0 cross-session leaks (single session),
0 unauthorized SOP changes.

Residual 3 failures (T07 conditional "kalau persyaratan kurang", T09 simplification
request, T10 page-citation follow-up) are **conversational/meta follow-ups, not service
facets** — outside Defect E's facet-recognition scope. They need broader PASAL 5/7
conversational-follow-up handling (recognise a conditional/simplification/citation
follow-up and re-use the prior grounded answer), not a model change (PASAL 14).
Per PASAL 11, <100% golden set ⇒ **PARTIAL**, not PASS.

## 10. Pre-existing langgraph test failure (attributed to HEAD, NOT caused by A/B/C/D)

`tests/test_v1_langgraph.py::test_existing_grounding_rejects_missing_evidence_and_unsupported_claim[True-None]`
fails with `UNGROUNDED_RESULT`. Attribution: reverted D (still fails), then
`git stash` of all three tracked changes (agent.py, grounding.py, ollama.py) and
ran at HEAD — **still fails**. Therefore PRE-EXISTING, independent of this work.

Cause: the opt-in LangGraph wrapper's `_evidence` node
(`app/workflow/v1_langgraph.py:97-122`) raises `UNGROUNDED_RESULT` when an
ungrounded core response is not the exact safe-abstention text; the empty-evidence
general path under the wrapper does not produce that text. This relates to problem
#4 but is specific to the opt-in wrapper. NOTE: the live DEFAULT runtime path
(`features.langgraph_workflow=False`, used for Stage A) DID produce the safe
abstention on T09/T10 — so the default path is safe. Beyond the authorized scope;
recorded, not fixed.

## 11. RAM / latency findings (PASAL 8, 8 GB CPU-only)

`reports/repro/ram_snapshot.json` (during runtime): total **7.68 GB**, available
**0.07–0.27 GB** (near saturation). Top consumers: `llama-server` (Ollama model
runner for llama3.2:1b) **973 MB**; Windows **Memory Compression 1.3 GB** (heavy
paging pressure); co-resident Qoder ~568 MB, Defender 159 MB, Edge WebView ~141 MB,
ChatGPT desktop ~85 MB. The backend + IndoBERT worker working sets are trimmed
under pressure (not in top 15), which contributes to first-request cold-load
latency after idle. The 1B model footprint (~1 GB) is appropriate for 8 GB; the
saturation is environmental contention + IndoBERT residency + compression overhead.

Latency (Stage A wall_ms, post-E run §9): non-LLM fast path T03=373, T05=294,
T02=1721, T08=2267 (<5 s steady state); T01=5660 and T06=5106 marginally exceed 5 s
(first-turn cold residue / requirements rendering), and T04=11675 (15-step procedure
rendering) exceeds the PASAL 11 p95<5 s non-LLM target ⇒ target NOT met on this run
(the heavy procedure turn dominates p95). IndoBERT cold load ~30.6 s exceeds the 30 s
stage timeout; warm-up (`warmup_worker.py`) is required before acceptance runs. No
model reload per request; worker stays resident.

## 12. Current status (13 Nov 2026)

- Defect A (general-path identity persistence): FIXED, runtime-proven.
- Defect B (table fast-path / first-answer abstention): FIXED, runtime-proven —
  T01 grounded "Siapkan Surat Permohonan." from genuine `…d9ae50f8`.
- Defect C (proxy-env HTTP 500): FIXED, runtime-proven (HTTP 200, llama3.2:1b).
- Defect D (conversation follow-up erases identity): FIXED, runtime-proven —
  Stage A improved 2/10 → 4/10 (T04, T06 now pass).
- Defect E (facet-recognition gaps): FIXED, general, runtime-proven (§8/§9) —
  cost/who/duration-phrasing follow-ups restore SOP scope; Stage A 4/10 → 7/10,
  unsupported factual claims 2 → 0. Residual T07/T09/T10 are conversational/meta
  follow-ups (conditional, simplification, page-citation), outside facet scope.
- Pre-existing langgraph wrapper failure: attributed to HEAD (§10), out of scope.
- SOP approval: only `…d9ae50f8` approved (operator-authorized, prior session).
  Empty Aktif stub `…75d5b40d` left untouched (no unauthorized status/source change).
- Model freeze intact: llama3.2:1b via local Ollama; no swap, no embedding change,
  no paid API, no new service/UI/DB.
- Acceptance: **PARTIAL** (Stage A 7/10; Stage B/C and metrics in the acceptance
  report). NOT production-ready; PASAL 11 full pass requires 100% golden set.
- Defect E code (engine.py, agent.py, grounding.py + facet tests): COMMITTED as
  `5fe714f0` (operator-authorized "Commit E (no push)"); A/B/C/D bundle is `61ffd389`.
  Not pushed.

## 13. Defect F — conversational/meta follow-ups drop SOP scope (CORE FIXED; T09/T10 residual)

The 3 residual Stage A failures (T07/T09/T10) are NOT service facets; they are
conversational/meta follow-ups. Root cause (code-traced, `app/hermes/agent.py`):

- Scope restoration (L329-331) is gated on `turn['uses_context']`, which requires a
  service facet (`engine.py:504`). A non-facet follow-up never restores the prior SOP
  scope even when `previous['document_id']` exists.
- **T09** "Bisa dijelaskan lebih sederhana?" and **T10** "Dari halaman berapa informasi
  tersebut?" match `_CONTEXTUAL_FOLLOWUP` (L118: "lebih sederhana", "tersebut"), so
  L351-353 sets `conversation=False` — but `scoped_document_ids` stays `[]` (L329 not
  triggered) → unscoped retrieval → `ev=0` → general ollama abstention. Recognised as a
  follow-up, yet the scope is dropped.
- **T07** "Kalau persyaratannya kurang?" → `facet=requirements`, but the conditional
  modifier "kurang" leaves `topic_hint={'kurang'}` → `uses_context=False`; and
  `_CONTEXTUAL_FOLLOWUP` does not match conditionals → scope not restored → unscoped →
  `ev=0` → abstention.

Runtime evidence (`stage_a_piak03_runtime.json`): T07/T09/T10 all `provider_status=ollama`,
`grounded=False`, `ev=0`, safe abstention (no fabrication). `previous.document_id` is
`d9ae50f8` (restored by T08), so the identity EXISTS but is not re-used for these turns.
This is contract problem #1/#2 on the residual conversational turns (PASAL 5).

Minimal GENERAL fix proposal (no model change, no PIAK-03-only rule — PASAL 3.7/14):
1. Restore prior SOP scope for a recognised contextual follow-up even without a facet:
   extend L329 to also fire when `previous['document_id']` and
   `_CONTEXTUAL_FOLLOWUP.search(user_input)` (T09/T10). Scoped retrieval then returns the
   prior SOP evidence; VERIFY the general path answers the citation/simplification
   grounded (a small citation/rephrase fast-path may still be needed — restoring scope is
   the necessary first step, not proven sufficient).
2. Recognise conditional follow-ups ("kalau/jika … kurang/tidak lengkap") as
   context-bearing (T07), restoring scope. The SOP does not state the conditional, so the
   correct outcome is a GROUNDED abstention (ev>0, cited), never a fabricated policy.
   Higher risk; needs careful grounding tests (PASAL 7 Path C).

Operator authorized "Authorize + implement F" (this session). Implemented as a
minimal GENERAL fix (no model/embedding change, no PIAK-03-only rule — PASAL 3.7/14):
- `app/language/engine.py` `service_turn`: add a general `conditional` flag
  (kalau/kalo/jika/bila/apabila/seandainya/umpama/misal).
- `app/hermes/agent.py`: `_contextual_scope_followup()` recognises anaphoric
  (`_CONTEXTUAL_FOLLOWUP`), possessive-facet ("-nya"), and conditional follow-ups
  whose residual hint is a modifier (not a new service name); the scope-restoration
  gate (L329) now also fires for these, so the prior SOP scope is restored. A
  new-service hint ("akta kelahiran") never restores prior scope (PASAL 5 switch).
- `app/knowledge/grounding.py`: `_conditional_absence()` — Path C cited abstention
  for a conditional follow-up on a validated SOP table ("Informasi ketentuan belum
  tercantum dalam SOP ini."), never a facet cell or invented policy.

TDD: `tests/test_hermes_v1_contextual_followup.py` (12 tests, RED→GREEN, generic
fixtures). Focused suites 113/113 green; broad scope 41 failed = identical
pre-existing HEAD set, zero failures in F-changed areas, +12 new tests pass.

## 14. Defect F runtime results (real llama3.2:1b, warm worker, build 53b6d3c0)

`reports/repro/stage_a_piak03_runtime.json` regenerated, backend pid 17780, build
`sha256:53b6d3c053a436f2a05e3ecf48e15a729298de9651a967984ab08a4b1f4cebba`.

**Stage A 7/10 → 8/10.** T07 "Kalau persyaratannya kurang?" now PASS:
`evidence_fast_path`, grounded=True, ev=1, doc d9ae50f8, cited abstention
"Informasi ketentuan belum tercantum dalam SOP ini." T01–T08 all grounded with the
correct SOP + page citations; **0 unsupported factual claims**.

Residual T09/T10 (still FAIL, safe): scope IS restored (scoped_document_ids=
[d9ae50f8]) but the contextual re-retrieval query (prior question + current
message) returns ev=0 → the scoped-no-evidence `local_rule` branch (agent.py:846)
abstains "Informasi tersebut tidak ditemukan dalam dokumen yang dipilih."
Restoring scope is necessary but NOT sufficient: a simplification (T09) or page
citation (T10) must be answered from the PRIOR turn's evidence, not a fresh
retrieval. Next step (further extension, needs authorization): reuse the prior
SOP evidence for a recognised contextual follow-up and add a grounded
citation/rephrase fast-path. The 1B model's ability to produce a grounded
simplification/citation is unverified; not claimed as fixed.

## 15. Defect F residual — prior-answer reuse IMPLEMENTED (test-layer verified; runtime PENDING)

The §14 next step is now coded under the operator's "Authorize + implement F"
(T09/T10 are part of F). Minimal, general change in `app/hermes/agent.py` only:

1. **Grounded-answer snapshot persistence** (before `remember_response`, ~L1276):
   when a turn produces a grounded answer with evidence and a `document_id`,
   `service_context` gains a compact `last_answer` {text, pages, title, document_id,
   source[:2000], chunk[:1000], score}. Keyed on document identity — not SOP-specific.
2. **Deterministic Path-A reuse fast-path** (~L852, before the scoped-no-evidence
   `local_rule` branch): for a recognised contextual follow-up
   (`_contextual_scope_followup`) with restored scope AND a prior `last_answer`,
   a citation request (`_CITATION_REQUEST`: halaman/sumber/dari mana/referensi/rujukan)
   answers "Informasi tersebut berasal dari {title}, halaman {pages}." and a
   simplification request (`_SIMPLIFY_REQUEST`: lebih sederhana/ringkas/…) reuses the
   prior grounded answer text. No re-retrieval, no LLM, no new facts; grounded=True,
   `evidence_fast_path`, citation evidence reconstructed from the snapshot.

This directly removes the §14 ev=0 dead-end: T09/T10 no longer depend on a fresh
contextual re-retrieval. General markers; a new-service hint still never restores
prior scope (guard test retained). No model/embedding/architecture change.

**Test-layer evidence (PASAL 10 A/B):**
- Focused: `tests/test_hermes_v1_contextual_followup.py` + context persistence/
  preservation = **20 passed** (0.90 s), including 3 new reuse tests
  (simplification reuses prior text; citation reuses prior pages [2,3]; no prior
  answer ⇒ no fabricated citation). File total 12 → **15 green**.
- Full suite: **92 failed, 1518 passed, 9 skipped, 2 errors** (223 s). Normalized
  FAILED-set `comm` vs the prior full-suite baseline `reports/repro/full_suite_e2.log`
  (92 failed, 1503 passed): **identical 92 = 92, zero only-in-baseline, zero
  only-in-current**. The +15 passed are exactly the new contextual-followup tests.
  **Attribution: ZERO new regressions from F core + residual.** Log:
  `reports/repro/regression_F_residual.log`.

**Runtime status: PENDING / BLOCKED (honest, PASAL 3.9).** The live backend
(pid 17780, build `sha256:53b6d3c0…`) loads code once at import and still runs the
F-core build, NOT this residual edit. Re-verifying T09/T10 against real llama3.2:1b
requires restarting that backend; the operator **declined** the restart this pass,
so no runtime re-run was performed. T09/T10 are therefore proven at the test layer
only and are **NOT claimed as runtime PASS**. Stage A runtime remains **8/10** until
a restart + Stage A re-run confirms the reuse path end-to-end. F (core + residual)
remains **uncommitted** (implementation authorized; commit not authorized).

## 16. Defect F residual — runtime 409 diagnosed + fixed; Stage A 10/10 (real runtime)

Supersedes §15's "runtime PENDING". The operator's "Jalankan semua yang belum
selesai" authorized the restart + re-run. Two distinct runtime defects surfaced
and were fixed minimally (TDD RED→GREEN for each):

**Defect G — reuse citation not bound by the knowledge boundary (HTTP 409).**
First restart (build `03f05cb8`): T01–T08 PASS, but T09/T10 returned **HTTP 409**
(~230 ms). Diagnosis (no traceback; route-level): persisted history for session
`web-51ffd922…` shows both turns reserved `NEW` then `FAILED HTTP_409_UNKNOWN`
(`reports/repro/hist_51ffd922.json`) ⇒ the 409 was raised DURING processing, not
by the idempotency gate. Source: `routes.py:1328 knowledge.validate_response(public)`
→ `v1_knowledge.py` `CHAT_SOURCE_VERSION_UNAVAILABLE`: the reuse fast-path cited
the prior SOP although this turn's scoped re-retrieval returned ev=0, so the
boundary's retrieval-time `_versions` map had no entry for the cited document.
The §15 reuse path was functionally right but violated the boundary's
fail-closed version guarantee.

Fix (general, security-preserving):
- `app/security/v1_knowledge.py`: new `V1KnowledgeBoundary.reuse_prior_citation(document_id)`
  — re-validates the source NOW (operator + local ollama; pilot ⇒ status Aktif /
  trial version match; non-pilot ⇒ document exists) and records the CURRENT
  version, so `validate_response` keeps its guarantee. Missing/inactive source ⇒
  409 (fail closed).
- `app/hermes/agent.py` reuse branch: calls the rebind BEFORE emitting the reused
  citation; on rejection falls back to the safe scoped `local_rule` abstention
  (no unbound citation ever leaves the agent).
- Tests: `tests/test_v1_knowledge_reuse_rebind.py` (4: bind+validate, missing
  source 409, operator/local-model guard, source-change detection) and 2 new
  agent tests (ev=0 follow-up + successful rebind ⇒ reuse fires; rejected rebind
  ⇒ abstain, no evidence, `local_rule`). Harnesses gained a rebind stub.

**Defect H — worker subprocess inherits ambient proxy env (Defect C class).**
After the G fix, warmup still failed (503, embedding RuntimeError). The backend
hides worker stderr (DEVNULL); direct worker diagnostic
(`reports/repro/diag_worker_stderr.py`) captured the real crash: at import time
`huggingface_hub` builds a global httpx client that parses ambient
`NO_PROXY=localhost,…,[::1],::1` → `httpx.InvalidURL: Invalid port: ':1]'`.
The worker died before loading the model; every embedding failed.
Fix: `app/language/semantic/indobert_client.py` `start()` strips all proxy
variables (HTTP(S)_PROXY/ALL_PROXY/NO_PROXY, both cases) from the child env —
the worker is local/offline with a cached model and never needs them.
Test: `tests/test_indobert_worker_proxy_env.py` (spawn-env capture). No model,
embedding-dimension, or architecture change.

**Runtime proof (PASAL 10 layer C — real Ollama llama3.2:1b, warm worker).**
Backend build `sha256:f86b1318…` (pid 18552), probe 200/ev=1/d9ae50f8, then
Stage A re-run (`reports/repro/stage_a_piak03_runtime.json`, session in file;
log `reports/repro/backend_f_rebind2.log`): **10/10 PASS**, all turns grounded,
ev=1, doc d9ae50f8, **0 unsupported claims**, all POST 200, 0 tracebacks/409/500.
- T09 "Bisa dijelaskan lebih sederhana?" → `evidence_fast_path`, reuses the prior
  grounded answer ("Menurut SOP: 3 Hari Kerja."), 144 ms, no LLM, no new facts.
- T10 "Dari halaman berapa informasi tersebut?" → "Informasi tersebut berasal
  dari PERMOHONAN DATA PRIBADI, halaman 2.", 153 ms, correct SOP + page citation.
Progression: 2/10 → 4/10 → 7/10 → 8/10 → **10/10**.

**Regression (PASAL 10 layer B):** final clean full suite after G+H
(`reports/repro/regression_F_rebind.log`, Ollama running, single run):
**89 failed, 1527 passed, 10 skipped, 2 errors** (224.7 s) vs identical-scope
HEAD baseline (`full_suite_e2.log`, 92 failed). Normalized FAILED-set `comm`:
**zero only-in-current**; 3 only-in-baseline
(`test_pdf_approval_activates_operator_retrieval_without_manual_chat`,
`test_create_retriever`, `test_knowledge_search_still_works`) — the langchain
pair is the documented ordering-flaky one (passes in isolation). **ZERO new
regressions from F+G+H.** Two earlier full-suite attempts were killed mid-run
by host RAM saturation / concurrent orphaned pytest trees sharing one log
(logs truncated, no summary) — not test failures; the successful run was
executed with the backend temporarily stopped to free RAM.