# Scanned SOP activity tables — 8 November 2026

Baseline: `0f172cde923cf765f1e2698050de253ed9063967`, continuing PR #8.

## Scope and acceptance

Continue the pending CAPIL-01 table reconstruction work through the shared Docling pipeline. Detect image-only ruled activity grids after OCR and before layout postprocessing/table reconstruction. No document-name dispatch, invented cell text, automatic approval, new UI or production database changes. Preserve physical page numbers and the original Docling export. Existing native-PDF normalization must keep working. Acceptance is table reconstruction on both activity pages of the archived scan (2 and 3); this alone does not certify every OCR word or every chat answer.

## Diagnosis

The original PDF is three image-only pages: zero native characters, zero vector drawings and zero tables detected by PyMuPDF on every page. The original `activity_grid_regions()` therefore returns no pages. Its geometry is useful for digital PDFs but cannot locate raster grids. Reproduction: call it against the tracked CAPIL-01 PDF and assert page 2 is present; this fails with an empty mapping.

Considered three predictions: raster/vector mismatch (native geometry stays empty despite visible lines); stage order (OCR cells must exist when matching header text); exact header matching (OCR loses short labels and partial column headings). The first raster run reconstructed page 3 but missed page 2 and still reported COMPLETE. Native stage inspection then proved that Docling 2.142.1 runs layout prediction before OCR: the old layout wrapper observed zero OCR cells. The rescue is now attached to the OCR stage, after raw layout and before postprocessing. Independent OCR passes also lost short `No.` and/or `Kelengkapan` labels. Header alternatives now require `Kegiatan`, one of `No`/`Pelaksana`, and one of `Kelengkapan`/`Mutu Baku`, within the top quarter of a sufficiently large ruled grid. No header values are repaired or substituted in the extracted content.

## Implementation and design

`scanned_activity_grid_regions()` uses CPU OpenCV morphology on Docling's page image and existing OCR cells. It proposes a bounded table region only when horizontal/vertical line components and procedure headers agree. The OCR-stage wrapper runs after OCR and raw layout prediction, before Docling's layout postprocessor assigns cells/children; Docling retains ownership of reconstruction. Native ruled grids retain their previous path. Detected region boxes are returned to the worker and matched to reconstructed table provenance in top-left physical-page coordinates (intersection-over-union at least 0.8). A missing matching table produces a warning; an unrelated table on the same page cannot satisfy this check. Parser/config fingerprints change so cached extractions cannot silently conceal the new behavior.

The small interface remains inside `docling_layout.py`; no OCR rerun, backend dependency, additional operator input or alternate RAG engine is introduced. The image detector's OpenCV dependency is already supplied by the Docling environment; the backend does not import it on the native normalization path.

## Validation

Use the previously agreed Knowledge/extraction seam. Deterministic tests exercise raster geometry plus OCR header inputs; they do not certify OCR model accuracy. Two header-loss variants were red before their fix, then green. Existing native-grid, outside-footnote, ingestion, selected-document chat, publication and review tests remain included. An opt-in native test calls the real conversion interface against the already tracked PDF and checks both physical activity pages, status, page count and retained Docling JSON.

Native command (requires local model weights and complete Tesseract ind+eng/osd data and configs):

```sh
NUSANTARA_NATIVE_DOCLING_TEST=1 NUSANTARA_TESSERACT_CMD=/usr/bin/tesseract TESSDATA_PREFIX=/path/to/tessdata .venv/bin/python -m pytest tests/test_docling_layout.py -q
```

No full OCR transcription or source PDF is added by this change. All native conversions use scratch output and isolated tests. IndoBERT/Ollama, Windows deployment and live browser behavior remain outside this verification.

## Final results

- Real Docling 2.142.1 conversion with CPU models and Tesseract ind+eng: **8 passed** in 116.43 seconds, including the native regression. Both detected activity regions on physical pages **2 and 3** have matching reconstructed table provenance; COMPLETE, three pages, retained original Docling JSON. This verifies reconstruction/presence, not exact transcription of every table cell or all 17 activities.
- Related backend regression suite (`test_docling_layout`, `test_selected_pdf_chat`, `test_capil01_knowledge`, `test_document_tools`, `test_sop_review`, `test_review_publication_v1`, `test_knowledge_pipeline_api`, `test_v1_review_execution_api`): **68 passed, 2 native tests skipped** in 9.33 seconds.
- Explicit real OCR/upload suite: **7 passed** in 8.32 seconds, using the archived PDF and isolated SQLite/fixture embeddings. No production approval or indexing performed.
- Ruff on layout, worker, config and layout tests: passed. Python compilation and `git diff --check`: passed. No frontend changes; frontend checks were not repeated. No claim of repository-wide lint/type cleanliness.
- Standards review found that worker-only dependencies could break default backend tests; optional imports now skip those worker cases. Re-review: **7 passed/1 skipped** with dependencies, **4 passed/4 skipped** simulating absent Docling; no remaining blocking findings.
- Spec review found a same-page unrelated-table loophole. The provenance IoU check and red/green regression fix it. Re-review confirmed correct OCR-stage ordering and no remaining blockers in the stated scope.
- `graphify update .` completed: **30,966 nodes / 74,925 edges**. Tool-version migration rewrites the historical 43,827-node graph and removes thousands of older cache entries. Restored the original tracked graph/cache rather than include unrelated migration churn; **committed graph remains stale**. Existing extraction warning: `patch_embedding_identity.py:44`.

Remaining: verify reconstructed cell contents and grounded CAPIL-01 chat answers with native IndoBERT/Ollama, then deploy/test the change on the user's Windows services. Table detection alone is not a release-completion claim. Other raster formats without readable headers or ruled lines remain outside this rescue and require the existing extraction/review path.
