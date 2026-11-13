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

## 8. Defect E — facet-recognition gaps → unscoped 1B generation (DIAGNOSED, out of authorized scope)

Several short follow-ups are not recognised as a service facet, so
`uses_context=False` (`engine.py:504`), scope is never restored, retrieval returns
`ev=0`, and the unscoped `llama3.2:1b` path echoes or fabricates:

| Turn | Question | Recognised? | Result |
|---|---|---|---|
| T02 | "Berapa lama?" | duration ✓ | fast path, grounded "3 Hari Kerja" |
| T08 | "Berapa hari kerjanya?" | **no** (intent=unknown) | unscoped 1B "3 hari" (ungrounded) |
| T03 | "Biayanya?" | **no** (ask_general_info) | unscoped 1B echo |
| T05 | "Siapa yang menangani?" | **no** (intent=unknown) | unscoped 1B echo |

This is contract problem #3 (wrong/missing evidence) and #4 (unsupported info)
on the residual turns. The operator explicitly chose NOT to fix Defect E in this
pass (authorization limited to the minimal Defect D fix). It is recorded here as
the proven remaining root cause; fixing it requires general facet/context
recognition work (PASAL 5/7), not a model change (PASAL 14).

## 9. Stage A runtime results (real llama3.2:1b, warm worker, after Defect D fix)

`reports/repro/stage_a_piak03_runtime.json`, session
`web-f2787751-05cb-4331-be17-955c6fc83014`, operator GENERAL chat (no binding),
genuine PIAK-03 SOP `…d9ae50f8` (Aktif, score 1.0). Ground truth from
`piak03_capil01_versions.json` (Row 1 → "Surat Permohonan" p1; Row 15 → "3 Hari
Kerja" p2; no Biaya column; 15-step flow).

| Turn | Question | provider_status | grounded | ev / doc | Response (abridged) | wall_ms | Verdict |
|---|---|---|---|---|---|---|---|
| T01 | Apa persyaratan permohonan data pribadi? | evidence_fast_path | True | 1 / d9ae50f8 p1 | "Siapkan Surat Permohonan." | 14225 | **PASS** |
| T02 | Berapa lama? | evidence_fast_path | True | 1 / d9ae50f8 p2 | "Menurut SOP: 3 Hari Kerja." | 2845 | **PASS** |
| T03 | Biayanya? | ollama | False | 0 | "Biaya permohonan data pribadi?" (echo) | 3205 | FAIL (E; no fabricated cost) |
| T04 | Bagaimana prosedurnya? | evidence_fast_path | True | 1 / d9ae50f8 p1+2 | full 15-step procedure | 10820 | **PASS** |
| T05 | Siapa yang menangani? | ollama | False | 0 | "User: Siapa yang menangani?" (echo) | 2388 | FAIL (E) |
| T06 | Apa yang harus dibawa? | evidence_fast_path | True | 1 / d9ae50f8 p1 | "Siapkan Surat Permohonan." | 4008 | **PASS** |
| T07 | Kalau persyaratannya kurang? | ollama | False | 0 | "…Assistant: Tidak." | 2729 | FAIL (E; unsupported) |
| T08 | Berapa hari kerjanya? | ollama | False | 0 | "Hari kerjanya adalah 3 hari." | 1439 | FAIL (E; ungrounded, value coincidentally correct) |
| T09 | Bisa dijelaskan lebih sederhana? | ollama | False | 0 | safe abstention | 8221 | FAIL-helpfulness / SAFE |
| T10 | Dari halaman berapa informasi tersebut? | ollama | False | 0 | safe abstention | 4631 | FAIL-helpfulness / SAFE |

**Golden set: 4/10 PASS (T01, T02, T04, T06).** Core problems #1 (first/follow-up),
#2 (SOP context) and #6 (Active SOP accuracy) are FIXED for the
requirements/duration/procedure fast-path facets, with correct page citations.
Residual 6 failures are Defect E (§8). Unsupported factual claims: T07 ("Tidak."),
T08 ("3 hari" ungrounded) = 2 (target 0 NOT met). T09/T10 produced the safe
abstention text (no fabrication). 0 crashes, 0 cross-session leaks (single session),
0 unauthorized SOP changes. Per PASAL 11, <100% golden set ⇒ **PARTIAL**, not PASS.

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

Latency (Stage A wall_ms): non-LLM fast path T02=2845, T06=4008 (<5 s steady state),
but T01=14225 (first-turn cold residue) and T04=10820 (15-step procedure) exceed the
PASAL 11 p95<5 s non-LLM target ⇒ target NOT met on this run. IndoBERT cold load
~30.6 s exceeds the 30 s stage timeout; warm-up (`warmup_worker.py`) is required
before acceptance runs. No model reload per request; worker stays resident.

## 12. Current status (13 Nov 2026)

- Defect A (general-path identity persistence): FIXED, runtime-proven.
- Defect B (table fast-path / first-answer abstention): FIXED, runtime-proven —
  T01 grounded "Siapkan Surat Permohonan." from genuine `…d9ae50f8`.
- Defect C (proxy-env HTTP 500): FIXED, runtime-proven (HTTP 200, llama3.2:1b).
- Defect D (conversation follow-up erases identity): FIXED, runtime-proven —
  Stage A improved 2/10 → 4/10 (T04, T06 now pass).
- Defect E (facet-recognition gaps): DIAGNOSED (§8), operator chose not to fix now.
- Pre-existing langgraph wrapper failure: attributed to HEAD (§10), out of scope.
- SOP approval: only `…d9ae50f8` approved (operator-authorized, prior session).
  Empty Aktif stub `…75d5b40d` left untouched (no unauthorized status/source change).
- Model freeze intact: llama3.2:1b via local Ollama; no swap, no embedding change,
  no paid API, no new service/UI/DB.
- Acceptance: **PARTIAL** (Stage A 4/10; Stage B/C and metrics in the acceptance
  report). NOT production-ready; PASAL 11 full pass requires 100% golden set.