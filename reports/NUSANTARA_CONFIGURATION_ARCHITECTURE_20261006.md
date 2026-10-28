# Nusantara Configuration Architecture — Design Contract Phase 4

Tanggal: 2026-10-06. Status: **DESIGN_READY — AWAITING APPROVAL**, belum diimplementasikan.

Dasar: baseline/discovery phase 0–1 yang dipertahankan, classification 3.371 occurrence phase 2, map statis phase 3, serta pemeriksaan source Settings/provider/RAG/path consumers. Kontrak command mewajibkan approval sesudah phase 4 sebelum phase 5. Persetujuan melanjutkan phase 2–4 tidak dianggap approval implementasi.

## Keputusan desain yang diusulkan

Gunakan Pydantic yang sudah tersedia. Tambahkan **satu module** `app/core/nusantara_config.py` untuk domain model, loader, dan safe validation; test kontrak pada `tests/test_configuration_contract.py`. Pemisahan loader/model ke banyak file belum diperlukan. Ini usulan nama/struktur, bukan file source yang sudah dibuat. Tidak membuat engine, Graphify runtime, LangGraph, dependency baru, atau global config mutable.

`NusantaraConfig` adalah immutable typed snapshot dengan nested models yang juga frozen, `extra=forbid`, finite numeric constraints, dan collection immutable. Mutable dict/list tidak dibiarkan sebagai escape hatch. Loader tidak mengimport `app.main`, routes, engine, SQLite store, atau worker; tidak mengeksekusi command, menulis file, membuat direktori, atau menyelesaikan credential secara otomatis.

Configuration hanya menyatakan parameter. Engine/consumer tetap menjalankan logic. Ketersediaan provider dan health adalah runtime observation terpisah, bukan bool config yang dapat membuat service dianggap healthy.

## Domain dan kontrak field

| Domain | Field utama / tipe | Default dan validasi usulan |
| --- | --- | --- |
| system | environment:str, debug:bool, application_name:str, version:str, timezone:str | Metadata default existing; environment explicit development untuk sandbox, tidak dianggap environment produksi efektif; timezone metadata Asia/Jakarta, tidak mengubah timestamp API |
| runtime | host:str, port:int, workers:int, stage_timeout_s:float, log_level:str, request_limit:int\|null | Existing host/port/log; workers1 usulan metadata, stage timeout30; port1–65535, workers>0, timeout finite>0; request_limit null berarti belum terintegrasi |
| llm | provider:str, base_url:str, model:str, auth_env_ref:str\|null, connection_timeout_s:float, generation:GenerationConfig | ollama/localhost/model existing, timeout120; nonempty model; HTTP(S) URL tanpa embedded credential/query secret; auth berupa nama variable, bukan nilai |
| generation | temperature:float\|null, top_p:float\|null, max_tokens:int, context_length:int | null/null mempertahankan provider defaults; max_tokens512; context4096 dan existing range512–131072; max_tokens>0 dan <=context; top_p(0,1], temperature finite>=0 sesuai adapter |
| embedding | provider:str, model:str, dimension:int, batch_size:int\|null, timeout_s:float | Profil RAG existing IndoBERT/base-p1/768D/60s; batch null jika belum ada consumer; dimension>0, kompatibilitas stored index harus divalidasi tanpa mengubahnya |
| rag | top_k:int, chunk_size:int, chunk_overlap:int, semantic_weight:float\|null, lexical_weight:float\|null, reranker_enabled:bool, reranker_model:str\|null, similarity_threshold:float\|null | top-k5, chunk512, overlap64, rerankerfalse; chunk>0, 0<=overlap<chunk; top-k>0; weight hanya production profile0.7/0.3, finite0–1 dan jumlah1; threshold null sampai consumer/range tervalidasi |
| knowledge | root:Path, database:Path, document_root:Path\|null, index:Path\|null, cache:Path\|null, store_backend:str | Database existing per profile, backend sqlite untuk current RAG; path lain null bila belum teridentifikasi; tidak membuka/membuat/memindahkan database |
| paths | project_root:Path, worker:Path, worker_python:Path | Existing root-local worker/interpreter dan explicit path override; platform-aware; worker existence diperiksa secara read-only pada integration preflight, tidak spawn |
| governance | trust_contract_ref:str, policy_contract_ref:str, grounding_contract_ref:str, evidence_requirement_ref:str | Reference/provenance atas kontrak existing; tidak ada aturan/threshold baru yang mengubah security decision |
| features | semantic_search:bool\|null, reranker:bool, graph_context:bool\|null, developer_core:bool\|null, experimental_features:bool | null berarti NOT_CONFIGURABLE_YET untuk unwired consumers; false experimental; perubahan governance/DeveloperCore tidak diaktifkan oleh flag |
| legacy_declarations | embedding_model:str, vector_store_type:str, privacy_filter_enabled:bool, context_window_size:int, session_timeout_minutes:int | Salin deklarasi Settings yang belum terbukti consumer; local-hash/memory bukan override untuk RAG IndoBERT/SQLite; metadata tidak mengklaim TTL atau policy enforcement |

