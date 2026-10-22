# Roadmap adopsi V1 — P0, P1, HOLD

Dokumen ini usulan [INFERENSI] dari bukti kode pada tiap gerbang; bukan izin implementasi atau klaim gerbang lulus. Tidak ada source diperbaiki. `OW` = `E:/OpenWebUI/.venv/Lib/site-packages/open_webui`.

## Hubungan dengan GATES.md

[FAKTA-KODE/DOKUMEN] `docs/audit/GATES.md:16-25` mengharuskan compatibility boundary /v1 dan human approval untuk perubahan berisiko; :54 acceptance berbasis evidence; :111 Gate2 hardening; :130 Gate3 observability; :175 Gate7 RAG; :187 Gate8 MCP; :199 Gate9 tool governance; :338 Gate18 human approval; :368 Gate20 regression/security; :381 Gate21 release/rollback. Dokumen memuat tabel awal dan tambahan audit historis pada bagian31+ (:444 dan seterusnya); status yang berbeda tidak disederhanakan menjadi PASS baru.

[INFERENSI] Gerbang A–F berikut adalah paket acceptance di dalam gerbang proyek yang sudah ada, **bukan urutan GATES pengganti**. Boleh mengumpulkan bukti untuk gate lama yang berlubang; tidak menganggap gate berikutnya lulus sebelum dependency evidence yang relevan lengkap. Urutan P0 dahulu, lalu P1; Hermes/Developer/Self-Learning tetap HOLD walau source legacy dipanggil jalur V1.

## A — P0: boundary SOP dan egress sebelum pengujian publik

Dasar: `app/api/routes.py:1024` chat dan :211-214 _project_v1_chat_response raw chunks; `app/knowledge/engine.py:46` unscoped search tanpa ACL; `app/hermes/agent.py:795/817` prompt evidence; `app/models/ollama.py:193` provisional delta sebelum grounding `app/hermes/agent.py:837`. Pola **ADAPT**: `OW/routers/retrieval.py:2722` _validate_collection_access. RISK-CMP-001/002/003. Gate5/7/20, dependency baseline Gate0/1 dan rencana rollback.

Acceptance terukur yang diusulkan:

- Tetapkan klasifikasi public/internal/restricted pada sumber dan identitas request; sumber tanpa klasifikasi ditolak dari publik.
- 100% case negatif public→restricted ditolak **sebelum** retrieval/prompt/model; yang diukur adalah event tahap, bukan sekadar respons akhir403.
- 0 raw SOP pada schema final, event streaming, source preview, history, public error dan public audit; sitasi publik hanya metadata yang disahkan.
- 0 request eksternal dibentuk/dikirim pada konteks SOP untuk request scoped maupun unscoped. Uji dengan provider stub, external network dimatikan.
- Uji delta berbahaya, cancel, provider error setelah delta, dan grounding reject; teks yang dilarang tidak pernah tampil sebelum reject.

PASS memerlukan kontrak disclosure yang disahkan, hasil negatif per-case, trace teredaksi serta review pemilik. Audit ini: **NOT_VERIFIED**, bukan PASS.

## B — P0: RAG PIAK-03 dari source resmi ke actual index

Dasar: `app/knowledge/engine.py:189` pipeline; `app/knowledge/rag.py:270` ingest_document dan :595 _query; `app/knowledge/indobert_embedding.py:21` profile768D; `tests/test_v1_service_dialogue.py:44` retrieval mock; `app/knowledge/chunker.py:18/20` strategy aliases. **KEEP** ingestion/grounding lokal; **ADAPT** pengujian actual-index. RISK-CMP-004/013. Gate7/12/20; dependency A dan Gate2/3 instrumentation.

Acceptance terukur yang diusulkan:

- Manifest PIAK-03 disahkan pemilik: source ID, revisi, checksum, izin pakai dan expected section IDs; laporan publik tidak membawa isi mentah.
- Satu ingest resmi menghasilkan receipt ekstraksi/chunk/embedding/index. Ingest sama dua kali tidak menambah duplikasi; revisi konflik ditolak atau dimigrasikan sesuai policy; failure tengah ingest meninggalkan 0 record parsial.
- Minimal20 pertanyaan non-hardcode, termasuk parafrasa, beda aspek, SOP yang mirip, dan pertanyaan tidak tersedia. Retrieval memakai actual V1 index/model, tidak monkeypatch search_knowledge.
- Target awal untuk sampel terkurasi: 100% kasus answerable menemukan section expected dalam top-k; 100% jawaban final didukung sumber/revisi yang benar; 100% unanswerable abstain; 0 fakta layanan tambahan tanpa evidence. Ini acceptance usulan untuk set terkurasi, bukan klaim generalisasi seluruh SOP.
- Uji mengubah label sampel dan menambahkan dokumen pembanding; jawaban mengikuti evidence, bukan mapping pertanyaan→jawaban. Catat actual chunker/reranker, bukan hanya nama konfigurasi.

PASS memerlukan trace actual-index teredaksi, penilaian pemilik atas jawaban/sitasi, dan bukti A tetap lulus. Audit ini: **SEBAGIAN kode, runtime NOT_VERIFIED**.

## C — P0: sesi, timeout dan stabilitas20-turn

