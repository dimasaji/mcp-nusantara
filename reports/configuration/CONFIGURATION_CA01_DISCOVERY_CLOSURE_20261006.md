# Nusantara Configuration — CA-01 Discovery Closure

Tanggal: 2026-10-06. **Audit lanjutan selesai — PASS_SCOPED_STATIC.** Triage 46 kandidat UNKNOWN selesai; gap CA-01 keseluruhan tetap **PARTIAL**, karena consumer completeness dan effective runtime belum terbukti.

Checkpoint Phase 0–10 dipakai sebagai dasar, tanpa mengulang phase atau successful tests. Original discovery/classification/map dan laporan Phase 10 tetap disimpan tanpa perubahan. Hasil baru merupakan overlay audit, bukan perubahan configuration behavior.

## Hasil triage

Seluruh 46 candidate IDs tercakup tepat satu kali, dengan source hash, historical line, current symbol locations, reviewed domain, disposition dan alasan. Perubahan line sejak integrasi Phase 7 ditangani lewat pencarian symbol AST; historical line tidak dianggap otomatis sebagai posisi source current.

| Disposition | Jumlah |
| --- | ---: |
| Configuration declarations | 2 |
| Direct configuration ENV reads | 3 |
| Secret ENV identifier | 1 |
| Test-harness configuration | 1 |
| Compile-time path policy | 1 |
| Unreferenced compile-time constant | 1 |
| Unwired config document | 1 |
| Build-tool configuration | 1 |
| Derived values/execution objects | 22 |
| Result schema/call metadata | 4 |
| Evaluation evidence data | 2 |
| Dependency injection | 2 |
| Compatibility aliases/lookups | 2 |
| Verification source paths | 2 |
| Test-fixture parameter | 1 |

Disposition menentukan peran occurrence. Configuration declaration, policy constant, result metadata, dan test fixture tidak disamakan sebagai runtime knobs. Review tidak menghapus kandidat dari historical inventory atau mengklaim seluruh kategori baru adalah setting aktif.

## Temuan yang memengaruhi rencana integrasi

- `CONTEXT_WINDOW_SIZE` pada env example dan `Settings.context_window_size` adalah deklarasi konfigurasi. Tidak ditemukan direct AST read `settings.context_window_size` pada source app. Field context state bernama sama memiliki consumer, tetapi bukan bukti wiring Settings. Snapshot alias mengisi legacy_declarations, bukan runtime enforcement.
- `NUSANTARA_DATA_DIR` dibaca V2 persistence dan MCP stdio; `NUSANTARA_WORKSPACE` diteruskan endpoint V2 dev ke DevCore. Source-to-consumer direct ENV reads terbukti secara statis; nilai runtime tidak diperiksa.
- `NUSANTARA_ADMIN_TOKEN` adalah identifier secret untuk fail-closed admin authorization. Nilai credential tidak dibaca/disimpan audit, policy tidak dimigrasikan.
- `rag_priority` adalah daftar source paths dalam protected DeveloperCore context routing. Ini path policy existing; bukan feature flag yang bebas diubah.
- `MIN_GROUNDED_CONFIDENCE` merupakan class constant reasoning; pencarian identifier menemukan deklarasi tanpa referensi app lain. Keberadaan constant tidak membuktikan threshold diberlakukan.
- `config/rag_runtime.json` adalah configuration document yang belum terbukti loaded. `scripts/baseline_rag_cache.py:23` membuat path dan memeriksa keberadaannya, lalu memakai parameter literal sendiri; reference path itu bukan pembacaan JSON. Consumer eksternal/dynamic tetap NOT_PROVEN.
- `HybridRAG`, parameter `rag`, nilai grounded/coverage/paragraphs/average-confidence dan fixture `n_rag` adalah alias, dependency atau hasil eksekusi. Kandidat tersebut tidak memerlukan migrasi sebagai configuration knobs hanya karena namanya cocok dengan heuristic discovery.

## Bukti consumer tambahan

AST audit mencakup **192 app Python files**, dengan **0 parse errors**. Ditemukan **16 Settings attribute access nodes**, **42 snapshot-parameter attribute access nodes**, dan **8 direct ENV read calls**. Jumlah access nodes mencakup akses group/leaf yang bersarang; bukan jumlah unique settings atau bukti semua field consumed.

Settings bindings dilacak dari import `app.core.config`. Snapshot bindings berasal dari nama parameter yang annotated NusantaraConfig pada file; bukti ini tidak melakukan interprocedural dataflow dan dapat memerlukan review shadowing/alias per function. Pemakaian alias seperti generation/self configuration tidak dicakup otomatis oleh inventaris direct parameter accesses. JSON mencantumkan batas tersebut, sehingga tidak mengklaim consumer completeness.

Graph existing dipakai sebagai navigasi Settings/KnowledgeEngine sebelum source audit; source current dan AST menjadi dasar overlay. Tidak menjalankan aplikasi, import module runtime, memuat `.env`, membuka DB, menjalankan worker/provider, atau mengubah source. Runtime identity dihitung hanya dari file untuk verifikasi build.

## Evidence dan batas penutupan

- `closure-ca01/UNKNOWN_TRIAGE_20261006.json`: semua 46 IDs dan reviewed dispositions.
- `closure-ca01/CONSUMER_LINKS_20261006.json`: direct Settings/snapshot/ENV links beserta source hashes.
- `closure-ca01/checkpoint.json`: verifikasi integritas dan titik lanjut.

Historical evidence hashes dan approved source hashes tetap cocok; 296 protected files tidak memiliki drift tambahan. Source build tetap `sha256:487ace8eb2a8ba4d8c979fdc7728cefe7802eb0b3f8f01d3f6462d9c83e9492a`. Regresi Phase 9 tetap berlaku karena tidak ada source/test changes: 353 pass, 28 subtests pass, 1 skip; DeveloperCore PASS_SCOPED.

**CA-01 belum ditutup penuh:** 46 UNKNOWN pada inventory lama kini memiliki overlay triage, tetapi discovery completeness, transitive consumer mapping, external/dynamic consumers dan effective live values masih belum terbukti. Tidak mengganti angka historical UNKNOWN dengan klaim “semua konfigurasi diketahui”.

Titik lanjut: desain wiring composition root dan precedence snapshot terhadap Settings/request overrides, dengan daftar field yang benar-benar consumed. Provider factory/model routing, RAG semantics dan runtime activation tetap membutuhkan rencana perubahan yang konkret sebelum implementasi; batas public API, CC-01, security policy, database/deployment/production tetap berlaku. Tidak membuat Phase 11 karena command berakhir pada Phase 10.

Configuration Architecture tetap **NOT_COMPLETE**; Nusantara V1 **FAIL/HOLD**. Audit ini menutup tahap triage dan menambah consumer evidence, tanpa menutup acceptance gates lama.
