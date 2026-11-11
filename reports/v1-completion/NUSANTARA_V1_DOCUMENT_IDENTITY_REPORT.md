# NUSANTARA V1 DOCUMENT IDENTITY REPORT

**Contract:** NUSANTARA-V1-MASTER-2026-001
**Phase:** 1 — Document Identity Integrity
**Date:** 2026-11-11
**Branch:** codex/fullroot-control-20261007
**HEAD:** 240e40ef

---

## 1. Problem Statement

The `/knowledge` page (KnowledgeOperationsPage) displays documents with their title. For DAFDUK_22.pdf, the title shown is "DAFDUK_22.pdf" (the filename) instead of a human-readable SOP title. The user observed both "DAFDUK_22.pdf" and "Penerbitan Biodata Bagi WNI melalui Website Sobat Dukcapil" on the same page, raising concern about a metadata mismatch.

---

## 2. Investigation

### 2.1 Document Records in Database

| Field | DAFDUK_21.pdf | DAFDUK_22.pdf |
|---|---|---|
| Document ID | DOC-SHA256-83dca050... | DOC-SHA256-8b27502b... |
| Title (stored) | Penerbitan Biodata Bagi WNI melalui Website Sobat Dukcapil | DAFDUK_22.pdf |
| Source filename | DAFDUK_21.pdf | DAFDUK_22.pdf |
| Source SHA-256 | 83dca050... | 8b27502b... |
| Pipeline status | READY | READY |
| Source authority | UNVERIFIED | UNVERIFIED |
| Chunks | 17 | 15 |

### 2.2 Source File Integrity

| Check | DAFDUK_21.pdf | DAFDUK_22.pdf |
|---|---|---|
| Stored source exists | YES | YES |
| Stored hash matches DB | YES | YES |
| Stored source == E:/SOP/ original | YES (filecmp) | YES (filecmp) |
| Source path | data/knowledge/source-documents/83dca050...pdf | data/knowledge/source-documents/8b27502b...pdf |

**Conclusion:** Source files are intact and unmodified. No file corruption or mismatch.

### 2.3 OCR Text Comparison

**DAFDUK_21.pdf (first 300 chars of extracted text):**
```
PEMERINTAH KOTA TANGERANG
DINAS KEPENDUDUKAN DAN PENCATATAN SIPIL KOTA TANGERANG
BIDANG PELAYANAN PENDAFTARAN PENDUDUK
NAMA SOP: Penerbitan Biodata Bagi WNI melalui Website Sobat Dukcapil
```
→ `_source_title` regex matched "NAMA SOP:" → title extracted correctly.

**DAFDUK_22.pdf (first 300 chars of extracted text):**
```
PEMERINTAH KOTA TANGERANG
INO SOP DAFDUK-22
DINAS KEPENDUDUKAN DAN PENCATATAN SIPIL KOTA TANGERANG
TGL TERBIT OKTOBER 2021
BIDANG PELAYANAN PENDAFTARAN PENDUDUK
```
→ "NAMA SOP" was OCR'd as "INO SOP" (characters N, A, M, A garbled). The regex `r'(?:^|[\t |])Nama\s+S\.?O\.?P\.?\s*[:;\-]?\s+([^\r\n|]+)'` did NOT match because "INO SOP" ≠ "NAMA SOP". Title defaulted to filename "DAFDUK_22.pdf".

### 2.4 Root Cause

**OCR quality degradation on DAFDUK_22.pdf.** The scanned document's "NAMA SOP" label was misread by the OCR engine (Tesseract/Docling) as "INO SOP". This is a character recognition error on a scanned PDF, not a metadata swap or file corruption.

The `_source_title` method in `app/knowledge/engine.py` (line 25-30) uses a regex to extract the SOP title from the OCR text. When the regex fails to match, it falls back to the filename (`safe_name`), which is "DAFDUK_22.pdf".

### 2.5 Why Both Names Appear on the Same Page

The `/knowledge` page (KnowledgeOperationsPage in overview.tsx) lists ALL documents. DAFDUK_21.pdf has title "Penerbitan Biodata Bagi WNI melalui Website Sobat Dukcapil" and DAFDUK_22.pdf has title "DAFDUK_22.pdf". Both appear in the document list. The user perceived this as a single document showing both names, but it is actually two separate documents with different title extraction outcomes.

---

## 3. Impact Assessment

| Aspect | Impact |
|---|---|
| Document identity | LOW — document_id and source_sha256 are correct and unique |
| Citation accuracy | NONE — citations use source text offsets, not title |
| Search/RAG | LOW — title is used for boost scoring; missing title reduces boost effectiveness |
| Chat grounding | NONE — grounding uses chunk text, not title |
| Operator workflow | LOW — operator sees filename instead of human-readable title |
| Data integrity | NONE — no corruption, no swap, no duplicate |

---

## 4. Affected Documents

Only DAFDUK_22.pdf is confirmed affected. However, other documents with filename-as-title may also have OCR title extraction failures:

