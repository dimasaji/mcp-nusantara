# Nusantara Configuration — Phase 5–6

Tanggal: 2026-10-06. Status: **COMPLETE — PASS_SCOPED** untuk source contract dan module isolated beserta testnya. Tidak mencakup integrasi runtime Phase 7 atau full regression Phase 9.

User menyetujui Phase 5–6 setelah desain Phase 4. Checkpoint Phase 0–4 dibaca dan hash evidence diverifikasi; audit/discovery/classification/map/desain tidak diulang atau ditulis ulang.

## Phase 5: aturan sumber final

Prioritas leaf-level: **DEFAULT → FILE → ENV → EXPLICIT**. File hanya JSON yang path-nya diberikan caller, maksimal 1 MiB; duplicate JSON keys, nonfinite JSON, root non-object, malformed/missing file, dan unknown field ditolak. Mapping bertingkat dibatasi kedalaman 12. Tidak mengevaluasi string, template environment, shell expression, atau source code.

Environment default kosong. Caller harus secara eksplisit memberi mapping environment; loader tidak membaca os.environ maupun `.env` otomatis. Alias case-insensitive; dua alias menuju field yang sama ditolak walaupun nilainya sama. Numeric/bool environment mengikuti JSON primitive, kemudian strict schema: bool `true/false`, integer tanpa coercion dari bool/float/string. Nama environment tidak terdaftar diabaikan sehingga credential dan setting lain dalam mapping tidak ikut disalin.

Alias existing: APP_NAME, APP_VERSION, DEBUG, HOST, PORT, LOG_LEVEL; LLM_PROVIDER, LLM_BASE_URL, LLM_MODEL, LLM_CONTEXT_TOKENS; EMBEDDING_MODEL, VECTOR_STORE_TYPE, PRIVACY_FILTER_ENABLED, CONTEXT_WINDOW_SIZE, SESSION_TIMEOUT_MINUTES; CHUNK_SIZE, CHUNK_OVERLAP, RETRIEVAL_TOP_K; NUSANTARA_KNOWLEDGE_DB, NUSANTARA_INDOBERT_PYTHON, NUSANTARA_INDOBERT_WORKER. Alias tambahan eksplisit: NUSANTARA_LLM_MODEL, NUSANTARA_RUNTIME_PORT, NUSANTARA_RAG_TOP_K. Alias map adalah MappingProxyType, bukan mutable registry.

EMBEDDING_MODEL/VECTOR_STORE_TYPE dan privacy/context-window/session-timeout masuk **legacy_declarations**, bukan mengubah RAG. Profil tunggal `current_v1_rag` merepresentasikan sumber RAG IndoBERT/768D/SQLite; production profile belum diaktifkan. Nilai field bisa dikonfigurasi dalam snapshot tanpa mengubah service/model/database yang sudah berjalan.

Evidence aturan: `phase-05-source/SOURCE_CONTRACT_20261006.json` dan checkpoint phase 5. Tidak menghapus `.env` loader/config lama atau mengganti precedence existing runtime.

## Phase 6: perubahan

- **Baru:** `app/core/nusantara_config.py`. Typed domain models Pydantic existing, nested frozen, frozen wrapper NusantaraConfig, provenance tuple berisi frozen records, loader dengan safe error boundary.
- **Baru:** `tests/test_configuration_contract.py`. Tidak ada perubahan existing tests.
- Kedua path belum ada sebelum implementasi; tidak ada existing source yang perlu disalin/ditimpa. Manifest hash protected sebelum implementasi menjadi baseline integritas. Rollback isolated berarti melepaskan penggunaan file baru pada tahap berikutnya; tidak ada runtime consumer yang perlu dipulihkan saat ini.

API: `load_nusantara_config(config_file=..., environment=..., overrides=..., project_root=...)`. Snapshot menyediakan property bertipe system, runtime, llm, embedding, rag, knowledge, paths, governance, features, legacy_declarations. Tidak ada instance config global. `safe_dump()` menghasilkan salinan baru, `canonical_json()` memakai ordering tetap; auth_env_ref dikecualikan dari dump/repr. Provenance mencatat source layer dan status UNWIRED/DECLARED_ONLY tanpa nilai input.

Schema memakai strict type, extra forbid, finite numeric values, bounds context/token/port/top-p, positive timeouts, chunk overlap < chunk size, weight pair dengan jumlah1, dan konsistensi reranker flags/model. Provider yang direpresentasikan hanya Ollama; backend snapshot knowledge hanya SQLite. Unsupported provider/store ditolak secara aman. Ini tidak membuktikan provider switching sudah tersedia pada runtime.