Default baru yang hanya metadata tidak boleh mempengaruhi runtime sampai consumer disetujui dan diuji. Environment/domain metadata baru bukan perubahan production environment. Profile production paths/weights hanya merepresentasikan source existing; aktivasi tetap di luar scope awal.

Contoh API konseptual: `load_nusantara_config(...).llm.model`, `.embedding.model`, `.rag.top_k`, `.runtime.port`. Ini bukan perintah membuat object live dalam tahap desain.

## Sumber, precedence, dan provenance — usulan untuk Phase 5

Precedence leaf-level: **default profil yang terdokumentasi → optional explicit JSON config file → selected environment names → explicit runtime overrides**. Phase 5 harus memfinalisasi daftar alias dan precedence sebelum source dibuat. JSON dipilih agar tidak menambah YAML parser dependency; TOML/YAML existing tetap dipetakan, tidak dihapus/diubah.

Config file opsional hanya dibaca ketika path diberikan caller, dibatasi ukuran (usulan1 MiB), dengan object schema diketahui. Tidak ada autodiscovery file produksi, executable interpolation, eval, shell expansion, dynamic imports, atau side effects. Unknown keys ditolak. Malformed/missing explicitly requested file dilaporkan dengan error tetap, bukan fallback diam-diam.

Explicit env mapping mendukung nama existing LLm/Settings case-insensitive, NUSANTARA_KNOWLEDGE_DB, dan NUSANTARA_INDOBERT_PYTHON/WORKER. Alias baru harus didaftarkan per field; konflik dua alias pada field yang sama ditolak, bukan tergantung urutan dict. Tidak ada mass-copy os.environ. Test menyuplai mapping environment terisolasi; loader tidak memuat `.env` produksi secara implicit. `.env` existing loader tetap utuh pada tahap additive.

Per-field provenance mencatat DEFAULT/FILE/ENV/EXPLICIT dan status CONSUMED/DECLARED_ONLY/UNWIRED; mencatat nama key dan lokasi yang aman, bukan secret value. Order canonical untuk serialisasi non-secret. Object tidak memiliki timestamp wall-clock sehingga input snapshot yang sama menghasilkan representasi sama.

V1 `request.model` adalah override existing per request: hanya field model, bukan arbitrary config dict. Persetujuan desain tidak mengubah public API atau CC-01.

## Kompatibilitas dan integrasi bertahap — Phase 7 proposal

Existing `Settings`, `get_settings()`, `settings`, field names, constructor signatures, endpoint schema, dan test monkeypatch behavior dipertahankan selama additive stage. Tidak mengganti mutable legacy Settings menjadi frozen object secara diam-diam. Snapshot baru immutable dan explicit; legacy Settings menjadi batas kompatibilitas yang terdokumentasi, bukan shared mutable source baru. Satu field hanya boleh mempunyai satu resolved snapshot dalam jalur yang sudah dimigrasikan; consumer legacy belum dimigrasikan tetap diberi provenance legacy.

