# Nusantara V1 — Knowledge Stabilization Final Report

## Status: PARTIAL (PASS for tested scope)

## 1. Ringkasan Perubahan

### Kode yang diubah (7 file backend)
1. `app/knowledge/docling_layout.py` — fix NameError (`layout_grid_regions` → `activity_grid_regions`)
2. `app/knowledge/engine.py` — fix NameError (`knowledge_preparation` → `None`); noise filter (score ≥ 0.32); document-level grouping; title boost (+0.15)
3. `app/knowledge/sop_review.py` — `is_pilot()` fix (exclude UNVERIFIED authority legacy docs)
4. `app/security/v1_knowledge.py` — session ID backward-compatible (1-128 chars)
5. `app/knowledge/grounding.py` — subset-token check (accept if all answer tokens in evidence)
6. `app/hermes/agent.py` — evidence_fast_path fallback (use source text when model fails)
7. `app/knowledge/docling_config.py` — tesseract_psm=6
8. `app/knowledge/docling_worker.py` — psm config
9. `app/core/error_taxonomy.py` — new module (TRANSIENT/PERMANENT/NEEDS_HUMAN/POLICY_DENIED)

### Scripts yang dibuat (8)
- `scripts/process_sop.py` — automated SOP processing orchestrator
- `scripts/fill_template.py` — Template A-M auto-fill (python-docx)
- `scripts/generate_golden_set.py` — Golden Set generator (Tier A/B/C)
- `scripts/validate_table_structure.py` — Table structure validation
- `scripts/validate_table_accuracy.py` — Table accuracy validation (93.6% coverage)
- `scripts/perf_baseline.py` — Performance baseline
- `scripts/run_search_eval.py` — Search evaluation
- `scripts/batch_process_all.py` — Batch processing 42 SOP

## 2. Root Cause yang Ditemukan

| # | Masalah | Klasifikasi | Status |
|---|---|---|---|
| 1 | Docling NameError (`layout_grid_regions`) | EXTRACTION_ERROR | FIXED |
| 2 | Engine NameError (`preparation`) | EXTRACTION_ERROR | FIXED |
| 3 | `is_pilot()` gating legacy docs | RETRIEVAL_ERROR | FIXED |
| 4 | Session ID too strict (web-UUID only) | RETRIEVAL_ERROR | FIXED |
| 5 | Grounding guard too strict | GENERATION_ERROR | FIXED |
| 6 | Search noise (nonsense queries) | RETRIEVAL_ERROR | FIXED |
| 7 | Duplicate docs in results | RETRIEVAL_ERROR | FIXED |
| 8 | OCR quality (fragmented text) | EXTRACTION_ERROR | PARTIAL (PSM=6, preprocessing not implemented) |
| 9 | Chunking (no boundary preservation) | CHUNKING_ERROR | NOT FIXED (low priority) |
| 10 | Haystack cleaning | CLEANING (safe) | NO CHANGE NEEDED |

## 3. Hasil Pengujian

### E2E (CAPIL_02 & CAPIL_04)
- Upload → OCR/Docling → Review → Approval → Indexing → Search → Chat ✅
- Persistensi (restart) ✅
- Access control (publik→403) ✅
- Idempotensi (re-upload→DUPLICATE) ✅
- Retry E2E ✅
- Follow-up chat E2E ✅
- Citation resolution E2E ✅
- Chat abstention E2E ✅

### Metrik Search (30 query berlabel)
- Recall@5: 0.9278
- MRR@10: 0.8333
- Precision@5: 0.3028
- Exact-match: 0.8
- Latency p95: 94.9ms

### Table Accuracy
- CAPIL_04: 93.6% coverage, STATUS: PASS

### Performa
- 2 SOP: 132.3s total, avg 66.1s/SOP
- Estimasi 42 SOP: ~46 menit

### Unit Tests
- 19 passed (backend_runtime_fixture, sop_review, knowledge_pipeline)

## 4. SOP Status
- Total dokumen di store: 64
- Aktif SOP: 21
- Gagal: 2 (RULED_GRID_HEADERS_INCOMPLETE, RULED_GRID_ACTIVITY_NUMBER_INVALID)
- Ditunda: 1 (CAPIL_03 — operator defer)

## 5. Risiko yang Masih Tersisa
1. OCR quality pada scan berkualitas rendah (teks terfragmentasi)
2. Precision@5 rendah (0.30) — query broad mengembalikan banyak doc
3. Table accuracy ground-truth belum ada (hanya coverage check)
4. 42-SOP batch processing belum dijalankan massal
5. Performance baseline formal (10 SOP batch, peak RAM) belum diukur
6. Golden Set per SOP belum dihasilkan massal (hanya 2 SOP)
7. Template A-M auto-fill belum dijalankan massal (hanya 2 SOP)

## 6. Commit Hash
- `d7fdaacf` — sync + fixes
- `9e0a3221` — docling_layout NameError fix
- `021f6da0` — OCR PSM tuning + template/golden set scripts
- `d394fcf5` — search precision tuning
- `3e50599c` — chore: remove trailing PY
- `8f8cd015` — table structure validation script
- `bf43c36a` — performance baseline script
- `3c50cafb` — error taxonomy
- `f4f93903` — table accuracy validation script
- `0b48db2a` — clean up git tracking

## 7. Status Akhir: PARTIAL (PASS for tested scope)

Kriteria kritis terpenuhi untuk scope yang diuji (CAPIL_02 & CAPIL_04).
Acceptance test penuh (16 poin) belum terpenuhi karena:
- 42-SOP batch processing belum dijalankan
- Table accuracy ground-truth belum ada
- Performance baseline formal belum diukur
- Golden Set per SOP belum dihasilkan massal
PY