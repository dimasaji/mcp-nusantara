# P0 tahap A — batas SOP V1

Tanggal:2026-10-21. Implementasi ini mengikuti persetujuan pemilik “Lanjutkan Proses Selanjutnya” sesudah usulan tahap pertama P0. Audit perbandingan sebelumnya tetap merupakan snapshot sebelum perbaikan; nomor barisnya tidak diperbarui seolah-olah temuan lama tidak pernah ada.

## Hasil implementasi

- Seluruh knowledge yang sudah ada diperlakukan **internal**. `app/security/v1_knowledge.py:18` V1KnowledgeBoundary mengembalikan evidence kosong untuk publik sebelum menyentuh retrieval, embedding atau store. Operator wajib terautentikasi di HTTP dan memakai provider Ollama. Belum ada fitur publikasi sumber; tidak ada dokumen otomatis diberi status public.
- `app/api/routes.py:1040` chat memvalidasi token yang diberikan, termasuk chat unscoped. `app/api/routes.py:1386` search_knowledge dan :1434 list_knowledge_documents juga operator-only, sehingga endpoint langsung tidak menjadi bypass. Header/body berisi document_ids atau operator=true tidak memberikan hak operator.
- `app/api/routes.py:176` _project_v1_chat_response mempertahankan bentuk citation V1 namun mengosongkan chunk. Judul/document_id tetap merupakan metadata operator, bukan izin membuka source di publik.
- Chat NDJSON kini mengirim status lalu final/error setelah grounding/projection. Observer delta dinonaktifkan selama penyelesaian request; tidak ada token model sementara yang ditampilkan. Client juga mengabaikan delta lama dan membuang chunk dalam PublicChatSchema (`control-plane/src/api.ts`, sendUserChat/PublicChatSchema).
- Riwayat/context/replay operator dan publik memakai namespace terpisah melalui `app/security/v1_knowledge.py:12` v1_session_id; `app/memory/engine.py:26` _store mendukung namespace baru. Riwayat legacy dikarantina tanpa dibaca, dimigrasikan atau dihapus. Caller yang tidak mengirim session_id memperoleh UUID baru (`app/api/routes.py:110` ChatRequest), bukan shared default web.
- UI remount pada perubahan credential dan memakai storage key P0 yang terpisah. Riwayat/tampilan operator tidak dipertahankan saat beralih ke publik, judul pertanyaan operator tidak ditulis ke localStorage, dan citation hanya menampilkan metadata (`control-plane/src/assistant.tsx`, UserChat/ChatSession).

## Perbaikan prasyarat yang ditemukan saat uji

Regresi ingestion nyata pada SQLite fixture gagal karena konstruktor RAG belum menginisialisasi `_chunker`. Pemeriksaan diff menunjukkan perubahan ini sudah ada sebelum pekerjaan tahap A. Konstruktor juga mengabaikan `embedding_func`, sehingga fixture/offline caller dapat memakai adapter model yang tidak dimaksudkan.

Perbaikan terbatas pada `app/knowledge/rag.py`, RAG.__init__: inisialisasi chunker berdasarkan konfigurasi atau instance eksplisit, serta hormati embedding_func eksplisit sebelum pilihan adapter default. Cabang legacy local-hash yang sudah ada dipertahankan. Tidak mengganti model produksi, melakukan re-embedding atau mengubah schema/index. Test ingestion idempotency/rollback dan scope25dokumen sekarang lulus.

## Evidence pengujian

Uji awal:8kasus boundary gagal pada implementasi lama. Endpoint search tambahan direproduksi mengembalikan HTTP200 kepada caller tanpa token; sesudah perubahan mengembalikan403 sebelum store diakses.

Runner akhir:

```powershell
& .venv/Scripts/python.exe -B scripts/test_v1_sop_boundary.py
```

Hasil akhir ditulis ke [python-tests.txt](../../../artifacts/cmp-p0-boundary/python-tests.txt): **89 passed**. Durasi yang tercantum dalam log adalah waktu test fixture, bukan waktu respons chat/model. Warning222berasal dari konfigurasi asyncio_mode saat plugin autoload dimatikan dan deprecation datetime.utcnow; tidak diubah dalam pekerjaan ini. Runner menjalankan tujuh file terpilih; bukan seluruh suite proyek.

Runner mematikan dotenv dan environment source Settings **sebelum collection**, memindahkan Path.home ke direktori sementara, mematikan bytecode/cache/plugin autoload, dan memasang tripwire untuk pembukaan .env serta data produksi. Import app.models memiliki side effect pemuatan Settings; hal ini ditemukan setelah run awal, lalu runner diperketat. Tidak ada credential dicetak atau disalin. Test boundary menggunakan transport ASGI in-process, provider stub, memori sementara, serta socket guard; test retrieval memakai SQLite/embedding sintetis di tmp_path, bukan database/model produksi.

Cakupan utama:

