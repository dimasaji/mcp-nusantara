# CAPIL-01 scan ingestion — 7 November 2026

Baseline: `2883958bc3b89ea0ca791523dbac3ac8b52e2e1f`, continuing PR #8.

## Requested behavior and scope

Use the actual CAPIL-01 Akta Kelahiran PDF already preserved in repository Knowledge archives, reproduce its failure, and fix the shared ingestion code rather than add a per-SOP handler. Acceptance: real scanned PDF uploads/indexes with a source-derived title; all three physical pages retain offsets into the exact indexed OCR text; mixed digital/scanned PDFs do not skip scans; low-alphabet garbage remains rejected; duplicate uploads remain idempotent; no automatic metadata confirmation, approval or public/operator chat publication.

## Source and extraction

Original tracked source: `reports/remediation/20261027-priority-fixes/database-before/0/source-documents/f9ad8a5dbdc7e16570122966ccad6dcfc3c36f447385789ae9b051a0838d7f1f.pdf`.
SHA-256 verified: `f9ad8a5dbdc7e16570122966ccad6dcfc3c36f447385789ae9b051a0838d7f1f`, 1,179,276 bytes, three scanned pages. Visually inspected page 1 to confirm CAPIL-01 and the Akta Kelahiran title, not PIAK-03 or a synthetic PDF.

Native extraction used Tesseract 5.5.0, PyMuPDF render scale 2 and `ind+eng`. Indonesian trained data came from official `tesseract-ocr/tessdata_fast`; English data was supplied by installed Tesseract. These external assets are not silently bundled into application setup. Full OCR text remains local to verification and is not included in the GitHub changes. Automated approval review rejected publication of that transcription because of potentially sensitive official identifiers/internal details; the safer deliverable contains shared code, synthetic deterministic tests and an opt-in native test against the PDF already tracked in the repository. No attempt was made to publish the rejected payload through another route.

The deterministic long-document regression uses fictional service wording with the same length/alphabet failure pattern. Separate explicit native tests use the actual CAPIL PDF. OCR mistakes and interleaved columns are not a verified reconstruction of table cells; indexing does not certify their accuracy.

## Diagnosis and changes

- Actual PDF upload failed with `EXTRACTED_TEXT_QUALITY_CHECK_FAILED`. Normalized OCR had 8,234 characters and 81 unique characters: 0.00984, below the old 0.015 ratio. The denominator grew with document length while the alphabet did not. Bounded the diversity sample to 2,048 characters; this remains a low-information screen, not an OCR accuracy certification. Repetition with a large alphabet may pass this heuristic; it does not establish correct words, table layout or meaningful content.
- Actual OCR placed `NAMA sop ;` inside a line containing the neighboring legal-grounds column. The former start-of-line/colon-only title recognizer fell back to the filename. Accept inline labels and OCR semicolons while retaining exact source wording as an unconfirmed suggestion. Preserve standalone and multiline legacy labels. The inferred title may still contain OCR errors or incomplete wrapped text; official metadata is separately reviewed.
- The former PDF-wide 40-character check skipped every scanned page if any other page contained enough native text. Select native text or OCR independently for each physical page. Blank pages and short native-only pages retain their native content without requiring an OCR installation; sparse raster pages and textless vector pages are eligible for OCR. Preserve the existing local Tesseract command/language behavior and failure handling.
- Build `source_pages` offsets from that exact list of extracted page strings. Previously OCR page provenance was lost by comparing OCR output against a second native-text extraction. No source PDF or existing Knowledge document is rewritten.

All behavior changes live in the existing `app/knowledge/engine.py`; no CAPIL-specific answer logic, new core engine or UI is introduced.

## Workflow and tests

Graphify: queried `sop ingestion metadata docling` before source traversal; graph references were checked against current code. Refresh outcome recorded after final changes.

Diagnosis: reproduced actual PDF upload failure before edits. Considered OCR corruption, length-biased quality checks, and embedding failure; replay of the unchanged OCR text isolated the quality check before embedding. Added a failing long-document regression before changing the check. Added failing mixed native/scanned PDF and title-recognition regressions before their fixes.

TDD uses the previously agreed Knowledge upload/retrieval/persistence seams. Tests use actual temporary SQLite storage and fixture embedding, with an external OCR fixture only for the deterministic mixed-page test. The explicit native test runs real Tesseract against the original CAPIL PDF, then checks indexing, three-page provenance, search, duplicate detection and non-publication. The native test is skipped by default unless `NUSANTARA_NATIVE_OCR_TEST=1` is set and `ind+eng` assets are available.

Reproduction/verification command:

```sh
NUSANTARA_NATIVE_OCR_TEST=1 TESSDATA_PREFIX=/path/to/tessdata .venv/bin/python -m pytest tests/test_capil01_knowledge.py -q
```

Codebase design: one page-extraction owner serves both PDF ingestion and the existing text-extraction helper. The facade supplies caller-visible page offsets; no migration or alternate store.

## Boundaries

CAPIL-01 was added only to isolated verification Knowledge databases, not the user's Windows production database. Native OCR and indexing success do not prove correct table reconstruction or all chat answers. Docling models/worker and native IndoBERT/Ollama were not run here. CAPIL remains `Menunggu ekstraksi`, unconfirmed and unapproved in the native test; chat publication is intentionally blocked until the existing review completes. No legal-validity assertion is made about the archived October 2021 SOP.

## Final verification and review

- Final backend run: **164 passed**, including all seven CAPIL regressions and the explicit native Tesseract test, in 11.97 seconds. The native CAPIL suite alone passed seven tests in 7.36 seconds.
- Actual archived CAPIL PDF produced **19 chunks** and physical source pages **1–3** in isolated Knowledge; status remains `Menunggu ekstraksi`. Fixture embedding was used, not a native IndoBERT inference.
- Ruff for the new test file, Python compilation and `git diff --check`: passed. The frontend is unchanged by this follow-up; its previous PR validation is separate.
- Standards: no blocking source-integrity, security or robustness findings. Reviewer independently ran 21 deterministic tests with one explicit native test skipped.
- Spec: reviewer found a blank/short-page OCR dependency regression; two cases were reproduced red, fixed, and re-reviewed. Clarified the low-alphabet quality limitation instead of claiming a general repetition detector. Final independent re-review: no remaining blockers in the defined ingestion scope; six CAPIL tests passed, native test skipped by default.
- `graphify update .` completed after final code changes: 30,937 nodes and 74,871 edges. As in the preceding task, tool version migration rewrites the older 43,827-node historical graph extensively; generated graph/cache changes were restored rather than commit an unrelated graph migration. **Committed graph remains stale.** The earlier extraction warning concerns pre-existing `patch_embedding_identity.py:44`.
