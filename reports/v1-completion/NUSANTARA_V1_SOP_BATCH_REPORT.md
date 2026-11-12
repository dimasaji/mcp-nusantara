# NUSANTARA V1 SOP BATCH REPORT

**Contract:** NUSANTARA-V1-MASTER-2026-001
**Phase:** 4 — 42 SOP Batch Completion
**Date:** 2026-11-12
**Branch:** codex/fullroot-control-20261007

---

## 1. Inventory Summary

- Total documents in index: 64
- SOP documents (CAPIL/DAFDUK/PIAK/PERMOHONAN): 44
- Standard SOP PDFs in E:/SOP/: 42 (38 scanned, 4 digital)

## 2. Status Distribution (SOP Documents)

| Status | Count | Description |
|---|---|---|
| Aktif | 32 | Approved and indexed, searchable via Chat |
| Menunggu ekstraksi | 7 | Docling extraction not yet run |
| Menunggu pemeriksaan isi | 2 | Content review pending |
| Menunggu metadata resmi | 2 | Official metadata not confirmed |
| Ditunda | 1 | Operator deferred (CAPIL_03) |
| Total | 44 | Includes 2 test files (DAFDUK_23_TEST, DAFDUK_24_new24) |

## 3. Documents Needing Action

### 3.1 Menunggu ekstraksi (7 documents)
| Document | Source File | Source Available |
|---|---|---|
| CAPIL_17 | CAPIL_17.pdf | Yes |
| CAPIL_18 | CAPIL_18.pdf | Yes |
| CAPIL_19 | CAPIL_19.pdf | Yes |
| CAPIL_21 | CAPIL_21.pdf | Yes |
| CAPIL_24 | CAPIL_24.pdf | Yes |
| DAFDUK_02 | DAFDUK_02.pdf | Yes |
| DAFDUK_03 | DAFDUK_03.pdf | Yes |

All 7 have source files available. Extraction can be triggered via API: POST /v1/knowledge/pipeline/reviews/{id}/process

### 3.2 Menunggu pemeriksaan isi (2 documents)
- SOP Permohonan Data Pribadi (PIAK-03) — content_ok pending
- Penerbitan KTP-el Baru Untuk WNI Melalui Website Sobat Dukcapil — content_ok pending

### 3.3 Menunggu metadata resmi (2 documents)
- PERMOHONAN_DATA_PRIBADI.pdf — metadata confirmation pending
- Pelayanan Penerbitan Akta Kelahiran bagi WNI — metadata confirmation pending

### 3.4 Ditunda (1 document)
- Pelayanan CAK3P Akta Kelahiran Online Kelurahan bagi WNI (CAPIL_03) — operator deferred

## 4. Aktif Documents (32)

All 32 have:
- Source file available and verified (hash match)
- Docling extraction COMPLETE
- Content review (content_ok) confirmed
- Official metadata confirmed
- Index ready (pipeline_status=READY)
- No open problems
- Approval recorded

## 5. Idempotency & Restart

- All documents use SHA-256 based document IDs (deterministic)
- Re-processing identical source returns DUPLICATE status
- Version binding prevents document/version switching in chat sessions
- Restart preserves all data (SQLite persistent store)

## 6. Batch Processing Status

- Scripts available: process_sop.py, process_all_pending.py, batch_process_all.py
- Processing time: ~66s/SOP (Docling OCR)
- 7 documents remaining (estimated: ~7.7 minutes total)
- No auto-approval (operator review required for each)

## 7. Known Issues

1. 7 documents need extraction (operator action to trigger)
2. 2 documents need content review (operator action)
3. 2 documents need metadata confirmation (operator action)
4. 1 document deferred (operator decision)
5. OCR preprocessing now enabled but not validated on degraded scans
6. Activity grid coverage: 19.4% (low)

## 8. Commit

- Phase 4 report only, no code changes
- Database state unchanged