- Public scoped/unscoped deny-before-retrieval, body operator tidak dipercaya, token salah ditolak sebelum model.
- Operator lokal tetap dapat retrieval; operator eksternal ditolak sebelum ledger/provider dibangun; percakapan eksternal publik tidak memperoleh evidence internal.
- Raw chunk tidak hadir pada projection, stream, atau pembacaan history; exception internal tidak bocor melalui event error.
- Isolasi context/history/idempotency dua audience pada session/request_id yang sama; replay tidak memanggil model dua kali; namespace baru durable setelah MemoryEngine dibuka ulang.
- UUID default unik, ingestion rollback/dedup, scope sebelum top-k, grounding dialog dan timeout sync.

UI:

```text
node node_modules/vitest/vitest.mjs run tests/chat-privacy.test.tsx tests/chat-stream.test.tsx tests/assistant.test.tsx tests/operator.test.tsx tests/operator-followup.test.tsx --reporter=dot
```

**45 passed,5files**. Semua fetch dimock. `node node_modules/typescript/bin/tsc --noEmit --incremental false` exit0. Bukan hasil browser/e2e/live server; tidak ada chat produksi atau API berbayar dipanggil.

## Batas penerimaan

Tahap A **implementasi dan regresi offline selesai**, bukan PASS release/global Guard. Tidak melakukan restart/deploy, migrasi DB, ingest SOP produksi, atau pengukuran model hidup. SOP publik sengaja belum diaktifkan: pemilik perlu menetapkan fakta layanan dan metadata apa yang boleh dipublikasikan. Konsekuensinya chat publik dapat abstain pada pertanyaan layanan yang sebelumnya memakai knowledge internal.

Riwayat lama tetap ada di disk tetapi tidak muncul melalui namespace P0 baru. Tidak membuka atau memigrasikan data lama otomatis. Token admin yang sudah ada tetap shared-admin, bukan RBAC multiuser lengkap; lifecycle/rotation dan principal governance tetap P1. Caller yang memilih sendiri session ID lemah tidak memperoleh jaminan ownership multiuser; session capability yang dihasilkan UI/default adalah UUID.

Selanjutnya P0 tahap B: PIAK-03 actual-index retrieval, jawaban/sitasi/abstention pada dataset resmi. Tahap C:20turn dan TTFT/total runtime. Hermes/Developer Agent/Self-Learning tetap HOLD; tidak ada source Hermes yang diedit dalam tahap A.

## Review perubahan dan rollback

Working tree awal sudah dirty pada tujuh file: routes.py, hermes/agent.py, knowledge/rag.py, control-plane/README.md, ui-routing.test.tsx, verification-pages.test.tsx, vitest.config.ts. Perubahan tersebut tidak dihapus. Diff terhadap HEAD berisi pekerjaan pemilik juga; **jangan memakai git reset/restore global** untuk rollback tugas ini.

File produk tahap A: app/security/v1_knowledge.py (baru), app/api/routes.py, app/memory/engine.py, app/knowledge/rag.py, control-plane/src/api.ts, control-plane/src/assistant.tsx. File test/runner: tests/test_v1_sop_boundary.py dan scripts/test_v1_sop_boundary.py (baru), control-plane/tests/chat-privacy.test.tsx (baru), assistant.test.tsx, chat-stream.test.tsx, serta penyesuaian auth/namespace pada test_audit_regressions.py, test_chat_request_idempotency.py, test_effective_rag_profile.py, test_v1_operator_control.py. Tiga file test berkomposisi aplikasi normal tidak dijalankan langsung; runner terisolasi memakai fungsi HTTP asli yang diekstrak AST agar tidak melakukan startup produksi.

Rollback terbatas harus membalik hanya hunk tahap A setelah review, menjaga perubahan pemilik. Tidak ada schema migration atau source document rewrite untuk dibalik. Key history lama tidak berubah; namespace baru tidak boleh disalin ke public legacy history saat rollback. Membalik guard akan membuka kembali risiko audit, sehingga release publik tidak boleh dilanjutkan dengan guard dibatalkan. Tidak ada script rollback destruktif dijalankan.

`graphify update .` dijalankan AST-only tanpa LLM/API. Update terakhir mencatat8958node,18210edge dan672community; warning syntax error pada patch_embedding_identity.py:44 berasal dari file lama di luar perubahan tahap A. Tidak memperbaiki file lama tersebut atau menjalankan pelabelan LLM. File graph yang dihasilkan bukan bukti bahwa gate release sudah lulus.

Verifikasi penutup:89test Python PASS dalam3.36s dengan tripwire file/SQLite produksi aktif;45test UI PASS; TypeScript exit0; `git diff --check` exit0 dan sintaks seluruh file Python baru valid. Run graphify terakhir exit0, tanpa perubahan topology tambahan. Status Git memuat perubahan tahap A serta tujuh file dirty yang sudah ada sejak baseline; tidak ada commit, push atau restart layanan dilakukan.
