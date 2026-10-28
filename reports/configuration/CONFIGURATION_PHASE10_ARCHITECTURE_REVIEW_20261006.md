# Nusantara Configuration — Phase 10 Architecture Review

Tanggal: 2026-10-06. **Review Phase 10 selesai: COMPLETE_WITH_OPEN_GAPS.** Implementasi dan regresi yang terbukti tetap **PASS_SCOPED**, DeveloperCore tetap **PASS_SCOPED**. Definition of Done Configuration Architecture **NOT_COMPLETE**. Acceptance Nusantara V1 tetap **FAIL/HOLD**.

## Jawaban review akhir

| Pertanyaan kontrak | Kesimpulan | Bukti dan batas |
| --- | --- | --- |
| Engine masih memiliki hard-coded configuration? | YA — gap terbuka | ModelRouter masih memilih literal llama/gpt; RAG memakai bobot 0.70/0.30 dan cutoff 0.30; KnowledgeEngine mempertahankan default top_k=5. Default di schema sah sebagai fallback; literal dalam consumer belum seluruhnya dipindahkan. |
| Model dapat diganti tanpa mengubah engine? | SEBAGIAN | OllamaProvider yang diberi snapshot memakai llm.model pada payload HTTP mocked. Default API memakai Settings existing, ModelRouter masih literal. Adapter embedding menolak model/dimensi selain IndoBERT base-p1/768; pergantian embedding/index belum tersedia. |
| Provider dapat diganti? | BELUM melalui snapshot | llm.provider hanya menerima ollama; embedding.provider hanya indobert; store_backend hanya sqlite. Kemampuan register provider pada router existing tidak membuktikan configuration-driven switching. |
| RAG parameter terpusat? | SEBAGIAN | Snapshot mengatur top_k, chunk_size/overlap pada RAG opt-in. Explicit KnowledgeBaseConfig/store/callback tetap memiliki prioritas. Bobot dan similarity_threshold ditolak oleh consumer, bukan diabaikan. Metadata reranker diteruskan; reranker model nyata belum dibuktikan. Facade search masih default top_k=5. |
| Path terkontrol? | SEBAGIAN | Path snapshot dinormalisasi secara lexical; database dan worker paths diteruskan pada consumer opt-in. Absolute path di luar project tetap diperbolehkan, symlink/existence/access tidak divalidasi loader. Jadi lexical resolution bukan workspace containment atau jaminan kecocokan index. |
| Secret aman? | PASS_SCOPED | Credential ENV tidak disalin, auth_env_ref tidak di-resolve dan tidak masuk dump/repr/provenance, URL dengan credential/query/fragment ditolak, public loader errors disanitasi. Public metadata bukan secret classifier; memasukkan secret ke field publik dapat mengeksposnya. Tidak mengklaim keamanan seluruh aplikasi/service. |
| Configuration dapat divalidasi? | PASS_SCOPED | Frozen strict schema, range/finite/cross-field checks, bounded JSON, duplicate/unknown-key rejection, env alias conflict checks, safe error boundary. Consumer preflight menolak embedding/RAG profile yang tidak didukung. Live health dan persisted-index compatibility belum dibuktikan. |
| Konfigurasi mudah ditest? | PASS_SCOPED | Loader isolated tanpa auto dotenv/os.environ, urutan DEFAULT < FILE < selected ENV < EXPLICIT; 52 contract dan 12 integration cases. Mock HTTP/worker/store dan isolated RAG ingestion/query; snapshot immutable. |
| Backward compatibility tetap terjaga? | PASS_SCOPED | Legacy constructors/default facade behavior dipertahankan dan regresi final lulus. Non-default explicit Ollama args mengalahkan snapshot, tetapi default-valued args dianggap unspecified saat opt-in. External clients, produksi dan deployment belum diverifikasi. |

## Referensi source yang ditinjau

- `app/core/nusantara_config.py:32–176`: schema/domain, provider literals dan secret reference; `:300–392`: validation boundary, precedence, lexical paths dan provenance.
- `app/models/ollama.py:35–81`: opt-in ctor precedence dan generation options; `:104–110`: payload model.
- `app/models/router.py:45–114`: pemilihan provider/model dengan literal existing.
- `app/knowledge/rag.py:203–249`: opt-in mapping dan rejection sebelum membuka store; `:508–509`, `:579`, `:604–605`: bobot/cutoff existing; reranker fallback sekitar `:668`.
- `app/knowledge/engine.py:11–14`, `:31–36`: forwarding snapshot dan default search top_k.
- `app/knowledge/indobert_embedding.py:21–37`: profile preflight dan worker path/timeout handoff.
- `app/api/routes.py:41`, `:801–803`, `:879–883`, `:924`: default KnowledgeEngine dan Settings/provider/retrieval path existing.
- `tests/test_configuration_contract.py:98–135`: safe URL, secret exclusion, immutability dan path checks; `tests/test_configuration_integration.py:22–168`: provider payload, worker/store mocks, RAG query dan protected-source checks.

Graph query CLI tidak dapat dijalankan karena uv trampoline pada environment ini. Fallback BFS pada graph existing dijalankan; query luas tercampur node temporary test fixtures, sehingga ditajamkan ke OllamaProvider/ModelRouter dari app. Graph dipakai untuk navigasi; source current dan test evidence menjadi dasar kesimpulan. Source location graph tidak dianggap otomatis identik dengan line source current. Tidak membangun ulang graph atau memasang dependency.

## Audit Definition of Done

