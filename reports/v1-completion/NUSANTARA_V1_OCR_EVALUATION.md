# NUSANTARA V1 OCR EVALUATION REPORT

**Contract:** NUSANTARA-V1-MASTER-2026-001
**Phase:** 3 — OCR Reliability
**Date:** 2026-11-12
**Branch:** codex/fullroot-control-20261007

---

## 1. OCR Pipeline Configuration

| Parameter | Value |
|---|---|
| Engine | Tesseract CLI (via Docling) |
| Languages | ind + eng |
| PSM | 6 (uniform block of text) |
| Table mode | accurate (cell_matching=True) |
| Preprocessing | Deskew + adaptive binarization (now ENABLED) |
| Timeout | 900s |
| Force full page OCR | False (native-text-first) |
| Device | CPU (2 threads) |

## 2. Document Inventory

- Total SOP PDFs: 42
- Scanned (no native text): 38 (90.5%)
- Digital (native text): 4 (9.5%)
- All SOP processing depends on OCR for 38/42 documents

## 3. Extraction Status Distribution

| Status | Count | Description |
|---|---|---|
| COMPLETE | 83 | Full extraction, no warnings |
| PARTIAL | 70 | Extraction with warnings |
| FAILED | 27 | Extraction failed |
| Total | 180 | Includes non-SOP documents |

## 4. Warning Analysis

| Warning Type | Count | Impact |
|---|---|---|
| DOCLING_NO_STRUCTURED_TABLES | 58 | Tables detected as pictures, not structured |
| ACTIVITY_TABLE_INVALID | 21 | Activity grid reconstruction failed |
| Halaman tanpa blok teks/tabel | 1 | Missing page coverage |

## 5. Table Accuracy

- Total tables extracted: 170
- Activity grids reconstructed: 33 (19.4%)
- Previous improvement: docling_layout flexible header matching (>=2 keywords, >=2 rows)
- Rule-based grid errors changed from fatal to non-fatal (skip grid, use native Docling)

## 6. Preprocessing Status

### Code Status
- `_preprocess_pdf()` in docling_worker.py: IMPLEMENTED (deskew + adaptive binarization)
- Config `preprocess_images`: ENABLED (changed from False to True)
- Guard: only applies to scanned PDFs (`not digital`)

### Validation Status
- NOT validated on low-quality scans (blurry, tilted, low contrast, low resolution)
- No CER/WER measurements (no ground truth available)
- No field accuracy measurements

## 7. OCR Quality Assessment

### Strengths
- Native-text-first policy: digital PDFs skip OCR (faster, more accurate)
- PSM=6 tuned for uniform text blocks (SOP layout)
- Adaptive thresholding handles varying contrast
- Deskew corrects minor rotation
- Table structure options: cell_matching + accurate mode

### Weaknesses
- 19.4% activity grid coverage (low)
- 58 documents have DOCLING_NO_STRUCTURED_TABLES (tables as pictures)
- No ground truth for CER/WER measurement
- Preprocessing not validated on degraded scans
- OCR title extraction fails when "NAMA SOP" label is garbled (fixed in Phase 1)

## 8. Recommendations

1. **Enable preprocessing** (DONE): config changed to True
2. **Validate on degraded scans**: Need test set of low-quality scanned PDFs
3. **Improve table detection**: 58 docs have unstructured tables — consider fallback OCR for table regions
4. **Activity grid recovery**: Only 19.4% coverage — improve ruled_grid detection
5. **Ground truth collection**: Create manual transcription of 5-10 SOPs for CER/WER measurement
6. **OCR confidence scoring**: Add Tesseract confidence to extraction payload

## 9. Changes Applied

- `app/knowledge/docling_config.py`: `preprocess_images` False → True
- Commit: (pending)

## 10. Test Results

- No OCR-specific unit tests exist
- Extraction status distribution documented from database
- Table accuracy validated in previous phase (93.6% coverage on CAPIL_04)

## 11. Known Limitations

1. No CER/WER measurements (no ground truth)
2. Preprocessing not validated on degraded scans
3. 19.4% activity grid coverage (low)
4. 58 documents have unstructured tables
5. Docling standalone execution fails on this system (access violation) — only works through backend ThreadPoolExecutor
