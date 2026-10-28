# MDE-01 Configuration Intelligence

Status: **PASS_SCOPED_STATIC — audit selesai, source tetap read-only.** Configuration Architecture **NOT_COMPLETE**, DeveloperCore **PASS_SCOPED**, Nusantara V1 **FAIL/HOLD**.

Perintah pengguna ditemukan di `docs/commands/NUSANTARA MASTER DEVELOPER ENGINE.md`; path `docs/NUSANTARA MASTER DEVELOPER ENGINE.md` tidak ada. Pelaksanaan mengikuti first task section 20: hanya MDE-01, laporan dan checkpoint, lalu berhenti. Phase 0–10 dan successful regression tidak diulang.

## Ringkasan yang diminta command

| Ukuran | Hasil dan arti |
| --- | --- |
| Total configuration fields | 75 central leaf fields: 56 snapshot dan 19 Settings; auxiliary config-schema candidates dicatat terpisah dalam JSON |
| Historical inventory | 3371 occurrences dipakai kembali; bukan 3371 unique runtime fields |
| Direct consumers | 39 static read sites pada 27 central fields; scoped AST bindings/aliases, bukan bukti nilai live |
| Transitive consumers | 2 bounded paths, didukung 3 snapshot-forwarding edges dengan import/local-class resolution |
| Dynamic candidates | 68 reflection sites untuk investigasi; sebagian mungkin tidak berkaitan dengan config. External launcher/service/request/subprocess consumers masih NOT_PROVEN |
| Hard-coded candidates | 6 behavior groups prioritas: router models, RAG weights, cutoff, reranker, facade top_k, production retriever semantics |
| Legacy declarations | 24 central declarations: 19 Settings + 5 snapshot legacy_declarations; 2732 historical LEGACY occurrences dicatat terpisah |
| Unwired configuration | 48 central fields tanpa direct AST read; kandidat unwired/indirect, bukan proven dead. Beberapa read sites hanya validation/rejection |
| Effective candidates | 80 records: 75 central defaults + 5 behavior/index candidates; 0 verified live values |
| Migration candidates | 15 finding records; 2 CRITICAL, 11 HIGH, 2 MEDIUM |

Seluruh 46 UNKNOWN memakai overlay triage sebelumnya. Source candidate/default/declaration dibedakan dari CONSUMED dan EFFECTIVE; konsumsi behavior opt-in untuk 14 fields didukung existing tests. Nilai static, metadata model, path reference, dan schema acceptance tidak dipromosikan menjadi konfigurasi aktif runtime.

## Evidence dan cakupan

AST audit mencakup 192 source Python app, 0 parse errors. Settings reads harus memiliki import binding dari app.core.config. Snapshot reads dilacak dalam scope function menggunakan parameter annotated NusantaraConfig, constructor-assigned members, serta alias lokal. Import/constructor/forwarding evidence tersedia dalam consumer map. Pendekatan ini masih lexical, tidak branch-sensitive dan tidak membuktikan seluruh dynamic dataflow.

Jalur transitive terbukti secara statis: KnowledgeEngine → create_rag → RAG, dan create_rag → RAG → IndoBERTEmbeddingAdapter. Kondisi explicit rag, KnowledgeBaseConfig/store/callback tetap membatasi jalur. Handoff adapter/worker constructor bukan bukti worker hidup.

Graph existing dipakai sebagai scoped navigation untuk Settings, OllamaProvider, ModelRouter, KnowledgeEngine, Hermes, RAG dan adapter. Confidence EXTRACTED/INFERRED tidak disamakan dengan proven field consumption. Source current dan exact import/call bindings memvalidasi temuan.

Existing isolated behavior tests menjadi evidence provider payload/options, RAG ingestion/query, worker-client constructor handoff dan DB path handoff. Tidak menjalankan test suite baru karena tidak ada perubahan source. Regresi baseline tetap 353 pass, 28 subtests pass, 1 skip. XML aggregate 382 tests memiliki 354 testcase elements; known symlink skip tidak ditutup oleh audit.

## Highest-risk findings

1. **MDE-CONFIG-008 — Embedding/index compatibility, CRITICAL.** Model dan dimensi adapter fixed-profile; index metadata belum diperiksa. Jangan memakai embedding baru terhadap index lama tanpa preflight dan migration scope.
2. **MDE-CONFIG-010 — Governance/features, CRITICAL.** References/flags tidak membuktikan enforcement. Configuration tidak memberi authorization; protected Trust/Policy tetap otoritatif.
3. **MDE-CONFIG-001 — Composition root, HIGH.** Default API memakai Settings dan constructors existing, bukan snapshot. Wiring dapat memengaruhi response/failure/latency; desain precedence dan compatibility diperlukan sebelum perubahan.
4. **MDE-CONFIG-004 — RAG weights, HIGH.** Canonical RAG fixed 0.70/0.30 berbeda dengan production retriever yang menormalisasi weights. Field bernama sama belum tentu behavior sama.
5. **MDE-CONFIG-005 — RAG threshold, HIGH.** Cutoff evidence 0.30 tidak otomatis identik dengan similarity_threshold. Behavioral contract diperlukan sebelum mengganti literal.

