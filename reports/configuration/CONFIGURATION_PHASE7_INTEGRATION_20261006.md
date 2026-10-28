# Nusantara Configuration — Phase 7 Integration

Tanggal: 2026-10-06. Status: **COMPLETE — PASS_SCOPED** untuk integrasi consumer opt-in.

User menginstruksikan lanjut Phase 7 dan integrasi. Implementasi menghubungkan snapshot Phase 6 secara **opt-in** ke existing consumer. Tidak mengaktifkan snapshot secara otomatis pada route/startup service atau mengubah protected CC-01/DeveloperCore/Trust/Policy. Phase 0–6 dan bukti historis tidak diulang atau ditulis ulang.

## Consumer yang dihubungkan

| Consumer | Konfigurasi yang digunakan | Override / compatibility |
| --- | --- | --- |
| OllamaProvider | llm.base_url/model/connection_timeout_s; generation.context_length/max_tokens/temperature/top_p | Keyword baru nusantara_config; tanpa snapshot, konstruksi dan Settings context existing tetap berlaku. Non-default constructor args tetap menang; request max_tokens/temperature/top_p menang atas generation snapshot |
| IndoBERTEmbeddingAdapter | paths.worker_python/worker dan embedding.timeout_s | Keyword snapshot opsional; constructor no-argument lama tetap berlaku. Existing worker/model base-p1/768D dipertahankan |
| RAG | Mapping snapshot ke KnowledgeBaseConfig: model/dimension/backend, chunk size/overlap, top-k, reranker settings; knowledge.database ke SQLite ctor | Explicit KnowledgeBaseConfig, vector_store, embedding_func tetap memiliki precedence. Config tidak membuat store sendiri; RAG tetap menggunakan constructor store existing saat tidak ada injected store |
| create_rag | Snapshot diteruskan ke RAG | Existing positional arguments dipertahankan; tanpa snapshot memakai pemanggilan lama |
| KnowledgeEngine | Snapshot diteruskan ke create_rag | Explicit rag tetap dipakai. search/search_knowledge mempertahankan signature dan default top_k=5; RAG.query tanpa top_k memakai top-k snapshot |

Semua perubahan berada pada empat existing source: `app/models/ollama.py`, `app/knowledge/indobert_embedding.py`, `app/knowledge/rag.py`, `app/knowledge/engine.py`. Test baru `tests/test_configuration_integration.py`. Tidak mengedit existing tests.

Backup sebelum edit berada di direktori yang dicatat `phase7_backup` pada `CONFIGURATION_PROGRESS.json`, dengan layout path app yang sama. Hash backup keempat file cocok dengan baseline sebelum integrasi. Audit 296 file baseline: empat perubahan yang diizinkan, 292 file lain tetap identik termasuk route CC-01, DeveloperCore, Settings, Trust/Policy, contracts, Docker, Oracle, dan kedua database. Source module/test Phase 6 juga tidak diubah.

## Parameter yang ditolak atau belum dihubungkan

Adapter IndoBERT menolak penggantian model/dimension yang belum diimplementasikan; RAG menjalankan preflight sebelum store dibuat. Bila custom embedding_func diberikan, callback explicit tetap digunakan. Snapshot RAG yang meminta semantic/lexical weights atau similarity threshold ditolak oleh consumer ini karena jalur production retriever tersendiri belum dimigrasikan. Tidak diam-diam memakai nilai yang belum terintegrasi.

Embedding batch size, auth reference resolution, runtime bind/workers/request limits, governance/feature flags, production profile, dan provider lain **belum dihubungkan**. Snapshot metadata/provenance tetap UNWIRED/DECLARED_ONLY; belum ada rewrite per-field status menjadi CONSUMED pada runtime diagnostics. Governance tetap descriptive references; tidak membuat engine Policy/Trust configuration mutator. Auth reference tidak dibaca sebagai credential atau ditambahkan ke HTTP headers.

Reranker flags/model dipetakan ke KnowledgeBaseConfig, tetapi existing RAG.query tetap memerlukan argument rerank untuk melakukan reranking. Tidak menambah reranker/model dependency baru. Settings embedding local-hash/store memory tetap legacy declaration; jalur RAG IndoBERT/SQLite tidak diganti.

Dengan snapshot diberikan, legacy Ollama constructor arguments yang nilainya tepat sama dengan default (localhost URL, llama3.2:1b, timeout120) dianggap unspecified dan digantikan snapshot. Constructor tidak dapat membedakan explicit argument bernilai default dari omission. Untuk memaksa behavior legacy, jangan berikan snapshot; non-default explicit arguments tetap menang. Keputusan ini hanya berlaku pada opt-in consumer dan tidak mengubah caller existing tanpa snapshot.

## VERIFY