Dasar: `app/memory/engine.py:26` persist hanya web-UUID, :60 begin_chat/:110 finish_chat; `app/api/routes.py:109` default session web; :78 _run_sync_v1; `app/models/ollama.py:199` timing; `control-plane/src/assistant.tsx:20-21` browser pointer. **KEEP** offload/idempotency; **ADAPT** contract session dan receipt latency. RISK-CMP-005/010/011. Gate2/3/6/10/20; dependency A/B.

Acceptance: jalankan rencana laporan10, tiga batch20 warm turn plus cold baseline terpisah; 20/20 turn per batch tanpa error tak terduga atau sesi hilang, reload/restart terkendali mempertahankan history, request ID yang sama tidak memanggil model dua kali, unknown outcome tidak diulang otomatis. Laporkan TTFT aman dan total untuk setiap turn serta p50/p95/max; model-not-called dipisahkan. Target detik ditetapkan pemilik sesudah baseline hardware. Bukan PASS jika hanya status HTTP200 atau preview awal tampil cepat.

## D — P1: Control Plane, global Guard dan human control

Dasar: `app/api/control_plane.py:142` select_model require_admin; `app/core/config.py:98` select_operator_runtime snapshot/revision; `app/core/control_plane_projection.py:129-137` historical/current NOT_VERIFIED; `app/security/auth.py:12` shared token; `app/models/openrouter.py:59` cost governance. Pola **ADAPT** verified user/admin `OW/utils/auth.py:567/622`; **KEEP** ledger, approval, warning fixture. RISK-CMP-008/009/012/014. Gate3/4/5/18/20; dependency A–C dan keputusan pemilik tentang batas global Guard.

Acceptance terukur yang diusulkan:

- Role matrix public/user/operator/admin dengan deny test untuk tiap operasi sensitif; 100% jalur mutasi wajib melewati Guard/policy yang sama, actor identity dari boundary tepercaya.
- Dashboard memperlihatkan build/config revision, source evidence, freshness dan status NOT_VERIFIED ketika receipt tidak tersedia. Artefak historis tidak mengubah live readiness menjadi PASS.
- Pilihan model/operator konflik revision ditolak, provider aktual sesuai receipt; status model tersedia tidak diartikan model sedang resident atau sudah menjawab.
- Budget reserve/settle/unknown, pricing revision dan manual reconciliation dapat ditelusuri; 0 dispatch saat governance tidak tersedia/budget habis; perubahan provider eksternal memerlukan izin sesuai policy pemilik dan tidak meniadakan SOP local-only.
- Per-principal quota serta overload visible; audit redacted, expiry/replay/payload binding teruji; 0 credential tersimpan dalam UI persistent storage yang tidak disahkan.

Global Guard berstatus belum selesai sesuai mandat pemilik; reuse fragmen yang ada, bukan engine duplikat. Acceptance ini tidak mengaktifkan Hermes/Developer Agent.

## E — P1: tutup jalur tools sebelum aktivasi; agent tetap HOLD

Dasar: `app/governance/tools.py:111` execute vs `app/mcp/mcp.py:71` call_tool; `app/tools/filesystem.py:23` read_file/:83 find_file; `app/execution/native.py:15` NativeExecutor.execute. **KEEP** governed registry; **ADAPT** adapter MCP ke boundary sama. RISK-CMP-006/007. Gate8/9/18/20; dependency D dan izin scope tools terpisah.

Acceptance: 100% registered executable tools memiliki schema, permission, risk, timeout, audit dan approval binding; unknown name/invalid args/expired approval/replay ditolak; .env/key/token/data restricted dan traversal/symlink escape tidak dapat dibaca; ukuran read dibatasi; timeout tidak dianggap sandbox OS. Uji mutasi hanya di fixture terisolasi setelah approval. Jika tools belum diperlukan P0, biarkan nonaktif; jangan buka caller agent untuk membuktikan registry.

**HOLD/SKIP** dynamic Python plugin loader `OW/utils/plugin.py:242/291`; **HOLD** Hermes baru, Developer Agent, Self-Learning, autonomous web/knowledge write. Legacy `app/api/routes.py:1171-1173` harus dicatat sebagai dependency runtime yang sudah ada; keputusan menghapus/menonaktifkannya bukan bagian audit ini.

## F — P1: evidence web terpisah dan release terkendali

Dasar: `app/knowledge/web_evidence.py:1` kandidat terisolasi tanpa active-store wiring; `OW/routers/retrieval.py:2174` search_web/:2554 process_web_search; `docs/audit/GATES.md:381` release/rollback. **ADAPT** provenance dan review sumber luar, **SKIP/HOLD** pencampuran otomatis ke SOP internal. Dependency A–E dan penerimaan pemilik.

Acceptance: sumber luar punya provenance, timestamp, checksum, izin penggunaan dan review; jawaban membedakan sumber internal resmi dan web; 0 pengiriman SOP ke search/provider eksternal; kandidat tidak otomatis menulis active index. Sebelum publikasi, semua risiko CRITICAL/HIGH yang berlaku pada exposure target ditutup dengan evidence, rollback disiapkan dan disetujui Gate21. Pentest tetap tidak dilakukan dalam audit ini; jadwalnya mengikuti keputusan pemilik terpisah.

Estimasi waktu/biaya implementasi: [ASUMSI] belum dibuat karena data hardware, target latency, kebijakan disclosure dan scope global Guard belum disahkan; tidak dipakai menentukan prioritas. Prioritas berasal dari boundary kode dan R8, bukan estimasi spekulatif.
