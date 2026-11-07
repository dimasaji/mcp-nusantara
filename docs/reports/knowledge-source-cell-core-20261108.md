# Shared Knowledge source-cell core — 8 November 2026

Baseline: `32e36758d5e060d20bbb261dd9b3d7cb06dd5901`, continuing PR #8.

## Scope and acceptance

Implement the user's requested autopilot fix to the Knowledge core, without per-document answer handlers, new operator forms, V2, automatic production approval, destructive migrations or a replacement engine. Preserve the current FastAPI, Docling/Tesseract/OpenCV, RAG and approval interfaces. Existing libraries cover this work; no additional production dependency is needed.

Acceptance: native digital and scanned tables supply the same `activity_rows` schema; original Docling cells/JSON and physical pages remain available; unreadable numbering or merged/overlapping cells cannot become certified procedures; requirements include explicit submission and initial intake-checklist cells rather than only row one; later internal documents are excluded from this shortcut; first-step questions remain scoped to that step. Verify the actual archived CAPIL-01 with 17 explicit source numbers, requirements from its second step, and the four-working-day duration on page 3. Verify persistence, duplicate uploads, operator-only publication and source-backed chat through isolated test storage. Native IndoBERT/Ollama and the user's Windows installation are separate deployment checks.

## Diagnosis and red/green evidence

- `normalize_activity_grids()` returned the original payload without `activity_rows` for scanned PDFs. A two-page synthetic Docling-cell regression failed with `KeyError: activity_rows` before the adapter was added.
- Replaying real CAPIL Docling output through the new adapter revealed missing numbers: both activity tables failed `ACTIVITY_TABLE_NUMBER_COLUMN_AMBIGUOUS`. TableFormer had reconstructed the tables but OCR omitted small digits. A whole-column read misread the first digit at low confidence; isolated cell reads recovered it but missed two other digits. The implementation accepts complementary high-confidence reads, refuses disagreement, and never fills missing numbers from row position. Real source crops then supplied digits 1–17.
- Initial source-cell normalization revealed that the duration cell existed but its `Keterangan` header was lost. The duration fact was absent. The worker now preserves OCR headers before table reconstruction and can re-read the bounded header band. An exact header is linked only to one geometrically matching body column; ambiguous matches remain unlabelled. No cross-document schema or document-specific answer is used.
- A requirements regression initially returned no facts for upload/checklist-style procedures. The shared selector now reads the initial submission/intake phase, deduplicates identical cells, stops before internal work and supports explicit first-step questions. The model-invention chat regression verifies that unrelated documents/costs do not enter the answer.

## Implementation and tradeoffs

`sop_tables.py` adapts Docling offset/span cells to the existing row contract and combines them with native physical-grid rows. It retains source-cell provenance and refuses incomplete numbering, duplicate/gapped sequences, overlapping cells and merged semantic columns. Invalid activity data is `PARTIAL` with diagnostic warnings and no authoritative activity rows. Existing strict PDF reads block publication/chat of partial extractions. Ordinary non-activity/prose documents retain their previous path.

`sop_table_ocr.py` is an adapter to the existing worker Tesseract installation. Bounded number/header crops only supplement source evidence; original `table_data` and Docling JSON are unchanged. Numbers require at least 90 confidence and no conflicting high-confidence reading. This is not a guarantee of OCR correctness. Header association uses source coordinates; unreadable/ambiguous fields can remain unavailable. Rescue currently requires a single number column directly before the activity column; other layouts fail conservatively.

`normalize_activity_grids()` retains native table geometry as its preferred path and supplies corresponding cell provenance. Both paths converge before retrieval. Full-document text includes all table blocks, so omission of a search projection cannot establish absence of cost/contact information. `pdf_sop.py`, `document_answers.py` and `document_context.py` share requirement selection; internal paperwork does not become an applicant checklist merely by occupying a later row. This deterministic selector covers explicitly recognisable initial intake wording, not every possible legal/service formulation.

Parser/config fingerprints are incremented (`adapter-10-source-cell-core`, `source-cell-core-4`) so old extractions cannot silently bypass the new logic. Existing approvals are not copied to changed extraction revisions. No production data or approval was modified.

## Verification and review

Real OCR outputs remain temporary; no full official-document transcription is published with this change.

- Final related backend regression suite: **130 passed, 2 native tests skipped** in 8.89 seconds across 15 modules (table core, answers/context, selected-PDF chat, layout, review/publication, pipeline/execution API, ingestion, metadata, boundary, search and Golden SOP chat).
- Full real Docling/Tesseract run: **8 passed** in 120.83 seconds. The native test verifies source numbers **1–17**, both activity pages, requirement phrases `Surat Keterangan Lahir` and `Alamat Email`, and **4 Hari Kerja** on physical page **3**. This verifies these acceptance facts, not every OCR word or every possible question. A subsequent idempotence-only normalization fix was checked by replaying the real extraction through the final adapter and repeating normalization; ordered rows, requirements, duration and identical second-pass output all passed.
- Isolated persistence/integration checks use real temporary SQLite storage and fixture embeddings/inference: approved tables survive reopening storage and answer source-backed questions, renamed re-uploads remain duplicates, public chat cannot retrieve the SOP, and invalid step structure remains PARTIAL, cannot be approved and cannot be read through the strict document-chat interface. Model-invention tests reject unrelated requirements/costs.
- Standards review found source-number sorting could hide reversed steps; the red regression now passes because physical table/row order is preserved before sequence validation. Both reviews found cross-table header leakage; source-page/rectangle filtering and aggregation of conflicting header observations fix it. Independent re-reviews report no remaining blockers. Final Standards core suite: **13 passed**; Spec re-review: **35 passed, 1 native skipped**.
- Repeated normalization initially duplicated full-document text. A red/green idempotence regression and final real-cell replay verify the fix.
- Ruff on the new core modules and affected layout/worker/config/answers/context/PDF/test files, Python compilation and `git diff --check`: passed. Existing `document_tools.py` legacy lint is not claimed clean; its change is the parser fingerprint. No frontend changes or new production dependencies.
- `graphify update .` completed after the changes: **31,017 nodes / 75,079 edges**. The tool migrates the older historical graph/cache; the original tracked graph/cache is retained to avoid unrelated migration churn. **Committed graph remains stale.** The existing `patch_embedding_identity.py:44` parse warning remains unrelated.

## Remaining runtime limits

No connection to the user's Windows services, production Knowledge database, native IndoBERT or Ollama was available. No deployment or native-model E2E PASS is claimed. The code and tests are reviewable through PR #8; applying them locally and checking real inference remain required. Other document layouts, unreadable OCR and ambiguous semantic cells can still require correction; the shared pipeline reports uncertainty rather than manufacturing procedure numbers or a checklist.