Targeted final: **93 passed, 0 failed**, 0,83 detik; bukti `CONFIGURATION_PHASE7_TARGETED_FINAL_20261006.xml`. Test baru mencakup HTTP mock yang membuktikan payload model/generation, parameter client IndoBERT tanpa menjalankan worker, incompatibility preflight sebelum store, actual RAG ingestion/query dengan fixture store terisolasi, ctor database-path handoff lewat mock, explicit dependency precedence, dan facade legacy top-k.

Percobaan awal `CONFIGURATION_PHASE7_TARGETED_20261006.xml`: 91 pass/2 fail karena test menganggap GenerateResponse adalah object sementara existing alias mengembalikan dict, dan MemoriaVectorStore lama tidak memenuhi seluruh protocol persisted-store. Percobaan kedua 92 pass/1 fail karena tuple semantic search fixture masih urutan lama. Fixture baru melengkapi protocol dan tuple order seperti backend persisted; existing runtime/test tidak diubah untuk memperbaiki hasil tersebut. Bukti ketiga lulus. In-memory fixture tidak membuktikan persistensi database produksi.

Regresi pertama: **352 passed, 1 failed, 1 skipped, 28 subtests passed**, 96,83 detik; `CONFIGURATION_PHASE7_REGRESSION_20261006.xml`. Satu existing test SessionMemory write gagal pada os.replace dengan Windows WinError5. Kedua source memory dan testnya tidak berubah. Diagnosis hanya kasus tersebut pada direktori baru: **1 passed**, 0,12 detik; `CONFIGURATION_PHASE7_MEMORY_DIAGNOSIS_20261006.xml`. Penyebab Windows access error belum dibuktikan; tidak mengatribusikannya secara pasti pada scanner/antivirus atau perubahan integrasi.

Regresi final: **353 passed, 1 skipped, 28 subtests passed, 0 failures/errors**, 108,26 detik; `CONFIGURATION_PHASE7_REGRESSION_FINAL_20261006.xml`. JUnit mencatat 382 testcase termasuk subtests dan skip. Dijalankan untuk verifikasi kegagalan yang belum terselesaikan, dengan direktori sementara baru dan tanpa concurrent scan. Ini merupakan run penuh kedua; bukan pengulangan audit baseline atau penghapusan evidence gagal.

Static scanner existing: **0 findings, PASS_SCOPED**, `CONFIGURATION_PHASE7_SECURITY_20261006.json`. Tidak mengklaim sertifikasi keamanan penuh. Existing Starlette/httpx dan datetime.utcnow deprecation warnings tercatat. Mandatory symlink Windows gate yang sudah terbuka belum ditutup oleh pekerjaan ini.

Graph AST existing diperbarui setelah tests selesai: **5.891 nodes, 9.691 edges, 1.304 communities**, HTML aggregated. Tidak ada LLM extraction atau runtime baru. Warning existing untuk temporary report directories/PDF/labels tetap tercatat; graph bukan bukti aktivasi runtime.

## Aktivasi, efek samping, dan kelanjutan

Konfigurasi dapat dipakai secara konkret oleh caller melalui `OllamaProvider(nusantara_config=config)`, `create_rag(nusantara_config=config, vector_store=isolated_store)`, atau `KnowledgeEngine(nusantara_config=config)`. Provider existing juga dapat diberikan ke Hermes lewat constructor dependency injection yang sudah ada; Hermes source/router tidak diubah, dan model literals pada ModelRouter belum dimigrasikan.

Test memakai mocked HTTP transport dan client IndoBERT serta store fixture/injected dependencies. Database path handoff memakai mock SQLite constructor. Tidak memindahkan, membuka, atau mengubah database produksi untuk verifikasi. Constructor RAG existing dalam penggunaan nyata tetap dapat initialize store ketika caller tidak memberi explicit store; ini behavior engine, bukan side effect loader. Operator harus memilih profile/path/permission yang benar sebelum aktivasi service.

Tidak restart/deploy service, install dependency/model, mengubah environment produksi, API publik, response projection, security policy, atau acceptance gate. Service user yang sedang berjalan masih memakai source yang dimuat saat startup. Identitas source kandidat tidak membuktikan deployment atau aktivasi snapshot pada proses tersebut.

Phase 7 ini adalah **consumer integration scoped**, bukan aktivasi end-to-end semua domain. Route/startup activation, provider switching, runtime/governance controls, production profile, serta API wiring protected tetap membutuhkan scope/approval tersendiri. Phase 8 validation/integration review dan Phase 10 architecture review belum ditutup; hasil regresi di turn ini adalah compatibility evidence, bukan klaim seluruh Configuration Architect DoD terpenuhi.

Rollback selektif menggunakan backup empat file setelah memeriksa perubahan user berikutnya; jangan reset global, menimpa perubahan baru, atau menghapus config/test/evidence lama. Resume membaca checkpoint dan melanjutkan pekerjaan yang belum selesai. **V1 keseluruhan tetap FAIL/HOLD.**