| Tahap | Integrasi yang dapat dipersiapkan | Batas persetujuan |
| --- | --- | --- |
| Runtime | Snapshot/validation dan read-only startup preflight; preserve launch defaults | Tidak mengubah deployment, Docker, service bind, CORS, public health version |
| Hermes/LLM | Factory dapat memberi config ke existing provider constructor tanpa mengubah engine semantics | V1 route memilih Ollama secara langsung; factory baru belum membuat V1 provider-switching bekerja. Editing protected route/CC-01 atau public API memerlukan approval khusus |
| Embedding | Parameter interpreter/worker/timeout ke constructor existing setelah explicit integration approval | Tidak mengganti model worker permanen atau dimension persisted vectors; tidak mengubah Ollama/worker installation |
| RAG | Mapping ke KnowledgeBaseConfig existing dan constructor injection | Preserve IndoBERT/SQLite; jangan menerapkan local-hash/memory legacy declaration ke RAG |
| Knowledge | Snapshot database path per profile, ctor arg existing | Tidak initialize store saat config loading; tidak move/migrate/write database |
| Governance | Contract references dan descriptive metadata | Tidak mengubah Trust/Policy/security policy/acceptance gate |
| API | Compatibility audit/test saja dalam initial scope | Endpoint/schema/CC-01 source tetap protected; behavior-changing wiring perlu approval tambahan |

Provider registry initial harus menyatakan hanya adapter yang benar-benar terintegrasi. Ollama dapat direpresentasikan; provider lain di configuration belum merupakan kemampuan end-to-end. Unsupported selection ditolak secara aman pada preflight consumer, tanpa fallback yang mengubah pilihan. Menambah provider adapter atau mengubah route provider selection menjadi keputusan lanjutan tersendiri. DoD “provider dapat diganti” **belum terpenuhi** oleh desain atau loader saja.

## Secret dan error contract

Secret tidak menjadi field plaintext pada snapshot, config file, report, repr, atau logs. Snapshot menyimpan authentication reference (nama variable) bila perlu; credential resolution hanya pada approved provider boundary. Existing llm_api_key value tidak disalin ke report/dump. Secret reference bukan nilai credential.

Error publik memakai kode dan allowlisted field identifiers, tanpa input_value, source payload, env value, URL credential, traceback filesystem, atau Pydantic error dict mentah. `hide_input_in_errors` saja tidak menjamin `.errors()` aman; wrapper harus membangun safe errors sendiri. Tidak mencetak config mentah; safe summary eksplisit dan exclude credential refs bila tidak diperlukan. Test harus menyuntik sentinel credential dan memeriksa seluruh repr/dump/error surfaces.

Pencegahan credential URL adalah validasi data baru pada loader isolated; perubahan security policy existing, CORS, auth, discovery hosts, Trust/Policy, atau handler HTTP tidak termasuk desain implementasi awal.

## Validation dan evidence plan — Phase 8/9

Target `tests/test_configuration_contract.py` harus memeriksa nested immutability, default profile, precedence seluruh layer, partial merge, alias conflict, finite/range/cross-field validation, unknown provider/field, missing requested file, invalid JSON, bounded read, required model, path resolution platform/CWD compatibility, malformed env, isolated explicit overrides, deterministic canonical snapshot, secret non-disclosure, serta no command/write/DB/worker side effects.

Integration tests harus memeriksa constructor menerima config sebenarnya; assertion import saja tidak cukup. Preserve V1 response projection/trust/citation dan schema existing. Verify lama Settings/model override tetap bekerja. Targeted harus PASS sebelum full regression, dan DeveloperCore tetap PASS_SCOPED. Tidak menjalankan tests baru dalam phase desain; tests source belum dibuat.

Backup setiap existing source sebelum edit, ubah satu consumer, targeted test, verify scope, checkpoint; existing-test failure akibat perubahan memicu stop/review. Pertahankan checkpoint historis. Rollback selektif, tanpa git reset/clean atau menghapus configuration lama.

## Review keputusan yang diperlukan

Approval berikutnya dapat memberi izin Phase 5–6 untuk memfinalisasi precedence/alias lalu membuat module isolated dan test kontrak. Phase 7 harus menyebut consumer/file yang diizinkan secara konkret; persetujuan umum desain tidak memperluas izin protected DeveloperCore/CC-01/Trust/Policy atau production.

Unknown 46 occurrence dan 2.732 legacy/historical occurrence tetap diberi status review. Desain tidak mengklaim seluruh hard-coded value sudah hilang, provider switch sudah aktif, effective runtime sudah terverifikasi, atau secret handling sudah dibuktikan oleh test. Phase 4 selesai sebagai dokumen reviewable; definition of done implementasi Phase 5–10 masih terbuka. **V1 keseluruhan tetap FAIL/HOLD.**
