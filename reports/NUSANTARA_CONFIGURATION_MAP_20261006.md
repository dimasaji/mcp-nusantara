# Nusantara Configuration Map — Phase 3

Status: **COMPLETE_SCOPED — STATIC MAP**, 2026-10-06. Tidak mengubah source atau membuktikan nilai runtime produksi.

Semua 3.371 occurrence hasil discovery dipetakan dalam `reports/configuration/phase-03-map/CONFIGURATION_MAP_20261006.json`: source/line, owner, consumer evidence, default yang aman atau VALUE_NOT_RECORDED, required, environment override, hard-coded candidate, dan risk. Klasifikasi lengkap berada pada `phase-02-classification/CONFIGURATION_CLASSIFICATION_20261006.json`.

## Cakupan klasifikasi

| Kategori | Occurrence |
| --- | ---: |
| SYSTEM | 6 |
| RUNTIME | 96 |
| LLM | 31 |
| MODEL | 124 |
| EMBEDDING | 47 |
| RAG | 123 |
| KNOWLEDGE | 22 |
| GOVERNANCE | 23 |
| PATH | 120 |
| FEATURE | 1 |
| LEGACY | 2.732 |
| UNKNOWN | 46 |

Kategori diturunkan dari identifier/path secara deterministik, lalu sumber pusat dan selected call sites ditinjau langsung. Legacy menyimpan functional_domain tersendiri. Backup/archive/audit artefacts bukan bukti jalur aktif; skrip operasional dan fixture test diberi lifecycle terpisah. UNKNOWN tetap eksplisit untuk review, bukan ditebak menjadi configuration aktif. File graph query memberi navigasi; source/AST memberi bukti lokasi.

## Settings pusat existing

Semua field berikut dideklarasikan di `app/core/config.py`; source default tersedia, jadi Required=NO untuk inisialisasi Settings. Environment override mengikuti nama field case-insensitive, tanpa prefix, dan `.env` existing loader. Default adalah deklarasi sumber, bukan nilai live. Semua adalah **default overridable**, bukan literal yang selalu mengunci runtime.

| Field (baris) | Default | Consumer app terbukti | Risk / catatan |
| --- | --- | --- | --- |
| app_name (7) | Nusantara Core + Hermes | routes.py:816 | LOW; metadata health |
| app_version (8) | 0.1.0 | routes.py:259,817,1661 | LOW; metadata, bukan deploy identity |
| debug (9) | false | NOT_PROVEN direct read | MEDIUM; jangan aktifkan produksi |
| host (10) | 127.0.0.1 | NOT_PROVEN direct read | MEDIUM; launcher menentukan bind aktual |
| port (11) | 8000 | NOT_PROVEN direct read | MEDIUM; bukan bukti service bind |
| llm_provider (12) | ollama | NOT_PROVEN direct read | HIGH; route memilih class Ollama langsung |
| llm_base_url (13) | http://localhost:11434 | routes.py:802,880; v2_routes.py:103,326 | MEDIUM; credential URL dilarang dalam desain dump |
| llm_api_key (14) | VALUE_NOT_RECORDED | NOT_PROVEN direct read | HIGH; credential value tidak diaudit/dump |
| llm_model (15) | llama3.2:1b | routes.py:803,883; v2_routes.py:104,326,333 | MEDIUM; request.model punya precedence di V1 chat |
| llm_context_tokens (16) | 4096 | models/ollama.py:47 | MEDIUM; provider memvalidasi 512–131072 |
| context_window_size (17) | 10 | NOT_PROVEN direct read | MEDIUM; deklarasi tidak membuktikan memory cap |
| session_timeout_minutes (18) | 30 | NOT_PROVEN direct read | MEDIUM; deklarasi tidak membuktikan TTL |
| embedding_model (19) | local-hash | NOT_PROVEN direct read | HIGH; berbeda dari constructor RAG |
| vector_store_type (20) | memory | NOT_PROVEN direct read | HIGH; berbeda dari store RAG |
| chunk_size (21) | 512 | NOT_PROVEN direct read | MEDIUM; KnowledgeBaseConfig punya field sendiri |
| chunk_overlap (22) | 64 | NOT_PROVEN direct read | MEDIUM; idem |
| retrieval_top_k (23) | 5 | routes.py:924; v2_routes.py:130 | MEDIUM; sebagian facade juga default 5 |
| privacy_filter_enabled (24) | true | NOT_PROVEN direct read | HIGH; flag tidak membuktikan policy aktif |
| log_level (25) | INFO | NOT_PROVEN direct read | MEDIUM; logging mempunyai setup tersendiri |

NOT_PROVEN direct read berarti pencarian `settings.<field>` tidak menemukan consumer app; bukan bukti tidak ada alias/dynamic access. Machine map juga mencatat consumer skrip/test/historical, tetapi tidak memperlakukannya sebagai eksekusi produksi.

## Parameter dan jalur terpisah

