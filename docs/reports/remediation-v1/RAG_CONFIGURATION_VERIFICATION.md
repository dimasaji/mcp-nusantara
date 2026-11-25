# RAG_CONFIGURATION_VERIFICATION

Status: `PARTIAL / CONTRACT_CONFLICT`
Checked at: `2026-11-23T00:25:36Z`

## Konstanta terverifikasi

- `SEMANTIC_WEIGHT = 0.70`
- `LEXICAL_WEIGHT = 0.30`
- `ABSOLUTE_RELEVANCE_GATE = 0.30`
- `RELATIVE_RELEVANCE_THRESHOLD = 0.50`
- Sumber: `app/knowledge/rag.py`.

## Hasil targeted

- `/data/tmp/opencode/remediation_rag_targeted.txt`
  - `tests/test_effective_rag_profile.py`: `29 passed`.
  - `tests/test_chat_source_recovery.py`: `19 passed`.
  - `tests/test_synthetic_rag_fixture.py`: `3 passed`.
  - `tests/test_configuration_integration.py`: `11 passed, 2 failed`.

## Failure tersisa

1. `test_rag_actual_query_and_ingestion_use_config`: `assert 1 == 3`.
   - `RAG.query` mengembalikan 1/2/3/5 evidence sesuai `top_k`.
   - `KnowledgeEngine.search_knowledge` melakukan document-level grouping sehingga 3 chunk dari 1 dokumen menjadi 1 hasil.
2. `test_r1_preserves_out_of_scope_protected_sources`: `FileNotFoundError` untuk `reports/CONFIGURATION_BASELINE_20261006.json`.

## Keputusan

Document-level grouping tidak diubah. `docs/MDE02_EFFECTIVE_CONFIGURATION_CONTRACT.md`, `docs/MDE-05_RAG_PROFILE_DESIGN.md`, `docs/forensic/NUSANTARA-V1-FORENSIC-AUDIT.md`, dan `docs/reports/post-ecc/NUSANTARA_ROOT_CAUSE_ANALYSIS.md` menunjukkan perilaku ini sebagai as-built V1 dan conflict keputusan kontrak, bukan defect retrieval baru.

Eksperimen lokal penghapusan grouping menyelesaikan test konfigurasi tetapi memunculkan 2 failure `tests/test_synthetic_rag_fixture.py`; eksperimen sudah di-revert dan tidak masuk patch.
