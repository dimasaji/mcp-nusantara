# Automatic upload review and physical PDF navigation

Baseline: 9de8e2c71ca242e064c2fef8b7230d609c5d39a1. Date: 2026-11-04.

User problem: uploaded CAPIL_01 requires selection again from the document list,
Docling remains NOT_PROCESSED, and only page 1 is accessible despite three pages.

Scope: successful upload, duplicate recognition and retry select their document;
opening an unprocessed PDF starts existing authorized Docling processing once;
physical pages remain accessible independently of OCR offsets. No automatic
approval, new UI gate, altered access policy, or invented citation offsets.

Workflow evidence:
- Graphify query ran before reading source.
- Diagnosis: upload handler did not set reviewDocument. Page navigation used only
  source text offsets and extracted blocks, both empty before OCR/Docling finishes.
  Upload indexing did not start the separate Docling review workflow.
- Regression at existing review/render seams: test for automatic processing and
  page 3 failed before changes; source count test failed with missing field before
  backend implementation. Upload-selection regression added after implementation.
- Design: retain current upload, review and authorized process endpoints. UI starts
  processing only for a user-opened, unprocessed PDF with source available. A ref
  prevents automatic retry loops for the same document/version after failure.
  Existing backend conversion deduplication and concurrency checks remain active.
  source_page_count comes from original PDF, separately from source_pages evidence.
- Preexisting changes in sop_review.py and SOPReviewPanel were preserved.

Validation:
- 14 SOP review UI tests passed, including auto-start and physical page selection.
- 9 Knowledge operations UI tests passed, including automatic opening after upload.
- 12 backend source-page/review tests passed.
- 9 preparation regressions passed in the earlier 10-test source-page run.
- Final TypeScript noEmit check passed; scoped diff check passed; new backend test
  Ruff check corrected import ordering.
- Read-only inspection confirms original CAPIL_01.pdf contains three physical pages.

Live browser upload, real conversion completion and runtime behavior after restart
are not verified by these fixture-based tests. Automatic conversion depends on the
operator keeping the review page open; errors remain visible with manual retry.
No stored document or approval was changed by this task's checks.

Independent Spec review found no blocking issues. Standards review found no rule
violations and noted optional consolidation of the short upload/retry selection
condition; retained locally to avoid an unnecessary abstraction for two callers.
Graphify update was invoked but did not complete and was interrupted; graph
freshness is unverified. It warned about missing optional PDF tooling.

## Follow-up: content confirmation and empty trials

Read-only CAPIL inspection found Docling COMPLETE and no content_ok events.
This alone does not identify the cause of the user's failed confirmation click.
Found a reproducible UI defect: content confirmation stayed enabled during
PROCESSING although the backend rejects it until COMPLETE. New rendering test
failed before correction and passes after. Button now waits for COMPLETE and
locks after persisted content_ok. Adjacent saved message derives from backend
state, not optimistic local state. Empty trials now explicitly explain that a
question must be submitted to record a trial; no trial or approval is fabricated.

The persistence fixture explicitly sets COMPLETE, and its existing remount
assertions remain intact. 15 review UI tests pass; TypeScript and scoped diff
checks pass. Both independent reviews report zero new findings. Exact live
CAPIL save behavior still needs verification after page refresh. No decisions
were written to production. Another Graphify update was attempted; completion
is not verified.
