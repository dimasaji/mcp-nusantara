# CAPIL_01 scanned PDF layout correction

Baseline: 9de8e2c71ca242e064c2fef8b7230d609c5d39a1. Date: 2026-11-04.

User symptom: CAPIL_01 results are disordered compared with PIAK-03.
Original CAPIL extraction: COMPLETE, 266 blocks; page 2 contains 261 text
fragments and zero tables. PIAK extraction: four structured blocks, including
two normalized tables and 15 activity rows. Original CAPIL has no native text
or vector table lines on all three pages: it is image-only. PDF page 2 visually
contains a wide procedure grid; page 3 continues numbered activities 9–17.

## Diagnosis and implementation

Graphify query preceded inspection. Compared extraction payloads and rendered
original PDF pages. Native-grid normalization cannot apply to image-only scans.
Also, the UI only rendered normalized headers/rows; native Docling table_cells
were displayed as a long Markdown string rather than a structured table.

TDD: synthetic image-grid detection failed before implementation; native cell
rendering with a merged header failed before implementation. Both now pass.

Changes:
- A separate raster grid detector identifies large table layout candidates from
  visible line projections; it guides Docling layout without inventing text.
- Native-grid normalization still uses native geometry only, preserving PIAK
  provenance. Raster regions are never labeled as native physical cell reads.
- Full-page OCR for scanned inputs supplies text for table reconstruction; digital
  inputs retain do_ocr=False. Empty table candidates are retained until later OCR
  assignment. Backend word cells are used when textline cells are unavailable.
- Worker validation warns when a detected raster table was not reconstructed;
  incomplete results are PARTIAL rather than falsely COMPLETE.
- The UI renders native cells using their original text, row/column offsets and
  spans, including empty grid positions. Existing normalized tables are retained.
- Parser/config fingerprints are bumped so reprocessing does not reuse old cache.

## Verification and limits

9 backend layout/context/document-tools tests passed; 16 SOP review UI tests
passed; TypeScript and scoped whitespace checks passed. Native PIAK grid tests
remain green. Model providers, authorization, original bytes and operator approval
are unchanged. No production extraction row was replaced during diagnosis.

Real conversion attempts: grid detection alone and initial full OCR remained
PARTIAL with missing page-2 table. Retaining the table candidate then recovered
the isolated original page 2 as COMPLETE with five blocks, including one 9-row,
10-column table. This improves fragmentation, but several actor columns remain
merged and OCR labels contain errors. It does not establish complete cell-level
fidelity or correct flowchart interpretation. Original PDF remains authoritative.
Final real three-page conversion: COMPLETE with no worker warnings, 10 blocks,
and one table on each physical page: page 1 has 24 rows × 4 columns; page 2 has
9 rows × 10 columns; page 3 has 10 rows × 10 columns. This replaces the old
266-block result (including 261 fragmented text blocks on page 2). Technical
completion does not certify actor-column separation, activity numbering, OCR
spelling, or flowchart arrows. Those remain inspection limitations.

`keep_empty_clusters` is explicitly recorded in extraction configuration; the
worker retains image table candidates until OCR/table stages assign content.
Pillow is declared in the SOP optional dependency group (already installed in
the inspected runtimes). Final TypeScript check passed. User must restart the
backend and explicitly reprocess CAPIL_01 to replace its existing cached output;
no production decision or extraction was changed by the isolated verification.

Standards review: no blocking violations, optional performance concerns about
repeated rasterization and raw-cell rendering complexity. Spec review: no scope
violation, but table presence alone does not certify accurate cell reconstruction.
Final incremental Spec review found no blocking issue and noted that mixed
digital/scanned documents run OCR document-wide under the existing digital test.
Graphify update attempted; extraction reached 326/326 uncached files but overall
update did not finish and was interrupted. Existing unrelated syntax warning
for patch_embedding_identity.py and optional PDF dependency warning remain.
