# Knowledge SOP Readiness Report

Tanggal: 2026-11-23
Scope: Nusantara V1 pipeline SOP nyata
Aturan: dokumen sintetis tidak digunakan sebagai bukti keberhasilan SOP nyata

## Status Pipeline

| Tahap | Status | Bukti / Penyebab |
|---|---|---|
| PDF SOP asli | BLOCKED | `find /data/home/mcp-nusantara -iname '*.pdf'` → 0 file |
| Extraction | BLOCKED | Tidak ada PDF input; artefak docling hanya muncul di pytest tmp sintetis yang sudah dihapus |
| Chunking | NOT VERIFIED | Tidak ada konten hasil ekstraksi |
| Indexing | BLOCKED | DB `data/knowledge/nusantara_knowledge.db`: `documents=0`, `chunks=0`, `document_extractions=0` |
| Retrieval | BLOCKED | Tidak ada chunk terindeks meski config `semantic_enabled`, `lexical_enabled`, `use_embeddings`, `use_sqlite_fts5` aktif |
| LLM | AVAILABLE | Ollama `0.40.17`, model `llama3.2:1b` terpasang |
| Citation | NOT VERIFIED | Tidak ada dokumen/evidence asli untuk dikutip |
| Answer Verification | NOT VERIFIED | Tidak ada jawaban SOP nyata yang dapat diverifikasi |

## Konfigurasi dan Model

- `config/rag_runtime.json` menetapkan model embedding `indobenchmark/indobert-base-p1`, `device: cpu`, `load_once/singleton/cache: true`, `min_score: 0.35`, `top_k: 5`, `grounding.enabled: true`, `allow_model_only_answer: false`.
- Tidak ditemukan direktori model/embedding atau checkpoint IndoBERT di workspace.
- `backend/nusantara-models/indobert_worker.py` tidak ada di working tree; algoritma `source_build_id` tetap memasukkan path tersebut bila ada.
- Tidak ada koneksi ke PDF SOP asli, admin token, atau kredensial operator yang tersedia untuk verifikasi end-to-end.

## Verdict

**KNOWLEDGE SOP READINESS: BLOCKED.**

Pipeline tidak dapat dinyatakan siap tanpa PDF SOP asli, model embedding yang sesuai, data terindeks, dan kredensial verifikasi. Artefak sintetis dari test tidak digunakan sebagai pengganti. Tidak ada perubahan database atau data operasional yang dilakukan.
