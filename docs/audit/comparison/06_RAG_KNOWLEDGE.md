# Fase5 — Knowledge dan RAG

`OW`=E:/OpenWebUI/.venv/Lib/site-packages/open_webui. [FAKTA-KODE] kecuali label lain. Tidak membaca SOP mentah, database warga, atau menjalankan retrieval/model.

**CRITICAL — publication blocker [INFERENSI]:** public projection menyertakan chunk sumber; bila knowledge berisi SOP internal, route publik dapat mengembalikan teks mentah. Bukti: `app/api/routes.py:1024` chat hanya memerlukan admin bila document_ids diisi (:1028-1032); `_project_v1_chat_response` :211-214 menyalin chunk; `app/hermes/agent.py:1079-1099` execute_v1 membentuk evidence chunk; `app/knowledge/engine.py:46-55` search_knowledge tanpa identitas/ACL saat scope None. Ini pelanggaran boundary pada kode yang harus ditutup sebelum publikasi, **bukan bukti runtime eksfiltrasi atau isi aktual SOP di store**.

| Area | Open WebUI (bukti) | Nusantara (bukti) | Status Nusantara | Severity | Rekomendasi | Aksi |
|---|---|---|---|---|---|---|
| Ingestion | OW/routers/retrieval.py:1572 process_file, :3017 process_files_batch | app/knowledge/engine.py:36-44 ingest_document -> rag; app/main.py:48 lifespan watcher scan | ADA | MEDIUM | P0 verifikasi revision/dedup/reindex pada sampel resmi | ADAPT |
| Retrieval | OW/routers/retrieval.py:2815 query_collection_handler | app/knowledge/rag.py:595 RAG._query; :483 _profile_descriptor semantic0.70 lexical0.30 | ADA | MEDIUM | P0 ukur top-k, jangan samakan hybrid ini dengan mesin BM25 produksi | KEEP |
| Vector scaling | OW/retrieval/vector/dbs/chroma.py:59 client CHROMA_DATA_PATH; OW/config.py:509 provider | app/knowledge/store.py:302 search_similarity full-scan SQLite | ADA | MEDIUM | P0 ukur corpus nyata; P1 adapt indexed search bila perlu | ADAPT |
| Rerank | [ASUMSI] model reranker efektif belum diverifikasi | app/knowledge/rag.py:480-490 _profile_descriptor menyebut simple_keyword_overlap | SEBAGIAN | MEDIUM | P0 tampilkan implementasi aktual, bukan nama konfigurasi model saja | KEEP |
| Grounding/tidak tahu | [ASUMSI] semantic guard setara belum dibuktikan | app/hermes/agent.py:837 execute_v1 _grounding_guard.validate; app/api/routes.py:183-186 allowlist no_evidence/grounded_abstention | ADA | HIGH | P0 uji jawaban benar dan abstain dengan evidence nyata | KEEP |
| Citation/privacy | OW/routers/retrieval.py:2722 _validate_collection_access | app/api/routes.py:211-214 _project_v1_chat_response chunk publik | RUSAK | CRITICAL | P0 hapus raw chunk dari boundary publik dan enforce ACL sebelum retrieval | ADAPT |
| Evidence non-SOP | OW/utils/middleware.py:1005 chat_completion_tools_handler dan tools fetch_url teridentifikasi pada :449 CITATION_TOOL_NAMES | [ASUMSI] web evidence pipeline V1 tervalidasi belum dibuktikan | SEBAGIAN | MEDIUM | P1 pisahkan public web evidence dari SOP internal; HOLD otonomi | ADAPT |

## Kesiapan PIAK-03

[FAKTA-KODE] `tests/test_v1_service_dialogue.py:44` setup menggunakan mocked knowledge; karena itu hasil test dialog tersebut tidak membuktikan retrieval nyata atau kualitas embedding aktual. [FAKTA-RUNTIME] Pencarian `rg -n 'PIAK[-_ ]?03' app --glob '*.py'` tidak menemukan label: **TIDAK DITEMUKAN setelah mencari pola tersebut di app Python**. [INFERENSI] Tidak ditemukan hardcode label sampel, tetapi ini tidak membuktikan seluruh implementasi bebas hardcode semantik/aturan domain.

[ASUMSI] Retrieval benar, jawaban benar, sitasi relevan, grounding, serta privacy PIAK-03 pada corpus terpasang **belum diverifikasi**. Model embedding efektif dan isi store tidak diakses. Lihat bukti tambahan chunker di bawah untuk perbedaan antara label strategy dan implementasi aktual.

## Chunking dan sumber luar yang benar-benar tersedia

[FAKTA-KODE] `app/knowledge/chunker.py:3` chunk_text memotong berdasarkan panjang karakter/overlap; :18 SentenceChunker dan :20 ParagraphChunker merupakan alias Chunker; :22 get_chunker tidak membedakan strategy. [INFERENSI] P0 ADAPT evaluasi keutuhan section/tabel SOP pada actual ingestion sebelum memilih algoritme baru; tidak menyebut alias tersebut sebagai tiga algoritme berbeda. `app/knowledge/parser.py:26` PDFParser menerima bytes dan memakai ekstraksi teks halaman, sedangkan `app/knowledge/engine.py:102` _extract_pipeline_text adalah jalur ekstraksi pipeline yang perlu dibedakan dari parser generik.

[FAKTA-KODE] `OW/routers/retrieval.py:2174` search_web dan :2554 process_web_search menyediakan acquisition web, dengan pemeriksaan permission:2562. Nusantara `app/knowledge/web_evidence.py:1` mendefinisikan acquisition kandidat yang sengaja terisolasi, tanpa route/model/active-store wiring; `ApprovalPrincipal` pada :34 mencatat approval/provenance. [INFERENSI] P1 ADAPT provenance dan review candidate terpisah dari SOP index; kemampuan kajian publik aktif V1 tetap belum terverifikasi. HOLD/SKIP autonomous acquisition yang mencampur data internal ke search/model luar.

P0 acceptance: dataset pertanyaan PIAK-03 disahkan pemilik; expected source/section dan expected abstention; retrieval trace top-k teredaksi, citation revision valid, output publik tanpa raw SOP, semua model call lokal; uji restart dan20 turn berurutan. Threshold recall/faithfulness diusulkan pada laporan13 dan harus disahkan pemilik, tidak diarang dari code coverage. P1 adapt Open WebUI collection-access checks sebelum retrieval; jangan meniru publikasi full chunks. HOLD skip autonomous web browsing yang mencampur konteks internal ke provider eksternal.