Temuan tambahan: ModelRouter selection literal bisa berbeda dari model payload provider; named reranker masih word-overlap fallback; facade default top_k=5 mengalahkan snapshot retrieval default. Settings local-hash/memory bukan bukti RAG memakai profil tersebut. `rag_runtime.json` hanya referenced path pada diagnostic script, bukan proven loaded JSON.

## Precedence, duplicate, effective context

18 pasangan deklarasi Settings/ENV alias → snapshot terpetakan. Kesamaan nama tidak membuktikan runtime equivalence. Loader precedence DEFAULT < JSON FILE < selected ENV < EXPLICIT sudah tervalidasi isolated; Settings auto dotenv berbeda dengan snapshot environment yang harus diberikan eksplisit.

Non-default explicit Ollama constructor values menang terhadap snapshot; default-valued arguments dianggap unspecified saat opt-in. Generation request options menang terhadap snapshot defaults. Explicit RAG dependency/config/callback punya prioritas. Snapshot path defaults dapat menutupi underlying client ENV fallback. Semua konflik/kontrak dicatat agar composition design tidak mengubah semantics diam-diam.

EffectiveConfiguration dirancang secara konseptual dalam laporan candidates: field, value candidate, source, consumer, status, risk. Mencakup provider/model, embedding/dimension, store, RAG knobs/reranker dan runtime host/port. Tidak dibuat runtime class, singleton, endpoint atau actual diagnostics. Semua live effective values tetap NOT_PROVEN. Credential values tidak diambil; secret reference/Settings key fields tidak direkam nilainya.

## Protected boundaries dan urutan rekomendasi

Protected boundaries: app/developer_core, CC-01/public API/schema, Trust/Policy/security, database/schema/production data, deployment/Docker/.env, Oracle/compliance/acceptance, constructor compatibility, dependencies/model/Ollama installation dan service restart. Semua finding mencatat boundary, impact, behavior tests, rollback dan status REPORT_ONLY.

Urutan rekomendasi: composition/compatibility/path ownership → actual provider capability/secret-reference design → model selection consistency → RAG behavior contracts → embedding/index safety → runtime enforcement → governance/feature mapping. Tidak mengklaim OpenAI atau Anthropic AVAILABLE; registry configuration acceptance tidak menggantikan actual adapter/capability proof.

Tahap berikutnya: **Composition Root design + impact analysis**, kemudian approval sebelum source changes. Desain harus menentukan cara snapshot, Settings, ENV dan request override membentuk dependency secara deterministik, serta mempertahankan public contracts. Tidak membuat Phase 11 atau generic execute/deploy tools.

## Output dan checkpoint

- `CONFIGURATION_INTELLIGENCE_20261006.json`: inventory, declarations, lifecycle, duplicate/conflict/precedence, dead/unwired candidates dan risk/order.
- `CONFIGURATION_CONSUMER_MAP_20261006.json`: scoped direct accesses, import/constructor evidence, transitive paths, dynamic candidates dan source hashes.
- `CONFIGURATION_EFFECTIVE_CANDIDATES_20261006.json`: conceptual context, 80 value candidates, behavior evidence dan NOT_PROVEN live status.
- `CONFIGURATION_MIGRATION_CANDIDATES_20261006.json`: 15 complete finding records dengan required tests, boundary, impact dan rollback.
- `checkpoint.json`: output hashes, protected integrity, resume state dan approval gate.

Source build tetap `sha256:487ace8eb2a8ba4d8c979fdc7728cefe7802eb0b3f8f01d3f6462d9c83e9492a`. Protected source/evidence harus cocok dengan checkpoint CA-01 sebelum audit ditutup. Tidak ada source/test edits, provider calls, worker execution, database connection, environment mutation, package/model install, restart atau deployment. Graph tidak dibangun ulang karena source tidak berubah.

Sesuai section 20: **“Berhenti setelah report dan checkpoint berhasil dibuat.”** dan **“Menunggu approval sebelum masuk ke Composition Root.”** MDE-01 berhenti pada checkpoint ini; roadmap belum dianggap selesai.