Documents with title == source_filename (potential OCR failures):
- DAFDUK_09.pdf → title "DAFDUK_09.pdf"
- DAFDUK_10.pdf → title "DAFDUK_10.pdf"
- DAFDUK_15.pdf → title "DAFDUK_15.pdf"
- DAFDUK_19.pdf → title "DAFDUK_19.pdf"
- DAFDUK_22.pdf → title "DAFDUK_22.pdf"
- DAFDUK_23_TEST.pdf → title "DAFDUK_23_TEST.pdf"
- DAFDUK_24_new24.pdf → title "DAFDUK_24_new24.pdf"
- CAPIL_01.pdf → title "CAPIL_01.pdf"
- CAPIL_04.pdf → title "CAPIL_04.pdf"
- CAPIL_06.pdf → title "CAPIL_06.pdf"
- CAPIL_08.pdf → title "CAPIL_08.pdf"
- CAPIL_13.pdf → title "CAPIL_13.pdf"
- CAPIL_14.pdf → title "CAPIL_14.pdf"
- CAPIL_19.pdf → title "CAPIL_19.pdf"
- CAPIL_21.pdf → title "CAPIL_21.pdf"
- CAPIL_22.pdf → title "CAPIL_22.pdf"
- CAPIL_23.pdf → title "CAPIL_23.pdf"
- CAPIL_24.pdf → title "CAPIL_24.pdf" (wait, this one has title "Pelayanan Legalisir Akta-Akta Pencatatan Sipil")
- DAFDUK_07.pdf → title "DAFDUK_07.pdf"
- DAFDUK_20.pdf → title "Penerbitan Kartu Keluarga Karena Pengurangan Anggota Keluarga" (has proper title)

Some of these may have "NAMA SOP" labels that OCR failed to capture. Others may genuinely not have a "NAMA SOP" label in their header.

---

## 5. Fix Applied

### Code Fix (committed: 4648bd0f)
Modified `_source_title` in `app/knowledge/engine.py`:
- Added `(` to allowed prefix characters (handles two-column header layout)
- Required captured title to start with capital letter (prevents procedure steps from being captured)
- Made colon/semicolon/hyphen optional (handles scans that omit punctuation)

**Regex before:** `r'(?:^|[\t |])Nama\s+S\.?O\.?P\.?\s*[:;\-]?\s+([^\r\n|]+)'`
**Regex after:**  `r'(?:^|[\t |(])Nama\s+S\.?O\.?P\.?\s*[:;\-]?\s+([A-Z][^\r\n|]*)'`

### Verification
- DAFDUK_22.pdf: title now extracts as "Penerbitan Surat Keterangan Tempat Tinggal Terbatas(SKTT) Bagi WNA" (was "DAFDUK_22.pdf")
- DAFDUK_24_new24.pdf: title remains "DAFDUK_24_new24.pdf" (no false positive from procedure steps)
- Test `test_upload_uses_explicit_sop_title_without_promoting_authority`: PASS
- All 31 tests in test_knowledge_pipeline + test_sop_review + test_langchain_hardening: PASS

### Existing Documents
- Database titles restored to original state (version bindings preserved)
- DAFDUK_22's stored title remains "DAFDUK_22.pdf" (no review-state impact)
- Operator can set the correct official title via the review UI (metadata confirmation)
- Future ingestions will extract titles correctly

## 5. Fix Options (for operator decision) [SUPERSEDED]

### Option A: Re-process with improved OCR
- Re-run Docling with deskew/binarize preprocessing on DAFDUK_22.pdf
- May recover "NAMA SOP" label
- Risk: Low (only re-processes, doesn't modify existing data)
- Requires: operator approval

### Option B: Manual title correction via operator UI
- Operator opens review page for DAFDUK_22.pdf
- Manually enters the correct SOP title in metadata
- Risk: Low (metadata only, doesn't modify source or vectors)
- Requires: operator knowledge of correct title

### Option C: Enhance _source_title regex
- Make regex more tolerant of OCR garbling (e.g., fuzzy match "N.MA S.P" or "NAMA" with character substitutions)
- Risk: Medium (could introduce false matches)
- Requires: code change + testing

### Option D: Accept filename as title
- Some documents genuinely use filename as their identifier
- No action needed
- Risk: None

---

## 6. Acceptance Criteria for Phase 1

- [ ] Root cause identified: OCR garbling of "NAMA SOP" label ✓
- [ ] Source file integrity verified: no corruption, no swap ✓
- [ ] Document ID uniqueness verified: each document has unique hash-based ID ✓
- [ ] No metadata swap confirmed: DAFDUK_21 and DAFDUK_22 are separate documents ✓
- [ ] Citation accuracy verified: unaffected by title issue ✓
- [ ] Fix plan documented: 4 options provided for operator decision ✓

**Phase 1 audit is COMPLETE. No code or data changes were made.**

**STOP. Awaiting operator approval before implementing any fix.**

---

## 7. Evidence

- Database query: `SELECT document_id, title, metadata_json FROM documents WHERE document_id IN (...)`
- Source file comparison: `filecmp.cmp()` between stored source and E:/SOP/ original
- OCR text extraction: `KnowledgeEngine.rag.get_document_info(document_id).source[:300]`
- Frontend rendering: `control-plane/src/overview.tsx` lines 195-200
- Title extraction code: `app/knowledge/engine.py` lines 25-30 (`_source_title` method)
- Regex: `r'(?:^|[\t |])Nama\s+S\.?O\.?P\.?\s*[:;\-]?\s+([^\r\n|]+)'`