| Configuration / source | Consumer / precedence existing | Default / override | Hard-coded? / risk |
| --- | --- | --- | --- |
| OllamaProvider constructor, models/ollama.py:35 | Caller route V1/V2 memberi URL/model | URL localhost:11434, model llama3.2:1b, timeout 120 s; explicit constructor override | Overridable constructor; MEDIUM |
| V1 provider selection, routes.py:879 | `/v1/chat` membuat OllamaProvider; llm_provider tidak dibaca | request.model → Settings.llm_model | Class selection hard-coded; HIGH, route/CC-01 protected |
| Ollama options, models/ollama.py:45 | Generate request → provider options | num_predict 512; max_tokens request dibatasi context; temperature/top_p hanya bila tersedia | Default generation literal; MEDIUM |
| ModelRouter.route, models/router.py | Registered providers + task tree | literal llama3.2:1b/gpt-4o-mini/gpt-4o pada cabang | Model names hard-coded; MEDIUM; bukan bukti V1 memakai router |
| KnowledgeBaseConfig, knowledge/schemas.py:142 | RAG/ChunkProcessor config | IndoBERT base-p1, 768D, sqlite, sentence, chunk512/overlap64/top-k5; reranker false, max_documents10000 | Typed overridable config; HIGH jika disatukan dengan Settings secara diam-diam |
| RAG constructor, knowledge/rag.py:202 | KnowledgeEngine → create_rag; RAG membangun store/embedding default | Explicit config/store/embedding_func → default constructors | Default store SQLite dan adapter IndoBERT; HIGH karena persisted vector compatibility |
| SQLiteVectorStore, knowledge/store.py:18 | RAG store | explicit db_path → NUSANTARA_KNOWLEDGE_DB → data/knowledge/nusantara_knowledge.db; relative ke cwd | ENV/constructor override; HIGH; init dapat membuat direktori/schema, loader tidak boleh memanggilnya |
| IndoBERTClient, language/semantic/indobert_client.py:21 | Language semantic/RAG embedding adapter | explicit interpreter/worker → NUSANTARA_INDOBERT_PYTHON/WORKER → project-local defaults; timeout60 s | Constructor/ENV; HIGH untuk executable path; loader tidak menjalankan worker |
| Worker model, nusantara-models/indobert_worker.py:9 | Existing IndoBERT worker | indobenchmark/indobert-base-p1 | Literal worker constant; HIGH untuk model/dimension/index compatibility |
| Production semantic retriever | ProductionHybridRAG path | semantic_weight0.7 / lexical_weight0.3; constructor parameters | Separate production profile; HIGH; tidak diubah |
| V1 stage budget, routes.py:62 | `_run_sync_v1` | timeout30 s | Helper default; MEDIUM; route protected |
| app/main.py | FastAPI metadata, CORS, logging setup | API version/title/origins literals | Configuration occurrences; security/API semantics out of scope |
| NUSANTARA_DATA_DIR | api/v2_routes.py:45; mcp/stdio_server.py:19 | Direct environment read; default value omitted in discovery | ENV; HIGH; multiple consumers |
| NUSANTARA_DISCOVERY_HOSTS | api/v2_routes.py:56 | Direct environment read; values omitted | Governance/security boundary; HIGH; no policy rewrite |
| NUSANTARA_WORKSPACE | api/v2_routes.py:332 | Direct environment read; values omitted | PATH; HIGH |
| NUSANTARA_ADMIN_TOKEN | security/auth.py:11 | Existing auth consumer; value/reference defaults omitted | SECRET; HIGH; auth handler tidak diubah |
| Trust/Policy/DeveloperCore constants | Existing modules, discovery occurrences | Preserve existing version/rules/caps | Protected contract/security; metadata only in initial design |

RAG consumer findings berasal dari source yang dibaca, bukan import yang membuka database/worker. Sumber lama tetap ada. Tidak semua numeric literal adalah configuration: requirement/status/input data harus direview sebelum ekstraksi.

## Konflik yang harus dipertahankan selama migrasi

1. Legacy Settings embedding/store adalah deklarasi local-hash/memory; RAG existing memakai IndoBERT/SQLite. Snapshot desain harus menampilkan keduanya dengan provenance. Jangan mengubah embedding, vector dimension, atau store backend agar nilai terlihat konsisten.
2. Memilih provider pada Settings belum memilih class provider di V1. Loader yang menerima provider lain tanpa consumer nyata akan menimbulkan konfigurasi palsu; konfigurasi unsupported harus ditolak sebelum execution bila adapter diaktifkan.
3. Governance dan feature flags tidak boleh mengubah Trust/Policy/security, CC-01, atau DeveloperCore tanpa approval tambahan. Flag baru yang tidak terhubung harus diberi status unsupported/metadata-only.
4. Path resolution cwd/project root berbeda antarmodule. Pertahankan path efektif existing; schema baru tidak memindahkan database atau membuat direktori.

Phase 3 selesai sebagai peta statis dengan unknowns eksplisit. Runtime verification dan integration tests baru dilakukan sesudah desain disetujui; V1 acceptance tetap FAIL/HOLD.