Path resolution bersifat leksikal, tidak memanggil resolve untuk mengikuti symlink, tidak memeriksa existence, tidak mkdir. Relative database mengikuti root yang ditangkap dari cwd bila project_root tidak diberikan. Default worker/interpreter tetap berbasis lokasi source project; explicit root menyusun sandbox defaults. Root tidak boleh diganti diam-diam melalui leaf overrides; gunakan argument project_root. Absolute path input dapat direpresentasikan, tetapi akses dan capability/security preflight tetap tanggung jawab consumer Phase 7.

Credential values tidak dimuat atau diselesaikan. Authentication reference hanya nama variable dengan pola identifier. URL provider harus HTTP(S), memiliki hostname, tidak memiliki embedded credential/query/fragment, dan port syntax valid/nonzero. Semua error loader menjadi ConfigurationError berisi kode tetap, tanpa raw Pydantic input/error dict atau isi file/env. Private schema bukan public error API; boundary yang didukung adalah loader.

Public metadata field seperti model/application_name harus digunakan untuk data non-secret; loader tidak dapat menebak credential yang sengaja dimasukkan ke field metadata. Tidak ada logging statement atau raw configuration logging. Governance refs/flags tetap metadata dan tidak memutasi security policy, Trust/Policy, DeveloperCore, atau CC-01.

## VERIFY

| Pemeriksaan | Hasil | Evidence |
| --- | --- | --- |
| Targeted awal | 50 passed, 0 failed; 0,42 s | CONFIGURATION_PHASE6_TARGETED_20261006.xml |
| Targeted final + existing compatibility | **116 passed**, termasuk **52 configuration tests**, 0 failed/errors/skipped; 11,06 s | CONFIGURATION_PHASE6_COMPAT_20261006.xml |
| Static scanner existing | 0 findings, PASS_SCOPED | CONFIGURATION_PHASE6_SECURITY_20261006.json |
| Protected source/config/DB/contract baseline | 296 file identik, 0 perubahan | phase-06-implementation/RESULT_20261006.json |

Sesudah 50 test pertama lulus, URL port validation diperketat dan dua kasus test ditambahkan; final source diverifikasi dengan compatibility suite. Ini bukan pengulangan baseline phase 0–4. Semua percobaan test disimpan.

Config tests meliputi precedence/merge/input unchanged, selected environment opt-in, `.env` tidak dimuat, alias conflict/order independence, strict types/nonfinite/ranges, unknown fields/provider, secret sentinel pada repr/dump/errors, nested immutability, defensive dump, lexical path/CWD compatibility, malformed/duplicate/oversized/missing file, missing/blank model, invalid env, depth cap/no interpolation, canonical determinism, weight/reranker cross-field consistency, dan larangan command/write/SQLite connection/engine import.

Compatibility suite menjalankan existing DeveloperCore/Gate14/mapper, CC-01 response projection, runtime identity, provider failure, dan V1 stage budget. Existing Starlette/httpx deprecation warning tetap muncul tanpa test failure. Test ini bukan integration proof untuk loader pada engine; existing paths tidak diubah.

Graph CLI existing diperbarui AST-only setelah perubahan: **5.359 nodes, 9.376 edges, 913 communities**, HTML aggregated community view. Warning existing: direktori temporary report tertentu tidak dapat dibaca, PDF extraction tidak tersedia, dan sebagian labels berasal dari hub. Tidak menjalankan LLM extraction atau membangun runtime Graphify baru.

## Checkpoint dan batas hasil

Checkpoint phase 6 COMPLETE/PASS_SCOPED; global progress selesai phase 0–6 dan menunggu scope integrasi Phase 7. Full runtime configuration validation Phase 8, full regression Phase 9, dan architecture review final Phase 10 **belum selesai**. File validation keseluruhan dan definition of done baru dapat ditutup setelah integration evidence tersedia.

Tidak mengedit `app/core/config.py`, engine, API routes/response projection, DeveloperCore, Trust/Policy, database, Docker, Oracle, production environment, atau config deployment. Service tidak direstart dan snapshot tidak digunakan oleh runtime existing. Build identity source baru bukan bukti service existing memuat source baru.

**V1 keseluruhan tetap FAIL/HOLD**. Gate oracle/symlink/deployment/compliance tidak ditutup oleh module isolated ini. Phase 7 harus menyebut consumer/file yang diizinkan; integrasi protected route/CC-01, security/governance/DeveloperCore, API publik, dan produksi tetap memerlukan approval khusus.