| Syarat | Status |
| --- | --- |
| Seluruh konfigurasi existing teridentifikasi | PARTIAL — 3371 candidates terinventarisasi; 46 UNKNOWN; completeness semantik belum terbukti |
| Sumber setiap konfigurasi diketahui | PASS_SCOPED_STATIC — setiap row punya source occurrence; sumber efektif runtime belum seluruhnya diketahui |
| Consumer setiap konfigurasi diketahui | NOT_COMPLETE — 3365 rows LOCAL_OCCURRENCE_ONLY; 6 STATIC_SETTINGS_READ; map bukan bukti seluruh consumer runtime |
| Hard-coded configuration terpetakan | PASS_SCOPED_STATIC — candidate map dan consumer terpilih; bukan bukti migrasi seluruh literal |
| Configuration domain terdefinisi | PASS_SCOPED |
| Configuration contract tersedia | PASS_SCOPED |
| Loader tervalidasi dan validation tersedia | PASS_SCOPED |
| Engine dapat membaca configuration | PASS_SCOPED_OPT_IN — provider, embedding adapter, RAG dan KnowledgeEngine; default startup belum aktif |
| Model dapat diganti melalui configuration | PARTIAL — Ollama opt-in terbukti; router/default API/embedding belum lengkap |
| Provider dapat diganti melalui configuration | NOT_COMPLETE |
| RAG configuration terstruktur | PASS_SCOPED_SCHEMA; consumer coverage PARTIAL |
| Runtime configuration terstruktur | PASS_SCOPED_SCHEMA; runtime controls belum terhubung |
| Secret tidak bocor | PASS_SCOPED_CONFIGURATION_SURFACES |
| Backward compatibility terjaga | PASS_SCOPED_EXISTING_TESTS |
| Targeted tests PASS | PASS_SCOPED — 93 final targeted cases |
| Regression PASS | PASS_SCOPED_WITH_EXISTING_SKIP — 353 pass, 28 passing subtests, 1 skip |
| DeveloperCore tetap PASS_SCOPED | PASS_SCOPED |
| Tidak ada perubahan production | PASS_SCOPED_WORKSPACE_INTEGRITY — protected DB/config/deploy source unchanged; no runtime activation |

## Pekerjaan penutupan yang belum dilakukan

| Gap | Langkah berikut dan bukti penutupan yang diperlukan |
| --- | --- |
| Consumer discovery belum lengkap | Review 46 UNKNOWN dan candidate aktif; buktikan source-to-consumer links, pisahkan legacy declarations dari runtime effective values. |
| Default startup/API belum memakai snapshot | Desain composition root dan precedence terhadap Settings/request overrides, lalu integrasi serta API compatibility tests. Tetap tunduk pada batas CC-01/API publik dan production activation. |
| Model/provider switching belum lengkap | Desain provider factory/capability contract dan routing model per task; buktikan pergantian melalui config tanpa literal engine. Tidak mengganti installation/model permanen dalam review ini. |
| Embedding/index compatibility | Tetapkan preflight dimensi/model dan prosedur index compatibility; hindari penggunaan embedding baru terhadap index lama tanpa bukti. Schema/migrasi/database movement memerlukan scope terpisah. |
| RAG knobs belum seluruhnya consumed | Putuskan semantics bobot/threshold/facade defaults/reranker nyata; tutup dengan behavior tests pada query, bukan hanya schema acceptance. |
| Runtime/features/governance masih declarations | Tentukan consumer tiap field, enforcement sesuai contract existing dan diagnostics CONSUMED; auth reference resolution, batch dan production profiles perlu desain. Perubahan security policy tidak termasuk review. |
| Path/live runtime belum terbukti | Tentukan apakah containment wajib; buktikan access, worker/provider health dan effective runtime build/config dalam verifikasi terpisah. |
| Acceptance V1 masih HOLD | Tutup symlink mandatory gate, oracle review/missing, compliance CC02–06 serta deployment/restart/workload/rollback dengan evidence masing-masing. |

Backlog ini adalah hasil review, bukan implementasi baru atau pemberian izin untuk perubahan produksi/protected contracts. Tidak ada Phase 11 dalam command; titik lanjut adalah penutupan gap berdasarkan scope yang dipilih.

## Integritas, bukti, dan checkpoint akhir

Semua evidence checkpoint Phase 0–9 dan source hash yang disetujui cocok. Build tetap `sha256:487ace8eb2a8ba4d8c979fdc7728cefe7802eb0b3f8f01d3f6462d9c83e9492a`. Sebanyak 296 protected files cocok dengan baseline plus empat approved changes Phase 7; tidak ada drift tambahan. Historical evidence tidak diubah.

Regresi Phase 9 dipakai kembali: 353 pass + 28 subtest pass + 1 skip; XML aggregate 382 tests dan 354 testcase elements. Tambahan current Hermes smoke 1 pass/8 assertions tetap scoped tanpa provider generation/network/worker/database. Initial memory WinError5 Phase 7 tetap tercatat, penyebab belum terbukti, diagnosis dan final suite lulus.

Phase 10 tidak mengubah source/test, menjalankan ulang successful suites, memuat credential, membuka database, mengaktifkan snapshot pada service, restart atau deployment. Graph update tidak diperlukan karena source tidak berubah. Review tidak memanggil provider eksternal atau menggunakan layanan LLM eksternal.

Output machine-readable: `reports/configuration/phase-10-review/RESULT_20261006.json`. Checkpoint: `reports/configuration/phase-10-review/checkpoint.json`. Semua Phase 0–10 memiliki checkpoint scoped; keseluruhan arsitektur tetap **NOT_COMPLETE**, V1 **FAIL/HOLD**.
