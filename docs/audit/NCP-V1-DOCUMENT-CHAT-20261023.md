# Selected PDF Chat repair — 23 October 2026

Status: **HOLD**. Patch tested against the real stored PDF and real Ollama through the production HTTP router in-process. It has **not** been verified on the active backend or through the operator UI. No operator rating, content approval, or final acceptance was recorded.

Document: PERMOHONAN DATA PRIBADI, `DOC-SHA256-75d5b40df368e826f8dc5eace35ccc0daaaf26499b241a278962832334e8db50`.

## Reproduction and cause

`artifacts/document-chat-20261023/reproduce.py` was run against active port 8000 before production code changes. All three questions returned HTTP 200 but failed grounding. The requirements response cited exactly the requested ID; duration and procedure returned local-rule/no-evidence responses. The active review endpoint returned 404. Evidence is in `active-before.json`.

`trace-original.json` records a separate local composition of the production code, the stored extraction, retrieved chunks, model payload/raw output, and grounding result. It is not instrumentation of the already-running port 8000 process. The requirements prompt included header/legal text and the end of the procedure, but not the submission input row. The model refused; the source guard rejected the refusal. Short follow-ups could lose retrieval or enter ordinary conversation. The October 19 index record had no page metadata.

Both pages of the original, hash-addressed PDF were rendered and visually inspected. The first activity is “Menyampaikan Surat Permohonan” and its Kelengkapan cell is “Surat Permohonan” (page 1). The final row states “3 Hari Kerja” (page 2). Qualifications such as SQL/Oracle are in a separate header section and are not applicant requirements. There are 15 numbered activity rows across both pages.

## Change

- Knowledge now reads recognized activity tables from the hash-verified stored PDF when an authenticated operator explicitly selects one non-pilot document. This exact source read uses the existing Evidence contract; it does not upgrade a fuzzy retrieval result. It neither replaces the index nor changes stored document metadata.
- `pdf_sop.py` retains columns, row order, and physical page numbers. Requirements use the Kelengkapan cell of a recognized initial submission activity. Duration uses an explicit completed-service row's Keterangan value, never a sum or an intermediate step time. Procedure quotes the ordered activity cells. Unknown layouts retain the existing retrieval path.
- Hermes keeps document aspect follow-ups in the evidence path and does not ask for a service identity when a selected source already supplies scope.
- Existing model phrasing and source validation remain. Table answers get additional vocabulary checks. A procedure must preserve the complete ordered quote; invented destinations, missing steps, or reversed order are rejected. Fallback text is assembled from extracted cells and validated again. The explicit `Kelengkapan:` label is recognized as requirement evidence; no threshold was reduced.
- Citations carry only the pages supplying the selected facts. Source authority and revision validity remain unverified.

Files: `app/knowledge/pdf_sop.py`, `engine.py`, `grounding.py`, `app/security/v1_knowledge.py`, `app/hermes/agent.py`, and `tests/test_selected_pdf_chat.py`.

## Verification

Final relevant suite: **107 passed, 2 skipped**, exit 0. Optional LangGraph tests are skipped. JUnit: `artifacts/document-chat-20261023/tests.xml`.

Command from repository root:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_selected_pdf_chat.py tests/test_v1_sop_boundary.py tests/test_hermes_v1_conversation.py tests/test_sop_review.py tests/test_knowledge_pipeline.py tests/test_ncp_v1_chat_contract.py tests/test_knowledge_pipeline_api.py -q --tb=short --disable-warnings --junitxml=artifacts/document-chat-20261023/tests.xml
```

`http_check.py` used the actual production V1 router with authentication and real Ollama (`llama3.2:1b`), through FastAPI TestClient, in one session. All three requests returned HTTP 200, grounded=true, supports_claim=true, and exactly the chosen document ID:

| Question | Verified result | Citation |
|---|---|---|
| Apa persyaratan menurut SOP PERMOHONAN DATA PRIBADI? | Kelengkapan: Surat Permohonan; activity: Menyampaikan Surat Permohonan | Page 1 |
| Berapa lama waktu penyelesaiannya? | Menurut SOP: 3 Hari Kerja | Page 2 |
| Bagaimana prosedurnya? | All 15 extracted activity rows in source order | Pages 1–2 |

Evidence: `patched-http.json`; model traces: `trace-final.json`. The final HTTP run occurred after the procedure-order fix. Model wording that invented requirements/verification steps or an unsupported destination was rejected; the validated source quote was returned with `evidence_fast_path`. The harness also confirmed unchanged stored document/index metadata. HTTP TestClient is **not** proof that the service on port 8000 loaded this patch, and is not browser evidence.

## Workflow evidence

- **Graphify:** query succeeded outside sandbox after the sandbox launcher failed. It scoped inspection to Hermes, Knowledge, document boundary, projection, and tests. AST update was run; final log is `artifacts/document-chat-20261023/graphify.txt`. Existing parser errors for `patch_embedding_identity.py` and its temporary copy were observed on the earlier successful update.
- **Diagnosing Bugs:** active HTTP reproduction failed before changes. Ranked hypotheses were incomplete table chunks, lost follow-up context, rejected model additions, and lost pagination. Captured prompts/outputs and original PDF established the failures described above. Diagnostic hooks exist only in the artifact harness, not production logging.
- **TDD:** the task explicitly requested the HTTP Chat and operator UI seams. Regression tests were run red before fixes for follow-up routing, selected table evidence, model-invented content, truncated procedure, and reversed procedure order; then green. Synthetic PDFs use different facts (Surat Pengantar, 7 Hari Kerja), preventing dependence on document-specific answers. UI verification remains blocked.
- **Codebase Design:** PDF extraction and factual selection remain in Knowledge; Hermes reuses its existing service-facts/model/Trust path. No replacement backend, provider, database, index, schema migration, or model configuration was introduced. Ruled-table recognition is deliberately conservative; arbitrary PDF layouts are outside this repair.
- **Standards review:** an independent reviewer found the procedure-order weakness. It was reproduced with a failing test and fixed; re-review found no remaining Standards issue in the task delta.
- **Spec review:** a separate reviewer found the same order issue. Re-review found no remaining implementation issue; active-runtime and UI acceptance remain HOLD.

Baseline HEAD: `a06ac0d0c98ee6fa6cca3b592b726cf5d60de2ad`, with pre-existing uncommitted work. Exact pre-task versions of modified files are in `artifacts/document-chat-20261023/before/`; `task.diff` isolates this task. Existing edits and untracked work were retained. No commit, push, operator decision, or forced process termination was performed.

## Remaining blockers

Canonical `service/nusantara-service.ps1 restart -AllowStop` was attempted. Its returned status remained HOLD/owned=false for both services, despite process exit 0. Exit 0 is not accepted as successful deployment. The active process identity could not be read from this Windows session, so no port-based kill was attempted.

The subsequent authenticated check still found the original active build ID `sha256:dfdcd28a42471ed13daa3dd1822ec4bef90a742c210279136697ecd2c3e7da37` and a 404 at the review endpoint. Evidence: `active-status.json` and `service-status.json`. An environment/session able to verify and restart the project-owned services is needed before claiming active runtime success.

The connected computer/browser inventory returned no apps or browsers. Opening an in-app browser failed with `Browser is not available: iab`. Therefore no UI screenshot, three-turn browser trial, or operator acceptance is claimed. After a verified canonical restart, the same three questions must still be tested through the actual UI in one session. Final operator approval belongs to the user.
